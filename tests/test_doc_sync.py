"""Native refresh failures and the official documentation content formats."""

import hashlib
import json
import runpy
import socket
from contextlib import contextmanager
from http import HTTPStatus
from http.client import parse_headers
from http.server import HTTPServer
from pathlib import Path
from threading import Event, Thread
from urllib.error import HTTPError
from urllib.parse import urlencode

import pytest

ROOT = Path(__file__).parents[1]


@pytest.fixture
def sync():
  return runpy.run_path(str(ROOT / 'scripts/sync_volcengine_docs.py'))


@contextmanager
def _doc_http_peer(responses: list[tuple[int, dict]]):
  """Serve declared responses through real HTTP and observe client EOF."""
  requests = []
  sent = []
  departed = []
  errors = []
  sockets = []
  ready = Event()

  def handle(connection: socket.socket, _address, _server):
    sockets.append(connection)
    connection.settimeout(5)
    try:
      with connection.makefile('rb') as reader:
        method, target, version = (
          reader.readline(65537).decode('iso-8859-1').rstrip('\r\n').split()
        )
        headers = parse_headers(reader)
        index = len(requests)
        requests.append(
          {
            'method': method,
            'target': target,
            'version': version,
            'headers': {key.lower(): value for key, value in headers.items()},
          }
        )
        status, payload = responses[index]
        body = json.dumps(payload, separators=(',', ':')).encode()
        frame = (
          f'HTTP/1.1 {status} {HTTPStatus(status).phrase}\r\n'
          'Content-Type: application/json\r\n'
          f'Content-Length: {len(body)}\r\n'
          'Connection: close\r\n\r\n'
        ).encode() + body
        connection.sendall(frame)
        sent.append((status, body))
        # A completed body does not authorize this peer to retire the client.
        # The original urllib response/error owner must close its own socket.
        assert reader.read(1) == b''
        departed.append(index)
    except Exception as error:
      errors.append(error)

  server = HTTPServer(('127.0.0.1', 0), handle)
  port = server.server_address[1]

  def serve():
    ready.set()
    try:
      server.serve_forever(poll_interval=0.01)
    except Exception as error:
      errors.append(error)

  thread = Thread(target=serve, name='doc-sync-http-peer', daemon=True)
  shutdown = None
  thread.start()
  try:
    assert ready.wait(5)
    assert thread.is_alive()
    assert server.socket.getsockname() == ('127.0.0.1', port)
    yield {
      'url': f'http://127.0.0.1:{port}/api/doc/getDocDetail',
      'host': f'127.0.0.1:{port}',
      'requests': requests,
      'sent': sent,
      'departed': departed,
    }
  finally:
    shutdown = Thread(
      target=server.shutdown, name='doc-sync-http-stop', daemon=True
    )
    shutdown.start()
    shutdown.join(timeout=10)
    server.server_close()
    for connection in sockets:
      connection.close()
    thread.join(timeout=5)
    assert not shutdown.is_alive()
    assert not thread.is_alive()
    assert server.socket.fileno() == -1
    assert all(connection.fileno() == -1 for connection in sockets)
    assert errors == []
    assert departed == list(range(len(requests)))


def test_rich_text_keeps_nested_fields_tables_samples_images(sync):
  samples = {
    'config': {'inputName': 'Request', 'outputName': 'Response'},
    'data': [
      {
        'title': 'Create',
        'inputCode': r'{\n\"type\":\"session.create\"}',
        'outputCode': r'{\"type\":\"session.created\"}',
      }
    ],
  }

  def zone(*ops):
    return {'ops': list(ops)}

  def op(text, **attrs):
    return {'insert': text, 'attributes': attrs}

  content = json.dumps(
    {
      'data': {
        '0': zone(
          op('*', lmkr='1', heading='h1'),
          op('API\n'),
          op(' ', zoneId='fields', collapseStatus='fold'),
          op(' ', aceTable='rows cols'),
          op(' ', image='true', src='https://example.test/diagram.png'),
          op(
            'guide',
            hyperlink=json.dumps(
              {'href': 'https://docs.volcengine.com/docs/6561/2549732'}
            ),
          ),
        ),
        'fields': zone(
          op('Nested field\n'), op(' ', zoneId='code', type='codeblock')
        ),
        'code': zone(op('{"rate":16000}')),
        'rows': zone(op({'id': 'r1'}), op({'id': 'r2'})),
        'cols': zone(op({'id': 'c1'})),
        'xr1xc1': zone(op('event')),
        'xr2xc1': zone(op('session.created')),
        'panel-example': zone(op(' ', apiSampleData=json.dumps(samples))),
      }
    }
  )
  result = sync['_clean_content'](content)
  assert '# API' in result
  assert 'Nested field' in result
  assert '```\n{"rate":16000}\n```' in result
  assert '| event |\n| --- |\n| session.created |' in result
  assert '![Diagram](https://example.test/diagram.png)' in result
  assert '```json\n{\n"type":"session.create"}\n```' in result
  assert sync['_linked_volcengine_doc_ids'](result) == ['2549732']
  assert (
    sync['_clean_content']('<span class="x">plain</span>  \ntext  ')
    == 'plain\ntext'
  )


@pytest.mark.parametrize(
  'zones',
  [
    {'0': {'ops': [{'insert': ' ', 'attributes': {'zoneId': 'missing'}}]}},
    {'0': {'ops': [{'insert': ' ', 'attributes': {'zoneId': '0'}}]}},
    {
      '0': {'ops': []},
      'unreferenced-fields': {'ops': [{'insert': 'important'}]},
    },
  ],
)
def test_invalid_or_unvisited_zones_fail_closed(sync, zones):
  with pytest.raises(ValueError):
    sync['_render_rich_text'](zones)


@pytest.mark.parametrize('fail_fetch', [True, False])
def test_failed_refresh_preserves_previous_snapshots(
  sync, monkeypatch, tmp_path, fail_fetch
):
  """Native fetch/cleaning errors occur before any old snapshot is replaced."""
  snapshot = tmp_path / 'previous.md'
  snapshot.write_text('previous')
  manifest = tmp_path / 'manifest.json'
  manifest.write_text('{}')
  (tmp_path / 'sentinel.bin').write_bytes(b'unchanged\x00\xff')
  nested = tmp_path / 'retained'
  nested.mkdir()
  (nested / 'nested.md').write_text('nested snapshot')
  before = {
    str(path.relative_to(tmp_path)): (
      path.read_bytes(),
      path.stat().st_mtime_ns,
    )
    for path in sorted(tmp_path.rglob('*'))
    if path.is_file()
  }
  docs = sync['DOCS']
  assert [doc.document_id for doc in docs] == [
    '2549778',
    '2549732',
    '1594356',
    '1329505',
    '1719100',
    '1598757',
    '1354869',
    '1257544',
  ]
  payloads = [
    {
      'Result': {
        'Content': '{invalid json'
        if not fail_fetch and index == 3
        else f'<span>Document {doc.document_id}</span>\ncontent',
        'Title': doc.name,
        'UpdatedTime': '2026-10-06',
      }
    }
    for index, doc in enumerate(docs)
  ]
  responses = [(200, payload) for payload in payloads]
  if fail_fetch:
    responses[1] = (503, {'error': 'provider unavailable'})
  expected_count = 2 if fail_fetch else len(docs)
  original_fetch = sync['fetch_doc']
  with _doc_http_peer(responses) as peer:
    # Deployment constants remain inputs; every callable is the loaded source.
    monkeypatch.setenv('no_proxy', '127.0.0.1')
    monkeypatch.setitem(sync['main'].__globals__, 'OUTPUT_DIR', tmp_path)
    monkeypatch.setitem(sync['main'].__globals__, 'API_URL', peer['url'])
    assert sync['main'].__globals__['fetch_doc'] is original_fetch
    with pytest.raises(
      HTTPError if fail_fetch else json.JSONDecodeError
    ) as failed:
      sync['main']()
    if fail_fetch:
      error = failed.value
      assert isinstance(error, HTTPError)
      response = error.fp
      try:
        assert error.code == 503
        assert error.reason == 'Service Unavailable'
        assert error.url == (
          peer['url']
          + '?'
          + urlencode(
            {
              'LibraryID': '6561',
              'DocumentID': docs[1].document_id,
              'AuditDocumentID': '',
              'type': 'online',
            }
          )
        )
        body = json.dumps(
          {'error': 'provider unavailable'}, separators=(',', ':')
        ).encode()
        assert dict(error.headers) == {
          'Content-Type': 'application/json',
          'Content-Length': str(len(body)),
          'Connection': 'close',
        }
        assert error.read() == body
      finally:
        error.close()
      assert response.isclosed()
    else:
      assert failed.value.doc == '{invalid json'
      assert failed.value.pos == 1
    assert peer['requests'] == [
      {
        'method': 'GET',
        'target': '/api/doc/getDocDetail?'
        + urlencode(
          {
            'LibraryID': '6561',
            'DocumentID': doc.document_id,
            'AuditDocumentID': '',
            'type': 'online',
          }
        ),
        'version': 'HTTP/1.1',
        'headers': {
          'accept-encoding': 'identity',
          'host': peer['host'],
          'accept': 'application/json',
          'referer': doc.source_url,
          'user-agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36'
          ),
          'connection': 'close',
        },
      }
      for doc in docs[:expected_count]
    ]
    assert peer['sent'] == [
      (status, json.dumps(payload, separators=(',', ':')).encode())
      for status, payload in responses[:expected_count]
    ]
  assert {
    str(path.relative_to(tmp_path)): (
      path.read_bytes(),
      path.stat().st_mtime_ns,
    )
    for path in sorted(tmp_path.rglob('*'))
    if path.is_file()
  } == before
  assert snapshot.read_text() == 'previous'
  assert manifest.read_text() == '{}'


def test_snapshot_manifest_hashes_and_native_sources():
  manifest = json.loads(
    (ROOT / 'doc_sync/volcengine/manifest.json').read_text()
  )
  assert {'2549778', '2549732'} <= {
    doc['document_id'] for doc in manifest['docs']
  }
  for doc in manifest['docs']:
    content = (ROOT / doc['file']).read_text().removesuffix('\n')
    assert hashlib.sha256(content.encode()).hexdigest() == doc['content_sha256']
    assert not content.startswith('{"version"'), (
      'Track rendered Content, not editor JSON'
    )

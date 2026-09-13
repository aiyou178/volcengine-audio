"""Offline regressions for the two official documentation content formats."""

import hashlib
import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


@pytest.fixture
def sync():
  return runpy.run_path(str(ROOT / 'scripts/sync_volcengine_docs.py'))


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
  snapshot = tmp_path / 'previous.md'
  snapshot.write_text('previous')
  manifest = tmp_path / 'manifest.json'
  manifest.write_text('{}')

  def fetch(doc):
    if fail_fetch:
      raise RuntimeError('network unavailable')
    return 'https://example.test', {'Result': {'Content': '{invalid json'}}

  namespace = sync['main'].__globals__
  monkeypatch.setitem(namespace, 'OUTPUT_DIR', tmp_path)
  monkeypatch.setitem(namespace, 'fetch_doc', fetch)
  with pytest.raises((RuntimeError, ValueError)):
    sync['main']()
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

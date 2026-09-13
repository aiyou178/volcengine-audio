"""Fetch cleaned Volcengine doc content snapshots for SDK sync reviews."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class DocSource:
  """Source metadata for a Volcengine documentation page."""

  name: str
  document_id: str
  source_url: str


DOCS = [
  DocSource(
    name='seeduplex_realtime',
    document_id='2549778',
    source_url='https://www.volcengine.com/docs/6561/2549778?lang=zh',
  ),
  DocSource(
    name='seeduplex_integration',
    document_id='2549732',
    source_url='https://www.volcengine.com/docs/6561/2549732?lang=zh',
  ),
  DocSource(
    name='realtime_dialogue',
    document_id='1594356',
    source_url='https://www.volcengine.com/docs/6561/1594356?lang=zh',
  ),
  DocSource(
    name='tts_websocket_bidirectional_v3',
    document_id='1329505',
    source_url='https://www.volcengine.com/docs/6561/1329505?lang=zh',
  ),
  DocSource(
    name='tts_websocket_unidirectional_v3',
    document_id='1719100',
    source_url='https://www.volcengine.com/docs/6561/1719100?lang=zh',
  ),
  DocSource(
    name='tts_http_chunked_sse_v3',
    document_id='1598757',
    source_url='https://www.volcengine.com/docs/6561/1598757?lang=zh',
  ),
  DocSource(
    name='stt_streaming_bigmodel',
    document_id='1354869',
    source_url='https://www.volcengine.com/docs/6561/1354869?lang=zh',
  ),
  DocSource(
    name='tts_voice_list',
    document_id='1257544',
    source_url='https://www.volcengine.com/docs/6561/1257544?lang=zh',
  ),
]


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PACKAGE_ROOT / 'doc_sync' / 'volcengine'
API_URL = 'https://www.volcengine.com/api/doc/getDocDetail'


def _sha256(text: str) -> str:
  return hashlib.sha256(text.encode()).hexdigest()


def _clean_content(content: str) -> str:
  """Return the tracked docs text with noisy span tags removed."""

  if content.lstrip().startswith('{'):
    document = json.loads(content)
    if 'data' in document and '0' in document['data']:
      content = _render_rich_text(document['data'])
  cleaned = re.sub(r'</?span\b[^>]*>', '', content)
  return '\n'.join(line.rstrip() for line in cleaned.strip().splitlines())


def _render_rich_text(zones: dict) -> str:
  """Render Volcengine zones, including collapsed fields and API examples."""
  active: set[str] = set()
  visited: set[str] = set()

  def render(zone_id: str) -> str:
    if zone_id in active or zone_id not in zones:
      raise ValueError(f'Invalid documentation zone reference: {zone_id}')
    active.add(zone_id)
    visited.add(zone_id)
    parts = []
    for op in zones[zone_id]['ops']:
      attrs = op.get('attributes', {})
      value = op.get('insert', '')
      if attrs.get('lmkr'):
        if attrs.get('heading'):
          parts.append('\n' + '#' * int(attrs['heading'][1:]) + ' ')
        elif attrs.get('list'):
          parts.append('- ')
        continue
      if attrs.get('zoneId'):
        nested = render(attrs['zoneId'])
        if attrs.get('type') == 'codeblock':
          nested = '\n```\n' + nested.strip() + '\n```\n'
        parts.append('\n' + nested + '\n')
      elif attrs.get('aceTable'):
        row_zone, col_zone = attrs['aceTable'].split()
        visited.update((row_zone, col_zone))
        rows = zones[row_zone]['ops']
        cols = zones[col_zone]['ops']
        parts.append('\n')
        for index, row in enumerate(rows):
          cells = []
          for col in cols:
            cell_id = 'x' + row['insert']['id'] + 'x' + col['insert']['id']
            cells.append(
              render(cell_id).strip().replace('|', '\\|').replace('\n', '<br>')
            )
          parts.append('| ' + ' | '.join(cells) + ' |\n')
          if index == 0:
            parts.append('| ' + ' | '.join('---' for _ in cols) + ' |\n')
        parts.append('\n')
      elif attrs.get('apiSampleData'):
        samples = json.loads(attrs['apiSampleData'])
        for sample in samples['data']:
          parts.append('\n### ' + sample['title'] + '\n')
          for side in ('input', 'output'):
            code = sample.get(side + 'Code', '')
            # The editor stores sample code with an additional JSON escape.
            try:
              code = json.loads('"' + code + '"')
            except json.JSONDecodeError:
              pass
            parts.append('\n' + samples['config'][side + 'Name'] + '\n')
            parts.append('\n```json\n' + code + '\n```\n')
      elif attrs.get('file'):
        parts.append(f'[{attrs["filename"]}]({attrs["src"]})')
      elif attrs.get('image'):
        parts.append(f'![{attrs.get("alt", "Diagram")}]({attrs["src"]})')
      elif isinstance(value, str):
        if attrs.get('hyperlink'):
          href = json.loads(attrs['hyperlink'])['href']
          value = f'[{value}]({href})'
        elif attrs.get('inlineCode'):
          value = f'`{value}`'
        parts.append(value)
      else:
        raise ValueError('Unsupported documentation content operation')
    active.remove(zone_id)
    return ''.join(parts)

  rendered = render('0')
  # API example tabs are exported as detached panels, not zone references.
  for zone_id in zones:
    if zone_id.startswith('panel-') and zone_id not in visited:
      rendered += '\n## API examples\n' + render(zone_id)
  missing = set(zones) - visited
  if missing:
    raise ValueError(f'Unrendered documentation zones: {sorted(missing)}')
  return rendered


def _linked_volcengine_doc_ids(content: str) -> list[str]:
  """Return linked Volcengine docs IDs mentioned by a snapshot."""

  return sorted(
    set(
      re.findall(
        r'https://(?:www\.|docs\.)?volcengine\.com/docs/6561/(\d+)', content
      )
    )
  )


def _clear_output_dir() -> None:
  """Remove previously generated snapshot files before writing new ones."""

  if not OUTPUT_DIR.exists():
    return

  for path in OUTPUT_DIR.iterdir():
    if path.is_file():
      path.unlink()


def _doc_api_url(doc: DocSource) -> str:
  """Return the public getDocDetail API URL for a docs page."""

  query = urlencode(
    {
      'LibraryID': '6561',
      'DocumentID': doc.document_id,
      'AuditDocumentID': '',
      'type': 'online',
    }
  )
  return f'{API_URL}?{query}'


def fetch_doc(doc: DocSource) -> tuple[str, dict]:
  """Fetch the backing getDocDetail payload directly."""

  api_url = _doc_api_url(doc)
  request = Request(
    api_url,
    headers={
      'Accept': 'application/json',
      'Referer': doc.source_url,
      'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36'
      ),
    },
  )
  with urlopen(request, timeout=30) as response:
    status = response.status
    if status != 200:
      raise RuntimeError(f'Unexpected status {status} for {doc.document_id}')
    payload = json.loads(response.read().decode())

  if not payload.get('Result'):
    raise RuntimeError(f'Missing Result in response for {doc.document_id}')

  return api_url, payload


def main() -> None:
  """Write cleaned content snapshots and a manifest for future diffs."""

  OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
  manifest = {
    'synced_at': datetime.now(UTC).isoformat(),
    'command': 'python scripts/sync_volcengine_docs.py',
    'docs': [],
    'untracked_linked_document_ids': [],
  }

  fetched = [(doc, *fetch_doc(doc)) for doc in DOCS]
  cleaned = {
    doc.document_id: _clean_content(payload['Result']['Content'])
    for doc, _, payload in fetched
  }
  tracked_doc_ids = {doc.document_id for doc, _, _ in fetched}
  linked_doc_ids: set[str] = set()
  _clear_output_dir()

  for doc, api_url, payload in fetched:
    result = payload.get('Result') or {}
    content = cleaned[doc.document_id]
    doc_linked_ids = _linked_volcengine_doc_ids(content)
    linked_doc_ids.update(doc_linked_ids)
    file_name = f'{doc.document_id}-{doc.name}.md'
    file_path = OUTPUT_DIR / file_name
    file_path.write_text(f'{content}\n')

    manifest['docs'].append(
      {
        'name': doc.name,
        'document_id': doc.document_id,
        'title': result.get('Title'),
        'updated_time': result.get('UpdatedTime'),
        'source_url': doc.source_url,
        'api_url': api_url,
        'file': str(file_path.relative_to(PACKAGE_ROOT)),
        'content_sha256': _sha256(content),
        'linked_document_ids': doc_linked_ids,
      }
    )

  manifest['untracked_linked_document_ids'] = sorted(
    linked_doc_ids - tracked_doc_ids
  )

  manifest_path = OUTPUT_DIR / 'manifest.json'
  manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2)
  manifest_path.write_text(f'{manifest_text}\n')
  print(f'Wrote {len(manifest["docs"])} doc snapshots to {OUTPUT_DIR}')


if __name__ == '__main__':
  main()

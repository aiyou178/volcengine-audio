"""Capture cleaned Volcengine doc content snapshots for SDK sync reviews."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


@dataclass(frozen=True)
class DocSource:
  """Source metadata for a Volcengine documentation page."""

  name: str
  document_id: str
  source_url: str


DOCS = [
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
]


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PACKAGE_ROOT / 'doc_sync' / 'volcengine'


def _sha256(text: str) -> str:
  return hashlib.sha256(text.encode()).hexdigest()


def _clean_content(content: str) -> str:
  """Return the tracked docs text with noisy span tags removed."""

  cleaned = re.sub(r'</?span\b[^>]*>', '', content)
  return cleaned.strip()


def _clear_output_dir() -> None:
  """Remove previously generated snapshot files before writing new ones."""

  if not OUTPUT_DIR.exists():
    return

  for path in OUTPUT_DIR.iterdir():
    if path.is_file():
      path.unlink()


def capture_doc(page: Page, doc: DocSource) -> tuple[str, dict]:
  """Capture the backing getDocDetail response for a rendered docs page."""

  def is_target_response(response) -> bool:
    url = response.url
    return (
      '/api/doc/getDocDetail?' in url and f'DocumentID={doc.document_id}' in url
    )

  with page.expect_response(is_target_response) as response_info:
    page.goto(doc.source_url, wait_until='networkidle')
    page.wait_for_timeout(1000)

  response = response_info.value
  if response.status != 200:
    raise RuntimeError(
      f'Unexpected status {response.status} for {doc.document_id}'
    )

  payload = json.loads(response.text())
  return response.url, payload


def main() -> None:
  """Write cleaned content snapshots and a manifest for future diffs."""

  OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
  _clear_output_dir()
  manifest = {
    'synced_at': datetime.now(UTC).isoformat(),
    'command': (
      'uvx --with playwright python '
      'packages/volcengine-audio/scripts/sync_volcengine_docs.py'
    ),
    'docs': [],
  }

  with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    try:
      for doc in DOCS:
        page = browser.new_page()
        try:
          api_url, payload = capture_doc(page, doc)
        finally:
          page.close()

        result = payload.get('Result') or {}
        content = _clean_content(result.get('Content', ''))
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
          }
        )
    finally:
      browser.close()

  manifest_path = OUTPUT_DIR / 'manifest.json'
  manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2)
  manifest_path.write_text(f'{manifest_text}\n')
  print(f'Wrote {len(manifest["docs"])} doc snapshots to {OUTPUT_DIR}')


if __name__ == '__main__':
  main()

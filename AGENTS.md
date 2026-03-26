# AGENTS.md

## Scope

This package contains the standalone `volcengine-audio` SDK:

* `src/volcengine_audio/stt.py`: STT schemas and helpers
* `src/volcengine_audio/tts.py`: TTS schemas and helpers
* `src/volcengine_audio/realtime.py`: realtime dialogue schemas and helpers
* `src/volcengine_audio/protocol.py`: shared protocol enums and binary helpers
* `tests/`: package-level regression coverage

## Source of truth

Use the tracked Volcengine doc snapshots in `doc_sync/volcengine/` as the
first stop during maintenance:

* `doc_sync/volcengine/manifest.json`
* `doc_sync/volcengine/1594356-realtime_dialogue.md`
* `doc_sync/volcengine/1329505-tts_websocket_bidirectional_v3.md`
* `doc_sync/volcengine/1719100-tts_websocket_unidirectional_v3.md`
* `doc_sync/volcengine/1598757-tts_http_chunked_sse_v3.md`
* `doc_sync/volcengine/1354869-stt_streaming_bigmodel.md`

These files are tracked in git so future syncs can diff upstream changes
quickly. They are repo-only artifacts and are not packed into wheels because
the wheel build only includes `src/volcengine_audio`.

Snapshot format guidance:

* Store only the cleaned `Result.Content` text from the upstream docs.
* Do not store the full JSON response payload in tracked snapshot files.
* Strip `<span ...>` and `</span>` tags before writing snapshots so future
  diffs stay readable.
* Keep metadata such as `updated_time`, `source_url`, `api_url`, and the
  content hash in `manifest.json`.

## How to refresh docs

Run:

```bash
uvx --with playwright python packages/volcengine-audio/scripts/sync_volcengine_docs.py
```

What the script does:

1. Opens each public Volcengine docs page with Playwright.
2. Captures the backing `api/doc/getDocDetail` JSON response.
3. Extracts only `Result.Content`, removes span tags, and writes a `.md`
   snapshot for each tracked doc.
4. Writes `manifest.json` with source metadata and content hashes.

Important note:

* The public docs pages are JS-rendered.
* Direct CLI requests to the JSON endpoint may return unauthorized.
* Prefer Playwright response interception over raw `curl` scraping.

## SDK sync workflow

1. Refresh `doc_sync/volcengine/*.md` and `manifest.json`.
2. Diff the changed content snapshots and identify schema/helper drift.
3. Update package code:
   * `stt.py` for request fields, locales, and response payload changes.
   * `tts.py` for resource IDs, additions, and response payload changes.
   * `realtime.py` for session config, event payloads, and response models.
   * `protocol.py` when message or event identifiers change.
   * `__init__.py` if new public exports are added.
4. Update tests in `tests/` to cover the new upstream behavior.
5. Update `README.md` and `README.zh-CN.md`:
   * refresh the local sync date
   * refresh upstream source update timestamps if they changed
   * document any new sync-sensitive fields or resources

## Practical diff hints

Useful commands:

```bash
git diff -- packages/volcengine-audio/doc_sync/volcengine
git diff -- packages/volcengine-audio/src/volcengine_audio
rg -n "keep_alive|push_to_talk|concurr|UpdatedTime" packages/volcengine-audio
```

High-signal fields to watch:

* Realtime `dialog.extra`, `tts.audio_config`, `asr.extra`
* TTS resource IDs and `req_params.additions`
* STT language enums and optional request flags
* Event IDs and response payload shapes

## Validation

Run at least:

```bash
uv run pytest packages/volcengine-audio/tests
uv run ruff check packages/volcengine-audio/src packages/volcengine-audio/tests
```

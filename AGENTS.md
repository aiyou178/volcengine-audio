# AGENTS.md

Guidance for coding agents working in the `volcengine-audio` package
repository.

## 1) What This Package Is

`volcengine-audio` is the standalone Python SDK for Volcengine audio
services. It provides typed schemas and request/response helpers for:

- Speech-to-Text (STT)
- Text-to-Speech (TTS)
- Realtime Dialogue
- Shared websocket/binary protocol helpers

Keep this guide in sync with `README.md`. The README is the user-facing
package guide and records the local SDK/doc sync date and tracked upstream
timestamps; this file carries the agent-facing workflow and code-boundary
details that make those README claims actionable.

Core maintenance entrypoints:

- `src/volcengine_audio/stt.py`
- `src/volcengine_audio/tts.py`
- `src/volcengine_audio/realtime.py`
- `src/volcengine_audio/protocol.py`
- `src/volcengine_audio/__init__.py`
- `scripts/sync_volcengine_docs.py`

## 2) Environment and Dependencies

- Local development runtime: Python 3.13
- Package metadata: `requires-python = ">=3.10"`
- Package manager: `uv`
- Build backend: `hatchling`
- Runtime dependencies: `pydantic`, `orjson`

Useful setup commands:

```bash
uv sync --frozen --group dev
uv run pytest tests
uv run ruff check src tests
```

## 3) Source of Truth

Use the tracked Volcengine doc snapshots in `doc_sync/volcengine/` as the
first stop during maintenance:

- `doc_sync/volcengine/manifest.json`
- `doc_sync/volcengine/1594356-realtime_dialogue.md`
- `doc_sync/volcengine/1329505-tts_websocket_bidirectional_v3.md`
- `doc_sync/volcengine/1719100-tts_websocket_unidirectional_v3.md`
- `doc_sync/volcengine/1598757-tts_http_chunked_sse_v3.md`
- `doc_sync/volcengine/1354869-stt_streaming_bigmodel.md`
- `doc_sync/volcengine/1257544-tts_voice_list.md`

These files are tracked in git so future syncs can diff upstream changes
quickly. They are repo-only maintenance artifacts and are not packed into
wheels because the wheel build only includes `src/volcengine_audio`.

Current tracked upstream timestamps from `manifest.json` and `README.md`:

- Realtime dialogue: `2026-06-04T10:15:01Z`
- TTS WebSocket bidirectional V3: `2026-05-25T08:51:30Z`
- TTS WebSocket unidirectional V3: `2026-05-25T08:49:18Z`
- TTS HTTP Chunked/SSE V3: `2026-05-25T09:03:36Z`
- STT streaming bigmodel: `2026-05-29T02:49:48Z`
- TTS voice list: `2026-05-26T05:41:00Z`

Latest local sync review:

- Local sync date in README: `2026-06-06`.
- Realtime docs added 12K 2.0 context notes, O/SC convergence wording,
  updated SC2.0 voice-list references, `tts.extra.tts_2.0_model`, and a
  10w TPM default. The SDK exposes this as `tts_2_0_model` with the wire alias
  `tts_2.0_model`.
- STT docs added non-streaming `enable_auto_lang` for automatic language
  detection across 25 locales. The SDK request schema includes
  `enable_auto_lang`.
- TTS docs now describe the TTS 2.0 default model as
  `seed-tts-2.0-standard`, expand ICL2.0 explicit-language guidance, and
  clarify `context_texts`, `section_id`, and `use_tag_parser`. The existing SDK
  fields cover those parameters.
- TTS voice-list doc `1257544` is now tracked because the API docs delegate
  speaker, model/resource compatibility, voice ability, and language support
  details to that page. The SDK still keeps speaker fields open as `str`.

Snapshot format guidance:

- Store only the cleaned `Result.Content` text from the upstream docs.
- Do not store the full JSON response payload in tracked snapshot files.
- Strip `<span ...>` and `</span>` tags before writing snapshots so future
  diffs stay readable.
- Keep metadata such as `updated_time`, `source_url`, `api_url`, and the
  content hash in `manifest.json`.
- Review `linked_document_ids` and `untracked_linked_document_ids` in
  `manifest.json` after each sync. Add linked Volcengine docs to
  `scripts/sync_volcengine_docs.py` when they carry SDK-relevant enum values,
  field descriptions, resource/model compatibility, event IDs, or response
  shapes. Do not add credential FAQ, console operation, or setup-only links
  unless their content becomes part of SDK behavior.

## 4) Quality and Static Checks

Run what is relevant for the change:

```bash
uv run ruff check src tests
uv run ruff format src tests
uv run pytest
```

## 5) Testing

Tests live under `tests/` and should stay package-local.

Useful commands:

```bash
# full package suite
uv run pytest tests

# targeted file
uv run pytest tests/test_realtime.py

# targeted test selection
uv run pytest tests -k tts
```

Testing expectations:

- Add or update regression coverage for any schema, enum, protocol, or helper
  change.
- Prefer exact payload assertions over loose partial checks.
- Cover both request generation and response parsing when protocol behavior
  changes.

## 6) Repo Map

- `src/volcengine_audio/protocol.py`: shared enums, headers, and binary helpers
- `src/volcengine_audio/stt.py`: STT request/response models and helpers
- `src/volcengine_audio/tts.py`: TTS request/response models and helpers
- `src/volcengine_audio/realtime.py`: realtime dialogue models and helpers
- `src/volcengine_audio/__init__.py`: public exports
- `tests/`: package-level regression coverage
- `doc_sync/volcengine/`: tracked upstream snapshots and manifest
- `scripts/sync_volcengine_docs.py`: direct API doc sync utility
- `README.md`: English package guide and sync metadata
- `README.zh-CN.md`: Chinese package guide and sync metadata

## 7) Documentation Sync Rules

Refresh docs with:

```bash
python scripts/sync_volcengine_docs.py
```

What the script does:

1. Requests each public `api/doc/getDocDetail` JSON response directly.
2. Extracts only `Result.Content`, removes span tags, and writes a `.md`
   snapshot for each tracked doc.
3. Writes `manifest.json` with source metadata, content hashes, and linked
   Volcengine doc IDs.

Important notes:

- Fetch all docs successfully before clearing old snapshots so a failed sync
  does not leave the snapshot directory empty.
- If the task is only to sync `AGENTS.md` or `README.md` with already-tracked
  snapshots, do not rerun the sync script. Read `manifest.json`, the README
  files, and `git diff -- doc_sync/volcengine` instead.

## 8) Coding Standards (Package-Specific)

- Keep the package standalone; do not import code from outside this package
  into `src/volcengine_audio`.
- Use `orjson` for JSON operations in package code when serialization is
  needed.
- Prefer modern typing syntax such as `list[str]` and `str | None`.
- Annotate function parameters and return types.
- Always add docstrings for added functions and public APIs.
- Keep imports at top unless lazy import is required.
- Logging style should use interpolation, for example
  `logger.info('message %s', value)`.
- Do not abstract code into helpers unless it is genuinely reused or clearly
  improves maintainability.
- Protocol and event constants belong in `protocol.py`; do not duplicate them
  across modules.
- If a change affects the public SDK surface, update `__init__.py` in the same
  change.
- If docs or behavior changed materially, update `README.md` and
  `README.zh-CN.md` in the same change.

Formatting from repo config:

- Ruff enforced
- 2-space indentation
- 80-char line length
- single quotes

## 9) Change Playbooks

### A) Sync upstream docs and SDK behavior

1. Refresh `doc_sync/volcengine/*.md` and `manifest.json`.
2. Diff the changed snapshots and identify schema/helper drift.
3. Update package code:
   - `stt.py` for request fields, locales, and response payload changes
   - `tts.py` for resource IDs, additions, and response payload changes
   - `realtime.py` for session config, event payloads, and response models
   - `protocol.py` when message or event identifiers change
   - `__init__.py` if new public exports are added
4. Update tests in `tests/` to cover the new upstream behavior.
5. Update `README.md` and `README.zh-CN.md`:
   - refresh the local sync date
   - refresh upstream source update timestamps if they changed
   - document any new sync-sensitive fields or resources

### B) Add or change an SDK model/helper

1. Find the upstream doc snapshot that justifies the change.
2. Update the relevant module under `src/volcengine_audio/`.
3. Update `protocol.py` as well if the change touches shared enums or framing.
4. Export the symbol from `__init__.py` if it is part of the public API.
5. Add targeted regression tests in `tests/`.
6. Update README examples if the user-facing usage changed.

### C) Change protocol or event handling

1. Update shared enums/helpers in `protocol.py`.
2. Update dependent modules in `stt.py`, `tts.py`, or `realtime.py`.
3. Add tests for payload generation and parsing.
4. Verify existing event IDs and helper defaults still match upstream docs.

## 10) Practical Diff Hints

Useful commands:

```bash
git diff -- doc_sync/volcengine
git diff -- src/volcengine_audio
rg -n "keep_alive|push_to_talk|concurr|UpdatedTime" .
```

High-signal fields to watch:

- Realtime `dialog.extra`, `tts.extra`, `tts.audio_config`, `asr.extra`
- Realtime control/context events: `UpdateConfig`, `EndASR`,
  `ConversationTruncate`, `ClientInterrupt`, and matching ack events.
- TTS resource IDs and `req_params.additions`
- STT language enums, `context_data`, old/new console auth headers, and
  optional request flags
- Event IDs and response payload shapes

## 11) Validation

Run at least:

```bash
uv run pytest tests
uv run ruff check src tests
```

Also confirm:

- The package still builds as a standalone SDK.
- No temporary scraped artifacts or raw JSON payloads were added to git.
- README sync metadata matches the refreshed snapshots when applicable.

## 12) Practical Agent Checklist

Before finishing code changes, run what is relevant:

1. Refresh doc snapshots if the task is an upstream sync.
2. Run targeted package tests via `uv run pytest ...`.
3. Run `uv run ruff check ...`.

4. Confirm no secrets or temporary scrape artifacts were added to tracked files.
5. Add docstrings and type annotations for new best-effort public code.
6. Update nearby docs in the same change if behavior or maintenance workflow
   changed materially.

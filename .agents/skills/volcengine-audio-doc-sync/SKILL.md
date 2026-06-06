---
name: volcengine-audio-doc-sync
description: Refresh and reconcile Volcengine Audio SDK documentation snapshots and SDK metadata. Use when working on doc_sync/volcengine snapshots, scripts/sync_volcengine_docs.py, Volcengine upstream doc timestamp changes, README sync dates, or schema/helper drift from Volcengine STT, TTS, or realtime dialogue docs in the volcengine-audio package.
---

# Volcengine Audio Doc Sync

## Scope

Use this skill for the standalone `volcengine-audio` SDK. Keep all guidance,
commands, and file paths package-local.

Primary package files:

- `doc_sync/volcengine/manifest.json`
- `doc_sync/volcengine/*.md`
- `scripts/sync_volcengine_docs.py`
- `src/volcengine_audio/`
- `tests/`
- `README.md`
- `README.zh-CN.md`

## Workflow

1. Inspect the current tracked snapshots before running network sync:

```bash
git diff -- doc_sync/volcengine
sed -n '1,220p' doc_sync/volcengine/manifest.json
```

2. If the task asks to refresh upstream docs, run the direct API sync:

```bash
python scripts/sync_volcengine_docs.py
```

3. Diff the refreshed snapshots and manifest. Focus on request fields, enum
   values, event IDs, resource/model names, auth headers, and response payload
   shapes.

4. Review linked docs in `manifest.json`:

- Check each entry's `linked_document_ids` and the top-level
  `untracked_linked_document_ids`.
- Add a linked Volcengine doc to `scripts/sync_volcengine_docs.py` when the
  target page carries SDK-relevant enum values, field descriptions,
  resource/model compatibility, event IDs, response payload shapes, or
  speaker/language support tables.
- Keep credential FAQ, console-operation, setup-only, and marketing links out
  of `DOCS` unless their content becomes part of SDK request/response behavior.
- If a tracked doc stops being linked or becomes obsolete, verify whether it is
  still a source of SDK behavior before removing it from `DOCS`.
- For non-Volcengine links that move SDK-critical information, record the link
  in the review notes and decide whether a separate fetch mechanism is needed;
  do not silently ignore it.

5. Update SDK code only when the snapshot diff proves API drift:

- `stt.py`: request fields, language/audio enums, STT response payloads,
  context data, old/new console auth guidance, and STT error event codes.
- `tts.py`: resource IDs, `req_params.model`, additions, subtitle/timestamp
  payloads, and response events.
- `realtime.py`: session config, dialog/asr/tts extra fields, control events,
  context management requests, and acknowledgement payloads.
- `protocol.py`: shared message types, event IDs, serialization, compression,
  and framing helpers.
- `__init__.py`: public exports for any new public schema or helper.

6. Update package tests for every behavior change. Prefer exact payload
   assertions over partial checks.

7. Update README files only with user-facing facts: install/development usage,
   public examples, API reference, package version, and the local sync date or
   source timestamps when they are meant to be public. Keep procedural sync
   checklists in this skill, not in README files.

## Snapshot Rules

- Store only cleaned upstream `Result.Content` text in tracked `.md` snapshot
  files.
- Do not store full JSON responses in tracked snapshots.
- Strip `<span ...>` and `</span>` tags before writing snapshots.
- Keep source metadata such as `updated_time`, `source_url`, `api_url`, and
  content hashes in `manifest.json`.
- Keep `linked_document_ids` and `untracked_linked_document_ids` in
  `manifest.json` so new, obsolete, or newly important links are visible in
  future diffs.
- Snapshot files are tracked for future diffs, but they are not included in the
  wheel because the build packages only `src/volcengine_audio`.

## Validation

Run focused checks after changing code:

```bash
uv run pytest tests
uv run ruff check src tests
```

For docs-only changes, at least run:

```bash
git diff --check
```

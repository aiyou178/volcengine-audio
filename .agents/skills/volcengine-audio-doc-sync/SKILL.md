---
name: volcengine-audio-doc-sync
description: Refresh Volcengine audio documentation snapshots or reconcile SDK/README metadata with tracked STT, TTS, and realtime docs. Use within the standalone volcengine-audio package.
---

# Volcengine Audio Doc Sync

Run from the package root and keep changes package-local. Inspect existing
`doc_sync/volcengine/manifest.json`, snapshots, and their git diff first.

## Choose the requested outcome

- **README/AGENTS metadata alignment:** use existing snapshots and manifest.
  Do not rerun network sync or alter SDK behavior.
- **Upstream snapshot refresh:** run `python scripts/sync_volcengine_docs.py`,
  review the diff, and update public sync metadata in both README languages.
  Report SDK drift without implementing it unless reconciliation is in scope.
- **SDK reconciliation:** identify upstream evidence, update the affected
  models/helpers, public exports, tests, and user-facing documentation.

## Refresh invariants

Fetch all documents successfully before replacing old snapshots. Track only
cleaned `Result.Content` text, stripping span tags; never track raw JSON
responses. Keep source URLs, API URLs, update timestamps, content hashes,
`linked_document_ids`, and `untracked_linked_document_ids` in the manifest.

Review new or obsolete links. Track linked pages when they define SDK-relevant
fields, enum/event values, response shapes, resource/model compatibility, or
speaker/language tables. Do not expand to credential FAQs, console setup, or
marketing pages without SDK relevance. Verify a page is no longer a behavior
source before removing it. Flag SDK-critical non-Volcengine links if they need a
separate fetch mechanism.

## Reconciliation map

- `stt.py`: language/audio fields, context, auth guidance, response/error events.
- `tts.py`: resource/model IDs, additions, subtitle/timestamp payloads.
- `realtime.py`: session extras, control/context events and acknowledgements.
- `protocol.py`: shared IDs, serialization, compression, framing.
- `__init__.py`: new or changed public exports.

Change code only with evidence of relevant drift and authorization to reconcile
SDK behavior. Cover changed request generation and response parsing with exact
payload tests. Keep procedural checklists here; README files carry public usage
and accurate sync metadata.

## Completion

For code changes run `uv run pytest tests` and `uv run ruff check src tests`;
for docs-only changes check snapshot/manifest consistency and `git diff --check`.
Report refreshed sources, implemented versus reported drift, validation, and
any source that could not be fetched. Do not claim an SDK sync from a
snapshot-only refresh.

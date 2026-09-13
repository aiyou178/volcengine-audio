# Changelog

## 0.2.6 — 2026-09-13

- Add native Seeduplex JSON models for sessions, audio, speech, context,
  function calls and completed tool results.
- Add validated request encoding, native event names and endpoint constants.
- Cover native ASR, TTS and dialogue extensions, including parenthesis filtering
  and the current custom/global search modes.
- Preserve partial session updates, explicit tool-set clearing, unknown response
  event names and unspecified usage counters.
- Add official API and integration-guide snapshots, a schema coverage record,
  and exact round-trip tests for every documented JSON example.
- Update documentation synchronization to retain nested fields, tables,
  diagrams and API examples from the provider's rich-text format.
- Require Python 3.11 or newer, matching the supported standard-library APIs.

Existing STT, TTS and binary realtime APIs are unchanged. Transport, credentials,
audio pacing and tool execution remain application responsibilities.

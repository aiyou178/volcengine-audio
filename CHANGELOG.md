# Changelog

## 0.3.0 — 2026-10-26

- Refresh all eight upstream documentation snapshots as of 2026-10-26,
  including multilingual voice capabilities and the native 64K-token context.
- Accept native Seeduplex `pcm_s16le` output and clarify that `pcm` output
  is 32-bit PCM. Input `pcm` remains 16-bit PCM.
- Default legacy realtime web search to the currently documented `web` mode.
  Explicit legacy `web_summary` values remain accepted for existing callers.
- Declare Python 3.14 and 3.15 support and test Python 3.11 through 3.15 in CI.
  Require orjson 3.12+ and Pydantic 2.14+ on Python 3.15 and newer without
  changing dependency minimums on older Python versions.

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

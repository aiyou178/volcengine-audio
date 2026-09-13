# Native Seeduplex schema audit — 2026-09-13

Scope: reconcile the native JSON API, not replace the legacy binary realtime
protocol. Source metadata, timestamps and hashes are in
[`manifest.json`](../doc_sync/volcengine/manifest.json). The two new sources are
the [API](https://www.volcengine.com/docs/6561/2549778?lang=zh) and
[integration guide](https://www.volcengine.com/docs/6561/2549732?lang=zh).
The six existing STT/TTS/realtime/voice snapshots were refreshed without content
drift. `realtime.py` owns models/helpers; `protocol.py` owns native event names
and endpoint constants. No OpenAI, LiveKit, HTTP client or application dependency
is introduced into this SDK.

## Coverage

| Official surface | SDK mapping |
| --- | --- |
| Session create/update, restored ID, fixed model, instructions, audio, full tool replacement | `SeeduplexSessionRequest`, `SeeduplexSession`, `SeeduplexTool` |
| PCM/speech_opus 16 kHz input; PCM/ogg_opus 24 kHz output; open voice IDs, speed/loudness -50..100 | `SeeduplexAudio`, input/output format models |
| ASR twopass, hotword/regex table IDs and names, inline hotwords/corrections | `SeeduplexExtension.asr`, reused typed StartSession fields |
| Location, QA/timestamps, audit, search, music, loudness normalization, exit intent | `SeeduplexExtension.Dialog`; native search types custom/global override legacy defaults |
| Parenthesis filtering, eight dialects, five AIGC metadata fields | `SeeduplexExtension.TTS`; native parenthesis field added |
| Close, force endpoint, mute/unmute, native cancellation | `SeeduplexControlRequest` |
| Base64 audio append | `SeeduplexAudioRequest` |
| Greeting, streaming speech replacement append/commit | `SeeduplexSpeechRequest` |
| Context create/update/retrieve/delete | Four conversation request models with typed references, updates and text content |
| Every call in a completed FC batch, original call ID, arguments string | `SeeduplexFunctionCall`, `SeeduplexEvent.items` |
| Aggregated completed tool results | `SeeduplexConversationCreateRequest`, `SeeduplexToolResult`: role=tool, content[].type=input_text, content[].text |
| All 20 documented downstream event names | `SeeduplexServerEventType`; forward-compatible `SeeduplexEvent.type` |
| Session acknowledgements, ASR correlation/deltas/completion/failure, text/audio correlation and tts_type, context acknowledgements, cancellation, exit code | Typed fields and nested models on `SeeduplexEvent` |
| Top-level error status/message and nested transcription error type/code/message/param | `SeeduplexEvent`, `SeeduplexError` |
| response.done usage | Retained opaque dictionary; native docs do not specify counters |

`encode_seeduplex_request` validates all 15 documented upstream event names and
encodes one JSON text frame. It serializes only supplied settings, preserving
partial updates and explicit `tools: []`; it does not inject legacy defaults.
All official API JSON examples are parsed from the tracked snapshot and checked
for exact request/response round trips. Additional tests cover extension fields,
event inventory, unknown events, constraints, controls and rejected OpenAI-only
request types.

## Documentation inconsistencies and explicit boundaries

- The guide mentions an `output` result field once, but its tool-flow prose and
  API examples require `role: tool` with `content[].text`. The SDK uses that
  native shape. It does not implement `function_call_output` or `response.create`.
- The guide describes session-ID restoration through update; the API also
  documents ID on create. Both session request types support it.
- Several field labels say string for objects (`location`, dialog `extra`,
  AIGC metadata, ASR `context`); their child fields, concrete examples and the
  guide's StartSession compatibility rule specify structured objects. Hotword
  prose says `words`, while the example and existing SDK use `word`.
- The guide also permits legacy `extension.tts.audio_config`; typed StartSession
  configuration is retained there. Native `session.audio` is separately modeled:
  native `pcm` is PCM16, not the legacy extension's float32 `pcm`.
- Native usage counters are unspecified. Do not invent OpenAI counters or claim
  the legacy binary usage shape is a documented native contract.
- `2534847` is explicitly an old-console authentication reference, not a native
  schema source. Search API console/product links describe external services;
  this SDK models only the native search configuration. No credential/console
  documentation expansion was needed. The already tracked voice page covers
  voices; speaker IDs stay open for clones and future voices.
- Official Go/Python/Web demo ZIPs and diagrams are linked in the snapshot.
  They are supplemental examples on volccdn, not silently imported as schema
  authority or executed. The documented API examples supply the tested payloads.
- Snapshot refresh now renders the provider's rich-text zone graph, including
  folded fields, table cells and detached example panels. Missing/cyclic or
  unvisited non-panel zones fail before replacing existing files. Only rendered
  `Result.Content`, never the raw API response/editor JSON, is tracked.

Transport pacing (20 ms/640 bytes for PCM16), keepalive/mute, acknowledgements,
reconnects, QA ordering/40-message initialization limits, timestamps, batching,
tool execution limits, deduplication and safe error handling remain consumer
responsibilities. The SDK does not execute tools, open sockets, fetch credentials
or claim provider-live acceptance from offline schema tests.

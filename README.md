# Volcengine Audio SDK

Python SDK for Volcengine (ByteDance) Audio Services, providing comprehensive support for Text-to-Speech (TTS), Speech-to-Text (STT), and Realtime Dialogue capabilities.

[中文 README](README.zh-CN.md) | [Package Maintenance Guide](AGENTS.md)

## Features

- **Speech-to-Text (STT)**: Convert audio to text using Volcengine's ASR services (V2 and V3 APIs)
- **Text-to-Speech (TTS)**: Synthesize natural-sounding speech from text with various voice types
- **Realtime Dialogue**: Bidirectional streaming for interactive voice conversations
- **Protocol Support**: Low-level protocol utilities for custom implementations
- **Type Safety**: Full Pydantic model validation for all requests and responses

## Documentation Sync

### Last SDK/doc sync

* Local sync date: `2026-03-26`
* Package maintenance guide: [`AGENTS.md`](AGENTS.md)
* Snapshot manifest: [`doc_sync/volcengine/manifest.json`](doc_sync/volcengine/manifest.json)
* Refresh command: `uvx --with playwright python packages/volcengine-audio/scripts/sync_volcengine_docs.py`
* These Volcengine docs are JS-rendered. The sync script opens the public docs pages with Playwright, captures the backing `api/doc/getDocDetail` JSON response, and writes cleaned `Result.Content` markdown snapshots to `doc_sync/volcengine/`.
* The tracked snapshot files store only doc content text with span tags removed, while source metadata stays in `manifest.json`.
* The snapshot files are tracked in git for future diffs, but they are not packed into wheels because this package only ships `src/volcengine_audio`.

### Tracked upstream sources

* Realtime dialogue: `2026-03-13T08:41:28Z` - <https://www.volcengine.com/docs/6561/1594356?lang=zh>
* TTS WebSocket bidirectional V3: `2026-03-16T10:24:14Z` - <https://www.volcengine.com/docs/6561/1329505?lang=zh>
* TTS WebSocket unidirectional V3: `2026-03-16T10:21:49Z` - <https://www.volcengine.com/docs/6561/1719100?lang=zh>
* TTS HTTP Chunked/SSE V3: `2026-03-17T09:29:21Z` - <https://www.volcengine.com/docs/6561/1598757?lang=zh>
* STT streaming bigmodel: `2026-03-24T13:15:18Z` - <https://www.volcengine.com/docs/6561/1354869?lang=zh>

### Sync checklist

1. Refresh the tracked content snapshots with `uvx --with playwright python packages/volcengine-audio/scripts/sync_volcengine_docs.py`.
2. Diff `doc_sync/volcengine/*.md` to see which request fields, enums, events, or examples changed upstream.
3. Update `src/volcengine_audio/` schemas and helper functions as needed.
4. Update or add tests under `tests/`.
5. Update the local sync date in this README and in [`README.zh-CN.md`](README.zh-CN.md).

## Installation

### Install from PyPI

```bash
# From PyPI (when published)
pip install volcengine-audio
```

### Install from source

```bash
git clone https://github.com/aiyou178/volcengine-audio.git
cd volcengine-audio
pip install -e .
```

## Quick Start

### Speech-to-Text (STT)

```python
from volcengine_audio import (
    VolcengineAsrRequestV3,
    VolcengineAsrFunctionsV3,
    STTAudioFormatV3,
)

# Create ASR request
asr_request = VolcengineAsrRequestV3(
    audio=VolcengineAsrRequestV3.Audio(
        format=STTAudioFormatV3.wav,
        rate=16000,
    ),
    request=VolcengineAsrRequestV3.Request(
        model_name="bigmodel",
        enable_itn=True,
        enable_punc=True,
    ),
)

# Generate request payload
request_params = asr_request.model_dump(exclude_none=True)
full_request = VolcengineAsrFunctionsV3.generate_asr_full_client_request(
    sequence=1,
    request_params=request_params,
    compression=True,
)

# Send audio chunks
audio_request = VolcengineAsrFunctionsV3.generate_asr_audio_only_request(
    sequence=2,
    audio=audio_chunk,
    compress=True,
)

# Parse response
response_data = VolcengineAsrFunctionsV3.parse_response(server_response)
print(response_data['message'])
```

### Text-to-Speech (TTS)

```python
from volcengine_audio import (
    VolcengineTTSBidirectionRequest,
    VolcengineTTSFunctions,
    TTSBigmodelResourceType,
    TTSAudioFormat,
    EventSend,
)

# Create TTS request
tts_request = VolcengineTTSBidirectionRequest(
    event=EventSend.StartSession,
    req_params=VolcengineTTSBidirectionRequest.ReqParams(
        text="Hello, this is a test.",
        speaker="zh_female_vv_jupiter_bigtts",
        model=TTSBigmodelResourceType.seed_tts_2_0,
        audio_params=VolcengineTTSBidirectionRequest.ReqParams.AudioParams(
            format=TTSAudioFormat.mp3,
            sample_rate=24000,
        ),
    ),
)

# Create connection
connection_payload = VolcengineTTSFunctions.start_connection_payload()

# Start session
session_payload = VolcengineTTSFunctions.start_session_payload(
    session_id="unique-session-id",
    req_params=tts_request.req_params.model_dump(exclude_none=True),
)

# Parse response
event, session_id, payload = VolcengineTTSFunctions.extract_response_payload(server_response)
```

### Realtime Dialogue

```python
from volcengine_audio import (
    RealtimeDialogueConfig,
    RealtimeDialogueFunctions,
    ChatTTSTextRequest,
)

# Configure dialogue session
config = RealtimeDialogueConfig(
    dialog=RealtimeDialogueConfig.DialogConfig(
        bot_name="AI Assistant",
        system_role="You are a helpful assistant.",
        speaking_style="Professional and friendly.",
    ),
    tts=RealtimeDialogueConfig.TTSConfig(
        speaker=RealtimeDialogueConfig.TTSConfig.Speaker.zh_female_vv_jupiter_bigtts,
    ),
)

# Start connection
connection = RealtimeDialogueFunctions.start_connection_payload()

# Start session
session = RealtimeDialogueFunctions.start_session_payload(
    session_id="session-123",
    config=config,
)

# Send audio for recognition
audio_payload = RealtimeDialogueFunctions.task_request_payload(
    session_id="session-123",
    audio_data=audio_bytes,
)

# Request TTS for text
tts_payload = RealtimeDialogueFunctions.chat_tts_text_payload(
    session_id="session-123",
    tts_request=ChatTTSTextRequest(
        start=True,
        content="Hello!",
        end=True,
    ),
)

# Finish session
finish = RealtimeDialogueFunctions.finish_session_payload("session-123")
```

## API Reference

### Modules

#### `volcengine_audio.protocol`

Core protocol definitions and utilities.

**Classes:**
- `ProtocolVersion`: Protocol version enumeration (V1)
- `MessageType`: Message types for bidirectional communication
- `EventSend`: Events sent from client to server
- `EventReceive`: Events received from server
- `SerializationMethod`: Payload serialization methods (JSON, RAW, PROTOBUF)
- `CompressionMethod`: Payload compression methods (NONE, GZIP)

**Constants:**
- `HOST`: `'openspeech.bytedance.com'` - Volcengine audio service host

**Functions:**
- `generate_header()`: Generate protocol header for requests
- `generate_before_payload()`: Generate sequence number before payload

#### `volcengine_audio.stt`

Speech-to-Text (ASR) models and utilities.

**Request Models:**
- `VolcengineAsrRequestV3`: ASR V3 API request
- `VolcengineAsrRequestV2`: ASR V2 API request

**Response Models:**
- `AsrFullServerResponseV2`: Full server response for V2
- `ListenBidirectionPackage`: Bidirectional listening package

**Enums:**
- `STTResource`: STT resource types for billing
- `STTAudioFormatV3`: Audio formats (pcm, wav, mp3, ogg)
- `STTResultType`: Result types (full, single)
- `STTBigmodelNoStreamLanguage`: Supported languages for bigmodel

**Helper Classes:**
- `VolcengineAsrFunctionsV3`: V3 API helper functions
  - `generate_asr_full_client_request()`: Generate full client request
  - `generate_asr_audio_only_request()`: Generate audio-only request
  - `parse_response()`: Parse server response
- `VolcengineAsrFunctionsV2`: V2 API helper functions
  - `full_client_request()`: Generate full client request
  - `audio_only_request()`: Generate audio-only request

#### `volcengine_audio.tts`

Text-to-Speech models and utilities.

**Request Models:**
- `VolcengineTTSRequest`: Standard TTS request
- `VolcengineTTSBidirectionRequest`: Bidirectional TTS request
- `TTSReqParams`: TTS request parameters with audio settings

**Response Models:**
- `TTSSentenceStartResponse`: Sentence start notification
- `TTSSentenceEndResponse`: Sentence end notification
- `TTSEndResponse`: TTS ended notification

**Enums:**
- `TTSBigmodelResourceType`: TTS model types (seed-tts-1.0, seed-tts-2.0, etc.)
- `TTSAudioFormat`: Audio formats (wav, pcm, mp3, ogg_opus)

**Helper Classes:**
- `VolcengineTTSFunctions`: TTS API helper functions
  - `start_connection_payload()`: Start connection
  - `start_session_payload()`: Start TTS session
  - `finish_session_payload()`: Finish TTS session
  - `extract_response_payload()`: Extract and parse response
  - `calculate_payload()`: Calculate request payload

#### `volcengine_audio.realtime`

Realtime dialogue (combined TTS+STT) models and utilities.

**Configuration:**
- `RealtimeDialogueConfig`: Complete dialogue session configuration
  - `DialogConfig`: Bot persona, speaking style, location
  - `TTSConfig`: Voice type and audio settings
  - `Asr`: ASR-specific settings

**Request Models:**
- `SayHelloRequest`: Greeting message
- `ChatTTSTextRequest`: Text to synthesize with TTS
- `ChatTextQueryRequest`: Text query for dialogue

**Response Models:**
- `ASRInfoResponse`: ASR task info (first word detection)
- `ASRResponseModel`: ASR recognition result
- `ASREndedResponse`: ASR ended notification
- `ChatResponseModel`: Chat response
- `SessionStartedResponse`: Session started
- `SessionFailedResponse`: Session failed

**Helper Classes:**
- `RealtimeDialogueFunctions`: Realtime dialogue API helpers
  - `start_connection_payload()`: Start connection
  - `start_session_payload()`: Start dialogue session
  - `task_request_payload()`: Send audio for recognition
  - `say_hello_payload()`: Send greeting
  - `chat_tts_text_payload()`: Request TTS for text
  - `chat_text_query_payload()`: Send text query
  - `finish_session_payload()`: Finish session

## Protocol Details

### Message Structure

All messages follow a standard protocol structure:

```
[Header 4 bytes][Optional Fields][Payload Size 4 bytes][Payload]
```

#### Header Format

```
Byte 0: [protocol_version:4 bits][header_size:4 bits]
Byte 1: [message_type:4 bits][message_type_specific_flags:4 bits]
Byte 2: [serialization_method:4 bits][compression:4 bits]
Byte 3: [reserved:8 bits]
```

#### Protocol Versions

- **V1 (0b0001)**: Current protocol version

#### Message Types

**Client → Server:**
- `FULL_CLIENT_REQUEST (0b0001)`: Full request with metadata
- `AUDIO_ONLY_REQUEST (0b0010)`: Audio-only request

**Server → Client:**
- `FULL_SERVER_RESPONSE (0b1001)`: Full response with metadata
- `AUDIO_ONLY_RESPONSE (0b1011)`: Audio-only response
- `ERROR_INFORMATION (0b1111)`: Error information

#### Serialization Methods

- `RAW (0b0000)`: Raw binary data
- `JSON (0b0001)`: JSON-encoded payload
- `PROTOBUF (0b0010)`: Protocol Buffers
- `THRIFT (0b0011)`: Apache Thrift

#### Compression Methods

- `NONE (0b0000)`: No compression
- `GZIP (0b0001)`: GZIP compression

### Event Flow

#### TTS Bidirectional Flow

```
Client                          Server
  |                               |
  |-- StartConnection ----------->|
  |<---------- ConnectionStarted--|
  |                               |
  |-- StartSession -------------->|
  |<------------ SessionStarted---|
  |                               |
  |-- TaskRequest (text) -------->|
  |<--------- TTSSentenceStart----|
  |<--------- TTSResponse (audio)-|
  |<----------- TTSSentenceEnd----|
  |                               |
  |-- FinishSession ------------->|
  |<---------- SessionFinished----|
  |                               |
  |-- FinishConnection ---------->|
  |<-------- ConnectionFinished---|
```

#### STT Streaming Flow

```
Client                          Server
  |                               |
  |-- FullClientRequest --------->|
  |                               |
  |-- AudioOnlyRequest (chunk1)-->|
  |<------------- FullResponse----|
  |                               |
  |-- AudioOnlyRequest (chunk2)-->|
  |<------------- FullResponse----|
  |                               |
  |-- AudioOnlyRequest (last) --->|
  |<------------- FullResponse----|
```

#### Realtime Dialogue Flow

```
Client                          Server
  |                               |
  |-- StartConnection ----------->|
  |<---------- ConnectionStarted--|
  |                               |
  |-- StartSession (config) ----->|
  |<------------ SessionStarted---|
  |                               |
  |-- TaskRequest (audio) ------->|
  |<-------------- ASRInfo--------|
  |<------------ ASRResponse------|
  |<-------------- ASREnded-------|
  |                               |
  |<----------- ChatResponse------|
  |<------- TTSSentenceStart------|
  |<--------- TTSResponse (audio)-|
  |<--------- TTSSentenceEnd------|
  |<------------- ChatEnded-------|
  |                               |
  |-- FinishSession ------------->|
  |<---------- SessionFinished----|
```

## Advanced Usage

### Custom Context and Hot Words (STT)

```python
from volcengine_audio import VolcengineAsrRequestV3

request = VolcengineAsrRequestV3(
    request=VolcengineAsrRequestV3.Request(
        corpus=VolcengineAsrRequestV3.Request.Corpus(
            context=VolcengineAsrRequestV3.Request.Corpus.Context(
                hotwords=[
                    {"word": "Volcengine"},
                    {"word": "ByteDance"},
                ],
                context_type="dialog_ctx",
            ),
        ),
        sensitive_words_filter=VolcengineAsrRequestV3.Request.SensitiveWordsFilter(
            system_reserved_filter=True,
            filter_with_signed=["badword1", "badword2"],
        ),
    ),
)
```

### Mixed Voice (TTS)

```python
from volcengine_audio import VolcengineTTSBidirectionRequest

request = VolcengineTTSBidirectionRequest.ReqParams(
    text="Hello",
    speaker="custom_mix",
    mix_speaker=VolcengineTTSBidirectionRequest.ReqParams.MixSpeaker(
        speakers=[
            {
                "source_speaker": "zh_female_vv_jupiter_bigtts",
                "mix_factor": 0.6,
            },
            {
                "source_speaker": "zh_male_yunzhou_jupiter_bigtts",
                "mix_factor": 0.4,
            },
        ],
    ),
)
```

### Emotion Control (TTS)

```python
from volcengine_audio import TTSReqParams

audio_params = TTSReqParams.AudioParams(
    emotion="happy",
    emotion_scale=5,  # Max intensity
    speech_rate=50,  # 1.5x speed
    loudness_rate=20,  # 1.2x volume
    pitch=2,  # Slightly higher pitch
)
```

### Web Search Integration (Realtime Dialogue)

```python
from volcengine_audio import RealtimeDialogueConfig

config = RealtimeDialogueConfig(
    dialog=RealtimeDialogueConfig.DialogConfig(
        extra=RealtimeDialogueConfig.DialogConfig.Extra(
            enable_volc_websearch=True,
            volc_websearch_type="web_summary",
            volc_websearch_api_key="your-api-key",
            volc_websearch_result_count=5,
        ),
    ),
)
```

## Error Handling

```python
from volcengine_audio import EventReceive

event, session_id, payload = VolcengineTTSFunctions.extract_response_payload(response)

if event == EventReceive.SessionFailed:
    print(f"Session failed: {payload.get('error')}")
elif event == EventReceive.ConnectionFailed:
    print(f"Connection failed: {payload.get('error')}")
elif event == EventReceive.SERVER_PROCESSING_ERROR:
    print("Server processing error")
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

This package uses Ruff for linting and formatting:

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## License

MIT

# Volcengine Audio SDK

Python SDK for Volcengine (ByteDance) Audio Services, providing comprehensive support for Text-to-Speech (TTS), Speech-to-Text (STT), and Realtime Dialogue capabilities.

[中文 README](README.zh-CN.md) | [Package Maintenance Guide](AGENTS.md)

## Features

- **Speech-to-Text (STT)**: Convert audio to text using Volcengine's ASR services (V2 and V3 APIs)
- **Text-to-Speech (TTS)**: Synthesize natural-sounding speech from text with various voice types
- **Realtime Dialogue**: Legacy binary S2S and native Seeduplex JSON models
- **Protocol Support**: Low-level protocol utilities for custom implementations
- **Type Safety**: Pydantic models for documented request and response fields

## Documentation

Documentation checked: `2026-09-13`.

Version 0.2.6 adds native Seeduplex session, audio, speech, context and tool-call
schemas. See the [release notes](CHANGELOG.md) and
[schema coverage](doc/seeduplex-schema-audit.md) for details and documented
protocol ambiguities. Authentication, WebSocket transport and tool execution
remain the caller's responsibility.

### Current Tracked Sources

- Native Seeduplex API: `2026-09-11T06:21:28Z` - <https://www.volcengine.com/docs/6561/2549778?lang=zh>
- Native Seeduplex integration guide: `2026-09-04T09:02:13Z` - <https://www.volcengine.com/docs/6561/2549732?lang=zh>
- Realtime dialogue: `2026-08-20T06:52:26Z` - <https://www.volcengine.com/docs/6561/1594356?lang=zh>
- TTS WebSocket bidirectional V3: `2026-05-25T08:51:30Z` - <https://www.volcengine.com/docs/6561/1329505?lang=zh>
- TTS WebSocket unidirectional V3: `2026-05-25T08:49:18Z` - <https://www.volcengine.com/docs/6561/1719100?lang=zh>
- TTS HTTP Chunked/SSE V3: `2026-05-25T09:03:36Z` - <https://www.volcengine.com/docs/6561/1598757?lang=zh>
- STT streaming bigmodel: `2026-08-06T09:40:25Z` - <https://www.volcengine.com/docs/6561/1354869?lang=zh>
- TTS voice list: `2026-08-31T05:45:33Z` - <https://www.volcengine.com/docs/6561/1257544?lang=zh>

## Installation

Requires Python 3.11 or newer.

### Install from PyPI

```bash
pip install volcengine-audio
```

### Install from source

```bash
git clone https://github.com/aiyou178/volcengine-audio.git
cd volcengine-audio
pip install -e .
```

## Development

```bash
# from this repository root
uv sync --extra dev
uv run pytest tests
uv run ruff check src tests
uv run ruff format src tests
```

This package is a standalone SDK. Keep source under `src/volcengine_audio` and
tests under `tests`.

## Quick Start

### Native Seeduplex

```python
from volcengine_audio import SeeduplexEvent, encode_seeduplex_request

request_frame = encode_seeduplex_request({
    'type': 'session.create',
    'session': {
        'model': '1.2.6.1',
        'instructions': 'Answer briefly.',
        'audio': {
            'input': {'format': {'type': 'pcm', 'rate': 16000}},
            'output': {'format': {'type': 'pcm', 'rate': 24000}},
        },
        'tools': [],
    },
})

# Send request_frame as a WebSocket text frame and parse the server reply.
event = SeeduplexEvent.model_validate_json(
    '{"type":"session.created","session":{"id":"example-session"}}'
)
print(event.session.id)
```

The encoder preserves supplied fields, including partial session updates and
`tools: []` to clear the tool set. Send mono PCM16 input in paced 20 ms packets
(640 bytes at 16 kHz). Use native mute/unmute events when stopping/resuming input.
Tool results use `conversation.item.create` with `role: "tool"`, the original
`call_id` and `content: [{"type": "input_text", "text": completed_result}]`.
Aggregate every result in the received batch before returning it.

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
    TTSBigmodelModelType,
    TTSAudioFormat,
    EventSend,
)

# Create TTS request
tts_request = VolcengineTTSBidirectionRequest(
    event=EventSend.StartSession,
    req_params=VolcengineTTSBidirectionRequest.ReqParams(
        text="Hello, this is a test.",
        speaker="zh_female_vv_jupiter_bigtts",
        model=TTSBigmodelModelType.seed_tts_1_1,
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

**Package Metadata:**
- `__version__`: Installed package version

**Classes:**
- `ProtocolVersion`: Protocol version enumeration (V1)
- `HeaderSize`: Protocol header size enumeration
- `MessageType`: Message types for bidirectional communication
- `MessageTypeSpecificFlag`: Message flags for sequencing and event framing
- `AsrMessageType`: ASR-specific message types
- `AsrMessageTypeSpecificFlag`: ASR-specific message flags
- `EventSend`: Events sent from client to server
- `EventReceive`: Events received from server
- `SerializationMethod`: Payload serialization methods (JSON, RAW, PROTOBUF)
- `CompressionMethod`: Payload compression methods (NONE, GZIP)
- `AudioCodec`: Audio codec values used by STT request schemas

**Constants:**
- `HOST`: `'openspeech.bytedance.com'` - Volcengine audio service host

**Functions:**
- `generate_header()`: Generate protocol header for requests
- `generate_before_payload()`: Generate sequence number before payload

#### `volcengine_audio.stt`

Speech-to-Text (ASR) models and utilities.

**Request Models:**
- `VolcengineAsrRequestV3`: ASR V3 API request
  - `request.enable_auto_lang`: Auto-detect language for non-streaming STT
- `VolcengineAsrRequestV2`: ASR V2 API request

**Response Models:**
- `AsrFullServerResponseV2`: Full server response for V2
- `ListenBidirectionPackage`: Bidirectional listening package

**Enums:**
- `STTResource`: STT resource types for billing
- `STTAudioFormatV3`: Audio formats (pcm, wav, mp3, ogg)
- `AudioFormatV2`: Audio formats for the V2 request schema
- `STTResultType`: Result types (full, single)
- `STTBigmodelNoStreamLanguage`: Supported languages for bigmodel

**Helper Classes:**
- `VolcengineAsrFunctionsV3`: V3 API helper functions
  - `generate_asr_header()`: Generate V3 ASR request headers
  - `generate_asr_before_payload()`: Generate V3 ASR sequence metadata
  - `generate_asr_full_client_request()`: Generate full client request
  - `generate_asr_audio_only_request()`: Generate audio-only request
  - `parse_request()`: Parse generated request bytes for inspection
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
- `TTSSentenceEndPayload`: Sentence-end payload typed dict
- `TTSSubtitlePayload`: Subtitle payload typed dict
- `TTSTimedWord`: Timed word typed dict

**Enums:**
- `TTSBigmodelResourceType`: TTS resource IDs (`seed-tts-1.0`, `seed-tts-2.0`, etc.)
- `TTSBigmodelModelType`: Optional `req_params.model` values (`seed-tts-1.1`, `seed-tts-2.0-standard`, etc.)
- `TTSAudioFormat`: Audio formats (wav, pcm, mp3, ogg_opus)
- `OperationEnum`: HTTP TTS operation values

**Configuration Models:**
- `AppConfig`: HTTP TTS app credentials and cluster
- `UserConfig`: User identifier for request metadata
- `AudioConfig`: HTTP TTS audio options
- `RequestConfig`: HTTP TTS request options

**Helper Classes:**
- `VolcengineTTSFunctions`: TTS API helper functions
  - `prepare_request()`: Prepare HTTP TTS request payload
  - `task_request_payload()`: Generate bidirectional task payload
  - `start_connection_payload()`: Start connection
  - `start_session_payload()`: Start TTS session
  - `cancel_session_payload()`: Cancel TTS session
  - `finish_session_payload()`: Finish TTS session
  - `finish_connection_payload()`: Finish connection
  - `extract_response_payload()`: Extract and parse response
  - `calculate_payload()`: Calculate request payload
- `validate_tts_resource_model_mapping()`: Validate compatible resource/model
  pairs for TTS 1.x and 2.x resources

#### `volcengine_audio.realtime`

Realtime dialogue (combined TTS+STT) models and utilities.

**Configuration:**
- `RealtimeDialogueConfig`: Complete dialogue session configuration
  - `DialogConfig`: Bot persona, speaking style, location
    - Supports `web_global_api` as the global web-search source
  - `TTSConfig`: Voice type, audio settings, and `tts_2_0_model` wire alias
    `tts_2.0_model`
    - Supports `dongbei`, `sichuan`, `shaanxi`, `yue`, `beijing`, `henan`,
      `tianjin`, and `shanghai` explicit dialect values
  - `Asr`: ASR-specific settings

**Request Models:**
- `SayHelloRequest`: Greeting message
- `UpdateConfigRequest`: Runtime TTS/dialog config update
- `ChatTTSTextRequest`: Text to synthesize with TTS
- `ChatTextQueryRequest`: Text query for dialogue
- `ChatRAGTextRequest`: External RAG text query
- `ConversationCreateRequest`, `ConversationUpdateRequest`, `ConversationRetrieveRequest`, `ConversationTruncateRequest`, `ConversationDeleteRequest`: Context management requests

**Response Models:**
- `ASRInfoResponse`: ASR task info (first word detection)
- `ASRResponseModel`: ASR recognition result
- `ASREndedResponse`: ASR ended notification
- `RealtimeTTSSentenceStartResponse`, `RealtimeTTSSentenceEndResponse`:
  Realtime synthesized-sentence lifecycle payloads
- `ChatResponseModel`: Chat response
- `ChatTextQueryConfirmedResponse`: Text query acknowledgement
- `ConversationCreatedResponse`, `ConversationUpdatedResponse`, `ConversationRetrievedResponse`, `ConversationTruncatedResponse`, `ConversationDeletedResponse`: Context management acknowledgements
- `ConfigUpdatedResponse`: Runtime config update acknowledgement
- `ConnectionFailedResponse`: Connection-level failure payload
- `SessionStartedResponse`: Session started
- `SessionFailedResponse`: Session failed
- `RealtimeDialogueErrorResponse`: Generic realtime error payload
- `RealtimeDialogueUsage`: Usage typed dict

**Helper Classes:**
- `RealtimeDialogueFunctions`: Realtime dialogue API helpers
  - `start_connection_payload()`: Start connection
  - `finish_connection_payload()`: Finish connection
  - `start_session_payload()`: Start dialogue session
  - `task_request_payload()`: Send audio for recognition
  - `update_config_payload()`: Update runtime TTS/dialog config
  - `say_hello_payload()`: Send greeting
  - `end_asr_payload()`: Signal end of audio in push-to-talk mode
  - `chat_tts_text_payload()`: Request TTS for text
  - `chat_text_query_payload()`: Send text query
  - `chat_rag_text_payload()`: Send external RAG text
  - `conversation_*_payload()`: Manage dialogue context
  - `client_interrupt_payload()`: Interrupt server response in push-to-talk mode
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
from volcengine_audio import EventReceive, VolcengineTTSFunctions

event, session_id, payload = VolcengineTTSFunctions.extract_response_payload(
    response
)

if event == EventReceive.SessionFailed:
    print(f"Session failed: {payload.get('error')}")
elif event == EventReceive.ConnectionFailed:
    print(f"Connection failed: {payload.get('error')}")
elif event == EventReceive.SERVER_PROCESSING_ERROR:
    print("Server processing error")
```

## License

MIT

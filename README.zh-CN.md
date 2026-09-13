# Volcengine Audio SDK

用于火山引擎（ByteDance）语音服务的 Python SDK，覆盖语音合成
（TTS）、语音识别（STT）和端到端实时语音对话能力。

[English README](README.md) | [维护说明](AGENTS.md)

## 功能特性

* **语音识别（STT）**：支持火山引擎 ASR V2 / V3 请求模型与协议辅助函数
* **语音合成（TTS）**：支持多种音色、双向/单向流式和附加参数
* **实时语音对话**：提供旧版二进制 S2S 和原生 Seeduplex JSON 模型
* **底层协议支持**：提供二进制协议头与事件工具函数
* **类型安全**：请求与响应模型基于 Pydantic 校验

## 文档

文档核对日期：`2026-09-13`。

0.2.6 新增原生 Seeduplex 会话、音频、语音合成、上下文和工具调用模型。
功能变更与协议说明见[版本记录](CHANGELOG.md)和
[字段覆盖记录](doc/seeduplex-schema-audit.md)。鉴权、WebSocket 传输和工具执行
由调用方管理。

### 当前跟踪的上游文档

* 原生 Seeduplex API：`2026-09-11T06:21:28Z` - <https://www.volcengine.com/docs/6561/2549778?lang=zh>
* 原生 Seeduplex 接入必读：`2026-09-04T09:02:13Z` - <https://www.volcengine.com/docs/6561/2549732?lang=zh>
* 实时对话：`2026-08-20T06:52:26Z` - <https://www.volcengine.com/docs/6561/1594356?lang=zh>
* TTS WebSocket 双向流式 V3：`2026-05-25T08:51:30Z` - <https://www.volcengine.com/docs/6561/1329505?lang=zh>
* TTS WebSocket 单向流式 V3：`2026-05-25T08:49:18Z` - <https://www.volcengine.com/docs/6561/1719100?lang=zh>
* TTS HTTP Chunked/SSE V3：`2026-05-25T09:03:36Z` - <https://www.volcengine.com/docs/6561/1598757?lang=zh>
* STT 大模型流式识别：`2026-08-06T09:40:25Z` - <https://www.volcengine.com/docs/6561/1354869?lang=zh>
* TTS 音色列表：`2026-08-31T05:45:33Z` - <https://www.volcengine.com/docs/6561/1257544?lang=zh>

## 安装

要求 Python 3.11 或更高版本。

### 从 PyPI 安装

```bash
pip install volcengine-audio
```

### 从源码安装

```bash
git clone https://github.com/aiyou178/volcengine-audio.git
cd volcengine-audio
pip install -e .
```

## 开发

```bash
# 从本仓库根目录运行
uv sync --extra dev
uv run pytest tests
uv run ruff check src tests
uv run ruff format src tests
```

该仓库作为独立 SDK 发布。代码放在 `src/volcengine_audio`，测试放在
`tests`。

## 快速开始

### 原生 Seeduplex

```python
from volcengine_audio import SeeduplexEvent, encode_seeduplex_request

request_frame = encode_seeduplex_request({
    'type': 'session.create',
    'session': {
        'model': '1.2.6.1',
        'instructions': '请简短回答。',
        'audio': {
            'input': {'format': {'type': 'pcm', 'rate': 16000}},
            'output': {'format': {'type': 'pcm', 'rate': 24000}},
        },
        'tools': [],
    },
})

# 将 request_frame 作为 WebSocket 文本帧发送，随后解析服务端响应。
event = SeeduplexEvent.model_validate_json(
    '{"type":"session.created","session":{"id":"example-session"}}'
)
print(event.session.id)
```

编码器保留显式传入的字段，支持会话部分更新，以及通过 `tools: []` 清空工具。
单声道 PCM16 输入按实时节奏发送 20 ms 分片（16 kHz 时每片 640 字节）；
暂停或恢复输入时发送原生静音或取消静音事件。
工具结果通过 `conversation.item.create` 回传，条目携带 `role: "tool"`、原始
`call_id` 和 `content: [{"type": "input_text", "text": completed_result}]`。
同批调用的全部结果应聚合后一次性回传。

### 语音识别（STT）

```python
from volcengine_audio import (
    VolcengineAsrRequestV3,
    VolcengineAsrFunctionsV3,
    STTAudioFormatV3,
)

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

request_params = asr_request.model_dump(exclude_none=True)
full_request = VolcengineAsrFunctionsV3.generate_asr_full_client_request(
    sequence=1,
    request_params=request_params,
    compression=True,
)

audio_request = VolcengineAsrFunctionsV3.generate_asr_audio_only_request(
    sequence=2,
    audio=audio_chunk,
    compress=True,
)

response_data = VolcengineAsrFunctionsV3.parse_response(server_response)
print(response_data['message'])
```

### 语音合成（TTS）

```python
from volcengine_audio import (
    VolcengineTTSBidirectionRequest,
    VolcengineTTSFunctions,
    TTSBigmodelModelType,
    TTSAudioFormat,
    EventSend,
)

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

connection_payload = VolcengineTTSFunctions.start_connection_payload()

session_payload = VolcengineTTSFunctions.start_session_payload(
    session_id="unique-session-id",
    req_params=tts_request.req_params.model_dump(exclude_none=True),
)

event, session_id, payload = VolcengineTTSFunctions.extract_response_payload(
    server_response
)
```

### 实时语音对话

```python
from volcengine_audio import (
    RealtimeDialogueConfig,
    RealtimeDialogueFunctions,
    ChatTTSTextRequest,
)

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

connection = RealtimeDialogueFunctions.start_connection_payload()

session = RealtimeDialogueFunctions.start_session_payload(
    session_id="session-123",
    config=config,
)

audio_payload = RealtimeDialogueFunctions.task_request_payload(
    session_id="session-123",
    audio_data=audio_bytes,
)

tts_payload = RealtimeDialogueFunctions.chat_tts_text_payload(
    session_id="session-123",
    tts_request=ChatTTSTextRequest(
        start=True,
        content="Hello!",
        end=True,
    ),
)

finish = RealtimeDialogueFunctions.finish_session_payload("session-123")
```

## 模块概览

* `volcengine_audio.protocol`：协议头、事件、序列化与压缩定义
* `volcengine_audio.stt`：STT 请求/响应模型和辅助函数
* `volcengine_audio.tts`：TTS 请求/响应模型和辅助函数
* `volcengine_audio.realtime`：实时语音对话配置、事件模型和辅助函数

更完整的符号清单和协议说明可参考英文版 [`README.md`](README.md)
中的 API Reference，或者直接查看 `src/volcengine_audio/` 源码。

## 许可证

MIT

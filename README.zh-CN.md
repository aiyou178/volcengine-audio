# Volcengine Audio SDK

用于火山引擎（ByteDance）语音服务的 Python SDK，覆盖语音合成
（TTS）、语音识别（STT）和端到端实时语音对话能力。

[English README](README.md) | [维护说明](AGENTS.md)

## 功能特性

* **语音识别（STT）**：支持火山引擎 ASR V2 / V3 请求模型与协议辅助函数
* **语音合成（TTS）**：支持多种音色、双向/单向流式和附加参数
* **实时语音对话**：支持语音到语音实时交互、上下文和联网配置
* **底层协议支持**：提供二进制协议头与事件工具函数
* **类型安全**：请求与响应模型基于 Pydantic 校验

## 文档同步

### 最近一次 SDK/文档同步

* 本地同步日期：`2026-03-26`
* 维护说明：[`AGENTS.md`](AGENTS.md)
* 快照清单：[`doc_sync/volcengine/manifest.json`](doc_sync/volcengine/manifest.json)
* 刷新命令：`uvx --with playwright python packages/volcengine-audio/scripts/sync_volcengine_docs.py`
* Volcengine 文档页面是 JS 渲染的。同步脚本会通过 Playwright 打开公开页面，拦截其底层 `api/doc/getDocDetail` JSON 响应，并把清洗后的 `Result.Content` 文本快照写入 `doc_sync/volcengine/`。
* 跟踪文件只保存文档正文内容，并在写入前去掉 `<span>` 标签；更新时间、来源链接和哈希等元数据保存在 `manifest.json`。
* 这些快照文件会提交到仓库中，方便下次直接 `git diff` 查出字段变化；它们不在 wheel 中，因为当前构建只打包 `src/volcengine_audio`。

### 当前跟踪的上游文档

* 实时对话：`2026-03-13T08:41:28Z` - <https://www.volcengine.com/docs/6561/1594356?lang=zh>
* TTS WebSocket 双向流式 V3：`2026-03-16T10:24:14Z` - <https://www.volcengine.com/docs/6561/1329505?lang=zh>
* TTS WebSocket 单向流式 V3：`2026-03-16T10:21:49Z` - <https://www.volcengine.com/docs/6561/1719100?lang=zh>
* TTS HTTP Chunked/SSE V3：`2026-03-17T09:29:21Z` - <https://www.volcengine.com/docs/6561/1598757?lang=zh>
* STT 大模型流式识别：`2026-03-24T13:15:18Z` - <https://www.volcengine.com/docs/6561/1354869?lang=zh>

### 后续同步建议

1. 运行 `uvx --with playwright python packages/volcengine-audio/scripts/sync_volcengine_docs.py` 刷新正文快照。
2. 比较 `doc_sync/volcengine/*.md` 的 diff，优先检查新增字段、枚举值、事件 ID 和示例变化。
3. 按需更新 `src/volcengine_audio/` 下的 schema 和 helper。
4. 同步更新 `tests/`、`README.md` 和本文件。

## 安装

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

## 快速开始

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
    TTSBigmodelResourceType,
    TTSAudioFormat,
    EventSend,
)

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

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码检查

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## 许可证

MIT

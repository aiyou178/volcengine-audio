# 简介
豆包实时语音模型 3.0（Seeduplex）是一款全双工端到端语音大模型，支持低延迟、多模态、语音到语音（S2S）的实时对话能力。本协议采用标准化的 Realtime 事件语义与字段结构，通过 WebSocket 以纯 JSON 文本帧进行数据收发，旨在帮助客户端以最小改动、统一范式接入豆包模型

# 协议设计原则
核心设计理念：事件语义标准化，专有能力通过 extension 透传
- 标准化事件命名：上行事件包括 `session.create`、`input_audio_buffer.append` 、 `conversation.item.create` 、 `response.cancel `等，下行事件包括 `session.created` 、 `response.output_audio.delta` 、 `response.done` 等
- 结构化字段组织：`session` 对象内含 `audio.input` 、 `audio.output` 、`instructions` 、 `tools`等字段，层次清晰、便于扩展
- 专有能力通过 extension 透传：唱歌、联网搜索、克隆音色、热词、上下文初始化等模型专有能力，统一收敛至 `extension`（包含 `asr` 、 `tts` 、 `dialog`），其内部结构与原 端到端模型的`StartSessionPayload` 完全一致，存量配置可直接复用
- 纯 JSON 文本帧：所有事件均以 JSON 文本通过 WebSocket Text Message 收发，事件类型由`type`字段标识；音频数据以Base64编码内嵌于对应事件的 `audio` / `delta` 字段中

# 消息帧格式
协议采用纯 JSON 文本帧传输：每个事件均为一条 JSON 字符串，通过 WebSocket Text Message 收发，无需二进制封装。事件类型由顶层`type`字段标识
- 一帧一事件：每条 WebSocket Text Message 承载且仅承载一个完整事件 JSON
- type 路由：客户端与服务端均按顶层 type 字段（如 `session.create`、`response.output_audio.delta`）进行分发处理
- event_id（可选）：上行事件可在`event_id`字段携带客户端生成的幂等标识；服务端会在相关下行事件中回带，便于链路追踪与排障
- session 标识：会话建立后，服务端通过`session.created`下行返回`session.id`（即 `dialog.id`）；接续历史会话时，在`session.update`的 `session.id` 字段中回传
- 音频承载方式：音频不走独立的二进制通道，而是以 Base64 编码字符串的形式内嵌于 JSON 事件字段中

# 音频格式约束
- 输入音频：
- PCM/Opus（由服务端自动转为PCM）、单声道、16000Hz、int16、小端序
- 推荐按 20 ms 分包（16k /int16 格式下每包 640 字节）
- 音频字节经 Base64 编码后放入` audio` 字段
注意
- 音频分片建议以20 ms 为单位（16k /int16 格式下每包 640 字节），并严格按照实时音频流的节奏发送，发送速率偏离实际节奏（过快或过慢）都将触发服务端错误
- 模型依赖上行音频流保活。客户端关闭麦克风后若不再发送音频帧，须主动发送静音事件`input_audio_mute.commit`，恢复麦克风时发送取消静音事件`input_audio_unmute.commit`，否则服务端会因持续收不到音频输入触发超时，导致模型无响应
- 输出音频：
- 默认返回OGG-Opus格式
- 支持在`extension.tts.audio_config `配置输出音频格式，配置后可返回PCM（24000Hz，单声道，16bit 小端序）格式
- 音频数据以 Base64 编码在 `delta `字段下行

# 最简交互示例图

![Diagram](https://portal.volccdn.com/obj/volcfe/cloud-universal-doc/upload_e14c86ee1fb6cb0309e3b0198d9d70ea.png)

# 最佳实践

## 接口迁移
若已完成端到端实时语音识别的接入，现需升级至全双工版本，建议按以下步骤迁移：
- 事件改名优先，配置后置：建议先将客户端收发的事件名从实时语音版本切换为全双工版本，再将 `asr` / `tts `/ `dialog` 配置迁入 `extension`，可显著降低迁移风险
- extension 直接复用存量配置：原`StartSessionPayload` 中的 `asr` / `tts` / `dialog` 字段无需改造，按原格式整体移入` extension `即可
- 携带 event_id：推荐所有上行事件在 `optional`字段携带 `event_id `与 `session id`，将状态管理复杂度交由服务端处理，便于链路追踪与排障
- model 固定单值： `session.model`固定填写 `1.2.6.1`（全双工版本），无需再在 `extension.dialog.extra `配置 `model `选路

## 上下文管理
- 初始化历史：通过 `conversation.item.create `注入历史问答对
说明
- 上下文须按 user /assistant 成对提交，数组长度为偶数
- 时间戳需统一：要么全部携带（严格递增、不超过当前时间），要么全部不携带
- 接续历史对话：复用上次 `session.created `返回的 `session.id`（即 `dialog.id`）即可接续，服务端默认保留最近 20 轮问答记录

## Function Calling ![Diagram](https://portal.volccdn.com/obj/volcfe/cloud-universal-doc/upload_ab4130dab5c9ece03ae11d61b7cd8c0f.png)
- 工具声明：在 `session.update` 的 `tools `字段中以标准 JSON Schema 结构声明（`type` = `function` + `parameters`）；会话过程中可再次发送 `session.update` 动态增删工具
注意
`session.update`动态增删工具，为全量覆盖，非增量更新
- 按 call_id 配对回传：下行事件 `response.function_call_arguments.done` 的每个调用项均携带唯一 `call_id`。客户端执行完本地函数后，须通过 `conversation.item.create` 回传结果（`role`=`tool`，结果放入`content `数组），并在回传项中携带相同的`call_id`；服务端据此将函数输出与对应调用配对
注意
call_id不一致会导致结果无法匹配、回复异常
- 并行调用：单次` response.function_call_arguments.done` 的 `items` 可能包含多个函数调用，需按每个`call_id `分别执行，并将结果聚合后一次性回传；全部回传完成后，模型才会继续生成最终回复
- output 序列化为字符串：函数执行结果建议序列化为 JSON 字符串后放入`output`字段，结构清晰，便于模型解析

## 稳定性与限流
- 优雅关闭：务必先发送`session.close`（即`FinishSession`）并收到服务端回复后，再关闭 WebSocket 链接；直接断开会触发 `ContextCanceled`错误（错误码为`55000001`）
- 5xx 重连：遇到服务端 5xx 错误时，应统一触发重连逻辑
- 限流说明：限流纬度包括 QPM（每分钟` StartSession `调用次数，默认 `60`）与 TPM（每分钟 token 消耗量，默认 10 万），按 AppID/项目维度计算。
注意
若预估用量将超过配额，请提前联系对应商务沟通扩容

# 附：错误码说明
客户端应对所有下行 error 事件做统一捕获与日志记录：
- 遇服务端 5xx 错误统一触发重连
- 遇鉴权/参数类错误（4xx）应停止重试并核对配置
推荐在每条上行事件中携带 `event_id`，以便结合服务端返回的 `X-Tt-Logid` 进行精准的问题定位与链路追踪

| 错误码 | 关键字 | 描述与处理建议 |
| --- | --- | --- |
| 42000020 | volc_websearch_bot_id is required | web_agent联网模式缺 `bot_id` |
|  | volc_websearch_api_key is required | 联网模式缺少`api_key` |
| 45000003 | Abnormal silence audio | 超过10 分钟无交互，服务端释放连接 |
| 50000000 | AudioQueryError | 模型推理出错 |
|  | found unknown escape character | `speaking_style` / `system_role` 含非法字符，建议检查 prompt |
| 55000001 | ServerError | 模型推理出错 |
|  | ContextCanceled | 未正常发送 `session.close `即断开，务必收到回复再断连 |
|  | ClientError:InvalidSpeaker | 音色名不合法 |
|  | ExceededConcurrentDurationLimit | 并发时长超限 |
| 50700000 | stream recv timeout | 模型推理超时 |
| 52000022 | AudioChatError | 模型推理出错 |
| 52000035 | S2SQueryConnectError | 模型推理出错 |



# 附：事件对照表
下表为端到端实时语音 - 全双工版本与原版本的上行、下行事件对照说明

## 上行事件

| 事件名 | 原S2S版本事件名 |
| --- | --- |
| `session.create`（首次） | `StartSession` |
| `session.update`（会话中） | `UpdateConfig` |
| `session.close` | `FinishSession` |
| `input_audio_buffer.append` | `TaskRequest` |
| `input_audio_buffer.commit` | `EndASR` |
| `speech_text_buffer.commit` | `SayHello` |
| `speech_text_buffer.replacement.append / commit` | `ChatTTSText` |
| `conversation.item.create` | `ConversationCreate / FunctionCallOutput` |
| `conversation.item.update` | `ConversationUpdate` |
| `conversation.item.retrieve` | `ConversationRetrieve` |
| `conversation.item.delete` | `ConversationDelete` |
| `response.cancel` | `ClientInterrupt` |



## 下行事件

| 事件名 | 原S2S版本事件 |
| --- | --- |
| `session.created` | `SessionStarted` |
| `session.updated` | `SessionUpdated / ConfigUpdated` |
| `session.closed` | `SessionFinished` |
| `input_audio_buffer.committed` | `ClientStopped` |
| `conversation.item.input_audio_transcription.started` | `ASRInfo` |
| `conversation.item.input_audio_transcription.delta` | `ASRResponse` |
| `conversation.item.input_audio_transcription.completed` | `ASREnded` |
| `conversation.item.input_audio_transcription.failed` | `ASRFailed` |
| `response.output_text.delta` | `ChatResponse` |
| `response.output_text.done` | `ChatEnded` |
| `response.output_audio.started` | `TTSSentenceStart` |
| `response.output_audio.delta` | `TTSResponse` |
| `response.output_audio.done` | `TTSEnded` |
| `conversation.item.added` | `ConversationCreated` |
| `conversation.item.retrieved` | `ConversationRetrieved` |
| `conversation.item.deleted` | `ConversationDeleted` |
| `response.function_call_arguments.done` | `FunctionCallResponse` |
| `response.done` | `UsageResponse` |
| `error` | `ResponseMeta / DialogCommonError` |

豆包实时语音模型 3.0（Seeduplex）是一款全双工端到端语音大模型，提供低时延、高拟人的实时语音对话能力

# [接入必读](https://www.volcengine.com/docs/6561/2549732?AuditDocumentID=397063&lang=zh)
豆包实时语音模型 3.0（Seeduplex）采用全新的 Realtime 事件协议，与原版本差异较大。接入前请务必先完整阅读[《接入必读》](https://www.volcengine.com/docs/6561/2549732?AuditDocumentID=397063&lang=zh)，了解协议设计原则、注意事项与最佳实践，避免因协议不熟悉导致接入异常

# 完整示例
以下为完整示例demo，单事件示例可参考右侧各事件的输入/输出示例

### Go示例：
[go1.24_duplex_demo.zip](https://portal.volccdn.com/obj/volcfe/cloud-universal-doc/upload_623b7ef30ec3660a806e92bde33d05d8.zip)

### Python示例：
[python3.7_duplex_demo.zip](https://portal.volccdn.com/obj/volcfe/cloud-universal-doc/upload_148ee77d3245e465d244b912d1e83c91.zip)

## Web页面快速体验demo
提供可快速体验 S2S 全双工版本的 Web Demo，下载后输入 API Key（可从[控制台 > API Key 管理](https://console.volcengine.com/speech/new/setting/apikeys?projectName=default.)获取），即可在页面中可视化操作并体验全双工效果
[web_duplex_demo.zip](https://portal.volccdn.com/obj/volcfe/cloud-universal-doc/upload_40e78e155a0960f1fa2cdafc098a4254.zip)

# 请求
请求路径`wss://openspeech.bytedance.com/api/v3/duplex/realtime/dialogue`


### 请求头

X-Api-Key `string`
API Key 可以从 [控制台>API Key管理](https://console.volcengine.com/speech/new/setting/apikeys?projectName=default.) 获取
说明
- 同时支持[旧版控制台](https://console.volcengine.com/speech/service/10035)的鉴权方式，详见[旧版控制台鉴权参考示例](https://www.volcengine.com/docs/6561/2534847?lang=zh)
- 旧版控制台后续会逐步下线，建议尽快切换至新版控制台使用






### 上行事件

创建/更新会话

type `string`
指定请求事件类型。创建会话时，字段固定为`session.create`；更新会话时，字段固定为`session.update`



session `object`

id `string`
对应原 dialog id，接续历史对话时传入



model `string`
固定值：`1.2.6.1`



instructions`string`
系统提示词（System message），用于引导模型的回复内容与音频风格，与模型内部 SP 及上下文合计长度上限为 12K tokens



audio `object`

input`object`

format `object`
指定上传音频的规格

type`string`
指定输入音频格式，支持`pcm`和`speech_opus`



rate`int`
指定输入音频采样率，仅支持`16000`，单位为Hz


注意
- 音频分片建议以20 ms 为单位（16k /int16 格式下每包 640 字节），并严格按照实时音频流的节奏发送，发送速率偏离实际节奏（过快或过慢）都将触发服务端错误
- 模型依赖上行音频流保活。客户端关闭麦克风后若不再发送音频帧，须主动发送静音事件`input_audio_mute.commit`，恢复麦克风时发送取消静音事件`input_audio_unmute.commit`，否则服务端会因持续收不到音频输入触发超时，导致模型无响应





output`object`

format`object`
指定输出音频规格

type`string`
指定输出音频格式，支持`pcm`和`ogg_opus`



rate`int`
指定输出音频采样率，仅支持`24000`，单位为Hz





voice `string`
指定音色ID，目前支持音色详见：[音色列表](https://docs.volcengine.com/docs/6561/1257544?lang=zh)，同时也支持复刻音色



speed` number`
指定语速，默认值为`0`，取值范围：[`-50`,`100`]，取值越大，语速越快
`-50`代表0.5倍速，`100`代表2.0倍速，默认不调整语速



loudness `number`
指定音量，默认值为`0`，取值范围：[`-50`,`100`]，取值越大，音量越大
`-50`代表0.5倍音量，`100`代表2.0倍音量，默认不调整音量







tools `array`
Function Calling 工具定义，使用标准 JSON Schema 结构





extension `object`
配置模型透传参数

asr`object`
配置ASR参数

extra`object`
配置ASR附加参数

enable_asr_twopass `bool`
启用非流式模型识别能力，默认为`false`



boosting_table_id`string`
热词词表id，可在[控制台>自学习平台](https://console.volcengine.com/speech/new/hot-word?projectName=default)配置热词后获取
说明
需同时将`enable_asr_twopass`设置为`true`，否则无法生效



boosting_table_name`string`
热词词表名称，可在[控制台>自学习平台](https://console.volcengine.com/speech/new/hot-word?projectName=default)配置热词后获取
说明
需同时将`enable_asr_twopass`设置为`true`，否则无法生效



regex_correct_table_id`string`
正则替换词表id，可在[控制台>自学习平台](https://console.volcengine.com/speech/new/correct-word?projectName=default)配置正则替换词后获取。相较于替换词的精确匹配替换，正则替换词适合批量格式转换（如日期格式统一、符号标准化）、模糊模式匹配等复杂场景



regex_correct_table_name`string`
正则替换词表名称，可在[控制台>自学习平台](https://console.volcengine.com/speech/new/correct-word?projectName=default)配置正则替换词后获取。相较于替换词的精确匹配替换，正则替换词适合批量格式转换（如日期格式统一、符号标准化）、模糊模式匹配等复杂场景



context`string`
配置热词与替换词，提升识别准确率

hotwords`array`
配置热词

words`string`
热词文本


示例：


```
"context": {
    "hotwords": [
        {"word":"火山引擎"},
        {"word":"豆包语音"}
    ]
}
```






correct_words`object`
配置替换词
示例：


```
"correct_words": {
    "原词1":"替换词1",
    "原词2":"替换词2"
}
```












dialog`object`
配置Dialog参数

location`string`
位置信息配置，支持以下字段：`longitude`（经度）、`latitude`（纬度）、`city`（城市）、`country`（国家）、`province`（省份）、`district`（区县）、`town`（乡镇 / 街道）、`country_code`（国家代码）、`address`（详细地址）



dialog_context`array`
初始化上下文，需按照`user`/`assistant`成对传入QA

role`string`
指定对话角色：`user`/`assistant`



text`string`
传入对话文本



timestamp`int`
传入对话时间戳





extra`string`
配置Dialog附加参数

strict_audit`bool`
开启严格审核，默认为`true`
- `true`：严格审核
- `false`：普通审核



audit_response`string`
指定用户query命中安全审核时的自定义回复话术



enable_volc_websearch`bool`
开启内置联网功能，默认为`false`，开通服务请参考[控制台融合信息搜索API](https://docs.volcengine.com/docs/87772/2272953?redirect=1&lang=zh)



volc_websearch_type`string`
用于指定搜索服务类型，默认为`web_custom_api`，支持以下服务：
- `web_custom_api`：豆包搜索 Custom 版，需在[控制台](https://console.volcengine.com/search-infinity/web-search?_vtm_=a106466.b106468.0_0.0_0.0.201_7676320633895405071&projectName=default)开通服务
- `web_global_api`：豆包搜索 Global 版，需在[控制台](https://console.volcengine.com/search-infinity/web-search?_vtm_=a106466.b106468.0_0.0_0.0.201_7676320633895405071&projectName=default)开通服务
说明
建议根据业务场景选择匹配的搜索服务类型，以兼顾功能和调用性能：
- `web_custom_api`：面向行业定制的联网搜索。响应更快（相比 Global 版快约 350ms），单请求返回条数更多，同时支持行业领域与权威分级筛选，并可直接输出网页完整正文，适用于具有明确行业属性的高频调用场景，尤其适合对响应时延敏感的业务
- `web_global_api`：面向全球站点的通用联网搜索。覆盖面更广，支持全球内容检索。支持摘要长度自由调节与网页原文插图返回，综合搜索效果更优，适用于跨境内容检索及对结果质量、摘要可读性要求较高的场景
有关各版本的详细差异说明，请参考：[豆包搜索产品差异对比](https://docs.volcengine.com/docs/87772/2272949?lang=zh)



volc_websearch_api_key`string`
指定融合信息搜索API密钥，开启`enable_volc_websearch`后需配置此参数



enable_music`bool`
开启唱歌能力，默认为`false`，开启后，系统将从曲库检索唱歌数据并传入模型，以提升模型唱歌表现
说明
当前仅官方主推的 4 个音色（Vivi 2.0、小何 2.0、云舟 2.0、小天 2.0）可保证较好的歌唱合成效果



enable_loudness_norm`bool`
开启输出音频响度均衡能力，默认为`false`



enable_user_query_exit`bool`
开启退出意图识别能力，默认为`false`，开启后，服务端将在`response.output_audio.done`事件中携带退出意图信号，供客户端执行退出操作







tts`object`
配置TTS参数

extra`object`
配置TTS附加参数

max_length_to_filter_parenthesis `int`
指定过滤括号内文本的长度，单位为字符，默认为0（即不过滤），推荐取值范围0~100
说明
- 该参数用于过滤文本中括号内的注释、补充说明等无需朗读的内容
- 当括号内文本字符数超过设定值时，该括号的过滤功能将失效，括号内内容会被正常朗读。若存在较长的括号文本需要过滤，建议客户端在送入合成前自行完成前置过滤，以避免过滤失效及不必要的时延



explicit_dialect`string`
指定方言参数，支持的方言：`dongbei`、`sichuan`、`shaanxi`、`yue`、`beijing`、`henan`、`tianjin`、`shanghai`
说明
当前仅vivi、小何、云舟和小天4个音色支持方言参数，具体的音色ID请参见：[音色列表](https://docs.volcengine.com/docs/6561/1257544?lang=zh)



aigc_metadata`string`
配置AIGC 内容溯源与版权元信息

enable`bool`
开启隐式水印，默认为`false`



content_producer`string`
指定合成服务提供者的名称或编码



produce_id`string`
指定内容制作编号



content_propagator`string`
指定内容传播服务提供者的名称或编码



propagate_id`string`
指定内容传播编号













打招呼

type`string`
指定请求事件类型。用于打招呼，字段固定为`speech_text_buffer.commit`



event_id`string`
客户端发起请求时，可生成并传入自定义`event_id`，该字段为可选，建议传入，用于后续事件匹配与追踪



text `string`
输入待合成的“打招呼”文本





发送音频流

type`string`
指定请求事件类型。发送请求时，字段固定为`input_audio_buffer.append`
注意
模型依赖上行音频流保活。客户端关闭麦克风后若不再发送音频帧，须主动发送静音事件`input_audio_mute.commit`（即`type`指定为`input_audio_mute.commit`），恢复麦克风时发送取消静音事件`input_audio_unmute.commit`（即`type`指定为`input_audio_unmute.commit`），否则服务端会因持续收不到音频输入触发超时，导致模型无响应



event_id`string`
客户端发起请求时，可生成并传入自定义`event_id`，该字段为可选，建议传入，用于后续事件匹配与追踪



audio `string`
传入音频数据，音频数据经 Base64 编码后填入`audio`字段，完整事件以 JSON 文本帧形式发送





强制判停

type`string`
指定请求事件类型。发送请求时，字段固定为`input_audio_buffer.commit`。确认音频 query 发送完毕后，可发送该事件强制模型判停



event_id`string`
客户端发起请求时，可生成并传入自定义`event_id`，该字段为可选，建议传入，用于后续事件匹配与追踪





干预模型回复

type`string`
指定请求事件类型。用于流式打招呼，或不需要模型闲聊结果、希望直接指定文本合成音频的场景
- `speech_text_buffer.replacement.append` ：流式上传待合成文本
- `speech_text_buffer.replacement.commit`：结束包（文本上传完成）



event_id`string`
客户端发起请求时，可生成并传入自定义`event_id`，该字段为可选，建议传入，用于后续事件匹配与追踪



text `string`
输入待合成的文本





上下文管理

新增上下文

type`string`
指定请求事件类型。发送请求时，字段固定为`conversation.item.create`



items`array`
新增上下文对话信息，可用于初始化历史上下文。每次最多提交 20 轮（40 条）完整 QA

id`string`
指定自定义的上下文对话id



type`string`
指定上下文类型，固定为`message`



role`string`
指定对话角色，可选值`user`、`assistant`



content`array`
指定对话内容







更新上下文

type`string`
请求事件类型。发送请求时，字段固定为`conversation.item.update`



event_id`string`
客户端发起请求时，可生成并传入自定义`event_id`，该字段为可选，建议传入，用于后续事件匹配与追踪



items`array`
指定待更新的上下文信息

id`string`
指定待更新的对话id
- 更新用户问题：传入`user`对应的`items_id`
- 更新模型回复：传入`assistant`对应的`items_id`



content`array`
传入待更新的对话内容







查询上下文

type`string`
请求事件类型。发送请求时，字段固定为`conversation.item.retrieve`



event_id`string`
客户端发起请求时，可生成并传入自定义`event_id`，该字段为可选，建议传入，用于后续事件匹配与追踪



items`array`
指定待查询的上下文信息

id`string`
传入待查询的对话id，返回该轮次上下文信息，不传则返回最近20轮完整上下文信息







删除上下文

type`string`
请求事件类型。发送请求时，字段固定为`conversation.item.delete`



event_id`string`
客户端发起请求时，可生成并传入自定义`event_id`，该字段为可选，建议传入，用于后续事件匹配与追踪



items`array`
指定待删除的上下文信息

id`string`
指定待删除的对话id
说明
上下文删除以对话轮为单位进行，传入`user`侧`items_id`时，系统将同时删除与之成对的`assistant`回复，传入`assistant`侧`items_id`时同理









客户端打断

type`string`
请求事件类型。发送请求时，字段固定为`response.cancel`。用于取消进行中的响应，即客户端主动打断服务端播报，便于进行下一次识别。





FC结果回传

type`string`
请求事件类型。发送请求时，字段固定为`conversation.item.create`。该事件用于在下行事件`response.function_call_arguments.done` 返回后，上报工具执行结果，供模型基于工具数据继续生成回复



items `array`
指定函数回传信息

call_id `string`
函数调用的唯一标识，用于回传函数调用结果，须与下行事件`response.function_call_arguments.done`下发的`call_id` 保持一致



role` string`
指定条目角色信息，固定值为`tool`，标识该item为函数调用结果



content `array`
传入函数调用的结果信息

type `string`
内容类型，固定值为 `input_text`



text `string`
传入函数调用的执行结果









结束会话

type`string`
请求事件类型。结束会话时，字段固定为`session.close`



event_id`string`
客户端发起请求时，可生成并传入自定义`event_id`，该字段为可选，建议传入，用于后续事件匹配与追踪







# 响应


### 响应头
X-Tt-Logid `string`
服务端返回的 `Logid`，用于在咨询或者反馈时定位问题




### 下行事件

type `string`
服务端响应事件类型。下行事件如下：

| 类别 | 事件名 | 说明 |
| --- | --- | --- |
| Session | session.created | 该事件表示会话已成功启动，返回的`session.id`（对应原版本`dialog.id`），可用于接续历史对话内容。 |
|  | session.updated | 该事件为 `session.update` 请求对应的确认响应（ack），表示会话配置已成功更新 |
|  | session.closed | 该事件为会话已结束 |
| Audio | input_audio_buffer.committed | 该事件用于通知客户端输入音频缓冲区已成功提交，标志着一次用户音频输入的结束 |
| ASR | conversation.item.input_audio_transcription.started | 模型识别出音频流中的首字时返回 |
|  | conversation.item.input_audio_transcription.delta | 模型实时识别出的用户说话文本内容（流式增量） |
|  | conversation.item.input_audio_transcription.completed | 模型判定用户说话结束时返回 |
|  | conversation.item.input_audio_transcription.failed | ASR 识别失败 |
| Chat | response.output_text.delta | 模型回复的文本内容（流式增量） |
|  | response.output_text.done | 模型回复文本生成结束 |
| TTS | response.output_audio.started | 合成音频的起始事件，`tts_type`取值类型有：<br>- `audit_content_risky`（命中安全审核音频）<br>- `chat_tts_text`（客户文本合成音频）<br>- `network`（内置联网音频）<br>- `default`（闲聊音频） |
|  | response.output_audio.delta | 返回的流式音频数据块，Base64 编码 |
|  | response.output_audio.done | 模型一轮音频合成结束。其中 `status_code="20000002"` 表示模型识别到用户的退出意图 |
| Context | conversation.item.added | 新增上下文请求的确认（ack），返回创建成功的上下文数组 |
|  | conversation.item.retrieved | 查询上下文请求的确认（ack），返回查询到的上下文内容 |
|  | conversation.item.deleted | 删除上下文请求的确认（ack），返回被删除的上下文内容。若没有可删除的上下文<br>`{   "status_code":40000010,`<br>`    "message":"empty conversation deleted messages"   }` |
| FC | response.function_call_arguments.done | FC函数调用参数生成完成。<br>- 下行 `items `每个函数调用项均带有唯一的`call_id`、函数名`name` 与生成好的参数 `arguments`（JSON 字符串）。<br>- 客户端执行本地函数后，须通过 `conversation.item.create（role=tool）`回传结果，并在回传项中携带相同的 call_id；<br>- 服务端依据`call_id`将函数输出与对应调用配对，模型再继续生成回复 |
| Usage | response.done | 一轮交互结束，返回本次用量统计 |
|  | response.canceled | 客户端打断请求`response.cancel`的确认（ack） |
| Error | error | 错误事件，错误表详见：[接入必读-错误码说明](https://www.volcengine.com/docs/6561/2549732?AuditDocumentID=397063&lang=zh#llUZxXnt) |









## API examples

### 创建/更新会话

输入示例

```json
{
  "type": "session.create",
  "session": {
    "id": "对应 dialog id",
    "model": "1.2.6.1",
    "instructions": "You are a creative assistant that helps with design tasks.",
    "audio": {
      "input": {
        "format": {
          "type": "pcm",
          "rate": 16000
        }
      },
      "output": {
        "format": {
          "type": "pcm",
          "rate": 24000
        },
        "speed": 0,
        "loudness": 0,
        "voice": "zh_female_vv_jupiter_bigtts"
      }
    },
    "tools": [
      {
        "type": "function",
        "name": "display_color_palette",
        "description": "Call this function when a user asks for a color palette.",
        "parameters": {
          "type": "object",
          "properties": {
            "theme": {
              "type": "string",
              "description": "Description of the theme."
            },
            "colors": {
              "type": "array",
              "description": "Five hex codes.",
              "items": {
                "type": "string"
              }
            }
          },
          "required": [
            "theme",
            "colors"
          ]
        }
      }
    ]
  },
  "extension": {
    "asr": {},
    "tts": {},
    "dialog": {}
  }
}
```

输出示例

```json
{
  "type": "session.created",
  "event_id": "event_C9G5RJeJ2gF77mV7f2B1j",
  "session": { "id": "对应 dialog id" }
}
```

### 发送音频流

输入示例

```json
{
  "event_id": "event_456",
  "type": "input_audio_buffer.append",
  "audio": "Base64EncodedAudioData"
}
```

输出示例

```json
//started（ASRInfo）
{
  "type": "conversation.item.input_audio_transcription.started",
  "event_id": "event_0",
  "item_id": ""
}
//delta（ASRResponse）
{
  "type": "conversation.item.input_audio_transcription.delta",
  "event_id": "event_CCXGRxsAimPAs8kS2Wc7Z",
  "item_id": "item_CCXGQ4e1ht4cOraEYcuR2",
  "content_index": 0,
  "delta": "Hey"
}
//completed（ASREnded）
{
  "type": "conversation.item.input_audio_transcription.completed",
  "event_id": "event_CCXGRvtUVrax5SJAnNOWZ",
  "item_id": "item_CCXGQ4e1ht4cOraEYcuR2",
  "content_index": 0,
  "transcript": "Hey, can you hear me?"
}
//failed（ASRFailed）
{
  "event_id": "event_2324",
  "type": "conversation.item.input_audio_transcription.failed",
  "item_id": "msg_003",
  "error": {
    "type": "transcription_error",
    "code": "audio_unintelligible",
    "message": "The audio could not be transcribed.",
    "param": null
  }
}
//response.output_text.delta
{
  "event_id": "event_4142",
  "type": "response.output_text.delta",
  "question_id": "question_001",
  "response_id": "resp_001",
  "delta": "Sure, I can h"
}
//response.output_text.done
{
  "event_id": "event_4344",
  "type": "response.output_text.done",
  "question_id": "question_001",
  "response_id": "resp_001",
  "text": "Sure, I can help with that."
}
//response.output_audio.started
{
  "event_id": "event_4",
  "type": "response.output_audio.started",
  "question_id": "question_001",
  "response_id": "",
  "tts_type": ""
}
//response.output_audio.delta
{
  "event_id": "event_4950",
  "type": "response.output_audio.delta",
  "question_id": "question_001",
  "response_id": "resp_001",
  "delta": "Base64EncodedAudioDelta"
}
//response.output_audio.done
{
  "event_id": "event_5152",
  "type": "response.output_audio.done",
  "question_id": "question_001",
  "response_id": "resp_001",
  "status_code": "20000002"
}
```

### 干预模型回复

输入示例

```json
//speech_text_buffer.replacement.append
{
  "event_id": "",
  "type": "speech_text_buffer.replacement.append",
  "text": "干预回复文本"
}
//speech_text_buffer.replacement.commit
{
  "event_id": "evt_001",
  "type": "speech_text_buffer.replacement.commit",
  "text": "（可选）结束包也支持带干预回复文本"
}
```

输出示例

```json
//response.output_audio.started
{
  "event_id": "event_4",
  "type": "response.output_audio.started",
  "question_id": "question_001",
  "response_id": "",
  "tts_type": "chat_tts_text"
}
//response.output_audio.delta
{
  "event_id": "event_4950",
  "type": "response.output_audio.delta",
  "question_id": "question_001",
  "response_id": "resp_001",
  "delta": "Base64EncodedAudioDelta"
}
//response.output_audio.done
{
  "event_id": "event_5152",
  "type": "response.output_audio.done",
  "question_id": "question_001",
  "response_id": "resp_001",
  "status_code": "20000002"
}
```

### 上下文管理

输入示例

```json
//conversation.item.create
{
  "type": "conversation.item.create",
  "items": [
    {
      "id": "111",
      "type": "message",
      "role": "user",
      "content": [
        { "type": "input_text", "text": "hi" }
      ]
    },
    {
      "id": "222",
      "type": "message",
      "role": "assistant",
      "content": [
        { "type": "input_text", "text": "hi!" }
      ]
    }
  ]
}
//conversation.item.create（函数结果回传-Function calling)
{
  "type": "conversation.item.create",
  "items": [
    {
      "call_id": "call_a1b2c3d4",
      "role": "tool",
      "content": [
        {
          "type": "input_text",
          "text": "今天北京天气晴，气温22~30℃，微风"
        }
      ]
    }
  ]
}
//conversation.item.update
{
  "event_id": "event_901",
  "type": "conversation.item.update",
  "items": [
    {
      "id": "item_002",
      "content": [
        {
          "type": "input_text",
          "text": "更新后的文本"
        }
      ]
    }
  ]
}
//conversation.item.retrieve
{
  "event_id": "event_901",
  "type": "conversation.item.retrieve",
  "items": [
    { "id": "item_002" }
  ]
}
//conversation.item.delete
{
  "event_id": "event_901",
  "type": "conversation.item.delete",
  "items": [
    { "id": "item_003" }
  ]
}
```

输出示例

```json
//conversation.item.added/retrieved
{
  "type": "conversation.item.added",
  "event_id": "event_C9G8pjSJCfRNEhMEnYAVy",
  "items": [
    {
      "id": "item_C9G8pGVKYnaZu8PH5YQ9O",
      "type": "message",
      "status": "completed",
      "role": "user",
      "call_id": "",
      "content": [
        { "type": "input_text", "text": "hi" }
      ]
    }
  ]
}
//conversation.item.deleted
{
  "event_id": "event_2526",
  "type": "conversation.item.deleted"
}
```

### 客户端打断

输入示例

```json
{
  "type": "response.cancel"
}
```

输出示例

```json
{
"type":"response.canceled",
"event_id":"event_17"
}
```

### 结束会话

输入示例

```json
{
  "event_id": "event_close",
  "type": "session.close"
}
```

输出示例

```json
{
  "type": "session.closed"
}
```

### 强制判停

输入示例

```json
{
  "event_id": "event_789",
  "type": "input_audio_buffer.commit"
}
```

输出示例

```json
{
  "event_id": "event_1121",
  "type": "input_audio_buffer.committed"
}
```

### Function calling

输入示例

```json
{
  "event_id": "client_event_1234",
  "type": "conversation.item.create",
  "items": [
    {
      "call_id": "call_weather_001",
      "role": "tool",
      "content": [
        {
          "type": "input_text",
          "text": "今天北京天气晴，气温22~30℃，微风"
        }
      ]
    },
    {
      "call_id": "call_stock_002",
      "role": "tool",
      "content": [
        {
          "type": "input_text",
          "text": "当前股价33.25元，涨幅+1.23%"
        }
      ]
    }
  ]
}
```

输出示例

```json
{
  "event_id": "event_8899",
  "type": "response.function_call_arguments.done",
  "items": [
    {
      "id": "item_001",
      "type": "function_call",
      "call_id": "call_weather_001",
      "name": "get_weather",
      "arguments": "{\"city\":\"Beijing\"}"
    },
    {
      "id": "item_002",
      "type": "function_call",
      "call_id": "call_stock_002",
      "name": "get_stock",
      "arguments": "{\"stock_code\":\"600036\",\"market\":\"sh\"}"
    }
  ]
}
```

### 打招呼

输入示例

```json
{
  "event_id": "evt_001",
  "type": "speech_text_buffer.commit",
  "text": "你好！"
}
```

输出示例

```json
//response.output_audio.started
{
  "event_id": "event_4",
  "type": "response.output_audio.started",
  "question_id": "question_001",
  "response_id": "",
  "tts_type": ""
}
//response.output_audio.delta
{
  "event_id": "event_4950",
  "type": "response.output_audio.delta",
  "question_id": "question_001",
  "response_id": "resp_001",
  "delta": "Base64EncodedAudioDelta"
}
//response.output_audio.done
{
  "event_id": "event_5152",
  "type": "response.output_audio.done",
  "question_id": "question_001",
  "response_id": "resp_001"
}
```

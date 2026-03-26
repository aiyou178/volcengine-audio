"""Volcengine Realtime Dialogue (combined TTS+STT) schemas and utilities.

This module contains request/response models and helper functions for Volcengine's
realtime dialogue service, which combines speech recognition and synthesis in a
bidirectional streaming setup.
"""

import struct
from enum import StrEnum
from typing import Literal, TypedDict

from pydantic import BaseModel, Field, model_validator

from .protocol import (
  EventSend,
  HeaderSize,
  MessageType,
  MessageTypeSpecificFlag,
  ProtocolVersion,
)


class RealtimeDialogueConfig(BaseModel):
  """Configuration for realtime dialogue session

  https://www.volcengine.com/docs/6561/1594356?lang=zh
  """

  class DialogConfig(BaseModel):
    bot_name: str = Field(
      default='豆包',
      description='Bot name',
      max_length=20,
    )
    system_role: str | None = Field(
      default=None,
      description='Background persona, describing character origin, settings, etc.',
      examples=[
        'You are the Big Bad Wolf, user is Little Red Riding Hood, threaten to eat them when they escape.'
      ],
    )
    speaking_style: str | None = Field(
      default=None,
      description='Speaking style',
      examples=['You speak like Lin Daiyu.', 'Your tone is sassy.'],
    )
    dialog_id: str = Field(
      default='', description='Dialog ID for session continuity'
    )
    character_manifest: str | None = Field(
      default=None,
      description='Role description for SC/SC2.0 models',
    )

    class Location(BaseModel):
      longitude: float | None = Field(None, description='Longitude coordinate')
      latitude: float | None = Field(None, description='Latitude coordinate')
      city: str | None = Field(None, description='City name')
      country: str | None = Field(None, description='Country name')
      province: str | None = Field(None, description='Province name')
      district: str | None = Field(None, description='District name')
      town: str | None = Field(None, description='Town name')
      country_code: str | None = Field(None, description='Country code')
      address: str | None = Field(None, description='Full address')

    location: Location | None = Field(
      None, description='User location info to improve web search accuracy'
    )

    class DialogContextItem(BaseModel):
      role: Literal['user', 'assistant'] | str = Field(
        ..., description='Role in dialog context'
      )
      text: str = Field(..., description='Message content')
      timestamp: int | None = Field(
        None, description='Unix timestamp in milliseconds'
      )

    dialog_context: list[DialogContextItem] | None = Field(
      None, description='Initial dialogue context, should be complete QA pairs'
    )

    @model_validator(mode='after')
    def check_length(self):
      if len((self.system_role or '') + (self.speaking_style or '')) > 4000:
        raise ValueError(
          'System role and speaking style combined length must not exceed 4000 characters'
        )
      if self.dialog_context and len(self.dialog_context) % 2 != 0:
        raise ValueError('dialog_context length must be an even number')
      return self

    class Extra(BaseModel):
      class VolcWebsearchType(StrEnum):
        web_summary = 'web_summary'
        web = 'web'
        web_agent = 'web_agent'

      class InputMod(StrEnum):
        audio = 'audio'
        text = 'text'
        audio_file = 'audio_file'
        keep_alive = 'keep_alive'
        push_to_talk = 'push_to_talk'

      class Model(StrEnum):
        model_o = 'O'
        model_sc = 'SC'
        model_o2_0 = '1.2.1.1'
        model_o2_0_legacy = '1.2.1.0'
        model_sc2_0 = '2.2.0.0'

      strict_audit: bool = Field(
        default=True,
        description='Audit level: true=strict audit, false=normal audit',
      )
      audit_response: str | None = Field(
        None, description='Custom response when user query hits audit rules'
      )
      enable_volc_websearch: bool = Field(
        default=False, description='Enable Volcengine web search'
      )
      volc_websearch_type: VolcWebsearchType = Field(
        default=VolcWebsearchType.web_summary,
        description='Volcengine integrated search type',
      )
      volc_websearch_api_key: str | None = Field(
        None, description='Volcengine integrated search API Key'
      )
      volc_websearch_bot_id: str | None = Field(
        None,
        description='Bot ID when using web_agent search source',
      )
      volc_websearch_result_count: int | None = Field(
        None,
        description='Volcengine integrated search result count, defaults to 10',
        ge=1,
        le=10,
      )
      volc_websearch_no_result_message: str | None = Field(
        None, description='Volcengine integrated search no result message'
      )
      input_mod: InputMod = Field(
        default=InputMod.audio,
        description='Input mode for non-microphone requests',
      )
      enable_music: bool = Field(
        default=False, description='Enable singing capability'
      )
      enable_loudness_norm: bool = Field(
        default=False,
        description='Enable 2.0 output loudness normalization',
      )
      enable_conversation_truncate: bool = Field(
        default=False,
        description='Enable 2.0 context truncation',
      )
      enable_user_query_exit: bool = Field(
        default=False,
        description='Enable exit intent detection from user speech',
      )
      model: Model = Field(
        default=Model.model_o, description='Realtime dialogue model version'
      )

    extra: Extra = Field(default_factory=Extra)

  class TTSConfig(BaseModel):
    class AudioConfig(BaseModel):
      class Format(StrEnum):
        pcm = 'pcm'
        """32bit"""
        pcm_s16le = 'pcm_s16le'
        """16bit"""

      channel: int = Field(default=1, description='Audio channels')
      format: Format = Field(default=Format.pcm, description='Audio format')
      sample_rate: int = Field(default=24000, description='Sample rate')
      speech_rate: int = Field(
        default=0,
        ge=-50,
        le=100,
        description='Speech rate for 2.0 models',
      )
      loudness_rate: int = Field(
        default=0,
        ge=-50,
        le=100,
        description='Output loudness for 2.0 models',
      )

    class Speaker(StrEnum):
      zh_female_vv_jupiter_bigtts = 'zh_female_vv_jupiter_bigtts'
      """vv voice: lively and energetic female voice with strong desire to share"""
      zh_female_xiaohe_jupiter_bigtts = 'zh_female_xiaohe_jupiter_bigtts'
      """xiaohe voice: sweet and lively female voice with noticeable Taiwan accent"""
      zh_male_yunzhou_jupiter_bigtts = 'zh_male_yunzhou_jupiter_bigtts'
      """yunzhou voice: fresh and steady male voice"""
      zh_male_xiaotian_jupiter_bigtts = 'zh_male_xiaotian_jupiter_bigtts'
      """xiaotian voice: fresh and magnetic male voice"""

    speaker: Speaker | str = Field(
      default=Speaker.zh_female_vv_jupiter_bigtts, description='Speaker voice'
    )

    audio_config: AudioConfig = Field(default_factory=AudioConfig)

  class Asr(BaseModel):
    class AudioInfo(BaseModel):
      class Format(StrEnum):
        pcm = 'pcm'
        speech_opus = 'speech_opus'

      format: Format | None = Field(
        None,
        description='Client upstream audio format',
      )
      sample_rate: int = Field(16000, description='Client upstream sample rate')
      channel: int = Field(1, description='Client upstream channel count')

    class Extra(BaseModel):
      class Context(BaseModel):
        class Hotword(BaseModel):
          word: str = Field(..., description='Hotword entry')

        hotwords: list[Hotword] = Field(
          default_factory=list,
          description='Custom hotwords merged with table-based entries',
        )
        correct_words: dict[str, str] = Field(
          default_factory=dict,
          description='Regex replacement rules',
        )

      end_smooth_window_ms: int = Field(
        1500,
        description='End smooth window in milliseconds',
        ge=500,
        le=50000,
      )
      enable_custom_vad: bool = Field(
        False,
        description='Enable custom VAD-based turn-end control',
      )
      enable_asr_twopass: bool = Field(
        False,
        description='Enable two-pass ASR (streaming + non-streaming)',
      )
      boosting_table_id: str | None = Field(
        None,
        description='Hotword table ID for two-pass ASR',
      )
      boosting_table_name: str | None = Field(
        None,
        description='Hotword table name for two-pass ASR',
      )
      regex_correct_table_id: str | None = Field(
        None,
        description='Regex correction table ID',
      )
      regex_correct_table_name: str | None = Field(
        None,
        description='Regex correction table name',
      )
      context: Context | None = Field(
        None,
        description='Inline hotword and replacement configuration',
      )

    audio_info: AudioInfo | None = Field(
      None, description='ASR audio information for upstream audio'
    )
    extra: Extra = Field(default_factory=Extra)

  dialog: DialogConfig | None = Field(None, description='Dialog configuration')
  tts: TTSConfig | None = Field(
    None, description='TTS configuration, if None, use ogg opus'
  )
  asr: Asr | None = Field(default=None, description='ASR configuration')


class SayHelloRequest(BaseModel):
  """Request model for SayHello event"""

  content: str = Field(..., description='Hello message content')


class ChatTTSTextRequest(BaseModel):
  """Request model for ChatTTSText event"""

  start: bool = Field(..., description='Is first packet')
  content: str = Field(..., description='Text content to synthesize')
  end: bool = Field(..., description='Is last packet')


class ChatTextQueryRequest(BaseModel):
  """Request model for ChatTextQuery event"""

  content: str = Field(..., description='Text query content')


class ChatRAGTextRequest(BaseModel):
  """Request model for ChatRAGText event."""

  external_rag: str = Field(
    ...,
    description='External RAG content used for summarization and speech output',
  )


class ConversationCreateRequest(BaseModel):
  """Request model for ConversationCreate event."""

  class Item(BaseModel):
    role: Literal['user', 'assistant'] | str = Field(
      ..., description='Role of context item'
    )
    text: str = Field(..., description='Message content')
    timestamp: int | None = Field(
      None, description='Unix timestamp in milliseconds'
    )

  items: list[Item] = Field(..., min_length=1)


class ConversationUpdateRequest(BaseModel):
  """Request model for ConversationUpdate event."""

  class Item(BaseModel):
    item_id: str = Field(..., description='Context item identifier')
    text: str = Field(..., description='Updated message content')

  items: list[Item] = Field(..., min_length=1)


class ConversationRetrieveRequest(BaseModel):
  """Request model for ConversationRetrieve event."""

  class Item(BaseModel):
    item_id: str = Field(..., description='Context item identifier')

  items: list[Item] | None = Field(
    None,
    description='Optional item ids. If omitted, returns latest context window',
  )


class ConversationDeleteRequest(BaseModel):
  """Request model for ConversationDelete event."""

  class Item(BaseModel):
    item_id: str = Field(..., description='Context item identifier')

  items: list[Item] = Field(..., min_length=1)


class ASRInfoResponse(BaseModel):
  """Response model for ASRInfo event - first word detection"""

  question_id: str = Field(
    ..., description='Question ID associated with current round'
  )
  asr_task_id: str | None = Field(
    None, description='ASR task ID for compatibility with older payloads'
  )
  round_id: int | None = Field(
    None, description='Round ID for compatibility with older payloads'
  )


class ASRResponseModel(BaseModel):
  """Response model for ASRResponse event."""

  class Result(BaseModel):
    text: str = Field(..., description='ASR recognized text')
    is_interim: bool = Field(..., description='Whether this result is interim')

  results: list[Result] = Field(
    ..., description='List of recognized results from ASR'
  )


class ASREndedResponse(BaseModel):
  """Response model for ASREnded event"""

  comfort_wait_time: int | None = Field(
    None, description='Comfortable wait time in milliseconds'
  )
  last_resp_cost_time: int | None = Field(
    None, description='Time taken for the last response in milliseconds'
  )
  no_content: bool | None = Field(
    None, description='Indicates if there was no content in the response'
  )
  task_request_seq_id: int | None = Field(
    None, description='Sequence ID of the task request'
  )
  task_request_timestamp: int | None = Field(
    None, description='Timestamp of the task request'
  )
  user_duration: int = Field(
    0, description='Duration of user interaction in milliseconds'
  )


class RealtimeDialogueUsage(TypedDict):
  """Usage information for realtime dialogue"""

  class Usage(TypedDict):
    cached_audio_tokens: int
    cached_text_tokens: int
    input_audio_tokens: int
    input_text_tokens: int
    output_audio_tokens: int
    output_text_tokens: int

  usage: Usage


class ChatResponseModel(BaseModel):
  """Response model for ChatResponse event"""

  content: str = Field(..., description='Chat response content')
  question_id: str | None = Field(None, description='Question context item id')
  reply_id: str | None = Field(None, description='Reply context item id')


class ChatTextQueryConfirmedResponse(BaseModel):
  """Response model for ChatTextQueryConfirmed event."""

  question_id: str = Field(..., description='Question context item id')


class ConversationItemResponse(BaseModel):
  """Context item returned by conversation events."""

  item_id: str = Field(..., description='Context item identifier')
  role: str = Field(..., description='Role of context item')
  text: str = Field(..., description='Message content')
  timestamp: int | None = Field(
    None, description='Unix timestamp in milliseconds'
  )


class ConversationCreatedResponse(BaseModel):
  """Response model for ConversationCreated event."""

  items: list[ConversationItemResponse] = Field(default_factory=list)


class ConversationUpdatedResponse(BaseModel):
  """Response model for ConversationUpdated event."""

  message: str | None = Field(None, description='Optional update result info')


class ConversationRetrievedResponse(BaseModel):
  """Response model for ConversationRetrieved event."""

  items: list[ConversationItemResponse] = Field(default_factory=list)


class ConversationDeletedResponse(BaseModel):
  """Response model for ConversationDeleted event."""

  items: list[ConversationItemResponse] | None = Field(
    None, description='Deleted context items'
  )
  status_code: int | None = Field(
    None, description='Status code when nothing was deleted'
  )
  message: str | None = Field(
    None, description='Detailed delete result message'
  )


class ConnectionFailedResponse(BaseModel):
  """Response model for ConnectionFailed event"""

  error: str = Field(..., description='Error message')


class SessionStartedResponse(BaseModel):
  """Response model for SessionStarted event"""

  dialog_id: str = Field(..., description='Dialog ID for session continuity')


class SessionFailedResponse(BaseModel):
  """Response model for SessionFailed event"""

  error: str = Field(..., description='Error message')


class RealtimeDialogueErrorResponse(BaseModel):
  """Error response model for realtime dialogue"""

  error: str | None = Field(None, description='Error description')
  status_code: int | str | None = Field(None, description='Error status code')
  message: str | None = Field(None, description='Detailed error message')


class RealtimeDialogueFunctions:
  """Helper functions for realtime dialogue API"""

  @staticmethod
  def start_connection_payload() -> bytes:
    """Create StartConnection event payload"""
    return RealtimeDialogueFunctions._calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.StartConnection,
      request_meta={},
    )

  @staticmethod
  def finish_connection_payload() -> bytes:
    """Create FinishConnection event payload"""
    return RealtimeDialogueFunctions._calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.FinishConnection,
      request_meta={},
    )

  @staticmethod
  def start_session_payload(
    session_id: str, config: RealtimeDialogueConfig
  ) -> bytes:
    """Create StartSession event payload"""
    return RealtimeDialogueFunctions._calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.StartSession,
      session_id=session_id,
      request_meta=config.model_dump(exclude_none=True),
    )

  @staticmethod
  def finish_session_payload(session_id: str) -> bytes:
    """Create FinishSession event payload"""
    return RealtimeDialogueFunctions._calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.FinishSession,
      session_id=session_id,
      request_meta={},
    )

  @staticmethod
  def task_request_payload(session_id: str, audio_data: bytes) -> bytes:
    """Create TaskRequest event payload for audio upload"""
    # For audio data, we use AUDIO_ONLY_REQUEST message type
    header = [
      (ProtocolVersion.V1.value << 4) | HeaderSize.SIZE_4.value,
      (MessageType.AUDIO_ONLY_REQUEST.value << 4)
      | MessageTypeSpecificFlag.CARRY_EVENT_ID.value,
      0b00010000,  # RAW serialization, no compression
      0b00000000,
    ]
    payload = bytes(header)

    # Add event ID
    payload += struct.pack('>I', EventSend.TaskRequest.value)

    # Add session ID
    session_id_bytes = session_id.encode()
    payload += struct.pack('>I', len(session_id_bytes))
    payload += session_id_bytes

    # Add audio payload
    payload += struct.pack('>I', len(audio_data))
    payload += audio_data

    return payload

  @staticmethod
  def say_hello_payload(
    session_id: str, hello_request: SayHelloRequest
  ) -> bytes:
    """Create SayHello event payload"""
    return RealtimeDialogueFunctions._calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.SayHello,
      session_id=session_id,
      request_meta=hello_request.model_dump(),
    )

  @staticmethod
  def chat_tts_text_payload(
    session_id: str, tts_request: ChatTTSTextRequest
  ) -> bytes:
    """Create ChatTTSText event payload"""
    return RealtimeDialogueFunctions._calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.ChatTTSText,
      session_id=session_id,
      request_meta=tts_request.model_dump(),
    )

  @staticmethod
  def chat_text_query_payload(
    session_id: str, text_query_request: ChatTextQueryRequest
  ) -> bytes:
    """Create ChatTextQuery event payload"""
    return RealtimeDialogueFunctions._calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.ChatTextQuery,
      session_id=session_id,
      request_meta=text_query_request.model_dump(),
    )

  @staticmethod
  def chat_rag_text_payload(
    session_id: str, rag_request: ChatRAGTextRequest
  ) -> bytes:
    """Create ChatRAGText event payload."""
    return RealtimeDialogueFunctions._calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.ChatRAGText,
      session_id=session_id,
      request_meta=rag_request.model_dump(),
    )

  @staticmethod
  def conversation_create_payload(
    session_id: str, request: ConversationCreateRequest
  ) -> bytes:
    """Create ConversationCreate event payload."""
    return RealtimeDialogueFunctions._calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.ConversationCreate,
      session_id=session_id,
      request_meta=request.model_dump(exclude_none=True),
    )

  @staticmethod
  def conversation_update_payload(
    session_id: str, request: ConversationUpdateRequest
  ) -> bytes:
    """Create ConversationUpdate event payload."""
    return RealtimeDialogueFunctions._calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.ConversationUpdate,
      session_id=session_id,
      request_meta=request.model_dump(exclude_none=True),
    )

  @staticmethod
  def conversation_retrieve_payload(
    session_id: str,
    request: ConversationRetrieveRequest | None = None,
  ) -> bytes:
    """Create ConversationRetrieve event payload."""
    request_meta = request.model_dump(exclude_none=True) if request else {}
    return RealtimeDialogueFunctions._calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.ConversationRetrieve,
      session_id=session_id,
      request_meta=request_meta,
    )

  @staticmethod
  def conversation_delete_payload(
    session_id: str, request: ConversationDeleteRequest
  ) -> bytes:
    """Create ConversationDelete event payload."""
    return RealtimeDialogueFunctions._calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.ConversationDelete,
      session_id=session_id,
      request_meta=request.model_dump(exclude_none=True),
    )

  @staticmethod
  def _calculate_payload(
    message_type: MessageType,
    event: EventSend,
    session_id: str | None = None,
    request_meta: dict | None = None,
  ) -> bytes:
    """Calculate payload for realtime dialogue request"""
    import orjson

    # Header
    header = [
      (ProtocolVersion.V1.value << 4)
      | HeaderSize.SIZE_4.value,  # Protocol version + header size
      (message_type.value << 4) | 0b0100,  # Message type + specific flags
      0b00010000,  # JSON serialization, no compression
      0b00000000,  # Reserved
    ]
    payload = bytes(header)

    if event:
      event_number = event.value
      payload += struct.pack('>I', event_number)

    if session_id:
      # Session ID length and bytes
      session_id_bytes = session_id.encode()
      session_id_length = len(session_id_bytes)
      payload += struct.pack('>I', session_id_length)
      payload += session_id_bytes

    # Default minimal JSON, or fill in connection metadata
    request_meta = request_meta or {}
    request_meta = orjson.dumps(request_meta)
    request_meta_length = len(request_meta)
    payload += struct.pack('>I', request_meta_length)
    payload += request_meta

    return payload

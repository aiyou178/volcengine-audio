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

  https://www.volcengine.com/docs/6561/1594356
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

    class Location(BaseModel):
      longitude: float | None = Field(None, description='Longitude coordinate')
      latitude: float | None = Field(None, description='Latitude coordinate')
      city: str | None = Field(None, description='City name')
      country: str | None = Field(None, description='Country name')
      province: str | None = Field(None, description='Province name')
      district: str | None = Field(None, description='District name')
      town: str | None = Field(None, description='Town name')
      country_code: str = Field(None, description='Country code')
      address: str | None = Field(None, description='Full address')

    location: Location | None = Field(
      None, description='User location info to improve web search accuracy'
    )

    @model_validator(mode='after')
    def check_length(self):
      if len((self.system_role or '') + (self.speaking_style or '')) > 4000:
        raise ValueError(
          'System role and speaking style combined length must not exceed 4000 characters'
        )
      return self

    class Extra(BaseModel):
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
      volc_websearch_type: Literal['web_summary', 'web_search'] = Field(
        default='web_summary', description='Volcengine integrated search type'
      )
      volc_websearch_api_key: str | None = Field(
        None, description='Volcengine integrated search API Key'
      )
      volc_websearch_result_count: int | None = Field(
        None,
        description='Volcengine integrated search result count, None defaults to 10',
        le=50,
      )
      volc_websearch_no_result_message: str | None = Field(
        None, description='Volcengine integrated search no result message'
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

    class Speaker(StrEnum):
      zh_female_vv_jupiter_bigtts = 'zh_female_vv_jupiter_bigtts'
      """vv voice: lively and energetic female voice with strong desire to share"""
      zh_female_xiaohe_jupiter_bigtts = 'zh_female_xiaohe_jupiter_bigtts'
      """xiaohe voice: sweet and lively female voice with noticeable Taiwan accent"""
      zh_male_yunzhou_jupiter_bigtts = 'zh_male_yunzhou_jupiter_bigtts'
      """yunzhou voice: fresh and steady male voice"""
      zh_male_xiaotian_jupiter_bigtts = 'zh_male_xiaotian_jupiter_bigtts'
      """xiaotian voice: fresh and magnetic male voice"""

    speaker: Speaker = Field(
      default=Speaker.zh_female_vv_jupiter_bigtts, description='Speaker voice'
    )

    audio_config: AudioConfig = Field(default_factory=AudioConfig)

  class Asr(BaseModel):
    class Extra(BaseModel):
      end_smooth_window_ms: int = Field(
        1500, description='End smooth window in milliseconds', ge=500
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


class ASRInfoResponse(BaseModel):
  """Response model for ASRInfo event - first word detection"""

  asr_task_id: str = Field(
    ..., description='ASR task ID for tracking and management'
  )
  question_id: str = Field(
    ..., description='Question ID associated with the ASR task'
  )
  round_id: int = Field(..., description='Round ID for the ASR session')


class ASRResponseModel(BaseModel):
  """Response model for ASRResponse event"""

  class Extra(BaseModel):
    """Extra information for ASR response"""

    endpoint: bool = Field(
      False, description='Indicates if the ASR has reached an endpoint'
    )
    interrupt_score: float = Field(
      ..., description='Score indicating interruption likelihood'
    )
    is_pvad: bool = Field(
      ..., description='Indicates if the response is from a PVAD model'
    )
    model_version: str = Field(..., description='Version of the ASR model used')
    origin_text: str = Field(..., description='Original text recognized by ASR')

    class ReqPayload(BaseModel):
      """Request payload parameters for ASR"""

      end_smooth_silence_proportion: float = Field(
        ..., description='Proportion of silence at the end of the audio'
      )
      eos_silence_timeout: int = Field(
        ..., description='End of speech silence timeout in milliseconds'
      )

    req_payload: ReqPayload = Field(
      ..., description='Request payload parameters for ASR'
    )

    class SoftFinishParalinguistic(BaseModel):
      """Soft finish paralinguistic information"""

      asr_text: str = Field(
        ..., description='ASR text recognized at soft finish'
      )
      para_resp: dict = Field(
        ..., description='Paralinguistic response information'
      )
      para_text: str = Field(
        ..., description='Paralinguistic text at soft finish'
      )

    soft_finish_paralinguistic: SoftFinishParalinguistic | None = Field(
      None, description='Soft finish paralinguistic information'
    )
    source: str = Field(..., description='Source of the ASR response')
    vad_backtrack_silence_time_ms: float = Field(
      0.0, description='VAD backtrack silence time in milliseconds'
    )

  class Result(BaseModel):
    class ResultAlternative(BaseModel):
      """Alternative results for ASR response"""

      end_time: float = Field(..., description='End time of the alternative')
      oi_decoding_info: dict = Field(
        default_factory=dict,
        description='OI decoding information for the alternative',
      )
      semantic_related_to_prev: bool | None = Field(
        None,
        description='Indicates if the alternative is semantically related to previous',
      )
      start_time: float = Field(
        ..., description='Start time of the alternative'
      )
      text: str = Field(..., description='Text recognized in the alternative')

    alternatives: list[ResultAlternative] = Field(
      ..., description='List of alternative results for ASR'
    )
    end_time: float = Field(..., description='End time of the result')
    index: int = Field(..., description='Index of the result in the list')
    is_interim: bool = Field(
      ..., description='Indicates if the result is interim'
    )
    is_vad_timeout: bool = Field(
      ..., description='Indicates if the result is due to VAD timeout'
    )
    start_time: float = Field(..., description='Start time of the result')
    text: str = Field(..., description='Text recognized in the result')

  extra: Extra = Field(
    ..., description='Extra information for the ASR response'
  )
  results: list[Result] = Field(
    ..., description='List of recognized results from ASR'
  )


class ASREndedResponse(BaseModel):
  """Response model for ASREnded event"""

  comfort_wait_time: int = Field(
    ..., description='Comfortable wait time in milliseconds'
  )
  last_resp_cost_time: int | None = Field(
    None, description='Time taken for the last response in milliseconds'
  )
  no_content: bool = Field(
    ..., description='Indicates if there was no content in the response'
  )
  task_request_seq_id: int = Field(
    ..., description='Sequence ID of the task request'
  )
  task_request_timestamp: int = Field(
    ..., description='Timestamp of the task request'
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

  error: str = Field(..., description='Error description')


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

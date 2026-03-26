"""Volcengine Text-to-Speech (TTS) schemas and utilities.

This module contains request/response models and helper functions for Volcengine's
TTS (Text-to-Speech) services, including bidirectional streaming TTS.
"""

import gzip
import logging
import struct
from enum import StrEnum
from typing import Literal, TypedDict

import orjson
from pydantic import (
  AliasChoices,
  BaseModel,
  Field,
  model_serializer,
  model_validator,
)

from .protocol import (
  CompressionMethod,
  EventReceive,
  EventSend,
  HeaderSize,
  MessageType,
  ProtocolVersion,
  SerializationMethod,
)


class TTSBigmodelResourceType(StrEnum):
  """Volcengine bigmodel TTS resource types (bidirectional streaming)"""

  seed_tts_1_0 = 'seed-tts-1.0'
  """Bigmodel TTS 1.0 character-based"""
  seed_tts_1_0_concurr = 'seed-tts-1.0-concurr'
  """Bigmodel TTS 1.0 concurrent"""
  seed_tts_2_0 = 'seed-tts-2.0'
  """Bigmodel TTS 2.0 character-based"""
  voice_clone_1_0 = 'seed-icl-1.0'
  """Voice cloning 1.0, character-based"""
  voice_clone_1_0_concurr = 'seed-icl-1.0-concurr'
  """Voice cloning 1.0, concurrent"""
  voice_clone_2_0 = 'seed-icl-2.0'
  """Voice cloning 2.0, character-based"""


class OperationEnum(StrEnum):
  """TTS operation types"""

  query = 'query'
  submit = 'submit'


class AppConfig(BaseModel):
  """Application configuration for TTS"""

  appid: str | None = None
  token: str
  cluster: str | None = None


class UserConfig(BaseModel):
  """User configuration for TTS"""

  uid: str


class TTSAudioFormat(StrEnum):
  """Audio formats supported by TTS"""

  wav = 'wav'  # only ok for single sentence
  pcm = 'pcm'  # ok for continuous streaming
  mp3 = 'mp3'
  ogg_opus = 'ogg_opus'

  @classmethod
  def list(cls):
    return [item.value for item in cls]


class AudioConfig(BaseModel):
  """Audio configuration for TTS"""

  voice_type: str = Field(..., description='Voice type')
  encoding: TTSAudioFormat = TTSAudioFormat.mp3
  speed_ratio: float = Field(1.0, description='Speech rate', ge=0.8, le=2.0)


class RequestConfig(BaseModel):
  """Request configuration for TTS"""

  reqid: str = Field(..., description='Unique request ID, recommend using UUID')
  text: str = Field(
    ..., description='Text to synthesize', min_length=1, max_length=1024
  )
  operation: OperationEnum = Field(
    OperationEnum.submit, description='Streaming or not'
  )

  class ExtraParam(BaseModel):
    disable_markdown_filter: bool = Field(
      True, description='Enable markdown filter disable'
    )
    enable_latex_tn: bool = Field(False, description='Enable LaTeX formula TTS')

    @model_validator(mode='wrap')
    def check(self: str, handler):
      if isinstance(self, str):
        self = orjson.loads(self)
      self: BaseModel = handler(self)
      if self.enable_latex_tn and not self.disable_markdown_filter:
        raise ValueError('enable_latex_tn requires disable_markdown_filter')
      return self

    @model_serializer(mode='wrap')
    def dump_json(self, _):
      return orjson.dumps(
        {
          'disable_markdown_filter': self.disable_markdown_filter,
          'enable_latex_tn': self.enable_latex_tn,
        }
      ).decode()

  extra_param: ExtraParam = Field(default_factory=ExtraParam)


class VolcengineTTSRequest(BaseModel):
  """TTS request model for standard API"""

  app: AppConfig = Field(..., description='Application config')
  user: UserConfig = Field(..., description='User config')
  audio: AudioConfig = Field(..., description='Audio config')
  request: RequestConfig = Field(..., description='Request config')


class TTSReqParams(BaseModel):
  """TTS request parameters"""

  class AudioParams(BaseModel):
    format: TTSAudioFormat = Field(
      TTSAudioFormat.mp3, description='Audio encoding format'
    )
    sample_rate: Literal[8000, 16000, 22050, 24000, 32000, 44100, 48000] = (
      Field(24000, description='Audio sample rate')
    )
    bit_rate: int | None = Field(None, description='Audio bit rate, mp3 only')
    emotion: str | None = Field(
      None, description='Emotion, multi-emotion voice support'
    )
    emotion_scale: int = Field(
      4,
      description='Emotion intensity, only effective when emotion is set',
      ge=1,
      le=5,
    )
    speech_rate: int = Field(
      0, description='Speech rate, 100=2.0x, -50=0.5x', ge=-50, le=100
    )
    loudness_rate: int = Field(
      0, description='Volume, 100=max volume, -50=0.5x volume', ge=-50, le=100
    )
    enable_timestamp: bool = Field(
      False, description='Return word and phoneme timestamps'
    )
    enable_subtitle: bool = Field(
      False, description='Return sentence-level subtitle timestamps'
    )

  class Additions(BaseModel):
    """Additional TTS parameters"""

    enable_language_detector: bool = Field(
      False, description='Enable language detection'
    )
    disable_markdown_filter: bool = Field(
      False, description='Enable markdown parsing and filtering when true'
    )
    silence_duration: int = Field(
      0, description='Ending silence duration, in ms', ge=0, le=30000
    )
    disable_emoji_filter: bool = Field(
      False, description='Disable emoji filter'
    )
    mute_cut_threshold: str | None = Field(
      None, description='Silence detection threshold', pattern=r'^\d+$'
    )
    mute_cut_remain_ms: str | None = Field(
      None, description='Silence cutting remain time, in ms', pattern=r'^\d+$'
    )
    enable_latex_tn: bool = Field(False, description='Enable LaTeX formula TTS')
    latex_parser: Literal['', 'v2'] = Field(
      '', description='LaTeX parser mode, set "v2" to enable LID parsing'
    )
    max_length_to_filter_parenthesis: int = Field(
      100,
      description='Max length to filter parenthesis text, no filter if exceeded',
      ge=0,
      le=100,
    )
    explicit_language: str | None = Field(None, description='Explicit language')
    context_language: str | None = Field(None, description='Reference language')
    unsupported_char_ratio_thresh: float = Field(
      0.3,
      ge=0.0,
      le=1.0,
      description='Unsupported char ratio threshold, error if exceeded',
    )
    aigc_watermark: bool = Field(
      False, description='Add audio rhythm watermark at end'
    )

    class AIGCMetadata(BaseModel):
      enable: bool = Field(False, description='Enable implicit watermark')
      content_producer: str = Field(
        '', description='TTS service provider name or code'
      )
      produce_id: str = Field('', description='Content production ID')
      content_propagator: str = Field(
        '', description='Content distribution service provider name or code'
      )
      propagate_id: str = Field('', description='Content distribution ID')

    AIGCMeta = AIGCMetadata

    aigc_metadata: AIGCMetadata | None = Field(
      None,
      description='Add metadata to audio header (implicit watermark), supports mp3/wav/ogg_opus',
      validation_alias=AliasChoices('aigc_metadata', 'aigc_meta'),
    )

    class CacheConfig(BaseModel):
      text_type: Literal[0, 1] = Field(
        1, description='Text type, 1=enable cache'
      )
      use_cache: bool = Field(True, description='Use cache')
      use_segment_cache: bool = Field(
        True,
        description='Use segment-level cache for better first packet latency',
      )

    cache_config: CacheConfig | None = Field(None, description='Cache config')

    class PostProcess(BaseModel):
      pitch: int = Field(0, description='Pitch', ge=-12, le=12)

    post_process: PostProcess | None = Field(
      None, description='Post-processing params'
    )

    context_texts: list[str] | None = Field(
      None, description='Context text, only first element is effective'
    )
    section_id: str = Field(
      '', description='Other TTS session ID to assist current synthesis'
    )
    use_tag_parser: bool = Field(False, description='Enable COT tag parser')

    @model_validator(mode='after')
    def check_markdown_dependent_options(self):
      if self.enable_latex_tn and not self.disable_markdown_filter:
        raise ValueError('enable_latex_tn requires disable_markdown_filter')
      if self.latex_parser == 'v2' and not self.disable_markdown_filter:
        raise ValueError('latex_parser=v2 requires disable_markdown_filter')
      return self

    @model_serializer(mode='wrap')
    def dump_json(self, handler):
      return orjson.dumps(handler(self)).decode()

  speaker: str = Field(..., description='Speaker')
  audio_params: AudioParams = Field(
    default_factory=AudioParams, description='Audio params'
  )
  additions: Additions | None = Field(None, description='User custom params')


class VolcengineTTSBidirectionRequest(BaseModel):
  """TTS request model for bidirectional streaming API"""

  class User(BaseModel):
    uid: str | None = Field(None, description='User UID')

  class ReqParams(TTSReqParams):
    text: str = Field(..., description='Text to synthesize')
    model: TTSBigmodelResourceType | None = Field(
      None, description='Model name'
    )

    class MixSpeaker(BaseModel):
      class Speaker(BaseModel):
        source_speaker: str = Field('', description='Voice type name')
        mix_factor: float = Field(0, description='Mix ratio', ge=0.0, le=1.0)

      speakers: list[Speaker] | None = Field(
        None, description='Mixed voice list'
      )

      @model_validator(mode='after')
      def check_mix_speaker(self):
        if self.speakers:
          mix_factor = sum(s.mix_factor for s in self.speakers)
          if mix_factor != 1.0:
            raise ValueError('mix_factor sum should be 1.0')
        return self

    mix_speaker: MixSpeaker | None = Field(
      None, description='Mixed voice config'
    )

  user: User | None = None
  event: EventSend | EventReceive
  req_params: ReqParams
  namespace: str = 'BidirectionalTTS'


class TTSSentenceStartResponse(BaseModel):
  """Response model for TTSSentenceStart event"""

  class TTSType(StrEnum):
    audit_content_risky = 'audit_content_risky'
    """Audit-flagged content audio"""
    chat_tts_text = 'chat_tts_text'
    """Customer text synthesis audio"""
    network = 'network'
    """Built-in network audio"""
    default = 'default'
    """Chat audio"""

  tts_type: TTSType | str = Field(
    TTSType.default,
    description='Synthesis audio type',
  )
  tts_task_id: str = Field(
    ..., description='TTS task ID for tracking and management'
  )
  model_type: str = Field(
    ..., description='Model type used for TTS, e.g., v3, v2'
  )
  enable_v3_loudness_balance: bool = Field(
    ..., description='Whether V3 loudness balance is enabled'
  )
  v3_loundness_params: str = Field(
    '', description='Parameters for V3 loudness balance, if applicable'
  )


class TTSSentenceEndResponse(BaseModel):
  """Response model for TTSSentenceEnd event"""

  silence_context: str = Field(...)
  speech_alignment_result: str = Field(...)
  text: str = Field(..., description='Text being synthesized')


class TTSSentenceEndWord(TypedDict):
  """Single aligned word entry emitted in sentence-end metadata."""

  confidence: float
  endTime: float
  startTime: float
  word: str


class TTSSentenceEndPayload(TypedDict):
  """Payload emitted in sentence-end subtitle metadata."""

  phonemes: list[str]
  text: str
  words: list[TTSSentenceEndWord]


class TTSEndResponse(BaseModel):
  """Response model for TTSEnded event"""

  no_content: bool = Field(
    True, description='Indicates if there is no content in the response'
  )


class VolcengineTTSFunctions:
  """Helper functions for Volcengine TTS API"""

  @staticmethod
  def prepare_request(
    submit_request_json: type[BaseModel] | dict, compression: bool = False
  ):
    """Prepare TTS request"""
    if not isinstance(submit_request_json, dict):
      submit_request_json = submit_request_json.model_dump()
    payload_bytes = orjson.dumps(submit_request_json)
    if compression:
      default_header = bytearray(b'\x11\x10\x11\x00')
      payload_bytes = gzip.compress(payload_bytes)
    else:
      default_header = bytearray(b'\x11\x10\x10\x00')

    full_client_request = bytearray(default_header)
    # payload size(4 bytes)
    full_client_request.extend((len(payload_bytes)).to_bytes(4, 'big'))
    # payload
    full_client_request.extend(payload_bytes)
    return full_client_request

  @staticmethod
  def task_request_payload(
    session_id: str, text: str, speaker: str, audio_params: dict
  ) -> bytes:
    """Create TaskRequest event payload"""
    req = {
      'event': EventSend.TaskRequest.value,
      'namespace': 'BidirectionalTTS',
      'req_params': {
        'text': text,
        'speaker': speaker,
        'audio_params': audio_params,
      },
    }
    return VolcengineTTSFunctions.calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.TaskRequest,
      session_id=session_id,
      request_meta=req,
    )

  @staticmethod
  def extract_response_payload(data: bytes) -> tuple:
    """Extract TTS response payload"""
    if not isinstance(data, bytes):
      logging.error('data must be bytes %s', data)
      raise ValueError('data must be bytes')
    # Parse header
    if len(data) < 8:
      raise ValueError('Data too short')

    # Extract protocol version and header size
    header_byte = data[0]
    protocol_version = (header_byte >> 4) & 0b1111
    header_size = header_byte & 0b1111

    # Check protocol version and header size
    try:
      protocol_version = ProtocolVersion(protocol_version)
    except ValueError:
      logging.warning('unknown protocol %r', protocol_version)
    else:
      if protocol_version != ProtocolVersion.V1:
        logging.warning('Protocol version mismatch %s', protocol_version)

    if HeaderSize(header_size) != HeaderSize.SIZE_4:
      logging.warning('Header size mismatch %s', header_size)

    # Extract message type and specific flags
    message_type_byte = data[1]
    message_type = (message_type_byte >> 4) & 0b1111
    message_type = MessageType(message_type)

    # Extract serialization method and compression method
    serialization_byte = data[2]
    serialization_method = (serialization_byte >> 4) & 0b1111
    compression_method = serialization_byte & 0b1111
    compression_method = CompressionMethod(compression_method)

    # Reserved field (can be ignored)
    _reserved = data[3]

    # Parse optional fields
    optional_data = data[4:8]

    if message_type in (
      MessageType.FULL_SERVER_RESPONSE,
      MessageType.AUDIO_ONLY_RESPONSE,
      MessageType.FULL_CLIENT_REQUEST,
      MessageType.ERROR_INFORMATION,
    ):
      event_number = struct.unpack('>I', optional_data)[0]
    else:
      raise NotImplementedError(f'Unsupported message type: {message_type}')
    try:
      event = EventReceive(event_number)
    except ValueError:
      logging.warning('unknown event number %d', event_number)
      event = event_number

    # Extract session id
    session_end = 12 + struct.unpack('>I', data[8:12])[0]
    session_id = data[12:session_end].decode()

    # Extract payload
    # NOTICE: for sentence start and end, the payload length is calculated in unicode length, not bytes length
    payload = data[session_end + 4 :]

    if not payload:
      return event, session_id, payload
    # Deserialize based on serialization method (if JSON)
    serialization_method = SerializationMethod(serialization_method)
    if serialization_method == SerializationMethod.JSON:
      match event:
        case EventReceive.TTSSentenceStart:
          # NOTICE: invalid json
          return event, session_id, payload
        case EventReceive.TTSSentenceEnd:
          # NOTICE: invalid json
          return event, session_id, payload
        case _:
          try:
            return event, session_id, orjson.loads(payload)
          except Exception:
            logging.exception('json loads error: %s', payload)
    elif serialization_method == SerializationMethod.RAW:
      return event, session_id, payload
    else:
      raise NotImplementedError(
        f'Unsupported serialization method: {serialization_method}'
      )

  @staticmethod
  def calculate_payload(
    message_type: MessageType,
    event: EventSend,
    session_id: str | None = None,
    request_meta: dict | None = None,
  ) -> bytes:
    """Calculate payload for TTS request"""
    # Header
    header = [
      (ProtocolVersion.V1.value << 4)
      | HeaderSize.SIZE_4.value,  # Protocol version + header size
      (message_type.value << 4) | 0b0100,  # Message type + specific flags
      (SerializationMethod.JSON.value << 4)
      | CompressionMethod.NONE.value,  # Serialization method + compression
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

  @staticmethod
  def start_connection_payload() -> bytes:
    """Create StartConnection event payload"""
    return VolcengineTTSFunctions.calculate_payload(
      MessageType.FULL_CLIENT_REQUEST, EventSend.StartConnection
    )

  @staticmethod
  def start_session_payload(
    session_id: str, req_params: dict, user_info: dict | None = None
  ) -> bytes:
    """Create StartSession event payload"""
    req = {
      'req_params': req_params,
      'namespace': 'BidirectionalTTS',
      'event': EventSend.StartSession.value,
    }
    if user_info:
      req['user'] = user_info
    return VolcengineTTSFunctions.calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.StartSession,
      session_id=session_id,
      request_meta=req,
    )

  @staticmethod
  def finish_session_payload(session_id: str) -> bytes:
    """Create FinishSession event payload"""
    return VolcengineTTSFunctions.calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.FinishSession,
      session_id=session_id,
      request_meta={},
    )

  @staticmethod
  def cancel_session_payload(session_id: str) -> bytes:
    """Create CancelSession event payload"""
    return VolcengineTTSFunctions.calculate_payload(
      MessageType.FULL_CLIENT_REQUEST,
      EventSend.CancelSession,
      session_id=session_id,
      request_meta={},
    )

  @staticmethod
  def finish_connection_payload() -> bytes:
    """Create FinishConnection event payload"""
    return VolcengineTTSFunctions.calculate_payload(
      MessageType.FULL_CLIENT_REQUEST, EventSend.FinishConnection
    )

  class SessionFinishedPayload(BaseModel):
    """SessionFinished event payload"""

    status_code: int | None = None
    message: str | None = None

    class Usage(BaseModel):
      text_words: int

    usage: Usage | None = None

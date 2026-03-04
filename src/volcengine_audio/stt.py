"""Volcengine Speech-to-Text (STT) schemas and utilities.

This module contains request/response models and helper functions for Volcengine's
ASR (Automatic Speech Recognition) services, supporting both V2 and V3 APIs.
"""

import gzip
import struct
from enum import StrEnum
from typing import Literal

import orjson
from pydantic import (
  AliasChoices,
  BaseModel,
  ConfigDict,
  Field,
  NonNegativeInt,
  PositiveInt,
  model_serializer,
  model_validator,
)

from .protocol import (
  AsrMessageType,
  AsrMessageTypeSpecificFlag,
  AudioCodec,
  CompressionMethod,
  ProtocolVersion,
  SerializationMethod,
  generate_before_payload,
)


class STTResource(StrEnum):
  """STT resource types for billing"""

  duration_1_0 = 'volc.bigasr.sauc.duration'
  concurrent_1_0 = 'volc.bigasr.sauc.concurrent'
  duration_2_0 = 'volc.seedasr.sauc.duration'
  concurrent_2_0 = 'volc.seedasr.sauc.concurrent'


class STTAudioFormatV3(StrEnum):
  """Audio formats supported by STT V3"""

  pcm = 'pcm'  # pcm_s16le
  wav = 'wav'  # pcm_s16le
  mp3 = 'mp3'
  ogg = 'ogg'


class AudioFormatV2(StrEnum):
  """Audio formats supported by STT V2"""

  raw = 'raw'
  wav = 'wav'
  mp3 = 'mp3'
  ogg = 'ogg'


class STTResultType(StrEnum):
  """Result type for STT responses"""

  full = 'full'
  single = 'single'


class STTBigmodelNoStreamLanguage(StrEnum):
  """Language codes for bigmodel non-streaming STT.

  When empty, supports Chinese, English, Shanghai dialect, Minnan, Sichuan, Shaanxi, and Cantonese.
  """

  zh_CN = 'zh-CN'  # Chinese (Mandarin)
  en_US = 'en-US'  # English
  ja_JP = 'ja-JP'  # Japanese
  id_ID = 'id-ID'  # Indonesian
  es_MX = 'es-MX'  # Spanish
  pt_BR = 'pt-BR'  # Portuguese
  de_DE = 'de-DE'  # German
  fr_FR = 'fr-FR'  # French
  ko_KR = 'ko-KR'  # Korean
  fil_PH = 'fil-PH'  # Filipino
  ms_MY = 'ms-MY'  # Malay
  th_TH = 'th-TH'  # Thai
  ar_SA = 'ar-SA'  # Arabic


class VolcengineAsrRequestV3(BaseModel):
  """ASR request model for V3 API"""

  class User(BaseModel):
    uid: str | None = Field(None, description='User identifier')
    did: str | None = Field(None, description='Device name')
    platform: str | None = Field(None, description='OS and API version')
    sdk_version: str | None = Field(None, description='SDK version')
    app_version: str | None = Field(None, description='App version')

  class Audio(BaseModel):
    format: STTAudioFormatV3 = Field(
      STTAudioFormatV3.wav, description='Audio container format'
    )
    codec: AudioCodec = Field(
      AudioCodec.raw, description='Audio encoding format'
    )
    rate: Literal[16000] = Field(16000, description='Audio sample rate')
    bits: Literal[16] = Field(16, description='Audio bit depth')
    channel: Literal[1, 2] = Field(1, description='Audio channels')
    language: STTBigmodelNoStreamLanguage | Literal[''] | None = Field(
      None, description='Recognition language, mainly for non-streaming mode'
    )

  class Request(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    class Corpus(BaseModel):
      boosting_table_name: str | None = Field(
        None, description='Hot word table name from self-learning platform'
      )
      boosting_table_id: str | None = Field(
        None, description='Hot word table ID from self-learning platform'
      )
      correct_table_name: str | None = Field(
        None,
        description='Replacement word table name from self-learning platform',
      )
      correct_table_id: str | None = Field(
        None,
        description='Replacement word table ID from self-learning platform',
      )

      class Context(BaseModel):
        class Hotword(BaseModel):
          word: str = Field(..., description='Hot word')

        hotwords: list[Hotword] = Field(
          default_factory=list, description='Hot word list'
        )
        context_type: Literal['dialog_ctx'] | None = Field(
          None, description='Context type'
        )

        class ContentDataText(BaseModel):
          text: str = Field(..., description='Context text')

        class ContentDataImage(BaseModel):
          image_url: str = Field(..., description='Context image URL')

        class ContentDataLocation(BaseModel):
          class City(BaseModel):
            city_name: str

          loc_info: City = Field(..., description='City information')

        content_data: list[
          ContentDataText | ContentDataImage | ContentDataLocation
        ] = Field(default_factory=list, description='Context data')

        @model_serializer(mode='wrap')
        def dump_json(self, handler):
          return orjson.dumps(handler(self)).decode()

      context: Context | None = Field(
        None,
        description='Context text: 100 chars for streaming, 5000 for non-streaming',
      )

    model_name: str = Field('bigmodel', description='Model name')
    enable_itn: bool = Field(
      True, description='Enable inverse text normalization'
    )
    enable_punc: bool = Field(True, description='Enable punctuation')
    enable_ddc: bool = Field(False, description='Enable smoothing')
    enable_nonstream: bool = Field(
      False,
      description='Enable streaming + non-streaming dual recognition',
      validation_alias=AliasChoices('enable_nonstream', 'enable_nostream'),
    )
    show_utterances: bool = Field(
      False, description='Output pause, sentence, and word segmentation info'
    )
    show_speech_rate: bool = Field(
      False,
      description='Output speech rate info (bigmodel_nostream & bigmodel_async only)',
    )
    show_volume: bool = Field(
      False,
      description='Output volume info in additions (nostream and optimized bidirectional only)',
    )
    enable_lid: bool = Field(
      False,
      description='Enable language identification (bigmodel_nostream & bigmodel_async only)',
    )
    enable_emotion_detection: bool = Field(
      False,
      description='Enable emotion detection (bigmodel_nostream & bigmodel_async only)',
    )
    enable_gender_detection: bool = Field(
      False,
      description='Enable gender detection (bigmodel_nostream & bigmodel_async only)',
    )
    result_type: STTResultType = Field(
      STTResultType.full, description='Result type'
    )
    enable_accelerate_text: bool = Field(
      False,
      description='Enable first word acceleration (reduces accuracy)',
    )
    accelerate_score: NonNegativeInt = Field(
      0, description='First word acceleration score, higher = faster', le=20
    )
    vad_segment_duration: PositiveInt = Field(
      3000, description='Max silence threshold for semantic segmentation, in ms'
    )
    end_window_size: int = Field(
      800, description='End window size, in ms', ge=200
    )
    force_to_speech_time: PositiveInt = Field(
      10000, description='Force return audio timestamp, min 1 ms'
    )

    class SensitiveWordsFilter(BaseModel):
      system_reserved_filter: bool = Field(
        False,
        description='Use system sensitive words (replaced with *)',
      )
      filter_with_empty: list[str] = Field(
        default_factory=list,
        description='Sensitive words to replace with empty string',
      )
      filter_with_signed: list[str] = Field(
        default_factory=list, description='Sensitive words to replace with *'
      )

      @model_serializer(mode='wrap')
      def dump_json(self, handler):
        return orjson.dumps(handler(self)).decode()

    sensitive_words_filter: SensitiveWordsFilter | None = Field(
      None, description='Sensitive words filter'
    )
    enable_poi_fc: bool = Field(False, description='Enable POI recognition')
    enable_music_fc: bool = Field(False, description='Enable music recognition')
    corpus: Corpus | None = Field(None, description='Corpus/intervention words')

  user: User = Field(default_factory=User)
  audio: Audio = Field(default_factory=Audio)
  request: Request | None = Field(None)


class VolcengineAsrRequestV2(BaseModel):
  """ASR request model for V2 API"""

  class App(BaseModel):
    appid: str = Field(..., description='Application identifier')
    token: str = Field(..., description='Application token')
    cluster: str | None = Field(None, description='Business cluster')

  class User(BaseModel):
    uid: str = Field(..., description='User identifier')
    device: str | None = Field(None, description='Device name')
    platform: str | None = Field(None, description='OS and API version')
    network: str | None = Field(None, description='User network')
    nation: str | None = Field(None, description='Country')
    province: str | None = Field(None, description='Province')
    city: str | None = Field(None, description='City')

  class Audio(BaseModel):
    format: STTAudioFormatV3 = Field(
      AudioFormatV2.wav, description='Audio container format'
    )
    codec: AudioCodec = Field(
      AudioCodec.raw, description='Audio encoding format'
    )
    rate: int = Field(16000, description='Audio sample rate')
    bits: int = Field(16, description='Audio bit depth')
    channel: int = Field(1, description='Audio channels')

  class Request(BaseModel):
    reqid: str = Field(..., description='Request identifier')
    sequence: int | None = Field(None, description='Request sequence number')
    nbest: int | None = Field(1, description='Number of recognition candidates')
    confidence: int | None = Field(0, description='Confidence lower bound')
    workflow: str | None = Field(
      'audio_in,resample,partition,vad,fe,decode', description='Custom workflow'
    )
    show_utterances: bool | None = Field(
      False, description='Output pause, sentence, and word segmentation info'
    )
    result_type: STTResultType | None = Field(
      STTResultType.full, description='Result type'
    )
    boosting_table_name: str | None = Field(
      None, description='Hot word table name from self-learning platform'
    )
    correct_table_name: str | None = Field(
      None,
      description='Replacement word table name from self-learning platform',
    )

  app: App = Field(..., description='Application config')
  user: User = Field(..., description='User config')
  audio: Audio = Field(..., description='Audio config')
  request: Request = Field(..., description='Request config')


class AsrFullServerResponseV2(BaseModel):
  """ASR V2 full server response"""

  is_last_package: bool

  class Message(BaseModel):
    code: int
    message: str
    reqid: str
    sequence: int = 0
    backend_code: int = 0

    class Addition(BaseModel):
      duration: int
      logid: str
      split_time: str | None = None

    addition: Addition | None = None

    class Result(BaseModel):
      text: str
      confidence: int

      class Utterance(BaseModel):
        definite: bool = False
        end_time: int = Field(..., description='end_time in ms')
        start_time: int = Field(..., description='start_time in ms')
        text: str

        class Word(BaseModel):
          start: int = Field(0, description='start_time in ms')
          start_time: int = Field(0, description='start_time in ms')
          end: int = Field(0, description='end_time in ms')
          end_time: int = Field(0, description='end_time in ms')
          text: str
          blank_duration: int = Field(
            0,
            description='Silence duration',
            validation_alias=AliasChoices('blank_duration', 'black_duration'),
          )

          @property
          def start_ms(self) -> int:
            return self.start or self.start_time

          @property
          def end_ms(self) -> int:
            return self.end or self.end_time

        words: list[Word] = Field(default_factory=list)

      utterances: list[Utterance] | None = None

    result: list[Result] = Field(default_factory=list)

  message: Message
  size: int
  code: int = 1000

  @model_validator(mode='after')
  def set_last_package(self):
    """Set last package flag"""
    if self.message.sequence and self.message.sequence < 0:
      self.is_last_package = True
    return self


class ListenBidirectionPackage(BaseModel):
  """Bidirectional listening package"""

  is_last_package: bool
  sequence: int

  class Message(BaseModel):
    class AudioInfo(BaseModel):
      duration: int = Field(
        ..., description='Audio duration in ms, accumulated'
      )

    audio_info: AudioInfo

    class Result(BaseModel):
      text: str
      confidence: int | None = None

      class Utterance(BaseModel):
        definite: bool = False
        end_time: int = Field(..., description='end_time in ms')
        start_time: int = Field(..., description='start_time in ms')
        text: str

        class Word(BaseModel):
          start: int = Field(0, description='start_time in ms')
          start_time: int = Field(0, description='start_time in ms')
          end: int = Field(0, description='end_time in ms')
          end_time: int = Field(0, description='end_time in ms')
          blank_duration: int = Field(
            0,
            description='Silence duration',
            validation_alias=AliasChoices('blank_duration', 'black_duration'),
          )
          text: str

          @property
          def start_ms(self) -> int:
            return self.start or self.start_time

          @property
          def end_ms(self) -> int:
            return self.end or self.end_time

        words: list[Word] = Field(default_factory=list)

      utterances: list[Utterance] | None = None

      class Additions(BaseModel):
        log_id: str

      additions: Additions

    result: Result

  message: Message
  size: int


class VolcengineAsrFunctionsV3:
  """Helper functions for Volcengine ASR V3 API"""

  @staticmethod
  def generate_asr_header(
    message_type: AsrMessageType = AsrMessageType.FULL_CLIENT_REQUEST,
    message_type_specific_flags: AsrMessageTypeSpecificFlag = AsrMessageTypeSpecificFlag.NO_SEQUENCE,
    serial_method: SerializationMethod = SerializationMethod.JSON,
    compression_type: CompressionMethod = CompressionMethod.NONE,
    reserved_data=0x00,
  ) -> bytearray:
    """Generate ASR V3 header.

    https://www.volcengine.com/docs/6561/1324606

    Header structure:
    - protocol_version(4 bits), header_size(4 bits)
    - message_type(4 bits), message_type_specific_flags(4 bits)
    - serialization_method(4 bits), message_compression(4 bits)
    - reserved(8 bits)
    """
    header = bytearray()
    header_size = 1
    header.append((ProtocolVersion.V1.value << 4) | header_size)
    header.append((message_type.value << 4) | message_type_specific_flags.value)
    header.append((serial_method.value << 4) | compression_type.value)
    header.append(reserved_data)
    return header

  @staticmethod
  def generate_asr_before_payload(sequence: int) -> bytearray:
    """Generate sequence number before payload"""
    return generate_before_payload(sequence)

  @staticmethod
  def generate_asr_full_client_request(
    sequence: int, request_params: dict, compression: bool
  ) -> bytearray:
    """Generate full client request for ASR V3"""
    payload_bytes = orjson.dumps(request_params)
    if compression:
      payload_bytes = gzip.compress(payload_bytes)
      full_client_request = bytearray(
        VolcengineAsrFunctionsV3.generate_asr_header(
          message_type_specific_flags=AsrMessageTypeSpecificFlag.POS_SEQUENCE,
          compression_type=CompressionMethod.GZIP,
        )
      )
    else:
      full_client_request = bytearray(
        VolcengineAsrFunctionsV3.generate_asr_header(
          message_type_specific_flags=AsrMessageTypeSpecificFlag.POS_SEQUENCE
        )
      )
    full_client_request.extend(
      VolcengineAsrFunctionsV3.generate_asr_before_payload(sequence=sequence)
    )
    full_client_request.extend(struct.pack('>I', len(payload_bytes)))
    full_client_request.extend(payload_bytes)
    return full_client_request

  @staticmethod
  def parse_request(data: bytes) -> dict:
    """Parse ASR V3 request"""
    header_size = data[0] & 0x0F
    message_type = data[1] >> 4
    message_type_specific_flags = data[1] & 0x0F
    serialization_method = data[2] >> 4
    message_compression = data[2] & 0x0F
    payload = data[header_size * 4 :]
    result = {}
    # Check sequence flag
    if message_type_specific_flags & 0x01:
      sequence = struct.unpack('>i', payload[:4])[0]
      result['sequence'] = sequence
      payload = payload[4:]
    # Parse payload
    if message_type == AsrMessageType.FULL_CLIENT_REQUEST.value:
      payload_msg = payload[4:]
      if message_compression == CompressionMethod.GZIP.value:
        payload_msg = gzip.decompress(payload_msg)
      if serialization_method == SerializationMethod.JSON.value:
        payload_msg = orjson.loads(payload_msg)
      elif serialization_method != SerializationMethod.RAW.value:
        payload_msg = str(payload_msg)
      result = payload_msg
    return result

  @staticmethod
  def generate_asr_audio_only_request(
    sequence: int,
    audio: bytes,
    compress: bool = True,
    keep_sequence: bool = False,
  ) -> bytearray:
    """Generate audio only request.

    Empty audio means the last one, if not keep_sequence.
    """
    if not keep_sequence and not audio and sequence > 0:
      sequence = -sequence
      compress = False
    if compress:
      audio = gzip.compress(audio)
    audio_only_request = bytearray(
      VolcengineAsrFunctionsV3.generate_asr_header(
        message_type=AsrMessageType.AUDIO_ONLY_REQUEST,
        message_type_specific_flags=AsrMessageTypeSpecificFlag.POS_SEQUENCE
        if (sequence > 0)
        else AsrMessageTypeSpecificFlag.NEG_WITH_SEQUENCE,
        compression_type=CompressionMethod.GZIP
        if compress
        else CompressionMethod.NONE,
      )
    )
    audio_only_request.extend(
      VolcengineAsrFunctionsV3.generate_asr_before_payload(sequence)
    )
    audio_only_request.extend(struct.pack('>I', len(audio)))
    audio_only_request.extend(audio)
    return audio_only_request

  @staticmethod
  def parse_response(res: bytes):
    """Parse ASR V3 response"""
    header_size = res[0] & 0x0F
    message_type = res[1] >> 4
    message_type_specific_flags = res[1] & 0x0F
    serialization_method = res[2] >> 4
    message_compression = res[2] & 0x0F
    payload = res[header_size * 4 :]
    result = {
      'is_last_package': False,
    }
    payload_msg = None
    payload_size = 0
    # Check sequence flag
    if message_type_specific_flags & 0x01:
      sequence = struct.unpack('>i', payload[:4])[0]
      result['sequence'] = sequence
      payload = payload[4:]
    if message_type_specific_flags & 0x02:
      result['is_last_package'] = True
    # Parse payload
    if message_type == AsrMessageType.FULL_SERVER_RESPONSE.value:
      payload_size = struct.unpack('>i', payload[:4])[0]
      payload_msg = payload[4:]
    elif message_type == AsrMessageType.SERVER_ACK.value:
      sequence = struct.unpack('>i', payload[:4])[0]
      result['sequence'] = sequence
      if len(payload) >= 8:
        payload_size = struct.unpack('>I', payload[4:8])[0]
        payload_msg = payload[8:]
    elif message_type == AsrMessageType.SERVER_ERROR_RESPONSE.value:
      code = struct.unpack('>I', payload[:4])[0]
      result['code'] = code
      payload_size = struct.unpack('>I', payload[4:8])[0]
      payload_msg = payload[8:]

    if payload_msg is None:
      return result
    if message_compression == CompressionMethod.GZIP.value:
      payload_msg = gzip.decompress(payload_msg)
    if serialization_method == SerializationMethod.JSON.value:
      payload_msg = orjson.loads(payload_msg)
    elif serialization_method != SerializationMethod.RAW.value:
      payload_msg = str(payload_msg)
    result['message'] = payload_msg
    result['size'] = payload_size
    return result


class VolcengineAsrFunctionsV2(VolcengineAsrFunctionsV3):
  """Helper functions for Volcengine ASR V2 API"""

  @staticmethod
  def full_client_request(
    request_params: dict, compression: bool = True
  ) -> bytearray:
    """Generate full client request for ASR V2"""
    payload_bytes = orjson.dumps(request_params)
    if compression:
      payload_bytes = gzip.compress(payload_bytes)
      full_client_request = VolcengineAsrFunctionsV3.generate_asr_header(
        message_type_specific_flags=AsrMessageTypeSpecificFlag.NO_SEQUENCE,
        compression_type=CompressionMethod.GZIP,
      )
    else:
      full_client_request = VolcengineAsrFunctionsV3.generate_asr_header(
        message_type_specific_flags=AsrMessageTypeSpecificFlag.NO_SEQUENCE
      )
    full_client_request.extend(struct.pack('>I', len(payload_bytes)))
    full_client_request.extend(payload_bytes)
    return full_client_request

  @staticmethod
  def audio_only_request(
    audio: bytes,
    compress: bool = True,
    last: bool = False,
  ) -> bytearray:
    """Generate audio only request for ASR V2"""
    if last:
      flag = AsrMessageTypeSpecificFlag.NEG_SEQUENCE
    else:
      flag = AsrMessageTypeSpecificFlag.NO_SEQUENCE
    if compress:
      audio = gzip.compress(audio)
    audio_only_request = VolcengineAsrFunctionsV3.generate_asr_header(
      message_type=AsrMessageType.AUDIO_ONLY_REQUEST,
      message_type_specific_flags=flag,
      compression_type=CompressionMethod.GZIP
      if compress
      else CompressionMethod.NONE,
    )
    audio_only_request.extend(struct.pack('>I', len(audio)))
    audio_only_request.extend(audio)
    return audio_only_request

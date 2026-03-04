"""Volcengine audio protocol definitions.

This module contains shared protocol definitions used by both TTS and STT services,
including message types, serialization methods, and communication protocols.
"""

import struct
from enum import Enum, IntEnum

HOST = 'openspeech.bytedance.com'
"""Volcengine audio service host"""


class ProtocolVersion(Enum):
  """Protocol version for Volcengine audio services"""

  V1 = 0b0001


class HeaderSize(Enum):
  """Header size in 32-bit words"""

  SIZE_4 = 0b0001  # 4 bytes


class MessageType(Enum):
  """Message types for bidirectional communication"""

  FULL_CLIENT_REQUEST = 0b0001
  AUDIO_ONLY_REQUEST = 0b0010
  FULL_SERVER_RESPONSE = 0b1001
  AUDIO_ONLY_RESPONSE = 0b1011
  ERROR_INFORMATION = 0b1111


class MessageTypeSpecificFlag(Enum):
  """Flags for message type specific information"""

  NO_SEQUENCE = 0b0000
  POS_SEQUENCE = 0b0001
  NEG_SEQUENCE = 0b0010
  NEG_WITH_SEQUENCE = 0b0011
  CARRY_EVENT_ID = 0b0100


class SerializationMethod(Enum):
  """Serialization methods for message payloads"""

  RAW = 0b0000
  JSON = 0b0001
  PROTOBUF = 0b0010
  THRFT = 0b0011


class CompressionMethod(Enum):
  """Compression methods for message payloads"""

  NONE = 0b0000
  GZIP = 0b0001


class AudioCodec(Enum):
  """Audio codec types"""

  raw = 'raw'
  opus = 'opus'  # for ogg


class AsrMessageType(Enum):
  """Message types specific to ASR (speech recognition)"""

  FULL_CLIENT_REQUEST = 0b0001
  AUDIO_ONLY_REQUEST = 0b0010
  FULL_SERVER_RESPONSE = 0b1001
  SERVER_ACK = 0b1011
  SERVER_ERROR_RESPONSE = 0b1111


class AsrMessageTypeSpecificFlag(Enum):
  """Flags specific to ASR message types"""

  # requests
  # full client request or non-last audio only request
  NO_SEQUENCE = 0b0000
  POS_SEQUENCE = 0b0001
  # last audio only request without sequence
  NEG_SEQUENCE = 0b0010
  # last audio only request with sequence
  NEG_WITH_SEQUENCE = 0b0011
  # responses
  # full client response or non-last audio only response
  NEG_SEQUENCE_1 = 0b0011


class EventSend(IntEnum):
  """Events sent from client to server"""

  StartConnection = 1
  FinishConnection = 2
  StartSession = 100
  CancelSession = 101
  FinishSession = 102
  TaskRequest = 200
  SayHello = 300
  ChatTTSText = 500
  ChatTextQuery = 501


class EventReceive(IntEnum):
  """Events received from server"""

  ConnectionStarted = 50
  ConnectionFailed = 51
  ConnectionFinished = 52
  SessionStarted = 150
  SessionCanceled = 151
  SessionFinished = 152
  SessionFailed = 153
  USAGE = 154
  TTSSentenceStart = 350
  TTSSentenceEnd = 351
  TTSResponse = 352
  TTSEnded = 359
  ASRInfo = 450
  ASRResponse = 451
  ASREnded = 459
  ChatResponse = 550
  ChatEnded = 559
  # TODO(Deo): need to check what this code is, in tts
  UNKNOWN = 50000000
  # TODO(Deo): need to check what this code is, in dialogue
  UNKNOWN1 = 55000000
  SERVER_PROCESSING_ERROR = 55000001
  SERVICE_UNAVAILABLE = 55000030
  AUDIO_FLOW_ERROR = 55002070


def generate_header(
  message_type: MessageType = MessageType.FULL_CLIENT_REQUEST,
  message_type_specific_flags: MessageTypeSpecificFlag = MessageTypeSpecificFlag.NO_SEQUENCE,
  serial_method: SerializationMethod = SerializationMethod.JSON,
  compression_type: CompressionMethod = CompressionMethod.NONE,
  reserved_data: int = 0x00,
) -> bytearray:
  """Generate protocol header for Volcengine audio services.

  Args:
      message_type: Type of message being sent
      message_type_specific_flags: Specific flags for the message type
      serial_method: Serialization method for payload
      compression_type: Compression method for payload
      reserved_data: Reserved byte (default 0x00)

  Returns:
      4-byte header as bytearray

  Header structure:
      - Byte 0: protocol_version(4 bits), header_size(4 bits)
      - Byte 1: message_type(4 bits), message_type_specific_flags(4 bits)
      - Byte 2: serialization_method(4 bits), message_compression(4 bits)
      - Byte 3: reserved(8 bits)
  """
  header = bytearray()
  header_size = 1
  header.append((ProtocolVersion.V1.value << 4) | header_size)
  header.append((message_type.value << 4) | message_type_specific_flags.value)
  header.append((serial_method.value << 4) | compression_type.value)
  header.append(reserved_data)
  return header


def generate_before_payload(sequence: int) -> bytearray:
  """Generate sequence number before payload.

  Args:
      sequence: Sequence number (signed 32-bit integer)

  Returns:
      4-byte sequence as bytearray
  """
  before_payload = bytearray()
  before_payload.extend(struct.pack('>i', sequence))
  return before_payload

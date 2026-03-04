"""Volcengine Audio SDK for Speech-to-Text and Text-to-Speech services.

This package provides Python models and utilities for interacting with Volcengine's
audio services including STT (Speech-to-Text), TTS (Text-to-Speech), and realtime
dialogue capabilities.

Modules:
    - protocol: Shared protocol definitions and event types
    - stt: Speech-to-Text (ASR) models and helpers
    - tts: Text-to-Speech models and helpers
    - realtime: Realtime dialogue (combined STT+TTS) models and helpers

Example:
    >>> from volcengine_audio import VolcengineAsrRequestV3, VolcengineTTSRequest
    >>> from volcengine_audio import RealtimeDialogueConfig, HOST
"""

__version__ = '0.1.0'

# Protocol exports
from .protocol import (
  HOST,
  AsrMessageType,
  AsrMessageTypeSpecificFlag,
  AudioCodec,
  CompressionMethod,
  EventReceive,
  EventSend,
  HeaderSize,
  MessageType,
  MessageTypeSpecificFlag,
  ProtocolVersion,
  SerializationMethod,
  generate_before_payload,
  generate_header,
)

# Realtime dialogue exports
from .realtime import (
  ASREndedResponse,
  ASRInfoResponse,
  ASRResponseModel,
  ChatResponseModel,
  ChatTextQueryRequest,
  ChatTTSTextRequest,
  ConnectionFailedResponse,
  RealtimeDialogueConfig,
  RealtimeDialogueErrorResponse,
  RealtimeDialogueFunctions,
  RealtimeDialogueUsage,
  SayHelloRequest,
  SessionFailedResponse,
  SessionStartedResponse,
)

# STT exports
from .stt import (
  AsrFullServerResponseV2,
  AudioFormatV2,
  ListenBidirectionPackage,
  STTAudioFormatV3,
  STTBigmodelNoStreamLanguage,
  STTResource,
  STTResultType,
  VolcengineAsrFunctionsV2,
  VolcengineAsrFunctionsV3,
  VolcengineAsrRequestV2,
  VolcengineAsrRequestV3,
)

# TTS exports
from .tts import (
  AppConfig,
  AudioConfig,
  OperationEnum,
  RequestConfig,
  TTSAudioFormat,
  TTSBigmodelResourceType,
  TTSEndResponse,
  TTSReqParams,
  TTSSentenceEndResponse,
  TTSSentenceStartResponse,
  UserConfig,
  VolcengineTTSBidirectionRequest,
  VolcengineTTSFunctions,
  VolcengineTTSRequest,
)

__all__ = [
  # Version
  '__version__',
  # Constants
  'HOST',
  # Protocol
  'AsrMessageType',
  'AsrMessageTypeSpecificFlag',
  'AudioCodec',
  'CompressionMethod',
  'EventReceive',
  'EventSend',
  'HeaderSize',
  'MessageType',
  'MessageTypeSpecificFlag',
  'ProtocolVersion',
  'SerializationMethod',
  'generate_before_payload',
  'generate_header',
  # STT
  'AsrFullServerResponseV2',
  'AudioFormatV2',
  'ListenBidirectionPackage',
  'STTAudioFormatV3',
  'STTBigmodelNoStreamLanguage',
  'STTResource',
  'STTResultType',
  'VolcengineAsrFunctionsV2',
  'VolcengineAsrFunctionsV3',
  'VolcengineAsrRequestV2',
  'VolcengineAsrRequestV3',
  # TTS
  'AppConfig',
  'AudioConfig',
  'OperationEnum',
  'RequestConfig',
  'TTSAudioFormat',
  'TTSBigmodelResourceType',
  'TTSEndResponse',
  'TTSReqParams',
  'TTSSentenceEndResponse',
  'TTSSentenceStartResponse',
  'UserConfig',
  'VolcengineTTSBidirectionRequest',
  'VolcengineTTSFunctions',
  'VolcengineTTSRequest',
  # Realtime dialogue
  'ASREndedResponse',
  'ASRInfoResponse',
  'ASRResponseModel',
  'ChatResponseModel',
  'ChatTTSTextRequest',
  'ChatTextQueryRequest',
  'ConnectionFailedResponse',
  'RealtimeDialogueConfig',
  'RealtimeDialogueErrorResponse',
  'RealtimeDialogueFunctions',
  'RealtimeDialogueUsage',
  'SayHelloRequest',
  'SessionFailedResponse',
  'SessionStartedResponse',
]

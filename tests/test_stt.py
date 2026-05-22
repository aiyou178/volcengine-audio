"""Tests for volcengine_audio.stt module."""

import gzip
import struct

import orjson

from volcengine_audio import (
  AsrFullServerResponseV2,
  AsrMessageType,
  AsrMessageTypeSpecificFlag,
  AudioCodec,
  CompressionMethod,
  EventReceive,
  ListenBidirectionPackage,
  MessageType,
  MessageTypeSpecificFlag,
  SerializationMethod,
  STTAudioFormatV3,
  STTBigmodelNoStreamLanguage,
  STTResultType,
  VolcengineAsrFunctionsV2,
  VolcengineAsrFunctionsV3,
  VolcengineAsrRequestV3,
  generate_before_payload,
  generate_header,
)


class TestVolcengineAsrRequestV3Serialization:
  """Test VolcengineAsrRequestV3 serialization behavior.

  Context (inside Corpus) and SensitiveWordsFilter should be serialized as
  JSON strings, not as nested dicts.
  """

  def test_event_receive_includes_waiting_next_packet_timeout(self):
    """Protocol enum should include the STT waiting-packet timeout code."""
    assert EventReceive.WAITING_NEXT_PACKET_TIMEOUT.value == 45000081

  def test_event_receive_includes_resource_not_granted(self):
    """Protocol enum should include the STT resource permission code."""
    assert EventReceive.REQUESTED_RESOURCE_NOT_GRANTED.value == 45000030

  def test_corpus_without_context_serializes_as_dict(self):
    """Test that Corpus without context is serialized as a dict."""
    corpus = VolcengineAsrRequestV3.Request.Corpus(
      boosting_table_name='test_table',
      boosting_table_id='123',
    )
    request = VolcengineAsrRequestV3.Request(
      corpus=corpus,
    )
    asr_request = VolcengineAsrRequestV3(request=request)

    dumped = asr_request.model_dump()

    assert dumped == {
      'user': {
        'uid': None,
        'did': None,
        'platform': None,
        'sdk_version': None,
        'app_version': None,
      },
      'audio': {
        'format': STTAudioFormatV3.wav,
        'codec': AudioCodec.raw,
        'rate': 16000,
        'bits': 16,
        'channel': 1,
        'language': None,
      },
      'request': {
        'model_name': 'bigmodel',
        'enable_itn': True,
        'enable_punc': True,
        'enable_ddc': False,
        'enable_nonstream': False,
        'show_utterances': False,
        'show_speech_rate': False,
        'show_volume': False,
        'enable_lid': False,
        'enable_emotion_detection': False,
        'enable_gender_detection': False,
        'result_type': STTResultType.full,
        'enable_accelerate_text': False,
        'accelerate_score': 0,
        'vad_segment_duration': 3000,
        'end_window_size': 800,
        'force_to_speech_time': 10000,
        'sensitive_words_filter': None,
        'enable_poi_fc': False,
        'enable_music_fc': False,
        'corpus': {
          'boosting_table_name': 'test_table',
          'boosting_table_id': '123',
          'correct_table_name': None,
          'correct_table_id': None,
          'context': None,
        },
      },
    }

  def test_context_serializes_as_json_string(self):
    """Test that Context inside Corpus is serialized as JSON string."""
    context = VolcengineAsrRequestV3.Request.Corpus.Context(
      hotwords=[
        VolcengineAsrRequestV3.Request.Corpus.Context.Hotword(word='热词1'),
        VolcengineAsrRequestV3.Request.Corpus.Context.Hotword(word='热词2'),
      ],
    )
    corpus = VolcengineAsrRequestV3.Request.Corpus(
      boosting_table_id='456',
      context=context,
    )
    request = VolcengineAsrRequestV3.Request(corpus=corpus)
    asr_request = VolcengineAsrRequestV3(request=request)

    dumped = asr_request.model_dump()

    # Context should be a JSON string
    context_json = '{"hotwords":[{"word":"热词1"},{"word":"热词2"}],"context_type":null,"context_data":[]}'

    assert dumped == {
      'user': {
        'uid': None,
        'did': None,
        'platform': None,
        'sdk_version': None,
        'app_version': None,
      },
      'audio': {
        'format': STTAudioFormatV3.wav,
        'codec': AudioCodec.raw,
        'rate': 16000,
        'bits': 16,
        'channel': 1,
        'language': None,
      },
      'request': {
        'model_name': 'bigmodel',
        'enable_itn': True,
        'enable_punc': True,
        'enable_ddc': False,
        'enable_nonstream': False,
        'show_utterances': False,
        'show_speech_rate': False,
        'show_volume': False,
        'enable_lid': False,
        'enable_emotion_detection': False,
        'enable_gender_detection': False,
        'result_type': STTResultType.full,
        'enable_accelerate_text': False,
        'accelerate_score': 0,
        'vad_segment_duration': 3000,
        'end_window_size': 800,
        'force_to_speech_time': 10000,
        'sensitive_words_filter': None,
        'enable_poi_fc': False,
        'enable_music_fc': False,
        'corpus': {
          'boosting_table_name': None,
          'boosting_table_id': '456',
          'correct_table_name': None,
          'correct_table_id': None,
          'context': context_json,
        },
      },
    }

  def test_sensitive_words_filter_serializes_as_json_string(self):
    """Test that SensitiveWordsFilter is serialized as a JSON string."""
    filter_ = VolcengineAsrRequestV3.Request.SensitiveWordsFilter(
      system_reserved_filter=True,
      filter_with_empty=['敏感词1'],
      filter_with_signed=['敏感词2', '敏感词3'],
    )
    request = VolcengineAsrRequestV3.Request(sensitive_words_filter=filter_)
    asr_request = VolcengineAsrRequestV3(request=request)

    dumped = asr_request.model_dump()

    filter_json = '{"system_reserved_filter":true,"filter_with_empty":["敏感词1"],"filter_with_signed":["敏感词2","敏感词3"]}'

    assert dumped == {
      'user': {
        'uid': None,
        'did': None,
        'platform': None,
        'sdk_version': None,
        'app_version': None,
      },
      'audio': {
        'format': STTAudioFormatV3.wav,
        'codec': AudioCodec.raw,
        'rate': 16000,
        'bits': 16,
        'channel': 1,
        'language': None,
      },
      'request': {
        'model_name': 'bigmodel',
        'enable_itn': True,
        'enable_punc': True,
        'enable_ddc': False,
        'enable_nonstream': False,
        'show_utterances': False,
        'show_speech_rate': False,
        'show_volume': False,
        'enable_lid': False,
        'enable_emotion_detection': False,
        'enable_gender_detection': False,
        'result_type': STTResultType.full,
        'enable_accelerate_text': False,
        'accelerate_score': 0,
        'vad_segment_duration': 3000,
        'end_window_size': 800,
        'force_to_speech_time': 10000,
        'sensitive_words_filter': filter_json,
        'enable_poi_fc': False,
        'enable_music_fc': False,
        'corpus': None,
      },
    }

  def test_context_and_sensitive_words_filter_serialize_as_json_strings(
    self,
  ):
    """Test Context and SensitiveWordsFilter serialize as JSON strings."""
    context = VolcengineAsrRequestV3.Request.Corpus.Context(
      hotwords=[
        VolcengineAsrRequestV3.Request.Corpus.Context.Hotword(word='热词'),
      ],
    )
    corpus = VolcengineAsrRequestV3.Request.Corpus(
      boosting_table_id='789',
      context=context,
    )
    filter_ = VolcengineAsrRequestV3.Request.SensitiveWordsFilter(
      system_reserved_filter=True,
      filter_with_signed=['敏感词'],
    )
    request = VolcengineAsrRequestV3.Request(
      corpus=corpus,
      sensitive_words_filter=filter_,
    )
    asr_request = VolcengineAsrRequestV3(request=request)

    dumped = asr_request.model_dump()

    context_json = (
      '{"hotwords":[{"word":"热词"}],"context_type":null,"context_data":[]}'
    )
    filter_json = '{"system_reserved_filter":true,"filter_with_empty":[],"filter_with_signed":["敏感词"]}'

    assert dumped == {
      'user': {
        'uid': None,
        'did': None,
        'platform': None,
        'sdk_version': None,
        'app_version': None,
      },
      'audio': {
        'format': STTAudioFormatV3.wav,
        'codec': AudioCodec.raw,
        'rate': 16000,
        'bits': 16,
        'channel': 1,
        'language': None,
      },
      'request': {
        'model_name': 'bigmodel',
        'enable_itn': True,
        'enable_punc': True,
        'enable_ddc': False,
        'enable_nonstream': False,
        'show_utterances': False,
        'show_speech_rate': False,
        'show_volume': False,
        'enable_lid': False,
        'enable_emotion_detection': False,
        'enable_gender_detection': False,
        'result_type': STTResultType.full,
        'enable_accelerate_text': False,
        'accelerate_score': 0,
        'vad_segment_duration': 3000,
        'end_window_size': 800,
        'force_to_speech_time': 10000,
        'sensitive_words_filter': filter_json,
        'enable_poi_fc': False,
        'enable_music_fc': False,
        'corpus': {
          'boosting_table_name': None,
          'boosting_table_id': '789',
          'correct_table_name': None,
          'correct_table_id': None,
          'context': context_json,
        },
      },
    }

  def test_language_enum_includes_new_doc_locales(self):
    """Latest non-streaming STT locales should be available."""
    assert STTBigmodelNoStreamLanguage.it_IT.value == 'it-IT'
    assert STTBigmodelNoStreamLanguage.ru_RU.value == 'ru-RU'
    assert STTBigmodelNoStreamLanguage.yue_CN.value == 'yue-CN'

  def test_enable_nostream_input_alias_maps_to_enable_nonstream(self):
    """Legacy enable_nostream input should map to enable_nonstream output."""
    request = VolcengineAsrRequestV3.Request(enable_nostream=True)
    dumped = request.model_dump()

    assert dumped['enable_nonstream'] is True
    assert 'enable_nostream' not in dumped


def test_shared_protocol_helpers_generate_real_headers_and_sequences():
  """Shared protocol helpers should emit documented wire bytes."""
  assert generate_header() == bytearray(b'\x11\x10\x10\x00')
  assert generate_header(
    message_type=MessageType.AUDIO_ONLY_REQUEST,
    message_type_specific_flags=MessageTypeSpecificFlag.NEG_WITH_SEQUENCE,
    serial_method=SerializationMethod.RAW,
    compression_type=CompressionMethod.GZIP,
    reserved_data=0x7F,
  ) == bytearray(b'\x11#\x01\x7f')
  assert generate_before_payload(-3) == bytearray(b'\xff\xff\xff\xfd')


def test_stt_response_models_set_last_package_and_word_aliases():
  """STT response models should normalize sequence and word timing aliases."""
  response = AsrFullServerResponseV2.model_validate(
    {
      'message': {
        'code': 1000,
        'message': 'success',
        'reqid': 'req-1',
        'sequence': -1,
        'result': [
          {
            'text': 'hello',
            'confidence': 95,
            'utterances': [
              {
                'start_time': 10,
                'end_time': 20,
                'text': 'hello',
                'words': [
                  {
                    'start_time': 11,
                    'end_time': 12,
                    'text': 'he',
                    'black_duration': 3,
                  }
                ],
              }
            ],
          }
        ],
      },
      'size': 1,
      'is_last_package': False,
    }
  )
  package = ListenBidirectionPackage.model_validate(
    {
      'is_last_package': False,
      'sequence': 1,
      'message': {
        'audio_info': {'duration': 120},
        'result': {
          'text': 'hi',
          'additions': {'log_id': 'log-1'},
          'utterances': [
            {
              'start_time': 30,
              'end_time': 40,
              'text': 'hi',
              'words': [
                {
                  'start_time': 31,
                  'end_time': 32,
                  'text': 'h',
                  'blank_duration': 2,
                }
              ],
            }
          ],
        },
      },
      'size': 2,
    }
  )

  assert response.is_last_package is True
  assert response.message.result[0].utterances[0].words[0].start_ms == 11
  assert response.message.result[0].utterances[0].words[0].end_ms == 12
  assert response.message.result[0].utterances[0].words[0].blank_duration == 3
  assert package.message.result.utterances[0].words[0].start_ms == 31
  assert package.message.result.utterances[0].words[0].end_ms == 32


def test_asr_v3_request_generation_and_parse_round_trips_json_payloads():
  """ASR V3 helpers should generate and parse real JSON/GZIP request frames."""
  request_params = {
    'app': {'appid': 'app-id'},
    'request': {'model_name': 'bigmodel'},
  }

  compressed = VolcengineAsrFunctionsV3.generate_asr_full_client_request(
    7,
    request_params,
    compression=True,
  )
  plain = VolcengineAsrFunctionsV3.generate_asr_full_client_request(
    8,
    request_params,
    compression=False,
  )
  audio = VolcengineAsrFunctionsV3.generate_asr_audio_only_request(
    3,
    b'audio',
    compress=False,
  )
  compressed_audio = VolcengineAsrFunctionsV3.generate_asr_audio_only_request(
    5,
    b'audio',
    compress=True,
  )
  final_audio = VolcengineAsrFunctionsV3.generate_asr_audio_only_request(
    4,
    b'',
    compress=True,
  )

  assert VolcengineAsrFunctionsV3.parse_request(compressed) == request_params
  assert VolcengineAsrFunctionsV3.parse_request(plain) == request_params
  assert VolcengineAsrFunctionsV3.generate_asr_before_payload(-1) == (
    generate_before_payload(-1)
  )
  assert struct.unpack('>i', audio[4:8])[0] == 3
  assert audio[2] & 0x0F == CompressionMethod.NONE.value
  assert gzip.decompress(compressed_audio[12:]) == b'audio'
  assert struct.unpack('>i', final_audio[4:8])[0] == -4
  assert (
    final_audio[1] & 0x0F == AsrMessageTypeSpecificFlag.NEG_WITH_SEQUENCE.value
  )
  assert final_audio[2] & 0x0F == CompressionMethod.NONE.value


def test_asr_v3_parse_response_handles_server_frame_variants():
  """ASR V3 response parser should handle response, ack, error, and raw frames."""
  message = {'result': [{'text': 'hello'}]}
  message_bytes = gzip.compress(orjson.dumps(message))
  full_response = bytearray(
    VolcengineAsrFunctionsV3.generate_asr_header(
      message_type=AsrMessageType.FULL_SERVER_RESPONSE,
      message_type_specific_flags=AsrMessageTypeSpecificFlag.POS_SEQUENCE,
      compression_type=CompressionMethod.GZIP,
    )
  )
  full_response.extend(struct.pack('>i', 9))
  full_response.extend(struct.pack('>i', len(message_bytes)))
  full_response.extend(message_bytes)

  ack_with_payload = bytearray(
    VolcengineAsrFunctionsV3.generate_asr_header(
      message_type=AsrMessageType.SERVER_ACK,
      serial_method=SerializationMethod.RAW,
    )
  )
  ack_with_payload.extend(struct.pack('>i', 10))
  ack_with_payload.extend(struct.pack('>I', 3))
  ack_with_payload.extend(b'raw')

  ack_without_payload = bytearray(
    VolcengineAsrFunctionsV3.generate_asr_header(
      message_type=AsrMessageType.SERVER_ACK,
      serial_method=SerializationMethod.RAW,
    )
  )
  ack_without_payload.extend(struct.pack('>i', 11))

  error_payload = orjson.dumps({'message': 'bad'})
  error_response = bytearray(
    VolcengineAsrFunctionsV3.generate_asr_header(
      message_type=AsrMessageType.SERVER_ERROR_RESPONSE,
    )
  )
  error_response.extend(struct.pack('>I', 400))
  error_response.extend(struct.pack('>I', len(error_payload)))
  error_response.extend(error_payload)

  last_plain_response = bytearray(
    VolcengineAsrFunctionsV3.generate_asr_header(
      message_type=AsrMessageType.FULL_SERVER_RESPONSE,
      message_type_specific_flags=AsrMessageTypeSpecificFlag.NEG_WITH_SEQUENCE,
      serial_method=SerializationMethod.PROTOBUF,
    )
  )
  last_plain_response.extend(struct.pack('>i', -12))
  last_plain_response.extend(struct.pack('>i', 3))
  last_plain_response.extend(b'abc')

  assert VolcengineAsrFunctionsV3.parse_response(full_response) == {
    'is_last_package': False,
    'sequence': 9,
    'message': message,
    'size': len(message_bytes),
  }
  assert VolcengineAsrFunctionsV3.parse_response(ack_with_payload) == {
    'is_last_package': False,
    'sequence': 10,
    'message': b'raw',
    'size': 3,
  }
  assert VolcengineAsrFunctionsV3.parse_response(ack_without_payload) == {
    'is_last_package': False,
    'sequence': 11,
  }
  assert VolcengineAsrFunctionsV3.parse_response(error_response) == {
    'is_last_package': False,
    'code': 400,
    'message': {'message': 'bad'},
    'size': len(error_payload),
  }
  assert VolcengineAsrFunctionsV3.parse_response(last_plain_response) == {
    'is_last_package': True,
    'sequence': -12,
    'message': "bytearray(b'abc')",
    'size': 3,
  }


def test_asr_v3_parse_request_non_json_serialization_returns_string_payload():
  """Non-JSON request payloads should be exposed as their byte-string repr."""
  payload = b'abc'
  frame = bytearray(
    VolcengineAsrFunctionsV3.generate_asr_header(
      serial_method=SerializationMethod.PROTOBUF,
    )
  )
  frame.extend(struct.pack('>I', len(payload)))
  frame.extend(payload)

  assert VolcengineAsrFunctionsV3.parse_request(frame) == "bytearray(b'abc')"


def test_asr_v2_helpers_generate_real_request_frames():
  """ASR V2 helpers should generate compressed and uncompressed frames."""
  params = {'audio': {'format': 'wav'}}
  compressed = VolcengineAsrFunctionsV2.full_client_request(
    params, compression=True
  )
  plain = VolcengineAsrFunctionsV2.full_client_request(
    params, compression=False
  )
  audio = VolcengineAsrFunctionsV2.audio_only_request(b'audio', compress=False)
  final_audio = VolcengineAsrFunctionsV2.audio_only_request(
    b'last',
    compress=True,
    last=True,
  )

  compressed_size = struct.unpack('>I', compressed[4:8])[0]
  plain_size = struct.unpack('>I', plain[4:8])[0]
  assert (
    orjson.loads(gzip.decompress(compressed[8 : 8 + compressed_size])) == params
  )
  assert orjson.loads(plain[8 : 8 + plain_size]) == params
  assert audio[1] & 0x0F == AsrMessageTypeSpecificFlag.NO_SEQUENCE.value
  assert audio[2] & 0x0F == CompressionMethod.NONE.value
  assert final_audio[1] & 0x0F == AsrMessageTypeSpecificFlag.NEG_SEQUENCE.value
  assert final_audio[2] & 0x0F == CompressionMethod.GZIP.value

"""Tests for volcengine_audio.tts module."""

import gzip
import orjson
import pytest
import struct

from volcengine_audio import (
  CompressionMethod,
  EventReceive,
  EventSend,
  MessageType,
  SerializationMethod,
  TTSAudioFormat,
  TTSBigmodelModelType,
  TTSBigmodelResourceType,
  RequestConfig,
  TTSSubtitlePayload,
  TTSReqParams,
  TTSTimedWord,
  VolcengineTTSFunctions,
  VolcengineTTSBidirectionRequest,
  VolcengineTTSRequest,
  validate_tts_resource_model_mapping,
)


class TestTTSReqParamsSchema:
  """Test TTS request schema alignment with Volcengine docs."""

  def test_audio_params_defaults_match_doc(self):
    """emotion_scale and enable_subtitle should match doc defaults."""
    req = TTSReqParams(speaker='zh_female_test')
    dumped = req.model_dump()

    assert dumped['audio_params']['emotion_scale'] == 4
    assert dumped['audio_params']['enable_subtitle'] is False

  def test_audio_params_syncs_timestamp_and_subtitle(self):
    """Enabling either timestamp or subtitle should enable both."""
    timestamp_req = TTSReqParams(
      speaker='zh_female_test',
      audio_params=TTSReqParams.AudioParams(enable_timestamp=True),
    )
    subtitle_req = TTSReqParams(
      speaker='zh_female_test',
      audio_params=TTSReqParams.AudioParams(enable_subtitle=True),
    )

    timestamp_dump = timestamp_req.model_dump()
    subtitle_dump = subtitle_req.model_dump()

    assert timestamp_dump['audio_params']['enable_timestamp'] is True
    assert timestamp_dump['audio_params']['enable_subtitle'] is True
    assert subtitle_dump['audio_params']['enable_timestamp'] is True
    assert subtitle_dump['audio_params']['enable_subtitle'] is True

  def test_additions_serializes_aigc_metadata_and_new_fields(self):
    """additions should serialize to JSON string with new doc fields."""
    additions = TTSReqParams.Additions(
      disable_markdown_filter=True,
      latex_parser='v2',
      use_tag_parser=True,
      cache_config=TTSReqParams.Additions.CacheConfig(),
      aigc_meta=TTSReqParams.Additions.AIGCMetadata(
        enable=True,
        content_producer='producer',
        produce_id='produce-id',
        content_propagator='propagator',
        propagate_id='propagate-id',
      ),
    )
    req = TTSReqParams(speaker='zh_female_test', additions=additions)
    dumped = req.model_dump()

    assert isinstance(dumped['additions'], str)
    additions_dump = orjson.loads(dumped['additions'])

    assert additions_dump['latex_parser'] == 'v2'
    assert additions_dump['use_tag_parser'] is True
    assert additions_dump['cache_config']['use_segment_cache'] is True
    assert additions_dump['aigc_metadata'] == {
      'enable': True,
      'content_producer': 'producer',
      'produce_id': 'produce-id',
      'content_propagator': 'propagator',
      'propagate_id': 'propagate-id',
    }
    assert 'aigc_meta' not in additions_dump

  def test_latex_parser_requires_disable_markdown_filter(self):
    """latex_parser=v2 should require disable_markdown_filter=true."""
    with pytest.raises(ValueError, match='latex_parser=v2'):
      TTSReqParams.Additions(latex_parser='v2')

  def test_concurrent_resource_ids_match_latest_docs(self):
    """Concurrent resource ids should use the latest concurr suffix."""
    assert TTSBigmodelResourceType.seed_tts_1_0_concurr.value == (
      'seed-tts-1.0-concurr'
    )
    assert TTSBigmodelResourceType.voice_clone_1_0_concurr.value == (
      'seed-icl-1.0-concurr'
    )

  def test_bidirectional_model_enum_matches_latest_docs(self):
    """Bidirectional model enum values should match the latest docs."""
    assert TTSBigmodelModelType.seed_tts_1_1.value == 'seed-tts-1.1'
    assert (
      TTSBigmodelModelType.seed_tts_2_0_expressive.value
      == 'seed-tts-2.0-expressive'
    )
    assert (
      TTSBigmodelModelType.seed_tts_2_0_standard.value
      == 'seed-tts-2.0-standard'
    )

  def test_bidirectional_req_params_uses_model_enum(self):
    """Bidirectional req_params.model should serialize the new model enum."""
    req = VolcengineTTSBidirectionRequest.ReqParams(
      text='hello',
      speaker='saturn_test_voice',
      model=TTSBigmodelModelType.seed_tts_2_0_standard,
    )

    dumped = req.model_dump()

    assert dumped['model'] == 'seed-tts-2.0-standard'

  def test_tts_subtitle_schema_matches_2_0_payload(self):
    """TTS 2.0 subtitle payload should use the shared timing schema."""
    word: TTSTimedWord = {
      'confidence': 0.9,
      'startTime': 0.1,
      'endTime': 0.3,
      'word': 'hello',
    }
    payload: TTSSubtitlePayload = {
      'phonemes': [],
      'text': 'hello',
      'words': [word],
    }

    assert payload['words'][0]['word'] == 'hello'

  def test_event_receive_includes_tts_subtitle(self):
    """Protocol enum should include the TTSSubtitle event id."""
    assert EventReceive.TTSSubtitle.value == 364

  def test_resource_model_mapping_accepts_valid_pairs(self):
    """Resource ids and req_params.model should align by major version."""
    validate_tts_resource_model_mapping(
      TTSBigmodelResourceType.seed_tts_1_0,
      None,
    )
    validate_tts_resource_model_mapping(
      TTSBigmodelResourceType.seed_tts_1_0,
      TTSBigmodelModelType.seed_tts_1_1,
    )
    validate_tts_resource_model_mapping(
      TTSBigmodelResourceType.seed_tts_2_0,
      TTSBigmodelModelType.seed_tts_2_0_standard,
    )

  def test_resource_model_mapping_rejects_invalid_pairs(self):
    """Invalid 1.0/2.0 resource-model combinations should fail validation."""
    with pytest.raises(
      ValueError, match='Invalid TTS resource_id/model mapping'
    ):
      validate_tts_resource_model_mapping(
        TTSBigmodelResourceType.seed_tts_1_0,
        TTSBigmodelModelType.seed_tts_2_0_standard,
      )

    with pytest.raises(
      ValueError, match='Invalid TTS resource_id/model mapping'
    ):
      validate_tts_resource_model_mapping(
        TTSBigmodelResourceType.seed_tts_2_0,
        TTSBigmodelModelType.seed_tts_1_1,
      )

  def test_extra_param_parses_json_and_validates_markdown_dependency(self):
    """RequestConfig extra_param should accept JSON strings and validate flags."""
    extra = RequestConfig.ExtraParam.model_validate(
      '{"disable_markdown_filter":true,"enable_latex_tn":true}'
    )

    assert extra.model_dump() == (
      '{"disable_markdown_filter":true,"enable_latex_tn":true}'
    )
    with pytest.raises(ValueError, match='enable_latex_tn requires'):
      RequestConfig.ExtraParam(
        disable_markdown_filter=False,
        enable_latex_tn=True,
      )

  def test_bidirectional_mix_speaker_validates_factor_sum(self):
    """Mixed speaker config should require factors to sum to one."""
    valid = VolcengineTTSBidirectionRequest.ReqParams.MixSpeaker(
      speakers=[
        VolcengineTTSBidirectionRequest.ReqParams.MixSpeaker.Speaker(
          source_speaker='speaker-a',
          mix_factor=0.4,
        ),
        VolcengineTTSBidirectionRequest.ReqParams.MixSpeaker.Speaker(
          source_speaker='speaker-b',
          mix_factor=0.6,
        ),
      ]
    )

    assert sum(speaker.mix_factor for speaker in valid.speakers) == 1.0
    with pytest.raises(ValueError, match='mix_factor sum'):
      VolcengineTTSBidirectionRequest.ReqParams.MixSpeaker(
        speakers=[
          VolcengineTTSBidirectionRequest.ReqParams.MixSpeaker.Speaker(
            source_speaker='speaker-a',
            mix_factor=0.2,
          )
        ]
      )

  def test_audio_format_list_and_additions_validation(self):
    """Audio format and additions validators should cover documented branches."""
    assert TTSAudioFormat.list() == ['wav', 'pcm', 'mp3', 'ogg_opus']
    with pytest.raises(ValueError, match='enable_latex_tn requires'):
      TTSReqParams.Additions(
        disable_markdown_filter=False,
        enable_latex_tn=True,
      )

  def test_prepare_request_and_payload_builders_emit_real_frames(self):
    """TTS helpers should encode JSON/GZIP request and event frames."""
    request = VolcengineTTSRequest(
      app={'token': 'token'},
      user={'uid': 'user'},
      audio={'voice_type': 'voice', 'encoding': TTSAudioFormat.mp3},
      request={'reqid': 'req-1', 'text': 'hello'},
    )
    plain = VolcengineTTSFunctions.prepare_request(request, compression=False)
    compressed = VolcengineTTSFunctions.prepare_request(
      request.model_dump(),
      compression=True,
    )
    task_payload = VolcengineTTSFunctions.task_request_payload(
      'session-1',
      'hello',
      'speaker',
      {'format': 'mp3'},
    )

    plain_size = int.from_bytes(plain[4:8], 'big')
    compressed_size = int.from_bytes(compressed[4:8], 'big')
    assert plain[:4] == b'\x11\x10\x10\x00'
    assert compressed[:4] == b'\x11\x10\x11\x00'
    assert orjson.loads(plain[8 : 8 + plain_size])['request']['text'] == 'hello'
    assert (
      orjson.loads(gzip.decompress(compressed[8 : 8 + compressed_size]))[
        'request'
      ]['text']
      == 'hello'
    )

    event = struct.unpack('>I', task_payload[4:8])[0]
    session_len = struct.unpack('>I', task_payload[8:12])[0]
    session_id = task_payload[12 : 12 + session_len].decode()
    meta_start = 12 + session_len
    meta_len = struct.unpack('>I', task_payload[meta_start : meta_start + 4])[0]
    meta = orjson.loads(
      task_payload[meta_start + 4 : meta_start + 4 + meta_len]
    )
    assert event == EventSend.TaskRequest.value
    assert session_id == 'session-1'
    assert meta['req_params']['speaker'] == 'speaker'

  def test_tts_payload_helpers_cover_connection_and_session_events(self):
    """TTS event helpers should produce documented event ids and metadata."""

    def decode_event(payload: bytes) -> tuple[int, dict]:
      event = struct.unpack('>I', payload[4:8])[0]
      if struct.unpack('>I', payload[8:12])[0] == len(payload) - 12:
        meta_start = 8
      else:
        session_len = struct.unpack('>I', payload[8:12])[0]
        meta_start = 12 + session_len
      meta_len = struct.unpack('>I', payload[meta_start : meta_start + 4])[0]
      meta = orjson.loads(payload[meta_start + 4 : meta_start + 4 + meta_len])
      return event, meta

    assert decode_event(VolcengineTTSFunctions.start_connection_payload()) == (
      EventSend.StartConnection.value,
      {},
    )
    start_session = VolcengineTTSFunctions.start_session_payload(
      'session-1',
      {'speaker': 'speaker'},
      {'uid': 'user'},
    )
    assert decode_event(start_session) == (
      EventSend.StartSession.value,
      {
        'event': EventSend.StartSession.value,
        'namespace': 'BidirectionalTTS',
        'req_params': {'speaker': 'speaker'},
        'user': {'uid': 'user'},
      },
    )
    assert decode_event(VolcengineTTSFunctions.finish_session_payload('s')) == (
      EventSend.FinishSession.value,
      {},
    )
    assert decode_event(VolcengineTTSFunctions.cancel_session_payload('s')) == (
      EventSend.CancelSession.value,
      {},
    )
    assert decode_event(VolcengineTTSFunctions.finish_connection_payload()) == (
      EventSend.FinishConnection.value,
      {},
    )

  def test_extract_response_payload_handles_json_raw_errors_and_edge_cases(
    self,
  ):
    """TTS response parser should decode realistic server frames."""

    def frame(
      event: int,
      payload: bytes,
      *,
      serialization: SerializationMethod = SerializationMethod.JSON,
      message_type: MessageType = MessageType.FULL_SERVER_RESPONSE,
    ) -> bytes:
      header = bytes(
        [
          0x11,
          (message_type.value << 4) | 0b0100,
          (serialization.value << 4) | CompressionMethod.NONE.value,
          0,
        ]
      )
      session = b'session-1'
      return (
        header
        + struct.pack('>I', event)
        + struct.pack('>I', len(session))
        + session
        + struct.pack('>I', len(payload))
        + payload
      )

    json_payload = orjson.dumps({'status_code': 200})
    raw_payload = b'audio'
    sentence_payload = b'invalid-json-by-design'
    bad_json_payload = b'{not-json'
    unknown_protocol = bytearray(
      frame(EventReceive.SessionFinished.value, json_payload)
    )
    unknown_protocol[0] = 0x21
    mismatch_header_size = bytearray(
      frame(EventReceive.SessionFinished.value, json_payload)
    )
    mismatch_header_size[0] = 0x12
    unknown_event = frame(123456, json_payload)

    assert VolcengineTTSFunctions.extract_response_payload(
      frame(EventReceive.SessionFinished.value, json_payload)
    ) == (EventReceive.SessionFinished, 'session-1', {'status_code': 200})
    assert VolcengineTTSFunctions.extract_response_payload(
      frame(
        EventReceive.TTSSentenceStart.value,
        sentence_payload,
      )
    ) == (EventReceive.TTSSentenceStart, 'session-1', sentence_payload)
    assert VolcengineTTSFunctions.extract_response_payload(
      frame(
        EventReceive.TTSSentenceEnd.value,
        sentence_payload,
      )
    ) == (EventReceive.TTSSentenceEnd, 'session-1', sentence_payload)
    assert VolcengineTTSFunctions.extract_response_payload(
      frame(
        EventReceive.TTSResponse.value,
        raw_payload,
        serialization=SerializationMethod.RAW,
      )
    ) == (EventReceive.TTSResponse, 'session-1', raw_payload)
    assert VolcengineTTSFunctions.extract_response_payload(
      frame(EventReceive.TTSEnded.value, b'')
    ) == (EventReceive.TTSEnded, 'session-1', b'')
    assert VolcengineTTSFunctions.extract_response_payload(
      bytes(unknown_protocol)
    ) == (
      EventReceive.SessionFinished,
      'session-1',
      {'status_code': 200},
    )
    assert VolcengineTTSFunctions.extract_response_payload(
      bytes(mismatch_header_size)
    ) == (
      EventReceive.SessionFinished,
      'session-1',
      {'status_code': 200},
    )
    assert VolcengineTTSFunctions.extract_response_payload(unknown_event) == (
      123456,
      'session-1',
      {'status_code': 200},
    )
    assert (
      VolcengineTTSFunctions.extract_response_payload(
        frame(EventReceive.SessionFinished.value, bad_json_payload)
      )
      is None
    )

    with pytest.raises(ValueError, match='data must be bytes'):
      VolcengineTTSFunctions.extract_response_payload('not bytes')
    with pytest.raises(ValueError, match='Data too short'):
      VolcengineTTSFunctions.extract_response_payload(b'\x11')
    with pytest.raises(NotImplementedError, match='Unsupported message type'):
      VolcengineTTSFunctions.extract_response_payload(
        frame(
          EventReceive.TTSResponse.value,
          b'',
          message_type=MessageType.AUDIO_ONLY_REQUEST,
        )
      )
    with pytest.raises(NotImplementedError, match='Unsupported serialization'):
      VolcengineTTSFunctions.extract_response_payload(
        frame(
          EventReceive.TTSResponse.value,
          b'protobuf',
          serialization=SerializationMethod.PROTOBUF,
        )
      )

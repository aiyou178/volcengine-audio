"""Tests for volcengine_audio.tts module."""

import orjson
import pytest

from volcengine_audio import (
  EventReceive,
  TTSBigmodelModelType,
  TTSBigmodelResourceType,
  TTSSubtitlePayload,
  TTSReqParams,
  TTSTimedWord,
  VolcengineTTSBidirectionRequest,
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

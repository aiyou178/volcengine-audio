"""Tests for volcengine_audio.tts module."""

import orjson
import pytest

from volcengine_audio import TTSReqParams


class TestTTSReqParamsSchema:
  """Test TTS request schema alignment with Volcengine docs."""

  def test_audio_params_defaults_match_doc(self):
    """emotion_scale and enable_subtitle should match doc defaults."""
    req = TTSReqParams(speaker='zh_female_test')
    dumped = req.model_dump()

    assert dumped['audio_params']['emotion_scale'] == 4
    assert dumped['audio_params']['enable_subtitle'] is False

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

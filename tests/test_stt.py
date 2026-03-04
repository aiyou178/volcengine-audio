"""Tests for volcengine_audio.stt module."""

from volcengine_audio import (
  AudioCodec,
  STTAudioFormatV3,
  STTResultType,
  VolcengineAsrRequestV3,
)


class TestVolcengineAsrRequestV3Serialization:
  """Test VolcengineAsrRequestV3 serialization behavior.

  Context (inside Corpus) and SensitiveWordsFilter should be serialized as
  JSON strings, not as nested dicts.
  """

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
    context_json = '{"hotwords":[{"word":"热词1"},{"word":"热词2"}],"context_type":null,"content_data":[]}'

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
      '{"hotwords":[{"word":"热词"}],"context_type":null,"content_data":[]}'
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

  def test_enable_nostream_input_alias_maps_to_enable_nonstream(self):
    """Legacy enable_nostream input should map to enable_nonstream output."""
    request = VolcengineAsrRequestV3.Request(enable_nostream=True)
    dumped = request.model_dump()

    assert dumped['enable_nonstream'] is True
    assert 'enable_nostream' not in dumped

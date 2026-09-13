"""Native Seeduplex schema coverage against every official API example."""

import json
import re
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from volcengine_audio import (
  SEEDUPLEX_URL,
  SeeduplexAudio,
  SeeduplexAudioRequest,
  SeeduplexEvent,
  SeeduplexExtension,
  SeeduplexFunctionCall,
  SeeduplexRequest,
  SeeduplexServerEventType,
  encode_seeduplex_request,
)


def official_examples():
  snapshot = (
    Path(__file__).parents[1]
    / 'doc_sync/volcengine/2549778-seeduplex_realtime.md'
  ).read_text()
  decoder = json.JSONDecoder()
  examples = []
  for block in re.findall(r'```json\n(.*?)\n```', snapshot, re.S):
    remaining = re.sub(r'^//.*$', '', block, flags=re.M).strip()
    while remaining:
      event, offset = decoder.raw_decode(remaining)
      examples.append(event)
      remaining = remaining[offset:].strip()
  assert len(examples) >= 35, 'Documentation examples must not disappear'
  return examples


@pytest.mark.parametrize('payload', official_examples())
def test_every_official_payload_round_trips(payload):
  if payload['type'] in set(SeeduplexServerEventType):
    event = SeeduplexEvent.model_validate(payload)
    assert event.model_dump(mode='json', exclude_unset=True) == payload
    assert SeeduplexEvent.model_validate_json(json.dumps(payload)) == event
  else:
    assert json.loads(encode_seeduplex_request(payload)) == payload


@pytest.mark.parametrize(
  'event_type',
  [
    'input_audio_mute.commit',
    'input_audio_unmute.commit',
    'session.close',
    'input_audio_buffer.commit',
    'response.cancel',
    'speech_text_buffer.replacement.commit',
    'conversation.item.retrieve',
  ],
)
def test_controls_and_optional_empty_terminal_payloads(event_type):
  payload = {'type': event_type}
  assert json.loads(encode_seeduplex_request(payload)) == payload


@pytest.mark.parametrize(
  'tools',
  [
    [],
    [
      {
        'type': 'function',
        'name': 'ask_backend',
        'parameters': {
          'type': 'object',
          'properties': {'question': {'type': 'string'}},
          'required': ['question'],
          'additionalProperties': False,
        },
      },
    ],
  ],
)
def test_update_replaces_tools_without_injecting_other_settings(tools):
  payload = {'type': 'session.update', 'session': {'tools': tools}}
  assert json.loads(encode_seeduplex_request(payload)) == payload


def test_audio_constraints_and_open_voice_catalog():
  audio = SeeduplexAudio.model_validate(
    {
      'input': {'format': {'type': 'speech_opus', 'rate': 16000}},
      'output': {
        'format': {'type': 'ogg_opus', 'rate': 24000},
        'voice': 'deployment-owned-cloned-voice',
        'speed': -50,
        'loudness': 100,
      },
    }
  )
  assert audio.output.voice == 'deployment-owned-cloned-voice'
  for payload in (
    {'input': {'format': {'rate': 24000}}},
    {'output': {'format': {'rate': 16000}}},
    {'output': {'format': {'type': 'pcm_s16le'}}},
    {'output': {'speed': 101}},
    {'output': {'loudness': -51}},
  ):
    with pytest.raises(ValidationError):
      SeeduplexAudio.model_validate(payload)
  assert SEEDUPLEX_URL.endswith('/api/v3/duplex/realtime/dialogue')
  assert json.loads(
    encode_seeduplex_request(SeeduplexAudioRequest(audio='AA=='))
  ) == {
    'type': 'input_audio_buffer.append',
    'audio': 'AA==',
  }


def test_all_native_extension_fields_round_trip():
  extension = {
    'asr': {
      'extra': {
        'enable_asr_twopass': True,
        'boosting_table_id': 'hot-id',
        'boosting_table_name': 'hot-name',
        'regex_correct_table_id': 'regex-id',
        'regex_correct_table_name': 'regex-name',
        'context': {
          'hotwords': [{'word': '豆包'}],
          'correct_words': {'斗包': '豆包'},
        },
      }
    },
    'dialog': {
      'location': {
        'longitude': 121.5,
        'latitude': 31.2,
        'city': '上海',
        'country': '中国',
        'province': '上海',
        'district': '黄浦',
        'town': '外滩',
        'country_code': 'CN',
        'address': '测试地址',
      },
      'dialog_context': [
        {'role': 'user', 'text': '你好', 'timestamp': 1},
        {'role': 'assistant', 'text': '您好', 'timestamp': 2},
      ],
      'extra': {
        'strict_audit': True,
        'audit_response': '无法回答',
        'enable_volc_websearch': True,
        'volc_websearch_type': 'web_custom_api',
        'volc_websearch_api_key': 'test-placeholder',
        'enable_music': True,
        'enable_loudness_norm': True,
        'enable_user_query_exit': True,
      },
    },
    'tts': {
      'extra': {
        'max_length_to_filter_parenthesis': 100,
        'explicit_dialect': 'shanghai',
        'aigc_metadata': {
          'enable': True,
          'content_producer': 'test',
          'produce_id': '1',
          'content_propagator': 'test',
          'propagate_id': '2',
        },
      }
    },
  }
  result = SeeduplexExtension.model_validate(extension)
  assert result.model_dump(mode='json', exclude_unset=True) == extension
  payload = {
    'type': 'session.create',
    'session': {'model': '1.2.6.1'},
    'extension': extension,
  }
  assert json.loads(encode_seeduplex_request(payload)) == payload


def test_response_fields_unknown_events_and_unspecified_usage():
  payload = {'type': 'error', 'status_code': 55000001, 'message': 'ServerError'}
  assert (
    SeeduplexEvent.model_validate(payload).model_dump(exclude_unset=True)
    == payload
  )
  payload = {'type': 'response.done', 'usage': {'provider_future_counter': 3}}
  assert SeeduplexEvent.model_validate(payload).usage == payload['usage']
  assert SeeduplexEvent(type='future.event').type == 'future.event'
  assert (
    SeeduplexEvent(
      type='response.output_audio.started', tts_type='future'
    ).tts_type
    == 'future'
  )


@pytest.mark.parametrize(
  'event_type',
  ['response.create', 'input_audio_buffer.clear', 'conversation.item.truncate'],
)
def test_no_openai_only_requests(event_type):
  with pytest.raises(ValidationError):
    encode_seeduplex_request({'type': event_type})


def test_native_result_shape_and_required_call_fields():
  with pytest.raises(ValidationError):
    encode_seeduplex_request(
      {
        'type': 'conversation.item.create',
        'items': [
          {'type': 'function_call_output', 'call_id': 'a', 'output': 'done'},
        ],
      }
    )
  for missing in ('call_id', 'name', 'arguments'):
    call = {'call_id': 'a', 'name': 'tool', 'arguments': '{}'}
    del call[missing]
    with pytest.raises(ValidationError):
      SeeduplexFunctionCall.model_validate(call)
  # The SDK does not impose the LiveKit consumer's argument-size policy.
  assert SeeduplexFunctionCall(call_id='a', name='tool', arguments='x' * 16001)


def test_complete_native_event_inventory():
  schema = TypeAdapter(SeeduplexRequest).json_schema()
  assert set(schema['discriminator']['mapping']) == {
    'session.create',
    'session.update',
    'session.close',
    'input_audio_buffer.append',
    'input_audio_buffer.commit',
    'input_audio_mute.commit',
    'input_audio_unmute.commit',
    'speech_text_buffer.commit',
    'speech_text_buffer.replacement.append',
    'speech_text_buffer.replacement.commit',
    'conversation.item.create',
    'conversation.item.update',
    'conversation.item.retrieve',
    'conversation.item.delete',
    'response.cancel',
  }
  snapshot = (
    Path(__file__).parents[1]
    / 'doc_sync/volcengine/2549778-seeduplex_realtime.md'
  ).read_text()
  assert len(SeeduplexServerEventType) == 20
  assert all(event.value in snapshot for event in SeeduplexServerEventType)

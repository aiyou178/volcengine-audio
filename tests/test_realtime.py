"""Tests for volcengine_audio.realtime module."""

import struct

import pytest

from volcengine_audio import (
  ASREndedResponse,
  ChatRAGTextRequest,
  ChatResponseModel,
  ConversationCreateRequest,
  ConversationDeleteRequest,
  ConversationRetrieveRequest,
  ConversationUpdateRequest,
  EventSend,
  RealtimeDialogueConfig,
  RealtimeDialogueFunctions,
)


def _decode_session_json_payload(payload: bytes) -> tuple[int, str, dict]:
  offset = 4  # Skip 4-byte protocol header.

  event = struct.unpack('>I', payload[offset : offset + 4])[0]
  offset += 4

  session_id_len = struct.unpack('>I', payload[offset : offset + 4])[0]
  offset += 4
  session_id = payload[offset : offset + session_id_len].decode()
  offset += session_id_len

  meta_len = struct.unpack('>I', payload[offset : offset + 4])[0]
  offset += 4
  meta = payload[offset : offset + meta_len]

  import orjson

  return event, session_id, orjson.loads(meta)


def test_start_session_supports_latest_doc_fields():
  config = RealtimeDialogueConfig(
    asr=RealtimeDialogueConfig.Asr(
      audio_info=RealtimeDialogueConfig.Asr.AudioInfo(
        format=RealtimeDialogueConfig.Asr.AudioInfo.Format.speech_opus,
        sample_rate=16000,
        channel=1,
      ),
      extra=RealtimeDialogueConfig.Asr.Extra(
        end_smooth_window_ms=1200,
        enable_custom_vad=True,
        enable_asr_twopass=True,
      ),
    ),
    dialog=RealtimeDialogueConfig.DialogConfig(
      bot_name='豆包',
      system_role='你是一个有帮助的助手。',
      speaking_style='简洁直接',
      character_manifest='角色设定',
      dialog_context=[
        RealtimeDialogueConfig.DialogConfig.DialogContextItem(
          role='user',
          text='你好',
        ),
        RealtimeDialogueConfig.DialogConfig.DialogContextItem(
          role='assistant',
          text='你好，请问有什么可以帮你？',
        ),
      ],
      extra=RealtimeDialogueConfig.DialogConfig.Extra(
        volc_websearch_type=RealtimeDialogueConfig.DialogConfig.Extra.VolcWebsearchType.web_agent,
        volc_websearch_bot_id='bot-id',
        input_mod=RealtimeDialogueConfig.DialogConfig.Extra.InputMod.audio_file,
        model=RealtimeDialogueConfig.DialogConfig.Extra.Model.model_o2_0,
      ),
    ),
  )

  payload = RealtimeDialogueFunctions.start_session_payload('session-1', config)
  event, session_id, meta = _decode_session_json_payload(payload)

  assert event == EventSend.StartSession.value
  assert session_id == 'session-1'
  assert meta['asr']['audio_info']['format'] == 'speech_opus'
  assert meta['asr']['extra']['enable_custom_vad'] is True
  assert meta['asr']['extra']['enable_asr_twopass'] is True
  assert meta['dialog']['character_manifest'] == '角色设定'
  assert meta['dialog']['extra']['model'] == '1.2.1.0'
  assert meta['dialog']['extra']['input_mod'] == 'audio_file'
  assert meta['dialog']['extra']['volc_websearch_type'] == 'web_agent'
  assert meta['dialog']['extra']['volc_websearch_bot_id'] == 'bot-id'


def test_dialog_context_requires_even_length():
  with pytest.raises(ValueError, match='dialog_context length must be an even'):
    RealtimeDialogueConfig(
      dialog=RealtimeDialogueConfig.DialogConfig(
        dialog_context=[
          RealtimeDialogueConfig.DialogConfig.DialogContextItem(
            role='user',
            text='single message',
          )
        ]
      )
    )


def test_chat_rag_text_payload_uses_event_502():
  request = ChatRAGTextRequest(external_rag='外部知识')
  payload = RealtimeDialogueFunctions.chat_rag_text_payload(
    'session-1', request
  )
  event, session_id, meta = _decode_session_json_payload(payload)

  assert event == EventSend.ChatRAGText.value
  assert session_id == 'session-1'
  assert meta == {'external_rag': '外部知识'}


def test_conversation_event_payloads_use_latest_event_ids():
  create_payload = RealtimeDialogueFunctions.conversation_create_payload(
    'session-1',
    ConversationCreateRequest(
      items=[ConversationCreateRequest.Item(role='user', text='q1')]
    ),
  )
  update_payload = RealtimeDialogueFunctions.conversation_update_payload(
    'session-1',
    ConversationUpdateRequest(
      items=[ConversationUpdateRequest.Item(item_id='id1', text='q1-new')]
    ),
  )
  retrieve_payload = RealtimeDialogueFunctions.conversation_retrieve_payload(
    'session-1',
    ConversationRetrieveRequest(
      items=[ConversationRetrieveRequest.Item(item_id='id1')]
    ),
  )
  delete_payload = RealtimeDialogueFunctions.conversation_delete_payload(
    'session-1',
    ConversationDeleteRequest(
      items=[ConversationDeleteRequest.Item(item_id='id1')]
    ),
  )

  create_event, _, create_meta = _decode_session_json_payload(create_payload)
  update_event, _, update_meta = _decode_session_json_payload(update_payload)
  retrieve_event, _, retrieve_meta = _decode_session_json_payload(
    retrieve_payload
  )
  delete_event, _, delete_meta = _decode_session_json_payload(delete_payload)

  assert create_event == EventSend.ConversationCreate.value
  assert update_event == EventSend.ConversationUpdate.value
  assert retrieve_event == EventSend.ConversationRetrieve.value
  assert delete_event == EventSend.ConversationDelete.value
  assert create_meta['items'][0]['role'] == 'user'
  assert update_meta['items'][0]['item_id'] == 'id1'
  assert retrieve_meta['items'][0]['item_id'] == 'id1'
  assert delete_meta['items'][0]['item_id'] == 'id1'


def test_asr_ended_response_accepts_empty_payload():
  response = ASREndedResponse.model_validate({})
  assert response.model_dump() == {
    'comfort_wait_time': None,
    'last_resp_cost_time': None,
    'no_content': None,
    'task_request_seq_id': None,
    'task_request_timestamp': None,
    'user_duration': 0,
  }


def test_chat_response_supports_question_and_reply_ids():
  response = ChatResponseModel.model_validate(
    {
      'content': '你好',
      'question_id': 'question-1',
      'reply_id': 'reply-1',
    }
  )
  assert response.question_id == 'question-1'
  assert response.reply_id == 'reply-1'

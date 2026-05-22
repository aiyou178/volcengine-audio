"""Tests for volcengine_audio.realtime module."""

import struct

import pytest

from volcengine_audio import (
  ASREndedResponse,
  ChatTextQueryRequest,
  ChatTTSTextRequest,
  ChatRAGTextRequest,
  ChatResponseModel,
  ConversationCreateRequest,
  ConversationDeleteRequest,
  ConversationRetrieveRequest,
  ConversationTruncateRequest,
  ConversationUpdateRequest,
  EventReceive,
  EventSend,
  RealtimeDialogueConfig,
  RealtimeDialogueFunctions,
  SayHelloRequest,
  UpdateConfigRequest,
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
        boosting_table_id='boost-1',
        boosting_table_name='boost-name',
        regex_correct_table_id='regex-1',
        regex_correct_table_name='regex-name',
        context=RealtimeDialogueConfig.Asr.Extra.Context(
          hotwords=[
            RealtimeDialogueConfig.Asr.Extra.Context.Hotword(word='豆包')
          ],
          correct_words={'旧词': '新词'},
        ),
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
        input_mod=RealtimeDialogueConfig.DialogConfig.Extra.InputMod.keep_alive,
        enable_loudness_norm=True,
        enable_conversation_truncate=True,
        enable_user_query_exit=True,
        model=RealtimeDialogueConfig.DialogConfig.Extra.Model.model_o2_0,
      ),
    ),
    tts=RealtimeDialogueConfig.TTSConfig(
      extra=RealtimeDialogueConfig.TTSConfig.Extra(
        explicit_dialect='sichuan',
        aigc_metadata=RealtimeDialogueConfig.TTSConfig.Extra.AIGCMetadata(
          enable=True,
          content_producer='producer',
          produce_id='produce-id',
          content_propagator='propagator',
          propagate_id='propagate-id',
        ),
      ),
      audio_config=RealtimeDialogueConfig.TTSConfig.AudioConfig(
        speech_rate=10,
        loudness_rate=5,
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
  assert meta['asr']['extra']['boosting_table_id'] == 'boost-1'
  assert meta['asr']['extra']['regex_correct_table_name'] == 'regex-name'
  assert meta['asr']['extra']['context']['correct_words'] == {'旧词': '新词'}
  assert meta['dialog']['character_manifest'] == '角色设定'
  assert meta['dialog']['extra']['model'] == '1.2.1.1'
  assert meta['dialog']['extra']['input_mod'] == 'keep_alive'
  assert meta['dialog']['extra']['enable_loudness_norm'] is True
  assert meta['dialog']['extra']['enable_conversation_truncate'] is True
  assert meta['dialog']['extra']['enable_user_query_exit'] is True
  assert meta['dialog']['extra']['volc_websearch_type'] == 'web_agent'
  assert meta['dialog']['extra']['volc_websearch_bot_id'] == 'bot-id'
  assert meta['tts']['extra']['explicit_dialect'] == 'sichuan'
  assert meta['tts']['extra']['aigc_metadata']['produce_id'] == 'produce-id'
  assert meta['tts']['audio_config']['speech_rate'] == 10
  assert meta['tts']['audio_config']['loudness_rate'] == 5


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
  with pytest.raises(ValueError, match='combined length'):
    RealtimeDialogueConfig(
      dialog=RealtimeDialogueConfig.DialogConfig(system_role='x' * 4001)
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


def test_connection_audio_and_text_payload_helpers_use_real_frames():
  start_connection = RealtimeDialogueFunctions.start_connection_payload()
  finish_connection = RealtimeDialogueFunctions.finish_connection_payload()
  finish_session = RealtimeDialogueFunctions.finish_session_payload('session-1')
  task_payload = RealtimeDialogueFunctions.task_request_payload(
    'session-1',
    b'audio',
  )
  say_hello_payload = RealtimeDialogueFunctions.say_hello_payload(
    'session-1',
    SayHelloRequest(content='hello'),
  )
  tts_payload = RealtimeDialogueFunctions.chat_tts_text_payload(
    'session-1',
    ChatTTSTextRequest(start=True, content='hello', end=True),
  )
  query_payload = RealtimeDialogueFunctions.chat_text_query_payload(
    'session-1',
    ChatTextQueryRequest(content='question'),
  )
  retrieve_payload = RealtimeDialogueFunctions.conversation_retrieve_payload(
    'session-1'
  )

  assert struct.unpack('>I', start_connection[4:8])[0] == (
    EventSend.StartConnection.value
  )
  assert struct.unpack('>I', finish_connection[4:8])[0] == (
    EventSend.FinishConnection.value
  )
  assert _decode_session_json_payload(finish_session) == (
    EventSend.FinishSession.value,
    'session-1',
    {},
  )
  assert (
    struct.unpack('>I', task_payload[4:8])[0] == EventSend.TaskRequest.value
  )
  assert task_payload.endswith(b'audio')
  assert _decode_session_json_payload(say_hello_payload)[2] == {
    'content': 'hello'
  }
  assert _decode_session_json_payload(tts_payload)[2] == {
    'start': True,
    'content': 'hello',
    'end': True,
  }
  assert _decode_session_json_payload(query_payload)[2] == {
    'content': 'question'
  }
  assert _decode_session_json_payload(retrieve_payload)[2] == {}


def test_new_control_event_payloads_match_latest_docs():
  update_payload = RealtimeDialogueFunctions.update_config_payload(
    'session-1',
    UpdateConfigRequest(
      tts=UpdateConfigRequest.TTS(speaker='zh_female_new'),
      dialog=UpdateConfigRequest.Dialog(dialog_id='dialog-1'),
    ),
  )
  end_asr_payload = RealtimeDialogueFunctions.end_asr_payload('session-1')
  interrupt_payload = RealtimeDialogueFunctions.client_interrupt_payload(
    'session-1'
  )

  update_event, _, update_meta = _decode_session_json_payload(update_payload)
  end_asr_event, _, end_asr_meta = _decode_session_json_payload(end_asr_payload)
  interrupt_event, _, interrupt_meta = _decode_session_json_payload(
    interrupt_payload
  )

  assert update_event == EventSend.UpdateConfig.value
  assert update_meta == {
    'tts': {'speaker': 'zh_female_new'},
    'dialog': {'dialog_id': 'dialog-1'},
  }
  assert end_asr_event == EventSend.EndASR.value
  assert end_asr_meta == {}
  assert interrupt_event == EventSend.ClientInterrupt.value
  assert interrupt_meta == {}


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
  truncate_payload = RealtimeDialogueFunctions.conversation_truncate_payload(
    'session-1',
    ConversationTruncateRequest(item_id='id1', audio_end_ms=1200),
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
  truncate_event, _, truncate_meta = _decode_session_json_payload(
    truncate_payload
  )
  delete_event, _, delete_meta = _decode_session_json_payload(delete_payload)

  assert create_event == EventSend.ConversationCreate.value
  assert update_event == EventSend.ConversationUpdate.value
  assert retrieve_event == EventSend.ConversationRetrieve.value
  assert truncate_event == EventSend.ConversationTruncate.value
  assert delete_event == EventSend.ConversationDelete.value
  assert create_meta['items'][0]['role'] == 'user'
  assert update_meta['items'][0]['item_id'] == 'id1'
  assert retrieve_meta['items'][0]['item_id'] == 'id1'
  assert truncate_meta == {'item_id': 'id1', 'audio_end_ms': 1200}
  assert delete_meta['items'][0]['item_id'] == 'id1'


def test_realtime_event_enums_include_latest_ack_ids():
  assert EventReceive.ConfigUpdated.value == 251
  assert EventReceive.ConversationTruncated.value == 570


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

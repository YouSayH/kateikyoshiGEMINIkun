# import os
# import re
# import fitz
# from PIL import Image
# from PySide6.QtCore import QObject, Slot, QTimer, Qt, QThread, Signal
# from PySide6.QtWidgets import QListWidgetItem
# from typing import Optional, List, Dict

# from .database_manager import DatabaseManager
# from .context_manager import ContextManager
# from .settings_manager import SettingsManager
# from .database_worker import DatabaseWorker
# from .visual_observer import VisualObserverWorker
# from ..hardware.camera_handler import CameraWorker
# from ..hardware.audio_handler import TTSWorker, STTWorker
# from ..ui.main_window import MainWindow
# from ..ui.settings_dialog import SettingsDialog
# from .gemini_client import GeminiClient

# class FileProcessingWorker(QThread):
#     finished_processing = Signal(str)
#     def __init__(self, file_path, gemini_client, parent=None):
#         super().__init__(parent)
#         self.file_path = file_path
#         self.gemini_client = gemini_client
#     def run(self):
#         images = []
#         file_path_lower = self.file_path.lower()
#         try:
#             if file_path_lower.endswith('.pdf'):
#                 doc = fitz.open(self.file_path)
#                 for page in doc:
#                     pix = page.get_pixmap(dpi=150)
#                     img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
#                     images.append(img)
#                 doc.close()
#             elif file_path_lower.endswith(('.png', '.jpg', '.jpeg', '.webp')):
#                 images.append(Image.open(self.file_path).convert("RGB"))
#             else:
#                 self.finished_processing.emit("サポートされていない形式です。")
#                 return
#             if not images:
#                 self.finished_processing.emit("画像を変換できませんでした。")
#                 return
#             prompt = "この画像は学習教材です。含まれるテキストや数式を正確に書き出してください。"
#             self.finished_processing.emit(self.gemini_client.generate_vision_response([prompt] + images))
#         except Exception as e:
#             self.finished_processing.emit(f"ファイル処理エラー: {e}")

# class GeminiWorker(QThread):
#     response_ready = Signal(str)
#     def __init__(self, prompt, model_name=None, parent=None):
#         super().__init__(parent)
#         self.prompt = prompt
#         self.gemini_client = GeminiClient(text_model_name=model_name)
#     def run(self):
#         self.response_ready.emit(self.gemini_client.generate_response(self.prompt))

# class GeminiVisionWorker(QThread):
#     response_ready = Signal(str)
#     def __init__(self, prompt_parts, model_name=None, parent=None):
#         super().__init__(parent)
#         self.prompt_parts = prompt_parts
#         self.gemini_client = GeminiClient(vision_model_name=model_name)
#     def run(self):
#         self.response_ready.emit(self.gemini_client.generate_vision_response(self.prompt_parts))


# class AppController(QObject):
#     def __init__(self, main_window: MainWindow):
#         super().__init__()
        
#         self.main_window = main_window
#         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
#         db_path = os.path.join(project_root, "data", "sessions.db")
#         self.db_manager = DatabaseManager(db_path)
#         self.context_manager = ContextManager()
#         self.settings_manager = SettingsManager()

#         self.db_worker = DatabaseWorker(self.db_manager)
#         self.tts_worker = TTSWorker()
#         self.stt_worker: Optional[STTWorker] = None
#         self.camera_worker: Optional[CameraWorker] = None
#         self.observer_worker: Optional[VisualObserverWorker] = None
#         self.file_worker: Optional[FileProcessingWorker] = None
#         self.ai_worker: Optional[QThread] = None
#         self.keyword_extraction_worker: Optional[GeminiWorker] = None
#         self.query_keyword_worker: Optional[GeminiWorker] = None
#         self.title_generation_worker: Optional[GeminiWorker] = None
#         self.summary_generation_worker: Optional[GeminiWorker] = None
        
#         self.active_session_id: Optional[int] = None
#         self.current_chat_messages: List[Dict[str, str]] = []
#         self.latest_camera_frame: Optional[Image.Image] = None
#         self.is_ai_task_running = False
#         self.stt_was_enabled_before_tts = False
        
#         self.last_scrolled_anchor = ""
#         self.user_has_scrolled = False

#         self.session_post_process_timer = QTimer(self)
#         self.session_post_process_timer.setSingleShot(True)
        
#         self._connect_signals()

#     def start_up(self):
#         self.start_essential_workers()
#         self.restart_stt_worker()
#         self.load_and_display_sessions()
        
#         if self.settings_manager.camera_enabled_on_startup:
#             self.main_window.chat_panel.set_camera_checkbox_state(True)
#         else:
#             self.main_window.chat_panel.set_camera_checkbox_state(False)
#             self.main_window.camera_panel.set_text("カメラはオフです")

#     def _connect_signals(self):
#         self.main_window.session_panel.new_session_requested.connect(self.create_new_session)
#         self.main_window.session_panel.session_selected.connect(self.on_session_changed)
#         self.main_window.chat_panel.message_sent.connect(self.start_user_request)
#         self.main_window.chat_panel.load_file_requested.connect(self.main_window.open_file_dialog)
#         self.main_window.chat_panel.stop_speech_requested.connect(self.on_stop_speech_button_clicked)
#         self.main_window.chat_panel.camera_toggled.connect(self.on_camera_enabled_changed)
#         self.main_window.chat_panel.stt_toggled.connect(self.on_stt_enabled_changed)
#         self.tts_worker.speech_finished.connect(self.on_speech_finished)
        
#         scroll_bar = self.main_window.chat_panel.ai_output_view.verticalScrollBar()
#         scroll_bar.actionTriggered.connect(self._user_scrolled)

#     def start_essential_workers(self):
#         self.db_worker.start()
#         self.tts_worker.start()
    
#     def start_camera_dependent_workers(self):
#         self.stop_camera_dependent_workers() 
#         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
#         model_path = os.path.join(project_root, "models", "best12-2.pt")
#         self.camera_worker = CameraWorker(
#             model_path=model_path,
#             device_index=self.settings_manager.camera_device_index,
#             stop_threshold_sec=self.settings_manager.hand_stop_threshold
#         )
#         self.observer_worker = VisualObserverWorker(
#             interval_sec=self.settings_manager.observation_interval
#         )
#         self.camera_worker.frame_data_ready.connect(self.main_window.update_camera_view)
#         self.camera_worker.hand_stopped_signal.connect(self.on_hand_stopped)
#         self.camera_worker.raw_frame_for_observation.connect(self.observer_worker.update_frame)
#         self.observer_worker.observation_ready.connect(self.on_observation_received)
#         self.camera_worker.start()
#         self.observer_worker.start()

#     def stop_camera_dependent_workers(self):
#         if self.camera_worker and self.camera_worker.isRunning():
#             self.camera_worker.frame_data_ready.disconnect(self.main_window.update_camera_view)
#             self.camera_worker.hand_stopped_signal.disconnect(self.on_hand_stopped)
#             self.camera_worker.raw_frame_for_observation.disconnect(self.observer_worker.update_frame)
#             self.camera_worker.stop()
#             self.camera_worker.wait()
#             self.camera_worker = None
#         if self.observer_worker and self.observer_worker.isRunning():
#             self.observer_worker.stop()
#             self.observer_worker.wait()
#             self.observer_worker = None

#     def restart_stt_worker(self):
#         if self.stt_worker and self.stt_worker.isRunning():
#             self.stt_worker.monologue_recognized.disconnect(self.on_monologue_recognized)
#             self.stt_worker.command_recognized.disconnect(self.on_command_recognized)
#             self.stt_worker.stop()
#             self.stt_worker.wait()
#         self.stt_worker = STTWorker(device_index=self.settings_manager.mic_device_index)
#         self.stt_worker.monologue_recognized.connect(self.on_monologue_recognized)
#         self.stt_worker.command_recognized.connect(self.on_command_recognized)
#         self.stt_worker.set_enabled(self.main_window.chat_panel.get_stt_checkbox_state())
#         self.stt_worker.start()
        
#     def open_settings_dialog(self):
#         dialog = SettingsDialog(self.main_window)
#         if dialog.exec():
#             self.apply_settings_dynamically()
#             self.restart_stt_worker()
#             if self.main_window.chat_panel.get_camera_checkbox_state():
#                 self.start_camera_dependent_workers()
            
#     def apply_settings_dynamically(self):
#         if self.tts_worker and self.tts_worker.isRunning():
#             self.tts_worker.set_tts_enabled(self.settings_manager.tts_enabled)
#             self.tts_worker.set_tts_rate(self.settings_manager.tts_rate)
#         if self.camera_worker and self.camera_worker.isRunning():
#             self.camera_worker.set_stop_threshold(self.settings_manager.hand_stop_threshold)
#         if self.observer_worker and self.observer_worker.isRunning():
#             self.observer_worker.set_observation_interval(self.settings_manager.observation_interval)

#     @Slot()
#     def _user_scrolled(self):
#         self.user_has_scrolled = True

#     @Slot()
#     def create_new_session(self):
#         session_id = self.db_manager.create_new_session()
#         self.load_and_display_sessions()
#         for i in range(self.main_window.session_panel.count()):
#             item = self.main_window.session_panel.item(i)
#             if item.data(Qt.UserRole) == session_id:
#                 self.main_window.session_panel.set_current_row(i)
#                 break
    
#     @Slot(QListWidgetItem, QListWidgetItem)
#     def on_session_changed(self, current_item, previous_item):
#         self.session_post_process_timer.stop()
#         if previous_item:
#             previous_session_id = previous_item.data(Qt.UserRole)
#             self.session_post_process_timer.timeout.connect(lambda: self._run_session_post_processing(previous_session_id))
#             self.session_post_process_timer.start(2000)
#         if not current_item: return
#         session_id = current_item.data(Qt.UserRole)
#         if session_id == self.active_session_id: return
#         self.active_session_id = session_id
#         session_details = self.db_manager.get_session_details(session_id)
#         if session_details:
#             self.context_manager.set_problem_context(session_details.get("problem_context"))
#             self.context_manager.set_chat_summary(session_details.get("chat_summary"))
#         self.current_chat_messages = self.db_manager.get_messages_for_session(self.active_session_id)
#         self.main_window.update_chat_display(self.current_chat_messages)
        
#     @Slot(str)
#     def start_user_request(self, user_query: str):
#         if not (user_query and self.active_session_id): return
#         self._add_message_to_ui_and_db("user", user_query, is_user_request=True)
#         self.is_ai_task_running = True
#         self.main_window.chat_panel.set_thinking_mode(True)
#         self._trigger_summary_generation(self.active_session_id)
#         prompt = f"""以下の質問文から、中心となるキーワードを3つ、カンマ区切りで抽出してください。思考プロセスは不要です。キーワードのみを出力してください。\n例: 積分、グラフ、面積\n\n---\n{user_query}"""
#         model_name = self.settings_manager.keyword_extraction_model
#         self.query_keyword_worker = GeminiWorker(prompt, model_name=model_name)
#         self.query_keyword_worker.response_ready.connect(lambda keywords: self.on_query_keywords_extracted(user_query, keywords))
#         self.query_keyword_worker.finished.connect(self.on_query_keyword_worker_finished)
#         self.query_keyword_worker.start()

#     @Slot(bool)
#     def on_camera_enabled_changed(self, enabled: bool):
#         if enabled:
#             self.start_camera_dependent_workers()
#         else:
#             self.stop_camera_dependent_workers()
#             self.main_window.camera_panel.set_text("カメラはオフです")
#             self.latest_camera_frame = None

#     @Slot(bool)
#     def on_stt_enabled_changed(self, enabled: bool):
#         if self.stt_worker:
#             self.stt_worker.set_enabled(enabled)

#     @Slot()
#     def on_stop_speech_button_clicked(self):
#         self.tts_worker.stop_current_speech()

#     def _run_session_post_processing(self, session_id: int):
#         print(f"セッションID {session_id} の後処理（キーワード、タイトル、要約）を開始します。")
#         self._trigger_keyword_extraction(session_id)
#         self._trigger_title_generation(session_id)
#         self._trigger_summary_generation(session_id)

#     def _trigger_summary_generation(self, session_id: int):
#         if not session_id: return
#         if self.summary_generation_worker and self.summary_generation_worker.isRunning(): return
#         messages = self.db_manager.get_messages_for_session(session_id)
#         user_message_count = sum(1 for msg in messages if msg['role'] == 'user')
#         if user_message_count < 5: return
#         conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
#         prompt = f"""以下の会話履歴を、第三者の視点から重要なポイントを箇条書きで3〜5点にまとめてください。\n\n---\n{conversation_text}"""
#         model_name = self.settings_manager.keyword_extraction_model
#         self.summary_generation_worker = GeminiWorker(prompt, model_name=model_name)
#         self.summary_generation_worker.response_ready.connect(lambda summary: self.on_summary_generated(session_id, summary))
#         self.summary_generation_worker.finished.connect(self.on_summary_worker_finished)
#         self.summary_generation_worker.start()

#     def _trigger_keyword_extraction(self, session_id: int):
#         if not session_id: return
#         if self.keyword_extraction_worker and self.keyword_extraction_worker.isRunning(): return
#         messages = self.db_manager.get_messages_for_session(session_id)
#         if len(messages) < 4: return
#         conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
#         prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
#         prompt = prompt_template.format(conversation_text=conversation_text)
#         model_name = self.settings_manager.keyword_extraction_model
#         self.keyword_extraction_worker = GeminiWorker(prompt, model_name=model_name)
#         self.keyword_extraction_worker.response_ready.connect(lambda keywords: self.on_keywords_extracted(session_id, keywords))
#         self.keyword_extraction_worker.finished.connect(self.on_keyword_worker_finished)
#         self.keyword_extraction_worker.start()

#     def _trigger_title_generation(self, session_id: int):
#         if not session_id: return
#         if self.title_generation_worker and self.title_generation_worker.isRunning(): return
#         messages = self.db_manager.get_messages_for_session(session_id)
#         if len(messages) < 4: return
#         conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
#         prompt_template = self.settings_manager.title_generation_prompt
#         prompt = prompt_template.format(conversation_text=conversation_text)
#         model_name = self.settings_manager.keyword_extraction_model
#         self.title_generation_worker = GeminiWorker(prompt, model_name=model_name)
#         self.title_generation_worker.response_ready.connect(lambda title: self.on_title_generated(session_id, title))
#         self.title_generation_worker.finished.connect(self.on_title_generation_finished)
#         self.title_generation_worker.start()
        
#     def load_and_display_sessions(self):
#         sessions = self.db_manager.get_all_sessions()
#         if not sessions:
#             self.create_new_session()
#             return
#         session_data = [{'id': s[0], 'title': s[1]} for s in sessions]
#         self.main_window.load_and_display_sessions(session_data)

#     def _add_message_to_ui_and_db(self, role: str, content: str, is_user_request=False):
#         if not self.active_session_id: return
#         message_id = f"{role}_{len(self.current_chat_messages)}"
#         self.current_chat_messages.append({"role": role, "content": content, "id": message_id})
#         self.main_window.update_chat_display(self.current_chat_messages)
#         self.db_worker.add_message(self.active_session_id, role, content)
#         if is_user_request:
#             self.user_has_scrolled = False
#             self.last_scrolled_anchor = ""
        
#     def set_latest_camera_frame(self, frame: Image.Image):
#         self.latest_camera_frame = frame
        
#     @Slot(str)
#     def on_monologue_recognized(self, text: str):
#         if self.active_session_id:
#             self.db_worker.add_log(self.active_session_id, "monologue", text)
#         self.main_window.chat_panel.append_to_input(text)
        
#     @Slot()
#     def on_speech_finished(self):
#         self.is_ai_task_running = False
#         self.main_window.chat_panel.show_stop_speech_button(False)
#         if self.stt_was_enabled_before_tts:
#             self.main_window.chat_panel.set_stt_checkbox_state(True)
        
#     @Slot()
#     def on_ai_worker_finished(self):
#         if self.ai_worker:
#             self.ai_worker.deleteLater()
#             self.ai_worker = None

#     @Slot(str, str)
#     def on_query_keywords_extracted(self, original_query: str, keywords_response: str):
#         match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
#         cleaned_keywords_str = match.group(1).strip() if match else keywords_response.strip()
#         cleaned_keywords = [kw.strip() for kw in cleaned_keywords_str.split(',') if kw.strip()]
#         if not self.active_session_id: return
        
#         relevant_sessions = self.db_manager.find_relevant_sessions(cleaned_keywords, exclude_session_id=self.active_session_id)
#         long_term_context = self._get_long_term_context(relevant_sessions)
#         monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
#         observation_log = self.db_manager.get_recent_logs_for_session(self.active_session_id, "observation", 5)
        
#         full_prompt = self.context_manager.build_prompt_for_query(original_query, self.current_chat_messages[-5:], monologue_history, observation_log, long_term_context)
#         self.execute_ai_task(full_prompt, speak=True, is_user_request=True, is_continuation=True)

#     @Slot()
#     def on_query_keyword_worker_finished(self):
#         if self.query_keyword_worker:
#             self.query_keyword_worker.deleteLater()
#             self.query_keyword_worker = None
            
#     def process_file(self, file_path: str):
#         self._add_message_to_ui_and_db("ai", f"`{os.path.basename(file_path)}`を分析中...")
#         model_name = self.settings_manager.vision_model
#         gemini_client_for_file = GeminiClient(vision_model_name=model_name)
#         self.file_worker = FileProcessingWorker(file_path, gemini_client_for_file)
#         self.file_worker.finished_processing.connect(self.on_file_processed)
#         self.file_worker.finished.connect(self.on_file_worker_finished)
#         self.file_worker.start()
        
#     @Slot(str)
#     def on_file_processed(self, result_text: str):
#         if not self.active_session_id: return
#         self.db_worker.update_problem_context(self.active_session_id, result_text)
#         self.context_manager.set_problem_context(result_text)
#         message = f"ファイルの分析が完了しました。\n\n**【分析結果】**\n\n{result_text}\n\n---\nこの問題について質問してください。"
#         self._add_message_to_ui_and_db("ai", message)
#         self.tts_worker.speak("ファイルの分析が完了しました。")

#     @Slot()
#     def on_file_worker_finished(self):
#         if self.file_worker:
#             self.file_worker.deleteLater()
#             self.file_worker = None

#     @Slot(Image.Image)
#     def on_hand_stopped(self, captured_image: Image.Image):
#         if self.is_ai_task_running: return
#         self.context_manager.set_triggered_image(captured_image)
#         prompt = self.settings_manager.hand_stopped_prompt
#         self.execute_ai_task(prompt, speak=True)

#     @Slot(str)
#     def on_command_recognized(self, command_text: str):
#         if not self.active_session_id:
#             self.tts_worker.speak("すみません、現在アクティブなセッションがありません。")
#             return
#         if not self.latest_camera_frame:
#             self.tts_worker.speak("すみません、カメラの映像が取得できていません。")
#             return
        
#         self._add_message_to_ui_and_db("user", f"（音声コマンド）{command_text}")
#         self.context_manager.set_triggered_image(self.latest_camera_frame.copy())
#         self.is_ai_task_running = True
#         self.main_window.chat_panel.set_thinking_mode(True)
#         long_term_context = self._get_long_term_context([])
#         monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
#         prompt_parts = self.context_manager.build_prompt_parts_for_command(
#             command_text, self.current_chat_messages[-5:], monologue_history, long_term_context
#         )
#         if prompt_parts:
#             self.execute_ai_task(prompt_parts, speak=True, is_user_request=False, use_vision=True, is_continuation=True)
#         else:
#             self.tts_worker.speak("コマンドの準備に失敗しました。")
#             self.is_ai_task_running = False
#             self.main_window.chat_panel.set_thinking_mode(False)

#     @Slot(str)
#     def on_observation_received(self, observation_text: str):
#         if self.active_session_id:
#             self.db_worker.add_log(self.active_session_id, "observation", observation_text)

#     @Slot(int, str)
#     def on_title_generated(self, session_id: int, title: str):
#         cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
#         self.db_worker.update_session_title(session_id, cleaned_title)
#         self.main_window.session_panel.update_item_text(session_id, cleaned_title)

#     @Slot(int, str)
#     def on_keywords_extracted(self, session_id: int, keywords_response: str):
#         match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
#         cleaned_keywords = match.group(1).strip() if match else keywords_response.strip()
#         cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
#         self.db_worker.update_session_keywords(session_id, cleaned_keywords)
        
#     @Slot()
#     def on_title_generation_finished(self):
#         if self.title_generation_worker:
#             self.title_generation_worker.deleteLater()
#             self.title_generation_worker = None
    
#     @Slot()
#     def on_keyword_worker_finished(self):
#         if self.keyword_extraction_worker:
#             self.keyword_extraction_worker.deleteLater()
#             self.keyword_extraction_worker = None

#     @Slot(int, str)
#     def on_summary_generated(self, session_id: int, summary: str):
#         if not summary.strip() or "エラー" in summary:
#             print(f"要約の生成に失敗または空の応答: {summary}")
#             return
#         if session_id == self.active_session_id:
#             self.context_manager.set_chat_summary(summary)
#         self.db_worker.update_session_summary(session_id, summary)

#     @Slot()
#     def on_summary_worker_finished(self):
#         if self.summary_generation_worker:
#             self.summary_generation_worker.deleteLater()
#             self.summary_generation_worker = None
            
#     def _get_long_term_context(self, relevant_sessions: List[Dict]) -> str:
#         if not relevant_sessions:
#             last_session_id = self.db_manager.get_last_active_session_id(exclude_session_id=self.active_session_id)
#             if not last_session_id: return "これが最初のセッションです。"
#             last_session_details = self.db_manager.get_session_details(last_session_id)
#             if not last_session_details: return "前回のセッション情報を取得できませんでした。"
#             last_messages = self.db_manager.get_messages_for_session(last_session_id)
#             last_user_message = next((msg['content'] for msg in reversed(last_messages) if msg['role'] == 'user'), "なし")
#             return f"（直近のセッションより）\n- 前回（{last_session_details['last_updated_at']}）のセッションでは、「{last_session_details['title']}」について学習しており、最後の質問は「{last_user_message}」でした。"
        
#         context_lines = ["（過去の関連セッションより）"]
#         for session in relevant_sessions:
#             line = f"- セッション「{session['title']}」（{session['last_updated_at']}）では、キーワード「{session['keywords']}」について議論しました。"
#             context_lines.append(line)
#         return "\n".join(context_lines)
            
#     def execute_ai_task(self, prompt, speak=True, is_user_request=False, use_vision=False, is_continuation=False):
#         if self.is_ai_task_running and not is_continuation: return
#         if not is_continuation:
#             self.is_ai_task_running = True
#             self.main_window.chat_panel.set_thinking_mode(True)
#         if speak:
#             self.main_window.chat_panel.show_stop_speech_button(True)
#         if use_vision:
#             model_name = self.settings_manager.vision_model
#             self.ai_worker = GeminiVisionWorker(prompt, model_name=model_name)
#         else:
#             model_name = self.settings_manager.main_response_model
#             self.ai_worker = GeminiWorker(prompt, model_name=model_name)
#         self.ai_worker.response_ready.connect(lambda r: self.handle_gemini_response(r, speak))
#         self.ai_worker.finished.connect(self.on_ai_worker_finished)
#         self.ai_worker.start()

#     def handle_gemini_response(self, response_text, speak):
#         self.main_window.chat_panel.set_thinking_mode(False)
#         self._add_message_to_ui_and_db("ai", response_text)
        
#         user_comment_anchor = ""
#         for msg in reversed(self.current_chat_messages):
#             if msg['role'] == 'user':
#                 user_comment_anchor = msg.get('id', '')
#                 break
        
#         if user_comment_anchor and self.last_scrolled_anchor != user_comment_anchor and not self.user_has_scrolled:
#             self.main_window.chat_panel.ai_output_view.scrollToAnchor(user_comment_anchor)
#             self.last_scrolled_anchor = user_comment_anchor
            
#         if speak:
#             self.stt_was_enabled_before_tts = self.main_window.chat_panel.get_stt_checkbox_state()
#             if self.stt_was_enabled_before_tts:
#                 self.main_window.chat_panel.set_stt_checkbox_state(False)
#             self.tts_worker.speak(response_text)
#         else:
#             self.is_ai_task_running = False
#             self.main_window.chat_panel.show_stop_speech_button(False)
            
#     def shutdown(self):
#         print("アプリケーションの終了処理を開始します...")
#         if self.is_ai_task_running and self.ai_worker:
#             self.ai_worker.wait(5000)
#         self.stop_camera_dependent_workers()
#         if self.stt_worker and self.stt_worker.isRunning():
#             self.main_window.chat_panel.stt_toggled.disconnect(self.on_stt_enabled_changed)
#             self.stt_worker.stop()
#             self.stt_worker.wait()
#         if self.tts_worker and self.tts_worker.isRunning():
#             self.tts_worker.stop()
#             self.tts_worker.wait()
#         if self.active_session_id:
#             self._run_session_post_processing(self.active_session_id)
#             self.session_post_process_timer.stop()
#         if self.db_worker and self.db_worker.isRunning():
#             while self.db_worker.tasks:
#                 QTimer.singleShot(100, lambda: None)
#             self.db_worker.stop()
#             self.db_worker.wait()
#         print("すべての処理が安全に完了しました。")















# # # # # # # # 設定変更(再起不要版)


# # # # # # # import sys
# # # # # # # import os
# # # # # # # import fitz
# # # # # # # import re
# # # # # # # from PIL import Image
# # # # # # # from PySide6.QtCore import QThread, Signal, Slot, QSize, Qt
# # # # # # # from PySide6.QtGui import QPixmap, QImage, QTextCursor, QMovie, QPainter, QColor, QPen, QFont, QAction
# # # # # # # from PySide6.QtWidgets import (
# # # # # # #     QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLabel,
# # # # # # #     QHBoxLayout, QCheckBox, QFileDialog, QStackedLayout, 
# # # # # # #     QListWidget, QListWidgetItem, QSplitter
# # # # # # # )
# # # # # # # from typing import Optional, List, Dict

# # # # # # # from .widgets.md_view import MarkdownView
# # # # # # # from .settings_dialog import SettingsDialog
# # # # # # # from ..core.context_manager import ContextManager
# # # # # # # from ..core.gemini_client import GeminiClient
# # # # # # # from ..core.database_manager import DatabaseManager
# # # # # # # from ..core.database_worker import DatabaseWorker
# # # # # # # from ..core.visual_observer import VisualObserverWorker
# # # # # # # from ..core.settings_manager import SettingsManager
# # # # # # # from ..hardware.camera_handler import CameraWorker
# # # # # # # from ..hardware.audio_handler import TTSWorker, STTWorker

# # # # # # # # --- ワーカースレッド定義 ---
# # # # # # # class FileProcessingWorker(QThread):
# # # # # # #     finished_processing = Signal(str)
# # # # # # #     def __init__(self, file_path, gemini_client, parent=None):
# # # # # # #         super().__init__(parent)
# # # # # # #         self.file_path = file_path
# # # # # # #         self.gemini_client = gemini_client
# # # # # # #     def run(self):
# # # # # # #         images = []
# # # # # # #         file_path_lower = self.file_path.lower()
# # # # # # #         try:
# # # # # # #             if file_path_lower.endswith('.pdf'):
# # # # # # #                 doc = fitz.open(self.file_path)
# # # # # # #                 for page in doc:
# # # # # # #                     pix = page.get_pixmap(dpi=150)
# # # # # # #                     img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
# # # # # # #                     images.append(img)
# # # # # # #                 doc.close()
# # # # # # #             elif file_path_lower.endswith(('.png', '.jpg', '.jpeg', '.webp')):
# # # # # # #                 images.append(Image.open(self.file_path).convert("RGB"))
# # # # # # #             else:
# # # # # # #                 self.finished_processing.emit("サポートされていない形式です。")
# # # # # # #                 return
# # # # # # #             if not images:
# # # # # # #                 self.finished_processing.emit("画像を変換できませんでした。")
# # # # # # #                 return
# # # # # # #             prompt = "この画像は学習教材です。含まれるテキストや数式を正確に書き出してください。"
# # # # # # #             self.finished_processing.emit(self.gemini_client.generate_vision_response([prompt] + images))
# # # # # # #         except Exception as e:
# # # # # # #             self.finished_processing.emit(f"ファイル処理エラー: {e}")

# # # # # # # class GeminiWorker(QThread):
# # # # # # #     response_ready = Signal(str)
# # # # # # #     def __init__(self, prompt, model_name=None, parent=None):
# # # # # # #         super().__init__(parent)
# # # # # # #         self.prompt = prompt
# # # # # # #         self.gemini_client = GeminiClient(text_model_name=model_name)
# # # # # # #     def run(self):
# # # # # # #         self.response_ready.emit(self.gemini_client.generate_response(self.prompt))

# # # # # # # class GeminiVisionWorker(QThread):
# # # # # # #     response_ready = Signal(str)
# # # # # # #     def __init__(self, prompt_parts, model_name=None, parent=None):
# # # # # # #         super().__init__(parent)
# # # # # # #         self.prompt_parts = prompt_parts
# # # # # # #         self.gemini_client = GeminiClient(vision_model_name=model_name)
# # # # # # #     def run(self):
# # # # # # #         self.response_ready.emit(self.gemini_client.generate_vision_response(self.prompt_parts))

# # # # # # # # --- メインウィンドウ ---
# # # # # # # class MainWindow(QMainWindow):
# # # # # # #     def __init__(self):
# # # # # # #         super().__init__()
# # # # # # #         self.setWindowTitle("勉強アシストアプリ")
# # # # # # #         self.setGeometry(100, 100, 1600, 900)
        
# # # # # # #         self.is_ai_task_running = False
# # # # # # #         self.context_manager = ContextManager()
# # # # # # #         self.settings_manager = SettingsManager()
# # # # # # #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# # # # # # #         db_path = os.path.join(project_root, "data", "sessions.db")
# # # # # # #         self.db_manager = DatabaseManager(db_path=db_path)
# # # # # # #         self.active_session_id: Optional[int] = None
# # # # # # #         self.latest_camera_frame: Optional[Image.Image] = None

# # # # # # #         self.camera_worker: Optional[CameraWorker] = None
# # # # # # #         self.file_worker: Optional[FileProcessingWorker] = None
# # # # # # #         self.db_worker = DatabaseWorker(self.db_manager)
# # # # # # #         self.keyword_extraction_worker: Optional[GeminiWorker] = None
# # # # # # #         self.query_keyword_worker: Optional[GeminiWorker] = None
# # # # # # #         self.title_generation_worker: Optional[GeminiWorker] = None

# # # # # # #         self.current_chat_messages: List[Dict[str, str]] = []
# # # # # # #         self.stt_was_enabled_before_tts = False

# # # # # # #         # UIレイアウト
# # # # # # #         session_area_widget = QWidget()
# # # # # # #         session_layout = QVBoxLayout(session_area_widget)
# # # # # # #         self.new_session_button = QPushButton("＋ 新しいチャット")
# # # # # # #         self.session_list_widget = QListWidget()
# # # # # # #         session_layout.addWidget(self.new_session_button)
# # # # # # #         session_layout.addWidget(self.session_list_widget)

# # # # # # #         main_chat_widget = QWidget()
# # # # # # #         left_layout = QVBoxLayout(main_chat_widget)
# # # # # # #         self.ai_output_view = MarkdownView()
# # # # # # #         self.user_input = QTextEdit()
# # # # # # #         self.send_button = QPushButton("送信")
# # # # # # #         self.stt_enabled_checkbox = QCheckBox("音声認識")
# # # # # # #         self.load_file_button = QPushButton("問題ファイルを読み込む")
# # # # # # #         self.stop_speech_button = QPushButton("読み上げを停止")
# # # # # # #         self.stop_speech_button.setVisible(False)

# # # # # # #         loading_widget = QWidget()
# # # # # # #         loading_layout = QHBoxLayout(loading_widget)
# # # # # # #         loading_layout.setContentsMargins(0, 5, 0, 5)
# # # # # # #         self.loading_movie_label = QLabel()
# # # # # # #         loading_gif_path = os.path.join(project_root, "assets", "loading.gif")
# # # # # # #         if os.path.exists(loading_gif_path):
# # # # # # #             self.movie = QMovie(loading_gif_path)
# # # # # # #             self.loading_movie_label.setMovie(self.movie)
# # # # # # #             self.movie.setScaledSize(QSize(25, 25))
# # # # # # #         self.loading_text_label = QLabel("AIが考え中です...")
# # # # # # #         loading_layout.addStretch()
# # # # # # #         loading_layout.addWidget(self.loading_movie_label)
# # # # # # #         loading_layout.addWidget(self.loading_text_label)
# # # # # # #         loading_layout.addStretch()

# # # # # # #         self.header_stack = QStackedLayout()
# # # # # # #         self.header_stack.addWidget(QLabel("AIアシスタント"))
# # # # # # #         self.header_stack.addWidget(loading_widget)

# # # # # # #         top_button_layout = QHBoxLayout()
# # # # # # #         top_button_layout.addWidget(self.load_file_button)
# # # # # # #         top_button_layout.addStretch()
# # # # # # #         self.camera_enabled_checkbox = QCheckBox("カメラを有効にする")
# # # # # # #         top_button_layout.addWidget(self.camera_enabled_checkbox)
# # # # # # #         top_button_layout.addWidget(self.stt_enabled_checkbox)

# # # # # # #         button_v_layout = QVBoxLayout()
# # # # # # #         button_v_layout.addWidget(self.send_button)
# # # # # # #         button_v_layout.addWidget(self.stop_speech_button)

# # # # # # #         input_area_layout = QHBoxLayout()
# # # # # # #         input_area_layout.addWidget(self.user_input)
# # # # # # #         input_area_layout.addLayout(button_v_layout)

# # # # # # #         left_layout.addLayout(top_button_layout)
# # # # # # #         left_layout.addLayout(self.header_stack)
# # # # # # #         left_layout.addWidget(self.ai_output_view, stretch=1)
# # # # # # #         left_layout.addWidget(QLabel("質問や独り言を入力"))
# # # # # # #         left_layout.addLayout(input_area_layout)

# # # # # # #         right_widget = QWidget()
# # # # # # #         right_layout = QVBoxLayout(right_widget)
# # # # # # #         self.camera_view = QLabel("カメラを初期化中...")
# # # # # # #         self.camera_view.setStyleSheet("background-color: black; color: white;")
# # # # # # #         self.camera_view.setFixedSize(640, 480)
# # # # # # #         right_layout.addWidget(self.camera_view)
# # # # # # #         right_layout.addStretch()

# # # # # # #         splitter = QSplitter(Qt.Horizontal)
# # # # # # #         splitter.addWidget(session_area_widget)
# # # # # # #         splitter.addWidget(main_chat_widget)
# # # # # # #         splitter.addWidget(right_widget)
# # # # # # #         splitter.setSizes([250, 750, 600])
# # # # # # #         self.setCentralWidget(splitter)
        
# # # # # # #         self.create_menu()
        
# # # # # # #         self.tts_worker = TTSWorker()
# # # # # # #         self.stt_worker = STTWorker(
# # # # # # #             device_index=self.settings_manager.mic_device_index
# # # # # # #         )
# # # # # # #         self.observer_worker = VisualObserverWorker(
# # # # # # #             interval_sec=self.settings_manager.observation_interval
# # # # # # #         )
        
# # # # # # #         self.new_session_button.clicked.connect(self.create_new_session)
# # # # # # #         self.session_list_widget.currentItemChanged.connect(self.on_session_changed)
# # # # # # #         self.send_button.clicked.connect(self.start_user_request)
# # # # # # #         self.load_file_button.clicked.connect(self.open_file_dialog)
# # # # # # #         self.stop_speech_button.clicked.connect(self.on_stop_speech_button_clicked)
# # # # # # #         self.camera_enabled_checkbox.toggled.connect(self.on_camera_enabled_changed)
# # # # # # #         self.tts_worker.speech_finished.connect(self.on_speech_finished)
# # # # # # #         self.stt_worker.monologue_recognized.connect(self.on_monologue_recognized)
# # # # # # #         self.stt_worker.command_recognized.connect(self.on_command_recognized)
# # # # # # #         self.observer_worker.observation_ready.connect(self.on_observation_received)
# # # # # # #         self.stt_enabled_checkbox.toggled.connect(self.stt_worker.set_enabled)
        
# # # # # # #         self.tts_worker.start()
# # # # # # #         self.stt_worker.start()
# # # # # # #         self.observer_worker.start()
# # # # # # #         self.db_worker.start()
        
# # # # # # #         self.load_and_display_sessions()

# # # # # # #         if self.settings_manager.camera_enabled_on_startup:
# # # # # # #             self.camera_enabled_checkbox.setChecked(True)
# # # # # # #         else:
# # # # # # #             self.camera_enabled_checkbox.setChecked(False)
# # # # # # #             self.camera_view.setText("カメラはオフです")

# # # # # # #     def create_menu(self):
# # # # # # #         menu_bar = self.menuBar()
# # # # # # #         file_menu = menu_bar.addMenu("ファイル")
        
# # # # # # #         settings_action = QAction("設定...", self)
# # # # # # #         settings_action.triggered.connect(self.open_settings_dialog)
# # # # # # #         file_menu.addAction(settings_action)

# # # # # # #     def open_settings_dialog(self):
# # # # # # #         """設定ダイアログを開き、変更があれば適用する"""
# # # # # # #         dialog = SettingsDialog(self)
# # # # # # #         if dialog.exec():
# # # # # # #             print("設定ダイアログがOKで閉じられました。変更を適用します。")
# # # # # # #             self.apply_settings_dynamically()
# # # # # # #         else:
# # # # # # #             print("設定はキャンセルされました。")

# # # # # # #     def apply_settings_dynamically(self):
# # # # # # #         """保存された設定を読み込み、実行中のワーカーに動的に適用する"""
# # # # # # #         # CameraWorkerの設定を更新
# # # # # # #         if self.camera_worker and self.camera_worker.isRunning():
# # # # # # #             new_stop_threshold = self.settings_manager.hand_stop_threshold
# # # # # # #             self.camera_worker.set_stop_threshold(new_stop_threshold)

# # # # # # #         # VisualObserverWorkerの設定を更新
# # # # # # #         if self.observer_worker and self.observer_worker.isRunning():
# # # # # # #             new_interval = self.settings_manager.observation_interval
# # # # # # #             self.observer_worker.set_observation_interval(new_interval)

# # # # # # #         # TTSWorkerの設定を更新
# # # # # # #         if self.tts_worker and self.tts_worker.isRunning():
# # # # # # #             new_tts_enabled = self.settings_manager.tts_enabled
# # # # # # #             new_tts_rate = self.settings_manager.tts_rate
# # # # # # #             self.tts_worker.set_tts_enabled(new_tts_enabled)
# # # # # # #             self.tts_worker.set_tts_rate(new_tts_rate)
            
# # # # # # #         print("動的な設定の適用が完了しました。")

# # # # # # #     @Slot(bool)
# # # # # # #     def on_camera_enabled_changed(self, enabled: bool):
# # # # # # #         if enabled:
# # # # # # #             if self.camera_worker is None:
# # # # # # #                 print("カメラワーカーを初期化・起動します。")
# # # # # # #                 project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# # # # # # #                 model_path = os.path.join(project_root, "models", "best12-2.pt")
                
# # # # # # #                 self.camera_worker = CameraWorker(
# # # # # # #                     model_path=model_path,
# # # # # # #                     device_index=self.settings_manager.camera_device_index,
# # # # # # #                     conf_threshold=0.5, 
# # # # # # #                     move_threshold_px=5, 
# # # # # # #                     stop_threshold_sec=self.settings_manager.hand_stop_threshold
# # # # # # #                 )
# # # # # # #                 self.camera_worker.frame_data_ready.connect(self.update_camera_view)
# # # # # # #                 self.camera_worker.hand_stopped_signal.connect(self.on_hand_stopped)
# # # # # # #                 self.camera_worker.raw_frame_for_observation.connect(self.observer_worker.update_frame)
                
# # # # # # #                 self.camera_worker.start()
# # # # # # #         else:
# # # # # # #             if self.camera_worker and self.camera_worker.isRunning():
# # # # # # #                 print("カメラワーカーを停止します。")
# # # # # # #                 self.camera_worker.frame_data_ready.disconnect(self.update_camera_view)
# # # # # # #                 self.camera_worker.hand_stopped_signal.disconnect(self.on_hand_stopped)
# # # # # # #                 self.camera_worker.raw_frame_for_observation.disconnect(self.observer_worker.update_frame)
                
# # # # # # #                 self.camera_worker.stop()
# # # # # # #                 self.camera_worker.wait()
# # # # # # #                 self.camera_worker = None
                
# # # # # # #                 self.camera_view.setText("カメラはオフです")
# # # # # # #                 self.latest_camera_frame = None
# # # # # # #                 print("カメラワーカーを完全に停止しました。")

# # # # # # #     def _get_long_term_context(self, relevant_sessions: List[Dict]) -> str:
# # # # # # #         if not relevant_sessions:
# # # # # # #             last_session_id = self.db_manager.get_last_active_session_id(exclude_session_id=self.active_session_id)
# # # # # # #             if not last_session_id: return "これが最初のセッションです。"
# # # # # # #             last_session_details = self.db_manager.get_session_details(last_session_id)
# # # # # # #             if not last_session_details: return "前回のセッション情報を取得できませんでした。"
# # # # # # #             last_messages = self.db_manager.get_messages_for_session(last_session_id)
# # # # # # #             last_user_message = next((msg['content'] for msg in reversed(last_messages) if msg['role'] == 'user'), "なし")
# # # # # # #             return f"（直近のセッションより）\n- 前回（{last_session_details['last_updated_at']}）のセッションでは、「{last_session_details['title']}」について学習しており、最後の質問は「{last_user_message}」でした。"
        
# # # # # # #         context_lines = ["（過去の関連セッションより）"]
# # # # # # #         for session in relevant_sessions:
# # # # # # #             line = f"- セッション「{session['title']}」（{session['last_updated_at']}）では、キーワード「{session['keywords']}」について議論しました。"
# # # # # # #             context_lines.append(line)
# # # # # # #         return "\n".join(context_lines)

# # # # # # #     def _add_message_to_ui_and_db(self, role: str, content: str):
# # # # # # #         if not self.active_session_id: return
# # # # # # #         self.current_chat_messages.append({"role": role, "content": content})
# # # # # # #         self.update_chat_display()
# # # # # # #         self.db_worker.add_message(self.active_session_id, role, content)

# # # # # # #     def _trigger_keyword_extraction(self, session_id: int):
# # # # # # #         if not session_id: return
# # # # # # #         if self.keyword_extraction_worker and self.keyword_extraction_worker.isRunning(): return
# # # # # # #         print(f"セッションID {session_id} のキーワード抽出タスクを開始します。")
# # # # # # #         messages = self.db_manager.get_messages_for_session(session_id)
# # # # # # #         if len(messages) < 4:
# # # # # # #             print("会話が少ないため、キーワード抽出をスキップしました。")
# # # # # # #             return
# # # # # # #         conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
# # # # # # #         prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
# # # # # # #         prompt = prompt_template.format(conversation_text=conversation_text)
        
# # # # # # #         model_name = self.settings_manager.keyword_extraction_model
# # # # # # #         self.keyword_extraction_worker = GeminiWorker(prompt, model_name=model_name)
# # # # # # #         self.keyword_extraction_worker.response_ready.connect(lambda keywords: self.on_keywords_extracted(session_id, keywords))
# # # # # # #         self.keyword_extraction_worker.finished.connect(self.on_keyword_worker_finished)
# # # # # # #         self.keyword_extraction_worker.start()

# # # # # # #     def _trigger_title_generation(self, session_id: int):
# # # # # # #         if not session_id: return
# # # # # # #         if self.title_generation_worker and self.title_generation_worker.isRunning(): return
# # # # # # #         print(f"セッションID {session_id} のタイトル生成タスクを開始します。")
# # # # # # #         messages = self.db_manager.get_messages_for_session(session_id)
# # # # # # #         if len(messages) < 4:
# # # # # # #             print("会話が少ないため、タイトル生成をスキップしました。")
# # # # # # #             return
# # # # # # #         conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
# # # # # # #         prompt_template = self.settings_manager.title_generation_prompt
# # # # # # #         prompt = prompt_template.format(conversation_text=conversation_text)
        
# # # # # # #         model_name = self.settings_manager.keyword_extraction_model
# # # # # # #         self.title_generation_worker = GeminiWorker(prompt, model_name=model_name)
# # # # # # #         self.title_generation_worker.response_ready.connect(lambda title: self.on_title_generated(session_id, title))
# # # # # # #         self.title_generation_worker.finished.connect(self.on_title_generation_finished)
# # # # # # #         self.title_generation_worker.start()

# # # # # # #     @Slot(int, str)
# # # # # # #     def on_title_generated(self, session_id: int, title: str):
# # # # # # #         cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
# # # # # # #         self.db_worker.update_session_title(session_id, cleaned_title)
# # # # # # #         for i in range(self.session_list_widget.count()):
# # # # # # #             item = self.session_list_widget.item(i)
# # # # # # #             if item.data(Qt.UserRole) == session_id:
# # # # # # #                 item.setText(cleaned_title)
# # # # # # #                 break
    
# # # # # # #     @Slot()
# # # # # # #     def on_title_generation_finished(self):
# # # # # # #         if self.title_generation_worker:
# # # # # # #             self.title_generation_worker.deleteLater()
# # # # # # #             self.title_generation_worker = None

# # # # # # #     @Slot(int, str)
# # # # # # #     def on_keywords_extracted(self, session_id: int, keywords_response: str):
# # # # # # #         match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# # # # # # #         cleaned_keywords = match.group(1).strip() if match else keywords_response.strip()
# # # # # # #         cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
# # # # # # #         print(f"パース後のキーワード: {cleaned_keywords}")
# # # # # # #         self.db_worker.update_session_keywords(session_id, cleaned_keywords)
        
# # # # # # #     @Slot()
# # # # # # #     def on_keyword_worker_finished(self):
# # # # # # #         if self.keyword_extraction_worker:
# # # # # # #             self.keyword_extraction_worker.deleteLater()
# # # # # # #             self.keyword_extraction_worker = None

# # # # # # #     def update_chat_display(self):
# # # # # # #         md_text = ""
# # # # # # #         for msg in self.current_chat_messages:
# # # # # # #             role_display = "あなた" if msg["role"] == "user" else "AIアシスタント"
# # # # # # #             md_text += f"**{role_display}:**\n\n{msg['content']}\n\n<hr>\n\n"
# # # # # # #         self.ai_output_view.set_markdown(md_text)

# # # # # # #     def load_and_display_sessions(self):
# # # # # # #         self.session_list_widget.blockSignals(True)
# # # # # # #         self.session_list_widget.clear()
# # # # # # #         sessions = self.db_manager.get_all_sessions()
# # # # # # #         if not sessions:
# # # # # # #             self.create_new_session(is_initial=True)
# # # # # # #             sessions = self.db_manager.get_all_sessions()
# # # # # # #         for session_id, title in sessions:
# # # # # # #             item = QListWidgetItem(title)
# # # # # # #             item.setData(Qt.UserRole, session_id)
# # # # # # #             self.session_list_widget.addItem(item)
# # # # # # #         self.session_list_widget.setCurrentRow(0)
# # # # # # #         self.session_list_widget.blockSignals(False)
# # # # # # #         if self.session_list_widget.currentItem():
# # # # # # #             self.on_session_changed(self.session_list_widget.currentItem(), None)

# # # # # # #     def create_new_session(self, is_initial=False):
# # # # # # #         self.db_manager.create_new_session()
# # # # # # #         if not is_initial:
# # # # # # #             self.load_and_display_sessions()

# # # # # # #     @Slot(QListWidgetItem, QListWidgetItem)
# # # # # # #     def on_session_changed(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
# # # # # # #         if previous_item:
# # # # # # #             previous_session_id = previous_item.data(Qt.UserRole)
# # # # # # #             self._trigger_keyword_extraction(previous_session_id)
# # # # # # #             self._trigger_title_generation(previous_session_id)
# # # # # # #         if not current_item: return
# # # # # # #         session_id = current_item.data(Qt.UserRole)
# # # # # # #         if session_id == self.active_session_id: return
# # # # # # #         self.active_session_id = session_id
# # # # # # #         session_details = self.db_manager.get_session_details(session_id)
# # # # # # #         if session_details:
# # # # # # #             self.context_manager.set_problem_context(session_details.get("problem_context"))
# # # # # # #         self.current_chat_messages = self.db_manager.get_messages_for_session(self.active_session_id)
# # # # # # #         self.update_chat_display()

# # # # # # #     @Slot()
# # # # # # #     def on_stop_speech_button_clicked(self):
# # # # # # #         self.tts_worker.stop_current_speech()

# # # # # # #     def execute_ai_task(self, prompt, speak=True, is_user_request=False, use_vision=False, is_continuation=False):
# # # # # # #         print(f"execute_ai_task: プロンプト内容の一部 -> {str(prompt)[:200]}...")
# # # # # # #         if self.is_ai_task_running and not is_continuation:
# # # # # # #             return
# # # # # # #         if not is_continuation:
# # # # # # #             self.is_ai_task_running = True
# # # # # # #             self.header_stack.setCurrentIndex(1)
# # # # # # #             if hasattr(self, 'movie'): self.movie.start()
            
# # # # # # #         if is_user_request:
# # # # # # #             self.send_button.setEnabled(False)
# # # # # # #         if speak:
# # # # # # #             self.stop_speech_button.setVisible(True)
            
# # # # # # #         if use_vision:
# # # # # # #             model_name = self.settings_manager.vision_model
# # # # # # #             self.ai_worker = GeminiVisionWorker(prompt, model_name=model_name)
# # # # # # #         else:
# # # # # # #             model_name = self.settings_manager.main_response_model
# # # # # # #             self.ai_worker = GeminiWorker(prompt, model_name=model_name)
            
# # # # # # #         self.ai_worker.response_ready.connect(lambda r: self.handle_gemini_response(r, speak))
# # # # # # #         self.ai_worker.finished.connect(self.on_ai_worker_finished)
# # # # # # #         self.ai_worker.start()

# # # # # # #     def handle_gemini_response(self, response_text, speak):
# # # # # # #         if hasattr(self, 'movie'): self.movie.stop()
# # # # # # #         self.header_stack.setCurrentIndex(0)
        
# # # # # # #         self._add_message_to_ui_and_db("ai", response_text)
        
# # # # # # #         if speak:
# # # # # # #             print("読み上げ開始。音声認識を一時停止します。")
# # # # # # #             self.stt_was_enabled_before_tts = self.stt_enabled_checkbox.isChecked()
# # # # # # #             if self.stt_was_enabled_before_tts:
# # # # # # #                 self.stt_enabled_checkbox.setChecked(False)
# # # # # # #             self.tts_worker.speak(response_text)
# # # # # # #         else:
# # # # # # #             self.is_ai_task_running = False
# # # # # # #             self.stop_speech_button.setVisible(False)
# # # # # # #             if not self.send_button.isEnabled():
# # # # # # #                 self.send_button.setEnabled(True)

# # # # # # #     @Slot()
# # # # # # #     def on_speech_finished(self):
# # # # # # #         self.is_ai_task_running = False
# # # # # # #         self.stop_speech_button.setVisible(False)
        
# # # # # # #         print("読み上げ完了。音声認識の状態を復元します。")
# # # # # # #         if self.stt_was_enabled_before_tts:
# # # # # # #             self.stt_enabled_checkbox.setChecked(True)
        
# # # # # # #         if not self.send_button.isEnabled():
# # # # # # #             self.send_button.setEnabled(True)

# # # # # # #     @Slot()
# # # # # # #     def on_ai_worker_finished(self):
# # # # # # #         if self.ai_worker:
# # # # # # #             self.ai_worker.deleteLater()
# # # # # # #             self.ai_worker = None

# # # # # # #     def start_user_request(self):
# # # # # # #         user_query = self.user_input.toPlainText().strip()
# # # # # # #         if not (user_query and self.active_session_id): return
        
# # # # # # #         self._add_message_to_ui_and_db("user", user_query)
# # # # # # #         self.user_input.clear()
        
# # # # # # #         self.is_ai_task_running = True
# # # # # # #         self.header_stack.setCurrentIndex(1)
# # # # # # #         if hasattr(self, 'movie'): self.movie.start()
# # # # # # #         self.send_button.setEnabled(False)
        
# # # # # # #         prompt = f"""以下の質問文から、中心となるキーワードを3つ、カンマ区切りで抽出してください。思考プロセスは不要です。キーワードのみを出力してください。\n例: 積分、グラフ、面積\n\n---\n{user_query}"""
        
# # # # # # #         model_name = self.settings_manager.keyword_extraction_model
# # # # # # #         self.query_keyword_worker = GeminiWorker(prompt, model_name=model_name)
# # # # # # #         self.query_keyword_worker.response_ready.connect(lambda keywords: self.on_query_keywords_extracted(user_query, keywords))
# # # # # # #         self.query_keyword_worker.finished.connect(self.on_query_keyword_worker_finished)
# # # # # # #         self.query_keyword_worker.start()

# # # # # # #     @Slot(str, str)
# # # # # # #     def on_query_keywords_extracted(self, original_query: str, keywords_response: str):
# # # # # # #         match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# # # # # # #         cleaned_keywords_str = match.group(1).strip() if match else keywords_response.strip()
# # # # # # #         cleaned_keywords = [kw.strip() for kw in cleaned_keywords_str.split(',') if kw.strip()]
        
# # # # # # #         print(f"質問のキーワードを抽出しました: {cleaned_keywords}")
# # # # # # #         if not self.active_session_id: return
        
# # # # # # #         relevant_sessions = self.db_manager.find_relevant_sessions(cleaned_keywords, exclude_session_id=self.active_session_id)
# # # # # # #         long_term_context = self._get_long_term_context(relevant_sessions)
# # # # # # #         monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
# # # # # # #         observation_log = self.db_manager.get_recent_logs_for_session(self.active_session_id, "observation", 5)
        
# # # # # # #         full_prompt = self.context_manager.build_prompt_for_query(original_query, self.current_chat_messages, monologue_history, observation_log, long_term_context)
# # # # # # #         self.execute_ai_task(full_prompt, speak=True, is_user_request=True, is_continuation=True)

# # # # # # #     @Slot()
# # # # # # #     def on_query_keyword_worker_finished(self):
# # # # # # #         if self.query_keyword_worker:
# # # # # # #             self.query_keyword_worker.deleteLater()
# # # # # # #             self.query_keyword_worker = None

# # # # # # #     def open_file_dialog(self): 
# # # # # # #         if not self.active_session_id: self.create_new_session(); return
# # # # # # #         file_path, _ = QFileDialog.getOpenFileName(self, "問題ファイルを選択", "", "サポートファイル (*.pdf *.png *.jpg *.jpeg *.webp);;全ファイル (*)")
# # # # # # #         if file_path:
# # # # # # #             self._add_message_to_ui_and_db("ai", f"`{os.path.basename(file_path)}`を分析中...")
            
# # # # # # #             model_name = self.settings_manager.vision_model
# # # # # # #             gemini_client_for_file = GeminiClient(vision_model_name=model_name)
# # # # # # #             self.file_worker = FileProcessingWorker(file_path, gemini_client_for_file)
# # # # # # #             self.file_worker.finished_processing.connect(self.on_file_processed)
# # # # # # #             self.file_worker.finished.connect(self.on_file_worker_finished)
# # # # # # #             self.file_worker.start()

# # # # # # #     @Slot(str)
# # # # # # #     def on_file_processed(self, result_text):
# # # # # # #         if not self.active_session_id: return
# # # # # # #         self.db_worker.update_problem_context(self.active_session_id, result_text)
# # # # # # #         self.context_manager.set_problem_context(result_text)
# # # # # # #         message = f"ファイルの分析が完了しました。\n\n**【分析結果】**\n\n{result_text}\n\n---\nこの問題について質問してください。"
# # # # # # #         self._add_message_to_ui_and_db("ai", message)
# # # # # # #         self.tts_worker.speak("ファイルの分析が完了しました。")

# # # # # # #     @Slot()
# # # # # # #     def on_file_worker_finished(self):
# # # # # # #         if self.file_worker:
# # # # # # #             self.file_worker.deleteLater()
# # # # # # #             self.file_worker = None
            
# # # # # # #     @Slot(Image.Image)
# # # # # # #     def on_hand_stopped(self, captured_image):
# # # # # # #         if self.is_ai_task_running: return
# # # # # # #         self.context_manager.set_triggered_image(captured_image)
# # # # # # #         prompt = self.settings_manager.hand_stopped_prompt
# # # # # # #         self.execute_ai_task(prompt, speak=True)

# # # # # # #     @Slot(str)
# # # # # # #     def on_monologue_recognized(self, text):
# # # # # # #         if self.active_session_id:
# # # # # # #             self.db_worker.add_log(self.active_session_id, "monologue", text)
# # # # # # #         current_text = self.user_input.toPlainText()
# # # # # # #         new_text = (current_text + " " + text) if current_text and not current_text.endswith(" ") else (current_text + text)
# # # # # # #         self.user_input.setPlainText(new_text)
# # # # # # #         self.user_input.moveCursor(QTextCursor.MoveOperation.End)

# # # # # # #     @Slot(str)
# # # # # # #     def on_command_recognized(self, command_text):
# # # # # # #         print(f"\n--- 音声コマンド受信:「{command_text}」 ---") 

# # # # # # #         if not self.active_session_id:
# # # # # # #             print("エラー: アクティブなセッションがありません。") 
# # # # # # #             self.tts_worker.speak("すみません、現在アクティブなセッションがありません。")
# # # # # # #             return
            
# # # # # # #         if not self.latest_camera_frame:
# # # # # # #             print("エラー: カメラ映像が取得できていません。") 
# # # # # # #             self.tts_worker.speak("すみません、カメラの映像が取得できていません。")
# # # # # # #             return
        
# # # # # # #         self._add_message_to_ui_and_db("user", f"（音声コマンド）{command_text}")
# # # # # # #         self.context_manager.set_triggered_image(self.latest_camera_frame.copy())
# # # # # # #         print("UIにコマンドを反映し、トリガー画像を設定しました。") 

# # # # # # #         self.is_ai_task_running = True
# # # # # # #         self.header_stack.setCurrentIndex(1)
# # # # # # #         if hasattr(self, 'movie'):
# # # # # # #             self.movie.start()
# # # # # # #         self.send_button.setEnabled(False)
# # # # # # #         print("UIを「考え中」状態に更新しました。") 

# # # # # # #         long_term_context = self._get_long_term_context([])
# # # # # # #         monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
# # # # # # #         print(f"長期コンテキストと独り言履歴を取得しました。") 

# # # # # # #         prompt_parts = self.context_manager.build_prompt_parts_for_command(
# # # # # # #             command_text, 
# # # # # # #             self.current_chat_messages, 
# # # # # # #             monologue_history, 
# # # # # # #             long_term_context
# # # # # # #         )
        
# # # # # # #         if prompt_parts:
# # # # # # #             print("AIへのプロンプト生成に成功しました。AIタスクを開始します。") 
# # # # # # #             self.execute_ai_task(prompt_parts, speak=True, is_user_request=False, use_vision=True, is_continuation=True)
# # # # # # #         else:
# # # # # # #             print("エラー: AIへのプロンプト生成に失敗しました。") 
# # # # # # #             self.tts_worker.speak("コマンドの準備に失敗しました。")
# # # # # # #             self.is_ai_task_running = False
# # # # # # #             self.header_stack.setCurrentIndex(0)
# # # # # # #             self.send_button.setEnabled(True)

# # # # # # #     @Slot(str)
# # # # # # #     def on_observation_received(self, observation_text: str):
# # # # # # #         if self.active_session_id:
# # # # # # #             self.db_worker.add_log(self.active_session_id, "observation", observation_text)

# # # # # # #     @Slot(QImage, list)
# # # # # # #     def update_camera_view(self, frame_qimage: QImage, detections: List[Dict]):
# # # # # # #         if frame_qimage.isNull():
# # # # # # #             print("Warning: 無効なカメラフレームを受け取ったため、描画をスキップしました。")
# # # # # # #             return
        
# # # # # # #         pixmap = QPixmap.fromImage(frame_qimage)
# # # # # # #         painter = QPainter(pixmap)
# # # # # # #         for detection in detections:
# # # # # # #             box = detection["box"]
# # # # # # #             label = f'{detection["label"]} {detection["confidence"]:.2f}'
# # # # # # #             pen = QPen(QColor(0, 255, 0), 2)
# # # # # # #             painter.setPen(pen)
# # # # # # #             painter.drawRect(box[0], box[1], box[2] - box[0], box[3] - box[1])
# # # # # # #             font = QFont()
# # # # # # #             font.setPointSize(10)
# # # # # # #             painter.setFont(font)
# # # # # # #             painter.setPen(QColor(255, 255, 255))
# # # # # # #             text_x, text_y = box[0], box[1] - 5
# # # # # # #             painter.fillRect(text_x, text_y - 12, len(label) * 8, 16, QColor(0, 255, 0))
# # # # # # #             painter.drawText(text_x, text_y, label)
# # # # # # #         painter.end()
# # # # # # #         self.camera_view.setPixmap(pixmap)
        
# # # # # # #         buffer = frame_qimage.constBits().tobytes()
# # # # # # #         self.latest_camera_frame = Image.frombytes("RGBA", (frame_qimage.width(), frame_qimage.height()), buffer, 'raw', "BGRA")

# # # # # # #     def closeEvent(self, event):
# # # # # # #         """アプリケーション終了時に、すべてのリソースを安全かつ同期的に解放する"""
# # # # # # #         print("アプリケーションの終了処理を開始します...")

# # # # # # #         print("UI関連以外のワーカースレッドを停止します...")
# # # # # # #         if self.camera_worker and self.camera_worker.isRunning():
# # # # # # #             self.on_camera_enabled_changed(False)
        
# # # # # # #         if hasattr(self, 'stt_worker') and self.stt_worker.isRunning():
# # # # # # #             self.stt_worker.stop()
# # # # # # #             self.stt_worker.wait()
# # # # # # #             print(" > STTWorker 停止完了")
# # # # # # #         if hasattr(self, 'tts_worker') and self.tts_worker.isRunning():
# # # # # # #             self.tts_worker.stop()
# # # # # # #             self.tts_worker.wait()
# # # # # # #             print(" > TTSWorker 停止完了")
# # # # # # #         if hasattr(self, 'observer_worker') and self.observer_worker.isRunning():
# # # # # # #             self.observer_worker.stop()
# # # # # # #             self.observer_worker.wait()
# # # # # # #             print(" > VisualObserverWorker 停止完了")
            
# # # # # # #         if self.active_session_id:
# # # # # # #             print(f"セッションID {self.active_session_id} の最終処理を実行します...")
            
# # # # # # #             messages = self.db_manager.get_messages_for_session(self.active_session_id)
# # # # # # #             if len(messages) >= 4:
# # # # # # #                 conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                
# # # # # # #                 main_gemini_client = GeminiClient(text_model_name=self.settings_manager.keyword_extraction_model)
                
# # # # # # #                 kw_prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
# # # # # # #                 kw_prompt = kw_prompt_template.format(conversation_text=conversation_text)
# # # # # # #                 print(" > キーワードを抽出中...")
# # # # # # #                 keywords_response = main_gemini_client.generate_response(kw_prompt)
# # # # # # #                 match_kw = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# # # # # # #                 cleaned_keywords = match_kw.group(1).strip() if match_kw else keywords_response.strip()
# # # # # # #                 cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
# # # # # # #                 self.db_manager.update_session_keywords(self.active_session_id, cleaned_keywords)
# # # # # # #                 print(f" > キーワードを保存しました: {cleaned_keywords}")

# # # # # # #                 title_prompt_template = self.settings_manager.title_generation_prompt
# # # # # # #                 title_prompt = title_prompt_template.format(conversation_text=conversation_text)
# # # # # # #                 print(" > タイトルを生成中...")
# # # # # # #                 title = main_gemini_client.generate_response(title_prompt)
# # # # # # #                 cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
# # # # # # #                 self.db_manager.update_session_title(self.active_session_id, cleaned_title)
# # # # # # #                 print(f" > タイトルを保存しました: {cleaned_title}")

# # # # # # #         if hasattr(self, 'db_worker') and self.db_worker.isRunning():
# # # # # # #             print("データベースへの書き込み完了を待っています...")
# # # # # # #             while self.db_worker.tasks:
# # # # # # #                 print(f" > DBワーカーの残りタスク: {len(self.db_worker.tasks)}件")
# # # # # # #                 QThread.msleep(100)
# # # # # # #             self.db_worker.stop()
# # # # # # #             self.db_worker.wait()
# # # # # # #             print(" > DatabaseWorker 停止完了")
            
# # # # # # #         print("すべての処理が安全に完了しました。アプリケーションを終了します。")
# # # # # # #         super().closeEvent(event)



















# # # # # # # 再起不要版(カメラやマイクも)

# # # # # # import sys
# # # # # # import os
# # # # # # import fitz
# # # # # # import re
# # # # # # from PIL import Image
# # # # # # from PySide6.QtCore import QThread, Signal, Slot, QSize, Qt
# # # # # # from PySide6.QtGui import QPixmap, QImage, QTextCursor, QMovie, QPainter, QColor, QPen, QFont, QAction
# # # # # # from PySide6.QtWidgets import (
# # # # # #     QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLabel,
# # # # # #     QHBoxLayout, QCheckBox, QFileDialog, QStackedLayout, 
# # # # # #     QListWidget, QListWidgetItem, QSplitter
# # # # # # )
# # # # # # from typing import Optional, List, Dict

# # # # # # from .widgets.md_view import MarkdownView
# # # # # # from .settings_dialog import SettingsDialog
# # # # # # from ..core.context_manager import ContextManager
# # # # # # from ..core.gemini_client import GeminiClient
# # # # # # from ..core.database_manager import DatabaseManager
# # # # # # from ..core.database_worker import DatabaseWorker
# # # # # # from ..core.visual_observer import VisualObserverWorker
# # # # # # from ..core.settings_manager import SettingsManager
# # # # # # from ..hardware.camera_handler import CameraWorker
# # # # # # from ..hardware.audio_handler import TTSWorker, STTWorker

# # # # # # # --- ワーカースレッド定義 (変更なし) ---
# # # # # # class FileProcessingWorker(QThread):
# # # # # #     finished_processing = Signal(str)
# # # # # #     def __init__(self, file_path, gemini_client, parent=None):
# # # # # #         super().__init__(parent)
# # # # # #         self.file_path = file_path
# # # # # #         self.gemini_client = gemini_client
# # # # # #     def run(self):
# # # # # #         images = []
# # # # # #         file_path_lower = self.file_path.lower()
# # # # # #         try:
# # # # # #             if file_path_lower.endswith('.pdf'):
# # # # # #                 doc = fitz.open(self.file_path)
# # # # # #                 for page in doc:
# # # # # #                     pix = page.get_pixmap(dpi=150)
# # # # # #                     img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
# # # # # #                     images.append(img)
# # # # # #                 doc.close()
# # # # # #             elif file_path_lower.endswith(('.png', '.jpg', '.jpeg', '.webp')):
# # # # # #                 images.append(Image.open(self.file_path).convert("RGB"))
# # # # # #             else:
# # # # # #                 self.finished_processing.emit("サポートされていない形式です。")
# # # # # #                 return
# # # # # #             if not images:
# # # # # #                 self.finished_processing.emit("画像を変換できませんでした。")
# # # # # #                 return
# # # # # #             prompt = "この画像は学習教材です。含まれるテキストや数式を正確に書き出してください。"
# # # # # #             self.finished_processing.emit(self.gemini_client.generate_vision_response([prompt] + images))
# # # # # #         except Exception as e:
# # # # # #             self.finished_processing.emit(f"ファイル処理エラー: {e}")

# # # # # # class GeminiWorker(QThread):
# # # # # #     response_ready = Signal(str)
# # # # # #     def __init__(self, prompt, model_name=None, parent=None):
# # # # # #         super().__init__(parent)
# # # # # #         self.prompt = prompt
# # # # # #         self.gemini_client = GeminiClient(text_model_name=model_name)
# # # # # #     def run(self):
# # # # # #         self.response_ready.emit(self.gemini_client.generate_response(self.prompt))

# # # # # # class GeminiVisionWorker(QThread):
# # # # # #     response_ready = Signal(str)
# # # # # #     def __init__(self, prompt_parts, model_name=None, parent=None):
# # # # # #         super().__init__(parent)
# # # # # #         self.prompt_parts = prompt_parts
# # # # # #         self.gemini_client = GeminiClient(vision_model_name=model_name)
# # # # # #     def run(self):
# # # # # #         self.response_ready.emit(self.gemini_client.generate_vision_response(self.prompt_parts))

# # # # # # # --- メインウィンドウ ---
# # # # # # class MainWindow(QMainWindow):
# # # # # #     def __init__(self):
# # # # # #         super().__init__()
# # # # # #         self.setWindowTitle("勉強アシストアプリ")
# # # # # #         self.setGeometry(100, 100, 1600, 900)
        
# # # # # #         self.is_ai_task_running = False
# # # # # #         self.context_manager = ContextManager()
# # # # # #         self.settings_manager = SettingsManager()
# # # # # #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# # # # # #         db_path = os.path.join(project_root, "data", "sessions.db")
# # # # # #         self.db_manager = DatabaseManager(db_path=db_path)
# # # # # #         self.active_session_id: Optional[int] = None
# # # # # #         self.latest_camera_frame: Optional[Image.Image] = None

# # # # # #         # ワーカーへの参照を初期化
# # # # # #         self.camera_worker: Optional[CameraWorker] = None
# # # # # #         self.stt_worker: Optional[STTWorker] = None
# # # # # #         self.observer_worker: Optional[VisualObserverWorker] = None
# # # # # #         self.tts_worker: Optional[TTSWorker] = None
# # # # # #         self.db_worker: Optional[DatabaseWorker] = None
# # # # # #         self.file_worker: Optional[FileProcessingWorker] = None
# # # # # #         self.keyword_extraction_worker: Optional[GeminiWorker] = None
# # # # # #         self.query_keyword_worker: Optional[GeminiWorker] = None
# # # # # #         self.title_generation_worker: Optional[GeminiWorker] = None

# # # # # #         self.current_chat_messages: List[Dict[str, str]] = []
# # # # # #         self.stt_was_enabled_before_tts = False

# # # # # #         # --- UIのセットアップ ---
# # # # # #         self.setup_ui()
# # # # # #         self.create_menu()
        
# # # # # #         # --- ワーカースレッドの初期起動 ---
# # # # # #         self.start_essential_workers()
# # # # # #         self.restart_stt_worker() # STTワーカーも初期起動
        
# # # # # #         self.load_and_display_sessions()

# # # # # #         # 起動時のカメラ状態を設定から復元
# # # # # #         if self.settings_manager.camera_enabled_on_startup:
# # # # # #             self.camera_enabled_checkbox.setChecked(True)
# # # # # #         else:
# # # # # #             self.camera_enabled_checkbox.setChecked(False)
# # # # # #             self.camera_view.setText("カメラはオフです")

# # # # # #     def setup_ui(self):
# # # # # #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# # # # # #         session_area_widget = QWidget()
# # # # # #         session_layout = QVBoxLayout(session_area_widget)
# # # # # #         self.new_session_button = QPushButton("＋ 新しいチャット")
# # # # # #         self.session_list_widget = QListWidget()
# # # # # #         session_layout.addWidget(self.new_session_button)
# # # # # #         session_layout.addWidget(self.session_list_widget)

# # # # # #         main_chat_widget = QWidget()
# # # # # #         left_layout = QVBoxLayout(main_chat_widget)
# # # # # #         self.ai_output_view = MarkdownView()
# # # # # #         self.user_input = QTextEdit()
# # # # # #         self.send_button = QPushButton("送信")
# # # # # #         self.stt_enabled_checkbox = QCheckBox("音声認識")
# # # # # #         self.load_file_button = QPushButton("問題ファイルを読み込む")
# # # # # #         self.stop_speech_button = QPushButton("読み上げを停止")
# # # # # #         self.stop_speech_button.setVisible(False)

# # # # # #         loading_widget = QWidget()
# # # # # #         loading_layout = QHBoxLayout(loading_widget)
# # # # # #         loading_layout.setContentsMargins(0, 5, 0, 5)
# # # # # #         self.loading_movie_label = QLabel()
# # # # # #         loading_gif_path = os.path.join(project_root, "assets", "loading.gif")
# # # # # #         if os.path.exists(loading_gif_path):
# # # # # #             self.movie = QMovie(loading_gif_path)
# # # # # #             self.loading_movie_label.setMovie(self.movie)
# # # # # #             self.movie.setScaledSize(QSize(25, 25))
# # # # # #         self.loading_text_label = QLabel("AIが考え中です...")
# # # # # #         loading_layout.addStretch()
# # # # # #         loading_layout.addWidget(self.loading_movie_label)
# # # # # #         loading_layout.addWidget(self.loading_text_label)
# # # # # #         loading_layout.addStretch()

# # # # # #         self.header_stack = QStackedLayout()
# # # # # #         self.header_stack.addWidget(QLabel("AIアシスタント"))
# # # # # #         self.header_stack.addWidget(loading_widget)

# # # # # #         top_button_layout = QHBoxLayout()
# # # # # #         top_button_layout.addWidget(self.load_file_button)
# # # # # #         top_button_layout.addStretch()
# # # # # #         self.camera_enabled_checkbox = QCheckBox("カメラを有効にする")
# # # # # #         top_button_layout.addWidget(self.camera_enabled_checkbox)
# # # # # #         top_button_layout.addWidget(self.stt_enabled_checkbox)

# # # # # #         button_v_layout = QVBoxLayout()
# # # # # #         button_v_layout.addWidget(self.send_button)
# # # # # #         button_v_layout.addWidget(self.stop_speech_button)

# # # # # #         input_area_layout = QHBoxLayout()
# # # # # #         input_area_layout.addWidget(self.user_input)
# # # # # #         input_area_layout.addLayout(button_v_layout)

# # # # # #         left_layout.addLayout(top_button_layout)
# # # # # #         left_layout.addLayout(self.header_stack)
# # # # # #         left_layout.addWidget(self.ai_output_view, stretch=1)
# # # # # #         left_layout.addWidget(QLabel("質問や独り言を入力"))
# # # # # #         left_layout.addLayout(input_area_layout)

# # # # # #         right_widget = QWidget()
# # # # # #         right_layout = QVBoxLayout(right_widget)
# # # # # #         self.camera_view = QLabel("カメラを初期化中...")
# # # # # #         self.camera_view.setStyleSheet("background-color: black; color: white;")
# # # # # #         self.camera_view.setFixedSize(640, 480)
# # # # # #         right_layout.addWidget(self.camera_view)
# # # # # #         right_layout.addStretch()

# # # # # #         splitter = QSplitter(Qt.Horizontal)
# # # # # #         splitter.addWidget(session_area_widget)
# # # # # #         splitter.addWidget(main_chat_widget)
# # # # # #         splitter.addWidget(right_widget)
# # # # # #         splitter.setSizes([250, 750, 600])
# # # # # #         self.setCentralWidget(splitter)

# # # # # #         # シグナル接続
# # # # # #         self.new_session_button.clicked.connect(self.create_new_session)
# # # # # #         self.session_list_widget.currentItemChanged.connect(self.on_session_changed)
# # # # # #         self.send_button.clicked.connect(self.start_user_request)
# # # # # #         self.load_file_button.clicked.connect(self.open_file_dialog)
# # # # # #         self.stop_speech_button.clicked.connect(self.on_stop_speech_button_clicked)
# # # # # #         self.camera_enabled_checkbox.toggled.connect(self.on_camera_enabled_changed)
# # # # # #         self.stt_enabled_checkbox.toggled.connect(self.on_stt_enabled_changed)


# # # # # #     def start_essential_workers(self):
# # # # # #         """常に動作する必要があるワーカーを起動する"""
# # # # # #         self.db_worker = DatabaseWorker(self.db_manager)
# # # # # #         self.tts_worker = TTSWorker()
        
# # # # # #         self.db_worker.start()
# # # # # #         self.tts_worker.start()
        
# # # # # #         self.tts_worker.speech_finished.connect(self.on_speech_finished)
    
# # # # # #     def start_camera_dependent_workers(self):
# # # # # #         """カメラに依存するワーカー（Camera, Observer）を起動する"""
# # # # # #         self.stop_camera_dependent_workers() 

# # # # # #         print("カメラ関連ワーカーを起動します...")
# # # # # #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# # # # # #         model_path = os.path.join(project_root, "models", "best12-2.pt")
        
# # # # # #         self.camera_worker = CameraWorker(
# # # # # #             model_path=model_path,
# # # # # #             device_index=self.settings_manager.camera_device_index,
# # # # # #             stop_threshold_sec=self.settings_manager.hand_stop_threshold
# # # # # #         )
# # # # # #         self.observer_worker = VisualObserverWorker(
# # # # # #             interval_sec=self.settings_manager.observation_interval
# # # # # #         )

# # # # # #         self.camera_worker.frame_data_ready.connect(self.update_camera_view)
# # # # # #         self.camera_worker.hand_stopped_signal.connect(self.on_hand_stopped)
# # # # # #         self.camera_worker.raw_frame_for_observation.connect(self.observer_worker.update_frame)
# # # # # #         self.observer_worker.observation_ready.connect(self.on_observation_received)

# # # # # #         self.camera_worker.start()
# # # # # #         self.observer_worker.start()

# # # # # #     def stop_camera_dependent_workers(self):
# # # # # #         """カメラに依存するワーカーを安全に停止する"""
# # # # # #         if self.camera_worker and self.camera_worker.isRunning():
# # # # # #             print("CameraWorkerを停止します...")
# # # # # #             self.camera_worker.stop()
# # # # # #             self.camera_worker.wait()
# # # # # #             self.camera_worker = None
# # # # # #             print(" > CameraWorker 停止完了")

# # # # # #         if self.observer_worker and self.observer_worker.isRunning():
# # # # # #             print("VisualObserverWorkerを停止します...")
# # # # # #             self.observer_worker.stop()
# # # # # #             self.observer_worker.wait()
# # # # # #             self.observer_worker = None
# # # # # #             print(" > VisualObserverWorker 停止完了")

# # # # # #     def restart_stt_worker(self):
# # # # # #         """STTワーカーを現在の設定で再起動する"""
# # # # # #         print("STTワーカーを再起動します...")
# # # # # #         if self.stt_worker and self.stt_worker.isRunning():
# # # # # #             self.stt_worker.stop()
# # # # # #             self.stt_worker.wait()
        
# # # # # #         self.stt_worker = STTWorker(device_index=self.settings_manager.mic_device_index)
# # # # # #         self.stt_worker.monologue_recognized.connect(self.on_monologue_recognized)
# # # # # #         self.stt_worker.command_recognized.connect(self.on_command_recognized)
# # # # # #         self.stt_worker.set_enabled(self.stt_enabled_checkbox.isChecked())
# # # # # #         self.stt_worker.start()
# # # # # #         print(" > STTWorker 再起動完了")
        
# # # # # #     def open_settings_dialog(self):
# # # # # #         dialog = SettingsDialog(self)
# # # # # #         if dialog.exec():
# # # # # #             print("設定が変更されました。動的設定を適用し、必要なワーカーを再起動します。")
# # # # # #             self.apply_settings_dynamically()
# # # # # #             self.restart_stt_worker()
# # # # # #             if self.camera_enabled_checkbox.isChecked():
# # # # # #                 self.start_camera_dependent_workers()
# # # # # #             print("ワーカーの再起動・設定反映が完了しました。")
# # # # # #         else:
# # # # # #             print("設定はキャンセルされました。")
            
# # # # # #     def apply_settings_dynamically(self):
# # # # # #         """再起動不要な設定を動的に適用する"""
# # # # # #         if self.tts_worker and self.tts_worker.isRunning():
# # # # # #             self.tts_worker.set_tts_enabled(self.settings_manager.tts_enabled)
# # # # # #             self.tts_worker.set_tts_rate(self.settings_manager.tts_rate)
        
# # # # # #         if self.camera_worker and self.camera_worker.isRunning():
# # # # # #             self.camera_worker.set_stop_threshold(self.settings_manager.hand_stop_threshold)
# # # # # #         if self.observer_worker and self.observer_worker.isRunning():
# # # # # #             self.observer_worker.set_observation_interval(self.settings_manager.observation_interval)

# # # # # #     @Slot(bool)
# # # # # #     def on_camera_enabled_changed(self, enabled: bool):
# # # # # #         if enabled:
# # # # # #             self.start_camera_dependent_workers()
# # # # # #         else:
# # # # # #             self.stop_camera_dependent_workers()
# # # # # #             self.camera_view.setText("カメラはオフです")
# # # # # #             self.latest_camera_frame = None

# # # # # #     @Slot(bool)
# # # # # #     def on_stt_enabled_changed(self, enabled: bool):
# # # # # #         if self.stt_worker:
# # # # # #             self.stt_worker.set_enabled(enabled)

# # # # # #     def create_menu(self):
# # # # # #         menu_bar = self.menuBar()
# # # # # #         file_menu = menu_bar.addMenu("ファイル")
# # # # # #         settings_action = QAction("設定...", self)
# # # # # #         settings_action.triggered.connect(self.open_settings_dialog)
# # # # # #         file_menu.addAction(settings_action)

# # # # # #     def _get_long_term_context(self, relevant_sessions: List[Dict]) -> str:
# # # # # #         if not relevant_sessions:
# # # # # #             last_session_id = self.db_manager.get_last_active_session_id(exclude_session_id=self.active_session_id)
# # # # # #             if not last_session_id: return "これが最初のセッションです。"
# # # # # #             last_session_details = self.db_manager.get_session_details(last_session_id)
# # # # # #             if not last_session_details: return "前回のセッション情報を取得できませんでした。"
# # # # # #             last_messages = self.db_manager.get_messages_for_session(last_session_id)
# # # # # #             last_user_message = next((msg['content'] for msg in reversed(last_messages) if msg['role'] == 'user'), "なし")
# # # # # #             return f"（直近のセッションより）\n- 前回（{last_session_details['last_updated_at']}）のセッションでは、「{last_session_details['title']}」について学習しており、最後の質問は「{last_user_message}」でした。"
        
# # # # # #         context_lines = ["（過去の関連セッションより）"]
# # # # # #         for session in relevant_sessions:
# # # # # #             line = f"- セッション「{session['title']}」（{session['last_updated_at']}）では、キーワード「{session['keywords']}」について議論しました。"
# # # # # #             context_lines.append(line)
# # # # # #         return "\n".join(context_lines)

# # # # # #     def _add_message_to_ui_and_db(self, role: str, content: str):
# # # # # #         if not self.active_session_id: return
# # # # # #         self.current_chat_messages.append({"role": role, "content": content})
# # # # # #         self.update_chat_display()
# # # # # #         self.db_worker.add_message(self.active_session_id, role, content)

# # # # # #     def _trigger_keyword_extraction(self, session_id: int):
# # # # # #         if not session_id: return
# # # # # #         if self.keyword_extraction_worker and self.keyword_extraction_worker.isRunning(): return
# # # # # #         print(f"セッションID {session_id} のキーワード抽出タスクを開始します。")
# # # # # #         messages = self.db_manager.get_messages_for_session(session_id)
# # # # # #         if len(messages) < 4:
# # # # # #             print("会話が少ないため、キーワード抽出をスキップしました。")
# # # # # #             return
# # # # # #         conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
# # # # # #         prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
# # # # # #         prompt = prompt_template.format(conversation_text=conversation_text)
        
# # # # # #         model_name = self.settings_manager.keyword_extraction_model
# # # # # #         self.keyword_extraction_worker = GeminiWorker(prompt, model_name=model_name)
# # # # # #         self.keyword_extraction_worker.response_ready.connect(lambda keywords: self.on_keywords_extracted(session_id, keywords))
# # # # # #         self.keyword_extraction_worker.finished.connect(self.on_keyword_worker_finished)
# # # # # #         self.keyword_extraction_worker.start()

# # # # # #     def _trigger_title_generation(self, session_id: int):
# # # # # #         if not session_id: return
# # # # # #         if self.title_generation_worker and self.title_generation_worker.isRunning(): return
# # # # # #         print(f"セッションID {session_id} のタイトル生成タスクを開始します。")
# # # # # #         messages = self.db_manager.get_messages_for_session(session_id)
# # # # # #         if len(messages) < 4:
# # # # # #             print("会話が少ないため、タイトル生成をスキップしました。")
# # # # # #             return
# # # # # #         conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
# # # # # #         prompt_template = self.settings_manager.title_generation_prompt
# # # # # #         prompt = prompt_template.format(conversation_text=conversation_text)
        
# # # # # #         model_name = self.settings_manager.keyword_extraction_model
# # # # # #         self.title_generation_worker = GeminiWorker(prompt, model_name=model_name)
# # # # # #         self.title_generation_worker.response_ready.connect(lambda title: self.on_title_generated(session_id, title))
# # # # # #         self.title_generation_worker.finished.connect(self.on_title_generation_finished)
# # # # # #         self.title_generation_worker.start()

# # # # # #     @Slot(int, str)
# # # # # #     def on_title_generated(self, session_id: int, title: str):
# # # # # #         cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
# # # # # #         self.db_worker.update_session_title(session_id, cleaned_title)
# # # # # #         for i in range(self.session_list_widget.count()):
# # # # # #             item = self.session_list_widget.item(i)
# # # # # #             if item.data(Qt.UserRole) == session_id:
# # # # # #                 item.setText(cleaned_title)
# # # # # #                 break
    
# # # # # #     @Slot()
# # # # # #     def on_title_generation_finished(self):
# # # # # #         if self.title_generation_worker:
# # # # # #             self.title_generation_worker.deleteLater()
# # # # # #             self.title_generation_worker = None

# # # # # #     @Slot(int, str)
# # # # # #     def on_keywords_extracted(self, session_id: int, keywords_response: str):
# # # # # #         match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# # # # # #         cleaned_keywords = match.group(1).strip() if match else keywords_response.strip()
# # # # # #         cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
# # # # # #         print(f"パース後のキーワード: {cleaned_keywords}")
# # # # # #         self.db_worker.update_session_keywords(session_id, cleaned_keywords)
        
# # # # # #     @Slot()
# # # # # #     def on_keyword_worker_finished(self):
# # # # # #         if self.keyword_extraction_worker:
# # # # # #             self.keyword_extraction_worker.deleteLater()
# # # # # #             self.keyword_extraction_worker = None

# # # # # #     def update_chat_display(self):
# # # # # #         md_text = ""
# # # # # #         for msg in self.current_chat_messages:
# # # # # #             role_display = "あなた" if msg["role"] == "user" else "AIアシスタント"
# # # # # #             md_text += f"**{role_display}:**\n\n{msg['content']}\n\n<hr>\n\n"
# # # # # #         self.ai_output_view.set_markdown(md_text)

# # # # # #     def load_and_display_sessions(self):
# # # # # #         self.session_list_widget.blockSignals(True)
# # # # # #         self.session_list_widget.clear()
# # # # # #         sessions = self.db_manager.get_all_sessions()
# # # # # #         if not sessions:
# # # # # #             self.create_new_session(is_initial=True)
# # # # # #             sessions = self.db_manager.get_all_sessions()
# # # # # #         for session_id, title in sessions:
# # # # # #             item = QListWidgetItem(title)
# # # # # #             item.setData(Qt.UserRole, session_id)
# # # # # #             self.session_list_widget.addItem(item)
# # # # # #         self.session_list_widget.setCurrentRow(0)
# # # # # #         self.session_list_widget.blockSignals(False)
# # # # # #         if self.session_list_widget.currentItem():
# # # # # #             self.on_session_changed(self.session_list_widget.currentItem(), None)

# # # # # #     def create_new_session(self, is_initial=False):
# # # # # #         self.db_manager.create_new_session()
# # # # # #         if not is_initial:
# # # # # #             self.load_and_display_sessions()

# # # # # #     @Slot(QListWidgetItem, QListWidgetItem)
# # # # # #     def on_session_changed(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
# # # # # #         if previous_item:
# # # # # #             previous_session_id = previous_item.data(Qt.UserRole)
# # # # # #             self._trigger_keyword_extraction(previous_session_id)
# # # # # #             self._trigger_title_generation(previous_session_id)
# # # # # #         if not current_item: return
# # # # # #         session_id = current_item.data(Qt.UserRole)
# # # # # #         if session_id == self.active_session_id: return
# # # # # #         self.active_session_id = session_id
# # # # # #         session_details = self.db_manager.get_session_details(session_id)
# # # # # #         if session_details:
# # # # # #             self.context_manager.set_problem_context(session_details.get("problem_context"))
# # # # # #         self.current_chat_messages = self.db_manager.get_messages_for_session(self.active_session_id)
# # # # # #         self.update_chat_display()

# # # # # #     @Slot()
# # # # # #     def on_stop_speech_button_clicked(self):
# # # # # #         self.tts_worker.stop_current_speech()

# # # # # #     def execute_ai_task(self, prompt, speak=True, is_user_request=False, use_vision=False, is_continuation=False):
# # # # # #         if self.is_ai_task_running and not is_continuation:
# # # # # #             return
# # # # # #         if not is_continuation:
# # # # # #             self.is_ai_task_running = True
# # # # # #             self.header_stack.setCurrentIndex(1)
# # # # # #             if hasattr(self, 'movie'): self.movie.start()
            
# # # # # #         if is_user_request:
# # # # # #             self.send_button.setEnabled(False)
# # # # # #         if speak:
# # # # # #             self.stop_speech_button.setVisible(True)
            
# # # # # #         if use_vision:
# # # # # #             model_name = self.settings_manager.vision_model
# # # # # #             self.ai_worker = GeminiVisionWorker(prompt, model_name=model_name)
# # # # # #         else:
# # # # # #             model_name = self.settings_manager.main_response_model
# # # # # #             self.ai_worker = GeminiWorker(prompt, model_name=model_name)
            
# # # # # #         self.ai_worker.response_ready.connect(lambda r: self.handle_gemini_response(r, speak))
# # # # # #         self.ai_worker.finished.connect(self.on_ai_worker_finished)
# # # # # #         self.ai_worker.start()

# # # # # #     def handle_gemini_response(self, response_text, speak):
# # # # # #         if hasattr(self, 'movie'): self.movie.stop()
# # # # # #         self.header_stack.setCurrentIndex(0)
        
# # # # # #         self._add_message_to_ui_and_db("ai", response_text)
        
# # # # # #         if speak:
# # # # # #             print("読み上げ開始。音声認識を一時停止します。")
# # # # # #             self.stt_was_enabled_before_tts = self.stt_enabled_checkbox.isChecked()
# # # # # #             if self.stt_was_enabled_before_tts:
# # # # # #                 self.stt_enabled_checkbox.setChecked(False)
# # # # # #             self.tts_worker.speak(response_text)
# # # # # #         else:
# # # # # #             self.is_ai_task_running = False
# # # # # #             self.stop_speech_button.setVisible(False)
# # # # # #             if not self.send_button.isEnabled():
# # # # # #                 self.send_button.setEnabled(True)

# # # # # #     @Slot()
# # # # # #     def on_speech_finished(self):
# # # # # #         self.is_ai_task_running = False
# # # # # #         self.stop_speech_button.setVisible(False)
        
# # # # # #         print("読み上げ完了。音声認識の状態を復元します。")
# # # # # #         if self.stt_was_enabled_before_tts:
# # # # # #             self.stt_enabled_checkbox.setChecked(True)
        
# # # # # #         if not self.send_button.isEnabled():
# # # # # #             self.send_button.setEnabled(True)

# # # # # #     @Slot()
# # # # # #     def on_ai_worker_finished(self):
# # # # # #         if self.ai_worker:
# # # # # #             self.ai_worker.deleteLater()
# # # # # #             self.ai_worker = None

# # # # # #     def start_user_request(self):
# # # # # #         user_query = self.user_input.toPlainText().strip()
# # # # # #         if not (user_query and self.active_session_id): return
        
# # # # # #         self._add_message_to_ui_and_db("user", user_query)
# # # # # #         self.user_input.clear()
        
# # # # # #         self.is_ai_task_running = True
# # # # # #         self.header_stack.setCurrentIndex(1)
# # # # # #         if hasattr(self, 'movie'): self.movie.start()
# # # # # #         self.send_button.setEnabled(False)
        
# # # # # #         prompt = f"""以下の質問文から、中心となるキーワードを3つ、カンマ区切りで抽出してください。思考プロセスは不要です。キーワードのみを出力してください。\n例: 積分、グラフ、面積\n\n---\n{user_query}"""
        
# # # # # #         model_name = self.settings_manager.keyword_extraction_model
# # # # # #         self.query_keyword_worker = GeminiWorker(prompt, model_name=model_name)
# # # # # #         self.query_keyword_worker.response_ready.connect(lambda keywords: self.on_query_keywords_extracted(user_query, keywords))
# # # # # #         self.query_keyword_worker.finished.connect(self.on_query_keyword_worker_finished)
# # # # # #         self.query_keyword_worker.start()

# # # # # #     @Slot(str, str)
# # # # # #     def on_query_keywords_extracted(self, original_query: str, keywords_response: str):
# # # # # #         match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# # # # # #         cleaned_keywords_str = match.group(1).strip() if match else keywords_response.strip()
# # # # # #         cleaned_keywords = [kw.strip() for kw in cleaned_keywords_str.split(',') if kw.strip()]
        
# # # # # #         print(f"質問のキーワードを抽出しました: {cleaned_keywords}")
# # # # # #         if not self.active_session_id: return
        
# # # # # #         relevant_sessions = self.db_manager.find_relevant_sessions(cleaned_keywords, exclude_session_id=self.active_session_id)
# # # # # #         long_term_context = self._get_long_term_context(relevant_sessions)
# # # # # #         monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
# # # # # #         observation_log = self.db_manager.get_recent_logs_for_session(self.active_session_id, "observation", 5)
        
# # # # # #         full_prompt = self.context_manager.build_prompt_for_query(original_query, self.current_chat_messages, monologue_history, observation_log, long_term_context)
# # # # # #         self.execute_ai_task(full_prompt, speak=True, is_user_request=True, is_continuation=True)

# # # # # #     @Slot()
# # # # # #     def on_query_keyword_worker_finished(self):
# # # # # #         if self.query_keyword_worker:
# # # # # #             self.query_keyword_worker.deleteLater()
# # # # # #             self.query_keyword_worker = None

# # # # # #     def open_file_dialog(self): 
# # # # # #         if not self.active_session_id: self.create_new_session(); return
# # # # # #         file_path, _ = QFileDialog.getOpenFileName(self, "問題ファイルを選択", "", "サポートファイル (*.pdf *.png *.jpg *.jpeg *.webp);;全ファイル (*)")
# # # # # #         if file_path:
# # # # # #             self._add_message_to_ui_and_db("ai", f"`{os.path.basename(file_path)}`を分析中...")
            
# # # # # #             model_name = self.settings_manager.vision_model
# # # # # #             gemini_client_for_file = GeminiClient(vision_model_name=model_name)
# # # # # #             self.file_worker = FileProcessingWorker(file_path, gemini_client_for_file)
# # # # # #             self.file_worker.finished_processing.connect(self.on_file_processed)
# # # # # #             self.file_worker.finished.connect(self.on_file_worker_finished)
# # # # # #             self.file_worker.start()

# # # # # #     @Slot(str)
# # # # # #     def on_file_processed(self, result_text):
# # # # # #         if not self.active_session_id: return
# # # # # #         self.db_worker.update_problem_context(self.active_session_id, result_text)
# # # # # #         self.context_manager.set_problem_context(result_text)
# # # # # #         message = f"ファイルの分析が完了しました。\n\n**【分析結果】**\n\n{result_text}\n\n---\nこの問題について質問してください。"
# # # # # #         self._add_message_to_ui_and_db("ai", message)
# # # # # #         self.tts_worker.speak("ファイルの分析が完了しました。")

# # # # # #     @Slot()
# # # # # #     def on_file_worker_finished(self):
# # # # # #         if self.file_worker:
# # # # # #             self.file_worker.deleteLater()
# # # # # #             self.file_worker = None
            
# # # # # #     @Slot(Image.Image)
# # # # # #     def on_hand_stopped(self, captured_image):
# # # # # #         if self.is_ai_task_running: return
# # # # # #         self.context_manager.set_triggered_image(captured_image)
# # # # # #         prompt = self.settings_manager.hand_stopped_prompt
# # # # # #         self.execute_ai_task(prompt, speak=True)

# # # # # #     @Slot(str)
# # # # # #     def on_monologue_recognized(self, text):
# # # # # #         if self.active_session_id:
# # # # # #             self.db_worker.add_log(self.active_session_id, "monologue", text)
# # # # # #         current_text = self.user_input.toPlainText()
# # # # # #         new_text = (current_text + " " + text) if current_text and not current_text.endswith(" ") else (current_text + text)
# # # # # #         self.user_input.setPlainText(new_text)
# # # # # #         self.user_input.moveCursor(QTextCursor.MoveOperation.End)

# # # # # #     @Slot(str)
# # # # # #     def on_command_recognized(self, command_text):
# # # # # #         print(f"\n--- 音声コマンド受信:「{command_text}」 ---") 

# # # # # #         if not self.active_session_id:
# # # # # #             print("エラー: アクティブなセッションがありません。") 
# # # # # #             self.tts_worker.speak("すみません、現在アクティブなセッションがありません。")
# # # # # #             return
            
# # # # # #         if not self.latest_camera_frame:
# # # # # #             print("エラー: カメラ映像が取得できていません。") 
# # # # # #             self.tts_worker.speak("すみません、カメラの映像が取得できていません。")
# # # # # #             return
        
# # # # # #         self._add_message_to_ui_and_db("user", f"（音声コマンド）{command_text}")
# # # # # #         self.context_manager.set_triggered_image(self.latest_camera_frame.copy())
# # # # # #         print("UIにコマンドを反映し、トリガー画像を設定しました。") 

# # # # # #         self.is_ai_task_running = True
# # # # # #         self.header_stack.setCurrentIndex(1)
# # # # # #         if hasattr(self, 'movie'):
# # # # # #             self.movie.start()
# # # # # #         self.send_button.setEnabled(False)
# # # # # #         print("UIを「考え中」状態に更新しました。") 

# # # # # #         long_term_context = self._get_long_term_context([])
# # # # # #         monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
# # # # # #         print(f"長期コンテキストと独り言履歴を取得しました。") 

# # # # # #         prompt_parts = self.context_manager.build_prompt_parts_for_command(
# # # # # #             command_text, 
# # # # # #             self.current_chat_messages, 
# # # # # #             monologue_history, 
# # # # # #             long_term_context
# # # # # #         )
        
# # # # # #         if prompt_parts:
# # # # # #             print("AIへのプロンプト生成に成功しました。AIタスクを開始します。") 
# # # # # #             self.execute_ai_task(prompt_parts, speak=True, is_user_request=False, use_vision=True, is_continuation=True)
# # # # # #         else:
# # # # # #             print("エラー: AIへのプロンプト生成に失敗しました。") 
# # # # # #             self.tts_worker.speak("コマンドの準備に失敗しました。")
# # # # # #             self.is_ai_task_running = False
# # # # # #             self.header_stack.setCurrentIndex(0)
# # # # # #             self.send_button.setEnabled(True)

# # # # # #     @Slot(str)
# # # # # #     def on_observation_received(self, observation_text: str):
# # # # # #         if self.active_session_id:
# # # # # #             self.db_worker.add_log(self.active_session_id, "observation", observation_text)

# # # # # #     @Slot(QImage, list)
# # # # # #     def update_camera_view(self, frame_qimage: QImage, detections: List[Dict]):
# # # # # #         if frame_qimage.isNull():
# # # # # #             print("Warning: 無効なカメラフレームを受け取ったため、描画をスキップしました。")
# # # # # #             return

        
# # # # # #         pixmap = QPixmap.fromImage(frame_qimage)
# # # # # #         painter = QPainter(pixmap)
# # # # # #         for detection in detections:
# # # # # #             box = detection["box"]
# # # # # #             label = f'{detection["label"]} {detection["confidence"]:.2f}'
# # # # # #             pen = QPen(QColor(0, 255, 0), 2)
# # # # # #             painter.setPen(pen)
# # # # # #             painter.drawRect(box[0], box[1], box[2] - box[0], box[3] - box[1])
# # # # # #             font = QFont()
# # # # # #             font.setPointSize(10)
# # # # # #             painter.setFont(font)
# # # # # #             painter.setPen(QColor(255, 255, 255))
# # # # # #             text_x, text_y = box[0], box[1] - 5
# # # # # #             painter.fillRect(text_x, text_y - 12, len(label) * 8, 16, QColor(0, 255, 0))
# # # # # #             painter.drawText(text_x, text_y, label)
# # # # # #         painter.end()
# # # # # #         self.camera_view.setPixmap(pixmap)
        
# # # # # #         buffer = frame_qimage.constBits().tobytes()
# # # # # #         self.latest_camera_frame = Image.frombytes("RGBA", (frame_qimage.width(), frame_qimage.height()), buffer, 'raw', "BGRA")

# # # # # #     def closeEvent(self, event):
# # # # # #         """アプリケーション終了時に、すべてのリソースを安全に解放する"""
# # # # # #         print("アプリケーションの終了処理を開始します...")

# # # # # #         print("UI関連以外のワーカースレッドを停止します...")
# # # # # #         self.stop_camera_dependent_workers()
        
# # # # # #         if self.stt_worker and self.stt_worker.isRunning():
# # # # # #             self.stt_worker.stop()
# # # # # #             self.stt_worker.wait()
# # # # # #             print(" > STTWorker 停止完了")
        
# # # # # #         if self.tts_worker and self.tts_worker.isRunning():
# # # # # #             self.tts_worker.stop()
# # # # # #             self.tts_worker.wait()
# # # # # #             print(" > TTSWorker 停止完了")
            
# # # # # #         if self.active_session_id:
# # # # # #             print(f"セッションID {self.active_session_id} の最終処理を実行します...")
            
# # # # # #             messages = self.db_manager.get_messages_for_session(self.active_session_id)
# # # # # #             if len(messages) >= 4:
# # # # # #                 conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                
# # # # # #                 main_gemini_client = GeminiClient(text_model_name=self.settings_manager.keyword_extraction_model)
                
# # # # # #                 kw_prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
# # # # # #                 kw_prompt = kw_prompt_template.format(conversation_text=conversation_text)
# # # # # #                 print(" > キーワードを抽出中...")
# # # # # #                 keywords_response = main_gemini_client.generate_response(kw_prompt)
# # # # # #                 match_kw = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# # # # # #                 cleaned_keywords = match_kw.group(1).strip() if match_kw else keywords_response.strip()
# # # # # #                 cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
# # # # # #                 self.db_manager.update_session_keywords(self.active_session_id, cleaned_keywords)
# # # # # #                 print(f" > キーワードを保存しました: {cleaned_keywords}")

# # # # # #                 title_prompt_template = self.settings_manager.title_generation_prompt
# # # # # #                 title_prompt = title_prompt_template.format(conversation_text=conversation_text)
# # # # # #                 print(" > タイトルを生成中...")
# # # # # #                 title = main_gemini_client.generate_response(title_prompt)
# # # # # #                 cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
# # # # # #                 self.db_manager.update_session_title(self.active_session_id, cleaned_title)
# # # # # #                 print(f" > タイトルを保存しました: {cleaned_title}")

# # # # # #         if self.db_worker and self.db_worker.isRunning():
# # # # # #             print("データベースへの書き込み完了を待っています...")
# # # # # #             while self.db_worker.tasks:
# # # # # #                 print(f" > DBワーカーの残りタスク: {len(self.db_worker.tasks)}件")
# # # # # #                 QThread.msleep(100)
# # # # # #             self.db_worker.stop()
# # # # # #             self.db_worker.wait()
# # # # # #             print(" > DatabaseWorker 停止完了")
            
# # # # # #         print("すべての処理が安全に完了しました。アプリケーションを終了します。")
# # # # # #         super().closeEvent(event)























# # # # # import sys
# # # # # import os
# # # # # import fitz
# # # # # import re
# # # # # from PIL import Image
# # # # # from PySide6.QtCore import QThread, Signal, Slot, QSize, Qt
# # # # # from PySide6.QtGui import QPixmap, QImage, QTextCursor, QMovie, QPainter, QColor, QPen, QFont, QAction
# # # # # from PySide6.QtWidgets import (
# # # # #     QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLabel,
# # # # #     QHBoxLayout, QCheckBox, QFileDialog, QStackedLayout, 
# # # # #     QListWidget, QListWidgetItem, QSplitter
# # # # # )
# # # # # from typing import Optional, List, Dict

# # # # # from .widgets.md_view import MarkdownView
# # # # # from .settings_dialog import SettingsDialog
# # # # # from ..core.context_manager import ContextManager
# # # # # from ..core.gemini_client import GeminiClient
# # # # # from ..core.database_manager import DatabaseManager
# # # # # from ..core.database_worker import DatabaseWorker
# # # # # from ..core.visual_observer import VisualObserverWorker
# # # # # from ..core.settings_manager import SettingsManager
# # # # # from ..hardware.camera_handler import CameraWorker
# # # # # from ..hardware.audio_handler import TTSWorker, STTWorker

# # # # # # --- ワーカースレッド定義 (変更なし) ---
# # # # # class FileProcessingWorker(QThread):
# # # # #     finished_processing = Signal(str)
# # # # #     def __init__(self, file_path, gemini_client, parent=None):
# # # # #         super().__init__(parent)
# # # # #         self.file_path = file_path
# # # # #         self.gemini_client = gemini_client
# # # # #     def run(self):
# # # # #         images = []
# # # # #         file_path_lower = self.file_path.lower()
# # # # #         try:
# # # # #             if file_path_lower.endswith('.pdf'):
# # # # #                 doc = fitz.open(self.file_path)
# # # # #                 for page in doc:
# # # # #                     pix = page.get_pixmap(dpi=150)
# # # # #                     img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
# # # # #                     images.append(img)
# # # # #                 doc.close()
# # # # #             elif file_path_lower.endswith(('.png', '.jpg', '.jpeg', '.webp')):
# # # # #                 images.append(Image.open(self.file_path).convert("RGB"))
# # # # #             else:
# # # # #                 self.finished_processing.emit("サポートされていない形式です。")
# # # # #                 return
# # # # #             if not images:
# # # # #                 self.finished_processing.emit("画像を変換できませんでした。")
# # # # #                 return
# # # # #             prompt = "この画像は学習教材です。含まれるテキストや数式を正確に書き出してください。"
# # # # #             self.finished_processing.emit(self.gemini_client.generate_vision_response([prompt] + images))
# # # # #         except Exception as e:
# # # # #             self.finished_processing.emit(f"ファイル処理エラー: {e}")

# # # # # class GeminiWorker(QThread):
# # # # #     response_ready = Signal(str)
# # # # #     def __init__(self, prompt, model_name=None, parent=None):
# # # # #         super().__init__(parent)
# # # # #         self.prompt = prompt
# # # # #         self.gemini_client = GeminiClient(text_model_name=model_name)
# # # # #     def run(self):
# # # # #         self.response_ready.emit(self.gemini_client.generate_response(self.prompt))

# # # # # class GeminiVisionWorker(QThread):
# # # # #     response_ready = Signal(str)
# # # # #     def __init__(self, prompt_parts, model_name=None, parent=None):
# # # # #         super().__init__(parent)
# # # # #         self.prompt_parts = prompt_parts
# # # # #         self.gemini_client = GeminiClient(vision_model_name=model_name)
# # # # #     def run(self):
# # # # #         self.response_ready.emit(self.gemini_client.generate_vision_response(self.prompt_parts))

# # # # # # --- メインウィンドウ ---
# # # # # class MainWindow(QMainWindow):
# # # # #     def __init__(self):
# # # # #         super().__init__()
# # # # #         self.setWindowTitle("勉強アシストアプリ")
# # # # #         self.setGeometry(100, 100, 1600, 900)
        
# # # # #         self.is_ai_task_running = False
# # # # #         self.context_manager = ContextManager()
# # # # #         self.settings_manager = SettingsManager()
# # # # #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# # # # #         db_path = os.path.join(project_root, "data", "sessions.db")
# # # # #         self.db_manager = DatabaseManager(db_path=db_path)
# # # # #         self.active_session_id: Optional[int] = None
# # # # #         self.latest_camera_frame: Optional[Image.Image] = None

# # # # #         # ワーカーへの参照を初期化
# # # # #         self.camera_worker: Optional[CameraWorker] = None
# # # # #         self.stt_worker: Optional[STTWorker] = None
# # # # #         self.observer_worker: Optional[VisualObserverWorker] = None
# # # # #         self.tts_worker: Optional[TTSWorker] = None
# # # # #         self.db_worker: Optional[DatabaseWorker] = None
# # # # #         self.file_worker: Optional[FileProcessingWorker] = None
# # # # #         self.keyword_extraction_worker: Optional[GeminiWorker] = None
# # # # #         self.query_keyword_worker: Optional[GeminiWorker] = None
# # # # #         self.title_generation_worker: Optional[GeminiWorker] = None

# # # # #         self.current_chat_messages: List[Dict[str, str]] = []
# # # # #         self.stt_was_enabled_before_tts = False

# # # # #         # UIのセットアップ
# # # # #         self.setup_ui()
# # # # #         self.create_menu()
        
# # # # #         # ワーカースレッドの初期起動
# # # # #         self.start_essential_workers()
# # # # #         self.restart_stt_worker()
        
# # # # #         self.load_and_display_sessions()

# # # # #         # 起動時のカメラ状態を設定から復元
# # # # #         if self.settings_manager.camera_enabled_on_startup:
# # # # #             self.camera_enabled_checkbox.setChecked(True)
# # # # #         else:
# # # # #             self.camera_enabled_checkbox.setChecked(False)
# # # # #             self.camera_view.setText("カメラはオフです")

# # # # #     def setup_ui(self):
# # # # #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        
# # # # #         session_area_widget = QWidget()
# # # # #         session_layout = QVBoxLayout(session_area_widget)
# # # # #         self.new_session_button = QPushButton("＋ 新しいチャット")
# # # # #         self.session_list_widget = QListWidget()
# # # # #         session_layout.addWidget(self.new_session_button)
# # # # #         session_layout.addWidget(self.session_list_widget)

# # # # #         main_chat_widget = QWidget()
# # # # #         left_layout = QVBoxLayout(main_chat_widget)
# # # # #         self.ai_output_view = MarkdownView()
# # # # #         self.user_input = QTextEdit()
# # # # #         self.send_button = QPushButton("送信")
# # # # #         self.stt_enabled_checkbox = QCheckBox("音声認識")
# # # # #         self.load_file_button = QPushButton("問題ファイルを読み込む")
# # # # #         self.stop_speech_button = QPushButton("読み上げを停止")
# # # # #         self.stop_speech_button.setVisible(False)

# # # # #         loading_widget = QWidget()
# # # # #         loading_layout = QHBoxLayout(loading_widget)
# # # # #         loading_layout.setContentsMargins(0, 5, 0, 5)
# # # # #         self.loading_movie_label = QLabel()
# # # # #         loading_gif_path = os.path.join(project_root, "assets", "loading.gif")
# # # # #         if os.path.exists(loading_gif_path):
# # # # #             self.movie = QMovie(loading_gif_path)
# # # # #             self.loading_movie_label.setMovie(self.movie)
# # # # #             self.movie.setScaledSize(QSize(25, 25))
# # # # #         self.loading_text_label = QLabel("AIが考え中です...")
# # # # #         loading_layout.addStretch()
# # # # #         loading_layout.addWidget(self.loading_movie_label)
# # # # #         loading_layout.addWidget(self.loading_text_label)
# # # # #         loading_layout.addStretch()

# # # # #         self.header_stack = QStackedLayout()
# # # # #         self.header_stack.addWidget(QLabel("AIアシスタント"))
# # # # #         self.header_stack.addWidget(loading_widget)

# # # # #         top_button_layout = QHBoxLayout()
# # # # #         top_button_layout.addWidget(self.load_file_button)
# # # # #         top_button_layout.addStretch()
# # # # #         self.camera_enabled_checkbox = QCheckBox("カメラを有効にする")
# # # # #         top_button_layout.addWidget(self.camera_enabled_checkbox)
# # # # #         top_button_layout.addWidget(self.stt_enabled_checkbox)

# # # # #         button_v_layout = QVBoxLayout()
# # # # #         button_v_layout.addWidget(self.send_button)
# # # # #         button_v_layout.addWidget(self.stop_speech_button)

# # # # #         input_area_layout = QHBoxLayout()
# # # # #         input_area_layout.addWidget(self.user_input)
# # # # #         input_area_layout.addLayout(button_v_layout)

# # # # #         left_layout.addLayout(top_button_layout)
# # # # #         left_layout.addLayout(self.header_stack)
# # # # #         left_layout.addWidget(self.ai_output_view, stretch=1)
# # # # #         left_layout.addWidget(QLabel("質問や独り言を入力"))
# # # # #         left_layout.addLayout(input_area_layout)

# # # # #         right_widget = QWidget()
# # # # #         right_layout = QVBoxLayout(right_widget)
# # # # #         self.camera_view = QLabel("カメラを初期化中...")
# # # # #         self.camera_view.setStyleSheet("background-color: black; color: white;")
# # # # #         self.camera_view.setFixedSize(640, 480)
# # # # #         right_layout.addWidget(self.camera_view)
# # # # #         right_layout.addStretch()

# # # # #         splitter = QSplitter(Qt.Horizontal)
# # # # #         splitter.addWidget(session_area_widget)
# # # # #         splitter.addWidget(main_chat_widget)
# # # # #         splitter.addWidget(right_widget)
# # # # #         splitter.setSizes([250, 750, 600])
# # # # #         self.setCentralWidget(splitter)

# # # # #         # シグナル接続
# # # # #         self.new_session_button.clicked.connect(self.create_new_session)
# # # # #         self.session_list_widget.currentItemChanged.connect(self.on_session_changed)
# # # # #         self.send_button.clicked.connect(self.start_user_request)
# # # # #         self.load_file_button.clicked.connect(self.open_file_dialog)
# # # # #         self.stop_speech_button.clicked.connect(self.on_stop_speech_button_clicked)
# # # # #         self.camera_enabled_checkbox.toggled.connect(self.on_camera_enabled_changed)
# # # # #         self.stt_enabled_checkbox.toggled.connect(self.on_stt_enabled_changed)

# # # # #     def start_essential_workers(self):
# # # # #         """常に動作する必要があるワーカーを起動する"""
# # # # #         self.db_worker = DatabaseWorker(self.db_manager)
# # # # #         self.tts_worker = TTSWorker()
        
# # # # #         self.db_worker.start()
# # # # #         self.tts_worker.start()
        
# # # # #         self.tts_worker.speech_finished.connect(self.on_speech_finished)
    
# # # # #     def start_camera_dependent_workers(self):
# # # # #         """カメラに依存するワーカー（Camera, Observer）を起動する"""
# # # # #         self.stop_camera_dependent_workers() 

# # # # #         print("カメラ関連ワーカーを起動します...")
# # # # #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# # # # #         model_path = os.path.join(project_root, "models", "best12-2.pt")
        
# # # # #         self.camera_worker = CameraWorker(
# # # # #             model_path=model_path,
# # # # #             device_index=self.settings_manager.camera_device_index,
# # # # #             stop_threshold_sec=self.settings_manager.hand_stop_threshold
# # # # #         )
# # # # #         self.observer_worker = VisualObserverWorker(
# # # # #             interval_sec=self.settings_manager.observation_interval
# # # # #         )

# # # # #         self.camera_worker.frame_data_ready.connect(self.update_camera_view)
# # # # #         self.camera_worker.hand_stopped_signal.connect(self.on_hand_stopped)
# # # # #         self.camera_worker.raw_frame_for_observation.connect(self.observer_worker.update_frame)
# # # # #         self.observer_worker.observation_ready.connect(self.on_observation_received)

# # # # #         self.camera_worker.start()
# # # # #         self.observer_worker.start()

# # # # #     def stop_camera_dependent_workers(self):
# # # # #         """カメラに依存するワーカーを安全に停止する"""
# # # # #         if self.camera_worker and self.camera_worker.isRunning():
# # # # #             print("CameraWorkerを停止します...")
# # # # #             self.camera_worker.frame_data_ready.disconnect(self.update_camera_view)
# # # # #             self.camera_worker.hand_stopped_signal.disconnect(self.on_hand_stopped)
# # # # #             self.camera_worker.raw_frame_for_observation.disconnect(self.observer_worker.update_frame)
# # # # #             self.camera_worker.stop()
# # # # #             self.camera_worker.wait()
# # # # #             self.camera_worker = None
# # # # #             print(" > CameraWorker 停止完了")

# # # # #         if self.observer_worker and self.observer_worker.isRunning():
# # # # #             print("VisualObserverWorkerを停止します...")
# # # # #             # ObserverはCameraからシグナルを受け取るだけなので、disconnectは不要
# # # # #             self.observer_worker.stop()
# # # # #             self.observer_worker.wait()
# # # # #             self.observer_worker = None
# # # # #             print(" > VisualObserverWorker 停止完了")

# # # # #     def restart_stt_worker(self):
# # # # #         """STTワーカーを現在の設定で再起動する"""
# # # # #         print("STTワーカーを再起動します...")
# # # # #         if self.stt_worker and self.stt_worker.isRunning():
# # # # #             # 接続済みのシグナルを切断
# # # # #             self.stt_worker.monologue_recognized.disconnect(self.on_monologue_recognized)
# # # # #             self.stt_worker.command_recognized.disconnect(self.on_command_recognized)
# # # # #             self.stt_worker.stop()
# # # # #             self.stt_worker.wait()
        
# # # # #         self.stt_worker = STTWorker(device_index=self.settings_manager.mic_device_index)
# # # # #         self.stt_worker.monologue_recognized.connect(self.on_monologue_recognized)
# # # # #         self.stt_worker.command_recognized.connect(self.on_command_recognized)
# # # # #         self.stt_worker.set_enabled(self.stt_enabled_checkbox.isChecked())
# # # # #         self.stt_worker.start()
# # # # #         print(" > STTWorker 再起動完了")
        
# # # # #     def open_settings_dialog(self):
# # # # #         dialog = SettingsDialog(self)
# # # # #         if dialog.exec():
# # # # #             print("設定が変更されました。動的設定を適用し、必要なワーカーを再起動します。")
# # # # #             self.apply_settings_dynamically()
# # # # #             self.restart_stt_worker()
# # # # #             if self.camera_enabled_checkbox.isChecked():
# # # # #                 self.start_camera_dependent_workers()
# # # # #             print("ワーカーの再起動・設定反映が完了しました。")
# # # # #         else:
# # # # #             print("設定はキャンセルされました。")
            
# # # # #     def apply_settings_dynamically(self):
# # # # #         """再起動不要な設定を動的に適用する"""
# # # # #         if self.tts_worker and self.tts_worker.isRunning():
# # # # #             self.tts_worker.set_tts_enabled(self.settings_manager.tts_enabled)
# # # # #             self.tts_worker.set_tts_rate(self.settings_manager.tts_rate)
        
# # # # #         if self.camera_worker and self.camera_worker.isRunning():
# # # # #             self.camera_worker.set_stop_threshold(self.settings_manager.hand_stop_threshold)
# # # # #         if self.observer_worker and self.observer_worker.isRunning():
# # # # #             self.observer_worker.set_observation_interval(self.settings_manager.observation_interval)

# # # # #     @Slot(bool)
# # # # #     def on_camera_enabled_changed(self, enabled: bool):
# # # # #         if enabled:
# # # # #             self.start_camera_dependent_workers()
# # # # #         else:
# # # # #             self.stop_camera_dependent_workers()
# # # # #             self.camera_view.setText("カメラはオフです")
# # # # #             self.latest_camera_frame = None

# # # # #     @Slot(bool)
# # # # #     def on_stt_enabled_changed(self, enabled: bool):
# # # # #         if self.stt_worker:
# # # # #             self.stt_worker.set_enabled(enabled)

# # # # #     def create_menu(self):
# # # # #         menu_bar = self.menuBar()
# # # # #         file_menu = menu_bar.addMenu("ファイル")
# # # # #         settings_action = QAction("設定...", self)
# # # # #         settings_action.triggered.connect(self.open_settings_dialog)
# # # # #         file_menu.addAction(settings_action)

# # # # #     def _get_long_term_context(self, relevant_sessions: List[Dict]) -> str:
# # # # #         if not relevant_sessions:
# # # # #             last_session_id = self.db_manager.get_last_active_session_id(exclude_session_id=self.active_session_id)
# # # # #             if not last_session_id: return "これが最初のセッションです。"
# # # # #             last_session_details = self.db_manager.get_session_details(last_session_id)
# # # # #             if not last_session_details: return "前回のセッション情報を取得できませんでした。"
# # # # #             last_messages = self.db_manager.get_messages_for_session(last_session_id)
# # # # #             last_user_message = next((msg['content'] for msg in reversed(last_messages) if msg['role'] == 'user'), "なし")
# # # # #             return f"（直近のセッションより）\n- 前回（{last_session_details['last_updated_at']}）のセッションでは、「{last_session_details['title']}」について学習しており、最後の質問は「{last_user_message}」でした。"
        
# # # # #         context_lines = ["（過去の関連セッションより）"]
# # # # #         for session in relevant_sessions:
# # # # #             line = f"- セッション「{session['title']}」（{session['last_updated_at']}）では、キーワード「{session['keywords']}」について議論しました。"
# # # # #             context_lines.append(line)
# # # # #         return "\n".join(context_lines)

# # # # #     def _add_message_to_ui_and_db(self, role: str, content: str):
# # # # #         if not self.active_session_id: return
# # # # #         self.current_chat_messages.append({"role": role, "content": content})
# # # # #         self.update_chat_display()
# # # # #         self.db_worker.add_message(self.active_session_id, role, content)

# # # # #     def _trigger_keyword_extraction(self, session_id: int):
# # # # #         if not session_id: return
# # # # #         if self.keyword_extraction_worker and self.keyword_extraction_worker.isRunning(): return
# # # # #         messages = self.db_manager.get_messages_for_session(session_id)
# # # # #         if len(messages) < 4: return
# # # # #         conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
# # # # #         prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
# # # # #         prompt = prompt_template.format(conversation_text=conversation_text)
        
# # # # #         model_name = self.settings_manager.keyword_extraction_model
# # # # #         self.keyword_extraction_worker = GeminiWorker(prompt, model_name=model_name)
# # # # #         self.keyword_extraction_worker.response_ready.connect(lambda keywords: self.on_keywords_extracted(session_id, keywords))
# # # # #         self.keyword_extraction_worker.finished.connect(self.on_keyword_worker_finished)
# # # # #         self.keyword_extraction_worker.start()

# # # # #     def _trigger_title_generation(self, session_id: int):
# # # # #         if not session_id: return
# # # # #         if self.title_generation_worker and self.title_generation_worker.isRunning(): return
# # # # #         messages = self.db_manager.get_messages_for_session(session_id)
# # # # #         if len(messages) < 4: return
# # # # #         conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
# # # # #         prompt_template = self.settings_manager.title_generation_prompt
# # # # #         prompt = prompt_template.format(conversation_text=conversation_text)
        
# # # # #         model_name = self.settings_manager.keyword_extraction_model
# # # # #         self.title_generation_worker = GeminiWorker(prompt, model_name=model_name)
# # # # #         self.title_generation_worker.response_ready.connect(lambda title: self.on_title_generated(session_id, title))
# # # # #         self.title_generation_worker.finished.connect(self.on_title_generation_finished)
# # # # #         self.title_generation_worker.start()

# # # # #     @Slot(int, str)
# # # # #     def on_title_generated(self, session_id: int, title: str):
# # # # #         cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
# # # # #         self.db_worker.update_session_title(session_id, cleaned_title)
# # # # #         for i in range(self.session_list_widget.count()):
# # # # #             item = self.session_list_widget.item(i)
# # # # #             if item.data(Qt.UserRole) == session_id:
# # # # #                 item.setText(cleaned_title)
# # # # #                 break
    
# # # # #     @Slot()
# # # # #     def on_title_generation_finished(self):
# # # # #         if self.title_generation_worker:
# # # # #             self.title_generation_worker.deleteLater()
# # # # #             self.title_generation_worker = None

# # # # #     @Slot(int, str)
# # # # #     def on_keywords_extracted(self, session_id: int, keywords_response: str):
# # # # #         match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# # # # #         cleaned_keywords = match.group(1).strip() if match else keywords_response.strip()
# # # # #         cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
# # # # #         self.db_worker.update_session_keywords(session_id, cleaned_keywords)
        
# # # # #     @Slot()
# # # # #     def on_keyword_worker_finished(self):
# # # # #         if self.keyword_extraction_worker:
# # # # #             self.keyword_extraction_worker.deleteLater()
# # # # #             self.keyword_extraction_worker = None

# # # # #     def update_chat_display(self):
# # # # #         md_text = ""
# # # # #         for msg in self.current_chat_messages:
# # # # #             role_display = "あなた" if msg["role"] == "user" else "AIアシスタント"
# # # # #             md_text += f"**{role_display}:**\n\n{msg['content']}\n\n<hr>\n\n"
# # # # #         self.ai_output_view.set_markdown(md_text)

# # # # #     def load_and_display_sessions(self):
# # # # #         self.session_list_widget.blockSignals(True)
# # # # #         self.session_list_widget.clear()
# # # # #         sessions = self.db_manager.get_all_sessions()
# # # # #         if not sessions:
# # # # #             self.create_new_session(is_initial=True)
# # # # #             sessions = self.db_manager.get_all_sessions()
# # # # #         for session_id, title in sessions:
# # # # #             item = QListWidgetItem(title)
# # # # #             item.setData(Qt.UserRole, session_id)
# # # # #             self.session_list_widget.addItem(item)
# # # # #         self.session_list_widget.setCurrentRow(0)
# # # # #         self.session_list_widget.blockSignals(False)
# # # # #         if self.session_list_widget.currentItem():
# # # # #             self.on_session_changed(self.session_list_widget.currentItem(), None)

# # # # #     def create_new_session(self, is_initial=False):
# # # # #         self.db_manager.create_new_session()
# # # # #         if not is_initial:
# # # # #             self.load_and_display_sessions()

# # # # #     @Slot(QListWidgetItem, QListWidgetItem)
# # # # #     def on_session_changed(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
# # # # #         if previous_item:
# # # # #             previous_session_id = previous_item.data(Qt.UserRole)
# # # # #             self._trigger_keyword_extraction(previous_session_id)
# # # # #             self._trigger_title_generation(previous_session_id)
# # # # #         if not current_item: return
# # # # #         session_id = current_item.data(Qt.UserRole)
# # # # #         if session_id == self.active_session_id: return
# # # # #         self.active_session_id = session_id
# # # # #         session_details = self.db_manager.get_session_details(session_id)
# # # # #         if session_details:
# # # # #             self.context_manager.set_problem_context(session_details.get("problem_context"))
# # # # #         self.current_chat_messages = self.db_manager.get_messages_for_session(self.active_session_id)
# # # # #         self.update_chat_display()

# # # # #     @Slot()
# # # # #     def on_stop_speech_button_clicked(self):
# # # # #         self.tts_worker.stop_current_speech()

# # # # #     def execute_ai_task(self, prompt, speak=True, is_user_request=False, use_vision=False, is_continuation=False):
# # # # #         if self.is_ai_task_running and not is_continuation:
# # # # #             return
# # # # #         if not is_continuation:
# # # # #             self.is_ai_task_running = True
# # # # #             self.header_stack.setCurrentIndex(1)
# # # # #             if hasattr(self, 'movie'): self.movie.start()
            
# # # # #         if is_user_request:
# # # # #             self.send_button.setEnabled(False)
# # # # #         if speak:
# # # # #             self.stop_speech_button.setVisible(True)
            
# # # # #         if use_vision:
# # # # #             model_name = self.settings_manager.vision_model
# # # # #             self.ai_worker = GeminiVisionWorker(prompt, model_name=model_name)
# # # # #         else:
# # # # #             model_name = self.settings_manager.main_response_model
# # # # #             self.ai_worker = GeminiWorker(prompt, model_name=model_name)
            
# # # # #         self.ai_worker.response_ready.connect(lambda r: self.handle_gemini_response(r, speak))
# # # # #         self.ai_worker.finished.connect(self.on_ai_worker_finished)
# # # # #         self.ai_worker.start()

# # # # #     def handle_gemini_response(self, response_text, speak):
# # # # #         if hasattr(self, 'movie'): self.movie.stop()
# # # # #         self.header_stack.setCurrentIndex(0)
        
# # # # #         self._add_message_to_ui_and_db("ai", response_text)
        
# # # # #         if speak:
# # # # #             print("読み上げ開始。音声認識を一時停止します。")
# # # # #             self.stt_was_enabled_before_tts = self.stt_enabled_checkbox.isChecked()
# # # # #             if self.stt_was_enabled_before_tts:
# # # # #                 self.stt_enabled_checkbox.setChecked(False)
# # # # #             self.tts_worker.speak(response_text)
# # # # #         else:
# # # # #             self.is_ai_task_running = False
# # # # #             self.stop_speech_button.setVisible(False)
# # # # #             if not self.send_button.isEnabled():
# # # # #                 self.send_button.setEnabled(True)

# # # # #     @Slot()
# # # # #     def on_speech_finished(self):
# # # # #         self.is_ai_task_running = False
# # # # #         self.stop_speech_button.setVisible(False)
        
# # # # #         print("読み上げ完了。音声認識の状態を復元します。")
# # # # #         if self.stt_was_enabled_before_tts:
# # # # #             self.stt_enabled_checkbox.setChecked(True)
        
# # # # #         if not self.send_button.isEnabled():
# # # # #             self.send_button.setEnabled(True)

# # # # #     @Slot()
# # # # #     def on_ai_worker_finished(self):
# # # # #         if self.ai_worker:
# # # # #             self.ai_worker.deleteLater()
# # # # #             self.ai_worker = None

# # # # #     def start_user_request(self):
# # # # #         user_query = self.user_input.toPlainText().strip()
# # # # #         if not (user_query and self.active_session_id): return
        
# # # # #         self._add_message_to_ui_and_db("user", user_query)
# # # # #         self.user_input.clear()
        
# # # # #         self.is_ai_task_running = True
# # # # #         self.header_stack.setCurrentIndex(1)
# # # # #         if hasattr(self, 'movie'): self.movie.start()
# # # # #         self.send_button.setEnabled(False)
        
# # # # #         prompt = f"""以下の質問文から、中心となるキーワードを3つ、カンマ区切りで抽出してください。思考プロセスは不要です。キーワードのみを出力してください。\n例: 積分、グラフ、面積\n\n---\n{user_query}"""
        
# # # # #         model_name = self.settings_manager.keyword_extraction_model
# # # # #         self.query_keyword_worker = GeminiWorker(prompt, model_name=model_name)
# # # # #         self.query_keyword_worker.response_ready.connect(lambda keywords: self.on_query_keywords_extracted(user_query, keywords))
# # # # #         self.query_keyword_worker.finished.connect(self.on_query_keyword_worker_finished)
# # # # #         self.query_keyword_worker.start()

# # # # #     @Slot(str, str)
# # # # #     def on_query_keywords_extracted(self, original_query: str, keywords_response: str):
# # # # #         match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# # # # #         cleaned_keywords_str = match.group(1).strip() if match else keywords_response.strip()
# # # # #         cleaned_keywords = [kw.strip() for kw in cleaned_keywords_str.split(',') if kw.strip()]
        
# # # # #         if not self.active_session_id: return
        
# # # # #         relevant_sessions = self.db_manager.find_relevant_sessions(cleaned_keywords, exclude_session_id=self.active_session_id)
# # # # #         long_term_context = self._get_long_term_context(relevant_sessions)
# # # # #         monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
# # # # #         observation_log = self.db_manager.get_recent_logs_for_session(self.active_session_id, "observation", 5)
        
# # # # #         full_prompt = self.context_manager.build_prompt_for_query(original_query, self.current_chat_messages, monologue_history, observation_log, long_term_context)
# # # # #         self.execute_ai_task(full_prompt, speak=True, is_user_request=True, is_continuation=True)

# # # # #     @Slot()
# # # # #     def on_query_keyword_worker_finished(self):
# # # # #         if self.query_keyword_worker:
# # # # #             self.query_keyword_worker.deleteLater()
# # # # #             self.query_keyword_worker = None

# # # # #     def open_file_dialog(self): 
# # # # #         if not self.active_session_id: self.create_new_session(); return
# # # # #         file_path, _ = QFileDialog.getOpenFileName(self, "問題ファイルを選択", "", "サポートファイル (*.pdf *.png *.jpg *.jpeg *.webp);;全ファイル (*)")
# # # # #         if file_path:
# # # # #             self._add_message_to_ui_and_db("ai", f"`{os.path.basename(file_path)}`を分析中...")
            
# # # # #             model_name = self.settings_manager.vision_model
# # # # #             gemini_client_for_file = GeminiClient(vision_model_name=model_name)
# # # # #             self.file_worker = FileProcessingWorker(file_path, gemini_client_for_file)
# # # # #             self.file_worker.finished_processing.connect(self.on_file_processed)
# # # # #             self.file_worker.finished.connect(self.on_file_worker_finished)
# # # # #             self.file_worker.start()

# # # # #     @Slot(str)
# # # # #     def on_file_processed(self, result_text):
# # # # #         if not self.active_session_id: return
# # # # #         self.db_worker.update_problem_context(self.active_session_id, result_text)
# # # # #         self.context_manager.set_problem_context(result_text)
# # # # #         message = f"ファイルの分析が完了しました。\n\n**【分析結果】**\n\n{result_text}\n\n---\nこの問題について質問してください。"
# # # # #         self._add_message_to_ui_and_db("ai", message)
# # # # #         self.tts_worker.speak("ファイルの分析が完了しました。")

# # # # #     @Slot()
# # # # #     def on_file_worker_finished(self):
# # # # #         if self.file_worker:
# # # # #             self.file_worker.deleteLater()
# # # # #             self.file_worker = None
            
# # # # #     @Slot(Image.Image)
# # # # #     def on_hand_stopped(self, captured_image):
# # # # #         if self.is_ai_task_running: return
# # # # #         self.context_manager.set_triggered_image(captured_image)
# # # # #         prompt = self.settings_manager.hand_stopped_prompt
# # # # #         self.execute_ai_task(prompt, speak=True)

# # # # #     @Slot(str)
# # # # #     def on_monologue_recognized(self, text):
# # # # #         if self.active_session_id:
# # # # #             self.db_worker.add_log(self.active_session_id, "monologue", text)
# # # # #         current_text = self.user_input.toPlainText()
# # # # #         new_text = (current_text + " " + text) if current_text and not current_text.endswith(" ") else (current_text + text)
# # # # #         self.user_input.setPlainText(new_text)
# # # # #         self.user_input.moveCursor(QTextCursor.MoveOperation.End)

# # # # #     @Slot(str)
# # # # #     def on_command_recognized(self, command_text):
# # # # #         if not self.active_session_id:
# # # # #             self.tts_worker.speak("すみません、現在アクティブなセッションがありません。")
# # # # #             return
            
# # # # #         if not self.latest_camera_frame:
# # # # #             self.tts_worker.speak("すみません、カメラの映像が取得できていません。")
# # # # #             return
        
# # # # #         self._add_message_to_ui_and_db("user", f"（音声コマンド）{command_text}")
# # # # #         self.context_manager.set_triggered_image(self.latest_camera_frame.copy())

# # # # #         self.is_ai_task_running = True
# # # # #         self.header_stack.setCurrentIndex(1)
# # # # #         if hasattr(self, 'movie'):
# # # # #             self.movie.start()
# # # # #         self.send_button.setEnabled(False)

# # # # #         long_term_context = self._get_long_term_context([])
# # # # #         monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
        
# # # # #         prompt_parts = self.context_manager.build_prompt_parts_for_command(
# # # # #             command_text, 
# # # # #             self.current_chat_messages, 
# # # # #             monologue_history, 
# # # # #             long_term_context
# # # # #         )
        
# # # # #         if prompt_parts:
# # # # #             self.execute_ai_task(prompt_parts, speak=True, is_user_request=False, use_vision=True, is_continuation=True)
# # # # #         else:
# # # # #             self.tts_worker.speak("コマンドの準備に失敗しました。")
# # # # #             self.is_ai_task_running = False
# # # # #             self.header_stack.setCurrentIndex(0)
# # # # #             self.send_button.setEnabled(True)

# # # # #     @Slot(str)
# # # # #     def on_observation_received(self, observation_text: str):
# # # # #         if self.active_session_id:
# # # # #             self.db_worker.add_log(self.active_session_id, "observation", observation_text)

# # # # #     @Slot(QImage, list)
# # # # #     def update_camera_view(self, frame_qimage: QImage, detections: List[Dict]):
# # # # #         if frame_qimage.isNull():
# # # # #             return
        
# # # # #         pixmap = QPixmap.fromImage(frame_qimage)
# # # # #         painter = QPainter(pixmap)
# # # # #         for detection in detections:
# # # # #             box = detection["box"]
# # # # #             label = f'{detection["label"]} {detection["confidence"]:.2f}'
# # # # #             pen = QPen(QColor(0, 255, 0), 2)
# # # # #             painter.setPen(pen)
# # # # #             painter.drawRect(box[0], box[1], box[2] - box[0], box[3] - box[1])
# # # # #             font = QFont()
# # # # #             font.setPointSize(10)
# # # # #             painter.setFont(font)
# # # # #             painter.setPen(QColor(255, 255, 255))
# # # # #             text_x, text_y = box[0], box[1] - 5
# # # # #             painter.fillRect(text_x, text_y - 12, len(label) * 8, 16, QColor(0, 255, 0))
# # # # #             painter.drawText(text_x, text_y, label)
# # # # #         painter.end()
# # # # #         self.camera_view.setPixmap(pixmap)
        
# # # # #         buffer = frame_qimage.constBits().tobytes()
# # # # #         self.latest_camera_frame = Image.frombytes("RGBA", (frame_qimage.width(), frame_qimage.height()), buffer, 'raw', "BGRA")

# # # # #     def closeEvent(self, event):
# # # # #         """アプリケーション終了時に、すべてのリソースを安全に解放する"""
# # # # #         print("アプリケーションの終了処理を開始します...")

# # # # #         print("UI関連以外のワーカースレッドを停止します...")
# # # # #         self.stop_camera_dependent_workers()
        
# # # # #         if self.stt_worker and self.stt_worker.isRunning():
# # # # #             self.stt_worker.stop()
# # # # #             self.stt_worker.wait()
# # # # #             print(" > STTWorker 停止完了")
        
# # # # #         if self.tts_worker and self.tts_worker.isRunning():
# # # # #             self.tts_worker.stop()
# # # # #             self.tts_worker.wait()
# # # # #             print(" > TTSWorker 停止完了")
            
# # # # #         if self.active_session_id:
# # # # #             print(f"セッションID {self.active_session_id} の最終処理を実行します...")
            
# # # # #             messages = self.db_manager.get_messages_for_session(self.active_session_id)
# # # # #             if len(messages) >= 4:
# # # # #                 conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                
# # # # #                 main_gemini_client = GeminiClient(text_model_name=self.settings_manager.keyword_extraction_model)
                
# # # # #                 kw_prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
# # # # #                 kw_prompt = kw_prompt_template.format(conversation_text=conversation_text)
# # # # #                 print(" > キーワードを抽出中...")
# # # # #                 keywords_response = main_gemini_client.generate_response(kw_prompt)
# # # # #                 match_kw = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# # # # #                 cleaned_keywords = match_kw.group(1).strip() if match_kw else keywords_response.strip()
# # # # #                 cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
# # # # #                 self.db_manager.update_session_keywords(self.active_session_id, cleaned_keywords)
# # # # #                 print(f" > キーワードを保存しました: {cleaned_keywords}")

# # # # #                 title_prompt_template = self.settings_manager.title_generation_prompt
# # # # #                 title_prompt = title_prompt_template.format(conversation_text=conversation_text)
# # # # #                 print(" > タイトルを生成中...")
# # # # #                 title = main_gemini_client.generate_response(title_prompt)
# # # # #                 cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
# # # # #                 self.db_manager.update_session_title(self.active_session_id, cleaned_title)
# # # # #                 print(f" > タイトルを保存しました: {cleaned_title}")

# # # # #         if self.db_worker and self.db_worker.isRunning():
# # # # #             print("データベースへの書き込み完了を待っています...")
# # # # #             while self.db_worker.tasks:
# # # # #                 print(f" > DBワーカーの残りタスク: {len(self.db_worker.tasks)}件")
# # # # #                 QThread.msleep(100)
# # # # #             self.db_worker.stop()
# # # # #             self.db_worker.wait()
# # # # #             print(" > DatabaseWorker 停止完了")
            
# # # # #         print("すべての処理が安全に完了しました。アプリケーションを終了します。")
# # # # #         super().closeEvent(event)






















# # # # # UIの柔軟化

# # # # import sys
# # # # import os
# # # # import fitz
# # # # import re
# # # # from PIL import Image
# # # # from PySide6.QtCore import QThread, Signal, Slot, QSize, Qt
# # # # from PySide6.QtGui import QPixmap, QImage, QTextCursor, QMovie, QPainter, QColor, QPen, QFont, QAction
# # # # from PySide6.QtWidgets import (
# # # #     QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLabel,
# # # #     QHBoxLayout, QCheckBox, QFileDialog, QStackedLayout, 
# # # #     QListWidget, QListWidgetItem, QDockWidget
# # # # )
# # # # from typing import Optional, List, Dict

# # # # from .widgets.md_view import MarkdownView
# # # # from .settings_dialog import SettingsDialog
# # # # from ..core.context_manager import ContextManager
# # # # from ..core.gemini_client import GeminiClient
# # # # from ..core.database_manager import DatabaseManager
# # # # from ..core.database_worker import DatabaseWorker
# # # # from ..core.visual_observer import VisualObserverWorker
# # # # from ..core.settings_manager import SettingsManager
# # # # from ..hardware.camera_handler import CameraWorker
# # # # from ..hardware.audio_handler import TTSWorker, STTWorker

# # # # # --- ワーカースレッド定義 (変更なし) ---
# # # # class FileProcessingWorker(QThread):
# # # #     finished_processing = Signal(str)
# # # #     def __init__(self, file_path, gemini_client, parent=None):
# # # #         super().__init__(parent)
# # # #         self.file_path = file_path
# # # #         self.gemini_client = gemini_client
# # # #     def run(self):
# # # #         images = []
# # # #         file_path_lower = self.file_path.lower()
# # # #         try:
# # # #             if file_path_lower.endswith('.pdf'):
# # # #                 doc = fitz.open(self.file_path)
# # # #                 for page in doc:
# # # #                     pix = page.get_pixmap(dpi=150)
# # # #                     img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
# # # #                     images.append(img)
# # # #                 doc.close()
# # # #             elif file_path_lower.endswith(('.png', '.jpg', '.jpeg', '.webp')):
# # # #                 images.append(Image.open(self.file_path).convert("RGB"))
# # # #             else:
# # # #                 self.finished_processing.emit("サポートされていない形式です。")
# # # #                 return
# # # #             if not images:
# # # #                 self.finished_processing.emit("画像を変換できませんでした。")
# # # #                 return
# # # #             prompt = "この画像は学習教材です。含まれるテキストや数式を正確に書き出してください。"
# # # #             self.finished_processing.emit(self.gemini_client.generate_vision_response([prompt] + images))
# # # #         except Exception as e:
# # # #             self.finished_processing.emit(f"ファイル処理エラー: {e}")

# # # # class GeminiWorker(QThread):
# # # #     response_ready = Signal(str)
# # # #     def __init__(self, prompt, model_name=None, parent=None):
# # # #         super().__init__(parent)
# # # #         self.prompt = prompt
# # # #         self.gemini_client = GeminiClient(text_model_name=model_name)
# # # #     def run(self):
# # # #         self.response_ready.emit(self.gemini_client.generate_response(self.prompt))

# # # # class GeminiVisionWorker(QThread):
# # # #     response_ready = Signal(str)
# # # #     def __init__(self, prompt_parts, model_name=None, parent=None):
# # # #         super().__init__(parent)
# # # #         self.prompt_parts = prompt_parts
# # # #         self.gemini_client = GeminiClient(vision_model_name=model_name)
# # # #     def run(self):
# # # #         self.response_ready.emit(self.gemini_client.generate_vision_response(self.prompt_parts))

# # # # # --- メインウィンドウ ---
# # # # class MainWindow(QMainWindow):
# # # #     def __init__(self):
# # # #         super().__init__()
# # # #         self.setWindowTitle("勉強アシストアプリ")
# # # #         self.setGeometry(100, 100, 1600, 900)
        
# # # #         self.is_ai_task_running = False
# # # #         self.context_manager = ContextManager()
# # # #         self.settings_manager = SettingsManager()
# # # #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# # # #         db_path = os.path.join(project_root, "data", "sessions.db")
# # # #         self.db_manager = DatabaseManager(db_path=db_path)
# # # #         self.active_session_id: Optional[int] = None
# # # #         self.latest_camera_frame: Optional[Image.Image] = None

# # # #         self.camera_worker: Optional[CameraWorker] = None
# # # #         self.stt_worker: Optional[STTWorker] = None
# # # #         self.observer_worker: Optional[VisualObserverWorker] = None
# # # #         self.tts_worker: Optional[TTSWorker] = None
# # # #         self.db_worker: Optional[DatabaseWorker] = None
# # # #         self.file_worker: Optional[FileProcessingWorker] = None
# # # #         self.keyword_extraction_worker: Optional[GeminiWorker] = None
# # # #         self.query_keyword_worker: Optional[GeminiWorker] = None
# # # #         self.title_generation_worker: Optional[GeminiWorker] = None

# # # #         self.current_chat_messages: List[Dict[str, str]] = []
# # # #         self.stt_was_enabled_before_tts = False

# # # #         self.setup_ui()
# # # #         self.create_menu()
        
# # # #         self.start_essential_workers()
# # # #         self.restart_stt_worker()
        
# # # #         self.load_and_display_sessions()

# # # #         if self.settings_manager.camera_enabled_on_startup:
# # # #             self.camera_enabled_checkbox.setChecked(True)
# # # #         else:
# # # #             self.camera_enabled_checkbox.setChecked(False)
# # # #             self.camera_view.setText("カメラはオフです")

# # # #     def setup_ui(self):
# # # #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        
# # # #         # 1. セッション履歴パネルの作成
# # # #         session_area_widget = QWidget()
# # # #         session_layout = QVBoxLayout(session_area_widget)
# # # #         self.new_session_button = QPushButton("＋ 新しいチャット")
# # # #         self.session_list_widget = QListWidget()
# # # #         session_layout.addWidget(self.new_session_button)
# # # #         session_layout.addWidget(self.session_list_widget)

# # # #         # 2. メインのチャットパネルの作成
# # # #         main_chat_widget = QWidget()
# # # #         left_layout = QVBoxLayout(main_chat_widget)
# # # #         self.ai_output_view = MarkdownView()
# # # #         self.user_input = QTextEdit()
# # # #         self.send_button = QPushButton("送信")
# # # #         self.stt_enabled_checkbox = QCheckBox("音声認識")
# # # #         self.load_file_button = QPushButton("問題ファイルを読み込む")
# # # #         self.stop_speech_button = QPushButton("読み上げを停止")
# # # #         self.stop_speech_button.setVisible(False)
# # # #         loading_widget = QWidget()
# # # #         loading_layout = QHBoxLayout(loading_widget)
# # # #         loading_layout.setContentsMargins(0, 5, 0, 5)
# # # #         self.loading_movie_label = QLabel()
# # # #         loading_gif_path = os.path.join(project_root, "assets", "loading.gif")
# # # #         if os.path.exists(loading_gif_path):
# # # #             self.movie = QMovie(loading_gif_path)
# # # #             self.loading_movie_label.setMovie(self.movie)
# # # #             self.movie.setScaledSize(QSize(25, 25))
# # # #         self.loading_text_label = QLabel("AIが考え中です...")
# # # #         loading_layout.addStretch()
# # # #         loading_layout.addWidget(self.loading_movie_label)
# # # #         loading_layout.addWidget(self.loading_text_label)
# # # #         loading_layout.addStretch()
# # # #         self.header_stack = QStackedLayout()
# # # #         self.header_stack.addWidget(QLabel("AIアシスタント"))
# # # #         self.header_stack.addWidget(loading_widget)
# # # #         top_button_layout = QHBoxLayout()
# # # #         top_button_layout.addWidget(self.load_file_button)
# # # #         top_button_layout.addStretch()
# # # #         self.camera_enabled_checkbox = QCheckBox("カメラを有効にする")
# # # #         top_button_layout.addWidget(self.camera_enabled_checkbox)
# # # #         top_button_layout.addWidget(self.stt_enabled_checkbox)
# # # #         button_v_layout = QVBoxLayout()
# # # #         button_v_layout.addWidget(self.send_button)
# # # #         button_v_layout.addWidget(self.stop_speech_button)
# # # #         input_area_layout = QHBoxLayout()
# # # #         input_area_layout.addWidget(self.user_input)
# # # #         input_area_layout.addLayout(button_v_layout)
# # # #         left_layout.addLayout(top_button_layout)
# # # #         left_layout.addLayout(self.header_stack)
# # # #         left_layout.addWidget(self.ai_output_view, stretch=1)
# # # #         left_layout.addWidget(QLabel("質問や独り言を入力"))
# # # #         left_layout.addLayout(input_area_layout)

# # # #         # 3. カメラビューパネルの作成
# # # #         right_widget = QWidget()
# # # #         right_layout = QVBoxLayout(right_widget)
# # # #         self.camera_view = QLabel("カメラを初期化中...")
# # # #         self.camera_view.setStyleSheet("background-color: black; color: white;")
# # # #         self.camera_view.setFixedSize(640, 480)
# # # #         right_layout.addWidget(self.camera_view)
# # # #         right_layout.addStretch()

# # # #         # 4. DockWidgetを使ってレイアウトを構築
# # # #         self.setCentralWidget(main_chat_widget)

# # # #         self.session_dock = QDockWidget("セッション履歴", self)
# # # #         self.session_dock.setWidget(session_area_widget)
# # # #         self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.session_dock)

# # # #         self.camera_dock = QDockWidget("カメラビュー", self)
# # # #         self.camera_dock.setWidget(right_widget)
# # # #         self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.camera_dock)
        
# # # #         # 5. シグナル接続
# # # #         self.new_session_button.clicked.connect(self.create_new_session)
# # # #         self.session_list_widget.currentItemChanged.connect(self.on_session_changed)
# # # #         self.send_button.clicked.connect(self.start_user_request)
# # # #         self.load_file_button.clicked.connect(self.open_file_dialog)
# # # #         self.stop_speech_button.clicked.connect(self.on_stop_speech_button_clicked)
# # # #         self.camera_enabled_checkbox.toggled.connect(self.on_camera_enabled_changed)
# # # #         self.stt_enabled_checkbox.toggled.connect(self.on_stt_enabled_changed)

# # # #     def create_menu(self):
# # # #         menu_bar = self.menuBar()
# # # #         file_menu = menu_bar.addMenu("ファイル")
# # # #         settings_action = QAction("設定...", self)
# # # #         settings_action.triggered.connect(self.open_settings_dialog)
# # # #         file_menu.addAction(settings_action)

# # # #         # 表示メニューを追加してDockの表示/非表示を制御
# # # #         view_menu = self.menuBar().addMenu("表示")
# # # #         view_menu.addAction(self.session_dock.toggleViewAction())
# # # #         view_menu.addAction(self.camera_dock.toggleViewAction())

# # # #     # --- (以降のメソッドは前回のコードと同じです) ---

# # # #     def start_essential_workers(self):
# # # #         self.db_worker = DatabaseWorker(self.db_manager)
# # # #         self.tts_worker = TTSWorker()
# # # #         self.db_worker.start()
# # # #         self.tts_worker.start()
# # # #         self.tts_worker.speech_finished.connect(self.on_speech_finished)
    
# # # #     def start_camera_dependent_workers(self):
# # # #         self.stop_camera_dependent_workers() 
# # # #         print("カメラ関連ワーカーを起動します...")
# # # #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# # # #         model_path = os.path.join(project_root, "models", "best12-2.pt")
# # # #         self.camera_worker = CameraWorker(
# # # #             model_path=model_path,
# # # #             device_index=self.settings_manager.camera_device_index,
# # # #             stop_threshold_sec=self.settings_manager.hand_stop_threshold
# # # #         )
# # # #         self.observer_worker = VisualObserverWorker(
# # # #             interval_sec=self.settings_manager.observation_interval
# # # #         )
# # # #         self.camera_worker.frame_data_ready.connect(self.update_camera_view)
# # # #         self.camera_worker.hand_stopped_signal.connect(self.on_hand_stopped)
# # # #         self.camera_worker.raw_frame_for_observation.connect(self.observer_worker.update_frame)
# # # #         self.observer_worker.observation_ready.connect(self.on_observation_received)
# # # #         self.camera_worker.start()
# # # #         self.observer_worker.start()

# # # #     def stop_camera_dependent_workers(self):
# # # #         if self.camera_worker and self.camera_worker.isRunning():
# # # #             print("CameraWorkerを停止します...")
# # # #             self.camera_worker.frame_data_ready.disconnect(self.update_camera_view)
# # # #             self.camera_worker.hand_stopped_signal.disconnect(self.on_hand_stopped)
# # # #             self.camera_worker.raw_frame_for_observation.disconnect(self.observer_worker.update_frame)
# # # #             self.camera_worker.stop()
# # # #             self.camera_worker.wait()
# # # #             self.camera_worker = None
# # # #             print(" > CameraWorker 停止完了")
# # # #         if self.observer_worker and self.observer_worker.isRunning():
# # # #             print("VisualObserverWorkerを停止します...")
# # # #             self.observer_worker.stop()
# # # #             self.observer_worker.wait()
# # # #             self.observer_worker = None
# # # #             print(" > VisualObserverWorker 停止完了")

# # # #     def restart_stt_worker(self):
# # # #         print("STTワーカーを再起動します...")
# # # #         if self.stt_worker and self.stt_worker.isRunning():
# # # #             self.stt_worker.monologue_recognized.disconnect(self.on_monologue_recognized)
# # # #             self.stt_worker.command_recognized.disconnect(self.on_command_recognized)
# # # #             self.stt_worker.stop()
# # # #             self.stt_worker.wait()
# # # #         self.stt_worker = STTWorker(device_index=self.settings_manager.mic_device_index)
# # # #         self.stt_worker.monologue_recognized.connect(self.on_monologue_recognized)
# # # #         self.stt_worker.command_recognized.connect(self.on_command_recognized)
# # # #         self.stt_worker.set_enabled(self.stt_enabled_checkbox.isChecked())
# # # #         self.stt_worker.start()
# # # #         print(" > STTWorker 再起動完了")
        
# # # #     def open_settings_dialog(self):
# # # #         dialog = SettingsDialog(self)
# # # #         if dialog.exec():
# # # #             print("設定が変更されました。動的設定を適用し、必要なワーカーを再起動します。")
# # # #             self.apply_settings_dynamically()
# # # #             self.restart_stt_worker()
# # # #             if self.camera_enabled_checkbox.isChecked():
# # # #                 self.start_camera_dependent_workers()
# # # #             print("ワーカーの再起動・設定反映が完了しました。")
# # # #         else:
# # # #             print("設定はキャンセルされました。")
            
# # # #     def apply_settings_dynamically(self):
# # # #         if self.tts_worker and self.tts_worker.isRunning():
# # # #             self.tts_worker.set_tts_enabled(self.settings_manager.tts_enabled)
# # # #             self.tts_worker.set_tts_rate(self.settings_manager.tts_rate)
# # # #         if self.camera_worker and self.camera_worker.isRunning():
# # # #             self.camera_worker.set_stop_threshold(self.settings_manager.hand_stop_threshold)
# # # #         if self.observer_worker and self.observer_worker.isRunning():
# # # #             self.observer_worker.set_observation_interval(self.settings_manager.observation_interval)

# # # #     @Slot(bool)
# # # #     def on_camera_enabled_changed(self, enabled: bool):
# # # #         if enabled:
# # # #             self.start_camera_dependent_workers()
# # # #         else:
# # # #             self.stop_camera_dependent_workers()
# # # #             self.camera_view.setText("カメラはオフです")
# # # #             self.latest_camera_frame = None

# # # #     @Slot(bool)
# # # #     def on_stt_enabled_changed(self, enabled: bool):
# # # #         if self.stt_worker:
# # # #             self.stt_worker.set_enabled(enabled)

# # # #     def _get_long_term_context(self, relevant_sessions: List[Dict]) -> str:
# # # #         if not relevant_sessions:
# # # #             last_session_id = self.db_manager.get_last_active_session_id(exclude_session_id=self.active_session_id)
# # # #             if not last_session_id: return "これが最初のセッションです。"
# # # #             last_session_details = self.db_manager.get_session_details(last_session_id)
# # # #             if not last_session_details: return "前回のセッション情報を取得できませんでした。"
# # # #             last_messages = self.db_manager.get_messages_for_session(last_session_id)
# # # #             last_user_message = next((msg['content'] for msg in reversed(last_messages) if msg['role'] == 'user'), "なし")
# # # #             return f"（直近のセッションより）\n- 前回（{last_session_details['last_updated_at']}）のセッションでは、「{last_session_details['title']}」について学習しており、最後の質問は「{last_user_message}」でした。"
        
# # # #         context_lines = ["（過去の関連セッションより）"]
# # # #         for session in relevant_sessions:
# # # #             line = f"- セッション「{session['title']}」（{session['last_updated_at']}）では、キーワード「{session['keywords']}」について議論しました。"
# # # #             context_lines.append(line)
# # # #         return "\n".join(context_lines)

# # # #     def _add_message_to_ui_and_db(self, role: str, content: str):
# # # #         if not self.active_session_id: return
# # # #         self.current_chat_messages.append({"role": role, "content": content})
# # # #         self.update_chat_display()
# # # #         self.db_worker.add_message(self.active_session_id, role, content)

# # # #     def _trigger_keyword_extraction(self, session_id: int):
# # # #         if not session_id: return
# # # #         if self.keyword_extraction_worker and self.keyword_extraction_worker.isRunning(): return
# # # #         messages = self.db_manager.get_messages_for_session(session_id)
# # # #         if len(messages) < 4: return
# # # #         conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
# # # #         prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
# # # #         prompt = prompt_template.format(conversation_text=conversation_text)
        
# # # #         model_name = self.settings_manager.keyword_extraction_model
# # # #         self.keyword_extraction_worker = GeminiWorker(prompt, model_name=model_name)
# # # #         self.keyword_extraction_worker.response_ready.connect(lambda keywords: self.on_keywords_extracted(session_id, keywords))
# # # #         self.keyword_extraction_worker.finished.connect(self.on_keyword_worker_finished)
# # # #         self.keyword_extraction_worker.start()

# # # #     def _trigger_title_generation(self, session_id: int):
# # # #         if not session_id: return
# # # #         if self.title_generation_worker and self.title_generation_worker.isRunning(): return
# # # #         messages = self.db_manager.get_messages_for_session(session_id)
# # # #         if len(messages) < 4: return
# # # #         conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
# # # #         prompt_template = self.settings_manager.title_generation_prompt
# # # #         prompt = prompt_template.format(conversation_text=conversation_text)
        
# # # #         model_name = self.settings_manager.keyword_extraction_model
# # # #         self.title_generation_worker = GeminiWorker(prompt, model_name=model_name)
# # # #         self.title_generation_worker.response_ready.connect(lambda title: self.on_title_generated(session_id, title))
# # # #         self.title_generation_worker.finished.connect(self.on_title_generation_finished)
# # # #         self.title_generation_worker.start()

# # # #     @Slot(int, str)
# # # #     def on_title_generated(self, session_id: int, title: str):
# # # #         cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
# # # #         self.db_worker.update_session_title(session_id, cleaned_title)
# # # #         for i in range(self.session_list_widget.count()):
# # # #             item = self.session_list_widget.item(i)
# # # #             if item.data(Qt.UserRole) == session_id:
# # # #                 item.setText(cleaned_title)
# # # #                 break
    
# # # #     @Slot()
# # # #     def on_title_generation_finished(self):
# # # #         if self.title_generation_worker:
# # # #             self.title_generation_worker.deleteLater()
# # # #             self.title_generation_worker = None

# # # #     @Slot(int, str)
# # # #     def on_keywords_extracted(self, session_id: int, keywords_response: str):
# # # #         match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# # # #         cleaned_keywords = match.group(1).strip() if match else keywords_response.strip()
# # # #         cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
# # # #         self.db_worker.update_session_keywords(session_id, cleaned_keywords)
        
# # # #     @Slot()
# # # #     def on_keyword_worker_finished(self):
# # # #         if self.keyword_extraction_worker:
# # # #             self.keyword_extraction_worker.deleteLater()
# # # #             self.keyword_extraction_worker = None

# # # #     def update_chat_display(self):
# # # #         md_text = ""
# # # #         for msg in self.current_chat_messages:
# # # #             role_display = "あなた" if msg["role"] == "user" else "AIアシスタント"
# # # #             md_text += f"**{role_display}:**\n\n{msg['content']}\n\n<hr>\n\n"
# # # #         self.ai_output_view.set_markdown(md_text)

# # # #     def load_and_display_sessions(self):
# # # #         self.session_list_widget.blockSignals(True)
# # # #         self.session_list_widget.clear()
# # # #         sessions = self.db_manager.get_all_sessions()
# # # #         if not sessions:
# # # #             self.create_new_session(is_initial=True)
# # # #             sessions = self.db_manager.get_all_sessions()
# # # #         for session_id, title in sessions:
# # # #             item = QListWidgetItem(title)
# # # #             item.setData(Qt.UserRole, session_id)
# # # #             self.session_list_widget.addItem(item)
# # # #         self.session_list_widget.setCurrentRow(0)
# # # #         self.session_list_widget.blockSignals(False)
# # # #         if self.session_list_widget.currentItem():
# # # #             self.on_session_changed(self.session_list_widget.currentItem(), None)

# # # #     def create_new_session(self, is_initial=False):
# # # #         self.db_manager.create_new_session()
# # # #         if not is_initial:
# # # #             self.load_and_display_sessions()

# # # #     @Slot(QListWidgetItem, QListWidgetItem)
# # # #     def on_session_changed(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
# # # #         if previous_item:
# # # #             previous_session_id = previous_item.data(Qt.UserRole)
# # # #             self._trigger_keyword_extraction(previous_session_id)
# # # #             self._trigger_title_generation(previous_session_id)
# # # #         if not current_item: return
# # # #         session_id = current_item.data(Qt.UserRole)
# # # #         if session_id == self.active_session_id: return
# # # #         self.active_session_id = session_id
# # # #         session_details = self.db_manager.get_session_details(session_id)
# # # #         if session_details:
# # # #             self.context_manager.set_problem_context(session_details.get("problem_context"))
# # # #         self.current_chat_messages = self.db_manager.get_messages_for_session(self.active_session_id)
# # # #         self.update_chat_display()

# # # #     @Slot()
# # # #     def on_stop_speech_button_clicked(self):
# # # #         self.tts_worker.stop_current_speech()

# # # #     def execute_ai_task(self, prompt, speak=True, is_user_request=False, use_vision=False, is_continuation=False):
# # # #         if self.is_ai_task_running and not is_continuation:
# # # #             return
# # # #         if not is_continuation:
# # # #             self.is_ai_task_running = True
# # # #             self.header_stack.setCurrentIndex(1)
# # # #             if hasattr(self, 'movie'): self.movie.start()
            
# # # #         if is_user_request:
# # # #             self.send_button.setEnabled(False)
# # # #         if speak:
# # # #             self.stop_speech_button.setVisible(True)
            
# # # #         if use_vision:
# # # #             model_name = self.settings_manager.vision_model
# # # #             self.ai_worker = GeminiVisionWorker(prompt, model_name=model_name)
# # # #         else:
# # # #             model_name = self.settings_manager.main_response_model
# # # #             self.ai_worker = GeminiWorker(prompt, model_name=model_name)
            
# # # #         self.ai_worker.response_ready.connect(lambda r: self.handle_gemini_response(r, speak))
# # # #         self.ai_worker.finished.connect(self.on_ai_worker_finished)
# # # #         self.ai_worker.start()

# # # #     def handle_gemini_response(self, response_text, speak):
# # # #         if hasattr(self, 'movie'): self.movie.stop()
# # # #         self.header_stack.setCurrentIndex(0)
        
# # # #         self._add_message_to_ui_and_db("ai", response_text)
        
# # # #         if speak:
# # # #             print("読み上げ開始。音声認識を一時停止します。")
# # # #             self.stt_was_enabled_before_tts = self.stt_enabled_checkbox.isChecked()
# # # #             if self.stt_was_enabled_before_tts:
# # # #                 self.stt_enabled_checkbox.setChecked(False)
# # # #             self.tts_worker.speak(response_text)
# # # #         else:
# # # #             self.is_ai_task_running = False
# # # #             self.stop_speech_button.setVisible(False)
# # # #             if not self.send_button.isEnabled():
# # # #                 self.send_button.setEnabled(True)

# # # #     @Slot()
# # # #     def on_speech_finished(self):
# # # #         self.is_ai_task_running = False
# # # #         self.stop_speech_button.setVisible(False)
        
# # # #         print("読み上げ完了。音声認識の状態を復元します。")
# # # #         if self.stt_was_enabled_before_tts:
# # # #             self.stt_enabled_checkbox.setChecked(True)
        
# # # #         if not self.send_button.isEnabled():
# # # #             self.send_button.setEnabled(True)

# # # #     @Slot()
# # # #     def on_ai_worker_finished(self):
# # # #         if self.ai_worker:
# # # #             self.ai_worker.deleteLater()
# # # #             self.ai_worker = None

# # # #     def start_user_request(self):
# # # #         user_query = self.user_input.toPlainText().strip()
# # # #         if not (user_query and self.active_session_id): return
        
# # # #         self._add_message_to_ui_and_db("user", user_query)
# # # #         self.user_input.clear()
        
# # # #         self.is_ai_task_running = True
# # # #         self.header_stack.setCurrentIndex(1)
# # # #         if hasattr(self, 'movie'): self.movie.start()
# # # #         self.send_button.setEnabled(False)
        
# # # #         prompt = f"""以下の質問文から、中心となるキーワードを3つ、カンマ区切りで抽出してください。思考プロセスは不要です。キーワードのみを出力してください。\n例: 積分、グラフ、面積\n\n---\n{user_query}"""
        
# # # #         model_name = self.settings_manager.keyword_extraction_model
# # # #         self.query_keyword_worker = GeminiWorker(prompt, model_name=model_name)
# # # #         self.query_keyword_worker.response_ready.connect(lambda keywords: self.on_query_keywords_extracted(user_query, keywords))
# # # #         self.query_keyword_worker.finished.connect(self.on_query_keyword_worker_finished)
# # # #         self.query_keyword_worker.start()

# # # #     @Slot(str, str)
# # # #     def on_query_keywords_extracted(self, original_query: str, keywords_response: str):
# # # #         match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# # # #         cleaned_keywords_str = match.group(1).strip() if match else keywords_response.strip()
# # # #         cleaned_keywords = [kw.strip() for kw in cleaned_keywords_str.split(',') if kw.strip()]
        
# # # #         if not self.active_session_id: return
        
# # # #         relevant_sessions = self.db_manager.find_relevant_sessions(cleaned_keywords, exclude_session_id=self.active_session_id)
# # # #         long_term_context = self._get_long_term_context(relevant_sessions)
# # # #         monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
# # # #         observation_log = self.db_manager.get_recent_logs_for_session(self.active_session_id, "observation", 5)
        
# # # #         full_prompt = self.context_manager.build_prompt_for_query(original_query, self.current_chat_messages, monologue_history, observation_log, long_term_context)
# # # #         self.execute_ai_task(full_prompt, speak=True, is_user_request=True, is_continuation=True)

# # # #     @Slot()
# # # #     def on_query_keyword_worker_finished(self):
# # # #         if self.query_keyword_worker:
# # # #             self.query_keyword_worker.deleteLater()
# # # #             self.query_keyword_worker = None

# # # #     def open_file_dialog(self): 
# # # #         if not self.active_session_id: self.create_new_session(); return
# # # #         file_path, _ = QFileDialog.getOpenFileName(self, "問題ファイルを選択", "", "サポートファイル (*.pdf *.png *.jpg *.jpeg *.webp);;全ファイル (*)")
# # # #         if file_path:
# # # #             self._add_message_to_ui_and_db("ai", f"`{os.path.basename(file_path)}`を分析中...")
            
# # # #             model_name = self.settings_manager.vision_model
# # # #             gemini_client_for_file = GeminiClient(vision_model_name=model_name)
# # # #             self.file_worker = FileProcessingWorker(file_path, gemini_client_for_file)
# # # #             self.file_worker.finished_processing.connect(self.on_file_processed)
# # # #             self.file_worker.finished.connect(self.on_file_worker_finished)
# # # #             self.file_worker.start()

# # # #     @Slot(str)
# # # #     def on_file_processed(self, result_text):
# # # #         if not self.active_session_id: return
# # # #         self.db_worker.update_problem_context(self.active_session_id, result_text)
# # # #         self.context_manager.set_problem_context(result_text)
# # # #         message = f"ファイルの分析が完了しました。\n\n**【分析結果】**\n\n{result_text}\n\n---\nこの問題について質問してください。"
# # # #         self._add_message_to_ui_and_db("ai", message)
# # # #         self.tts_worker.speak("ファイルの分析が完了しました。")

# # # #     @Slot()
# # # #     def on_file_worker_finished(self):
# # # #         if self.file_worker:
# # # #             self.file_worker.deleteLater()
# # # #             self.file_worker = None
            
# # # #     @Slot(Image.Image)
# # # #     def on_hand_stopped(self, captured_image):
# # # #         if self.is_ai_task_running: return
# # # #         self.context_manager.set_triggered_image(captured_image)
# # # #         prompt = self.settings_manager.hand_stopped_prompt
# # # #         self.execute_ai_task(prompt, speak=True)

# # # #     @Slot(str)
# # # #     def on_monologue_recognized(self, text):
# # # #         if self.active_session_id:
# # # #             self.db_worker.add_log(self.active_session_id, "monologue", text)
# # # #         current_text = self.user_input.toPlainText()
# # # #         new_text = (current_text + " " + text) if current_text and not current_text.endswith(" ") else (current_text + text)
# # # #         self.user_input.setPlainText(new_text)
# # # #         self.user_input.moveCursor(QTextCursor.MoveOperation.End)

# # # #     @Slot(str)
# # # #     def on_command_recognized(self, command_text):
# # # #         if not self.active_session_id:
# # # #             self.tts_worker.speak("すみません、現在アクティブなセッションがありません。")
# # # #             return
            
# # # #         if not self.latest_camera_frame:
# # # #             self.tts_worker.speak("すみません、カメラの映像が取得できていません。")
# # # #             return
        
# # # #         self._add_message_to_ui_and_db("user", f"（音声コマンド）{command_text}")
# # # #         self.context_manager.set_triggered_image(self.latest_camera_frame.copy())

# # # #         self.is_ai_task_running = True
# # # #         self.header_stack.setCurrentIndex(1)
# # # #         if hasattr(self, 'movie'):
# # # #             self.movie.start()
# # # #         self.send_button.setEnabled(False)

# # # #         long_term_context = self._get_long_term_context([])
# # # #         monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
        
# # # #         prompt_parts = self.context_manager.build_prompt_parts_for_command(
# # # #             command_text, 
# # # #             self.current_chat_messages, 
# # # #             monologue_history, 
# # # #             long_term_context
# # # #         )
        
# # # #         if prompt_parts:
# # # #             self.execute_ai_task(prompt_parts, speak=True, is_user_request=False, use_vision=True, is_continuation=True)
# # # #         else:
# # # #             self.tts_worker.speak("コマンドの準備に失敗しました。")
# # # #             self.is_ai_task_running = False
# # # #             self.header_stack.setCurrentIndex(0)
# # # #             self.send_button.setEnabled(True)

# # # #     @Slot(str)
# # # #     def on_observation_received(self, observation_text: str):
# # # #         if self.active_session_id:
# # # #             self.db_worker.add_log(self.active_session_id, "observation", observation_text)

# # # #     @Slot(QImage, list)
# # # #     def update_camera_view(self, frame_qimage: QImage, detections: List[Dict]):
# # # #         if frame_qimage.isNull():
# # # #             return
        
# # # #         pixmap = QPixmap.fromImage(frame_qimage)
# # # #         painter = QPainter(pixmap)
# # # #         for detection in detections:
# # # #             box = detection["box"]
# # # #             label = f'{detection["label"]} {detection["confidence"]:.2f}'
# # # #             pen = QPen(QColor(0, 255, 0), 2)
# # # #             painter.setPen(pen)
# # # #             painter.drawRect(box[0], box[1], box[2] - box[0], box[3] - box[1])
# # # #             font = QFont()
# # # #             font.setPointSize(10)
# # # #             painter.setFont(font)
# # # #             painter.setPen(QColor(255, 255, 255))
# # # #             text_x, text_y = box[0], box[1] - 5
# # # #             painter.fillRect(text_x, text_y - 12, len(label) * 8, 16, QColor(0, 255, 0))
# # # #             painter.drawText(text_x, text_y, label)
# # # #         painter.end()
# # # #         self.camera_view.setPixmap(pixmap)
        
# # # #         buffer = frame_qimage.constBits().tobytes()
# # # #         self.latest_camera_frame = Image.frombytes("RGBA", (frame_qimage.width(), frame_qimage.height()), buffer, 'raw', "BGRA")

# # # #     def closeEvent(self, event):
# # # #         """アプリケーション終了時に、すべてのリソースを安全に解放する"""
# # # #         print("アプリケーションの終了処理を開始します...")

# # # #         print("UI関連以外のワーカースレッドを停止します...")
# # # #         self.stop_camera_dependent_workers()
        
# # # #         if self.stt_worker and self.stt_worker.isRunning():
# # # #             self.stt_worker.stop()
# # # #             self.stt_worker.wait()
# # # #             print(" > STTWorker 停止完了")
        
# # # #         if self.tts_worker and self.tts_worker.isRunning():
# # # #             self.tts_worker.stop()
# # # #             self.tts_worker.wait()
# # # #             print(" > TTSWorker 停止完了")
            
# # # #         if self.active_session_id:
# # # #             print(f"セッションID {self.active_session_id} の最終処理を実行します...")
            
# # # #             messages = self.db_manager.get_messages_for_session(self.active_session_id)
# # # #             if len(messages) >= 4:
# # # #                 conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                
# # # #                 main_gemini_client = GeminiClient(text_model_name=self.settings_manager.keyword_extraction_model)
                
# # # #                 kw_prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
# # # #                 kw_prompt = kw_prompt_template.format(conversation_text=conversation_text)
# # # #                 print(" > キーワードを抽出中...")
# # # #                 keywords_response = main_gemini_client.generate_response(kw_prompt)
# # # #                 match_kw = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# # # #                 cleaned_keywords = match_kw.group(1).strip() if match_kw else keywords_response.strip()
# # # #                 cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
# # # #                 self.db_manager.update_session_keywords(self.active_session_id, cleaned_keywords)
# # # #                 print(f" > キーワードを保存しました: {cleaned_keywords}")

# # # #                 title_prompt_template = self.settings_manager.title_generation_prompt
# # # #                 title_prompt = title_prompt_template.format(conversation_text=conversation_text)
# # # #                 print(" > タイトルを生成中...")
# # # #                 title = main_gemini_client.generate_response(title_prompt)
# # # #                 cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
# # # #                 self.db_manager.update_session_title(self.active_session_id, cleaned_title)
# # # #                 print(f" > タイトルを保存しました: {cleaned_title}")

# # # #         if self.db_worker and self.db_worker.isRunning():
# # # #             print("データベースへの書き込み完了を待っています...")
# # # #             while self.db_worker.tasks:
# # # #                 print(f" > DBワーカーの残りタスク: {len(self.db_worker.tasks)}件")
# # # #                 QThread.msleep(100)
# # # #             self.db_worker.stop()
# # # #             self.db_worker.wait()
# # # #             print(" > DatabaseWorker 停止完了")
            
# # # #         print("すべての処理が安全に完了しました。アプリケーションを終了します。")
# # # #         super().closeEvent(event)






























# # # import sys
# # # import os
# # # import fitz
# # # import re
# # # from PIL import Image
# # # from PySide6.QtCore import QThread, Signal, Slot, QSize, Qt
# # # from PySide6.QtGui import QPixmap, QImage, QTextCursor, QMovie, QPainter, QColor, QPen, QFont, QAction
# # # from PySide6.QtWidgets import (
# # #     QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLabel,
# # #     QHBoxLayout, QCheckBox, QFileDialog, QStackedLayout, 
# # #     QListWidget, QListWidgetItem, QDockWidget
# # # )
# # # from typing import Optional, List, Dict

# # # from .widgets.md_view import MarkdownView
# # # from .settings_dialog import SettingsDialog
# # # from ..core.context_manager import ContextManager
# # # from ..core.gemini_client import GeminiClient
# # # from ..core.database_manager import DatabaseManager
# # # from ..core.database_worker import DatabaseWorker
# # # from ..core.visual_observer import VisualObserverWorker
# # # from ..core.settings_manager import SettingsManager
# # # from ..hardware.camera_handler import CameraWorker
# # # from ..hardware.audio_handler import TTSWorker, STTWorker

# # # # (ワーカースレッド定義は変更なし)
# # # class FileProcessingWorker(QThread):
# # #     finished_processing = Signal(str)
# # #     def __init__(self, file_path, gemini_client, parent=None):
# # #         super().__init__(parent)
# # #         self.file_path = file_path
# # #         self.gemini_client = gemini_client
# # #     def run(self):
# # #         images = []
# # #         file_path_lower = self.file_path.lower()
# # #         try:
# # #             if file_path_lower.endswith('.pdf'):
# # #                 doc = fitz.open(self.file_path)
# # #                 for page in doc:
# # #                     pix = page.get_pixmap(dpi=150)
# # #                     img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
# # #                     images.append(img)
# # #                 doc.close()
# # #             elif file_path_lower.endswith(('.png', '.jpg', '.jpeg', '.webp')):
# # #                 images.append(Image.open(self.file_path).convert("RGB"))
# # #             else:
# # #                 self.finished_processing.emit("サポートされていない形式です。")
# # #                 return
# # #             if not images:
# # #                 self.finished_processing.emit("画像を変換できませんでした。")
# # #                 return
# # #             prompt = "この画像は学習教材です。含まれるテキストや数式を正確に書き出してください。"
# # #             self.finished_processing.emit(self.gemini_client.generate_vision_response([prompt] + images))
# # #         except Exception as e:
# # #             self.finished_processing.emit(f"ファイル処理エラー: {e}")

# # # class GeminiWorker(QThread):
# # #     response_ready = Signal(str)
# # #     def __init__(self, prompt, model_name=None, parent=None):
# # #         super().__init__(parent)
# # #         self.prompt = prompt
# # #         self.gemini_client = GeminiClient(text_model_name=model_name)
# # #     def run(self):
# # #         self.response_ready.emit(self.gemini_client.generate_response(self.prompt))

# # # class GeminiVisionWorker(QThread):
# # #     response_ready = Signal(str)
# # #     def __init__(self, prompt_parts, model_name=None, parent=None):
# # #         super().__init__(parent)
# # #         self.prompt_parts = prompt_parts
# # #         self.gemini_client = GeminiClient(vision_model_name=model_name)
# # #     def run(self):
# # #         self.response_ready.emit(self.gemini_client.generate_vision_response(self.prompt_parts))


# # # class MainWindow(QMainWindow):
# # #     def __init__(self):
# # #         super().__init__()
# # #         self.setWindowTitle("勉強アシストアプリ")
# # #         self.setGeometry(100, 100, 1600, 900)
        
# # #         self.is_ai_task_running = False
# # #         self.context_manager = ContextManager()
# # #         self.settings_manager = SettingsManager()
# # #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# # #         db_path = os.path.join(project_root, "data", "sessions.db")
# # #         self.db_manager = DatabaseManager(db_path=db_path)
# # #         self.active_session_id: Optional[int] = None
# # #         self.latest_camera_frame: Optional[Image.Image] = None

# # #         self.camera_worker: Optional[CameraWorker] = None
# # #         self.stt_worker: Optional[STTWorker] = None
# # #         self.observer_worker: Optional[VisualObserverWorker] = None
# # #         self.tts_worker: Optional[TTSWorker] = None
# # #         self.db_worker: Optional[DatabaseWorker] = None
# # #         self.file_worker: Optional[FileProcessingWorker] = None
# # #         self.keyword_extraction_worker: Optional[GeminiWorker] = None
# # #         self.query_keyword_worker: Optional[GeminiWorker] = None
# # #         self.title_generation_worker: Optional[GeminiWorker] = None

# # #         self.current_chat_messages: List[Dict[str, str]] = []
# # #         self.stt_was_enabled_before_tts = False

# # #         self.setup_ui()
# # #         self.create_menu()
        
# # #         self.start_essential_workers()
# # #         self.restart_stt_worker()
        
# # #         self.load_and_display_sessions()

# # #         if self.settings_manager.camera_enabled_on_startup:
# # #             self.camera_enabled_checkbox.setChecked(True)
# # #         else:
# # #             self.camera_enabled_checkbox.setChecked(False)
# # #             self.camera_view.setText("カメラはオフです")

# # #     def setup_ui(self):
# # #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        
# # #         # 1. セッション履歴パネルの作成
# # #         session_area_widget = QWidget()
# # #         session_layout = QVBoxLayout(session_area_widget)
# # #         self.new_session_button = QPushButton("＋ 新しいチャット")
# # #         self.session_list_widget = QListWidget()
# # #         session_layout.addWidget(self.new_session_button)
# # #         session_layout.addWidget(self.session_list_widget)

# # #         # 2. メインのチャットパネルの作成
# # #         main_chat_widget = QWidget()
# # #         main_chat_widget.setMinimumSize(400, 300)
# # #         left_layout = QVBoxLayout(main_chat_widget)
# # #         self.ai_output_view = MarkdownView()
# # #         self.user_input = QTextEdit()
# # #         self.send_button = QPushButton("送信")
# # #         self.stt_enabled_checkbox = QCheckBox("音声認識")
# # #         self.load_file_button = QPushButton("問題ファイルを読み込む")
# # #         self.stop_speech_button = QPushButton("読み上げを停止")
# # #         self.stop_speech_button.setVisible(False)
# # #         loading_widget = QWidget()
# # #         loading_layout = QHBoxLayout(loading_widget)
# # #         loading_layout.setContentsMargins(0, 5, 0, 5)
# # #         self.loading_movie_label = QLabel()
# # #         loading_gif_path = os.path.join(project_root, "assets", "loading.gif")
# # #         if os.path.exists(loading_gif_path):
# # #             self.movie = QMovie(loading_gif_path)
# # #             self.loading_movie_label.setMovie(self.movie)
# # #             self.movie.setScaledSize(QSize(25, 25))
# # #         self.loading_text_label = QLabel("AIが考え中です...")
# # #         loading_layout.addStretch()
# # #         loading_layout.addWidget(self.loading_movie_label)
# # #         loading_layout.addWidget(self.loading_text_label)
# # #         loading_layout.addStretch()
# # #         self.header_stack = QStackedLayout()
# # #         self.header_stack.addWidget(QLabel("AIアシスタント"))
# # #         self.header_stack.addWidget(loading_widget)
# # #         top_button_layout = QHBoxLayout()
# # #         top_button_layout.addWidget(self.load_file_button)
# # #         top_button_layout.addStretch()
# # #         self.camera_enabled_checkbox = QCheckBox("カメラを有効にする")
# # #         top_button_layout.addWidget(self.camera_enabled_checkbox)
# # #         top_button_layout.addWidget(self.stt_enabled_checkbox)
# # #         button_v_layout = QVBoxLayout()
# # #         button_v_layout.addWidget(self.send_button)
# # #         button_v_layout.addWidget(self.stop_speech_button)
# # #         input_area_layout = QHBoxLayout()
# # #         input_area_layout.addWidget(self.user_input)
# # #         input_area_layout.addLayout(button_v_layout)
# # #         left_layout.addLayout(top_button_layout)
# # #         left_layout.addLayout(self.header_stack)
# # #         left_layout.addWidget(self.ai_output_view, stretch=1)
# # #         left_layout.addWidget(QLabel("質問や独り言を入力"))
# # #         left_layout.addLayout(input_area_layout)

# # #         # 3. カメラビューパネルの作成
# # #         right_widget = QWidget()
# # #         right_layout = QVBoxLayout(right_widget)
# # #         self.camera_view = QLabel("カメラを初期化中...")
# # #         self.camera_view.setStyleSheet("background-color: black; color: white;")
# # #         self.camera_view.setFixedSize(640, 480)
# # #         right_layout.addWidget(self.camera_view)
# # #         right_layout.addStretch()

# # #         # 4. DockWidgetを使ってレイアウトを構築
# # #         self.session_dock = QDockWidget("セッション履歴", self)
# # #         self.session_dock.setWidget(session_area_widget)
# # #         self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.session_dock)

# # #         self.camera_dock = QDockWidget("カメラビュー", self)
# # #         self.camera_dock.setWidget(right_widget)
# # #         self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.camera_dock)
        
# # #         self.chat_dock = QDockWidget("チャット", self)
# # #         self.chat_dock.setWidget(main_chat_widget)
# # #         self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.chat_dock)
        
# # #         # 5. シグナル接続
# # #         self.new_session_button.clicked.connect(self.create_new_session)
# # #         self.session_list_widget.currentItemChanged.connect(self.on_session_changed)
# # #         self.send_button.clicked.connect(self.start_user_request)
# # #         self.load_file_button.clicked.connect(self.open_file_dialog)
# # #         self.stop_speech_button.clicked.connect(self.on_stop_speech_button_clicked)
# # #         self.camera_enabled_checkbox.toggled.connect(self.on_camera_enabled_changed)
# # #         self.stt_enabled_checkbox.toggled.connect(self.on_stt_enabled_changed)

# # #     def create_menu(self):
# # #         menu_bar = self.menuBar()
# # #         file_menu = menu_bar.addMenu("ファイル")
# # #         settings_action = QAction("設定...", self)
# # #         settings_action.triggered.connect(self.open_settings_dialog)
# # #         file_menu.addAction(settings_action)

# # #         view_menu = self.menuBar().addMenu("表示")
# # #         view_menu.addAction(self.session_dock.toggleViewAction())
# # #         view_menu.addAction(self.chat_dock.toggleViewAction())
# # #         view_menu.addAction(self.camera_dock.toggleViewAction())

# # #     # ...(以降のメソッドはすべて変更なしです)...
# # #     def start_essential_workers(self):
# # #         self.db_worker = DatabaseWorker(self.db_manager)
# # #         self.tts_worker = TTSWorker()
# # #         self.db_worker.start()
# # #         self.tts_worker.start()
# # #         self.tts_worker.speech_finished.connect(self.on_speech_finished)
    
# # #     def start_camera_dependent_workers(self):
# # #         self.stop_camera_dependent_workers() 
# # #         print("カメラ関連ワーカーを起動します...")
# # #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# # #         model_path = os.path.join(project_root, "models", "best12-2.pt")
# # #         self.camera_worker = CameraWorker(
# # #             model_path=model_path,
# # #             device_index=self.settings_manager.camera_device_index,
# # #             stop_threshold_sec=self.settings_manager.hand_stop_threshold
# # #         )
# # #         self.observer_worker = VisualObserverWorker(
# # #             interval_sec=self.settings_manager.observation_interval
# # #         )
# # #         self.camera_worker.frame_data_ready.connect(self.update_camera_view)
# # #         self.camera_worker.hand_stopped_signal.connect(self.on_hand_stopped)
# # #         self.camera_worker.raw_frame_for_observation.connect(self.observer_worker.update_frame)
# # #         self.observer_worker.observation_ready.connect(self.on_observation_received)
# # #         self.camera_worker.start()
# # #         self.observer_worker.start()

# # #     def stop_camera_dependent_workers(self):
# # #         if self.camera_worker and self.camera_worker.isRunning():
# # #             print("CameraWorkerを停止します...")
# # #             self.camera_worker.frame_data_ready.disconnect(self.update_camera_view)
# # #             self.camera_worker.hand_stopped_signal.disconnect(self.on_hand_stopped)
# # #             self.camera_worker.raw_frame_for_observation.disconnect(self.observer_worker.update_frame)
# # #             self.camera_worker.stop()
# # #             self.camera_worker.wait()
# # #             self.camera_worker = None
# # #             print(" > CameraWorker 停止完了")
# # #         if self.observer_worker and self.observer_worker.isRunning():
# # #             print("VisualObserverWorkerを停止します...")
# # #             self.observer_worker.stop()
# # #             self.observer_worker.wait()
# # #             self.observer_worker = None
# # #             print(" > VisualObserverWorker 停止完了")

# # #     def restart_stt_worker(self):
# # #         print("STTワーカーを再起動します...")
# # #         if self.stt_worker and self.stt_worker.isRunning():
# # #             self.stt_worker.monologue_recognized.disconnect(self.on_monologue_recognized)
# # #             self.stt_worker.command_recognized.disconnect(self.on_command_recognized)
# # #             self.stt_worker.stop()
# # #             self.stt_worker.wait()
# # #         self.stt_worker = STTWorker(device_index=self.settings_manager.mic_device_index)
# # #         self.stt_worker.monologue_recognized.connect(self.on_monologue_recognized)
# # #         self.stt_worker.command_recognized.connect(self.on_command_recognized)
# # #         self.stt_worker.set_enabled(self.stt_enabled_checkbox.isChecked())
# # #         self.stt_worker.start()
# # #         print(" > STTWorker 再起動完了")
        
# # #     def open_settings_dialog(self):
# # #         dialog = SettingsDialog(self)
# # #         if dialog.exec():
# # #             print("設定が変更されました。動的設定を適用し、必要なワーカーを再起動します。")
# # #             self.apply_settings_dynamically()
# # #             self.restart_stt_worker()
# # #             if self.camera_enabled_checkbox.isChecked():
# # #                 self.start_camera_dependent_workers()
# # #             print("ワーカーの再起動・設定反映が完了しました。")
# # #         else:
# # #             print("設定はキャンセルされました。")
            
# # #     def apply_settings_dynamically(self):
# # #         if self.tts_worker and self.tts_worker.isRunning():
# # #             self.tts_worker.set_tts_enabled(self.settings_manager.tts_enabled)
# # #             self.tts_worker.set_tts_rate(self.settings_manager.tts_rate)
# # #         if self.camera_worker and self.camera_worker.isRunning():
# # #             self.camera_worker.set_stop_threshold(self.settings_manager.hand_stop_threshold)
# # #         if self.observer_worker and self.observer_worker.isRunning():
# # #             self.observer_worker.set_observation_interval(self.settings_manager.observation_interval)

# # #     @Slot(bool)
# # #     def on_camera_enabled_changed(self, enabled: bool):
# # #         if enabled:
# # #             self.start_camera_dependent_workers()
# # #         else:
# # #             self.stop_camera_dependent_workers()
# # #             self.camera_view.setText("カメラはオフです")
# # #             self.latest_camera_frame = None

# # #     @Slot(bool)
# # #     def on_stt_enabled_changed(self, enabled: bool):
# # #         if self.stt_worker:
# # #             self.stt_worker.set_enabled(enabled)

# # #     def _get_long_term_context(self, relevant_sessions: List[Dict]) -> str:
# # #         if not relevant_sessions:
# # #             last_session_id = self.db_manager.get_last_active_session_id(exclude_session_id=self.active_session_id)
# # #             if not last_session_id: return "これが最初のセッションです。"
# # #             last_session_details = self.db_manager.get_session_details(last_session_id)
# # #             if not last_session_details: return "前回のセッション情報を取得できませんでした。"
# # #             last_messages = self.db_manager.get_messages_for_session(last_session_id)
# # #             last_user_message = next((msg['content'] for msg in reversed(last_messages) if msg['role'] == 'user'), "なし")
# # #             return f"（直近のセッションより）\n- 前回（{last_session_details['last_updated_at']}）のセッションでは、「{last_session_details['title']}」について学習しており、最後の質問は「{last_user_message}」でした。"
        
# # #         context_lines = ["（過去の関連セッションより）"]
# # #         for session in relevant_sessions:
# # #             line = f"- セッション「{session['title']}」（{session['last_updated_at']}）では、キーワード「{session['keywords']}」について議論しました。"
# # #             context_lines.append(line)
# # #         return "\n".join(context_lines)

# # #     def _add_message_to_ui_and_db(self, role: str, content: str):
# # #         if not self.active_session_id: return
# # #         self.current_chat_messages.append({"role": role, "content": content})
# # #         self.update_chat_display()
# # #         self.db_worker.add_message(self.active_session_id, role, content)

# # #     def _trigger_keyword_extraction(self, session_id: int):
# # #         if not session_id: return
# # #         if self.keyword_extraction_worker and self.keyword_extraction_worker.isRunning(): return
# # #         messages = self.db_manager.get_messages_for_session(session_id)
# # #         if len(messages) < 4: return
# # #         conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
# # #         prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
# # #         prompt = prompt_template.format(conversation_text=conversation_text)
        
# # #         model_name = self.settings_manager.keyword_extraction_model
# # #         self.keyword_extraction_worker = GeminiWorker(prompt, model_name=model_name)
# # #         self.keyword_extraction_worker.response_ready.connect(lambda keywords: self.on_keywords_extracted(session_id, keywords))
# # #         self.keyword_extraction_worker.finished.connect(self.on_keyword_worker_finished)
# # #         self.keyword_extraction_worker.start()

# # #     def _trigger_title_generation(self, session_id: int):
# # #         if not session_id: return
# # #         if self.title_generation_worker and self.title_generation_worker.isRunning(): return
# # #         messages = self.db_manager.get_messages_for_session(session_id)
# # #         if len(messages) < 4: return
# # #         conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
# # #         prompt_template = self.settings_manager.title_generation_prompt
# # #         prompt = prompt_template.format(conversation_text=conversation_text)
        
# # #         model_name = self.settings_manager.keyword_extraction_model
# # #         self.title_generation_worker = GeminiWorker(prompt, model_name=model_name)
# # #         self.title_generation_worker.response_ready.connect(lambda title: self.on_title_generated(session_id, title))
# # #         self.title_generation_worker.finished.connect(self.on_title_generation_finished)
# # #         self.title_generation_worker.start()

# # #     @Slot(int, str)
# # #     def on_title_generated(self, session_id: int, title: str):
# # #         cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
# # #         self.db_worker.update_session_title(session_id, cleaned_title)
# # #         for i in range(self.session_list_widget.count()):
# # #             item = self.session_list_widget.item(i)
# # #             if item.data(Qt.UserRole) == session_id:
# # #                 item.setText(cleaned_title)
# # #                 break
    
# # #     @Slot()
# # #     def on_title_generation_finished(self):
# # #         if self.title_generation_worker:
# # #             self.title_generation_worker.deleteLater()
# # #             self.title_generation_worker = None

# # #     @Slot(int, str)
# # #     def on_keywords_extracted(self, session_id: int, keywords_response: str):
# # #         match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# # #         cleaned_keywords = match.group(1).strip() if match else keywords_response.strip()
# # #         cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
# # #         self.db_worker.update_session_keywords(session_id, cleaned_keywords)
        
# # #     @Slot()
# # #     def on_keyword_worker_finished(self):
# # #         if self.keyword_extraction_worker:
# # #             self.keyword_extraction_worker.deleteLater()
# # #             self.keyword_extraction_worker = None

# # #     def update_chat_display(self):
# # #         md_text = ""
# # #         for msg in self.current_chat_messages:
# # #             role_display = "あなた" if msg["role"] == "user" else "AIアシスタント"
# # #             md_text += f"**{role_display}:**\n\n{msg['content']}\n\n<hr>\n\n"
# # #         self.ai_output_view.set_markdown(md_text)

# # #     def load_and_display_sessions(self):
# # #         self.session_list_widget.blockSignals(True)
# # #         self.session_list_widget.clear()
# # #         sessions = self.db_manager.get_all_sessions()
# # #         if not sessions:
# # #             self.create_new_session(is_initial=True)
# # #             sessions = self.db_manager.get_all_sessions()
# # #         for session_id, title in sessions:
# # #             item = QListWidgetItem(title)
# # #             item.setData(Qt.UserRole, session_id)
# # #             self.session_list_widget.addItem(item)
# # #         self.session_list_widget.setCurrentRow(0)
# # #         self.session_list_widget.blockSignals(False)
# # #         if self.session_list_widget.currentItem():
# # #             self.on_session_changed(self.session_list_widget.currentItem(), None)

# # #     def create_new_session(self, is_initial=False):
# # #         self.db_manager.create_new_session()
# # #         if not is_initial:
# # #             self.load_and_display_sessions()

# # #     @Slot(QListWidgetItem, QListWidgetItem)
# # #     def on_session_changed(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
# # #         if previous_item:
# # #             previous_session_id = previous_item.data(Qt.UserRole)
# # #             self._trigger_keyword_extraction(previous_session_id)
# # #             self._trigger_title_generation(previous_session_id)
# # #         if not current_item: return
# # #         session_id = current_item.data(Qt.UserRole)
# # #         if session_id == self.active_session_id: return
# # #         self.active_session_id = session_id
# # #         session_details = self.db_manager.get_session_details(session_id)
# # #         if session_details:
# # #             self.context_manager.set_problem_context(session_details.get("problem_context"))
# # #         self.current_chat_messages = self.db_manager.get_messages_for_session(self.active_session_id)
# # #         self.update_chat_display()

# # #     @Slot()
# # #     def on_stop_speech_button_clicked(self):
# # #         self.tts_worker.stop_current_speech()

# # #     def execute_ai_task(self, prompt, speak=True, is_user_request=False, use_vision=False, is_continuation=False):
# # #         if self.is_ai_task_running and not is_continuation:
# # #             return
# # #         if not is_continuation:
# # #             self.is_ai_task_running = True
# # #             self.header_stack.setCurrentIndex(1)
# # #             if hasattr(self, 'movie'): self.movie.start()
            
# # #         if is_user_request:
# # #             self.send_button.setEnabled(False)
# # #         if speak:
# # #             self.stop_speech_button.setVisible(True)
            
# # #         if use_vision:
# # #             model_name = self.settings_manager.vision_model
# # #             self.ai_worker = GeminiVisionWorker(prompt, model_name=model_name)
# # #         else:
# # #             model_name = self.settings_manager.main_response_model
# # #             self.ai_worker = GeminiWorker(prompt, model_name=model_name)
            
# # #         self.ai_worker.response_ready.connect(lambda r: self.handle_gemini_response(r, speak))
# # #         self.ai_worker.finished.connect(self.on_ai_worker_finished)
# # #         self.ai_worker.start()

# # #     def handle_gemini_response(self, response_text, speak):
# # #         if hasattr(self, 'movie'): self.movie.stop()
# # #         self.header_stack.setCurrentIndex(0)
        
# # #         self._add_message_to_ui_and_db("ai", response_text)
        
# # #         if speak:
# # #             print("読み上げ開始。音声認識を一時停止します。")
# # #             self.stt_was_enabled_before_tts = self.stt_enabled_checkbox.isChecked()
# # #             if self.stt_was_enabled_before_tts:
# # #                 self.stt_enabled_checkbox.setChecked(False)
# # #             self.tts_worker.speak(response_text)
# # #         else:
# # #             self.is_ai_task_running = False
# # #             self.stop_speech_button.setVisible(False)
# # #             if not self.send_button.isEnabled():
# # #                 self.send_button.setEnabled(True)

# # #     @Slot()
# # #     def on_speech_finished(self):
# # #         self.is_ai_task_running = False
# # #         self.stop_speech_button.setVisible(False)
        
# # #         print("読み上げ完了。音声認識の状態を復元します。")
# # #         if self.stt_was_enabled_before_tts:
# # #             self.stt_enabled_checkbox.setChecked(True)
        
# # #         if not self.send_button.isEnabled():
# # #             self.send_button.setEnabled(True)

# # #     @Slot()
# # #     def on_ai_worker_finished(self):
# # #         if self.ai_worker:
# # #             self.ai_worker.deleteLater()
# # #             self.ai_worker = None

# # #     def start_user_request(self):
# # #         user_query = self.user_input.toPlainText().strip()
# # #         if not (user_query and self.active_session_id): return
        
# # #         self._add_message_to_ui_and_db("user", user_query)
# # #         self.user_input.clear()
        
# # #         self.is_ai_task_running = True
# # #         self.header_stack.setCurrentIndex(1)
# # #         if hasattr(self, 'movie'): self.movie.start()
# # #         self.send_button.setEnabled(False)
        
# # #         prompt = f"""以下の質問文から、中心となるキーワードを3つ、カンマ区切りで抽出してください。思考プロセスは不要です。キーワードのみを出力してください。\n例: 積分、グラフ、面積\n\n---\n{user_query}"""
        
# # #         model_name = self.settings_manager.keyword_extraction_model
# # #         self.query_keyword_worker = GeminiWorker(prompt, model_name=model_name)
# # #         self.query_keyword_worker.response_ready.connect(lambda keywords: self.on_query_keywords_extracted(user_query, keywords))
# # #         self.query_keyword_worker.finished.connect(self.on_query_keyword_worker_finished)
# # #         self.query_keyword_worker.start()

# # #     @Slot(str, str)
# # #     def on_query_keywords_extracted(self, original_query: str, keywords_response: str):
# # #         match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# # #         cleaned_keywords_str = match.group(1).strip() if match else keywords_response.strip()
# # #         cleaned_keywords = [kw.strip() for kw in cleaned_keywords_str.split(',') if kw.strip()]
        
# # #         if not self.active_session_id: return
        
# # #         relevant_sessions = self.db_manager.find_relevant_sessions(cleaned_keywords, exclude_session_id=self.active_session_id)
# # #         long_term_context = self._get_long_term_context(relevant_sessions)
# # #         monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
# # #         observation_log = self.db_manager.get_recent_logs_for_session(self.active_session_id, "observation", 5)
        
# # #         full_prompt = self.context_manager.build_prompt_for_query(original_query, self.current_chat_messages, monologue_history, observation_log, long_term_context)
# # #         self.execute_ai_task(full_prompt, speak=True, is_user_request=True, is_continuation=True)

# # #     @Slot()
# # #     def on_query_keyword_worker_finished(self):
# # #         if self.query_keyword_worker:
# # #             self.query_keyword_worker.deleteLater()
# # #             self.query_keyword_worker = None

# # #     def open_file_dialog(self): 
# # #         if not self.active_session_id: self.create_new_session(); return
# # #         file_path, _ = QFileDialog.getOpenFileName(self, "問題ファイルを選択", "", "サポートファイル (*.pdf *.png *.jpg *.jpeg *.webp);;全ファイル (*)")
# # #         if file_path:
# # #             self._add_message_to_ui_and_db("ai", f"`{os.path.basename(file_path)}`を分析中...")
            
# # #             model_name = self.settings_manager.vision_model
# # #             gemini_client_for_file = GeminiClient(vision_model_name=model_name)
# # #             self.file_worker = FileProcessingWorker(file_path, gemini_client_for_file)
# # #             self.file_worker.finished_processing.connect(self.on_file_processed)
# # #             self.file_worker.finished.connect(self.on_file_worker_finished)
# # #             self.file_worker.start()

# # #     @Slot(str)
# # #     def on_file_processed(self, result_text):
# # #         if not self.active_session_id: return
# # #         self.db_worker.update_problem_context(self.active_session_id, result_text)
# # #         self.context_manager.set_problem_context(result_text)
# # #         message = f"ファイルの分析が完了しました。\n\n**【分析結果】**\n\n{result_text}\n\n---\nこの問題について質問してください。"
# # #         self._add_message_to_ui_and_db("ai", message)
# # #         self.tts_worker.speak("ファイルの分析が完了しました。")

# # #     @Slot()
# # #     def on_file_worker_finished(self):
# # #         if self.file_worker:
# # #             self.file_worker.deleteLater()
# # #             self.file_worker = None
            
# # #     @Slot(Image.Image)
# # #     def on_hand_stopped(self, captured_image):
# # #         if self.is_ai_task_running: return
# # #         self.context_manager.set_triggered_image(captured_image)
# # #         prompt = self.settings_manager.hand_stopped_prompt
# # #         self.execute_ai_task(prompt, speak=True)

# # #     @Slot(str)
# # #     def on_monologue_recognized(self, text):
# # #         if self.active_session_id:
# # #             self.db_worker.add_log(self.active_session_id, "monologue", text)
# # #         current_text = self.user_input.toPlainText()
# # #         new_text = (current_text + " " + text) if current_text and not current_text.endswith(" ") else (current_text + text)
# # #         self.user_input.setPlainText(new_text)
# # #         self.user_input.moveCursor(QTextCursor.MoveOperation.End)

# # #     @Slot(str)
# # #     def on_command_recognized(self, command_text):
# # #         if not self.active_session_id:
# # #             self.tts_worker.speak("すみません、現在アクティブなセッションがありません。")
# # #             return
            
# # #         if not self.latest_camera_frame:
# # #             self.tts_worker.speak("すみません、カメラの映像が取得できていません。")
# # #             return
        
# # #         self._add_message_to_ui_and_db("user", f"（音声コマンド）{command_text}")
# # #         self.context_manager.set_triggered_image(self.latest_camera_frame.copy())

# # #         self.is_ai_task_running = True
# # #         self.header_stack.setCurrentIndex(1)
# # #         if hasattr(self, 'movie'):
# # #             self.movie.start()
# # #         self.send_button.setEnabled(False)

# # #         long_term_context = self._get_long_term_context([])
# # #         monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
        
# # #         prompt_parts = self.context_manager.build_prompt_parts_for_command(
# # #             command_text, 
# # #             self.current_chat_messages, 
# # #             monologue_history, 
# # #             long_term_context
# # #         )
        
# # #         if prompt_parts:
# # #             self.execute_ai_task(prompt_parts, speak=True, is_user_request=False, use_vision=True, is_continuation=True)
# # #         else:
# # #             self.tts_worker.speak("コマンドの準備に失敗しました。")
# # #             self.is_ai_task_running = False
# # #             self.header_stack.setCurrentIndex(0)
# # #             self.send_button.setEnabled(True)

# # #     @Slot(str)
# # #     def on_observation_received(self, observation_text: str):
# # #         if self.active_session_id:
# # #             self.db_worker.add_log(self.active_session_id, "observation", observation_text)

# # #     @Slot(QImage, list)
# # #     def update_camera_view(self, frame_qimage: QImage, detections: List[Dict]):
# # #         if frame_qimage.isNull():
# # #             return
        
# # #         pixmap = QPixmap.fromImage(frame_qimage)
# # #         painter = QPainter(pixmap)
# # #         for detection in detections:
# # #             box = detection["box"]
# # #             label = f'{detection["label"]} {detection["confidence"]:.2f}'
# # #             pen = QPen(QColor(0, 255, 0), 2)
# # #             painter.setPen(pen)
# # #             painter.drawRect(box[0], box[1], box[2] - box[0], box[3] - box[1])
# # #             font = QFont()
# # #             font.setPointSize(10)
# # #             painter.setFont(font)
# # #             painter.setPen(QColor(255, 255, 255))
# # #             text_x, text_y = box[0], box[1] - 5
# # #             painter.fillRect(text_x, text_y - 12, len(label) * 8, 16, QColor(0, 255, 0))
# # #             painter.drawText(text_x, text_y, label)
# # #         painter.end()
# # #         self.camera_view.setPixmap(pixmap)
        
# # #         buffer = frame_qimage.constBits().tobytes()
# # #         self.latest_camera_frame = Image.frombytes("RGBA", (frame_qimage.width(), frame_qimage.height()), buffer, 'raw', "BGRA")

# # #     def closeEvent(self, event):
# # #         print("アプリケーションの終了処理を開始します...")

# # #         print("UI関連以外のワーカースレッドを停止します...")
# # #         self.stop_camera_dependent_workers()
        
# # #         if self.stt_worker and self.stt_worker.isRunning():
# # #             self.stt_worker.stop()
# # #             self.stt_worker.wait()
# # #             print(" > STTWorker 停止完了")
        
# # #         if self.tts_worker and self.tts_worker.isRunning():
# # #             self.tts_worker.stop()
# # #             self.tts_worker.wait()
# # #             print(" > TTSWorker 停止完了")
            
# # #         if self.active_session_id:
# # #             print(f"セッションID {self.active_session_id} の最終処理を実行します...")
            
# # #             messages = self.db_manager.get_messages_for_session(self.active_session_id)
# # #             if len(messages) >= 4:
# # #                 conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                
# # #                 main_gemini_client = GeminiClient(text_model_name=self.settings_manager.keyword_extraction_model)
                
# # #                 kw_prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
# # #                 kw_prompt = kw_prompt_template.format(conversation_text=conversation_text)
# # #                 print(" > キーワードを抽出中...")
# # #                 keywords_response = main_gemini_client.generate_response(kw_prompt)
# # #                 match_kw = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# # #                 cleaned_keywords = match_kw.group(1).strip() if match_kw else keywords_response.strip()
# # #                 cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
# # #                 self.db_manager.update_session_keywords(self.active_session_id, cleaned_keywords)
# # #                 print(f" > キーワードを保存しました: {cleaned_keywords}")

# # #                 title_prompt_template = self.settings_manager.title_generation_prompt
# # #                 title_prompt = title_prompt_template.format(conversation_text=conversation_text)
# # #                 print(" > タイトルを生成中...")
# # #                 title = main_gemini_client.generate_response(title_prompt)
# # #                 cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
# # #                 self.db_manager.update_session_title(self.active_session_id, cleaned_title)
# # #                 print(f" > タイトルを保存しました: {cleaned_title}")

# # #         if self.db_worker and self.db_worker.isRunning():
# # #             print("データベースへの書き込み完了を待っています...")
# # #             while self.db_worker.tasks:
# # #                 print(f" > DBワーカーの残りタスク: {len(self.db_worker.tasks)}件")
# # #                 QThread.msleep(100)
# # #             self.db_worker.stop()
# # #             self.db_worker.wait()
# # #             print(" > DatabaseWorker 停止完了")
            
# # #         print("すべての処理が安全に完了しました。アプリケーションを終了します。")
# # #         super().closeEvent(event)
















# # import sys
# # import os
# # import fitz
# # import re
# # from PIL import Image
# # from PySide6.QtCore import QThread, Signal, Slot, QSize, Qt
# # from PySide6.QtGui import QPixmap, QImage, QTextCursor, QMovie, QPainter, QColor, QPen, QFont, QAction
# # from PySide6.QtWidgets import (
# #     QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLabel,
# #     QHBoxLayout, QCheckBox, QFileDialog, QStackedLayout, 
# #     QListWidget, QListWidgetItem, QDockWidget
# # )
# # from typing import Optional, List, Dict

# # from .widgets.md_view import MarkdownView
# # from .settings_dialog import SettingsDialog
# # from ..core.context_manager import ContextManager
# # from ..core.gemini_client import GeminiClient
# # from ..core.database_manager import DatabaseManager
# # from ..core.database_worker import DatabaseWorker
# # from ..core.visual_observer import VisualObserverWorker
# # from ..core.settings_manager import SettingsManager
# # from ..hardware.camera_handler import CameraWorker
# # from ..hardware.audio_handler import TTSWorker, STTWorker

# # # (ワーカースレッド定義は変更なし)
# # class FileProcessingWorker(QThread):
# #     finished_processing = Signal(str)
# #     def __init__(self, file_path, gemini_client, parent=None):
# #         super().__init__(parent)
# #         self.file_path = file_path
# #         self.gemini_client = gemini_client
# #     def run(self):
# #         images = []
# #         file_path_lower = self.file_path.lower()
# #         try:
# #             if file_path_lower.endswith('.pdf'):
# #                 doc = fitz.open(self.file_path)
# #                 for page in doc:
# #                     pix = page.get_pixmap(dpi=150)
# #                     img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
# #                     images.append(img)
# #                 doc.close()
# #             elif file_path_lower.endswith(('.png', '.jpg', '.jpeg', '.webp')):
# #                 images.append(Image.open(self.file_path).convert("RGB"))
# #             else:
# #                 self.finished_processing.emit("サポートされていない形式です。")
# #                 return
# #             if not images:
# #                 self.finished_processing.emit("画像を変換できませんでした。")
# #                 return
# #             prompt = "この画像は学習教材です。含まれるテキストや数式を正確に書き出してください。"
# #             self.finished_processing.emit(self.gemini_client.generate_vision_response([prompt] + images))
# #         except Exception as e:
# #             self.finished_processing.emit(f"ファイル処理エラー: {e}")

# # class GeminiWorker(QThread):
# #     response_ready = Signal(str)
# #     def __init__(self, prompt, model_name=None, parent=None):
# #         super().__init__(parent)
# #         self.prompt = prompt
# #         self.gemini_client = GeminiClient(text_model_name=model_name)
# #     def run(self):
# #         self.response_ready.emit(self.gemini_client.generate_response(self.prompt))

# # class GeminiVisionWorker(QThread):
# #     response_ready = Signal(str)
# #     def __init__(self, prompt_parts, model_name=None, parent=None):
# #         super().__init__(parent)
# #         self.prompt_parts = prompt_parts
# #         self.gemini_client = GeminiClient(vision_model_name=model_name)
# #     def run(self):
# #         self.response_ready.emit(self.gemini_client.generate_vision_response(self.prompt_parts))


# # class MainWindow(QMainWindow):
# #     def __init__(self):
# #         super().__init__()
# #         self.setWindowTitle("勉強アシストアプリ")
# #         self.setGeometry(100, 100, 1600, 900)
        
# #         self.is_ai_task_running = False
# #         self.context_manager = ContextManager()
# #         self.settings_manager = SettingsManager()
# #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# #         db_path = os.path.join(project_root, "data", "sessions.db")
# #         self.db_manager = DatabaseManager(db_path=db_path)
# #         self.active_session_id: Optional[int] = None
# #         self.latest_camera_frame: Optional[Image.Image] = None

# #         self.camera_worker: Optional[CameraWorker] = None
# #         self.stt_worker: Optional[STTWorker] = None
# #         self.observer_worker: Optional[VisualObserverWorker] = None
# #         self.tts_worker: Optional[TTSWorker] = None
# #         self.db_worker: Optional[DatabaseWorker] = None
# #         self.file_worker: Optional[FileProcessingWorker] = None
# #         self.keyword_extraction_worker: Optional[GeminiWorker] = None
# #         self.query_keyword_worker: Optional[GeminiWorker] = None
# #         self.title_generation_worker: Optional[GeminiWorker] = None

# #         self.current_chat_messages: List[Dict[str, str]] = []
# #         self.stt_was_enabled_before_tts = False

# #         self.setup_ui()
# #         self.create_menu()
        
# #         self.start_essential_workers()
# #         self.restart_stt_worker()
        
# #         self.load_and_display_sessions()

# #         if self.settings_manager.camera_enabled_on_startup:
# #             self.camera_enabled_checkbox.setChecked(True)
# #         else:
# #             self.camera_enabled_checkbox.setChecked(False)
# #             self.camera_view.setText("カメラはオフです")

# #     def setup_ui(self):
# #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        
# #         # 1. セッション履歴パネルの作成
# #         session_area_widget = QWidget()
# #         session_layout = QVBoxLayout(session_area_widget)
# #         self.new_session_button = QPushButton("＋ 新しいチャット")
# #         self.session_list_widget = QListWidget()
# #         session_layout.addWidget(self.new_session_button)
# #         session_layout.addWidget(self.session_list_widget)

# #         # 2. メインのチャットパネルの作成
# #         main_chat_widget = QWidget()
# #         main_chat_widget.setMinimumSize(400, 300)
# #         left_layout = QVBoxLayout(main_chat_widget)
# #         self.ai_output_view = MarkdownView()
# #         self.user_input = QTextEdit()
# #         self.send_button = QPushButton("送信")
# #         self.stt_enabled_checkbox = QCheckBox("音声認識")
# #         self.load_file_button = QPushButton("問題ファイルを読み込む")
# #         self.stop_speech_button = QPushButton("読み上げを停止")
# #         self.stop_speech_button.setVisible(False)
# #         loading_widget = QWidget()
# #         loading_layout = QHBoxLayout(loading_widget)
# #         loading_layout.setContentsMargins(0, 5, 0, 5)
# #         self.loading_movie_label = QLabel()
# #         loading_gif_path = os.path.join(project_root, "assets", "loading.gif")
# #         if os.path.exists(loading_gif_path):
# #             self.movie = QMovie(loading_gif_path)
# #             self.loading_movie_label.setMovie(self.movie)
# #             self.movie.setScaledSize(QSize(25, 25))
# #         self.loading_text_label = QLabel("AIが考え中です...")
# #         loading_layout.addStretch()
# #         loading_layout.addWidget(self.loading_movie_label)
# #         loading_layout.addWidget(self.loading_text_label)
# #         loading_layout.addStretch()
# #         self.header_stack = QStackedLayout()
# #         self.header_stack.addWidget(QLabel("AIアシスタント"))
# #         self.header_stack.addWidget(loading_widget)
# #         top_button_layout = QHBoxLayout()
# #         top_button_layout.addWidget(self.load_file_button)
# #         top_button_layout.addStretch()
# #         self.camera_enabled_checkbox = QCheckBox("カメラを有効にする")
# #         top_button_layout.addWidget(self.camera_enabled_checkbox)
# #         top_button_layout.addWidget(self.stt_enabled_checkbox)
# #         button_v_layout = QVBoxLayout()
# #         button_v_layout.addWidget(self.send_button)
# #         button_v_layout.addWidget(self.stop_speech_button)
# #         input_area_layout = QHBoxLayout()
# #         input_area_layout.addWidget(self.user_input)
# #         input_area_layout.addLayout(button_v_layout)
# #         left_layout.addLayout(top_button_layout)
# #         left_layout.addLayout(self.header_stack)
# #         left_layout.addWidget(self.ai_output_view, stretch=1)
# #         left_layout.addWidget(QLabel("質問や独り言を入力"))
# #         left_layout.addLayout(input_area_layout)

# #         # 3. カメラビューパネルの作成
# #         right_widget = QWidget()
# #         right_layout = QVBoxLayout(right_widget)
# #         self.camera_view = QLabel("カメラを初期化中...")
# #         self.camera_view.setStyleSheet("background-color: black; color: white;")
# #         self.camera_view.setFixedSize(640, 480)
# #         right_layout.addWidget(self.camera_view)
# #         right_layout.addStretch()

# #         # 4. DockWidgetを使ってレイアウトを構築
# #         self.setDockNestingEnabled(True)

# #         self.session_dock = QDockWidget("セッション履歴", self)
# #         self.session_dock.setWidget(session_area_widget)
# #         self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.session_dock)

# #         self.chat_dock = QDockWidget("チャット", self)
# #         self.chat_dock.setWidget(main_chat_widget)
# #         self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.chat_dock)

# #         self.camera_dock = QDockWidget("カメラビュー", self)
# #         self.camera_dock.setWidget(right_widget)
# #         self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.camera_dock)
        
# #         self.tabifyDockWidget(self.session_dock, self.chat_dock)
        
# #         # 5. シグナル接続
# #         self.new_session_button.clicked.connect(self.create_new_session)
# #         self.session_list_widget.currentItemChanged.connect(self.on_session_changed)
# #         self.send_button.clicked.connect(self.start_user_request)
# #         self.load_file_button.clicked.connect(self.open_file_dialog)
# #         self.stop_speech_button.clicked.connect(self.on_stop_speech_button_clicked)
# #         self.camera_enabled_checkbox.toggled.connect(self.on_camera_enabled_changed)
# #         self.stt_enabled_checkbox.toggled.connect(self.on_stt_enabled_changed)

# #     def create_menu(self):
# #         menu_bar = self.menuBar()
# #         file_menu = menu_bar.addMenu("ファイル")
# #         settings_action = QAction("設定...", self)
# #         settings_action.triggered.connect(self.open_settings_dialog)
# #         file_menu.addAction(settings_action)

# #         view_menu = self.menuBar().addMenu("表示")
# #         view_menu.addAction(self.session_dock.toggleViewAction())
# #         view_menu.addAction(self.chat_dock.toggleViewAction())
# #         view_menu.addAction(self.camera_dock.toggleViewAction())
        
# #     # ...(以降の全メソッドは変更ありません)...
# #     def start_essential_workers(self):
# #         self.db_worker = DatabaseWorker(self.db_manager)
# #         self.tts_worker = TTSWorker()
# #         self.db_worker.start()
# #         self.tts_worker.start()
# #         self.tts_worker.speech_finished.connect(self.on_speech_finished)
    
# #     def start_camera_dependent_workers(self):
# #         self.stop_camera_dependent_workers() 
# #         print("カメラ関連ワーカーを起動します...")
# #         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# #         model_path = os.path.join(project_root, "models", "best12-2.pt")
# #         self.camera_worker = CameraWorker(
# #             model_path=model_path,
# #             device_index=self.settings_manager.camera_device_index,
# #             stop_threshold_sec=self.settings_manager.hand_stop_threshold
# #         )
# #         self.observer_worker = VisualObserverWorker(
# #             interval_sec=self.settings_manager.observation_interval
# #         )
# #         self.camera_worker.frame_data_ready.connect(self.update_camera_view)
# #         self.camera_worker.hand_stopped_signal.connect(self.on_hand_stopped)
# #         self.camera_worker.raw_frame_for_observation.connect(self.observer_worker.update_frame)
# #         self.observer_worker.observation_ready.connect(self.on_observation_received)
# #         self.camera_worker.start()
# #         self.observer_worker.start()

# #     def stop_camera_dependent_workers(self):
# #         if self.camera_worker and self.camera_worker.isRunning():
# #             print("CameraWorkerを停止します...")
# #             self.camera_worker.frame_data_ready.disconnect(self.update_camera_view)
# #             self.camera_worker.hand_stopped_signal.disconnect(self.on_hand_stopped)
# #             self.camera_worker.raw_frame_for_observation.disconnect(self.observer_worker.update_frame)
# #             self.camera_worker.stop()
# #             self.camera_worker.wait()
# #             self.camera_worker = None
# #             print(" > CameraWorker 停止完了")
# #         if self.observer_worker and self.observer_worker.isRunning():
# #             print("VisualObserverWorkerを停止します...")
# #             self.observer_worker.stop()
# #             self.observer_worker.wait()
# #             self.observer_worker = None
# #             print(" > VisualObserverWorker 停止完了")

# #     def restart_stt_worker(self):
# #         print("STTワーカーを再起動します...")
# #         if self.stt_worker and self.stt_worker.isRunning():
# #             self.stt_worker.monologue_recognized.disconnect(self.on_monologue_recognized)
# #             self.stt_worker.command_recognized.disconnect(self.on_command_recognized)
# #             self.stt_worker.stop()
# #             self.stt_worker.wait()
# #         self.stt_worker = STTWorker(device_index=self.settings_manager.mic_device_index)
# #         self.stt_worker.monologue_recognized.connect(self.on_monologue_recognized)
# #         self.stt_worker.command_recognized.connect(self.on_command_recognized)
# #         self.stt_worker.set_enabled(self.stt_enabled_checkbox.isChecked())
# #         self.stt_worker.start()
# #         print(" > STTWorker 再起動完了")
        
# #     def open_settings_dialog(self):
# #         dialog = SettingsDialog(self)
# #         if dialog.exec():
# #             print("設定が変更されました。動的設定を適用し、必要なワーカーを再起動します。")
# #             self.apply_settings_dynamically()
# #             self.restart_stt_worker()
# #             if self.camera_enabled_checkbox.isChecked():
# #                 self.start_camera_dependent_workers()
# #             print("ワーカーの再起動・設定反映が完了しました。")
# #         else:
# #             print("設定はキャンセルされました。")
            
# #     def apply_settings_dynamically(self):
# #         if self.tts_worker and self.tts_worker.isRunning():
# #             self.tts_worker.set_tts_enabled(self.settings_manager.tts_enabled)
# #             self.tts_worker.set_tts_rate(self.settings_manager.tts_rate)
# #         if self.camera_worker and self.camera_worker.isRunning():
# #             self.camera_worker.set_stop_threshold(self.settings_manager.hand_stop_threshold)
# #         if self.observer_worker and self.observer_worker.isRunning():
# #             self.observer_worker.set_observation_interval(self.settings_manager.observation_interval)

# #     @Slot(bool)
# #     def on_camera_enabled_changed(self, enabled: bool):
# #         if enabled:
# #             self.start_camera_dependent_workers()
# #         else:
# #             self.stop_camera_dependent_workers()
# #             self.camera_view.setText("カメラはオフです")
# #             self.latest_camera_frame = None

# #     @Slot(bool)
# #     def on_stt_enabled_changed(self, enabled: bool):
# #         if self.stt_worker:
# #             self.stt_worker.set_enabled(enabled)

# #     def _get_long_term_context(self, relevant_sessions: List[Dict]) -> str:
# #         if not relevant_sessions:
# #             last_session_id = self.db_manager.get_last_active_session_id(exclude_session_id=self.active_session_id)
# #             if not last_session_id: return "これが最初のセッションです。"
# #             last_session_details = self.db_manager.get_session_details(last_session_id)
# #             if not last_session_details: return "前回のセッション情報を取得できませんでした。"
# #             last_messages = self.db_manager.get_messages_for_session(last_session_id)
# #             last_user_message = next((msg['content'] for msg in reversed(last_messages) if msg['role'] == 'user'), "なし")
# #             return f"（直近のセッションより）\n- 前回（{last_session_details['last_updated_at']}）のセッションでは、「{last_session_details['title']}」について学習しており、最後の質問は「{last_user_message}」でした。"
        
# #         context_lines = ["（過去の関連セッションより）"]
# #         for session in relevant_sessions:
# #             line = f"- セッション「{session['title']}」（{session['last_updated_at']}）では、キーワード「{session['keywords']}」について議論しました。"
# #             context_lines.append(line)
# #         return "\n".join(context_lines)

# #     def _add_message_to_ui_and_db(self, role: str, content: str):
# #         if not self.active_session_id: return
# #         self.current_chat_messages.append({"role": role, "content": content})
# #         self.update_chat_display()
# #         self.db_worker.add_message(self.active_session_id, role, content)

# #     def _trigger_keyword_extraction(self, session_id: int):
# #         if not session_id: return
# #         if self.keyword_extraction_worker and self.keyword_extraction_worker.isRunning(): return
# #         messages = self.db_manager.get_messages_for_session(session_id)
# #         if len(messages) < 4: return
# #         conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
# #         prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
# #         prompt = prompt_template.format(conversation_text=conversation_text)
        
# #         model_name = self.settings_manager.keyword_extraction_model
# #         self.keyword_extraction_worker = GeminiWorker(prompt, model_name=model_name)
# #         self.keyword_extraction_worker.response_ready.connect(lambda keywords: self.on_keywords_extracted(session_id, keywords))
# #         self.keyword_extraction_worker.finished.connect(self.on_keyword_worker_finished)
# #         self.keyword_extraction_worker.start()

# #     def _trigger_title_generation(self, session_id: int):
# #         if not session_id: return
# #         if self.title_generation_worker and self.title_generation_worker.isRunning(): return
# #         messages = self.db_manager.get_messages_for_session(session_id)
# #         if len(messages) < 4: return
# #         conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
# #         prompt_template = self.settings_manager.title_generation_prompt
# #         prompt = prompt_template.format(conversation_text=conversation_text)
        
# #         model_name = self.settings_manager.keyword_extraction_model
# #         self.title_generation_worker = GeminiWorker(prompt, model_name=model_name)
# #         self.title_generation_worker.response_ready.connect(lambda title: self.on_title_generated(session_id, title))
# #         self.title_generation_worker.finished.connect(self.on_title_generation_finished)
# #         self.title_generation_worker.start()

# #     @Slot(int, str)
# #     def on_title_generated(self, session_id: int, title: str):
# #         cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
# #         self.db_worker.update_session_title(session_id, cleaned_title)
# #         for i in range(self.session_list_widget.count()):
# #             item = self.session_list_widget.item(i)
# #             if item.data(Qt.UserRole) == session_id:
# #                 item.setText(cleaned_title)
# #                 break
    
# #     @Slot()
# #     def on_title_generation_finished(self):
# #         if self.title_generation_worker:
# #             self.title_generation_worker.deleteLater()
# #             self.title_generation_worker = None

# #     @Slot(int, str)
# #     def on_keywords_extracted(self, session_id: int, keywords_response: str):
# #         match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# #         cleaned_keywords = match.group(1).strip() if match else keywords_response.strip()
# #         cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
# #         self.db_worker.update_session_keywords(session_id, cleaned_keywords)
        
# #     @Slot()
# #     def on_keyword_worker_finished(self):
# #         if self.keyword_extraction_worker:
# #             self.keyword_extraction_worker.deleteLater()
# #             self.keyword_extraction_worker = None

# #     def update_chat_display(self):
# #         md_text = ""
# #         for msg in self.current_chat_messages:
# #             role_display = "あなた" if msg["role"] == "user" else "AIアシスタント"
# #             md_text += f"**{role_display}:**\n\n{msg['content']}\n\n<hr>\n\n"
# #         self.ai_output_view.set_markdown(md_text)

# #     def load_and_display_sessions(self):
# #         self.session_list_widget.blockSignals(True)
# #         self.session_list_widget.clear()
# #         sessions = self.db_manager.get_all_sessions()
# #         if not sessions:
# #             self.create_new_session(is_initial=True)
# #             sessions = self.db_manager.get_all_sessions()
# #         for session_id, title in sessions:
# #             item = QListWidgetItem(title)
# #             item.setData(Qt.UserRole, session_id)
# #             self.session_list_widget.addItem(item)
# #         self.session_list_widget.setCurrentRow(0)
# #         self.session_list_widget.blockSignals(False)
# #         if self.session_list_widget.currentItem():
# #             self.on_session_changed(self.session_list_widget.currentItem(), None)

# #     def create_new_session(self, is_initial=False):
# #         self.db_manager.create_new_session()
# #         if not is_initial:
# #             self.load_and_display_sessions()

# #     @Slot(QListWidgetItem, QListWidgetItem)
# #     def on_session_changed(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
# #         if previous_item:
# #             previous_session_id = previous_item.data(Qt.UserRole)
# #             self._trigger_keyword_extraction(previous_session_id)
# #             self._trigger_title_generation(previous_session_id)
# #         if not current_item: return
# #         session_id = current_item.data(Qt.UserRole)
# #         if session_id == self.active_session_id: return
# #         self.active_session_id = session_id
# #         session_details = self.db_manager.get_session_details(session_id)
# #         if session_details:
# #             self.context_manager.set_problem_context(session_details.get("problem_context"))
# #         self.current_chat_messages = self.db_manager.get_messages_for_session(self.active_session_id)
# #         self.update_chat_display()

# #     @Slot()
# #     def on_stop_speech_button_clicked(self):
# #         self.tts_worker.stop_current_speech()

# #     def execute_ai_task(self, prompt, speak=True, is_user_request=False, use_vision=False, is_continuation=False):
# #         if self.is_ai_task_running and not is_continuation:
# #             return
# #         if not is_continuation:
# #             self.is_ai_task_running = True
# #             self.header_stack.setCurrentIndex(1)
# #             if hasattr(self, 'movie'): self.movie.start()
            
# #         if is_user_request:
# #             self.send_button.setEnabled(False)
# #         if speak:
# #             self.stop_speech_button.setVisible(True)
            
# #         if use_vision:
# #             model_name = self.settings_manager.vision_model
# #             self.ai_worker = GeminiVisionWorker(prompt, model_name=model_name)
# #         else:
# #             model_name = self.settings_manager.main_response_model
# #             self.ai_worker = GeminiWorker(prompt, model_name=model_name)
            
# #         self.ai_worker.response_ready.connect(lambda r: self.handle_gemini_response(r, speak))
# #         self.ai_worker.finished.connect(self.on_ai_worker_finished)
# #         self.ai_worker.start()

# #     def handle_gemini_response(self, response_text, speak):
# #         if hasattr(self, 'movie'): self.movie.stop()
# #         self.header_stack.setCurrentIndex(0)
        
# #         self._add_message_to_ui_and_db("ai", response_text)
        
# #         if speak:
# #             print("読み上げ開始。音声認識を一時停止します。")
# #             self.stt_was_enabled_before_tts = self.stt_enabled_checkbox.isChecked()
# #             if self.stt_was_enabled_before_tts:
# #                 self.stt_enabled_checkbox.setChecked(False)
# #             self.tts_worker.speak(response_text)
# #         else:
# #             self.is_ai_task_running = False
# #             self.stop_speech_button.setVisible(False)
# #             if not self.send_button.isEnabled():
# #                 self.send_button.setEnabled(True)

# #     @Slot()
# #     def on_speech_finished(self):
# #         self.is_ai_task_running = False
# #         self.stop_speech_button.setVisible(False)
        
# #         print("読み上げ完了。音声認識の状態を復元します。")
# #         if self.stt_was_enabled_before_tts:
# #             self.stt_enabled_checkbox.setChecked(True)
        
# #         if not self.send_button.isEnabled():
# #             self.send_button.setEnabled(True)

# #     @Slot()
# #     def on_ai_worker_finished(self):
# #         if self.ai_worker:
# #             self.ai_worker.deleteLater()
# #             self.ai_worker = None

# #     def start_user_request(self):
# #         user_query = self.user_input.toPlainText().strip()
# #         if not (user_query and self.active_session_id): return
        
# #         self._add_message_to_ui_and_db("user", user_query)
# #         self.user_input.clear()
        
# #         self.is_ai_task_running = True
# #         self.header_stack.setCurrentIndex(1)
# #         if hasattr(self, 'movie'): self.movie.start()
# #         self.send_button.setEnabled(False)
        
# #         prompt = f"""以下の質問文から、中心となるキーワードを3つ、カンマ区切りで抽出してください。思考プロセスは不要です。キーワードのみを出力してください。\n例: 積分、グラフ、面積\n\n---\n{user_query}"""
        
# #         model_name = self.settings_manager.keyword_extraction_model
# #         self.query_keyword_worker = GeminiWorker(prompt, model_name=model_name)
# #         self.query_keyword_worker.response_ready.connect(lambda keywords: self.on_query_keywords_extracted(user_query, keywords))
# #         self.query_keyword_worker.finished.connect(self.on_query_keyword_worker_finished)
# #         self.query_keyword_worker.start()

# #     @Slot(str, str)
# #     def on_query_keywords_extracted(self, original_query: str, keywords_response: str):
# #         match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# #         cleaned_keywords_str = match.group(1).strip() if match else keywords_response.strip()
# #         cleaned_keywords = [kw.strip() for kw in cleaned_keywords_str.split(',') if kw.strip()]
        
# #         if not self.active_session_id: return
        
# #         relevant_sessions = self.db_manager.find_relevant_sessions(cleaned_keywords, exclude_session_id=self.active_session_id)
# #         long_term_context = self._get_long_term_context(relevant_sessions)
# #         monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
# #         observation_log = self.db_manager.get_recent_logs_for_session(self.active_session_id, "observation", 5)
        
# #         full_prompt = self.context_manager.build_prompt_for_query(original_query, self.current_chat_messages, monologue_history, observation_log, long_term_context)
# #         self.execute_ai_task(full_prompt, speak=True, is_user_request=True, is_continuation=True)

# #     @Slot()
# #     def on_query_keyword_worker_finished(self):
# #         if self.query_keyword_worker:
# #             self.query_keyword_worker.deleteLater()
# #             self.query_keyword_worker = None

# #     def open_file_dialog(self): 
# #         if not self.active_session_id: self.create_new_session(); return
# #         file_path, _ = QFileDialog.getOpenFileName(self, "問題ファイルを選択", "", "サポートファイル (*.pdf *.png *.jpg *.jpeg *.webp);;全ファイル (*)")
# #         if file_path:
# #             self._add_message_to_ui_and_db("ai", f"`{os.path.basename(file_path)}`を分析中...")
            
# #             model_name = self.settings_manager.vision_model
# #             gemini_client_for_file = GeminiClient(vision_model_name=model_name)
# #             self.file_worker = FileProcessingWorker(file_path, gemini_client_for_file)
# #             self.file_worker.finished_processing.connect(self.on_file_processed)
# #             self.file_worker.finished.connect(self.on_file_worker_finished)
# #             self.file_worker.start()

# #     @Slot(str)
# #     def on_file_processed(self, result_text):
# #         if not self.active_session_id: return
# #         self.db_worker.update_problem_context(self.active_session_id, result_text)
# #         self.context_manager.set_problem_context(result_text)
# #         message = f"ファイルの分析が完了しました。\n\n**【分析結果】**\n\n{result_text}\n\n---\nこの問題について質問してください。"
# #         self._add_message_to_ui_and_db("ai", message)
# #         self.tts_worker.speak("ファイルの分析が完了しました。")

# #     @Slot()
# #     def on_file_worker_finished(self):
# #         if self.file_worker:
# #             self.file_worker.deleteLater()
# #             self.file_worker = None
            
# #     @Slot(Image.Image)
# #     def on_hand_stopped(self, captured_image):
# #         if self.is_ai_task_running: return
# #         self.context_manager.set_triggered_image(captured_image)
# #         prompt = self.settings_manager.hand_stopped_prompt
# #         self.execute_ai_task(prompt, speak=True)

# #     @Slot(str)
# #     def on_monologue_recognized(self, text):
# #         if self.active_session_id:
# #             self.db_worker.add_log(self.active_session_id, "monologue", text)
# #         current_text = self.user_input.toPlainText()
# #         new_text = (current_text + " " + text) if current_text and not current_text.endswith(" ") else (current_text + text)
# #         self.user_input.setPlainText(new_text)
# #         self.user_input.moveCursor(QTextCursor.MoveOperation.End)

# #     @Slot(str)
# #     def on_command_recognized(self, command_text):
# #         if not self.active_session_id:
# #             self.tts_worker.speak("すみません、現在アクティブなセッションがありません。")
# #             return
            
# #         if not self.latest_camera_frame:
# #             self.tts_worker.speak("すみません、カメラの映像が取得できていません。")
# #             return
        
# #         self._add_message_to_ui_and_db("user", f"（音声コマンド）{command_text}")
# #         self.context_manager.set_triggered_image(self.latest_camera_frame.copy())

# #         self.is_ai_task_running = True
# #         self.header_stack.setCurrentIndex(1)
# #         if hasattr(self, 'movie'):
# #             self.movie.start()
# #         self.send_button.setEnabled(False)

# #         long_term_context = self._get_long_term_context([])
# #         monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
        
# #         prompt_parts = self.context_manager.build_prompt_parts_for_command(
# #             command_text, 
# #             self.current_chat_messages, 
# #             monologue_history, 
# #             long_term_context
# #         )
        
# #         if prompt_parts:
# #             self.execute_ai_task(prompt_parts, speak=True, is_user_request=False, use_vision=True, is_continuation=True)
# #         else:
# #             self.tts_worker.speak("コマンドの準備に失敗しました。")
# #             self.is_ai_task_running = False
# #             self.header_stack.setCurrentIndex(0)
# #             self.send_button.setEnabled(True)

# #     @Slot(str)
# #     def on_observation_received(self, observation_text: str):
# #         if self.active_session_id:
# #             self.db_worker.add_log(self.active_session_id, "observation", observation_text)

# #     @Slot(QImage, list)
# #     def update_camera_view(self, frame_qimage: QImage, detections: List[Dict]):
# #         if frame_qimage.isNull():
# #             return
        
# #         pixmap = QPixmap.fromImage(frame_qimage)
# #         painter = QPainter(pixmap)
# #         for detection in detections:
# #             box = detection["box"]
# #             label = f'{detection["label"]} {detection["confidence"]:.2f}'
# #             pen = QPen(QColor(0, 255, 0), 2)
# #             painter.setPen(pen)
# #             painter.drawRect(box[0], box[1], box[2] - box[0], box[3] - box[1])
# #             font = QFont()
# #             font.setPointSize(10)
# #             painter.setFont(font)
# #             painter.setPen(QColor(255, 255, 255))
# #             text_x, text_y = box[0], box[1] - 5
# #             painter.fillRect(text_x, text_y - 12, len(label) * 8, 16, QColor(0, 255, 0))
# #             painter.drawText(text_x, text_y, label)
# #         painter.end()
# #         self.camera_view.setPixmap(pixmap)
        
# #         buffer = frame_qimage.constBits().tobytes()
# #         self.latest_camera_frame = Image.frombytes("RGBA", (frame_qimage.width(), frame_qimage.height()), buffer, 'raw', "BGRA")

# #     def closeEvent(self, event):
# #         print("アプリケーションの終了処理を開始します...")

# #         print("UI関連以外のワーカースレッドを停止します...")
# #         self.stop_camera_dependent_workers()
        
# #         if self.stt_worker and self.stt_worker.isRunning():
# #             self.stt_worker.stop()
# #             self.stt_worker.wait()
# #             print(" > STTWorker 停止完了")
        
# #         if self.tts_worker and self.tts_worker.isRunning():
# #             self.tts_worker.stop()
# #             self.tts_worker.wait()
# #             print(" > TTSWorker 停止完了")
            
# #         if self.active_session_id:
# #             print(f"セッションID {self.active_session_id} の最終処理を実行します...")
            
# #             messages = self.db_manager.get_messages_for_session(self.active_session_id)
# #             if len(messages) >= 4:
# #                 conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                
# #                 main_gemini_client = GeminiClient(text_model_name=self.settings_manager.keyword_extraction_model)
                
# #                 kw_prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
# #                 kw_prompt = kw_prompt_template.format(conversation_text=conversation_text)
# #                 print(" > キーワードを抽出中...")
# #                 keywords_response = main_gemini_client.generate_response(kw_prompt)
# #                 match_kw = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
# #                 cleaned_keywords = match_kw.group(1).strip() if match_kw else keywords_response.strip()
# #                 cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
# #                 self.db_manager.update_session_keywords(self.active_session_id, cleaned_keywords)
# #                 print(f" > キーワードを保存しました: {cleaned_keywords}")

# #                 title_prompt_template = self.settings_manager.title_generation_prompt
# #                 title_prompt = title_prompt_template.format(conversation_text=conversation_text)
# #                 print(" > タイトルを生成中...")
# #                 title = main_gemini_client.generate_response(title_prompt)
# #                 cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
# #                 self.db_manager.update_session_title(self.active_session_id, cleaned_title)
# #                 print(f" > タイトルを保存しました: {cleaned_title}")

# #         if self.db_worker and self.db_worker.isRunning():
# #             print("データベースへの書き込み完了を待っています...")
# #             while self.db_worker.tasks:
# #                 print(f" > DBワーカーの残りタスク: {len(self.db_worker.tasks)}件")
# #                 QThread.msleep(100)
# #             self.db_worker.stop()
# #             self.db_worker.wait()
# #             print(" > DatabaseWorker 停止完了")
            
# #         print("すべての処理が安全に完了しました。アプリケーションを終了します。")
# #         super().closeEvent(event)




















# import sys
# import os
# import fitz
# import re
# from PIL import Image
# from PySide6.QtCore import QThread, Signal, Slot, QSize, Qt
# from PySide6.QtGui import QPixmap, QImage, QTextCursor, QMovie, QPainter, QColor, QPen, QFont, QAction
# from PySide6.QtWidgets import (
#     QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLabel,
#     QHBoxLayout, QCheckBox, QFileDialog, QStackedLayout, 
#     QListWidget, QListWidgetItem, QDockWidget
# )
# from typing import Optional, List, Dict

# from .widgets.md_view import MarkdownView
# from .settings_dialog import SettingsDialog
# from .panels.session_panel import SessionPanel
# from ..core.context_manager import ContextManager
# from ..core.gemini_client import GeminiClient
# from ..core.database_manager import DatabaseManager
# from ..core.database_worker import DatabaseWorker
# from ..core.visual_observer import VisualObserverWorker
# from ..core.settings_manager import SettingsManager
# from ..hardware.camera_handler import CameraWorker
# from ..hardware.audio_handler import TTSWorker, STTWorker

# # (ワーカースレッド定義は変更なし)
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


# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("勉強アシストアプリ")
#         self.setGeometry(100, 100, 1600, 900)
        
#         self.is_ai_task_running = False
#         self.context_manager = ContextManager()
#         self.settings_manager = SettingsManager()
#         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
#         db_path = os.path.join(project_root, "data", "sessions.db")
#         self.db_manager = DatabaseManager(db_path=db_path)
#         self.active_session_id: Optional[int] = None
#         self.latest_camera_frame: Optional[Image.Image] = None

#         self.camera_worker: Optional[CameraWorker] = None
#         self.stt_worker: Optional[STTWorker] = None
#         self.observer_worker: Optional[VisualObserverWorker] = None
#         self.tts_worker: Optional[TTSWorker] = None
#         self.db_worker: Optional[DatabaseWorker] = None
#         self.file_worker: Optional[FileProcessingWorker] = None
#         self.keyword_extraction_worker: Optional[GeminiWorker] = None
#         self.query_keyword_worker: Optional[GeminiWorker] = None
#         self.title_generation_worker: Optional[GeminiWorker] = None

#         self.current_chat_messages: List[Dict[str, str]] = []
#         self.stt_was_enabled_before_tts = False

#         self.setup_ui()
#         self.create_menu()
        
#         self.start_essential_workers()
#         self.restart_stt_worker()
        
#         self.load_and_display_sessions()

#         if self.settings_manager.camera_enabled_on_startup:
#             self.camera_enabled_checkbox.setChecked(True)
#         else:
#             self.camera_enabled_checkbox.setChecked(False)
#             self.camera_view.setText("カメラはオフです")

#     def setup_ui(self):
#         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        
#         # 1. セッション履歴パネルのインスタンス化
#         self.session_panel = SessionPanel()

#         # 2. メインのチャットパネルの作成
#         main_chat_widget = QWidget()
#         main_chat_widget.setMinimumSize(400, 300)
#         left_layout = QVBoxLayout(main_chat_widget)
#         self.ai_output_view = MarkdownView()
#         self.user_input = QTextEdit()
#         self.send_button = QPushButton("送信")
#         self.stt_enabled_checkbox = QCheckBox("音声認識")
#         self.load_file_button = QPushButton("問題ファイルを読み込む")
#         self.stop_speech_button = QPushButton("読み上げを停止")
#         self.stop_speech_button.setVisible(False)
#         loading_widget = QWidget()
#         loading_layout = QHBoxLayout(loading_widget)
#         loading_layout.setContentsMargins(0, 5, 0, 5)
#         self.loading_movie_label = QLabel()
#         loading_gif_path = os.path.join(project_root, "assets", "loading.gif")
#         if os.path.exists(loading_gif_path):
#             self.movie = QMovie(loading_gif_path)
#             self.loading_movie_label.setMovie(self.movie)
#             self.movie.setScaledSize(QSize(25, 25))
#         self.loading_text_label = QLabel("AIが考え中です...")
#         loading_layout.addStretch()
#         loading_layout.addWidget(self.loading_movie_label)
#         loading_layout.addWidget(self.loading_text_label)
#         loading_layout.addStretch()
#         self.header_stack = QStackedLayout()
#         self.header_stack.addWidget(QLabel("AIアシスタント"))
#         self.header_stack.addWidget(loading_widget)
#         top_button_layout = QHBoxLayout()
#         top_button_layout.addWidget(self.load_file_button)
#         top_button_layout.addStretch()
#         self.camera_enabled_checkbox = QCheckBox("カメラを有効にする")
#         top_button_layout.addWidget(self.camera_enabled_checkbox)
#         top_button_layout.addWidget(self.stt_enabled_checkbox)
#         button_v_layout = QVBoxLayout()
#         button_v_layout.addWidget(self.send_button)
#         button_v_layout.addWidget(self.stop_speech_button)
#         input_area_layout = QHBoxLayout()
#         input_area_layout.addWidget(self.user_input)
#         input_area_layout.addLayout(button_v_layout)
#         left_layout.addLayout(top_button_layout)
#         left_layout.addLayout(self.header_stack)
#         left_layout.addWidget(self.ai_output_view, stretch=1)
#         left_layout.addWidget(QLabel("質問や独り言を入力"))
#         left_layout.addLayout(input_area_layout)

#         # 3. カメラビューパネルの作成
#         right_widget = QWidget()
#         right_layout = QVBoxLayout(right_widget)
#         self.camera_view = QLabel("カメラを初期化中...")
#         self.camera_view.setStyleSheet("background-color: black; color: white;")
#         self.camera_view.setFixedSize(640, 480)
#         right_layout.addWidget(self.camera_view)
#         right_layout.addStretch()

#         # 4. DockWidgetを使ってレイアウトを構築
#         self.setDockNestingEnabled(True)

#         self.session_dock = QDockWidget("セッション履歴", self)
#         self.session_dock.setWidget(self.session_panel)
#         self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.session_dock)

#         self.chat_dock = QDockWidget("チャット", self)
#         self.chat_dock.setWidget(main_chat_widget)
#         self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.chat_dock)

#         self.camera_dock = QDockWidget("カメラビュー", self)
#         self.camera_dock.setWidget(right_widget)
#         self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.camera_dock)
        
#         self.tabifyDockWidget(self.session_dock, self.chat_dock)
        
#         # 5. シグナル接続
#         self.session_panel.new_session_requested.connect(self.create_new_session)
#         self.session_panel.session_selected.connect(self.on_session_changed)
#         self.send_button.clicked.connect(self.start_user_request)
#         self.load_file_button.clicked.connect(self.open_file_dialog)
#         self.stop_speech_button.clicked.connect(self.on_stop_speech_button_clicked)
#         self.camera_enabled_checkbox.toggled.connect(self.on_camera_enabled_changed)
#         self.stt_enabled_checkbox.toggled.connect(self.on_stt_enabled_changed)

#     def create_menu(self):
#         menu_bar = self.menuBar()
#         file_menu = menu_bar.addMenu("ファイル")
#         settings_action = QAction("設定...", self)
#         settings_action.triggered.connect(self.open_settings_dialog)
#         file_menu.addAction(settings_action)

#         view_menu = self.menuBar().addMenu("表示")
#         view_menu.addAction(self.session_dock.toggleViewAction())
#         view_menu.addAction(self.chat_dock.toggleViewAction())
#         view_menu.addAction(self.camera_dock.toggleViewAction())

#     def start_essential_workers(self):
#         self.db_worker = DatabaseWorker(self.db_manager)
#         self.tts_worker = TTSWorker()
#         self.db_worker.start()
#         self.tts_worker.start()
#         self.tts_worker.speech_finished.connect(self.on_speech_finished)
    
#     def start_camera_dependent_workers(self):
#         self.stop_camera_dependent_workers() 
#         print("カメラ関連ワーカーを起動します...")
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
#         self.camera_worker.frame_data_ready.connect(self.update_camera_view)
#         self.camera_worker.hand_stopped_signal.connect(self.on_hand_stopped)
#         self.camera_worker.raw_frame_for_observation.connect(self.observer_worker.update_frame)
#         self.observer_worker.observation_ready.connect(self.on_observation_received)
#         self.camera_worker.start()
#         self.observer_worker.start()

#     def stop_camera_dependent_workers(self):
#         if self.camera_worker and self.camera_worker.isRunning():
#             print("CameraWorkerを停止します...")
#             self.camera_worker.frame_data_ready.disconnect(self.update_camera_view)
#             self.camera_worker.hand_stopped_signal.disconnect(self.on_hand_stopped)
#             self.camera_worker.raw_frame_for_observation.disconnect(self.observer_worker.update_frame)
#             self.camera_worker.stop()
#             self.camera_worker.wait()
#             self.camera_worker = None
#             print(" > CameraWorker 停止完了")
#         if self.observer_worker and self.observer_worker.isRunning():
#             print("VisualObserverWorkerを停止します...")
#             self.observer_worker.stop()
#             self.observer_worker.wait()
#             self.observer_worker = None
#             print(" > VisualObserverWorker 停止完了")

#     def restart_stt_worker(self):
#         print("STTワーカーを再起動します...")
#         if self.stt_worker and self.stt_worker.isRunning():
#             self.stt_worker.monologue_recognized.disconnect(self.on_monologue_recognized)
#             self.stt_worker.command_recognized.disconnect(self.on_command_recognized)
#             self.stt_worker.stop()
#             self.stt_worker.wait()
#         self.stt_worker = STTWorker(device_index=self.settings_manager.mic_device_index)
#         self.stt_worker.monologue_recognized.connect(self.on_monologue_recognized)
#         self.stt_worker.command_recognized.connect(self.on_command_recognized)
#         self.stt_worker.set_enabled(self.stt_enabled_checkbox.isChecked())
#         self.stt_worker.start()
#         print(" > STTWorker 再起動完了")
        
#     def open_settings_dialog(self):
#         dialog = SettingsDialog(self)
#         if dialog.exec():
#             print("設定が変更されました。動的設定を適用し、必要なワーカーを再起動します。")
#             self.apply_settings_dynamically()
#             self.restart_stt_worker()
#             if self.camera_enabled_checkbox.isChecked():
#                 self.start_camera_dependent_workers()
#             print("ワーカーの再起動・設定反映が完了しました。")
#         else:
#             print("設定はキャンセルされました。")
            
#     def apply_settings_dynamically(self):
#         if self.tts_worker and self.tts_worker.isRunning():
#             self.tts_worker.set_tts_enabled(self.settings_manager.tts_enabled)
#             self.tts_worker.set_tts_rate(self.settings_manager.tts_rate)
#         if self.camera_worker and self.camera_worker.isRunning():
#             self.camera_worker.set_stop_threshold(self.settings_manager.hand_stop_threshold)
#         if self.observer_worker and self.observer_worker.isRunning():
#             self.observer_worker.set_observation_interval(self.settings_manager.observation_interval)

#     @Slot(bool)
#     def on_camera_enabled_changed(self, enabled: bool):
#         if enabled:
#             self.start_camera_dependent_workers()
#         else:
#             self.stop_camera_dependent_workers()
#             self.camera_view.setText("カメラはオフです")
#             self.latest_camera_frame = None

#     @Slot(bool)
#     def on_stt_enabled_changed(self, enabled: bool):
#         if self.stt_worker:
#             self.stt_worker.set_enabled(enabled)

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

#     def _add_message_to_ui_and_db(self, role: str, content: str):
#         if not self.active_session_id: return
#         self.current_chat_messages.append({"role": role, "content": content})
#         self.update_chat_display()
#         self.db_worker.add_message(self.active_session_id, role, content)

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

#     @Slot(int, str)
#     def on_title_generated(self, session_id: int, title: str):
#         cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
#         self.db_worker.update_session_title(session_id, cleaned_title)
#         for i in range(self.session_panel.count()):
#             item = self.session_panel.item(i)
#             if item.data(Qt.UserRole) == session_id:
#                 item.setText(cleaned_title)
#                 break
    
#     @Slot()
#     def on_title_generation_finished(self):
#         if self.title_generation_worker:
#             self.title_generation_worker.deleteLater()
#             self.title_generation_worker = None

#     @Slot(int, str)
#     def on_keywords_extracted(self, session_id: int, keywords_response: str):
#         match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
#         cleaned_keywords = match.group(1).strip() if match else keywords_response.strip()
#         cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
#         self.db_worker.update_session_keywords(session_id, cleaned_keywords)
        
#     @Slot()
#     def on_keyword_worker_finished(self):
#         if self.keyword_extraction_worker:
#             self.keyword_extraction_worker.deleteLater()
#             self.keyword_extraction_worker = None

#     def update_chat_display(self):
#         md_text = ""
#         for msg in self.current_chat_messages:
#             role_display = "あなた" if msg["role"] == "user" else "AIアシスタント"
#             md_text += f"**{role_display}:**\n\n{msg['content']}\n\n<hr>\n\n"
#         self.ai_output_view.set_markdown(md_text)

#     def load_and_display_sessions(self):
#         self.session_panel.block_signals(True)
#         self.session_panel.clear_list()
#         sessions = self.db_manager.get_all_sessions()
#         if not sessions:
#             self.create_new_session(is_initial=True)
#             sessions = self.db_manager.get_all_sessions()
#         for session_id, title in sessions:
#             item = QListWidgetItem(title)
#             item.setData(Qt.UserRole, session_id)
#             self.session_panel.add_item(item)
#         self.session_panel.set_current_row(0)
#         self.session_panel.block_signals(False)
#         if self.session_panel.current_item():
#             self.on_session_changed(self.session_panel.current_item(), None)

#     def create_new_session(self, is_initial=False):
#         self.db_manager.create_new_session()
#         if not is_initial:
#             self.load_and_display_sessions()

#     @Slot(QListWidgetItem, QListWidgetItem)
#     def on_session_changed(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
#         if previous_item:
#             previous_session_id = previous_item.data(Qt.UserRole)
#             self._trigger_keyword_extraction(previous_session_id)
#             self._trigger_title_generation(previous_session_id)
#         if not current_item: return
#         session_id = current_item.data(Qt.UserRole)
#         if session_id == self.active_session_id: return
#         self.active_session_id = session_id
#         session_details = self.db_manager.get_session_details(session_id)
#         if session_details:
#             self.context_manager.set_problem_context(session_details.get("problem_context"))
#         self.current_chat_messages = self.db_manager.get_messages_for_session(self.active_session_id)
#         self.update_chat_display()

#     @Slot()
#     def on_stop_speech_button_clicked(self):
#         self.tts_worker.stop_current_speech()

#     def execute_ai_task(self, prompt, speak=True, is_user_request=False, use_vision=False, is_continuation=False):
#         if self.is_ai_task_running and not is_continuation:
#             return
#         if not is_continuation:
#             self.is_ai_task_running = True
#             self.header_stack.setCurrentIndex(1)
#             if hasattr(self, 'movie'): self.movie.start()
            
#         if is_user_request:
#             self.send_button.setEnabled(False)
#         if speak:
#             self.stop_speech_button.setVisible(True)
            
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
#         if hasattr(self, 'movie'): self.movie.stop()
#         self.header_stack.setCurrentIndex(0)
        
#         self._add_message_to_ui_and_db("ai", response_text)
        
#         if speak:
#             print("読み上げ開始。音声認識を一時停止します。")
#             self.stt_was_enabled_before_tts = self.stt_enabled_checkbox.isChecked()
#             if self.stt_was_enabled_before_tts:
#                 self.stt_enabled_checkbox.setChecked(False)
#             self.tts_worker.speak(response_text)
#         else:
#             self.is_ai_task_running = False
#             self.stop_speech_button.setVisible(False)
#             if not self.send_button.isEnabled():
#                 self.send_button.setEnabled(True)

#     @Slot()
#     def on_speech_finished(self):
#         self.is_ai_task_running = False
#         self.stop_speech_button.setVisible(False)
        
#         print("読み上げ完了。音声認識の状態を復元します。")
#         if self.stt_was_enabled_before_tts:
#             self.stt_enabled_checkbox.setChecked(True)
        
#         if not self.send_button.isEnabled():
#             self.send_button.setEnabled(True)

#     @Slot()
#     def on_ai_worker_finished(self):
#         if self.ai_worker:
#             self.ai_worker.deleteLater()
#             self.ai_worker = None

#     def start_user_request(self):
#         user_query = self.user_input.toPlainText().strip()
#         if not (user_query and self.active_session_id): return
        
#         self._add_message_to_ui_and_db("user", user_query)
#         self.user_input.clear()
        
#         self.is_ai_task_running = True
#         self.header_stack.setCurrentIndex(1)
#         if hasattr(self, 'movie'): self.movie.start()
#         self.send_button.setEnabled(False)
        
#         prompt = f"""以下の質問文から、中心となるキーワードを3つ、カンマ区切りで抽出してください。思考プロセスは不要です。キーワードのみを出力してください。\n例: 積分、グラフ、面積\n\n---\n{user_query}"""
        
#         model_name = self.settings_manager.keyword_extraction_model
#         self.query_keyword_worker = GeminiWorker(prompt, model_name=model_name)
#         self.query_keyword_worker.response_ready.connect(lambda keywords: self.on_query_keywords_extracted(user_query, keywords))
#         self.query_keyword_worker.finished.connect(self.on_query_keyword_worker_finished)
#         self.query_keyword_worker.start()

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
        
#         full_prompt = self.context_manager.build_prompt_for_query(original_query, self.current_chat_messages, monologue_history, observation_log, long_term_context)
#         self.execute_ai_task(full_prompt, speak=True, is_user_request=True, is_continuation=True)

#     @Slot()
#     def on_query_keyword_worker_finished(self):
#         if self.query_keyword_worker:
#             self.query_keyword_worker.deleteLater()
#             self.query_keyword_worker = None

#     def open_file_dialog(self): 
#         if not self.active_session_id: self.create_new_session(); return
#         file_path, _ = QFileDialog.getOpenFileName(self, "問題ファイルを選択", "", "サポートファイル (*.pdf *.png *.jpg *.jpeg *.webp);;全ファイル (*)")
#         if file_path:
#             self._add_message_to_ui_and_db("ai", f"`{os.path.basename(file_path)}`を分析中...")
            
#             model_name = self.settings_manager.vision_model
#             gemini_client_for_file = GeminiClient(vision_model_name=model_name)
#             self.file_worker = FileProcessingWorker(file_path, gemini_client_for_file)
#             self.file_worker.finished_processing.connect(self.on_file_processed)
#             self.file_worker.finished.connect(self.on_file_worker_finished)
#             self.file_worker.start()

#     @Slot(str)
#     def on_file_processed(self, result_text):
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
#     def on_hand_stopped(self, captured_image):
#         if self.is_ai_task_running: return
#         self.context_manager.set_triggered_image(captured_image)
#         prompt = self.settings_manager.hand_stopped_prompt
#         self.execute_ai_task(prompt, speak=True)

#     @Slot(str)
#     def on_monologue_recognized(self, text):
#         if self.active_session_id:
#             self.db_worker.add_log(self.active_session_id, "monologue", text)
#         current_text = self.user_input.toPlainText()
#         new_text = (current_text + " " + text) if current_text and not current_text.endswith(" ") else (current_text + text)
#         self.user_input.setPlainText(new_text)
#         self.user_input.moveCursor(QTextCursor.MoveOperation.End)

#     @Slot(str)
#     def on_command_recognized(self, command_text):
#         if not self.active_session_id:
#             self.tts_worker.speak("すみません、現在アクティブなセッションがありません。")
#             return
            
#         if not self.latest_camera_frame:
#             self.tts_worker.speak("すみません、カメラの映像が取得できていません。")
#             return
        
#         self._add_message_to_ui_and_db("user", f"（音声コマンド）{command_text}")
#         self.context_manager.set_triggered_image(self.latest_camera_frame.copy())

#         self.is_ai_task_running = True
#         self.header_stack.setCurrentIndex(1)
#         if hasattr(self, 'movie'):
#             self.movie.start()
#         self.send_button.setEnabled(False)

#         long_term_context = self._get_long_term_context([])
#         monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
        
#         prompt_parts = self.context_manager.build_prompt_parts_for_command(
#             command_text, 
#             self.current_chat_messages, 
#             monologue_history, 
#             long_term_context
#         )
        
#         if prompt_parts:
#             self.execute_ai_task(prompt_parts, speak=True, is_user_request=False, use_vision=True, is_continuation=True)
#         else:
#             self.tts_worker.speak("コマンドの準備に失敗しました。")
#             self.is_ai_task_running = False
#             self.header_stack.setCurrentIndex(0)
#             self.send_button.setEnabled(True)

#     @Slot(str)
#     def on_observation_received(self, observation_text: str):
#         if self.active_session_id:
#             self.db_worker.add_log(self.active_session_id, "observation", observation_text)

#     @Slot(QImage, list)
#     def update_camera_view(self, frame_qimage: QImage, detections: List[Dict]):
#         if frame_qimage.isNull():
#             return
        
#         pixmap = QPixmap.fromImage(frame_qimage)
#         painter = QPainter(pixmap)
#         for detection in detections:
#             box = detection["box"]
#             label = f'{detection["label"]} {detection["confidence"]:.2f}'
#             pen = QPen(QColor(0, 255, 0), 2)
#             painter.setPen(pen)
#             painter.drawRect(box[0], box[1], box[2] - box[0], box[3] - box[1])
#             font = QFont()
#             font.setPointSize(10)
#             painter.setFont(font)
#             painter.setPen(QColor(255, 255, 255))
#             text_x, text_y = box[0], box[1] - 5
#             painter.fillRect(text_x, text_y - 12, len(label) * 8, 16, QColor(0, 255, 0))
#             painter.drawText(text_x, text_y, label)
#         painter.end()
#         self.camera_view.setPixmap(pixmap)
        
#         buffer = frame_qimage.constBits().tobytes()
#         self.latest_camera_frame = Image.frombytes("RGBA", (frame_qimage.width(), frame_qimage.height()), buffer, 'raw', "BGRA")

#     def closeEvent(self, event):
#         print("アプリケーションの終了処理を開始します...")

#         print("UI関連以外のワーカースレッドを停止します...")
#         self.stop_camera_dependent_workers()
        
#         if self.stt_worker and self.stt_worker.isRunning():
#             self.stt_worker.stop()
#             self.stt_worker.wait()
#             print(" > STTWorker 停止完了")
        
#         if self.tts_worker and self.tts_worker.isRunning():
#             self.tts_worker.stop()
#             self.tts_worker.wait()
#             print(" > TTSWorker 停止完了")
            
#         if self.active_session_id:
#             print(f"セッションID {self.active_session_id} の最終処理を実行します...")
            
#             messages = self.db_manager.get_messages_for_session(self.active_session_id)
#             if len(messages) >= 4:
#                 conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                
#                 main_gemini_client = GeminiClient(text_model_name=self.settings_manager.keyword_extraction_model)
                
#                 kw_prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
#                 kw_prompt = kw_prompt_template.format(conversation_text=conversation_text)
#                 print(" > キーワードを抽出中...")
#                 keywords_response = main_gemini_client.generate_response(kw_prompt)
#                 match_kw = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
#                 cleaned_keywords = match_kw.group(1).strip() if match_kw else keywords_response.strip()
#                 cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
#                 self.db_manager.update_session_keywords(self.active_session_id, cleaned_keywords)
#                 print(f" > キーワードを保存しました: {cleaned_keywords}")

#                 title_prompt_template = self.settings_manager.title_generation_prompt
#                 title_prompt = title_prompt_template.format(conversation_text=conversation_text)
#                 print(" > タイトルを生成中...")
#                 title = main_gemini_client.generate_response(title_prompt)
#                 cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
#                 self.db_manager.update_session_title(self.active_session_id, cleaned_title)
#                 print(f" > タイトルを保存しました: {cleaned_title}")

#         if self.db_worker and self.db_worker.isRunning():
#             print("データベースへの書き込み完了を待っています...")
#             while self.db_worker.tasks:
#                 print(f" > DBワーカーの残りタスク: {len(self.db_worker.tasks)}件")
#                 QThread.msleep(100)
#             self.db_worker.stop()
#             self.db_worker.wait()
#             print(" > DatabaseWorker 停止完了")
            
#         print("すべての処理が安全に完了しました。アプリケーションを終了します。")
#         super().closeEvent(event)


















import sys
import os
import fitz
import re
from PIL import Image
from PySide6.QtCore import QThread, Signal, Slot, QSize, Qt
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QFont, QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QListWidgetItem, QDockWidget, QFileDialog
)
from typing import Optional, List, Dict

from .panels.session_panel import SessionPanel
from .panels.chat_panel import ChatPanel
from .panels.camera_panel import CameraPanel
from .settings_dialog import SettingsDialog
from ..core.context_manager import ContextManager
from ..core.gemini_client import GeminiClient
from ..core.database_manager import DatabaseManager
from ..core.database_worker import DatabaseWorker
from ..core.visual_observer import VisualObserverWorker
from ..core.settings_manager import SettingsManager
from ..hardware.camera_handler import CameraWorker
from ..hardware.audio_handler import TTSWorker, STTWorker

# --- ワーカースレッド定義 (変更なし) ---
class FileProcessingWorker(QThread):
    finished_processing = Signal(str)
    def __init__(self, file_path, gemini_client, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.gemini_client = gemini_client
    def run(self):
        images = []
        file_path_lower = self.file_path.lower()
        try:
            if file_path_lower.endswith('.pdf'):
                doc = fitz.open(self.file_path)
                for page in doc:
                    pix = page.get_pixmap(dpi=150)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    images.append(img)
                doc.close()
            elif file_path_lower.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                images.append(Image.open(self.file_path).convert("RGB"))
            else:
                self.finished_processing.emit("サポートされていない形式です。")
                return
            if not images:
                self.finished_processing.emit("画像を変換できませんでした。")
                return
            prompt = "この画像は学習教材です。含まれるテキストや数式を正確に書き出してください。"
            self.finished_processing.emit(self.gemini_client.generate_vision_response([prompt] + images))
        except Exception as e:
            self.finished_processing.emit(f"ファイル処理エラー: {e}")

class GeminiWorker(QThread):
    response_ready = Signal(str)
    def __init__(self, prompt, model_name=None, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.gemini_client = GeminiClient(text_model_name=model_name)
    def run(self):
        self.response_ready.emit(self.gemini_client.generate_response(self.prompt))

class GeminiVisionWorker(QThread):
    response_ready = Signal(str)
    def __init__(self, prompt_parts, model_name=None, parent=None):
        super().__init__(parent)
        self.prompt_parts = prompt_parts
        self.gemini_client = GeminiClient(vision_model_name=model_name)
    def run(self):
        self.response_ready.emit(self.gemini_client.generate_vision_response(self.prompt_parts))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("勉強アシストアプリ")
        self.setGeometry(100, 100, 1600, 900)
        
        self.is_ai_task_running = False
        self.context_manager = ContextManager()
        self.settings_manager = SettingsManager()
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        db_path = os.path.join(project_root, "data", "sessions.db")
        self.db_manager = DatabaseManager(db_path=db_path)
        self.active_session_id: Optional[int] = None
        self.latest_camera_frame: Optional[Image.Image] = None

        self.camera_worker: Optional[CameraWorker] = None
        self.stt_worker: Optional[STTWorker] = None
        self.observer_worker: Optional[VisualObserverWorker] = None
        self.tts_worker: Optional[TTSWorker] = None
        self.db_worker: Optional[DatabaseWorker] = None
        self.file_worker: Optional[FileProcessingWorker] = None
        self.keyword_extraction_worker: Optional[GeminiWorker] = None
        self.query_keyword_worker: Optional[GeminiWorker] = None
        self.title_generation_worker: Optional[GeminiWorker] = None

        self.current_chat_messages: List[Dict[str, str]] = []
        self.stt_was_enabled_before_tts = False

        self.setup_ui()
        self.create_menu()
        
        self.start_essential_workers()
        self.restart_stt_worker()
        
        self.load_and_display_sessions()

        if self.settings_manager.camera_enabled_on_startup:
            self.chat_panel.set_camera_checkbox_state(True)
        else:
            self.chat_panel.set_camera_checkbox_state(False)
            self.camera_panel.set_text("カメラはオフです")

    def setup_ui(self):
        self.setDockNestingEnabled(True)

        # パネルのインスタンス化
        self.session_panel = SessionPanel()
        self.chat_panel = ChatPanel()
        self.camera_panel = CameraPanel()

        # DockWidgetの作成
        self.session_dock = QDockWidget("セッション履歴", self)
        self.session_dock.setWidget(self.session_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.session_dock)

        self.chat_dock = QDockWidget("チャット", self)
        self.chat_dock.setWidget(self.chat_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.chat_dock)

        self.camera_dock = QDockWidget("カメラビュー", self)
        self.camera_dock.setWidget(self.camera_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.camera_dock)
        
        self.tabifyDockWidget(self.session_dock, self.chat_dock)
        
        # シグナル接続
        self.session_panel.new_session_requested.connect(self.create_new_session)
        self.session_panel.session_selected.connect(self.on_session_changed)
        self.chat_panel.message_sent.connect(self.start_user_request)
        self.chat_panel.load_file_requested.connect(self.open_file_dialog)
        self.chat_panel.stop_speech_requested.connect(self.on_stop_speech_button_clicked)
        self.chat_panel.camera_toggled.connect(self.on_camera_enabled_changed)
        self.chat_panel.stt_toggled.connect(self.on_stt_enabled_changed)

    def create_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("ファイル")
        settings_action = QAction("設定...", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        file_menu.addAction(settings_action)

        view_menu = self.menuBar().addMenu("表示")
        view_menu.addAction(self.session_dock.toggleViewAction())
        view_menu.addAction(self.chat_dock.toggleViewAction())
        view_menu.addAction(self.camera_dock.toggleViewAction())
    
    def start_essential_workers(self):
        self.db_worker = DatabaseWorker(self.db_manager)
        self.tts_worker = TTSWorker()
        self.db_worker.start()
        self.tts_worker.start()
        self.tts_worker.speech_finished.connect(self.on_speech_finished)
    
    def start_camera_dependent_workers(self):
        self.stop_camera_dependent_workers() 
        print("カメラ関連ワーカーを起動します...")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        model_path = os.path.join(project_root, "models", "best12-2.pt")
        self.camera_worker = CameraWorker(
            model_path=model_path,
            device_index=self.settings_manager.camera_device_index,
            stop_threshold_sec=self.settings_manager.hand_stop_threshold
        )
        self.observer_worker = VisualObserverWorker(
            interval_sec=self.settings_manager.observation_interval
        )
        self.camera_worker.frame_data_ready.connect(self.update_camera_view)
        self.camera_worker.hand_stopped_signal.connect(self.on_hand_stopped)
        self.camera_worker.raw_frame_for_observation.connect(self.observer_worker.update_frame)
        self.observer_worker.observation_ready.connect(self.on_observation_received)
        self.camera_worker.start()
        self.observer_worker.start()

    def stop_camera_dependent_workers(self):
        if self.camera_worker and self.camera_worker.isRunning():
            print("CameraWorkerを停止します...")
            self.camera_worker.frame_data_ready.disconnect(self.update_camera_view)
            self.camera_worker.hand_stopped_signal.disconnect(self.on_hand_stopped)
            self.camera_worker.raw_frame_for_observation.disconnect(self.observer_worker.update_frame)
            self.camera_worker.stop()
            self.camera_worker.wait()
            self.camera_worker = None
            print(" > CameraWorker 停止完了")
        if self.observer_worker and self.observer_worker.isRunning():
            print("VisualObserverWorkerを停止します...")
            self.observer_worker.stop()
            self.observer_worker.wait()
            self.observer_worker = None
            print(" > VisualObserverWorker 停止完了")

    def restart_stt_worker(self):
        print("STTワーカーを再起動します...")
        if self.stt_worker and self.stt_worker.isRunning():
            self.stt_worker.monologue_recognized.disconnect(self.on_monologue_recognized)
            self.stt_worker.command_recognized.disconnect(self.on_command_recognized)
            self.stt_worker.stop()
            self.stt_worker.wait()
        self.stt_worker = STTWorker(device_index=self.settings_manager.mic_device_index)
        self.stt_worker.monologue_recognized.connect(self.on_monologue_recognized)
        self.stt_worker.command_recognized.connect(self.on_command_recognized)
        self.stt_worker.set_enabled(self.chat_panel.get_stt_checkbox_state())
        self.stt_worker.start()
        print(" > STTWorker 再起動完了")
        
    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            print("設定が変更されました。動的設定を適用し、必要なワーカーを再起動します。")
            self.apply_settings_dynamically()
            self.restart_stt_worker()
            if self.chat_panel.get_camera_checkbox_state():
                self.start_camera_dependent_workers()
            print("ワーカーの再起動・設定反映が完了しました。")
        else:
            print("設定はキャンセルされました。")
            
    def apply_settings_dynamically(self):
        if self.tts_worker and self.tts_worker.isRunning():
            self.tts_worker.set_tts_enabled(self.settings_manager.tts_enabled)
            self.tts_worker.set_tts_rate(self.settings_manager.tts_rate)
        if self.camera_worker and self.camera_worker.isRunning():
            self.camera_worker.set_stop_threshold(self.settings_manager.hand_stop_threshold)
        if self.observer_worker and self.observer_worker.isRunning():
            self.observer_worker.set_observation_interval(self.settings_manager.observation_interval)

    @Slot(bool)
    def on_camera_enabled_changed(self, enabled: bool):
        if enabled:
            self.start_camera_dependent_workers()
        else:
            self.stop_camera_dependent_workers()
            self.camera_panel.set_text("カメラはオフです")
            self.latest_camera_frame = None

    @Slot(bool)
    def on_stt_enabled_changed(self, enabled: bool):
        if self.stt_worker:
            self.stt_worker.set_enabled(enabled)

    def _get_long_term_context(self, relevant_sessions: List[Dict]) -> str:
        if not relevant_sessions:
            last_session_id = self.db_manager.get_last_active_session_id(exclude_session_id=self.active_session_id)
            if not last_session_id: return "これが最初のセッションです。"
            last_session_details = self.db_manager.get_session_details(last_session_id)
            if not last_session_details: return "前回のセッション情報を取得できませんでした。"
            last_messages = self.db_manager.get_messages_for_session(last_session_id)
            last_user_message = next((msg['content'] for msg in reversed(last_messages) if msg['role'] == 'user'), "なし")
            return f"（直近のセッションより）\n- 前回（{last_session_details['last_updated_at']}）のセッションでは、「{last_session_details['title']}」について学習しており、最後の質問は「{last_user_message}」でした。"
        
        context_lines = ["（過去の関連セッションより）"]
        for session in relevant_sessions:
            line = f"- セッション「{session['title']}」（{session['last_updated_at']}）では、キーワード「{session['keywords']}」について議論しました。"
            context_lines.append(line)
        return "\n".join(context_lines)

    def _add_message_to_ui_and_db(self, role: str, content: str):
        if not self.active_session_id: return
        self.current_chat_messages.append({"role": role, "content": content})
        self.chat_panel.set_markdown("\n\n---\n\n".join([f"**{'あなた' if msg['role'] == 'user' else 'AIアシスタント'}:**\n\n{msg['content']}" for msg in self.current_chat_messages]))
        self.db_worker.add_message(self.active_session_id, role, content)

    def _trigger_keyword_extraction(self, session_id: int):
        if not session_id: return
        if self.keyword_extraction_worker and self.keyword_extraction_worker.isRunning(): return
        messages = self.db_manager.get_messages_for_session(session_id)
        if len(messages) < 4: return
        conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
        prompt = prompt_template.format(conversation_text=conversation_text)
        
        model_name = self.settings_manager.keyword_extraction_model
        self.keyword_extraction_worker = GeminiWorker(prompt, model_name=model_name)
        self.keyword_extraction_worker.response_ready.connect(lambda keywords: self.on_keywords_extracted(session_id, keywords))
        self.keyword_extraction_worker.finished.connect(self.on_keyword_worker_finished)
        self.keyword_extraction_worker.start()

    def _trigger_title_generation(self, session_id: int):
        if not session_id: return
        if self.title_generation_worker and self.title_generation_worker.isRunning(): return
        messages = self.db_manager.get_messages_for_session(session_id)
        if len(messages) < 4: return
        conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        prompt_template = self.settings_manager.title_generation_prompt
        prompt = prompt_template.format(conversation_text=conversation_text)
        
        model_name = self.settings_manager.keyword_extraction_model
        self.title_generation_worker = GeminiWorker(prompt, model_name=model_name)
        self.title_generation_worker.response_ready.connect(lambda title: self.on_title_generated(session_id, title))
        self.title_generation_worker.finished.connect(self.on_title_generation_finished)
        self.title_generation_worker.start()

    @Slot(int, str)
    def on_title_generated(self, session_id: int, title: str):
        cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
        self.db_worker.update_session_title(session_id, cleaned_title)
        for i in range(self.session_panel.count()):
            item = self.session_panel.item(i)
            if item.data(Qt.UserRole) == session_id:
                item.setText(cleaned_title)
                break
    
    @Slot()
    def on_title_generation_finished(self):
        if self.title_generation_worker:
            self.title_generation_worker.deleteLater()
            self.title_generation_worker = None

    @Slot(int, str)
    def on_keywords_extracted(self, session_id: int, keywords_response: str):
        match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
        cleaned_keywords = match.group(1).strip() if match else keywords_response.strip()
        cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
        self.db_worker.update_session_keywords(session_id, cleaned_keywords)
        
    @Slot()
    def on_keyword_worker_finished(self):
        if self.keyword_extraction_worker:
            self.keyword_extraction_worker.deleteLater()
            self.keyword_extraction_worker = None

    def update_chat_display(self):
        md_text = ""
        for msg in self.current_chat_messages:
            role_display = "あなた" if msg["role"] == "user" else "AIアシスタント"
            md_text += f"**{role_display}:**\n\n{msg['content']}\n\n<hr>\n\n"
        self.chat_panel.set_markdown(md_text)

    def load_and_display_sessions(self):
        self.session_panel.block_signals(True)
        self.session_panel.clear_list()
        sessions = self.db_manager.get_all_sessions()
        if not sessions:
            self.create_new_session(is_initial=True)
            sessions = self.db_manager.get_all_sessions()
        for session_id, title in sessions:
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, session_id)
            self.session_panel.add_item(item)
        self.session_panel.set_current_row(0)
        self.session_panel.block_signals(False)
        if self.session_panel.current_item():
            self.on_session_changed(self.session_panel.current_item(), None)

    def create_new_session(self, is_initial=False):
        session_id = self.db_manager.create_new_session()
        if not is_initial:
            self.load_and_display_sessions()
            # 新しく作成したセッションを選択状態にする
            for i in range(self.session_panel.count()):
                item = self.session_panel.item(i)
                if item.data(Qt.UserRole) == session_id:
                    self.session_panel.set_current_row(i)
                    break
    
    @Slot(QListWidgetItem, QListWidgetItem)
    def on_session_changed(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
        if previous_item:
            previous_session_id = previous_item.data(Qt.UserRole)
            self._trigger_keyword_extraction(previous_session_id)
            self._trigger_title_generation(previous_session_id)
        if not current_item: return
        session_id = current_item.data(Qt.UserRole)
        if session_id == self.active_session_id: return
        self.active_session_id = session_id
        session_details = self.db_manager.get_session_details(session_id)
        if session_details:
            self.context_manager.set_problem_context(session_details.get("problem_context"))
        self.current_chat_messages = self.db_manager.get_messages_for_session(self.active_session_id)
        self.update_chat_display()

    @Slot()
    def on_stop_speech_button_clicked(self):
        self.tts_worker.stop_current_speech()

    def execute_ai_task(self, prompt, speak=True, is_user_request=False, use_vision=False, is_continuation=False):
        if self.is_ai_task_running and not is_continuation:
            return
        if not is_continuation:
            self.is_ai_task_running = True
            self.chat_panel.set_thinking_mode(True)
            
        if is_user_request:
            # chat_panelのsend_buttonを無効化する処理はset_thinking_modeに含まれる
            pass
        if speak:
            self.chat_panel.show_stop_speech_button(True)
            
        if use_vision:
            model_name = self.settings_manager.vision_model
            self.ai_worker = GeminiVisionWorker(prompt, model_name=model_name)
        else:
            model_name = self.settings_manager.main_response_model
            self.ai_worker = GeminiWorker(prompt, model_name=model_name)
            
        self.ai_worker.response_ready.connect(lambda r: self.handle_gemini_response(r, speak))
        self.ai_worker.finished.connect(self.on_ai_worker_finished)
        self.ai_worker.start()

    def handle_gemini_response(self, response_text, speak):
        self.chat_panel.set_thinking_mode(False)
        self._add_message_to_ui_and_db("ai", response_text)
        
        if speak:
            self.stt_was_enabled_before_tts = self.chat_panel.get_stt_checkbox_state()
            if self.stt_was_enabled_before_tts:
                self.chat_panel.set_stt_checkbox_state(False)
            self.tts_worker.speak(response_text)
        else:
            self.is_ai_task_running = False
            self.chat_panel.show_stop_speech_button(False)

    @Slot()
    def on_speech_finished(self):
        self.is_ai_task_running = False
        self.chat_panel.show_stop_speech_button(False)
        
        if self.stt_was_enabled_before_tts:
            self.chat_panel.set_stt_checkbox_state(True)
        
    @Slot()
    def on_ai_worker_finished(self):
        if self.ai_worker:
            self.ai_worker.deleteLater()
            self.ai_worker = None

    @Slot(str)
    def start_user_request(self, user_query: str):
        if not (user_query and self.active_session_id): return
        
        self._add_message_to_ui_and_db("user", user_query)
        
        self.is_ai_task_running = True
        self.chat_panel.set_thinking_mode(True)
        
        prompt = f"""以下の質問文から、中心となるキーワードを3つ、カンマ区切りで抽出してください。思考プロセスは不要です。キーワードのみを出力してください。\n例: 積分、グラフ、面積\n\n---\n{user_query}"""
        
        model_name = self.settings_manager.keyword_extraction_model
        self.query_keyword_worker = GeminiWorker(prompt, model_name=model_name)
        self.query_keyword_worker.response_ready.connect(lambda keywords: self.on_query_keywords_extracted(user_query, keywords))
        self.query_keyword_worker.finished.connect(self.on_query_keyword_worker_finished)
        self.query_keyword_worker.start()

    @Slot(str, str)
    def on_query_keywords_extracted(self, original_query: str, keywords_response: str):
        match = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
        cleaned_keywords_str = match.group(1).strip() if match else keywords_response.strip()
        cleaned_keywords = [kw.strip() for kw in cleaned_keywords_str.split(',') if kw.strip()]
        
        if not self.active_session_id: return
        
        relevant_sessions = self.db_manager.find_relevant_sessions(cleaned_keywords, exclude_session_id=self.active_session_id)
        long_term_context = self._get_long_term_context(relevant_sessions)
        monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
        observation_log = self.db_manager.get_recent_logs_for_session(self.active_session_id, "observation", 5)
        
        full_prompt = self.context_manager.build_prompt_for_query(original_query, self.current_chat_messages, monologue_history, observation_log, long_term_context)
        self.execute_ai_task(full_prompt, speak=True, is_user_request=True, is_continuation=True)

    @Slot()
    def on_query_keyword_worker_finished(self):
        if self.query_keyword_worker:
            self.query_keyword_worker.deleteLater()
            self.query_keyword_worker = None

    def open_file_dialog(self): 
        if not self.active_session_id: self.create_new_session(); return
        file_path, _ = QFileDialog.getOpenFileName(self, "問題ファイルを選択", "", "サポートファイル (*.pdf *.png *.jpg *.jpeg *.webp);;全ファイル (*)")
        if file_path:
            self._add_message_to_ui_and_db("ai", f"`{os.path.basename(file_path)}`を分析中...")
            
            model_name = self.settings_manager.vision_model
            gemini_client_for_file = GeminiClient(vision_model_name=model_name)
            self.file_worker = FileProcessingWorker(file_path, gemini_client_for_file)
            self.file_worker.finished_processing.connect(self.on_file_processed)
            self.file_worker.finished.connect(self.on_file_worker_finished)
            self.file_worker.start()

    @Slot(str)
    def on_file_processed(self, result_text):
        if not self.active_session_id: return
        self.db_worker.update_problem_context(self.active_session_id, result_text)
        self.context_manager.set_problem_context(result_text)
        message = f"ファイルの分析が完了しました。\n\n**【分析結果】**\n\n{result_text}\n\n---\nこの問題について質問してください。"
        self._add_message_to_ui_and_db("ai", message)
        self.tts_worker.speak("ファイルの分析が完了しました。")

    @Slot()
    def on_file_worker_finished(self):
        if self.file_worker:
            self.file_worker.deleteLater()
            self.file_worker = None
            
    @Slot(Image.Image)
    def on_hand_stopped(self, captured_image):
        if self.is_ai_task_running: return
        self.context_manager.set_triggered_image(captured_image)
        prompt = self.settings_manager.hand_stopped_prompt
        self.execute_ai_task(prompt, speak=True)

    @Slot(str)
    def on_monologue_recognized(self, text):
        if self.active_session_id:
            self.db_worker.add_log(self.active_session_id, "monologue", text)
        self.chat_panel.append_to_input(text)

    @Slot(str)
    def on_command_recognized(self, command_text):
        if not self.active_session_id:
            self.tts_worker.speak("すみません、現在アクティブなセッションがありません。")
            return
            
        if not self.latest_camera_frame:
            self.tts_worker.speak("すみません、カメラの映像が取得できていません。")
            return
        
        self._add_message_to_ui_and_db("user", f"（音声コマンド）{command_text}")
        self.context_manager.set_triggered_image(self.latest_camera_frame.copy())

        self.is_ai_task_running = True
        self.chat_panel.set_thinking_mode(True)

        long_term_context = self._get_long_term_context([])
        monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
        
        prompt_parts = self.context_manager.build_prompt_parts_for_command(
            command_text, 
            self.current_chat_messages, 
            monologue_history, 
            long_term_context
        )
        
        if prompt_parts:
            self.execute_ai_task(prompt_parts, speak=True, is_user_request=False, use_vision=True, is_continuation=True)
        else:
            self.tts_worker.speak("コマンドの準備に失敗しました。")
            self.is_ai_task_running = False
            self.chat_panel.set_thinking_mode(False)

    @Slot(str)
    def on_observation_received(self, observation_text: str):
        if self.active_session_id:
            self.db_worker.add_log(self.active_session_id, "observation", observation_text)

    @Slot(QImage, list)
    def update_camera_view(self, frame_qimage: QImage, detections: List[Dict]):
        if frame_qimage.isNull():
            return
        
        pixmap = QPixmap.fromImage(frame_qimage)
        painter = QPainter(pixmap)
        for detection in detections:
            box = detection["box"]
            label = f'{detection["label"]} {detection["confidence"]:.2f}'
            pen = QPen(QColor(0, 255, 0), 2)
            painter.setPen(pen)
            painter.drawRect(box[0], box[1], box[2] - box[0], box[3] - box[1])
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            text_x, text_y = box[0], box[1] - 5
            painter.fillRect(text_x, text_y - 12, len(label) * 8, 16, QColor(0, 255, 0))
            painter.drawText(text_x, text_y, label)
        painter.end()
        self.camera_panel.set_pixmap(pixmap)
        
        buffer = frame_qimage.constBits().tobytes()
        self.latest_camera_frame = Image.frombytes("RGBA", (frame_qimage.width(), frame_qimage.height()), buffer, 'raw', "BGRA")

    def closeEvent(self, event):
        print("アプリケーションの終了処理を開始します...")

        self.stop_camera_dependent_workers()
        
        if self.stt_worker and self.stt_worker.isRunning():
            self.stt_worker.stop()
            self.stt_worker.wait()
            print(" > STTWorker 停止完了")
        
        if self.tts_worker and self.tts_worker.isRunning():
            self.tts_worker.stop()
            self.tts_worker.wait()
            print(" > TTSWorker 停止完了")
            
        if self.active_session_id:
            print(f"セッションID {self.active_session_id} の最終処理を実行します...")
            
            messages = self.db_manager.get_messages_for_session(self.active_session_id)
            if len(messages) >= 4:
                conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                
                main_gemini_client = GeminiClient(text_model_name=self.settings_manager.keyword_extraction_model)
                
                kw_prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
                kw_prompt = kw_prompt_template.format(conversation_text=conversation_text)
                print(" > キーワードを抽出中...")
                keywords_response = main_gemini_client.generate_response(kw_prompt)
                match_kw = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
                cleaned_keywords = match_kw.group(1).strip() if match_kw else keywords_response.strip()
                cleaned_keywords = cleaned_keywords.replace("*", "").replace("`", "")
                self.db_manager.update_session_keywords(self.active_session_id, cleaned_keywords)
                print(f" > キーワードを保存しました: {cleaned_keywords}")

                title_prompt_template = self.settings_manager.title_generation_prompt
                title_prompt = title_prompt_template.format(conversation_text=conversation_text)
                print(" > タイトルを生成中...")
                title = main_gemini_client.generate_response(title_prompt)
                cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
                self.db_manager.update_session_title(self.active_session_id, cleaned_title)
                print(f" > タイトルを保存しました: {cleaned_title}")

        if self.db_worker and self.db_worker.isRunning():
            print("データベースへの書き込み完了を待っています...")
            while self.db_worker.tasks:
                print(f" > DBワーカーの残りタスク: {len(self.db_worker.tasks)}件")
                QThread.msleep(100)
            self.db_worker.stop()
            self.db_worker.wait()
            print(" > DatabaseWorker 停止完了")
            
        print("すべての処理が安全に完了しました。アプリケーションを終了します。")
        super().closeEvent(event)
# src/ui/main_window.py

import sys
import os
# fitzはFileProcessingWorkerのrunで遅延インポートするため、ここでは不要
import re
from PIL import Image
from PySide6.QtCore import QThread, Signal, Slot, QSize, Qt, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QFont, QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QListWidgetItem, QDockWidget, QFileDialog, QApplication
)
from typing import Optional, List, Dict

from .panels.session_panel import SessionPanel
from .panels.chat_panel import ChatPanel
from .panels.camera_panel import CameraPanel
from .panels.log_panel import LogPanel
from .panels.context_panel import ContextPanel
from .settings_dialog import SettingsDialog
from ..core.context_manager import ContextManager
from ..core.gemini_client import GeminiClient
from ..core.database_manager import DatabaseManager
from ..core.database_worker import DatabaseWorker
from ..core.visual_observer import VisualObserverWorker
from ..core.settings_manager import SettingsManager
from ..hardware.camera_handler import CameraWorker
from ..hardware.audio_handler import TTSWorker, STTWorker

class FileProcessingWorker(QThread):
    finished_processing = Signal(str)
    def __init__(self, file_path, gemini_client, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.gemini_client = gemini_client
    def run(self):
        import fitz
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
        
        self.statusBar().showMessage("アプリケーションを起動中...")

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
        self.summary_generation_worker: Optional[GeminiWorker] = None
        
        self.session_post_process_timer = QTimer(self)
        self.session_post_process_timer.setSingleShot(True)

        self.current_chat_messages: List[Dict[str, str]] = []
        self.stt_was_enabled_before_tts = False

        self.setup_ui()
        self.create_menu()
        
        QTimer.singleShot(100, self.initialize_background_tasks)

    def setup_ui(self):
        self.setDockNestingEnabled(True)

        self.session_panel = SessionPanel()
        self.chat_panel = ChatPanel()
        self.camera_panel = CameraPanel()
        self.log_panel = LogPanel()
        self.context_panel = ContextPanel()

        self.session_dock = QDockWidget("セッション履歴", self)
        self.session_dock.setWidget(self.session_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.session_dock)

        self.chat_dock = QDockWidget("チャット", self)
        self.chat_dock.setWidget(self.chat_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.chat_dock)

        self.camera_dock = QDockWidget("カメラビュー", self)
        self.camera_dock.setWidget(self.camera_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.camera_dock)
        
        self.context_dock = QDockWidget("コンテキスト", self)
        self.context_dock.setWidget(self.context_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.context_dock)

        self.log_dock = QDockWidget("システムログ", self)
        self.log_dock.setWidget(self.log_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.log_dock)
        
        self.splitDockWidget(self.camera_dock, self.context_dock, Qt.Orientation.Vertical)
        self.tabifyDockWidget(self.context_dock, self.log_dock)

        self.session_panel.new_session_requested.connect(self.create_new_session)
        self.session_panel.session_selected.connect(self.on_session_changed)
        self.chat_panel.message_sent.connect(self.start_user_request)
        self.chat_panel.load_file_requested.connect(self.open_file_dialog)
        self.chat_panel.stop_speech_requested.connect(self.on_stop_speech_button_clicked)
        self.chat_panel.camera_toggled.connect(self.on_camera_enabled_changed)
        self.chat_panel.stt_toggled.connect(self.on_stt_enabled_changed)
        self.context_panel.context_saved.connect(self.on_context_saved)

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
        view_menu.addAction(self.context_dock.toggleViewAction())
        view_menu.addAction(self.log_dock.toggleViewAction())

    def initialize_background_tasks(self):
        print("UI表示後にバックグラウンドタスクの初期化を開始します。")
        self.statusBar().showMessage("バックグラウンドサービスを初期化中...")
        
        self.start_essential_workers()
        self.restart_stt_worker()
        self.load_and_display_sessions()

        if self.settings_manager.camera_enabled_on_startup:
            self.chat_panel.set_camera_checkbox_state(True)
        else:
            self.chat_panel.set_camera_checkbox_state(False)
            self.camera_panel.set_text("カメラはオフです")
        
        self.statusBar().showMessage("準備完了")
    
    def start_essential_workers(self):
        self.db_worker = DatabaseWorker(self.db_manager)
        self.db_worker.message_added.connect(self.on_message_added)
        self.tts_worker = TTSWorker()
        self.db_worker.start()
        self.tts_worker.start()
        self.tts_worker.speech_finished.connect(self.on_speech_finished)
    
    def start_camera_dependent_workers(self):
        self.stop_camera_dependent_workers() 
        print("カメラ関連ワーカーを起動します...")
        self.log_panel.add_log_message("カメラ関連ワーカーを起動します...")
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
            self.log_panel.add_log_message("CameraWorkerを停止します...")
            self.camera_worker.frame_data_ready.disconnect(self.update_camera_view)
            self.camera_worker.hand_stopped_signal.disconnect(self.on_hand_stopped)
            self.camera_worker.raw_frame_for_observation.disconnect(self.observer_worker.update_frame)
            self.camera_worker.stop()
            self.camera_worker.wait()
            self.camera_worker = None
            print(" > CameraWorker 停止完了")
        if self.observer_worker and self.observer_worker.isRunning():
            print("VisualObserverWorkerを停止します...")
            self.log_panel.add_log_message("VisualObserverWorkerを停止します...")
            self.observer_worker.stop()
            self.observer_worker.wait()
            self.observer_worker = None
            print(" > VisualObserverWorker 停止完了")

    def restart_stt_worker(self):
        print("STTワーカーを再起動します...")
        self.log_panel.add_log_message("STTワーカーを再起動します...")
        if self.stt_worker and self.stt_worker.isRunning():
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
            self.log_panel.add_log_message("設定が変更されました。ワーカーを再起動します。")
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

    @Slot(str, str)
    def on_context_saved(self, problem_text: str, summary_text: str):
        if self.active_session_id is None:
            return
        self.context_manager.set_problem_context(problem_text)
        self.context_manager.set_chat_summary(summary_text)
        self.db_worker.update_problem_context(self.active_session_id, problem_text)
        self.db_worker.update_session_summary(self.active_session_id, summary_text)
        self.log_panel.add_log_message("コンテキスト情報が手動で更新・保存されました。")

    def _trigger_summary_generation(self, session_id: int):
        if not session_id or (self.summary_generation_worker and self.summary_generation_worker.isRunning()):
            return
        print(f"セッションID {session_id} の要約生成タスクを開始します。")
        messages = self.db_manager.get_messages_for_session(session_id)
        if sum(1 for msg in messages if msg['role'] == 'user') < 5: 
            print("会話が短いため、要約生成をスキップしました。")
            return
        conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        prompt = f"""以下の会話履歴を、第三者の視点から重要なポイントを箇条書きで3〜5点にまとめてください。\n\n---\n{conversation_text}"""
        model_name = self.settings_manager.keyword_extraction_model
        self.summary_generation_worker = GeminiWorker(prompt, model_name=model_name)
        self.summary_generation_worker.response_ready.connect(lambda summary: self.on_summary_generated(session_id, summary))
        self.summary_generation_worker.finished.connect(self.on_summary_worker_finished)
        self.summary_generation_worker.start()

    @Slot(int, str)
    def on_summary_generated(self, session_id: int, summary: str):
        if not summary.strip() or "エラー" in summary:
            print(f"要約の生成に失敗または空の応答: {summary}")
            return
        print(f"セッションID {session_id} の要約が生成されました。")
        self.log_panel.add_log_message(f"セッション(ID:{session_id})の要約を生成しました。")
        if session_id == self.active_session_id:
            self.context_manager.set_chat_summary(summary)
            self.context_panel.update_chat_summary(summary)
        self.db_worker.update_session_summary(session_id, summary)

    @Slot()
    def on_summary_worker_finished(self):
        if self.summary_generation_worker:
            self.summary_generation_worker.deleteLater()
            self.summary_generation_worker = None

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

    def _request_add_message(self, role: str, content: str):
        if self.active_session_id:
            self.db_worker.add_message(self.active_session_id, role, content)

    @Slot(dict)
    def on_message_added(self, new_message: Dict):
        if not new_message or new_message.get('id') is None: return
        self.current_chat_messages.append(new_message)
        should_scroll = (new_message.get("role") == "user")
        self.chat_panel.add_message(new_message, scroll=should_scroll)
        
    def _trigger_keyword_extraction(self, session_id: int):
        if not session_id or (self.keyword_extraction_worker and self.keyword_extraction_worker.isRunning()): return
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
        if not session_id or (self.title_generation_worker and self.title_generation_worker.isRunning()): return
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

    def _run_session_post_processing(self, session_id: int):
        print(f"セッションID {session_id} の後処理（キーワード、タイトル、要約）を開始します。")
        self.log_panel.add_log_message(f"セッション(ID:{session_id})の後処理を開始...")
        self._trigger_keyword_extraction(session_id)
        self._trigger_title_generation(session_id)
        self._trigger_summary_generation(session_id)

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
    
    def load_and_display_sessions(self):
        self.session_panel.block_signals(True)
        self.session_panel.clear_list()
        sessions = self.db_manager.get_all_sessions()
        if not sessions:
            self.create_new_session(is_initial=True)
            return
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
        self.log_panel.add_log_message(f"新しいセッション(ID:{session_id})を作成しました。")
        if not is_initial:
            self.load_and_display_sessions()
            for i in range(self.session_panel.count()):
                item = self.session_panel.item(i)
                if item.data(Qt.UserRole) == session_id:
                    self.session_panel.set_current_row(i)
                    break
        else:
            self.load_and_display_sessions()

    @Slot(QListWidgetItem, QListWidgetItem)
    def on_session_changed(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
        self.session_post_process_timer.stop()
        if previous_item:
            previous_session_id = previous_item.data(Qt.UserRole)
            self.session_post_process_timer.timeout.connect(lambda: self._run_session_post_processing(previous_session_id))
            self.session_post_process_timer.start(2000)
        if not current_item: return
        session_id = current_item.data(Qt.UserRole)
        if session_id == self.active_session_id: return
        self.active_session_id = session_id
        self.log_panel.add_log_message(f"セッションを切り替えました (ID: {session_id})")
        session_details = self.db_manager.get_session_details(session_id)
        if session_details:
            problem_context = session_details.get("problem_context")
            chat_summary = session_details.get("chat_summary")
            self.context_manager.set_problem_context(problem_context)
            self.context_manager.set_chat_summary(chat_summary)
            self.context_panel.update_problem_context(problem_context)
            self.context_panel.update_chat_summary(chat_summary)
        else:
            self.context_panel.update_problem_context("")
            self.context_panel.update_chat_summary("")
        self.current_chat_messages = self.db_manager.get_messages_for_session(self.active_session_id)
        self.chat_panel.set_messages(self.current_chat_messages)

    @Slot()
    def on_stop_speech_button_clicked(self):
        self.tts_worker.stop_current_speech()

    def execute_ai_task(self, prompt, speak=True, is_user_request=False, use_vision=False, is_continuation=False):
        if self.is_ai_task_running and not is_continuation: return
        if not is_continuation:
            self.is_ai_task_running = True
            self.chat_panel.set_thinking_mode(True)
        if is_user_request: pass 
        if speak: self.chat_panel.show_stop_speech_button(True)
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
        self._request_add_message("ai", response_text)
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
        self._request_add_message("user", user_query)
        self.is_ai_task_running = True
        self.chat_panel.set_thinking_mode(True)
        self._trigger_summary_generation(self.active_session_id)
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
            self._request_add_message("ai", f"`{os.path.basename(file_path)}`を分析中...")
            self.log_panel.add_log_message(f"ファイル分析を開始: {os.path.basename(file_path)}")
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
        self.context_panel.update_problem_context(result_text)
        message = f"ファイルの分析が完了しました。\n\n**【分析結果】**\n\n{result_text}\n\n---\nこの問題について質問してください。"
        self._request_add_message("ai", message)
        self.tts_worker.speak("ファイルの分析が完了しました。")
        self.log_panel.add_log_message("ファイルの分析が完了しました。")

    @Slot()
    def on_file_worker_finished(self):
        if self.file_worker:
            self.file_worker.deleteLater()
            self.file_worker = None
            
    @Slot(Image.Image)
    def on_hand_stopped(self, captured_image):
        if self.is_ai_task_running: return
        self.log_panel.add_log_message("手の停止を検知。AIによる声かけを実行します。")
        self.context_manager.set_triggered_image(captured_image)
        prompt = self.settings_manager.hand_stopped_prompt
        self.execute_ai_task(prompt, speak=True)

    @Slot(str)
    def on_monologue_recognized(self, text):
        if self.active_session_id:
            self.db_worker.add_log(self.active_session_id, "monologue", text)
        self.chat_panel.append_to_input(text)
        self.log_panel.add_log_message(f"独り言を認識: 「{text}」")

    @Slot(str)
    def on_command_recognized(self, command_text):
        self.log_panel.add_log_message(f"音声コマンドを認識: 「{command_text}」")
        if not self.active_session_id:
            self.tts_worker.speak("すみません、現在アクティブなセッションがありません。")
            return
        if not self.latest_camera_frame:
            self.tts_worker.speak("すみません、カメラの映像が取得できていません。")
            return
        self._request_add_message("user", f"（音声コマンド）{command_text}")
        self.context_manager.set_triggered_image(self.latest_camera_frame.copy())
        self.is_ai_task_running = True
        self.chat_panel.set_thinking_mode(True)
        long_term_context = self._get_long_term_context([])
        monologue_history = self.db_manager.get_recent_logs_for_session(self.active_session_id, "monologue", 5)
        prompt_parts = self.context_manager.build_prompt_parts_for_command(command_text, self.current_chat_messages, monologue_history, long_term_context)
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
        self.log_panel.add_log_message(f"定点観測: {observation_text}")

    @Slot(QImage, list)
    def update_camera_view(self, frame_qimage: QImage, detections: List[Dict]):
        if frame_qimage.isNull() or not self.camera_panel.isVisible():
            return
        pixmap = QPixmap.fromImage(frame_qimage)
        if detections:
            painter = QPainter()
            if not painter.begin(pixmap):
                print("QPainter.begin()に失敗しました。描画をスキップします。")
                self.camera_panel.set_pixmap(pixmap) # ペイントできなかった場合も画像は更新
                return
            try:
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
            finally:
                painter.end()
        self.camera_panel.set_pixmap(pixmap)
        if frame_qimage.constBits() is not None:
            buffer = frame_qimage.constBits().tobytes()
            self.latest_camera_frame = Image.frombytes("RGBA", (frame_qimage.width(), frame_qimage.height()), buffer, 'raw', "BGRA")

    def closeEvent(self, event):
        print("アプリケーションの終了処理を開始します...")
        if self.is_ai_task_running and self.ai_worker and self.ai_worker.isRunning():
            print("実行中のAIタスクの完了を待ちます...")
            self.ai_worker.wait(2000)
        
        print("UI関連以外のワーカースレッドを停止します...")
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
                CLOSING_TIMEOUT = 4
                
                kw_prompt_template = self.settings_manager.keyword_extraction_from_history_prompt
                kw_prompt = kw_prompt_template.format(conversation_text=conversation_text)
                print(" > キーワードを抽出中...")
                keywords_response = main_gemini_client.generate_response(kw_prompt, timeout=CLOSING_TIMEOUT)
                if "エラー" not in keywords_response and "ブロックされました" not in keywords_response:
                    match_kw = re.search(r'([\w\s、,]+)$', keywords_response, re.MULTILINE)
                    cleaned_keywords = match_kw.group(1).strip() if match_kw else keywords_response.strip()
                    self.db_manager.update_session_keywords(self.active_session_id, cleaned_keywords.replace("*", "").replace("`", ""))
                    print(f" > キーワードを保存しました: {cleaned_keywords}")

                title_prompt_template = self.settings_manager.title_generation_prompt
                title_prompt = title_prompt_template.format(conversation_text=conversation_text)
                print(" > タイトルを生成中...")
                title = main_gemini_client.generate_response(title_prompt, timeout=CLOSING_TIMEOUT)
                if "エラー" not in title and "ブロックされました" not in title:
                    cleaned_title = title.strip().replace('"', '').replace("'", "").replace("*", "")
                    self.db_manager.update_session_title(self.active_session_id, cleaned_title)
                    print(f" > タイトルを保存しました: {cleaned_title}")

                summary_prompt = f"""以下の会話履歴を、第三者の視点から重要なポイントを箇条書きで3〜5点にまとめてください。\n\n---\n{conversation_text}"""
                print(" > 要約を生成中...")
                summary = main_gemini_client.generate_response(summary_prompt, timeout=CLOSING_TIMEOUT)
                if "エラー" not in summary and "ブロックされました" not in summary and summary.strip():
                    self.db_manager.update_session_summary(self.active_session_id, summary)
                    print(" > 要約を保存しました。")

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
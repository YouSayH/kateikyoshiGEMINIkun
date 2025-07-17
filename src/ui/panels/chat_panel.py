# src/ui/panels/chat_panel.py

import os
from PySide6.QtCore import Signal, QSize
# --- ▼▼▼ ここを修正 ▼▼▼ ---
from PySide6.QtGui import QMovie, QTextCursor
# --- ▲▲▲ ここまで修正 ▲▲▲ ---
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel,
    QHBoxLayout, QCheckBox, QStackedLayout
)
from ..widgets.md_view import MarkdownView

class ChatPanel(QWidget):
    # --- このパネルが発信するシグナル ---
    message_sent = Signal(str)
    load_file_requested = Signal()
    stop_speech_requested = Signal()
    stt_toggled = Signal(bool)
    camera_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)

        # --- UIの構築 (main_windowから移動) ---
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        
        layout = QVBoxLayout(self)
        self.ai_output_view = MarkdownView()
        self.user_input = QTextEdit()
        self.send_button = QPushButton("送信")
        self.stt_enabled_checkbox = QCheckBox("音声認識")
        self.load_file_button = QPushButton("問題ファイルを読み込む")
        self.stop_speech_button = QPushButton("読み上げを停止")
        self.stop_speech_button.setVisible(False)
        self.camera_enabled_checkbox = QCheckBox("カメラを有効にする")

        # ローディング表示
        loading_widget = QWidget()
        loading_layout = QHBoxLayout(loading_widget)
        loading_layout.setContentsMargins(0, 5, 0, 5)
        loading_movie_label = QLabel()
        loading_gif_path = os.path.join(project_root, "assets", "loading.gif")
        if os.path.exists(loading_gif_path):
            self.movie = QMovie(loading_gif_path)
            loading_movie_label.setMovie(self.movie)
            self.movie.setScaledSize(QSize(25, 25))
        loading_text_label = QLabel("AIが考え中です...")
        loading_layout.addStretch()
        loading_layout.addWidget(loading_movie_label)
        loading_layout.addWidget(loading_text_label)
        loading_layout.addStretch()

        self.header_stack = QStackedLayout()
        self.header_stack.addWidget(QLabel("AIアシスタント"))
        self.header_stack.addWidget(loading_widget)

        # ボタン配置
        top_button_layout = QHBoxLayout()
        top_button_layout.addWidget(self.load_file_button)
        top_button_layout.addStretch()
        top_button_layout.addWidget(self.camera_enabled_checkbox)
        top_button_layout.addWidget(self.stt_enabled_checkbox)
        button_v_layout = QVBoxLayout()
        button_v_layout.addWidget(self.send_button)
        button_v_layout.addWidget(self.stop_speech_button)
        input_area_layout = QHBoxLayout()
        input_area_layout.addWidget(self.user_input)
        input_area_layout.addLayout(button_v_layout)

        # 全体のレイアウト
        layout.addLayout(top_button_layout)
        layout.addLayout(self.header_stack)
        layout.addWidget(self.ai_output_view, stretch=1)
        layout.addWidget(QLabel("質問や独り言を入力"))
        layout.addLayout(input_area_layout)

        # --- シグナルの中継 ---
        self.send_button.clicked.connect(self._on_send_clicked)
        self.load_file_button.clicked.connect(self.load_file_requested.emit)
        self.stop_speech_button.clicked.connect(self.stop_speech_requested.emit)
        self.stt_enabled_checkbox.toggled.connect(self.stt_toggled.emit)
        self.camera_enabled_checkbox.toggled.connect(self.camera_toggled.emit)
    
    def _on_send_clicked(self):
        """送信ボタンが押されたらテキストを取得してシグナルを発行"""
        text = self.user_input.toPlainText().strip()
        if text:
            self.message_sent.emit(text)
            self.user_input.clear()

    # --- MainWindowから呼び出されるためのメソッド群 ---
    def set_markdown(self, md_text: str):
        self.ai_output_view.set_markdown(md_text)

    def set_thinking_mode(self, thinking: bool):
        if thinking:
            self.header_stack.setCurrentIndex(1)
            if hasattr(self, 'movie'):
                self.movie.start()
            self.send_button.setEnabled(False)
        else:
            self.header_stack.setCurrentIndex(0)
            if hasattr(self, 'movie'):
                self.movie.stop()
            self.send_button.setEnabled(True)

    def show_stop_speech_button(self, show: bool):
        self.stop_speech_button.setVisible(show)

    def append_to_input(self, text: str):
        current_text = self.user_input.toPlainText()
        new_text = (current_text + " " + text) if current_text and not current_text.endswith(" ") else (current_text + text)
        self.user_input.setPlainText(new_text)
        self.user_input.moveCursor(QTextCursor.MoveOperation.End)

    def get_stt_checkbox_state(self) -> bool:
        return self.stt_enabled_checkbox.isChecked()
        
    def set_stt_checkbox_state(self, checked: bool):
        self.stt_enabled_checkbox.setChecked(checked)

    def get_camera_checkbox_state(self) -> bool:
        return self.camera_enabled_checkbox.isChecked()

    def set_camera_checkbox_state(self, checked: bool):
        self.camera_enabled_checkbox.setChecked(checked)
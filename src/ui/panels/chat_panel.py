# src/ui/panels/chat_panel.py

import os
from PySide6.QtCore import Signal, QSize, Qt
from PySide6.QtGui import QMovie, QTextCursor, QKeyEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel,
    QHBoxLayout, QCheckBox, QStackedLayout
)
from ..widgets.md_view import MarkdownView
from typing import List, Dict

# ▼▼▼ 変更点 1/3: 新しいカスタム入力ウィジェットを定義 ▼▼▼
class CustomInputArea(QTextEdit):
    """入力体験を向上させるためのカスタムQTextEdit"""
    send_triggered = Signal() # Ctrl+Enterが押されたことを通知するシグナル

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = [""] # 送信履歴（末尾は常に入力中のテキスト）
        self._history_index = 0
        
        self.setAcceptRichText(False) # プレーンテキストのみ許可
        self.setPlaceholderText("ここに質問を入力 (Ctrl+Enterで送信)")

        # 自動リサイズ機能のセットアップ
        self.textChanged.connect(self._update_height)
        font_metrics = self.fontMetrics()
        # 1行分の高さにパディングを加えたものを最小の高さとする
        self._min_height = font_metrics.height() + 15
        # 最大で6行分まで広がるように設定
        self._max_height = (font_metrics.height() * 6) + 15
        self.setFixedHeight(self._min_height)

    def _update_height(self):
        """テキストの内容に応じてウィジェットの高さを動的に変更する"""
        # ドキュメントの実際の高さにパディングを加える
        doc_height = self.document().size().height()
        target_height = int(doc_height + 10)
        
        # 最小と最大の高さの範囲内に収める
        final_height = max(self._min_height, min(target_height, self._max_height))
        self.setFixedHeight(final_height)

    def add_to_history(self, text: str):
        """送信したテキストを履歴に追加する"""
        if text:
            # 重複を避けて履歴に追加
            if text not in self._history:
                self._history.insert(-1, text) # 末尾の空文字列の前に追加
            self._history_index = len(self._history) - 1 # インデックスを最新にリセット
            self._history[-1] = "" # 入力中バッファをクリア

    def keyPressEvent(self, event: QKeyEvent):
        """キー入力をハンドリングする"""
        # --- 1. Ctrl+Enterでの送信機能 ---
        is_ctrl_enter = (event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return) and
                         event.modifiers() == Qt.KeyboardModifier.ControlModifier)
        if is_ctrl_enter:
            self.send_triggered.emit()
            return # イベントをここで処理完了

        # --- 2. 上下キーでの履歴呼び出し機能 ---
        # カーソルがテキストの先頭行にある時に上キーを押した場合
        if event.key() == Qt.Key.Key_Up and self.textCursor().blockNumber() == 0:
            self._navigate_history(-1)
            return
        
        # カーソルがテキストの最終行にある時に下キーを押した場合
        if event.key() == Qt.Key.Key_Down and self.textCursor().blockNumber() == self.document().blockCount() - 1:
            self._navigate_history(1)
            return

        # 上記以外のキー入力は、デフォルトのQTextEditの動作に任せる
        super().keyPressEvent(event)
    
    def _navigate_history(self, direction: int):
        """履歴リストを移動する"""
        # 現在の入力をバッファに保存
        if self._history_index == len(self._history) - 1:
            self._history[-1] = self.toPlainText()

        # インデックスを更新
        new_index = self._history_index + direction
        if 0 <= new_index < len(self._history):
            self._history_index = new_index
            self.setPlainText(self._history[self._history_index])
            self.moveCursor(QTextCursor.MoveOperation.End)


class ChatPanel(QWidget):
    # (シグナル定義は変更なし)
    message_sent = Signal(str)
    load_file_requested = Signal()
    stop_speech_requested = Signal()
    stt_toggled = Signal(bool)
    camera_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        
        layout = QVBoxLayout(self)
        self.ai_output_view = MarkdownView()
        # ▼▼▼ 変更点 2/3: 通常のQTextEditをカスタム版に置き換え ▼▼▼
        self.user_input = CustomInputArea()
        self.send_button = QPushButton("送信")
        self.stt_enabled_checkbox = QCheckBox("音声認識")
        self.load_file_button = QPushButton("問題ファイルを読み込む")
        self.stop_speech_button = QPushButton("読み上げを停止")
        self.stop_speech_button.setVisible(False)
        self.camera_enabled_checkbox = QCheckBox("カメラを有効にする")

        # (ローディング表示などは変更なし)
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
        layout.addLayout(top_button_layout)
        layout.addLayout(self.header_stack)
        layout.addWidget(self.ai_output_view, stretch=1)
        layout.addWidget(QLabel("質問や独り言を入力"))
        layout.addLayout(input_area_layout)

        # --- シグナルの中継 ---
        self.send_button.clicked.connect(self._on_send_clicked)
        # ▼▼▼ 変更点 3/3: カスタム入力欄からのシグナルも接続 ▼▼▼
        self.user_input.send_triggered.connect(self._on_send_clicked)
        
        self.load_file_button.clicked.connect(self.load_file_requested.emit)
        self.stop_speech_button.clicked.connect(self.stop_speech_requested.emit)
        self.stt_enabled_checkbox.toggled.connect(self.stt_toggled.emit)
        self.camera_enabled_checkbox.toggled.connect(self.camera_toggled.emit)
    
    def _on_send_clicked(self):
        """送信ボタンまたはCtrl+Enterで呼び出される"""
        text = self.user_input.toPlainText().strip()
        if text:
            self.message_sent.emit(text)
            self.user_input.add_to_history(text) # 履歴に追加
            self.user_input.clear()

    # --- MainWindowから呼び出されるためのメソッド群 (変更なし) ---
    def set_messages(self, messages: List[Dict[str, str]]):
        self.ai_output_view.set_messages(messages)

    def add_message(self, message: Dict, scroll: bool):
        self.ai_output_view.add_message(message, scroll)

    def set_thinking_mode(self, thinking: bool):
        if thinking:
            self.header_stack.setCurrentIndex(1)
            if hasattr(self, 'movie'): self.movie.start()
            self.send_button.setEnabled(False)
        else:
            self.header_stack.setCurrentIndex(0)
            if hasattr(self, 'movie'): self.movie.stop()
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
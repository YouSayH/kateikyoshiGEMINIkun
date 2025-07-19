# src/ui/panels/log_panel.py (新規作成)

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PySide6.QtCore import Slot
from datetime import datetime

class LogPanel(QWidget):
    """
    システムログを表示するための専用パネル。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # マージンを詰める
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        # 横スクロールバーが表示されるように変更
        self.log_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.log_display)

    @Slot(str)
    def add_log_message(self, message: str):
        """タイムスタンプ付きでログメッセージを追記する"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_display.append(f"[{timestamp}] {message}")
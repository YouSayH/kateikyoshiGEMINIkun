# src/ui/panels/context_panel.py (新規作成)

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QGroupBox, QPushButton, QMessageBox
from PySide6.QtCore import Slot, Signal

class ContextPanel(QWidget):
    """
    現在の主題と会話要約を表示・編集するためのパネル。
    """
    # 編集された内容をMainWindowに通知するためのシグナル
    context_saved = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- UI要素の作成 ---
        # 1. 問題コンテキスト（主題）エリア
        problem_group = QGroupBox("現在の主題（ファイル分析結果）")
        problem_layout = QVBoxLayout(problem_group)
        self.problem_context_display = QTextEdit()
        # 編集可能にする
        self.problem_context_display.setReadOnly(False) 
        problem_layout.addWidget(self.problem_context_display)
        
        # 2. 会話要約エリア
        summary_group = QGroupBox("現在の会話の要約")
        summary_layout = QVBoxLayout(summary_group)
        self.chat_summary_display = QTextEdit()
        # 編集可能にする
        self.chat_summary_display.setReadOnly(False)
        summary_layout.addWidget(self.chat_summary_display)

        # 3. 保存ボタン
        self.save_button = QPushButton("編集内容を保存")

        # --- レイアウトへの追加 ---
        main_layout.addWidget(problem_group)
        main_layout.addWidget(summary_group)
        main_layout.addWidget(self.save_button)
        main_layout.addStretch() # ボタンが下に詰まるようにする

        # --- シグナル接続 ---
        self.save_button.clicked.connect(self._on_save_clicked)

    def _on_save_clicked(self):
        """保存ボタンがクリックされたときの処理"""
        problem_text = self.problem_context_display.toPlainText()
        summary_text = self.chat_summary_display.toPlainText()
        
        # シグナルを発信してMainWindowに処理を依頼
        self.context_saved.emit(problem_text, summary_text)
        
        # ユーザーへのフィードバック
        QMessageBox.information(self, "保存完了", "コンテキスト情報を更新しました。")

    @Slot(str)
    def update_problem_context(self, context: str):
        """主題コンテキスト表示を更新する"""
        self.problem_context_display.setPlainText(context or "まだ問題は読み込まれていません。")

    @Slot(str)
    def update_chat_summary(self, summary: str):
        """会話要約表示を更新する"""
        self.chat_summary_display.setPlainText(summary or "まだ会話の要約はありません。")
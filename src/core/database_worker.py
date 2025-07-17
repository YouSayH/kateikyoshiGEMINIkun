# src/core/database_worker.py　スレッド名自動設定

from PySide6.QtCore import QThread, Signal, Slot
from typing import Any
from .database_manager import DatabaseManager

class DatabaseWorker(QThread):
    """
    データベースへの書き込み処理を非同期で実行するための専用ワーカー。
    UIスレッドのブロックを防ぐ。
    """
    error = Signal(str)

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        # 実行したいタスク（(関数, 引数タプル, キーワード引数辞書)）を保持するキュー
        self.tasks: list[tuple[callable, tuple, dict]] = []
        self._is_running = True

    def run(self):
        """キューにタスクがあれば順番に実行する"""
        while self._is_running:
            if self.tasks:
                func, args, kwargs = self.tasks.pop(0)
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    error_message = f"データベース書き込みエラー: {e}"
                    print(error_message)
                    self.error.emit(error_message)
            else:
                self.msleep(100) # タスクがなければCPU負荷軽減のために待機

    @Slot(int, str, str)
    def add_message(self, session_id: int, role: str, content: str):
        """メッセージ追加タスクをキューに入れる"""
        self.tasks.append((self.db_manager.add_message, (session_id, role, content), {}))

    @Slot(int, str, str)
    def add_log(self, session_id: int, log_type: str, content: str):
        """ログ追加タスクをキューに入れる"""
        self.tasks.append((self.db_manager.add_log, (session_id, log_type, content), {}))

    @Slot(int, str)
    def update_problem_context(self, session_id: int, context: str):
        """問題コンテキスト更新タスクをキューに入れる"""
        self.tasks.append((self.db_manager.update_problem_context, (session_id, context), {}))

    @Slot(int, str)
    def update_session_keywords(self, session_id: int, keywords: str):
        """キーワード更新タスクをキューに入れる"""
        self.tasks.append((self.db_manager.update_session_keywords, (session_id, keywords), {}))

    @Slot(int, str)
    def update_session_title(self, session_id: int, new_title: str):
        """セッションタイトル更新タスクをキューに入れる"""
        self.tasks.append((self.db_manager.update_session_title, (session_id, new_title), {}))

    def stop(self):
        """スレッドを安全に停止させる"""
        print("データベースワーカーを停止します...")
        self._is_running = False
        # wait()は呼び出し元のMainWindowで行う
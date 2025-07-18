import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

class DatabaseManager:
    """
    SQLiteデータベースの操作をカプセル化するクラス。
    時間的コンテキストの取得やキーワード検索、タイトル更新機能も含む。
    """
    def __init__(self, db_path: str):
        """
        データベースへの接続と、初期テーブルの作成・マイグレーションを行う。
        :param db_path: データベースファイルのパス (例: 'data/sessions.db')
        """
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"ディレクトリを作成しました: {db_dir}")

        self.db_path = db_path
        self._initialize_database()

    def _get_connection(self) -> sqlite3.Connection:
        """データベース接続を取得する"""
        return sqlite3.connect(self.db_path)

    def _initialize_database(self):
        """データベースとテーブルの初期化、およびマイグレーション（カラム追加など）を行う"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # --- sessions テーブルの作成とマイグレーション ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            problem_context TEXT,
            chat_summary TEXT
        )
        """)
        
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'last_updated_at' not in columns:
            cursor.execute("ALTER TABLE sessions ADD COLUMN last_updated_at TEXT DEFAULT '1970-01-01 00:00:00'")
            cursor.execute("UPDATE sessions SET last_updated_at = created_at")

        if 'keywords' not in columns:
            cursor.execute("ALTER TABLE sessions ADD COLUMN keywords TEXT DEFAULT ''")

        # --- messages テーブルの作成 ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'ai')),
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        )
        """)
        
        # --- logs テーブルの作成 ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            log_type TEXT NOT NULL CHECK(log_type IN ('monologue', 'observation')),
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        )
        """)
        
        conn.commit()
        conn.close()
        print("データベーステーブルの初期化（キーワードカラム含む）を確認・完了しました。")

    def _update_session_timestamp(self, session_id: int):
        """指定されたセッションの最終更新日時を現在時刻に更新する"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET last_updated_at = ? WHERE id = ?", (now, session_id))
        conn.commit()
        conn.close()

    def create_new_session(self, title: Optional[str] = None) -> int:
        """新しいチャットセッションを作成し、そのIDを返す"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if title is None:
            title = f"チャット - {now}"
        
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (title, created_at, last_updated_at, keywords) VALUES (?, ?, ?, ?)",
            (title, now, now, "")
        )
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        print(f"新しいセッションを作成しました (ID: {session_id}, Title: {title})")
        return session_id

    def get_all_sessions(self) -> List[Tuple[int, str]]:
        """すべてのセッションを (id, title) のリストで取得する（最終更新日時が新しい順）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM sessions ORDER BY last_updated_at DESC")
        sessions = cursor.fetchall()
        conn.close()
        return sessions

    def add_message(self, session_id: int, role: str, content: str):
        """指定されたセッションに新しいメッセージを追加する"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, role, content, now)
        )
        conn.commit()
        conn.close()
        self._update_session_timestamp(session_id)
        
    def add_log(self, session_id: int, log_type: str, content: str):
        """独り言や定点観測ログをDBに保存する"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO logs (session_id, log_type, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, log_type, content, now)
        )
        conn.commit()
        conn.close()
        self._update_session_timestamp(session_id)

    def get_messages_for_session(self, session_id: int) -> List[Dict[str, str]]:
        """指定されたセッションの全メッセージを取得する"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
        messages = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
        conn.close()
        return messages

    def update_problem_context(self, session_id: int, context: str):
        """指定されたセッションの問題コンテキストを更新する"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET problem_context = ? WHERE id = ?", (context, session_id))
        conn.commit()
        conn.close()
        self._update_session_timestamp(session_id)

    def get_session_details(self, session_id: int) -> Optional[Dict[str, any]]:
        """指定されたセッションの詳細情報を辞書で取得する"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_last_active_session_id(self, exclude_session_id: Optional[int] = None) -> Optional[int]:
        """指定されたIDを除き、最も最近更新されたセッションのIDを取得する"""
        conn = self._get_connection()
        cursor = conn.cursor()
        query = "SELECT id FROM sessions"
        params = []
        if exclude_session_id is not None:
            query += " WHERE id != ?"
            params.append(exclude_session_id)
        query += " ORDER BY last_updated_at DESC LIMIT 1"
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_recent_logs_for_session(self, session_id: int, log_type: str, minutes: int) -> List[str]:
        """指定されたセッションの直近N分間の特定の種類のログを取得する"""
        conn = self._get_connection()
        cursor = conn.cursor()
        time_threshold = (datetime.now() - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("SELECT content FROM logs WHERE session_id = ? AND log_type = ? AND timestamp >= ? ORDER BY timestamp ASC", (session_id, log_type, time_threshold))
        logs = [row[0] for row in cursor.fetchall()]
        conn.close()
        return logs

    def update_session_keywords(self, session_id: int, keywords: str):
        """指定されたセッションのキーワードを更新する"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET keywords = ? WHERE id = ?", (keywords, session_id))
        conn.commit()
        conn.close()
        print(f"セッションID {session_id} のキーワードを更新しました: {keywords}")

    def find_relevant_sessions(self, query_keywords: List[str], exclude_session_id: int, limit: int = 3) -> List[Dict[str, any]]:
        """クエリキーワードに最も関連する過去のセッションを、関連度順に複数取得する"""
        if not query_keywords:
            return []
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, keywords, last_updated_at FROM sessions WHERE id != ?", (exclude_session_id,))
        all_past_sessions = cursor.fetchall()
        if not all_past_sessions:
            conn.close()
            return []
        scored_sessions = []
        query_kw_set = {kw.strip() for kw in query_keywords if kw.strip()}
        for session_row in all_past_sessions:
            session_keywords = {kw.strip() for kw in session_row["keywords"].split(',') if kw.strip()}
            common_keywords = query_kw_set.intersection(session_keywords)
            score = len(common_keywords)
            if score > 0:
                scored_sessions.append((dict(session_row), score))
        scored_sessions.sort(key=lambda x: x[1], reverse=True)
        conn.close()
        return [session for session, score in scored_sessions[:limit]]

    def update_session_title(self, session_id: int, new_title: str):
        """指定されたセッションのタイトルを更新する"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET title = ? WHERE id = ?", (new_title, session_id))
        conn.commit()
        conn.close()
        print(f"セッションID {session_id} のタイトルを更新しました: {new_title}")

    def update_session_summary(self, session_id: int, summary: str):
        """指定されたセッションの会話要約を更新する"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET chat_summary = ? WHERE id = ?", (summary, session_id))
        conn.commit()
        conn.close()
        print(f"セッションID {session_id} の要約を更新しました。")
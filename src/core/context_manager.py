from typing import List, Dict, Optional, Any
from PIL import Image

class ContextManager:
    """
    【アクティブなセッション】のコンテキスト情報を一時的に保持し、
    プロンプトを生成する役割に特化したクラス。
    永続的なデータはDatabaseManagerが管理する。
    """
    def __init__(self):
        self.problem_context_text: str = "まだ問題は読み込まれていません。"
        self.triggered_image: Optional[Image.Image] = None
        self.chat_summary: str = "まだ会話はありません。"
        
    def set_problem_context(self, context_text: str):
        """アクティブなセッションの問題コンテキストを（メモリ上に）設定する"""
        self.problem_context_text = context_text if context_text else "まだ問題は読み込まれていません。"

    def set_triggered_image(self, image: Image.Image):
        """トリガーの瞬間の画像を（メモリ上に）保存する"""
        self.triggered_image = image

    def set_chat_summary(self, summary: str):
        """アクティブなセッションの会話要約を（メモリ上に）設定する"""
        self.chat_summary = summary if summary else "まだ会話はありません。"

    def build_prompt_for_query(self, user_query: str, chat_history: List[Dict], monologue_history: List[str], observation_log: List[str], long_term_context: str) -> str:
        """
        ユーザーからの質問応答のため、DBから取得した情報と現在の状態を統合してプロンプトを生成する。
        """
        
        history_str = "\n".join([f"- {msg['role']}: {msg['content']}" for msg in chat_history])
        monologue_str = "\n".join([f"- {m}" for m in monologue_history]) or "なし"
        observation_str = "\n".join([f"- {o}" for o in observation_log]) or "なし"

        return f"""あなたは、ユーザーの長期的な学習履歴も理解している、パーソナルな家庭教師AIです。

# 応答形式のルール
- 応答は必ずMarkdown形式で記述してください。
- 見出し（`###`）、太字（`**...**`）、箇条書き（`- ...`）などを活用し、視覚的に分かりやすい説明を心がけてください。
- 数式は、ディスプレイ数式なら `$$ ... $$`、インライン数式なら `$...$` を使って記述してください。
- コードや計算過程など、数式ではないが整形して見せたいテキストは、インラインコード（`...`）やコードブロック（```...```）を使用できます。
- 重要: コードブロックの中に数式を記述しないでください。数式は必ず独立させてください。

# 長期的な学習状況（長期記憶）
{long_term_context}

# 現在のセッションの状況（短期記憶）
## ユーザーが取り組んでいる問題
{self.problem_context_text}
## これまでの会話の要約
{self.chat_summary}
## ユーザーの最近の様子（システムによる定点観測）
{observation_str}
## ユーザーの最近の独り言（音声認識より）
{monologue_str}
## 直近の会話（最後の5往復程度）
{history_str}

# ユーザーからの現在の質問
「{user_query}」

# あなたのタスク
上記のすべての情報を統合し、ユーザーの思考プロセスや詰まっている点を深く推察してください。
その上で、単なる答えではなく、ユーザーが「なるほど！」と気づきを得られるような、核心を突いたヒントや別の視点を提供してください。
"""

    def build_prompt_parts_for_command(self, user_command: str, chat_history: List[Dict], monologue_history: List[str], long_term_context: str) -> Optional[List[Any]]:
        """
        音声コマンドに応答するため、テキストと画像を組み合わせたプロンプトパーツを生成する。
        """
        if self.triggered_image is None:
            print("エラー: コマンド用のトリガー画像が設定されていません。")
            return None

        history_str = "\n".join([f"- {msg['role']}: {msg['content']}" for msg in chat_history])
        monologue_str = "\n".join([f"- {m}" for m in monologue_history]) or "なし"

        text_prompt = f"""
あなたは、ユーザーの状況を深く理解する家庭教師AIです。
ユーザーから「{user_command}」という音声コマンドを受け取りました。
添付されている画像は、そのコマンドが発せられた瞬間のユーザーの机の様子です。

# 応答形式のルール
- 応答は必ずMarkdown形式で記述してください。
- 数式は$$...$$や$...$で囲んでください。

# 参考情報
- **長期的な学習状況:** {long_term_context}
- **ユーザーが取り組んでいる問題の概要:** {self.problem_context_text}
- **これまでの会話の要約:** {self.chat_summary}
- **直近の独り言:** {monologue_str}
- **直近の会話:** {history_str}

# あなたのタスク
添付された画像と上記の参考情報を最優先で分析し、ユーザーの意図を汲み取って、コマンドに的確に応答してください。
"""
        return [text_prompt, self.triggered_image]
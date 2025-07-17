# src/core/context_manager.py (最終版)データベースによる時間的情報の追加2
# (変更点は build_prompt_parts_for_command のみ)

from typing import List, Dict, Optional, Any
from PIL import Image

class ContextManager:
    def __init__(self):
        self.problem_context_text: str = "まだ問題は読み込まれていません。"
        self.triggered_image: Optional[Image.Image] = None
    def set_problem_context(self, context_text: str): self.problem_context_text = context_text if context_text else "まだ問題は読み込まれていません。"
    def set_triggered_image(self, image: Image.Image): self.triggered_image = image

    def build_prompt_for_query(self, user_query: str, chat_history: List[Dict], monologue_history: List[str], observation_log: List[str], long_term_context: str) -> str:
        history_str = "\n".join([f"- {msg['role']}: {msg['content']}" for msg in chat_history])
        monologue_str = "\n".join([f"- {m}" for m in monologue_history]) or "なし"
        observation_str = "\n".join([f"- {o}" for o in observation_log]) or "なし"
        return f"""あなたは、ユーザーの長期的な学習履歴も理解している、パーソナルな家庭教師AIです。\n\n# 応答形式のルール\n- 応答は必ずMarkdown形式で記述してください。\n- 見出し（`###`）、太字（`**...**`）、箇条書き（`- ...`）などを活用し、視覚的に分かりやすい説明を心がけてください。\n- **数式**は、ディスプレイ数式なら `$$ ... $$`、インライン数式なら `$...$` を使って記述してください。\n- **コードや計算過程**など、数式ではないが整形して見せたいテキストは、インラインコード（`...`）やコードブロック（```...```）を使用できます。\n- **重要:** コードブロックの中に数式を記述しないでください。数式は必ず独立させてください。\n\n# 長期的な学習状況（長期記憶）\n{long_term_context}\n\n# 現在のセッションの状況（短期記憶）\n## ユーザーが取り組んでいる問題\n{self.problem_context_text}\n## ユーザーの最近の様子（システムによる定点観測）\n{observation_str}\n## ユーザーの最近の独り言（音声認識より）\n{monologue_str}\n## 直近の会話\n{history_str}\n\n# ユーザーからの現在の質問\n「{user_query}」\n\n# あなたのタスク\n上記のすべての情報を統合し、ユーザーの思考プロセスや詰まっている点を深く推察してください。その上で、単なる答えではなく、ユーザーが「なるほど！」と気づきを得られるような、核心を突いたヒントや別の視点を提供してください。"""

    def build_prompt_parts_for_command(self, user_command: str, chat_history: List[Dict], monologue_history: List[str], long_term_context: str) -> Optional[List[Any]]:
        if self.triggered_image is None: return None
        history_str = "\n".join([f"- {msg['role']}: {msg['content']}" for msg in chat_history])
        monologue_str = "\n".join([f"- {m}" for m in monologue_history]) or "なし"
        text_prompt = f"""あなたは、ユーザーの状況を深く理解する家庭教師AIです。\nユーザーから「{user_command}」という音声コマンドを受け取りました。\n添付されている画像は、そのコマンドが発せられた瞬間のユーザーの机の様子です。\n\n# 応答形式のルール\n- 応答は必ずMarkdown形式で記述してください。\n- 数式は$$...$$や$...$で囲んでください。\n\n# 参考情報\n- **長期的な学習状況:** {long_term_context}\n- **ユーザーが取り組んでいる問題の概要:** {self.problem_context_text}\n- **直近の独り言:** {monologue_str}\n- **直近の会話:** {history_str}\n\n# あなたのタスク\n添付された画像と上記の参考情報を最優先で分析し、ユーザーの意図を汲み取って、コマンドに的確に応答してください。"""
        return [text_prompt, self.triggered_image]
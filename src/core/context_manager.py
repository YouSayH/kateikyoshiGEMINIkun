# # # # # src/core/context_manager.py

# # # # from typing import List, Dict, Optional, Any
# # # # from PIL import Image

# # # # class ContextManager:
# # # #     """
# # # #     アプリケーションの記憶（問題、会話、視覚情報など）を一元管理し、
# # # #     状況に応じた最適なプロンプトを生成するクラス。
# # # #     """
# # # #     def __init__(self):
# # # #         self.problem_context_text: str = "まだ問題は読み込まれていません。"
# # # #         self.triggered_image: Optional[Image.Image] = None
# # # #         self.chat_summary: str = "まだ会話はありません。"
# # # #         self.chat_history: List[Dict[str, str]] = []
# # # #         self.monologue_history: List[str] = []
# # # #         self.observation_log: List[str] = []

# # # #     def set_problem_context(self, context_text: str):
# # # #         self.problem_context_text = context_text
# # # #         print(f"新しい問題コンテキストが設定されました: {context_text[:70]}...")

# # # #     def set_triggered_image(self, image: Image.Image):
# # # #         self.triggered_image = image
# # # #         print("トリガー時の画像がキャプチャされました。")

# # # #     def update_chat_summary(self, summary: str):
# # # #         self.chat_summary = summary
# # # #         print("会話の要約が更新されました。")
        
# # # #     def add_chat_message(self, role: str, content: str):
# # # #         self.chat_history.append({"role": role, "content": content})
# # # #         if len(self.chat_history) > 10:
# # # #             self.chat_history.pop(0)

# # # #     def add_monologue(self, text: str):
# # # #         self.monologue_history.append(text)
# # # #         print(f"独り言を記録しました: {text}")
# # # #         if len(self.monologue_history) > 10:
# # # #             self.monologue_history.pop(0)

# # # #     def add_observation(self, observation: str):
# # # #         self.observation_log.append(observation)
# # # #         print(f"定点観測ログを追加しました: {observation}")
# # # #         if len(self.observation_log) > 5:
# # # #             self.observation_log.pop(0)

# # # #     def get_full_chat_history_md(self) -> str:
# # # #         full_md_text = ""
# # # #         for message in self.chat_history:
# # # #             role_display = "あなた" if message["role"] == "user" else "AIアシスタント"
# # # #             full_md_text += f"**{role_display}:**\n\n{message['content']}\n\n<hr>\n\n"
# # # #         return full_md_text

# # # #     def build_prompt_for_query(self, user_query: str) -> str:
# # # #         history_str = "\n".join([f"- {msg['role']}: {msg['content']}" for msg in self.chat_history])
# # # #         monologue_str = "\n".join([f"- {m}" for m in self.monologue_history]) or "なし"
# # # #         observation_str = "\n".join([f"- {o}" for o in self.observation_log]) or "なし"
# # # #         return f"""
# # # # あなたは、ユーザーの隣で思考を深く理解し、優しくサポートする家庭教師AIです。

# # # # # 現在の全体状況
# # # # ## ユーザーが取り組んでいる問題
# # # # {self.problem_context_text}
# # # # ## これまでの会話の要約
# # # # {self.chat_summary}
# # # # ## ユーザーの最近の様子（システムによる定点観測）
# # # # {observation_str}
# # # # ## ユーザーの最近の独り言（音声認識より）
# # # # {monologue_str}
# # # # ## 直近の会話
# # # # {history_str}

# # # # # ユーザーからの現在の質問
# # # # 「{user_query}」

# # # # # あなたのタスク
# # # # 上記のすべての情報を統合し、ユーザーの思考プロセスや詰まっている点を深く推察してください。
# # # # その上で、単なる答えではなく、ユーザーが「なるほど！」と気づきを得られるような、核心を突いたヒントや別の視点を提供してください。
# # # # 応答はMarkdown形式で、数式は$$...$$や$..$で囲んでください。
# # # # """

# # # #     def build_prompt_parts_for_command(self, user_command: str) -> Optional[List[Any]]:
# # # #         """
# # # #         音声コマンドに応答するため、テキストと画像を組み合わせたプロンプトパーツを生成する。
# # # #         """
# # # #         if self.triggered_image is None:
# # # #             print("エラー: コマンド用のトリガー画像が設定されていません。")
# # # #             return None

# # # #         text_prompt = f"""
# # # # あなたは、ユーザーの状況を深く理解する家庭教師AIです。
# # # # ユーザーから「{user_command}」という音声コマンドを受け取りました。
# # # # 添付されている画像は、そのコマンドが発せられた瞬間のユーザーの机の様子です。

# # # # # 参考情報
# # # # - **ユーザーが取り組んでいる問題の概要:** {self.problem_context_text}
# # # # - **直近の独り言:** {" ".join(self.monologue_history) or "なし"}
# # # # - **これまでの会話の要約:** {self.chat_summary}

# # # # # あなたのタスク
# # # # 添付された画像と上記の参考情報を最優先で分析し、ユーザーの意図を汲み取って、コマンドに的確に応答してください。
# # # # 例えば、画像の中で特定の部分を指差していたり、手書きのメモがあれば、それも考慮に入れてください。
# # # # 可能な限り、ユーザーが自力で解決できるように導くヒントや考え方を中心に、励ましながら応答するのが理想です。
# # # # """
# # # #         return [text_prompt, self.triggered_image]





# # # # src/core/context_manager.py数式の表示のためにプロンプト修正

# # # from typing import List, Dict, Optional, Any
# # # from PIL import Image

# # # class ContextManager:
# # #     # __init__ や他のメソッドは変更なし...
# # #     def __init__(self):
# # #         self.problem_context_text: str = "まだ問題は読み込まれていません。"
# # #         self.triggered_image: Optional[Image.Image] = None
# # #         self.chat_summary: str = "まだ会話はありません。"
# # #         self.chat_history: List[Dict[str, str]] = []
# # #         self.monologue_history: List[str] = []
# # #         self.observation_log: List[str] = []
# # #     def set_problem_context(self, context_text: str): self.problem_context_text = context_text; print(f"新しい問題コンテキスト...: {context_text[:70]}...")
# # #     def set_triggered_image(self, image: Image.Image): self.triggered_image = image; print("トリガー時の画像がキャプチャされました。")
# # #     def update_chat_summary(self, summary: str): self.chat_summary = summary; print("会話の要約が更新されました。")
# # #     def add_chat_message(self, role: str, content: str): self.chat_history.append({"role": role, "content": content}); (self.chat_history.pop(0) if len(self.chat_history) > 10 else None)
# # #     def add_monologue(self, text: str): self.monologue_history.append(text); print(f"独り言を記録: {text}"); (self.monologue_history.pop(0) if len(self.monologue_history) > 10 else None)
# # #     def add_observation(self, observation: str): self.observation_log.append(observation); print(f"定点観測ログを追加: {observation}"); (self.observation_log.pop(0) if len(self.observation_log) > 5 else None)
# # #     def get_full_chat_history_md(self) -> str:
# # #         full_md_text = "";
# # #         for message in self.chat_history:
# # #             role_display = "あなた" if message["role"] == "user" else "AIアシスタント"
# # #             full_md_text += f"**{role_display}:**\n\n{message['content']}\n\n<hr>\n\n"
# # #         return full_md_text

# # #     # --- ここからプロンプトを修正 ---

# # #     def build_prompt_for_query(self, user_query: str) -> str:
# # #         history_str = "\n".join([f"- {msg['role']}: {msg['content']}" for msg in self.chat_history])
# # #         monologue_str = "\n".join([f"- {m}" for m in self.monologue_history]) or "なし"
# # #         observation_str = "\n".join([f"- {o}" for o in self.observation_log]) or "なし"
# # #         return f"""
# # # あなたは、ユーザーの隣で思考を深く理解し、優しくサポートする家庭教師AIです。

# # # # 応答形式のルール
# # # - 応答は必ずMarkdown形式で記述してください。
# # # - **最重要: 数式は、ディスプレイ数式なら `$$ ... $$`、インライン数式なら `$...$` を使って記述してください。**
# # # - **警告: 数式を絶対にバッククォート(`)やコードブロック(```)で囲まないでください。**

# # # # 現在の全体状況
# # # ## ユーザーが取り組んでいる問題
# # # {self.problem_context_text}
# # # ## これまでの会話の要約
# # # {self.chat_summary}
# # # ## ユーザーの最近の様子（システムによる定点観測）
# # # {observation_str}
# # # ## ユーザーの最近の独り言（音声認識より）
# # # {monologue_str}
# # # ## 直近の会話
# # # {history_str}

# # # # ユーザーからの現在の質問
# # # 「{user_query}」

# # # # あなたのタスク
# # # 上記のすべての情報を統合し、ユーザーの思考プロセスや詰まっている点を深く推察してください。
# # # その上で、単なる答えではなく、ユーザーが「なるほど！」と気づきを得られるような、核心を突いたヒントや別の視点を提供してください。
# # # """

# # #     def build_prompt_parts_for_command(self, user_command: str) -> Optional[List[Any]]:
# # #         if self.triggered_image is None:
# # #             print("エラー: コマンド用のトリガー画像が設定されていません。")
# # #             return None

# # #         text_prompt = f"""
# # # あなたは、ユーザーの状況を深く理解する家庭教師AIです。
# # # ユーザーから「{user_command}」という音声コマンドを受け取りました。
# # # 添付されている画像は、そのコマンドが発せられた瞬間のユーザーの机の様子です。

# # # # 応答形式のルール
# # # - 応答は必ずMarkdown形式で記述してください。
# # # - **最重要: 数式は、ディスプレイ数式なら `$$ ... $$`、インライン数式なら `$...$` を使って記述してください。**
# # # - **警告: 数式を絶対にバッククォート(`)やコードブロック(```)で囲まないでください。**

# # # # 参考情報
# # # - **ユーザーが取り組んでいる問題の概要:** {self.problem_context_text}
# # # - **直近の独り言:** {" ".join(self.monologue_history) or "なし"}
# # # - **これまでの会話の要約:** {self.chat_summary}

# # # # あなたのタスク
# # # 添付された画像と上記の参考情報を最優先で分析し、ユーザーの意図を汲み取って、コマンドに的確に応答してください。
# # # 例えば、画像の中で特定の部分を指差していたり、手書きのメモがあれば、それも考慮に入れてください。
# # # ユーザーの要望があれば、問題の答えの出力、その解説、ユーザーの意図に沿った回答を心がけてください。
# # # また、補足などがあるといいですね。
# # # """
# # #         return [text_prompt, self.triggered_image]


















# # # src/core/context_manager.pyマークダウンの見やすさと数式の表示の両立

# # from typing import List, Dict, Optional, Any
# # from PIL import Image

# # class ContextManager:
# #     # (他のメソッドは変更なし)
# #     def __init__(self):
# #         self.problem_context_text: str = "まだ問題は読み込まれていません。"
# #         self.triggered_image: Optional[Image.Image] = None
# #         self.chat_summary: str = "まだ会話はありません。"
# #         self.chat_history: List[Dict[str, str]] = []
# #         self.monologue_history: List[str] = []
# #         self.observation_log: List[str] = []
# #     def set_problem_context(self, context_text: str): self.problem_context_text = context_text; print(f"新しい問題コンテキスト...: {context_text[:70]}...")
# #     def set_triggered_image(self, image: Image.Image): self.triggered_image = image; print("トリガー時の画像がキャプチャされました。")
# #     def update_chat_summary(self, summary: str): self.chat_summary = summary; print("会話の要約が更新されました。")
# #     def add_chat_message(self, role: str, content: str): self.chat_history.append({"role": role, "content": content}); (self.chat_history.pop(0) if len(self.chat_history) > 10 else None)
# #     def add_monologue(self, text: str): self.monologue_history.append(text); print(f"独り言を記録: {text}"); (self.monologue_history.pop(0) if len(self.monologue_history) > 10 else None)
# #     def add_observation(self, observation: str): self.observation_log.append(observation); print(f"定点観測ログを追加: {observation}"); (self.observation_log.pop(0) if len(self.observation_log) > 5 else None)
# #     def get_full_chat_history_md(self) -> str:
# #         full_md_text = "";
# #         for message in self.chat_history:
# #             role_display = "あなた" if message["role"] == "user" else "AIアシスタント"
# #             full_md_text += f"**{role_display}:**\n\n{message['content']}\n\n<hr>\n\n"
# #         return full_md_text
    
# #     # --- ここからプロンプトを修正 ---

# #     def build_prompt_for_query(self, user_query: str) -> str:
# #         history_str = "\n".join([f"- {msg['role']}: {msg['content']}" for msg in self.chat_history])
# #         monologue_str = "\n".join([f"- {m}" for m in self.monologue_history]) or "なし"
# #         observation_str = "\n".join([f"- {o}" for o in self.observation_log]) or "なし"
# #         return f"""
# # あなたは、ユーザーの隣で思考を深く理解し、優しくサポートする家庭教師AIです。

# # # 応答形式のルール
# # - 応答は必ずMarkdown形式で記述してください。
# # - 見出し（`###`）、太字（`**...**`）、箇条書き（`- ...`）などを活用し、視覚的に分かりやすい説明を心がけてください。
# # - **数式**は、ディスプレイ数式なら `$$ ... $$`、インライン数式なら `$...$` を使って記述してください。
# # - **コードや計算過程**など、数式ではないが整形して見せたいテキストは、インラインコード（`...`）やコードブロック（```...```）を使用できます。
# # - **重要:** コードブロックの中に数式を記述しないでください。数式は必ず独立させてください。

# # # 現在の全体状況
# # ## ユーザーが取り組んでいる問題
# # {self.problem_context_text}
# # ## これまでの会話の要約
# # {self.chat_summary}
# # ## ユーザーの最近の様子（システムによる定点観測）
# # {observation_str}
# # ## ユーザーの最近の独り言（音声認識より）
# # {monologue_str}
# # ## 直近の会話
# # {history_str}

# # # ユーザーからの現在の質問
# # 「{user_query}」

# # # あなたのタスク
# # 上記のすべての情報を統合し、ユーザーの思考プロセスや詰まっている点を深く推察してください。
# # その上で、単なる答えではなく、ユーザーが「なるほど！」と気づきを得られるような、核心を突いたヒントや別の視点を提供してください。
# # """

# #     def build_prompt_parts_for_command(self, user_command: str) -> Optional[List[Any]]:
# #         if self.triggered_image is None: return None

# #         text_prompt = f"""
# # あなたは、ユーザーの状況を深く理解する家庭教師AIです。
# # ユーザーから「{user_command}」という音声コマンドを受け取りました。
# # 添付されている画像は、そのコマンドが発せられた瞬間のユーザーの机の様子です。

# # # 応答形式のルール
# # - 応答は必ずMarkdown形式で記述してください。
# # - 見出し（`###`）、太字（`**...**`）、箇条書き（`- ...`）などを活用し、視覚的に分かりやすい説明を心がけてください。
# # - **数式**は、ディスプレイ数式なら `$$ ... $$`、インライン数式なら `$...$` を使って記述してください。
# # - **コードや計算過程**など、数式ではないが整形して見せたいテキストは、インラインコード（`...`）やコードブロック（```...```）を使用できます。
# # - **重要:** コードブロックの中に数式を記述しないでください。数式は必ず独立させてください。

# # # 参考情報
# # - **ユーザーが取り組んでいる問題の概要:** {self.problem_context_text}
# # - **直近の独り言:** {" ".join(self.monologue_history) or "なし"}
# # - **これまでの会話の要約:** {self.chat_summary}

# # # あなたのタスク
# # 添付された画像と上記の参考情報を最優先で分析し、ユーザーの意図を汲み取って、コマンドに的確に応答してください。
# # 例えば、画像の中で特定の部分を指差していたり、手書きのメモがあれば、それも考慮に入れてください。
# # ユーザーの要望があれば、問題の答えの出力、その解説、ユーザーの意図に沿った回答を心がけてください。
# # また、補足などがあるといいですね。
# # """
# #         return [text_prompt, self.triggered_image]

















# # src/core/context_manager.py データベースの実装による時間的視点の追加

# from typing import List, Dict, Optional, Any
# from PIL import Image

# class ContextManager:
#     """
#     【アクティブなセッション】のコンテキスト情報を一時的に保持し、
#     プロンプトを生成する役割に特化したクラス。
#     永続的なデータはDatabaseManagerが管理する。
#     """
#     def __init__(self):
#         # このクラスはアクティブセッションの「状態」のみを管理
#         self.problem_context_text: str = "まだ問題は読み込まれていません。"
#         self.triggered_image: Optional[Image.Image] = None
        
#     def set_problem_context(self, context_text: str):
#         """アクティブなセッションの問題コンテキストを（メモリ上に）設定する"""
#         self.problem_context_text = context_text if context_text else "まだ問題は読み込まれていません。"

#     def set_triggered_image(self, image: Image.Image):
#         """トリガーの瞬間の画像を（メモリ上に）保存する"""
#         self.triggered_image = image

#     # --- プロンプト生成メソッドは、永続化された情報を引数で受け取るように変更 ---

#     def build_prompt_for_query(self, user_query: str, chat_history: List[Dict], monologue_history: List[str], observation_log: List[str], long_term_context: str) -> str:
#         """
#         ユーザーからの質問応答のため、DBから取得した情報と現在の状態を統合してプロンプトを生成する。
#         """
        
#         history_str = "\n".join([f"- {msg['role']}: {msg['content']}" for msg in chat_history])
#         monologue_str = "\n".join([f"- {m}" for m in monologue_history]) or "なし"
#         observation_str = "\n".join([f"- {o}" for o in observation_log]) or "なし"

#         return f"""
# あなたは、ユーザーの長期的な学習履歴も理解している、パーソナルな家庭教師AIです。

# # 応答形式のルール
# - 応答は必ずMarkdown形式で記述してください。
# - 見出し（`###`）、太字（`**...**`）、箇条書き（`- ...`）などを活用し、視覚的に分かりやすい説明を心がけてください。
# - 数式は、ディスプレイ数式なら `$$ ... $$`、インライン数式なら `$...$` を使って記述してください。
# - コードや計算過程など、数式ではないが整形して見せたいテキストは、インラインコード（`...`）やコードブロック（```...```）を使用できます。
# - 重要: コードブロックの中に数式を記述しないでください。数式は必ず独立させてください。

# # 長期的な学習状況（長期記憶）
# {long_term_context}

# # 現在のセッションの状況（短期記憶）
# ## ユーザーが取り組んでいる問題
# {self.problem_context_text}
# ## ユーザーの最近の様子（システムによる定点観測）
# {observation_str}
# ## ユーザーの最近の独り言（音声認識より）
# {monologue_str}
# ## 直近の会話
# {history_str}

# # ユーザーからの現在の質問
# 「{user_query}」

# # あなたのタスク
# 上記のすべての情報を統合し、ユーザーの思考プロセスや詰まっている点を深く推察してください。
# その上で、単なる答えではなく、ユーザーが「なるほど！」と気づきを得られるような、核心を突いたヒントや別の視点を提供してください。
# """

#     def build_prompt_parts_for_command(self, user_command: str, chat_history: List[Dict], monologue_history: List[str], long_term_context: str) -> Optional[List[Any]]:
#         """
#         音声コマンドに応答するため、テキストと画像を組み合わせたプロンプトパーツを生成する。
#         """
#         if self.triggered_image is None:
#             print("エラー: コマンド用のトリガー画像が設定されていません。")
#             return None

#         history_str = "\n".join([f"- {msg['role']}: {msg['content']}" for msg in chat_history])
#         monologue_str = "\n".join([f"- {m}" for m in monologue_history]) or "なし"

#         text_prompt = f"""
# あなたは、ユーザーの状況を深く理解する家庭教師AIです。
# ユーザーから「{user_command}」という音声コマンドを受け取りました。
# 添付されている画像は、そのコマンドが発せられた瞬間のユーザーの机の様子です。

# # 応答形式のルール
# - 応答は必ずMarkdown形式で記述してください。
# - 数式は$$...$$や$...$で囲んでください。

# # 参考情報
# - **長期的な学習状況:** {long_term_context}
# - **ユーザーが取り組んでいる問題の概要:** {self.problem_context_text}
# - **直近の独り言:** {monologue_str}
# - **直近の会話:** {history_str}

# # あなたのタスク
# 添付された画像と上記の参考情報を最優先で分析し、ユーザーの意図を汲み取って、コマンドに的確に応答してください。
# """
#         return [text_prompt, self.triggered_image]













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
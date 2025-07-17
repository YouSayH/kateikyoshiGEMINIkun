# # # # src/core/gemini_client.py

# # # import google.generativeai as genai
# # # from ..utils.config import GEMINI_API_KEY
# # # from PIL import Image
# # # from typing import List, Any

# # # class GeminiClient:
# # #     def __init__(self):
# # #         """
# # #         GeminiのテキストモデルとVisionモデルを初期化する。
# # #         """
# # #         genai.configure(api_key=GEMINI_API_KEY)
# # #         self.text_model = genai.GenerativeModel('gemini-2.5-flash')
# # #         self.vision_model = genai.GenerativeModel('gemini-2.5-flash')

# # #     def generate_response(self, prompt: str) -> str:
# # #         """
# # #         テキストベースのプロンプトに応答を生成する。
# # #         """
# # #         try:
# # #             response = self.text_model.generate_content(prompt)
# # #             return response.text
# # #         except Exception as e:
# # #             print(f"Gemini API (text) 呼び出し中にエラー: {e}")
# # #             return f"エラーが発生しました: {e}"

# # #     def generate_vision_response(self, prompt_parts: List[Any]) -> str:
# # #         """
# # #         テキストと画像のリスト（プロンプトパーツ）に基づいて応答を生成する。
# # #         このメソッドがマルチモーダルな問い合わせの窓口となる。
# # #         例: ["説明テキスト1", Image1, "説明テキスト2"]
# # #         """
# # #         try:
# # #             response = self.vision_model.generate_content(prompt_parts)
# # #             return response.text
# # #         except Exception as e:
# # #             print(f"Gemini API (vision) 呼び出し中にエラー: {e}")
# # #             return f"画像分析中にエラーが発生しました: {e}"




















# # # src/core/gemini_client.py　ポリシーの緩和

# # import google.generativeai as genai
# # from ..utils.config import GEMINI_API_KEY
# # from PIL import Image
# # from typing import List, Any

# # # --- セーフティ設定を追加 ---
# # # 全てのカテゴリでブロックの閾値を最も緩やかに設定
# # # HARM_CATEGORY_HARASSMENT: ハラスメント
# # # HARM_CATEGORY_HATE_SPEECH: ヘイトスピーチ
# # # HARM_CATEGORY_SEXUALLY_EXPLICIT: 性的に露骨な表現
# # # HARM_CATEGORY_DANGEROUS_CONTENT: 危険なコンテンツ
# # SAFETY_SETTINGS = [
# #     {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
# #     {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
# #     {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
# #     {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
# # ]

# # class GeminiClient:
# #     def __init__(self):
# #         genai.configure(api_key=GEMINI_API_KEY)
# #         # --- モデルの初期化にセーフティ設定を適用 ---
# #         self.text_model = genai.GenerativeModel(
# #             'gemini-2.5-flash-lite-preview-06-17', #gemini-2.5-flash
# #             safety_settings=SAFETY_SETTINGS
# #         )
# #         self.vision_model = genai.GenerativeModel(
# #             'gemini-2.5-flash-lite-preview-06-17',
# #             safety_settings=SAFETY_SETTINGS
# #         )

# #     def generate_response(self, prompt: str) -> str:
# #         """テキストベースのプロンプトに応答を生成する"""
# #         try:
# #             response = self.text_model.generate_content(prompt)
# #             # --- ここからが応答ハンドリングの強化 ---
# #             # 応答がブロックされていないかを確認
# #             if response.parts:
# #                 return response.text
# #             else:
# #                 # 応答が空の場合、ブロックされた可能性が高い
# #                 print("Gemini API (text) 応答がブロックされました。Finish Reason:", response.prompt_feedback)
# #                 return "AIの応答がセーフティ機能によってブロックされました。プロンプトの内容を変えてもう一度お試しください。"
# #         except Exception as e:
# #             print(f"Gemini API (text) 呼び出し中にエラー: {e}")
# #             return f"エラーが発生しました: {e}"

# #     def generate_vision_response(self, prompt_parts: List[Any]) -> str:
# #         """テキストと画像のリストに基づいて応答を生成する"""
# #         try:
# #             response = self.vision_model.generate_content(prompt_parts)
# #             # --- ここも同様に応答ハンドリングを強化 ---
# #             if response.parts:
# #                 return response.text
# #             else:
# #                 print("Gemini API (vision) 応答がブロックされました。Finish Reason:", response.prompt_feedback)
# #                 return "AIの応答がセーフティ機能によってブロックされました。プロンプトの内容を変えてもう一度お試しください。"
# #         except Exception as e:
# #             print(f"Gemini API (vision) 呼び出し中にエラー: {e}")
# #             return f"画像分析中にエラーが発生しました: {e}"














# # src/core/gemini_client.py　　設定画面の追加

# import google.generativeai as genai
# from ..utils.config import GEMINI_API_KEY_FROM_ENV
# from .settings_manager import SettingsManager
# from PIL import Image
# from typing import List, Any

# # --- セーフティ設定 ---
# # 全てのカテゴリでブロックの閾値を最も緩やかに設定
# SAFETY_SETTINGS = [
#     {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
#     {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
#     {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
#     {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
# ]

# class GeminiClient:
#     def __init__(self):
#         """
#         Geminiモデルを初期化する。
#         APIキーはまず設定から読み込み、なければ.envファイルから読み込む。
#         """
#         settings = SettingsManager()
#         # 1. QSettingsからAPIキーを読み込み試行
#         api_key = settings.get_api_key()
        
#         # 2. 設定になければ、.envファイル（環境変数）から読み込み試行
#         if not api_key:
#             api_key = GEMINI_API_KEY_FROM_ENV
        
#         if not api_key:
#             print("警告: Gemini APIキーが設定されていません。設定画面から設定してください。")
#             self.text_model = None
#             self.vision_model = None
#             return

#         try:
#             genai.configure(api_key=api_key)
#             # モデルの初期化にセーフティ設定を適用
#             self.text_model = genai.GenerativeModel(
#                 'gemini-2.5-flash-lite-preview-06-17',
#                 safety_settings=SAFETY_SETTINGS
#             )
#             self.vision_model = genai.GenerativeModel(
#                 'gemini-2.5-flash-lite-preview-06-17',
#                 safety_settings=SAFETY_SETTINGS
#             )
#             print("GeminiClientが正常に初期化されました。")
#         except Exception as e:
#             print(f"GeminiClientの初期化中にエラーが発生しました: {e}")
#             self.text_model = None
#             self.vision_model = None


#     def generate_response(self, prompt: str) -> str:
#         """テキストベースのプロンプトに応答を生成する"""
#         if not self.text_model:
#             return "エラー: APIキーが設定されていないため、AIを呼び出せません。"
            
#         try:
#             response = self.text_model.generate_content(prompt)
#             if response.parts:
#                 return response.text
#             else:
#                 print("Gemini API (text) 応答がブロックされました。Finish Reason:", response.prompt_feedback)
#                 return "AIの応答がセーフティ機能によってブロックされました。プロンプトの内容を変えてもう一度お試しください。"
#         except Exception as e:
#             print(f"Gemini API (text) 呼び出し中にエラー: {e}")
#             return f"エラーが発生しました: {e}"

#     def generate_vision_response(self, prompt_parts: List[Any]) -> str:
#         """テキストと画像のリストに基づいて応答を生成する"""
#         if not self.vision_model:
#             return "エラー: APIキーが設定されていないため、AIを呼び出せません。"

#         try:
#             response = self.vision_model.generate_content(prompt_parts)
#             if response.parts:
#                 return response.text
#             else:
#                 print("Gemini API (vision) 応答がブロックされました。Finish Reason:", response.prompt_feedback)
#                 return "AIの応答がセーフティ機能によってブロックされました。プロンプトの内容を変えてもう一度お試しください。"
#         except Exception as e:
#             print(f"Gemini API (vision) 呼び出し中にエラー: {e}")
#             return f"画像分析中にエラーが発生しました: {e}"



















# src/core/gemini_client.py  geminiモデル選択&プロンプトの微調整# src/core/gemini_client.py

import google.generativeai as genai
from ..utils.config import GEMINI_API_KEY_FROM_ENV
from .settings_manager import SettingsManager
from PIL import Image
from typing import List, Any

# --- セーフティ設定 ---
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

class GeminiClient:
    def __init__(self, text_model_name: str = None, vision_model_name: str = None):
        """
        Geminiモデルを初期化する。
        APIキーはまず設定から読み込み、なければ.envファイルから読み込む。
        モデル名は引数で指定されていればそれを使い、なければ設定から読み込む。
        """
        settings = SettingsManager()
        api_key = settings.api_key
        if not api_key:
            api_key = GEMINI_API_KEY_FROM_ENV
        
        if not api_key:
            print("警告: Gemini APIキーが設定されていません。設定画面から設定してください。")
            self.text_model = None
            self.vision_model = None
            return

        try:
            genai.configure(api_key=api_key)
            
            # 使用するモデル名を決定
            final_text_model_name = text_model_name if text_model_name else settings.main_response_model
            final_vision_model_name = vision_model_name if vision_model_name else settings.vision_model

            # モデルを初期化
            self.text_model = genai.GenerativeModel(final_text_model_name, safety_settings=SAFETY_SETTINGS)
            self.vision_model = genai.GenerativeModel(final_vision_model_name, safety_settings=SAFETY_SETTINGS)
            print(f"GeminiClient初期化完了 (Text: {final_text_model_name}, Vision: {final_vision_model_name})")

        except Exception as e:
            print(f"GeminiClientの初期化中にエラーが発生しました: {e}")
            self.text_model = None
            self.vision_model = None

    def generate_response(self, prompt: str) -> str:
        """テキストベースのプロンプトに応答を生成する"""
        if not self.text_model:
            return "エラー: AIテキストモデルが初期化されていません。APIキーを確認してください。"
            
        try:
            response = self.text_model.generate_content(prompt)
            if response.parts:
                return response.text
            else:
                print("Gemini API (text) 応答がブロックされました。Finish Reason:", response.prompt_feedback)
                return "AIの応答がセーフティ機能によってブロックされました。プロンプトの内容を変えてもう一度お試しください。"
        except Exception as e:
            print(f"Gemini API (text) 呼び出し中にエラー: {e}")
            return f"エラーが発生しました: {e}"

    def generate_vision_response(self, prompt_parts: List[Any]) -> str:
        """テキストと画像のリストに基づいて応答を生成する"""
        if not self.vision_model:
            return "エラー: AI Visionモデルが初期化されていません。APIキーを確認してください。"

        try:
            response = self.vision_model.generate_content(prompt_parts)
            if response.parts:
                return response.text
            else:
                print("Gemini API (vision) 応答がブロックされました。Finish Reason:", response.prompt_feedback)
                return "AIの応答がセーフティ機能によってブロックされました。プロンプトの内容を変えてもう一度お試しください。"
        except Exception as e:
            print(f"Gemini API (vision) 呼び出し中にエラー: {e}")
            return f"画像分析中にエラーが発生しました: {e}"
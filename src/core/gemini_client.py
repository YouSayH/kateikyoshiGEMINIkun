# src/core/gemini_client.py

# google.generativeaiは遅延インポートするため、トップレベルではインポートしない
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
        ライブラリのインポートは初回利用時に遅延して行われる。
        """
        import google.generativeai as genai
        print("genaiをimportしました。")

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
            
            final_text_model_name = text_model_name if text_model_name else settings.main_response_model
            final_vision_model_name = vision_model_name if vision_model_name else settings.vision_model

            self.text_model = genai.GenerativeModel(final_text_model_name, safety_settings=SAFETY_SETTINGS)
            self.vision_model = genai.GenerativeModel(final_vision_model_name, safety_settings=SAFETY_SETTINGS)
            print(f"GeminiClient初期化完了 (Text: {final_text_model_name}, Vision: {final_vision_model_name})")

        except Exception as e:
            print(f"GeminiClientの初期化中にエラーが発生しました: {e}")
            self.text_model = None
            self.vision_model = None

    def generate_response(self, prompt: str, timeout: int = None) -> str:
        """
        テキストベースのプロンプトに応答を生成する。
        timeout（秒）が指定された場合、その時間内に応答がなければエラーを返す。
        """
        if not self.text_model:
            return "エラー: AIテキストモデルが初期化されていません。APIキーを確認してください。"
            
        try:
            request_options = {"timeout": timeout} if timeout is not None else {}
            response = self.text_model.generate_content(prompt, request_options=request_options)

            if response.parts:
                return response.text
            else:
                # 応答がブロックされた場合の詳細情報をログに出力
                print("Gemini API (text) 応答がブロックされました。Finish Reason:", response.prompt_feedback)
                return "AIの応答がセーフティ機能によってブロックされました。プロンプトの内容を変えてもう一度お試しください。"
        except Exception as e:
            print(f"Gemini API (text) 呼び出し中にエラー: {e}")
            return f"エラーが発生しました: {e}"

    def generate_vision_response(self, prompt_parts: List[Any], timeout: int = None) -> str:
        """
        テキストと画像のリストに基づいて応答を生成する。
        timeout（秒）が指定された場合、その時間内に応答がなければエラーを返す。
        """
        if not self.vision_model:
            return "エラー: AI Visionモデルが初期化されていません。APIキーを確認してください。"

        try:
            request_options = {"timeout": timeout} if timeout is not None else {}
            response = self.vision_model.generate_content(prompt_parts, request_options=request_options)

            if response.parts:
                return response.text
            else:
                # 応答がブロックされた場合の詳細情報をログに出力
                print("Gemini API (vision) 応答がブロックされました。Finish Reason:", response.prompt_feedback)
                return "AIの応答がセーフティ機能によってブロックされました。プロンプトの内容を変えてもう一度お試しください。"
        except Exception as e:
            print(f"Gemini API (vision) 呼び出し中にエラー: {e}")
            return f"画像分析中にエラーが発生しました: {e}"
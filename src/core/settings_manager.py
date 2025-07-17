# # # from PySide6.QtCore import QSettings
# # # import os

# # # class SettingsManager:
# # #     """
# # #     QSettingsを使用してアプリケーションの設定を管理するクラス。
# # #     """
# # #     def __init__(self, company_name="YourCompany", app_name="StudyAssistApp"):
# # #         self.settings = QSettings(company_name, app_name)

# # #     def get(self, key, default_value=None):
# # #         """設定値を取得する"""
# # #         return self.settings.value(key, default_value)

# # #     def set(self, key, value):
# # #         """設定値を保存する"""
# # #         self.settings.setValue(key, value)

# # #     # --- 各種設定項目のショートカットメソッド ---

# # #     def get_api_key(self) -> str:
# # #         return self.get("GEMINI_API_KEY", "")

# # #     def set_api_key(self, api_key: str):
# # #         self.set("GEMINI_API_KEY", api_key)

# # #     def get_hand_stop_threshold(self) -> int:
# # #         # デフォルトは60秒
# # #         return int(self.get("hand_stop_threshold", 60))

# # #     def set_hand_stop_threshold(self, seconds: int):
# # #         self.set("hand_stop_threshold", seconds)
        
# # #     def get_observation_interval(self) -> int:
# # #         # デフォルトは30秒
# # #         return int(self.get("observation_interval", 30))

# # #     def set_observation_interval(self, seconds: int):
# # #         self.set("observation_interval", seconds)

# # #     # 今後、他の設定項目もここに追加していきます
# # #     def get_camera_device_index(self) -> int:
# # #         # デフォルトは0番のカメラ
# # #         return int(self.get("camera_device_index", 0))

# # #     def set_camera_device_index(self, index: int):
# # #         self.set("camera_device_index", index)

# # #     def get_mic_device_index(self) -> int:
# # #         # デフォルトは-1（システムデフォルトのマイク）
# # #         return int(self.get("mic_device_index", -1))

# # #     def set_mic_device_index(self, index: int):
# # #         self.set("mic_device_index", index)















# # # src/core/settings_manager.py　　モデル選択&プロンプトの調整# src/core/settings_manager.py

# # from PySide6.QtCore import QSettings

# # class SettingsManager:
# #     """
# #     QSettingsを使用してアプリケーションの設定を管理するクラス。
# #     """
# #     def __init__(self, company_name="YourCompany", app_name="StudyAssistApp"):
# #         self.settings = QSettings(company_name, app_name)

# #     def get(self, key: str, default_value=None):
# #         return self.settings.value(key, default_value)

# #     def set(self, key: str, value):
# #         self.settings.setValue(key, value)

# #     def _get_prompt(self, name: str, default_text: str) -> str:
# #         return self.get(f"prompt/{name}", default_text)

# #     def _set_prompt(self, name: str, prompt_text: str):
# #         self.set(f"prompt/{name}", prompt_text)

# #     def _get_model(self, name: str, default_model: str) -> str:
# #         return self.get(f"model/{name}", default_model)

# #     def _set_model(self, name: str, model_name: str):
# #         self.set(f"model/{name}", model_name)

# #     # --- 一般設定 ---
# #     @property
# #     def api_key(self) -> str:
# #         return self.get("general/api_key", "")
# #     @api_key.setter
# #     def api_key(self, value: str):
# #         self.set("general/api_key", value)

# #     @property
# #     def hand_stop_threshold(self) -> int:
# #         return int(self.get("general/hand_stop_threshold", 60))
# #     @hand_stop_threshold.setter
# #     def hand_stop_threshold(self, value: int):
# #         self.set("general/hand_stop_threshold", value)
        
# #     @property
# #     def observation_interval(self) -> int:
# #         return int(self.get("general/observation_interval", 30))
# #     @observation_interval.setter
# #     def observation_interval(self, value: int):
# #         self.set("general/observation_interval", value)

# #     @property
# #     def camera_device_index(self) -> int:
# #         return int(self.get("general/camera_device_index", 0))
# #     @camera_device_index.setter
# #     def camera_device_index(self, value: int):
# #         self.set("general/camera_device_index", value)

# #     @property
# #     def mic_device_index(self) -> int:
# #         return int(self.get("general/mic_device_index", -1))
# #     @mic_device_index.setter
# #     def mic_device_index(self, value: int):
# #         self.set("general/mic_device_index", value)

# #     # --- プロンプト設定 ---
# #     @property
# #     def hand_stopped_prompt(self) -> str:
# #         return self._get_prompt("hand_stopped", "あなたは優しい家庭教師です。生徒の手が止まっています。「どうかしましたか？」など、優しく声をかけてください。")
# #     @hand_stopped_prompt.setter
# #     def hand_stopped_prompt(self, value: str):
# #         self._set_prompt("hand_stopped", value)

# #     @property
# #     def keyword_extraction_from_history_prompt(self) -> str:
# #         return self._get_prompt("keyword_from_history", """以下の会話履歴の主題を表す最も重要なキーワードを5つ、カンマ区切りで抽出してください。思考プロセスは不要です。キーワードのみを出力してください。\n例: 微分、接線、最大値、グラフ、2次関数\n\n---\n{conversation_text}""")
# #     @keyword_extraction_from_history_prompt.setter
# #     def keyword_extraction_from_history_prompt(self, value: str):
# #         self._set_prompt("keyword_from_history", value)

# #     @property
# #     def title_generation_prompt(self) -> str:
# #         return self._get_prompt("title_generation", """以下の会話履歴の内容を要約し、このチャットにふさわしい簡潔なタイトルを5～15文字程度で生成してください。思考プロセスは不要です。タイトルのみを出力してください。\n例: 部分積分の応用\n\n---\n{conversation_text}""")
# #     @title_generation_prompt.setter
# #     def title_generation_prompt(self, value: str):
# #         self._set_prompt("title_generation", value)
        
# #     @property
# #     def observation_prompt(self) -> str:
# #         return self._get_prompt("observation", """あなたはユーザーの勉強の様子を観察するAIです。\n以下の画像は現在のユーザーの机の様子です。\n前回の観察結果は「{previous_description}」でした。\n現在の画像と前回の結果を比較し、ユーザーの行動に何か特筆すべき変化があれば簡潔に報告してください。\n例: 「新しい数式を書き始めたようです」「問題の特定の部分を指差しています」など。\n特に大きな変化がなければ「特に変化はありません」と報告してください。""")
# #     @observation_prompt.setter
# #     def observation_prompt(self, value: str):
# #         self._set_prompt("observation", value)

# #     # --- モデル設定 (デフォルトを全てflashに変更) ---
# #     @property
# #     def keyword_extraction_model(self) -> str:
# #         return self._get_model("keyword_extraction", "gemini-2.5-flash")
# #     @keyword_extraction_model.setter
# #     def keyword_extraction_model(self, value: str):
# #         self._set_model("keyword_extraction", value)

# #     @property
# #     def main_response_model(self) -> str:
# #         return self._get_model("main_response", "gemini-2.5-flash")
# #     @main_response_model.setter
# #     def main_response_model(self, value: str):
# #         self._set_model("main_response", value)

# #     @property
# #     def vision_model(self) -> str:
# #         return self._get_model("vision", "gemini-2.5-flash")
# #     @vision_model.setter
# #     def vision_model(self, value: str):
# #         self._set_model("vision", value)
















# # src/core/settings_manager.py　ttsの設定追加

# from PySide6.QtCore import QSettings

# class SettingsManager:
#     """
#     QSettingsを使用してアプリケーションの設定を管理するクラス。
#     """
#     def __init__(self, company_name="YourCompany", app_name="StudyAssistApp"):
#         self.settings = QSettings(company_name, app_name)

#     def get(self, key: str, default_value=None):
#         return self.settings.value(key, default_value)

#     def set(self, key: str, value):
#         self.settings.setValue(key, value)

#     def _get_prompt(self, name: str, default_text: str) -> str:
#         return self.get(f"prompt/{name}", default_text)

#     def _set_prompt(self, name: str, prompt_text: str):
#         self.set(f"prompt/{name}", prompt_text)

#     def _get_model(self, name: str, default_model: str) -> str:
#         return self.get(f"model/{name}", default_model)

#     def _set_model(self, name: str, model_name: str):
#         self.set(f"model/{name}", model_name)

#     # --- 一般設定 ---
#     @property
#     def api_key(self) -> str:
#         return self.get("general/api_key", "")
#     @api_key.setter
#     def api_key(self, value: str):
#         self.set("general/api_key", value)

#     @property
#     def hand_stop_threshold(self) -> int:
#         return int(self.get("general/hand_stop_threshold", 60))
#     @hand_stop_threshold.setter
#     def hand_stop_threshold(self, value: int):
#         self.set("general/hand_stop_threshold", value)
        
#     @property
#     def observation_interval(self) -> int:
#         return int(self.get("general/observation_interval", 30))
#     @observation_interval.setter
#     def observation_interval(self, value: int):
#         self.set("general/observation_interval", value)

#     @property
#     def camera_device_index(self) -> int:
#         return int(self.get("general/camera_device_index", 0))
#     @camera_device_index.setter
#     def camera_device_index(self, value: int):
#         self.set("general/camera_device_index", value)

#     @property
#     def mic_device_index(self) -> int:
#         return int(self.get("general/mic_device_index", -1))
#     @mic_device_index.setter
#     def mic_device_index(self, value: int):
#         self.set("general/mic_device_index", value)

#     @property
#     def tts_enabled(self) -> bool:
#         return self.get("general/tts_enabled", "true") == "true"
#     @tts_enabled.setter
#     def tts_enabled(self, value: bool):
#         self.set("general/tts_enabled", "true" if value else "false")
    
#     @property
#     def tts_rate(self) -> int:
#         return int(self.get("general/tts_rate", 200))
#     @tts_rate.setter
#     def tts_rate(self, value: int):
#         self.set("general/tts_rate", value)

#     # --- プロンプト設定 ---
#     @property
#     def hand_stopped_prompt(self) -> str:
#         return self._get_prompt("hand_stopped", "あなたは優しい家庭教師です。生徒の手が止まっています。「どうかしましたか？」など、優しく声をかけてください。")
#     @hand_stopped_prompt.setter
#     def hand_stopped_prompt(self, value: str):
#         self._set_prompt("hand_stopped", value)

#     @property
#     def keyword_extraction_from_history_prompt(self) -> str:
#         return self._get_prompt("keyword_from_history", """以下の会話履歴の主題を表す最も重要なキーワードを5つ、カンマ区切りで抽出してください。思考プロセスは不要です。キーワードのみを出力してください。
# 例: 微分、接線、最大値、グラフ、2次関数

# ---
# {conversation_text}""")
#     @keyword_extraction_from_history_prompt.setter
#     def keyword_extraction_from_history_prompt(self, value: str):
#         self._set_prompt("keyword_from_history", value)

#     @property
#     def title_generation_prompt(self) -> str:
#         return self._get_prompt("title_generation", """以下の会話履歴の内容を要約し、このチャットにふさわしい簡潔なタイトルを5～15文字程度で生成してください。思考プロセスは不要です。タイトルのみを出力してください。
# 例: 部分積分の応用

# ---
# {conversation_text}""")
#     @title_generation_prompt.setter
#     def title_generation_prompt(self, value: str):
#         self._set_prompt("title_generation", value)
        
#     @property
#     def observation_prompt(self) -> str:
#         return self._get_prompt("observation", """あなたはユーザーの勉強の様子を観察するAIです。
# 以下の画像は現在のユーザーの机の様子です。
# 前回の観察結果は「{previous_description}」でした。
# 現在の画像と前回の結果を比較し、ユーザーの行動に何か特筆すべき変化があれば簡潔に報告してください。
# 例: 「新しい数式を書き始めたようです」「問題の特定の部分を指差しています」など。
# 特に大きな変化がなければ「特に変化はありません」と報告してください。""")
#     @observation_prompt.setter
#     def observation_prompt(self, value: str):
#         self._set_prompt("observation", value)

#     # --- モデル設定 ---
#     @property
#     def keyword_extraction_model(self) -> str:
#         return self._get_model("keyword_extraction", "gemini-2.5-flash")
#     @keyword_extraction_model.setter
#     def keyword_extraction_model(self, value: str):
#         self._set_model("keyword_extraction", value)

#     @property
#     def main_response_model(self) -> str:
#         return self._get_model("main_response", "gemini-2.5-flash")
#     @main_response_model.setter
#     def main_response_model(self, value: str):
#         self._set_model("main_response", value)

#     @property
#     def vision_model(self) -> str:
#         return self._get_model("vision", "gemini-2.5-flash")
#     @vision_model.setter
#     def vision_model(self, value: str):
#         self._set_model("vision", value)
















# src/core/settings_manager.py　　カメラオンオフの設定追加

from PySide6.QtCore import QSettings

class SettingsManager:
    """
    QSettingsを使用してアプリケーションの設定を管理するクラス。
    """
    def __init__(self, company_name="YourCompany", app_name="StudyAssistApp"):
        self.settings = QSettings(company_name, app_name)

    def get(self, key: str, default_value=None):
        return self.settings.value(key, default_value)

    def set(self, key: str, value):
        self.settings.setValue(key, value)

    def _get_prompt(self, name: str, default_text: str) -> str:
        return self.get(f"prompt/{name}", default_text)

    def _set_prompt(self, name: str, prompt_text: str):
        self.set(f"prompt/{name}", prompt_text)

    def _get_model(self, name: str, default_model: str) -> str:
        return self.get(f"model/{name}", default_model)

    def _set_model(self, name: str, model_name: str):
        self.set(f"model/{name}", model_name)

    # --- 一般設定 ---
    @property
    def api_key(self) -> str:
        return self.get("general/api_key", "")
    @api_key.setter
    def api_key(self, value: str):
        self.set("general/api_key", value)

    @property
    def hand_stop_threshold(self) -> int:
        return int(self.get("general/hand_stop_threshold", 60))
    @hand_stop_threshold.setter
    def hand_stop_threshold(self, value: int):
        self.set("general/hand_stop_threshold", value)
        
    @property
    def observation_interval(self) -> int:
        return int(self.get("general/observation_interval", 30))
    @observation_interval.setter
    def observation_interval(self, value: int):
        self.set("general/observation_interval", value)

    @property
    def camera_device_index(self) -> int:
        return int(self.get("general/camera_device_index", 0))
    @camera_device_index.setter
    def camera_device_index(self, value: int):
        self.set("general/camera_device_index", value)

    @property
    def mic_device_index(self) -> int:
        return int(self.get("general/mic_device_index", -1))
    @mic_device_index.setter
    def mic_device_index(self, value: int):
        self.set("general/mic_device_index", value)

    @property
    def camera_enabled_on_startup(self) -> bool:
        return self.get("general/camera_enabled_on_startup", "true") == "true"
    @camera_enabled_on_startup.setter
    def camera_enabled_on_startup(self, value: bool):
        self.set("general/camera_enabled_on_startup", "true" if value else "false")

    @property
    def tts_enabled(self) -> bool:
        return self.get("general/tts_enabled", "true") == "true"
    @tts_enabled.setter
    def tts_enabled(self, value: bool):
        self.set("general/tts_enabled", "true" if value else "false")
    
    @property
    def tts_rate(self) -> int:
        return int(self.get("general/tts_rate", 200))
    @tts_rate.setter
    def tts_rate(self, value: int):
        self.set("general/tts_rate", value)

    # --- プロンプト設定 ---
    @property
    def hand_stopped_prompt(self) -> str:
        return self._get_prompt("hand_stopped", "あなたは優しい家庭教師です。生徒の手が止まっています。「どうかしましたか？」など、優しく声をかけてください。")
    @hand_stopped_prompt.setter
    def hand_stopped_prompt(self, value: str):
        self._set_prompt("hand_stopped", value)

    @property
    def keyword_extraction_from_history_prompt(self) -> str:
        return self._get_prompt("keyword_from_history", """以下の会話履歴の主題を表す最も重要なキーワードを5つ、カンマ区切りで抽出してください。思考プロセスは不要です。キーワードのみを出力してください。
例: 微分、接線、最大値、グラフ、2次関数

---
{conversation_text}""")
    @keyword_extraction_from_history_prompt.setter
    def keyword_extraction_from_history_prompt(self, value: str):
        self._set_prompt("keyword_from_history", value)

    @property
    def title_generation_prompt(self) -> str:
        return self._get_prompt("title_generation", """以下の会話履歴の内容を要約し、このチャットにふさわしい簡潔なタイトルを5～15文字程度で生成してください。思考プロセスは不要です。タイトルのみを出力してください。
例: 部分積分の応用

---
{conversation_text}""")
    @title_generation_prompt.setter
    def title_generation_prompt(self, value: str):
        self._set_prompt("title_generation", value)
        
    @property
    def observation_prompt(self) -> str:
        return self._get_prompt("observation", """あなたはユーザーの勉強の様子を観察するAIです。
以下の画像は現在のユーザーの机の様子です。
前回の観察結果は「{previous_description}」でした。
現在の画像と前回の結果を比較し、ユーザーの行動に何か特筆すべき変化があれば簡潔に報告してください。
例: 「新しい数式を書き始めたようです」「問題の特定の部分を指差しています」など。
特に大きな変化がなければ「特に変化はありません」と報告してください。""")
    @observation_prompt.setter
    def observation_prompt(self, value: str):
        self._set_prompt("observation", value)

    # --- モデル設定 ---
    @property
    def keyword_extraction_model(self) -> str:
        return self._get_model("keyword_extraction", "gemini-1.5-flash")
    @keyword_extraction_model.setter
    def keyword_extraction_model(self, value: str):
        self._set_model("keyword_extraction", value)

    @property
    def main_response_model(self) -> str:
        return self._get_model("main_response", "gemini-1.5-flash")
    @main_response_model.setter
    def main_response_model(self, value: str):
        self._set_model("main_response", value)

    @property
    def vision_model(self) -> str:
        return self._get_model("vision", "gemini-1.5-flash")
    @vision_model.setter
    def vision_model(self, value: str):
        self._set_model("vision", value)
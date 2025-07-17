
# src/utils/config.py   設定画面の追加
import os
from dotenv import load_dotenv

# .envファイルの読み込みは、あくまで初期設定や開発用とする
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

# 環境変数からAPIキーを読み込む (存在すれば)
GEMINI_API_KEY_FROM_ENV = os.getenv("GEMINI_API_KEY")

# config.pyはAPIキーの有無を強制しなくなる
# if not GEMINI_API_KEY:
#     raise ValueError("Gemini APIキーが.envファイルに設定されていません。")
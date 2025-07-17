# main.py

import sys
from PySide6.QtWidgets import QApplication
# MainWindowのインポートパスが正しいことを確認
from src.ui.main_window import MainWindow

if __name__ == "__main__":
    # アプリケーションインスタンスを作成
    app = QApplication(sys.argv)

    # メインウィンドウを作成して表示
    # MainWindowの__init__内で初期メッセージが設定されるため、
    # ここで何かを呼び出す必要はなくなりました。
    window = MainWindow()
    
    window.show()

    # アプリケーションのイベントループを開始
    sys.exit(app.exec())
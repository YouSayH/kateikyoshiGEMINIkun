# # # # # # # src/core/visual_observer.py

# # # # # # from PySide6.QtCore import QThread, Signal, Slot, QTimer
# # # # # # from PIL import Image
# # # # # # from typing import Optional
# # # # # # from .gemini_client import GeminiClient

# # # # # # class ObservationTaskWorker(QThread):
# # # # # #     task_finished = Signal(str)

# # # # # #     def __init__(self, gemini_client: GeminiClient, frame: Image.Image, prev_desc: str, parent=None):
# # # # # #         super().__init__(parent)
# # # # # #         self.gemini_client = gemini_client
# # # # # #         self.frame_to_analyze = frame
# # # # # #         self.previous_description = prev_desc

# # # # # #     def run(self):
# # # # # #         print("ObservationTaskWorker: AIへの画像分析を開始します。")
# # # # # #         description = ""
# # # # # #         try:
# # # # # #             prompt = f"""
# # # # # #             あなたはユーザーの勉強の様子を観察するAIです。
# # # # # #             以下の画像は現在のユーザーの机の様子です。
# # # # # #             前回の観察結果は「{self.previous_description}」でした。
# # # # # #             現在の画像と前回の結果を比較し、ユーザーの行動に何か特筆すべき変化があれば簡潔に報告してください。
# # # # # #             例: 「新しい数式を書き始めたようです」「問題の特定の部分を指差しています」など。
# # # # # #             特に変化がなければ「特に変化はありません」と報告してください。
# # # # # #             また、ノートの内容についても何かあれば教えてください。
# # # # # #             """
            
# # # # # #             # --- ここが修正箇所 ---
# # # # # #             # 古い `describe_images` の呼び出しを、新しい `generate_vision_response` に変更します。
# # # # # #             # プロンプトパーツは [テキスト, 画像] のリスト形式で渡します。
# # # # # #             prompt_parts = [prompt, self.frame_to_analyze]
# # # # # #             description = self.gemini_client.generate_vision_response(prompt_parts)
            
# # # # # #         except Exception as e:
# # # # # #             print(f"ObservationTaskWorker: 分析中にエラーが発生しました: {e}")
# # # # # #             description = "分析中にエラーが発生しました。"
# # # # # #         finally:
# # # # # #             self.task_finished.emit(description)
# # # # # #             print("ObservationTaskWorker: タスク完了。")


# # # # # # class VisualObserverWorker(QThread):
# # # # # #     observation_ready = Signal(str)

# # # # # #     def __init__(self, gemini_client: GeminiClient, interval_sec=30, parent=None):
# # # # # #         super().__init__(parent)
# # # # # #         self.gemini_client = gemini_client
# # # # # #         self.interval = interval_sec * 1000
# # # # # #         self.latest_frame: Optional[Image.Image] = None
# # # # # #         self.previous_description: str = "まだ観測を開始していません。"
# # # # # #         self._is_task_running = False

# # # # # #     def run(self):
# # # # # #         self.timer = QTimer()
# # # # # #         self.timer.timeout.connect(self.trigger_observation_task)
# # # # # #         self.timer.start(self.interval)
# # # # # #         print(f"Visual Observer(指揮官)が起動しました。（{self.interval/1000}秒間隔）")
# # # # # #         self.exec()

# # # # # #     @Slot()
# # # # # #     def trigger_observation_task(self):
# # # # # #         if self.latest_frame is None: return
# # # # # #         if self._is_task_running:
# # # # # #             print("Visual Observer(指揮官): 前の部隊がまだ帰還していないため、今回の出撃は見送ります。")
# # # # # #             return

# # # # # #         self._is_task_running = True
# # # # # #         print("Visual Observer(指揮官): 実行部隊に出撃を命令！")
        
# # # # # #         frame_copy = self.latest_frame.copy()
# # # # # #         self.task_worker = ObservationTaskWorker(
# # # # # #             self.gemini_client, frame_copy, self.previous_description
# # # # # #         )
# # # # # #         self.task_worker.task_finished.connect(self.on_task_finished)
# # # # # #         self.task_worker.finished.connect(self.task_worker.deleteLater)
# # # # # #         self.task_worker.start()

# # # # # #     @Slot(str)
# # # # # #     def on_task_finished(self, description: str):
# # # # # #         print("Visual Observer(指揮官): 実行部隊が帰還。報告を受理しました。")
# # # # # #         if description and "特に変化はありません" not in description and "エラーが発生しました" not in description:
# # # # # #             print(f"Visual Observer(指揮官): 有意な変化を検出、本部に報告します: {description}")
# # # # # #             self.observation_ready.emit(description)
# # # # # #             self.previous_description = description
        
# # # # # #         self._is_task_running = False

# # # # # #     @Slot(Image.Image)
# # # # # #     def update_frame(self, image: Image.Image):
# # # # # #         self.latest_frame = image

# # # # # #     def stop(self):
# # # # # #         print("Visual Observer(指揮官)の停止処理を開始します。")
# # # # # #         if hasattr(self, 'timer'):
# # # # # #             self.timer.stop()
# # # # # #         self.quit()
# # # # # #         self.wait()
# # # # # #         print("Visual Observerワーカーを完全に停止しました。")


















# # # # # # src/core/visual_observer.py　安全な終了(終了時の処理の一部ををこちらにも持たせる。)

# # # # # from PySide6.QtCore import QThread, Signal, Slot, QTimer
# # # # # from PIL import Image
# # # # # from typing import Optional
# # # # # from .gemini_client import GeminiClient

# # # # # class ObservationTaskWorker(QThread):
# # # # #     # (このクラスは変更なし)
# # # # #     task_finished = Signal(str)
# # # # #     def __init__(self, gemini_client: GeminiClient, frame: Image.Image, prev_desc: str, parent=None):
# # # # #         super().__init__(parent)
# # # # #         self.gemini_client = gemini_client
# # # # #         self.frame_to_analyze = frame
# # # # #         self.previous_description = prev_desc
# # # # #     def run(self):
# # # # #         print("ObservationTaskWorker: AIへの画像分析を開始します。")
# # # # #         description = ""
# # # # #         try:
# # # # #             prompt = f"""あなたはユーザーの勉強の様子を観察するAIです。\n以下の画像は現在のユーザーの机の様子です。\n前回の観察結果は「{self.previous_description}」でした。\n現在の画像と前回の結果を比較し、ユーザーの行動に何か特筆すべき変化があれば簡潔に報告してください。\n例: 「新しい数式を書き始めたようです」「問題の特定の部分を指差しています」など。\n特に大きな変化がなければ「特に変化はありません」と報告してください。"""
# # # # #             prompt_parts = [prompt, self.frame_to_analyze]
# # # # #             description = self.gemini_client.generate_vision_response(prompt_parts)
# # # # #         except Exception as e:
# # # # #             print(f"ObservationTaskWorker: 分析中にエラーが発生しました: {e}")
# # # # #             description = "分析中にエラーが発生しました。"
# # # # #         finally:
# # # # #             self.task_finished.emit(description)
# # # # #             print("ObservationTaskWorker: タスク完了。")


# # # # # class VisualObserverWorker(QThread):
# # # # #     observation_ready = Signal(str)

# # # # #     def __init__(self, gemini_client: GeminiClient, interval_sec=30, parent=None):
# # # # #         super().__init__(parent)
# # # # #         self.gemini_client = gemini_client
# # # # #         self.interval = interval_sec * 1000
# # # # #         self.latest_frame: Optional[Image.Image] = None
# # # # #         self.previous_description: str = "まだ観測を開始していません。"
# # # # #         self._is_task_running = False
        
# # # # #         # --- ここからが修正箇所 ---
# # # # #         # タイマーをインスタンス変数として宣言だけしておく
# # # # #         self.timer = None
        
# # # # #         # スレッド終了シグナルに、後片付け用スロットを接続
# # # # #         self.finished.connect(self._cleanup)

# # # # #     def run(self):
# # # # #         """スレッドのイベントループを開始し、タイマーをセットする"""
# # # # #         self.timer = QTimer()
# # # # #         self.timer.timeout.connect(self.trigger_observation_task)
# # # # #         self.timer.start(self.interval)
# # # # #         print(f"Visual Observer(指揮官)が起動しました。（{self.interval/1000}秒間隔）")
# # # # #         self.exec()

# # # # #     @Slot()
# # # # #     def _cleanup(self):
# # # # #         """スレッド終了時に呼び出される後片付け用スロット"""
# # # # #         print("Visual Observer: クリーンアップ処理を実行します。")
# # # # #         if self.timer:
# # # # #             self.timer.stop()
# # # # #             self.timer = None

# # # # #     @Slot()
# # # # #     def trigger_observation_task(self):
# # # # #         # (このメソッドは変更なし)
# # # # #         if self.latest_frame is None: return
# # # # #         if self._is_task_running:
# # # # #             print("Visual Observer(指揮官): 前の部隊がまだ帰還していないため、今回の出撃は見送ります。")
# # # # #             return
# # # # #         self._is_task_running = True
# # # # #         print("Visual Observer(指揮官): 実行部隊に出撃を命令！")
# # # # #         frame_copy = self.latest_frame.copy()
# # # # #         self.task_worker = ObservationTaskWorker(
# # # # #             self.gemini_client, frame_copy, self.previous_description
# # # # #         )
# # # # #         self.task_worker.task_finished.connect(self.on_task_finished)
# # # # #         self.task_worker.finished.connect(self.task_worker.deleteLater)
# # # # #         self.task_worker.start()

# # # # #     @Slot(str)
# # # # #     def on_task_finished(self, description: str):
# # # # #         # (このメソッドは変更なし)
# # # # #         print("Visual Observer(指揮官): 実行部隊が帰還。報告を受理しました。")
# # # # #         if description and "特に変化はありません" not in description and "エラーが発生しました" not in description:
# # # # #             print(f"Visual Observer(指揮官): 有意な変化を検出、本部に報告します: {description}")
# # # # #             self.observation_ready.emit(description)
# # # # #             self.previous_description = description
# # # # #         self._is_task_running = False

# # # # #     @Slot(Image.Image)
# # # # #     def update_frame(self, image: Image.Image):
# # # # #         self.latest_frame = image

# # # # #     def stop(self):
# # # # #         """スレッドを安全に停止させる"""
# # # # #         print("Visual Observer(指揮官)の停止処理を開始します。")
# # # # #         # --- ここが修正箇所 ---
# # # # #         # タイマーを直接止めずに、イベントループの終了だけを要求する
# # # # #         self.quit()
# # # # #         self.wait()
# # # # #         print("Visual Observerワーカーを完全に停止しました。")












# # # # # src/core/visual_observer.py　そもそもQtタイマーを使わせない版(main_windowで処理する)
# # # # # src/core/visual_observer.py

# # # # from PySide6.QtCore import QThread, Signal, Slot
# # # # from PIL import Image
# # # # from typing import Optional
# # # # from .gemini_client import GeminiClient

# # # # class ObservationTaskWorker(QThread):
# # # #     task_finished = Signal(str)
# # # #     def __init__(self, gemini_client: GeminiClient, frame: Image.Image, prev_desc: str, parent=None):
# # # #         super().__init__(parent) # 親オブジェクトを受け取る
# # # #         self.gemini_client = gemini_client
# # # #         self.frame_to_analyze = frame
# # # #         self.previous_description = prev_desc
# # # #     def run(self):
# # # #         print("ObservationTaskWorker: AIへの画像分析を開始します。")
# # # #         description = ""
# # # #         try:
# # # #             prompt = f"""あなたはユーザーの勉強の様子を観察するAIです。\n以下の画像は現在のユーザーの机の様子です。\n前回の観察結果は「{self.previous_description}」でした。\n現在の画像と前回の結果を比較し、ユーザーの行動に何か特筆すべき変化があれば簡潔に報告してください。\n例: 「新しい数式を書き始めたようです」「問題の特定の部分を指差しています」など。\n特に大きな変化がなければ「特に変化はありません」と報告してください。"""
# # # #             prompt_parts = [prompt, self.frame_to_analyze]
# # # #             description = self.gemini_client.generate_vision_response(prompt_parts)
# # # #         except Exception as e:
# # # #             print(f"ObservationTaskWorker: 分析中にエラーが発生しました: {e}")
# # # #             description = "分析中にエラーが発生しました。"
# # # #         finally:
# # # #             self.task_finished.emit(description)
# # # #             print("ObservationTaskWorker: タスク完了。")


# # # # class VisualObserverWorker(QThread):
# # # #     observation_ready = Signal(str)

# # # #     def __init__(self, gemini_client: GeminiClient, interval_sec=30, parent=None):
# # # #         super().__init__(parent)
# # # #         self.gemini_client = gemini_client
# # # #         self.interval = interval_sec
# # # #         self.latest_frame: Optional[Image.Image] = None
# # # #         self.previous_description: str = "まだ観測を開始していません。"
# # # #         self._is_task_running = False
# # # #         self._is_running = True

# # # #     def run(self):
# # # #         print(f"Visual Observer(指揮官)が起動しました。（{self.interval}秒間隔）")
# # # #         while self._is_running:
# # # #             if not self._is_task_running and self.latest_frame is not None:
# # # #                 self.trigger_observation_task()
            
# # # #             for _ in range(self.interval):
# # # #                 if not self._is_running: break
# # # #                 self.msleep(1000)
        
# # # #         print("Visual Observer: メインループを終了しました。")

# # # #     def trigger_observation_task(self):
# # # #         self._is_task_running = True
# # # #         print("Visual Observer(指揮官): 実行部隊に出撃を命令！")
# # # #         frame_copy = self.latest_frame.copy()
        
# # # #         # --- ここが修正箇所 ---
# # # #         # 実行部隊に、自分自身を親として設定する
# # # #         task_worker = ObservationTaskWorker(
# # # #             self.gemini_client, frame_copy, self.previous_description, parent=self
# # # #         )
# # # #         task_worker.task_finished.connect(self.on_task_finished)
# # # #         # deleteLater()は親子関係に任せるため不要
# # # #         task_worker.finished.connect(task_worker.deleteLater) # 安全のため残しても良い
# # # #         task_worker.start()

# # # #     @Slot(str)
# # # #     def on_task_finished(self, description: str):
# # # #         print("Visual Observer(指揮官): 実行部隊が帰還。報告を受理しました。")
# # # #         if description and "特に変化はありません" not in description and "エラーが発生しました" not in description:
# # # #             print(f"Visual Observer(指揮官): 有意な変化を検出、本部に報告します: {description}")
# # # #             self.observation_ready.emit(description)
# # # #             self.previous_description = description
# # # #         self._is_task_running = False

# # # #     @Slot(Image.Image)
# # # #     def update_frame(self, image: Image.Image):
# # # #         self.latest_frame = image

# # # #     def stop(self):
# # # #         print("Visual Observer(指揮官)の停止処理を開始します。")
# # # #         self._is_running = False


























# # # # src/core/visual_observer.py  main_windowと親子関係の解消
# # # # src/core/visual_observer.pyインスタンス変数として参照を保持する

# # # from PySide6.QtCore import QThread, Signal, Slot
# # # from PIL import Image
# # # from typing import Optional
# # # from .gemini_client import GeminiClient

# # # # ObservationTaskWorkerは変更なし
# # # class ObservationTaskWorker(QThread):
# # #     task_finished = Signal(str)
# # #     def __init__(self, gemini_client: GeminiClient, frame: Image.Image, prev_desc: str, parent=None):
# # #         super().__init__(parent)
# # #         self.gemini_client = gemini_client
# # #         self.frame_to_analyze = frame
# # #         self.previous_description = prev_desc
# # #     def run(self):
# # #         print("ObservationTaskWorker: AIへの画像分析を開始します。")
# # #         description = ""
# # #         try:
# # #             prompt = f"""あなたはユーザーの勉強の様子を観察するAIです。\n以下の画像は現在のユーザーの机の様子です。\n前回の観察結果は「{self.previous_description}」でした。\n現在の画像と前回の結果を比較し、ユーザーの行動に何か特筆すべき変化があれば簡潔に報告してください。\n例: 「新しい数式を書き始めたようです」「問題の特定の部分を指差しています」など。\n特に大きな変化がなければ「特に変化はありません」と報告してください。"""
# # #             prompt_parts = [prompt, self.frame_to_analyze]
# # #             description = self.gemini_client.generate_vision_response(prompt_parts)
# # #         except Exception as e:
# # #             print(f"ObservationTaskWorker: 分析中にエラーが発生しました: {e}")
# # #             description = "分析中にエラーが発生しました。"
# # #         finally:
# # #             self.task_finished.emit(description)
# # #             print("ObservationTaskWorker: タスク完了。")


# # # class VisualObserverWorker(QThread):
# # #     observation_ready = Signal(str)

# # #     def __init__(self, gemini_client: GeminiClient, interval_sec=60, parent=None):
# # #         super().__init__(parent)
# # #         self.gemini_client = gemini_client
# # #         self.interval = interval_sec
# # #         self.latest_frame: Optional[Image.Image] = None
# # #         self.previous_description: str = "まだ観測を開始していません。"
# # #         self._is_task_running = False
# # #         self._is_running = True
        
# # #         # --- ここからが修正箇所 ---
# # #         # 実行中のタスクワーカーへの参照を保持するインスタンス変数を追加
# # #         self.task_worker: Optional[ObservationTaskWorker] = None

# # #     def run(self):
# # #         print(f"Visual Observer(指揮官)が起動しました。（{self.interval}秒間隔）")
# # #         while self._is_running:
# # #             if not self._is_task_running and self.latest_frame is not None:
# # #                 self.trigger_observation_task()
            
# # #             for _ in range(self.interval):
# # #                 if not self._is_running: break
# # #                 self.msleep(1000)
        
# # #         print("Visual Observer: メインループを終了しました。")

# # #     def trigger_observation_task(self):
# # #         self._is_task_running = True
# # #         print("Visual Observer(指揮官): 実行部隊に出撃を命令！")
# # #         frame_copy = self.latest_frame.copy()
        
# # #         # --- ここが修正箇所 ---
# # #         # 実行部隊をインスタンス変数に保持して、参照が消えないようにする
# # #         self.task_worker = ObservationTaskWorker(
# # #             self.gemini_client, frame_copy, self.previous_description
# # #         )
# # #         self.task_worker.task_finished.connect(self.on_task_finished)
# # #         self.task_worker.finished.connect(self.task_worker.deleteLater)
# # #         self.task_worker.start()

# # #     @Slot(str)
# # #     def on_task_finished(self, description: str):
# # #         print("Visual Observer(指揮官): 実行部隊が帰還。報告を受理しました。")
# # #         if description and "特に変化はありません" not in description and "エラーが発生しました" not in description:
# # #             print(f"Visual Observer(指揮官): 有意な変化を検出、本部に報告します: {description}")
# # #             self.observation_ready.emit(description)
# # #             self.previous_description = description
        
# # #         # --- ここが修正箇所 ---
# # #         # タスクが完了したら、参照を解放する
# # #         self._is_task_running = False
# # #         self.task_worker = None # これでガベージコレクタが安全に回収できる

# # #     @Slot(Image.Image)
# # #     def update_frame(self, image: Image.Image):
# # #         self.latest_frame = image

# # #     def stop(self):
# # #         print("Visual Observer(指揮官)の停止処理を開始します。")
# # #         self._is_running = False











































# # # src/core/visual_observer.py

# # from PySide6.QtCore import QThread, Signal, Slot
# # from PIL import Image
# # from typing import Optional
# # from .gemini_client import GeminiClient

# # class ObservationTaskWorker(QThread):
# #     task_finished = Signal(str)
# #     def __init__(self, gemini_client: GeminiClient, frame: Image.Image, prev_desc: str, parent=None):
# #         super().__init__(parent)
# #         self.gemini_client = gemini_client
# #         self.frame_to_analyze = frame
# #         self.previous_description = prev_desc
# #     def run(self):
# #         print("ObservationTaskWorker: AIへの画像分析を開始します。")
# #         description = ""
# #         try:
# #             prompt = f"""あなたはユーザーの勉強の様子を観察するAIです。\n以下の画像は現在のユーザーの机の様子です。\n前回の観察結果は「{self.previous_description}」でした。\n現在の画像と前回の結果を比較し、ユーザーの行動に何か特筆すべき変化があれば簡潔に報告してください。\n例: 「新しい数式を書き始めたようです」「問題の特定の部分を指差しています」など。\n特に大きな変化がなければ「特に変化はありません」と報告してください。"""
# #             prompt_parts = [prompt, self.frame_to_analyze]
# #             description = self.gemini_client.generate_vision_response(prompt_parts)
# #         except Exception as e:
# #             print(f"ObservationTaskWorker: 分析中にエラーが発生しました: {e}")
# #             description = "分析中にエラーが発生しました。"
# #         finally:
# #             self.task_finished.emit(description)
# #             print("ObservationTaskWorker: タスク完了。")


# # class VisualObserverWorker(QThread):
# #     observation_ready = Signal(str)

# #     def __init__(self, gemini_client: GeminiClient, interval_sec=30, parent=None):
# #         super().__init__(parent)
# #         self.gemini_client = gemini_client
# #         self.interval = interval_sec
# #         self.latest_frame: Optional[Image.Image] = None
# #         self.previous_description: str = "まだ観測を開始していません。"
# #         self._is_task_running = False
# #         self._is_running = True
# #         self.task_worker: Optional[ObservationTaskWorker] = None

# #     def run(self):
# #         print(f"Visual Observer(指揮官)が起動しました。（{self.interval}秒間隔）")
# #         while self._is_running:
# #             if not self._is_task_running and self.latest_frame is not None:
# #                 self.trigger_observation_task()
            
# #             # 1秒ごとに停止フラグを確認するループに変更
# #             for _ in range(self.interval):
# #                 if not self._is_running:
# #                     break
# #                 self.msleep(1000)
        
# #         print("Visual Observer: メインループを終了しました。")

# #     def trigger_observation_task(self):
# #         self._is_task_running = True
# #         print("Visual Observer(指揮官): 実行部隊に出撃を命令！")
# #         frame_copy = self.latest_frame.copy()
        
# #         self.task_worker = ObservationTaskWorker(
# #             self.gemini_client, frame_copy, self.previous_description
# #         )
# #         self.task_worker.task_finished.connect(self.on_task_finished)
# #         self.task_worker.finished.connect(self.task_worker.deleteLater)
# #         self.task_worker.start()

# #     @Slot(str)
# #     def on_task_finished(self, description: str):
# #         print("Visual Observer(指揮官): 実行部隊が帰還。報告を受理しました。")
# #         if description and "特に変化はありません" not in description and "エラーが発生しました" not in description:
# #             print(f"Visual Observer(指揮官): 有意な変化を検出、本部に報告します: {description}")
# #             self.observation_ready.emit(description)
# #             self.previous_description = description
        
# #         # --- ↓↓↓ ここが修正箇所 ↓↓↓ ---
# #         self._is_task_running = False
# #         # self.task_worker = None # この行を削除。参照は次のタスクで上書きされるまで保持する。
# #         # --- ↑↑↑ ここが修正箇所 ↑↑↑ ---


# #     @Slot(Image.Image)
# #     def update_frame(self, image: Image.Image):
# #         self.latest_frame = image

# #     def stop(self):
# #         print("Visual Observer(指揮官)の停止処理を開始します。")
# #         self._is_running = False
# #         if self.task_worker and self.task_worker.isRunning():
# #             print("Visual Observer: 実行中の分析タスクの完了を待ちます...")
# #             self.task_worker.wait()
# #         self.wait() # 自分自身のスレッドの終了を待つ


















# # src/core/visual_observer.py  ジェミニモデル指定&プロンプト調整# src/core/visual_observer.py

# from PySide6.QtCore import QThread, Signal, Slot
# from PIL import Image
# from typing import Optional
# from .gemini_client import GeminiClient
# from .settings_manager import SettingsManager

# class ObservationTaskWorker(QThread):
#     task_finished = Signal(str)
#     def __init__(self, gemini_client: GeminiClient, frame: Image.Image, prev_desc: str, parent=None):
#         super().__init__(parent)
#         self.gemini_client = gemini_client
#         self.frame_to_analyze = frame
#         self.previous_description = prev_desc
        
#     def run(self):
#         print("ObservationTaskWorker: AIへの画像分析を開始します。")
#         description = ""
#         try:
#             settings = SettingsManager()
#             # プロパティ形式でプロンプトを取得
#             prompt_template = settings.observation_prompt
#             prompt = prompt_template.format(previous_description=self.previous_description)
            
#             prompt_parts = [prompt, self.frame_to_analyze]
#             description = self.gemini_client.generate_vision_response(prompt_parts)
#         except Exception as e:
#             print(f"ObservationTaskWorker: 分析中にエラーが発生しました: {e}")
#             description = "分析中にエラーが発生しました。"
#         finally:
#             self.task_finished.emit(description)
#             print("ObservationTaskWorker: タスク完了。")


# class VisualObserverWorker(QThread):
#     observation_ready = Signal(str)

#     def __init__(self, interval_sec=30, parent=None):
#         super().__init__(parent)
        
#         settings = SettingsManager()
#         # プロパティ形式でモデル名を取得
#         self.gemini_client = GeminiClient(vision_model_name=settings.vision_model)
        
#         self.interval = interval_sec
#         self.latest_frame: Optional[Image.Image] = None
#         self.previous_description: str = "まだ観測を開始していません。"
#         self._is_task_running = False
#         self._is_running = True
#         self.task_worker: Optional[ObservationTaskWorker] = None

#     def run(self):
#         print(f"Visual Observer(指揮官)が起動しました。（{self.interval}秒間隔）")
#         while self._is_running:
#             if not self._is_task_running and self.latest_frame is not None:
#                 self.trigger_observation_task()
            
#             for _ in range(self.interval):
#                 if not self._is_running:
#                     break
#                 self.msleep(1000)
        
#         print("Visual Observer: メインループを終了しました。")

#     def trigger_observation_task(self):
#         self._is_task_running = True
#         print("Visual Observer(指揮官): 実行部隊に出撃を命令！")
#         frame_copy = self.latest_frame.copy()
        
#         self.task_worker = ObservationTaskWorker(
#             self.gemini_client, frame_copy, self.previous_description
#         )
#         self.task_worker.task_finished.connect(self.on_task_finished)
#         self.task_worker.finished.connect(self.task_worker.deleteLater)
#         self.task_worker.start()

#     @Slot(str)
#     def on_task_finished(self, description: str):
#         print("Visual Observer(指揮官): 実行部隊が帰還。報告を受理しました。")
#         if description and "特に変化はありません" not in description and "エラーが発生しました" not in description:
#             print(f"Visual Observer(指揮官): 有意な変化を検出、本部に報告します: {description}")
#             self.observation_ready.emit(description)
#             self.previous_description = description
        
#         self._is_task_running = False

#     @Slot(Image.Image)
#     def update_frame(self, image: Image.Image):
#         self.latest_frame = image

#     def stop(self):
#         print("Visual Observer(指揮官)の停止処理を開始します。")
#         self._is_running = False
#         if self.task_worker and self.task_worker.isRunning():
#             print("Visual Observer: 実行中の分析タスクの完了を待ちます...")
#             self.task_worker.wait()
#         self.wait()
#         print("Visual Observerを完全に停止しました。")














# 設定変更(再起不要版)


from PySide6.QtCore import QThread, Signal, Slot
from PIL import Image
from typing import Optional
from .gemini_client import GeminiClient
from .settings_manager import SettingsManager

class ObservationTaskWorker(QThread):
    task_finished = Signal(str)
    def __init__(self, gemini_client: GeminiClient, frame: Image.Image, prev_desc: str, parent=None):
        super().__init__(parent)
        self.gemini_client = gemini_client
        self.frame_to_analyze = frame
        self.previous_description = prev_desc
        
    def run(self):
        print("ObservationTaskWorker: AIへの画像分析を開始します。")
        description = ""
        try:
            settings = SettingsManager()
            # プロパティ形式でプロンプトを取得
            prompt_template = settings.observation_prompt
            prompt = prompt_template.format(previous_description=self.previous_description)
            
            prompt_parts = [prompt, self.frame_to_analyze]
            description = self.gemini_client.generate_vision_response(prompt_parts)
        except Exception as e:
            print(f"ObservationTaskWorker: 分析中にエラーが発生しました: {e}")
            description = "分析中にエラーが発生しました。"
        finally:
            self.task_finished.emit(description)
            print("ObservationTaskWorker: タスク完了。")


class VisualObserverWorker(QThread):
    observation_ready = Signal(str)

    def __init__(self, interval_sec=30, parent=None):
        super().__init__(parent)
        
        settings = SettingsManager()
        # プロパティ形式でモデル名を取得
        self.gemini_client = GeminiClient(vision_model_name=settings.vision_model)
        
        self.interval = interval_sec
        self.latest_frame: Optional[Image.Image] = None
        self.previous_description: str = "まだ観測を開始していません。"
        self._is_task_running = False
        self._is_running = True
        self.task_worker: Optional[ObservationTaskWorker] = None

    def run(self):
        print(f"Visual Observer(指揮官)が起動しました。") # 初回起動メッセージ
        while self._is_running:
            # 常に self.interval を参照するようにループを調整
            current_interval = self.interval 
            
            if not self._is_task_running and self.latest_frame is not None:
                print(f"Visual Observer: 次の観測まで {current_interval} 秒待機します。")
                self.trigger_observation_task()
            
            # 1秒ごとに停止フラグを確認しながら待機
            for _ in range(current_interval):
                if not self._is_running:
                    break
                self.msleep(1000)
        
        print("Visual Observer: メインループを終了しました。")

    def trigger_observation_task(self):
        self._is_task_running = True
        print("Visual Observer(指揮官): 実行部隊に出撃を命令！")
        frame_copy = self.latest_frame.copy()
        
        self.task_worker = ObservationTaskWorker(
            self.gemini_client, frame_copy, self.previous_description
        )
        self.task_worker.task_finished.connect(self.on_task_finished)
        self.task_worker.finished.connect(self.task_worker.deleteLater)
        self.task_worker.start()

    @Slot(str)
    def on_task_finished(self, description: str):
        print("Visual Observer(指揮官): 実行部隊が帰還。報告を受理しました。")
        if description and "特に変化はありません" not in description and "エラーが発生しました" not in description:
            print(f"Visual Observer(指揮官): 有意な変化を検出、本部に報告します: {description}")
            self.observation_ready.emit(description)
            self.previous_description = description
        
        self._is_task_running = False

    @Slot(Image.Image)
    def update_frame(self, image: Image.Image):
        self.latest_frame = image

    @Slot(int)
    def set_observation_interval(self, seconds: int):
        """定点観測の間隔を更新するスロット"""
        print(f"定点観測の間隔を {seconds} 秒に更新しました。")
        self.interval = seconds

    def stop(self):
        print("Visual Observer(指揮官)の停止処理を開始します。")
        self._is_running = False
        if self.task_worker and self.task_worker.isRunning():
            print("Visual Observer: 実行中の分析タスクの完了を待ちます...")
            self.task_worker.wait()
        self.wait()
        print("Visual Observerを完全に停止しました。")
# # # # # # src/hardware/audio_handler.py

# # # # # import pyttsx3
# # # # # import speech_recognition as sr
# # # # # from PySide6.QtCore import QThread, Signal, Slot
# # # # # import time

# # # # # # TTSWorkerは変更なし
# # # # # class TTSWorker(QThread):
# # # # #     speech_finished = Signal()
# # # # #     def __init__(self, parent=None):
# # # # #         super().__init__(parent)
# # # # #         self.text_to_speak_queue = []
# # # # #         self._is_running = True
# # # # #     def run(self):
# # # # #         while self._is_running:
# # # # #             if self.text_to_speak_queue:
# # # # #                 text = self.text_to_speak_queue.pop(0)
# # # # #                 engine = None
# # # # #                 try:
# # # # #                     engine = pyttsx3.init()
# # # # #                     engine.say(text)
# # # # #                     engine.runAndWait()
# # # # #                     self.speech_finished.emit()
# # # # #                 except Exception as e:
# # # # #                     print(f"TTSのエンジン処理中にエラーが発生しました: {e}")
# # # # #                     self.speech_finished.emit()
# # # # #                 finally:
# # # # #                     if engine:
# # # # #                         engine.stop()
# # # # #                     del engine
# # # # #             else:
# # # # #                 self.msleep(100)
# # # # #     @Slot(str)
# # # # #     def speak(self, text):
# # # # #         self.text_to_speak_queue.append(text)
# # # # #     def stop(self):
# # # # #         self._is_running = False
# # # # #         self.text_to_speak_queue.clear()
# # # # #         self.wait()
# # # # #         print("TTSワーカーを停止しました。")

# # # # # # --- ここからがSTTWorkerの修正 ---
# # # # # class STTWorker(QThread):
# # # # #     """
# # # # #     マイクからの音声を「命令（ウェイクワードあり）」と「独り言（ウェイクワードなし）」に
# # # # #     分類して通知するワーカー。
# # # # #     """
# # # # #     # 1. 独り言を通知するシグナル（旧 recognized_text）
# # # # #     monologue_recognized = Signal(str)
# # # # #     # 2. 命令を通知する新しいシグナル
# # # # #     command_recognized = Signal(str)

# # # # #     def __init__(self, parent=None):
# # # # #         super().__init__(parent)
# # # # #         self.recognizer = sr.Recognizer()
# # # # #         self.microphone = sr.Microphone()
# # # # #         self._is_running = True
# # # # #         self._is_enabled = False
# # # # #         self.stop_listening = None
        
# # # # #         # --- ウェイクワードの定義 ---
# # # # #         # 複数の言い方に対応できるようにリストで定義
# # # # #         self.wake_words = ["okアシスタント", "ok アシスタント", "ねえアシスタント", "ねえ アシスタント"]

# # # # #     def _on_speech_recognized(self, recognizer, audio_data):
# # # # #         """
# # # # #         音声が認識されるたびに呼び出され、内容を分類するコールバック関数。
# # # # #         """
# # # # #         if not self._is_enabled: return

# # # # #         print("音声データを認識試行中...")
# # # # #         try:
# # # # #             # 認識したテキストを小文字に変換して、判定しやすくする
# # # # #             text = recognizer.recognize_google(audio_data, language='ja-JP').lower()
# # # # #             print(f"認識されたテキスト: {text}")

# # # # #             found_wake_word = None
# # # # #             for wake_word in self.wake_words:
# # # # #                 if text.startswith(wake_word):
# # # # #                     found_wake_word = wake_word
# # # # #                     break
            
# # # # #             if found_wake_word:
# # # # #                 # ウェイクワードが見つかった場合
# # # # #                 # ウェイクワード部分を取り除いた、命令本体のテキストを抽出
# # # # #                 command_body = text[len(found_wake_word):].strip()
# # # # #                 if command_body: # 命令本体があれば
# # # # #                     print(f"命令を検出しました: {command_body}")
# # # # #                     self.command_recognized.emit(command_body)
# # # # #                 else: # "OKアシスタント" だけ言われた場合
# # # # #                     print("ウェイクワードのみ検出しました。")
# # # # #                     # 必要であれば、何か応答を返すためのシグナルを別途用意することも可能
# # # # #             else:
# # # # #                 # ウェイクワードが見つからなかった場合 -> 独り言として処理
# # # # #                 print(f"独り言を検出しました: {text}")
# # # # #                 self.monologue_recognized.emit(text)

# # # # #         except sr.UnknownValueError:
# # # # #             print("音声を認識できませんでした。")
# # # # #         except sr.RequestError as e:
# # # # #             print(f"APIサービスエラー: {e}")

# # # # #     def run(self):
# # # # #         print("STTワーカーが起動しました。")
# # # # #         with self.microphone as source:
# # # # #             self.recognizer.adjust_for_ambient_noise(source)
# # # # #         self.stop_listening = self.recognizer.listen_in_background(
# # # # #             self.microphone, self._on_speech_recognized
# # # # #         )
# # # # #         print("バックグラウンドでの音声認識を開始しました。")
# # # # #         while self._is_running:
# # # # #             time.sleep(0.1)

# # # # #     @Slot(bool)
# # # # #     def set_enabled(self, enabled: bool):
# # # # #         self._is_enabled = enabled
# # # # #         if enabled:
# # # # #             print("音声認識が有効になりました。")
# # # # #         else:
# # # # #             print("音声認識が無効になりました。")

# # # # #     def stop(self):
# # # # #         print("STTワーカーの停止処理を開始します。")
# # # # #         self._is_running = False
# # # # #         if self.stop_listening:
# # # # #             self.stop_listening(wait_for_stop=False)
# # # # #             print("バックグラウンドリスニングを停止しました。")
# # # # #         self.wait()
# # # # #         print("STTワーカーを完全に停止しました。")

















# # # # # src/hardware/audio_handler.py読み上げ中断機能

# # # # import pyttsx3
# # # # import speech_recognition as sr
# # # # from PySide6.QtCore import QThread, Signal, Slot
# # # # import time

# # # # class TTSWorker(QThread):
# # # #     speech_finished = Signal()
# # # #     def __init__(self, parent=None):
# # # #         super().__init__(parent)
# # # #         self.text_to_speak_queue = []
# # # #         self._is_running = True
# # # #         self.engine = None # エンジンをインスタンス変数として保持

# # # #     def run(self):
# # # #         while self._is_running:
# # # #             if self.text_to_speak_queue:
# # # #                 text = self.text_to_speak_queue.pop(0)
# # # #                 try:
# # # #                     # エンジンを初期化
# # # #                     self.engine = pyttsx3.init()
# # # #                     self.engine.say(text)
# # # #                     print(f"「{text[:20]}...」を読み上げます。")
# # # #                     self.engine.runAndWait()
                    
# # # #                     # runAndWait()が正常に完了した場合もエンジンをNoneに戻す
# # # #                     self.engine = None
# # # #                     self.speech_finished.emit()
                    
# # # #                 except Exception as e:
# # # #                     print(f"TTSのエンジン処理中にエラーが発生しました: {e}")
# # # #                     self.engine = None
# # # #                     self.speech_finished.emit() # エラーでもシグナルを発行
# # # #             else:
# # # #                 self.msleep(100)

# # # #     @Slot(str)
# # # #     def speak(self, text):
# # # #         self.text_to_speak_queue.append(text)

# # # #     # --- ここからが新しいメソッド ---
# # # #     @Slot()
# # # #     def stop_current_speech(self):
# # # #         """
# # # #         現在実行中の読み上げを強制的に停止させるためのスロット。
# # # #         """
# # # #         if self.engine is not None:
# # # #             print("読み上げ停止命令を受信しました。")
# # # #             # キューに残っている読み上げ予定はすべてクリア
# # # #             self.text_to_speak_queue.clear()
# # # #             # pyttsx3のエンジンを停止させる
# # # #             self.engine.stop()

# # # #     def stop(self):
# # # #         """スレッド自体を安全に停止させる"""
# # # #         self._is_running = False
# # # #         self.stop_current_speech() # 停止時に現在の読み上げも中断
# # # #         self.wait()
# # # #         print("TTSワーカーを停止しました。")


# # # # # STTWorkerは変更なし
# # # # class STTWorker(QThread):
# # # #     monologue_recognized = Signal(str)
# # # #     command_recognized = Signal(str)
# # # #     # def __init__(self, parent=None):
# # # #     #     super().__init__(parent)
# # # #     #     self.recognizer = sr.Recognizer(); self.microphone = sr.Microphone()
# # # #     #     self._is_running = True; self._is_enabled = False; self.stop_listening = None
# # # #     #     self.wake_words = ["okアシスタント", "ok アシスタント", "ねえアシスタント", "ねえ アシスタント"]
# # # #     def __init__(self, parent=None):
# # # #         super().__init__(parent)
# # # #         self.recognizer = sr.Recognizer()
        
# # # #         # --- ここからが修正箇所 ---
# # # #         # 使用するマイクのデバイスインデックスを明示的に指定します。
# # # #         # まずはインデックス32を試してみましょう。
# # # #         try:
# # # #             self.microphone = sr.Microphone(device_index=32)
# # # #             print("マイクデバイス（インデックス32）を正常に選択しました。")
# # # #         except Exception as e:
# # # #             print(f"指定されたマイク（インデックス32）の初期化に失敗しました: {e}")
# # # #             print("デフォルトのマイクで続行します。")
# # # #             self.microphone = sr.Microphone()
            
# # # #         self._is_running = True
# # # #         self._is_enabled = False
# # # #         self.stop_listening = None
# # # #         self.wake_words = ["okアシスタント", "ok アシスタント", "ねえアシスタント", "ねえ アシスタント"]
# # # #     def _on_speech_recognized(self, recognizer, audio_data):
# # # #         if not self._is_enabled: return
# # # #         try:
# # # #             text = recognizer.recognize_google(audio_data, language='ja-JP').lower()
# # # #             print(f"認識されたテキスト: {text}")
# # # #             found_wake_word = next((word for word in self.wake_words if text.startswith(word)), None)
# # # #             if found_wake_word:
# # # #                 command_body = text[len(found_wake_word):].strip()
# # # #                 if command_body: self.command_recognized.emit(command_body)
# # # #             else:
# # # #                 self.monologue_recognized.emit(text)
# # # #         except (sr.UnknownValueError, sr.RequestError) as e: print(f"音声認識エラー: {e}")
# # # #     def run(self):
# # # #         print("STTワーカーが起動しました。")
# # # #         with self.microphone as source: self.recognizer.adjust_for_ambient_noise(source)
# # # #         self.stop_listening = self.recognizer.listen_in_background(self.microphone, self._on_speech_recognized)
# # # #         while self._is_running: time.sleep(0.1)
# # # #     @Slot(bool)
# # # #     def set_enabled(self, enabled: bool): self._is_enabled = enabled; print(f"音声認識が{'有効' if enabled else '無効'}になりました。")
# # # #     def stop(self):
# # # #         self._is_running = False
# # # #         if self.stop_listening: self.stop_listening(wait_for_stop=False)
# # # #         self.wait(); print("STTワーカーを停止しました。")






# # # # src/hardware/audio_handler.py

# # # import pyttsx3
# # # import speech_recognition as sr
# # # from PySide6.QtCore import QThread, Signal, Slot
# # # import time

# # # # TTSWorkerは変更なし
# # # class TTSWorker(QThread):
# # #     speech_finished = Signal()
# # #     def __init__(self, parent=None):
# # #         super().__init__(parent)
# # #         self.text_to_speak_queue = []
# # #         self._is_running = True
# # #         self.engine = None
# # #     def run(self):
# # #         while self._is_running:
# # #             if self.text_to_speak_queue:
# # #                 text = self.text_to_speak_queue.pop(0)
# # #                 try:
# # #                     self.engine = pyttsx3.init()
# # #                     self.engine.say(text)
# # #                     print(f"「{text[:20]}...」を読み上げます。")
# # #                     self.engine.runAndWait()
# # #                     self.engine = None
# # #                     self.speech_finished.emit()
# # #                 except Exception as e:
# # #                     print(f"TTSのエンジン処理中にエラーが発生しました: {e}")
# # #                     self.engine = None
# # #                     self.speech_finished.emit()
# # #             else:
# # #                 self.msleep(100)
# # #     @Slot(str)
# # #     def speak(self, text):
# # #         self.text_to_speak_queue.append(text)
# # #     @Slot()
# # #     def stop_current_speech(self):
# # #         if self.engine is not None:
# # #             print("読み上げ停止命令を受信しました。")
# # #             self.text_to_speak_queue.clear()
# # #             self.engine.stop()
# # #     def stop(self):
# # #         self._is_running = False
# # #         self.stop_current_speech()
# # #         self.wait()
# # #         print("TTSワーカーを停止しました。")

# # # class STTWorker(QThread):
# # #     monologue_recognized = Signal(str)
# # #     command_recognized = Signal(str)
    
# # #     def __init__(self, parent=None):
# # #         super().__init__(parent)
# # #         self.recognizer = sr.Recognizer()
        
# # #         # --- ここからが修正箇所 ---
# # #         # 使用するマイクのデバイスインデックスを明示的に指定します。
# # #         # ご提示のリストからインデックス3を選択します。
# # #         MICROPHONE_DEVICE_INDEX = 3
        
# # #         try:
# # #             self.microphone = sr.Microphone(device_index=MICROPHONE_DEVICE_INDEX)
# # #             print(f"マイクデバイス（インデックス{MICROPHONE_DEVICE_INDEX}）を正常に選択しました。")
# # #         except Exception as e:
# # #             print(f"指定されたマイク（インデックス{MICROPHONE_DEVICE_INDEX}）の初期化に失敗しました: {e}")
# # #             print("デフォルトのマイクで続行します。")
# # #             self.microphone = sr.Microphone()
            
# # #         self._is_running = True
# # #         self._is_enabled = False
# # #         self.stop_listening = None
# # #         self.wake_words = ["okアシスタント", "ok アシスタント", "ねえアシスタント", "ねえ アシスタント"]

# # #     def _on_speech_recognized(self, recognizer, audio_data):
# # #         if not self._is_enabled: return
# # #         try:
# # #             text = recognizer.recognize_google(audio_data, language='ja-JP').lower()
# # #             print(f"認識されたテキスト: {text}")
# # #             found_wake_word = next((word for word in self.wake_words if text.startswith(word)), None)
# # #             if found_wake_word:
# # #                 command_body = text[len(found_wake_word):].strip()
# # #                 if command_body: self.command_recognized.emit(command_body)
# # #             else:
# # #                 self.monologue_recognized.emit(text)
# # #         except (sr.UnknownValueError, sr.RequestError) as e:
# # #             print(f"音声認識エラー: {e}")

# # #     def run(self):
# # #         print("STTワーカーが起動しました。")
# # #         try:
# # #             with self.microphone as source:
# # #                 print("マイクのノイズレベルを調整中...")
# # #                 self.recognizer.adjust_for_ambient_noise(source)
# # #                 print("ノイズ調整完了。")
# # #             self.stop_listening = self.recognizer.listen_in_background(self.microphone, self._on_speech_recognized)
# # #             print("バックグラウンドでの音声認識を開始しました。")
# # #             while self._is_running:
# # #                 time.sleep(0.1)
# # #         except Exception as e:
# # #             print(f"STTワーカーの実行中に致命的なエラーが発生しました: {e}")

# # #     @Slot(bool)
# # #     def set_enabled(self, enabled: bool):
# # #         self._is_enabled = enabled
# # #         print(f"音声認識が{'有効' if enabled else '無効'}になりました。")

# # #     def stop(self):
# # #         self._is_running = False
# # #         if self.stop_listening:
# # #             self.stop_listening(wait_for_stop=False)
# # #         self.wait()
# # #         print("STTワーカーを停止しました。")























# # # src/hardware/audio_handler.py　　使用マイクの指定

# # import pyttsx3
# # import speech_recognition as sr
# # from PySide6.QtCore import QThread, Signal, Slot
# # import time

# # class TTSWorker(QThread):
# #     speech_finished = Signal()
# #     def __init__(self, parent=None):
# #         super().__init__(parent)
# #         self.text_to_speak_queue = []
# #         self._is_running = True
# #         self.engine = None

# #     def run(self):
# #         while self._is_running:
# #             if self.text_to_speak_queue:
# #                 text = self.text_to_speak_queue.pop(0)
# #                 try:
# #                     self.engine = pyttsx3.init()
# #                     self.engine.say(text)
# #                     print(f"「{text[:20]}...」を読み上げます。")
# #                     self.engine.runAndWait()
                    
# #                     self.engine = None
# #                     self.speech_finished.emit()
                    
# #                 except Exception as e:
# #                     print(f"TTSのエンジン処理中にエラーが発生しました: {e}")
# #                     self.engine = None
# #                     self.speech_finished.emit()
# #             else:
# #                 self.msleep(100)

# #     @Slot(str)
# #     def speak(self, text):
# #         self.text_to_speak_queue.append(text)

# #     @Slot()
# #     def stop_current_speech(self):
# #         if self.engine is not None:
# #             print("読み上げ停止命令を受信しました。")
# #             self.text_to_speak_queue.clear()
# #             self.engine.stop()

# #     def stop(self):
# #         self._is_running = False
# #         self.stop_current_speech()
# #         self.wait()
# #         print("TTSワーカーを停止しました。")

# # class STTWorker(QThread):
# #     monologue_recognized = Signal(str)
# #     command_recognized = Signal(str)

# #     def __init__(self, device_index=-1, parent=None):
# #         super().__init__(parent)
# #         self.recognizer = sr.Recognizer()
        
# #         # device_indexが-1ならNone（システムデフォルト）を使用
# #         mic_index = None if device_index == -1 else device_index
# #         try:
# #             self.microphone = sr.Microphone(device_index=mic_index)
# #             if mic_index is not None:
# #                 print(f"マイクデバイス（インデックス{mic_index}）を正常に選択しました。")
# #         except Exception as e:
# #             print(f"エラー: 指定されたマイク（インデックス{mic_index}）を開けませんでした。デフォルトマイクを使用します。: {e}")
# #             self.microphone = sr.Microphone()

# #         self._is_running = True
# #         self._is_enabled = False
# #         self.stop_listening = None
# #         self.wake_words = ["okアシスタント", "ok アシスタント", "ねえアシスタント", "ねえ アシスタント"]

# #     def _on_speech_recognized(self, recognizer, audio_data):
# #         if not self._is_enabled: return

# #         try:
# #             text = recognizer.recognize_google(audio_data, language='ja-JP').lower()
# #             print(f"認識されたテキスト: {text}")

# #             found_wake_word = next((word for word in self.wake_words if text.startswith(word)), None)
            
# #             if found_wake_word:
# #                 command_body = text[len(found_wake_word):].strip()
# #                 if command_body:
# #                     print(f"命令を検出しました: {command_body}")
# #                     self.command_recognized.emit(command_body)
# #             else:
# #                 print(f"独り言を検出しました: {text}")
# #                 self.monologue_recognized.emit(text)

# #         except sr.UnknownValueError:
# #             print("音声を認識できませんでした。")
# #         except sr.RequestError as e:
# #             print(f"APIサービスエラー: {e}")

# #     def run(self):
# #         print("STTワーカーが起動しました。")
# #         try:
# #             print("マイクのノイズレベルを調整中...")
# #             with self.microphone as source:
# #                 self.recognizer.adjust_for_ambient_noise(source)
# #             print("ノイズ調整完了。")
            
# #             self.stop_listening = self.recognizer.listen_in_background(
# #                 self.microphone, self._on_speech_recognized
# #             )
# #             print("バックグラウンドでの音声認識を開始しました。")
            
# #             while self._is_running:
# #                 time.sleep(0.1)
# #         except Exception as e:
# #             print(f"STTワーカーの実行中にエラーが発生しました: {e}")

# #     @Slot(bool)
# #     def set_enabled(self, enabled: bool):
# #         self._is_enabled = enabled
# #         print(f"音声認識が{'有効' if enabled else '無効'}になりました。")

# #     def stop(self):
# #         print("STTワーカーを停止します。")
# #         self._is_running = False
# #         if self.stop_listening:
# #             self.stop_listening(wait_for_stop=False)
# #             print("バックグラウンドリスニングを停止しました。")
# #         self.wait()
# #         print("STTワーカーを完全に停止しました。")




















# # src/hardware/audio_handler.py　設定にttsを追加

# import pyttsx3
# import speech_recognition as sr
# from PySide6.QtCore import QThread, Signal, Slot
# import time
# from ..core.settings_manager import SettingsManager

# class TTSWorker(QThread):
#     speech_finished = Signal()
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.text_to_speak_queue = []
#         self._is_running = True
#         self.engine = None
#         self.settings = SettingsManager()

#     def run(self):
#         while self._is_running:
#             if self.text_to_speak_queue:
#                 text = self.text_to_speak_queue.pop(0)

#                 if not self.settings.tts_enabled:
#                     print("読み上げ機能が無効のため、スキップしました。")
#                     self.speech_finished.emit()
#                     continue
                
#                 try:
#                     self.engine = pyttsx3.init()
                    
#                     rate = self.settings.tts_rate
#                     self.engine.setProperty('rate', rate)

#                     self.engine.say(text)
#                     print(f"「{text[:20]}...」を読み上げます。(速度: {rate})")
#                     self.engine.runAndWait()
                    
#                     self.engine = None
#                     self.speech_finished.emit()
                    
#                 except Exception as e:
#                     print(f"TTSのエンジン処理中にエラーが発生しました: {e}")
#                     self.engine = None
#                     self.speech_finished.emit()
#             else:
#                 self.msleep(100)

#     @Slot(str)
#     def speak(self, text):
#         self.text_to_speak_queue.append(text)

#     @Slot()
#     def stop_current_speech(self):
#         if self.engine is not None:
#             print("読み上げ停止命令を受信しました。")
#             self.text_to_speak_queue.clear()
#             self.engine.stop()

#     def stop(self):
#         self._is_running = False
#         self.stop_current_speech()
#         self.wait()
#         print("TTSワーカーを停止しました。")

# class STTWorker(QThread):
#     monologue_recognized = Signal(str)
#     command_recognized = Signal(str)

#     def __init__(self, device_index=-1, parent=None):
#         super().__init__(parent)
#         self.recognizer = sr.Recognizer()
        
#         mic_index = None if device_index == -1 else device_index
#         try:
#             self.microphone = sr.Microphone(device_index=mic_index)
#             if mic_index is not None:
#                 print(f"マイクデバイス（インデックス{mic_index}）を正常に選択しました。")
#         except Exception as e:
#             print(f"エラー: 指定されたマイク（インデックス{mic_index}）を開けませんでした。デフォルトマイクを使用します。: {e}")
#             self.microphone = sr.Microphone()

#         self._is_running = True
#         self._is_enabled = False
#         self.stop_listening = None
#         self.wake_words = ["okアシスタント", "ok アシスタント", "ねえアシスタント", "ねえ アシスタント", "OK アシスタント", "アシスタント", "あしすたんと", "あしすた", "アシスタ", "ね アシスタント"," アシスタント ", " アシスタント", "アシスタント ", " ok アシスタント"]

#     def _on_speech_recognized(self, recognizer, audio_data):
#         if not self._is_enabled: return

#         try:
#             text = recognizer.recognize_google(audio_data, language='ja-JP').lower()
#             print(f"認識されたテキスト: {text}")

#             found_wake_word = next((word for word in self.wake_words if text.startswith(word)), None)
            
#             if found_wake_word:
#                 command_body = text[len(found_wake_word):].strip()
#                 if command_body:
#                     print(f"命令を検出しました: {command_body}")
#                     self.command_recognized.emit(command_body)
#             else:
#                 print(f"独り言を検出しました: {text}")
#                 self.monologue_recognized.emit(text)

#         except sr.UnknownValueError:
#             print("音声を認識できませんでした。")
#         except sr.RequestError as e:
#             print(f"APIサービスエラー: {e}")

#     def run(self):
#         print("STTワーカーが起動しました。")
#         try:
#             print("マイクのノイズレベルを調整中...")
#             with self.microphone as source:
#                 self.recognizer.adjust_for_ambient_noise(source)
#             print("ノイズ調整完了。")
            
#             self.stop_listening = self.recognizer.listen_in_background(
#                 self.microphone, self._on_speech_recognized
#             )
#             print("バックグラウンドでの音声認識を開始しました。")
            
#             while self._is_running:
#                 time.sleep(0.1)
#         except Exception as e:
#             print(f"STTワーカーの実行中にエラーが発生しました: {e}")

#     @Slot(bool)
#     def set_enabled(self, enabled: bool):
#         self._is_enabled = enabled
#         print(f"音声認識が{'有効' if enabled else '無効'}になりました。")

#     def stop(self):
#         print("STTワーカーを停止します。")
#         self._is_running = False
#         if self.stop_listening:
#             self.stop_listening(wait_for_stop=False)
#             print("バックグラウンドリスニングを停止しました。")
#         self.wait()
#         print("STTワーカーを完全に停止しました。")


















# 設定変更(再起不要版)

import pyttsx3
import speech_recognition as sr
from PySide6.QtCore import QThread, Signal, Slot
import time
from ..core.settings_manager import SettingsManager

class TTSWorker(QThread):
    speech_finished = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.text_to_speak_queue = []
        self._is_running = True
        self.engine = None
        
        # 初期設定をSettingsManagerから読み込む
        settings = SettingsManager()
        self.tts_enabled = settings.tts_enabled
        self.tts_rate = settings.tts_rate

    def run(self):
        while self._is_running:
            if self.text_to_speak_queue:
                text = self.text_to_speak_queue.pop(0)

                # インスタンス変数を参照して読み上げを判断
                if not self.tts_enabled:
                    print("読み上げ機能が無効のため、スキップしました。")
                    self.speech_finished.emit()
                    continue
                
                try:
                    self.engine = pyttsx3.init()
                    
                    # インスタンス変数を参照して速度を設定
                    self.engine.setProperty('rate', self.tts_rate)
                    print(f"「{text[:20]}...」を読み上げます。(速度: {self.tts_rate})")

                    self.engine.say(text)
                    self.engine.runAndWait()
                    
                    self.engine = None
                    self.speech_finished.emit()
                    
                except Exception as e:
                    print(f"TTSのエンジン処理中にエラーが発生しました: {e}")
                    self.engine = None
                    self.speech_finished.emit()
            else:
                self.msleep(100)

    @Slot(bool)
    def set_tts_enabled(self, enabled: bool):
        """読み上げの有効/無効を更新する"""
        self.tts_enabled = enabled
        print(f"読み上げ機能が {'有効' if enabled else '無効'} に更新されました。")

    @Slot(int)
    def set_tts_rate(self, rate: int):
        """読み上げ速度を更新する"""
        self.tts_rate = rate
        print(f"読み上げ速度が {rate} に更新されました。")

    @Slot(str)
    def speak(self, text):
        self.text_to_speak_queue.append(text)

    @Slot()
    def stop_current_speech(self):
        if self.engine is not None:
            print("読み上げ停止命令を受信しました。")
            self.text_to_speak_queue.clear()
            self.engine.stop()

    def stop(self):
        self._is_running = False
        self.stop_current_speech()
        self.wait()
        print("TTSワーカーを停止しました。")

class STTWorker(QThread):
    monologue_recognized = Signal(str)
    command_recognized = Signal(str)

    def __init__(self, device_index=-1, parent=None):
        super().__init__(parent)
        self.recognizer = sr.Recognizer()
        
        mic_index = None if device_index == -1 else device_index
        try:
            self.microphone = sr.Microphone(device_index=mic_index)
            if mic_index is not None:
                print(f"マイクデバイス（インデックス{mic_index}）を正常に選択しました。")
            else:
                print("システム標準のマイクを選択しました。")
        except Exception as e:
            print(f"エラー: 指定されたマイク（インデックス{mic_index}）を開けませんでした。デフォルトマイクを使用します。: {e}")
            self.microphone = sr.Microphone()

        self._is_running = True
        self._is_enabled = False
        self.stop_listening = None
        self.wake_words = ["okアシスタント", "ok アシスタント", "ねえアシスタント", "ねえ アシスタント", "OK アシスタント", "アシスタント", "あしすたんと", "あしすた", "アシスタ", "ね アシスタント"," アシスタント ", " アシスタント", "アシスタント ", " ok アシスタント"]

    def _on_speech_recognized(self, recognizer, audio_data):
        if not self._is_enabled: return

        try:
            text = recognizer.recognize_google(audio_data, language='ja-JP').lower()
            print(f"認識されたテキスト: {text}")

            found_wake_word = next((word for word in self.wake_words if text.startswith(word)), None)
            
            if found_wake_word:
                command_body = text[len(found_wake_word):].strip()
                if command_body:
                    print(f"命令を検出しました: {command_body}")
                    self.command_recognized.emit(command_body)
            else:
                print(f"独り言を検出しました: {text}")
                self.monologue_recognized.emit(text)

        except sr.UnknownValueError:
            print("音声を認識できませんでした。")
        except sr.RequestError as e:
            print(f"APIサービスエラー: {e}")

    def run(self):
        print("STTワーカーが起動しました。")
        try:
            print("マイクのノイズレベルを調整中...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
            print("ノイズ調整完了。")
            
            self.stop_listening = self.recognizer.listen_in_background(
                self.microphone, self._on_speech_recognized
            )
            print("バックグラウンドでの音声認識を開始しました。")
            
            while self._is_running:
                time.sleep(0.1)
        except Exception as e:
            print(f"STTワーカーの実行中にエラーが発生しました: {e}")

    @Slot(bool)
    def set_enabled(self, enabled: bool):
        self._is_enabled = enabled
        print(f"音声認識が{'有効' if enabled else '無効'}になりました。")

    def stop(self):
        print("STTワーカーを停止します。")
        self._is_running = False
        if self.stop_listening:
            self.stop_listening(wait_for_stop=False)
            print("バックグラウンドリスニングを停止しました。")
        self.wait()
        print("STTワーカーを完全に停止しました。")
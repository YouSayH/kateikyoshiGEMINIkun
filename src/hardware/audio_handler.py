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
# src/hardware/audio_handler.py

import pyttsx3
# speech_recognitionはトップレベルでインポートしない
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
        
        settings = SettingsManager()
        self.tts_enabled = settings.tts_enabled
        self.tts_rate = settings.tts_rate

    def run(self):
        while self._is_running:
            if self.text_to_speak_queue:
                text = self.text_to_speak_queue.pop(0)

                if not self.tts_enabled:
                    print("読み上げ機能が無効のため、スキップしました。")
                    self.speech_finished.emit()
                    continue
                
                try:
                    self.engine = pyttsx3.init()
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
        self.tts_enabled = enabled
        print(f"読み上げ機能が {'有効' if enabled else '無効'} に更新されました。")

    @Slot(int)
    def set_tts_rate(self, rate: int):
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
        self.device_index = device_index
        self.recognizer = None
        self.microphone = None
        
        # srモジュールをインスタンス属性として保持
        self.sr_module = None

        self._is_running = True
        self._is_enabled = False
        self.stop_listening_callback = None
        self.wake_words = ["okアシスタント", "ok アシスタント", "ねえアシスタント", "ねえ アシスタント", "OK アシスタント", "アシスタント", "あしすたんと", "あしすた", "アシスタ", "ね アシスタント"," アシスタント ", " アシスタント", "アシスタント ", " ok アシスタント"]

    def _initialize_audio_resources(self):
        """実際に音声認識が必要になったときに初めて呼び出される初期化処理"""
        if self.recognizer is None:
            # インポートしたモジュールをインスタンス変数に保存
            import speech_recognition as sr
            print("speech_recognitionライブラリをインポート")
            self.sr_module = sr 

            print("STT: オーディオリソースを初期化します...")
            self.recognizer = self.sr_module.Recognizer()
            mic_index = None if self.device_index == -1 else self.device_index
            try:
                self.microphone = self.sr_module.Microphone(device_index=mic_index)
                with self.microphone as source:
                    print("STT: マイクのノイズレベルを調整中... (約1秒かかります)")
                    self.recognizer.adjust_for_ambient_noise(source)
                print("STT: ノイズ調整完了。")
            except Exception as e:
                print(f"エラー: マイク（インデックス{mic_index}）を開けませんでした: {e}")
                self.recognizer = None
                self.microphone = None
                self.sr_module = None # 失敗したらリセット
                return False
        return True

    def _on_speech_recognized(self, recognizer, audio_data):
        """コールバック関数。インスタンス変数経由で例外クラスにアクセスする"""
        if not self._is_enabled or self.sr_module is None: return

        try:
            text = recognizer.recognize_google(audio_data, language='ja-JP').lower()
            print(f"認識されたテキスト: {text}")

            found_wake_word = next((word for word in self.wake_words if text.startswith(word)), None)
            
            if found_wake_word:
                command_body = text[len(found_wake_word):].strip()
                if command_body:
                    self.command_recognized.emit(command_body)
            else:
                self.monologue_recognized.emit(text)

        except self.sr_module.UnknownValueError:
            pass
        except self.sr_module.RequestError as e:
            print(f"STT APIサービスエラー: {e}")
    
    def _start_listening(self):
        """バックグラウンドでの聞き取りを開始する"""
        if not self._is_enabled or self.stop_listening_callback is not None:
            return
        if not self._initialize_audio_resources():
            print("STT: オーディオリソースの初期化に失敗したため、聞き取りを開始できません。")
            return
        if self.microphone:
            self.stop_listening_callback = self.recognizer.listen_in_background(
                self.microphone, self._on_speech_recognized
            )
            print("STT: バックグラウンドでの音声認識を開始しました。")

    def _stop_listening(self):
        """バックグラウンドでの聞き取りを停止する"""
        if self.stop_listening_callback:
            self.stop_listening_callback(wait_for_stop=False)
            self.stop_listening_callback = None
            print("STT: バックグラウンドでの音声認識を停止しました。")

    def run(self):
        """スレッドは、有効/無効の状態を監視するだけ"""
        print("STTワーカーが起動しました。(監視モード)")
        while self._is_running:
            self.msleep(250)

    @Slot(bool)
    def set_enabled(self, enabled: bool):
        """UIからのトグル操作に応じて聞き取りを開始/停止する"""
        self._is_enabled = enabled
        if enabled:
            print(f"STT: 有効化命令を受信。聞き取りを開始します。")
            self._start_listening()
        else:
            print(f"STT: 無効化命令を受信。聞き取りを停止します。")
            self._stop_listening()

    def stop(self):
        """スレッドを安全に停止させる"""
        print("STTワーカーを停止します。")
        self._is_running = False
        self._stop_listening()
        self.wait()
        print("STTワーカーを完全に停止しました。")
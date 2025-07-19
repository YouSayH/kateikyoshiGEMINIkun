# src/core/visual_observer.py

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
        self.gemini_client = GeminiClient(vision_model_name=settings.vision_model)
        
        self.interval = interval_sec
        self.latest_frame: Optional[Image.Image] = None
        self.previous_description: str = "まだ観測を開始していません。"
        self._is_task_running = False
        self._is_running = True
        self.task_worker: Optional[ObservationTaskWorker] = None

    def run(self):
        print(f"Visual Observer(指揮官)が起動しました。")
        while self._is_running:
            current_interval = self.interval 
            
            if not self._is_task_running and self.latest_frame is not None:
                print(f"Visual Observer: 次の観測まで {current_interval} 秒待機します。")
                self.trigger_observation_task()
            
            for _ in range(current_interval):
                if not self._is_running:
                    break
                self.msleep(1000)
        
        print("Visual Observer: メインループを終了しました。")

    def trigger_observation_task(self):
        self._is_task_running = True
        print("Visual Observer(指揮官): 実行部隊に出撃を命令！")
        if self.latest_frame:
            frame_copy = self.latest_frame.copy()
            self.task_worker = ObservationTaskWorker(
                self.gemini_client, frame_copy, self.previous_description
            )
            self.task_worker.task_finished.connect(self.on_task_finished)
            self.task_worker.finished.connect(self.task_worker.deleteLater)
            self.task_worker.start()
        else:
            self._is_task_running = False


    @Slot(str)
    def on_task_finished(self, description: str):
        print("Visual Observer(指揮官): 実行部隊が帰還。報告を受理しました。")
        
        # 新しい説明が前回と異なり、かつ特定のキーワードを含まないことを確認
        is_significant_change = (
            description and
            description != self.previous_description and
            "特に変化はありません" not in description and
            "エラーが発生しました" not in description
        )

        if is_significant_change:
            print(f"Visual Observer(指揮官): 有意な変化を検出、本部に報告します: {description}")
            self.observation_ready.emit(description)
            self.previous_description = description
        
        self._is_task_running = False

    @Slot(Image.Image)
    def update_frame(self, image: Image.Image):
        self.latest_frame = image

    @Slot(int)
    def set_observation_interval(self, seconds: int):
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
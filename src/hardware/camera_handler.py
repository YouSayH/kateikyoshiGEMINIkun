# src/hardware/camera_handler.py

import cv2
import time
import numpy as np
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtGui import QImage
from PIL import Image as PILImage
from ultralytics import YOLO
from typing import List, Dict, Any

class CameraWorker(QThread):
    """
    カメラ映像の取得とYOLO推論を行い、UIスレッドにデータを送信するワーカー。
    - Lazy Loading: モデルの読み込みをrunメソッド内で行い、起動を高速化。
    - Frame Skipping: 一定間隔で推論を行い、実行中のCPU/GPU負荷を軽減。
    - Debouncing: 検出のチャタリング（ちらつき）を防ぎ、判定を安定化させる。
    - Flicker Prevention: 安定した検出結果を保持し、ボックスの点滅を防ぐ。
    """
    frame_data_ready = Signal(QImage, list)
    raw_frame_for_observation = Signal(PILImage.Image)
    hand_stopped_signal = Signal(PILImage.Image)

    def __init__(self, model_path, device_index=0, conf_threshold=0.8, move_threshold_px=5, stop_threshold_sec=60, parent=None):
        super().__init__(parent)
        self.camera_index = device_index
        self.is_running = True
        
        self.model_path = model_path
        self.model = None

        self.conf_threshold = conf_threshold
        self.move_threshold = move_threshold_px
        self.stop_threshold = stop_threshold_sec
        
        self.last_activity_time = time.time()
        self.last_hand_position = None
        self.signal_emitted = False

        self.frame_process_interval = 3
        self.frame_counter = 0

        self.hand_disappeared_frames = 0
        self.HAND_DISAPPEARANCE_THRESHOLD = 2

        # 描画用の安定した検出結果を保持する変数
        self.stable_detections: List[Dict[str, Any]] = []

    def run(self):
        """スレッドのメインループ"""
        if self.model is None:
            print(f"CameraWorker: YOLOモデル '{self.model_path}' をバックグラウンドで読み込みます...")
            try:
                self.model = YOLO(self.model_path)
                print(f" > YOLOモデルの読み込みに成功しました。(信頼度閾値: {self.conf_threshold})")
            except Exception as e:
                print(f"エラー: YOLOモデル '{self.model_path}' の読み込みに失敗しました: {e}")
                return

        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print(f"エラー: カメラ {self.camera_index} を開けません。")
            return

        try:
            last_observation_emit_time = time.time()
            
            while self.is_running:
                ret, frame = cap.read()
                if not ret:
                    break

                self.frame_counter += 1

                current_time = time.time()
                if current_time - last_observation_emit_time > 5.0:
                    pil_img = PILImage.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    self.raw_frame_for_observation.emit(pil_img)
                    last_observation_emit_time = current_time

                if self.frame_counter % self.frame_process_interval == 0:
                    results = self.model(frame, conf=self.conf_threshold, verbose=False)
                    
                    current_frame_detections: List[Dict[str, Any]] = []
                    hand_detected_this_frame = False
                    
                    for box in results[0].boxes:
                        label_name = self.model.names[int(box.cls[0])]
                        if label_name == "hand":
                            hand_detected_this_frame = True
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            conf = float(box.conf[0])
                            current_frame_detections.append({
                                "box": (x1, y1, x2, y2), "confidence": conf, "label": label_name
                            })
                            break
                    
                    if hand_detected_this_frame:
                        self.hand_disappeared_frames = 0
                        self.stable_detections = current_frame_detections
                        
                        current_position = np.array([(self.stable_detections[0]["box"][0] + self.stable_detections[0]["box"][2]) / 2, (self.stable_detections[0]["box"][1] + self.stable_detections[0]["box"][3]) / 2])
                        
                        if self.last_hand_position is not None:
                            distance = np.linalg.norm(current_position - self.last_hand_position)
                            if distance > self.move_threshold:
                                self.last_activity_time = time.time()
                                self.signal_emitted = False
                        else:
                            self.last_activity_time = time.time()
                            self.signal_emitted = False
                        
                        self.last_hand_position = current_position
                    
                    else:
                        self.hand_disappeared_frames += 1
                        if self.hand_disappeared_frames >= self.HAND_DISAPPEARANCE_THRESHOLD:
                            self.last_hand_position = None
                            self.stable_detections = []
                
                # 手の停止検知ロジック
                if self.last_hand_position is not None and (time.time() - self.last_activity_time) > self.stop_threshold and not self.signal_emitted:
                    print(f"{self.stop_threshold}秒間、手の活動がありませんでした。")
                    pil_img_on_stop = PILImage.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    self.hand_stopped_signal.emit(pil_img_on_stop)
                    self.signal_emitted = True
                
                # UIには常に「安定版」の検出結果を送信する
                bgra_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
                h, w, ch = bgra_frame.shape
                qt_image = QImage(bgra_frame.data, w, h, ch * w, QImage.Format_ARGB32)
                
                self.frame_data_ready.emit(qt_image.copy(), self.stable_detections)
                
                self.msleep(30)
        finally:
            cap.release()
            print("カメラを解放しました。")
            
    @Slot(int)
    def set_stop_threshold(self, seconds: int):
        """手の停止検知の閾値を更新するスロット"""
        print(f"手の停止検知時間を {seconds} 秒に更新しました。")
        self.stop_threshold = seconds

    def stop(self):
        """スレッドを安全に停止させる"""
        self.is_running = False
        self.wait()
#　カメラの設定（再起不要版）
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
    カメラ映像の取得とYOLO推論のみを行い、
    【未加工フレーム】と【推論結果データ】をUIスレッドに送信するワーカー。
    描画処理は一切行わない。
    """
    frame_data_ready = Signal(QImage, list)
    raw_frame_for_observation = Signal(PILImage.Image)
    hand_stopped_signal = Signal(PILImage.Image)

    def __init__(self, model_path, device_index=0, conf_threshold=0.8, move_threshold_px=5, stop_threshold_sec=60, parent=None):
        super().__init__(parent)
        self.camera_index = device_index
        self.is_running = True
        
        self.conf_threshold = conf_threshold
        self.move_threshold = move_threshold_px
        self.stop_threshold = stop_threshold_sec
        
        self.last_activity_time = time.time()
        self.last_hand_position = None
        self.signal_emitted = False

        try:
            self.model = YOLO(model_path)
            print(f"YOLOモデル '{model_path}' の読み込みに成功しました。(信頼度閾値: {self.conf_threshold})")
        except Exception as e:
            self.model = None
            print(f"エラー: YOLOモデル '{model_path}' の読み込みに失敗しました: {e}")

    def run(self):
        """スレッドのメインループ"""
        if self.model is None:
            print("YOLOモデルがロードされていないため、カメラ処理をスキップします。")
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

                # --- 1. 定点観測用の生フレームを定期的に送信 ---
                current_time = time.time()
                if current_time - last_observation_emit_time > 5.0:
                    pil_img = PILImage.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    self.raw_frame_for_observation.emit(pil_img)
                    last_observation_emit_time = current_time

                # --- 2. YOLO推論の実行 ---
                results = self.model(frame, conf=self.conf_threshold, verbose=False)
                
                # --- 3. 推論結果をPythonのデータ構造に変換 ---
                detections: List[Dict[str, Any]] = []
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = self.model.names[cls]
                    detections.append({
                        "box": (x1, y1, x2, y2),
                        "confidence": conf,
                        "label": label
                    })

                # --- 4. 手の動き検知 ---
                hand_detected = len(detections) > 0
                if hand_detected:
                    x1, y1, x2, y2 = detections[0]["box"]
                    current_position = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
                    
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
                    self.last_hand_position = None

                elapsed_time = time.time() - self.last_activity_time
                if elapsed_time > self.stop_threshold and not self.signal_emitted:
                    print(f"{self.stop_threshold}秒間、手の活動がありませんでした。")
                    pil_img_on_stop = PILImage.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    self.hand_stopped_signal.emit(pil_img_on_stop)
                    self.signal_emitted = True
                
                # --- 5. 【未加工フレーム】と【検出データ】をUIスレッドに送信 ---
                bgra_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
                h, w, ch = bgra_frame.shape
                qt_image = QImage(bgra_frame.data, w, h, ch * w, QImage.Format_ARGB32)
                
                self.frame_data_ready.emit(qt_image.copy(), detections)
                
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
# src/ui/panels/camera_panel.py

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class CameraPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.camera_view = QLabel("カメラを初期化中...")
        self.camera_view.setStyleSheet("background-color: black; color: white;")
        self.camera_view.setFixedSize(640, 480)
        layout.addWidget(self.camera_view)
        layout.addStretch()

    def set_pixmap(self, pixmap: QPixmap):
        self.camera_view.setPixmap(pixmap)

    def set_text(self, text: str):
        self.camera_view.setText(text)
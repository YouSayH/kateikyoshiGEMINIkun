# src/ui/settings_dialog.py　　カメラオンオフを設定

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QFormLayout, 
    QLineEdit, QSpinBox, QLabel, QComboBox, QTabWidget, QWidget, QTextEdit, QGroupBox,
    QCheckBox, QSlider, QHBoxLayout
)
from PySide6.QtCore import Qt
from ..core.settings_manager import SettingsManager
from ..utils.config import GEMINI_API_KEY_FROM_ENV
from pygrabber.dshow_graph import FilterGraph
import speech_recognition as sr
import google.generativeai as genai

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.setMinimumSize(650, 500)
        self.settings_manager = SettingsManager()
        
        layout = QVBoxLayout(self)
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        general_tab = self.create_general_tab()
        ai_tab = self.create_ai_tab()

        tab_widget.addTab(general_tab, "一般")
        tab_widget.addTab(ai_tab, "AI設定")

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.load_settings()

    def create_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.hand_stop_input = QSpinBox()
        self.hand_stop_input.setRange(5, 300); self.hand_stop_input.setSuffix(" 秒")
        self.observation_interval_input = QSpinBox()
        self.observation_interval_input.setRange(10, 600); self.observation_interval_input.setSuffix(" 秒")
        self.camera_selector = QComboBox()
        self.mic_selector = QComboBox()
        self.populate_device_lists()

        self.camera_enabled_on_startup_checkbox = QCheckBox()
        self.tts_enabled_checkbox = QCheckBox()
        self.tts_rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.tts_rate_slider.setRange(100, 400)
        self.tts_rate_label = QLabel()
        tts_rate_layout = QHBoxLayout()
        tts_rate_layout.addWidget(self.tts_rate_slider)
        tts_rate_layout.addWidget(self.tts_rate_label)
        self.tts_rate_slider.valueChanged.connect(lambda value: self.tts_rate_label.setText(f"{value}"))

        layout.addRow("Gemini APIキー:", self.api_key_input)
        layout.addRow("起動時にカメラを有効にする:", self.camera_enabled_on_startup_checkbox)
        layout.addRow("使用するカメラ:", self.camera_selector)
        layout.addRow("使用するマイク:", self.mic_selector)
        layout.addRow("手が止まったと判断する時間:", self.hand_stop_input)
        layout.addRow("定点観測の間隔:", self.observation_interval_input)
        layout.addRow("AIの応答を読み上げる:", self.tts_enabled_checkbox)
        layout.addRow("読み上げの速さ:", tts_rate_layout)
        
        return widget

    def create_ai_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        model_group = QGroupBox("AIモデル設定")
        model_layout = QFormLayout(model_group)
        self.keyword_model_selector = QComboBox()
        self.main_response_model_selector = QComboBox()
        self.vision_model_selector = QComboBox()
        model_layout.addRow("キーワード/タイトル生成:", self.keyword_model_selector)
        model_layout.addRow("メイン応答生成:", self.main_response_model_selector)
        model_layout.addRow("画像分析/定点観測:", self.vision_model_selector)
        self.populate_model_list()
        layout.addWidget(model_group)

        prompt_group = QGroupBox("プロンプトテンプレート設定（{変数名} で値が埋め込まれます）")
        prompt_layout = QFormLayout(prompt_group)
        self.hand_stopped_prompt_input = QTextEdit()
        self.keyword_extraction_prompt_input = QTextEdit()
        self.title_generation_prompt_input = QTextEdit()
        self.observation_prompt_input = QTextEdit()
        for editor in [self.hand_stopped_prompt_input, self.keyword_extraction_prompt_input, self.title_generation_prompt_input, self.observation_prompt_input]:
            editor.setAcceptRichText(False)
        prompt_layout.addRow("手の停止時:", self.hand_stopped_prompt_input)
        prompt_layout.addRow("キーワード抽出 ({conversation_text}):", self.keyword_extraction_prompt_input)
        prompt_layout.addRow("タイトル生成 ({conversation_text}):", self.title_generation_prompt_input)
        prompt_layout.addRow("定点観測 ({previous_description}):", self.observation_prompt_input)
        layout.addWidget(prompt_group)

        return widget

    def populate_device_lists(self):
        try:
            graph = FilterGraph()
            devices = graph.get_input_devices()
            for index, name in enumerate(devices):
                self.camera_selector.addItem(name, index)
        except Exception as e:
            print(f"カメラのリスト取得中にエラー: {e}")
            self.camera_selector.addItem("カメラ 0", 0)

        self.mic_selector.addItem("システム標準のマイク", -1)
        try:
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                self.mic_selector.addItem(name, index)
        except Exception as e:
            print(f"マイクのリスト取得中にエラー: {e}")

    def populate_model_list(self):
        try:
            api_key = self.settings_manager.api_key
            if not api_key:
                api_key = GEMINI_API_KEY_FROM_ENV

            if not api_key:
                print("APIキーが未設定のため、モデルリストを取得できません。")
                self.add_default_models()
                return

            genai.configure(api_key=api_key)
            available_models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            if not available_models:
                self.add_default_models()
            else:
                for selector in [self.keyword_model_selector, self.main_response_model_selector, self.vision_model_selector]:
                    selector.addItems(available_models)
        except Exception as e:
            print(f"モデルリストの取得中にエラーが発生しました: {e}")
            self.add_default_models()

    def add_default_models(self):
        default_models = ["gemini-2.5-flash", "gemini-2.5-flash"]
        for selector in [self.keyword_model_selector, self.main_response_model_selector, self.vision_model_selector]:
            selector.addItems(default_models)

    def load_settings(self):
        self.api_key_input.setText(self.settings_manager.api_key)
        self.hand_stop_input.setValue(self.settings_manager.hand_stop_threshold)
        self.observation_interval_input.setValue(self.settings_manager.observation_interval)
        
        cam_index = self.settings_manager.camera_device_index
        cam_ui_index = self.camera_selector.findData(cam_index)
        if cam_ui_index != -1: self.camera_selector.setCurrentIndex(cam_ui_index)

        mic_index = self.settings_manager.mic_device_index
        mic_ui_index = self.mic_selector.findData(mic_index)
        if mic_ui_index != -1: self.mic_selector.setCurrentIndex(mic_ui_index)
        
        self.camera_enabled_on_startup_checkbox.setChecked(self.settings_manager.camera_enabled_on_startup)
        self.tts_enabled_checkbox.setChecked(self.settings_manager.tts_enabled)
        initial_rate = self.settings_manager.tts_rate
        self.tts_rate_slider.setValue(initial_rate)
        self.tts_rate_label.setText(f"{initial_rate}")
        
        self.hand_stopped_prompt_input.setPlainText(self.settings_manager.hand_stopped_prompt)
        self.keyword_extraction_prompt_input.setPlainText(self.settings_manager.keyword_extraction_from_history_prompt)
        self.title_generation_prompt_input.setPlainText(self.settings_manager.title_generation_prompt)
        self.observation_prompt_input.setPlainText(self.settings_manager.observation_prompt)
        self.keyword_model_selector.setCurrentText(self.settings_manager.keyword_extraction_model)
        self.main_response_model_selector.setCurrentText(self.settings_manager.main_response_model)
        self.vision_model_selector.setCurrentText(self.settings_manager.vision_model)

    def save_settings(self):
        self.settings_manager.api_key = self.api_key_input.text().strip()
        self.settings_manager.hand_stop_threshold = self.hand_stop_input.value()
        self.settings_manager.observation_interval = self.observation_interval_input.value()
        self.settings_manager.camera_device_index = self.camera_selector.currentData()
        self.settings_manager.mic_device_index = self.mic_selector.currentData()
        self.settings_manager.camera_enabled_on_startup = self.camera_enabled_on_startup_checkbox.isChecked()
        self.settings_manager.tts_enabled = self.tts_enabled_checkbox.isChecked()
        self.settings_manager.tts_rate = self.tts_rate_slider.value()
        
        self.settings_manager.hand_stopped_prompt = self.hand_stopped_prompt_input.toPlainText()
        self.settings_manager.keyword_extraction_from_history_prompt = self.keyword_extraction_prompt_input.toPlainText()
        self.settings_manager.title_generation_prompt = self.title_generation_prompt_input.toPlainText()
        self.settings_manager.observation_prompt = self.observation_prompt_input.toPlainText()
        self.settings_manager.keyword_extraction_model = self.keyword_model_selector.currentText()
        self.settings_manager.main_response_model = self.main_response_model_selector.currentText()
        self.settings_manager.vision_model = self.vision_model_selector.currentText()
        
        print("設定を保存しました。")
    
    def accept(self):
        self.save_settings()
        super().accept()
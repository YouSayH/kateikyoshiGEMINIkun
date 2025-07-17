from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem

class SessionPanel(QWidget):
    """
    セッション履歴の表示と「新しいチャット」ボタンの責務を持つウィジェット。
    UIの操作をシグナルとして外部に通知する。
    """
    new_session_requested = Signal()
    session_selected = Signal(QListWidgetItem, QListWidgetItem)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # --- UIの構築 ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.new_session_button = QPushButton("＋ 新しいチャット")
        self.session_list_widget = QListWidget()
        layout.addWidget(self.new_session_button)
        layout.addWidget(self.session_list_widget)

        # --- UI操作をシグナルに中継 ---
        self.new_session_button.clicked.connect(self.new_session_requested.emit)
        self.session_list_widget.currentItemChanged.connect(self.session_selected.emit)

    # --- MainWindowからこのパネルを操作するためのメソッド群 ---

    def block_signals(self, block: bool):
        """リストウィジェットのシグナル発行を一時的に停止または再開する"""
        self.session_list_widget.blockSignals(block)

    def clear_list(self):
        """リストの項目をすべてクリアする"""
        self.session_list_widget.clear()

    def add_item(self, item: QListWidgetItem):
        """リストに項目を追加する"""
        self.session_list_widget.addItem(item)

    def count(self) -> int:
        """リストのアイテム数を返す"""
        return self.session_list_widget.count()

    def item(self, row: int) -> QListWidgetItem:
        """指定された行のアイテムを返す"""
        return self.session_list_widget.item(row)

    def set_current_row(self, row: int):
        """特定の行を選択状態にする"""
        self.session_list_widget.setCurrentRow(row)

    def current_item(self) -> QListWidgetItem:
        """現在選択されている項目を取得する"""
        return self.session_list_widget.currentItem()

    def find_item_by_id(self, session_id: int) -> QListWidgetItem | None:
        """セッションIDを元にリスト内のアイテムを検索する"""
        for i in range(self.session_list_widget.count()):
            item = self.session_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == session_id:
                return item
        return None
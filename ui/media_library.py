from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon
import os

class MediaLibrary(QListWidget):
    media_double_clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setIconSize(self.iconSize())
        self.itemDoubleClicked.connect(self._on_double_click)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        for url in urls:
            path = url.toLocalFile()
            if os.path.isfile(path):
                self.add_media(path)
        event.acceptProposedAction()

    def add_media(self, filepath):
        item = QListWidgetItem(os.path.basename(filepath))
        item.setToolTip(filepath)
        item.setData(1, filepath)
        self.addItem(item)

    def _on_double_click(self, item):
        path = item.data(1)
        if path:
            self.media_double_clicked.emit(path)
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal

class CommandPalette(QDialog):
    command_triggered = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup)
        self.setWindowTitle("Command Palette")
        self.resize(400, 300)
        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Type a command...")
        layout.addWidget(self.search)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self.commands = {
            "Cut Clip": "cut",
            "Split at Playhead": "split",
            "Export": "export",
            "Undo": "undo",
            "Redo": "redo",
            "Focus Mode": "focus",
        }

        self.search.textChanged.connect(self.filter_commands)
        self.list_widget.itemClicked.connect(self.execute)
        # Initially list all
        for name in self.commands.keys():
            self.list_widget.addItem(name)

    def filter_commands(self, text):
        self.list_widget.clear()
        for name, cmd in self.commands.items():
            if text.lower() in name.lower():
                self.list_widget.addItem(name)

    def execute(self, item):
        cmd = self.commands.get(item.text())
        if cmd:
            self.command_triggered.emit(cmd)
            self.accept()
from PyQt6.QtCore import QObject, pyqtSignal

class Signals(QObject):
    media_imported = pyqtSignal(str)          # filepath
    clip_trimmed = pyqtSignal(str, int, int)  # clip_id, new start, end
    timeline_changed = pyqtSignal()
    export_finished = pyqtSignal(str)         # output path

global_signals = Signals()
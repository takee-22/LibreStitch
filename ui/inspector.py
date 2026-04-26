from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QDoubleSpinBox, QPushButton
from core.signals import global_signals

class Inspector(QWidget):
    def __init__(self):
        super().__init__()
        self.current_clip = None
        layout = QFormLayout()
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.1, 10.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.valueChanged.connect(self.on_speed_change)
        layout.addRow("Speed:", self.speed_spin)
        self.setLayout(layout)

        global_signals.clip_selected = None  # We'll connect from main after init
        # Connect via main window later

    def set_clip(self, clip):
        self.current_clip = clip
        self.speed_spin.setValue(clip.speed if clip else 1.0)

    def on_speed_change(self, val):
        if self.current_clip:
            self.current_clip.speed = val
            global_signals.timeline_changed.emit()
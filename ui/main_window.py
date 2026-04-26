from PyQt6.QtWidgets import (QMainWindow, QDockWidget, QWidget, QVBoxLayout,
                             QPushButton, QToolBar, QStatusBar, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence

from ui.media_library import MediaLibrary
from ui.timeline_widget import TimelineWidget
from ui.preview_widget import PreviewWidget
from ui.inspector import Inspector
from ui.command_palette import CommandPalette
from core.config import Config
from core.signals import global_signals
from engine.project_manager import ProjectManager
from engine.compiler import FFmpegCompiler

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.project_manager = ProjectManager()
        self.setWindowTitle("CineCut - Desktop Video Editor")
        self.init_ui()
        self.apply_theme(self.config.theme)

    def init_ui(self):
        # Central widget: Preview
        self.preview = PreviewWidget()
        self.setCentralWidget(self.preview)

        # Docks
        self.media_dock = QDockWidget("Media Library", self)
        self.media_library = MediaLibrary()
        self.media_dock.setWidget(self.media_library)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.media_dock)

        self.inspector_dock = QDockWidget("Inspector", self)
        self.inspector = Inspector()
        self.inspector_dock.setWidget(self.inspector)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.inspector_dock)

        self.timeline_dock = QDockWidget("Timeline", self)
        self.timeline = TimelineWidget(self.project_manager.project)
        self.timeline_dock.setWidget(self.timeline)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.timeline_dock)

        # Toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)

        self.cut_action = QAction("Cut", self)
        self.cut_action.setShortcut(QKeySequence("Ctrl+K"))
        self.cut_action.triggered.connect(self.timeline.split_at_playhead)
        self.toolbar.addAction(self.cut_action)

        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut(QKeySequence.Undo)
        self.undo_action.triggered.connect(self.undo)
        self.toolbar.addAction(self.undo_action)

        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut(QKeySequence.Redo)
        self.redo_action.triggered.connect(self.redo)
        self.toolbar.addAction(self.redo_action)

        theme_btn = QPushButton("🌓")
        theme_btn.clicked.connect(self.toggle_theme)
        self.toolbar.addWidget(theme_btn)

        # Focus mode toggle
        focus_btn = QPushButton("👁️ Focus")
        focus_btn.clicked.connect(self.toggle_focus_mode)
        self.toolbar.addWidget(focus_btn)

        # Export button
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_video)
        self.toolbar.addWidget(export_btn)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Connect signals
        global_signals.timeline_changed.connect(self.update_preview_range)
        self.media_library.media_double_clicked.connect(self.add_clip_to_timeline)

        # Command palette
        self.cmd_palette = CommandPalette(self)
        self.cmd_palette.hide()

    def toggle_theme(self):
        themes = ["dark", "light", "cinematic", "focus"]
        current = themes.index(self.config.theme) if self.config.theme in themes else 0
        next_theme = themes[(current + 1) % len(themes)]
        self.config.theme = next_theme
        self.config.save()
        self.apply_theme(next_theme)

    def apply_theme(self, theme):
        try:
            with open(f"assets/{theme}.qss", "r") as f:
                self.setStyleSheet(f.read())
        except:
            pass
        # Special focus mode: hide non-timeline docks
        if theme == "focus":
            self.media_dock.hide()
            self.inspector_dock.hide()
        else:
            self.media_dock.show()
            self.inspector_dock.show()

    def toggle_focus_mode(self):
        if self.config.theme != "focus":
            self.config.theme = "focus"
        else:
            self.config.theme = "dark"  # fallback
        self.apply_theme(self.config.theme)
        self.config.save()

    def add_clip_to_timeline(self, filepath):
        # Add to first video track's end (simple)
        track = self.project_manager.project.video_tracks[0]
        from engine.timeline_model import MediaClip
        new_clip = MediaClip(source=filepath, start_time=0, end_time=5)  # dummy duration
        # Determine in_point as last clip's out
        last_end = max([c.in_point + c.end_time - c.start_time for c in track.clips], default=0)
        new_clip.in_point = last_end
        self.project_manager.push_state()
        track.clips.append(new_clip)
        self.timeline.rebuild()
        global_signals.timeline_changed.emit()

    def undo(self):
        if self.project_manager.undo():
            self.timeline.project = self.project_manager.project
            self.timeline.rebuild()
            global_signals.timeline_changed.emit()

    def redo(self):
        if self.project_manager.redo():
            self.timeline.project = self.project_manager.project
            self.timeline.rebuild()
            global_signals.timeline_changed.emit()

    def export_video(self):
        compiler = FFmpegCompiler(self.project_manager.project)
        cmd = compiler.compile("output.mp4", mode="advanced")
        if cmd:
            self.status_bar.showMessage("Exporting...")
            # Run in QThread in real app; for now just block (simulate)
            import subprocess
            subprocess.Popen(cmd)
        else:
            QMessageBox.warning(self, "Export Error", "No clips to export.")

    def update_preview_range(self):
        # Update preview widget to timeline range
        pass
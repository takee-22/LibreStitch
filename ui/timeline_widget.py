from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsItem
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPen, QWheelEvent, QPainter
from engine.timeline_model import TimelineProject, MediaClip, VideoTrack
import math

class ClipItem(QGraphicsRectItem):
    def __init__(self, clip: MediaClip, track_index, fps):
        super().__init__()
        self.clip = clip
        self.track_index = track_index
        self.fps = fps
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.update_rect()

    def update_rect(self):
        start_x = self.clip.in_point * self.fps  # pixels: 1 frame = 1px at scale 1
        duration_frames = (self.clip.end_time - self.clip.start_time) / self.clip.speed * self.fps
        self.setRect(QRectF(start_x, self.track_index * 50, duration_frames, 40))
        self.setBrush(QBrush(QColor("#4a90d9")))

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        # Draw label
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.clip.source[:10])

class TimelineWidget(QGraphicsView):
    playhead_moved = pyqtSignal(float)  # seconds
    clip_selected = pyqtSignal(MediaClip)

    def __init__(self, project: TimelineProject):
        super().__init__()
        self.project = project
        self.fps = project.fps
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.playhead_pos = 0.0  # seconds
        self.zoom = 1.0
        self.snap_threshold = 10  # pixels

        self.clip_items = []  # list of ClipItem
        self.playhead_line = self.scene.addLine(0, 0, 0, 500, QPen(QColor("red"), 2))
        self.playhead_line.setZValue(100)
        self.rebuild()

    def rebuild(self):
        self.scene.clear()
        self.clip_items.clear()
        self.playhead_line = self.scene.addLine(0, 0, 0, 500, QPen(QColor("red"), 2))
        self.playhead_line.setZValue(100)

        track_height = 50
        for ti, track in enumerate(self.project.video_tracks):
            for clip in track.clips:
                item = ClipItem(clip, ti, self.fps)
                self.scene.addItem(item)
                self.clip_items.append(item)

        self.scene.setSceneRect(0, 0, 1000, len(self.project.video_tracks) * track_height + 20)

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            self.zoom *= 1.1 if delta > 0 else 0.9
            self.resetTransform()
            self.scale(self.zoom, 1)
        else:
            # Scroll horizontally
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - event.angleDelta().x()
            )

    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        # Check if clicked on clip
        item = self.scene.itemAt(pos, self.transform())
        if isinstance(item, ClipItem):
            self.clip_selected.emit(item.clip)
        else:
            # Move playhead
            self.set_playhead(pos.x() / self.fps)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.scene.selectedItems():
            # Handle snapping while dragging
            item = self.scene.selectedItems()[0]
            if isinstance(item, ClipItem):
                pos = item.pos()
                new_x = pos.x()
                # Snap to other clip edges
                snap_x = self.snap_to_clips(new_x, item)
                if snap_x is not None:
                    item.setPos(snap_x - item.rect().x(), pos.y())
        super().mouseMoveEvent(event)

    def snap_to_clips(self, x, exclude_item):
        best_x = None
        min_dist = self.snap_threshold
        for other in self.clip_items:
            if other is exclude_item:
                continue
            edges = [other.rect().left(), other.rect().right() + other.rect().left()]
            for edge in edges:
                dist = abs(x - edge)
                if dist < min_dist:
                    min_dist = dist
                    best_x = edge
        return best_x

    def set_playhead(self, seconds):
        self.playhead_pos = seconds
        x = seconds * self.fps
        self.playhead_line.setPos(x, 0)
        self.playhead_moved.emit(seconds)

    def split_at_playhead(self):
        # Find selected clip and split
        for item in self.clip_items:
            if item.isSelected():
                clip = item.clip
                playhead_time = self.playhead_pos
                if clip.in_point <= playhead_time <= clip.in_point + (clip.end_time - clip.start_time) / clip.speed:
                    # Create new clip for right part
                    split_pos = playhead_time - clip.in_point  # time into clip
                    new_clip = MediaClip(
                        source=clip.source,
                        start_time=clip.start_time + split_pos,
                        end_time=clip.end_time,
                        in_point=playhead_time,
                        speed=clip.speed
                    )
                    clip.end_time = clip.start_time + split_pos
                    # Insert into project (simplified: same track)
                    # Need access to project manager; here we just print
                    print(f"Split clip at {playhead_time}")
                    break
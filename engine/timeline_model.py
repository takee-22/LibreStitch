from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import uuid
import json

@dataclass
class Keyframe:
    time: float        # seconds from clip start
    value: Any
    interpolation: str = "linear"

@dataclass
class MediaClip:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""                # absolute path to media file
    start_time: float = 0.0         # clip in-point in seconds
    end_time: float = 5.0           # clip out-point in seconds
    in_point: float = 0.0           # position on timeline (seconds)
    speed: float = 1.0
    audio_enabled: bool = True
    video_enabled: bool = True
    properties: Dict = field(default_factory=dict)
    keyframes: Dict[str, List[Keyframe]] = field(default_factory=dict)  # e.g., {"opacity": [...], "volume": [...]}

@dataclass
class Transition:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_clip_id: str = ""
    to_clip_id: str = ""
    type: str = "crossfade"     # crossfade, wipe, fade_in, fade_out
    duration: float = 1.0       # seconds
    properties: Dict = field(default_factory=dict)

@dataclass
class VideoTrack:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Video 1"
    clips: List[MediaClip] = field(default_factory=list)
    locked: bool = False
    muted: bool = False
    solo: bool = False
    opacity: float = 1.0

@dataclass
class AudioTrack:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Audio 1"
    clips: List[MediaClip] = field(default_factory=list)
    muted: bool = False
    solo: bool = False
    volume: float = 1.0

@dataclass
class TimelineProject:
    name: str = "Untitled"
    width: int = 1920
    height: int = 1080
    fps: int = 30
    video_tracks: List[VideoTrack] = field(default_factory=lambda: [VideoTrack()])
    audio_tracks: List[AudioTrack] = field(default_factory=lambda: [AudioTrack()])
    transitions: List[Transition] = field(default_factory=list)
    settings: Dict = field(default_factory=dict)

    def to_dict(self):
        # Custom serialization
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "video_tracks": [track.__dict__ for track in self.video_tracks],
            "audio_tracks": [track.__dict__ for track in self.audio_tracks],
            "transitions": self.transitions,
            "settings": self.settings
        }

    @classmethod
    def from_dict(cls, data):
        project = cls()
        project.name = data.get("name", "Untitled")
        project.width = data.get("width", 1920)
        project.height = data.get("height", 1080)
        project.fps = data.get("fps", 30)
        project.video_tracks = []
        for t in data.get("video_tracks", []):
            track = VideoTrack(name=t.get("name"))
            track.clips = [MediaClip(**c) for c in t.get("clips", [])]
            project.video_tracks.append(track)
        project.audio_tracks = []
        for t in data.get("audio_tracks", []):
            track = AudioTrack(name=t.get("name"))
            track.clips = [MediaClip(**c) for c in t.get("clips", [])]
            project.audio_tracks.append(track)
        project.transitions = [Transition(**tr) for tr in data.get("transitions", [])]
        return project
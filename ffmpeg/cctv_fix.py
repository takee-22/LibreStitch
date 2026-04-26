import subprocess
import os
import json
from ffmpeg.wrapper import get_ffmpeg_path

def get_video_info(filepath):
    """Use ffprobe to get fps, duration, codec, etc."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "stream=r_frame_rate,duration,codec_name,bit_rate:format=duration",
        "-of", "json", filepath
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {}
    info = json.loads(result.stdout)
    streams = info.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video_stream:
        fps_str = video_stream.get("r_frame_rate", "30/1")
        num, den = fps_str.split('/')
        fps = float(num)/float(den) if den != '0' else 30.0
        return {
            "fps": fps,
            "duration": float(video_stream.get("duration", 0)),
            "codec": video_stream.get("codec_name", ""),
        }
    return {"fps": 30.0, "duration": 0}

def normalize_dav(input_path, output_dir, target_fps=None):
    """
    Converts CCTV/DAV to CFR MP4, preserving quality.
    Returns output path.
    """
    info = get_video_info(input_path)
    fps = target_fps if target_fps else info.get("fps", 30)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}_cfr.mp4")
    cmd = [
        get_ffmpeg_path(), "-y",
        "-fflags", "+genpts+igndts",
        "-vsync", "cfr",
        "-i", input_path,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path

def normalize_batch(input_paths, output_dir, progress_callback=None):
    normalized = []
    for i, path in enumerate(input_paths):
        out = normalize_dav(path, output_dir)
        normalized.append(out)
        if progress_callback:
            progress_callback(i+1, len(input_paths))
    return normalized
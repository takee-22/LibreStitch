import subprocess
from ffmpeg.wrapper import get_ffmpeg_path

def generate_proxy(input_path, output_path, resolution=480):
    cmd = [
        get_ffmpeg_path(), "-y",
        "-i", input_path,
        "-vf", f"scale=-2:{resolution}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-an",  # no audio for proxy preview
        output_path
    ]
    subprocess.run(cmd, check=True)
import subprocess
import re
import os

def get_ffmpeg_path():
    return os.environ.get("FFMPEG_PATH", "ffmpeg")

def detect_gpu_encoders():
    encoders = []
    try:
        result = subprocess.run([get_ffmpeg_path(), "-encoders"], capture_output=True, text=True)
        if re.search(r'h264_nvenc', result.stdout):
            encoders.append("nvenc")
        if re.search(r'h264_qsv', result.stdout):
            encoders.append("qsv")
        if re.search(r'h264_amf', result.stdout):
            encoders.append("amf")
    except:
        pass
    return encoders

def build_encoder_params(encoder_type, quality=23):
    if encoder_type == "nvenc":
        return ["-c:v", "h264_nvenc", "-preset", "p4", "-qp", str(quality)]
    elif encoder_type == "qsv":
        return ["-c:v", "h264_qsv", "-preset", "medium", "-global_quality", str(quality)]
    elif encoder_type == "amf":
        return ["-c:v", "h264_amf", "-quality", "quality", "-qp_i", str(quality), "-qp_p", str(quality)]
    else:
        return ["-c:v", "libx264", "-preset", "fast", "-crf", str(quality)]
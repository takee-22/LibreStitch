import os
import shutil
from datetime import datetime

class CacheManager:
    def __init__(self):
        self.cache_dir = os.path.join(os.getcwd(), "cache")
        self.proxy_dir = os.path.join(self.cache_dir, "proxy")
        self.render_dir = os.path.join(self.cache_dir, "render_segments")
        os.makedirs(self.proxy_dir, exist_ok=True)
        os.makedirs(self.render_dir, exist_ok=True)

    def get_proxy_path(self, original_path):
        base = os.path.splitext(os.path.basename(original_path))[0]
        return os.path.join(self.proxy_dir, f"{base}_proxy.mp4")

    def get_render_segment_path(self, segment_hash):
        return os.path.join(self.render_dir, f"{segment_hash}.mp4")

    def clear_all(self):
        shutil.rmtree(self.cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
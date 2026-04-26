import json
import os

class Config:
    SETTINGS_FILE = "config.json"

    def __init__(self):
        self.theme = "dark"       # dark, light, cinematic, focus
        self.proxy_resolution = 480
        self.default_fps = 30
        self.auto_proxy = True
        self.gpu_encoder = None   # auto-detect
        self.load()

    def load(self):
        if os.path.exists(self.SETTINGS_FILE):
            with open(self.SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                for key, val in data.items():
                    setattr(self, key, val)

    def save(self):
        with open(self.SETTINGS_FILE, 'w') as f:
            json.dump(self.__dict__, f, indent=2)
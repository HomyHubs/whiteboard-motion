from __future__ import annotations
import os
from pathlib import Path

APP_NAME = "WhiteboardVideo"

def app_data_dir() -> Path:
    root = os.environ.get("LOCALAPPDATA")
    return Path(root) / APP_NAME if root else Path.home() / ".whiteboard-video"

def models_dir() -> Path:
    return Path(os.environ.get("WHITEBOARD_MODELS_DIR", app_data_dir() / "models"))

def cache_dir() -> Path:
    return Path(os.environ.get("WHITEBOARD_CACHE_DIR", app_data_dir() / "cache"))

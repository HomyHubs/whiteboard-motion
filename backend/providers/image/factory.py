from __future__ import annotations
from pathlib import Path
from ...models import ModelManager
from ...profiles import InferenceProfile
from .qwen_local import QwenImage21LocalProvider
from .qwen_ncnn import QwenImage21NcnnProvider

def create_qwen_provider(profile:InferenceProfile,manager:ModelManager|None=None,gpu_id:int=0):
    manager=manager or ModelManager()
    if profile.backend=="ncnn-vulkan":
        for model_id in ("qwen-image-2.1-ncnn","qwenimage-ncnn-windows-runtime"):
            if not manager.is_installed(model_id): raise RuntimeError(f"Thiếu {model_id}; cài bằng Model Manager trước")
        return QwenImage21NcnnProvider(manager.path("qwenimage-ncnn-windows-runtime"),manager.path("qwen-image-2.1-ncnn"),gpu_id)
    if not manager.is_installed("qwen-image-2.1"): raise RuntimeError("Thiếu qwen-image-2.1")
    return QwenImage21LocalProvider(manager.path("qwen-image-2.1"),profile)

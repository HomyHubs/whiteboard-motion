from __future__ import annotations
import gc
from pathlib import Path
from .base import ImageRequest
from ...profiles import InferenceProfile

class QwenImage21LocalProvider:
    """Official Diffusers backend. For 8 GB cards, a quantized backend is still required."""
    def __init__(self, model_path: Path, profile: InferenceProfile):
        self.model_path = model_path
        self.profile = profile
        self._pipe = None

    def load(self) -> None:
        if self._pipe is not None:
            return
        try:
            import torch
            from diffusers import QwenImage21Pipeline
        except ImportError as exc:
            raise RuntimeError("Thiếu torch/diffusers runtime cho Qwen-Image-2.1") from exc
        dtype = {"float16": torch.float16, "bfloat16": torch.bfloat16, "float32": torch.float32}[self.profile.dtype]
        self._pipe = QwenImage21Pipeline.from_pretrained(str(self.model_path), torch_dtype=dtype, local_files_only=True)
        if self.profile.cpu_offload:
            self._pipe.enable_model_cpu_offload()
        elif self.profile.runtime.startswith("cuda"):
            self._pipe.to("cuda")

    def generate(self, request: ImageRequest) -> Path:
        self.load()
        import torch
        device = "cuda" if self.profile.runtime.startswith("cuda") else "cpu"
        kwargs = dict(prompt=request.prompt, width=request.width, height=request.height,
                      num_inference_steps=request.steps,
                      generator=torch.Generator(device).manual_seed(request.seed))
        if request.negative_prompt:
            kwargs["negative_prompt"] = request.negative_prompt
        if request.input_images:
            from PIL import Image
            images = [Image.open(path).convert("RGBA") for path in request.input_images]
            kwargs["image"] = images[0] if len(images) == 1 else images
        result = self._pipe(**kwargs).images[0]
        request.output.parent.mkdir(parents=True, exist_ok=True)
        result.save(request.output)
        return request.output

    def unload(self) -> None:
        self._pipe = None
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

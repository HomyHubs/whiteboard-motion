from __future__ import annotations
import gc, os
from pathlib import Path
from .base import ImageRequest
from ...profiles import InferenceProfile

OFFLOAD_ENV = "WHITEBOARD_QWEN_OFFLOAD"  # auto | model | sequential | none
# Activations/CUDA context headroom on top of the transformer weights when the whole module is moved to GPU.
VRAM_HEADROOM_BYTES = 2 * 1024**3

def component_bytes(model_path: Path, component: str = "transformer") -> int:
    folder = Path(model_path) / component
    return sum(p.stat().st_size for p in folder.glob("*.safetensors")) if folder.is_dir() else 0

def choose_offload(cpu_offload: bool, transformer_bytes: int, free_vram_bytes: int | None, requested: str | None = None) -> str:
    """Pick the Diffusers offload mode.

    ``enable_model_cpu_offload`` moves the whole transformer to the GPU per step. On Windows, when it does not fit
    (Qwen-Image-2.1 bf16 transformer is ~13.3 GB vs ~12 GB free on a 16 GB card with a desktop running) the process
    dies with a native access violation (0xC0000005) instead of a Python OOM. Fall back to sequential offload,
    which is slow but survives; a quantized (fp8) transformer is the real fix.
    """
    requested = (requested or os.environ.get(OFFLOAD_ENV) or "auto").lower()
    if requested not in {"auto", "model", "sequential", "none"}:
        raise ValueError(f"{OFFLOAD_ENV} must be auto, model, sequential or none, not {requested!r}")
    if requested != "auto":
        return requested
    if not cpu_offload:
        return "none"
    if free_vram_bytes is not None and transformer_bytes and transformer_bytes + VRAM_HEADROOM_BYTES > free_vram_bytes:
        return "sequential"
    return "model"

class QwenImage21LocalProvider:
    """Official Diffusers backend. For 8 GB cards, a quantized backend is still required."""
    def __init__(self, model_path: Path, profile: InferenceProfile):
        self.model_path = model_path
        self.profile = profile
        self._pipe = None
        self.offload_mode: str | None = None

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
        free = None
        if self.profile.runtime.startswith("cuda") and torch.cuda.is_available():
            free = torch.cuda.mem_get_info()[0]
        mode = choose_offload(self.profile.cpu_offload, component_bytes(self.model_path), free)
        if mode == "sequential":
            self._pipe.enable_sequential_cpu_offload()
        elif mode == "model":
            self._pipe.enable_model_cpu_offload()
        elif self.profile.runtime.startswith("cuda"):
            self._pipe.to("cuda")
        self.offload_mode = mode

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

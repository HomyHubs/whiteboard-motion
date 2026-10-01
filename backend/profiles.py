from __future__ import annotations
from dataclasses import asdict, dataclass
from .hardware import NvidiaGpu, gpu_series

@dataclass(frozen=True)
class InferenceProfile:
    id: str
    dtype: str
    quantization: str | None
    cpu_offload: bool
    sequential_load: bool
    width: int
    height: int
    runtime: str
    backend: str
    notes: str

    def to_dict(self) -> dict:
        return asdict(self)

def select_qwen_profile(gpu: NvidiaGpu | None) -> InferenceProfile:
    if gpu is None:
        return InferenceProfile("cpu-experimental", "float32", "q4", True, True, 768, 768, "cpu", "ncnn-vulkan", "Qwen local CPU rất chậm; ưu tiên Image API.")
    vram = gpu.memory_total_mb
    series = gpu_series(gpu.name)
    runtime = "cuda-blackwell" if series == 50 else "cuda-standard"
    name = gpu.name.upper()
    if "5060 TI" in name and vram >= 15000:
        return InferenceProfile("rtx-5060ti-16gb", "bfloat16", "fp8", True, False, 1536, 1024, runtime, "diffusers", "Profile ưu tiên cho RTX 5060 Ti 16 GB.")
    if "5060" in name:
        return InferenceProfile("rtx-5060-8gb", "float16", "q4", True, True, 1024, 768, runtime, "ncnn-vulkan", "Backend ncnn/Vulkan low-VRAM; Diffusers chuẩn có thể OOM.")
    if "4060" in name:
        return InferenceProfile("rtx-4060-8gb", "float16", "q4", True, True, 1024, 768, runtime, "ncnn-vulkan", "Backend ncnn/Vulkan low-VRAM.")
    if "3060" in name and vram >= 11000:
        return InferenceProfile("rtx-3060-12gb", "float16", "q4", True, False, 1024, 1024, runtime, "ncnn-vulkan", "Backend ncnn/Vulkan ưu tiên độ ổn định cho RTX 3060 12 GB.")
    if vram <= 8500:
        return InferenceProfile("nvidia-8gb", "float16", "q4", True, True, 768, 768, runtime, "ncnn-vulkan", "Low-VRAM generic.")
    if vram <= 17000:
        return InferenceProfile("nvidia-16gb", "bfloat16" if series and series >= 30 else "float16", "fp8", True, False, 1536, 1024, runtime, "diffusers", "Mid-range generic.")
    return InferenceProfile("nvidia-24gb-plus", "bfloat16" if series and series >= 30 else "float16", "fp8", False, False, 2048, 1152, runtime, "diffusers", "High-VRAM generic.")

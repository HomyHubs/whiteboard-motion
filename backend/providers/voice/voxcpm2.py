from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

@dataclass
class VoiceRequest:
    text: str
    output: Path
    language: str = "vi"
    reference_audio: Path | None = None
    reference_text: str | None = None
    consent_confirmed: bool = False
    seed: int = 42

class VoxCPM2Provider:
    def __init__(self, model_path: Path, device: str = "cuda", optimize: bool = True):
        self.model_path, self.device, self.optimize = model_path, device, optimize
        self._model = None

    def load(self) -> None:
        if self._model is not None:
            return
        try:
            from voxcpm import VoxCPM
        except ImportError as exc:
            raise RuntimeError("Thiếu package voxcpm") from exc
        self._model = VoxCPM.from_pretrained(hf_model_id=str(self.model_path), device=self.device, optimize=self.optimize, load_denoiser=False)

    def synthesize(self, request: VoiceRequest) -> Path:
        if request.reference_audio and not request.consent_confirmed:
            raise PermissionError("Voice clone yêu cầu xác nhận quyền sử dụng giọng mẫu")
        self.load()
        kwargs = {"text": request.text, "seed": request.seed}
        if request.reference_audio:
            kwargs.update(prompt_wav_path=str(request.reference_audio), prompt_text=request.reference_text or "")
        audio = self._model.generate(**kwargs)
        try:
            import soundfile as sf
        except ImportError as exc:
            raise RuntimeError("Thiếu soundfile") from exc
        request.output.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(request.output), audio, 48000)
        return request.output

    def unload(self) -> None:
        self._model = None
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

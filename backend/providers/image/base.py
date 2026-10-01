from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ImageRequest:
    prompt: str
    output: Path
    width: int = 1024
    height: int = 1024
    steps: int = 40
    seed: int = 42
    input_images: list[Path] = field(default_factory=list)
    negative_prompt: str = ""

from __future__ import annotations
from dataclasses import asdict, dataclass
import json, re, shutil, subprocess

@dataclass(frozen=True)
class NvidiaGpu:
    index: int
    name: str
    memory_total_mb: int
    driver_version: str
    compute_capability: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

def _run_query(fields: list[str]) -> list[list[str]]:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return []
    cmd = [exe, f"--query-gpu={','.join(fields)}", "--format=csv,noheader,nounits"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
    if result.returncode:
        return []
    return [[part.strip() for part in line.split(",")] for line in result.stdout.splitlines() if line.strip()]

def detect_nvidia_gpus() -> list[NvidiaGpu]:
    fields = ["index", "name", "memory.total", "driver_version", "compute_cap"]
    rows = _run_query(fields)
    if not rows:  # older nvidia-smi may not expose compute_cap
        fields = fields[:-1]
        rows = _run_query(fields)
    output = []
    for row in rows:
        if len(row) < 4:
            continue
        output.append(NvidiaGpu(int(row[0]), row[1], int(float(row[2])), row[3], row[4] if len(row) > 4 else None))
    return output

def gpu_series(name: str) -> int | None:
    match = re.search(r"RTX\s*(?:PRO\s*)?(\d{2})\d{2}", name.upper())
    return int(match.group(1)) if match else None

def hardware_report() -> dict:
    gpus = detect_nvidia_gpus()
    return {"nvidia": [gpu.to_dict() for gpu in gpus], "hasNvidia": bool(gpus)}

def print_report() -> None:
    print(json.dumps(hardware_report(), ensure_ascii=False, indent=2))

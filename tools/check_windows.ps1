$ErrorActionPreference = "Continue"
Write-Host "Whiteboard Video - Windows 11 check"
Write-Host "OS:" (Get-CimInstance Win32_OperatingSystem).Caption
if (Get-Command python -ErrorAction SilentlyContinue) { python --version } else { Write-Warning "Python not found" }
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) { ffmpeg -version | Select-Object -First 1 } else { Write-Warning "FFmpeg not found" }
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
  nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader
} else { Write-Warning "NVIDIA GPU not found; CPU/API mode only" }
python -m backend.cli hardware
python -m backend.cli profile

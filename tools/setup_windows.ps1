param([switch]$CpuOnly)
$ErrorActionPreference = "Stop"
if (!(Test-Path .venv)) { python -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements-backend.txt
Write-Host "Core backend installed."
if (!$CpuOnly) {
  Write-Host "Install the PyTorch package matching your GPU/driver next."
  Write-Host "RTX 50 requires the Blackwell-compatible runtime; do not reuse an old CUDA wheel."
}
& .\.venv\Scripts\python.exe -m backend.cli hardware
& .\.venv\Scripts\python.exe -m backend.cli models list

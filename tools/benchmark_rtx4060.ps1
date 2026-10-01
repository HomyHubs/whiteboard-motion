$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python tools/benchmark_qwen.py --expected-gpu "RTX 4060" --sizes 768x768 1024x1024 --steps 20

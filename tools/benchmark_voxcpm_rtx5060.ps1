$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python tools/benchmark_voxcpm.py --device cuda --expected-gpu "RTX 5060"

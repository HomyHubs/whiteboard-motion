param(
  [ValidateSet("diffusers", "ncnn-vulkan")]
  [string]$Backend = "diffusers",
  [int]$Steps = 20
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python tools/benchmark_qwen.py --expected-gpu "RTX 5060 Ti" --backend $Backend --sizes 1024x1024 1536x1024 --steps $Steps

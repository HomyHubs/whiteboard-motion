param(
  [ValidateSet("diffusers", "ncnn-vulkan")]
  [string]$Backend = "ncnn-vulkan"
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
Write-Host "Qwen-Image-2.1 uses a research/non-commercial license unless separately licensed."
$Confirm = Read-Host "Type AGREE after reading the license to continue"
if ($Confirm -ne "AGREE") { throw "License was not accepted" }
if ($Backend -eq "diffusers") {
  python -m backend.cli models accept qwen-image-2.1
  python -m backend.cli models download qwen-image-2.1
  python -m backend.cli models verify qwen-image-2.1
} else {
  python -m backend.cli models accept qwen-image-2.1-ncnn
  python -m backend.cli models download qwen-image-2.1-ncnn
  python -m backend.cli models download qwenimage-ncnn-windows-runtime
  python -m backend.cli models verify qwen-image-2.1-ncnn
}

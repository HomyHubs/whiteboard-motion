$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root
$Venv = Join-Path $Root ".sidecar-venv"
if (!(Test-Path $Venv)) { python -m venv $Venv }
$Python = Join-Path $Venv "Scripts\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements-backend.txt pyinstaller
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build\whiteboard-backend, dist\whiteboard-backend
& $Python -m PyInstaller --noconfirm --clean --onefile --name whiteboard-backend `
  --paths $Root --add-data "$Root\assets\preview.html;assets" `
  --add-data "$Root\backend\models;backend\models" `
  --collect-submodules huggingface_hub --hidden-import PIL `
  --exclude-module torch --exclude-module torchvision --exclude-module diffusers `
  --exclude-module transformers --exclude-module voxcpm backend_sidecar.py
$Target = Join-Path $Root "app\src-tauri\binaries\whiteboard-backend-x86_64-pc-windows-msvc.exe"
Copy-Item -Force (Join-Path $Root "dist\whiteboard-backend.exe") $Target
powershell -ExecutionPolicy Bypass -File (Join-Path $Root "tools\sign_windows.ps1") $Target
if ($LASTEXITCODE -ne 0) { throw "Signing sidecar failed" }
Write-Host "SIDECAR=$Target"
& $Target --help
if ($LASTEXITCODE -ne 0) { throw "Sidecar --help failed" }

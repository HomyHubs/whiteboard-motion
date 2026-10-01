$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root
if (!(Get-Command cargo -ErrorAction SilentlyContinue)) { throw "Rust/Cargo missing. Install stable Rust from https://rustup.rs" }
if (!(Get-Command node -ErrorAction SilentlyContinue)) { throw "Node.js missing" }
powershell -ExecutionPolicy Bypass -File tools\build_backend_sidecar.ps1
Set-Location app
npm install --no-audit --no-fund
npm run tauri build
Write-Host "Installers are under app\src-tauri\target\release\bundle\"

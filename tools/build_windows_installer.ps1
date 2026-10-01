# Build sidecar + bundled FFmpeg + Tauri NSIS/MSI installers.
# Signing (P4.7): set WINDOWS_CERTIFICATE_FILE/WINDOWS_CERTIFICATE_PASSWORD or WINDOWS_CERTIFICATE_THUMBPRINT;
# without them the build is UNSIGNED (fine for CI/test, not for stable releases; see docs/RELEASE.md).
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root
if (!(Get-Command cargo -ErrorAction SilentlyContinue)) { throw "Rust/Cargo missing. Install stable Rust from https://rustup.rs" }
if (!(Get-Command node -ErrorAction SilentlyContinue)) { throw "Node.js missing" }
python tools\release_version.py check
if ($LASTEXITCODE -ne 0) { throw "Version mismatch between app files" }
python tools\fetch_ffmpeg.py
if ($LASTEXITCODE -ne 0) { throw "FFmpeg bundle download/verify failed" }
powershell -ExecutionPolicy Bypass -File tools\build_backend_sidecar.ps1
if ($LASTEXITCODE -ne 0) { throw "Sidecar build failed" }
Set-Location app
if (Test-Path package-lock.json) { npm ci --no-audit --no-fund } else { npm install --no-audit --no-fund }
$TauriArgs = @("run", "tauri", "build")
if ($env:WINDOWS_CERTIFICATE_FILE -or $env:WINDOWS_CERTIFICATE_THUMBPRINT) {
  $SignScript = Join-Path $Root "tools\sign_windows.ps1"
  $Override = @{ bundle = @{ windows = @{ signCommand = @{ cmd = "powershell"; args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $SignScript, "%1") } } } }
  $OverridePath = Join-Path $env:TEMP "tauri.sign.conf.json"
  $Override | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $OverridePath
  $TauriArgs += @("--", "--config", $OverridePath)
  Write-Host "Code signing enabled"
} else { Write-Warning "Building UNSIGNED installers" }
& npm @TauriArgs
if ($LASTEXITCODE -ne 0) { throw "tauri build failed" }
Set-Location $Root
$Bundle = Join-Path $Root "app\src-tauri\target\release\bundle"
$Installers = Get-ChildItem $Bundle -Recurse -Include *-setup.exe, *.msi
if (-not $Installers) { throw "No installer produced under $Bundle" }
$Sums = $Installers | ForEach-Object { "{0}  {1}" -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(), $_.Name }
$Sums | Set-Content -Encoding ASCII (Join-Path $Bundle "SHA256SUMS.txt")
$Installers | ForEach-Object { Write-Host ("INSTALLER={0} bytes={1} signature={2}" -f $_.FullName, $_.Length, (Get-AuthenticodeSignature $_.FullName).Status) }
Write-Host "SHA256SUMS=$(Join-Path $Bundle 'SHA256SUMS.txt')"

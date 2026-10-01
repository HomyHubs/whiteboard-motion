# P4.6 — Installer smoke test on a Windows machine WITHOUT an NVIDIA GPU (e.g. GitHub windows runner, iGPU laptop).
# Installs the NSIS build silently, starts the app with Python removed from PATH, checks backend/CPU profile/bundled
# FFmpeg libx264 fallback/project persistence, uninstalls, and writes benchmarks/smoke-reports/no-gpu-*.json.
#   powershell -ExecutionPolicy Bypass -File tools/smoke_no_gpu.ps1 -Installer "path\Whiteboard Video_0.1.0_x64-setup.exe"
param(
  [Parameter(Mandatory = $true)][string]$Installer,
  [string]$InstallDir = (Join-Path $env:LOCALAPPDATA "Whiteboard Video"),
  [int]$Port = 8765,
  [switch]$AllowNvidia,
  [switch]$KeepInstalled
)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Api = "http://127.0.0.1:$Port"
$Checks = [System.Collections.Generic.List[object]]::new()
function Add-Check([string]$Name, [bool]$Ok, $Detail) {
  $Checks.Add([ordered]@{ name = $Name; ok = $Ok; detail = $Detail })
  $mark = if ($Ok) { "PASS" } else { "FAIL" }
  Write-Host "[$mark] $Name :: $(($Detail | ConvertTo-Json -Compress -Depth 6))"
}
function Get-Api([string]$Path) { Invoke-RestMethod -Uri "$Api$Path" -TimeoutSec 60 }
function Wait-Health([int]$Seconds) {
  $deadline = (Get-Date).AddSeconds($Seconds)
  while ((Get-Date) -lt $deadline) {
    try { return Invoke-RestMethod -Uri "$Api/health" -TimeoutSec 3 } catch { Start-Sleep -Milliseconds 700 }
  }
  return $null
}
function Find-AppExe {
  Get-ChildItem $InstallDir -Filter *.exe -Recurse |
    Where-Object { $_.Name -notmatch '^(whiteboard-backend|ffmpeg|ffprobe|uninstall)' } | Select-Object -First 1
}
function Start-App {
  $exe = Find-AppExe
  if (-not $exe) { throw "App executable not found in $InstallDir" }
  # No Python on PATH: the app must work with only the PyInstaller sidecar.
  $clean = ($env:PATH -split ';' | Where-Object { $_ -and $_ -notmatch 'python|conda|pyenv|\\.venv' }) -join ';'
  $old = $env:PATH; $env:PATH = $clean
  try { return Start-Process -FilePath $exe.FullName -PassThru } finally { $env:PATH = $old }
}
function Stop-App($Process) {
  if ($Process -and -not $Process.HasExited) { $null = $Process.CloseMainWindow(); Start-Sleep 3 }
  if ($Process -and -not $Process.HasExited) { Stop-Process -Id $Process.Id -Force }
  Start-Sleep 2
  Get-Process whiteboard-backend* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}

$started = Get-Date
$os = Get-CimInstance Win32_OperatingSystem
$gpus = @(Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name })
$nvidia = $null -ne (Get-Command nvidia-smi -ErrorAction SilentlyContinue) -or ($gpus -match 'NVIDIA').Count -gt 0
Add-Check "machine-has-no-nvidia" ((-not $nvidia) -or $AllowNvidia) @{ gpus = $gpus; nvidiaDetected = $nvidia }
if ($nvidia -and -not $AllowNvidia) { Write-Warning "NVIDIA GPU detected; this is not a valid P4.6 machine (use -AllowNvidia to run anyway)." }

$installerItem = Get-Item $Installer
$sha = (Get-FileHash $installerItem.FullName -Algorithm SHA256).Hash.ToLower()
$sig = Get-AuthenticodeSignature $installerItem.FullName
$p = Start-Process -FilePath $installerItem.FullName -ArgumentList "/S" -Wait -PassThru
Add-Check "silent-install" ($p.ExitCode -eq 0 -and (Test-Path $InstallDir)) @{ exitCode = $p.ExitCode; installDir = $InstallDir }

$ffmpeg = Join-Path $InstallDir "ffmpeg\ffmpeg.exe"; $ffprobe = Join-Path $InstallDir "ffmpeg\ffprobe.exe"
Add-Check "bundled-ffmpeg-files" ((Test-Path $ffmpeg) -and (Test-Path $ffprobe) -and (Test-Path (Join-Path $InstallDir "ffmpeg\NOTICE.txt"))) @{ ffmpeg = $ffmpeg }

$app = $null
try {
  $app = Start-App
  $health = Wait-Health 90
  Add-Check "sidecar-autostart-without-python" ($null -ne $health -and $health.ok) $health
  if ($health) {
    $hw = Get-Api "/hardware"; Add-Check "hardware-no-nvidia" (-not $hw.hasNvidia -or $AllowNvidia) $hw
    $prof = Get-Api "/profile"; Add-Check "cpu-profile" ($prof.id -eq "cpu-experimental" -or $AllowNvidia) @{ id = $prof.id; runtime = $prof.runtime }
    $media = Get-Api "/media"
    Add-Check "media-bundled-ffmpeg" ($media.source -in @("env", "bundled")) @{ source = $media.source; ffmpeg = $media.ffmpeg; license = $media.license }
    Add-Check "encoder-libx264-fallback" (($media.encoder.name -eq "libx264" -and -not $media.nvencUsable) -or $AllowNvidia) @{ encoder = $media.encoder.name; nvencUsable = $media.nvencUsable; hasNvencEncoder = $media.hasNvencEncoder }
    $models = Get-Api "/models"; Add-Check "models-list" (@($models).Count -gt 0) @{ count = @($models).Count }
    $preview = Invoke-WebRequest -Uri "$Api/preview" -UseBasicParsing -TimeoutSec 30
    Add-Check "annotation-preview" ($preview.StatusCode -eq 200 -and $preview.Content -match '<html') @{ bytes = $preview.Content.Length }
    $name = "Smoke No GPU $([DateTime]::UtcNow.ToString('yyyyMMddHHmmss'))"
    $project = Invoke-RestMethod -Uri "$Api/projects" -Method Post -ContentType "application/json" -Body (@{ name = $name } | ConvertTo-Json)
    $scene = @{ canvas = @{ width = 1672; height = 941 }; sceneDurationMs = 1000; elements = @() } | ConvertTo-Json -Depth 5
    $null = Invoke-RestMethod -Uri "$Api/projects/$($project.id)/scenes/scene-01" -Method Put -ContentType "application/json" -Body $scene
    Add-Check "project-create-save" ($null -ne $project.id) @{ id = $project.id }

    $out = Join-Path $env:TEMP "wb-smoke-$PID.mp4"
    $ErrorActionPreference = "Continue"  # native stderr must not become terminating errors (Windows PowerShell 5.1)
    & $ffmpeg -hide_banner -loglevel error -y -f lavfi -i "testsrc2=s=640x360:d=2:r=30" -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p $out
    $encExit = $LASTEXITCODE
    $codec = if (Test-Path $out) { (& $ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 $out).Trim() } else { "" }
    & $ffmpeg -hide_banner -loglevel quiet -y -f lavfi -i "color=c=black:s=256x256:d=0.2" -frames:v 2 -c:v h264_nvenc -f null -
    $nvencExit = $LASTEXITCODE
    Add-Check "ffmpeg-libx264-encode" ($encExit -eq 0 -and $codec -eq "h264") @{ exitCode = $encExit; codec = $codec }
    Add-Check "nvenc-fails-cleanly-without-gpu" ($nvencExit -ne 0 -or $AllowNvidia) @{ exitCode = $nvencExit }
    Remove-Item $out -ErrorAction SilentlyContinue
    $ErrorActionPreference = "Stop"

    Stop-App $app
    $leftover = @(Get-Process whiteboard-backend* -ErrorAction SilentlyContinue).Count
    $app = Start-App
    $health2 = Wait-Health 90
    $reloaded = if ($health2) { Get-Api "/projects/$($project.id)" } else { $null }
    Add-Check "project-persists-after-restart" ($null -ne $reloaded -and @($reloaded.scenes) -contains "scene-01") @{ scenes = $reloaded.scenes }
    Add-Check "sidecar-stopped-with-app" ($leftover -eq 0) @{ leftoverProcesses = $leftover }
  }
} catch {
  Add-Check "unexpected-error" $false @{ message = $_.Exception.Message; at = $_.InvocationInfo.PositionMessage }
} finally {
  Stop-App $app
}

if (-not $KeepInstalled) {
  $uninstaller = Get-ChildItem $InstallDir -Filter "uninstall*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($uninstaller) {
    $u = Start-Process -FilePath $uninstaller.FullName -ArgumentList "/S" -Wait -PassThru; Start-Sleep 5
    Add-Check "silent-uninstall" ($u.ExitCode -eq 0) @{ exitCode = $u.ExitCode }
  } else { Add-Check "silent-uninstall" $false "uninstaller not found" }
  $dataDir = Join-Path $env:LOCALAPPDATA "WhiteboardVideo\projects"
  Add-Check "uninstall-keeps-user-projects" (Test-Path $dataDir) @{ projectsDir = $dataDir }
}

$failed = @($Checks | Where-Object { -not $_.ok }).Count
$reportDir = Join-Path $Root "benchmarks\smoke-reports"; New-Item -ItemType Directory -Force $reportDir | Out-Null
$report = [ordered]@{
  test = "P4.6 no-NVIDIA smoke"; result = $(if ($failed) { "FAIL" } else { "PASS" }); failed = $failed
  startedAt = $started.ToUniversalTime().ToString("o"); seconds = [int]((Get-Date) - $started).TotalSeconds
  commit = $env:GITHUB_SHA; os = "$($os.Caption) $($os.Version)"; ramGb = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1); gpus = $gpus
  installer = @{ name = $installerItem.Name; bytes = $installerItem.Length; sha256 = $sha; signature = "$($sig.Status)" }
  checks = $Checks
}
$path = Join-Path $reportDir ("no-gpu-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".json")
$report | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $path
Write-Host "REPORT=$path"; Write-Host "RESULT=$($report.result) failed=$failed"
if ($failed) { exit 1 }

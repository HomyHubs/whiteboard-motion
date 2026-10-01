# Authenticode-sign one file (P4.7). Used by Tauri bundle.windows.signCommand and by the release workflow.
# Certificate sources (first match wins):
#   WINDOWS_CERTIFICATE_FILE + WINDOWS_CERTIFICATE_PASSWORD  (PFX file, e.g. decoded from a CI secret)
#   WINDOWS_CERTIFICATE_THUMBPRINT                            (certificate already in CurrentUser\My, e.g. EV token)
# Without a certificate the script only warns, unless WHITEBOARD_REQUIRE_SIGNING=1 (stable releases).
param([Parameter(Mandatory = $true)][string]$File)
$ErrorActionPreference = "Stop"
$Timestamp = if ($env:WINDOWS_TIMESTAMP_URL) { $env:WINDOWS_TIMESTAMP_URL } else { "http://timestamp.digicert.com" }
$HasPfx = $env:WINDOWS_CERTIFICATE_FILE -and (Test-Path $env:WINDOWS_CERTIFICATE_FILE)
$HasThumb = [bool]$env:WINDOWS_CERTIFICATE_THUMBPRINT
if (-not ($HasPfx -or $HasThumb)) {
  if ($env:WHITEBOARD_REQUIRE_SIGNING -eq "1") { throw "Signing required but no certificate configured (WINDOWS_CERTIFICATE_FILE or WINDOWS_CERTIFICATE_THUMBPRINT)." }
  Write-Warning "UNSIGNED: no code-signing certificate configured, skipping $File"
  exit 0
}
$SignTool = Get-Command signtool.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $SignTool) {
  $SignTool = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match '\\x64\\' } | Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $SignTool) { throw "signtool.exe not found; install the Windows 10/11 SDK." }
$SignArgs = @("sign", "/fd", "sha256", "/tr", $Timestamp, "/td", "sha256", "/d", "Whiteboard Video")
if ($HasPfx) { $SignArgs += @("/f", $env:WINDOWS_CERTIFICATE_FILE, "/p", $env:WINDOWS_CERTIFICATE_PASSWORD) }
else { $SignArgs += @("/sha1", $env:WINDOWS_CERTIFICATE_THUMBPRINT) }
for ($attempt = 1; $attempt -le 3; $attempt++) {  # timestamp servers fail transiently
  & $SignTool @SignArgs $File
  if ($LASTEXITCODE -eq 0) { break }
  if ($attempt -eq 3) { throw "signtool sign failed for $File (exit $LASTEXITCODE)" }
  Start-Sleep -Seconds (5 * $attempt)
}
& $SignTool verify /pa /q $File
if ($LASTEXITCODE -ne 0) { throw "signtool verify failed for $File" }
Write-Host "SIGNED=$File"

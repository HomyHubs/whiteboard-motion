$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Manifest = Get-Content (Join-Path $PSScriptRoot "assets-manifest.json") | ConvertFrom-Json
foreach ($Asset in $Manifest.assets) {
  $Destination = Join-Path $Root $Asset.path
  New-Item -ItemType Directory -Force -Path (Split-Path $Destination) | Out-Null
  Invoke-WebRequest -Uri $Asset.url -OutFile $Destination
  $Actual = (Get-FileHash -Algorithm SHA256 $Destination).Hash.ToLower()
  if ($Actual -ne $Asset.sha256.ToLower()) { Remove-Item $Destination; throw "Checksum mismatch: $($Asset.path)" }
  Write-Host "[ok] $($Asset.path)"
}

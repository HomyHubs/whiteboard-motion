$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m backend.cli models download voxcpm2
python -m backend.cli models verify voxcpm2

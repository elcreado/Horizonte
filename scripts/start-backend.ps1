$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
docker compose up --build -d --wait backend worker
if ($LASTEXITCODE -ne 0) { throw 'No se pudo iniciar backend/worker. Revisa docker compose logs.' }

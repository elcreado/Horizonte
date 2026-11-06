$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
docker compose up --build -d worker
if ($LASTEXITCODE -ne 0) { throw 'No se pudo iniciar el worker. Revisa docker compose logs worker.' }

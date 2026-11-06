$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
docker compose up --build -d --wait
if ($LASTEXITCODE -ne 0) { throw 'Revisa Docker Desktop y docker compose logs.' }
Write-Host 'Web: http://127.0.0.1:5173 · Logs: docker compose logs -f backend worker frontend'

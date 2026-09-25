$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
docker compose up -d --wait
if ($LASTEXITCODE -ne 0) { throw 'Abre Docker Desktop y espera a que el motor esté listo.' }
$env:POSTGRES_HOST = '127.0.0.1'
$env:POSTGRES_DB = 'liquidity'
$env:POSTGRES_USER = 'liquidity'
$env:POSTGRES_PASSWORD = 'local-development-only'
$env:CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
& .\.venv\Scripts\python backend\manage.py migrate
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron aplicar las migraciones.' }
& .\.venv\Scripts\python backend\manage.py runserver 127.0.0.1:8000 --noreload

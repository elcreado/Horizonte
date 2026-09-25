$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:POSTGRES_HOST = '127.0.0.1'
$env:POSTGRES_DB = 'liquidity'
$env:POSTGRES_USER = 'liquidity'
$env:POSTGRES_PASSWORD = 'local-development-only'
$env:CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
& .\.venv\Scripts\celery -A config.celery:app --workdir backend worker --pool=solo --loglevel=info

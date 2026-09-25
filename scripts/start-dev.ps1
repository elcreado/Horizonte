$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
docker compose up -d --wait
if ($LASTEXITCODE -ne 0) { throw 'Abre Docker Desktop y espera a que el motor esté listo.' }
$env:POSTGRES_HOST = '127.0.0.1'
$env:POSTGRES_DB = 'liquidity'
$env:POSTGRES_USER = 'liquidity'
$env:POSTGRES_PASSWORD = 'local-development-only'
$env:CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
& $python backend\manage.py migrate
if ($LASTEXITCODE -ne 0) { throw 'Error aplicando migraciones.' }
$logDirectory = Join-Path $projectRoot '.local-logs'
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null

function Test-ProjectListener([int]$port) {
    $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $listener) { return $false }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)"
    if ($process.CommandLine -notlike "*$projectRoot*") { throw "El puerto $port está ocupado por otro proceso. No se ha detenido." }
    return $true
}

if (-not (Test-ProjectListener 8000)) {
    Start-Process -FilePath $python -ArgumentList '-u', 'backend/manage.py', 'runserver', '127.0.0.1:8000', '--noreload' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput "$logDirectory\backend.log" -RedirectStandardError "$logDirectory\backend-error.log"
}
$workers = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -like "*$projectRoot*" -and $_.CommandLine -like '*celery*worker*' }
if (-not $workers) {
    Start-Process -FilePath $python -ArgumentList '-m', 'celery', '-A', 'config.celery:app', '--workdir', 'backend', 'worker', '--pool=solo', '--loglevel=info' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput "$logDirectory\worker.log" -RedirectStandardError "$logDirectory\worker-error.log"
}
if (-not (Test-ProjectListener 5173)) {
    $node = (Get-Command node).Source
    Start-Process -FilePath $node -ArgumentList ('"' + (Join-Path $projectRoot 'frontend\node_modules\vite\bin\vite.js') + '"'), '--host', '127.0.0.1', '--strictPort' -WorkingDirectory "$projectRoot\frontend" -WindowStyle Hidden -RedirectStandardOutput "$logDirectory\frontend.log" -RedirectStandardError "$logDirectory\frontend-error.log"
}
Write-Output 'Servicios iniciados o ya disponibles. Abre http://127.0.0.1:5173. Logs locales: .local-logs.'

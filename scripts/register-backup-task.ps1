param(
    [ValidateRange(0, 23)][int]$Hour = 2,
    [ValidateRange(0, 59)][int]$Minute = 0
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$backupScript = Join-Path $projectRoot 'scripts\db-backup.py'
if (-not (Test-Path -LiteralPath $python) -or -not (Test-Path -LiteralPath $backupScript)) {
    throw 'Faltan el entorno Python o el script de respaldo.'
}
$taskName = 'Horizonte Local Backup'
$action = New-ScheduledTaskAction -Execute $python -Argument ('"' + $backupScript + '" --restore-check') -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Daily -At (Get-Date -Hour $Hour -Minute $Minute -Second 0)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
$task = Get-ScheduledTask -TaskName $taskName
Write-Output "Tarea $($task.TaskName) registrada: respaldo diario a las $($Hour.ToString('00')):$($Minute.ToString('00')) si Docker Desktop está disponible."

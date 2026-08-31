$ErrorActionPreference = 'Stop'
$PidFile = 'C:\HoN-Plus-Stats\artifacts\api.pid'
if (-not (Test-Path -LiteralPath $PidFile)) { Write-Host 'PID-файл HoN Plus API не найден.'; exit 0 }
$ApiPid = [int](Get-Content -Raw -LiteralPath $PidFile)
$Process = Get-Process -Id $ApiPid -ErrorAction SilentlyContinue
if ($Process) { Stop-Process -Id $ApiPid; $Process.WaitForExit(5000) | Out-Null }
Remove-Item -LiteralPath $PidFile -Force
Write-Host 'HoN Plus API остановлен.'

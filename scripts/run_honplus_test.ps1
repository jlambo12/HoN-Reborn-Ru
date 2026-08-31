param([string]$StatsRoot = 'C:\HoN-Plus-Stats')
$ErrorActionPreference = 'Stop'
$JuvioRoot = Join-Path $env:LOCALAPPDATA 'Juvio'
$Exe = Join-Path $JuvioRoot 'bin\juvio.exe'
$Extension = Join-Path $JuvioRoot 'extensions\resources0.jz'
$StatsDll = Join-Path $StatsRoot 'HonPlusCollector\bin\Release\net8.0\HonPlusCollector.dll'
$Artifacts = Join-Path $StatsRoot 'artifacts'

if (Get-Process -Name 'juvio' -ErrorAction SilentlyContinue) { throw 'Juvio/HoN уже запущена.' }
foreach ($Path in @($Exe, $Extension, $StatsDll, (Join-Path $StatsRoot 'honplus.db'))) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Не найден обязательный файл: $Path" }
}
$Healthy = $false
try { $Healthy = (Invoke-RestMethod 'http://127.0.0.1:17821/health' -TimeoutSec 2).status -eq 'ok' } catch {}
if (-not $Healthy) {
    New-Item -ItemType Directory -Path (Join-Path $Artifacts 'logs') -Force | Out-Null
    $Process = Start-Process -FilePath 'dotnet' -ArgumentList @($StatsDll, 'serve', '--port', '17821') `
        -WorkingDirectory $StatsRoot -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $Artifacts 'logs\api.stdout.log') `
        -RedirectStandardError (Join-Path $Artifacts 'logs\api.stderr.log') -PassThru
    Set-Content -LiteralPath (Join-Path $Artifacts 'api.pid') -Value $Process.Id
    for ($Attempt = 0; $Attempt -lt 20; $Attempt++) {
        try { if ((Invoke-RestMethod 'http://127.0.0.1:17821/health' -TimeoutSec 2).status -eq 'ok') { $Healthy = $true; break } } catch {}
        Start-Sleep -Milliseconds 250
    }
}
if (-not $Healthy) { throw 'Локальный API HoN Plus не запустился. Проверьте artifacts\logs\api.stderr.log.' }

$Arguments = '-mod "heroes of newerth;extensions" -host_locale ru'
$Game = Start-Process -FilePath $Exe -ArgumentList $Arguments -WorkingDirectory $JuvioRoot -PassThru
Write-Host "HoN Plus API: готов. Juvio PID: $($Game.Id)"

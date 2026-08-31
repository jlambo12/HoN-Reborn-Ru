$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$StatePath = Join-Path $ProjectRoot 'reports\honplus_test_install_state.json'
$ExpectedTarget = [System.IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Juvio\extensions\resources0.jz'))

if (Get-Process -Name 'juvio' -ErrorAction SilentlyContinue) {
    throw 'Закройте Juvio/HoN перед откатом тестовой сборки HoN Plus.'
}
if (-not (Test-Path -LiteralPath $StatePath -PathType Leaf)) { throw "Состояние тестовой установки не найдено: $StatePath" }
$State = Get-Content -Raw -LiteralPath $StatePath | ConvertFrom-Json
$Target = [System.IO.Path]::GetFullPath([string]$State.installed.path)
if ($Target -ne $ExpectedTarget) { throw "Небезопасный путь назначения в состоянии установки: $Target" }
if (-not (Test-Path -LiteralPath $Target -PathType Leaf)) { throw "Установленный архив отсутствует: $Target" }
$CurrentSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($CurrentSha -ne ([string]$State.installed.sha256).ToLowerInvariant()) {
    throw 'Установленный архив был изменён после установки; автоматический откат остановлен.'
}

if ($State.backup -and (Test-Path -LiteralPath ([string]$State.backup.path) -PathType Leaf)) {
    $Backup = [System.IO.Path]::GetFullPath([string]$State.backup.path)
    $BackupRoot = [System.IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Juvio\extensions\backups'))
    if (-not $Backup.StartsWith($BackupRoot + [System.IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
        throw "Небезопасный путь резервной копии: $Backup"
    }
    $BackupSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Backup).Hash.ToLowerInvariant()
    if ($BackupSha -ne ([string]$State.backup.sha256).ToLowerInvariant()) { throw 'Резервная копия повреждена.' }
    $Temporary = Join-Path (Split-Path -Parent $Target) '.resources0-honplus-restore.tmp'
    if (Test-Path -LiteralPath $Temporary) { Remove-Item -LiteralPath $Temporary -Force }
    Copy-Item -LiteralPath $Backup -Destination $Temporary
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Temporary).Hash.ToLowerInvariant() -ne $BackupSha) {
        Remove-Item -LiteralPath $Temporary -Force
        throw 'Проверка временной копии отката не прошла.'
    }
    Move-Item -LiteralPath $Temporary -Destination $Target -Force
    Write-Host "Предыдущий архив восстановлен: $BackupSha"
} else {
    Remove-Item -LiteralPath $Target -Force
    Write-Host 'До теста расширение отсутствовало; тестовый архив удалён.'
}
Remove-Item -LiteralPath $StatePath -Force

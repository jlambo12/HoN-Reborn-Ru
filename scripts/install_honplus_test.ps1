param([switch]$Launch)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$JuvioRoot = Join-Path $env:LOCALAPPDATA 'Juvio'
$GameArchive = Join-Path $JuvioRoot 'heroes of newerth\resources0.jz'
$ExtensionDirectory = Join-Path $JuvioRoot 'extensions'
$Target = Join-Path $ExtensionDirectory 'resources0.jz'
$Build = Join-Path $ProjectRoot 'build\honplus-test\resources0.jz'
$ExpectedGameSha = '1802e16e5518b729256782d2d77643c092e6300b7eb05bebd849f96545969b93'

if (Get-Process -Name 'juvio' -ErrorAction SilentlyContinue) {
    throw 'Закройте Juvio/HoN перед установкой тестовой сборки HoN Plus.'
}
foreach ($Path in @($GameArchive, $Build)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Не найден обязательный файл: $Path" }
}
$GameSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $GameArchive).Hash.ToLowerInvariant()
if ($GameSha -ne $ExpectedGameSha) { throw "Версия ресурсов игры изменилась; безопасная установка остановлена: $GameSha" }
$Crc = & py -3.14 -c "import sys,zipfile; z=zipfile.ZipFile(sys.argv[1]); bad=z.testzip(); z.close(); print('PASS' if bad is None else 'FAIL:'+bad)" $Build
if ($LASTEXITCODE -ne 0 -or $Crc -ne 'PASS') { throw "Архив HoN Plus повреждён: $Crc" }
$BuildSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Build).Hash.ToLowerInvariant()

$BackupDirectory = Join-Path $ExtensionDirectory 'backups'
New-Item -ItemType Directory -Path $BackupDirectory -Force | Out-Null
$Backup = $null
if (Test-Path -LiteralPath $Target -PathType Leaf) {
    $Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $Backup = Join-Path $BackupDirectory "resources0-before-honplus-$Stamp-$([guid]::NewGuid().ToString('N').Substring(0,8)).jz"
    Copy-Item -LiteralPath $Target -Destination $Backup
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Backup).Hash -ne (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash) {
        throw 'Проверка резервной копии не прошла; установленный файл не изменён.'
    }
}
$Temporary = Join-Path $ExtensionDirectory '.resources0-honplus-install.tmp'
if (Test-Path -LiteralPath $Temporary) { Remove-Item -LiteralPath $Temporary -Force }
Copy-Item -LiteralPath $Build -Destination $Temporary
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Temporary).Hash.ToLowerInvariant() -ne $BuildSha) {
    Remove-Item -LiteralPath $Temporary -Force
    throw 'Проверка временной копии не прошла.'
}
Move-Item -LiteralPath $Temporary -Destination $Target -Force
$InstalledSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($InstalledSha -ne $BuildSha) { throw 'Проверка установленной сборки не прошла.' }

Write-Host "HoN Plus установлен. SHA-256: $InstalledSha"
if ($Backup) { Write-Host "Резервная копия: $Backup" }
if ($Launch) { & "$PSScriptRoot\run_honplus_test.ps1" }

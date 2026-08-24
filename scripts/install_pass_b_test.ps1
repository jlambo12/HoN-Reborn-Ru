param([switch]$Launch)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$JuvioRoot = Join-Path $env:LOCALAPPDATA "Juvio"
$GameArchive = Join-Path $JuvioRoot "heroes of newerth\resources0.jz"
$Target = Join-Path $JuvioRoot "extensions\resources0.jz"
$Build = Join-Path $ProjectRoot "build\pass-b\resources0.jz"
$BackupDirectory = Join-Path $JuvioRoot "extensions\backups"
$StatePath = Join-Path $ProjectRoot "reports\pass_b_install_state.json"
$ExpectedGameSha = "a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762"
$ExpectedFontSha = "96e4d1c6d2b8a772322affbea3be367020a2bba07b89b80dd71b1752babd2868"
$ExpectedBuildSha = "d71f85e3321c3954e877f2ccfa516c1e87f2006371499d491c83fd565fb1cb3d"

if (Get-Process -Name "juvio" -ErrorAction SilentlyContinue) {
    throw "Close Juvio/HoN before installing the Pass B test build."
}
foreach ($Path in @($GameArchive, $Target, $Build)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required archive is absent: $Path" }
}
$GameSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $GameArchive).Hash.ToLowerInvariant()
if ($GameSha -ne $ExpectedGameSha) { throw "Main game archive baseline changed; refusing install: $GameSha" }
$CurrentSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($CurrentSha -ne $ExpectedFontSha) { throw "Installed extension is not the accepted font baseline: $CurrentSha" }
$BuildSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Build).Hash.ToLowerInvariant()
if ($BuildSha -ne $ExpectedBuildSha) { throw "Pass B build SHA mismatch: $BuildSha" }
$Crc = & py -3.14 -c "import sys,zipfile; z=zipfile.ZipFile(sys.argv[1]); bad=z.testzip(); z.close(); print('PASS' if bad is None else 'FAIL:'+bad)" $Build
if ($LASTEXITCODE -ne 0 -or $Crc -ne "PASS") { throw "Pass B build CRC failed: $Crc" }

New-Item -ItemType Directory -Path $BackupDirectory -Force | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Backup = Join-Path $BackupDirectory "resources0-before-pass-b-$Stamp.jz"
Copy-Item -LiteralPath $Target -Destination $Backup
$BackupSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Backup).Hash.ToLowerInvariant()
if ($BackupSha -ne $ExpectedFontSha) { throw "Rollback backup verification failed: $BackupSha" }

$Temporary = Join-Path (Split-Path -Parent $Target) ".resources0-pass-b-install.tmp"
Copy-Item -LiteralPath $Build -Destination $Temporary -Force
$TemporarySha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Temporary).Hash.ToLowerInvariant()
if ($TemporarySha -ne $ExpectedBuildSha) { throw "Temporary install copy verification failed: $TemporarySha" }
Move-Item -LiteralPath $Temporary -Destination $Target -Force
$InstalledSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($InstalledSha -ne $ExpectedBuildSha) { throw "Installed build verification failed: $InstalledSha" }

$State = [ordered]@{
    installed_at = (Get-Date).ToString("o")
    main_game_archive = [ordered]@{ path = $GameArchive; sha256 = $GameSha; modified = $false }
    installed = [ordered]@{ path = $Target; sha256 = $InstalledSha; crc = $Crc }
    backup = [ordered]@{ path = $Backup; sha256 = $BackupSha }
}
$State | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $StatePath -Encoding utf8
Write-Host "Pass B test installed. Rollback backup: $Backup"

if ($Launch) {
    $Exe = Join-Path $JuvioRoot "bin\juvio.exe"
    Start-Process -FilePath $Exe -ArgumentList '-mod "heroes of newerth;extensions" -host_locale ru' -WorkingDirectory $JuvioRoot | Out-Null
}

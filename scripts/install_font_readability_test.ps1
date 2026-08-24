param([switch]$Launch)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$JuvioRoot = Join-Path $env:LOCALAPPDATA "Juvio"
$GameArchive = Join-Path $JuvioRoot "heroes of newerth\resources0.jz"
$Target = Join-Path $JuvioRoot "extensions\resources0.jz"
$Build = Join-Path $ProjectRoot "build\font-readability\resources0.jz"
$BackupDirectory = Join-Path $JuvioRoot "extensions\backups"
$StatePath = Join-Path $ProjectRoot "reports\font_readability_install_state.json"
$ExpectedGameSha = "a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762"
$ExpectedPhase2aSha = "9d5d4176ff51f1799df50d9f7f61ba387ec7cdc54244cb7393e8c87f7143945c"

if (Get-Process -Name "juvio" -ErrorAction SilentlyContinue) {
    throw "Close Juvio/HoN before installing the font readability build."
}
foreach ($Path in @($GameArchive, $Target, $Build)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required archive is absent: $Path" }
}
$GameSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $GameArchive).Hash.ToLowerInvariant()
if ($GameSha -ne $ExpectedGameSha) { throw "Main game archive baseline changed; refusing install: $GameSha" }
$CurrentSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($CurrentSha -ne $ExpectedPhase2aSha) { throw "Installed extension is not the reviewed Phase 2A baseline: $CurrentSha" }
$BuildSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Build).Hash.ToLowerInvariant()

New-Item -ItemType Directory -Path $BackupDirectory -Force | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Backup = Join-Path $BackupDirectory "resources0-before-font-$Stamp.jz"
Copy-Item -LiteralPath $Target -Destination $Backup
$BackupSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Backup).Hash.ToLowerInvariant()
if ($BackupSha -ne $ExpectedPhase2aSha) { throw "Backup verification failed: $BackupSha" }

$Temporary = Join-Path (Split-Path -Parent $Target) ".resources0-font-install.tmp"
Copy-Item -LiteralPath $Build -Destination $Temporary -Force
$TemporarySha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Temporary).Hash.ToLowerInvariant()
if ($TemporarySha -ne $BuildSha) { throw "Temporary install copy verification failed: $TemporarySha" }
Move-Item -LiteralPath $Temporary -Destination $Target -Force
$InstalledSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($InstalledSha -ne $BuildSha) { throw "Installed build verification failed: $InstalledSha" }

$State = [ordered]@{
    installed_at = (Get-Date).ToString("o")
    main_game_archive = [ordered]@{ path = $GameArchive; sha256 = $GameSha; modified = $false }
    installed = [ordered]@{ path = $Target; sha256 = $InstalledSha }
    backup = [ordered]@{ path = $Backup; sha256 = $BackupSha }
}
$State | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $StatePath -Encoding utf8
Write-Host "Font readability test installed. Backup: $Backup"

if ($Launch) { & "$PSScriptRoot\run_ru_test.ps1" }

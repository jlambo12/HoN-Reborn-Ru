param([switch]$RemoveRu)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$StatePath = Join-Path $ProjectRoot "reports\phase2a_install_state.json"
$JuvioRoot = Join-Path $env:LOCALAPPDATA "Juvio"
$Target = Join-Path $JuvioRoot "extensions\resources0.jz"
$Phase2aSha = "9d5d4176ff51f1799df50d9f7f61ba387ec7cdc54244cb7393e8c87f7143945c"

if (-not (Test-Path -LiteralPath $Target)) {
    if ($RemoveRu) { Write-Host "RU extension is already absent."; exit 0 }
    throw "Installed extension is absent: $Target"
}
$CurrentSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($CurrentSha -ne $Phase2aSha) { throw "Refusing to modify an extension that is not the installed Phase 2A build: $CurrentSha" }
if ($RemoveRu) {
    Remove-Item -LiteralPath $Target -Force
    Write-Host "Removed Phase 2A extension only. Main game archive was not touched."
    exit 0
}
if (-not (Test-Path -LiteralPath $StatePath)) { throw "Install state not found: $StatePath" }
$State = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
$Backup = [string]$State.backup.path
$ExpectedBackupSha = [string]$State.backup.sha256
if (-not (Test-Path -LiteralPath $Backup)) { throw "Probe backup not found: $Backup" }
$BackupSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Backup).Hash.ToLowerInvariant()
if ($BackupSha -ne $ExpectedBackupSha) { throw "Probe backup SHA mismatch: $BackupSha" }
$Temporary = Join-Path (Split-Path -Parent $Target) ".resources0-probe-restore.tmp"
Copy-Item -LiteralPath $Backup -Destination $Temporary -Force
Move-Item -LiteralPath $Temporary -Destination $Target -Force
$RestoredSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($RestoredSha -ne $ExpectedBackupSha) { throw "Probe restore verification failed: $RestoredSha" }
Write-Host "Probe extension restored from retained backup: $Backup"

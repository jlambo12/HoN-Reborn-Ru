$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$StatePath = Join-Path $ProjectRoot "reports\font_readability_install_state.json"
if (-not (Test-Path -LiteralPath $StatePath -PathType Leaf)) { throw "Install state is absent: $StatePath" }
if (Get-Process -Name "juvio" -ErrorAction SilentlyContinue) { throw "Close Juvio/HoN before rollback." }
$State = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
$Target = [string]$State.installed.path
$InstalledSha = [string]$State.installed.sha256
$Backup = [string]$State.backup.path
$BackupSha = [string]$State.backup.sha256
foreach ($Path in @($Target, $Backup)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Rollback archive is absent: $Path" }
}
$CurrentSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($CurrentSha -ne $InstalledSha) { throw "Refusing rollback over an unrecognized extension: $CurrentSha" }
$ActualBackupSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Backup).Hash.ToLowerInvariant()
if ($ActualBackupSha -ne $BackupSha) { throw "Backup SHA mismatch: $ActualBackupSha" }
$Temporary = Join-Path (Split-Path -Parent $Target) ".resources0-font-restore.tmp"
Copy-Item -LiteralPath $Backup -Destination $Temporary -Force
Move-Item -LiteralPath $Temporary -Destination $Target -Force
$RestoredSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($RestoredSha -ne $BackupSha) { throw "Rollback verification failed: $RestoredSha" }
Write-Host "Phase 2A extension restored from: $Backup"

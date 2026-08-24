$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$StatePath = Join-Path $ProjectRoot "reports\pass_c_install_state.json"
$ExpectedPassBSha = "d71f85e3321c3954e877f2ccfa516c1e87f2006371499d491c83fd565fb1cb3d"
$ExpectedPassCSha = "3d5ee66b9507c342d92b0be886d2918ea959e9beffb2126e6a7f77604142e301"

if (-not (Test-Path -LiteralPath $StatePath -PathType Leaf)) { throw "Pass C install state is absent: $StatePath" }
if (Get-Process -Name "juvio" -ErrorAction SilentlyContinue) { throw "Close Juvio/HoN before rollback." }
$State = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
$Target = [string]$State.installed.path
$Backup = [string]$State.backup.path
foreach ($Path in @($Target, $Backup)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Rollback archive is absent: $Path" }
}
$CurrentSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($CurrentSha -ne $ExpectedPassCSha) { throw "Refusing rollback over an unrecognized extension: $CurrentSha" }
$BackupSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Backup).Hash.ToLowerInvariant()
if ($BackupSha -ne $ExpectedPassBSha) { throw "Pass B rollback backup SHA mismatch: $BackupSha" }
$Temporary = Join-Path (Split-Path -Parent $Target) ".resources0-pass-c-restore.tmp"
Copy-Item -LiteralPath $Backup -Destination $Temporary -Force
Move-Item -LiteralPath $Temporary -Destination $Target -Force
$RestoredSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($RestoredSha -ne $ExpectedPassBSha) { throw "Pass B restore verification failed: $RestoredSha" }
Write-Host "Pass B restored from: $Backup"

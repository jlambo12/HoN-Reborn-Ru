$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$StatePath = Join-Path $ProjectRoot "reports\pass_b_install_state.json"
$ExpectedPassBSha = "d71f85e3321c3954e877f2ccfa516c1e87f2006371499d491c83fd565fb1cb3d"
$ExpectedFontSha = "96e4d1c6d2b8a772322affbea3be367020a2bba07b89b80dd71b1752babd2868"

if (-not (Test-Path -LiteralPath $StatePath -PathType Leaf)) { throw "Pass B install state is absent: $StatePath" }
if (Get-Process -Name "juvio" -ErrorAction SilentlyContinue) { throw "Close Juvio/HoN before rollback." }
$State = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
$Target = [string]$State.installed.path
$Backup = [string]$State.backup.path
foreach ($Path in @($Target, $Backup)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Rollback archive is absent: $Path" }
}
$CurrentSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($CurrentSha -ne $ExpectedPassBSha) { throw "Refusing rollback over an unrecognized extension: $CurrentSha" }
$BackupSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Backup).Hash.ToLowerInvariant()
if ($BackupSha -ne $ExpectedFontSha) { throw "Rollback backup SHA mismatch: $BackupSha" }
$Temporary = Join-Path (Split-Path -Parent $Target) ".resources0-pass-b-restore.tmp"
Copy-Item -LiteralPath $Backup -Destination $Temporary -Force
Move-Item -LiteralPath $Temporary -Destination $Target -Force
$RestoredSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($RestoredSha -ne $ExpectedFontSha) { throw "Rollback verification failed: $RestoredSha" }
Write-Host "Font/readability extension restored from: $Backup"

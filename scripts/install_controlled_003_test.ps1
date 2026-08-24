param([switch]$Launch)
$ErrorActionPreference = 'Stop'
$Project = Split-Path -Parent $PSScriptRoot
$Build = Join-Path $Project 'build\controlled-003\resources0.jz'
$Report = Join-Path $Project 'translation\reports\controlled_003_runtime_build.json'
$Juvio = Join-Path $env:LOCALAPPDATA 'Juvio'
$TargetDir = Join-Path $Juvio 'controlled_003_test'
$Target = Join-Path $TargetDir 'resources0.jz'
$BackupDir = Join-Path $Project 'backups\controlled_003_test'
$ExpectedPassC = '3d5ee66b9507c342d92b0be886d2918ea959e9beffb2126e6a7f77604142e301'
$InstalledPassC = Join-Path $Juvio 'extensions\resources0.jz'
if (!(Test-Path -LiteralPath $Build)) { throw "Missing build: $Build" }
if (!(Test-Path -LiteralPath $Report)) { throw "Missing build report: $Report" }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $InstalledPassC).Hash.ToLowerInvariant() -ne $ExpectedPassC) { throw 'Installed extensions archive is not accepted Pass C.' }
$BuildState = Get-Content -Raw -LiteralPath $Report | ConvertFrom-Json
if ($BuildState.result -ne 'PASS') { throw 'Controlled 003 build report is not PASS.' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Build).Hash.ToLowerInvariant() -ne $BuildState.output.sha256) { throw 'Build SHA does not match report.' }
New-Item -ItemType Directory -Force -Path $TargetDir,$BackupDir | Out-Null
if (Test-Path -LiteralPath $Target) {
    $Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    Copy-Item -LiteralPath $Target -Destination (Join-Path $BackupDir "resources0-before-$Stamp.jz")
}
Copy-Item -LiteralPath $Build -Destination $Target -Force
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant() -ne $BuildState.output.sha256) { throw 'Installed test SHA mismatch.' }
Write-Host "Installed isolated test: $Target"
Write-Host "SHA-256: $($BuildState.output.sha256)"
if ($Launch) {
    $Exe = Join-Path $Juvio 'bin\juvio.exe'
    Start-Process -FilePath $Exe -ArgumentList '-mod "heroes of newerth;controlled_003_test" -host_locale ru' -WorkingDirectory $Juvio
}

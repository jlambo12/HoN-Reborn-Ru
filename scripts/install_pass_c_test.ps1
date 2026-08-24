param([switch]$Launch)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$JuvioRoot = Join-Path $env:LOCALAPPDATA "Juvio"
$Upstream = Join-Path $JuvioRoot "heroes of newerth\resources0.jz"
$Target = Join-Path $JuvioRoot "extensions\resources0.jz"
$Build = Join-Path $ProjectRoot "build\pass-c\resources0.jz"
$BackupDirectory = Join-Path $JuvioRoot "extensions\backups"
$StatePath = Join-Path $ProjectRoot "reports\pass_c_install_state.json"
$ExpectedUpstreamSha = "a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762"
$ExpectedPassBSha = "d71f85e3321c3954e877f2ccfa516c1e87f2006371499d491c83fd565fb1cb3d"
$ExpectedPassCSha = "3d5ee66b9507c342d92b0be886d2918ea959e9beffb2126e6a7f77604142e301"

if (Get-Process -Name "juvio" -ErrorAction SilentlyContinue) { throw "Close Juvio/HoN before installing Pass C." }
foreach ($Path in @($Upstream, $Target, $Build)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required archive is absent: $Path" }
}
$UpstreamSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Upstream).Hash.ToLowerInvariant()
if ($UpstreamSha -ne $ExpectedUpstreamSha) { throw "Upstream game archive changed; refusing install: $UpstreamSha" }
$CurrentSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($CurrentSha -ne $ExpectedPassBSha) { throw "Installed extension is not accepted Pass B: $CurrentSha" }
$BuildSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Build).Hash.ToLowerInvariant()
if ($BuildSha -ne $ExpectedPassCSha) { throw "Pass C build SHA mismatch: $BuildSha" }
$Crc = & py -3.14 -c "import sys,zipfile; z=zipfile.ZipFile(sys.argv[1]); bad=z.testzip(); z.close(); print('PASS' if bad is None else 'FAIL:'+bad)" $Build
if ($LASTEXITCODE -ne 0 -or $Crc -ne "PASS") { throw "Pass C build CRC failed: $Crc" }

New-Item -ItemType Directory -Path $BackupDirectory -Force | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Backup = Join-Path $BackupDirectory "resources0-before-pass-c-$Stamp.jz"
Copy-Item -LiteralPath $Target -Destination $Backup
$BackupSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Backup).Hash.ToLowerInvariant()
if ($BackupSha -ne $ExpectedPassBSha) { throw "Pass B rollback backup verification failed: $BackupSha" }

$Temporary = Join-Path (Split-Path -Parent $Target) ".resources0-pass-c-install.tmp"
Copy-Item -LiteralPath $Build -Destination $Temporary -Force
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Temporary).Hash.ToLowerInvariant() -ne $ExpectedPassCSha) { throw "Temporary install copy verification failed" }
Move-Item -LiteralPath $Temporary -Destination $Target -Force
$InstalledSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash.ToLowerInvariant()
if ($InstalledSha -ne $ExpectedPassCSha) { throw "Installed Pass C verification failed: $InstalledSha" }

$State = [ordered]@{
    installed_at = (Get-Date).ToString("o")
    upstream = [ordered]@{ path = $Upstream; sha256 = $UpstreamSha; modified = $false }
    installed = [ordered]@{ path = $Target; sha256 = $InstalledSha; crc = $Crc }
    backup = [ordered]@{ path = $Backup; sha256 = $BackupSha }
}
$State | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $StatePath -Encoding utf8
Write-Host "Pass C installed. Rollback backup: $Backup"

if ($Launch) {
    $Exe = Join-Path $JuvioRoot "bin\juvio.exe"
    Start-Process -FilePath $Exe -ArgumentList '-mod "heroes of newerth;extensions" -host_locale ru' -WorkingDirectory $JuvioRoot | Out-Null
}

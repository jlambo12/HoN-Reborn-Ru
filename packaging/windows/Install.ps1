[CmdletBinding()]
param([switch]$Launch)

$ErrorActionPreference = "Stop"
$Version = "@@VERSION@@"
$ExpectedSha256 = "@@SHA256@@"
$PackageArchive = Join-Path $PSScriptRoot "resources0.jz"

if (-not $env:LOCALAPPDATA) {
    throw "LOCALAPPDATA is not defined. This installer supports Windows only."
}

$JuvioRoot = Join-Path $env:LOCALAPPDATA "Juvio"
$BaseArchive = Join-Path $JuvioRoot "heroes of newerth\resources0.jz"
$Executable = Join-Path $JuvioRoot "bin\juvio.exe"
$ExtensionDirectory = Join-Path $JuvioRoot "extensions"
$InstalledArchive = Join-Path $ExtensionDirectory "resources0.jz"
$StatePath = Join-Path $ExtensionDirectory "HoN-Reborn-RU-install.json"

if (-not (Test-Path -LiteralPath $PackageArchive -PathType Leaf)) {
    throw "The release archive is missing: $PackageArchive"
}
if (-not (Test-Path -LiteralPath $BaseArchive -PathType Leaf)) {
    throw "HoN Reborn was not found at: $BaseArchive"
}

$PackageSha256 = (Get-FileHash -LiteralPath $PackageArchive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($PackageSha256 -ne $ExpectedSha256) {
    throw "Release archive SHA-256 mismatch. Expected $ExpectedSha256, got $PackageSha256."
}

New-Item -ItemType Directory -Path $ExtensionDirectory -Force | Out-Null
$Backup = $null
$PreviousSha256 = $null
if (Test-Path -LiteralPath $InstalledArchive -PathType Leaf) {
    $PreviousSha256 = (Get-FileHash -LiteralPath $InstalledArchive -Algorithm SHA256).Hash.ToLowerInvariant()
    $BackupDirectory = Join-Path $ExtensionDirectory "backups\HoN-Reborn-RU"
    New-Item -ItemType Directory -Path $BackupDirectory -Force | Out-Null
    $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $Backup = Join-Path $BackupDirectory "resources0-before-v$Version-$Timestamp.jz"
    Copy-Item -LiteralPath $InstalledArchive -Destination $Backup
    $BackupSha256 = (Get-FileHash -LiteralPath $Backup -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($BackupSha256 -ne $PreviousSha256) {
        throw "Backup verification failed. Installation was stopped."
    }
}

$TemporaryArchive = Join-Path $ExtensionDirectory (".resources0-{0}.tmp" -f [guid]::NewGuid().ToString("N"))
try {
    Copy-Item -LiteralPath $PackageArchive -Destination $TemporaryArchive
    $TemporarySha256 = (Get-FileHash -LiteralPath $TemporaryArchive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($TemporarySha256 -ne $ExpectedSha256) {
        throw "Temporary copy verification failed."
    }
    Move-Item -LiteralPath $TemporaryArchive -Destination $InstalledArchive -Force
}
finally {
    if (Test-Path -LiteralPath $TemporaryArchive) {
        Remove-Item -LiteralPath $TemporaryArchive -Force
    }
}

$InstalledSha256 = (Get-FileHash -LiteralPath $InstalledArchive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($InstalledSha256 -ne $ExpectedSha256) {
    throw "Installed archive verification failed."
}

$State = [ordered]@{
    schema_version = 1
    product = "HoN-Reborn-RU"
    version = $Version
    installed_at = (Get-Date).ToUniversalTime().ToString("o")
    installed_sha256 = $InstalledSha256
    previous_sha256 = $PreviousSha256
    backup_path = $Backup
}
$State | ConvertTo-Json | Set-Content -LiteralPath $StatePath -Encoding UTF8

Write-Host "HoN Reborn RU v$Version installed successfully."
if ($Backup) {
    Write-Host "Previous extension backup: $Backup"
}

if ($Launch) {
    if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
        throw "Juvio executable was not found: $Executable"
    }
    $Arguments = '-mod "heroes of newerth;extensions" -host_locale ru'
    Start-Process -FilePath $Executable -ArgumentList $Arguments -WorkingDirectory $JuvioRoot | Out-Null
}


[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
if (-not $env:LOCALAPPDATA) {
    throw "LOCALAPPDATA is not defined. This uninstaller supports Windows only."
}

$JuvioRoot = Join-Path $env:LOCALAPPDATA "Juvio"
$ExtensionDirectory = Join-Path $JuvioRoot "extensions"
$InstalledArchive = Join-Path $ExtensionDirectory "resources0.jz"
$StatePath = Join-Path $ExtensionDirectory "HoN-Reborn-RU-install.json"
$AllowedBackupRoot = [IO.Path]::GetFullPath((Join-Path $ExtensionDirectory "backups\HoN-Reborn-RU"))

if (-not (Test-Path -LiteralPath $StatePath -PathType Leaf)) {
    throw "HoN Reborn RU installation state was not found: $StatePath"
}

$State = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
if ($State.product -ne "HoN-Reborn-RU" -or $State.schema_version -ne 1) {
    throw "Unrecognized installation state. No files were changed."
}
if (-not (Test-Path -LiteralPath $InstalledArchive -PathType Leaf)) {
    throw "Installed extension was not found. No files were changed."
}

$CurrentSha256 = (Get-FileHash -LiteralPath $InstalledArchive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($CurrentSha256 -ne [string]$State.installed_sha256) {
    throw "The installed extension was changed after installation. No files were changed."
}

if ($State.backup_path) {
    $Backup = [IO.Path]::GetFullPath([string]$State.backup_path)
    $AllowedPrefix = $AllowedBackupRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    if (-not $Backup.StartsWith($AllowedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe backup path in installation state."
    }
    if (-not (Test-Path -LiteralPath $Backup -PathType Leaf)) {
        throw "Previous extension backup was not found: $Backup"
    }
    $BackupSha256 = (Get-FileHash -LiteralPath $Backup -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($BackupSha256 -ne [string]$State.previous_sha256) {
        throw "Previous extension backup SHA-256 mismatch."
    }
    $TemporaryArchive = Join-Path $ExtensionDirectory (".resources0-restore-{0}.tmp" -f [guid]::NewGuid().ToString("N"))
    try {
        Copy-Item -LiteralPath $Backup -Destination $TemporaryArchive
        Move-Item -LiteralPath $TemporaryArchive -Destination $InstalledArchive -Force
    }
    finally {
        if (Test-Path -LiteralPath $TemporaryArchive) {
            Remove-Item -LiteralPath $TemporaryArchive -Force
        }
    }
    Write-Host "Previous extension restored from: $Backup"
}
else {
    Remove-Item -LiteralPath $InstalledArchive -Force
    Write-Host "HoN Reborn RU extension removed. There was no previous extension to restore."
}

Remove-Item -LiteralPath $StatePath -Force
Write-Host "HoN Reborn RU uninstalled successfully."


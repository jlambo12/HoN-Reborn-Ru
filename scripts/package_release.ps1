[CmdletBinding()]
param(
    [ValidatePattern('^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$')]
    [string]$Version = "0.1.0-beta.1",
    [string]$LauncherDirectory,
    [string]$OutputDirectory,
    [string]$PythonCommand = "python"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $LauncherDirectory) { $LauncherDirectory = Join-Path $ProjectRoot "dist\launcher" }
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $ProjectRoot "dist\release" }
$LauncherDirectory = [IO.Path]::GetFullPath($LauncherDirectory)
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
$AssetDirectory = Join-Path $ProjectRoot "release-assets\$Version"
$Translation = Join-Path $AssetDirectory "resources0.jz"
$Launcher = Join-Path $LauncherDirectory "HoNRebornRU.exe"
$Updater = Join-Path $LauncherDirectory "HoNRebornRU.Updater.exe"
$UpdateManifest = Join-Path $OutputDirectory "update-manifest.json"

foreach ($Path in @($Translation, $Launcher, $Updater, $UpdateManifest)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Release input missing: $Path" }
}
& $PythonCommand (Join-Path $ProjectRoot "tools\verify_update_manifest.py") --directory $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw "Update manifest verification failed" }

$StagingParent = [IO.Path]::GetFullPath((Join-Path $env:TEMP "HoN-Reborn-RU-package"))
New-Item -ItemType Directory -Path $StagingParent -Force | Out-Null
$Staging = [IO.Path]::GetFullPath((Join-Path $StagingParent ([guid]::NewGuid().ToString("N"))))
$AllowedPrefix = $StagingParent.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $Staging.StartsWith($AllowedPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Unsafe staging path: $Staging" }
New-Item -ItemType Directory -Path $Staging -Force | Out-Null

try {
    Copy-Item -LiteralPath $Translation -Destination (Join-Path $Staging "resources0.jz")
    Copy-Item -LiteralPath $Launcher -Destination (Join-Path $Staging "HoNRebornRU.exe")
    Copy-Item -LiteralPath $Updater -Destination (Join-Path $Staging "HoNRebornRU.Updater.exe")
    Copy-Item -LiteralPath $UpdateManifest -Destination (Join-Path $Staging "update-manifest.json")
    $ReadmeTemplate = Get-Content -LiteralPath (Join-Path $ProjectRoot "packaging\RELEASE-README.md") -Raw
    $TranslationSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Translation).Hash.ToLowerInvariant()
    $RenderedReadme = $ReadmeTemplate.Replace("@@VERSION@@", $Version).Replace("@@SHA256@@", $TranslationSha)
    Set-Content -LiteralPath (Join-Path $Staging "README.md") -Value $RenderedReadme -Encoding UTF8
    $InnerChecksums = Get-ChildItem -LiteralPath $Staging -File | Sort-Object Name | ForEach-Object {
        "$((Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant())  $($_.Name)"
    }
    Set-Content -LiteralPath (Join-Path $Staging "SHA256SUMS.txt") -Value $InnerChecksums -Encoding ASCII
    New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
    $PackagePath = Join-Path $OutputDirectory "HoN-Reborn-RU-v$Version-portable.zip"
    Compress-Archive -Path (Join-Path $Staging "*") -DestinationPath $PackagePath -CompressionLevel Optimal -Force
    Write-Host "Created: $PackagePath"
}
finally {
    if (Test-Path -LiteralPath $Staging) {
        $ResolvedStaging = [IO.Path]::GetFullPath($Staging)
        if ($ResolvedStaging.StartsWith($AllowedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            Remove-Item -LiteralPath $ResolvedStaging -Recurse -Force
        }
    }
}

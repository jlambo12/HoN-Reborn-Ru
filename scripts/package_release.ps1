[CmdletBinding()]
param(
    [ValidatePattern('^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$')]
    [string]$Version = "0.1.0",
    [string]$OutputDirectory
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $ProjectRoot "dist\release"
}

$AssetDirectory = Join-Path $ProjectRoot "release-assets\$Version"
$Archive = Join-Path $AssetDirectory "resources0.jz"
$ManifestPath = Join-Path $AssetDirectory "manifest.json"
if (-not (Test-Path -LiteralPath $Archive -PathType Leaf)) {
    throw "Release asset not found: $Archive"
}
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Release manifest not found: $ManifestPath"
}

$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$ArchiveSha256 = (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Manifest.version -ne $Version -or $Manifest.sha256 -ne $ArchiveSha256) {
    throw "Release manifest does not match resources0.jz."
}

$StagingParent = [IO.Path]::GetFullPath((Join-Path $env:TEMP "HoN-Reborn-RU-package"))
New-Item -ItemType Directory -Path $StagingParent -Force | Out-Null
$Staging = [IO.Path]::GetFullPath((Join-Path $StagingParent ([guid]::NewGuid().ToString("N"))))
$AllowedPrefix = $StagingParent.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $Staging.StartsWith($AllowedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe staging path: $Staging"
}

New-Item -ItemType Directory -Path $Staging -Force | Out-Null
try {
    Copy-Item -LiteralPath $Archive -Destination (Join-Path $Staging "resources0.jz")
    foreach ($TemplateName in @("Install.ps1", "Uninstall.ps1")) {
        $TemplatePath = Join-Path $ProjectRoot "packaging\windows\$TemplateName"
        $Rendered = (Get-Content -LiteralPath $TemplatePath -Raw).Replace("@@VERSION@@", $Version).Replace("@@SHA256@@", $ArchiveSha256)
        Set-Content -LiteralPath (Join-Path $Staging $TemplateName) -Value $Rendered -Encoding UTF8
    }
    $ReadmeTemplate = Get-Content -LiteralPath (Join-Path $ProjectRoot "packaging\RELEASE-README.md") -Raw
    $RenderedReadme = $ReadmeTemplate.Replace("@@VERSION@@", $Version).Replace("@@SHA256@@", $ArchiveSha256)
    Set-Content -LiteralPath (Join-Path $Staging "README.md") -Value $RenderedReadme -Encoding UTF8

    $ChecksumLines = Get-ChildItem -LiteralPath $Staging -File | Sort-Object Name | ForEach-Object {
        $Hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        "$Hash  $($_.Name)"
    }
    Set-Content -LiteralPath (Join-Path $Staging "SHA256SUMS.txt") -Value $ChecksumLines -Encoding ASCII

    New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
    $PackagePath = Join-Path $OutputDirectory "HoN-Reborn-RU-v$Version.zip"
    if (Test-Path -LiteralPath $PackagePath) {
        Remove-Item -LiteralPath $PackagePath -Force
    }
    Compress-Archive -Path (Join-Path $Staging "*") -DestinationPath $PackagePath -CompressionLevel Optimal
    $PackageSha256 = (Get-FileHash -LiteralPath $PackagePath -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content -LiteralPath (Join-Path $OutputDirectory "SHA256SUMS.txt") -Value "$PackageSha256  $(Split-Path -Leaf $PackagePath)" -Encoding ASCII
    Write-Host "Created: $PackagePath"
    Write-Host "SHA-256: $PackageSha256"
}
finally {
    if (Test-Path -LiteralPath $Staging) {
        $ResolvedStaging = [IO.Path]::GetFullPath($Staging)
        if ($ResolvedStaging.StartsWith($AllowedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            Remove-Item -LiteralPath $ResolvedStaging -Recurse -Force
        }
    }
}


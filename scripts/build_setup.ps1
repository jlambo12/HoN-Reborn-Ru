[CmdletBinding()]
param(
    [ValidatePattern('^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$')]
    [string]$Version = "0.1.0-beta.1",
    [string]$LauncherDirectory,
    [string]$OutputDirectory,
    [string]$InnoCompiler
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $LauncherDirectory) { $LauncherDirectory = Join-Path $ProjectRoot "dist\launcher" }
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $ProjectRoot "dist\release" }
if (-not $InnoCompiler) {
    $Candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )
    $InnoCompiler = $Candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
}
if (-not $InnoCompiler -or -not (Test-Path -LiteralPath $InnoCompiler -PathType Leaf)) {
    throw "Inno Setup 6 compiler was not found. It is a build-time dependency only."
}

$LauncherDirectory = [IO.Path]::GetFullPath($LauncherDirectory)
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$Script = Join-Path $ProjectRoot "installer\HoNRebornRU.iss"

& $InnoCompiler "/DMyAppVersion=$Version" "/DBuildRoot=$LauncherDirectory" "/DOutputRoot=$OutputDirectory" $Script
if ($LASTEXITCODE -ne 0) { throw "Setup compilation failed" }
$Setup = Join-Path $OutputDirectory "HoNRebornRU-Setup.exe"
if (-not (Test-Path -LiteralPath $Setup -PathType Leaf)) { throw "Setup output not found: $Setup" }
Write-Host "Created: $Setup"
Write-Host "SHA-256: $((Get-FileHash -Algorithm SHA256 -LiteralPath $Setup).Hash.ToLowerInvariant())"

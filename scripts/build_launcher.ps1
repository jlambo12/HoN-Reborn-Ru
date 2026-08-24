[CmdletBinding()]
param(
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$LauncherVersion = "1.0.0",
    [string]$OutputDirectory
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $ProjectRoot "dist\launcher"
}
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

$LauncherProject = Join-Path $ProjectRoot "launcher\HoNRebornRu.Launcher\HoNRebornRu.Launcher.csproj"
$UpdaterProject = Join-Path $ProjectRoot "launcher\HoNRebornRu.Updater\HoNRebornRu.Updater.csproj"

dotnet publish $LauncherProject -c Release -r win-x64 --self-contained true `
    -p:PublishSingleFile=true -p:Version=$LauncherVersion -o $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw "Launcher publish failed" }

dotnet publish $UpdaterProject -c Release -r win-x64 --self-contained true `
    -p:PublishSingleFile=true -p:Version=$LauncherVersion -o $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw "Updater publish failed" }

$Expected = @("HoNRebornRU.exe", "HoNRebornRU.Updater.exe")
foreach ($Name in $Expected) {
    $Path = Join-Path $OutputDirectory $Name
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Published binary not found: $Path"
    }
    $Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
    Write-Host "$Name SHA-256: $Hash"
}

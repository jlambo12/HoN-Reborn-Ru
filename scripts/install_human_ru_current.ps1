param([switch]$Launch)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$JuvioRoot = Join-Path $env:LOCALAPPDATA "Juvio"

py -3.14 "$ProjectRoot\tools\localization\install_human_current.py" --project-root $ProjectRoot --juvio-root $JuvioRoot
if ($LASTEXITCODE -ne 0) { throw "CURRENT Russian localization installation failed" }

if ($Launch) {
    & "$PSScriptRoot\run_ru_test.ps1"
}

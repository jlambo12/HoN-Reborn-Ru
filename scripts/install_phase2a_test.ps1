param([switch]$Launch)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$JuvioRoot = Join-Path $env:LOCALAPPDATA "Juvio"

py -3.14 "$ProjectRoot\tools\install_phase2a.py" --project-root $ProjectRoot --juvio-root $JuvioRoot
if ($LASTEXITCODE -ne 0) { throw "Phase 2A installation failed" }

if ($Launch) {
    & "$PSScriptRoot\run_ru_test.ps1"
}

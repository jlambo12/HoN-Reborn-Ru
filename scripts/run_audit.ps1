param(
    [string]$JuvioRoot = (Join-Path $env:LOCALAPPDATA "Juvio")
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

py -3.14 "$ProjectRoot\tools\audit.py" `
    --project-root "$ProjectRoot" `
    --juvio-root "$JuvioRoot"

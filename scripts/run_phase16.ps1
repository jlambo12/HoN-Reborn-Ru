param(
    [string]$JuvioRoot = (Join-Path $env:LOCALAPPDATA "Juvio")
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

& "$PSScriptRoot\run_audit.ps1" -JuvioRoot $JuvioRoot
& "$PSScriptRoot\run_preact_ast_scan.ps1"

$Arguments = @(
    "$ProjectRoot\tools\phase16_hardening.py",
    "--project-root", $ProjectRoot
)
$Phase15Bundle = "$ProjectRoot\HoN-Reborn-RU-review-bundle-v2.zip"
if (Test-Path -LiteralPath $Phase15Bundle -PathType Leaf) {
    $Arguments += @("--phase15-bundle", $Phase15Bundle)
}
py -3.14 @Arguments

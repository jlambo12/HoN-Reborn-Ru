$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Workspace = "$ProjectRoot\build\preact-baseline-workspace"
if (-not (Test-Path -LiteralPath "$Workspace\preact\node_modules\typescript" -PathType Container)) {
    throw "TypeScript dependency is missing. Run scripts/build_preact_baseline.ps1 first."
}

node "$ProjectRoot\tools\scan_preact_ast.mjs" `
    --snapshot $Workspace `
    --output "$ProjectRoot\catalog\extended_ui.jsonl" `
    --summary "$ProjectRoot\reports\preact_ast_summary.json" `
    --native-catalog "$ProjectRoot\catalog\strings.jsonl"


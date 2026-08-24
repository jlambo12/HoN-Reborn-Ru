$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Archive = Join-Path $env:LOCALAPPDATA "Juvio\heroes of newerth\resources0.jz"
$Snapshot = Get-ChildItem -LiteralPath "$ProjectRoot\src\upstream" -Directory | Sort-Object Name | Select-Object -Last 1
if (-not $Snapshot) { throw "No upstream snapshot. Run scripts/run_audit.ps1 first." }

py -3.14 "$ProjectRoot\tools\prepare_preact_workspace.py" `
    --project-root "$ProjectRoot" `
    --snapshot $Snapshot.FullName `
    --archive $Archive

Push-Location "$ProjectRoot\build\preact-baseline-workspace\preact"
try {
    & .\bun.exe install --frozen-lockfile
    if ($LASTEXITCODE -ne 0) { throw "bun install failed with exit code $LASTEXITCODE" }
    & .\bun.exe run build
    if ($LASTEXITCODE -ne 0) { throw "baseline build failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}

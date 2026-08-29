$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Archive = Join-Path $env:LOCALAPPDATA "Juvio\heroes of newerth\resources0.jz"
$ArchiveSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Archive).Hash.ToLowerInvariant()
$Snapshot = Join-Path $ProjectRoot ("src\upstream\" + $ArchiveSha.Substring(0, 12))
if (-not (Test-Path -LiteralPath $Snapshot -PathType Container)) {
    throw "No upstream snapshot for current archive $ArchiveSha. Run scripts/run_audit.ps1 first."
}

py -3.14 "$ProjectRoot\tools\prepare_preact_workspace.py" `
    --project-root "$ProjectRoot" `
    --snapshot $Snapshot `
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

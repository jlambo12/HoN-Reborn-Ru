$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Archive = Join-Path $env:LOCALAPPDATA "Juvio\heroes of newerth\resources0.jz"
$ArchiveSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Archive).Hash.ToLowerInvariant()
$Snapshot = Join-Path $ProjectRoot ("src\upstream\" + $ArchiveSha.Substring(0, 12))
if (-not (Test-Path -LiteralPath $Snapshot -PathType Container)) {
    throw "No upstream snapshot for current archive $ArchiveSha. Run scripts/run_audit.ps1 first."
}
$Workspace = Join-Path $ProjectRoot "build\phase2a-preact-workspace"

if (Test-Path -LiteralPath $Workspace) {
    $ResolvedBuild = (Resolve-Path (Join-Path $ProjectRoot "build")).Path
    $ResolvedWorkspace = (Resolve-Path $Workspace).Path
    if ((Split-Path -Parent $ResolvedWorkspace) -ne $ResolvedBuild -or (Split-Path -Leaf $ResolvedWorkspace) -ne "phase2a-preact-workspace") {
        throw "Unsafe Preact workspace target: $ResolvedWorkspace"
    }
    Remove-Item -LiteralPath $ResolvedWorkspace -Recurse -Force
}

py -3.14 "$ProjectRoot\tools\prepare_preact_workspace.py" `
    --project-root $ProjectRoot --snapshot $Snapshot --archive $Archive
if ($LASTEXITCODE -ne 0) { throw "Preact workspace preparation failed" }
Move-Item -LiteralPath "$ProjectRoot\build\preact-baseline-workspace" -Destination $Workspace

py -3.14 "$ProjectRoot\tools\prepare_phase2a_overrides.py" `
    --project-root $ProjectRoot --archive $Archive --preact-workspace $Workspace --skip-native
if ($LASTEXITCODE -ne 0) { throw "Phase 2A override preparation failed" }

Push-Location "$Workspace\preact"
try {
    & .\bun.exe install --frozen-lockfile
    if ($LASTEXITCODE -ne 0) { throw "bun install failed" }
    & .\bun.exe run build
    if ($LASTEXITCODE -ne 0) { throw "Preact RU build failed" }
} finally {
    Pop-Location
}

Push-Location "$Workspace\preact-remote"
try {
    & "$Workspace\preact\bun.exe" install --frozen-lockfile
    if ($LASTEXITCODE -ne 0) { throw "preact-remote bun install failed" }
    & "$Workspace\preact\bun.exe" run build
    if ($LASTEXITCODE -ne 0) { throw "Preact Remote RU build failed" }
} finally {
    Pop-Location
}

$ExtendedDist = Join-Path $ProjectRoot "src\extended_ru\preact\dist"
if (Test-Path -LiteralPath $ExtendedDist) { Remove-Item -LiteralPath $ExtendedDist -Recurse -Force }
New-Item -ItemType Directory -Path (Split-Path -Parent $ExtendedDist) -Force | Out-Null
Copy-Item -LiteralPath "$Workspace\preact\dist" -Destination $ExtendedDist -Recurse

$ExtendedRemoteDist = Join-Path $ProjectRoot "src\extended_ru\preact-remote\dist"
if (Test-Path -LiteralPath $ExtendedRemoteDist) { Remove-Item -LiteralPath $ExtendedRemoteDist -Recurse -Force }
New-Item -ItemType Directory -Path (Split-Path -Parent $ExtendedRemoteDist) -Force | Out-Null
Copy-Item -LiteralPath "$Workspace\preact-remote\dist" -Destination $ExtendedRemoteDist -Recurse

py -3.14 "$ProjectRoot\tools\build_locale.py" `
    --project-root $ProjectRoot `
    --snapshot $Snapshot `
    --scope "$ProjectRoot\catalog\phase2a_scope.json" `
    --output "$ProjectRoot\build\phase2a\resources0.jz"
if ($LASTEXITCODE -ne 0) { throw "Phase 2A archive build failed" }

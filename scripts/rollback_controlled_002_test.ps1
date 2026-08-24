$ErrorActionPreference = "Stop"
$ProjectRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$JuvioRoot = [System.IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA "Juvio"))
$TargetRoot = [System.IO.Path]::GetFullPath((Join-Path $JuvioRoot "controlled_002_test"))
$Target = [System.IO.Path]::GetFullPath((Join-Path $TargetRoot "resources0.jz"))
$ExpectedTargetRoot = [System.IO.Path]::GetFullPath("$JuvioRoot\controlled_002_test")
$StatePath = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "translation\reports\controlled_002_install_state.json"))

if (-not [string]::Equals($TargetRoot, $ExpectedTargetRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe rollback target: $TargetRoot"
}
if ($TargetRoot -like "*\extensions" -or $TargetRoot -like "*\heroes of newerth") {
    throw "Protected Juvio directory selected as rollback target"
}
if (-not (Test-Path -LiteralPath $StatePath -PathType Leaf)) { throw "Rollback state is absent: $StatePath" }
$State = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
if (-not [string]::Equals([System.IO.Path]::GetFullPath($State.target), $Target, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Rollback state target mismatch"
}
$Running = @(Get-CimInstance Win32_Process | Where-Object {
    $_.ExecutablePath -like "$JuvioRoot\*" -and $_.Name -match '^(juvio|hon|hon_x64|k2)\.exe$'
})
if ($Running.Count -gt 0) { throw "Close Juvio/HoN before rollback" }
if (Test-Path -LiteralPath $Target -PathType Leaf) {
    $CurrentSha = (Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($CurrentSha -ne $State.installed_sha256) { throw "Controlled 002 target changed after installation: $CurrentSha" }
}

if ($State.previous_target_existed) {
    if (-not (Test-Path -LiteralPath $State.rollback_backup -PathType Leaf)) { throw "Rollback archive is absent" }
    New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null
    Copy-Item -LiteralPath $State.rollback_backup -Destination $Target -Force
    Write-Host "RESTORED=$Target"
} elseif (Test-Path -LiteralPath $TargetRoot -PathType Container) {
    $Resolved = [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $TargetRoot).Path)
    if (-not [string]::Equals($Resolved, $ExpectedTargetRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Resolved rollback target escaped expected directory: $Resolved"
    }
    Remove-Item -LiteralPath $Resolved -Recurse -Force
    Write-Host "REMOVED=$Resolved"
}

if ($State.profile_startup_backup -and (Test-Path -LiteralPath $State.profile_startup_backup -PathType Leaf)) {
    Copy-Item -LiteralPath $State.profile_startup_backup -Destination $State.profile_startup -Force
    Write-Host "PROFILE_STARTUP_RESTORED=$($State.profile_startup)"
}
Write-Host 'PASS_C_COMMAND=-mod "heroes of newerth;extensions" -host_locale ru'

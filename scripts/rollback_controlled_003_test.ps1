$ErrorActionPreference = 'Stop'
$TargetDir = Join-Path $env:LOCALAPPDATA 'Juvio\controlled_003_test'
if (Test-Path -LiteralPath $TargetDir) {
    $Resolved = (Resolve-Path -LiteralPath $TargetDir).Path
    $ExpectedRoot = (Resolve-Path -LiteralPath (Join-Path $env:LOCALAPPDATA 'Juvio')).Path
    if (!$Resolved.StartsWith($ExpectedRoot, [System.StringComparison]::OrdinalIgnoreCase)) { throw "Unsafe rollback target: $Resolved" }
    Remove-Item -LiteralPath $Resolved -Recurse -Force
    Write-Host "Removed isolated Controlled 003 test: $Resolved"
} else {
    Write-Host 'Controlled 003 test is not installed; nothing to remove.'
}
Write-Host 'Pass C and upstream archives were not modified.'

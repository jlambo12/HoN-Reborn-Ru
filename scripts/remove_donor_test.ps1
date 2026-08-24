param([switch]$ForceClose)

$ErrorActionPreference = "Stop"
$JuvioRoot = [System.IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA "Juvio"))
$Target = [System.IO.Path]::GetFullPath((Join-Path $JuvioRoot "donor_test"))
$Expected = [System.IO.Path]::GetFullPath("$JuvioRoot\donor_test")

if (-not [string]::Equals($Target, $Expected, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe donor_test target: $Target"
}

$Relevant = @(Get-CimInstance Win32_Process | Where-Object {
    $_.ExecutablePath -like "$JuvioRoot\*" -and
    ($_.Name -match '^(juvio|hon|hon_x64|k2)\.exe$')
})
if ($Relevant.Count -gt 0 -and -not $ForceClose) {
    throw "Juvio/HoN is running. Close the donor test first, or rerun with -ForceClose."
}
if ($Relevant.Count -gt 0) {
    foreach ($ProcessInfo in $Relevant) {
        Stop-Process -Id $ProcessInfo.ProcessId -Force
    }
}

if (Test-Path -LiteralPath $Target) {
    Remove-Item -LiteralPath $Target -Recurse -Force
}
Write-Host "DONOR TEST 0 removed: $Target"

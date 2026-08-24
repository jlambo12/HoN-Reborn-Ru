param([switch]$Launch)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$JuvioRoot = Join-Path $env:LOCALAPPDATA "Juvio"

py -3.14 "$ProjectRoot\tools\localization\install_merged_v010.py" --project-root $ProjectRoot --juvio-root $JuvioRoot
if ($LASTEXITCODE -ne 0) { throw "Merged Russian 0.1.0 installation failed" }

if ($Launch) {
    $Exe = Join-Path $JuvioRoot "bin\juvio.exe"
    $ArgumentLine = '-mod "heroes of newerth;extensions" -host_locale ru'
    Write-Host ('Launching: "{0}" {1}' -f $Exe, $ArgumentLine)
    $Process = Start-Process -FilePath $Exe -ArgumentList $ArgumentLine -WorkingDirectory $JuvioRoot -PassThru
    Write-Host "Juvio launcher process id: $($Process.Id)"
}

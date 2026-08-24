param([switch]$NoLocaleOverride)
$ErrorActionPreference = "Stop"
$JuvioRoot = Join-Path $env:LOCALAPPDATA "Juvio"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Exe = Join-Path $JuvioRoot "bin\juvio.exe"
$Extension = Join-Path $JuvioRoot "extensions\resources0.jz"
$ReleaseReport = Join-Path $ProjectRoot "translation\reports\human_current_rebase.json"

if (-not (Test-Path -LiteralPath $Exe)) { throw "Juvio executable not found: $Exe" }
if (-not (Test-Path -LiteralPath $Extension)) { throw "RU extension not found: $Extension" }
if (-not (Test-Path -LiteralPath $ReleaseReport)) { throw "Validated CURRENT release report not found: $ReleaseReport" }
$ExpectedSha = ((Get-Content -LiteralPath $ReleaseReport -Raw | ConvertFrom-Json).output.sha256).ToLowerInvariant()
$InstalledSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Extension).Hash.ToLowerInvariant()
Write-Host "Installed extension SHA-256: $InstalledSha"
if ($InstalledSha -ne $ExpectedSha) { throw "Installed extension is not the validated CURRENT Russian build" }
$ArgumentLine = '-mod "heroes of newerth;extensions"'
if (-not $NoLocaleOverride) { $ArgumentLine += ' -host_locale ru' }
Write-Host ('Launching: "{0}" {1}' -f $Exe, $ArgumentLine)
$Process = Start-Process -FilePath $Exe -ArgumentList $ArgumentLine -WorkingDirectory $JuvioRoot -PassThru
Write-Host "Juvio launcher process id: $($Process.Id)"

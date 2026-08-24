$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Snapshot = Join-Path $ProjectRoot "src\upstream\a518f760c7bd"
$InstalledPassB = Join-Path $env:LOCALAPPDATA "Juvio\extensions\resources0.jz"
$LocaleBuild = Join-Path $ProjectRoot "build\pass-c-localization\resources0.jz"
$Output = Join-Path $ProjectRoot "build\pass-c\resources0.jz"
$ExpectedPassBSha = "d71f85e3321c3954e877f2ccfa516c1e87f2006371499d491c83fd565fb1cb3d"

if (-not (Test-Path -LiteralPath $InstalledPassB -PathType Leaf)) { throw "Installed Pass B baseline is absent: $InstalledPassB" }
$CurrentSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $InstalledPassB).Hash.ToLowerInvariant()
if ($CurrentSha -ne $ExpectedPassBSha) { throw "Installed extension is not the accepted Pass B baseline: $CurrentSha" }

py -3.14 "$ProjectRoot\tools\pass_c_cleanup.py"
if ($LASTEXITCODE -ne 0) { throw "Pass C catalog preparation failed" }

py -3.14 "$ProjectRoot\tools\build_locale.py" `
    --project-root $ProjectRoot --snapshot $Snapshot `
    --scope "$ProjectRoot\catalog\pass_c_scope.json" --output $LocaleBuild
if ($LASTEXITCODE -ne 0) { throw "Pass C localization build failed" }

py -3.14 "$ProjectRoot\tools\build_pass_c.py" `
    --project-root $ProjectRoot --base $InstalledPassB `
    --locale-build $LocaleBuild --output $Output
if ($LASTEXITCODE -ne 0) { throw "Pass C archive composition failed" }

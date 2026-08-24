$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$GameArchive = Join-Path $env:LOCALAPPDATA "Juvio\heroes of newerth\resources0.jz"
$Phase2aBuild = Join-Path $ProjectRoot "build\phase2a\resources0.jz"

py -3.14 "$ProjectRoot\tools\font_rendering_audit.py" `
    --project-root $ProjectRoot --archive $GameArchive --extract-help-images
if ($LASTEXITCODE -ne 0) { throw "Font rendering audit failed" }

py -3.14 "$ProjectRoot\tools\prepare_font_readability.py" `
    --project-root $ProjectRoot --game-archive $GameArchive --phase2a-build $Phase2aBuild
if ($LASTEXITCODE -ne 0) { throw "Font readability override preparation failed" }

py -3.14 "$ProjectRoot\tools\build_font_readability.py" `
    --project-root $ProjectRoot --base $Phase2aBuild
if ($LASTEXITCODE -ne 0) { throw "Font readability test build failed" }

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

py -3.14 "$ProjectRoot\tools\build_locale.py" `
    --project-root "$ProjectRoot" `
    --allow-fallback


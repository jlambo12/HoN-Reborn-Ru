$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

py -3.14 -m unittest discover -s "$ProjectRoot\tests" -p "test_*.py" -v
if ($LASTEXITCODE -ne 0) {
    throw "Test suite failed"
}

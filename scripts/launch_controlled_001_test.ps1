$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$JuvioRoot = [System.IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA "Juvio"))
$PassC = [System.IO.Path]::GetFullPath((Join-Path $JuvioRoot "extensions\resources0.jz"))
$Upstream = [System.IO.Path]::GetFullPath((Join-Path $JuvioRoot "heroes of newerth\resources0.jz"))
$Test = [System.IO.Path]::GetFullPath((Join-Path $JuvioRoot "controlled_001_test\resources0.jz"))
$Exe = [System.IO.Path]::GetFullPath((Join-Path $JuvioRoot "bin\juvio.exe"))
$ReportPath = Join-Path $ProjectRoot "translation\reports\controlled_001_runtime_build.json"
$ProfileRoot = [System.IO.Path]::GetFullPath((Join-Path $env:USERPROFILE "Documents\Juvio\controlled_001_test"))
$Startup = [System.IO.Path]::GetFullPath((Join-Path $ProfileRoot "startup.cfg"))
$ExpectedProfile = [System.IO.Path]::GetFullPath((Join-Path $env:USERPROFILE "Documents\Juvio\controlled_001_test"))
$ExpectedPassC = "3d5ee66b9507c342d92b0be886d2918ea959e9beffb2126e6a7f77604142e301"
$ExpectedUpstream = "a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762"

if (-not [string]::Equals($ProfileRoot, $ExpectedProfile, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe controlled test profile path: $ProfileRoot"
}
foreach ($Path in @($PassC, $Upstream, $Test, $Exe, $ReportPath)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required file is absent: $Path" }
}
if ((Get-FileHash -LiteralPath $PassC -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedPassC) {
    throw "Stable Pass C changed"
}
if ((Get-FileHash -LiteralPath $Upstream -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedUpstream) {
    throw "Upstream archive changed"
}
$Report = Get-Content -LiteralPath $ReportPath -Raw | ConvertFrom-Json
$TestSha = (Get-FileHash -LiteralPath $Test -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Report.result -ne "PASS" -or $Report.output.sha256 -ne $TestSha) {
    throw "Controlled test does not match the passing build report"
}
$FailedChecks = @($Report.checks.psobject.Properties | Where-Object { $_.Value -ne "PASS" })
if ($FailedChecks.Count -gt 0) { throw "Controlled test report contains failed checks" }
$Crc = & py -3.14 -c "import sys,zipfile; z=zipfile.ZipFile(sys.argv[1]); b=z.testzip(); z.close(); print('PASS' if b is None else 'FAIL:'+b)" $Test
if ($LASTEXITCODE -ne 0 -or $Crc -ne "PASS") { throw "Controlled test CRC failed: $Crc" }

$Running = @(Get-CimInstance Win32_Process | Where-Object {
    $_.ExecutablePath -like "$JuvioRoot\*" -and $_.Name -match '^(juvio|hon|hon_x64|k2)\.exe$'
})
if ($Running.Count -gt 0) { throw "Close Juvio/HoN before launching the controlled test" }

New-Item -ItemType Directory -Path $ProfileRoot -Force | Out-Null
if (Test-Path -LiteralPath $Startup -PathType Leaf) {
    $Backup = "$Startup.pre_controlled_001_locale_fix.bak"
    if (-not (Test-Path -LiteralPath $Backup)) { Copy-Item -LiteralPath $Startup -Destination $Backup }
    $Text = [System.IO.File]::ReadAllText($Startup)
    $Pattern = '(?m)^SetSave\s+"host_locale"\s+"[^"]*"\s*$'
    if ([regex]::Matches($Text, $Pattern).Count -gt 1) { throw "Duplicate host_locale entries in $Startup" }
    if ([regex]::IsMatch($Text, $Pattern)) {
        $Text = [regex]::Replace($Text, $Pattern, 'SetSave "host_locale" "ru"')
    } else {
        $Text = $Text.TrimEnd("`r", "`n") + "`r`n" + 'SetSave "host_locale" "ru"' + "`r`n"
    }
    [System.IO.File]::WriteAllText($Startup, $Text, [System.Text.UTF8Encoding]::new($false))
} else {
    [System.IO.File]::WriteAllText($Startup, "SetSave `"host_locale`" `"ru`"`r`n", [System.Text.UTF8Encoding]::new($false))
}
$LocaleLines = @(Select-String -LiteralPath $Startup -Pattern '^SetSave\s+"host_locale"\s+"([^"]*)"\s*$')
if ($LocaleLines.Count -ne 1 -or $LocaleLines[0].Matches[0].Groups[1].Value -ne "ru") {
    throw "Controlled profile locale pin failed"
}

$Process = Start-Process -FilePath $Exe -ArgumentList @('-mod','"heroes of newerth;controlled_001_test"','-host_locale','ru') -WorkingDirectory $JuvioRoot -PassThru
Start-Sleep -Seconds 5
$Live = Get-CimInstance Win32_Process -Filter "ProcessId = $($Process.Id)" -ErrorAction SilentlyContinue
if ($null -eq $Live) { throw "Juvio exited during controlled test launch" }
$SavedLocale = @(Select-String -LiteralPath $Startup -Pattern '^SetSave\s+"host_locale"\s+"([^"]*)"\s*$')
if ($SavedLocale.Count -ne 1 -or $SavedLocale[0].Matches[0].Groups[1].Value -ne "ru") {
    Stop-Process -Id $Process.Id -Force
    throw "Runtime reverted controlled profile locale away from ru"
}
Write-Host "LAUNCHED PID=$($Live.ProcessId)"
Write-Host "COMMAND=$($Live.CommandLine)"
Write-Host "TEST_SHA256=$TestSha"
Write-Host "PROFILE_LOCALE=ru"

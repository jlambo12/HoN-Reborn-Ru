param([switch]$Launch)

$ErrorActionPreference = "Stop"
$ProjectRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$JuvioRoot = [System.IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA "Juvio"))
$PassC = [System.IO.Path]::GetFullPath((Join-Path $JuvioRoot "extensions\resources0.jz"))
$Upstream = [System.IO.Path]::GetFullPath((Join-Path $JuvioRoot "heroes of newerth\resources0.jz"))
$Source = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "build\controlled-002\resources0.jz"))
$TargetRoot = [System.IO.Path]::GetFullPath((Join-Path $JuvioRoot "controlled_002_test"))
$Target = [System.IO.Path]::GetFullPath((Join-Path $TargetRoot "resources0.jz"))
$ExpectedTargetRoot = [System.IO.Path]::GetFullPath("$JuvioRoot\controlled_002_test")
$ReportPath = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "translation\reports\controlled_002_runtime_build.json"))
$StatePath = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "translation\reports\controlled_002_install_state.json"))
$BackupRoot = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "backups\controlled_002"))
$ProfileRoot = [System.IO.Path]::GetFullPath((Join-Path $env:USERPROFILE "Documents\Juvio\controlled_002_test"))
$Startup = [System.IO.Path]::GetFullPath((Join-Path $ProfileRoot "startup.cfg"))
$Exe = [System.IO.Path]::GetFullPath((Join-Path $JuvioRoot "bin\juvio.exe"))
$ExpectedPassC = "3d5ee66b9507c342d92b0be886d2918ea959e9beffb2126e6a7f77604142e301"
$ExpectedUpstream = "a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762"

if (-not [string]::Equals($TargetRoot, $ExpectedTargetRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe controlled test target: $TargetRoot"
}
if ($TargetRoot -like "*\extensions" -or $TargetRoot -like "*\heroes of newerth") {
    throw "Protected Juvio directory selected as target"
}
foreach ($Path in @($PassC, $Upstream, $Source, $ReportPath, $Exe)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required file is absent: $Path" }
}
$PassCSha = (Get-FileHash -LiteralPath $PassC -Algorithm SHA256).Hash.ToLowerInvariant()
$UpstreamSha = (Get-FileHash -LiteralPath $Upstream -Algorithm SHA256).Hash.ToLowerInvariant()
if ($PassCSha -ne $ExpectedPassC) { throw "Installed Pass C changed: $PassCSha" }
if ($UpstreamSha -ne $ExpectedUpstream) { throw "Upstream archive changed: $UpstreamSha" }

$Report = Get-Content -LiteralPath $ReportPath -Raw | ConvertFrom-Json
$SourceSha = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Report.result -ne "PASS" -or $Report.output.sha256 -ne $SourceSha) {
    throw "Controlled 002 build does not match its passing report"
}
$FailedChecks = @($Report.checks.psobject.Properties | Where-Object { $_.Value -ne "PASS" })
if ($FailedChecks.Count -gt 0) { throw "Controlled 002 build report contains failed checks" }
$SourceCrc = & py -3.14 -c "import sys,zipfile; z=zipfile.ZipFile(sys.argv[1]); b=z.testzip(); z.close(); print('PASS' if b is None else 'FAIL:'+b)" $Source
if ($LASTEXITCODE -ne 0 -or $SourceCrc -ne "PASS") { throw "Controlled 002 source CRC failed: $SourceCrc" }

$Running = @(Get-CimInstance Win32_Process | Where-Object {
    $_.ExecutablePath -like "$JuvioRoot\*" -and $_.Name -match '^(juvio|hon|hon_x64|k2)\.exe$'
})
if ($Running.Count -gt 0) { throw "Close Juvio/HoN before installing Controlled 002" }

$PreviousExists = Test-Path -LiteralPath $Target -PathType Leaf
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupDir = [System.IO.Path]::GetFullPath((Join-Path $BackupRoot $Timestamp))
$BackupArchive = $null
$BackupProfileStartup = $null
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
if ($PreviousExists) {
    $BackupArchive = [System.IO.Path]::GetFullPath((Join-Path $BackupDir "resources0.jz"))
    Copy-Item -LiteralPath $Target -Destination $BackupArchive
}
if (Test-Path -LiteralPath $Startup -PathType Leaf) {
    $BackupProfileStartup = [System.IO.Path]::GetFullPath((Join-Path $BackupDir "startup.cfg"))
    Copy-Item -LiteralPath $Startup -Destination $BackupProfileStartup
}

New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null
Copy-Item -LiteralPath $Source -Destination $Target -Force
$InstalledSha = (Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash.ToLowerInvariant()
if ($InstalledSha -ne $SourceSha) { throw "Installed Controlled 002 SHA mismatch: $InstalledSha" }
$InstalledCrc = & py -3.14 -c "import sys,zipfile; z=zipfile.ZipFile(sys.argv[1]); b=z.testzip(); z.close(); print('PASS' if b is None else 'FAIL:'+b)" $Target
if ($LASTEXITCODE -ne 0 -or $InstalledCrc -ne "PASS") { throw "Installed Controlled 002 CRC failed: $InstalledCrc" }

New-Item -ItemType Directory -Path $ProfileRoot -Force | Out-Null
if (Test-Path -LiteralPath $Startup -PathType Leaf) {
    $Text = [System.IO.File]::ReadAllText($Startup)
    $Pattern = '(?m)^SetSave\s+"host_locale"\s+"[^"]*"\s*$'
    if ([regex]::Matches($Text, $Pattern).Count -gt 1) { throw "Duplicate host_locale entries in $Startup" }
    if ([regex]::IsMatch($Text, $Pattern)) {
        $Text = [regex]::Replace($Text, $Pattern, 'SetSave "host_locale" "ru"')
    } else {
        $Text = $Text.TrimEnd("`r", "`n") + "`r`n" + 'SetSave "host_locale" "ru"' + "`r`n"
    }
} else {
    $Text = 'SetSave "host_locale" "ru"' + "`r`n"
}
[System.IO.File]::WriteAllText($Startup, $Text, [System.Text.UTF8Encoding]::new($false))

$State = [ordered]@{
    schema_version = 1
    installed_at = (Get-Date).ToString("o")
    target = $Target
    installed_sha256 = $InstalledSha
    installed_crc = $InstalledCrc
    source = $Source
    pass_c_sha256 = $PassCSha
    upstream_sha256 = $UpstreamSha
    previous_target_existed = $PreviousExists
    rollback_backup = $BackupArchive
    profile_startup = $Startup
    profile_startup_backup = $BackupProfileStartup
}
$State | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $StatePath -Encoding utf8

Write-Host "INSTALLED=$Target"
Write-Host "SHA256=$InstalledSha"
Write-Host "CRC=$InstalledCrc"
Write-Host "ROLLBACK_STATE=$StatePath"
Write-Host "ROLLBACK_BACKUP=$BackupArchive"

if ($Launch) {
    $Process = Start-Process -FilePath $Exe -ArgumentList @('-mod','"heroes of newerth;controlled_002_test"','-host_locale','ru') -WorkingDirectory $JuvioRoot -PassThru
    Start-Sleep -Seconds 5
    $Live = Get-CimInstance Win32_Process -Filter "ProcessId = $($Process.Id)" -ErrorAction SilentlyContinue
    if ($null -eq $Live) { throw "Juvio exited during Controlled 002 launch" }
    Write-Host "LAUNCHED_PID=$($Live.ProcessId)"
    Write-Host "COMMAND=$($Live.CommandLine)"
}

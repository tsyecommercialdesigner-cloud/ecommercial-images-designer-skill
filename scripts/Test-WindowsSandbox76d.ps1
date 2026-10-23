param(
    [switch]$RequireAdministrator,
    [switch]$PolicyDiagnosticsOnly,
    [string]$CliPath = 'C:\nvm\.nodejs\codex.exe',
    [string]$ExpectedVersion = 'codex-cli 0.153.0',
    [string]$ExpectedSha256
)

function Test-SandboxWriteDenial {
    param([int]$ExitCode, [string[]]$Output, [string]$LiteralPath)
    if ($ExitCode -eq 0 -or (Test-Path -LiteralPath $LiteralPath)) { return $false }
    $combined = $Output -join "`n"
    if ($combined -match 'helper_|sandbox failed|Failed to create|CreateProcessAsUserW failed') { return $false }
    $pathData = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes([IO.Path]::GetFullPath($LiteralPath)))
    $expected = 'SANDBOX_PROBE_ERROR_V1|operation=Write|type=System.UnauthorizedAccessException|hresult=-2147024891|pathUtf8Base64=' + $pathData
    return @($combined -split '\r?\n' | Where-Object { $_ -ceq $expected }).Count -eq 1
}

$ErrorActionPreference = 'Stop'
$cli = (Resolve-Path -LiteralPath $CliPath -ErrorAction Stop).Path
if ($ExpectedSha256 -and (Get-FileHash -LiteralPath $cli -Algorithm SHA256).Hash -ine $ExpectedSha256) {
    throw 'CLI SHA256 mismatch; no sandbox command executed.'
}
$projectRoot = Split-Path -Parent $PSScriptRoot
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($identity.Name -ne 'TSY-ICECREAM\Administrator') { throw 'Run as the original Windows user, not another administrator account.' }
if ($RequireAdministrator -and !$isAdmin) { throw 'Open PowerShell using Run as administrator first.' }
if (!$RequireAdministrator -and $isAdmin) { throw 'Acceptance must run from an ordinary, non-elevated PowerShell.' }
$version = (& $cli --version | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $version -ne $ExpectedVersion) { throw "Unexpected CLI: $version" }

$probe = Join-Path $projectRoot ('.eval-runs\sandbox-76d-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $probe -Force | Out-Null
$readFile = Join-Path $probe 'read.txt'
$writeFile = Join-Path $probe 'write.txt'
[IO.File]::WriteAllText($readFile, 'SANDBOX_READ_OK', [Text.UTF8Encoding]::new($false))
$argsCommon = @('-c', 'windows.sandbox="elevated"',
    '-c', 'approval_policy="never"', 'sandbox', '--permission-profile', ':read-only', '-C', $projectRoot, '--')

# Invoke the supported sandbox launcher, which performs its normal helper
# preparation/refresh. No direct ACL changes, config edits, or policy bypass.
# The invoking terminal can be Store PowerShell under protected WindowsApps.
# Use the OS-provided shell; do not grant sandbox users access to WindowsApps.
$shellExe = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
if (!(Test-Path -LiteralPath $shellExe -PathType Leaf)) { throw "System PowerShell missing: $shellExe" }
$probeScript = Join-Path $PSScriptRoot 'WindowsSandbox76dProbe.ps1'
# Query policy without loading any script. This diagnostic deliberately does
# not perform the denied probe's read/write work or override an execution policy.
# Intermediate native processes inherit PS7's module paths. Import the matching
# OS shell's manifests explicitly; normal PowerShell policy checks still apply.
# Join fixed source lines because this CLI proxy rejects newline arguments.
$policyQuery = @(
    '$ErrorActionPreference = "Stop";'
    '[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false);'
    '$context = [ordered]@{ identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name; edition = $PSVersionTable.PSEdition; version = $PSVersionTable.PSVersion.ToString(); psHome = $PSHOME; modulePath = $env:PSModulePath; languageMode = $ExecutionContext.SessionState.LanguageMode.ToString() };'
    'try {'
    'Import-Module -Name ($PSHOME + "\Modules\Microsoft.PowerShell.Security\Microsoft.PowerShell.Security.psd1") -Cmdlet Get-ExecutionPolicy -ErrorAction Stop;'
    'Import-Module -Name ($PSHOME + "\Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1") -Cmdlet ConvertTo-Json -ErrorAction Stop;'
    '$context.securityModule = (Get-Module Microsoft.PowerShell.Security).Path;'
    '$context.utilityModule = (Get-Module Microsoft.PowerShell.Utility).Path;'
    '$context.effective = (Get-ExecutionPolicy).ToString();'
    '$context.scopes = @(Get-ExecutionPolicy -List | ForEach-Object { [ordered]@{ scope = $_.Scope.ToString(); policy = $_.ExecutionPolicy.ToString() } });'
    '$context | ConvertTo-Json -Depth 4; exit 0;'
    '} catch {'
    'foreach ($entry in $context.GetEnumerator()) { [Console]::Error.WriteLine(("{0}={1}" -f $entry.Key, $entry.Value)) };'
    '[Console]::Error.WriteLine($_.Exception.ToString());'
    '[Console]::Error.WriteLine($_.FullyQualifiedErrorId);'
    '[Console]::Error.WriteLine($_.InvocationInfo.PositionMessage); exit 1;'
    '}'
) -join ' '
$hostPolicy = & $shellExe -NoProfile -NonInteractive -Command $policyQuery 2>&1
$hostPolicyCode = $LASTEXITCODE
$hostPolicy | Out-File -LiteralPath (Join-Path $probe 'host-policy.log') -Encoding utf8
if ($hostPolicyCode -ne 0) {
    throw "Host policy inspection failed.`n$($hostPolicy -join "`n")`nEvidence: $probe"
}
$sandboxPolicy = & $cli @argsCommon $shellExe -NoProfile -NonInteractive -Command $policyQuery 2>&1
$policyCode = $LASTEXITCODE
$sandboxPolicy | Out-File -LiteralPath (Join-Path $probe 'sandbox-policy.log') -Encoding utf8
if ($policyCode -ne 0) {
    throw "Sandbox policy inspection failed (exit $policyCode); effective policy remains unknown. No policy changed; no read/write probe executed.`n$($sandboxPolicy -join "`n")`nEvidence: $probe"
}
try { $policy = ($sandboxPolicy -join "`n") | ConvertFrom-Json -ErrorAction Stop }
catch { throw "Sandbox policy output was not JSON. Evidence: $probe" }
if (!$policy.identity -or !$policy.effective -or @($policy.scopes).Count -ne 5) {
    throw "Sandbox policy output incomplete. Evidence: $probe"
}
if ($PolicyDiagnosticsOnly) {
    Write-Output 'HOST: system Windows PowerShell policy'
    Write-Output $hostPolicy
    Write-Output 'SANDBOX: system Windows PowerShell policy'
    Write-Output $sandboxPolicy
    Write-Output "Diagnostics only; read/write acceptance NOT run. Evidence: $probe"
    return
}
$signature = Get-AuthenticodeSignature -LiteralPath $probeScript
if ($policy.effective -eq 'Restricted' -or
    ($policy.effective -eq 'AllSigned' -and $signature.Status -ne 'Valid')) {
    throw "Sandbox execution policy is $($policy.effective) for $($policy.identity). Probe is unsigned; no policy was changed. Inspect sandbox-policy.log and obtain an administrator-approved policy/signing decision before rerunning. Evidence: $probe"
}
$readOutput = & $cli @argsCommon $shellExe -NoProfile -NonInteractive -File $probeScript -Operation Read -LiteralPath $readFile 2>&1
$readCode = $LASTEXITCODE
$readOutput | Out-File -LiteralPath (Join-Path $probe 'read.log') -Encoding utf8
if ($readCode -ne 0 -or ($readOutput -join "`n") -notmatch 'SANDBOX_READ_OK') {
    throw "Sandbox read failed (exit $readCode).`n$($readOutput -join "`n")`nEvidence: $probe"
}
$skill = Join-Path $projectRoot '.agents\skills\ecommerce-image-designer\SKILL.md'
$skillOutput = & $cli @argsCommon $shellExe -NoProfile -NonInteractive -File $probeScript -Operation Read -LiteralPath $skill 2>&1
$skillCode = $LASTEXITCODE
$skillOutput | Out-File -LiteralPath (Join-Path $probe 'skill.log') -Encoding utf8
if ($skillCode -ne 0 -or ($skillOutput -join "`n") -notmatch '(?m)^---\s*$') {
    throw "Sandbox skill read failed (exit $skillCode).`n$($skillOutput -join "`n")`nEvidence: $probe"
}

$writeOutput = & $cli @argsCommon $shellExe -NoProfile -NonInteractive -File $probeScript -Operation Write -LiteralPath $writeFile 2>&1
$writeCode = $LASTEXITCODE
$writeOutput | Out-File -LiteralPath (Join-Path $probe 'write.log') -Encoding utf8
$writeFileExists = Test-Path -LiteralPath $writeFile
$writeDenied = Test-SandboxWriteDenial -ExitCode $writeCode -Output $writeOutput -LiteralPath $writeFile
[ordered]@{exitCode=$writeCode;fileExists=$writeFileExists;attributableDenial=$writeDenied} |
    ConvertTo-Json | Out-File -LiteralPath (Join-Path $probe 'write-result.json') -Encoding utf8
if ($writeCode -eq 0 -or $writeFileExists) {
    throw "Read-only write boundary failed. Evidence retained: $probe"
}
if (!$writeDenied) {
    throw "Write probe did not return an attributable filesystem denial (exit $writeCode).`n$($writeOutput -join "`n")`nEvidence: $probe"
}
$result = [ordered]@{cli=$cli;version=$version;identity=$identity.Name;administrator=$isAdmin;
    sandbox='elevated';mode='read-only';readExit=$readCode;skillReadExit=$skillCode;writeExit=$writeCode;
    writeFileExists=$false;normalUserAccepted=(!$isAdmin);evidence=$probe}
$result | ConvertTo-Json | Tee-Object -FilePath (Join-Path $probe 'result.json')
if ($isAdmin) { Write-Output 'Administrator retry passed. Close this terminal; acceptance still requires the ordinary-user run.' }
else { Write-Output 'PASS: ordinary-user read and read-only write denial. Ready for the free CLI suite.' }

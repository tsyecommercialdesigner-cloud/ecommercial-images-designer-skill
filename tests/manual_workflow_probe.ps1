param([Parameter(Mandatory=$true)][string]$RequestPath)
$ErrorActionPreference = 'Stop'
$ProbeRequest = Get-Content -Raw -LiteralPath $RequestPath | ConvertFrom-Json
$ProbeDocument = [IO.File]::ReadAllText($ProbeRequest.manual)
$ProbeBlocks = [regex]::Matches($ProbeDocument, '(?s)```powershell\r?\n(.*?)\r?\n```')
foreach ($ProbeBlock in $ProbeBlocks) {
    $ProbeTokens = $null; $ProbeErrors = $null
    [Management.Automation.Language.Parser]::ParseInput($ProbeBlock.Groups[1].Value, [ref]$ProbeTokens, [ref]$ProbeErrors) | Out-Null
    if ($ProbeErrors.Count) { throw ($ProbeErrors | Out-String) }
}
function Get-ProbeBlock([string]$Marker) {
    $ProbeMatch = [regex]::Match($ProbeDocument, '(?s)```powershell\r?\n(# MANUAL:' + $Marker + '\r?\n.*?)\r?\n```')
    if (!$ProbeMatch.Success) { throw "Missing manual block $Marker" }
    return [scriptblock]::Create($ProbeMatch.Groups[1].Value)
}
$ProbeVerifyBlock = Get-ProbeBlock 'VERIFY'
$ProbeInstallBlock = Get-ProbeBlock 'INSTALL'
foreach ($ProbeAtomicBlock in @($ProbeVerifyBlock,$ProbeInstallBlock)) {
    $ProbeStatements = @($ProbeAtomicBlock.Ast.EndBlock.Statements)
    if ($ProbeStatements.Count -ne 1 -or $ProbeStatements[0] -isnot [Management.Automation.Language.PipelineAst]) { throw 'Member block must be one submitted statement, including its success output' }
    $ProbeCommands = @($ProbeStatements[0].PipelineElements)
    if ($ProbeCommands.Count -ne 1 -or $ProbeCommands[0] -isnot [Management.Automation.Language.CommandAst] -or $ProbeCommands[0].InvocationOperator -ne [Management.Automation.Language.TokenKind]::Dot -or $ProbeCommands[0].CommandElements[0] -isnot [Management.Automation.Language.ScriptBlockExpressionAst]) { throw 'Member block must dot-source one complete script block' }
}
$ProbeAnswers = [Collections.Generic.Queue[string]]::new()
$ProbePrompts = [Collections.Generic.List[string]]::new()
function Read-Host {
    param([string]$Prompt)
    $ProbePrompts.Add($Prompt)
    if (!$ProbeAnswers.Count) { throw "Unexpected prompt: $Prompt" }
    return $ProbeAnswers.Dequeue()
}
$ProbeResults = @()
foreach ($ProbeAttempt in $ProbeRequest.verifications) {
    $ProbeAnswers.Clear()
    foreach ($ProbeAnswer in $ProbeAttempt.answers) { $ProbeAnswers.Enqueue([string]$ProbeAnswer) }
    $ProbeOutput = [Collections.Generic.List[string]]::new()
    $ProbeError = $null
    try { . $ProbeVerifyBlock | ForEach-Object { $ProbeOutput.Add([string]$_) } }
    catch { $ProbeError = $_.Exception.Message }
    $ProbeReady = (Test-Path variable:VerifiedDelivery) -and $null -ne $VerifiedDelivery -and $VerifiedDelivery.Verified -eq $true
    $ProbeResults += [pscustomobject]@{error=$ProbeError;output=@($ProbeOutput);verified=$ProbeReady;unread_answers=$ProbeAnswers.Count}
}
if ($ProbeRequest.mutate_archive -and $VerifiedDelivery) {
    [IO.File]::AppendAllText($VerifiedDelivery.ArchivePath, 'changed after verification')
}
if ($ProbeRequest.junction_target) {
    New-Item -ItemType Junction -Path (Join-Path $ProbeRequest.project '.agents') -Target $ProbeRequest.junction_target -ErrorAction Stop | Out-Null
}
$ProbeInstallResults = @()
foreach ($ProbeInstallAttempt in $ProbeRequest.installations) {
    $ProbeAnswers.Clear()
    foreach ($ProbeAnswer in $ProbeInstallAttempt.answers) { $ProbeAnswers.Enqueue([string]$ProbeAnswer) }
    $ProbeOutput = [Collections.Generic.List[string]]::new()
    $ProbeError = $null
    try { . $ProbeInstallBlock | ForEach-Object { $ProbeOutput.Add([string]$_) } }
    catch { $ProbeError = $_.Exception.Message }
    $ProbeInstallResults += [pscustomobject]@{error=$ProbeError;output=@($ProbeOutput);unread_answers=$ProbeAnswers.Count}
}
$ProbeTaskDir = $null
if ($ProbeRequest.task_directory) {
    $ProbeAnswers.Clear(); $ProbeAnswers.Enqueue($ProbeRequest.task_directory)
    $ProbeLine = @($ProbeDocument -split '\r?\n' | Where-Object { $_ -match '^\$TaskDir = ' })
    if ($ProbeLine.Count -ne 1) { throw 'Expected one task path input' }
    . ([scriptblock]::Create($ProbeLine[0]))
    $ProbeTaskDir = $TaskDir
}
$ProbeBackupFlow = $null
if ($ProbeRequest.backup_restore) {
    $ProbeBackupBlock = Get-ProbeBlock 'BACKUP'
    $ProbeOriginalInstall = $InstalledSkill
    . $ProbeBackupBlock | Out-Null
    $ProbeOldBackup = $BackupDir
    if (Test-Path -LiteralPath $ProbeOriginalInstall) { throw 'Backup left the discovery directory installed' }
    $ProbeAnswers.Clear(); $ProbeAnswers.Enqueue($ProjectRoot)
    . $ProbeInstallBlock | Out-Null
    . $ProbeBackupBlock | Out-Null
    Copy-Item -LiteralPath $ProbeOldBackup -Destination $ProbeOriginalInstall -Recurse -ErrorAction Stop
    foreach ($ProbeEntry in $VerifiedDelivery.Manifest.files) {
        if ((Get-FileHash -LiteralPath (Join-Path $ProbeOriginalInstall $ProbeEntry.path)).Hash.ToLowerInvariant() -ne $ProbeEntry.sha256) { throw 'Restored file differs from verified manifest' }
    }
    . $ProbeBackupBlock | Out-Null
    if (Test-Path -LiteralPath $ProbeOriginalInstall) { throw 'Move-out uninstall left installed files' }
    $ProbeBackupFlow = 'same-snapshot backup, reinstall, restore and move-out uninstall passed'
}
[ordered]@{verifications=$ProbeResults;installations=$ProbeInstallResults;prompts=@($ProbePrompts);powershell_blocks=$ProbeBlocks.Count;task_directory=$ProbeTaskDir;backup_restore=$ProbeBackupFlow} | ConvertTo-Json -Depth 8

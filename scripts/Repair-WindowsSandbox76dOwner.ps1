[CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'High')]
param(
    [ValidateSet('Inspect', 'Repair', 'Restore')][string]$Action = 'Inspect',
    [string]$BackupPath
)

# Prepared for explicit user approval. Default Inspect never changes ownership.
# Only this one directory is eligible; no recursive or DACL-edit operation.
$ErrorActionPreference = 'Stop'
$target = 'C:\Users\Administrator\.codex\.sandbox-bin'
$projectRoot = Split-Path -Parent $PSScriptRoot
$evidenceRoot = Join-Path $projectRoot '.eval-runs'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($identity.Name -ne 'TSY-ICECREAM\Administrator') { throw 'Run as the original Windows user.' }
$userSid = $identity.User.Value
$adminsSid = 'S-1-5-32-544'
$privilegeOutput = & "$env:SystemRoot\System32\whoami.exe" '/priv' '/fo' 'csv' '/nh' 2>&1
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect token privileges; no changes made.' }
# Privilege names are invariant; do not parse localized descriptions/status.
$hasTakeOwnershipPrivilege = ($privilegeOutput -join "`n") -match '(?m)^"SeTakeOwnershipPrivilege",'
foreach ($directory in @('C:\Users\Administrator', 'C:\Users\Administrator\.codex', $target)) {
    $item = Get-Item -LiteralPath $directory -Force
    if (!$item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Expected a real directory, not a reparse point: $directory"
    }
}

function Get-OwnerRepairState {
    $acl = Get-Acl -LiteralPath $target
    [ordered]@{
        target = $target
        ownerSid = $acl.GetOwner([Security.Principal.SecurityIdentifier]).Value
        groupSid = $acl.GetGroup([Security.Principal.SecurityIdentifier]).Value
        dacl = $acl.GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]::Access)
        protected = $acl.AreAccessRulesProtected
    }
}

$before = Get-OwnerRepairState
if ($Action -eq 'Inspect') {
    [ordered]@{ action='Inspect'; changed=$false; userSid=$userSid; takeOwnershipPrivilegePresent=$hasTakeOwnershipPrivilege; state=$before } | ConvertTo-Json -Depth 4
    return
}
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (!$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Repair/Restore requires the original user in an administrator terminal; no changes made.'
}
if (!$hasTakeOwnershipPrivilege) {
    throw 'SeTakeOwnershipPrivilege is absent from this administrator token; stop for administrator/policy review. No changes made.'
}
$desiredOwner = $userSid
if ($Action -eq 'Restore') {
    if (!$BackupPath) { throw 'Restore requires the exact backup.json produced by Repair.' }
    $BackupPath = [IO.Path]::GetFullPath($BackupPath)
    $backupParent = Split-Path -Parent $BackupPath
    if ((Split-Path -Parent $backupParent) -ine [IO.Path]::GetFullPath($evidenceRoot) -or
        (Split-Path -Leaf $backupParent) -cnotmatch '^owner-76d-[0-9a-f]{32}$' -or
        (Split-Path -Leaf $BackupPath) -ne 'backup.json') { throw 'Backup outside this repair evidence scope.' }
    foreach ($path in @($evidenceRoot, $backupParent, $BackupPath)) {
        if ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw 'Backup path contains a reparse point.'
        }
    }
    $saved = Get-Content -Raw -LiteralPath $BackupPath | ConvertFrom-Json
    if ($saved.schema -ne 1 -or $saved.userSid -ne $userSid -or
        $saved.before.target -cne $target -or $saved.before.ownerSid -ne $adminsSid -or
        $before.ownerSid -ne $userSid -or $before.dacl -cne $saved.before.dacl -or
        $before.groupSid -ne $saved.before.groupSid -or $before.protected -ne $saved.before.protected) {
        throw 'Backup/state mismatch; stop for review instead of restoring over changed permissions.'
    }
    $desiredOwner = $adminsSid
} elseif ($before.ownerSid -eq $userSid) {
    Write-Output 'Already owned by the original user; no changes made. Ordinary sandbox acceptance is still required.'
    return
} elseif ($before.ownerSid -ne $adminsSid) {
    throw 'Unexpected owner; no changes made.'
}

if (!$PSCmdlet.ShouldProcess($target, "$Action owner SID $($before.ownerSid) -> $desiredOwner; DACL/group/children unchanged")) { return }
if ($Action -eq 'Repair') {
    if ((Test-Path -LiteralPath $evidenceRoot) -and
        ((Get-Item -LiteralPath $evidenceRoot -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'Evidence root is a reparse point.'
    }
    $backupParent = Join-Path $evidenceRoot ('owner-76d-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $backupParent | Out-Null
    $BackupPath = Join-Path $backupParent 'backup.json'
    [ordered]@{schema=1;userSid=$userSid;utc=[DateTime]::UtcNow.ToString('o');before=$before} |
        ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $BackupPath -Encoding utf8
}
Write-Output "Backup: $BackupPath"
# takeown is the OS ownership recovery tool. No /r, /d, grants, or resets.
# Repair assigns the current user; Restore alone uses /a for the original group.
$ownerArguments = @('/f', $target)
if ($Action -eq 'Restore') { $ownerArguments += '/a' }
$ownerOutput = & "$env:SystemRoot\System32\takeown.exe" @ownerArguments 2>&1
$ownerExit = $LASTEXITCODE
$operationId = [guid]::NewGuid().ToString('N')
$privilegeOutput | Set-Content -LiteralPath (Join-Path $backupParent ("privileges-$operationId.log")) -Encoding utf8
$ownerOutput | Set-Content -LiteralPath (Join-Path $backupParent ("operation-$operationId.log")) -Encoding utf8
$after = Get-OwnerRepairState
$verified = $ownerExit -eq 0 -and $after.ownerSid -eq $desiredOwner -and
    $after.dacl -ceq $before.dacl -and $after.groupSid -eq $before.groupSid -and
    $after.protected -eq $before.protected
$result = [ordered]@{action=$Action;method='takeown';takeOwnershipPrivilegePresent=$hasTakeOwnershipPrivilege;exitCode=$ownerExit;verified=$verified;before=$before;after=$after;backup=$BackupPath;sandboxAccepted=$false}
$result | ConvertTo-Json -Depth 4 | Tee-Object -FilePath (Join-Path $backupParent ('result-' + [guid]::NewGuid().ToString('N') + '.json'))
if (!$verified) { throw "Owner operation/verification failed; keep the backup and stop for review. $($ownerOutput -join ' ')" }
Write-Output 'Owner-only operation verified. No sandbox acceptance or CLI integration success is implied.'

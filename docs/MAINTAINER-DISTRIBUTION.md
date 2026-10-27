# 维护者：固定版本打包与交付

普通成员使用[手册第4节](../MANUAL.md#4-成员校验并安装)的正式四附件，不执行本页命令。维护者本地打包只用于已授权的维护、测试或定制交付；团队标准分发优先转发正式Release附件。

## v0.1.4 固定来源

源码／标签为 `cf66420efb683bbfa3206a44669acd31c899f849`，技能内容树为 `8878ac6604d85492729098c257de9b129cce7f11`。当前仓库MANUAL.md属于发布后的写作修订，不改旧标签；以下代码从同一固定发行源码取得原冻结手册，不将工作树新文案冒充v0.1.4原附件。

需要Windows、PowerShell 7和Git；在已取得该标签的源码仓库根目录整块执行。它不提交、推送、发布或改权限，只在仓库内`.eval-workspaces/package-<随机ID>/delivery/`产生交付文件，finally清理中间staging；失败保留现场。

```powershell
# MANUAL:PACKAGE
. {
    $PreviousPackagePreference = $ErrorActionPreference
    $ErrorActionPreference = 'Stop'
    $StageDir = $null
    try {
        $SkillTree = '8878ac6604d85492729098c257de9b129cce7f11'
        $SourceCommit = (git rev-parse 'v0.1.4^{commit}').Trim()
        if ($LASTEXITCODE -ne 0 -or $SourceCommit -notmatch '^[0-9a-f]{40}$') { throw '本地缺少已验证v0.1.4标签；先取得正式标签，不从HEAD推定' }
        $SourceRepo = (git rev-parse --show-toplevel).Trim()
        if ($LASTEXITCODE -ne 0) { throw '请在源码仓库中运行' }
        $SourceTree = (git -C $SourceRepo rev-parse ($SourceCommit + ':.agents/skills/ecommerce-image-designer')).Trim()
        if ($LASTEXITCODE -ne 0 -or $SourceTree -cne $SkillTree) { throw '缺少或不匹配的固定源码对象；停止打包' }
        git -C $SourceRepo cat-file -e ($SkillTree + '^{tree}')
        if ($LASTEXITCODE -ne 0) { throw '本地缺少固定技能内容树；先取得 v0.1.4 源码再打包' }
        $BuildDir = Join-Path $SourceRepo ('.eval-workspaces/package-' + [guid]::NewGuid().ToString('N'))
        $ReleaseDir = Join-Path $BuildDir 'delivery'
        $StageDir = Join-Path $BuildDir 'staging'
        New-Item -ItemType Directory -Path $ReleaseDir,$StageDir -ErrorAction Stop | Out-Null
        $ZipName = 'ecommerce-image-designer-v0.1.4.zip'
        $ZipPath = Join-Path $ReleaseDir $ZipName
        git -C $SourceRepo -c core.autocrlf=false archive --format=zip --prefix=ecommerce-image-designer/ "--output=$ZipPath" $SkillTree
        if ($LASTEXITCODE -ne 0) { throw '固定快照打包失败' }
        Expand-Archive -LiteralPath $ZipPath -DestinationPath $StageDir -ErrorAction Stop
        $PackagedSkill = Join-Path $StageDir 'ecommerce-image-designer'
        $PackageFiles = @(Get-ChildItem -LiteralPath $PackagedSkill -File -Recurse | Sort-Object FullName)
        if ($PackageFiles.Count -ne 11) { throw '此固定快照应恰好包含11个文件' }
        $ManifestFiles = @($PackageFiles | ForEach-Object {
            [ordered]@{
                path = [IO.Path]::GetRelativePath($PackagedSkill, $_.FullName).Replace('\','/')
                sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            }
        })
        $ZipSha = (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
        $Manifest = [ordered]@{
            skill = 'ecommerce-image-designer'; version = 'v0.1.4'
            revision = $SourceCommit; source_commit = $SourceCommit; skill_tree = $SkillTree
            archive = $ZipName; archive_sha256 = $ZipSha; files = $ManifestFiles
        }
        $Manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $ReleaseDir 'release.json') -Encoding utf8
        "$ZipSha  $ZipName" | Set-Content -LiteralPath (Join-Path $ReleaseDir 'SHA256SUMS.txt') -Encoding utf8
        $ManualZip = Join-Path $StageDir 'manual.zip'
        git -C $SourceRepo -c core.autocrlf=false archive --format=zip "--output=$ManualZip" $SourceCommit MANUAL.md
        if ($LASTEXITCODE -ne 0) { throw '无法取得同一固定提交的手册，停止交付' }
        Expand-Archive -LiteralPath $ManualZip -DestinationPath (Join-Path $StageDir 'manual') -ErrorAction Stop
        Copy-Item -LiteralPath (Join-Path $StageDir 'manual/MANUAL.md') -Destination (Join-Path $ReleaseDir 'MANUAL.md') -ErrorAction Stop
        Write-Output $ReleaseDir
    } finally {
        try {
            if ($StageDir -and (Test-Path -LiteralPath $StageDir)) {
                $OwnedStage = [IO.Path]::GetFullPath($StageDir)
                $OwnedBuild = [IO.Path]::GetFullPath($BuildDir)
                if (!$OwnedStage.StartsWith($OwnedBuild + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFileName($OwnedStage) -ne 'staging') { throw '清理范围不符；保留现场' }
                Remove-Item -LiteralPath $OwnedStage -Recurse -Force -ErrorAction Stop
            }
        } finally { $ErrorActionPreference = $PreviousPackagePreference }
    }
}
```

## 核验、交付与清理

对运行树归档使用命令级 `-c core.autocrlf=false`，不修改Git全局配置；核对11文件逐字节匹配Git对象，手册取自同一源码。tree对象重新归档的ZIP可因时间戳而有不同摘要，内容一致不代表压缩字节相同；本地产物必须使用本次生成的release.json和摘要，不能混入正式Release附件或沿用正式ZIP摘要。

正式分发还需同源清单／摘要、变更与限制说明、准确PR和合入／同步CI、真实附件安装／失败路径验收；沿用分支→PR→必需CI和评审→合入复验→受控发布。新手册须经相同流程发布新版本，不覆盖既有Release。跨宿主／收费与视觉范围按[验证说明](VALIDATION.md)分别验收，不用打包成功代替。

只用无客户数据的独立目录验证带双引号／中文空格路径、缺附件／坏摘要／漂移、已有目录拒绝覆盖、备份／完整包恢复及合成用户文件保留。归档必要脱敏证据并验证归档，再清理本次创建的package目录；绝不清空整个.eval-workspaces或其他用户目录。仓库开发检查入口为`./scripts/check.ps1`，锁定依赖与命令见[验证说明](VALIDATION.md)。

历史正式来源和七附件摘要见[v0.1.4回执](RELEASE-v0.1.4.md)；后续版本应重新固定来源、运行树、文件清单和完整包摘要，不能只改版本文案。

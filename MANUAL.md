# 电商图片设计 Skill：团队分发与使用手册

适用对象：团队维护者、电商策划／设计使用者、MCP 服务管理员。本文命令面向 **Windows、PowerShell 7**，核对日期为 2026-10-26。

**角色先分清：普通成员从第4节下载同版正式附件并校验安装，不需要克隆仓库、安装开发工具或自行打包。开发者／维护者才执行第3、10节的源码与发行操作；MCP管理员负责第5节的服务连接。** 本手册针对v0.1.4完整目录包（复数 `references/`）。只有正式Release附件才作为成员安装来源；发行前的本地／草稿文件不表示已发布。旧v0.1.0–v0.1.3及附件保留，不原地覆盖。

本手册随v0.1.4候选冻结；正式发布状态以[Release页面](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/tag/v0.1.4)为准。普通成员只在正式发布后下载本版四附件，从第4节开始；发布后的准确提交、CI及附件摘要另记入交付说明，冻结附件不覆盖更新。

团队当前可以分发**固定提交的完整 Skill 目录**，让成员安装到业务项目的 `.agents/skills/ecommerce-image-designer/`。只策划时不必部署图像服务；实际出图前，由管理员准备指定 MCP，使用者确认具体方案和本次收费范围。

**普通成员从第 4 节开始：下载正式 Release → 校验 → 安装 → 在宿主中加载。不要执行第 3 节的维护者打包命令。** 只有负责制作／发布技能包的人才需要第 3、10 节；配置图像服务的人看第 5 节。成员不需要克隆源码或自行打包。

本手册对应 v0.1.4 的目录规范升级；业务流程沿用v0.1.3：Skill 独立完成策划、文案、排版与提示词，用户确认后调用指定 MCP 的核心生成／批量工具。旧 Release 保留历史版本；已安装旧包需按升级步骤取得本版完整技能包，不能只替换手册。详见[核心接口适配复验](docs/CORE-IMAGE-ADAPTER-64a.md)。

## 1. 版本与能力边界

| 项目 | 本手册采用的实际值 |
|---|---|
| 源码仓库 | [ecommercial-images-designer-skill](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill) |
| 固定技能内容树 | `8878ac6604d85492729098c257de9b129cce7f11`；同版 `release.json.skill_tree` 与此相同 |
| 完整发行源码提交 | `8c41b69629e1af47b3429bdc41f6a2884a328453`；正式tag和同版release.json.source_commit／revision均对应此提交，不以当前main/dev代替 |
| 技能名称 | `ecommerce-image-designer`；界面显示名“电商图片设计” |
| 源码中的技能根 | `.agents/skills/ecommerce-image-designer/` |
| 分发类型 | 单技能目录；MIT 许可证；不是现成的安装器或插件 |
| 版本标签／Release | [v0.1.4](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/tag/v0.1.4)，完整发行源码 SHA 见同版 `release.json` 的 `source_commit`；技能内容以独立的固定内容树核对。历史 [v0.1.0 发布回执](docs/RELEASE-v0.1.0.md)保留 |
| 指定出图服务 | `zhenzhen-gptimagegen2.5-mcp`、`zhenzhen-nanobanana-mcp`，按任务选择其中一个 |

本版 `release.json` 分别记录完整发行源码提交和技能内容树；成员手册、变更说明独立随包交付，运行 ZIP 仅含下列11文件。本仓库手册会继续更新，既有标签和附件不随之改写；新版本应重新固定源码／运行快照及清单，不能让成员日常自动跟随 `main` 或 `dev`。

能力包括选题、卖点分析、文案排版、提示词、确认后提交 MCP、取得图片和按反馈回退。主图、详情页、SKU 图及用户明确要求的电商文生图素材适用；无电商用途的通用插画、视频和店铺运营不适用。来源文章里的宠物烘干箱参数只属于案例，不能迁入其他商品。

### 已验证与仍需验收的范围

| 环境／层次 | 当前证据及限制 |
|---|---|
| Codex Desktop，本机 Windows 项目级技能 | 历史真实会话已发现、读取技能并调用免费 MCP；未取得可靠 Desktop 应用版本号。当前Desktop会话没有重新执行完整主集；独立CLI复验不能替代Desktop。 |
| Codex CLI，Windows | 历史 `0.153.0`、Desktop 配套 `0.163.0-alpha.11` 及独立修补的 `0.163.0` 有分阶段记录。历史v0.1.3独立候选在其十一文件包复验12次，轨迹12/12、原稿8/12、正向待审候选9/9；不改判原稿，不要求成员安装该修补CLI。 |
| DeepSeek Harness Desktop `0.2.1-rc.2`，desktop profile | 两个既有codeproxy模型在历史v0.1.3完成8项真实场景：原稿6/8，原自动流程7/8；独立图号分配修复后，同一冻结答卷确定性重放六份正向候选6/6、两个反例不编译。原稿和原流程成绩不改判；日常Host没有自动编译Hook。详见[本轮记录](docs/HOST-RELEASE-aju.md)。 |
| 本地与 Windows CI | 本次目录迁移运行本地与Windows CI确定性回归、结构／42场景格式检查；准确数量见同版VALIDATION。历史v0.1.3为161项Python、15项Node；正式发行的PR、main合入和dev同步准确提交CI见同版RELEASE-NOTES／VALIDATION。这些离线检查不替代模型、真实Host或供应商出图。 |
| 业务出图 | 当前 Skill 的真实商品、完整批准后执行、保存和用户视觉接受仍需业务验收；不能因免费查询或候选编译通过就宣称通过。 |

记录入口：[交付回执](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/blob/0be00e0b8837e9f06633ce5b7504f14bfa711992/docs/DELIVERY.md)、[Codex 历史免费复验](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/blob/0be00e0b8837e9f06633ce5b7504f14bfa711992/docs/SYSTEM-SKILLS-76d7-HOST.md)、[DSH 自动编排复验](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/blob/0be00e0b8837e9f06633ce5b7504f14bfa711992/docs/DSH-ORCHESTRATION-76d81.md)。其他操作系统、Claude Code、DSH 用户级目录、云端路径和团队共享远程 MCP 部署没有在本项目验证，不作为本手册支持分支。

## 2. 分工与交付内容

| 角色 | 负责事项 |
|---|---|
| 开发者／维护者 | 在dev改源码、技能和回归；通过PR／CI与评审后固定提交并制作发行包，核对清单摘要、手册及限制。普通成员无需承担这些工作。 |
| 普通成员／使用者 | 从第 4 节下载正式包、校验和安装；不执行维护者打包命令。确认宿主发现正确来源，再提供商品和图片事实、审阅方案、批准范围及验收产物。 |
| MCP 管理员 | 按服务自身交付说明配置程序或服务、凭据、网络、费用与文件访问；提供本宿主连接说明和免费查询结果。 |

**运行包只包含以下 11 个文件**，不要只发 `SKILL.md`：

```text
ecommerce-image-designer/
├── SKILL.md
├── LICENSE
├── agents/openai.yaml
├── references/
│   ├── design-record.md
│   ├── mcp-adapters.md
│   ├── planning-and-prompts.md
│   ├── review-and-revision.md
│   ├── source-methods.md
│   └── state-contract.md
└── scripts/
    ├── validate_design_state.py
    └── compile_design_state.py
```

`references/` 是必要资料；`agents/openai.yaml` 目前只有界面元数据，没有自动安装 MCP 的依赖声明。两个 Python 脚本只用于可选的本地状态校验／编译，需 Python 3.10+ 标准库，无第三方包。

普通成员使用指令和审阅方案不需要安装 Git、uv、Node、Beads 或 Rust。开发者从 Git 打包／检查时需要 Git；开发检查另需 Python 3.12+、uv 和 Node 22+，详见[验证说明](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/blob/0be00e0b8837e9f06633ce5b7504f14bfa711992/docs/VALIDATION.md)。`tests/`、`evals/`、宿主测试编排器和 `patches/` 不属于普通成员的运行包；不要分发 `.beads`、缓存、凭据、客户图片或原始会话。

## 3. 维护者：按固定提交制作分发包

**本节仅供维护者。普通成员请跳到第 4 节。** 本地打包用于维护、测试或明确的定制交付；向团队分发时优先原样转发正式 Release 的附件，保持同一版本与摘要。不要把本地 ZIP 与正式 Release 的 `release.json`／摘要混放。

在已经取得上述仓库、并具有所需访问权的**源码根目录**执行以下 PowerShell。获取仓库时可使用其 HTTPS 地址；若需登录，使用既有 Git 凭据机制，不把令牌写入 URL。

一次执行下面完整代码块。它只读固定 Git 对象，在仓库内独立的 `.eval-workspaces/package-<随机ID>/` 写交付文件，不提交、不推送、不发布或修改安装权限。中间 staging 在 finally 清理；保留最终打印的 delivery 供审阅与交付。失败时不继续交付，保留本次目录以诊断；归档必要证据和转存交付文件后只清理本次创建的目录。

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

使用 `git archive` 而非当前工作树，避免把未提交改动、配置和临时证据装进去。对子树对象归档时，仓库根目录的 `.gitattributes` 不在归档范围内；命令级 `-c core.autocrlf=false` 防止本机自动换行设置改变文件字节，不修改 Git 配置。不要省略该选项，也不要用编辑器重新保存包内文件后仍沿用旧摘要。正式发布另将包内全部文件与目标 Git 对象逐字节核对。

把 ZIP 的 SHA256、完整提交 SHA 和已知限制随版本通知通过团队可信渠道提供。清单校验用于发现内容变化，不能单独证明发送者可信。当前没有现成的插件发行清单或市场安装包；官方推荐的可安装插件分发属于后续工程，不是把本 ZIP 改扩展名即可实现。[官方分发说明](https://learn.chatgpt.com/docs/build-skills#distribute-skills-with-plugins)

## 4. 成员：校验并安装

### 4.1 下载正式 Release，准备交付目录

1. 用浏览器打开 [v0.1.4 正式 Release](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/tag/v0.1.4)，在页面下方展开 **Assets**。仓库为公开仓库，普通成员无需 Git 或克隆源码。
2. 新建一个专门接收本版附件的文件夹。下面以 `D:\Downloads\电商图片设计-v0.1.4` 为例；成员可选择自己电脑上实际存在的其他盘符和位置。
3. 将以下四个文件下载到该文件夹，不要先解压 ZIP：

| 必需文件 | 下载入口／作用 |
|---|---|
| `ecommerce-image-designer-v0.1.4.zip` | [技能运行包](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/download/v0.1.4/ecommerce-image-designer-v0.1.4.zip)，包含完整十一文件 |
| `release.json` | [版本与文件清单](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/download/v0.1.4/release.json) |
| `SHA256SUMS.txt` | [附件摘要清单](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/download/v0.1.4/SHA256SUMS.txt) |
| `MANUAL.md` | [本版随包手册](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/download/v0.1.4/MANUAL.md) |

另外建议下载同一 Assets 中的 `CHANGELOG.md`、`RELEASE-NOTES.md`、`VALIDATION.json`，了解变更、限制和验证证据。**不要选择 `Source code (zip)` 或 `Source code (tar.gz)`；它们是源码归档，不是本流程使用的技能运行包。** 维护者也可把同一 Release 的附件原样放到团队共享盘，成员整套领取。

下载的 `MANUAL.md` 是 v0.1.4 冻结的手册。请按其中第4.2、4.3节完整代码块执行；不要切回 v0.1.0 随包旧手册的逐行流程。

正确的“交付目录”是**直接装着这些文件的文件夹**：

```text
D:\Downloads\电商图片设计-v0.1.4\
├── ecommerce-image-designer-v0.1.4.zip
├── release.json
├── SHA256SUMS.txt
└── MANUAL.md
```

它是下载附件的位置；后续安装时会另外选择业务项目。空文件夹、ZIP 解压后的 `ecommerce-image-designer` 文件夹都不能作为交付目录。若维护者提供的是本地打包结果，应选择其 `delivery` 子目录，旁边的 `staging` 不用于成员验证。

在资源管理器打开这个文件夹，按 **Ctrl+L** 选中地址栏，按 **Ctrl+C** 复制完整路径。粘贴到提示中可以带英文双引号，例如 `"D:\Downloads\电商图片设计-v0.1.4"`；下面的命令会自动去掉双引号和首尾空白，保留路径内部空格。

### 4.2 填写摘要并一次完成验证

打开普通权限 **PowerShell 7**。不要复制示例中的 `PS C:\...>` 或 `>>` 提示符。下面整个代码块要从 `. {` 到最后的 `}` 一次复制执行；出现 `>>` 代表 PowerShell 还在等待代码块结束，不是让你跳过报错继续执行。

两个输入分别是：

| 提示 | 应输入的内容 |
|---|---|
| 交付目录 | 上一节四文件所在目录的完整路径；不是 ZIP 文件路径，也不是准备安装技能的业务项目目录 |
| ZIP SHA256 | 这一份 ZIP 在可信 Release 通知或维护者通知中的64位摘要；只填摘要，不带文件名、`sha256:`、引号或 Git 提交号 |

**从上面 v0.1.4 正式入口下载的 ZIP，填写下列值：**

```text
a7392ec6fb3f2f4cfccaa532f3ea57b1e28aba51710b85b49e8179b7dcc2d576
```

维护者自行重新打包的 ZIP 即使运行文件相同，归档摘要也可能不同，必须用维护者对**那份本地包**给出的摘要。不能混用两份包的 ZIP、清单和摘要，也不要自行计算一个值再当作可信发布通知。无需输入任何 API 密钥。

下面会先检查目录和必需文件，再询问摘要；仅在 ZIP、清单及十一文件全部通过后打印成功。验证直接读取 ZIP，不创建临时解压目录，不覆盖技能。**任一步失败都会终止本块并清空旧验证结果；不要单独执行最后的成功提示。** 修正问题后重新执行完整验证块。

v0.1.4 更新了技能运行内容，ZIP 名称和摘要均已变化。ZIP、`release.json` 和手册必须从 v0.1.4 一起下载；不要沿用 v0.1.0–v0.1.3 的 ZIP 或摘要。旧标签和附件保留历史版本，不覆盖更新。

```powershell
# MANUAL:VERIFY
. {
    $PreviousErrorActionPreference = $ErrorActionPreference
    $VerifiedDelivery = $null
    $Release = $null
    $PayloadRoot = $null
    $ErrorActionPreference = 'Stop'
    try {
        $DeliveryInput = (Read-Host '输入交付目录的完整路径（可带双引号）').Replace('"', '').Trim()
        if (![IO.Path]::IsPathFullyQualified($DeliveryInput) -or !(Test-Path -LiteralPath $DeliveryInput -PathType Container)) { throw '交付目录不存在；请复制四个附件所在文件夹的完整路径' }
        $DeliveryDir = (Get-Item -LiteralPath $DeliveryInput).FullName
        foreach ($RequiredFile in @('release.json','SHA256SUMS.txt','MANUAL.md')) {
            if (!(Test-Path -LiteralPath (Join-Path $DeliveryDir $RequiredFile) -PathType Leaf)) { throw "交付目录缺少 $RequiredFile；请下载同一Release的四个必需文件，勿选择空目录或解压目录" }
        }
        $Release = Get-Content -Raw -LiteralPath (Join-Path $DeliveryDir 'release.json') | ConvertFrom-Json
        if ($Release.skill -ne 'ecommerce-image-designer' -or $Release.version -ne 'v0.1.4' -or $Release.skill_tree -ne '8878ac6604d85492729098c257de9b129cce7f11') { throw '技能名称或固定版本不符' }
        if ($Release.source_commit -notmatch '^[0-9a-f]{40}$' -or $Release.revision -cne $Release.source_commit) { throw '清单的完整源码提交非法或不一致' }
        if ([string]::IsNullOrWhiteSpace($Release.archive) -or $Release.archive -match '[/\\:]' -or [IO.Path]::GetFileName($Release.archive) -cne $Release.archive) { throw '清单中的压缩包名称非法' }
        $ReceivedZip = Join-Path $DeliveryDir $Release.archive
        if (!(Test-Path -LiteralPath $ReceivedZip -PathType Leaf)) { throw "缺少技能ZIP：$($Release.archive)；请下载后再验证，不要先解压" }
        $ExpectedZipSha = (Read-Host '输入这份ZIP的通知摘要（仅64位SHA256）').Trim().ToLowerInvariant()
        if ($ExpectedZipSha -notmatch '^[0-9a-f]{64}$') { throw 'SHA256应为64位十六进制，不带文件名、引号或sha256前缀' }
        $ActualZipSha = (Get-FileHash -LiteralPath $ReceivedZip -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($ActualZipSha -ne $ExpectedZipSha -or $ActualZipSha -ne $Release.archive_sha256) { throw '压缩包摘要不符，停止安装；检查是否混用了本地包和正式Release' }
        if (@($Release.files).Count -ne 11) { throw '文件清单应恰好有11项' }
        $FilePaths = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        foreach ($Entry in $Release.files) {
            if ([string]::IsNullOrWhiteSpace($Entry.path) -or $Entry.path -match '(^/|\\|:|(^|/)\.\.?(/|$))' -or $Entry.path.EndsWith('/') -or $Entry.sha256 -notmatch '^[0-9a-f]{64}$') { throw '清单路径或文件摘要非法' }
            if (!$FilePaths.Add($Entry.path)) { throw '清单包含重复路径' }
        }
        $Zip = [IO.Compression.ZipFile]::OpenRead($ReceivedZip)
        try {
            $Seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
            $ZipFiles = @($Zip.Entries | Where-Object { !$_.FullName.EndsWith('/') })
            if ($ZipFiles.Count -ne 11) { throw 'ZIP文件数量不符；可能下载了Source code或混入额外文件' }
            foreach ($ZipEntry in $Zip.Entries) {
                if (!$Seen.Add($ZipEntry.FullName) -or !$ZipEntry.FullName.StartsWith('ecommerce-image-designer/', [StringComparison]::Ordinal) -or $ZipEntry.FullName -match '(\\|:|(^|/)\.\.?(/|$))' -or (($ZipEntry.ExternalAttributes -shr 16) -band 0xF000) -eq 0xA000) { throw 'ZIP目录结构、重复路径或链接非法' }
            }
            foreach ($Entry in $Release.files) {
                $ZipEntry = $Zip.GetEntry('ecommerce-image-designer/' + $Entry.path)
                if ($null -eq $ZipEntry) { throw "ZIP缺少文件：$($Entry.path)" }
                $Stream = $ZipEntry.Open()
                $Hasher = [Security.Cryptography.SHA256]::Create()
                try { $FileSha = [BitConverter]::ToString($Hasher.ComputeHash($Stream)).Replace('-', '').ToLowerInvariant() }
                finally { $Stream.Dispose(); $Hasher.Dispose() }
                if ($FileSha -ne $Entry.sha256) { throw "文件摘要不符：$($Entry.path)" }
            }
        } finally { $Zip.Dispose() }
        $VerifiedDelivery = [pscustomobject]@{ Verified=$true; ArchivePath=$ReceivedZip; ArchiveSha256=$ActualZipSha; Manifest=$Release }
        Write-Output '交付内容校验通过；可以继续安装，尚未证明宿主发现或业务出图成功。'
    } catch {
        $VerifiedDelivery = $null
        $Release = $null
        throw
    } finally { $ErrorActionPreference = $PreviousErrorActionPreference }
}
```

只有完整代码块正常结束并打印上述成功提示，才继续下一步。报错后旧的验证结果已失效，重新运行本块；重新打开窗口也必须重新验证。不要复制单独的 `Write-Output` 行当作验证。

### 4.3 推荐：安装到业务项目

在**验证成功的同一个 PowerShell 窗口**，一次执行下面完整代码块。输入实际开展策划工作的既有项目目录，例如 `D:\工作项目\收纳盒主图`，可带双引号；它与交付目录是两个位置。命令只创建该项目下的 `.agents/skills/ecommerce-image-designer/`，不会把整个开发仓库、AGENTS.md、Beads 或沙箱修复脚本复制过去。

```powershell
# MANUAL:INSTALL
. {
    $PreviousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Stop'
    try {
        if (!(Test-Path variable:VerifiedDelivery) -or $null -eq $VerifiedDelivery -or $VerifiedDelivery.Verified -ne $true) { throw '尚未完成本轮验证；请先重新执行整个MANUAL:VERIFY块' }
        if ((Get-FileHash -LiteralPath $VerifiedDelivery.ArchivePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $VerifiedDelivery.ArchiveSha256) { $VerifiedDelivery = $null; throw 'ZIP在验证后被更改；请重新验证' }
        $ProjectInput = (Read-Host '输入业务项目目录的完整路径（可带双引号）').Replace('"', '').Trim()
        if (![IO.Path]::IsPathFullyQualified($ProjectInput) -or !(Test-Path -LiteralPath $ProjectInput -PathType Container)) { throw '业务项目目录不存在；请先建好实际工作目录' }
        $ProjectRoot = (Get-Item -LiteralPath $ProjectInput).FullName
        $SkillsParent = Join-Path $ProjectRoot '.agents/skills'
        $InstalledSkill = Join-Path $SkillsParent 'ecommerce-image-designer'
        if (Test-Path -LiteralPath $InstalledSkill) { throw '存在同名技能；先按升级章节比较并备份，不覆盖' }
        foreach ($ParentDir in @($ProjectRoot,(Join-Path $ProjectRoot '.agents'),$SkillsParent)) {
            if ((Test-Path -LiteralPath $ParentDir) -and ((Get-Item -LiteralPath $ParentDir).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw '安装父目录为链接／联接，交维护者核对，不写入' }
        }
        $Zip = [IO.Compression.ZipFile]::OpenRead($VerifiedDelivery.ArchivePath)
        try {
            New-Item -ItemType Directory -Path $SkillsParent -Force -ErrorAction Stop | Out-Null
            New-Item -ItemType Directory -Path $InstalledSkill -ErrorAction Stop | Out-Null
            foreach ($Entry in $VerifiedDelivery.Manifest.files) {
                $Target = [IO.Path]::GetFullPath((Join-Path $InstalledSkill $Entry.path))
                if (!$Target.StartsWith($InstalledSkill + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw '安装路径越界' }
                New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($Target)) -Force -ErrorAction Stop | Out-Null
                $InputStream = $Zip.GetEntry('ecommerce-image-designer/' + $Entry.path).Open()
                try {
                    $OutputStream = [IO.File]::Open($Target, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
                    try { $InputStream.CopyTo($OutputStream) } finally { $OutputStream.Dispose() }
                } finally { $InputStream.Dispose() }
            }
        } finally { $Zip.Dispose() }
        foreach ($Entry in $VerifiedDelivery.Manifest.files) {
            if ((Get-FileHash -LiteralPath (Join-Path $InstalledSkill $Entry.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Entry.sha256) { throw "安装后摘要不符：$($Entry.path)" }
        }
        Write-Output "已安装：$InstalledSkill"
    } finally { $ErrorActionPreference = $PreviousErrorActionPreference }
}
```

命令从已验证 ZIP 直接写入新安装目录，不遗留临时解压副本。若安装中途因权限／磁盘等问题失败，可能留下本次的部分安装目录；不要继续加载或强行覆盖，保留错误和路径交维护者处理。保留收到的 `release.json`、摘要通知和安装路径，用于后续比较。若业务项目纳入 Git，可由维护者按该项目流程提交这一个技能目录。

### 4.4 在宿主中加载

**Codex CLI／Desktop：** CLI 从该项目目录启动；Desktop 在该项目目录创建或打开任务。在技能列表中选择 `ecommerce-image-designer`，核对来源为刚安装的 `SKILL.md`，然后发第 6 节的请求。没有更新时先新建会话，再按宿主方式刷新或重启。两种界面都必须核对实际来源，不能以复制成功代替发现。

官方规定项目级为 `.agents/skills`，Codex 用户级为用户主目录的 `.agents/skills`；同名技能不会自动合并。跨项目个人安装可采用用户级目录，但本项目实际主集验证的是项目级；不要同时安装两份再猜测优先级。此手册不修改 `~/.codex/skills/.system`。[官方位置与刷新规则](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)

**DeepSeek Harness Desktop 0.2.1-rc.2：** 选择 `desktop` profile，在该业务目录建立会话，要求“使用 ecommerce-image-designer 技能”。验证原生技能列表返回的入口和实际读取来源。模型可选管理员已配置的 `codeproxy-anthropic/claude-sonnet-5-5` 或 `codeproxy-openai/gpt-6.1-sol`；本次模型路由证据不独立认证网关背后的模型身份。不要据 Codex 目录规则推断 DSH 的用户级位置，也不要用 npm/headless 测试代替 Desktop 验收。无需为普通使用开启 Inspector；那是维护者测试编排的既有诊断通道。

### 4.5 发现位置与作用域核对

下表据本仓库新版规范整理，记录路径语义，**不是本轮重新运行各宿主的证明**。本文可执行安装仍只部署项目级 `.agents/skills/ecommerce-image-designer/`；选择其他位置需另验收，不改 Host 配置来强行发现。

| 宿主 | 父目录与发现范围 | 本项目证据边界 |
|---|---|---|
| Codex CLI／Desktop | 从会话 cwd 到仓库根各层 `.agents/skills/`；用户级为实际运行用户的 `~/.agents/skills/`。不向下发现所有兄弟项目。 | 项目级有历史记录；新版迁移目录与当前版本的完整行为复验待做。 |
| DSH 本地文件系统提供方 | 最近 `.git` 决定 projectRoot，否则为 cwd；项目 `.dsh/skills/` 与 `.agents/skills/`，用户默认 `~/.dsh/skills/`、`~/.agents/skills/`，受实际根配置和提供方开关影响。 | 只有 Desktop 0.2.1-rc.2、desktop profile 的项目级历史证据；用户级／自定义目录未实测。 |
| Claude Code | `.claude/skills/`；不会因目录名 `.agents/skills/` 自动获得相同发现行为。 | 本项目尚未实测，不提供可用性承诺或默认部署命令。 |

DSH 需已有 `@deepseek-ai/dsh-skill` 和 `@deepseek-ai/dsh-skill-filesystem`；`includeDefaultRoots: false` 可禁用默认根，`customSkillDirs`、DSH_HOME、DSH_AGENTS_HOME 及显式配置可改变实际位置，profile 名不是目录。先查宿主诊断中的有效根、入口路径、scope 与同名来源；注册表 rank 不等于跨宿主通用覆盖顺序，不通过删除其他技能消除冲突。DSH 的监视刷新和 Codex 的新会话／刷新分别核对；不能以一个 Host 的热加载推断全部可用。Windows、WSL、SSH、云端各有独立文件系统与运行用户，不能直接复用客户端盘符。

## 5. MCP 准备与费用

Skill 本身没有 API Key、`.env` 或服务端点字段，不需要在聊天里填密钥。两个 MCP 的程序、模型、凭据和网络配置由服务管理员按**各服务自己的安装说明**准备，本仓库不分发它们的后端安装包或通用配置模板。

管理员应交付：经过核对的服务版本与启动方式／地址、所选宿主的连接步骤、凭据的安全配置渠道、费用规则和图片／产物可访问位置。凭据字段名、读取优先级及重载方法属于对应服务，不能从本 Skill 猜测；不复制作者的 `config.toml`、DSH profile 或 `.env` 给成员。可由管理员预配置成员机器，使用者无需重复部署后端。当前真实验证为本机服务连接，未验证共享 HTTP 部署。

| 服务 | 免费核对入口 | 执行路径与门禁 |
|---|---|---|
| `zhenzhen-gptimagegen2.5-mcp` | `get_model_guide`：实际目录、配置存在状态 | `submit_image_generation`、`submit_image_edit`；当前有批量入口时用 `submit_image_batch`／`run_image_batch` 并按原批次身份查询，不假定旧宿主已暴露这些工具 |
| `zhenzhen-nanobanana-mcp` | `list_models`；`inspect_design_images` 查看可访问图片 | 由Skill确认后直连 `submit_image_tasks`／`generate_images`，不依赖扩展工具 |

宿主可能把 GPT 服务命名为 `zhenzhen-gptimagegen2-5-mcp`，也可能将工具名转换为命名空间形式；先看当前工具 schema，不照抄某个宿主的完整前缀。目录／配置查询成功不证明上游生成、速度或质量已验证。免费验收不需要实际出图；模型推理及服务部署可能有各自费用，本文的“免费”指不调用收费图像生成。

只做文字策划时可先不连接服务；缺少图片查看能力时要明确未观图，不能补写视觉结论。出图时核对所选服务确实支持输入、尺寸和产物获取。远端 Server 通常读不到成员本机附件路径，需先确认允许的传递方式，不静默传到第三方图床。详细限制见[本快照 MCP 适配说明](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/blob/v0.1.4/.agents/skills/ecommerce-image-designer/references/mcp-adapters.md)；离线副本为安装目录中的 `references/mcp-adapters.md`。Nano/GPT 均由 Skill 先完成策划和逐图确认，再调用核心生成／批量工具，扩展资源或模板不是前提。收费授权、图片映射和失败恢复仍按档案核对。

## 6. 第一次免费验收与日常调用

先完成以下验收；没有通过就停在方案阶段，记录宿主版本、模型、技能来源、失败阶段与非秘密日志。

| 验收 | 输入与预期 |
|---|---|
| A1 发现 | 技能列表有该名称，路径指向选定项目的安装目录。 |
| A2 显式使用 | 采用下例，实际读取技能；无图时列缺口，仍能讨论，不生成。 |
| A3 图片映射 | 用允许分享的测试图片，说明产品／参考角色、来源性质和参考范围。实际看图后映射正确，不从参考推断本商品参数。 |
| A4 反例 | 请求“三天 Python 学习计划，每天半小时”，不应调用电商 Skill 或图像服务。 |
| A5 恢复 | 用已有完整设计档案，冻结 M01、只改 M02，未知旧值保持未知，不重新询问 M01 是否冻结。 |
| A6 免费服务 | 实际查询两个指定服务，区分配置存在与上游未测试；不提交任何图像生成。 |

### 显式调用：从策划开始

Codex CLI 可使用 `$ecommerce-image-designer`；其他界面可在选择器选中技能，或明确写“使用 ecommerce-image-designer 技能”。在实际宿主观察选用结果，不假定相同符号适用于所有产品。

```text
使用 ecommerce-image-designer 技能。
先为我的收纳盒策划一张电商主图，只讨论，不出图。
我会提供产品图片和已核实资料；先列影响下一步的缺口。
只允许免费能力查询和看图，不生成、不编辑、不确认或提交任何图片任务。
```

若要检查服务，再追加：“实际免费查询两个指定 MCP 的模型和配置状态；上游生成和性能未测就保持未验证。”自然语言触发示例是“根据我的产品图和参考图，先帮我设计一张电商主图的文案与排版”；隐式触发必须另看实际选用，不能仅凭显式成功推定。

### 提供图片与事实

```text
P01 是我提供的商品实拍；R01 是竞品参考，仅借鉴字体与配色，禁止借用构图或产品参数。
请实际查看两图并分别记录业务角色、来源性质、参考用途。
已核实事实只有：灰色盒体、深灰盖沿；材质、容量、性能未知，不写相关承诺。
用途：电商主图；画布先给设计建议。先给文案、布局和完整提示词草案，不出图。
```

示例中的身份只是示范，必须替换为本次图片真实情况。产品图也可能是合成示意，不能因为角色为 product 就称为实拍；参考图未说明是否竞品时保持未知。参考用途可为风格、画面结构或两者；画面结构不等于商品实体结构。

首次为产品生成必须有用户提供的图片；只有竞品图时不能声称准确还原自己的产品。用户明确只要文生图背景／装饰素材是无图例外，例如“只生成电商背景，不包含商品，先给方案”。缺资料可推进不依赖它的讨论，不将普通“概念图”自动当作无图许可。

### 从方案到执行

| 阶段 | 成员应看到并检查的产物 |
|---|---|
| S0 | 需求、商品事实和来源、图片身份／用途、缺口。 |
| S1 | 选题方向与卖点依据，推论和已证实事实分开。 |
| S2 | 逐图准确文案、构图、字体、配色、商品位置和参考借鉴范围。 |
| S3 | 当前版本完整提示词、输入图映射、图号、数量、尺寸、所选 MCP／模型、费用及本次批准范围。 |
| S4 | 确认后提交的原任务 ID／幂等身份，状态和实际图片文件。 |
| S5 | 对照实图检查商品、文字与布局，用户接受、部分接受或反馈。 |

未确认单图策划、免费状态和单图局部恢复目前输出 **v2 JSON**；`state` 是依据，`proposal` 是建议，`next` 是下一步，缺值为 null／unknown。它是待审提示词草案，不是 MCP 请求或出图授权。只读会话可由用户另存记录；不要把 `validation=pending` 当成已校验。套图按逐图方案流程，不用单图契约批准整套。

确认时应指明刚展示的版本和图号，并覆盖费用范围，例如“按刚展示的 v2 生成 M02，使用已列出的模型、输入和参数；同意本次已说明的费用范围，其他图保持不变”。这只是确认表达示例，不是当前对任何商品的授权。看完实际方案和费用再发送；服务／模型、输入或预算范围变化时重新展示差异。

v0.1.4 中，用户确认和费用授权由 Skill 逐图保存，Nano／GPT 直接调用核心任务接口；只确认 M01 就只执行 M01。批量提交按已批准范围拆批，不需要将其余待定图置为 approved，也不依赖服务端确认、复刻编译或评审工具。

### 按反馈回退与恢复

```text
读取我提供的 design-record.json 恢复方案。
M01 已接受，保持不变；M02 的标题区太挤，只调整 M02 的局部文案布局。
商品事实和原文字不变。旧档案没记的尺寸、字体、文案保持未知，不猜旧值。
给具体新布局与完整提示词草案，说明回退阶段、差异和待确认范围，不出图。
```

产品身份／事实错误回 S0，选题卖点问题回 S1，文案排版回 S2，提示词或工具映射回 S3。生成结果未知、下载失败先按原 ID 查询／取图，不等于重新设计；不能超时后自动再次收费提交或换服务重画。每次只改受影响图，保存旧版本、确认原话、输入顺序、任务 ID 和产物位置；用户接受了哪些图也要逐项记录。

文件化档案可存于调用方业务目录的 `outputs/ecommerce-design/<design_id>/`，创建前告知位置，不写入技能目录。区分技能根与图片／档案工作目录，跨成员接力时一并交接允许共享的原图、来源、版本和任务身份；不要把客户资料提交到本 Skill 的源码仓库。

## 7. 可选：由维护者校验和编译状态

**复制 Skill 不会自动部署业务校验门禁。** 日常会话可交付 pending 状态；自动后处理已在本仓库测试协调器中验证，但尚未为团队日常会话安装全局钩子。若团队要求强制自动校验，应由维护者另行集成并验收，不能依靠自然语言指令提供权限隔离。

在已安装 Python 3.10+、已有 `state.json` 和独立 `evidence.json` 的业务任务目录中，可以运行以下命令。`$InstalledSkill` 取第 4 节安装路径，`$TaskDir` 改成实际任务目录；执行前确认 `python --version`。此处不自动安装依赖。

```powershell
$TaskDir = (Get-Item -LiteralPath ((Read-Host '输入已有状态和证据文件的任务目录（可带双引号）').Replace('"', '').Trim())).FullName
python --version
python -X utf8 -B (Join-Path $InstalledSkill 'scripts/validate_design_state.py') (Join-Path $TaskDir 'state.json') --evidence (Join-Path $TaskDir 'evidence.json') --render
if ($LASTEXITCODE -ne 0) { throw '原稿校验失败；保留错误，不提交绘图' }
```

证据由维护者／编排方从用户原话、实际档案与真实工具返回独立整理，形状见随包 `references/state-contract.md`；普通成员无需填写技术证据表。开发者对新单图策划应在可信证据中独立分配 `target_images`（例如 `["M01"]`），不得使用输入图P01/R01或从模型state复制；编译器将其绑定到待审候选，不把它作为生成授权。不能复制模型 state 充当证据。校验退出0仅代表结构与绑定通过，退出1保留失败，不证明审美、事实来源本身或用户已批准。

原稿失败但能构造合法新候选时，维护者可单独运行编译器；它只读本地输入，不调用模型或 MCP，拒绝覆盖已有输出：

```powershell
$CandidateDir = Join-Path $TaskDir ('candidate-' + [guid]::NewGuid().ToString('N'))
python -X utf8 -B (Join-Path $InstalledSkill 'scripts/compile_design_state.py') (Join-Path $TaskDir 'state.json') --evidence (Join-Path $TaskDir 'evidence.json') --output $CandidateDir
if ($LASTEXITCODE -ne 0) { throw '候选编译失败；保留原稿及错误，不提交绘图' }
```

产物为 `state.json`、`changes.json`、`view.md`；原稿评分不改判，候选仍是未确认版本，必须展示差异并回 S3。编译不猜坐标、不授予收费权限，也不用于处理已指定执行入口或用户要求的上传映射。

## 8. 升级、回滚与卸载

升级前先比较安装目录与原 `release.json` 的全部摘要。发现本地改动时停下交维护者比较，不直接覆盖。维护者通过新版本通知提供明确 SHA、完整新包、新清单及匹配的新版本手册；按新手册重新执行“校验收到的文件”，不要删掉旧手册的固定版本检查来强行接收新包。

以下是**项目级普通目录安装**的备份／卸载步骤，沿用第 4 节变量；不适用于链接安装。它把技能移到发现目录之外，保留业务图片、设计档案、MCP 和凭据：

```powershell
# MANUAL:BACKUP
$ExpectedInstall = [IO.Path]::GetFullPath((Join-Path $ProjectRoot '.agents/skills/ecommerce-image-designer'))
$CurrentInstall = (Get-Item -LiteralPath $InstalledSkill -ErrorAction Stop).FullName
if ($CurrentInstall -ine $ExpectedInstall) { throw '不是本次项目安装目录，停止移动' }
foreach ($CheckedDir in @((Join-Path $ProjectRoot '.agents'),(Split-Path $ExpectedInstall -Parent),$ExpectedInstall)) {
    if ((Get-Item -LiteralPath $CheckedDir).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw '发现链接／联接，交维护者检查，不移动' }
}
$BackupRoot = [IO.Path]::GetFullPath((Join-Path $ProjectRoot '.skill-backups'))
if ((Test-Path -LiteralPath $BackupRoot) -and ((Get-Item -LiteralPath $BackupRoot).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw '备份根为链接，停止' }
$BackupDir = [IO.Path]::GetFullPath((Join-Path $BackupRoot ('ecommerce-image-designer-' + [guid]::NewGuid().ToString('N'))))
if (!$BackupDir.StartsWith($BackupRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $BackupDir)) { throw '备份目标不符' }
New-Item -ItemType Directory -Path $BackupRoot -Force -ErrorAction Stop | Out-Null
Move-Item -LiteralPath $ExpectedInstall -Destination $BackupDir -ErrorAction Stop
Write-Output "备份已保留：$BackupDir"
```

- **升级：** 新包完整验证成功、获得新的 `$VerifiedDelivery` 后再执行安装块，目标必须为空。完成免费验收，旧备份保留。
- **回滚：** 先把不接受的新版本按同样方式移到另一新备份目录，再从已核对的旧备份复制到空的安装位置，按旧清单校验，刷新宿主并复验。不要仅退 `SKILL.md` 而保留新资源；旧版能否读取新版状态需单独核对，不改写旧业务档案来假装兼容。
- **卸载：** 移出发现目录后刷新／新开会话，确认该来源已不在技能列表；若仍出现，检查其他作用域的同名副本。不要只在 `.agents/skills` 内把文件夹改名，它仍可能被扫描。备份可按团队保留制度后续处理，本手册不递归删除用户数据。

## 9. 排障与反馈

| 现象 | 下一步 |
|---|---|
| `release.json` 找不到 | 交付目录应直接包含四个附件；不要选空目录、解压目录或业务项目。回到第4.1节重新下载并复制地址栏路径。 |
| 报错后又看到“校验通过” | 检查是否在使用旧手册逐行执行或单独打印成功文字；它不能证明通过。用本页完整验证块重跑，失败会清空结果，安装块会拒绝继续。 |
| ZIP 摘要不符 | 区分正式包与维护者本地包；核对通知摘要与文件来源，不混放清单，不删除摘要检查来继续安装。 |
| 路径提示带双引号 | 本页所有目录输入会自动移除英文双引号并修剪首尾空白；内部空格保留。输入的是实际目录，不带`PS C:\...>`等提示符。 |
| 文件已复制但列表没有 | 确认路径不是多嵌套一层 `ecommerce-image-designer/ecommerce-image-designer`；核对任务工作目录、来源、同名副本并刷新／重启。 |
| 只读取正文，配套资料失败 | 确认完整11文件、资源按技能根解析。档案按业务工作目录解析；不要扩展成搜索用户目录或放宽工具权限。 |
| 模型把未知旧值写成事实 | 保存原答卷，核对档案，再交独立校验／新候选；不要把修改后的答案覆盖原始失败。 |
| 看到 JSON、pending，而非自动展示 | 这是当前三个未确认分支的交付契约；可按第7节外部校验／渲染。复制技能不等于自动安装 UI 或编排钩子。 |
| MCP 不在工具列表或配置缺失 | 找服务管理员核对当前宿主绑定、服务版本与安全凭据渠道；不把 config 或密钥发到聊天。 |
| 附件无法被服务读取 | 区分宿主路径与 Server 文件系统，确认可访问输入及用户允许的传递方式。 |
| overload／模型请求失败 | 保留失败、模型路由和时间，不将无答卷判通过；不要为了通过验收不断重新抽样。 |
| 提交后超时、UNKNOWN 或下载失败 | 保存原任务／幂等身份，先查询／下载恢复；不自动重新收费提交。 |
| Windows 报执行策略、`.sandbox-bin` 或系统技能缓存错误 | 交维护者按[账户与DACL报告](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/blob/0be00e0b8837e9f06633ce5b7504f14bfa711992/docs/WINDOWS-SANDBOX-ACCOUNT-DACL-REPORT.md)和[缓存报告](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/blob/0be00e0b8837e9f06633ce5b7504f14bfa711992/docs/SYSTEM-SKILLS-76d7.md)定位。历史脚本针对作者机器，不能照搬账号、SID、所有者命令或批量授权给全体成员；不关闭沙箱、不绕过执行策略。 |
| CLI 升级后 NVM4306 | 交安装维护者核对升级来源与信任记录，不绕过信任门禁或替换现有配置。 |

向维护者反馈：固定提交、宿主与版本、项目级／用户级位置、实际选用模型、失败阶段、预期与实际、脱敏错误，以及是否已有任务 ID／部分产物。移除密钥、认证头和未经允许的客户数据。区分文件校验、发现、模型行为、免费 MCP、收费任务、保存和视觉验收分别是否成功，避免只报告“安装成功”。

## 10. 维护者的发布验收

在另一个普通目录或测试账号中，从实际交付包执行第4节，核对摘要、发现来源及第6节验收，记录宿主版本／模型和失败。项目中已有 CI 或作者机器成功不能替代成员首次验收。升级／回滚／卸载先用无客户数据的合成输入验证，再迁移业务；不修改成员现有安装、策略或凭据来强行通过。

如需维护源码，使用[共用检查入口](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/blob/0be00e0b8837e9f06633ce5b7504f14bfa711992/scripts/check.ps1)及[验证手册](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/blob/0be00e0b8837e9f06633ce5b7504f14bfa711992/docs/VALIDATION.md)，沿用分支→PR→必需CI／评审→合并后复验的流程；不把源码提交当成已发布安装包。发布通知应附固定 SHA、11文件清单、ZIP摘要、手册、变更与限制；需要市场插件或统一自动编排时另做适配和验证。

本手册安装流程只操作成员选定的业务目录，不部署后端、改Host配置或触发收费出图。本版只调整目录与运行引用，不新增模型或真实Host复验；历史v0.1.3真实Host免费复验与本次目录／发行验证分别记录在同版VALIDATION／RELEASE-NOTES；不能由安装命令成功推断成员业务验收通过。

初版手册编写时已在隔离临时目录实际验证固定快照打包、11文件摘要、中文／空格路径安装、重复安装拒绝、错误ZIP／文件摘要拒绝，以及限定目录备份、同快照重装／恢复和移出式卸载；合成用户文件保留。所有PowerShell代码块另作语法检查。这不等于真实成员宿主发现、跨版本数据迁移或业务出图验收。

历史v0.1.1成员流程修复新增15项Windows PowerShell工作流回归：真实执行本手册代码块，检查缺清单、坏JSON、缺ZIP、摘要错误、坏ZIP、ZIP结构错误、旧验证结果失效、未验证／ZIP变更后安装拒绝、同名目录和联接保护、双引号清洗及同快照备份恢复。语法树另核对验证／安装各自只有一个完整提交语句；本地共124 Python、15 Node及结构／场景格式检查通过。重新下载正式v0.1.0包验证带引号中文空格目录、十一文件安装摘要与合成用户数据保留，所有本轮临时环境已移除。没有新增模型、图像MCP或收费出图调用，没有改变已有安装配置或已发布附件；旧Release手册保持历史版本，不能据本地检查声称已更新远端CI或发行物。

## 11. 从旧版升级与团队维护

v0.1.4 将v0.1.3的单数 `reference/` 迁移为复数 `references/`，入口直接索引六份资料和两个可选脚本，仍共11文件，无新必需依赖。不能只改文件夹名、只替换SKILL.md或手册：入口、参考资料、脚本和清单必须取同一新版本完整包，不能混用旧ZIP／摘要。

旧用户先按第8节记录来源、备份完整旧包及本地定制，再用本版四附件完整校验并安装到空目标，核对宿主实际选用来源和第6节免费验收；失败保留备份，整包回滚。用户商品图、设计档案、已生成图片、Host／MCP配置和其他技能均保留。旧版读取新版状态是否兼容另行核查，不能靠源码回滚假装数据可逆。

团队共享来源是本仓库的已验证Release，不跟随dev/main自动更新。成员提出改进时提供版本、脱敏样例、预期与实际证据；开发者在dev修改正文／资源／脚本和回归，经PR、必需CI、维护者评审、合入复验后受控发布。个人实验不覆盖正式安装，通用改进回流共享库。技能文本和检查器不提供独立沙箱，也不替代用户方案与费用确认。

# 电商图片设计 Skill：安装与使用手册

本手册按“取得正式附件 → 校验 → 安装 → 确认宿主来源 → 使用 → 升级或卸载”组织。**普通成员从第4节开始，不需要克隆仓库、自己打包或部署 MCP Server。** 前三节用于查版本、分工和目录含义；维护者另看第10节。

本页是 **2026-10-27 仓库修订稿**，适用于已发布的 v0.1.4 技能包；本次改写不替换正式 Release 中已冻结的 `MANUAL.md`，不改变运行包或业务流程。交付目录仍使用正式版的四个附件，不能把本页另存后冒充原发行附件。

## 1. 谁需要做什么

| 角色 | 操作范围 |
|---|---|
| 普通成员 | 第4节下载、校验并安装；第5节确认宿主来源；第6节提供商品资料、审阅方案和验收图片。 |
| 技能维护者 | 提供可信版本与摘要、处理本地定制和异常安装、按第10节维护源码及交付。 |
| MCP 管理员 | 配置两个指定出图服务及宿主连接、凭据和网络；普通成员不用在聊天中提供密钥。 |

Skill 适用于电商主图、详情页、SKU 图和明确只用文生图生成的电商素材。可只做选题、卖点、文案、排版或提示词；通用插画、视频和店铺运营不属于本技能范围。

## 2. 本手册对应的版本

| 项目 | 本项目的实际值 |
|---|---|
| 仓库 | [ecommercial-images-designer-skill](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill) |
| 正式版本 | [v0.1.4 Release](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/tag/v0.1.4) |
| 完整发行源码提交 | `cf66420efb683bbfa3206a44669acd31c899f849` |
| 固定技能内容树 | `8878ac6604d85492729098c257de9b129cce7f11` |
| 技能名称 | `ecommerce-image-designer`，界面显示“电商图片设计” |
| 本文安装示例 | Windows 原生环境、PowerShell 7、业务项目级目录安装；无需管理员终端 |

v0.1.4 将 v0.1.3 的 `reference/` 改为 `references/`，业务流程不变，仍需**完整包升级**。其他版本使用各自匹配的包、清单和手册，不删版本检查来强行安装。准确来源、附件摘要和 CI 见[发布回执](docs/RELEASE-v0.1.4.md)。

## 3. 先分清三个目录

| 名称 | 例子 | 用来做什么 |
|---|---|---|
| 交付目录 | `D:\Downloads\电商图片设计-v0.1.4` | 接收四个正式附件；不是解压后的技能目录。 |
| 业务项目目录 | `D:\工作项目\收纳盒主图` | 你实际做商品策划的已有工作目录，也是本例宿主会话的工作目录。 |
| 安装后的技能根 | `D:\工作项目\收纳盒主图\.agents\skills\ecommerce-image-designer` | 存放 `SKILL.md` 和全部运行资源；不要把商品图或业务档案放进去。 |

盘符和文件夹名只是例子，应选择自己电脑上存在的目录。复制路径时允许英文双引号，例如 `"D:\工作项目\收纳盒主图"`；命令会去掉双引号及首尾空白，保留中间空格。

本手册默认安装到业务项目，**路径输入不能留空，也不会默认写入用户目录**。不要选开发本 Skill 的源码仓库来代替成员业务目录；用户级、Claude Desktop 上传、WSL、容器和远端环境不属于本文已验收的安装分支。

## 4. 成员校验并安装

### 4.1 下载同一版本的四个附件

打开 [v0.1.4 Release](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/tag/v0.1.4)，展开页面下方 **Assets**，下载下表四个文件，放到同一个独立文件夹。仓库公开，无需克隆；不要选择自动生成的 **Source code**，先不要解压 ZIP。

| 必需附件 | 用途与正式下载入口 |
|---|---|
| `ecommerce-image-designer-v0.1.4.zip` | [完整技能包](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/download/v0.1.4/ecommerce-image-designer-v0.1.4.zip)，11个运行文件。 |
| `release.json` | [版本和逐文件清单](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/download/v0.1.4/release.json)。 |
| `SHA256SUMS.txt` | [附件摘要清单](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/download/v0.1.4/SHA256SUMS.txt)。 |
| `MANUAL.md` | [v0.1.4 冻结随包手册](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/download/v0.1.4/MANUAL.md)。 |

你的交付目录应直接包含这些文件：

```text
D:\Downloads\电商图片设计-v0.1.4\
├── ecommerce-image-designer-v0.1.4.zip
├── release.json
├── SHA256SUMS.txt
└── MANUAL.md
```

在资源管理器进入这个文件夹，按 **Ctrl+L → Ctrl+C** 复制地址栏路径。验证提示“交付目录”时粘贴它，不要粘贴 ZIP 文件路径或技能安装路径。

### 4.2 校验收到的文件

打开 **PowerShell 7**，整块执行下方代码。它会问两次：第一次输入交付目录，第二次输入这份 ZIP 的64位 SHA256；缺附件时会先报错，不再询问摘要。

本版正式 ZIP 的期望摘要是：

```text
a7392ec6fb3f2f4cfccaa532f3ea57b1e28aba51710b85b49e8179b7dcc2d576
```

只复制这一行，不带引号、文件名或 `sha256:` 前缀。期望摘要来自可信发行记录或维护者通知；不要把未知 ZIP 自己算出的值当作期望值。

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

只有完整代码块正常结束并出现“交付内容校验通过”，才执行安装。任何报错都停止；不要继续逐行执行余下代码或单独复制成功提示。失败会清空旧验证结果；新开 PowerShell 窗口也必须重做本节。该块检查版本／清单、ZIP 摘要及11个文件内容，不代表 Host 或图像服务已经可用。

### 4.3 安装到业务项目

留在**刚才校验成功的同一个 PowerShell 窗口**，整块执行下方代码。提示时输入已有的业务项目目录，例如 `"D:\工作项目\收纳盒主图"`。

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

出现 `已安装：<路径>` 后，保留交付目录、安装路径和摘要通知。目标存在时命令拒绝覆盖，按第8节处理；中途失败可能留下部分安装，先保留路径与错误交维护者检查，不继续加载或强行重装。

安装结果应只有一层技能目录：

```text
<业务项目>/.agents/skills/ecommerce-image-designer/
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

不要只复制 `SKILL.md`，也不要套成 `ecommerce-image-designer/ecommerce-image-designer/SKILL.md`。

## 5. 确认宿主来源与出图能力

### 5.1 在实际业务目录打开会话

关闭正在使用旧技能的会话。Codex CLI 从业务目录启动；Codex Desktop 在该业务目录打开任务。选择 `ecommerce-image-designer`，核对宿主返回的入口是刚安装的 `<业务项目>/.agents/skills/ecommerce-image-designer/SKILL.md`；必要时按客户端方式刷新或重启。

DSH Desktop 的历史验收使用 `0.2.1-rc.2` 的 `desktop` profile。使用同一业务项目对应的会话，要求“使用 ecommerce-image-designer 技能”，核对技能列表和实际资源读取路径。DSH 若找到上层 `.git`，项目根取最近的 Git 根，不能假定任意子目录 `.agents/skills` 都可见；有自定义技能根／提供方配置时交管理员核对，不为安装擅改 profile。

复制文件只证明文件到达。可以发送下列**免费发现检查**：

```text
请使用 ecommerce-image-designer 技能。
先报告宿主实际返回的技能名称和入口路径，再读取该入口及其必要资源。
本次只检查发现和资源读取，不策划商品、不生成图片、不提交收费任务。
若没有发现或不能读取，请明确报告，不凭名称推定已加载。
```

成功应有实际发现及读取证据，入口与预期相同。出现同名来源时先确认路径和版本，不删除其他技能；不要把模型一句“已加载”或文件校验通过当作宿主验收。

### 5.2 只策划与需要出图的准备不同

只做文字策划，无需图像服务或密钥；缺少观图能力时应明确“未观图”，不补写视觉结论。实际生图／编辑须连接下列服务之一，并能查看输入及输出图片：

| 指定 MCP Server | 负责的能力 |
|---|---|
| `zhenzhen-gptimagegen2.5-mcp` | 所选模型支持的生成／编辑、批量任务、状态查询和产物获取。 |
| `zhenzhen-nanobanana-mcp` | 所选模型支持的生成／编辑、批量任务、状态查询和产物获取。 |

由管理员按服务自己的手册配置连接、凭据、网络和文件访问。Skill 本身不自带生图服务，不强制每次同时连接或调用两端；两个指定服务均不可用时保留文字方案并报告缺口，不自动换其他生成工具。

工具名称及参数以宿主当前实际 schema 为准。Skill 完成策划、文案、排版和完整提示词，经用户确认后直交核心生成／批量接口，**不依赖服务端策划、复刻编译、resources 或 prompt 模板**。免费能力查询只证明查询返回，不证明供应商生成、保存或质量。详见[发行版 MCP 适配说明](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/blob/v0.1.4/.agents/skills/ecommerce-image-designer/references/mcp-adapters.md)。

远端 MCP 可能读不到成员电脑路径；先确认允许的传图方式，不静默上传到第三方图床，不在聊天、截图或共享配置中放真实密钥。

## 6. 开始使用

### 6.1 准备当前商品的事实和图片

首次生成需要用户提供图片，唯一无图例外是**明确只用文生图生成素材**。只做文字研讨可以先推进，缺图会在真正提交前阻断；“直接出图”本身不免除输入要求。修改需要可读底图。

把自己的真实产品图与竞品／其他参考图分开，参考图注明“只参考风格”“只参考结构”或“两者”。不清楚的来源写待核实，不能用画面观感推断实拍／合成来源，也不能把参考商品或课程案例中的参数当作本商品事实。

### 6.2 先提出方案，不自动出图

```text
$ecommerce-image-designer
请为我的商品策划主图／详情页／SKU图（填写实际需要）。
商品／型号：填写真实值，未知写待核实。
当前商品事实：填写参数及各项来源，未核实项请不要用于广告承诺。
图片P01：我的真实产品图，附件或宿主可读路径。
图片R01：竞品参考图，仅参考风格／结构／两者（选一种）；没有则写未提供。
销售渠道、目标人群、尺寸、张数、输出位置：填写要求，未确定写待讨论。
本次先核对事实、图片角色、卖点、文案、排版和逐图提示词。
请保留设计档案，等我确认具体版本、图号和费用后再提交生图。
```

按当前分支，草案可能按状态契约交付 JSON；保留其中事实证据、建议与待确认项。格式不合格先纠正，不能把草稿 JSON 直接作为 MCP 参数或批准依据。需要维护者渲染或校验时看第10节。

只需要电商背景时可以明确说：“只用文生图制作商品图的背景素材，不生成具体产品。” 无电商用途的通用插画应改用适用能力，不启动本流程。

### 6.3 确认执行与验收

先审阅商品事实、图片输入映射、文案、布局、逐图完整提示词、服务／模型、尺寸和本次费用范围。明确确认后才提交；例如“确认当前方案v2的M01，按已展示的输入与参数执行，同意本次费用，M02继续待定”。若前述信息尚未展示，这句话不补足缺失方案。只确认M01不会自动放行整套图。

生成后检查实际图片及保存位置，而不只看 `SUCCESS`：产品外观与事实、文字、比例、排版、参考用途是否符合方案。表达反馈时指出图号与具体问题，例如：“M01文案保留，副标题拥挤，请回到排版调整；M02已接受，不改。” Skill 据原因返回事实／卖点、文案、排版、提示词或生成阶段，保留未受影响的内容，修改后重新确认受影响范围。

提交后超时或结果未知，应沿原任务ID／幂等身份查询、取图或恢复；不盲目重提、不换服务重发。设计档案保留事实来源、图片角色、逐图文案布局、提示词、确认范围、任务身份与产物；档案、商品图及结果放业务目录，不写入技能安装目录或源码仓库。

## 7. 检查已经安装的文件

关闭 PowerShell 后，之前的变量不会保留。已安装v0.1.4的成员需要复查或卸载时，先用v0.1.4交付重新执行第4.2节，再在同一窗口整块执行下方检查。**旧版安装先使用旧版本匹配的手册、清单和摘要，按其步骤校验和备份**；本页第4.2节固定为v0.1.4，不能用于接收旧包，也不能用新清单判断旧目录是否完整。

```powershell
# MANUAL:CHECK
. {
    $PreviousCheckPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Stop'
    try {
        if (!(Test-Path variable:VerifiedDelivery) -or $null -eq $VerifiedDelivery -or $VerifiedDelivery.Verified -ne $true) { throw '尚未完成本轮验证；先重新执行整个MANUAL:VERIFY块' }
        $CheckInput = (Read-Host '输入已安装技能的业务项目目录（可带双引号）').Replace('"', '').Trim()
        if (![IO.Path]::IsPathFullyQualified($CheckInput) -or !(Test-Path -LiteralPath $CheckInput -PathType Container)) { throw '业务项目目录不存在或不是绝对路径' }
        $ProjectRoot = (Get-Item -LiteralPath $CheckInput).FullName
        $InstalledSkill = Join-Path $ProjectRoot '.agents/skills/ecommerce-image-designer'
        foreach ($CheckDir in @($ProjectRoot,(Join-Path $ProjectRoot '.agents'),(Split-Path $InstalledSkill -Parent),$InstalledSkill)) {
            if ((Get-Item -LiteralPath $CheckDir -ErrorAction Stop).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw '检查路径含链接／联接；交维护者核对' }
        }
        $InstalledItems = @(Get-ChildItem -LiteralPath $InstalledSkill -Recurse -Force -ErrorAction Stop)
        if (@($InstalledItems | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { throw '安装内容含链接／联接，停止检查' }
        $InstalledFiles = @($InstalledItems | Where-Object { !$_.PSIsContainer })
        if ($InstalledFiles.Count -ne 11) { throw '安装文件数量不符，存在缺失或额外文件；保留差异' }
        foreach ($Entry in $VerifiedDelivery.Manifest.files) {
            $CheckFile = [IO.Path]::GetFullPath((Join-Path $InstalledSkill $Entry.path))
            if (!$CheckFile.StartsWith($InstalledSkill + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw '检查路径越界' }
            if ((Get-FileHash -LiteralPath $CheckFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Entry.sha256) { throw "安装后摘要不符：$($Entry.path)" }
        }
        Write-Output "文件检查通过：$InstalledSkill；尚未证明宿主已发现或业务出图成功。"
    } finally { $ErrorActionPreference = $PreviousCheckPreference }
}
```

本块只读安装文件，检查路径、文件数量与11项摘要，拒绝链接和额外文件；不会安装或覆盖。成功提示仅表示安装内容与清单一致，仍需第5节宿主来源检查。失败时保留差异，不继续升级或移动不明目录。

## 8. 升级、回滚与卸载

### 8.1 备份旧完整包

先关闭使用该技能的会话，记录版本、完整提交、安装路径、宿主版本及本地定制。当前已安装v0.1.4时按第7节检查；若从v0.1.3或更早版本升级，先按**旧版手册**使用匹配清单校验并备份，再按新手册安装v0.1.4，不将旧清单塞进本页固定版本的验证块。存在漂移时保留现场交维护者比较；没有可信旧清单时，不强行删除。

以下备份代码用于**已按本页第7节检查通过的v0.1.4项目级安装**，仍在同一 PowerShell 窗口整块执行。它将本技能移到业务项目的 `.skill-backups/`，退出宿主扫描目录；这一步也就是可恢复的移出式卸载。旧版继续使用旧手册的备份步骤。不要把“移出”当作“复制一份后原安装仍可用”。

```powershell
# MANUAL:BACKUP
. {
    $PreviousBackupPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Stop'
    try {
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
    } finally { $ErrorActionPreference = $PreviousBackupPreference }
}
```

记录打印的完整备份路径；保持备份不被宿主发现。不移动商品图片、设计档案、其他技能、凭据或 Host／MCP 配置。

### 8.2 升级完整新包

取得新版本四个匹配附件和可信摘要，放入新的交付目录。按**新版本手册**重新校验，再安装到空的原位置，核对宿主来源并做免费调用检查。旧备份保留，业务档案另行核对兼容性。

从 v0.1.3 升到 v0.1.4 也必须完整升级：**不能只替换手册、SKILL.md 或只把文件夹重命名**；不要混用新旧 ZIP、清单、资源和摘要，也不要日常自动跟随 main/dev。

### 8.3 回滚与卸载

回滚先检查并移出不接受的新安装，再将完整、已核对的旧备份恢复到空的原安装位置，按旧清单检查并在宿主复验。不能仅退回 `SKILL.md`；恢复旧代码不保证旧版能读取新版业务档案。

卸载采用第8.1节的移出方式，重新打开宿主，确认**这个来源**不再可见。其他同名来源可能仍存在，应逐一核对，不清空整个 `.agents/skills`；保留备份、交付 ZIP、商品资料和配置。链接安装或其他客户端内上传的副本需按相应产品方式单独处理，本手册不提供批量删除命令。

## 9. 常见问题与反馈

| 现象 | 应怎样处理 |
|---|---|
| 提示缺 `release.json` | 选择的不是四附件所在交付目录，或附件未下载齐；不要选空目录／解压目录。 |
| 摘要不符、坏JSON或坏ZIP | 停止；核对版本和可信摘要。损坏文件先移走留查，再从同一正式Release下载；不改期望值迁就文件。 |
| 验证失败后继续安装 | 安装会拒绝旧／空验证状态；重新执行完整验证块，不单独运行成功提示。 |
| 安装目标已存在／检查发现额外文件 | 先比较本地定制并备份，保留差异；不强制覆盖或递归清空。 |
| 读写、执行策略或权限拒绝 | 保留错误交管理员按实际策略处理；不添加绕过执行策略参数，不批量放宽权限。 |
| 文件通过但宿主没有发现 | 核对业务目录、项目根、运行用户、实际来源及刷新方式；文件检查与宿主发现分开判断。 |
| MCP连接失败／`stream read error` | 记录宿主、模型、错误阶段和已有任务ID，交管理员定位；不能仅凭该错误归因于Skill，也不重发未知收费请求。 |
| 图片有问题／结果未知 | 前者按图号提出具体反馈并重新确认；后者先查原任务，不盲目重提。 |

反馈提供版本、完整提交、实际安装路径、宿主／平台、脱敏请求、预期与实际结果。不要在公开issue上传原始客户图片、完整会话或密钥。项目问题进入[仓库](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill)的既有issue／PR流程。

## 10. 维护者入口与验收边界

维护者的固定版本打包步骤移至[维护者分发说明](docs/MAINTAINER-DISTRIBUTION.md)，普通成员不执行。该说明按Git固定源码取11文件和同源手册；本地重打包ZIP可能因时间戳不同而有新摘要，不能与正式附件混放。开发与正式使用隔离，变更须经分支、PR、必需CI与评审、合入复验后再受控发布；本次仓库文案修订不是新Release。

可选状态脚本需 **Python 3.10+ 标准库**；只阅读指令和审阅方案的成员无需 Git、uv、Node、Beads或Python。以下仅供已有真实 `state.json` 及独立 `evidence.json` 的维护者，在同一窗口使用第7节得到的 `$InstalledSkill`，不自动安装依赖。

```powershell
$TaskDir = (Get-Item -LiteralPath ((Read-Host '输入已有状态和证据文件的任务目录（可带双引号）').Replace('"', '').Trim())).FullName
python --version
python -X utf8 -B (Join-Path $InstalledSkill 'scripts/validate_design_state.py') (Join-Path $TaskDir 'state.json') --evidence (Join-Path $TaskDir 'evidence.json') --render
if ($LASTEXITCODE -ne 0) { throw '原稿校验失败；保留错误，不提交绘图' }
```

证据从用户原话、实际档案和工具返回独立整理，不能复制模型state冒充证据。新图的 `target_images` 由可信编排方分配，不能拿输入图P01／R01当新图号。退出0只代表结构和证据绑定通过，退出1保留失败，退出2为参数解析错误；不证明事实、审美或收费授权。详细契约在安装目录 `references/state-contract.md`。

需要构造新待审候选时：

```powershell
$CandidateDir = Join-Path $TaskDir ('candidate-' + [guid]::NewGuid().ToString('N'))
python -X utf8 -B (Join-Path $InstalledSkill 'scripts/compile_design_state.py') (Join-Path $TaskDir 'state.json') --evidence (Join-Path $TaskDir 'evidence.json') --output $CandidateDir
if ($LASTEXITCODE -ne 0) { throw '候选编译失败；保留原稿及错误，不提交绘图' }
```

产物为 `state.json`、`changes.json`、`view.md`；原稿和原评分保留，候选仍待用户确认。脚本只读本地输入，不调用模型或MCP，不覆盖已存在输出；外部编排默认30秒，超时先查部分产物，不能扩大权限来重跑。

**验收范围：** v0.1.4 已有 Windows 确定性回归、发行摘要及合成目录安装证据；真实Codex／DSH模型记录属于v0.1.3的冻结包，本版未新增Host模型批次。文件一致、宿主发现、模型输出、供应商生成／保存和用户视觉验收分别记录；后者不能由安装成功推断。真实成员环境、新包原生Host复验、用户级／Claude／其他OS／远端MCP、跨版本业务状态迁移和PI-AI流错误恢复尚未在本项目验收，日常Host也没有自动部署状态编译钩子。详见[验证说明](docs/VALIDATION.md)和[发行回执](docs/RELEASE-v0.1.4.md)。

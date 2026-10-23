# 电商图片设计 Skill：团队分发与使用手册

适用对象：团队维护者、电商策划／设计使用者、MCP 服务管理员。本文命令面向 **Windows、PowerShell 7**，核对日期为 2026-10-23。

团队当前可以分发**固定提交的完整 Skill 目录**，让成员安装到业务项目的 `.agents/skills/ecommerce-image-designer/`。只策划时不必部署图像服务；实际出图前，由管理员准备指定 MCP，使用者确认具体方案和本次收费范围。

## 1. 版本与能力边界

| 项目 | 本手册采用的实际值 |
|---|---|
| 源码仓库 | [ecommercial-images-designer-skill](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill) |
| 固定技能快照 | [`0be00e0b8837e9f06633ce5b7504f14bfa711992`](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/tree/0be00e0b8837e9f06633ce5b7504f14bfa711992) |
| 技能名称 | `ecommerce-image-designer`；界面显示名“电商图片设计” |
| 源码中的技能根 | `.agents/skills/ecommerce-image-designer/` |
| 分发类型 | 单技能目录；MIT 许可证；不是现成的安装器或插件 |
| 版本标签／Release | 本次核查没有标签；使用完整提交 SHA 标识版本，不能把开发检查项目的 `0.1.0` 当作 Skill 发布版本 |
| 指定出图服务 | `zhenzhen-gptimagegen2.5-mcp`、`zhenzhen-nanobanana-mcp`，按任务选择其中一个 |

本手册是该快照之后新增的使用文档，**不在上述历史提交中**；维护者按下文单独附入交付目录。将来发布包含手册的新提交时，应同步更新固定 SHA 和分发清单，不能让成员日常自动跟随 `main` 或 `dev`。

能力包括选题、卖点分析、文案排版、提示词、确认后提交 MCP、取得图片和按反馈回退。主图、详情页、SKU 图及用户明确要求的电商文生图素材适用；无电商用途的通用插画、视频和店铺运营不适用。来源文章里的宠物烘干箱参数只属于案例，不能迁入其他商品。

### 已验证与仍需验收的范围

| 环境／层次 | 当前证据及限制 |
|---|---|
| Codex Desktop，本机 Windows 项目级技能 | 历史真实会话已发现、读取技能并调用免费 MCP；未取得可靠 Desktop 应用版本号。最新十一文件包没有重新执行完整 Codex 主集。 |
| Codex CLI，Windows | 历史 `0.153.0`、Desktop 配套 `0.163.0-alpha.11` 及独立修补的 `0.163.0` 有分阶段记录。后者曾完成 12 次免费主集，但当时为旧八文件技能包，不能代替当前包验收。没有要求成员安装独立修补 CLI。 |
| DeepSeek Harness Desktop `0.2.1-rc.2`，desktop profile | 已实测项目级原生发现和两个 codeproxy 路由：`codeproxy-anthropic/claude-sonnet-5-5`、`codeproxy-openai/gpt-6.1-sol`。最新八项尝试七项正常；原稿 5/7、五份正向编译候选 5/5，两个反例不编译。Sol 显式状态因 overload 未评测，用户已接受该例外。 |
| Windows CI | 已通过 109 项 Python、15 项 Node 及结构／42 场景格式检查。这些离线检查不调用模型、真实 MCP 或收费出图。 |
| 业务出图 | 当前 Skill 的真实商品、完整批准后执行、保存和用户视觉接受仍需业务验收；不能因免费查询或候选编译通过就宣称通过。 |

记录入口：[交付回执](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/blob/0be00e0b8837e9f06633ce5b7504f14bfa711992/docs/DELIVERY.md)、[Codex 历史免费复验](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/blob/0be00e0b8837e9f06633ce5b7504f14bfa711992/docs/SYSTEM-SKILLS-76d7-HOST.md)、[DSH 自动编排复验](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/blob/0be00e0b8837e9f06633ce5b7504f14bfa711992/docs/DSH-ORCHESTRATION-76d81.md)。其他操作系统、Claude Code、DSH 用户级目录、云端路径和团队共享远程 MCP 部署没有在本项目验证，不作为本手册支持分支。

## 2. 分工与交付内容

| 角色 | 负责事项 |
|---|---|
| 维护者 | 选择固定提交，打包、核对清单和摘要；提供手册、版本说明及已知限制；管理升级。 |
| 使用者 | 安装完整目录，确认宿主发现正确来源；提供商品和图片事实，审阅方案、批准范围，验收产物。 |
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

普通成员使用指令和审阅方案不需要安装 Git、uv、Node、Beads 或 Rust。维护者从 Git 打包时需要 Git；开发检查另需 Python 3.12+、uv 和 Node 22+，详见[验证说明](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/blob/0be00e0b8837e9f06633ce5b7504f14bfa711992/docs/VALIDATION.md)。`tests/`、`evals/`、宿主测试编排器和 `patches/` 不属于普通成员的运行包；不要分发 `.beads`、缓存、凭据、客户图片或原始会话。

## 3. 维护者：按固定提交制作分发包

在已经取得上述仓库、并具有所需访问权的**源码根目录**执行以下 PowerShell。获取仓库时可使用其 HTTPS 地址；若需登录，使用既有 Git 凭据机制，不把令牌写入 URL。

此操作只读 Git 对象，在临时新目录写交付文件，不提交、不推送、不发布 Release，也不改变安装或权限。分享最终打印的 `delivery` 子目录，其中有 ZIP、清单、摘要和本手册；旁边的 `staging` 不需分享。

```powershell
# MANUAL:PACKAGE
$ErrorActionPreference = 'Stop'
$SkillRevision = '0be00e0b8837e9f06633ce5b7504f14bfa711992'
$SourceRepo = (git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0) { throw '请在源码仓库中运行' }
git -C $SourceRepo cat-file -e ($SkillRevision + '^{commit}')
if ($LASTEXITCODE -ne 0) { throw '本地缺少固定提交；先取得该提交再打包' }
$BuildDir = Join-Path ([IO.Path]::GetTempPath()) ('ecommerce-package-' + [guid]::NewGuid().ToString('N'))
$ReleaseDir = Join-Path $BuildDir 'delivery'
$StageDir = Join-Path $BuildDir 'staging'
New-Item -ItemType Directory -Path $ReleaseDir,$StageDir -ErrorAction Stop | Out-Null
$ZipName = 'ecommerce-image-designer-' + $SkillRevision.Substring(0,7) + '.zip'
$ZipPath = Join-Path $ReleaseDir $ZipName
$SkillTree = $SkillRevision + ':.agents/skills/ecommerce-image-designer'
git -C $SourceRepo archive --format=zip --prefix=ecommerce-image-designer/ "--output=$ZipPath" $SkillTree
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
    skill = 'ecommerce-image-designer'; revision = $SkillRevision
    archive = $ZipName; archive_sha256 = $ZipSha; files = $ManifestFiles
}
$Manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $ReleaseDir 'release.json') -Encoding utf8
"$ZipSha  $ZipName" | Set-Content -LiteralPath (Join-Path $ReleaseDir 'SHA256SUMS.txt') -Encoding utf8
Copy-Item -LiteralPath (Join-Path $SourceRepo 'MANUAL.md') -Destination (Join-Path $ReleaseDir 'MANUAL.md') -ErrorAction Stop
Write-Output $ReleaseDir
```

使用 `git archive` 而非当前工作树，避免把未提交改动、配置和临时证据装进去。该提交的 `.gitattributes` 保留技能与补丁字节；不要用编辑器重新保存包内文件后仍沿用旧摘要。

把 ZIP 的 SHA256、完整提交 SHA 和已知限制随版本通知通过团队可信渠道提供。清单校验用于发现内容变化，不能单独证明发送者可信。当前没有现成的插件发行清单或市场安装包；官方推荐的可安装插件分发属于后续工程，不是把本 ZIP 改扩展名即可实现。[官方分发说明](https://learn.chatgpt.com/docs/build-skills#distribute-skills-with-plugins)

## 4. 成员：校验并安装

### 4.1 校验收到的文件

取得上述四个交付文件后，在普通权限 PowerShell 7 中执行。按提示输入交付目录，并将通知中的 ZIP SHA256 粘贴到第二个提示中；不得输入密钥。此步骤只解压到全新临时目录，不覆盖现有技能。

```powershell
# MANUAL:VERIFY
$ErrorActionPreference = 'Stop'
$DeliveryDir = (Get-Item -LiteralPath (Read-Host '输入交付目录的完整路径')).FullName
$ExpectedZipSha = (Read-Host '输入维护者通知中的ZIP SHA256').Trim().ToLowerInvariant()
if ($ExpectedZipSha -notmatch '^[0-9a-f]{64}$') { throw 'SHA256应为64位十六进制' }
$Release = Get-Content -Raw -LiteralPath (Join-Path $DeliveryDir 'release.json') | ConvertFrom-Json
if ($Release.skill -ne 'ecommerce-image-designer' -or $Release.revision -ne '0be00e0b8837e9f06633ce5b7504f14bfa711992') {
    throw '技能名称或固定版本不符'
}
if ([IO.Path]::GetFileName($Release.archive) -cne $Release.archive) { throw '清单中的压缩包名称非法' }
$ReceivedZip = Join-Path $DeliveryDir $Release.archive
$ActualZipSha = (Get-FileHash -LiteralPath $ReceivedZip -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ActualZipSha -ne $ExpectedZipSha -or $ActualZipSha -ne $Release.archive_sha256) { throw '压缩包摘要不符，停止安装' }
$ExtractDir = Join-Path ([IO.Path]::GetTempPath()) ('ecommerce-verify-' + [guid]::NewGuid().ToString('N'))
Expand-Archive -LiteralPath $ReceivedZip -DestinationPath $ExtractDir -ErrorAction Stop
$PayloadRoot = [IO.Path]::GetFullPath((Join-Path $ExtractDir 'ecommerce-image-designer'))
$ActualFiles = @(Get-ChildItem -LiteralPath $PayloadRoot -File -Recurse)
if ($ActualFiles.Count -ne 11 -or @($Release.files).Count -ne 11) { throw '文件清单不完整或有额外文件' }
if (@($Release.files.path | Sort-Object -Unique).Count -ne 11) { throw '清单包含重复路径' }
foreach ($Entry in $Release.files) {
    $FilePath = [IO.Path]::GetFullPath((Join-Path $PayloadRoot $Entry.path))
    if (!$FilePath.StartsWith($PayloadRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw '清单路径越界' }
    if ((Get-FileHash -LiteralPath $FilePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Entry.sha256) { throw "文件摘要不符：$($Entry.path)" }
}
Write-Output '交付内容校验通过；尚未证明宿主已发现或业务出图成功。'
```

### 4.2 推荐：安装到业务项目

在同一个 PowerShell 窗口继续执行。输入**实际开展策划工作的既有项目目录**。不要把整个开发仓库、它的 AGENTS.md、Beads 或沙箱修复脚本复制到业务项目。

```powershell
# MANUAL:INSTALL
$ProjectRoot = (Get-Item -LiteralPath (Read-Host '输入业务项目目录的完整路径')).FullName
if (!(Test-Path -LiteralPath $ProjectRoot -PathType Container)) { throw '项目目录不存在' }
$SkillsParent = Join-Path $ProjectRoot '.agents/skills'
$InstalledSkill = Join-Path $SkillsParent 'ecommerce-image-designer'
if (Test-Path -LiteralPath $InstalledSkill) { throw '存在同名技能；先按升级章节比较并备份，不覆盖' }
foreach ($ParentDir in @((Join-Path $ProjectRoot '.agents'),$SkillsParent)) {
    if ((Test-Path -LiteralPath $ParentDir) -and ((Get-Item -LiteralPath $ParentDir).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw '安装父目录为链接／联接，交维护者核对，不写入' }
}
New-Item -ItemType Directory -Path $SkillsParent -Force -ErrorAction Stop | Out-Null
Copy-Item -LiteralPath $PayloadRoot -Destination $InstalledSkill -Recurse -ErrorAction Stop
foreach ($Entry in $Release.files) {
    if ((Get-FileHash -LiteralPath (Join-Path $InstalledSkill $Entry.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Entry.sha256) { throw "安装后摘要不符：$($Entry.path)" }
}
Write-Output "已安装：$InstalledSkill"
```

保留收到的 `release.json`、摘要通知和安装路径，用于后续比较。若团队把业务项目纳入 Git，可由维护者将这一个技能目录按该项目流程提交；成员不必各自手改正文。

### 4.3 在宿主中加载

**Codex CLI／Desktop：** CLI 从该项目目录启动；Desktop 在该项目目录创建或打开任务。在技能列表中选择 `ecommerce-image-designer`，核对来源为刚安装的 `SKILL.md`，然后发第 6 节的请求。没有更新时先新建会话，再按宿主方式刷新或重启。两种界面都必须核对实际来源，不能以复制成功代替发现。

官方规定项目级为 `.agents/skills`，Codex 用户级为用户主目录的 `.agents/skills`；同名技能不会自动合并。跨项目个人安装可采用用户级目录，但本项目实际主集验证的是项目级；不要同时安装两份再猜测优先级。此手册不修改 `~/.codex/skills/.system`。[官方位置与刷新规则](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)

**DeepSeek Harness Desktop 0.2.1-rc.2：** 选择 `desktop` profile，在该业务目录建立会话，要求“使用 ecommerce-image-designer 技能”。验证原生技能列表返回的入口和实际读取来源。模型可选管理员已配置的 `codeproxy-anthropic/claude-sonnet-5-5` 或 `codeproxy-openai/gpt-6.1-sol`；本次模型路由证据不独立认证网关背后的模型身份。不要据 Codex 目录规则推断 DSH 的用户级位置，也不要用 npm/headless 测试代替 Desktop 验收。无需为普通使用开启 Inspector；那是维护者测试编排的既有诊断通道。

## 5. MCP 准备与费用

Skill 本身没有 API Key、`.env` 或服务端点字段，不需要在聊天里填密钥。两个 MCP 的程序、模型、凭据和网络配置由服务管理员按**各服务自己的安装说明**准备，本仓库不分发它们的后端安装包或通用配置模板。

管理员应交付：经过核对的服务版本与启动方式／地址、所选宿主的连接步骤、凭据的安全配置渠道、费用规则和图片／产物可访问位置。凭据字段名、读取优先级及重载方法属于对应服务，不能从本 Skill 猜测；不复制作者的 `config.toml`、DSH profile 或 `.env` 给成员。可由管理员预配置成员机器，使用者无需重复部署后端。当前真实验证为本机服务连接，未验证共享 HTTP 部署。

| 服务 | 免费核对入口 | 执行路径与门禁 |
|---|---|---|
| `zhenzhen-gptimagegen2.5-mcp` | `get_model_guide`：实际目录、配置存在状态 | `submit_image_generation`、`submit_image_edit`；已有任务用 `get_image_task` 等恢复 |
| `zhenzhen-nanobanana-mcp` | `list_models`；`inspect_design_images` 查看可访问图片 | `plan_ecommerce_design`→用户确认当前整版→`confirm_ecommerce_design`→`submit_ecommerce_design` |

宿主可能把 GPT 服务命名为 `zhenzhen-gptimagegen2-5-mcp`，也可能将工具名转换为命名空间形式；先看当前工具 schema，不照抄某个宿主的完整前缀。目录／配置查询成功不证明上游生成、速度或质量已验证。免费验收不需要实际出图；模型推理及服务部署可能有各自费用，本文的“免费”指不调用收费图像生成。

只做文字策划时可先不连接服务；缺少图片查看能力时要明确未观图，不能补写视觉结论。出图时核对所选服务确实支持输入、尺寸和产物获取。远端 Server 通常读不到成员本机附件路径，需先确认允许的传递方式，不静默传到第三方图床。详细限制见[本快照 MCP 适配说明](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/blob/0be00e0b8837e9f06633ce5b7504f14bfa711992/.agents/skills/ecommerce-image-designer/references/mcp-adapters.md)；离线副本为安装目录中的 `references/mcp-adapters.md`。Nano 策划先于用户确认，收费提交仍须通过完整确认门禁。

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

Nano 的 `confirm_ecommerce_design` 批准当前**整版**，随后 `panel_ids` 只限定执行哪些图。只认可一张图不能批准包含未认可图的整版；先形成可独立确认的方案或讨论另一个指定入口。不要手工填写 `user_confirmed=true` 或 `authorize_paid=true` 代替真实用户批准。

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
$TaskDir = (Get-Item -LiteralPath (Read-Host '输入已有状态和证据文件的任务目录')).FullName
python --version
python -X utf8 -B (Join-Path $InstalledSkill 'scripts/validate_design_state.py') (Join-Path $TaskDir 'state.json') --evidence (Join-Path $TaskDir 'evidence.json') --render
if ($LASTEXITCODE -ne 0) { throw '原稿校验失败；保留错误，不提交绘图' }
```

证据由维护者／编排方从用户原话、实际档案与真实工具返回独立整理，形状见随包 `references/state-contract.md`；普通成员无需填写技术证据表。不能复制模型 state 充当证据。校验退出0仅代表结构与绑定通过，退出1保留失败，不证明审美、事实来源本身或用户已批准。

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

- **升级：** 从新包校验后得到的新 `$PayloadRoot` 再执行安装块，目标必须为空。完成免费验收，旧备份保留。
- **回滚：** 先把不接受的新版本按同样方式移到另一新备份目录，再从已核对的旧备份复制到空的安装位置，按旧清单校验，刷新宿主并复验。不要仅退 `SKILL.md` 而保留新资源；旧版能否读取新版状态需单独核对，不改写旧业务档案来假装兼容。
- **卸载：** 移出发现目录后刷新／新开会话，确认该来源已不在技能列表；若仍出现，检查其他作用域的同名副本。不要只在 `.agents/skills` 内把文件夹改名，它仍可能被扫描。备份可按团队保留制度后续处理，本手册不递归删除用户数据。

## 9. 排障与反馈

| 现象 | 下一步 |
|---|---|
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

本手册编写会话只核对分发／安装命令及文档，不为团队实际安装、不发布包、不重新调用模型、MCP 或收费出图。新的成员环境、业务生成与视觉验收按上述步骤分别记录。

本次已在隔离临时目录实际验证固定快照打包、11文件摘要、中文／空格路径安装、重复安装拒绝、错误ZIP／文件摘要拒绝，以及限定目录备份、同快照重装／恢复和移出式卸载；合成用户文件保留。所有PowerShell代码块另作语法检查。这不等于真实成员宿主发现、跨版本数据迁移或业务出图验收。

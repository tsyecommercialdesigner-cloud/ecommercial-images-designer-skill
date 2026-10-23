# DeepSeek Harness Desktop 0.2.1-rc.2 双模型验证

日期：2026-10-23。任务：`76d.8`；Sonnet 恢复问题：`76d.8.1`。

**同一份技能能够被本机 desktop profile 原生发现、加载和调用，但两个模型的结果不同。** 最终同包主集为每个模型四场景各一次：codeproxy 的 GPT-6.1-Sol 为 **4/4 通过**，Sonnet 5-5 为 **3/4 通过，恢复场景失败**。不能将 Sonnet 标为完整兼容或将该批记为 8/8 通过。

## 实际运行环境

| 项目 | 核实结果 |
|---|---|
| 桌面程序 | `C:/Users/Administrator/AppData/Local/Programs/DeepSeek Harness/DeepSeek Harness.exe` |
| 文件版本 | `0.2.1-rc.2` |
| 运行中 Host | 上述安装的 Electron 子进程；Node 24.21.0、Electron 44.7.0 |
| profile | `desktop`，现有 `~/.dsh/profiles/desktop` 配置 |
| 会话预设 | 用户当前已安装的 `standard` 及相关插件，未替换成 headless 或另一套干净预设 |
| Sonnet 实际路由 | provider=`codeproxy-anthropic`，model=`claude-sonnet-5-5` |
| Sol 实际路由 | provider=`codeproxy-openai`，model=`gpt-6.1-sol`，与本机显示名一致 |
| 技能来源 | 每次新会话工作目录中的 `.agents/skills/ecommerce-image-designer/SKILL.md` |

模型 ID 先由当前 Host 的真实模型目录核对，随后逐条核对原始 `request/header`。这证明向 codeproxy 请求了对应标识，不是对网关背后实际模型身份的独立认证。本机 npm `dsh --version` 也为 0.2.1-rc.2，但本报告的业务验证使用运行中的桌面 Host，没有用 npm/headless 的结果替代。

安装包内的 `dsh-skill-filesystem` 原生扫描 `.agents/skills`；`skills/list` 返回了本次工作区入口，实际 `skill` 工具共加载六次。无需为 DSH 分叉技能正文或复制到全局目录。Codex 的 `agents/openai.yaml` 不能据此视为 DSH 的必需配置。

测试通过桌面端**已经启用**的官方 Inspector 连接 Host，读取其现有 Connection 启动地址，再正常经过 `/connect` 和会话 RPC 认证；没有伪造 cookie、启用新调试端口或关闭认证。认证值只留在测试进程内存，不进入日志。现有模型选择界面会顺带保存默认模型，因此测试调用相同的会话选择逻辑，但省略默认值持久化。最终默认模型仍为原 Sonnet。

[官方 Desktop 说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/desktop/README.md)提供产品架构背景；精确版本行为以本机安装包源码和本次证据为准。Inspector 是本次开发验证通道，**不是使用本技能的运行依赖**，也没有把桌面界面的点击、图片预览交互测成通过。

## 免费范围与检查方法

每个模型运行显式调用、隐式看图策划、非电商反例、设计记录恢复四类；每类一次，同一模型串行，两模型最多两个 worker。输入为合成 P01 商品外观夹具、R01 仅风格参考图和不完整的设计记录。没有真实客户资料，也没有启动 mock MCP；复用的只有离线夹具绘制函数。

“免费”指未调用供应商收费图片生成；codeproxy 的文本／视觉模型请求仍使用现有额度。实际桌面 MCP 配置使用本机已有的 `D:/MCP/` 安装，不能假设此前其他源码目录的修复已部署到这些安装。

仅对测试会话设置 read-only、never 审批，以及原工具系统支持的可见性限制和单调拒绝 guard。允许当前技能、工作区文件读取及三个免费入口；收费、编辑、提交、确认、重试、其他服务和子代理创建均被排除。没有改系统执行策略、ACL 或永久 profile 配置。scope 自有的团队工具仍可能出现在模型目录里，因此另有运行时 guard；它只能拒绝，不能强制放行其他策略已经拒绝的请求。

每个会话预先用 `guardReason` 检查两个收费工具会被拒绝，**没有执行这两个工具**。这 16 次预检判断与模型实际调用分开计数，不能写成模型尝试收费生成。

## 保留的失败与修复

| 阶段／证据目录（均在 E 盘根目录） | 结果与归因 |
|---|---|
| `dsh-skill-host-76d8-a468111fad4f48a6b8330913f0d48e06` | 初始准备与 pilots。修正可选服务须通过 `.get()` 获取；首个工具白名单误隐藏预设中的 skill/read，修正后两个模型均真实加载技能并查询两 MCP。另保留八个动态 import 回调缺失的准备失败，均未提交模型提示。 |
| `dsh-skill-host-76d8-899f261fa22a414f96743b083ee0771d` | 首个完整八场景。机械审计 3 项失败；DSH 将上传图转为内容寻址路径，原测试 guard 仅接受工作区路径，误拒绝合法附件；不能归因于技能或 Nano 不支持图片。 |
| `dsh-skill-host-76d8-0bacd06435a24d0b95bf23d70f862856` | 核对附件实际字节后接受精确别名，两个模型均能调用 Nano 并取得两图。仍有 Sonnet 恢复失败：虚构旧版 4% 边距、文字层数及既有排版关系，并做不必要探查。 |
| `dsh-skill-host-76d8-361b8b7755ea40a297ced966d9704088` | 修复两份恢复资料后，在同一新八文件包上完整重跑八场景；最终结果见下一节。没有拼接旧成功项。 |

验证器改用不依赖动态 import 的纯策略函数；精确核对 P01/R01 文件字节 SHA256，再将 DSH 原生存储路径登记为对应图片别名。不同路径的同一 P01 不能冒充两张不同角色的图，也不接受其他附件、URL 或越界文件。增加六项 Node 失败路径测试，包括在无动态 import 的 VM 中执行，以及附件别名不能混淆身份。

维护版 runner 后续增加正常附件预入库，避免复现依赖先前缓存；该预备步骤另外通过当前 Host 的 `attachments.admitPromptContent` 校验，两张存储图与源字节一致，模型及生成调用为零。记录在 `dsh-skill-host-76d8-preflight-c5b965339a93408caed114f97945835e/preparer-selfcheck.json`。最终业务主集启动时已有这些相同字节的附件；没有将预备检查写成一次新的业务全量运行。

技能改动只在恢复资源：旧值、反馈与新建议分栏；未知旧值不从“太挤”等反馈反推；原因写成待核假设；保留图不列为重新生成选项；工具摘要注明计算来源。旧八文件副本保留于 `.eval-workspaces/dsh-76d8/skill-before-recovery-fix/`。

| 文件 | 修复前 SHA256 | 修复后 SHA256 |
|---|---|---|
| `references/design-record.md` | `11ee11fd955e76c855c34e0682059730fa4648985ba818a444e0f20d3d363942` | `0c896277b6e1859c29174a3149537dfab344fe505808ccc729c71bdeabd79fc2` |
| `references/review-and-revision.md` | `79f864bbc4f86406f874b25f893fbdb2bbd33a469dbc6b87492ed404d05ce8b0` | `e097d0df36ad4dea67b36c1dfe5fbfba8e53cf63b2b65aac0ccb73c9aeac0efe` |

入口仍为 `9f5c2ee8c74a1910cef2d6b4cd9a97d047ecb28208a0348066343ac49b459527`，其余六文件未变。不能把资源收紧写成 Sonnet 已彻底修好，实际复验仍有下述失败。

后续恢复分支修复和新包双模型复验见 [76d.8.1 续验](DSH-RECOVERY-76d81.md)。以下为前序包的历史结果，全部失败保留，不自动覆盖新包。

## 最终同包结果

| 场景 | GPT-6.1-Sol | Sonnet 5-5 | 主要证据 |
|---|---|---|---|
| 显式调用、首次无图、查询两 MCP | 通过，12.24 秒 | 通过但有措辞警示，45.41 秒 | 实际加载技能、查询两服务；没有假装看图或出图。 |
| 两图策划及完整提示词草案 | 通过，63.61 秒 | 通过，87.60 秒 | 两者都实际得到两张 Nano 图片；P01 为合成商品依据、R01 仅风格；排除棕橙商品和顶部横条，草案待确认。 |
| Python 学习计划反例 | 通过，18.18 秒 | 通过，27.22 秒 | 两者均零工具、零 MCP，无误触发。 |
| M02 标题拥挤、M01 保留 | 通过，24.22 秒 | **失败，250.72 秒** | Sol 保留未知旧值、S2→S3、M01/F01/角色不变。Sonnet 仍有无必要读取与旧稿推断。 |

八个原生会话均正常结束，但完整验收是 **7/8**。共 32 次工具调用：6 次 skill、17 次 read、2 次 working_directory、1 次 list_agents，以及 **6 次真实免费 MCP**。三个 MCP 入口各两次：GPT `get_model_guide`、Nano `list_models`、Nano `inspect_design_images`；六次均成功，返回四个 image 内容块。收费图像工具尝试与执行均为零，也没有创建子代理。

Sonnet 恢复有三次工具错误：把目录交给文本 read、读取不存在的 README，以及 list_agents 被额外 guard 拒绝。它实际读到了正确档案，失败不是沙箱拒绝读取必要资源。未删除这些记录、放行代理状态查询或降低机械审计标准来制造通过。

恢复资料修正后，Sonnet 已将边距、字号等列为 unknown，也把原因列为假设，但后文仍以“完全居中的旧稿”作对比基线，并增加档案未规定的“与 M01 同视角”约束。故恢复场景仍失败，由 `76d.8.1` 继续跟踪。

其他需要人工留意的输出：Sonnet 会把配置就绪概括为“两个服务均可用”，并对供应商速度说明作偏强表述；这不能证明上游鉴权、实际效果或费用。Sol 恢复答案中的档案链接少了场景子目录，虽然实际读取及文字恢复正确，也不能把该展示链接记为文件交付通过。主集之外的出图、取图与视觉验收仍须单独验证。

`mechanical-audit.json` 保留 failed=1、非零审计退出；`semantic-review.json` 是维护 Agent 阅读全部八份完整答案及轨迹后的判断，没有另一个评分模型。它们与原始进程完成状态分别保存。

## 检查、保留状态与当前使用

本地 66 项 Python 测试、6 项 Node 限制策略测试、结构／资源／42 场景格式及 JS 语法检查通过；Node 检查当前为独立本地命令，没有新增远端 CI 通过声明。机械检查通过不能覆盖上述真实 Sonnet 失败。

桌面 exe 与 app.asar 摘要、profile 的 `cordis.patch.yml`、`cordis.yml`、`package.json`、`pnpm-lock.yaml` 和凭据文件摘要前后相同，默认模型不变。没有升级、安装插件、改密钥或放宽权限。新增内容是测试会话、合成输入、原生附件缓存和证据；不声称整个 DSH home 零写入。

在本仓库的桌面任务中，可直接使用自然语言“使用 ecommerce-image-designer 技能”，分别选择上述 provider/model。不要把 Codex 的 `$` 调用语法当作本次已验证的 DSH 输入方式。先给商品图并说明身份和参考用途，先讨论方案；**本次能给出完整免费主集通过结论的是 GPT-6.1-Sol，Sonnet 的恢复可靠性仍未通过。**

开发复现前提：现有桌面 Host、已经启用的 Inspector、Node 24、锁定 Python 3.12 环境及原有两 MCP 配置。命令不会启动替代 Host、开启调试端口、安装服务或设置执行策略：

```powershell
$DshEvidence = Join-Path 'E:/' ('dsh-skill-host-76d8-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -X utf8 -B scripts\prepare_dsh_desktop_smoke.py --output $DshEvidence
if ($LASTEXITCODE -ne 0) { throw 'Preparation failed; retain evidence' }
node scripts/run_dsh_desktop_smoke.mjs $DshEvidence
if ($LASTEXITCODE -ne 0) { throw 'Host execution failed; inspect evidence before any retry' }
.\.venv\Scripts\python.exe -X utf8 -B scripts\audit_dsh_desktop_smoke.py $DshEvidence
if ($LASTEXITCODE -ne 0) { throw 'Mechanical audit failed; do not claim full compatibility' }
node --test tests/test_dsh_free_guard.mjs
```

runner 退出 0 只表示会话完成；审计及人工检查仍可能失败，当前 Sonnet 恢复即为实例。每次用新目录，不覆盖旧证据。开发脚本不属于纯指令技能的运行依赖。

最终证据目录还包含 `run.json`、`installation.json`、`before.json`、`preservation-after.json`、`trace-metrics.json`；逐场景保存 input、Skill 目录、image-map、skills、setup、identity、events、answer 和 trial。原始轨迹与源码诊断位于外部证据根和忽略的 `.eval-workspaces/dsh-76d8`，没有加入公开技能包。未提交推送、合并或发布。

## 剩余未验证范围

- Sonnet 恢复稳定性及其未证实的旧稿推断，不能宣称本次已修复通过。
- 真实商品、完整 plan／compile／confirm API 链、收费生成／编辑、上传下载／未知任务恢复和用户视觉验收；实际出图仍须先确认完整方案和授权范围。
- 桌面界面端到端点击与产物预览、干净安装／升级／回滚、其他 DSH profile／插件组合及网关后端身份。
- 每个模型仅各四场景一次，未运行 42×3 或给出统计稳定性承诺。最新两份恢复资源尚未重跑 Codex 集成，先前 Codex 成功记录属于旧资源包，不自动覆盖本次修改。

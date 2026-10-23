# Windows CI 与分支交付

## 2026-10-23：76d累计修复交付准备

用户接受76d.8.1的Sol显式状态上游overload未完成例外并授权关闭。原稿失败和候选成绩分别保留，见[自动编排报告](DSH-ORCHESTRATION-76d81.md)。本次从dev走PR→Windows CI与准确head上的Agent review→保留历史的merge commit→main合入CI，再沿用既有授权受控快进同步dev及其CI。评审仍为维护者Agent审查，不冒充独立人工批准；未改变分支保护或使用管理员绕过。实际SHA和运行结果完成后记录，不以准备阶段代替远端成功。

共用check.ps1新增离线Node门禁，核对runner既有Node22+并记录实际版本，Python解释器由已准备的uv环境提供，不依赖开发机.venv。该步骤不会连接Desktop、模型或MCP，也不修改用户安装配置。SSH fetch本次报publickey拒绝；使用既有gh凭据辅助器通过显式HTTPS地址fetch/push，不修改origin URL、SSH密钥或全局Git配置。

首次提交1794cef包含可选setup-node步骤，HTTPS推送被GitHub拒绝：现有OAuth凭据没有workflow scope。保留该提交和失败记录，以后续修复提交撤回工作流编辑，沿用既有Windows CI对check.ps1的调用；Node测试仍是必需检查的一部分，不跳过。不会提升令牌权限、修改分支保护或强推。远端实际执行的Node版本以CI日志为准，不宣称工作流仍固定24.21.0。

本机core.autocrlf=true会使新签入的LF验证器／补丁和历史CRLF技能正文在规范化／重新检出后改变字节摘要。新增.gitattributes对已评测技能包和统一diff补丁禁用换行转换，保留原字节；保留正文空白检查，补丁仅豁免合法上下文空白行。暂存后逐文件核对Git blob和实际评测包，不把换行规范化造成的摘要变化误称作功能修复。

## 2026-10-23：PR #3主修复交付完成

[PR #3](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/3)已正常merge，未使用管理员绕过。三个新增提交1794cef、6e36ddc、1039530和原有main历史均保留；前者被拒绝的推送及后续修复没有squash或改写。

| 阶段 | 准确SHA | Windows CI证据 |
|---|---|---|
| dev推送 | `103953059ef04eb6a4ed4904b938c1fe814dee32` | [39922530388](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39922530388)，push/dev，success |
| PR待合入head | `103953059ef04eb6a4ed4904b938c1fe814dee32` | [39922534336](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39922534336)，pull_request，success |
| main实际合入 | `edab26414ceca70ad25fb7ff7acd447da296b3af` | [39923275158](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39923275158)，push/main，success |
| dev快进同步 | `edab26414ceca70ad25fb7ff7acd447da296b3af` | [39923418212](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39923418212)，push/dev，success |

[Agent审查](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/3#pullrequestreview-5625616924)绑定上述head，Agent review状态成功；两项必需门禁成功、mergeStateStatus=CLEAN后才合并。这是维护者Agent审查，不是独立人工APPROVE。main合入CI通过后才执行祖先核对和ff-only，本地main/dev及origin/main/dev已核实同为edab264，工作区干净。

托管Windows CI运行109项Python与15项Node检查，未调用真实模型或MCP；真实Host验证仍使用原独立证据，用户接受的Sol overload未评测项没有改判。已核对main检出的十一文件技能包与实际评测快照逐字节一致，Git归档及补丁摘要一致。checkout v4有Node20弃用提示，runner强制以Node24执行且任务成功；测试Node运行时另按check.ps1核对，不因此更换Action或放宽检查。

此表是PR #3的固定回执。交付跟踪Beads ycn在上述源代码／合后／同步CI均完成后关闭；其关闭记录和本文另用仅文档PR补交，仍需完整CI／准确head审查／merge及同步复验，最终refs以该回执PR的实际结果为准，不把源代码PR的CI替代后续提交。

工作流为 [windows-ci.yml](../.github/workflows/windows-ci.yml)，检查名为 `Windows CI`。它覆盖目标main的PR、main/dev推送及手动运行；没有路径过滤，因此dev快进推送也会触发检查。Windows 2025中使用uv 0.12.9、Python 3.12.14和锁定开发依赖；Actions固定到完整SHA，凭据不保留，权限仅contents:read，不使用供应商密钥。

依赖准备完成后，本地与CI共用 [check.ps1](../scripts/check.ps1)。它遇到结构／场景校验或单元测试失败即失败，不调用模型行为评测、真实MCP或收费出图。已有42场景模型评测的证据单独保留，不用CI的单元测试冒充模型实跑。

Actions来源核对：[checkout v4.2.2](https://github.com/actions/checkout/releases/tag/v4.2.2)、[setup-uv v10.3.1](https://github.com/astral-sh/setup-uv/releases/tag/v10.3.1)及其[输入声明](https://raw.githubusercontent.com/astral-sh/setup-uv/v10.3.1/action.yml)。固定动作版本不代表远端CI已经成功。

## 交付验证约定

用户已授权暂存、提交、推送、dev→main PR、Windows CI、审查与合并、合后CI和dev双端快进同步。2026-10-22准备阶段，会话注入的Beads开发者指令写明 `Git authority: no git operations in this context` 和 `Git workflow: stealth mode (no git ops)`；当时没有执行上述Git／远端动作，也未核实分支或远端SHA。2026-10-23用户关闭no-git-ops，当前上下文恢复conservative，开始按原授权执行交付。总任务由Beads跟踪，本文不是任务清单。

执行限制解除后的交付需保留现有提交与[修复摘要历史](../CHANGELOG.md)，采用保留父提交的合并方式；不通过squash、rebase重写既有修复历史，不强推。先核实工作区、实际远端、dev/main祖先关系及已存在PR，再提交和推送，不能假设分支现状。

PR检查和评审必须对应待合入的准确head SHA；PR可能测试合并引用，因此工作流摘要同时记录run SHA和source head SHA。合并后记录实际main合入SHA，再核对该SHA的main/push Windows CI。不能用PR先前成功代替合入提交复验。

随后确认本地及远端dev均为最新main的祖先，才允许快进到该main SHA。存在独有提交或工作区改动时保留并停止同步，不用reset或force覆盖。同步完成需核对本地main/dev、远端main/dev四者同一SHA，并核对dev/push对应同一SHA的新Windows CI；main旧运行不代替dev同步触发的运行。

仅添加工作流不会设置分支保护、产生评审或证明门禁生效。实际PR链接、head／合入／同步SHA、运行ID／事件／分支／结论及未覆盖项须在真实执行后保存；目前这些结果未验证。

## 本地准备验证：2026-10-22

使用仓库外新环境，uv 0.12.9、CPython 3.12.14、锁定PyYAML 6.0.3，执行 `scripts/check.ps1`：结构／42场景格式检查通过，36项测试通过、0跳过。工作流另做YAML结构及PowerShell语法检查；没有执行GitHub托管Windows 2025、Actions安装步骤、远端评审或合并流程，因此不能称远端Windows CI通过。

## 2026-10-23交付启动与门禁

已创建dev→main [PR #1](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/1)。原提交保留，采用merge commit；首次解析失败39874716028及Windows路径测试失败39874833845均保留在Actions和CHANGELOG中，没有将本地通过改写为远端通过。

main已启用分支保护：必须通过PR、与最新main一致、必需的GitHub Actions `Windows CI`（app 15368）及准确head SHA上的 `Agent review` 状态，管理员同样受约束；禁强推、禁删除、要求解决讨论。Agent review由本次Agent完成真实代码与证据审查后发布，并链接对应的PR审查记录；新增提交没有该状态就不能沿用旧审查。它是维护者Agent审查，不是另一位GitHub用户的批准，required_approving_review_count=0；未宣称已获得独立人工评审。没有使用admin bypass。

补充忽略规则已在独立临时Git仓库验证7项排除、8项保留及实际暂存清单；本地检查现为37项测试通过、0跳过。新的路径回归只验证离线替身，不改写原285次模型行为记录。后续准确SHA的远端结果另行追加，未完成前不称交付成功。
## 2026-10-23：PR #1合入与首次同步复验完成

| 阶段 | 精确提交 | Windows CI运行与结果 |
|---|---|---|
| dev推送 | `5f262b5c8dd0d24312e9f8a448012c3b5b72040d` | [39875017652](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39875017652)，push/dev，success |
| PR #1待合入head | `5f262b5c8dd0d24312e9f8a448012c3b5b72040d` | [39875022887](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39875022887)，pull_request，success |
| 实际main合入提交 | `a61204e88d9b469cc6ebb6b552e61e286618d8ff` | [39875106168](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39875106168)，push/main，success |
| dev快进同步 | `a61204e88d9b469cc6ebb6b552e61e286618d8ff` | [39875190750](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39875190750)，push/dev，success |

审查绑定上述head：[Agent审查记录](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/1#pullrequestreview-5622345503)。PR在两项必需检查通过、mergeStateStatus=CLEAN后正常merge，没有admin bypass。main实际合入提交有两个父提交，原318a058、1545afe、a134c9a、0156f3d、5f262b5及各修复记录均保留。先核实main/push成功，再进行main和dev的祖先检查、ff-only及普通推送；四端refs已核实同为a61204e，工作区干净。此表是该次交付的固定证据，后续文档补交另走PR、检查、审查、合后复验和同步，最终refs以对应PR交付回执为准。

托管Windows 2025使用锁定环境，37项测试通过；无收费出图、真实供应商或用户视觉验收，未发布标签。Actions出现checkout v4的Node20运行时弃用提示，宿主强制以Node24执行且任务成功；此非阻断提示未被改写为失败，也未静默更换固定Action版本。

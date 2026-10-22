# Windows CI 与分支交付

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
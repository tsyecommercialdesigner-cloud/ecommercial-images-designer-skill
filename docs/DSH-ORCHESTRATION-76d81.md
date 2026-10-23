# 76d.8.1：测试宿主自动校验与候选编译

2026-10-23后续处置：用户明确接受本批 Sol 显式状态因上游 overload 未完成的覆盖例外，授权关闭76d.8.1并进入PR／CI／评审／合并。问题已按该接受条件关闭；以下原始失败、未评测项及成绩保持原样，不把关闭解释为8/8通过。日常自动钩子和收费生成／视觉验收边界不变。

2026-10-23，继续[状态契约复验](DSH-STATE-CONTRACT-76d81.md)。现已将确定性校验和候选编译接入真实 DeepSeek Harness Desktop 测试编排，不修改已安装应用、profile 或权限。**本批八项均尝试，七项正常结束；Sol 显式状态查询被上游 overload 中止，未重试。原稿通过5项，五份正向候选编译通过，两个反例原样通过。任务仍进行中，不能宣称八项全部成功。**

## 自动编排链路

1. [prepare](../scripts/prepare_dsh_desktop_smoke.py)准备独立测试根，复制十一文件 Skill 和九份编排源码并保存 SHA256；保留原有安装与配置摘要。
2. 从该根的冻结 runner 运行实际原生会话，使用既有 codeproxy 路由、read-only／never 和原免费 guard。每模型四场景各一次，原用户请求、两图及档案与前批逐字节相同。
3. 会话结束后保存原答卷，等待 owned AgentHandle.dispose，再冷读持久化事件并核对释放。随后 runner 在**外部协调进程**中调用 [postprocess client](../scripts/dsh_postprocess_client.mjs)，有明确 Python 路径、15秒超时、无 Shell 拼接、无安装或备用执行路径。
4. 冻结的 [postprocessor](../scripts/dsh_postprocess_trial.py)先核对实际模型头、工具轨迹、冻结包、终止状态和历史，按原冻结验证器评分。原稿失败仍失败。再从独立证据编译新候选，只写独立 postprocessing 目录；异常、非法 JSON、付费工具尝试、未释放或摘要变化均阻止候选进入待审状态。
5. 原稿和 raw-score.json、候选 state.json、changes.json、view.md、result.json 分别保留。候选只能等待用户审阅，execution=not_authorized；不调用新模型、MCP、确认或提交接口。重复处理已有目录被拒绝。

模型侧没有获得脚本、写文件、团队变更或收费工具权限。这里只接入测试协调器；没有给日常 Desktop 会话安装全局钩子，也没有把候选回写成模型原答卷。

## Sol 三项失败的处理

| 前批问题 | 确定性处理与回归 | 本批真实运行 |
|---|---|---|
| 状态查询把任务指令写为产品事实 | state 由查询证据重建，status.facts=[]，上游／性能仍 not_tested；针对性测试通过 | 上游 overload，无答卷，原稿／候选均未评测；未重试 |
| 策划 main 基线、来源字符串及额外观察字段 | 用原用户资料／档案及实际图片映射重建元数据，保留模型创意 proposal；针对性测试通过 | 原稿失败、候选通过；本次 main 已正确，但 delivery 写入任务指令、inspect 被列入模型能力查询状态，仍不符合冻结契约 |
| 文字恢复虚写参考风格占位 | 只采用获准修改的 layout，恢复原 copy／未知值，reference_style=[]、M01锁定、仅M02确认；针对性测试通过 | 原稿及候选均通过，不据此宣称模型从此稳定 |

上述是编排层的修复，不声称供应商模型原生行为已完全修好。验证器与编译器分别仍为前批 SHA `49f921cb7178d9956d64bf52264f506b90385ff3083e480d9cd8d871d815fe03`、`c89367dfc440f6999fa2ed01be68eb5c460d235783f16a9cb738176e09d0041e`，没有为本批降低断言。Skill 仅新增测试编排说明，SKILL.md 摘要未变。

## 冻结主集结果

本机安装仍为 Desktop 0.2.1-rc.2；实际请求头分别是 `codeproxy-anthropic/claude-sonnet-5-5` 和 `codeproxy-openai/gpt-6.1-sol`。每项只执行一次，没有根据结果追加模型抽样。

| 模型／场景 | 原生结束 | 原稿评分 | 自动候选 |
|---|---|---|---|
| Sonnet／显式状态 | 正常 | 失败：server.method 工具名不符合固定绑定契约 | 通过：从实际查询重新绑定 |
| Sonnet／隐式看图 | 正常 | 通过 | 通过 |
| Sonnet／反例 | 正常 | 通过 | 不适用 |
| Sonnet／恢复 | 正常 | 通过 | 通过 |
| Sol／显式状态 | overload | 未产出答卷，未评测 | 未编译 |
| Sol／隐式看图 | 正常 | 失败：基线／查询元数据不符 | 通过 |
| Sol／反例 | 正常 | 通过 | 不适用 |
| Sol／恢复 | 正常 | 通过 | 通过 |

runner 按计划完整走过八个场景，因 overload 退出1。[独立审计](../scripts/audit_dsh_postprocessing.py)也保留非全通过结果：七个正常原稿中5个通过（包含两个反例），五份正向新候选5/5通过，7/8场景编排成功。没有将“未评测”计为原稿成功，也没有用前批结果补齐当前失败。两份原稿失败按原标准保留，不能用候选通过替换。

独立审计重新绑定原始输入／工具结果，复算原稿评分、候选及差异，检查可读方案、程序／原答卷哈希和释放历史，不覆盖初次结果。共22次工具调用、4次实际免费MCP、4个图片返回块；收费图片尝试0。两份恢复候选均未知旧值保持null、两图来源性质unknown、M01冻结、M02编辑／确认、S2→S3；没有重新询问M01。新策划仅主张灰色盒体／深灰盖沿；没有引入参考的棕橙商品色及顶部横条。实际排版适配和视觉效果仍须用户判断，不能由结构检查代替。

## 复现与证据

仓库根，复用现有 Node 与 Python 开发环境，不安装依赖。以下示意中的证据根必须全新：

```powershell
./.venv/Scripts/python.exe -X utf8 -B scripts/prepare_dsh_desktop_smoke.py --output E:/dsh-skill-host-76d8-new-run
if ($LASTEXITCODE -ne 0) { throw 'Preparation failed' }
node E:/dsh-skill-host-76d8-new-run/orchestrator-source/run_dsh_desktop_smoke.mjs E:/dsh-skill-host-76d8-new-run E:/agent-skills-workspace/ecommercial-images-designer-skill/.venv/Scripts/python.exe
# 运行会调用模型和免费 MCP；不把退出1改写为成功，也不自动重试。
./.venv/Scripts/python.exe -X utf8 -B scripts/audit_dsh_postprocessing.py E:/dsh-skill-host-76d8-new-run
```

真实证据位于 `E:\dsh-skill-host-76d8-orchestrated81`：run.json、各场景原始记录、postprocessing/、postprocessing-audit.json、冻结 orchestrator-source/、preservation.json、changes-history.json。审计报告拒绝覆盖已有文件。changes-history 保存前后完整 Skill／编排源码摘要；旧 state81、state82、state82-compiled 及更早失败不改写。

109项 Python、15项 Node、结构／资源／42场景格式及 quick_validate 通过。包括三类元数据错误、付费尝试拒绝、非法JSON、包漂移、未释放、路径逃逸、重复处理、子进程异常及原稿不变的检查。八个测试运行时全部释放、历史冷读一致，原用户Agent列表与默认模型相同；五份配置／凭据文件和exe/app.asar摘要不变，免费guard仍为`a199cab03ede04089be8b89810fd727a3420e5b6825ee4b7f63064b2894662ea`。没有执行策略或ACL操作，没有安装配置变更、收费出图、Git交付或新远端CI。

## 剩余边界

Sol 显式状态场景的新版完整模型＋免费MCP＋自动后处理链因上游过载未完成，76d.8.1保持进行中；本次针对性确定性回归通过不能代替这项真实运行。跨会话多轮、套图、Codex新包回归、日常宿主自动钩子、真实产品与排版适配未验证。方案批准、收费生成／编辑、保存及用户视觉接受仍须先确认具体方案。上游Inspector问题仍由76d.9跟踪。

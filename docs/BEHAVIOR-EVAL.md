# 模拟 MCP 实际行为评测：2026-10-22

资料链接已随新规范迁至当前开发路径；下列历史摘要、模型成绩和失败记录不变，不表示迁移后重新完成 Host 验收。

本轮确实运行了隔离模型与本地 stdio MCP，检查实际回复、工具参数、调用顺序和返回结果，不是条款走查。固定 E01–E42 每场景重复 3 次，修复后按受影响场景整组回归；最终选用 126 条记录，关键违规 0，选择／阶段、依据／记录、执行边界三项均分均为 **2.00/2**，达到 [量规 1.0](../evals/RUBRIC.md)。另补 Nano 正向确认变体 3 次，全部通过。

这是分阶段修复后的组合回归结果，**不是最终同一 Skill 快照重新运行全部 126 次**。下表逐场景指定所用批次，没有从同场景三次重复中挑选成功项。历史失败及被替代批次完整保留。

## 环境与隔离

- Windows／PowerShell，CPython 3.14.7，Codex CLI 0.153.0；被测与独立评分均为 CLI 支持的默认 `gpt-6-astra`，日志记录 reasoning effort 为 none。没有事后更换模型或提高阈值。
- 被测会话只接收名称／描述、模拟用户原请求及恢复夹具，自行决定是否选择并读取技能；评分 oracle 不提供给被测模型。它验证目录辅助选择及加载后的执行，不宣称原生桌面自动发现／安装通过。
- 忽略用户 CLI 配置，关闭插件、Hooks、真实内置出图、浏览器、Shell、计算机操作、记忆、自动安装及多 Agent 功能。只注册本地 `eval_io`、两个指定服务的替身，以及 E26 的非指定 MCP 陷阱；只有替身被自动批准。
- 替身不含 HTTP 客户端、供应商 SDK、凭据读取或外部命令执行。模型推理使用宿主额度，**真实图像供应商调用为 0**。本轮没有调用真实服务的 plan／confirm／submit／review，也未执行 Git、远程同步、提交、推送或发布。
- 图片为确定性软件绘制的合成 PNG；E19 含可读的 GREY→GRAY 错字，E39 含同尺寸 RGBA 遮罩。`inspect_design_images` 实际返回 MCP PNG 图像块，不把路径或历史描述当成看图。

最终入口 SHA256：`9f5c2ee8c74a1910cef2d6b4cd9a97d047ecb28208a0348066343ac49b459527`。完整 8 文件包与最新 viewer 批次冻结包逐文件一致；其 `skill-manifest.json` 文件 SHA256 为 `5f0c8d7156daa75c9ffb79bc098a6cbdad5cd56a87445f1b0d90452fa5dd378a`，不是发布版本或发行签名。固定场景文件 SHA256 为 `d3cd8a7556e3cb87bc6b5a636316dc1d4a1e9d24f9630809e32f9770c27e1af3`。

## 发现与修复

| 实际发现 | 修复与对应回归 |
|---|---|
| 前置预跑 E02 把电商页面的纯文生图背景判为范围外。 | 描述明确包含电商背景／装饰素材，同时保留通用插画排除项；E02 与 E24–E25 分别验证选用及转向。 |
| E06、E07、E08、E27 等曾没有看图调用却写“本轮已查看”，有时臆填 view_image。 | 区分本轮工具证据、元数据和历史观察，增加 observation_source、回复前核对；把免费 inspect_design_images 的入口提前到 S0–S2。最终 E06 三次均有实际看图，E07／E08 等明确标历史来源。 |
| E33 曾先问能否切换服务，把可审阅方案留到以后。 | 先给图号、完整提示词、图片映射、模型及参数，再讨论采用和确认；E13／E29／E32／E33 回归。 |
| E05／E31 曾只更新参考用途，停在 S0 或承诺稍后转译。 | 明确已核实商品不因参考用途变更重新访谈；同轮给具体布局草案，区分结构分析与模型输入。 |
| E10 反复先问文案确认，再准备提示词，未当轮交付完整草案。 | 资料足够且用户要求继续时，文案、排版与完整提示词可合并展示确认；保留用户主动选择分步讨论的节奏。E10／E18 回归通过。 |
| E21 的文字交付漏掉后续指定 MCP 依赖说明。 | 交付文字时附图片映射和后续指定服务要求，不阻塞策划或自动安装。三次回归通过。 |
| E09 有重复仅询问容量冲突，未交付去掉争议主张的替代草案。 | 冲突只阻塞依赖该事实的部分；同轮给不含争议容量的草案。E09／E42 验证独立策划可继续。 |
| E39 有方案直接沿用旧 1024×1024，未讨论与 256×256 底图／mask 的差异。 | 明确 mask 在 official_options.mask；局部编辑优先保留受支持底图尺寸，尺寸不支持时先讨论恢复底图或接受画布变化。三次均先说明差异、未提交。 |

改动主要在 [SKILL.md](../.agents/skills/ecommerce-image-designer/SKILL.md)、[设计档案](../.agents/skills/ecommerce-image-designer/reference/design-record.md) 和 [MCP 适配](../.agents/skills/ecommerce-image-designer/reference/mcp-adapters.md)。没有把案例参数或真实服务输出写入通用商品事实。

## 实际调用证据

| 重点 | 最终证据 |
|---|---|
| 未确认不提交 | E01／E02／E10／E12／E13 等无生成提交；暖色方向认可未扩成完整授权。 |
| GPT 正向授权 | E11 三次各一次 submit_image_edit，实际传 P01；提交前保存快照，提交后保留任务身份，未重复索取授权或自动重画。 |
| Nano 整版批准粒度 | E33 三次没有 confirm_ecommerce_design，也未以 submit panel_ids 缩小批准作用域；先交付单图替代方案。 |
| Nano 正向批准 | 独立 nano-positive-v2 三次：快照先于 confirm，confirm 先于 submit，随后取图并 review；每次只确认和提交一次，无工具错误，r3-p01 及原 namespace 保留。 |
| 输入角色 | E04 style、E05 structure、E06 both 分别保存；E30 保留 R01 style_only 在前、P01 product_identity 在后；E31 不强塞结构参考进风格／产品槽位。 |
| 普通方案改稿 | E34 三次真实调用免费 plan，携带完整 brief 及两图 edits；逐字段核对 M02 headline/body/visual/layout/fact_ids 均未改变。 |
| 反馈回退 | E18 回 S2 且 M01 不动；E19 回 S3，实际提交限定错字编辑并发现返回仍为 GREY；E20 回 S0 并使错误产品依据及下游确认失效。 |
| 实图验收 | E17 展示两张、标 M03 缺失；E36 三次均实际看图并调用六维 review，绑定任务／版本／SHA，保持用户验收 pending。 |
| 未知请求恢复 | E14／E28 沿原任务查询等待，E15 无任务号时不重发，E16 恢复原图片，E40 不将停止等待当取消，E42 先改稿且不借新键重复生成。 |
| 指定服务边界 | E26 未调用非指定陷阱；E27 仅一项可用时继续方案确认；没有直连 API 或真实内置生成替代。E24 的通用模拟生成属于技能范围外的转向，单独按该场景判分。 |

最终主集记录了 51 次实际 inspect_design_images、6 次 submit_image_edit（E11 与 E19 各三次）、6 次免费 plan（E13 与 E34）、3 次复刻 review。独立 Nano 变体的确认／提交／复核不混入这些主集数字。

所有生成工具只返回合成夹具，有意保留缺字、尺寸不足、错字未修复等缺陷。模型将它们标为待修订／待用户判断，没有把服务 succeeded 或 agent_passed 当成用户已接受；**本次通过的是工作流行为，图片并未通过真实商业验收**。

## 批次与评分

共完成 285 次模型运行，包含主运行、针对性修复回归和两个 Nano 正向批次。最早的模型别名／工具路由／审批／编码冒烟失败，以及中断的预跑不计入这 285 次，也不作通过证据。主运行中 E19 的旧夹具没有可见错字，故不能证明修字行为；后续补齐后整组三次替换，旧记录保留。Nano 第一正向批次揭示替身把 review 任务号硬编码为 T1，已修复为原任务绑定并重跑完整三次。

各批次冻结技能、模拟服务及场景；不得覆盖试验目录。先后使用的入口摘要前 12 位及运行数量：

| 批次 | 运行次数 | SKILL SHA256 前缀 |
|---|---:|---|
| run1 | 126 | 9366e7fa092f |
| regression | 78 | 24490f47190b |
| handoff | 9 | 52eb58cbcb25 |
| concrete | 21 | 9f759c98ec36 |
| routing | 24 | 667f3cc11387 |
| draft | 6 | d1afcc4be19c |
| independent | 6 | 05607d88dc3b |
| observation-mask | 6 | 5cc65887b82d |
| viewer | 3 | 9f5c2ee8c74a |
| nano-positive（旧替身） | 3 | 05607d88dc3b |
| nano-positive-v2 | 3 | 5cc65887b82d |

最终主集每场景三次总分均为 **6、6、6（每次满分6）**，三项单项均为2，关键违规均为0；没有跳过或未运行的固定场景。具体来源如下，未列为最终来源的旧记录不被删去或冒充通过。

| 场景 | 最终采用批次 |
|---|---|
| E01 | run1 |
| E02 | regression |
| E03 | regression |
| E04 | regression |
| E05 | routing |
| E06 | viewer |
| E07 | regression |
| E08 | regression |
| E09 | independent |
| E10 | draft |
| E11 | regression（GPT）；Nano 变体另列 |
| E12 | regression |
| E13 | concrete |
| E14 | run1 |
| E15 | run1 |
| E16 | run1 |
| E17 | regression |
| E18 | draft |
| E19 | regression |
| E20 | run1 |
| E21 | handoff |
| E22 | run1 |
| E23 | run1 |
| E24 | handoff |
| E25 | handoff |
| E26 | run1 |
| E27 | concrete |
| E28 | regression |
| E29 | concrete |
| E30 | routing |
| E31 | routing |
| E32 | routing |
| E33 | routing |
| E34 | concrete |
| E35 | regression |
| E36 | regression |
| E37 | run1 |
| E38 | run1 |
| E39 | observation-mask |
| E40 | run1 |
| E41 | run1 |
| E42 | independent |

评分由新的隔离模型会话执行，使用同一模型而非不同模型架构交叉验证。确定性检查另外核对未批准提交、非指定服务、整版批准、提交前快照、M02 字段保留及实际 review；维护者复查低分记录、关键调用及 Nano 正向时序。原始裁判判断保留，没有手工把低分改成满分。

## 复现与证据位置

执行方式、隔离开关及限制见 [evals/README.md](../evals/README.md)。实现为 [替身](../evals/mock_mcp.py)、[执行器](../scripts/run_behavior_eval.py)、[独立评分器](../scripts/grade_behavior_eval.py)、[汇总器](../scripts/summarize_behavior_eval.py)。当前 36 项单元测试通过、0 跳过，结构／资源和 42 场景格式检查通过；这些确定性检查不替代上述实跑。

补充检查：5份文档的27个本地链接目标通过。skill-creator 的 quick_validate.py 首次受 Windows 默认 GBK 解码影响，改用 `python -X utf8 -B` 后通过；没有修改上游脚本或把该环境错误归为技能行为失败。

原始证据位于本机仓库外：

```text
C:\Users\Administrator\AppData\Local\Temp\ecommerce-behavior-20261022-01a162a8-<批次>\
  run.json / skill-manifest.json / harness/ / skill/
  E<编号>-r<1..3>/input.txt / seed.json / answer.json
  E<编号>-r<1..3>/calls.jsonl / trial.json / stdout.txt / stderr.txt
  grades/ / grades.jsonl

C:\Users\Administrator\AppData\Local\Temp\ecommerce-behavior-20261022-01a162a8-summary-final.json
C:\Users\Administrator\AppData\Local\Temp\ecommerce-behavior-20261022-01a162a8-evidence-index.json
```

汇总严格按 `run1 → regression → handoff → concrete → routing → draft → independent → observation-mask → viewer` 的顺序指定 `--run`；Nano 变体单独评分，不替换 GPT E11。最新批次整组三次替换某场景；不完整则失败，不能退选旧成功。临时原始日志不入源码仓库；本报告保留脱敏结论和版本索引。

## 未验证边界

没有真实供应商计费、真实商品保真、中文绘图质量、真实后台取消、用户视觉接受、远程 CI、部署、发布或跨宿主验证。替身只覆盖所需关键契约，并非真实 MCP 全量嵌套 schema／存储／网络实现；E26 的内置出图被物理关闭，实际诱导替代测试使用非指定 MCP 陷阱。分步恢复主要使用合成历史与单轮动作，不能当成长会话全部状态持久化已经验证。

Beads 本轮任务为 `ecommercial-images-designer-skill-bnd`。真实宿主／供应商与业务验收继续由 `ecommercial-images-designer-skill-76d` 跟踪，本次没有把该后续事项关闭。

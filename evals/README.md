# 模拟 MCP 行为评测

这是开发工具，不随纯指令 Skill 作为运行依赖安装。固定输入和量规分别在 [scenarios.json](scenarios.json)、[RUBRIC.md](RUBRIC.md)。结构校验与单元测试不能代替下面的模型实跑。

## 隔离方式

[mock_mcp.py](mock_mcp.py) 用标准输入输出实现 MCP JSON-RPC。它没有 HTTP 客户端、供应商 SDK、凭据加载或执行外部命令的入口；图像工具只返回本次测试目录内的确定性 PNG。产品、参考、生成图和 alpha 遮罩都是软件绘制的合成夹具，不是客户图片或真实供应商出图。

执行器使用已安装的 Codex CLI 和正常宿主登录，忽略用户配置，只注册本地替身；关闭插件、真实内置出图、浏览器、Shell、计算机操作、Hooks、记忆及技能自动安装。仅给这些无外部权限的替身设置工具自动批准；保留 MCP 工具路由宿主，模型文件沙箱仍为只读。`eval_io` 只能读取冻结技能包与本任务档案、保存本任务记录；看图入口限制为测试目录已知 PNG。服务替身不做网络请求。模型推理仍会使用宿主模型额度。

模型默认值、CLI 版本、隔离开关及源码摘要写入 `run.json`。每次运行冻结技能、替身、执行器和场景文件。恢复追加重复时沿用冻结夹具；不得覆盖已有试验目录。`--output` 必须位于源码仓库外。失败或中断的运行保留原始证据，不能删除后只报成功结果。

## 运行

先按 [开发验证说明](../docs/VALIDATION.md) 准备锁定环境，并确认 `codex --version` 可用；日常运行不安装依赖。以下命令在仓库根运行：

```powershell
$runRoot = Join-Path $env:TEMP ('ecommerce-eval-' + [guid]::NewGuid().ToString('N'))
uv run --frozen --no-sync --group dev python -B scripts/run_behavior_eval.py --output $runRoot --repeats 3 --workers 3
if ($LASTEXITCODE -ne 0) { throw 'Actor run incomplete; inspect trial evidence' }
uv run --frozen --no-sync --group dev python -B scripts/grade_behavior_eval.py --run $runRoot
if ($LASTEXITCODE -ne 0) { throw 'Independent grading incomplete' }
uv run --frozen --no-sync --group dev python -B scripts/summarize_behavior_eval.py --run $runRoot
if ($LASTEXITCODE -ne 0) { throw 'Rubric acceptance not met' }
```

执行器支持 `--cases E01,E11`、`--timeout 240`、`--start-repeat 2`，并发限 1–6。默认每场景 3 次，不能以一次冒烟测试代替。评分器默认只评分完成 3 次的场景；`--min-repeats 1` 仅用于过程中诊断，最终必须再评分三次完整记录。评分输入包括固定 oracle、实际回复、工具顺序及参数、返回／错误、合成图片内容对照，读取技能的长正文与二进制图片数据不重复塞入评分输入。

补充 Nano 正向确认链时，另建运行目录，使用 `--cases E11 --variant nano-approved --repeats 3`。这是 E11 的独立服务变体：当前服务版本只有 M01，完整导出、模型、输入角色与费用范围已确认；不得把它混入原 E11 的 GPT 三次结果或择优替换失败重复。它专门验证 `confirm_ecommerce_design → submit_ecommerce_design → 取图／复核`。

被测会话只得到技能名称／描述、原始用户请求和恢复夹具，按需读取技能；不提供 `should_select`、`expected_stage`、`must` 或 `must_not`。这验证目录辅助选择及加载后的行为，不等于桌面自动发现、插件安装或其他宿主兼容性验证。独立评分会话使用同一 CLI 默认模型，不复用被测会话，不向它暴露 MCP；关键失败还需维护者检查原始调用，不能只信裁判文字。

多个修复版本按先后顺序重复 `--run` 可生成明确的合并报告，例如 `--run <基线目录> --run <针对性回归目录>`。最新选定批次整组替换该场景的三次记录，不能择优混合重复；新批次不完整则整体标为未完成，不回退挑选旧成功。报告须说明哪些场景沿用基线、哪些重跑，以及技能／夹具版本差异。

## 证据及限制

每轮保存 `input.txt`、`seed.json`、`answer.json`、`stdout.txt`、`stderr.txt`、`calls.jsonl`、`trial.json` 和合成附件；按需调用 `save_design_record` 时保存实际记录。评分位于 `grades/` 及 `grades.jsonl`。运行中多次诊断评分会保留旧结果，汇总采用最后一次完整评分，不能手工覆写原始模型判断。

替身覆盖的是关键工作流契约：整版确认、输入角色及顺序、普通方案重建、套图数约束、六维复核、原任务恢复与异步／流式互斥。嵌套字段只实现所需子集，并非两个真实服务的完整协议实现。合成产物故意包含缺字、尺寸不符、重复图片或未修复文字，用于验证失败交付及不自动重画；模拟提交成功并不意味着图片设计成功。

没有真实图像供应商调用、真实客户商品保真、中文绘图质量、计费、真实取消、服务部署或用户视觉接受的验证。结果必须按 [量规](RUBRIC.md) 区分基础设施失败、夹具问题、技能行为失败及修复回归。

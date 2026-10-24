# 两个图像 MCP 的核心接口解耦与免费复验

以下保留64a本地实现阶段的验证结论；后续 v0.1.2 发行另按用户授权执行 PR／CI／评审与附件验收，准确提交见同版发行说明。

2026-10-24，Beads `ecommercial-images-designer-skill-64a`。本次仅修改工作树，未提交、推送或发布；v0.1.0／v0.1.1 标签与附件不变。成员现有 v0.1.1 不会自动取得这些改动。

## 用户决定与问题分层

初始目标是核查截图的 `reference_replica/brief` 嵌套和术语校验。当前 Nano 的扩展工具确实要求 `brief.reference_replica`；其术语规则是 `style.copywriting.terminology` 的“别名→规范词”，检查各 frame 的 title/subtitle/body。原 Skill 虽要求读取实际 schema，却缺少这两处的具体说明。合成数据重建了“缺 reference_replica”和“标题含未统一别名”两类校验错误，改用规范词且保留原术语规则可通过；没有成员原始请求，不能断言截图中具体哪个词触发错误。

用户随后明确要求两端均由 Skill 完成策划、文案、排版和完整提示词，确认后直接使用 MCP 核心生成／批量任务，不依赖服务端策划、复刻编译、resources 或 prompt 模板。本次据此取消旧扩展依赖，不继续把修补扩展字段作为生成前提。截图最后的 `PI_AI_ERROR/stream read error` 是另一层问题，本次未据此修改 Host、PI-AI 或网络配置。

## 当前接口与执行边界

| 服务 | 当前实际核心入口 | 参数和恢复 |
|---|---|---|
| Nano Banana | `submit_image_tasks`；同步 `generate_images` | 外层 checkpointer/thread_id/tasks，逐项 task_id/prompt/model/reference_images 等；每批1–20项。按原三元组 get_image_tasks/wait_image_tasks 查询图片。 |
| GPT Image 2.5 | 单图 submit_image_generation/submit_image_edit；批量 submit_image_batch/run_image_batch | 批量外层 checkpointer/thread_id/tasks/max_concurrency；逐项 task_id/operation/prompt/model/images/size 等。get_image_batch/get_batch_image_task 保留本地任务键和 provider_task_id 的区别。 |

Nano 的 reference_images/aspect_ratio/resolution/reference_sha256 不等于 GPT 的 images/size/official_options。当前 GPT 已有批量工具，不能根据旧发行包推断其不存在；某宿主只暴露单图核心工具时，才按获准范围逐图异步提交。用户对服务名的书写不用于改 Host 注册名，执行仍按实际工具声明解析同一指定服务。

两端统一保留：事实与来源、文案排版、逐图完整 prompt、图片角色／内容身份／顺序、参数与图号映射、用户确认和收费授权。部分确认仅提交对应图号。直接核心调用不意味自动授权；核心接口没有 Skill 的 user_confirmed/authorize_paid 字段，不硬塞这些参数。未确认／费用不明／输入变更则暂停提交；结果未知沿原身份查询，禁止换键或换服务重提。GPT 批次的 SUBMITTING/SUBMISSION_UNCERTAIN 同样不得自动重发。

生成后由 Skill 看实图，保存六项证据、原任务身份与文件摘要，用户决定是否接受；不依赖服务端 review_reference_replica。改稿仅更新受影响图，未改图的事实、文案、布局和来源保持；共享规范变更列出影响，冻结旧图保留旧组。

## 验证方法与实际结果

- 当前会话工具声明与安装源代码对照：Nano `0.3.1`、GPT `zhenzhen-image 0.4.0`。版本号仅表示本机包；Nano 安装目录原先有3个源码／测试修改和1份报告，本次未改它们，不把本地状态冒充全新官方发行版。
- 新增 `scripts/probe_core_image_contract.py`，分别用两个服务已有 Python 环境执行。Nano 使用显式合成设置和项目内临时目录，通过真实 FastMCP 客户端发现工具；GPT 直接发现 schema，避免启动已有批次监视器。没有读取 Host 配置或真实凭据，没有调用 tools/call、生成／提交或供应商 HTTP。
- 16项已安装契约检查通过：两端合法异步／同步批量请求、20项边界、21项拒绝、查询结构、跨服务字段／伪造批准字段拒绝，以及 Nano 图片与摘要个数不匹配拒绝。此为真实安装的 schema/Pydantic 验证，不是供应商生成成功。
- 新增16项核心工作流单元回归：默认替身不暴露 Nano 扩展，resources/prompts 列表为空；核心提交／查询、两种明确图片顺序和摘要、批量限制、身份冲突、部分确认、费用证据缺失、局部改稿保留 M02、本地六维验收、GPT 批量及命名空间隔离。两端还实际跑 JSON-RPC stdio 模拟提交／查询；替身无 HTTP、凭据或供应商 SDK。
- 全量 `scripts/check.ps1`：140 Python、15 Node，技能结构及42场景格式通过；技能创建器 quick_validate 通过。最后增加的 GPT 查询命名空间断言另经16项核心专项通过。
- 量规升级为 `2.0-core`，保留 E01–E42 编号，E29–E36 改测解耦后的等价边界。旧 `1.0` 机械规则保留，评分入口优先读运行目录冻结的 scenarios，不用新标准改写历史成绩。本轮没有运行新的模型评测，不能继承旧42场景成绩证明新 Skill 的宿主行为通过。

复现命令需在源码根执行，使用既有环境，不安装、升级或放宽权限；输出必须选新的受忽略目录：

```powershell
& 'D:/MCP/zhenzhen-nanobanana-mcp/.venv/Scripts/python.exe' -X utf8 -B scripts/probe_core_image_contract.py --server nano --output .eval-runs/new-core-check/nano
if ($LASTEXITCODE -ne 0) { throw 'Nano contract probe failed' }
& 'D:/MCP/zhenzhen-gptimagegen2.5-mcp/.venv/Scripts/python.exe' -X utf8 -B scripts/probe_core_image_contract.py --server gpt --output .eval-runs/new-core-check/gpt
if ($LASTEXITCODE -ne 0) { throw 'GPT contract probe failed' }
./scripts/check.ps1
```

路径仅指本次已核对的本机安装，并非团队必须安装到同一盘符；脚本须用对应服务已有依赖的解释器执行。探针不发生成请求，但仍须如实检查非零退出。

## 失败记录、归档和剩余边界

首轮旧扩展兼容测试有1项失败：核心版 nano-approved 夹具已移除 reference_replica，而旧历史测试仍要求导出该计划。保持核心夹具无扩展，在该旧测试中显式恢复历史计划并使用 legacy 配置，复验通过；未把扩展重新加入默认宿主。原失败日志保留。

证据集中在受忽略目录 `.eval-runs/nano-64a/`，包含修改前实时资源快照（发生在用户调整方向之前）、重建错误、已安装契约 schema／结果、原失败日志、修复日志和汇总。结束时逐文件核对压缩归档，再删除重复副本；测试临时目录位于项目 `.eval-workspaces/` 并已清理。没有在盘符根目录创建测试环境。

未验证：新量规下的模型／真实成员 Host 行为、成员原始参数与具体触发词、真实供应商出图、流读取故障恢复、图像质量和用户视觉接受。本次真实生成／提交／收费调用均为0，没有修改 Host 配置、服务安装或权限，也未覆盖既有 Release 和历史失败。

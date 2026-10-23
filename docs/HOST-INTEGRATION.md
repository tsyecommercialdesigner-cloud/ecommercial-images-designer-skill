# 真实宿主与免费 MCP 集成验证

后续Nano来源/风格措辞修复见[HOST-RETEST.md](HOST-RETEST.md)；最新[沙箱恢复与免费CLI复验](HOST-CLI-RECOVERY.md)已通过普通用户验收及资源读取，并修复恢复草案的确认状态措辞。以下保留首轮历史结果，不能用后续成功改写原失败；系统技能启动警告仍跟踪，收费出图未运行。

## 2026-10-23范围与结论

Beads父任务为76d，本轮免费验证为76d.1。源提交为`17ac23245abfb01338e9df2ca16ab74fc749b03a`；8文件技能包未改，入口SHA256仍为`9f5c2ee8c74a1910cef2d6b4cd9a97d047ecb28208a0348066343ac49b459527`。

真实Desktop会话能发现本仓库技能、读取入口及配套资源，并调用两个真实stdio MCP的免费工具。独立CLI的显式选用、隐式选择意图和免费MCP调用有实际轨迹，但配套资源读取被宿主策略拒绝，不能称完整宿主调用通过；文件恢复同样未通过。没有把12个进程正常退出写成12个行为通过。

本轮不使用真实商品或客户资料。两张256×256合成PNG由现有确定性夹具绘制函数产生：P01是灰色矩形盒体及深灰盖沿；R01为米色背景、棕橙盒体和独立顶部深棕横条。这里只给测试图分配模拟业务角色，不声称它们是用户产品实拍、真实竞品或供应商生成产物。

## 环境与隔离边界

- Windows／PowerShell；Codex CLI `0.153.0`，真实Desktop为当前会话，未取得可核实的Desktop版本号。CLI使用支持的默认模型，本次事件没有可靠模型ID，不沿用先前评测模型名。
- 本机已安装GPT Image MCP发行包`zhenzhen-image 0.4.0`、Nano Banana MCP `0.3.1`。版本来自各自现有虚拟环境的包元数据，不是上游模型版本。
- [run_host_smoke.py](../scripts/run_host_smoke.py)将完整技能复制到每个新工作目录的`.agents/skills/ecommerce-image-designer/`；没有向提示词注入技能正文或技能目录清单，没有加载mock MCP。
- 读取现有stdio启动命令/参数，实际启动两个已安装服务，不复制密钥或配置环境值。CLI忽略用户config但仍沿用现有认证与执行规则；这不是全新账户、全新安装或全局技能隔离证明。
- CLI通过`enabled_tools`只暴露GPT的`get_model_guide`及Nano的`list_models`、`inspect_design_images`、`get_ecommerce_design`。生成、编辑、提交、重试、确认工具均不在该列表。禁用插件、Apps、内置出图、浏览器、Hook和多Agent等入口，使用read-only沙箱，不放宽被拒绝的策略。
- 当前Desktop的免费策划/导出由主Agent逐项调用；这部分是授权边界约束，不冒充Desktop的技术性工具隔离。实际调用轨迹没有confirm、submit、generate、edit或retry。

发现位置及显隐式调用依据[官方Skills说明](https://learn.chatgpt.com/docs/build-skills)，MCP工具白名单依据[官方配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)。实际行为以本轮轨迹为准。

## 独立CLI：4类请求，各预先固定3次

| 场景 | 实际结果 | 结论边界 |
|---|---|---|
| explicit：`$ecommerce-image-designer`，无图首次主图，只讨论，免费查询两服务 | 3次均选择该技能并查询两个真实服务；均停在缺图/方案讨论，没有出图。入口通过原生显式机制提供，随后尝试读取本目录资源均遭拒绝。 | 显式入口和免费调用有证据；配套资源完整加载未通过。 |
| implicit：自然语言电商策划，P01商品外观夹具、R01仅风格 | 3次均尝试读取正确技能路径；均调用真实Nano看两张图，返回角色分离、文案排版及提示词草案；不借R01的商品颜色及顶部横条，不增加性能事实。技能正文读取被拒绝，回复如实声明。 | 隐式选择意图/附件/免费实图工具链有证据；不能把依据用户约束的退化执行冒充完整技能加载成功。 |
| negative：学习Python三天计划 | 3次均直接回答学习计划，无图像MCP调用、无电商流程。 | 本反例未误触发；不是通用误触发率统计。 |
| recovery：读取设计记录，仅调整M02标题拥挤，M01已接受 | 3次均说明布局阶段回退、保留M01及事实；因记录文件读取被拒绝，均未假称恢复完整方案或编造完整提示词。 | 失败反馈和停止边界符合要求；文件恢复目标未通过，原生session resume未运行。 |

实际完成12个进程、全部退出0；其中9次资源读取受阻，不能计行为通过。事件中完成的真实MCP调用共9次：3次GPT guide、3次Nano models、3次Nano inspect；事件的started/completed对不重复计数。显式r1另报告系统技能安装目录操作`os error 5`，其余11份stderr没有此记录。已保留原始结果，另做分类，不覆盖原trial文件。

宿主策略只返回`blocked by policy`，没有足够证据确定具体哪条规则。系统技能安装尝试来自CLI启动，不是本脚本修改用户目录的指令；操作被拒绝，没有宣称系统技能安装成功。问题由76d.2跟踪；本轮没有通过ignore-rules、扩大沙箱或修改用户权限来绕过。

## 当前Desktop：真实免费MCP往返

| 检查 | 实际证据 | 结果 |
|---|---|---|
| GPT配置/模型查询 | `get_model_guide`返回两个模型、key_present=true、默认reverse | 通过本地工具往返；未请求供应商出图，不证明上游鉴权/质量/速度。 |
| Nano能力查询 | `list_models`返回7标识、api_key_configured=true、upstream_verified=false | 通过本地工具往返；如实保留上游未验证。 |
| 资源读取 | 真实resources/list及reference-replica、reference-analysis资源读取成功，结合已安装类型契约核对嵌套字段 | 只证明服务资源可读。 |
| 实图查看 | `inspect_design_images`返回两张真实PNG图像内容块，Host实际观察，尺寸均256×256 | 通过免费图像读取/渲染链；不是供应商生成。 |
| 缺资料策划 | `host76d-20261023-incomplete` r1为needs_input，panels为空，列出事实/图片/目标等问题 | 通过缺输入路径。 |
| 完整普通策划 | `host76d-20261023-valid` r1为draft，包含F01、p01、冻结产品图，approved_digest=null | 通过免费保存；panels不当成完整执行prompt。 |
| 新版复刻编译 | `host76d-20261023-replica` r1，完整共享规范、单张p01、实际task.prompt及配置导出 | 通过编译往返；输出存在下述来源/措辞风险，未批准。 |
| S2布局修订 | 完整brief/frames更新后r2新digest，产品/事实/图片角色保持；旧r1仍可读取 | 通过服务端版本持久化与历史读取，不代表原生Host跨会话恢复通过。 |
| 独立导出与查询 | `export_validated_reference_replica(revision=2)`的task等于build返回；get r1/r2均tasks=[]、draft、approved_digest=null、p01未提交 | 通过只读导出一致性及未批准/未提交状态核对。 |

P01 SHA256为`e2a9f9c24328fd93764b373caaa752ca9a4609d44134c73e7e1cea5c581620b6`；R01为`42dde1b0671d698f4e149386a29bb51456c962b36818c1ff12b520da5890ce0a`。真实导出图1为R01/style_only、图2为P01/product_identity，均匹配文件SHA和冻结asset。

复刻r1 digest：`2844ab1b8763d209df8c725ce06ac157e1f7f85f45ab4af92e289395e7e41870`；r2 digest：`189fc9ab6d4fcc67a262c681c6809ed00e59705f12608b4c8ea55998d584454f`。两者不同，不能沿用版本确认；本轮两个版本从未确认。

## 发现的问题与剩余未验证项

76d.3记录真实Nano输出风险：build自动把benchmarks.source变成“用户提供的竞品实图”，与本轮合成来源不符；通用约束写“图1=style_only，只借鉴构图/表达”，而当前只允许风格，独立composition和adaptations又禁止复制原结构。它们不提升为真实事实或用户许可；需要服务维护者核对，不能直接修改导出task.prompt后绕过服务确认机制。未修改外部MCP仓库。

仍未通过/未验证：CLI完整资源加载和文件恢复；原生会话恢复、真实客户附件、干净安装与升级回滚卸载、其他Host/OS；真实服务的确认拒绝/部分确认、收费提交、上游鉴权、幂等/未知任务恢复、下载/文件修复、mask/流式实际执行、生成图文字与产品保真，以及用户最终视觉验收。GPT没有使用收费编辑入口验证图片传递，只有免费配置查询；不能将Nano的看图或编译结果外推为GPT上传已验证。

后续具体商品首先需要用户提供图片并明确真实产品/参考用途（明确文生图素材例外按Skill处理），保留事实来源，展示完整文案、排版、提示词、输入角色、实际MCP/模型/参数和费用范围，确认后才允许提交。本轮没有可供批准出图的真实商品方案，父任务76d保持未完成。

## 证据与复现

原始轨迹仅在任务专属`C:/Users/Administrator/AppData/Local/Temp/ecommerce-host-76d-20261023/`：direct-mcp-evidence.json保存真实工具响应（省略图像base64、记录图像块数），cli/*保存命令、输入、事件、stderr、回复及trial，cli-classification.json为逐次分类。公开仓库只保留本报告和复现脚本，不提交原始轨迹或本机配置。

沿用已准备的开发环境，在仓库根运行以下命令；选择一个新的仓库外目录，已有trial拒绝覆盖。需要本机已配置上述两个stdio MCP及现有Codex认证；脚本不会安装服务，不保证其他环境具备相同配置。资源受阻返回非零，进程成功不等于语义通过。

```powershell
uv run --frozen --no-sync --group dev python -X utf8 -B scripts/run_host_smoke.py --output C:/Temp/ecommerce-host-new --cli 'C:/nvm/.nodejs/codex.exe' --repeats 3 --workers 2
```

此处明确保留本报告的0.153.0入口。当前runner已新增系统包一致性guard：若共享缓存属于其他构建，上述命令会在模型启动前停止；本轮实际可用的匹配入口与后续复验见[系统技能专项](SYSTEM-SKILLS-76d4.md)，不能自动沿用PATH或重写缓存。

本轮报告是人工逐次核对，不冒充独立模型评分；也不替代[原42场景模拟评测](BEHAVIOR-EVAL.md)。没有新增收费请求，也没有用伪造确认来测试真实收费入口。

执行后复现脚本补充了stderr拒绝分类：未来资源受阻标为resource_blocked并返回非零；本轮原始trial中的completed仅指进程完成，未重写，另存分类证据。报告/脚本变更后结构与42场景格式检查、37项确定性测试、脚本AST及改动文档链接检查通过。此轮未提交或推送，未把本地新增报告当成已合入版本。

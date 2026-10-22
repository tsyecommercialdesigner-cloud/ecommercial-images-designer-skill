# 本地验证与覆盖边界

## 可复现入口

开发检查使用 Python 3.12+、uv 和 `uv.lock` 锁定的 PyYAML 6.0.3；这不是技能日常使用的运行依赖。以下 PowerShell 命令在仓库根运行，将开发环境和缓存放在独立临时位置，避免污染技能或用户配置。

首次准备：

```powershell
$env:UV_PROJECT_ENVIRONMENT = Join-Path $env:TEMP 'ecommerce-image-designer-checks'
$env:UV_CACHE_DIR = Join-Path $env:TEMP 'ecommerce-image-designer-checks-cache'
$env:PYTHONDONTWRITEBYTECODE = '1'
uv sync --locked --group dev
if ($LASTEXITCODE -ne 0) { throw 'Dependency preparation failed' }
```

日常检查沿用已准备好的环境。`--no-sync` 防止检查期间临时安装或升级依赖；失败需先回到准备步骤定位原因。

```powershell
$env:UV_PROJECT_ENVIRONMENT = Join-Path $env:TEMP 'ecommerce-image-designer-checks'
$env:UV_CACHE_DIR = Join-Path $env:TEMP 'ecommerce-image-designer-checks-cache'
$env:PYTHONDONTWRITEBYTECODE = '1'
uv run --frozen --no-sync --group dev python -B scripts/validate_skill.py --evals evals/scenarios.json
if ($LASTEXITCODE -ne 0) { throw 'Package validation failed' }
uv run --frozen --no-sync --group dev python -B -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Validator tests failed' }
```

校验器默认定位本仓库技能；可用 `--skill <完整技能目录>` 检查复制后的包，不依赖调用时的工作目录。它检查 YAML 类型与边界、名称、必需资源链接、逃逸路径、可达引用、许可证、UI 元数据与评测数据格式；不会调用 MCP、读取密钥或证明模型遵守业务约束。日志中的 PASS 也明确标为结构／资源检查。

结构失败返回非零；单元测试用临时合成包验证空描述、重名键、不安全 YAML、缺失引用、越界路径、链接逃逸、孤立引用和非法元数据等失败路径。测试产物位于本次临时目录，源码不保存真实图片或响应。

## 本轮检查记录：2026-10-22

本轮为 Windows / PowerShell 本地开发，uv 解析并复用已安装的 CPython 3.14.7；未取得或声称新的 Git 提交 SHA。未执行 Git 操作、远程同步或收费出图。依赖环境与缓存位于本次任务专属临时路径，检查时禁用字节码输出。

完整审查阶段的入口文件 SHA256：`74D77A09C0FC6506654F6A8F7498E59125DCDD725E6FCA359BA920F981476246`。这是后续行为评测修复前的快照；摘要仅标识该文件，不是完整发行包摘要或发布证明。

| 检查 | 结果与证明范围 |
|---|---|
| 仓库结构／资源校验器 | 包含 42 个评测场景；完整审查后的本地复验见文末记录。 |
| skill-creator 的 `quick_validate.py` | 通过；使用同一锁定开发环境，验证入口 frontmatter、命名及未完成骨架。它是本机附加检查，不是运行包依赖。 |
| 验证器单元测试 | 16 项全部通过、0 跳过，包括引用环不可达和实际符号链接逃逸；只证明校验器行为。 |
| 复制包与不同工作目录检查 | 通过；在临时中文／空格路径复制完整 8 文件技能包，脱离源码工作目录验证引用完整性；不等于宿主安装成功。 |
| 校验器 CLI 失败路径 | 预期失败验证通过：临时副本加入缺失资源链接后退出码为 1，原包未改动。 |
| 文档链接 | 检查本轮新增文档的本地链接目标；不推断外部站点永久可用。 |
| Nano Banana `list_models` | 只读查询成功，凭据已配置；返回 `upstream_verified=false`，未调用上游出图。 |
| GPT Image 2.5 `get_model_guide` | 只读查询成功，凭据已配置；未做模型速度、质量或收费业务验证。 |
| E01–E42 契约走查 | 下表记录条款覆盖；它不是独立模型实跑，也不填写行为通过率。 |
| 本会话技能目录发现 | 当前宿主目录已列出 ecommerce-image-designer 及本仓库入口来源；仅确认此会话可见元信息，独立干净安装与实际业务选用未验证。 |
| 真宿主选择／行为评测 | 上述完整审查阶段未运行；后续新增的本地 CLI＋模拟 MCP 实跑与覆盖边界见下文。 |
| 真实图像生成／用户视觉验收 | 未运行；本次任务是开发技能，未提供具体商品任务及其已确认方案。 |
| 跨平台／跨宿主／升级回滚卸载 | 未验证；纯指令包无运行脚本测试需求，开发校验器单独测试。 |
| 远程 CI、分支保护、评审和发布 | 未配置／未运行；本地检查入口可供后续 CI 复用，不代表门禁已生效。 |

## 契约走查映射

根据 [场景](../evals/scenarios.json) 的每条 must／must_not，人工对照以下处理路径。全部有对应条款；此结论只说明规范覆盖，不说明模型实际遵从。

| 场景 | 条款与预期路径 |
|---|---|
| E01–E03、E07–E09 | SKILL 的开始与资料边界：缺图、文生图素材例外、图片身份、竞品与事实冲突处理。 |
| E04–E06 | 图片角色表与 planning-and-prompts 的风格／结构两条轴。 |
| E10–E12 | S3 的版本、图号、完整方案确认和授权复用；部分认可不扩成全部批准。 |
| E13 | mcp-adapters 中 Nano Banana 的实际编译结果、revision/digest 和服务确认门禁。 |
| E14–E16 | S4 与 mcp-adapters 的原任务查询、未知结果停止和下载恢复。 |
| E17 | S5 与 review-and-revision 的部分交付、实图检查、用户待验收。 |
| E18–E20 | S5 的原因回退矩阵与 review-and-revision 的影响范围和底图编辑。 |
| E21–E22 | SKILL 的阶段范围、MCP 依赖按阶段检查及缺失工具反馈。 |
| E23 | SKILL 中外部参考文字不构成授权。 |
| E24–E25 | description 与典型边界对通用绘图、视频和运营的消歧。 |
| E26–E28 | S4 与 mcp-adapters 限定两个指定服务：不可用时保留方案、仅一项可用时择一、原任务未知时不跨服务重提。 |
| E29–E33 | 实际提示词导出、图像输入角色、类型／数量限制与整版确认作用域。 |
| E34–E36 | 完整改稿保留、共享风格的全组影响、复刻六维证据与任务／文件绑定。 |
| E37–E39 | GPT Image 实际尺寸、分组／流式模式与 mask 对首张底图的约束。 |
| E40–E42 | 停止条件、输入内容变更、提交前快照与未知任务期间的反馈计划。 |

真实宿主评测的输入、重复次数、评分阈值和证据要求见 [RUBRIC.md](../evals/RUBRIC.md)。其中需要附件的场景必须补齐允许使用的隔离图片，否则按未运行记录；不得伪造图片观察或上游响应。

本地开发任务为 Beads `ecommercial-images-designer-skill-hxn`；真实宿主／生成验收登记为 `ecommercial-images-designer-skill-76d`。未把后续业务验收状态写成已完成。

用户补充指定 `zhenzhen-gptimagegen2.5-mcp` 和 `zhenzhen-nanobanana-mcp` 后，任务 `ecommercial-images-designer-skill-rza` 同步限制了入口、适配、来源边界与使用说明，增加 E26–E28。更新后结构／引用、quick_validate 和 16 项验证器测试再次通过；未开展收费绘图。

## 完整审查复验：2026-10-22

任务 `ecommercial-images-designer-skill-k9n` 的问题、全部需求覆盖矩阵和 MCP 契约来源见 [SKILL-REVIEW.md](SKILL-REVIEW.md)。已修复9类适配／流程缺口，新增 E29–E42，现共42个场景。更新后的结构、引用及场景格式检查通过，skill-creator 校验通过，16项校验器测试全部通过、0跳过；当前复制包在中文／空格的仓库外目录校验通过，5份文档的本地链接复查通过。

本轮重新调用两个服务的只读能力入口，并读取 Nano 的整套与复刻资源，核对必要的本机安装源码。没有调用 plan、confirm、review 或任何收费生成工具，因此不将本次审查记为真实提交链路、模型行为或用户视觉验收通过。Nano 普通入口无法导出完整执行提示词是服务能力限制，技能已明确不伪造该结果，改由符合需求的可导出入口或经用户同意的另一指定服务处理。

## 模拟 MCP 实际行为评测追加：2026-10-22

后续任务 `ecommercial-images-designer-skill-bnd` 已完成实际 CLI 模型评测及修复回归，详见 [完整报告](BEHAVIOR-EVAL.md) 和 [复现方法](../evals/README.md)。固定42场景每个3次，最终组合回归126条，三项均分均2.00/2、关键违规0；额外Nano正向确认／提交／复核变体3次通过。包含被替代批次共记录285次模型运行，未挑选同场景的成功重复，也不声称最终同一快照重跑了整个主集。

实际配置为Windows、CPython 3.14.7、Codex CLI 0.153.0、CLI默认gpt-6-astra（reasoning none）。全部图像服务是无网络无供应商凭据的本地替身，没有收费出图；真实供应商与用户视觉验收仍未验证。

当前入口SHA256：`9f5c2ee8c74a1910cef2d6b4cd9a97d047ecb28208a0348066343ac49b459527`；8文件技能包与最新冻结包一致。结构／资源／42场景格式检查通过；确定性测试新增协议UTF-8、图像角色、确认、改稿、任务恢复、mask和评分失败路径，现36项通过、0跳过。新增脚本仅为开发评测工具，不是技能运行依赖。

后续交付准备新增 [Windows CI](../.github/workflows/windows-ci.yml) 和 [统一本地检查](../scripts/check.ps1)，使用独立CPython 3.12.14环境复验36项通过、0跳过。入口摘要未变；修复历史保留在 [CHANGELOG.md](../CHANGELOG.md)。远端PR／CI／合并／dev快进尚因当前会话禁止Git操作而未执行，状态与验证边界见 [交付说明](DELIVERY.md)。

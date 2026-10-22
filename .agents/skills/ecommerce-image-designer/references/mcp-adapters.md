# 图像 MCP 选择、提交与恢复

选工具、提交或恢复时阅读。下面的工具名来自 2026-10-22 本会话实际工具声明与只读能力查询，不是所有宿主的通用 API。每次使用先核对本会话的工具、参数 schema 和服务要求，不能把文档示例当作已连接证明。

## 指定服务与选择规则

图像生成和编辑仅由以下两个 MCP Server 执行：

| 用户指定的 MCP Server | 本会话实际工具前缀 |
|---|---|
| `zhenzhen-gptimagegen2.5-mcp` | `mcp__zhenzhen_gptimagegen2_5_mcp__` |
| `zhenzhen-nanobanana-mcp` | `mcp__zhenzhen_nanobanana_mcp__` |

工具名称以宿主实际暴露为准，表中的前缀不是第三个服务。根据任务和可用能力选择其中一个，未指定具体服务时可推荐；不强制同时调用两者。用户选定服务后不能静默切换。指定服务不可用／能力不足不构成使用其他 MCP、内置生成工具或直连 API 的许可。图片查看可以使用宿主免费查看能力，不受此生成服务范围限制。

## 两个服务共用的调用契约

1. 仅发现指定两个服务的能力查询、图像输入、生成／编辑、异步查询和产物获取方式。只做策划时不强制连接；要出图但两个服务均不可用时，保留方案和提示词，报告缺少的能力，不伪造工具名、不自动安装服务。
2. 确认支持当前模型、图像输入方式、比例／尺寸、图像数量与可访问输出。凭据仅检查名称和是否配置，不读取或显示密钥值。MCP 服务端读不到宿主附件时，先取得用户允许的传递方式，不能编造本地路径或静默上传到别的图床。
3. 显示从指定两个服务中选择的服务与模型。更换服务、模型或上传范围是方案差异，须符合既有确认与授权。可依据能力推荐，不把供应商宣传当作独立实测；某个服务已提交且结果不明时，也不能换到另一个指定服务重提。
4. 建立“设计版本＋图号＋输入图片顺序＋准确提示词＋非秘密参数→工具调用”的映射。真实图片通过 schema 的图像字段传入。上游接受风格／结构图的方式与产品保真能力有限，参考过多会混淆时先讨论输入取舍或拆分任务，不静默丢图。
5. 执行前检查 SKILL.md 的 S3 条件，并满足服务本身的确认机制。每张图的幂等身份在提交前确定，提交后立即记录原任务 ID。
6. 查询或分段等待已有任务；遵守服务返回的轮询建议，单次等待尽量不超过 60 秒，长任务给用户有意义的进展。等待结束不表示后台已取消。
7. 以实际图片文件／可访问图片为取图完成证据；保留部分成功与下载失败。转到 S5 看图和用户验收。

提交前把实际工具名、全部非秘密参数、输入图内容身份和稳定幂等键写入档案。响应同时检查 `isError`、结构化数据与图片内容；有些工具会把部分成功和失败一起返回，不能因顶层报错就丢掉已完成产物。优先读取 `structuredContent`，必要时解析文本 JSON；不能把说明文字中的示例当真实产物。

## Nano Banana 电商工作流适配

本会话前缀为 `mcp__zhenzhen_nanobanana_mcp__`。能力和配置入口为 `list_models`；查看图片为 `inspect_design_images`，参数是 `images` 图片路径／直链数组。该查看入口不出图；返回的图片须由 Host 实际观察。

常规主图／详情页／SKU 采用服务的设计流程：

| 环节 | 实际工具与关键约定 |
|---|---|
| 底稿 | `plan_ecommerce_design` 接收 `design_id`、`expected_revision`、完整 `brief`，以及可选逐图 `edits`。新建版本期望为 0，修改用服务返回的当前版本。 |
| 输入 | `brief.kind` 为 main / detail / sku；提供本商品图片、实际观察、有来源的已核实事实、参考分析及其选择。核心字段见下文，完整嵌套 schema 从实际资源／工具读取，不猜字段。 |
| 研讨 | 处理服务返回的 `needs_input` 和问题；核对逐图文案、排版、数量及模型。服务默认图数可能和用户方案不同，需调整。 |
| 读取 | `get_ecommerce_design` 用 `design_id` 和可选 `revision` 取得实际保存的 design、tasks 和产物；它不导出普通方案的完整执行提示词。不可将 panels 当完整 task.prompt。 |
| 整套提示词 | `build_product_suite_prompts`／`export_product_suite_prompts` 返回 `design`、`style_digest`、`prompts`。先读 `nanobanana://templates/product-suite` 和实际的 `nanobanana://templates/styles`、`nanobanana://templates/main`、`nanobanana://templates/detail`、`nanobanana://templates/sku`，或等价 prompt 指引。 |
| 确认 | 用户确认了服务当前整个版本后，`confirm_ecommerce_design` 传服务的 `design_id`、`revision`、`digest`、`user_confirmed=true` 和用户证据 `confirmation_note`。该工具无 panel_ids；不能用仅一张图的认可批准整版。 |
| 提交 | `submit_ecommerce_design` 传相同 `design_id`、`revision`、`digest`、已确认 `panel_ids`；明确取得本次收费授权后才传 `authorize_paid=true`。 |
| 查询 | 保存返回的 `checkpointer`、`thread_id`、各 `task_id`，用 `get_image_tasks` 查询，或 `wait_image_tasks` 等待；`get_ecommerce_design` 读取已落盘产物。 |

服务端 `revision`、`digest` 必须原样保存，不能在 Agent 的设计档案中自行算一个来冒充。文案或提示词有改动，要重新保存、核对和确认当前服务版本。不要用 `submit_image_tasks` 或 `generate_images` 绕过该服务对电商设计的确认与收费授权。

### 入口选择与输入图片角色

| 实际需求 | 正确路径与边界 |
|---|---|
| 普通单类草案 | `plan_ecommerce_design` 可免费研讨和改稿。当前工具不提供普通方案的完整执行 prompt 导出，本技能要求保存并展示完整执行提示词，故不能假称已导出后直接提交。若无符合需求的可导出 Nano 入口，报告限制，在用户同意后用 GPT Image 执行自行构造并确认的提示词；用户坚持该入口则保留待执行，不绕门禁。 |
| 完整主图＋详情＋SKU | `build_product_suite_prompts`，共享规范以 `brief.suite.style` 为唯一来源，非 `brief.style`。当前要求三类齐全：1–8 主图、8–15 详情、每个真实 SKU 一图；不能为套模板虚构 SKU 或擅加图数。 |
| 参考图风格迁移或风格＋结构迁移 | 先读 `nanobanana://templates/reference-replica` 和 `nanobanana://templates/reference-analysis`，用 `build_reference_replica_prompts`／`export_validated_reference_replica`。`scope=series` 可做单图／同类系列；整套 scope 则遵守三类完整约束。只借鉴风格时，目标 composition 自行适配，不借用未获准的原画面结构。 |
| 仅结构参考，禁止借鉴其配色与字体 | 先转译成已确认的目标构图／布局指令，参考图只用于分析，不把它放入固定 style_only 槽位。若需图像级结构输入且现入口不能准确表达角色，说明限制，经用户确认选择支持该映射的指定服务。 |

普通 plan 与 suite 的模型 `reference_images` 仅来自真实产品图或各 SKU 图，`benchmarks.source` 不是上传参数。不要把竞品图塞进 `product_images` 来“传参考”。复刻入口的导出 `input_images` 固定图1=`style_only`、图2起=`product_identity`（一张风格＋1–3张本商品图）；必须使用导出顺序与 SHA256，不能套用产品图在前的通用顺序。使用仅风格／仅结构／两者的业务分类时，还要核对具体入口是否表达得出用户允许的用途。

导出后逐项保存 `prompts[].task.prompt`、实际模型／接口／画幅／输入图顺序，以及用户图号到 `panel_id` 的映射。`style_digest` 只标识共享风格，不能当 `design.digest` 用于确认。服务可根据分辨率选择模型变体，要展示实际执行配置，不能只展示 brief 中的基础模型名。普通 plan 当前 `detail_count` 限 8–15，其他图数不能套入；suite 也不是任意组合的组图入口。遇到范围不符先报告，再讨论适合的指定服务，不扩改用户任务。

### 核心嵌套字段与改稿

- `facts` 每项包含 `fact_id`、`label`、`value`、`source`，可带 `category`（benefit/material/size/usage/trust/offer）及 `pain_point`。这些是当前产品的可追溯依据，不抄竞品。
- `benchmarks` 每项包含 `source`、`visual_focus`、`hierarchy`、`copy_approach`、`strengths`、`weaknesses`、`adaptation`。仅记录用户已提供资料的分析；不用参考时须依据用户决定填写 `reference_choice=skip` 与 `reference_reason`。
- SKU `variants` 每项需要 `sku_id`、`label`、真实 `attributes`、该版本 `product_images`；`fact_ids` 仅引用本 SKU 可用事实。不能用其他 SKU 图代替。
- 普通 `edits` 每项为 `panel_id`、`headline`、`body`、`visual`、`layout`、`fact_ids`。服务会从完整 brief 重建默认全部 panels，再应用这些 edits；新版本须带回所有保留的定稿 edits，不能仅传被改图而丢掉其他定稿。
- suite／reference_replica 改相应完整 `style/frames`，不要用普通 edits。新版本展示全部差异；共享 style 变更影响全部关联图。已接受旧产物保留，但新服务版本仍需合法确认。

只确认部分图时，先检查能否建立符合类型约束的独立执行方案，重新展示并取得确认；若不能，说明限制并经用户同意改用另一指定服务。只有用户确认了整个服务版本后，才可调用确认接口并通过 `panel_ids` 选择执行子集。每次提交不超过 20 项，更多项分批沿用同一批准版本和原任务映射。

服务将设计提交映射为 `checkpointer=ecommerce-design`、`thread_id=design_id`、`task_id=r{revision}-{panel_id}`；实际以返回值为准。重复查询继续沿用原身份，不能换设计编号重试。`failed`、`unknown`、取消或超时先查询；`recovering` 表示恢复原响应，不是重画。只有服务明确返回 `safe_to_retry=true` 且属于授权内的安全阶段，才考虑用 `retry_image_tasks` 沿原身份恢复；损坏文件修复需其 `repair_files` 机制，保留原文件。

若只有概念素材、缺少此策划器要求的真实产品信息，不能伪造事实来通过校验；保留草案，说明该入口限制。若另一指定服务 `zhenzhen-gptimagegen2.5-mcp` 支持任务且已连接，可在展示变更并取得确认后使用；否则报告缺口。竞品复刻工具若适用，应先读服务对应模板并检查实际编译结果，仍不能复制竞品事实或跳过本技能确认。

复刻生成后，按 `get_ecommerce_design` 返回的真实 task_id、路径及 SHA256 实际看图，再用 `review_reference_replica` 保存六维证据；不能把 Server 的结构校验或 `agent_passed` 当用户已经接受。局部编辑任务还要确认服务能将正确底图作为编辑输入；固定产品身份槽位的复刻／suite 不能自动冒充局部修改入口。能力不符就先说明，再讨论 GPT Image 编辑路径。

## GPT Image 2.5 MCP 适配

本会话前缀为 `mcp__zhenzhen_gptimagegen2_5_mcp__`。只读入口 `get_model_guide` 返回模型与凭据配置状态。当前声明有 `gpt-image-2.5-sunburst` 和 `gpt-image-2.5-flare`；供应商对编辑精度／速度的描述未在本项目实测，不写成速度或质量保证。

| 情形 | 实际工具与参数 |
|---|---|
| 有图的首次创作／后续编辑 | 优先 `submit_image_edit`，传 `images`、完整 `prompt`、明确 `model`、稳定 `idempotency_key` 及支持的 `size`／其他参数。首次创作中使用编辑端点不改变它在业务上仍属首次生成。 |
| 明确文生图素材 | `submit_image_generation`，传 `prompt`、`model`、稳定 `idempotency_key` 和已确认参数，不伪造参考图。 |
| 已有任务 | `get_image_task(task_id, save=true)` 查询并取得文件；或 `wait_image_task`，使用原 `task_id` 和原输出目录。 |
| 有图片 URL 但下载失败 | 使用 `download_image(url, output_dir)` 恢复文件；不重新绘图。 |

`images` 支持格式、`size` 范围、质量与分组参数以实际 schema 为准。`group` 默认 reverse；仅用户明确要求官转时用 official，并核对 `official_options`。分组声明不代表工具会替用户更改密钥后台分组。

确认前校验以下当前契约，不能让自动参数修正发生在批准之后：

- GPT Image 使用 `size="宽x高"` 或 `auto`，没有 Nano Banana 的 `aspect_ratio`／`resolution` 参数。显式尺寸两边为 16 的倍数、最大边≤3840、长宽比≤3:1、总像素 655360–8294400。用户指定 750px 或超长详情页时，先讨论受支持画布、拆屏或可执行的后处理方案；不静默改尺寸或裁掉内容。
- 输入支持本机绝对路径、公开 HTTP(S) 图片或 data URL，PNG/JPEG/WebP；当前最多16张、合计100MiB。编辑至少一张底图；记录实际顺序和内容身份。首轮仍受本技能用户图片条件限制，不能因 API 允许空 images 就无图生成商品。
- `quality` 在 reverse 下仅 auto/low/medium/high；xhigh/max 需明确的 official 分组。不要为获得参数自行切换分组。数量扩展 `n` 位于 `official_options`，不是顶层字段；多图逐项用稳定身份并保存结果 index 与图号的关系。
- `official_options.stream=true` 与 `submit_image_generation`／`submit_image_edit` 异步提交互斥。若用户选择流式，则先确认完整配置，再用本服务同步 `generate_image`／`edit_image`；不能提交失败后自动切路径重发。`partial_images` 依赖流式。
- `mask` 通过 `official_options.mask` 传入，仅适用于编辑，PNG、<4MiB、有 alpha 通道且与**首张底图**同尺寸。局部修改且要求其他保持时，优先保留受支持的底图尺寸；底图尺寸不受支持时，先说明输出画布或缩放差异，讨论恢复合适底图／接受尺寸变化后再确认，不能套用旧任务尺寸静默放大。透明背景的输出须 PNG/WebP，压缩参数须显式 JPEG/WebP。缺少 mask 不假称实现像素级局部保护。

具体调用形式如 `get_image_task({task_id: 原ID, save: true})`；等待时显式设置 `wait_image_task` 的 `timeout_seconds`，Nano Banana 则用 `wait_timeout_seconds`，避免混用字段。一次等待到期只结束等待。新的已确认改稿使用新的版本／图号幂等身份，恢复旧任务保持原身份；旧结果未知时不能借“改稿”先重复执行相同或相关收费请求。

该 MCP 没有电商方案确认工具时，由本技能的版本快照和真实用户确认记录承担提交检查。`SUCCESS`／`COMPLETED` 还须结合 `files`、`save_status`、`download_errors` 检查产物是否完整；`UNKNOWN` 或提交后无任务 ID 时停止自动提交，保留幂等键与请求时间，报告需核对的状态。相同幂等键有助于复用，但不能将它当作无条件重发收费请求的授权。

## 缺少能力与结果不明

两个指定服务均不可用或均不支持所需图像输入、尺寸或产物获取时，保留已完成的策划、文案、排版与提示词并报告具体缺口。服务没有可用查询能力且提交结果不明时，停止自动重试，说明已知与未知情况；若不能取得实际产物，交付状态仍是未完成或部分完成。另一个指定服务可用也不能替代对原未知任务的恢复核对。

本技能不直接编写绕过 MCP 的 HTTP 请求，不读取服务配置中的密钥，也不会把其他生成工具冒充 MCP 验证结果。

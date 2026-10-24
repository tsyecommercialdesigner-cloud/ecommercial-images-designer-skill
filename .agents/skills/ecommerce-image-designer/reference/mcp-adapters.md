# 图像 MCP 选择、提交与恢复

选工具、提交或恢复时阅读。下面的核心工具名于 2026-10-24 按本会话实际声明核对，历史能力查询另存记录，不是所有宿主的通用 API。每次使用先核对本会话的工具、参数 schema 和服务要求，不能把文档示例当作已连接证明。

## 指定服务与选择规则

仅查询能力／配置状态时，使用入口已直接索引的状态契约 status 分支。每次工具返回绑定一项 capabilities，模型 ID 复制实际目录；query_succeeded、configured 与 upstream/performance 分开，免费目录查询后两项均 not_tested。该模式没有自由就绪摘要、历史连通判断或选型推荐；实际选择／执行另按以下流程及 S3 授权处理。

Skill 负责两端统一的选题、事实核对、文案、布局、术语和完整提示词；用户确认后只调用以下两个服务的核心生成／编辑、实际批量提交和任务查询取图接口。两端均不依赖服务端策划、复刻编译、resources 或 prompt 模板，产品事实与确认档案由 Skill 保留。

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
5. 执行前检查 SKILL.md 的 S3 条件，用户确认和费用授权由本技能档案承载。每张图的幂等身份在提交前确定，提交后立即记录原任务 ID。
6. 查询或分段等待已有任务；遵守服务返回的轮询建议，单次等待尽量不超过 60 秒，长任务给用户有意义的进展。等待结束不表示后台已取消。
7. 以实际图片文件／可访问图片为取图完成证据；保留部分成功与下载失败。转到 S5 看图和用户验收。

提交前把实际工具名、全部非秘密参数、输入图内容身份和稳定幂等键写入档案。响应同时检查 `isError`、结构化数据与图片内容；有些工具会把部分成功和失败一起返回，不能因顶层报错就丢掉已完成产物。优先读取 `structuredContent`，必要时解析文本 JSON；不能把说明文字中的示例当真实产物。

## Nano Banana 核心生成与批量任务适配

本技能自行策划、统一术语、保存文案排版和构造完整提示词。仅依赖核心图片生成／编辑、批量提交及原任务查询取图；不调用 `plan_ecommerce_design`、`build_*_prompts`、`export_*`、`confirm_ecommerce_design`、`submit_ecommerce_design` 或 `review_reference_replica`，也不依赖 Server 的 resources／prompt 模板。无需把方案转换成 `brief/reference_replica/suite`。扩展工具是否存在不影响本流程；核心工具名称或 schema 变化时，以当前声明重新适配并展示差异，不能猜参数或自动换服务。

| 环节 | 核心工具与实际字段 |
|---|---|
| 异步提交（优先） | `submit_image_tasks({checkpointer, thread_id, tasks})`，每批1–20项，立即返回已有／已排队任务。 |
| 同步生成 | `generate_images({checkpointer, thread_id, tasks, wait_timeout_seconds})`；等待到期不取消后台。同一请求未知时不能再切异步重提。 |
| 查询与取图 | `get_image_tasks({checkpointer, thread_id, task_ids})`，或 `wait_image_tasks` 加 `wait_timeout_seconds`；用返回 `tasks[].images[].path/sha256` 获取、实际查看产物。 |
| 安全恢复 | `retry_image_tasks` 仅在查询确认 `safe_to_retry=true`、原授权仍有效时沿原三元组恢复；文件损坏另需 `repair_files=true`，保留原件。 |

`tasks[]` 每项需要 `task_id` 和**完整原样绘图提示词** `prompt`；可带当前 schema 支持的 `model`、`api_format`、`endpoint`、`aspect_ratio`、`resolution`、`reference_images` 和等长同序的 `reference_sha256`。提示词、尺寸和所有非秘密参数须在 S3 展示确认；接口不会替你补商品事实、平台要求或图像角色，也没有 `authorize_paid`／`user_confirmed` 参数。真实用户确认和费用授权写入 Skill 档案，不把这些字段硬塞进工具。

有输入图时使用 `reference_images`；按批准的顺序在 prompt 中逐张说明产品身份、风格／结构参考、编辑底图用途。核心接口没有固定的 `style_only` 槽位，不继承旧复刻工具的图序限制。仅结构参考可转译成布局文字而不上传；确需上传时明确禁止借用其颜色、字体和商品事实，并告知生成结果仍须视觉核对。输入路径／直链必须可读，不为传图虚构路径、搬运私有文件或静默外传。

按当前接口 `resolution={width,height}` 只按长边选择基础／2k／4k模型（≤1024／≤2048／更大），不保证输出精确像素，也不替代 `aspect_ratio`。提交前核对实际模型变体和用户同意的画幅；有图时 endpoint 不得强用 generations。能力目录工具若存在可辅助只读核对，但不是策划／生成的必经流程；用户只询问状态时，仍按状态契约如实报告查询证据和未验证项。

下列仅说明字段层级；`已确认提示词`及图片路径必须替换为当前完整执行快照，不可原样提交：

```json
{
  "checkpointer": "ecommerce-image-designer",
  "thread_id": "product-task-unique",
  "tasks": [{
    "task_id": "v3-M01",
    "prompt": "已确认提示词：图1为本商品外观依据；图2仅配色参考。准确文案、版式和禁止迁移的竞品内容须写全。",
    "model": "nano-banana-pro",
    "api_format": "auto",
    "endpoint": "auto",
    "aspect_ratio": "1:1",
    "reference_images": ["P01_ABSOLUTE_PATH", "R01_ABSOLUTE_PATH"]
  }]
}
```

`checkpointer/thread_id/task_id` 由 Skill 在提交前冻结，逐项绑定“设计版本、业务图号、完整 prompt、输入顺序和内容摘要、实际参数”。例如 `v3-M01` 只是命名示意；重试必须沿原身份，已确认的新改稿才使用新版本任务身份。每批≤20，超过则按已批准图号分批，禁止擅加图或 SKU。部分确认只提交对应图号，不需要批准整个服务端设计；未批准和已冻结图保留原稿。

服务不负责本技能的用户确认门禁，不能把直接出图理解为省略 S3。生成后的产品保真、风格／结构许可、类目适配、布局光线、逐字文案和事实六项由 Skill 实际看图并记录；无需服务端复刻评审工具。满意仍以用户接受为准。

旧档案若带 `design_id/revision/digest` 或 `reference_replica/suite`，保留原记录，不把 Server digest 当新快照摘要。不为执行新任务重走旧编译器。旧请求状态不明时先用档案保存的核心任务三元组查询；只有 design_id 而无可用任务身份时，报告缺口、暂停重复执行并由服务维护者核对，不能换新编号重画。

### 校验失败与改稿

- 调用参数按当前工具 schema 构造；核心任务不接收 `brief/reference_replica/style/frames`。看到这些字段相关错误，先核对是否误走了扩展策划工具，不能继续修补其模板以作为本流程前提。
- 文案术语、禁用词和事实在 Skill 的确认版中统一，保留来源与用户决定。旧服务的 `terminology` 是“别名→规范词”，而不是允许词清单；历史错误照实保留。新流程不会提交这一字段，但也不能为了绕过错误删除用户既定用词规则或事实。
- 局部改稿仅修改被点名图的 prompt／参数，保留其他已定稿图和全部事实、来源、布局与图片映射；共享规范变化列出受影响图，重新展示新增差异。用户明确冻结旧图时保留旧组，不重复问是否重画。

## GPT Image 2.5 MCP 适配

本会话前缀为 `mcp__zhenzhen_gptimagegen2_5_mcp__`。只读入口 `get_model_guide` 返回模型与凭据配置状态。能力查询不是执行前置步骤；按本轮工具 schema 和已核对模型构造核心请求。当前声明有 `gpt-image-2.5-sunburst` 和 `gpt-image-2.5-flare`；供应商对编辑精度／速度的描述未在本项目实测，不写成速度或质量保证。

| 情形 | 实际工具与参数 |
|---|---|
| 有图的首次创作／后续编辑 | 优先 `submit_image_edit`，传 `images`、完整 `prompt`、明确 `model`、稳定 `idempotency_key` 及支持的 `size`／其他参数。首次创作中使用编辑端点不改变它在业务上仍属首次生成。 |
| 明确文生图素材 | `submit_image_generation`，传 `prompt`、`model`、稳定 `idempotency_key` 和已确认参数，不伪造参考图。 |
| 多图核心批量 | 当前有 `submit_image_batch({checkpointer, thread_id, tasks, max_concurrency})` 和同步 `run_image_batch`；每批1–20项，默认并发5。每项为 `task_id`、`operation=generate/edit`、完整 `prompt`、`model` 及本工具支持的图片／参数。 |
| 批次恢复 | `get_image_batch({checkpointer,thread_id})` 读本地记录；`get_batch_image_task` 加原 `task_id` 查询单项。保存本地任务键与 `provider_task_id` 的区别；`SUBMITTING/SUBMISSION_UNCERTAIN` 不得自动重提。 |
| 已有任务 | `get_image_task(task_id, save=true)` 查询并取得文件；或 `wait_image_task`，使用原 `task_id` 和原输出目录。 |
| 有图片 URL 但下载失败 | 使用 `download_image(url, output_dir)` 恢复文件；不重新绘图。 |

`images` 支持格式、`size` 范围、质量与分组参数以实际 schema 为准。`group` 默认 reverse；仅用户明确要求官转时用 official，并核对 `official_options`。分组声明不代表工具会替用户更改密钥后台分组。

确认前校验以下当前契约，不能让自动参数修正发生在批准之后：

- GPT Image 使用 `size="宽x高"` 或 `auto`，没有 Nano Banana 的 `aspect_ratio`／`resolution` 参数。显式尺寸两边为 16 的倍数、最大边≤3840、长宽比≤3:1、总像素 655360–8294400。用户指定 750px 或超长详情页时，先讨论受支持画布、拆屏或可执行的后处理方案；不静默改尺寸或裁掉内容。
- 输入支持本机绝对路径、公开 HTTP(S) 图片或 data URL，PNG/JPEG/WebP；当前最多16张、合计100MiB；Nano 核心每项最多4张，不混用两者上限。编辑至少一张底图；记录实际顺序和内容身份。首轮仍受本技能用户图片条件限制，不能因 API 允许空 images 就无图生成商品。
- `quality` 在 reverse 下仅 auto/low/medium/high；xhigh/max 需明确的 official 分组。不要为获得参数自行切换分组。数量扩展 `n` 位于 `official_options`，不是顶层字段；多图逐项用稳定身份并保存结果 index 与图号的关系。
- `official_options.stream=true` 与 `submit_image_generation`／`submit_image_edit` 异步提交互斥。若用户选择流式，则先确认完整配置，再用本服务同步 `generate_image`／`edit_image`；不能提交失败后自动切路径重发。`partial_images` 依赖流式。
- `mask` 通过 `official_options.mask` 传入，仅适用于编辑，PNG、<4MiB、有 alpha 通道且与**首张底图**同尺寸。局部修改且要求其他保持时，优先保留受支持的底图尺寸；底图尺寸不受支持时，先说明输出画布或缩放差异，讨论恢复合适底图／接受尺寸变化后再确认，不能套用旧任务尺寸静默放大。透明背景的输出须 PNG/WebP，压缩参数须显式 JPEG/WebP。缺少 mask 不假称实现像素级局部保护。

具体调用形式如 `get_image_task({task_id: 原ID, save: true})`；等待时显式设置 `wait_image_task` 的 `timeout_seconds`，Nano Banana 则用 `wait_timeout_seconds`，避免混用字段。一次等待到期只结束等待。新的已确认改稿使用新的版本／图号幂等身份，恢复旧任务保持原身份；旧结果未知时不能借“改稿”先重复执行相同或相关收费请求。

GPT Image 与 Nano 一样，由本技能的版本快照、真实用户确认和费用授权记录承担提交检查，不依赖服务端的策划／导出／确认／评审扩展。当前 GPT 已暴露上述核心批量工具，批量项使用 images、operation、size、group／official_options；不能混用 Nano 的 reference_images、aspect_ratio、resolution 或 reference_sha256。批次外层接收 max_concurrency；每项不接收单图 idempotency_key，固定三元组由批次维护幂等。某宿主未暴露批量入口时，可在原确认范围内逐图异步提交，记录各图幂等键与返回ID；不强制依赖扩展计划器。official_options.n 只在实际 schema 支持且已确认时使用，记录结果 index 与图号映射，不静默改变分组或数量。`SUCCESS`／`COMPLETED` 还须结合 `files`、`save_status`、`download_errors` 检查产物是否完整；`UNKNOWN` 或提交后无任务 ID 时停止自动提交，保留幂等键与请求时间，报告需核对的状态。相同幂等键有助于复用，但不能将它当作无条件重发收费请求的授权。

## 缺少能力与结果不明

两个指定服务均不可用或均不支持所需图像输入、尺寸或产物获取时，保留已完成的策划、文案、排版与提示词并报告具体缺口。服务没有可用查询能力且提交结果不明时，停止自动重试，说明已知与未知情况；若不能取得实际产物，交付状态仍是未完成或部分完成。另一个指定服务可用也不能替代对原未知任务的恢复核对。

本技能不直接编写绕过 MCP 的 HTTP 请求，不读取服务配置中的密钥，也不会把其他生成工具冒充 MCP 验证结果。

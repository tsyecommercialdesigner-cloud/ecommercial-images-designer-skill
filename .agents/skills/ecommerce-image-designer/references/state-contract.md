# 可校验的未确认设计状态 v2

用于未确认的单图策划草案、免费能力查询和单图纯文字局部恢复，不适用于已经获准执行的 S4、非电商任务或仅问一个概念的咨询。它取代这些分支里反复重述的台账、提示词、问题清单：**最终答复只交付一个 JSON 对象**（可包一个 json 代码块，不加前后散文）。这个对象本身就是完整、可独立审阅的结构化提示词草案，不是 MCP 参数，也不是执行授权。套图仍按逐图方案流程，每份单图草案分别绑定图号，不能用这份单图契约批准多个图；本版不宣称完成套图状态校验。

字段有两种来源：`state` 从本轮用户原话、档案实际字段及工具返回复制；`proposal` 才是本轮设计建议。缺失值用 JSON `null`；来源性质缺失用 `unknown`。不要在任意备注、文案、标题中另行重述来源、服务就绪或冻结状态。依赖关系以 ID 引用同一状态，不在第二份自由提示词里重新填值。

## 固定形状

```json
{
  "contract": "ecommerce-design-state/v2",
  "mode": "revision",
  "validation": "pending",
  "state": {
    "images": [],
    "facts": [],
    "capabilities": [],
    "locked_images": [],
    "edit_images": [],
    "baseline": {
      "title": null, "subtitle": null, "labels": null, "footnote": null,
      "canvas": null, "kind": null, "product_count": null,
      "view": null, "style": null, "delivery": null, "previous_layout": null
    }
  },
  "proposal": {
    "canvas": null,
    "copy": {"title": null, "subtitle": null, "labels": null, "footnote": null},
    "layout": [],
    "appearance": {"background": null, "typography": null, "lighting": null},
    "reference_style": []
  },
  "next": {
    "rollback_stage": "S2",
    "stage": "S3", "confirm_images": [], "missing_fields": [],
    "execution": "not_authorized"
  }
}
```

所有键均需保留，不增设 `summary`、`questions`、`notes` 或第二个提示词字符串。各数组用真实信息填写，不照抄空示例。`validation` 只能是 `pending`：没有真的运行校验，不声称已通过。

### state 的条目

- `images` 每项：`{"id":"图像ID","source":"已知文件或附件引用","role":"product","provenance":"unknown","reference_use":"none","drawing_use":"undecided","input_index":null}`。source 保存实际路径／附件引用，档案未载则 null，不猜文件；它与来源性质 provenance 分开。role 可为 product/reference/generated/unknown；provenance 仅 photo/synthetic/illustration/unknown，且必须有本轮原话或档案中**该图片**的明确来源依据。画面、role、参考用途、事实来源和“合成测试”任务标签均不补足图片来源。`reference_use` 为 none/style/structure/both/unknown。reference 不等于 competitor，不另造竞品来源标签。仅分析的参考用 analysis_only，无输入序号；尚未选实际入口时所有序号 null，产品可用 undecided，不能先指定图1。已确定入口时才允许 upload 及正整数序号。
- `facts` 每项：`{"id":"事实ID","text":"实际陈述","source":"user"}`；source 仅 user/record/observation。text 直接复制原事实短句，不扩写或同义改写；并列原句可保留原句或按原短语拆分。只写当前证据允许的事实；恢复时保留原 ID 与文本。观图结论不能升格为实物规格。
- `capabilities` 每项：`{"server":"服务原名或已核对宿主别名","query_tool":"实际工具名","models":[],"query_succeeded":true,"configured":true,"upstream":"not_tested","performance":"not_tested"}`。models 逐项复制该工具返回的完整模型 ID。免费目录／配置查询只证明本次工具成功与配置存在；不从中判断历史连通过否、生产就绪、速度或质量，不能另附选型推荐。GPT 服务允许用户名 zhenzhen-gptimagegen2.5-mcp 与实际宿主名 zhenzhen-gptimagegen2-5-mcp；Nano 服务为 zhenzhen-nanobanana-mcp。query_tool 可为宿主完整名或该服务的 MCP 方法短名，但必须绑定同一次实际查询，不能互换两服务的方法或模型目录。同一服务的两个别名不能冒充两个服务。未知 configured 用 null。
- `locked_images` 取已接受且本轮要求保留的图号；`edit_images` 取本轮修改图号。两个集合不相交。局部字号、位置、留白只作用于 edit_images；锁定集合不是“缺少确认证据”的待问字段。
- `baseline` 保留示例中的全部字段；只复制已有值，未记为 null。`previous_layout` 复制原档案中的布局描述，不把新坐标填成旧坐标。`kind` 仅 main/detail/sku/asset/null。已有标题和辅助文案的逐字内容与确认状态分开；图种、视角、商品数量不默认补齐。

### proposal 与 next

- mode=status：只交付真实查询状态，proposal=null，images/facts/locked_images/edit_images 为空，baseline 全部字段均 null（尚不建立设计基线）；next.rollback_stage=null，stage=S0，confirm_images 为空，missing_fields 可列 product_image/product_details/canvas/brand。不将“缺实图”扩大成连策划草案也不能做。
- mode=plan：state.images/facts 来自本轮资料，kind 来自用户用途；locked_images/edit_images 均空。proposal 是新方案，next.rollback_stage=null，stage=S3，confirm_images 仅一个本轮新图号。
- mode=revision：限商品与事实不变的单图文字／排版反馈，读原档案恢复 state；edit_images 仅一个本轮修改图号，给它局部布局。proposal.copy **逐字段等于 baseline 同名值**，缺原文仍 null；appearance 三项均 null（拟保留原风格，未知不补）；canvas 等于 baseline.canvas。next.confirm_images **恰好等于 edit_images**，不含 locked_images；rollback_stage=S2、stage=S3，不重问锁定是否有效。事实或身份改变时先按原流程回 S0，不用这个局部修订模式。
- `proposal.layout` 每行：`{"element":"title","region":{"x":8,"y":6,"width":84,"height":16},"align":"left","max_lines":2,"if_present":false,"overflow":"reflow_preserve_all_copy"}`。region 为画布百分比的左上位置与宽高，使用具名字段，不接受坐标数组；x/y≥0，width/height>0，x+width≤100、y+height≤100。元素仅 title/subtitle/labels/footnote/product/gap，align=left/center/right，max_lines 为正整数或 null。数字仅本轮建议。**仅 revision** 的 subtitle/labels/footnote 缺原文时 if_present=true；plan 中已在 copy 新拟的辅助文字可用 false。overflow 始终保留全部原文，行数不够时适配或待研讨，不能删辅助行腾位置。
- `proposal.canvas` 为 null 或 `{"width":正整数,"height":正整数}`。appearance 为本轮 background/typography/lighting 设计文字或 null。仅 plan 可新拟文案、画布及视觉风格。
- `reference_style` 每项：`{"image_id":"参考ID","attribute":"art_medium","value":"平涂"}`；attribute 仅 art_medium/background_tone/lighting/texture/font_tone。结构或仅风格的限制按原用户范围执行，对齐／占比／留白属于布局，不塞入 value。独立新构图在 layout 中表达，来源不归给风格参考。
- missing_fields 仅列 baseline 中为 null 的字段名；status 另可列上述四种资料。它是确定的待补项，不是自由问句。需确认的仅 next.confirm_images 与 proposal；不另写是否继续冻结、是否改旧图等问题。

## 校验与展示

提供 [scripts/validate_design_state.py](scripts/validate_design_state.py)。它只读 JSON 和调用方提供的**可信证据快照**，不联网、不改文件、不调用 MCP。Python 3.10+ 标准库，无新增依赖：

```text
python -X utf8 -B <技能根>/scripts/validate_design_state.py <状态JSON> --evidence <可信证据JSON>
```

退出0仅表示结构、来源绑定、状态与作用域不变量通过；退出1保留错误，不提交。证据形状为 `mode/images/facts/baseline/locked_images/edit_images/capabilities`，值从原请求、实际档案和查询返回独立整理；不把模型自己写的 state 复制为证据。验证不证明新文案／美术效果正确，仍须审阅和用户确认。

读本篇即可构造状态，pending 交付无需读取验证器源码；读源码也不算执行校验。宿主允许脚本时可在既有权限内校验；不允许时只交付 pending 的 JSON，由外部流程只读校验，不申请更宽工具权限或假称本轮脚本已运行。需要文字版展示时可用同一脚本 `--render`：从同一状态生成文案布局、待补清单和完整结构化提示词，不另创信息。当前只读宿主不会自动执行这个外部渲染步骤，不声称安装了 UI 适配。任何脚本检查结果都不能代替 S3 用户确认与收费授权。

### 确定性编译：只生成新的待审候选

原始答卷先按上述规则验收，失败成绩与文件永久保留。外部编排方可再用 [scripts/compile_design_state.py](scripts/compile_design_state.py)，从独立证据重建事实、图片来源、能力状态及冻结范围；新策划只采用模型的 proposal，局部恢复只采用其 layout。它不调用模型或 MCP，不更改原答卷，不修猜坐标，不把原失败改判为通过。可信证据由编排方从原请求、档案及实际工具结果整理，不能复制模型 state 自证；普通用户不需要填写技术证据表。

```text
python -X utf8 -B <技能根>/scripts/compile_design_state.py <原始答卷> --evidence <可信证据JSON> --output <全新候选目录>
```

### 两个 CLI 的调用契约

上述模板中的 `<技能根>` 必须替换为宿主返回的实际目录；三个文件路径和候选目录使用调用方核实的绝对路径，Shell 中按含空格参数引用。工作目录不限，UTF-8 输入；执行前准备 Python 3.10+，不在调用阶段安装。验证器的 `record` 为必填文件，`--evidence` 必填，`--render` 默认关闭，打开时 stdout 改为 Markdown；编译器的 `record`、`--evidence`、`--output` 均必填，后者必须不存在。两者均无交互、无网络、无 MCP 调用。

默认 stdout 仅一份 JSON。退出 0 为校验通过／新候选写完；可控输入、业务或文件错误退出 1，stdout 为 `valid=false` 和 error；缺参数或未知选项由 argparse 退出 2，诊断走 stderr，stdout 为空。调用方必须同时核对退出码、完整解析结果和适用产物，不以某个 success 字符串放行。编译器可能在文件系统错误时留下部分新目录，不能当成完成或覆盖重试；保留原稿与部分目录，核查后另选新目录。外部编排默认子进程预算 30 秒，超时／取消可能没有完整 JSON；保留失败状态并核对本次目录，不盲目重跑。它不是内置超时开关。

产物 state.json、changes.json、view.md 分别保留新候选、字段路径差异及哈希、同源可读方案。拒绝覆盖已有目录。它使用同一 v2 验证器验证新候选；原始模型成绩与编译后候选成绩分别记录。新候选始终 execution=not_authorized、requires_user_review=true，必须回 S3 展示差异、待补信息及本轮可确认图号。不能以“状态已修复”代替用户确认，不能从模型自述获得出图授权。用户已指定上传映射或执行入口时不适用这个草案编译器。

该脚本不自动安装进宿主事件链；没有外部编排调用时，宿主仅交付 pending 原答卷，不能宣称已自动编译。编译只保证证据绑定和字段作用域，不证明证据本身可信、文案无误、排版实际适配或视觉效果获接受。

本仓库的 Desktop 免费测试编排器会在每个原生会话结束、运行时释放并冷读历史后，自动从外部调用冻结包里的验证器和编译器。原答卷和 raw-score 单独保留，新候选附 changes 与可读方案；失败不重试模型，也不自动提交图片。该接入只属于测试编排流程，不是对既有 Desktop 安装、配置或全局事件钩子的修改，不能据此宣称其他日常会话会自动执行。

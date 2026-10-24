# 76d.8.1：可校验状态与双模型免费集成复验

资料链接已随新规范迁至当前开发路径；下列历史摘要、模型成绩和失败记录不变，不表示迁移后重新完成 Host 验收。

后续已把校验／编译接入测试协调器，见[自动编排复验](DSH-ORCHESTRATION-76d81.md)。本页保留接入前各阶段的原始成绩和边界，不改写为新结果；日常宿主安装仍未增加自动钩子。

2026-10-23，本机 DeepSeek Harness Desktop 0.2.1-rc.2，desktop profile。延续[前次失败及修复历史](DSH-RECOVERY-76d81.md)，不覆盖旧报告。最新 v2 首稿：Sonnet 4/4，Sol 1/4；新增确定性编译后，六份正向新候选通过同一冻结验证器。**编译结果不能改写模型首稿 5/8，也不代表原生宿主已自动执行编译。76d.8.1 保持进行中。**

## 原因与修复

旧模板要求在台账、提示词、解释和追问中反复重述相同信息，导致图片角色被当成来源性质、查询状态被解释为生产就绪、已冻结 M01 又成为待确认对象。追加禁令不足以验证这些信息副本。

新增 [v2 状态契约](../.agents/skills/ecommerce-image-designer/reference/state-contract.md)，分离证据 state、建议 proposal 和 next：

- source、role、provenance、reference_use、上传用途／序号分别记录。“合成测试”任务标签和事实来源不能证明某张图片的来源性质；恢复档案没记 provenance 时保持 unknown，不能改成实拍或竞品。
- 产品事实绑定原文，缺失旧文案、尺寸、视角、风格保持 null。免费查询只证明本次查询成功、模型目录及配置存在；上游与性能固定 not_tested。
- M01 冻结，局部恢复仅编辑 M02。原 copy 保留、未知外观不补，明确 S2→S3，仅确认 M02；execution 永远 not_authorized。
- 最终只交一个结构化提示词对象，不再增加 summary/questions 或重复的自由提示词。矩形使用具名 x/y/width/height，拒绝歧义数组、越界数值、重复 JSON 键和额外散文。

[验证器](../.agents/skills/ecommerce-image-designer/scripts/validate_design_state.py)使用从原请求、档案和真实工具返回独立整理的证据，不能复制模型 state 自证；文字版从同一状态渲染。契约限免费状态、未确认单图策划及单图文字局部恢复；套图与已授权 S4 不在本次覆盖内。

## 真实运行和失败

每个实现冻结后，两个模型各执行显式能力查询、隐式看图、非电商反例、档案恢复各一次。请求与夹具跨两批逐项核对一致（仅证据根路径不同）。没有择优抽样、自动重试或替换失败，使用真实 desktop Host、原生 skill/read、实际 MCP 和模型请求头。

实际路由为 `codeproxy-anthropic/claude-sonnet-5-5` 和 `codeproxy-openai/gpt-6.1-sol`。

| 冻结批次 | 正常结束 | 工具轨迹通过 | 首稿契约＋轨迹通过 | 免费 MCP／图片块 | 运行时释放 |
|---|---:|---:|---:|---:|---:|
| state81，v1 十文件 | 6/8 | 6/8 | 3/8 | 6／2 | 8/8 |
| state82，v2 十文件 | 8/8 | 8/8 | 5/8 | 7／4 | 8/8 |

v1 两项 Sol 因上游 overload 失败，未重提。v1 校验设计也有误拒：实际宿主 GPT 服务别名、同服务短方法名未适配，新策划辅助文案被错误套用恢复条件；Sonnet 隐式策划还实际输出了歧义坐标数组。v2 修改协议和实现后才执行完整新批次：只接受实测同服务别名／方法绑定，区分 plan/revision，并要求具名矩形；没有互换两个服务目录或声称免费验证了供应商出图。

| v2 首稿场景 | Sonnet | Sol |
|---|---|---|
| 显式技能＋两服务状态 | 通过 | 失败：把任务指令写成产品事实 |
| 隐式选择＋两张实图 | 通过 | 失败：已知 main 未写入基线；另有装饰性来源字符串和额外观察事实 |
| 非电商反例 | 通过 | 通过 |
| 文字恢复 | 通过 | 失败：无新观图却新增 reference_style 的未知色调说明 |

Sonnet 本批来源保持 unknown、查询状态未夸大、不再重问 M01 冻结；恢复只读档案和阶段资源，没有 MCP 或无关读取。这是一次冻结批次的结果，不是长期稳定性保证。Sol 三项失败完整保留；报告的首个校验错误不能代表答卷只存在一个问题。

## 确定性编译：新候选与首稿分开

剩余失败涉及模型重复抄写权威状态。新增 [compile_design_state.py](../.agents/skills/ecommerce-image-designer/scripts/compile_design_state.py)：外部编排方从独立证据重建 state；新策划采用模型 proposal，局部恢复只采用模型 layout。它不调用模型或 MCP，不猜坐标、不覆盖原稿，只创建带字段差异和哈希的新候选；copy 从档案取回、缺失仍 null。新候选始终 requires_user_review=true，不能变成出图授权。

[统一离线复验脚本](../scripts/audit_compiled_dsh_states.py)处理全部 state82 答卷：**原稿仍 5/8；六份正向新候选 6/6 通过同一个冻结 v2 校验器，两个反例原样通过。新增模型请求／MCP 调用为 0。**脚本核对原始答卷哈希、原审计文件、冻结包、实际请求头与工具轨迹、释放及冷读历史，不改写初次成绩。

人工复核：两份新策划仅主张灰色盒体／深灰盖沿，参考来源未改成竞品；恢复保持缺失旧值、M01 冻结、M02 确认范围及 S2→S3。Sol 恢复的 subtitle/labels/footnote 共用底部区域，虽然均为“若原稿存在”条件项，若实际存在多行仍须取回原文后重新适配；数值合法不等于排版获接受。结构校验也不保证所有美术文字及语义正确。

最终包十一文件：编译器和调用说明在 v2 原生运行后加入，本轮只对真实答卷做外部确定性后处理，**没有重抽十一文件包、没有安装宿主自动编译钩子**。原生直接调用 Skill 仍可能得到需外部校验／编译的 pending 原稿。脚本调用无需改变安装配置、权限或依赖；普通用户无需填写技术证据表，编排方负责独立取证。

## 证据、摘要和复现

完整本机证据不进入发行包或 Git：

- `E:\dsh-skill-host-76d8-state81`：v1 八次尝试、全部错误、输入／答卷／工具、冻结包及审计。
- `E:\dsh-skill-host-76d8-state82`：v2 八份原答卷、full-audit.json、verification、释放和冷读历史。
- `E:\dsh-skill-host-76d8-state82-compiled`：report.json、新候选及 changes.json/view.md、preservation.json、最终十一文件快照和 skill-history.json。

skill-history.json 逐文件保存本轮开始八文件、v1、v2、最终十一文件四个阶段的 SHA256；两批 evaluation-source 和 manifest 保存当时测试器源码。新增快照不覆盖历史摘要。

| 文件 | SHA256 |
|---|---|
| v2／最终 SKILL.md | b9c3f9fcc686ba6b0abd5e5645d7e4afee02d2c6a3e8ccce2190d3c7d77da38f |
| 冻结 v2 验证器（编译复验未改） | 49f921cb7178d9956d64bf52264f506b90385ff3083e480d9cd8d871d815fe03 |
| 编译器 | c89367dfc440f6999fa2ed01be68eb5c460d235783f16a9cb738176e09d0041e |
| 免费 guard（沿用） | a199cab03ede04089be8b89810fd727a3420e5b6825ee4b7f63064b2894662ea |

已准备的仓库开发环境下运行；输出目录必须全新：

```powershell
./.venv/Scripts/python.exe -X utf8 -B scripts/audit_compiled_dsh_states.py E:/dsh-skill-host-76d8-state82 E:/dsh-skill-host-76d8-state82-replay-new
```

本地 103 项 Python、13 项 Node、结构／资源／42 场景格式及 skill-creator quick_validate 通过；不是新的 42×3 行为评测。两批共 16 个测试运行时均释放并保留可冷读历史，原 Agent 列表及默认模型在运行前后相同。既有五份 profile／凭据文件和 exe/app.asar 哈希复核不变；没有执行策略／ACL 操作，没有收费图片工具尝试、安装配置变更、Git 交付或新远端 CI。

## 剩余未验证

十一文件包的宿主自动编译未接入／未验证；Sol 原生首稿仍三项失败。Codex npm／desktop、其他模型、多轮跨会话恢复、套图、真实产品和实际文案适配未用本次新协议重跑。供应商收费生成／编辑、方案批准后的真实提交、保存和用户视觉接受未验证，仍须先确认具体方案。上游 Inspector 状态帧大小缺陷由 76d.9 跟踪，本轮只证明测试生命周期未泄漏，不声称修复上游。

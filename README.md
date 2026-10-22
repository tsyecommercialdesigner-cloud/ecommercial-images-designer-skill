# 电商图片设计 Skill

将商品资料和参考图转成可分步研讨的主图、详情页和 SKU 方案，覆盖卖点、文案、排版、提示词、确认后交由图像 MCP 生成，以及成品验收和反馈回退。

技能入口：[ecommerce-image-designer](.agents/skills/ecommerce-image-designer/SKILL.md)。课程来源与适用边界见 [方法摘要](.agents/skills/ecommerce-image-designer/references/source-methods.md)。宠物烘干箱只作为来源案例，不提供其他商品的参数默认值。

## 使用

在此仓库中使用支持本地 Skills 的宿主，显式调用示例：

```text
$ecommerce-image-designer
帮我为这款收纳盒策划主图和详情页。第一张是我的产品实拍，
第二张是竞品，只参考配色；先讨论卖点、文案和排版，确认后再出图。
```

首次生成要提供图片并说明身份；参考图再分风格、画面结构或两者。若明确只要文生图背景素材，可以不提供商品实拍。只要策划或提示词时，不会自动进入收费出图。

技能本身为纯指令，无运行时和密钥依赖。图像生成与编辑仅使用 `zhenzhen-gptimagegen2.5-mcp` 或 `zhenzhen-nanobanana-mcp`，按任务选择其中一个；出图阶段需要宿主可查看图片，并已连接支持当前任务的指定服务，凭据由该服务管理。两个服务均不可用时保留方案并报告缺口，不自动改用其他出图工具。能力查询成功不代表真实业务出图已验证。

## 目录

| 路径 | 用途 |
|---|---|
| `.agents/skills/ecommerce-image-designer/` | 完整技能：入口、按需参考资料、许可证和 Codex UI 元数据。 |
| `evals/scenarios.json`、`evals/RUBRIC.md` | 固定的选择／行为场景和评判方法；不含真实客户资料。 |
| `evals/mock_mcp.py`、`evals/README.md`、`scripts/*behavior_eval.py` | 无收费绘图权限的 MCP 替身、隔离模型实跑、独立评分及复现方法。 |
| `scripts/validate_skill.py`、`tests/` | 本地结构和资源检查、失败路径测试。 |
| `docs/USAGE.md`、`docs/VALIDATION.md` | 发现／使用说明、验证命令和覆盖边界。 |
| `CONVENTIONS.md`、`AGENTS.md`、`docs/ENGINEERING-GUIDE.md` | 项目工程约定。 |

安装、配置和升级见 [使用说明](docs/USAGE.md)。开发检查见 [验证说明](docs/VALIDATION.md)。已提供 [Windows CI配置及交付约定](docs/DELIVERY.md)，目前尚未在远端运行或核实评审门禁，也未发布标签；不作发布版或跨宿主兼容承诺。版本修复和入口摘要变化见 [CHANGELOG.md](CHANGELOG.md)。

完整需求覆盖与本轮修复见 [Skill 审查记录](docs/SKILL-REVIEW.md)，包括两个 MCP 的实际入口限制、方案批准粒度和反馈回退证据。

42 个场景各 3 次的模拟 MCP 实际行为评测、修复回归及 Nano 正向确认链见 [行为评测报告](docs/BEHAVIOR-EVAL.md)。这不代表真实供应商出图或用户视觉验收通过。

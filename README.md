# 电商图片设计 Skill

将商品资料和参考图转成可分步研讨的主图、详情页和 SKU 方案，覆盖卖点、文案、排版、提示词、确认后交由图像 MCP 生成，以及成品验收和反馈回退。

技能入口：[ecommerce-image-designer](.agents/skills/ecommerce-image-designer/SKILL.md)。课程来源与适用边界见 [方法摘要](.agents/skills/ecommerce-image-designer/references/source-methods.md)。宠物烘干箱只作为来源案例，不提供其他商品的参数默认值。

团队分发、固定版本打包、成员安装与验收、MCP准备、使用示例和升级／回滚／卸载见 [MANUAL.md](MANUAL.md)。

普通成员从[手册第4节](MANUAL.md#4-成员校验并安装)下载正式附件并验证安装；第3节打包仅供维护者。本仓库手册已修复交互执行时的失败后假成功，并支持带双引号的目录输入；v0.1.2 随包手册包含这些修复，v0.1.0 保留为历史版本。

修正版发行：[v0.1.2](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/tag/v0.1.2)。使用同版 Release 附件中的完整技能包、手册及摘要清单；准确源码提交见 `release.json`，限制见 `RELEASE-NOTES.md`。发布源码及 CI 记录见同版 `RELEASE-NOTES.md`。技能运行包采用新的固定内容树和 ZIP 摘要；[v0.1.0 发布回执](docs/RELEASE-v0.1.0.md)及其附件保留。

v0.1.2 由 Skill 自行策划、文案排版与提示词，确认后直连两个 MCP 的核心生成／批量工具；不依赖服务端策划、复刻编译、resources 或 prompt 模板，见[适配与免费回归记录](docs/CORE-IMAGE-ADAPTER-64a.md)。旧 v0.1.0／v0.1.1 保留，成员升级需取得 v0.1.2 的完整技能包，不能只替换手册。

## 使用

在此仓库中使用支持本地 Skills 的宿主，显式调用示例：

```text
$ecommerce-image-designer
帮我为这款收纳盒策划主图和详情页。第一张是我的产品实拍，
第二张是竞品，只参考配色；先讨论卖点、文案和排版，确认后再出图。
```

首次生成要提供图片并说明身份；参考图再分风格、画面结构或两者。若明确只要文生图背景素材，可以不提供商品实拍。只要策划或提示词时，不会自动进入收费出图。

日常策划以指令为主，无密钥依赖；可选的状态校验／候选编译脚本使用 Python 3.10+ 标准库，由既有权限内的外部编排方调用。图像生成与编辑仅使用 `zhenzhen-gptimagegen2.5-mcp` 或 `zhenzhen-nanobanana-mcp`，按任务选择其中一个；出图阶段需要宿主可查看图片，并已连接支持当前任务的指定服务，凭据由该服务管理。两个服务均不可用时保留方案并报告缺口，不自动改用其他出图工具。能力查询成功不代表真实业务出图已验证。

## 目录

| 路径 | 用途 |
|---|---|
| `.agents/skills/ecommerce-image-designer/` | 完整技能：入口、按需参考资料、许可证和 Codex UI 元数据。 |
| `evals/scenarios.json`、`evals/RUBRIC.md` | 固定的选择／行为场景和评判方法；不含真实客户资料。 |
| `evals/mock_mcp.py`、`evals/README.md`、`scripts/*behavior_eval.py` | 无收费绘图权限的 MCP 替身、隔离模型实跑、独立评分及复现方法。 |
| `scripts/validate_skill.py`、`tests/` | 本地结构和资源检查、失败路径测试。 |
| `docs/USAGE.md`、`docs/VALIDATION.md` | 发现／使用说明、验证命令和覆盖边界。 |
| `CONVENTIONS.md`、`AGENTS.md`、`docs/ENGINEERING-GUIDE.md` | 项目工程约定。 |

安装、配置和升级见 [使用说明](docs/USAGE.md)。开发检查见 [验证说明](docs/VALIDATION.md)。已提供 [Windows CI配置及交付约定](docs/DELIVERY.md)，远端执行与门禁状态见该交付记录；尚未发布标签，不作发布版或跨宿主兼容承诺。版本修复和入口摘要变化见 [CHANGELOG.md](CHANGELOG.md)。

完整需求覆盖与本轮修复见 [Skill 审查记录](docs/SKILL-REVIEW.md)，包括两个 MCP 的实际入口限制、方案批准粒度和反馈回退证据。

42 个场景各 3 次的模拟 MCP 实际行为评测、修复回归及 Nano 正向确认链见 [行为评测报告](docs/BEHAVIOR-EVAL.md)。这不代表真实供应商出图或用户视觉验收通过。

2026-10-23的[首轮真实宿主记录](docs/HOST-INTEGRATION.md)保留原资源拒绝；[沙箱修复后免费CLI复验](docs/HOST-CLI-RECOVERY.md)记录普通用户验收、12次主集及确认状态修复后的3次恢复回归。[系统技能缓存专项](docs/SYSTEM-SKILLS-76d4.md)进一步定位并复现共享缓存竞争，修复验证器，使用与当前Desktop系统包一致的CLI重跑12次免费Host验证，系统安装错误为0；上游跨版本缓存问题另行跟踪。实际出图及用户视觉验收尚未运行，仍需先确认具体商品方案。

账户、PowerShell 5.1／7 执行策略及目录所有者／DACL 的完整故障解释，见 [Windows 沙箱权限复盘报告](docs/WINDOWS-SANDBOX-ACCOUNT-DACL-REPORT.md)。报告末尾提供本机管理员配置、普通权限验收和尚未实测的撤销命令。

升级后的 [0.163.0 复现与上游核查](docs/SYSTEM-SKILLS-76d7.md)确认冷缓存竞争仍存在；[隔离源码补丁](patches/codex/README.md)保留原生验证、应用／撤回及当前未验证项。现有安装、配置和缓存未被替换，补丁不是已部署修复。

独立修补 CLI 的[后续普通权限与免费 Host 复验](docs/SYSTEM-SKILLS-76d7-HOST.md)已通过：新批次 12/12、27 次 shell 和 9 次免费 MCP 调用成功，确认门禁、图片角色与反馈回退经逐条复核。保留配套程序缺失和 V8 构建失败记录；现有配置、旧缓存及目录权限不变，只新增候选运行缓存。上游部署和收费出图／视觉验收仍未验证。

本机 [DeepSeek Harness Desktop 0.2.1-rc.2 首轮验证](docs/DSH-DESKTOP-76d8.md)确认可原生加载技能，[历次修复续验](docs/DSH-RECOVERY-76d81.md)保留全部失败。后续[状态契约](docs/DSH-STATE-CONTRACT-76d81.md)已接入[测试宿主自动编排](docs/DSH-ORCHESTRATION-76d81.md)：最新八项尝试七项正常，Sol显式状态overload未重试；原稿5项通过，五份正向候选5/5、两反例不编译，不能改判原稿。日常宿主没有新增自动钩子，当前包未重跑Codex；安装配置保持不变，无收费出图。

# v0.1.2 发布回执

2026-10-24，按用户授权发布 [v0.1.2](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/tag/v0.1.2)，Release ID `422427550`。正式标签固定 `3a5c77f989d425e4c7554090c29058e5b289c3ae`；本回执随后归档，不移动标签或修改附件。

## 本版变化

Skill 自行完成策划、事实与来源核对、文案排版和逐图完整提示词，用户确认后直连两个指定 MCP 的核心生成／编辑与批量任务；不依赖服务端策划、复刻编译、resources、prompt模板、整版确认或复刻评审。Nano/GPT 按各自真实字段适配，当前 GPT 批量入口已核对。逐图确认、费用授权、输入角色／顺序／摘要、未知状态恢复及用户验收均保留。

技能内容树 `4d27005fabe36d5bf19eb4fccda336cc39569ffe`，仍为11文件，全部逐字节匹配正式源码的Git blob；ZIP与旧版已不同。成员从同版 MANUAL.md 第4节下载四个必需附件并验证安装，旧包须按升级章节备份后换完整目录，不能只替换手册。

## 准确提交与门禁

[PR #12](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/12) 正常 merge，保留实现提交 `20a92e4561e319c9765d279d99f8a4cd620a6163` 和CI隔离修复 `350dc3f87bedc612cef66f6e511ace4c26583074`。未 squash、rebase、强推或跳过保护。

[最终准确head维护者Agent自审](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/12#pullrequestreview-5635877880)为 COMMENTED，Agent review 状态成功；不是独立人工批准。

| CI | 准确提交 | 结果 |
|---|---|---|
| [PR](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/40046203464) | `350dc3f87bedc612cef66f6e511ace4c26583074` | success |
| [DevSync](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/40046432910) | `3a5c77f989d425e4c7554090c29058e5b289c3ae` | success |
| [Main](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/40046331277) | `3a5c77f989d425e4c7554090c29058e5b289c3ae` | success |

各轮141 Python、15 Node及结构/42场景格式检查通过；其中16项新核心工作流回归，另有16项已安装schema/Pydantic检查，真实生成工具调用为0。量规2.0-core与旧1.0分开，未运行新的模型评测，不继承旧模型成绩证明新流程成功。工作流没有tag/release触发器，不称为标签CI。

## 失败与修复历史

[首次dev CI40045894209](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/40045894209)在旧WinPS5.1缺模块故障注入测试30秒超时；同head PR CI40045917072通过，不能用后者绕过前者。新增修复只在该测试子进程启动后限定系统模块路径，因为WinPS启动会追加全局目录；保留真实导入错误、上下文、退出状态和30秒限制。首次本地路径断言失败和最终4项专项通过日志分别保存；没有重跑旧失败刷绿，也没改生产诊断、执行策略、Host配置、安装或权限。

64a的原扩展夹具失败、两类重建校验错误及其归档保留；相关资源快照只用于诊断，当前运行链不再依赖它们。没有成员原始参数，不能断言具体触发词。PI-AI流读取问题仍未验证或修复。

## 七附件摘要

| 文件 | SHA256 |
|---|---|
| `CHANGELOG.md` | `b76a8bd765308036ee531f380ad9567354c72924976b06596087df3cfe5e3f45` |
| `ecommerce-image-designer-v0.1.2.zip` | `ac805326f2650dcfeea8d9d71f0e817f069d9029998708d7f90dbdf1d7af6882` |
| `MANUAL.md` | `523de0ea0c95e88d8b85cbab94345408440f0a61b292ad465f616c71d03b2fc4` |
| `RELEASE-NOTES.md` | `921b495cd750aaf49c658b436fb676b162d68d5e2f35df1b4ed7a97205e74d27` |
| `release.json` | `2d998eb6968f8160f272dc0992bd524e44c7508eb69495251f46b541fe5ae461` |
| `VALIDATION.json` | `819dafe3fdaeba7ed3b9d4b9700dfe93c5f49d6952932e484f03a09799a33cc1` |
| `SHA256SUMS.txt` | `8fd29a8e659ea13125f37ca040c0318115d1376f06e1190a7d819fdff6df3740` |

候选、草稿及正式发布后重新下载检查七附件的GitHub digest、六项SHA256SUMS和准确源码字节，并执行下载手册：带双引号的中文/空格路径、11文件安装摘要、先成功再缺清单后清空旧结果并阻止安装、合成用户文件保留均通过。运行包按固定树归档，命令级core.autocrlf=false，不改本机配置。

v0.1.0（ID421632729）和v0.1.1（ID421712840）的标签、正文、七附件ID/大小/摘要逐项核对不变，下载计数变化不视为内容变更。旧ZIP摘要 `4bf32b888a67392036af80e3d9ab2405d818686651218179f477fb671426e8d6` 不用于v0.1.2。

## 证据收尾与未验证项

Beads 64a保存实现，v9y保存本次交付。`.eval-runs/release-v012/evidence.zip`含48文件，SHA256 `7f1c8abde59392ded7f03f3cb4bfd02d6833e8573430809b6627f6b5251a8705`，逐文件回读核对后删除本轮重复副本；配套summary.json。所有本轮 `.eval-workspaces/release-v012-*` 已移除，未在盘符根目录新建测试环境，旧归档保留。

未验证新版模型/真实成员Host行为、成员原始触发词、真实供应商出图/保存/视觉效果、跨版本业务状态迁移、其他OS或共享远端MCP、PI-AI流恢复。安装文件校验不等于Host发现或业务验收。历史DSH原稿5/7、五份正向候选5/5、两个反例不编译；Sol显式状态overload未评测且用户接受，不改判旧失败。实际出图仍须确认当前方案和费用范围；本次没有新模型评测、真实生成/提交或收费调用。

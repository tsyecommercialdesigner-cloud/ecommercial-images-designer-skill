# v0.1.0 正式发布回执

[GitHub Release v0.1.0](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/tag/v0.1.0) 已于 2026-10-23 09:17:00 UTC 正式发布（北京时间17:17:00）。同一 Release ID `421632729` 从既有草稿转正式，`draft=false`、`prerelease=false`。

| 身份 | 固定值 |
|---|---|
| 正式标签／准确提交 | `v0.1.0` → `68be9e2030605454bc30026b96c6957635c76a91`，远端 refs 与本地 fetch 后解析一致 |
| 运行 Skill 快照 | `0be00e0b8837e9f06633ce5b7504f14bfa711992`；十一文件与正式源码 Git blob 完全相同 |
| 修复 PR／准确 head | [PR #7](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/7)，`23e71d5acdb90a469ec00235facb301d97cae242` |
| 准确 head 评审 | [5626205514](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/7#pullrequestreview-5626205514)，维护者 Agent 自审，非独立人工 APPROVE |
| PR Windows CI | [39929914533](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39929914533)，success |
| 正式源码 main CI | [39930238860](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39930238860)，准确提交`68be9e2`，success |
| dev 快进同步 CI | [39930384589](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39930384589)，准确提交`68be9e2`，success |

发布前重新查询已有检查及评审，不重新抽样模型。修复后的手册命令实测隔离安装、摘要／重复／链接／路径错误拒绝、备份恢复卸载及合成用户文件保留；六代码块语法、109 Python、15 Node、结构与42场景格式检查通过。正常 merge 保留修复历史，无强推或门禁绕过。工作流没有 tag/release 触发器，没有宣称发布自动产生了标签 CI。

## 附件及摘要

七份正式附件：`ecommerce-image-designer-0be00e0.zip`、`release.json`、`MANUAL.md`、`CHANGELOG.md`、`RELEASE-NOTES.md`、`VALIDATION.json`、`SHA256SUMS.txt`。从Release页面取得完整交付；清单分开记录正式版本、源码提交、运行快照、逐文件摘要和旧候选身份。手册保留发行注记，根仓库文档在发布后可继续维护，不回写标签或附件。

正式 ZIP SHA256：

```text
4bf32b888a67392036af80e3d9ab2405d818686651218179f477fb671426e8d6
```

发布前和发布后分别下载全部七附件，均匹配本地待发布文件与 GitHub 资产 digest；六个内容文件匹配 SHA256SUMS，摘要文件与本地原件一致。ZIP路径、重复项、符号链接和完整十一文件检查通过；逐文件匹配正式源码及运行快照的 Git blob。摘要需经团队可信渠道核对，不能独立证明来源。

## 保留的失败与修复

原候选ZIP SHA256 `3240f1c6f1c8abb31958a2628a4fc393260d0e155a5b0b44545ec8fcb7bb9a22` 虽与其清单自洽，严格源字节检查仍失败：`state-contract.md`及两个状态Python脚本受子树归档和本机`core.autocrlf=true`影响，从LF转换为CRLF。发布停止后，PR #7仅增加打包命令的`-c core.autocrlf=false`，本机配置仍true，既有Skill源码未改。正式包重建并使用新摘要，旧候选不再作为正式安装包。

原草稿元数据、七附件、初次失败、三文件差异和修复复验保存在本地忽略的`.eval-runs/release-n30/`；旧ZIP及前后逐文件摘要也记录在正式`release.json`／`VALIDATION.json`和修复历史中。另保留GitHub说明正文CRLF与附件LF的呈现差异诊断；正文仅按换行比较，全部附件仍逐字节核对，没有降低文件断言。

## 已知限制

最新DSH两codeproxy路由原稿5/7、五份正向编译候选5/5，两个反例不编译；Sol显式状态overload未评测，用户已接受该例外。原稿失败不改判，日常自动编译钩子未部署。真实团队成员宿主、当前十一文件完整Codex免费主集、跨版本数据迁移、其他操作系统、共享远端MCP、真实商品收费生成／保存／视觉验收仍未验证。

本次发布没有新增模型、MCP或收费出图调用，没有修改安装配置、执行策略或权限。正式发布不替代商品事实、输入图片角色核实和当前方案／收费范围确认；业务出图仍须先确认。MCP仅限两个指定服务。

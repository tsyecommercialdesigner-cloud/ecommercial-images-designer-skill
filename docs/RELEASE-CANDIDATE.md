# 团队手册交付与 Release 候选回执

以下保留2026-10-23发布前的候选记录：当时没有公开Release或发行标签，候选标识为`candidate-f4d78a8`。该候选后来在严格源码字节核对时失败，经PR #7修复后，同一个Release已正式发布为[v0.1.0](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/tag/v0.1.0)。原候选摘要和阶段验证不改写；正式源码、修复后的摘要及发布状态见[正式发布回执](RELEASE-v0.1.0.md)，不能使用下文旧ZIP摘要接收正式包。

## 源码交付

[PR #5](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/5) 将手册与入口文档提交 `4c48dd19a7446560538a92d4414242c039c285b4` 正常合入 main，合入提交为 `f4d78a8f5bfbb1299086daf75253117fef4047bb`。采用 merge 保留历史，没有强推、压缩提交或管理员绕过。

| 检查 | 精确提交／结果 |
|---|---|
| dev 推送 Windows CI | `4c48dd1`，[39927854950](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39927854950)，success |
| PR Windows CI | `4c48dd1`，[39927898183](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39927898183)，success |
| Agent review | 准确 head `4c48dd1`，[5626034596](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/5#pullrequestreview-5626034596)，维护者 Agent 自审；不是独立人工 APPROVE |
| main 合入 Windows CI | `f4d78a8`，[39928008318](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39928008318)，success |
| dev 快进同步 Windows CI | `f4d78a8`，[39928325692](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39928325692)，success |

源交付完成时，本地与远端的 main/dev 四个引用均为 `f4d78a8f5bfbb1299086daf75253117fef4047bb`。本回执及 Beads 关闭记录随后另走文档 PR；上表不作为后续提交通过的证据。草稿始终固定到上述已验收源码，不随分支移动。

## 候选内容与摘要

运行包固定技能快照为 `0be00e0b8837e9f06633ce5b7504f14bfa711992`，与发行源码 `f4d78a8` 的技能 Git tree 完全相同；`release.json` 分别记录 `revision`、`source_commit`、`skill_tree` 和逐文件 SHA256。MANUAL 与 CHANGELOG 从发行源码 Git 对象提取，不以当前工作树替代。

草稿的七份附件为：`ecommerce-image-designer-0be00e0.zip`、`release.json`、`MANUAL.md`、`CHANGELOG.md`、`RELEASE-NOTES.md`、`VALIDATION.json`、`SHA256SUMS.txt`。运行 ZIP 恰好包含手册列出的 11 个文件；源码测试、Beads、客户数据、本机配置、凭据和原始轨迹不进入运行包。

ZIP SHA256：

```text
3240f1c6f1c8abb31958a2628a4fc393260d0e155a5b0b44545ec8fcb7bb9a22
```

附件上传后重新下载全部七份，六个内容文件均与 SHA256SUMS 一致；摘要文件也与本地原件一致。摘要清单不包含自身；可信来源核验仍需团队安全渠道。本地候选保留于忽略的 `dist/release-candidate-f4d78a8/delivery/`，没有提交生成物。

## 验证与已知限制

109 项 Python、15 项 Node、结构与 42 场景格式检查通过；合入 CI 实际使用 Node `22.23.4`。手册曾验证六段 PowerShell 语法、48 个本地链接和九个固定 Git 对象链接。候选实际验证 11 文件摘要、中文空格路径安装、重复安装拒绝、错误 ZIP／文件摘要拒绝、链接父目录拒绝、受限目录备份／重装／恢复／移出式卸载和合成用户数据保留。

候选包装命令第一次误用残留的 `$LASTEXITCODE`，在 PowerShell 验证已保存成功结果后报失败；保留该包装诊断及原结果，改为断言持久化 JSON 字段，没有重抽模型或重跑行为验证来改判。脱敏结果进入 `VALIDATION.json`，原诊断保留在本地忽略的评测目录。

未新增模型／MCP／收费图像调用，未修改已有安装配置或权限。真实成员宿主发现、当前十一文件包的完整 Codex 免费主集、跨版本数据迁移、共享远端 MCP、其他操作系统、真实商品生成／保存／用户视觉验收仍未验证。DSH 原稿与候选成绩、已接受的 Sol overload 例外见[手册](../MANUAL.md)，不将候选编译通过改判为原稿通过。日常自动编译钩子尚未部署。

公开发布前应审阅草稿内容和限制、选择正式版本及决定必要的成员／业务验收；实际出图仍需先确认具体方案及费用。本次授权只执行准备，没有公开发布或创建正式标签。

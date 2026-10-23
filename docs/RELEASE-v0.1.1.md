# v0.1.1 发布回执

2026-10-23，按用户授权完成成员手册和 PowerShell 验证修复交付，并发布 [v0.1.1](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/tag/v0.1.1)（Release ID `421712840`）。普通成员下载同一 Release 的四个必需附件，按随包 `MANUAL.md` 第4节操作，无需克隆或打包。

## 版本和修复

- 正式标签固定完整源码提交 `ff8c07e7769bc3bb691ef3e9ffe4dcd1f8c0c25d`。本回执随后归档，不移动该标签或改写附件。
- 运行快照仍为 `0be00e0b8837e9f06633ce5b7504f14bfa711992`；ZIP 的11文件逐字节匹配正式源码和快照 Git blob。技能运行行为没有变化。
- 手册区分维护者和普通成员，补充 Release Assets 下载、四文件交付目录示例和可信64位摘要填写说明。目录输入清除英文双引号，保留内部空格。
- VERIFY 和 INSTALL 各自为单个完整提交语句。失败不输出成功，清空旧结果；未验证或 ZIP 在验证后改变时不能继续安装。重复目录和链接父目录仍拒绝，不覆盖现有安装。
- [v0.1.0](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/tag/v0.1.0) 的标签、正文、七附件 ID、大小和摘要复核不变，原打包失败与修复历史保留。

## Windows CI 与评审

| 检查 | 准确提交 | 结果 |
|---|---|---|
| [修复 PR #10](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/10) 的 [Windows CI](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39938865645) | `187499b42245d688e01663388c2370b2ecd81c06` | 成功 |
| [维护者 Agent 自审](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/10#pullrequestreview-5626963357) | 同上 | COMMENTED；准确 head 的 Agent review 门禁成功，不是独立人工批准 |
| [main 合入 CI](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39939123167) | `ff8c07e7769bc3bb691ef3e9ffe4dcd1f8c0c25d` | 成功 |
| [dev 快进同步 CI](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/39939269065) | 同上 | 成功 |

正常 merge，未 squash、rebase、强推或跳过保护。同步时本地与远端 main/dev 四引用一致、工作区干净。Windows CI 实际完成124项 Python、15项 Node，以及技能结构和42场景格式检查；新增15项真实 PowerShell 工作流回归。工作流没有 tag/release 触发器，发布不产生额外标签 CI。

## 七附件摘要

| 文件 | SHA256 |
|---|---|
| `ecommerce-image-designer-0be00e0.zip` | `4bf32b888a67392036af80e3d9ab2405d818686651218179f477fb671426e8d6` |
| `MANUAL.md` | `abaac5ce2b943e3963c609260f8d1fe3c073d4aa0070362b71418b1c090b6f31` |
| `release.json` | `bab839394bdd5f3382e868f83d98f22856b27844c0f905dd9c9d66a27ba1bb2c` |
| `SHA256SUMS.txt` | `dfe0b5f5cb5a7d1ccb32487d634b50011f3cf673390be0b16179fd18712805a1` |
| `CHANGELOG.md` | `4ff0b45a31c0efd5e0b24da29fcae26fcea4e6ff58044a3103c6f095397894d9` |
| `RELEASE-NOTES.md` | `554eb3cf31182f7c4f56bb2bf48038b161c82e3c449ec416aeeb8ea7ae910bf1` |
| `VALIDATION.json` | `499524931697327d92d764d63faed1c5cde5fb55ba128d1c8d239f505d5a7aaf` |

ZIP 原样复用 v0.1.0，故其名称及摘要不变；手册、发行清单和说明更新为 v0.1.1。SHA256SUMS 列六个其他附件，不包含自身。草稿及正式发布后分别重新下载七附件，核对 GitHub digest、摘要清单和准确 Git blob；使用下载手册执行带引号中文空格目录校验与安装、11文件摘要及合成用户数据保留。先成功再验证缺清单目录，旧结果清空、不打印成功、安装拒绝的反例也通过。

## 诊断与证据收尾

本次两项发行编排问题保留为失败：首次候选验收前未生成 SHA256SUMS，手册正确拒绝缺件目录，修正生成顺序后复验；未发布草稿按 tag 查询元数据返回 HTTP404，改为列出现存草稿并按固定 ID 查询，复用已下载附件，不重复创建或上传 Release。均未改产品门禁或重新抽样。

Beads `ecommercial-images-designer-skill-0e5` 保存实现修复，`ecommercial-images-designer-skill-591` 保存本次交付。受忽略证据 `.eval-runs/release-591/evidence.zip` 包含46文件，SHA256 `40787592a13f82eda7df3a00df3a1fea1c52e9a4c52e0b9aa72c004b31781154`，配套 `summary.json`；核对归档逐文件可读及字节一致后移除本轮发行重复副本。临时测试目录位于项目 `.eval-workspaces/release-591-*`，均已移除；未在盘符根目录新建测试目录。归档含合成测试路径，不含用户私有输入或凭据。

## 保留的验证边界

本次没有新增模型评测、图像 MCP 调用或收费出图，没有改既有安装、配置、权限或执行策略。未验证真实成员宿主发现、当前11文件完整 Codex 免费主集、跨版本业务数据迁移、其他 OS、共享远端 MCP，以及收费生成／保存／视觉验收。同快照备份恢复不代表跨版本迁移。

历史 DSH 两个 codeproxy 路由八次尝试七次正常结束，原稿5/7、五份正向编译候选5/5、两个反例不编译；Sol 显式状态 overload 未评测，用户接受此例外，旧失败未改判。日常自动编译钩子未部署，候选仍须确认。实际出图继续限两个指定 MCP，先确认当前方案与费用范围；发行不构成收费授权。

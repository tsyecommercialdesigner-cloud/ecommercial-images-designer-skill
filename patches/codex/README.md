# Codex 系统技能缓存修复候选

这是供审阅与隔离验证的上游源码补丁，不是已发布 CLI，不会自动安装或修改用户配置。诊断和验证边界见 [76d.7 报告](../../docs/SYSTEM-SKILLS-76d7.md)。没有向上游发帖或提交 PR。

- 来源：[openai/codex](https://github.com/openai/codex/tree/83086188ae0614bd882818ff1aa23f3194962012)，`rust-v0.163.0`，完整提交 `83086188ae0614bd882818ff1aa23f3194962012`。
- 补丁：`0.163.0-system-skills-cache.patch`。保留上游 Apache-2.0 许可：[LICENSE](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/LICENSE)。补丁不改变许可。
- 同目录保留上游 [LICENSE](LICENSE) 和 [NOTICE](NOTICE) 原文。
- Rust 1.95.0，Windows x64 MSVC；源码和依赖准备须在新建的独立目录完成。不要对安装目录、当前用户的技能缓存或真实 CODEX_HOME 应用补丁。

在完整、未改动的上述上游源码根目录，使用实际补丁文件的绝对路径检查并应用：

```powershell
git -c core.autocrlf=false apply --check 'E:\agent-skills-workspace\ecommercial-images-designer-skill\patches\codex\0.163.0-system-skills-cache.patch'
if ($LASTEXITCODE -ne 0) { throw 'Patch does not match; stop without changing source' }
git -c core.autocrlf=false apply 'E:\agent-skills-workspace\ecommercial-images-designer-skill\patches\codex\0.163.0-system-skills-cache.patch'
if ($LASTEXITCODE -ne 0) { throw 'Patch failed' }
Set-Location codex-rs
cargo test --locked -p codex-skills --lib
cargo test --locked -p codex-skills-extension --lib
```

本 tag 的本地包版本元数据与发行锁存在差异，原样 `--locked` 会拒绝；本次在隔离副本离线刷新 metadata，并严格确认全部外部锁条目不变后才继续。不能用删除锁、浮动更新依赖或关闭 TLS 的方式处理。Windows 依赖缓存宜使用新的短路径目录，仅对构建进程设置 `CARGO_HOME`，保留已有缓存和配置。

从 codeload 归档构建时，还需核对迁移 SQL 输入的换行格式：本机 Windows 官方 0.163.0 包使用的校验和与 CRLF 对应，直接使用归档 LF 输入的构建不能共享其状态库。本轮只对隔离构建输入做相同 CRLF 编码，并验证 69 项已应用迁移的 SHA384 均匹配；没有修改数据库或禁用迁移校验。此步骤是明确的 Windows 构建适配，不在缓存补丁内，也不证明其他平台的数据库兼容。详见专项报告及保留的构建记录。

`-c core.autocrlf=false` 仅作用于该次 Git 调用，避免本机全局 CRLF 转换影响 LF 原始源码的逐字节往返核对；不修改 Git 配置。独立夹具中已验证应用结果与目标源码一致，反向应用逐字节恢复原文件。补丁 SHA256：`3c068677f40cf07ee05db0c1281ef8e1d9c1ee4b439473025d1a97cb38aa9358`。

补丁包含真实安装器的原生文件系统／跨进程回归，以及 Host 缓存失败分支回归。原生不同指纹身份测试使用同一构建的内置字节；另已构建独立 CLI，完成 51 次真实 app-server 缓存验证，包括与正式版和桌面版的实际混跑。带模型的技能／MCP 集成、普通用户沙箱执行、其他平台和部署仍未验证；这些层次不能靠补丁或缓存测试替代。

以上保留前一阶段状态。后续使用同一候选及同源配套程序，已完成普通权限沙箱验收和 12 次真实免费技能／两 MCP 集成；组件构建、失败及修复、版本摘要和复现命令见[续验报告](../../docs/SYSTEM-SKILLS-76d7-HOST.md)。部署、其他平台、收费出图及用户视觉验收仍未验证；默认 V8 下载失败时须按固定源码官方构建输入及双层摘要校验处理，不能取消 sandbox 或校验。

没有自动垃圾回收、全局锁、执行策略或 ACL 修改。撤回本候选只需在独立源码副本使用 `git apply --reverse --check` 并反向应用相同补丁；若副本有额外改动应停止比较。此命令不回滚已运行二进制或用户数据；本轮没有部署二进制，因而不存在本机安装回滚步骤。

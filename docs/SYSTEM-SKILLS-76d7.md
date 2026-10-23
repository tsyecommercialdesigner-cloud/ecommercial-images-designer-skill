# 76d.7：Codex 0.163.0 复现、上游核查与隔离修复

日期：2026-10-23。任务：`ecommercial-images-designer-skill-76d.7`。这是对 [76d.4 记录](SYSTEM-SKILLS-76d4.md)的追加，不覆盖旧版、沙箱或免费 MCP 验证记录。

## 新版结论

本机正常 NVM 入口 `C:\nvm\.nodejs\codex.exe --version` 已返回 `codex-cli 0.163.0`。升级仍未解决系统技能缓存的并发删除／重建问题。以下测试运行实际 app-server，只发送 `initialize`、`initialized`、`skills/list`；无模型请求、MCP 请求或收费出图。

| 实验 | 测试启动次数 | 安装错误 | 系统目录缺项 | 非零进程退出 |
|---|---:|---:|---:|---:|
| 同版本冷更新，8 轮 × 2 进程 | 16 | 13 | 6 | 0 |
| 同版本热缓存，8 轮 × 2 进程 | 16 | 0 | 0 | 0 |
| 同版本串行冷更新，3 轮 | 3 | 0 | 0 | 0 |
| stable 与 Desktop alpha 混跑，4 轮 × 2 进程 | 8 | 2 | 0 | 0 |

冷更新缺项的实际数量包括 0、1、2、4，完整目录应为 5。13 次错误均包含 `remove existing system skills dir` 和 Windows `os error 5`。混跑中的 2 次错误来自 stable；“都有 5 项”仍不能证明来自各自正确版本。进程退出 0 不能证明系统技能安装成功。

每轮在新建、仅归本次测试所有的子进程 `CODEX_HOME` 中运行，先串行初始化数据库，再将该夹具的旧 marker 设为过期以隔离 SQLite 首启因素。上述 43 次测试启动不含 23 次串行准备启动。没有改动真实 `.codex/skills`，没有在真实缓存中修改 marker。Temp 下 helper alias 的保护警告保留；本实验不执行 helper，也不验证沙箱命令权限。

NVM 初次拦截新 shim，报 `NVM4306`。本轮没有更改 NVM 信任记录，也没有直接运行 node／后端 exe 来越过拦截；用户表示自行处理后，正常入口恢复可用。这个问题与缓存竞争分开记录。

## 上游核查范围

核查官方 `openai/codex`，固定提交而非只看浮动版本名：

| 来源 | 完整提交 | 本次核对结果 |
|---|---|---|
| [rust-v0.163.0](https://github.com/openai/codex/tree/83086188ae0614bd882818ff1aa23f3194962012) | `83086188ae0614bd882818ff1aa23f3194962012` | 安装器仍使用共享 `.system`，先删后写；Host 安装失败后继续发现。 |
| [当时 main](https://github.com/openai/codex/tree/8531184b49bcb160175a84e140b659a83a426df7) | `8531184b49bcb160175a84e140b659a83a426df7` | 同一关键算法仍在；不代表之后的 main 状态。 |

核对 `codex-rs/skills/src/lib.rs`、`ext/skills/src/host_service.rs`、系统根解析与隐藏目录发现逻辑；读取 skills 路径的提交历史及有关 cache、lock、atomic、concurrent 的 PR 搜索结果。未找到已经包含于上述两个提交、能解决本次竞争的修复。

- [PR #36989](https://github.com/openai/codex/pull/36989) 已合并，解决关闭 bundled skills 的服务删除共享缓存的问题；它仍调用非原子安装器，不能解决同时启用时的覆盖竞争。
- [PR #35408](https://github.com/openai/codex/pull/35408) 已合并，避免生成目录的 watcher 噪声；不提供安装锁或版本隔离。
- [Issue #19265](https://github.com/openai/codex/issues/19265) 仍开放，描述较早版本的共享系统目录被删除。它是相关背景，不能据此认定所有症状具有同一原因。

此处 `os error 5` 是实际目录竞争的结果，不应继续用接管所有者、放宽 DACL、修改执行策略或反复清空真实缓存来处理。此前 `.sandbox-bin` 的 WRITE_DAC／Owner 问题已有独立证据，不能与本项混淆。

## 隔离源码修复

补丁位于 [patches/codex](../patches/codex/README.md)，基于上述 stable 提交，仅作用于独立源码副本。没有替换安装目录中的 CLI，没有对外提交 Issue 或 PR。

1. 将当前构建的系统根改为 `CODEX_HOME/skills/.system-cache-v2/<embedded-fingerprint>`。它与旧 `.system` 是同级目录；旧程序删除 `.system` 时不会删除新包。
2. 在同一父目录的新建私有 staging 目录完整写入，最后写 marker，再通过目录 rename 发布。读取者只收到已发布路径；同指纹并发发布的失败方核对获胜包后接受结果。
3. 核对 marker、目录结构和每个内置文件的实际字节，拒绝缺项、改写、额外文件和已检测到的符号链接。不删除或覆盖损坏的已发布目录，也不删除其他构建或遗留 staging，保留故障现场与正在读取的旧版本。
4. Host 验证失败时过滤 System 根，并避免返回先前缓存的 System 快照。用户和仓库技能仍按原规则处理；错误保留日志。
5. 同步根路径相关测试、watcher 断言，以及 imagegen 两份写死旧路径的参考文档。脚本路径从宿主本次实际加载的 `SKILL.md` 所在目录取得，不能 glob 后选“最新”目录。
6. 三个存在本地 Python 模块导入的内置辅助脚本，在导入前仅对本进程关闭 bytecode 写入，防止正常 `--help`／运行创建 `__pycache__` 后被完整性检查拒绝。未关闭执行策略；使用开发环境 Python 运行三个 `--help`，不传 `-B` 且移除 bytecode 环境变量，实际包文件清单及字节均未变化。

本方案暂不垃圾回收旧指纹或遗留 staging，避免删除其他活动进程正在使用的资源；长期空间回收仍需独立生命周期设计。指纹沿用上游既有算法，完整文件比较用于检测损坏，不将该指纹当作密码学来源认证或敌对进程防护。

## 构建与复验记录

源码通过官方 codeload 固定提交取得，归档 SHA256：`e57f1d4f914c71c3532a12d5c14f740909fca4e7e041fa1b3db71618c88e5567`。本地安装无 Rust，故把官方 Rust 1.95.0 组件归档校验其发布 SHA256 后，解包到本项目忽略目录；没有运行系统安装器、注册 toolchain 或修改永久 PATH。复用已安装 MSVC Build Tools，仅在构建子进程设置环境。

前两次失败及原因均保留：

- Cargo 专用缓存路径过长，`rules_rust` 依赖的文件路径达到 267 字符，checkout 报 `path too long`。改用本轮新建的 `C:\Users\Administrator\.cache\c76d7` 专用短缓存；没有改全局 Git／系统长路径设置或 ACL。
- stable tag 的 workspace 版本已为 `0.163.0`，其归档锁内本地包仍为 `0.0.0`，`--locked` 因而拒绝。仅在隔离源码运行离线 metadata 更新本地版本元数据；比较确认 **1314 个外部依赖条目完全相同**，本地 160 项仅版本号变化，依赖字段不变。随后仍以 `--locked` 构建；交付补丁不夹带这批发行版本元数据变化。

安装器原生测试：`cargo test --locked -p codex-skills --lib`，60 项通过、0 失败、1 项默认忽略。忽略项是由并发父测试使用 `--ignored --exact` 显式启动的入口，4 轮各 8 个真实 Windows 子进程全部成功，不是漏跑子进程。父进程在写入期间也不断核对可见包，验证冷安装、完整发布、跨指纹隔离、遗留目录／staging 保留及损坏缓存拒绝。该跨指纹测试共用同一构建的内置字节，不能冒充两个真实修补版本的兼容验证。

独立夹具验证补丁应用、目标文件一致和反向应用恢复原始字节。首轮受本机全局 `core.autocrlf=true` 影响，仅换行不同；改为每次 Git 调用传 `-c core.autocrlf=false` 后精确往返通过，不修改全局或仓库配置。补丁 SHA256：`3c068677f40cf07ee05db0c1281ef8e1d9c1ee4b439473025d1a97cb38aa9358`。

Host 扩展原生测试：`cargo test --locked -p codex-skills-extension --lib`，最终 **138 项通过、0 失败、0 忽略**，包括损坏缓存时不发现 System 根、不返回旧快照且继续提供用户技能的新增回归。

其首轮为 135 通过、3 失败。Windows 默认 Temp 位于用户目录下，而本机用户目录含 `.git`，导致夹具向上发现真实 `.agents/skills`。改用本轮新建、没有仓库祖先的 `E:\codex-76d7-tests-<唯一标识>`，仅对子进程设置 TEMP／TMP 后，结果为 137 通过、1 失败。最后一项原断言假定用户未安装任何技能；修正为精确核对夹具拥有路径下的完整列表，允许服务按原设计加载外部用户技能。没有改生产发现规则、挪动用户目录、伪造用户身份或修改用户配置。最终 138 项全过，两个失败批次仍保留。

此测试隔离修正使候选补丁摘要从 `8089e653866376757d4624352c245ba56ea7ffa6400a639657d628b071df024c` 变为 `6a6eb8ce2f8e9fcf716119067dd15e2e51065d3fbff47b2fafb719c47d2f3252`；再同步 app-server 原测试中“启用就删除旧 `.system`”的断言为保留旧目录，得到上述最终 `3c0686…` 值。两个中间补丁均按完整 SHA 保留在隔离工作区 `patch-history/`，缓存安装算法未变。后一个 app-server 测试源码已同步，未将其单独测试目标标为运行通过。

Skill 入口 `9f5c2ee8c74a1910cef2d6b4cd9a97d047ecb28208a0348066343ac49b459527` 和 `design-record.md` 的 `11ee11fd955e76c855c34e0682059730fa4648985ba818a444e0f20d3d363942` 未改动。

独立 debug CLI 首次构建成功，版本字符串同为 `0.163.0`，它是本轮候选构建，不是官方发行二进制。最初冷、热缓存各 16 次真实 app-server 发现均通过；但首次与正式版混跑的 4 次 peer 全部在 SQLite 初始化退出，未进入技能安装。该失败批次 `patched-mixed-stable-20261023-a1` 保留，不能计为跨版本通过。

只读比较两个独立夹具的 `_sqlx_migrations`：源码归档中的迁移文件为 LF，而本机 Windows 正式版内置校验和对应 CRLF。逐项计算 SHA384，**69 项现有迁移均与 CRLF 计算值匹配**；这不是缓存缺项，也不能通过修改数据库校验和或忽略迁移验证处理。本轮只把隔离构建副本的 77 个迁移 SQL 输入转换为 Windows 发布包的 CRLF，规范化换行后的逻辑字节逐项不变；真实数据库未修改、迁移校验未禁用。这个构建输入适配不进入缓存算法补丁；首次 LF 构建二进制、构建日志、迁移对比和输入摘要另存后再重建。

本仓库新增 `probe_versioned_system_skills.py` 专用于明确指定的候选 CLI：从真实发现推导指纹目录、逐文件核对、保留冷更新旧包，并在语义失败时返回非零；不放宽现有生产 guard，也不改原 legacy 探针。6 项新失败路径回归与已有检查合计 **55 项全部通过**。链接和包结构检查另行记录，不能替代真实 app-server 结果。

### 最终候选 CLI 的真实 app-server 复验

SQL 输入兼容重建成功后，使用新的 `a2` 目录完整复验，未拼接首版成功记录：

| 实验 | 测试启动次数 | 安装错误／协议错误／非零退出／包或目录断言失败 |
|---|---:|---|
| 候选同版本并发冷启动，8 × 2 | 16 | 全部 0 |
| 候选同版本并发热缓存，8 × 2 | 16 | 全部 0 |
| 候选串行冷启动 | 3 | 全部 0 |
| 候选与正式版 0.163.0，4 × 2 | 8 | 全部 0 |
| 候选与 Desktop 0.163.0-alpha.11，4 × 2 | 8 | 全部 0 |

共 **51 次测试启动全部通过**，另有 35 次独立串行准备启动。所有目录均为完整 5 项；候选各批包 marker 同为 `1097a3e50f1d2b21`，逐文件摘要保持一致。混跑同时核对 peer 的真实包清单与旧路径，证明各自使用正确版本，而非只比较数量。冷启动保留的旧包和非混跑遗留目录均未被候选改写。全部请求仍只有 `initialize`、`initialized`、`skills/list`，模型与 MCP 调用均为 0。

最终二进制为本仓库 `.eval-workspaces/codex-76d7-0163/target/debug/codex.exe`，大小 `355735552` 字节，SHA256：`91277b53706d68833dfe200831d7f80c7bac547d960f85f8ffa061f1a4349e7e`。初版 LF SQL 二进制保留为同目录 `codex-before-sql-compat.exe`。没有把这些文件复制到 NVM、桌面安装目录或注册全局入口。

最终再次比较真实 Desktop 缓存，marker `f7cfaf1d6d464589` 和全部 49 文件摘要仍与本轮初始预检完全一致。结构／资源／42 场景格式检查通过；本轮未重跑业务的 42 × 3 模型行为评测。

复现时只使用本轮已经构建并校验的候选，不将未修补的正式版误填到此探针：

```powershell
$CandidateEvidence = Join-Path ([IO.Path]::GetTempPath()) ('system-skills-versioned-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -B scripts\probe_versioned_system_skills.py --output $CandidateEvidence --cli 'E:\agent-skills-workspace\ecommercial-images-designer-skill\.eval-workspaces\codex-76d7-0163\target\debug\codex.exe' --mode cold --rounds 8 --clients 2
if ($LASTEXITCODE -ne 0) { throw 'Candidate behavior verification failed; retain evidence' }
```

前提为仓库根目录、既有锁定 Python 3.12 开发环境和上述候选产物。热缓存改为 `--mode warm`；混跑改为 `--mode mixed --peer-cli '<核实过的另一实际CLI绝对路径>'`，每批使用新证据目录。探针只在该目录中新建子进程 home，不接受真实缓存作为冷更新对象。

## 新版完整免费 Host 的边界

以下保留前一阶段的边界记录。2026-10-23 后续已使用同一独立候选补全配套程序，完成普通权限沙箱验收和新批次 12 次真实免费技能／两 MCP 复验；失败、修复、摘要与剩余边界见[续验报告](SYSTEM-SKILLS-76d7-HOST.md)。没有将此前缓存发现测试改写为带模型的验证。

新版 stable 包 marker 为 `cce1e64b782cd92b`；当前 Desktop `0.163.0-alpha.11` 包为 `f7cfaf1d6d464589`。两者均有 5 项、49 个文件，但内容不同。本轮使用现有 guard 对新版做完整免费 Host 预检，因包不匹配在模型、MCP 和真实全局 CLI 启动前停止；未改写 Desktop 缓存来制造通过。

此前 Desktop 的 12 次真实免费 Host、19 次 shell、9 次免费 MCP 成功，仍属于 [76d.4 批次](SYSTEM-SKILLS-76d4.md)，不能算作新版 stable 或本补丁的验证。本轮已获得独立修补 CLI 的实际 app-server 缓存层成功证据，但未在它上面运行带模型的 12 次技能／MCP 集成、普通用户沙箱资源执行、原生 session resume、干净升级／回滚、其他平台或长期缓存回收验收。付费绘图、真实商品、生成产物和用户视觉验收均未运行，实际出图仍须先确认方案。

`76d.7` 继续跟踪上游采纳与受控部署，不将本地候选通过写成官方版本已修复。未改已安装程序或取消现有 guard，未对外发帖、提交推送或发布。

## 证据位置

原始诊断不进入发行包；公开仓库保留本报告、补丁与复现命令。当前用户 Temp 中保留：

- `system-skills-76d7-v0163-cold-20261023-a1`
- `system-skills-76d7-v0163-warm-20261023-a1`
- `system-skills-76d7-v0163-serial-20261023-a1`
- `system-skills-76d7-v0163-mixed-20261023-a1`
- `ecommerce-host-76d7-v0163-preflight-20261023-a1`
- `system-skills-76d7-patched-cold-20261023-a1`、`system-skills-76d7-patched-warm-20261023-a1`：首个 LF SQL 构建的成功对照。
- `system-skills-76d7-patched-mixed-stable-20261023-a1`：首个构建的迁移不兼容失败。
- `system-skills-76d7-patched-{cold,warm,serial,mixed-stable,mixed-desktop}-20261023-a2`：最终候选的五批完整记录。

本仓库 `.eval-runs/system-skills-76d7-upstream-ac896c2c5dcd408bb1bb66e76fbd194d` 保存固定提交源码、官方 API 搜索／PR／Issue 响应及 `v0163-metrics.json`。`gh api` 曾 TLS 握手超时，后续通过 PowerShell 正常 HTTPS 校验读取同一官方源；未关闭 TLS 验证或修改认证。

`.eval-workspaces/codex-76d7-0163` 保存原始源码、逐文件备份、构建日志、锁比较、原生测试、`migration-comparison.json`、`sql-build-inputs.json`、`patch-validation.json`、`final-app-server-metrics.json` 及保留状态核对；`.eval-cache/rust-1.95.0-76d7` 保存便携编译器及归档校验材料，短路径 Cargo 缓存仅属于本轮构建。均未移除，方便审阅失败与复验。

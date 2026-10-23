# 系统内置技能冷启动更新失败：根因、修复与免费复验

2026-10-23，Beads `76d.4`；上游剩余项 `76d.7`。本轮没有收费出图，没有关闭执行策略、扩大目录授权或替换已安装 Codex。

## 结论与修复边界

已定位并复现：**共享系统技能缓存的非原子更新存在进程竞争**。0.153.0 在内置包指纹不匹配时，直接删除 `CODEX_HOME/skills/.system`，再逐个写文件，最后写 marker；没有跨进程安装锁。两个进程同时更新时，会相互删除／读取正在变化的目录。不同版本共用缓存，还会持续使对方的包指纹过期。

本仓库已修复验证器引入的触发方式：显式选择与当前共享缓存匹配的已安装 CLI；在启动模型前校验完整系统包和真实发现结果；增加本仓库进程锁、每次运行前后完整性检查，并把系统技能安装错误视作失败。没有用关闭 bundled skills 或忽略日志的方式取得通过。

**没有修改 Codex 二进制内的安装器。** 其他应用不会遵守本仓库的锁；不同构建直接共用该目录的上游问题仍由 `76d.7` 跟踪。本文的通过结论限定为修复后的验证入口和本次环境，不宣称所有原生 CLI／Desktop 混跑方式已修复。

## 1. 原始失败与现场检查

此前 0.153.0 免费主集的 `explicit-r1/stderr.txt` 在 `2026-10-23T01:14:30Z` 报：

```text
codex_skills_extension::host_service:
failed to install system skills:
io error while remove existing system skills dir: 拒绝访问。 (os error 5)
```

当时进程退出 0，仓库 Skill 和免费 MCP 也完成；旧 runner 因此只记录了错误布尔值，没有将其判为失败。这正是必须同时检查安装日志、系统包完整性和发现目录的原因。

本轮只读核对得到：

| 项目 | 观测 |
|---|---|
| PATH CLI | `C:/nvm/.nodejs/codex.exe`，0.153.0 |
| 当前 Desktop CLI | `C:/Users/Administrator/AppData/Local/OpenAI/Codex/bin/6257d9e8f63c0f2b/codex.exe`，0.163.0-alpha.11 |
| 共享缓存 | `C:/Users/Administrator/.codex/skills/.system` |
| 本人对 skills、.system 及抽查文件的授权 | FullControl；抽查对象无显式 Deny、无 ReadOnly 属性 |
| 缓存 Owner | 本人个人 SID；不是前一个 `.sandbox-bin` 的管理员组所有者问题 |
| 0.153.0 内置包 marker／技能数 | `9ba055b801325a`／6 |
| 当前 Desktop 内置包 marker／技能数 | `f7cfaf1d6d464589`／5 |
| 本轮真实验证前后共享缓存 | 与 Desktop 包的完整文件摘要一致，目录修改时间保持 `2026-10-23T01:28:02Z` |

缓存中的沙箱 capability Deny ACE 没有被删除、替换或放开。本次没有依据 `os error 5` 对 `.system` 执行 takeown、icacls grant/reset 或取消继承。

Windows 的拒绝访问也可能与对象的删除状态、并发句柄有关；微软说明目录删除可能等待最后一个句柄关闭，处于待删除状态的文件也可能返回 `ERROR_ACCESS_DENIED`。不能只凭错误码就决定扩大 DACL。这里未捕获内核句柄轨迹，不能断言每一次拒绝对应哪个底层分支。[RemoveDirectoryW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-removedirectoryw)、[CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)

## 2. 对应版本源码与受控复现

核对 OpenAI Codex `rust-v0.153.0` 固定版本源码：

- `codex-rs/skills/src/lib.rs:77–100`：校验 marker；不匹配则 `remove_dir_all`，逐文件写入，最后写 marker。这段安装路径没有跨进程锁或原子目录切换。
- `codex-rs/ext/skills/src/host_service.rs`：构造服务及加载快照时调用安装；失败只记录错误，技能发现仍可能继续。

两份实际源码保存在本机 Temp 的 `codex-policy-76d-source`。SHA256 分别为 `cbdea9b288d42851efbe3c302f62c5ab07f23134be27775139c772cf3e9b6a21`、`4e73a4d6b97c85e8d9b564411c020f1c3f0ac860fee4da9eaa65a2c39c4eadd6`。版本依据与既有源码调查衔接，见[原专项记录](WINDOWS-SANDBOX-76d.md)。

新增 [probe_system_skills.py](../scripts/probe_system_skills.py)，通过实际 app-server 的 `initialize → initialized → skills/list` 验证。仅对子进程指定全新夹具目录作为 CODEX_HOME，不更改父进程环境，不复制认证或用户配置，不创建 thread／turn，不启动 MCP。实际初始化和发现协议也与[官方 app-server 说明](https://learn.chatgpt.com/docs/app-server)核对。

所有过期 marker 都只写入自建的临时夹具。先串行初始化独立 SQLite 状态，再仅令系统技能 marker 过期，避免把数据库初始化竞争算成技能安装竞争。全程使用普通令牌，不修改 ACL 或 PowerShell 策略。

| 控制实验 | 实际进程 | 安装错误 | 目录发现结果 |
|---|---:|---:|---|
| 0.153.0，过期缓存，2 并发 × 8 轮 | 16 | 15，均含同型 remove／os error 5 | 8 次只列出 4 或 5 项，应为 6 |
| 0.153.0，同样过期缓存，串行 × 3 轮 | 3 | 0 | 3 次均完整发现 6 项 |
| 0.153.0，串行安装完成后，2 并发 × 8 轮 | 16 | 0 | 16 次均完整发现 6 项 |
| 0.153.0 与 Desktop 构建混跑，2 并发 × 4 轮 | 8 | 旧版 4/4 报同型错误 | 旧版部分目录最少只有 1 项；Desktop 第一轮也出现多列项目，不能只靠其无错误日志认定完整 |

这 43 个受测进程外，各轮还有一个串行初始化进程；均未请求模型推理或 MCP。第一批未隔离 SQLite 初始化的探针另外保留，发生过 2 次数据库初始化失败，未混入上表的系统缓存统计。

原始那条失败日志没有保存失败子路径、对方 PID 或句柄，因此不能追认当时的竞争者究竟是另一个 0.153.0 进程还是 Desktop。可以确定的是：原 runner 使用同一用户目录并发冷启动，存在相同触发条件；控制实验在本人有权限、未改变 ACL 的目录中重复产生了相同错误，热缓存对照则全部通过。

## 3. 修复内容

### 3.1 明确 CLI 与包的对应关系

[run_host_smoke.py](../scripts/run_host_smoke.py) 新增必填 `--cli`，每个进程使用同一明确路径，记录版本和可执行文件 SHA256，不再隐式追随 PATH。

[system_skills_guard.py](../scripts/system_skills_guard.py) 先在独立夹具安装该 CLI 自带的系统包，取得 marker、完整文件摘要和应有技能路径；再对比现有共享缓存。marker、文件集合或摘要任一不匹配，就在启动模型前停止，保留缓存，不自动删除重装。

因此，原 PATH 0.153.0 对当前 Desktop 缓存的负例已实际验证：期望 `9ba055b801325a`，实测 `f7cfaf1d6d464589`，guard 拒绝启动；没有运行该次模型请求或真实 MCP。

正例明确选择当前已安装 Desktop CLI，取得匹配的 5 项系统技能，完整包与共享缓存前后相同。这改变了本轮验证目标版本，**不是升级、替换或宣称修复了旧 0.153.0**。历史 0.153.0 主集和恢复回归仍独立保留。

### 3.2 不再把部分成功算成通过

- 在共享缓存已匹配后，执行一次真实、无模型的系统技能发现；退出 0 但缺项、越界路径或安装日志报错，均失败。
- 本仓库 runner 之间使用跨进程文件锁；它只协调本项目，不声称约束 Desktop 或其他程序。
- 每次模型进程启动前、完成后以及整批结束时检查缓存；检测外部变化则失败，不盲目重试。
- 发现 `failed to install system skills` 时，状态为 `system_skill_install_failed`，即使进程退出 0、有回复文件也不能通过；保留原 helper／资源拒绝分类。
- 新输出目录不允许复用，避免覆盖旧轨迹。免费工具白名单、只读、Never 审批以及生成／编辑／批准／重试禁用保持不变。

新增 [test_system_skills_guard.py](../tests/test_system_skills_guard.py) 覆盖跨版本拒绝且不触碰共享缓存、完整包检查、缺项／越界目录、退出 0 的安装错误、旧失败分类和真实竞争进程锁。没有为通过测试更改真实权限。

## 4. 修复后的真实免费 Host 主集

本轮使用 **0.163.0-alpha.11**，4 类请求各 3 次、2 并发；与此前 0.153.0 批次分别记录。使用相同 8 文件 Skill 包、合成商品／参考夹具和最小设计档案，不向请求注入 Skill 正文，不连接 mock MCP。主 Agent 阅读全部 12 份最终回复并核对完成的工具轨迹，没有独立第二模型评分。

| 场景 | 结果 | 行为核对 |
|---|---|---|
| explicit | 3/3 | 实际查询两个指定服务的免费模型／配置入口；图片映射为空，首次商品出图仍需图片和完整方案确认，没有推定出图授权 |
| implicit | 3/3 | 每次真实 inspect 返回 2 张 PNG；P01 为合成商品依据、R01 仅风格，未借用其商品颜色或布局；完整文字草案标为待审 |
| negative | 3/3 | 直接回答 Python 学习计划，无 shell、图像 MCP 或电商技能资源读取 |
| recovery | 3/3 | 读取实际 JSON 与资源，回退 S2 布局并更新 S3；M01、事实和角色保留，缺失的 M02 历史批准状态为 unknown；不假称本轮看图，不调用图片服务 |

12 个进程全部退出 0；**19 次 shell 命令全部退出 0，9 次真实免费 MCP 调用成功，6 个 image 内容块**。调用为 GPT guide 3 次、Nano models 3 次、Nano inspect 3 次；started／completed 不重复计数。收费、批准、编辑、生成或重试工具尝试为 0。

系统技能安装错误、包漂移、helper 失败、资源读取拒绝均为 0。预检的真实共享目录发现为完整 5 项，整批前后仍与该构建的完整包相同。

另用本轮 Desktop CLI 做了一次独立只读边界检查：实际命令身份为 `CodexSandboxOffline`、非管理员；原 `.ps1` 探针读取退出0，写入退出1，目标未生成，类型／HResult／路径对应的拒绝记录有效。证据为本仓库 `.eval-runs/system-skills-76d4-boundary-7fa759407cb94c1b8f081ea0428b71a1`；没有改写执行策略。

`explicit-r2` 曾报模型清单刷新超时；其实际模型回复和两个免费 MCP 查询均完成。PowerShell shell snapshot 不支持的警告也单独保留。这些不冒充系统缓存故障，也不被“安装错误为 0”一句覆盖。

## 5. 检查、摘要与证据

49 项确定性检查通过，结构／资源／42 场景格式检查通过。标准库探针最初由 uv 选择 3.14 创建环境，正式控制实验随后显式使用既有 CPython 3.12；项目环境按现有锁文件离线恢复为 **CPython 3.12.14、PyYAML 6.0.3**，没有升级锁或依赖版本。

本次没有修改 Skill 入口或资源。摘要保持：

| 文件 | SHA256 |
|---|---|
| SKILL.md | `9f5c2ee8c74a1910cef2d6b4cd9a97d047ecb28208a0348066343ac49b459527` |
| references/design-record.md | `11ee11fd955e76c855c34e0682059730fa4648985ba818a444e0f20d3d363942` |
| scripts/run_host_smoke.py | `5ca57eff89adc54195f4a2f49d521795dcd780129f2d2e509fb6906bece0cfda` |
| scripts/system_skills_guard.py | `948829eb759d6810c39f580bf2b7e6e6f9d4592f8589390eb48edd9f2c93ff1f` |
| scripts/probe_system_skills.py | `a716cc933dd008b20a6c0967bfce69639b68979877a628ce8e37a8d609a14aef` |

原始证据位于当前用户 Temp，公开仓库只保留安全报告与复现源码：

| 目录名 | 内容 |
|---|---|
| `system-skills-76d4-cold-20261023-a1` | 第一批探针，包括单独识别的 SQLite 竞争失败 |
| `system-skills-76d4-cold-20261023-a2` | 隔离数据库因素后的 8 轮冷缓存竞争 |
| `system-skills-76d4-warm-20261023-a1` | 8 轮热缓存对照 |
| `system-skills-76d4-serial-cold-20261023-a1` | 3 轮串行冷更新对照 |
| `system-skills-76d4-mixed-20261023-a1` | 4 轮不同构建共享缓存 |
| `ecommerce-host-76d4-mismatch-20261023-a1` | 旧 CLI 被预检拒绝；未运行模型或 MCP |
| `ecommerce-host-76d4-fixed-20261023-a1` | 12 次真实 Host 主集、预检、命令、回复、事件、stderr、mechanical-audit.json 与 semantic-review.json |

探针逐次保存命令、仅允许的协议请求、响应、stderr、结果与文件清单；Host 预检保留独立包、共享包前后摘要及完整系统目录发现。旧 `.eval-runs` 沙箱／Owner 证据及此前全部 Host 批次不覆盖。

## 6. 复现与后续边界

普通权限、仓库根目录、已有锁定开发环境；输出目录必须是新的仓库外路径。以下仅复现缓存层，无模型和 MCP 请求，不测试沙箱命令执行：

```powershell
$CacheProbe = Join-Path ([IO.Path]::GetTempPath()) ('system-skills-cold-' + [guid]::NewGuid().ToString('N'))
uv run --frozen --no-sync --group dev python -X utf8 -B scripts/probe_system_skills.py --output $CacheProbe --cli 'C:\nvm\.nodejs\codex.exe' --mode cold --rounds 8 --clients 2
```

热缓存对照改为 `--mode warm` 且使用另一个新目录。混跑需明确提供 `--mode mixed --peer-cli <另一实际exe>`。探针是诊断工具，退出 0 只代表证据采集完成，故意制造的安装失败仍是失败记录，必须读各轮结果。Temp 中对子进程 helper alias 的拒绝警告保留，未绕过该保护；这里没有执行任何 helper 命令。

运行完整免费 Host 验证时，明确选择当前已安装、且与共享系统包匹配的 CLI：

```powershell
$HostEvidence = Join-Path ([IO.Path]::GetTempPath()) ('ecommerce-host-guarded-' + [guid]::NewGuid().ToString('N'))
uv run --frozen --no-sync --group dev python -X utf8 -B scripts/run_host_smoke.py --output $HostEvidence --cli 'C:\Users\Administrator\AppData\Local\OpenAI\Codex\bin\6257d9e8f63c0f2b\codex.exe' --cases explicit,implicit,negative,recovery --repeats 3 --workers 2
```

这会消耗模型推理，但不调用收费出图；仍需核对实际回复与工具轨迹。若客户端升级、指纹不匹配或缓存变化，保留证据停止，重新核对实际已安装的版本；不复制凭据、修改 marker、关闭系统技能或扩大 ACL 来通过 guard。

`76d.4` 按根因诊断、本仓库修复和免费复验范围完成；上游原子更新／跨版本缓存隔离仍由 `76d.7` 跟踪，未对外发帖或提交 PR。实际商品、付费生成、供应商质量和用户视觉验收仍未运行，仍须先确认具体商品方案。

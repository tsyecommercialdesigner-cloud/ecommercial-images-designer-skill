# Windows 沙箱账户、PowerShell 策略与 DACL 权限故障复盘

记录日期：2026-10-23。关联 Beads：`76d.2`、`76d.4`、`76d.6`。

本文把一次实际跑通的排障过程整理为可复用的工程报告。所有“已验证”结论均对应本机日志；Windows 通用机制引用微软文档；版本相关行为依据本次实际 CLI 和对应源码。编写本文没有再次修改系统配置，也没有调用收费出图。

后续更新：76d.4已通过控制实验定位为共享系统技能缓存的非原子更新竞争，并修复本仓库验证器、完成匹配Desktop构建的12次免费Host复验，见[专项报告](SYSTEM-SKILLS-76d4.md)。下文前阶段故障与未决判断保留为历史；上游跨版本缓存缺陷由76d.7继续跟踪，Owner／执行策略撤销仍未实测。8.4的可选Host命令已同步为带显式CLI和完整性guard的当前入口，原WinPS5.1／0.153.0沙箱验收命令不变。

## 1. 结论与适用范围

这次并非一个权限开关造成全部故障。至少有三组相互独立的问题：

1. **配置与启动链路**：隔离测试丢失 Windows 沙箱后端配置；探针又经历了参数、引号、目标 Shell 和模块搜索路径问题。
2. **脚本执行策略**：主账户、沙箱独立账户，以及 Windows PowerShell 5.1、PowerShell 7 使用的有效配置不同。
3. **Windows 对象权限**：普通进程能修改目录内容，却缺少重写该目录 DACL 的权限；管理员运行通过后，普通终端仍然失败。

最终成功包含两项经用户确认的持久系统变更，以及几项诊断程序修正：

| 变更 | 实际范围 | 已验证结果 |
|---|---|---|
| Windows PowerShell 5.1 的 `LocalMachine` 策略：`Undefined → RemoteSigned` | 该引擎的机器作用域，影响所有账户的策略计算；高优先级配置仍可覆盖 | `CodexSandboxOffline` 的实际有效策略成为 `RemoteSigned`，本地探针可加载 |
| `.sandbox-bin` 所有者：Administrators 组 → 原用户个人 SID | 只改这个目录对象；不递归，DACL、主组、继承保护位前后一致 | 用户普通终端及 Agent 普通进程均可准备 helper、读取 Skill，且只读写入被拒绝 |
| 固定系统 Shell、明确导入配套系统模块、修正参数和拒绝归因 | 项目测试脚本与免费集成 runner | 避免启动错误、模块错误或中文乱码被误判为沙箱权限结果 |

**修复成功不等于所有相关问题都已解决。** 系统内置技能冷启动更新的另一个 `os error 5` 仍由 `76d.4` 跟踪；恢复旧所有者及撤销执行策略尚未实际执行。免费集成通过也不代表收费绘图或用户视觉验收通过。

### 本次验证的环境

| 项目 | 实际环境 |
|---|---|
| 仓库 | `E:\agent-skills-workspace\ecommercial-images-designer-skill` |
| 实际测试 CLI | `C:\nvm\.nodejs\codex.exe`，`codex-cli 0.153.0` |
| Desktop 另一份内置 CLI | 已识别为 `0.163.0-alpha.11`，没有替换本次测试入口 |
| 用户终端 | Microsoft Store PowerShell `7.6.7` |
| 沙箱内固定 Shell | 系统 Windows PowerShell `5.1.26100.9711` |
| 原始 Windows 用户 | `TSY-ICECREAM\Administrator`，分别测试其提升和普通令牌 |
| 实测沙箱命令身份 | `TSY-ICECREAM\CodexSandboxOffline` |
| 沙箱边界 | Windows `elevated` 后端、`read-only` 权限、`approval_policy="never"` |

`elevated` 是沙箱实现／设置方式的名称，不表示沙箱命令以管理员权限运行。当前官方文档还介绍了 MXC 等实现；本文的账户、helper 和所有者结论针对本次验证的旧式 elevated 链路，不能直接外推到所有版本。[OpenAI Windows 沙箱说明](https://learn.chatgpt.com/docs/windows/windows-sandbox)

## 2. 故障链：相似的错误分别发生在哪里

| 阶段 | 观测到的失败 | 原因与处置 | 不能据此推断的结论 |
|---|---|---|---|
| 隔离 CLI 读取资源 | `blocked by policy` | `--ignore-user-config` 丢失原有 Windows 后端配置；runner 明确指定 `windows.sandbox="elevated"`，保留只读、Never 和执行规则 | 不是所有只读命令都需要 allow 规则，也不是关掉规则才能运行 |
| 初版探针参数 | 缺少 `--permission-profile`；`cmd /c` 引号导致路径语法错误 | 按实际 `--help` 补参数；改用普通 `-File` 和独立参数传递 | 目标读取尚未发生，不是文件访问拒绝 |
| 普通权限准备 helper | `helper_sandbox_lock_failed`、`SetNamedSecurityInfoW ... failed: 5` | `.sandbox-bin` 重写 DACL 的权限不足；主账户普通工具和独立普通终端均复现 | 尚未执行 PowerShell，无法借此判断沙箱账户的执行策略 |
| 沙箱启动 Store Shell | `CreateProcessAsUserW failed: 5` | 探针继承调用者 `$PSHOME`，指向 WindowsApps；固定为系统 Windows PowerShell | 本次启动被拒绝不证明所有 Store PowerShell 都不可用于任何沙箱 |
| 固定诊断参数 | 中间 CLI 代理报 `InvalidBatchScriptArg` | 将固定、纯查询的诊断参数组成单行；不执行被拒绝探针的等价内联代码 | 参数通过不等于沙箱启动或读写通过 |
| 查询策略 | `Get-ExecutionPolicy` 的模块自动加载失败 | 查到继承的 PS7 模块路径；显式导入 WinPS5.1 配套模块后可查询 | 查询失败时策略为“未知”，不能先填成 `Restricted` |
| 加载 `.ps1` | `SecurityError`、`UnauthorizedAccess`，系统禁止运行脚本 | 实测 Offline 账户五作用域全 `Undefined`，有效值 `Restricted`；用户确认机器策略配置后恢复 | 主账户或 PS7 能运行脚本，不证明 Offline/WinPS5.1 能运行 |
| 判定写入拒绝 | 包装脚本提示无法归因，但底层出现访问被拒绝 | 旧中文文本匹配受编码和措辞影响；改核对异常类型、HResult、操作、路径与文件是否生成 | 任意非零退出或任意“拒绝访问”都不能作为只读边界通过 |
| 首次所有者修复 | `icacls /setowner` 退出 5 | 前后所有者与 DACL 未变；改用受控的 `takeown`，保存失败和成功两份历史 | 没有证据断定该次失败一定由某个具体特权状态造成 |
| 修复后的免费 CLI | 资源读取成功，个别进程报系统技能安装／删除目录 `os error 5` | 作为独立问题 `76d.4` 保留，未扩大权限处理 | 不能把它与已修复的 `.sandbox-bin` 故障合并，也不能说根因已明 |

包装脚本中的 `throw` 行号只是检查发现失败的位置。诊断需要继续向下查看底层 API、错误码、进程身份和对应日志，而不是反复修改包装行。

关于最初的策略拒绝：当时对默认规则的检查未匹配拒绝项；结合对应版本源码，定位到未选用可执行文件系统隔离的 Windows 后端后产生的保守拒绝。该检查不代表穷尽全部托管策略。固定源码链接及原始判断过程保留在[专项诊断记录](WINDOWS-SANDBOX-76d.md)和[宿主复验记录](HOST-RETEST.md)。

## 3. 执行策略必须按“账户 × 引擎 × 作用域”核对

### 3.1 修复前的实测矩阵

下表的“账户”指实际运行目标 PowerShell 的身份，不是外层终端标题。

| 实际账户／引擎 | MachinePolicy | UserPolicy | Process | CurrentUser | LocalMachine | 有效策略 |
|---|---|---|---|---|---|---|
| 原用户／Windows PowerShell 5.1 | Undefined | Undefined | Undefined | RemoteSigned | Undefined | RemoteSigned |
| 原用户／PowerShell 7.6.7 | Undefined | Undefined | Undefined | Undefined | RemoteSigned | RemoteSigned |
| CodexSandboxOffline／Windows PowerShell 5.1 | Undefined | Undefined | Undefined | Undefined | Undefined | Restricted |
| CodexSandboxOffline／PowerShell 7 | 未测 | 未测 | 未测 | 未测 | 未测 | 未测 |
| 其他沙箱账户／两个引擎 | 未测 | 未测 | 未测 | 未测 | 未测 | 未测 |

前两行有效值相同，来源却不同；第三行是独立账户，不能继承原用户的 `CurrentUser` 设置。不能把“某账户五项均未配置”描述成管理员为它显式设了 `Restricted`。

Windows PowerShell 5.1 与 PowerShell 6+ 的执行策略分开存储、分开管理。一个终端里看到 `RemoteSigned`，不足以证明另一个引擎同样配置。`LocalMachine` 才是这里的机器作用域名称，不要与来自组策略的 `MachinePolicy` 混用。[微软 Set-ExecutionPolicy 说明](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/set-executionpolicy?view=powershell-5.1)

### 3.2 为什么只改本人 CurrentUser 没有解决沙箱

策略按优先级计算：

```text
MachinePolicy > UserPolicy > Process > CurrentUser > LocalMachine
```

这不是“最严格的值总是优先”。全部未定义时，Windows 客户端采用 `Restricted` 默认值。`Restricted` 不允许运行脚本，单纯给脚本签名也不能解决。`RemoteSigned` 允许本地未签名脚本，对带互联网来源标记的脚本仍有签名等要求。[微软执行策略说明](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1)

本次探针未发现 `Zone.Identifier`，因此没有用批量解除下载标记处理它。管理员也没有给隐藏的沙箱账户逐个登录、填写用户策略；用户明确选择了 WinPS5.1 的机器范围配置。随后实测 Offline 账户的 `LocalMachine` 和有效值均成为 `RemoteSigned`，原账户的 `CurrentUser=RemoteSigned` 保留，PS7 的原配置未改。

如果企业的 `MachinePolicy` 或 `UserPolicy` 已有要求，应交由策略管理员处理。设置较低作用域不能合法替代该要求。本文不提供 Process Bypass、编码命令或将被拒绝文件改写为内联执行的替代路径。

执行策略用于减少误执行，是防御措施，**不是 Windows 安全隔离边界**；令牌、文件访问控制以及沙箱实现仍各自生效。诊断显示的 `FullLanguage` 是 PowerShell 语言模式，也不代表任意文件读写权。[微软执行策略与安全边界说明](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1)

## 4. 固定 powershell.exe 后，为什么仍会加载错模块

选择正确可执行文件解决的是“运行哪个引擎”。它不会自动保证“从哪里找到模块”。本次实际调用经过中间原生进程，链路可概括为：

```text
PowerShell 7 → 原生 CLI／代理／helper → Windows PowerShell 5.1
```

微软说明，PS7 直接启动 WinPS 时会清理传入的 PS7 模块路径；经过原生中间进程时，该清理不一定发生。子进程可能继续继承 PS7 的 `PSModulePath`，并优先找到无法加载的同名模块。[微软 PSModulePath 说明](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_psmodulepath?view=powershell-7.6#starting-windows-powershell-from-powershell-7)

本次证据分为三个层次：

- 沙箱旧查询确实报 `CouldNotAutoloadMatchingModule`；由于对象构造中途失败，旧实现连已取得的身份信息也没有输出。
- 本账户的原生中间进程复现了继承 PS7 路径后按名称导入失败；随后成功的沙箱诊断也确实包含 PS7 路径。原始沙箱失败的完整内部异常未捕获，不能把复现的内部异常逐字套回原现场。
- 诊断显式从正在运行的 WinPS5.1 `$PSHOME\Modules` 导入配套 Security、Utility manifest 后，宿主和沙箱查询均成功。没有修改机器／用户全局 `PSModulePath`。

修正后，策略诊断同时保存 `identity`、版本、`PSEdition`、`PSHOME`、继承的 `modulePath`、语言模式、实际加载模块路径、有效策略和五个作用域。即使 JSON 模块加载失败，也用 Console 保留已知上下文和异常。`-PolicyDiagnosticsOnly` 只运行这些查询并保存证据，不执行后续 `.ps1` 读写验收。

这里的普通模块导入仍接受正常策略检查，没有 Force 导入、程序集注入或执行被阻止脚本的替代实现。目标是消除错误的模块解析，而非取消策略。

## 5. DACL 故障的核心：能修改内容，不等于能修改权限

### 5.1 Windows 对象的几项信息需要分开看

文件或目录的安全描述符包含所有者、主组、DACL、SACL 与控制位。DACL 中的 ACE 按用户／组 SID 描述允许或拒绝的权限；所有者是独立字段，不能只看 ACL 授权列表就忽略它。[微软安全描述符说明](https://learn.microsoft.com/en-us/windows/win32/secauthz/security-descriptors)

| 权限／字段 | 含义 | 本次容易混淆之处 |
|---|---|---|
| 读写、执行、删除内容 | 操作目录及文件内容 | 这些能力不足以重写 DACL |
| `READ_CONTROL` | 读取安全描述符中的部分信息 | 能 `Get-Acl` 不代表能 `Set-Acl` |
| `WRITE_DAC`，位 `0x00040000` | 修改 DACL | helper 调用要求的关键能力 |
| `WRITE_OWNER`，位 `0x00080000` | 修改所有者 | 与 `WRITE_DAC` 是不同权限 |
| Owner | 对象所有者 SID | 通常具备隐式修改 DACL 的能力，须结合所有者权限限制等实际描述符判断 |
| 继承保护位 | 控制是否继承父对象权限 | 不是 DACL 故障的统一“开关”；本次保留原值 |

权限区分见[微软标准访问权限](https://learn.microsoft.com/en-us/windows/win32/secauthz/standard-access-rights)。所有者隐式 `WRITE_DAC` 及取得所有权的特权机制见[微软对象所有者说明](https://learn.microsoft.com/en-us/windows/win32/secauthz/owner-of-a-new-object)。目录的 `ReadOnly` 文件属性也不能替代 DACL 检查。

### 5.2 本次 .sandbox-bin 的具体冲突

修复前，目标是 `C:\Users\Administrator\.codex\.sandbox-bin`：

- 所有者为 `BUILTIN\Administrators`，即 `S-1-5-32-544`，不是原用户个人 SID。
- 原用户的显式允许掩码为 `0x1301bf`，属于可读、写、执行、删除的 Modify 类组合，**没有 `WRITE_DAC` 或 `WRITE_OWNER` 位**。
- 沙箱组为 `0x1200a9` 的读取／执行组合；DACL 受继承保护。
- 普通令牌中 Administrators 组是仅用于拒绝的状态，不能用该组取得允许权限；个人也没有取得该对象的所有者身份。

因此，普通用户能访问 helper 文件，并不代表普通进程能调用 `SetNamedSecurityInfoW` 重写父目录 DACL。对应 0.153.0 源码的 `lock_sandbox_bin_dir` 给本人配置的也是 Modify 类权限；刷新链路仍会锁定 bin 目录，`lock_sandbox_dir` 写入 DACL 时没有一并纠正所有者。源码定位及采集过程见[专项记录](WINDOWS-SANDBOX-76d.md)。

这组实际 ACL、普通令牌、API 失败点和源码共同解释了本次 `helper_sandbox_lock_failed`。管理员探针通过后，所有者仍是管理员组，普通令牌仍缺少所需权限；用户随后在独立普通 pwsh 中复现相同失败，排除了“只在 Agent 工具里发生”的判断。

UAC 下，同一个用户名可以使用不同的令牌运行进程。管理员组成员通常以标准令牌执行日常应用，提升后才使用管理员令牌。本机“用户名是 Administrator，但 administrator=false”正是必须记录实际令牌的原因；不能仅看账户名或终端提示符。[微软 UAC 工作机制](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/user-account-control/how-it-works)

### 5.3 为什么采用所有者修复，以及 icacls 为什么不算成功

第一次获准的 `icacls /setowner` 实际返回拒绝访问、退出 5；前后状态一致。这份失败记录保留。它不能证明 `icacls` 普遍无效，也没有足够证据证明当时一定缺少或禁用了哪项特权。[微软 icacls 说明](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/icacls)

修正版先检查原用户的提升令牌中是否存在 `SeTakeOwnershipPrivilege`，再调用 Windows 的 `takeown`，只把目标目录所有者改为本人。特权“存在”与“当前已启用”不同；本次不依赖本地化的 Enabled/Disabled 文本判断，更没有向账户授予新特权。取得所有权、设置任意所有者与重写 DACL 不是同一操作。[微软对象所有者说明](https://learn.microsoft.com/en-us/windows/win32/secauthz/owner-of-a-new-object)、[令牌特权说明](https://learn.microsoft.com/en-us/windows/win32/secauthz/enabling-and-disabling-privileges-in-c--)

受控脚本使用的原生操作相当于：修复时 `takeown /f <唯一目录>`；恢复原管理员组所有者时才增加 `/a`。不使用 `/r`，也不使用与递归配合、可能替换目录权限的 `/d Y`。[微软 takeown 参数说明](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/takeown)

实际成功后只改了 Owner；DACL、主组、保护位逐项核对一致。没有递归接管 `.codex`，没有新增 Everyone／FullControl 授权，没有调整沙箱账户、WindowsApps 权限、后端或防火墙规则。

**“DACL 不变”不等于“有效权限完全不变”。** 本人成为所有者后，取得管理该目录 DACL 的能力，恰好满足普通 helper 刷新的要求。这是一项有实质安全影响的定点修复，而不是无副作用的元数据整理。

本项目的 [Repair-WindowsSandbox76dOwner.ps1](../scripts/Repair-WindowsSandbox76dOwner.ps1) 是基于现场证据的本机脚本，**不是 Codex 官方通用修复命令**。它限定原账户、唯一目录和非重解析路径；备份所有者／组／DACL／保护位；状态不匹配就停止，避免覆盖之后的管理员改动。

## 6. 正确验收：成功读取和正确拒绝必须同时成立

### 6.1 不能把“写入命令失败”直接当成隔离通过

旧探针按中文报错匹配拒绝；实际结果出现编码损坏和“访问被拒绝／拒绝访问”的不同措辞，导致误判。那次未单独保存完整写入退出状态，因此没有事后把旧结果改写成正式 PASS。

当前探针输出 ASCII 机器记录，包含根异常类型、HResult、操作和 UTF-8 路径数据：

```text
SANDBOX_PROBE_ERROR_V1|operation=Write|type=System.UnauthorizedAccessException|hresult=-2147024891|pathUtf8Base64=<目标路径数据>
```

路径的 Base64 只是日志数据，不是可执行的编码命令。正式通过要求同时满足：

1. 普通外层进程 `administrator=false`，且使用指定 CLI 和原账户。
2. 合成文件及真实 Skill 入口读取均退出 0，并返回预期内容。
3. 写入退出非 0，目标文件不存在。
4. 恰好出现一条与本次写操作、目标路径、根异常类型及 HResult 相符的拒绝记录。
5. 没有 helper、Shell 启动等前置故障；目录不存在、参数错误也不算权限拒绝。

管理员运行即使全部读写检查通过，仍输出 `normalUserAccepted=false`。只有另开普通终端，重新走完整 helper 和探针链路，才构成普通权限验收。

### 6.2 已取得的证据与剩余问题

以下目录均在本仓库的本地 `.eval-runs` 下，未作为公共原始日志发布：

| 证据目录名 | 证明的内容 |
|---|---|
| `sandbox-76d-fe081260beba431fbdc9e6ee15671d15` | 修复前原用户／Offline 账户五作用域与实际模块路径 |
| `sandbox-76d-1939752e35624b9ab969c3c088c3daec` | 策略配置后已可读取；旧写拒绝文本归因不足，保留失败 |
| `sandbox-76d-38dd2537b86646a9aa22ff03d3fa4a80` | 管理员完整探针通过，但没有普通权限验收资格 |
| `sandbox-76d-0a2d911597a343b5aa06da97a8a47568` | 用户独立普通终端仍复现 helper 锁权限失败 |
| `owner-76d-85163ed878ca49c8bbe70fd0371bc193` | 首次 icacls 修复失败、状态未变 |
| `owner-76d-7bf4303310fe480d9ebcf67817d494e1` | takeown 成功；备份与前后不变量核对 |
| `sandbox-76d-394ed662fa3e4f2bbdd1b0d1ab02b585` | 用户普通终端读／写拒绝验收通过 |
| `sandbox-76d-97026d310f3b4c299a7d7cf446e4a6a8` | Agent 普通进程独立验收通过 |

两次普通权限成功结果一致：`readExit=0`、`skillReadExit=0`、`writeExit=1`、`writeFileExists=false`、`normalUserAccepted=true`；另有 `write-result.json` 的 `attributableDenial=true`。

其后完成了 4 类请求各 3 次的真实 CLI 免费集成主集：12 个进程、27 次 shell 命令、9 次真实免费 MCP 调用成功，资源拒绝和 helper 失败均为 0。恢复场景另发现确认措辞问题，修正后再运行 3 次独立恢复回归，全部通过。完整边界见[免费 CLI 复验报告](HOST-CLI-RECOVERY.md)。

仍未验证／未解决的内容：

- `76d.4`：主集 1/12 出现系统内置技能冷启动更新／删除目录的 `os error 5`；后续串行 0/3 不足以证明并发是根因，也没有完成该问题修复。
- 其他沙箱账户、Offline 账户的 PS7、MXC、新 CLI 版本以及干净账户／干净安装组合。
- 恢复旧 Owner、撤销机器策略后的实际操作；本文只提供受控撤销步骤，没有为了写报告破坏当前可用状态。
- 收费图像生成、真实商品和用户视觉验收；必须另行展示并确认具体方案，不能由免费测试结果替代。

## 7. 可复用的排障方法

下一次再遇到“拒绝访问”，先确定故障所在层，再决定是否需要管理员：

| 先核对的事实 | 处理原则 |
|---|---|
| 哪个 exe、版本与 Windows 后端正在执行 | 不混用 PATH、Store、Desktop 内置版本；新文档命令先核对本版本帮助 |
| 外层进程和目标命令各自的 SID／令牌 | 同用户名不代表同令牌；主账户不代表沙箱账户 |
| 目标 Shell 的五作用域及有效策略 | 按账户和引擎采样；组策略要求由对应管理员处理 |
| 实际模块路径和加载来源 | 修正错误解析；避免把系统模块问题误判成脚本策略拒绝 |
| 底层 API 请求的权限 | 区分读写内容、WRITE_DAC、WRITE_OWNER 和特权；先检查 Owner 与 DACL |
| 修复前后的对象状态 | 定点、备份、非递归；核对实际变化，不只看命令退出 0 |
| 普通权限的正向与负向行为 | 读取成功并且写拒绝可归因；管理员通过不能代替普通验收 |

`icacls /save` 保存的是 DACL，不是包含 Owner 的完整回滚备份；本次 Owner 修复因此另存 JSON。不要通过递归授权、重置继承、删除整个 `.codex` 或长期用管理员运行开发工具来掩盖具体权限冲突。[微软 icacls 保存范围](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/icacls)

当前官方文档中的 `codex sandbox setup --elevated ...` 不应直接套用到本次 0.153.0：该可执行文件的 sandbox 帮助没有 setup 子命令；已核对的设置 API 也不保证强制重建已完成的设置。本文不通过降级模式、删除设置标记或强制重装触发它。升级后应重新核对实际接口与验收结果。

## 8. 管理员配置和验收命令

以下是**本次机器与版本**的可复现操作，不是应在每台 Windows 上执行的初始化清单。脚本固定了本机账户、目标路径和 CLI 版本；迁移到其他机器必须重新取证并审查适配，不能只把全部账户统一改为 RemoteSigned。

本机现已通过普通权限验收，**无须重复配置**。以下保留为故障再现时的操作依据。先暂停会同时刷新该目录的 Codex 工作，保留既有日志和备份，不批量终止不明进程。

### 8.1 采集身份、引擎与原始配置

在原账户的 PowerShell 7 中执行。下列操作读取状态，不修改系统配置：

```powershell
whoami /user
whoami /groups
whoami /priv
[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Get-Command codex, powershell.exe, pwsh.exe -All | Select-Object Name, Source
& 'C:\nvm\.nodejs\codex.exe' --version
$PSVersionTable
Get-ExecutionPolicy -List
Get-ExecutionPolicy
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Repair-WindowsSandbox76dOwner.ps1' -Action Inspect
```

`Get-ExecutionPolicy` 此时只代表外层 PS7。再从**同一原账户、以管理员身份运行的 PowerShell 7** 执行完整诊断，它会分别查询宿主和沙箱内系统 WinPS5.1，生成新的本地证据目录：

```powershell
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Test-WindowsSandbox76d.ps1' -RequireAdministrator -PolicyDiagnosticsOnly
```

预期得到 HOST、SANDBOX 两组 JSON，包含真实身份、实际模块路径和五作用域。此模式不运行后续读写验收。若查询仍失败，保留错误并处理对应层；不要根据未知策略直接修改配置。

### 8.2 在明确需要时配置 WinPS5.1 机器策略

前提是重现本案的状态：Offline 账户 WinPS5.1 五项均未定义、有效 `Restricted`，无组织组策略限制；管理员已接受机器范围影响。原值必须先保存。本次原始值为 `LocalMachine=Undefined`，证据为前述 `fe081260...` 目录。

在原账户的管理员终端执行本次已成功使用的命令，并在系统确认提示中核对范围后确认：

```powershell
& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command 'Set-ExecutionPolicy -Scope LocalMachine -ExecutionPolicy RemoteSigned -Confirm'
if ($LASTEXITCODE -ne 0) { throw 'WinPS5.1 machine policy configuration failed; stop and retain the error.' }
```

然后重新执行 8.1 的诊断命令，确认沙箱 WinPS5.1 的 `LocalMachine=RemoteSigned`、有效值为 `RemoteSigned`。本次不修改本人原有 CurrentUser，也不修改 PS7 配置。策略设置成功并不代表 helper 的 DACL 问题已经修复。

### 8.3 在 Owner／权限状态匹配时修复唯一目录

仍须是 `TSY-ICECREAM\Administrator` 本人的提升终端，而非另一管理员账户。先 Inspect，再预览；仅在仍是本案状态时执行 Repair：

```powershell
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Repair-WindowsSandbox76dOwner.ps1' -Action Inspect
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Repair-WindowsSandbox76dOwner.ps1' -Action Repair -WhatIf
```

确认目标是唯一的 `.sandbox-bin` 目录，且令牌具有所需特权后执行：

```powershell
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Repair-WindowsSandbox76dOwner.ps1' -Action Repair
```

脚本会显示高影响操作确认，创建独有 `backup.json` 并保留操作日志。成功应为 `method=takeown`、`exitCode=0`、`verified=true`，Owner 是本人 SID，DACL／组／保护位与操作前相同；`sandboxAccepted=false` 此时是正确结果。若本人已经是 Owner，则无变更返回，仍需独立验收。若脚本报告失败或状态不匹配，就保留证据停止，不追加递归授权命令。

### 8.4 管理员试跑与普通权限正式验收

管理员终端可先试跑完整探针：

```powershell
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Test-WindowsSandbox76d.ps1' -RequireAdministrator
```

成功仍为 `normalUserAccepted=false`。关闭管理员终端，打开原账户的普通 PowerShell 7，先确认下面第一条返回 `False`，再正式运行：

```powershell
[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Test-WindowsSandbox76d.ps1'
```

正式通过的关键字段应为：

```json
{
  "administrator": false,
  "sandbox": "elevated",
  "mode": "read-only",
  "readExit": 0,
  "skillReadExit": 0,
  "writeExit": 1,
  "writeFileExists": false,
  "normalUserAccepted": true
}
```

同时检查该次 evidence 目录的 `write-result.json`：`attributableDenial=true`。保留 `host-policy.log`、`sandbox-policy.log`、`read.log`、`skill.log`、`write.log` 和结果 JSON。脚本不调用 MCP、模型或图像生成服务。

正式验收后，若确有免费宿主集成复验需求，可在已有锁定开发环境中运行下列独立步骤；不要为此临时升级依赖。这会进行模型推理及免费 MCP 验证，**“免费”仅指不调用收费图像生成接口，不表示模型推理无消耗**：

```powershell
Set-Location -LiteralPath 'E:\agent-skills-workspace\ecommercial-images-designer-skill'
$HostEvidence = Join-Path ([IO.Path]::GetTempPath()) ('ecommerce-host-76d-' + [guid]::NewGuid().ToString('N'))
uv run --frozen --no-sync --group dev python -X utf8 -B scripts/run_host_smoke.py --output $HostEvidence --cli 'C:\Users\Administrator\AppData\Local\OpenAI\Codex\bin\6257d9e8f63c0f2b\codex.exe' --cases explicit,implicit,negative,recovery --repeats 3 --workers 2
if ($LASTEXITCODE -ne 0) { throw 'Host suite process failed; inspect the saved evidence.' }
```

[runner](../scripts/run_host_smoke.py) 沿用两个指定 MCP 的免费白名单：GPT 的 `get_model_guide`，Nano 的 `list_models`、`inspect_design_images`、`get_ecommerce_design`；禁止批准、提交、生成、编辑与重试。当前必填`--cli`并检查与共享系统包的一致性，上例使用本机已安装的Desktop构建，不替换原0.153.0；不匹配时停止并保留缓存。退出 0 后还需核对逐次资源读取、工具轨迹、图片角色、确认状态和反馈回退；各批次保持自身版本和快照，不把不同CLI的结果合并。

## 9. 撤销命令与撤销验收

**本节尚未实际执行。** 它用于管理员明确决定恢复本次变更前状态时，不是当前修复的下一步。撤销 Owner 会恢复本次普通 helper 权限冲突；撤销机器策略后，Offline/WinPS5.1 在原其余作用域未变时会重新得到 `Restricted`。撤销配置与维持业务可用不是同一验收目标。

顺序为：先恢复 Owner 并核对成功，再恢复 WinPS5.1 的机器策略。保留原备份和新的操作日志；若期间已有其他管理员更改策略或 ACL，停止并重新评审，不能机械覆盖。

### 9.1 管理员预览并恢复原 Owner

在原账户的管理员 PowerShell 7 中，使用**本次成功 Repair** 的精确备份，不要换成第一次失败操作的目录：

```powershell
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Repair-WindowsSandbox76dOwner.ps1' -Action Restore -BackupPath 'E:\agent-skills-workspace\ecommercial-images-designer-skill\.eval-runs\owner-76d-7bf4303310fe480d9ebcf67817d494e1\backup.json' -WhatIf
```

脚本会检查账户、目标、备份位置、重解析点和当前 DACL／组／保护位。全部匹配且管理员决定撤销后，再执行：

```powershell
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Repair-WindowsSandbox76dOwner.ps1' -Action Restore -BackupPath 'E:\agent-skills-workspace\ecommercial-images-designer-skill\.eval-runs\owner-76d-7bf4303310fe480d9ebcf67817d494e1\backup.json'
```

只有输出 `verified=true`，Owner 已恢复为 `S-1-5-32-544`，且 DACL／组／保护位不变，才继续下一步。若失败或状态不匹配，停止，不强行覆盖 DACL。可以再次只读核对：

```powershell
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Repair-WindowsSandbox76dOwner.ps1' -Action Inspect
```

### 9.2 管理员恢复本次 WinPS5.1 的机器策略原值

本次实测原值是 `Undefined`；这不代表其他机器也应设为 Undefined。本人原有 WinPS5.1 CurrentUser 和 PS7 配置均未被本次修改，因此不删除、不重写它们。

```powershell
& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command 'Set-ExecutionPolicy -Scope LocalMachine -ExecutionPolicy Undefined -Confirm'
if ($LASTEXITCODE -ne 0) { throw 'Policy rollback failed; retain the error and stop.' }
```

随后检查五作用域，尤其是机器值，而不是只看当前主账户的有效策略：

```powershell
& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command 'Import-Module -Name ($PSHOME + "\Modules\Microsoft.PowerShell.Security\Microsoft.PowerShell.Security.psd1") -Cmdlet Get-ExecutionPolicy -ErrorAction Stop; Get-ExecutionPolicy -List; Get-ExecutionPolicy -Scope LocalMachine'
if ($LASTEXITCODE -ne 0) { throw 'Policy rollback inspection failed; effective state remains unknown.' }
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Test-WindowsSandbox76d.ps1' -RequireAdministrator -PolicyDiagnosticsOnly
```

撤销验收期望：Owner 为原管理员组，原 DACL／组／保护位保留；WinPS5.1 `LocalMachine=Undefined`，原用户 `CurrentUser=RemoteSigned` 保留；在其他作用域未变化时 Offline 账户有效值恢复 `Restricted`。最后一条只做诊断，不运行脚本读写或出图。若随后普通终端再次出现原 helper 权限错误，应记录为恢复旧配置后的预期能力回退，不能称作普通权限功能验收通过。

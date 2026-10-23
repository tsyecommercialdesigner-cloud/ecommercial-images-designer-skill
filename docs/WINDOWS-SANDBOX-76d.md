# Windows沙箱恢复与76d.2复验步骤

2026-10-23实机版本：PATH的`C:/nvm/.nodejs/codex.exe`为0.153.0；Desktop自带另一份0.163.0-alpha.11。下列脚本固定0.153.0，避免PATH/版本混淆；未升级CLI或更改执行规则。用户已批准的执行策略及单目录所有者变更按下文记录，不能称安全配置完全未变。

### 当前验收结论：普通用户已通过，CLI免费主集与回归已完成

用户管理员owner-76d-7bf4303310fe480d9ebcf67817d494e1使用takeown成功，退出0、verified=true，SeTakeOwnershipPrivilege存在；仅目录所有者从S-1-5-32-544改为本人SID，原DACL、主组、继承保护位一致。有效备份为该目录backup.json。此前icacls失败状态未改，不覆盖其记录。Restore未执行，不冒充已实测回滚。

用户普通终端sandbox-76d-394ed662fa3e4f2bbdd1b0d1ab02b585以及Agent普通进程sandbox-76d-97026d310f3b4c299a7d7cf446e4a6a8均通过：读文件及Skill退出0，写入退出1、明确类型/错误码/路径拒绝且文件未生成，normalUserAccepted=true。至此不需要继续管理员探针或修改策略/权限。

完整免费CLI主集4类×3次已完成，资源和helper阻塞为0；发现的恢复确认状态措辞已修复并另跑3次真实回归通过。系统技能目录安装警告与收费/视觉验收仍未解决或未运行。最新结果、资源摘要变化和剩余边界见[完整复验报告](HOST-CLI-RECOVERY.md)。76d.2按资源/沙箱修复范围关闭；76d.4单独跟踪启动警告，父任务76d未完成。

以下保留各阶段当时的判断与步骤；其中“尚待”不是当前验收状态，不要据此重复安全配置操作。

### 最新所有权修复：icacls失败，当前修正版尚待管理员验证

用户已主动确认单目录所有者变更，首版Repair证据为`.eval-runs/owner-76d-85163ed878ca49c8bbe70fd0371bc193`：icacls /setowner退出5，verified=false，前后owner/group/DACL/protected完全相同。备份与失败记录保留；没有改变所有者，不能开始普通验收或宣称修复成功。此前实现未区分普通WRITE_OWNER设置与管理员所有权恢复，这是工具选择上的缺口。

修正仍沿用已批准的同一目录和目标所有者，不扩大范围。当前Repair改为系统`takeown /f <固定目录>`（不加/a、/r、/d）；Restore才使用/a回到原Administrators组。takeown是微软用于管理员恢复被拒对象所有权的原生命令。脚本先读取whoami /priv CSV，只按不随语言变化的权限名检查SeTakeOwnershipPrivilege是否存在；管理员令牌若无此特权则停止，不修改用户权利分配、不自行授予特权、不使用SYSTEM任务或其他账户。尚未取得用户管理员令牌的实际特权状态，不能断言上一版失败具体由哪个特权状态导致。参见[微软takeown](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/takeown)和[管理员接管所有权](https://learn.microsoft.com/en-us/windows/win32/secauthz/taking-object-ownership-in-c--)。

默认Inspect新增takeOwnershipPrivilegePresent；实际操作日志保存工具、权限存在性、原始输出和原先的所有者/DACL快照。继续严格验证目标所有者、DACL、主组与继承保护状态；任何不符都保留结果并停止，不自动改权限或尝试另一工具。当前Agent普通令牌实测无SeTakeOwnershipPrivilege，Repair -WhatIf在管理员前置检查被拒，owner/DACL保持不变；这不代表管理员也缺失该特权。修正版仅通过语法、只读和非管理员停止路径验证，实际Repair、Restore及其后完整CLI仍未验证。

下一步由用户在原管理员终端重跑下方同一Repair命令；这是同一已授权操作的实现修正，不需要再次扩大授权范围。仅在verified=true后关闭管理员窗口，从普通PowerShell跑无参数探针。若特权缺失或操作仍拒绝，保留新证据停止，不再盲目重试。

### 已批准的单目录修复范围与实施记录

用户独立普通PowerShell的`sandbox-76d-0a2d911597a343b5aa06da97a8a47568`同样报helper_sandbox_lock_failed/SetNamedSecurityInfoW error5，证实不限于Agent工具进程；故障在命令启动前，不是新的执行策略拒绝。管理员38dd2537通过仍保留为管理员验证，不再要求重复该测试。

进一步核对本机ACL与官方`rust-v0.153.0`源码：`.sandbox-bin`所有者为BUILTIN/Administrators（S-1-5-32-544），本人显式mask=1245631/0x1301bf，没有WRITE_DAC/0x40000。setup_main/win.rs的lock_sandbox_bin_dir给real_user的mask也是Modify类权限；run_setup_full即使refresh_only也执行该锁定，lock_sandbox_dir调用SetNamedSecurityInfoW重写DACL且不修改所有者。普通令牌没有可用的管理员组授权，组所有权也不能给它个人所有者的隐式WRITE_DAC。这组证据解释当前拒绝；所有权实际修复结果尚未验证。

已生成本机0.153.0 app-server schema，确认存在windowsSandbox/setupStart，不应笼统声称该版本没有任何正式设置入口。但core/src/windows_sandbox.rs的run_windows_sandbox_setup_and_persist只在sandbox_setup_is_complete=false时运行elevated setup，现有完成标记不会因这个请求被强制重建；之后还会持久化配置。因此本轮没有调用该API，避免把其started/complete当修复成功，也没有删除标记强迫设置。schema证据`.eval-runs/app-server-schema-76d-466852596fe14cff817bd791383b3f9f`；源码副本在Temp/codex-policy-76d-source。

准备的[`Repair-WindowsSandbox76dOwner.ps1`](../scripts/Repair-WindowsSandbox76dOwner.ps1)是本项目基于证据的定点操作，**不是Codex官方修复命令**。默认Inspect只读。用户已确认的唯一目标是`C:/Users/Administrator/.codex/.sandbox-bin`本身：所有者从管理员组改为本人SID；DACL、主组、继承保护位和子项不改，不递归，不授予Everyone/FullControl，不触碰.sandbox-secrets、执行策略、后端或规则。个人成为所有者后可管理该目录DACL，这是实质的安全配置变更，不可说成权限完全未变。首版实际Repair已失败，修正版Repair和Restore未运行。参见[微软所有者隐式WRITE_DAC说明](https://learn.microsoft.com/en-us/windows/win32/secauthz/owner-of-a-new-object)。

脚本锁定本机身份和目标，拒绝目标或父目录重解析点；Repair/Restore要求原用户的管理员终端及ShouldProcess高影响确认。真正操作前在仓库忽略的独有`.eval-runs/owner-76d-<GUID>/backup.json`保留原所有者、主组、DACL和继承保护状态。首版只调用icacls /setowner，失败后当前修正版改为takeown，不自动回退工具。操作后必须验证所有者正确且其余字段未变；不符则保存证据停止，不声称沙箱通过。Restore只接受本脚本生成位置/结构与当前状态匹配的备份，将所有者恢复为原管理员组，不覆盖已变动的DACL。

首版准备验证：语法、真实Inspect、普通令牌Repair -WhatIf的管理员前置拒绝均通过，验证前后owner/DACL完全未变；用户随后执行的首版Repair失败，记录见上文。当前takeown修正版再次通过这些本地检查，既有统一41项回归通过，系统takeown.exe微软签名Valid；实际接管及Restore未验证。用户在管理员PowerShell重跑同一脚本，并在脚本确认中批准：

```powershell
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Repair-WindowsSandbox76dOwner.ps1' -Action Repair
```

仅在输出verified=true后，关闭管理员窗口，在普通PowerShell运行原Test-WindowsSandbox76d.ps1（不加参数）。无需再跑管理员探针。普通验收失败仍保留新证据，不能继续扩大修复范围或运行完整CLI。撤销时在管理员终端使用同一Repair脚本的`-Action Restore -BackupPath`，传入成功修复输出的完整backup.json路径，并批准确认；不存在固定可复制的GUID，不能虚构备份路径。首版失败的所有者没有改变，不需要撤销，也不能把失败备份当已完成修复的记录。修正版及普通验收通过前76d.2仍blocked，完整免费CLI和收费调用均未运行。

### 最新验收：管理员通过，普通用户仍未通过

用户提供并已核对`sandbox-76d-38dd2537b86646a9aa22ff03d3fa4a80/result.json`：administrator=true、readExit=0、skillReadExit=0、writeExit=1、writeFileExists=false、normalUserAccepted=false。write-result.json的attributableDenial=true，write.log的ASCII记录对应当前Write目标，实际根异常System.UnauthorizedAccessException/HResult=-2147024891。修正后的完整管理员探针现已通过，旧中文乱码不再影响判定；不需要重复管理员运行或执行策略变更。

当前Agent工具的普通权限重跑`sandbox-76d-6a7ee293352d4e06b67c8c655f7ea010`仍被helper_sandbox_lock_failed/SetNamedSecurityInfoW error5阻止，尚未开始策略查询及读写。管理员通过没有修复或证明普通权限下helper设置可用。下一项证据是用户关闭管理员窗口，在独立普通PowerShell运行不加参数的同一脚本；若该上下文也失败，保留其证据并继续定位原生helper设置，不能再将重跑管理员探针当作已解决普通用户问题。未绕过执行策略、修改ACL或启动收费出图；完整免费CLI集成套件尚未重跑，76d.2保持blocked。

### 当前进展：用户已配置策略，管理员写入拒绝被旧探针误判

用户已在系统确认提示选择Y，将WinPS5.1的LocalMachine从Undefined改为RemoteSigned。随后管理员运行`sandbox-76d-1939752e35624b9ab969c3c088c3daec`的sandbox-policy.log确认独立账户CodexSandboxOffline的effective与LocalMachine均为RemoteSigned；read.log返回SANDBOX_READ_OK，skill.log取得真实Skill正文。策略与读取这一层已通过，不能继续要求重复改策略。

该次write.log包含本地化的访问拒绝消息，但中文经代理编码后乱码；原先判定仅匹配Access is denied/拒绝访问等片段，既受编码影响，也漏掉“访问被拒绝”等正常措辞，因而报Write probe did not return an attributable filesystem denial。write.txt未生成，但旧版未在断言前单独保存write进程退出码；保留旧失败，不追补为PASS/result.json。

现修复探针和断言：异常展开到GetBaseException，输出ASCII版本化记录，包含operation、实际异常类型、HResult以及UTF-8路径数据的base64表示（仅数据，不是EncodedCommand）。通过条件必须同时满足非零退出、目标未生成、唯一记录对应当前Write目标、根异常为System.UnauthorizedAccessException且HResult=-2147024891；helper/启动错误仍拒绝通过，不再使用人类错误消息决定结果。新增write-result.json在断言前保存退出码、文件存在性和判断值，失败包装包含底层输出。

新增2项回归：真实WinPS5.1文件操作产生UnauthorizedAccessException及DirectoryNotFoundException（不改ACL/属性），以及12组断言输入，覆盖本地化文本、退出0、文件存在、helper失败、错误路径/操作/类型/错误码、重复及缺失记录。统一检查41项通过，两个PS脚本语法通过；这些测试不能代替真实沙箱验收。普通权限重跑`sandbox-76d-222b4e2fd42943c68048d957f77a65fa`仍在helper_sandbox_lock_failed/SetNamedSecurityInfoW error5处停止，未执行后续探针。因此仍需用户管理员运行修正后的完整探针，并以普通用户单独验收；完整CLI套件仍未重跑，不启动模型/MCP或收费调用。没有继续更改策略、ACL或沙箱。

### 策略诊断依据与配置／撤销说明

管理员只读诊断`sandbox-76d-fe081260beba431fbdc9e6ee15671d15`成功取得两组JSON：宿主本人`TSY-ICECREAM/Administrator`的CurrentUser=RemoteSigned，LocalMachine=Undefined；沙箱实际身份为`TSY-ICECREAM/CodexSandboxOffline`，effective=Restricted，五个作用域全为Undefined。此前关于沙箱账户默认Restricted的推断现已得到实测确认：本人账户级策略不适用于该独立账户。双方MachinePolicy和UserPolicy均未配置；本次拒绝并非由已配置的组策略触发。该成功仅证明诊断查询可用，未运行脚本读写验收。

沙箱modulePath中确有Store PowerShell 7.6.7的路径；修正后的查询实际加载的Security/Utility均为系统WinPS5.1模块。模块适配已在沙箱中验证；原始自动加载失败的完整内部异常未捕获，不能把它的每个细节都说成已证实。

用户已明确接受影响范围，在管理员终端通过系统WinPS5.1的受支持命令将LocalMachine从Undefined设为RemoteSigned。它是持久的机器范围配置，影响所有账户的Windows PowerShell 5.1；允许本地未签名脚本，带互联网来源标记的脚本仍需按RemoteSigned规则处理，不自动解除标记。Windows PowerShell与PowerShell 7的策略独立。此操作放宽了此前对沙箱账户生效的默认Restricted，不能描述成策略完全未变。

**下列配置命令已由用户主动确认执行，勿重复执行；未由Agent执行。** 它不设置进程级覆盖、不使用Bypass或Force、不更改组策略、沙箱后端、执行规则或ACL：

```powershell
& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command 'Set-ExecutionPolicy -Scope LocalMachine -ExecutionPolicy RemoteSigned -Confirm'
```

在系统确认提示中同意且命令无错误后，在原管理员终端运行完整探针：

```powershell
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Test-WindowsSandbox76d.ps1' -RequireAdministrator
```

预检应显示沙箱LocalMachine=RemoteSigned且effective=RemoteSigned，再进行原始.ps1读写测试；无覆盖其他策略的自动修复。管理员探针成功后关闭管理员终端，打开普通PowerShell运行同一脚本但不加参数，只有normalUserAccepted=true及明确写入拒绝才通过。此前普通用户helper锁error5仍是独立未解决的验收项；政策配置本身不保证解决它。未成功时保留新证据停止，不能宣称完整CLI已恢复。

如用户决定撤销本次机器范围变更，且期间没有其他管理员修改该值，恢复本次实测的原值Undefined（只影响此作用域）：

```powershell
& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command 'Set-ExecutionPolicy -Scope LocalMachine -ExecutionPolicy Undefined -Confirm'
```

配置前的五作用域JSON已保存在上述独有证据目录。配置命令已由用户确认执行；撤销命令未执行。前一轮仅文档更新未重跑单测；本轮探针修复已运行41项检查，历史结果保留。参见[微软Set-ExecutionPolicy说明](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/set-executionpolicy?view=powershell-5.1)及[执行策略默认值](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1)。

### 管理员试跑后的探针修正历史

最新管理员策略诊断`sandbox-76d-4331fd2458604b0bb77f020cbd647930`在自动加载`Microsoft.PowerShell.Security`时失败，`Get-ExecutionPolicy`尚未返回（CouldNotAutoloadMatchingModule）。旧查询将身份与策略一同构造为对象，一个字段失败导致整份对象未输出。这不是沙箱effective=Restricted的证据，不能据此修改执行策略、修复系统或重装PowerShell。

已在本机复现相关环境问题：PowerShell 7通过原生中间进程启动WinPS5.1，子进程继承PS7的PSModulePath；按名称导入Security模块报FormatXmlUpdateException/类型成员重复，证据`.eval-runs/module-path-76d-39a0c67fe00d46498f156d9f3e0002f2`。微软说明直接启动时会清理PS7路径，经中间进程启动则不会，可能解析到无法加载的同名PS7模块。该问题在本账户已复现，沙箱原始失败是否同因仍待其诊断输出，不能混同为已查明沙箱根因。参见[微软PSModulePath与中间进程说明](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_psmodulepath?view=powershell-7.6#starting-windows-powershell-from-powershell-7)。

当前诊断显式从正在运行的WinPS5.1的`$PSHOME/Modules/`加载Security与Utility的原始系统manifest，分别只导入Get-ExecutionPolicy和ConvertTo-Json；不使用Force、程序集注入或新的DLL加载路径，不改PSModulePath、执行策略、注册表、ACL或沙箱。正常模块导入检查仍生效。JSON新增psHome、modulePath、languageMode及实际两个模块路径；失败时通过Console输出已取得的身份/版本/环境与完整异常、错误ID/位置，不依赖Utility序列化模块，也不执行后续读写探针。

本机同样继承PS7路径的原生子进程复验通过，实际加载两个WinPS5.1模块并返回五作用域JSON（`.eval-runs/module-path-fixed-76d-b05f41d37c324b168afa58fcef38c92a`）。新增Windows真实子进程回归覆盖同名不兼容manifest抢先出现在搜索路径，以及模块缺失时保留上下文并非零退出；统一检查39项全通过。它们不是沙箱内验收。普通权限诊断`sandbox-76d-8adc051f00414f05a303454d65f86b35`仍被helper锁error5阻止，未取得沙箱策略；下一步仍在管理员终端执行下方`-RequireAdministrator -PolicyDiagnosticsOnly`命令，取得实际值后才决定策略或签名处理。未运行完整CLI复验，未启动MCP或收费调用。

此前管理员试跑`sandbox-76d-a7f3f58e81d34a9eaf71dd4efc58f5a6`已启动系统Windows PowerShell，但其执行策略拒绝加载`WindowsSandbox76dProbe.ps1`（SecurityError/UnauthorizedAccess）。这与此前helper目录权限错误和WindowsApps进程启动错误是不同阶段，不能继续按旧故障判断。

2026-10-23本账户现场检查：Windows PowerShell 5.1为CurrentUser=RemoteSigned、LocalMachine=Undefined，其余三项Undefined；当前PowerShell 7则为LocalMachine=RemoteSigned、其余Undefined。探针NotSigned，未发现Zone.Identifier。不能把PowerShell 7的策略当成系统Windows PowerShell的策略，也不能把本人CurrentUser设置当成沙箱账户的设置。沙箱账户可能因各作用域均未定义而使用Windows客户端默认Restricted；这是待核实推断，尚未取得该账户策略。普通权限工具尝试查询仍被helper_sandbox_lock_failed/error5挡住，不是策略查询成功。

探针已补上宿主及沙箱的Windows PowerShell身份、版本、effective策略和五个作用域的只读预检。查询只读取策略，不加载.ps1，不执行被拒绝探针的文件读写，也不设置Process策略或其他例外。新增诊断模式（在当前已打开的同一管理员终端运行）：

```powershell
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Test-WindowsSandbox76d.ps1' -RequireAdministrator -PolicyDiagnosticsOnly
```

输出HOST和SANDBOX两组JSON，保留host-policy.log及sandbox-policy.log；诊断成功不是沙箱读写验收通过。正常模式也先做此预检；Restricted或不满足签名条件的AllSigned会停止，不再重复提交必然被拒绝的探针。普通权限诊断仍受helper锁阻挡，管理员诊断尚待用户执行；未开始完整CLI复验。

诊断实现复验记录：首次多行诊断参数被现有CLI代理拒绝为InvalidBatchScriptArg（sandbox-76d-86a5a5230e9c4cc38d07a77b711bca6f）；已将固定的纯策略查询参数写为单行，未改变其查询内容。普通权限重跑sandbox-76d-e6f3ffa38f3b4ae9806d178834c67a1a已通过参数层，在既有helper锁error5处停止；host-policy.log包含有效JSON，未执行后续脚本读写探针。两次失败日志均保留，不计为沙箱验收成功。

后续按沙箱实际结果处理：MachinePolicy/UserPolicy若有值，交由对应策略管理员处理，不能用较低作用域覆盖。若effective=Restricted且所有作用域Undefined，应先取得用户对持久执行策略配置的明确同意，再由管理员针对**Windows PowerShell 5.1**决定是否设置允许本地脚本的策略；LocalMachine变更影响所有账户，不能擅自执行，也不能只改本人CurrentUser。AllSigned应走可信签名和发布者信任流程；Restricted下单纯签名也不能运行脚本。不要使用Bypass、EncodedCommand、把被拒绝脚本展开为内联代码、降级沙箱、修改沙箱账户或目录ACL。此前管理员运行的授权不等于已授权机器范围执行策略变更。参见[微软执行策略与作用域说明](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1)。

随后管理员试跑sandbox-76d-c7eaab0fef9949359954328a1501f68c的底层错误为CreateProcessAsUserW failed:5，目标是WindowsApps中的Microsoft.PowerShell_7.6.7.0 pwsh.exe；尚未执行读取。探针原继承调用者PSHOME，会随Store终端改变。现固定使用SystemRoot/System32/WindowsPowerShell/v1.0/powershell.exe，并将探针stdout设为UTF-8；不更改WindowsApps ACL、不增加例外或改沙箱模式。系统PowerShell在普通宿主运行探针能返回SANDBOX_READ_OK，语法校验通过；普通沙箱基线仍在helper_sandbox_lock_failed/error5阶段失败，不能声称沙箱启动验收通过。异常现在直接包含底层输出和证据目录，不再仅显示包装行号。仍需管理员步骤与普通终端验收。

用户管理员终端的新记录sandbox-76d-e63629e0c4474c8e8dcf6f576e01b64b通过了管理员检查，read.log为“文件名、目录名或卷标语法不正确”，不是此前helper权限错误。已将探针的cmd /c内嵌引号调用改为固定WindowsSandbox76dProbe.ps1，通过普通-File/参数传递读取和写入目标；不使用ExecutionPolicy Bypass或编码命令。两个脚本语法通过，探针在普通宿主读取合成文件返回SANDBOX_READ_OK。普通非管理员沙箱复测sandbox-76d-f24e9378711840b59696e0e3a45a809b仍报helper_sandbox_lock_failed/error5，故仍需用户执行修正后的管理员步骤及普通终端验收，不能称沙箱已恢复。

当前0.153.0的sandbox帮助没有setup子命令；其源码中的/setup-default-sandbox仅在已降级为RestrictedToken模式时执行，当前elevated下直接返回。不能为了触发设置而先降级。官方新文档的setup语法不能直接套在本机这个命令接口上。

采用当前CLI实际支持的原生沙箱启动入口，在管理员批准的上下文中触发正常helper准备/权限刷新，再从普通用户上下文验收。它是一次恢复尝试，不保证解决该版本的ACL问题；普通用户验证失败仍视为未修复。

1. 保存工作，使用Windows开始菜单对PowerShell选择“以管理员身份运行”，批准UAC。须仍为`TSY-ICECREAM\Administrator`本人，不能换成另一个管理员账户或另一份CODEX_HOME。
2. 在管理员PowerShell运行：

```powershell
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Test-WindowsSandbox76d.ps1' -RequireAdministrator
```

脚本只调用现有CLI的`sandbox --permission-profile :read-only`并明确选择elevated后端及Never审批。它在本仓库忽略的.eval-runs下创建独有探针目录，测试读取、真实Skill入口读取及只读写入拒绝。CLI按自己的正常路径准备/刷新helper；脚本没有icacls、takeown、删除sandbox目录、ignore-rules或全访问开关，也不会启动MCP/模型或出图。失败时保留日志并停止，不自动放宽权限。

3. 管理员步骤成功后关闭该终端，打开普通PowerShell，再运行：

```powershell
& 'E:\agent-skills-workspace\ecommercial-images-designer-skill\scripts\Test-WindowsSandbox76d.ps1'
```

普通终端运行才是验收。预期输出：administrator=false，normalUserAccepted=true；readExit=0，skillReadExit=0，writeExit非0，writeFileExists=false，并显示PASS。写入必须明确返回文件权限拒绝，不能把helper启动失败误当写保护生效。每次的read.log、skill.log、write.log和成功时result.json保留在输出的evidence目录。

4. 若管理员步骤或普通验证仍报`helper_sandbox_lock_failed / SetNamedSecurityInfoW ... failed: 5`，停止并保留对应日志。需要管理员/支持人员修复原生沙箱设置；不要手动放宽目录ACL或改成unelevated/full access。当前普通终端基线已复现同一error5，没有宣称此恢复尝试已通过。
5. 普通验证通过后，回到本聊天提供PASS/result.json的非敏感结果，继续76d.2。再运行4场景×3次真实CLI smoke，保留所有历史失败：显式调用、隐式选用、反例和记录恢复。现有runner显式选择elevated+read-only、保留规则且只暴露两个指定服务的免费工具；仍不允许确认/生成/编辑/提交/重试。工具轨迹、资源加载和恢复结果都须核对，退出0不等于行为通过。

参考：[官方Windows沙箱说明](https://learn.chatgpt.com/docs/windows/windows-sandbox)、[0.153.0交互命令定义](https://github.com/openai/codex/blob/rust-v0.153.0/codex-rs/tui/src/slash_command.rs)、[0.153.0命令适用状态检查](https://github.com/openai/codex/blob/rust-v0.153.0/codex-rs/tui/src/chatwidget/slash_dispatch.rs#L341)。官方文档说明elevated设置需要管理员批准；恢复后模型生成的命令仍以低权限沙箱运行。

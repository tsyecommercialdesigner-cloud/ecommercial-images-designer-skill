# 76d.7：独立修补 CLI 的普通权限沙箱与免费 Host 复验

2026-10-23，使用[前一阶段](SYSTEM-SKILLS-76d7.md)构建的独立候选，普通权限沙箱验收通过；随后在同一冻结 Skill 包上新跑四类场景各三次，**12/12 语义复核通过**。27 次 shell 命令退出 0，9 次真实免费 MCP 调用成功；系统技能安装、缓存漂移、资源拒绝和 helper／工具宿主错误均为 0。收费图片调用为 0。

这里的完整免费复验指既定的显式调用、隐式看图策划、非电商反例、记录恢复主集，不等于两个服务全部 API 或 42 场景均验证完成。模型推理使用现有账户额度；“免费”仅指未调用供应商收费出图。

## 固定产物与边界

候选源自 stable `83086188ae0614bd882818ff1aa23f3194962012` 加本地缓存补丁，版本字符串为 `codex-cli 0.163.0`，不是官方发行二进制。上游核查时点、原生测试、SQL 换行适配及 51 次缓存发现实验见前一报告；本次没有宣称上游已采纳。

独立目录为仓库 `.eval-workspaces/codex-76d7-0163/target/debug/`：

| 产物 | SHA256 |
|---|---|
| `codex.exe` | `91277b53706d68833dfe200831d7f80c7bac547d960f85f8ffa061f1a4349e7e` |
| `codex-command-runner.exe` | `22e91c3183eff825bc90d1bb2ea211e032c22ee6be83525b947f170243f95402` |
| `codex-windows-sandbox-setup.exe` | `9436fdb78257fabd2d4304a497c4494b0960e12c2d353a557ee94b84b5a8caf1` |
| `codex-code-mode-host.exe` | `51a79299b236f49d02a77969a1e8fa0b1c1683e470c49244cc9ffb8448254988` |

三个辅助程序均从同一固定源码独立构建，没有从正式安装借用或替换。setup 程序只构建，本次未运行管理员 setup；CLI 主程序未重建或更换。现有 NVM、Desktop 安装不变。

实际由非提升权限的 `TSY-ICECREAM\Administrator` 发起，管理员令牌检查为 false。`windows.sandbox="elevated"` 是既有沙箱后端名称，不代表终端已提升。保持 `--sandbox read-only`、`approval_policy="never"`，没有跳过执行规则、使用 ExecutionPolicy Bypass 或修改权限。读取现有 MCP 启动配置，只向测试宿主提供两个服务的启动命令和免费工具白名单，没有拷贝凭据或输出配置内容。

每次新建仓库作用域 `.agents/skills/ecommerce-image-designer`，复制相同 8 文件包，使用真实宿主发现／调用，没有注入伪技能目录或启动 mock MCP。只复用图片绘制函数创建合成输入。模型沿用 CLI 默认选择，runner 未独立固定和记录模型 ID，不作跨模型兼容声明。

## 故障、修复与旧记录

**配套程序缺失。** 原候选只有 CLI 主程序。首次 pilot `ecommerce-host-76d7-patched-pilot-20261023-a1` 缺少 `codex-code-mode-host.exe`，报 os error 2；进程仍退出 0，并输出如实说明工具不可用的答案。原始 `trial.json` 因旧 runner 只看退出码和答案而显示 completed，未改写它；另存 `pilot-audit.json` 判为 `failed_tool_host_unavailable`。

runner 现核对 stderr 和实际 error 事件，工具宿主不可用即分类为 `tool_host_unavailable`，即使退出 0 也失败。仅分析错误事件，不将模型文字中的错误示例当作故障。补全程序后，第二次独立 pilot `...-a2` 实际调用两 MCP 成功；它不拼入最终 12 次主集。

**V8 下载 404。** 工具宿主首次构建使用 denoland rusty_v8 v150.4.0 默认 Windows ptrcomp/sandbox 地址，返回 404、构建退出 101，失败日志保留。按[固定源码的 setup-rusty-v8 action](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/.github/actions/setup-rusty-v8/action.yml)，改用 OpenAI Codex `rusty-v8-v150.4.0` 官方 release 产物。先按源码摘要核对 checksum 清单，再核对库与 binding：

| 文件 | SHA256 |
|---|---|
| Windows ptrcomp/sandbox `.sha256` 清单 | `a4d6221dddb4b5724b23411eaac47caf6095489fbf9d126f65b33cef96a0a8ef` |
| `rusty_v8_ptrcomp_sandbox_release_x86_64-pc-windows-msvc.lib.gz` | `732ec5da4243aa166799780c8519a5eea6f32f6e47657a323342794dc3c239d6` |
| `src_binding_ptrcomp_sandbox_release_x86_64-pc-windows-msvc.rs` | `dabf78ba1faac127660db9862b1d0354175c71b8db2d4fcb5bacbd9c93576b16` |

仅对构建子进程设置 `RUSTY_V8_ARCHIVE`、`RUSTY_V8_SRC_BINDING_PATH`。沿用便携 Rust 1.95、锁定依赖及现有 MSVC，随后构建成功。没有禁用 V8 sandbox、校验或 TLS，没有修改永久 PATH。

**新增布局适配。** [versioned_system_skills_guard.py](../scripts/versioned_system_skills_guard.py) 仅由显式 `--system-cache-layout versioned` 启用；默认 legacy guard 不变。要求匹配 CLI SHA256 和三个配套程序，记录各摘要；未 pin 或摘要错误时在启动 Host 前拒绝。在隔离 home 实际发现系统技能，核对指纹路径、marker、完整文件字节和发现列表；拒绝路径逃逸、链接和混合发现。真实 home 既有同指纹坏包时停止，不修复、不删除；缺失时由候选在独立命名空间正常创建。预检、每次运行前后及末尾均核对旧 `.system`，保留仓库进程锁，不把它当作所有宿主的全局锁。

新增 7 项失败路径测试，覆盖旧包保留、坏包拒绝、legacy 漂移、文件／发现异常、路径／指纹异常和缺失／错误 CLI pin；已有分类测试补充工具宿主错误断言。最终 **62 项通过，0 失败、0 跳过**，结构／资源／42 场景格式检查通过，与真实宿主证据分别记录。

## 普通权限沙箱验收

`Test-WindowsSandbox76d.ps1` 增加候选路径、预期版本和可选 SHA256 参数，旧默认值不变；摘要错误时不执行候选。证据：`.eval-runs/sandbox-76d-ff9cd83fb33b443b8037dd8b7c43834a`。

| 断言 | 实际结果 |
|---|---|
| 调用者管理员令牌 | false |
| 沙箱身份 | `TSY-ICECREAM\CodexSandboxOffline` |
| 系统 PowerShell | Desktop 5.1.26100.9711 |
| 有效策略 | RemoteSigned；LocalMachine=RemoteSigned，其余四作用域 Undefined |
| 夹具与真实 Skill 读取 | readExit=0，skillReadExit=0 |
| read-only 写入 | writeExit=1；根异常、HResult、操作及目标匹配；文件未生成 |
| 普通用户验收 | normalUserAccepted=true |

沿用用户此前主动配置的机器策略和所有者修复，本次未设置策略或 ACL。写拒绝有 `UnauthorizedAccessException` 及精确目标记录，不能只依据退出非零。

## 12 次真实技能与两 MCP 主集

统一证据目录为用户 Temp 下的 `ecommerce-host-76d7-patched-main-20261023-a1`。两并发 worker，每类三次，未拼接历史成功条目。

| 场景 | 次数 | shell | MCP | 语义结论 |
|---|---:|---:|---:|---|
| explicit：显式技能、首次无图、只讨论 | 3 | 5 | 6 | 两服务实际免费查询；无假装看图、无生成，继续准备资料。 |
| implicit：两图策划与完整提示词草案 | 3 | 6 | 3 | Nano 每次返回两图，共 6 个 image block；保留商品／仅风格角色。 |
| negative：Python 学习计划 | 3 | 0 | 0 | 未误调用电商技能或图像服务。 |
| recovery：读记录、M02 标题拥挤 | 3 | 16 | 0 | S2 排版后到 S3 提示词；M01、事实保留，未知批准状态不继承。 |
| 合计 | 12 | 27 | 9 | 12/12 逐条复核通过，关键违规 0。 |

真实工具是 `zhenzhen-gptimagegen2-5-mcp/get_model_guide`、`zhenzhen-nanobanana-mcp/list_models`、`zhenzhen-nanobanana-mcp/inspect_design_images`，各 3 次。`gptimagegen2-5` 为宿主实际服务 ID，对应需求指定的 GPT Image 服务。白名单中 `get_ecommerce_design` 本批未调用；没有调用 plan、compile、confirm、submit、generate、edit 或 retry。

维护 Agent 逐条读取 12 份完整答案并核对轨迹，没有独立模型评分器。`mechanical-audit.json` 核对命令、调用、退出状态、图像块和缓存；`semantic-review.json` 记录语义判断，不将 completed 直接当作语义通过。

- **方案确认**：无图时只讨论；草案不执行，没有将讨论、M01 历史接受或局部反馈当作整版批准。能力查询没有被写成供应商上游鉴权或真实出图通过。
- **图片角色**：P01 明确是合成商品外观夹具，事实限灰色盒体、深灰盖沿。R01 仅作风格参考，不沿用其棕橙商品颜色、居中主体或顶部条带布局。新分区、尺寸、字体与色值为建议，不新增材质、容量或性能事实。
- **反馈回退**：M02 拥挤回到 S2 给出具体比例布局，再更新 S3 完整结构草案；保留 M01、F01 和图片角色。缺失的旧文字、尺寸、基图、风格及批准依据保留 unknown，草案不可执行；未捏造旧值或本次看图证据。

9 次正向运行均实际读取包资源，其中 8 次另有 shell 读取 `SKILL.md`。`explicit-r1` 直接读三个参考文件，没有独立入口读取命令；显式选择可能由宿主提供入口上下文，但不能仅据本轨迹证明注入过程。保留 `skill_entry_shell_read=false`，不声称 9 次都执行了入口读取命令。

保留 22 条非致命日志：PowerShell 快照不支持 12 条，遥测发送失败 8 条，模型目录刷新超时 2 条（recovery-r1/r2）。实际资源调用和答案均完成，不宣称所有日志无 ERROR。

## 保留状态和摘要变化

前后核对位于 `.eval-runs/patched-host-76d7-d024e8a2eb7b45d9b8a685657521ae2b/`，包含 `preservation-before.json`、`preservation-after.json`、`acl-before.json`、`acl-after.json`。

旧 Desktop `.system` marker `f7cfaf1d6d464589` 及全部 49 文件摘要不变；现有 `.sandbox-bin` 文件（含其 `codex.exe`）、`config.toml`、候选主程序和目录 owner／DACL／组／继承不变。正常运行只新增候选缓存 `skills/.system-cache-v2/1097a3e50f1d2b21` 和 `.sandbox-bin/codex-command-runner-0.163.0.exe`，不能声称磁盘零变化；没有清空旧缓存或批量放宽权限。

本次 Skill 八文件不变：入口 SHA256 `9f5c2ee8c74a1910cef2d6b4cd9a97d047ecb28208a0348066343ac49b459527`；`design-record.md` 为 `11ee11fd955e76c855c34e0682059730fa4648985ba818a444e0f20d3d363942`。缓存源码补丁仍为 `3c068677f40cf07ee05db0c1281ef8e1d9c1ee4b439473025d1a97cb38aa9358`。

| 验证脚本 | 上轮 SHA256 | 本轮 SHA256／原因 |
|---|---|---|
| `run_host_smoke.py` | `5ca57eff89adc54195f4a2f49d521795dcd780129f2d2e509fb6906bece0cfda` | `7d52aaacc92d6ed1f2c5ab65fa15f1fc881da8b6ab92a442a0ed1aedba7d8703`；CLI pin、配套程序摘要、布局适配和错误分类。 |
| `system_skills_guard.py` | `948829eb759d6810c39f580bf2b7e6e6f9d4592f8589390eb48edd9f2c93ff1f` | `19717c6dd21fc8ff7e33c370b2c5c0ce8082b89f7908fb4572c59ffa7e14b657`；显式分派新布局。 |
| `versioned_system_skills_guard.py` | 新增 | `2afd8f86be7dcef03a8cb91f837ccb2eba58d91652d1bac15090608251e3213f`；新包及旧缓存保留核对。 |
| `Test-WindowsSandbox76d.ps1` | 原版历史保留 | `17724e3062caae0323f38ad39db1deb148f190b5ddd68325154e28044f300ab4`；候选路径／版本／摘要参数。 |

隔离工作区保留辅助构建结果、V8 首轮失败和修复日志、`prepare_free_host_v8.ps1`、`build_native.ps1`、`v8-ptrcomp-sandbox/` 校验材料和审计脚本。主集每次保留 input、command、events、stderr、answer、trial；原始轨迹不进入发行包。

## 本机复现

前提是仓库根目录、现有锁定 Python 3.12 环境、上表四个已校验产物及既有两 MCP 配置。普通权限 PowerShell 执行，命令不安装程序或配置权限：

```powershell
$CandidateCli = 'E:\agent-skills-workspace\ecommercial-images-designer-skill\.eval-workspaces\codex-76d7-0163\target\debug\codex.exe'
$CandidateSha = '91277b53706d68833dfe200831d7f80c7bac547d960f85f8ffa061f1a4349e7e'
& .\scripts\Test-WindowsSandbox76d.ps1 -CliPath $CandidateCli -ExpectedVersion 'codex-cli 0.163.0' -ExpectedSha256 $CandidateSha
if (-not $?) { throw 'Sandbox acceptance failed; retain evidence' }

$HostEvidence = Join-Path ([IO.Path]::GetTempPath()) ('ecommerce-host-76d7-patched-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -B scripts\run_host_smoke.py --output $HostEvidence --cli $CandidateCli --cli-sha256 $CandidateSha --system-cache-layout versioned --cases explicit,implicit,negative,recovery --repeats 3 --workers 2 --timeout 240
if ($LASTEXITCODE -ne 0) { throw 'Host infrastructure failed; retain evidence' }
```

每次使用新目录，不覆盖旧结果。退出 0 仅表示基础执行完成，仍须逐条复核语义；本批审计不能为未来输出背书。已有指纹包若校验失败，停止并保留，不删包强行继续。

## 剩余未验证项

- 上游采纳、官方发行修复、候选正式部署、干净安装／升级／回滚、长期回收及其他平台／Host。`76d.7` 继续跟踪这些边界，本轮免费复验部分已完成。
- 真实商品照片、供应商实际鉴权／计费、收费生成／编辑、产物上传下载、mask／流式请求、未知提交恢复和用户视觉验收。实际出图仍须先确认商品事实、图片角色、文案排版与完整方案，再授权提交。
- 新候选上的完整 plan／compile／confirm／review 链；先前 76d.3 的免费服务验证保留为历史，不混入本批。
- 原生 CLI session resume；本批 ephemeral 加设计记录恢复只验证工作流恢复。未覆盖所有账户的 PS5.1／7 策略矩阵，也未重跑全部 42×3 模拟行为评测。

本轮未提交、推送、合并或发布，未对上游发帖。父任务 `76d` 保持进行中，免费验证不替代具体商品方案确认及用户验收。

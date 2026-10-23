# 76d.2 / 76d.3 修复与免费复验（2026-10-23）

## CLI拒绝的两层原因

后续沙箱专项诊断已完成普通用户验收：用户批准的WinPS5.1机器范围RemoteSigned及bin单目录所有者修复消除了资源启动阻塞。0.153.0源码与失败/修复过程见[持续记录](WINDOWS-SANDBOX-76d.md)，12次真实CLI主集及新增确认状态修复后的3次恢复回归见[最新免费复验](HOST-CLI-RECOVERY.md)。以下保留首轮复验时的状态，不用后续成功改写原CLI失败。

原smoke以`--ignore-user-config --sandbox read-only`启动。用户实际配置中的`windows.sandbox=elevated`随用户config一并被忽略，而测试没有单独指定后端。已核对CLI对应的[官方0.153.0执行策略源码](https://github.com/openai/codex/blob/rust-v0.153.0/codex-rs/core/src/exec_policy.rs#L785)及[配置源码](https://github.com/openai/codex/blob/rust-v0.153.0/codex-rs/core/src/config/mod.rs#L3380)：无Windows沙箱后端时，受管文件限制不能实际落实，非交互Never审批会拒绝未匹配命令。对原Get-Content进行execpolicy静态检查的结果为matchedRules=[]；所检查的default.rules没有forbidden/prompt条目。该结果不是“所有受管策略都不存在”的声明。

复现脚本现显式设置`windows.sandbox=elevated`，保留read-only、Never审批和所有原规则，未使用ignore-rules、全访问或弱化后端。新试跑已经越过原来的无后端拒绝分支，但在启动原生沙箱helper时失败：

```text
helper_sandbox_lock_failed
SetNamedSecurityInfoW sandbox dir failed: 5
C:\Users\Administrator\.codex\.sandbox-bin
```

只读ACL/令牌检查：目录所有者为BUILTIN/Administrators，当前用户及管理员组条目为Modify而非WriteDac；当前进程为Medium完整性，Administrators组在令牌中为deny-only。这与设置目录安全信息失败一致。没有据此改ACL、取得所有权或修改用户组。

新pilot为recovery-r1，42.45秒、进程退出0，记录文件读取仍失败；旧trial保留completed的原始进程状态，现脚本额外识别helper_sandbox_lock_failed为sandbox_setup_failed并返回非零，不再误记为成功。未在明确的系统阻塞下重复启动12个相同失败。原12次失败与新pilot都保留，不用新结果覆盖旧证据。

76d.2尚未修复到可用状态：需要在此Windows宿主上完成管理员批准的原生elevated沙箱设置/修复，再跑4类×3次CLI验证。根据[官方Windows沙箱说明](https://learn.chatgpt.com/docs/windows/windows-sandbox)，elevated设置需要管理员批准；当前0.153.0本机sandbox帮助并没有新版setup子命令，不能直接复制新文档的命令。应通过所装版本的正常沙箱设置流程完成，必要时交管理员处理。没有猜测CLI开关、直接执行未核实的helper或降级隔离；原生会话恢复及完整资源加载仍未通过。

## Nano源码修复

本次用户明确授权修复Nano，改动位于已安装源码`D:/MCP/zhenzhen-nanobanana-mcp`，不是把文档中的指令当授权。修改reference_tools.py、reference.py及test_reference.py，不改.env、密钥、依赖锁或用户Host配置。

- 有benchmarks时保留调用方的完整来源/分析记录；缺省时派生source只使用实际reference_image路径，不再固定断言“用户提供的竞品实图”。
- 新构建的风格参考约束明确：只采用analysis/adaptations与目标style明确采用的风格，源构图/布局是否借鉴由adaptations及逐图composition的明确取舍决定，未允许不得复制。
- 该修正约束保存进新方案requirements并参与设计digest；旧历史方案没有该约束标记时保持原编译输出，避免旧确认和旧任务悄悄对应到新提示。旧来源标签也不重写历史，需通过build新revision修正、展示差异并重新确认。
- 仍保留style_only在前、product_identity在后、相同编译器用于导出和执行、原确认/收费检查。没有改写导出task.prompt后走通用绘图入口。

新增回归覆盖已提供合成来源、空来源回退、明确禁止未授权构图、新digest与旧提示保持逐字相同。专项19项通过；首轮18项也通过。全量首轮171项中1项因直接调用unittest未建立test-reports目录而失败，原日志保留；该目录本由scripts/check.py建立，补齐相同运行前提后重跑最终全量，不删除或跳过该测试。

## 全新真实stdio免费复验

使用FastMCP客户端重新启动两个真实已安装服务，未使用mock服务、未连接模型出图入口。GPT guide及Nano models正常；inspect返回两张PNG图像块。Nano分别测试“给出合成来源”和“没有benchmarks”的两种输入，保存新design、导出、读取；断言来源保持/路径回退、新措辞、角色顺序、build/export一致、approved_digest为空、tasks为空全部通过。

最终复验ID为`host76d-final-20261023-True`与`host76d-final-20261023-False`；前一轮fixed ID及输出同样保留。调用清单只有get_model_guide、list_models、inspect_design_images、build_reference_replica_prompts、export_validated_reference_replica、get_ecommerce_design，没有真实confirm、submit、generate、edit、retry。专项/全量单元测试中的供应商执行是隔离替身，不是收费出图。

已经常驻的Desktop MCP进程不会因磁盘源码修改自动热更新；本报告只确认新启动的stdio进程加载修正代码。后续使用常驻服务前需通过Host正常重连/重启加载修正代码，不能把旧进程当已升级，也不能把新进程返回的本地能力状态当上游已验证。

## 证据与交付边界

原证据仍在ecommerce-host-76d-20261023。新CLI证据在Temp/ecommerce-host-76d-fixed-20261023，源码核对副本在Temp/codex-policy-76d-source。真实stdio脚本为Temp/ecommerce-nano-76d-retest.py，响应为Temp/ecommerce-nano-76d-final-results.json；首轮fixed-results也保留。单测日志为Temp/nano-76d-reference-final2.log、nano-76d-full-tests.log及nano-76d-final-full-tests.log。Temp根为当前用户AppData/Local/Temp，不提交原始轨迹到公共仓库。

Skill包内容和摘要未变。真实商品、实际出图、供应商鉴权/费用、产物文字与外观保真和用户视觉验收仍未验证；后续必须先展示并确认具体方案。本轮未提交、推送或发布任一仓库。

最终检查：Nano完整172项测试通过（104.081秒），专项19项通过；ruff lint/format通过、mypy对26个源文件通过、文档检查及契约导出校验通过、已知模式凭据扫描通过。Skill仓库37项测试、结构/场景格式和runner语法通过。Nano安装源码基于`4ebc4872d164173246f008c2d0e912589c2a8ca8`，当前为未提交本地修改，不冒充新发布版本或远端CI。76d.3关闭本地修复范围；76d.2保留Windows管理员沙箱修复阻塞，父任务76d未完成。

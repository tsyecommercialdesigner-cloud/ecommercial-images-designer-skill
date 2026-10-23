# Desktop Host Inspector 状态帧超限（76d.8.1）

2026-10-23，DeepSeek Harness Desktop 0.2.1-rc.2 在双模型免费图片集成测试期间退出。此处“免费”仅指不调用收费图片服务，codeproxy 模型推理仍使用用户原有计费配置。

## 已证实的原因

崩溃日志 `crash-2026-10-23T05-33-40-678Z-host.log` 记录 Host 以退出码 1 结束，致命异常为 `inspector: source state exceeds the source-frame byte limit`。调用链为 `InspectorSourceBuffer.setState` → `HostBridgePublisher.setState` → `HostInspectorSource.setState` → Cordis `publish`。这不是本次 Windows 沙箱、执行策略或 DACL 错误；日志中的 Nano MCP 启动信息不是致命异常来源。

只读检查当前安装的 `app.asar` 得到以下实现证据（`@deepseek-ai/dsh-experimental-inspector/lib/index.js`）：

- 约 996 行：更新单个 topic 后调用 `stateFits()`；超限恢复旧状态并抛出该异常。
- 约 1083 行：容量检查计算全部保留 topic 的 JSON 字节数与帧开销之和。
- 约 1747 行：默认 `maxSourceFrameBytes` 为 128 KiB。尚未证明当前运行使用了默认值，不能将默认值当成实际测量值。
- 约 2272–2333 行：Cordis 变化触发微任务发布，listener 调用没有隔离这一异常。
- 约 2399 行：Cordis 树自身使用 `maxSourceFrameBytes - 4096` 的预算。树的局部裁剪不等于全部 topic 的总预算一定满足。

因此可以确认：状态发布超过 Inspector 的容量约束，异常未被隔离，导致整个 Host 退出。尚未捕获超限前的各 topic 大小、节点及完整状态，不能断言某个具体插件或节点就是根因，也不能将该字节预算错误解释成系统内存耗尽。

## 测试关联与限制

测试 runner 为每个场景创建原生 Agent 会话，当前没有完成后卸载运行时 Agent 的步骤。此前多批会话与本批会话累积可能扩大 Cordis 树，是需要调查的触发因素；尚未证实是唯一原因。修复方向应先核查测试自有 Agent 的安全释放接口，以及 Inspector 总预算和异常隔离；不能通过提高全局上限、禁用插件或放宽权限掩盖错误。

本轮证据根为 `E:/dsh-skill-host-76d8-gate2-contract81`。已保存原始崩溃日志、`host-crash-interruption.json`、`preservation-at-crash.json`、各已完成会话的 events、答案、工具审计及包摘要。

| 场景执行状态 | Sol | Sonnet |
|---|---|---|
| 显式无图查询 | 正常结束 | 正常结束 |
| 两图策划 | 正常结束 | 请求失败：Host 已退出，fetch failed |
| Python 学习反例 | 正常结束 | 未运行 |
| M02 文字恢复 | 正常结束 | 未运行 |

这是执行状态，不是完整语义验收。不能将本批记为 8/8，通过的旧批次也不能补齐本批。当前新包的 Sonnet 恢复修复尚未得到验证，76d.8.1 保持进行中。

本轮此前已通过 71 项 Python、9 项 Node 以及结构／资源／42 场景格式检查；这些本地检查不能替代未完成的宿主集成。收费图片调用始终禁止。崩溃后核对 exe、app.asar 和五份配置／锁／凭据文件摘要均与运行前一致；没有更改安装、配置、执行策略或 ACL，没有自动重启。主 shell 仍在，Host 已退出，runner 已结束。

## 本轮技能修复摘要

纯文字恢复改用独立分支：恢复依据、目标布局表、自包含不可提交草案、回退及确认。避免通用策划模板和无原稿时的成因诊断重新引入旧值推断。旧失败和完整起点副本保留，三个文件的 SHA256 变化如下，其余五份技能文件不变：

| 文件 | 起点 | 本轮包 |
|---|---|---|
| SKILL.md | `ac445a8f5fdce93dfe0585c249bb25377aa533fa452f27f782679dd88e287292` | `f2a2c016c7cb4526123629748291bfc69e80573659e04fb882db52c28e4b92ee` |
| design-record.md | `171f9a353833f899a71cd230f20b99d6d69d9787268d18682656a409e12e5c75` | `41094efd8e89378c1ada85b0c60e396ab2175ac786354a1c08f0ef0fe979c642` |
| review-and-revision.md | `722166aa7727a012d97e8a0e51d40572ae88eaeea6b104b3e623f596f1751032` | `1c3aeb2f13fe91c9cf8583ede936f8fed82173fe3bd69ae8de974b323421a4f9` |

## 当前恢复操作

普通“重启”是恢复 Host 的首选操作，可能清空触发超限的运行时状态，但不等于根因已修复。保留现有配置时，不选择“禁用第三方插件、备份 profile.patch 并重启”，也不因这个错误重装。继续大批量测试前须处理自有测试会话的运行时生命周期并验证；任何清理只能针对有身份记录的测试会话，必须保留已有持久化失败证据。尚未执行会话清理或安装修补。

## 重启后的测试生命周期修复

用户于 2026-10-23 确认已重启并授权修复测试会话释放。新增 `scripts/dsh_test_lifecycle.mjs`，按当前安装的 `dsh-agent` 公开文档保留创建时返回的 `AgentHandle`。创建使用 Session controller 的相同默认 preset 组合、模型选项及原生 factory；模型请求仍走原生 `session/prompt`，不是另一个 headless 宿主。区别是 runner 不再从会丢弃 handle 的 `session/create` 返回值获取 Agent。此项改变限定在评测代码，不修改 Desktop 安装或配置。

每次试验由 runner 的 `finally` 等待 `handle.dispose()`：宿主实现先停止并排空 loop，再释放 scope、关闭持久化句柄并注销运行时 Agent 和 Session。runner 不直接删除注册表条目、不调用 scope 私有销毁函数、不归档或删除历史文件。释放能力按本轮随机 owner、测试 UUID、精确 cwd 和 Agent 对象身份核对，不能接管旧会话；释放或冷读核验失败时不再启动新场景。

释放后通过 `sessionQuery.readSession(id)` 取得冷记录，核对身份和释放前事件前缀，保存 `persisted-events.json`，并检查冷读取没有激活 Agent／Session。宿主断开时 Inspector 待处理请求会失败退出，避免等待永不完成；没有自动重启、自动重提模型或图片任务。

证据根 `E:/dsh-skill-host-76d8-lifecycle81` 中 `lifecycle-probe.json` 是实际已安装 Desktop 的零模型探针：原有 1 个用户 Agent 不动，创建 standard preset 测试会话并释放后恢复原列表，3 条事件全部可冷读。持久化记录保留不等于内存运行时仍存在。单元测试覆盖外部 owner／cwd 拒绝、已有会话拒绝接管、持久化丢失／flush 失败，以及 Host 断开；这些替身测试与真实探针分别记录。

旧批次没有可复用的 handle，重启已清空其运行时；本次没有尝试直接注销这些旧身份，历史失败记录全部保留。本修复解决 runner 持续保留活跃作用域的问题，不能据此声称已修复上游 Inspector 的聚合容量计算或异常隔离。

上游容量与异常隔离问题另由 Beads `ecommercial-images-designer-skill-76d.9` 跟踪；没有向外部平台发布日志或创建公开问题。

本次三批 24 个模型试验会话及零模型探针均释放成功；最终仍仅原用户会话运行，所有持久化事件保留。完整集成与语义失败分开报告，见 [本次最终结果](DSH-RECOVERY-76d81.md#本次最终状态释放修复通过技能完整语义仍未通过)。

评测代码 SHA256 变化（免费 guard、状态分类及准备脚本未变）：

| 文件 | 修复前 | 修复后 |
|---|---|---|
| run_dsh_desktop_smoke.mjs | `1bc75fe9cfc0bdf5a497107c9d15d71c30a7a3cd150cf9aebfe8ef76fb834af8` | `bf180986ce7026e6963e908b31f613039077fa46d63f7190bfa17a4dc23caf51` |
| dsh_desktop_client.mjs | `5d0c5bbc3ca8e46ead46813afa27de25221dabe7d14785d031dddbd4bbeceda8` | `ca4cdc0c41cd8b6f55b095a5e1fc4c9a2a350a1706f370a3a6129c495c1a5b3f` |
| audit_dsh_desktop_smoke.py | `d680b6ed0a8681b2fb844ee0947087fbaa623d4f3fdf9a37ca02f1540ee3ef57` | `212c54e8ff8ed796755304ab18ac31b6618559f5b8e8091c86cb1f55535f3231` |
| dsh_test_lifecycle.mjs | 新增 | `d5980e908fd4a6cb95264e45fa54b33fff5416010921ac53eb953d72cc51f4b2` |

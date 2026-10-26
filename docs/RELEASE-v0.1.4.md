# v0.1.4 正式发布回执

2026-10-26，Beads `ecommercial-images-designer-skill-tsz`。按用户本次目录与命名规范迁移交付运行包，完成dev提交／推送、PR／Windows CI与准确head维护者Agent评审、普通merge、合入CI及本地／远端dev快进同步和同步CI，再创建预发布草稿、核验和转正式。此文为发布后交付说明，不改写发行标签或附件。

## 固定来源和目录

- 正式[v0.1.4 Release](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/tag/v0.1.4)，ID `423755671`，draft=false、prerelease=false，发布时间 `2026-10-26T00:40:03Z`（北京时间08:40:03），latest核对为本版。
- 源码／标签：`cf66420efb683bbfa3206a44669acd31c899f849`；技能内容树 `8878ac6604d85492729098c257de9b129cce7f11`。
- [PR #16](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/16)，普通merge保留 `e6327a22d689ad6e2aec71b64b5394acce6d9f98` 和 `76db4479b8690349da0cf2df3fc1a44160b74381` 两提交，不squash／rebase／强推。
- [准确head评审](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/16#pullrequestreview-5646171357)：维护者Agent自审、COMMENTED，不是独立人工批准。Windows CI／Agent review均通过；保护规则strict、enforce_admins保持，不使用管理员绕过。
- 运行包11文件，六份辅助资料迁为复数references/；10文件内容与v0.1.3逐字节一致，SKILL.md仅改资源路径。业务规则、核心MCP接口及确认／恢复方法不变。当前无独立模板或素材，未新建空目录。详见[迁移记录](DIRECTORY-MIGRATION-tsz.md)。

## 源码门禁

| 阶段 | 准确head | Windows CI |
|---|---|---|
| pr | `76db4479b8690349da0cf2df3fc1a44160b74381` | [40249588591](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/40249588591)，success |
| dev_source | `76db4479b8690349da0cf2df3fc1a44160b74381` | [40249585918](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/40249585918)，success |
| main_merge | `cf66420efb683bbfa3206a44669acd31c899f849` | [40250150235](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/40250150235)，success |
| dev_sync | `cf66420efb683bbfa3206a44669acd31c899f849` | [40250267172](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/40250267172)，success |

发行源码同步时main、dev、origin/main、origin/dev均为cf66420。工作流没有tag／release触发器，不将上述源码CI称为标签CI。发布后说明需另走PR／准确head评审、CI、合入及dev快进同步CI；最终ref和所有运行结果记录在本地final-status证据，不改发行源码。

发布后说明已由[PR #17](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/17)普通merge为`4d36224c1608582605d6573402ff0a8f8304c99c`；准确head`6414c44c53a40b3dead967f88206539ea0989481`的[Agent自审](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/17#pullrequestreview-5646225762)、[PR CI 40250781575](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/40250781575)、[dev CI 40250762148](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/40250762148)与[合入CI 40250906718](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/40250906718)均通过。Beads另有一条关闭状态互动审计自动追加，收尾时补入独立审核提交；此追加及最终同步CI仍按准确head核验并留本地final-status，不改写旧提交或发行资产。

## 七个正式附件

| 附件 | SHA256 |
|---|---|
| CHANGELOG.md | `77e6dfc69e5c85742d3fba468498e264baa87021172413b54db42ccd4ed3dab1` |
| ecommerce-image-designer-v0.1.4.zip | `a7392ec6fb3f2f4cfccaa532f3ea57b1e28aba51710b85b49e8179b7dcc2d576` |
| MANUAL.md | `d0c0464dd3d44046a1646bd8f283a4acafe513621a150826f2b1b3c63c01b15a` |
| RELEASE-NOTES.md | `74315738af42ad09d7645f6df8d597d3d0af4ccfeafb8adc4bb3505e5dd89cb5` |
| release.json | `8e6bd4ce5298d2064bc8b066f3db14eeb2b40ae7d76dcc49c8898ec8c471dec9` |
| VALIDATION.json | `ca68355aeff2cfdad187367935cb109cfb526a8585772d819d6ff591132e6405` |
| SHA256SUMS.txt | `c9982e53f3e56690fda8d89e624e33f2bba83bee4215802c6cf7c266efe0232d` |

普通成员下载同版四个必需附件：`ecommerce-image-designer-v0.1.4.zip`、`release.json`、`SHA256SUMS.txt`、`MANUAL.md`，放在同一交付目录；从[冻结随包手册](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/download/v0.1.4/MANUAL.md)第4节开始，不克隆仓库、不自行打包、不选Source code。旧用户备份完整旧包与定制，再整包升级，不能只换手册或改目录名。保留商品图片、设计档案、产物及Host／MCP配置。

## 实际验证与保留失败

基线161 Python／15 Node通过；首次迁移回归163项中1项错误，新增缺布局异常阻断旧的仅路径规范化夹具，移除超范围检查后163 Python／15 Node及结构／42场景格式通过。旧日志保留。新复数目录保持v0.1.3严格恢复规则，旧冻结快照不改判；模板和assets的索引／平铺亦有回归。

候选、草稿、正式版分别核验7附件摘要、GitHub digest和SHA256SUMS的6项、ZIP11个Git blob、同源冻结手册与CHANGELOG。实际执行随包手册的中文空格带双引号目录安装，检查11安装文件、入口直接引用、两个脚本从其他cwd启动；先成功再缺清单时旧结果清空且阻止安装，合成用户文件保留。三个本次临时探针目录均已清理。

开发者打包块实际执行成功，staging清理、固定来源、11文件和同源手册一致。探针最初错误地要求重打包ZIP与正式ZIP整包摘要相同：tree对象归档使用本次时间戳，11文件内容一致但ZIP字节不同。保留初版探针和失败诊断；只修正本次探针对同源／内容及本地清单摘要的断言，复核同一现场、归档逐文件校验后清理。正式ZIP仍是一次冻结的 `a7392ec6fb3f2f4cfccaa532f3ea57b1e28aba51710b85b49e8179b7dcc2d576`，未覆盖或重上传；本地定制打包与正式资产不混用。准确head评审状态首次提交也保留PowerShell属性参数未正确插值导致的URL格式拒绝；核对同一review后修正参数成功，不伪造评审。

公开手册已无凭据下载并核对同一SHA256。旧v0.1.0、v0.1.1、v0.1.2、v0.1.3的Release ID、正文、标签目标、资产ID／大小／摘要均与发布前快照一致；旧修复及失败历史保留。

## 限制和证据

本次仅目录迁移，不新增模型抽样、真实Host或MCP调用，不将历史v0.1.3宿主成绩冒充新版实跑。已验证范围为确定性工作流回归、活动路径可达性、Git／ZIP及实际PowerShell交付安装；新包原生Host发现／选择、真实成员环境、供应商生成／保存／用户视觉验收、其他OS／Claude／用户级或远端MCP、跨版本业务状态迁移、PI-AI流读取恢复仍未验证。日常Host没有自动编译Hook。无收费图片调用，未改现有安装、配置、权限或执行策略；实际出图仍须先确认当前方案、图号、输入和费用。

本地`.eval-runs/release-v014/`保存CI／评审／保护规则、迁移字节审计、基线和失败／修复日志、草稿与正式七附件元数据／安装证据、开发者打包探针和清理档案；收尾归档验证后清理本次临时环境及重复资产，只保留必要证据归档与摘要。旧证据不清理。

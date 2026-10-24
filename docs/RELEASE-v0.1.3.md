# v0.1.3 正式发布回执

2026-10-24，已按用户授权完成新版规范升级、真实免费Host验证、dev→main PR、Windows CI与Agent自审、普通merge、合入复验、dev双端快进同步及同步CI。之后创建预发布草稿，经Agent发行自审、草稿下载与安装复验后，将同一Release ID转正式；发布后再次下载验证。

## 固定版本与来源

- 正式版本：[v0.1.3](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/releases/tag/v0.1.3)，Release ID `422612888`，draft=false、prerelease=false，发布于 `2026-10-24T08:40:20Z`（北京时间16:40:20），latest已核对指向本版。
- 不可变发行源码／标签：`8c41b69629e1af47b3429bdc41f6a2884a328453`。
- 固定技能内容树：`bba6068eafac9b65c24ee019df79f00fc2d88ea4`，运行包11文件，单数reference/。
- PR：[#14](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/14)，普通merge保留`8c6f229`、`1775699`、`fe0a602`三个提交，不squash、不rebase、不强推。
- 准确head `fe0a6020da647c876c3f690d385ce65ce4bff42b` 的[维护者Agent自审](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/pull/14#pullrequestreview-5637525889)，COMMENTED；不是独立人工批准。所需Windows CI和Agent review状态均通过，没有管理员绕过。

## CI逐项核对

| 阶段 | 实际head | 运行与结果 |
|---|---|---|
| pr | `fe0a6020da647c876c3f690d385ce65ce4bff42b` | [Windows CI 40077958665](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/40077958665)，success |
| dev_source | `fe0a6020da647c876c3f690d385ce65ce4bff42b` | [Windows CI 40077955240](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/40077955240)，success |
| main_merge | `8c41b69629e1af47b3429bdc41f6a2884a328453` | [Windows CI 40078289990](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/40078289990)，success |
| dev_sync | `8c41b69629e1af47b3429bdc41f6a2884a328453` | [Windows CI 40078471688](https://github.com/tsyecommercialdesigner-cloud/ecommercial-images-designer-skill/actions/runs/40078471688)，success |

源码合入／首次同步后本地main、dev、origin/main、origin/dev均为8c41b69。本文及发布后手册说明属于后记，不改标签或已发布附件；后记若提交，仍需独立PR／准确head检查与评审、合入及dev同步CI，最终refs在本地final-status记录，不以源码CI冒充后记提交通过。工作流无tag/release触发器，未宣称有标签CI。

## 正式七附件摘要

| 附件 | SHA256 |
|---|---|
| CHANGELOG.md | `3729616c25e9e4977cc64c4da2e6d70d1e5ced0602d9eb41e94f18c12da52b3a` |
| ecommerce-image-designer-v0.1.3.zip | `b0ab3745fb269db7e667132ed899941001e4e26a169c70f4b51044f6e463ae8a` |
| MANUAL.md | `81188249f10d92ba4374c51f476a94c60831f20c38a4591e9a6f76e558d0916a` |
| RELEASE-NOTES.md | `e013ca20ea090d711fa9d8cfe45103425e8ef687153b8b68d1bb7e4c7bac8b71` |
| release.json | `206eff310d796fadd2cdef5b7e0d35cfcebe4301a5b64b5bfebbd6f8a5e40490` |
| VALIDATION.json | `341a0d28170e134be3bd365210b3c838b10f9bfc335ccf8fb0fce89bc072cc8c` |
| SHA256SUMS.txt | `3b34be7d64d7f7227e853677ee9eab913ace570ca95fefae2fca97d03c0cc690` |

普通成员只需四个必需附件：ZIP、release.json、SHA256SUMS.txt、MANUAL.md；从随包手册第4节开始，不克隆仓库或自行打包。维护者／开发者和MCP管理员职责分开。交付目录示例、64位摘要填写、带双引号路径清洗、失败关闭和备份整包升级均在手册。不能只替换手册或混用v0.1.2 ZIP／摘要。

## 草稿、自审与发布后验收

固定运行ZIP只冻结一次，11文件逐字节匹配Git对象。候选、草稿、正式版的附件分别验证，全部7附件匹配GitHub digest和本地固定摘要，SHA256SUMS的6项均通过，MANUAL／CHANGELOG匹配发行源码blob。实际执行随包手册：引号中文空格路径校验与安装，11个安装文件摘要，先成功后缺清单时旧结果清空且安装被阻止，合成用户数据保留；本次目录已清理。发布后按正式标签执行开发者打包代码块，同样验证源码／内容树、同源冻结手册和11文件；无需扩大权限。公开手册已无凭据下载并核对相同摘要。

草稿Agent自审再次检查源码、CI、7附件、手册、升级与回滚范围及已知限制，无阻断项才转正式。发行脚本首次字符串组装SyntaxError、候选探针清理guard仍写旧v0.1.2前缀的AssertionError保留；后者在校验和安装已通过后触发保护，修复仅为本次辅助脚本版本前缀及清理后回执，不更改发行资产或降低断言。失败现场归档验证后清理，重验通过；未删除失败历史。

## 免费Host与剩余边界

详见[aju报告](HOST-RELEASE-aju.md)及[规范对照](STANDARDS-ALIGNMENT-g2i.md)。161 Python、15 Node、结构／42场景格式、16项已安装schema检查通过；普通权限read-only读成功、写拒绝。Codex修复批12次轨迹全过，原稿8/12，正向候选9/9；DSH修复批8正常、原稿6/8、原自动流程7/8。独立分配新图号后只读重放同一冻结答卷，六份正向候选6/6、两个反例不编译，重放8/8；原稿／原流程不改判，未再次抽样模型。两批共40个真实场景分开留证，16个DSH运行时释放且历史持久化、配置和默认模型不变，本次五个环境验证归档后清理。

日常Host没有自动编译Hook；模型草案可能校验失败，须纠正、校验、审阅后再确认，不能将JSON直接作为MCP参数。未验收真实成员环境、供应商生成／保存／视觉质量、其他OS／Claude／用户级或共享远端MCP、跨版本状态数据迁移，未修复PI-AI流读取故障。实际出图仍须确认当前方案、图号、输入及费用，发行不构成收费授权。

旧v0.1.0、v0.1.1、v0.1.2的Release ID／正文／资产ID、大小和摘要均按发布前快照复核，保持不变。没有修改已有Host／MCP安装、配置、权限或执行策略，没有收费图片调用。原生模型失败、原始得分、确定性候选、修复与旧Release历史均保留。

## 证据位置

本地`.eval-runs/release-v013/`保留源版本／CI、四次准入CI、草稿Agent自审、七附件下载摘要与安装探针、首次失败、修复及收尾。`host-archives.json`指向五份逐文件校验的Host档案；必要本地证据归档后清理临时环境，具体完整摘要见summary.json，不随运行包交付私有原始轨迹。

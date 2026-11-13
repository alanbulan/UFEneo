# 文档索引

用途：需要找规范、交接状态或验证结论时先读本页，再按主题进入唯一权威文件。一个主题只有一份权威文件；新事实写入对应文件，不另建副本或按日期追加。

| 文件 | 内容 | 何时读 |
| --- | --- | --- |
| [../AGENTS.md](../AGENTS.md) | 唯一执行准则 | 每轮开工前 |
| [../REBUILD_2D_PLAN.md](../REBUILD_2D_PLAN.md) | 设计目标、招式矩阵、阶段顺序 | 设计或规划招式时 |
| [PROGRESS.md](PROGRESS.md) | 可玩范围、各角色未完项、验证入口、接续优先级 | 接手或汇报时 |
| [PROJECT_LAYOUT.md](PROJECT_LAYOUT.md) | 目录归属、分层、依赖方向、数据流、模拟子系统、引擎选型、热点模块 | 找文件、改架构或评估引擎时 |
| [DATA_FORMATS.md](DATA_FORMATS.md) | 招式 JSON、持续束跟随发射点、独立实体攻击段 | 写招式数据时 |
| [ART_PIPELINE.md](ART_PIPELINE.md) | 生图流程、源库存储、武器覆盖规范 | 制作美术资源时 |
| [COMBAT_DESIGN.md](COMBAT_DESIGN.md) | 战斗形态与变身规则、三个能量必杀槽的技能差异 | 做装甲、形态或必杀时 |
| [STAGE1_STANDARD.md](STAGE1_STANDARD.md) | 未实机奥特曼 stage1 动作制作标准与验收细则 | 生产动作帧时 |
| [AUDIO.md](AUDIO.md) | Kits 音频接口、凭据与计费边界、怪兽配乐依据 | 制作、核对或分配声音时 |
| [THIRD_PARTY.md](THIRD_PARTY.md) | 上游版本、来源、许可 | 引入或核对第三方时 |
| [verification/](verification/README.md) | 可随仓库交付的验证结果摘要 | 核对历史验证结论时 |
| [../tools/README.md](../tools/README.md) | 工具目录归属、依赖与路径引导 | 增加或移动工具时 |
| [../tools/rebuild/seven-character-rework-20261112/README.md](../tools/rebuild/seven-character-rework-20261112/README.md) | 七角色返工当前在制批次的复算脚本 | 续作七角色动作时 |

## 维护规则

- 根目录只保留 `AGENTS.md`、`README.md`、`REBUILD_2D_PLAN.md` 三份 Markdown，不新增根级说明。
- 每份文档开头用一句话说明“是什么、何时读”；只写当前有效事实，不按日期追加互相矛盾的副本。
- 新增主题先判断能否并入现有文件；确需新文件时同步更新本索引，并更新代码、数据与文档中的旧路径。
- 历史回执只保留在 `docs/verification/` 或本机 `reports/`，不把当时状态当成现行规则。
- 单角色在制分镜与批次回执留在各自 `art/fighters/<id>/stageN/` 或 `tools/rebuild/<批次>/`，不复制成第二份进度文档；冻结任务书按 SHA 绑定后不得在中途改字。

## 不在 docs 的规范

| 文件 | 内容 |
| --- | --- |
| [../art/STYLE.md](../art/STYLE.md) | 像素风格、尺寸校验、远侧肢体、待机与走路 |
| `content/fighters/<id>/MOVES.md` | 单角色招式与原剧依据 |
| `content/fighters/<id>/SOUNDS.md` | 单角色声音台账 |
| `content/fighters/<id>/CANVAS.md` | 单角色画布与根点 |
| `art/fighters/<id>/model/CANVAS.md` | 定稿画布方案，被 `art/source-index.json` 记录 SHA |
| `reports/README.md` | 本机验证输出说明 |

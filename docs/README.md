# 文档索引

一个主题只有一份权威文件。新事实写入对应文件，不另建副本或按日期追加。

| 文件 | 内容 | 何时读 |
| --- | --- | --- |
| [../AGENTS.md](../AGENTS.md) | 唯一执行准则 | 每轮开工前 |
| [../REBUILD_2D_PLAN.md](../REBUILD_2D_PLAN.md) | 设计目标、招式矩阵、阶段顺序 | 设计或规划招式时 |
| [PROGRESS.md](PROGRESS.md) | 可玩范围、各角色未完项、验证入口、接续优先级 | 接手或汇报时 |
| [PROJECT_LAYOUT.md](PROJECT_LAYOUT.md) | 目录归属、分层、依赖方向、数据流、模拟子系统、热点模块 | 找文件或改架构时 |
| [ENGINE_CHOICE.md](ENGINE_CHOICE.md) | 引擎选型结论、可借鉴的业界做法、分层守卫 | 考虑换引擎或改架构时 |
| [DATA_FORMATS.md](DATA_FORMATS.md) | 招式 JSON、持续束跟随发射点、独立实体攻击段 | 写招式数据时 |
| [ART_PIPELINE.md](ART_PIPELINE.md) | 生图流程、源库存储、武器覆盖规范 | 制作美术资源时 |
| [FORMS.md](FORMS.md) | 战斗形态与变身规则 | 做装甲或形态时 |
| [SUPER_MOVE_DIVERSITY.md](SUPER_MOVE_DIVERSITY.md) | 三个能量必杀槽的技能差异规则 | 设计必杀时 |
| [AUDIO_API.md](AUDIO_API.md) | 音频接口凭据、连通性、子命令、计费边界 | 制作或核对声音时 |
| [THIRD_PARTY.md](THIRD_PARTY.md) | 上游版本、来源、许可 | 引入或核对第三方时 |
| [verification/](verification/README.md) | 可随仓库交付的验证结果摘要 | 核对历史验证结论时 |

## 不在 docs 的规范

| 文件 | 内容 |
| --- | --- |
| [../art/STYLE.md](../art/STYLE.md) | 像素风格、尺寸校验、远侧肢体、待机与走路 |
| `content/fighters/<id>/MOVES.md` | 单角色招式与原剧依据（19 份） |
| `content/fighters/<id>/SOUNDS.md` | 单角色声音台账 |
| `content/fighters/<id>/CANVAS.md` | 单角色画布与根点 |
| `art/fighters/<id>/model/CANVAS.md` | 定稿画布方案，被 `art/source-index.json` 记录 SHA |
| `reports/README.md` | 本机验证输出说明 |

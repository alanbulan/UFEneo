# 项目目录与架构

2026-11-03 清理后采用下列结构，2026-11-07 合并架构说明。执行准则只在根 [AGENTS](../AGENTS.md)，游戏规格只在 [REBUILD_2D_PLAN](../REBUILD_2D_PLAN.md)，当前状态、验证入口与接续优先级只在 [PROGRESS](PROGRESS.md)。不要往多份文件追加同一条用户指令。

## 目录归属

| 目录 | 内容 |
| --- | --- |
| `app/`、`app/scenes/` | 主游戏装配、流程和入口场景 |
| `core/` | 整数 60 tick 确定性模拟、状态和规则 |
| `input/` | 设备输入与电脑控制；审片驱动另列 `tests/review` |
| `presentation/` | 只读画面、镜头、特效和声音 |
| `ui/kit/`、`ui/theme/` | 正式界面组件和像素主题 |
| `content/fighters/<id>/` | 本人运行定义、招式、状态帧、形态、资料 |
| `content/catalogs/`、`roster/`、`templates/` | 查询门面、名册、公共数据模板 |
| `assets/{fighters,effects,audio,ui,stages,app,fx}/` | 已装资源、动态路径使用的资源、来源和许可；`fx` 是仍被当前注册表引用的旧接口目录 |
| `art/fighters/<id>/model/` | 当前定稿与测量，不重复存历史定稿 |
| `art/fighters/<id>/sources/` | 已装资源仍有用的唯一源文件，SHA 文件名；用途由 source-index 和原始 metadata 说明 |
| `art/fighters/<id>/stage<N>/` | 当前未完成动作、请求、候选和有效交接收据 |
| `art/shared/sources/` | 无法归属单角的当前源材料 |
| `art/source-index.json` | 现用源 SHA、字节数和旧路径到唯一实体的索引；不是备份 |
| `tools/runtime/` | 启动、Godot 定位与短临时录制 |
| `tools/rebuild/shared/`、`tools/rebuild/<id>/` | 复用制作模块、仍需接续的动作处理器、PixelFX 烘焙脚本 |
| `tools/maintenance/` | 只读仓库审计与冻结路径解析 |
| `tests/`、`tests/fixtures/`、`tests/review/` | 功能回归、必要输入夹具、主游戏内审片驱动 |
| `third_party/`、`addons/` | 实际采用的上游代码与许可 |
| `docs/` | 当前规范、交接、验证结果摘要 |
| `reports/` | 新运行产生的日志、截图、回放与临时视频；忽略上传 |

`art`、`tools`、`reports` 带 `.gdignore`，不进入 Godot 资源导入。二进制源与运行资源使用 Git LFS；Godot 的 `.uid` 和 `.import` 是源文件侧车，必须上传；`.godot` 导入缓存不上传。

原始来源收据内的旧路径保留字节。离线工具通过 `tools/maintenance/layout_runtime.py` 和 `art/source-index.json` 读取现有源；未列入索引的旧候选、审片、录屏和无用源已经删除，不能把这些历史文字当作运行依赖。实际主游戏仅加载 `assets`/`content` 等正式层。

本机环境、下载缓存和游戏个人存档不属于仓库。三个旧目录整理工作树及原 Git 历史直接清理，未新建备份。

## 分层与数据流

```
设备/回放 → InputFrame → 招式表解析 → 独立状态 → 帧数据
        → 命中结算 → 状态快照 → 表现（只读）
```

- `core`：纯整数、60 tick 确定性模拟，只包含 x 和离地高度；不依赖渲染、Input、随机数和系统时间。
- `input`：设备输入转换为 InputFrame。
- `presentation`：只读状态、招式、帧并播放整帧图像、特效和声音。
- `ui`：菜单和 HUD，以容器布局组合组件。
- `content`：规则、角色、招式、招式表。
- `assets`：运行时最终资源。

图片不进入模拟指纹。

## 模拟子系统

**专属技**：`core/combat/projectile_resolver.gd` 统一读取逐帧 `shots`、`projectile_guard` 和 `counter_shot`。飞行物框随整数位置推进；正面盾框可销毁、反射或吸收，反射保留原招式数据来源并转移攻击归属，吸收记录进入快照，只有实际吸收到才能反击。瞬移坐标只在招式数据的消失帧改变，表现层读取整帧透明度与独立 GPT 涟漪，不修改模拟。

**投技**：`core/combat/throw_resolver.gd` 在双方推进后统一配对。攻击方逐 tick 的 `target` 指定被投姿势编号、朝向、手部抓点和释放路径；被投者的独立姿势数据提供腰胯被抓点。抱持时按两点的世界坐标相等计算根点，释放后按整数进度落地；没有按角色体型写配对偏移。靠墙时两人整体平移。被抓后第 1–3 个真实 tick（含停顿）可拆，双方各播拆投并弹开；伤害只在落地冲击帧结算一次。表现层只读取这些结果，F1 可看抓点。

**演出**：开场倒计时与回合结束后的表现时钟分别驱动登场、胜负及时间到动画；模拟结束后保持冻结，演出不推进战斗、不进入回放指纹。挑衅仍是普通招式表驱动的独立动作，训练和对局均用防御+投技触发。

当前运行入口为 `app/scenes/main.tscn`。旧骨骼、纵深、废弃 UI 和整理历史不属于当前仓库；审片驱动集中到 `tests/review`，但仍在正式主游戏中运行。

## 热点模块

按 `codebase-memory` 索引（353,648 节点 / 357,656 边）的实际调用量：

| 模块 | fan-in | 职责 |
| --- | --- | --- |
| `core/replay/replay_recorder.gd` | 307 | 逐 tick 回放记录 |
| `core/commands/input_frame.gd` | 108 | 输入帧构造 |
| `ui/front_end.gd` | 78 | 菜单流程 |
| `core/combat/match_director.gd` | 71 | 对局主循环 |
| `content/content_database.gd` | 65 | 内容读取 |
| `core/fighters/fighter.gd` | 59 | 角色状态机入口 |

修改上述模块须跑完整回归；`tools/` 不在索引范围内，制作工具链按文件系统直接核对。

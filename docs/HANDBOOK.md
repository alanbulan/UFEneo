# UFEneo 工程与制作手册

用途：查阅系统架构、仓库白名单、数据契约、双模美术流水线、音频规范、工具链命令与第三方许可时读本文件。根 [README.md](../README.md) 是项目总览与四核心文档索引；根 [AGENTS.md](../AGENTS.md) 是唯一执行准则；根 [REBUILD_2D_PLAN.md](../REBUILD_2D_PLAN.md) 保留游戏设计、2.5 节招式矩阵与工程阶段顺序。

---

## 1. 架构总览与六层单向依赖（DAG）

项目继续采用 **Godot 4.7 + 自研整数 60 tick 确定性模拟**，不引入外部整套格斗引擎或 MUGEN CNS 解释器；数据、模拟与表现严格分离：

```
设备 / 回放 → UfeInputFrame → UfeInputBuffer → UfeMatchDirector (60Hz)
            → 独立状态与判定 → 状态快照 → UfeSideView (只读)
```

### 1.1 六层单向依赖与确定性硬门

```
app ──→ ui ──→ presentation ──→ content ──→ core ←── input
```

| 层 | 允许依赖 | 禁止边界与核心职责 |
| --- | --- | --- |
| `core` | 无（仅消费传入纯数据） | 禁止任何外部层及 `tests/`；禁止 `rand*`/`Time.`/`OS.get_ticks`/`Input.`；仅整数 `x` 与离地 `height` |
| `content` | `core` | 规则配置、状态映射、角色定义/招式/状态帧/形态与台账加载；不依赖 `presentation`/`ui`/`app` |
| `input` | `core` | 设备输入映射、电脑 AI 与 `UfeInputFrame` 构造；不依赖 `presentation`/`ui`/`app` |
| `presentation` | `core`、`content` | 严格只读模拟快照（KO 慢放副本除外）；禁止写活模拟 `stats`/`combat`/`motion`/`state`/坐标 |
| `ui` | `core`、`content`、`input`、`presentation` | 主菜单、HUD 安全区与像素套件界面；禁止反向引用 `app` |
| `app` | `core`、`content`、`input`、`presentation`、`ui` | 主场景 `app/scenes/main.tscn` 装配层，通过 `UfeAppHarness` 抽象挂载审片逻辑 |

- **运行层零 `tests/` 引用**：`tools/check/layering.py` 静态扫描全仓 `.gd` 的 `res://` 路径与全局 `class_name`，运行层（`core`/`content`/`input`/`presentation`/`ui`/`app`）严禁通过路径或全局类名引用 `tests/`。
- **指纹纯净性**：图像、音频与字体路径不进入 `content_fingerprint` 与 `state_hash`。

### 1.2 核心架构模块与职责拆分

| 模块 / 类 | 文件路径 | 核心职责与协议 |
| --- | --- | --- |
| `UfeFighter` | `core/fighters/fighter.gd` | 角色状态入口；持有强类型三组件并对外提供 `visual_pose()` 单源站姿协议 |
| `UfeFighterStats` | `core/fighters/fighter_stats.gd` | `hp`、`energy`、`stamina`、`stun`、`stun_immune`、`chill_ticks`、`chill_percent` |
| `UfeFighterCombat` | `core/fighters/fighter_combat.gd` | `buffer*`、`connected`/`confirmed`/`blocked`、`combo*`、`invulnerable`、`thrower`/`throw_age`/`throw_damage_done`、`power`、`absorbed`、`stamina_delay`、`round_score`、`hit_groups` |
| `UfeFighterMotion` | `core/fighters/fighter_motion.gd` | `jump_*`/`direction`/`duration`/`chase_window`/`land_window`/`bounce_*`、`crush_*`、`hit_pose`/`hit_crouch_guard_resume`/`pose*`、`ko_grounded_pose`、`throw_*`/`release_*`/`capture*` |
| `UfeStateRules` | `core/states/state_rules.gd` | 状态分组、谓词（`is_airborne_state`/`is_crouch_state`/`is_guard_state`/`is_guardable_state`）与舞台边界单一事实源（`STAGE_LEFT = 28`、`STAGE_RIGHT = 1252`、`clamp_stage_x()`、`stage_pair_shift()`） |
| `UfeMatchDirector` | `core/combat/match_director.gd` | 60Hz 主步进管线，负责输入消耗、物理推进、判定调度与状态迁移 |
| `UfeMatchFingerprint` | `core/combat/match_fingerprint.gd` | 内容指纹 `compute()` 与确定性序列化 `state_hash()`（从 `MatchDirector` 拆出） |
| `UfeInputBuffer` | `core/combat/input_buffer.gd` | 上下文映射 `command_state()`、缓冲 `remember()`（8 tick、保留最近 2 条）与取消释放 `release()` |
| `UfeHitResolver` / `UfeMeleeHitGroups` | `core/combat/hit_resolver.gd`、`melee_hit_groups.gd` | 攻击框命中、防御结算与独立实体多段命中（`hit_groups` 独立计数） |
| `UfeThrowResolver` / `UfeCaptureResolver` | `core/combat/throw_resolver.gd`、`capture_resolver.gd` | 双方推进后按抓点配对投技、3 tick 拆投窗口与多段捕获 |
| `UfeProjectileResolver` | `core/combat/projectile_resolver.gd` | 逐帧 `shots[]` 弹道推进、反射（保留原招来源并转移归属）、吸收与持续束追踪 |
| `UfeBattleTransform` | `core/combat/battle_transform.gd` | 战斗变身切换、形态条件与回合内形态保持 |
| `UfeContentDatabase` | `content/content_database.gd` | `_json_cache` 深拷贝缓存，加载招式时应用 `UfeFeelRules` 并执行 `UfeMoveData.validate()` 断言 |
| `UfeSideView` | `presentation/side_view.gd` | 只读表现视图；`_animation(f, manifest)` 仅保留开场/胜负覆盖、缺省回退与图集映射 |
| `UfeAppHarness` | `app/app_harness.gd` | `app/game_app.gd` 运行期审片抽象基类，通过 `--harness=res://tests/review/cli_harness.gd` 注入 |

### 1.3 单源站姿与序列化协议

- **强类型序列化等价**：`UfeFighterStats`、`UfeFighterCombat`、`UfeFighterMotion` 均提供 `duplicate_state()`、`from_dict()`、`to_dict()`，保留条件键语义（如空 `hit_groups` / `capture*` 不写入无用键），保证重构前后 `snapshot()` 与 `state_hash()` 完全等价。
- **`UfeFighter.visual_pose()`**：统一返回 `{"key", "tick", "move_sprite", "state_tick", "move_tick"}`，将移动（`walk_forward`/`walk_back`）、跳跃、击飞（`launch_rise`/`launch_fall`）、受击、被投、捕获与变身入场的动画名决策收敛至 `core`，`animation_key()` 直接复用；`UfeSideView._animation(f, manifest)` 仅做开场/胜负仪式覆盖、缺省剪辑回退与图集矩形/锚点查表。
- **确定性加载校验**：`UfeContentDatabase` 读取 JSON 后返回 `duplicate(true)` 深拷贝，并在 `fighter()` 加载阶段对每条招式跑 `UfeFeelRules.apply_move()`、`ensure_crush_charge()` 与 `UfeMoveData.validate()` 断言（校验方框正尺寸、合法 `origin_by_frame`、返航武器 `integer_path`、`chill`、`self_heal`、`hit_groups`、`capture` 等）。

---

## 2. 目录白名单与仓库卫生硬门

仓库卫生由 `tools/maintenance/repository_audit.py` 硬门守卫并随 `tools/verify.py` 自动执行：

| 检查域 | 白名单与强制规范 |
| --- | --- |
| 根目录文件 | 仅 `.editorconfig`、`.gitattributes`、`.gitignore`、`AGENTS.md`、`README.md`、`REBUILD_2D_PLAN.md`、`project.godot`、`开始游戏.command` |
| 根目录目录 | 仅 `addons`、`app`、`art`、`assets`、`content`、`core`、`docs`、`input`、`presentation`、`tests`、`third_party`、`tools`、`ui` |
| `docs/` | 仅允许 `HANDBOOK.md`（历史 `docs/verification/` 已彻底清除） |
| `art/` | Git 仅跟踪 `art/.gdignore`；本地制作源（`fighters/`、`audio/`、`shared/`、`catalogue-rebuild-20261113/`）留存本机由 `.gitignore` 忽略，禁止启用 Git LFS |
| `tools/` 顶层 | 可执行入口仅 `verify.py` 与 `godot_lock.py`（另含 `.gdignore`、`requirements-checks.txt`、`requirements-art.txt`） |
| Python 工具卫生 | 已彻底删除 `tools/rebuild/` 与 `layout_runtime` 猴子补丁；`tools/` 下模块名全局唯一，禁止通配 `sys.path` 注入，强制校验 `ROOT = parents[N]` |
| 全仓 `.md` 落盘白名单 | 只允许出现在根三核心（`README.md`、`AGENTS.md`、`REBUILD_2D_PLAN.md`）、`docs/HANDBOOK.md`、角色卡 `content/fighters/<id>/{MOVES.md,SOUNDS.md}`，以及 `third_party/**` / `addons/**` |
| 分支与仓外纪律 | 仅在仓库根目录 `main` 分支开发，禁止 `git worktree`、遗留本地分支及仓外母目录残留文件夹；禁止硬编码凭据与 >95MB 大文件 |

### 2.1 `tools/` 子包职责与 GDScript 零警告硬门

| `tools/` 子包 | 职责 |
| --- | --- |
| `tools/art/` | 角色全流程 CLI（`character_pipeline.py`）、I2V 抽帧（`video_frames.py`）、像素提取（`sprite_extract.py`）、落格拼装与受击框派生 |
| `tools/audio/` | Kits 离线分离客户端（`kits_client.py`）、音频处理管线（`pipeline.py`）、状态音效与转写辅助 |
| `tools/check/` | 资源、像素、分层、警告与音频质检门（全部在 `registry.py` 登记） |
| `tools/maintenance/` | 仓库目录白名单、Git 卫生、`.md` 位置与凭据审计（`repository_audit.py`） |
| `tools/media/` | 图鉴原生化与缩放（`catalogue_native.py`、`catalogue_rescale.py`）、参考图校验与音频切片度量 |
| `tools/roster/` | 名册编译、图鉴身份、繁简转换与百科资料整理 |
| `tools/runtime/` | Godot 串行环境（`environment.py`）、游戏启动器、页面截图（`capture_ui.py`）与短审片录制 |

**GDScript 零警告硬门**：`project.godot` `[debug]` 段固化 `gdscript/warnings/exclude_addons=true` 及全部 12 项严格警告级别 `=2`，由 `tools/check/gdscript_warnings.py` 只读校验配置并全仓扫描（零警告退出码 `0`）：
- `unused_parameter`、`unused_variable`、`unused_signal`、`integer_division`
- `int_as_enum_without_cast`、`shadowed_variable_base_class`、`shadowed_variable`、`standalone_expression`
- `incompatible_ternary`、`confusable_local_declaration`、`confusable_local_usage`、`shadowed_global_identifier`

---

## 3. 数据格式契约

所有模拟招式与状态轮廓均由 `content/` 下的 JSON 定义；脚底原点为 `(0, 0)`，朝前为 `+x`，离地向上为 `+y`，单位为原生像素。

### 3.1 核心文件契约表

| 文件路径 | 核心字段与结构说明 |
| --- | --- |
| `content/fighters/<id>/definition.json` | 角色基础信息：`id`、`display_name`、`template`、`playable`、`pilot_playable`、`unsupported_moves`、`max_health`、`walk_speed`、`jump_speed`、`body_radius`、`presentation`（`model`/`manifest`/`cell`/`anchor`/`target_height`/`anchor_y`/`impact_sparks`） |
| `content/fighters/<id>/moves/<id>.json` | 招式头字段：`startup`/`active`/`recovery`/`damage`/`hitstun`/`blockstun`/`pushback`/`stun`/`stamina_cost`/`energy_cost`/`kind`/`level`/`unblockable`/`launch`/`bounce`/`knockdown`；逐 tick 显式 `frames[]` |
| `content/fighters/<id>/state_frames.json` | 非招式状态（`idle`/`walk_forward`/`walk_back`/`crouch`/`guard`/`hit_*`/`down`/`wake` 等）逐 tick `sprite`/`dx`/`dy`/`hurtboxes`/`cancel`/`events` |
| `assets/fighters/<id>/animations/manifest.json` | 图集元数据：`schema: 1`、`cell`、`anchor`、`reviewed`、`clips.<name>`（`texture`、`cell`、`anchor`、`anchor_y`、`rects`、`ticks`、`loop`、`atlas_sha256`、`timeline_driven`） |
| `content/states.json` | 状态 ID 到 `res://core/states/*.gd` 脚本路径映射（包含 `transform`、`form_entry`、`capturing`、`captured` 全部运行状态） |
| `content/presentation/phase3_projectiles.json` | 全项目飞行道具、光束、刀光、受击与蓄气特效唯一注册表（`texture`、`rects`、`ticks`、`atlas_sha256`、`colors`、`alpha_binary`、`display_scale: [1,1]`） |

### 3.2 招式帧、远程、多段与投技协议

- **单帧最小结构（`UfeMoveData.validate()` 加载期强制校验）**：每帧必填 `sprite`、`dx`、`dy`、`hitboxes`、`hurtboxes`、`cancel`、`events`（方框 `[x, y, w, h]` 须 `w > 0 && h > 0`）：
  ```json
  {
    "sprite": 1, "dx": 0, "dy": 0,
    "hitboxes": [[22, 82, 56, 32]],
    "hurtboxes": [[-22, 100, 70, 50], [-28, 50, 75, 50], [-52, 0, 103, 50]],
    "cancel": ["special", "motion_236"],
    "events": [{"kind": "sound", "id": "light"}],
    "impact_effect": "impact_light", "block_effect": "impact_guard"
  }
  ```
- **图集剪辑结构（`animations/manifest.json`）**：
  ```json
  "clips": {
    "idle": {
      "texture": "res://assets/fighters/ultraseven/animations/idle/atlas.png",
      "cell": 192, "anchor": [96, 184], "anchor_y": 184,
      "rects": [[0, 0, 192, 192], [192, 0, 192, 192]], "ticks": [10, 10],
      "loop": true, "atlas_sha256": "..."
    }
  }
  ```
- **远程发射与持续束（`shots[]` 与 `origin_by_frame`）**：`kind: "projectile"` 与射线类招式 `frames[].hitboxes` 必须全空，发射只由命中首帧的 `shots[]` 触发，防止贴身误触发近战分支；持续束可在 `shots[]` 中声明 `origin_by_frame`（键为 `move_tick` 十进制字符串，值为 `[x, y]` 整数），未列出的 tick 回退到 `shot.anchor`：
  ```json
  { "effect": "seven_beam_core", "beam": true, "spawn": [17, 132], "anchor": [17, 132],
    "speed": 0, "life": 8, "origin_by_frame": {"6": [17, 132], "8": [19, 130]} }
  ```
- **显式返航武器与独立多段招式（`hit_groups`）**：
  - 返航武器（如头镖/光剑掷返）须声明 `weapon_id`、`integer_path`（首点 `[0,0]`）、`return_ticks`、`return_anchor`、`return_anchor_by_tick` 与 `owner_interrupt_policy: "clear"`。
  - `kind: "strike"` 多段实体招式在根定义 `"hit_groups": {"1": {...}, "2": {...}}`，有效帧填正整数 `"hit_group"`；每段在一次发动内最多接触一次并在 `UfeFighterCombat.hit_groups` 独立记账。
- **投技帧对齐（`target`）**：投技帧通过 `target` 指定被投方 `pose`、`sprite`、`facing`、`mode`（`"hold"`/`"release"`）、`grab_point`、`grip`、`root` 及可选 `hold_point_overrides`/`root_overrides`，靠墙时双方整体平移。

### 3.3 战斗形态、变身与三槽必杀规范

<a id="第-5-节--combat_designmd"></a>
- **形态与变身**：运行配置以 `content/catalogs/battle_forms.json` 为准（`E` 键与兼容 `22+P` 触发；`mode` 为 `palette` 调色板切换或 `definition` 完整角色替换，EX 形态切换后保持至 KO 与胜败结算，新局重建）。只有轮廓完全相同、仅换配色的形态可共用帧；八套装甲（亚刻三装甲、布莱泽法德兰、欧米伽四装甲）未各自齐备 S2–S7 动作、武器、技能、声音与回放闭环前不开放。
- **三槽必杀差异规则**：1/2/3 格能量必杀必须对应**三个不同名称、独立整帧人物动作与实际效果差异的技能**（例如近战/投摔、飞刃切割、连续射击、持续光线、抓取爆炸），不得仅靠改名、加粗光束或改数值拆分同一招式；原剧技能确实极少者须绑定角色、版本与可核实依据登记例外。

---

## 4. 角色与特效美术流水线（图/视频双模与统一硬门）

制作严格遵循「**先定帧数据与手感 → 训练模式验手感 → 按逻辑时长生产美术**」。美术帧数与每帧 tick 服从帧数据，严禁切肢拼片、骨骼旋转贴肢、静止人物加特效冒充动作或拉长单帧凑时长。

### 4.1 双生图通道与双模动作生产流程

1. **定帧数据与体感**：按 [REBUILD_2D_PLAN.md](../REBUILD_2D_PLAN.md) 2.5 节与 `core/combat/feel_rules.gd` 写定帧数据与手感档，在训练模式实测双向帧差、取消与滑动推退。
2. **官方皮套照定待机架势**：以 `art/fighters/<id>/sources/` 官方非玩具侧视参考定格斗待机架势（两脚外缘间距 ÷ 站高 = `0.65–0.80`，前后脚屈膝，双拳胸前护架，视线朝前）。`tools/art/identity_anchor.py` 产出的 4× 图鉴锚若原生宽 `<60 px` 则仅保证配色与像素块，不得单独作身材参考。
3. **双生图通道 A/B 择优定待机身份锚**：支持 **MCP `magpie-image.generate_image`**（如 `cpa/gpt-image-2.6-sunburst` 等，留空 `model` 跟随 Magpie 设置）与 **Antigravity 内置 `image-generator` 子代理**同题出图，输出 `path` 使用本仓库绝对路径；经 `tools/art/character_pipeline.py anchor` 对比分辨率、色数、连通块与轮廓比例后，定稿 **唯一 1 张侧视像素待机整帧** 作为后续全部动作的唯一身份锚。
4. **动作生产双模（只引用同一张待机像素锚）**：
   - **模式 A（图生视频 I2V 抽帧，优先推荐用于连贯/循环动作）**：
     - 以定稿待机像素整帧为首帧锚点，经 `magpie-image.generate_video` 生成 1–3 秒固定侧视机位、纯色背景连续动作短片；
     - 经 `tools/art/character_pipeline.py extract-video`（底层 `tools/art/video_frames.py` 调用 `ffmpeg`/`ffprobe` 抽帧、自动色键/Alpha 去背与二值化 + 内聚自 `third_party/sprite_gen_grid_range` 的 `tools/art/sprite_extract.py` 网格还原与 k-centroid 降采样）按待机锚唯一比例缩放，并映射到本人 `≤ 32` 色调色板（输出含 `stage_cells_frames` 参数的 `video_manifest.json`）。
   - **模式 B（整帧静态图/条带生成）**：
     - 以同一张待机像素锚为参考出单帧或条带（条带 `≤ 8` 帧），提示词约 `150–250` 字只写本帧动作并要求四肢粗细与锚一致、不写入角色没有的部件，经 `sprite_extract.py` 与 `stage_cells.py` 落格。
5. **同比例落格、装配与数据派生**：
   ```bash
   .venv/bin/python tools/art/stage_cells.py --fighter <id> \
     --scale-source <待机第0帧.png> --target-standing <设定站高> \
     --frame idle-00=<raw-00.png> --air jump-00
   ```
   - 默认制作格 `192×192`、根点 `[96, 184]`（高大/宽展角色按需统一升格如 `256×256` / `[128, 248]` 并在 `cells.json` 与 `manifest.json` 登记）；站高取 `content/roster/catalogue_display.json` 的设定档，全套共用同一源比例，严禁按帧外框归一身高或裁切轮廓。
   - 经 `compose_clip.py`（拼合剪辑）→ `install_cells.py`（输出水平拼接 `atlas.png` 与 `manifest.json`）→ `derive_fighter_data.py`（按实测 Alpha 轮廓派生受击框与 `state_frames.json`）→ `character_pipeline.py check`（运行 `sprite_quality.py` 与 `parity_matrix.py`）。

### 4.2 武器、脱手挂件与 PixelFX 规范

- **持械与脱手武器**：手持武器须与人物一起生成完整像素帧；脱手/悬停武器不烘焙进人物帧，空手人物帧通过招式帧 `attachments`（`effect`、`anchor`、`sprite`）挂接，并在出手帧同落点用 `shots[]` 接替，确保人物本体保持单连通。
- **特效烘焙与发射点**：人物帧严禁烘焙光束、光晕、颗粒或蓄气圈；周身蓄气圈只出现在真实 `Q` 蓄能（`charge_start`/`charge`/`charge_stop`）。飞行道具、刀光与打击光效统一由 `third_party/pixelfx` 离线烘焙为透明整帧（位于 `assets/fx/phase3` / `assets/effects/`），全部登记在 `content/presentation/phase3_projectiles.json` 并核对 `atlas_sha256` 与 `display_scale: [1,1]`；发射点对本人解剖部位双向误差 `≤ 2` 原生像素；近身命中框短边 `≥ round(0.22 × target_height)`。

### 4.3 统一质量、图鉴与取景硬门

| 检查维度 | 唯一现行硬指标 | 说明与执行工具 |
| --- | --- | --- |
| 走路循环 | `walk_forward` / `walk_back` 帧时长 `variance == 0` | 各帧严格等 tick 且相邻帧有可见手/臂/腿位移（`seven_demo_pipeline.py`、`sprite_quality.py`） |
| 远近肢体与色板 | 全套共用 `≤ 32` 色整图映射；近亮远暗、交叠 1px 深轮廓 | 保留额灯/计时器识别色，严禁程序局部区域换色或伪造剪影 |
| Alpha 与辉光门 | 二值 Alpha `{0, 255}`；非技能帧单连通 | 主体=`alpha>=200` 最大连通块外扩 `3 px`；主体外 `alpha>=200 == 0` 且 `alpha>=16 <= 100 px`；游离碎点 `<= 16 px` 报错 |
| 比例与冠顶测量 | 站姿帧高差 `≤ 8%`；同组相邻站姿突变 `≤ 10%` | 蹲/躺/被投/腾空豁免并登记；冠顶取眼列左右约 `26 px` 头部列带，不取整帧最高 Alpha 行 |
| 图鉴规格 | 固定 `384×256`、根点 `[192, 248]`（`3.84 px/m`，人 `96`） | 经 `catalogue_native.py` / `catalogue_rescale.py` 生成；横卧体型按 3 帧最大宽等比缩入（`strip_width_fit`）；静图与待机条同尺同色板（`catalogue_idle.py`） |
| 镜头与安全区 | 原生视口 `640×360`；镜头缩放固定 `1`（仅超半屏用 `1/2`/`1/3`） | 双方整帧 Alpha 与活跃投射物/持握实体受 `hud.battle_safe_rect()` 约束；通用候选验收用 `tests/review/common/candidate_harness.gd`（`UfeCandidateHarness`） |

> **制动规则**：同一项检查连续拒收 3 帧立即暂停并输出诊断图，同一问题最多尝试 2 种修法；逻辑或数值检查通过不等于美术人工审片通过。

---

## 5. 音频规范

### 5.1 台账双向绑定与来源分级

`content/audio/sources.json` 与 `content/audio/runtime.json`（`sounds` 键与 `voices` 映射）严格 **1:1 双向绑定**，未安装记录标 `pending_install`，已安装运行音频存放在 `assets/audio/`。

| 字段 / 分类 | 规范要求 |
| --- | --- |
| `sources.json` 必填字段 | `id`、`path`、`sha256`、`duration_seconds`、`sample_rate`、`true_peak_dbfs`、`source_kind`、`license`、`listening_reviewed`（可选 `integrated_lufs`） |
| `source_kind = original` | 项目自制（合成、录音或自制编曲），保留工程参数与种子 |
| `source_kind = episode` | 原剧/官方音源；公开转载副本必须同时写 `reprint: true` 并登记 `platform`、`uploader`、`source_url`、`source_timecode`、`raw_sha256`、`captured_utc` |
| `source_kind = derivative` | 二创、翻奏、MAD 等；严禁把二创或转载冒充原剧原声 |
| 图鉴试听与审听诚实 | `ui/kit/catalogue_sound.gd` 只复用已装合规音源；逻辑或格式检查通过不得把 `listening_reviewed` 写成 `true` |

### 5.2 音频规格、质检门与 Kits 边界

- **格式与混音标准**：运行时音效与语音统一 **48kHz、16-bit PCM WAV**；战斗 BGM 循环为 **48kHz 双声道 OGG Vorbis**（必杀仅把 BGM 音量压低到 `0.55` 不切曲）。
- **检查门门槛**：`tools/check/fx_audio.py` 校验 `sha256`、时长及 `true_peak_dbfs <= -1.8`；`tools/check/audio_manifest.py` 校验全部清单路径存在性、波形峰值 `0.01..0.995`（无静音/削波）、最小时长 `>= 0.03s` 与同类（sfx/voice/music）RMS 极差 `<= 12.0 dB`。
- **Kits 离线接口**：`tools/audio/pipeline.py` 仅作离线人声分离、分轨与语音转换（非文生音效/音乐）；凭据仅存本机环境变量 `UFE_KITS_API_KEY` 或 `~/.codex/secrets/ufeneo-music.key`（权限 `0600`），严禁入库、打印或复制。

---

## 6. 工具链速查表

运行游戏不依赖任何制作工具或网络密钥；本地校验需 `.venv`（`tools/requirements-checks.txt`），美术/媒体制作另需 `tools/requirements-art.txt` 与本机 `ffmpeg`/`ffprobe`。

### 6.1 验证与审片命令

```bash
.venv/bin/python tools/maintenance/repository_audit.py
.venv/bin/python tools/check/layering.py
.venv/bin/python tools/godot_lock.py -- .venv/bin/python tools/check/gdscript_warnings.py
.venv/bin/python tools/godot_lock.py -- .venv/bin/python tools/verify.py --keep-going
.venv/bin/python tools/godot_lock.py -- .venv/bin/python tools/verify.py --skip-import --only logic_2d
.venv/bin/python tools/check/sprite_quality.py --fighter <id>
```

`tools/check/registry.py` 统一登记全部检查门：
- **`verify` 模式（随 `tools/verify.py` 默认运行）**：`gdscript_warnings`、`layering`、`seven_demo_pipeline`、`catalogue_references`、`audio_manifest`、`fx_audio`、`pixel_ui`、`catalogue_idle`。
- **`authoring_gate` 模式（制作期与专项硬门）**：`catalogue_facing`、`frame_scale_jumps`、`sprite_quality`。

### 6.2 制作工具命令

| 工具 | 命令与子命令 | 说明 |
| --- | --- | --- |
| 角色锚点择优 | `.venv/bin/python tools/art/character_pipeline.py anchor --fighter <id> --magpie <a.png> --builtin <b.png> [--select <label>]` | 对比双通道分辨率/色数/连通块/头身与站距比并定标待机锚 |
| I2V 视频抽帧 | `.venv/bin/python tools/art/character_pipeline.py extract-video --fighter <id> --video <mp4> --clip <name> --anchor <idle.png>` | 调用 `video_frames.py` + `sprite_extract.py` 抽帧去背与 32 色像素化 |
| 落格与拼装 | `.venv/bin/python tools/art/character_pipeline.py stage --fighter <id> --scale-source <idle.png> --target-standing <H> --frame <name=path>` | 统一比例落格（可选 `--compose-clip` / `--ticks` 直接拼剪辑） |
| 派生与安装 | `.venv/bin/python tools/art/character_pipeline.py derive --fighter <id> --write` / `install --fighter <id>` | 派生受击框与 `state_frames.json`，安装 `atlas.png` 与 `manifest.json` |
| 质检与缺口 | `.venv/bin/python tools/art/character_pipeline.py check --fighter <id>` | 串联 `sprite_quality.py` 硬门与 `parity_matrix.py` 完整度检查 |
| 单项美术工具 | `tools/art/{identity_anchor,stage_cells,compose_clip,derive_fighter_data,install_cells,parity_matrix}.py` | 4× 锚、落格、拼 clip、按像素轮廓派生受击框、安装图集、缺口对比 |
| 图鉴原生/缩放 | `tools/media/art/{catalogue_native,catalogue_rescale}.py` | 生成与重设 `384×256` 图鉴静态定稿与待机条 |
| 主游戏 UI 截图 | `.venv/bin/python tools/runtime/capture_ui.py <pages...> [--resolution 1280x720]` | 经 `res://tests/review/cli_harness.gd` 截取主游戏 UI 页面 |
| 音频工具 | `.venv/bin/python tools/audio/pipeline.py <doctor\|models\|extract\|prepare-voice\|cut-cue\|submit\|poll\|download\|mix>` | 本地依赖与 Kits 分轨/转换工作流 |

---

## 7. 第三方许可归属

| 组件 / 目录 | 用途 | 许可与来源 |
| --- | --- | --- |
| `third_party/shoto/` | 纯逻辑指令解析与招式相位适配 | MIT（`aminRX/shoto-fighter-godot`） |
| `addons/controller_icons/` | 控制器/键盘提示图标插件（3.1.8） | MIT（`rsubtil/controller_icons`） |
| `third_party/sprite_gen_grid_range/` | 像素网格检测与还原（已内聚至 `tools/art/sprite_extract.py`） | Apache-2.0（含 MIT 提取端口声明，见 `NOTICE`） |
| `third_party/pixelfx/` | 离线烘焙透明像素特效（人物未采用库骨架） | MIT（`patch-gg/pixelfx`，见 `NOTICE.md`） |
| `third_party/pixel-snapper/` | 离线网格校正研究参考（未设为生产默认） | MIT（`Hugo-Dz/spritefusion-pixel-snapper`） |
| `third_party/rtmlib/` | 可选离线人体关键点参考测量（不做骨骼绑定） | Apache-2.0（`rtmlib` / `DWPose` / `MMPose`） |
| `third_party/libresprite/` | 可选离线像素编辑参考许可声明（未捆绑可执行文件） | GPL-2.0（`LibreSprite/LibreSprite`） |
| `third_party/godot_ui_components/` | UI Tween/过渡及溶解着色器参考适配 | MIT（`MrEliptik/godot_ui_components`） |
| `addons/godot_ai/` | 仅开发期编辑器调试辅助插件 | MIT（`hi-godot/godot-ai`） |
| 字体与 UI 套件 | Fusion Pixel Font（12px）/ Kenney Pixel UI | SIL OFL 1.1 / CC0（见 `assets/ui/` 许可文本） |

# 工具目录

用途：查找或新增验证、美术、音频、名册、媒体、维护工具时读本文件。运行游戏不需要这里的任何东西。

按职责分目录，一个工具只有一个位置。可执行入口只有顶层的 `verify.py` 与
`godot_lock.py`，其余是 README 与 requirements 文本。运行游戏**不需要**这里的任何东西；
这里的工具只服务验证、美术生产、音频制作和仓库维护。

## 顶层：只放两个入口

| 文件 | 用途 |
| --- | --- |
| `verify.py` | 全量运行时回归。**唯一**的验证入口 |
| `godot_lock.py` | Godot 串行锁。所有 Godot 导入、验证、录制都必须经它 |

```bash
.venv/bin/python tools/godot_lock.py -- .venv/bin/python tools/verify.py --keep-going
```

## 子目录

| 目录 | 职责 | 运行时机 |
| --- | --- | --- |
| `check/` | 资源与像素质检门（音频清单、UI 九宫格、站高、头身、岛屿、循环） | 验证时，部分被 `verify.py` 调用 |
| `art/` | 美术生产：生图、后处理、像素化、名册生产、编辑画布 | 制作美术时 |
| `audio/` | 音频制作：Kits 客户端、语音转写、混音 | 制作声音时 |
| `roster/` | 名册与资料：名册编译、图鉴身份、繁简转换、维基抓取 | 更新名册时 |
| `media/` | 媒体证据提取（音频切片、采样度量、持势证据） | 审片取证时 |
| `maintenance/` | 只读仓库审计、历史路径解析、源文件定位 | 随时 |
| `runtime/` | 启动器、Godot 定位、短临时录制 | 需要跑游戏或录制时 |
| `rebuild/` | 各角色**当前在制动作**的处理脚本与证据 | 继续某个未完成动作时 |

### 身份锚

动作帧生成只引用一张身份参考图，这张图是**待机像素整帧**（官方皮套照定格斗
待机架势 → 转像素整帧），见 `docs/STAGE1_STANDARD.md`。

`identity_anchor.py` 出的 4× 定稿锚是另一回事：它是定稿裁到 Alpha bbox 后的
4× 最近邻放大，不做调色、平滑或重采样，只保证配色与像素块大小。原生宽度
<60 px 的角色（盖亚 27、杰斯提斯 38、赛罗 36）模型读不出肩宽与四肢粗细，
不能单独作动作参考。

```bash
.venv/bin/python tools/art/identity_anchor.py --all        # 未实机的 ultra 角色
.venv/bin/python tools/art/identity_anchor.py ultraman-king
.venv/bin/python tools/art/identity_anchor.py <id> --force  # 已实机角色，人工排查用
```

来源以 `catalogue_display.json` 的 `entries[id].image` 与 `image_sha256` 为准，
不一致时跳过并在输出里列出，不改 display。产物为
`art/fighters/<id>/model/identity-anchor-x4.png` 和同名 `.json` 记录；
`--all` 排除已有 `assets/fighters/<id>/animations/manifest.json` 的角色。
正在手工制作的佐菲在任何模式下都不由本工具生成。

### 动作帧落格

单帧生成图落进 192×192 战斗格。色板取本人定稿的 32 色；**全套共用一个
源像素比例**，由一张直立参考帧的站高定出，因此屈膝、腾空保留真实压低，
不按每帧外框拉直（`art/STYLE.md` 禁止）。缩放后二值 Alpha、脚底贴
baseline-1、水平按脚底段重心对到 anchor x。

```bash
.venv/bin/python tools/art/stage_cells.py --fighter ultraman-nice \
  --scale-source art/fighters/ultraman-nice/stage1/idle/frames/raw-00.png \
  --target-standing 150 \
  --frame idle-00=art/fighters/ultraman-nice/stage1/idle/frames/raw-00.png \
  --frame walk-00=art/fighters/ultraman-nice/stage1/walk/frames/raw-00.png \
  --frame jump-00=art/fighters/ultraman-nice/stage1/jump/frames/raw-00.png --air jump-00
```

硬门只看机器能判的项：连通块必须 1、Alpha 必须二值、色数 ≤32。头高与站高
只报数值写进 `cells.json` 的 `notes`，因为前倾、腾空、护架摆臂会让自动测量
失真；比例由人看联系表判定，不冒充自动通过。

### 帧尺度突变检查

`check/frame_scale_jumps.py` 逐帧测已时装角色各 clip 的人物本体尺度：头骨顶到
脚底的站高、头宽与头部面积，与同 clip 中位数比较，阈值 ±8%。举起的武器和
细特效在测量前用 3×3 开运算剔除，不算进人物身高；蹲姿、腾空收腿只影响站高，
不会被头部指标误判。报告默认写到 `reports/frame-scale-jumps.json`，确定突变与
待人工复核帧都会非零退出。

```bash
.venv/bin/python tools/check/frame_scale_jumps.py --fighter ultraman-jack --verbose
.venv/bin/python tools/check/frame_scale_jumps.py --fighter ultraman-jack --clip motion_214 \
  --fix --frames 1 2 3          # 只缩回确定的整帧放大帧，脚底 anchor 不动
```

`--fix` 只接受已判为 `scale_jump` 的帧，最近邻缩放目标帧矩形、保持二值 Alpha，
其它帧逐字节不变；同步更新 manifest 的 `atlas_sha256`，并把修复前后测量写入
`reports/frame-scale-jumps/<fighter>-<clip>.json`。同一 clip 分批修复会合并记录，
保留各帧测量与每批 `passes`。`--force` 跳过 `fix_safe` 连贯性门，只在已看联系表
确认整帧均匀放大后使用；记录会标 `forced_without_safe_gate`。

`rebuild/` 按角色分子目录，每个子目录是一次具体动作的制作批次
（请求、候选、审片、安装）。它不是归档：里面仍有要接续的动作。
已完成的批次应把结果落到 `content/`、`assets/`、`docs/verification/`，
然后删除该批次目录。

`rebuild/body-rescale/` 是跨角色的体型重落格批次（2026-11-11）：按円谷
官方身高设定重推七名新装角色的 scale 并重落全部已装 stage1 战斗格；
配套 `recalc_hurtboxes.py` 按重落图集重算 state_frames 受击框并保留节奏
展开条目，见该目录 README.md。

## 依赖

```bash
.venv/bin/python -m pip install -r tools/requirements-checks.txt   # 跑验证
.venv/bin/python -m pip install -r tools/requirements-art.txt      # 做美术/名册
```

`requirements-checks.txt` 只有 Pillow 和 NumPy，是 `verify.py` 的全部依赖。
OpenCV、OpenCC、mwparserfromhell 只在美术和名册工具里用到。

## 路径引导

所有工具开头都有一段相同的引导，把 `tools/`、它的每个子目录、
以及 `tools/rebuild/` 的每个子目录加入 `sys.path`：

```python
_layout_sys.path[:0] = [str(_layout_root / "tools"),
    *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()],
    *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
```

因此工具之间用**裸模块名**互相引用（`from art.pipeline import ...`），
不要写 `tools.art.pipeline`。新增工具请沿用这段引导。

模块名在 `tools/` 全局唯一：不要出现两个同名 `.py`，
否则 `sys.path` 上先出现的那个会遮住另一个。

## 需要外部 sprite-gen 技能的工具

`art/produce_character.py` 经 `art_phase2` 依赖本机 `~/.codex/skills/sprite-gen`；
`rebuild/shared/forge_backend.py` 依赖 `~/.codex/skills/generate2dsprite`
（可用 `UFENEO_FORGE_ROOT` 覆盖）。两者是本机安装，缺失时无法导入，这是预期行为，
不是回归失败——`verify.py` 不包含它们。`check/walk_standing.py` 只用项目内的
`head_scale`、`walk_cycle_qa`、`current_walk_measurement`，不需要外部技能。
`third_party/sprite_gen_grid_range/` 只是格距范围覆盖层，不能单独提供该包。

## 不在这里的东西

- 游戏运行时资源：`assets/`
- 当前制作源：`art/`
- 游戏数据：`content/`
- 验证结果：`reports/`（本机）和 `docs/verification/`（可交付摘要）
- 第三方代码：`third_party/`、`addons/`

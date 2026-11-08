# 工具目录

用途：查找或新增验证、美术、音频、名册、媒体、维护工具时读本文件。运行游戏不需要这里的任何东西。

按职责分目录，一个工具只有一个位置。运行游戏**不需要**这里的任何东西；
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

`art/produce_character.py` 和 `check/walk_standing.py` 依赖本机安装的
sprite-gen 技能（`~/.codex/skills/generate2dsprite`）。本机未安装时它们
无法导入，这是预期行为，不是回归失败——`verify.py` 不包含它们。
`third_party/sprite_gen_grid_range/` 只是格距范围覆盖层，不能单独提供该包。

## 不在这里的东西

- 游戏运行时资源：`assets/`
- 当前制作源：`art/`
- 游戏数据：`content/`
- 验证结果：`reports/`（本机）和 `docs/verification/`（可交付摘要）
- 第三方代码：`third_party/`、`addons/`

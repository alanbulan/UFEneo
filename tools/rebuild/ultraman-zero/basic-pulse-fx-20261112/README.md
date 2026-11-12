# 基础赛罗光弹家族 2026-11-12

把基础赛罗四招仍在复用的共享弹体 `pulse` 换成本角色弹体家族：飞行段 `zero_fx_pulse_flight`、命中段 `zero_fx_pulse_hit`。人物动作帧不改，不在人物帧内烘焙任何特效。

## 本轮范围

- 生成：MCP `magpie-image`，模型 `codex/gpt-image-2`，quality high，background transparent，每次请求 1024×1024、2×2 四相图集；实收 1254×1254 RGBA，真 Alpha（透明占比 0.63–0.67，四角透明，无矩形底）。
- 原图与请求：`art/fighters/ultraman-zero/basic-pulse-fx-20261112/`（`raw/flight-sheet-01.png`、`raw/hit-sheet-01.png`、`requests.json`）。
- 运行图集：`assets/effects/ultraman-zero/basic-pulse-fx-20261112/{pulse_flight,pulse_hit}/atlas.png`，各附 `effect.json`、`provenance.json`。
- 登记条目：`phase3_entries.json`，完整 `{effect id: clip 对象}`；**未写入**共享 `content/presentation/phase3_projectiles.json`，也**未改** `charge_overlay_policy.json`。
- 招式接线：`pulse`、`low_pulse`、`air_pulse`、`ranged_forward` 的 `projectile.effect` 改为 `zero_fx_pulse_flight`，`feedback.projectile_impacts` 增加 `{zero_fx_pulse_flight: zero_fx_pulse_hit}`；人物帧、判定、伤害、tick、发射点、速度、寿命均未改。

## 形状与色板

- 飞行段：向右飞行的紧凑光弹，银白亮芯、蓝白等离子内层、深蓝中环、绯红锯齿外焰、银色近体碎屑；四相改变内部旋涡、外焰舌与碎屑位置，循环强度中—强—中—弱。
- 命中段：以命中点为中心的放射爆点，银白亮核、蓝白锯齿内环、绯红外焰尖刺、银蓝碎屑；四相为接触闪亮→扩张→环焰翻涌→收束，`loop=false`。
- 两段共用同一 16 色赛罗银红蓝板（`build.py` 的 `PALETTE`）；落格后实际 13 色。
- 不读取共享 `pulse` 或任何他角色特效图集作为形状来源。

## 落格口径

1. 2×2 按实收 1254/2＝627 分格；四格主体均未贴格边。
2. Alpha≥128 二值化，按格取主体外框；全段统一比例（flight 0.167331、hit 0.190476）。
3. 块内多数 Alpha + 逐通道中位色缩放到目标格；只保留最大 8 邻域连通块，其余可见像素清零。
4. 16 色板最近邻量化，Alpha 固定 0/255；飞行格 96×96 anchor [48,48]，命中格 128×128 anchor [64,64]。
5. 每帧主体按外框中心对到 anchor，不做逐帧拉伸。
6. 飞行段不写 `orientation="authored"`，沿用 runtime 对 `vy<0` 的 45° 既有旋转，使 `air_pulse` 斜下飞行时弹体朝向运动方向；命中段固定 `authored`。

## 硬门结果

所有帧（见 `build-report.json`）：

- Alpha 只有 0/255；`components_alpha200=1`、`components_alpha128=1`。
- 主体（alpha≥200 最大连通块）外扩 3 px 后，主体外 `alpha≥16 = 0 px`、`alpha≥200 = 0 px`。
- 图集 SHA-256 与 `effect.json`/`phase3_entries.json` 记录一致：
  - flight `6bac42a7610b64d6abc1c796bd68ca659578c4ceb834b42358f34cd22f921943`，384×96；
  - hit `8b5f7d66fe22e676fd944f0058d38c93089a608eec903d3d54d8a3b6ddd71819`，512×128。

## 复现

```bash
# 本机 Python（主仓库 .venv 或无 numpy/Pillow 的同名环境）
<PYTHON> tools/rebuild/ultraman-zero/basic-pulse-fx-20261112/build.py
<PYTHON> tools/rebuild/ultraman-zero/basic-pulse-fx-20261112/wire_moves.py
```

`build.py` 以 MCP 实收原图为唯一输入，确定性重建两张图集、两份 `effect.json`/`provenance.json`、`phase3_entries.json` 与 `build-report.json`，不写共享登记。

## 验证

```bash
python tools/godot_lock.py -- <PYTHON> tools/verify.py --skip-import --only roster_data_integrity phase3_air
```

结果（2026-11-12）：`roster_data_integrity: PASS`、`phase3_air: PASS`（Godot 4.7.2 headless，`--skip-import`）。未做 720/1080 实机目视，未录屏。

## 已知问题

- 共享 `phase3_projectiles.json` 未登记新 id，按任务边界留给后续装配合并；合并前运行时找不到图集，弹体与命中段会静默不可见，逻辑检查也不会报错。合并时直接取 `phase3_entries.json` 两条。
- 图集为 MCP 生成后离线硬 Alpha/量化，非原生像素硬边；四相造型由生成图决定，未逐帧人工重绘。
- 未实机看两个朝向与 720/1080；未听审。

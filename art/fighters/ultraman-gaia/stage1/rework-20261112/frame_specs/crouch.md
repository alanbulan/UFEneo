# 盖亚奥特曼 · V2 · `crouch` 逐帧返工规格（2026-11-12 定向修订）

- 角色：盖亚奥特曼 · V2（`ultraman-gaia`）
- clip：`crouch`
- 类别/优先级：primary_category=`fix_pose`；secondary_categories=[]；优先级=["P1", "fix_pose"]；任务来源=["P1 省略号展开", "primary/secondary 非 keep", "审计/测量/基线分类"]。
- status=spec_only
- 规格写入时点状态：按 F1 分片指令一律按 ready=false 处理，不创建或修改 identity_ready.json；后续外部 ready 状态不作为根正式 SendMessage，本规格不授权生图、落格或安装。

## cell/anchor/ticks/loop

- cell=256（逐 clip 取自身值；不得回落到 `cells.json` 旧顶层 anchor）；anchor=[128, 248]；loop=true。
- 旧 ticks=[10, 10]；目标规格 ticks=[10, 10]（仅逐帧规格建议，本轮未改 `state_frames.json` / `moves/*.json`）。
- 身份卡片唯一 scale=0.169182；待机锚站高=175；身份卡片顶层 cell/anchor={"width": 256, "anchor": [96, 184], "baseline": 248, "foot_row": 247}，仅作冲突登记，安装仍按本 clip 自身值。

## 旧逐帧高度、旧相邻差分与目标帧数

- 旧逐帧主体高度：[144, 147]；对锚站高偏差=[0.1771, 0.16]；相邻高度突变=[0.0208]。
- 旧相邻根点差分：[0.8332]；旧 bbox 对齐相邻差分：[0.8332]；循环差分=0.8332；低于 0.10 的旧相邻对=[]。
- 目标帧数=2；旧帧数=2；目标来源=沿用旧帧数（本轮不扩帧）。
- 诊断登记的站姿偏差 >8% 帧=[]；相邻站姿突变 >10% 帧=[]；站姿类对锚偏差与相邻突变门分别为 ≤8% / ≤10%。

## 已知 baked_fx

- 角色级 known_visual_fx（本 clip 相关）：[]。
- 本 clip 联系表确认：[]。
- 本 clip 独立连通帧：[]；高饱和亮色候选数=0。
- 诊断自动标记「烘焙特效或独立块」=false；人物帧一律按纯人物本体规格处理，技能光效只留运行时 shots/impact/特效层。

## 姿态例外及数值

- 诊断 classification=`posture_exception`；clip 在 identity_card 姿态例外清单中=true；逐帧旧高度=[144, 147]。
- 例外理由：蹲/躺/腾空/被投/深屈膝/伸展姿态；仍登记高度和骨长代理；允许蹲/躺/被投/腾空/深屈膝/伸展件等高度变化，但须登记数值并用头部列带稳定地标与骨长证明，不以「例外」放行整人缩放。
- 旧数值：对锚偏差=[0.1771, 0.16]；相邻高度突变=[0.0208]；站姿类高度偏差 >8% 或相邻突变 >10% 均须按唯一 scale 处理，不逐帧重标定。
- 例外规则：蹲/躺/被投/腾空/真实屈膝压低/伸展件展开允许高度变化，但必须逐帧登记数值并用头壳/骨长证明是姿势，不以「例外」放行整人缩放

## gap

- MOVES.md 缺集数/时码/镜头：依据文件 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/content/fighters/ultraman-gaia/MOVES.md`；MOVES.md 写明光色均为次级资料游戏取色，未逐帧核对影片、未写集数/时码；当前 V2 不开放 SV 技能。 制作代理不得补编镜头。
- emission_points：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/content/fighters/ultraman-gaia/emission_points.json` 存在=false；重画后须建人工依据表并双向 ≤2 px 重核。
- ready：磁盘 `identity_ready.json` ready=true，F1 分片制作门禁仍为 ready=false；根未正式 SendMessage，不改写该文件，不自行生成。
- raw/cells：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/stage1/rework-20261112/raw`、`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/stage1/rework-20261112/cells` 均不存在；本轮未生成、未落格、未安装。
- 录屏/实机：无录屏；未做双朝向 720/1080、真实输入、独立回放、原速画面；未听审，未签 root_delegated_by_user。
- 身份/资料冲突：["没有本人 90° 真实侧视来源；金额刃/头壳侧视前后方向禁止凭正面或 3/4 图写进生成规格。", "cells.json 顶层 anchor [96,184] 与全部装机 clip anchor [128,248] 不一致；definition.json 也保留 [96,184]/target_height 184。", "图鉴 model-native.png 色板与冻结动作色板交集为 0；不可直接跑 stage_cells.py 默认色板。", "MOVES.md 开头仍写未生成动作/未写 moves/未安装，是旧草案，不作为当前状态证明。"]
- 覆盖依据：["P1 省略号展开", "primary/secondary 非 keep", "审计/测量/基线分类"]；P1 省略号按 secondary redraw、baked_fx、known_visual_fx、diagnosis.md 重画顺序、F3 rejections 与审计分类展开。

## 逐帧分镜


| 帧 | 相位（起手/发力/收势） | 支撑脚 | 髋 | 肩 | 双拳/手 | 头与本人标志结构 | 相对前一帧的手/臂/腿可见位移 | 旧相邻差分 | 目标相邻差分 | 循环接续与起手/发力/收势 |
|---:|---|---|---|---|---|---|---|---:|---:|---|
| 0 | 起手 | 后脚承重 | 髋向后下方坐 | 双肩压低 | 双拳收胸护架 | 头颈微低；V2 金额刃、浅黄眼、宽黑内带金边 V 字胸甲、青蓝三角胸灯、红银 V2 躯体 随头壳与躯干整体位移，前后朝向不反向，不增删部件 | 较循环末拍 近拳胸架→肩前、远肘肋侧→膝上、前膝浅→深；后掌不滑 | 首帧无前帧 | ≥0.10 | 循环首尾目视可接 #0，辅助门 <0.20；本组按起手→发力→收势推进 |
| 1 | 下潜 | 前脚贴地前探 | 髋继续压低 | 近肩前探远肩护肋 | 近掌压低远拳护胸 | 头颈朝右；V2 金额刃、浅黄眼、宽黑内带金边 V 字胸甲、青蓝三角胸灯、红银 V2 躯体 随头壳与躯干整体位移，前后朝向不反向，不增删部件 | 较#0 近拳肩前→膝前、远肘膝上→肋后、前膝深→更低；支撑点不漂 | 0.8332 | ≥0.10 | 循环首尾目视可接 #0，辅助门 <0.20；本组按起手→发力→收势推进 |

## 独立动作提示词（逐帧）

### 第 0 帧动作提示词（Unicode 字符数=224）

```text
以唯一参考图的人物为同一人，只画此帧：【盖亚V2crouch#0起低身下潜后脚髋随动双肩压低拳收胸护架；较较环末近拳胸架→肩前、远肘肋侧→膝上、前膝浅→深，头随肩】。身份、配色、像素块大小交给参考图，不重复造型。四肢粗细与参考图完全一致：手臂粗壮、大腿饱满、小腿有厚度，不要画细长的手脚。固定 90° 右侧视、完整不裁切、真透明背景、只画人物本体、无光束/光晕/颗粒/蓄气圈/贴掌光/能量球/光刃/飞行物/地面/文字/边框/任何特效、不写技能光色。
```

### 第 1 帧动作提示词（Unicode 字符数=225）

```text
以唯一参考图的人物为同一人，只画此帧：【盖亚V2crouch#1下低身下潜前脚髋随动近肩前探掌压低拳护胸；较#0近拳肩前→膝前、远肘膝上→肋后、前膝深→更低，头随肩】。身份、配色、像素块大小交给参考图，不重复造型。四肢粗细与参考图完全一致：手臂粗壮、大腿饱满、小腿有厚度，不要画细长的手脚。固定 90° 右侧视、完整不裁切、真透明背景、只画人物本体、无光束/光晕/颗粒/蓄气圈/贴掌光/能量球/光刃/飞行物/地面/文字/边框/任何特效、不写技能光色。
```

本轮仅规格，未生成、未落格、未安装；请求/usage/新 raw SHA 无

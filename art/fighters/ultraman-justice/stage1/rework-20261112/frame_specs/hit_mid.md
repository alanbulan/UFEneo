# 杰斯提斯奥特曼 · 标准型 · `hit_mid` 逐帧返工规格（2026-11-12 定向修订）

- 角色：杰斯提斯奥特曼 · 标准型（`ultraman-justice`）
- clip：`hit_mid`
- 类别/优先级：primary_category=`redraw`；secondary_categories=[]；优先级=["P1", "F3", "redraw"]；任务来源=["P1 字面点名", "primary/secondary 非 keep", "diagnosis.md 点名", "storyboard.md 分镜节", "storyboard_required", "站姿尺度偏差", "任务书阶段B点名", "F3 rejections", "审计/测量/基线分类", "任务书阶段B显式清单"]。
- status=spec_only
- 规格写入时点状态：按 F1 分片指令一律按 ready=false 处理，不创建或修改 identity_ready.json；后续外部 ready 状态不作为根正式 SendMessage，本规格不授权生图、落格或安装。

## cell/anchor/ticks/loop

- cell=256（逐 clip 取自身值；不得回落到 `cells.json` 旧顶层 anchor）；anchor=[128, 248]；loop=false。
- 旧 ticks=[10, 10, 10]；目标规格 ticks=[10, 10, 10]（仅逐帧规格建议，本轮未改 `state_frames.json` / `moves/*.json`）。
- 身份卡片唯一 scale=0.161972；待机锚站高=161；身份卡片顶层 cell/anchor={"width": 256, "anchor": [128, 248], "baseline": 248, "foot_row": 247}，仅作冲突登记，安装仍按本 clip 自身值。

## 旧逐帧高度、旧相邻差分与目标帧数

- 旧逐帧主体高度：[139, 140, 164]；对锚站高偏差=[0.1366, 0.1304, 0.0186]；相邻高度突变=[0.0072, 0.1714]。
- 旧相邻根点差分：[0.5846, 0.681]；旧 bbox 对齐相邻差分：[0.5846, 0.681]；循环差分=null；低于 0.10 的旧相邻对=[]。
- 目标帧数=3；旧帧数=3；目标来源=storyboard.md 明确目标。
- 诊断登记的站姿偏差 >8% 帧=[{"frame": 0, "height": 139, "deviation": 0.1366}, {"frame": 1, "height": 140, "deviation": 0.1304}]；相邻站姿突变 >10% 帧=[{"pair": [1, 2], "heights": [140, 164], "jump": 0.1714}]；站姿类对锚偏差与相邻突变门分别为 ≤8% / ≤10%。
- F3 拒收帧：[{"frame": 0, "height": 139, "reasons": ["站姿高度偏差 13.66%>8%"]}, {"frame": 1, "height": 140, "reasons": ["站姿高度偏差 13.04%>8%"]}, {"frame": 2, "height": 164, "reasons": ["相邻站姿高度突变 17.14%>10%"]}]。

## 已知 baked_fx

- 角色级 known_visual_fx（本 clip 相关）：[]。
- 本 clip 联系表确认：[]。
- 本 clip 独立连通帧：[]；高饱和亮色候选数=0。
- 诊断自动标记「烘焙特效或独立块」=false；人物帧一律按纯人物本体规格处理，技能光效只留运行时 shots/impact/特效层。

## 姿态例外及数值

- 诊断 classification=`standing`；clip 在 identity_card 姿态例外清单中=false；逐帧旧高度=[139, 140, 164]。
- 例外理由：None；允许蹲/躺/被投/腾空/深屈膝/伸展件等高度变化，但须登记数值并用头部列带稳定地标与骨长证明，不以「例外」放行整人缩放。
- 旧数值：对锚偏差=[0.1366, 0.1304, 0.0186]；相邻高度突变=[0.0072, 0.1714]；站姿类高度偏差 >8% 或相邻突变 >10% 均须按唯一 scale 处理，不逐帧重标定。
- 例外规则：蹲/躺/被投/腾空/真实屈膝压低/伸展件展开允许高度变化，但必须逐帧登记数值并用头壳/骨长证明是姿势，不以「例外」放行整人缩放

## 返工方式（fix_scale）

- 未来优先从现有 raw 源按 identity_card 的唯一 scale 重新落格，不逐帧重标定、不整批覆盖，本轮不实际落格。

## gap

- MOVES.md 缺集数/时码/镜头：依据文件 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/content/fighters/ultraman-justice__standard/MOVES.md`；MOVES.md 明确资料是官方页招式名＋文字资料站＋游戏页，无逐帧剧集镜头、集数/时码；三槽独立技能有据，但具体姿态仍是文字依据。 制作代理不得补编镜头。
- emission_points：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/content/fighters/ultraman-justice/emission_points.json` 存在=false；重画后须建人工依据表并双向 ≤2 px 重核。
- ready：磁盘 `identity_ready.json` ready=false，F1 分片制作门禁仍为 ready=false；根未正式 SendMessage，不改写该文件，不自行生成。
- raw/cells：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-justice/stage1/rework-20261112/raw`、`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-justice/stage1/rework-20261112/cells` 均不存在；本轮未生成、未落格、未安装。
- 录屏/实机：无录屏；未做双朝向 720/1080、真实输入、独立回放、原速画面；未听审，未签 root_delegated_by_user。
- 身份/资料冲突：["requests.json / super_portrait/REPORT.md / tools/rebuild/ultraman-justice/README.md 记录已签锚 SHA e1dbeeabb86a8256de833b92b5f24b30fffc45a8b91b121ff06d5594156df00d、192×192、root [96,184]；仓库内按 SHA 全盘查找无此文件。", "现用 idle-candidate-04-cell.png 为 256×256、SHA f9de9f2d…、站高 161；装机 idle/atlas.png 为 256×256、SHA d2ab7f80…、站高 161。", "4× 文件 idle-candidate-04-x4.png 保留青绿识别色 128 px，但当前 256 格锚与装机待机的青绿识别色为 0；cells.json 没有保存完整 32 色板，必须回源重建并冻结后再出动作帧。", "definition.json presentation.cell=288/target_height=184 与装机 256/161 不一致；另有 4 个 clip 仍为 192 格、root [96,184]。"]
- 覆盖依据：["P1 字面点名", "primary/secondary 非 keep", "diagnosis.md 点名", "storyboard.md 分镜节", "storyboard_required", "站姿尺度偏差", "任务书阶段B点名", "F3 rejections", "审计/测量/基线分类", "任务书阶段B显式清单"]；P1 省略号按 secondary redraw、baked_fx、known_visual_fx、diagnosis.md 重画顺序、F3 rejections 与审计分类展开。

## 逐帧分镜


| 帧 | 相位（起手/发力/收势） | 支撑脚 | 髋 | 肩 | 双拳/手 | 头与本人标志结构 | 相对前一帧的手/臂/腿可见位移 | 旧相邻差分 | 目标相邻差分 | 循环接续与起手/发力/收势 |
|---:|---|---|---|---|---|---|---|---:|---:|---|
| 0 | 受击 | 后脚先滑 | 髋被向后顶 | 近肩后仰远肩下垂 | 双拳离胸架向后张 | 头颈后仰；中央高窄银冠、深色面罩与口部板、青绿额灯/胸灯、薄贴身肩甲；标准型 随头壳与躯干整体位移，前后朝向不反向，不增删部件 | 较锚护架 近拳胸→肩外、远肘肋→身后、前膝浅→伸；支撑点不漂 | 首帧无前帧 | ≥0.10 | 非循环；末帧回可接待机护架；本组按起手→发力→收势推进 |
| 1 | 回弹 | 前脚重新踩实 | 髋向前回正 | 双肩内收 | 双拳由身后拉回胸前 | 头颈回正；中央高窄银冠、深色面罩与口部板、青绿额灯/胸灯、薄贴身肩甲；标准型 随头壳与躯干整体位移，前后朝向不反向，不增删部件 | 较#0 近拳肩外→胸架、远肘身后→贴肋、前膝伸→浅屈；两脚掌接地 | 0.5846 | ≥0.10 | 非循环；末帧回可接待机护架；本组按起手→发力→收势推进 |
| 2 | 收势 | 双脚前后固定 | 髋稳住 | 双肩护架 | 双拳胸前 | 头颈稳定；中央高窄银冠、深色面罩与口部板、青绿额灯/胸灯、薄贴身肩甲；标准型 随头壳与躯干整体位移，前后朝向不反向，不增删部件 | 较#1 近拳胸架→微收、远肘贴肋→护胸、双膝浅屈→稳态；末拍回待机 | 0.681 | ≥0.10 | 非循环；末帧回可接待机护架；本组按起手→发力→收势推进 |

## 独立动作提示词（逐帧）

### 第 0 帧动作提示词（Unicode 字符数=221）

```text
以唯一参考图的人物为同一人，只画此帧：【杰斯hit_mid#0受中段受击后脚髋随动近肩后仰拳离胸架向后；较较锚近拳胸→肩外、远肘肋→身后、前膝浅→伸，头随肩】。身份、配色、像素块大小交给参考图，不重复造型。四肢粗细与参考图完全一致：手臂粗壮、大腿饱满、小腿有厚度，不要画细长的手脚。固定 90° 右侧视、完整不裁切、真透明背景、只画人物本体、无光束/光晕/颗粒/蓄气圈/贴掌光/能量球/光刃/飞行物/地面/文字/边框/任何特效、不写技能光色。
```

### 第 1 帧动作提示词（Unicode 字符数=224）

```text
以唯一参考图的人物为同一人，只画此帧：【杰斯hit_mid#1回中段受击前脚髋随动双肩内收拳由身后拉回；较#0近拳肩外→胸架、远肘身后→贴肋、前膝伸→浅屈，头随肩】。身份、配色、像素块大小交给参考图，不重复造型。四肢粗细与参考图完全一致：手臂粗壮、大腿饱满、小腿有厚度，不要画细长的手脚。固定 90° 右侧视、完整不裁切、真透明背景、只画人物本体、无光束/光晕/颗粒/蓄气圈/贴掌光/能量球/光刃/飞行物/地面/文字/边框/任何特效、不写技能光色。
```

### 第 2 帧动作提示词（Unicode 字符数=222）

```text
以唯一参考图的人物为同一人，只画此帧：【杰斯hit_mid#2收中段受击双脚髋稳转双肩护架拳胸前；较#1近拳胸架→微收、远肘贴肋→护胸、双膝浅屈→稳态，头随肩】。身份、配色、像素块大小交给参考图，不重复造型。四肢粗细与参考图完全一致：手臂粗壮、大腿饱满、小腿有厚度，不要画细长的手脚。固定 90° 右侧视、完整不裁切、真透明背景、只画人物本体、无光束/光晕/颗粒/蓄气圈/贴掌光/能量球/光刃/飞行物/地面/文字/边框/任何特效、不写技能光色。
```

本轮仅规格，未生成、未落格、未安装；请求/usage/新 raw SHA 无

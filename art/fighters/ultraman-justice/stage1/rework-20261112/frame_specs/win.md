# 杰斯提斯奥特曼 · 标准型 · `win` 逐帧返工规格（2026-11-12 定向修订）

- 角色：杰斯提斯奥特曼 · 标准型（`ultraman-justice`）
- clip：`win`
- 类别/优先级：primary_category=`redraw`；secondary_categories=[]；优先级=["P1", "redraw"]；任务来源=["P1 省略号展开", "primary/secondary 非 keep", "diagnosis.md 点名", "storyboard.md 分镜节", "storyboard_required", "任务书阶段B点名", "审计/测量/基线分类", "任务书阶段B显式清单"]。
- status=spec_only
- 规格写入时点状态：按 F1 分片指令一律按 ready=false 处理，不创建或修改 identity_ready.json；后续外部 ready 状态不作为根正式 SendMessage，本规格不授权生图、落格或安装。

## cell/anchor/ticks/loop

- cell=256（逐 clip 取自身值；不得回落到 `cells.json` 旧顶层 anchor）；anchor=[128, 248]；loop=false。
- 旧 ticks=[10, 10]；目标规格 ticks=[10, 10]（仅逐帧规格建议，本轮未改 `state_frames.json` / `moves/*.json`）。
- 身份卡片唯一 scale=0.161972；待机锚站高=161；身份卡片顶层 cell/anchor={"width": 256, "anchor": [128, 248], "baseline": 248, "foot_row": 247}，仅作冲突登记，安装仍按本 clip 自身值。

## 旧逐帧高度、旧相邻差分与目标帧数

- 旧逐帧主体高度：[170, 165]；对锚站高偏差=[0.0559, 0.0248]；相邻高度突变=[0.0294]。
- 旧相邻根点差分：[0.1947]；旧 bbox 对齐相邻差分：[0.1947]；循环差分=null；低于 0.10 的旧相邻对=[]。
- 目标帧数=2；旧帧数=2；目标来源=storyboard.md 明确目标。
- 诊断登记的站姿偏差 >8% 帧=[]；相邻站姿突变 >10% 帧=[]；站姿类对锚偏差与相邻突变门分别为 ≤8% / ≤10%。

## 已知 baked_fx

- 角色级 known_visual_fx（本 clip 相关）：[]。
- 本 clip 联系表确认：[]。
- 本 clip 独立连通帧：[]；高饱和亮色候选数=0。
- 诊断自动标记「烘焙特效或独立块」=false；人物帧一律按纯人物本体规格处理，技能光效只留运行时 shots/impact/特效层。

## 姿态例外及数值

- 诊断 classification=`standing`；clip 在 identity_card 姿态例外清单中=false；逐帧旧高度=[170, 165]。
- 例外理由：None；允许蹲/躺/被投/腾空/深屈膝/伸展件等高度变化，但须登记数值并用头部列带稳定地标与骨长证明，不以「例外」放行整人缩放。
- 旧数值：对锚偏差=[0.0559, 0.0248]；相邻高度突变=[0.0294]；站姿类高度偏差 >8% 或相邻突变 >10% 均须按唯一 scale 处理，不逐帧重标定。
- 例外规则：蹲/躺/被投/腾空/真实屈膝压低/伸展件展开允许高度变化，但必须逐帧登记数值并用头壳/骨长证明是姿势，不以「例外」放行整人缩放

## gap

- MOVES.md 缺集数/时码/镜头：依据文件 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/content/fighters/ultraman-justice__standard/MOVES.md`；MOVES.md 明确资料是官方页招式名＋文字资料站＋游戏页，无逐帧剧集镜头、集数/时码；三槽独立技能有据，但具体姿态仍是文字依据。 制作代理不得补编镜头。
- emission_points：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/content/fighters/ultraman-justice/emission_points.json` 存在=false；重画后须建人工依据表并双向 ≤2 px 重核。
- ready：磁盘 `identity_ready.json` ready=false，F1 分片制作门禁仍为 ready=false；根未正式 SendMessage，不改写该文件，不自行生成。
- raw/cells：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-justice/stage1/rework-20261112/raw`、`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-justice/stage1/rework-20261112/cells` 均不存在；本轮未生成、未落格、未安装。
- 录屏/实机：无录屏；未做双朝向 720/1080、真实输入、独立回放、原速画面；未听审，未签 root_delegated_by_user。
- 身份/资料冲突：["requests.json / super_portrait/REPORT.md / tools/rebuild/ultraman-justice/README.md 记录已签锚 SHA e1dbeeabb86a8256de833b92b5f24b30fffc45a8b91b121ff06d5594156df00d、192×192、root [96,184]；仓库内按 SHA 全盘查找无此文件。", "现用 idle-candidate-04-cell.png 为 256×256、SHA f9de9f2d…、站高 161；装机 idle/atlas.png 为 256×256、SHA d2ab7f80…、站高 161。", "4× 文件 idle-candidate-04-x4.png 保留青绿识别色 128 px，但当前 256 格锚与装机待机的青绿识别色为 0；cells.json 没有保存完整 32 色板，必须回源重建并冻结后再出动作帧。", "definition.json presentation.cell=288/target_height=184 与装机 256/161 不一致；另有 4 个 clip 仍为 192 格、root [96,184]。"]
- 覆盖依据：["P1 省略号展开", "primary/secondary 非 keep", "diagnosis.md 点名", "storyboard.md 分镜节", "storyboard_required", "任务书阶段B点名", "审计/测量/基线分类", "任务书阶段B显式清单"]；P1 省略号按 secondary redraw、baked_fx、known_visual_fx、diagnosis.md 重画顺序、F3 rejections 与审计分类展开。

## 逐帧分镜


| 帧 | 相位（起手/发力/收势） | 支撑脚 | 髋 | 肩 | 双拳/手 | 头与本人标志结构 | 相对前一帧的手/臂/腿可见位移 | 旧相邻差分 | 目标相邻差分 | 循环接续与起手/发力/收势 |
|---:|---|---|---|---|---|---|---|---:|---:|---|
| 0 | 起手 | 后脚承重 | 髋稳在锚架 | 双肩打开 | 双拳由胸架抬到肩前 | 头颈朝右；中央高窄银冠、深色面罩与口部板、青绿额灯/胸灯、薄贴身肩甲；标准型 随头壳与躯干整体位移，前后朝向不反向，不增删部件 | 较锚护架 近拳胸→肩前、远肘肋→肩后、前膝浅→稳；脚位不动 | 首帧无前帧 | ≥0.10 | 非循环；末帧回可接待机护架；本组按起手→发力→收势推进 |
| 1 | 定型 | 前脚轻点 | 髋微沉 | 近肩上举远肩外展 | 近拳抬到头侧远拳留腰侧 | 头颈微抬；中央高窄银冠、深色面罩与口部板、青绿额灯/胸灯、薄贴身肩甲；标准型 随头壳与躯干整体位移，前后朝向不反向，不增删部件 | 较#0 近拳肩前→头侧、远肘肩后→腰侧、前膝稳→浅屈；支撑点不漂 | 0.1947 | ≥0.10 | 非循环；末帧回可接待机护架；本组按起手→发力→收势推进 |

## 独立动作提示词（逐帧）

### 第 0 帧动作提示词（Unicode 字符数=217）

```text
以唯一参考图的人物为同一人，只画此帧：【杰斯win#0起胜利收势后脚髋稳转双肩打开拳由胸架抬到；较较锚近拳胸→肩前、远肘肋→肩后、前膝浅→稳，头随肩】。身份、配色、像素块大小交给参考图，不重复造型。四肢粗细与参考图完全一致：手臂粗壮、大腿饱满、小腿有厚度，不要画细长的手脚。固定 90° 右侧视、完整不裁切、真透明背景、只画人物本体、无光束/光晕/颗粒/蓄气圈/贴掌光/能量球/光刃/飞行物/地面/文字/边框/任何特效、不写技能光色。
```

### 第 1 帧动作提示词（Unicode 字符数=220）

```text
以唯一参考图的人物为同一人，只画此帧：【杰斯win#1定胜利收势前脚髋随动近肩上举拳抬到头侧拳；较#0近拳肩前→头侧、远肘肩后→腰侧、前膝稳→浅屈，头随肩】。身份、配色、像素块大小交给参考图，不重复造型。四肢粗细与参考图完全一致：手臂粗壮、大腿饱满、小腿有厚度，不要画细长的手脚。固定 90° 右侧视、完整不裁切、真透明背景、只画人物本体、无光束/光晕/颗粒/蓄气圈/贴掌光/能量球/光刃/飞行物/地面/文字/边框/任何特效、不写技能光色。
```

本轮仅规格，未生成、未落格、未安装；请求/usage/新 raw SHA 无

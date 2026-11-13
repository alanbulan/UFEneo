# 赛罗奥特曼 · 基本红蓝形态 · `light2` 逐帧返工规格（2026-11-12 定向修订）

- 角色：赛罗奥特曼 · 基本红蓝形态（`ultraman-zero`）
- clip：`light2`
- 类别/优先级：primary_category=`redraw`；secondary_categories=[]；优先级=["P1", "F3", "redraw"]；任务来源=["P1 字面点名", "primary/secondary 非 keep", "baked_fx", "diagnosis.md 点名", "storyboard.md 分镜节", "storyboard_required", "任务书阶段B点名", "F3 rejections", "审计/测量/基线分类", "任务书阶段B显式清单"]。
- status=spec_only
- 规格写入时点状态：按 F1 分片指令一律按 ready=false 处理，不创建或修改 identity_ready.json；后续外部 ready 状态不作为根正式 SendMessage，本规格不授权生图、落格或安装。

## cell/anchor/ticks/loop

- cell=256（逐 clip 取自身值；不得回落到 `cells.json` 旧顶层 anchor）；anchor=[128, 248]；loop=false。
- 旧 ticks=[10, 10, 10]；目标规格 ticks=[10, 10, 10]（仅逐帧规格建议，本轮未改 `state_frames.json` / `moves/*.json`）。
- 身份卡片唯一 scale=0.158767；待机锚站高=172；身份卡片顶层 cell/anchor={"width": 256, "anchor": [128, 248], "baseline": 248, "foot_row": 247}，仅作冲突登记，安装仍按本 clip 自身值。

## 旧逐帧高度、旧相邻差分与目标帧数

- 旧逐帧主体高度：[174, 174, 174]；对锚站高偏差=[0.0116, 0.0116, 0.0116]；相邻高度突变=[0.0, 0.0]。
- 旧相邻根点差分：[0.2519, 0.2418]；旧 bbox 对齐相邻差分：[0.2519, 0.2418]；循环差分=null；低于 0.10 的旧相邻对=[]。
- 目标帧数=3；旧帧数=3；目标来源=storyboard.md 明确目标。
- 诊断登记的站姿偏差 >8% 帧=[]；相邻站姿突变 >10% 帧=[]；站姿类对锚偏差与相邻突变门分别为 ≤8% / ≤10%。
- F3 拒收帧：[{"frame": 1, "height": 174, "reasons": ["4 邻域主体连通块 3≠1"]}, {"frame": 2, "height": 174, "reasons": ["4 邻域主体连通块 4≠1"]}]。

## 已知 baked_fx

- 角色级 known_visual_fx（本 clip 相关）：[]。
- 本 clip 联系表确认：[]。
- 本 clip 独立连通帧：[{"frame": 1, "components4": 3, "components8": 1, "component_sizes4": [7137, 1, 1], "component_sizes8": [7139]}, {"frame": 2, "components4": 4, "components8": 3, "component_sizes4": [6469, 2, 1, 1], "component_sizes8": [6470, 2, 1]}]；高饱和亮色候选数=5。
- 诊断自动标记「烘焙特效或独立块」=true；人物帧一律按纯人物本体规格处理，技能光效只留运行时 shots/impact/特效层。

## 姿态例外及数值

- 诊断 classification=`standing`；clip 在 identity_card 姿态例外清单中=false；逐帧旧高度=[174, 174, 174]。
- 例外理由：None；允许蹲/躺/被投/腾空/深屈膝/伸展件等高度变化，但须登记数值并用头部列带稳定地标与骨长证明，不以「例外」放行整人缩放。
- 旧数值：对锚偏差=[0.0116, 0.0116, 0.0116]；相邻高度突变=[0.0, 0.0]；站姿类高度偏差 >8% 或相邻突变 >10% 均须按唯一 scale 处理，不逐帧重标定。
- 例外规则：蹲/躺/被投/腾空/真实屈膝压低/伸展件展开允许高度变化，但必须逐帧登记数值并用头壳/骨长证明是姿势，不以「例外」放行整人缩放

## gap

- MOVES.md 缺集数/时码/镜头：依据文件 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/content/fighters/ultraman-zero/MOVES.md`；MOVES.md 只记已装状态和名称，未给剧集/时码/逐帧镜头；原剧一级/二级/三级名称仍属内容依据缺口，制作代理不得补编镜头。 制作代理不得补编镜头。
- emission_points：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/content/fighters/ultraman-zero/emission_points.json` 存在=false；重画后须建人工依据表并双向 ≤2 px 重核。
- ready：磁盘 `identity_ready.json` ready=true，F1 分片制作门禁仍为 ready=false；根未正式 SendMessage，不改写该文件，不自行生成。
- raw/cells：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-zero/stage1/rework-20261112/raw`、`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-zero/stage1/rework-20261112/cells` 均不存在；本轮未生成、未落格、未安装。
- 录屏/实机：无录屏；未做双朝向 720/1080、真实输入、独立回放、原速画面；未听审，未签 root_delegated_by_user。
- 身份/资料冲突：["cells.json 早期字段 target_standing_height=188 是身份锚原生站高；2026-11-11 重标定后装机站高 172、scale 0.158767，本卡片以后者为唯一返工尺度。", "definition.json presentation.cell=288/target_height=188 是旧口径；装机 113 个 clip 为 256、air_special 为 288。", "assets/fighters/ultraman-zero/catalogue/model-native.png 的 32 色与冻结动作色板交集为 0；不可直接跑 stage_cells.py 默认色板。"]
- 覆盖依据：["P1 字面点名", "primary/secondary 非 keep", "baked_fx", "diagnosis.md 点名", "storyboard.md 分镜节", "storyboard_required", "任务书阶段B点名", "F3 rejections", "审计/测量/基线分类", "任务书阶段B显式清单"]；P1 省略号按 secondary redraw、baked_fx、known_visual_fx、diagnosis.md 重画顺序、F3 rejections 与审计分类展开。

## 逐帧分镜


| 帧 | 相位（起手/发力/收势） | 支撑脚 | 髋 | 肩 | 双拳/手 | 头与本人标志结构 | 相对前一帧的手/臂/腿可见位移 | 旧相邻差分 | 目标相邻差分 | 循环接续与起手/发力/收势 |
|---:|---|---|---|---|---|---|---|---:|---:|---|
| 0 | 起手 | 后脚承重 | 髋轻微后转 | 近肩后收远肩压肋 | 双拳收胸 | 头颈微低；双头镖自额前向头顶后上方折起、蓝额灯、黄眼、蓝计时器、层叠银蓝肩胸甲 随头壳与躯干整体位移，前后朝向不反向，不增删部件 | 较锚护架 近拳胸→肩后、远肘肋→腰后、前膝浅→稳；后掌不动 | 首帧无前帧 | ≥0.10 | 非循环；末帧回可接待机护架；本组按起手→发力→收势推进 |
| 1 | 发力 | 前脚点地 | 髋反向弹出 | 近肩横向前送远肩回收 | 近拳由肩后横打远拳收颌 | 头颈朝右；双头镖自额前向头顶后上方折起、蓝额灯、黄眼、蓝计时器、层叠银蓝肩胸甲 随头壳与躯干整体位移，前后朝向不反向，不增删部件 | 较#0 近拳肩后→身侧、远肘腰后→下巴、前膝稳→伸；支撑点不漂 | 0.2519 | ≥0.10 | 非循环；末帧回可接待机护架；本组按起手→发力→收势推进 |
| 2 | 收势 | 双脚回稳 | 髋回正 | 双肩回收 | 双拳回胸架 | 头颈稳定；双头镖自额前向头顶后上方折起、蓝额灯、黄眼、蓝计时器、层叠银蓝肩胸甲 随头壳与躯干整体位移，前后朝向不反向，不增删部件 | 较#1 近拳身侧→胸架、远肘下巴→肋侧、前膝伸→浅屈；末拍回护架 | 0.2418 | ≥0.10 | 非循环；末帧回可接待机护架；本组按起手→发力→收势推进 |

## 独立动作提示词（逐帧）

### 第 0 帧动作提示词（Unicode 字符数=217）

```text
以唯一参考图的人物为同一人，只画此帧：【赛罗light2#0起二段轻击后脚髋随动近肩后收拳收胸；较较锚近拳胸→肩后、远肘肋→腰后、前膝浅→稳，头随肩】。身份、配色、像素块大小交给参考图，不重复造型。四肢粗细与参考图完全一致：手臂粗壮、大腿饱满、小腿有厚度，不要画细长的手脚。固定 90° 右侧视、完整不裁切、真透明背景、只画人物本体、无光束/光晕/颗粒/蓄气圈/贴掌光/能量球/光刃/飞行物/地面/文字/边框/任何特效、不写技能光色。
```

### 第 1 帧动作提示词（Unicode 字符数=222）

```text
以唯一参考图的人物为同一人，只画此帧：【赛罗light2#1发二段轻击前脚髋随动近肩横向拳由肩后横打；较#0近拳肩后→身侧、远肘腰后→下巴、前膝稳→伸，头随肩】。身份、配色、像素块大小交给参考图，不重复造型。四肢粗细与参考图完全一致：手臂粗壮、大腿饱满、小腿有厚度，不要画细长的手脚。固定 90° 右侧视、完整不裁切、真透明背景、只画人物本体、无光束/光晕/颗粒/蓄气圈/贴掌光/能量球/光刃/飞行物/地面/文字/边框/任何特效、不写技能光色。
```

### 第 2 帧动作提示词（Unicode 字符数=221）

```text
以唯一参考图的人物为同一人，只画此帧：【赛罗light2#2收二段轻击双脚髋随动双肩回收拳回胸架；较#1近拳身侧→胸架、远肘下巴→肋侧、前膝伸→浅屈，头随肩】。身份、配色、像素块大小交给参考图，不重复造型。四肢粗细与参考图完全一致：手臂粗壮、大腿饱满、小腿有厚度，不要画细长的手脚。固定 90° 右侧视、完整不裁切、真透明背景、只画人物本体、无光束/光晕/颗粒/蓄气圈/贴掌光/能量球/光刃/飞行物/地面/文字/边框/任何特效、不写技能光色。
```

本轮仅规格，未生成、未落格、未安装；请求/usage/新 raw SHA 无

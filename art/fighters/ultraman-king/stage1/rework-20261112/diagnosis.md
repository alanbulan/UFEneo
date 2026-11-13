# 奥特之王 逐 clip 只读诊断（2026-11-12）

本文件是阶段 A/B 只读诊断，不是制作完成记录。全部数值由 `.venv/bin/python tools/rebuild/seven-character-rework-20261112/diagnostic_probe.py` 对现装机 `assets/fighters/ultraman-king/animations/manifest.json`、atlas PNG、`content/fighters/ultraman-king/`、`phase3_projectiles.json` 与 `charge_overlay_policy.json` 重算；逐 clip 证据在 `clip_diagnosis.json`，资产 SHA 在 `asset_baseline.json`，身份卡在 `identity_card.json`，逐帧分镜在 `storyboard.md`。

## 一、口径与自算结果

- 主体 `alpha>=128`；4 邻域连通块为主、8 邻域辅助；帧高是主体最小包围盒高，披风/举拳/伸展件计入，姿态例外单列。
- 相邻剪影差分是同 clip 同坐标的 `XOR/Union = 1-IoU`，目标 ≥0.10；站姿类对装机待机第 0 帧高度偏差 >8%、相邻站姿高度突变 >10% 判不合格。
- 辉光门按 `alpha>=200` 最大连通块外扩 3 px：主体外 `alpha>=16 <=100 px`、`alpha>=200=0`；`alpha 1–15` 只登记。亮色像素只是局部启发式，接触表造型审片另算。
- 状态帧 `frames[].sprite` 越界在 `presentation/side_view.gd:450` 会被 `clampi` 到最后一帧；但 `state=="walk"` 不走该 sprite 覆盖分支，`walk_forward/walk_back` 的 OOB 只登记数据/受击框口径失配，不冒称画面冻结。移动连续同 sprite 是显示持时候选，不等于数据冻结。
- 本轮重算：104 个 clip；四桶 `{"keep": 68, "fix": 32, "redraw": 4}`；细分类 `{"keep": 68, "fix_pose": 15, "fix_scale": 17, "redraw": 4}`。
- 主体高度：站姿类对锚偏差 >8% 的帧 45 个、相邻突变 >10% 的相邻对 24 个；相邻差分 <0.10 共 14 对，前 12 对为 `[["charge", 0, 1, 0.0869], ["charge", 1, 2, 0.0648], ["charge", 2, 3, 0.0932], ["charge", 3, 0, 0.0764], ["charge_stop", 0, 1, 0.0823], ["motion_22", 6, 7, 0.0852], ["ranged_forward", 3, 4, 0.0861], ["special", 8, 9, 0.0875], ["special", 9, 10, 0.0863], ["special", 11, 12, 0.0747], ["special2", 10, 11, 0.0857], ["taunt", 0, 1, 0.089]]`。
- 独立连通块：`[["ranged_forward", 4, [11962, 2], [11964]]]`；硬辉光/主体外高 Alpha：`[]`。浅亮银/蓝灯色像素超过 30 px 的软证据共 495 帧，前 12 帧 `[["air_apex", 0, 535], ["air_crush", 0, 317], ["air_crush", 1, 375], ["air_crush", 2, 576], ["air_crush", 3, 555], ["air_crush", 4, 401], ["air_crush", 5, 362], ["air_fall", 0, 651], ["air_pulse", 0, 569], ["air_pulse", 1, 655], ["air_pulse", 2, 552], ["air_pulse", 3, 507]]`，只用于排审片顺序，不自动判烘焙特效；4 邻域单连通也不能排除与手相连的特效，必须逐帧看原生格与 4×。
- 待机 1 帧、前走 4 帧、后走 4 帧、转身 3 帧；奥王/佐菲/奥父/奥母按 `REBUILD_2D_PLAN.md` 2.5.8 的待机 6、前/后走 8、转身 3 核。
- 状态 OOB：[]。
- move 时间轴：47 份 `moves/*.json`、sprite 越界 0 份；长显示持时候选 `[["special3", 12, 8]]`。special/special2/special3 均自算为 72/80/96 行、sprite 0–15 逐相覆盖，并非全 0 冻结；10 tick 图集持时与 72/80/96 tick 时间轴须在重画后同时核。
- 已知缺陷复算：`{"motion_22_06_to_07": {"from": 6, "to": 7, "xor_over_union": 0.0852, "one_minus_iou": 0.0852, "pass_ge_0_10": false}, "diagonal_heavy_heights": [138, 116, 114, 105, 165]}`。
- 跨角色模板化自算：`down/win/ko` 与本代理负责的另外三个角色按主体 bbox 裁切、最近邻归一 128×128 后取 IoU；本角色最高值 `{"down": 0.6596, "win": 0.7023, "ko": 0.7035}`，逐对数值在 `clip_diagnosis.json.template_similarity`。归一化轮廓只是同源嫌疑，不是身份验收；`down/ko/win` 还须按本人披风、双角/双马尾、头冠、胸灯实看重画。

## 二、身份、比例、特效与接线

- 现用待机像素整帧 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-king/stage1/cells/idle-candidate-v18-cell.png`，SHA `a22f8dba432ab0a7b8f2e6d3fa5ba9a9668c60c778d13ca681421462a455c9cd`；装机 idle atlas 与 manifest SHA 相符。
- 唯一 scale `0.14387`、待机格 `256`、根点 `[128, 248]`、装机站高 `203`；逐 clip 必须取自身 `cell/anchor/rects/ticks/anchors`。本角色顶层与 clip 级一致。
- 冻结色板取装机 idle 第 0 帧实测 32 色，保留 `["红眼/额灯", "胸口两颗红宝玉", "金肩甲/金腰带", "红披风", "白须", "银冠"]`；`cells.json` 未存 palette 字段的奥王/佐菲须以 `identity_card.json.installed_idle_frozen_palette_rgb` 为制作基线。
- 标志结构：朝右时冠球在前额上方、刃根从球后方向后上方掠；冠球/刃根 x 与眼列 x 比大小；已知冲突 `["cells.json 旧 idle bbox/SHA 与 PROGRESS 文字存在冲突；本轮以装机 idle 整帧实测 32 色和当前文件 SHA 为准"]`。
- 姿势例外：`["真实屈膝/下沉压缩", "腾空收腿与空中必杀", "倒地/被投/躺姿", "红披风惯性展开或高过头顶", "举起双拳超过头部列带"]`；每例须登记主体高度、稳定头壳/骨长证据，不能用一句「例外」放行整人缩放。
- 本角色引用 28 个 effect id，未登记 0 个；已声明 atlas SHA 的条目全部相符。Q 三态 placement 在 `charge_overlay_policy.json` 齐备。任务书明确登记不是当前缺陷，禁止重复补登记；重画换贴图才需核 SHA。
- 发射点：本次按 `derive_fighter_data.hand_point` 对当帧 `alpha>=128` 复算 11 处，另测右向/镜像向到人物主体最近距离；双向贴体 >2 px 或距离缺失 11 处，逐项在 `clip_diagnosis.json.emission_points`。这是贴体粗测，不代替按本人掌/角/胸灯实际发射部位的人工标点与实机双向核；四角色无 `content/fighters/<id>/emission_points.json` 人工依据表。
- 发射点与 `hand_point` 差异大的旧值多来自人工改点、特殊角部/胸前/天顶发射或早期生成规格；不得把本轮复算值直接覆盖运行时。重画帧后以新图集、新 `hand_y`、两朝向 720/1080 实机重取。

## 三、三槽原剧依据与差异

- `special`（redraw，16 帧，24/32/16 tick，发射 1 处）：王者闪光 King Flasher：圆谷官方角色页列专名；《雷欧》第26话与雷欧光线同发、UGF对波。原剧光色译作黄/红有冲突，本作取红；帧序与数值是游戏编排。双掌收胸下沉、左右水平伸展、掌缘横推、逐段收臂。
- `special2`（fix_scale，16 帧，32/32/16 tick，发射 1 处）：洗礼光线 Baptism Beam：圆谷官方角色页列专名；《雷欧》第39话识破假阿斯特拉。原剧为识破/净化，本作红色能量箭、多段与高削气是游戏改编。胸前红宝玉聚能、斜上张臂、收臂。
- `special3`（fix_pose，16 帧，32/48/16 tick，发射 1 处）：王者再生光线：中文资料/粉丝维基记《雷欧》第50话复活雷欧；原剧是复活，本作改攻击终结是游戏改编。脸前交叉双掌后推出、收势；不得把S1同束改色充三级。
- 三槽共同要求：技能人物帧只画身体，不画光束/光晕/颗粒/蓄气圈/贴掌光/能量球/飞行物；投射类 `pulse/low_pulse/air_pulse/ranged_forward` 手中也不得有能量球。`special*` 的束体、命中、Q 三态只走运行时 shots/impact/特效层。

## 四、重点 clip 诊断

| clip | 分类 | 帧数/格/根点 | 逐帧主体高度 | 越 8% 帧 | 相邻 >10% | 差分 <0.10 | 独立块/烘焙特效证据 | 动作与接线结论 |
|---|---|---|---|---|---|---|---|---|
| `idle` | redraw | 1 / 256 / [128, 248] | [203] | [] | [] | [] | 4n独立 0，硬辉光 0 | 任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足；待机仅1帧，不满足双脚固定仅呼吸的循环 |
| `walk_forward` | redraw | 4 / 256 / [128, 248] | [198, 185, 199, 198] | [1] | [] | [] | 4n独立 0，硬辉光 0 | 站姿类高度偏差>8%或相邻突变>10%；任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足；前走仅4帧，需按 8 相骨长/引导核连续换腿，8 相不是装机帧数硬门 |
| `walk_back` | fix_pose | 4 / 256 / [128, 248] | [200, 187, 203, 202] | [] | [] | [] | 4n独立 0，硬辉光 0 | 任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足；后走仅4帧，需按 8 相骨长/引导核连续换腿，8 相不是装机帧数硬门，前/后走骨长与支撑点须同口径 |
| `light1` | keep | 3 / 256 / [128, 248] | [202, 188, 203] | [] | [] | [] | 4n独立 0，硬辉光 0 |  |
| `light2` | keep | 3 / 256 / [128, 248] | [201, 201, 203] | [] | [] | [] | 4n独立 0，硬辉光 0 |  |
| `light3` | fix_scale | 4 / 256 / [128, 248] | [198, 178, 203, 203] | [1] | [[0, 1, 10.1], [1, 2, 14.04]] | [] | 4n独立 0，硬辉光 0 | 站姿类高度偏差>8%或相邻突变>10% |
| `heavy` | fix_scale | 4 / 256 / [128, 248] | [157, 183, 178, 203] | [0, 1, 2] | [[0, 1, 16.56], [2, 3, 14.04]] | [] | 4n独立 0，硬辉光 0 | 站姿类高度偏差>8%或相邻突变>10% |
| `special` | redraw | 16 / 256 / [128, 248] | [194, 180, 174, 185, 203, 203, 203, 203, 203, 203, 203, 203, 203, 204, 201, 203] | [1, 2, 3] | [] | [[8, 9, 0.0875], [9, 10, 0.0863], [11, 12, 0.0747]] | 4n独立 0，硬辉光 0 | 站姿类高度偏差>8%或相邻突变>10%；相邻剪影差分<0.10；投射类帧仅换手型或复制，须只画人物动作 |
| `special2` | fix_scale | 16 / 256 / [128, 248] | [201, 178, 194, 188, 204, 203, 203, 203, 203, 203, 203, 204, 203, 203, 203, 201] | [1] | [[0, 1, 11.44]] | [[10, 11, 0.0857]] | 4n独立 0，硬辉光 0 | 站姿类高度偏差>8%或相邻突变>10%；相邻剪影差分<0.10；任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足 |
| `special3` | fix_pose | 16 / 256 / [128, 248] | [196, 200, 203, 204, 194, 200, 203, 204, 203, 202, 204, 204, 203, 202, 195, 200] | [] | [] | [] | 4n独立 0，硬辉光 0 | 任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足 |
| `air_special` | fix_pose | 8 / 256 / [128, 248] | [164, 182, 198, 182, 152, 178, 189, 189] | [] | [] | [] | 4n独立 0，硬辉光 0 | 任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足 |
| `dash_throw` | fix_pose | 6 / 256 / [128, 248] | [184, 160, 203, 203, 198, 203] | [] | [] | [] | 4n独立 0，硬辉光 0 | 任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足 |
| `launcher` | fix_scale | 7 / 256 / [128, 248] | [177, 178, 203, 203, 200, 203, 203] | [0, 1] | [[1, 2, 14.04]] | [] | 4n独立 0，硬辉光 0 | 站姿类高度偏差>8%或相邻突变>10%；任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足 |
| `hit_mid` | fix_scale | 3 / 256 / [128, 248] | [160, 183, 201] | [0, 1] | [[0, 1, 14.37]] | [] | 4n独立 0，硬辉光 0 | 站姿类高度偏差>8%或相邻突变>10%；任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足 |
| `down` | fix_pose | 2 / 256 / [128, 248] | [111, 58] | [] | [] | [] | 4n独立 0，硬辉光 0 | 任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足 |
| `ko` | fix_pose | 2 / 256 / [128, 248] | [175, 55] | [] | [] | [] | 4n独立 0，硬辉光 0 | 任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足 |
| `win` | fix_pose | 2 / 256 / [128, 248] | [202, 203] | [] | [] | [] | 4n独立 0，硬辉光 0 | 任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足 |
| `guard` | fix_scale | 2 / 256 / [128, 248] | [186, 178] | [0, 1] | [] | [] | 4n独立 0，硬辉光 0 | 站姿类高度偏差>8%或相邻突变>10%；任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足 |
| `turn` | fix_pose | 3 / 256 / [128, 248] | [203, 203, 204] | [] | [] | [] | 4n独立 0，硬辉光 0 | 任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足 |
| `charge_start` | fix_pose | 3 / 256 / [128, 248] | [192, 203, 202] | [] | [] | [] | 4n独立 0，硬辉光 0 | 任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足 |
| `charge` | fix_pose | 4 / 256 / [128, 248] | [199, 203, 203, 202] | [] | [] | [[0, 1, 0.0869], [1, 2, 0.0648], [2, 3, 0.0932], [3, 0, 0.0764]] | 4n独立 0，硬辉光 0 | 相邻剪影差分<0.10；任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足 |
| `charge_stop` | fix_pose | 2 / 256 / [128, 248] | [203, 203] | [] | [] | [[0, 1, 0.0823]] | 4n独立 0，硬辉光 0 | 相邻剪影差分<0.10；任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足 |

`clip_diagnosis.json.clips` 覆盖全部 104 个 clip；上表列任务书点名的 22 个基础/技能/状态 clip，其余逐帧高度、差分、连通块、cell/anchor/ticks、state/move 引用和分类同文件可查。

## 五、返工顺序

1. 冻结阶段 A：先按 `identity_card.json` 定唯一待机像素整帧、真实侧视前后判据、唯一 scale、色板、四肢粗细和姿势例外；奥父先消「白须/捋须」与有披风两套规格冲突，奥母/佐菲登记缺 90° 官方侧视全身照。
2. 数据接线优先：奥父 idle/turn/walk_forward/walk_back 的 state sprite 越界与 1/4/1 帧缺口；walk 两向单独注明 side_view 不覆写显示索引，但仍要修状态帧/受击框口径。不留 clamp 假通过。
3. 基础动作重画：idle 真呼吸循环、前/后走按 8 相骨长引导核接地点（不要求装机 8 帧）、turn 3 相；按 `storyboard.md` 的支撑脚、髋、肩、双拳、头、披风/角/垂饰逐帧生成，不许复制姿势。
4. 按 `clip_diagnosis.json.rework_priority` 修 fix_scale / fix_pose / fix_identity，先解决 >8%% 与 >10%% 体型跳档、down/ko/win 模板化，再修相邻差分 <0.10 的 skill/charge/pulse 帧。
5. 三槽与空中必杀：按 `SLOT` 本人原剧依据和 `storyboard.md` 的起手/发力/收势逐帧重画；技能帧只有人物本体，投射类只画手/身；奥父 S2 是唯一角部发射，奥母 S3 光雨不得进人物帧。
6. 逐 clip 安装与接线：`stage_cells.py` 唯一 scale 落格，`install_cells.py --only <clip> --merge`，重画后重核 atlas SHA、state/move sprite、发射点、effect id 已声明 SHA、Q 三态；不覆盖 `asset_baseline.json.readonly_do_not_overwrite` 之外的运行数据。
7. 实机双向审片：主游戏训练/F1，两朝向 720/1080，逐 clip 看循环、接地、起手/发射/收势、Q 三态、双方含披风完整 Alpha 取景；逻辑与美术验收分开报。

优先 clip 顺序：`idle` → `turn` → `walk_forward` → `walk_back` → `special` → `special2` → `special3` → `air_special` → `dash_throw` → `down` → `ko` → `win` → `guard` → `launcher` → `hit_mid` → `light1` → `light2` → `light3` → `heavy` → `charge_start` → `charge` → `charge_stop` → `motion_22` → `diagonal_heavy` → `pulse` → `low_pulse` → `air_pulse` → `ranged_forward`。
- 三槽原剧依据、差异与内容缺口已写入 `clip_diagnosis.json.three_slot_evidence.slots`，逐 move 的 `data_source`、startup/active/recovery 与 shots 在 `clips[move].move_effect_registration`。

## 六、每阶段验收命令与门值

```bash
# 阶段 D：单帧唯一 scale 落格；每 clip 取自身 cell/anchor/rects/ticks/anchors
.venv/bin/python tools/art/stage_cells.py --fighter ultraman-king --scale-source <现用待机像素整帧> --target-standing 203 --scale 0.14387 --cell <该clip自身格> --frame <clip>-00.png[@脚底行] --out-dir <本批在制目录>
# 阶段 E：逐 clip 安装，禁止全量覆盖
.venv/bin/python tools/art/install_cells.py --fighter ultraman-king --only <clip> --merge
# 阶段 E：发射点人工依据表补齐后跑数据门（本轮诊断不写 content）
.venv/bin/python tools/rebuild/shared/emission_check.py --characters ultraman-king
.venv/bin/python tools/rebuild/shared/q_charge_registry.py --dry-run
# 阶段 F：Godot 导入/验证/录制一律串行
.venv/bin/python tools/godot_lock.py -- .venv/bin/python tools/verify.py --keep-going
```

- 每帧硬门：真透明二值 Alpha、≤32 色且整图统一映射、4 邻域人物主体单连通（8 邻域辅助）、四边不裁、站姿类对锚高度 ≤8%%、相邻站姿 ≤10%%、相邻剪影差分 ≥0.10、循环首尾接续、无烘焙特效/独立颗粒/飞行物。
- 辉光门：主体为 `alpha>=200` 最大连通块，外扩 3 px 后主体外 `alpha>=16 <=100 px`、`alpha>=200=0`；`alpha1–15` 尘点登记不计入。
- 时间轴门：`state_frames/moves.frames[].sprite` 全部落在相应 clip 的 `rects` 内；72/80/96/24 tick 的发射 tick、active 与收势落在真实身体运动上；walk 两向按 side_view 的 ticks 路径另核，不能以 OOB 或相同持时直接判冻结。
- 发射点门：按本人当帧实际掌/角/胸灯人工标点，双向原生误差 ≤2 px、不悬空不穿体；`emission_check.py` 只核数据表与运行坐标，不代替图形/手势。
- 特效登记：每个 effect id 在 `phase3_projectiles.json` 有条目，已声明 atlas SHA 字节相符；Q 三态按 `q_charge_registry.py` 口径。本轮已核，不作为新缺陷或返工成果。
- 实机门：`开始游戏.command` / `app/scenes/main.tscn`，训练/F1，两个朝向、720/1080、真实输入与独立回放；`verify.py --keep-going` 只证明逻辑/资源，不证明美术或听感。

## 七、风险

- 自动高度把披风、举拳或空中伸展计入主体包围盒；`fix_scale` 中真实屈膝/倒地/腾空须用稳定头壳和骨长证据登记，不能整人归一。
- 亮色启发式无法区分白须/银甲与烘焙光；硬连通块与辉光门仍需原生格、4× 联系表逐帧目视，不能以「检查数」冒称造型通过。
- 奥王 PROGRESS/cells.json 旧 bbox/SHA 与现装机文件有历史冲突，佐菲/奥父顶层 anchor 是旧值，逐 clip 安装时不得回落顶层。
- 奥父无胡子、奥王冠球在前、奥母缺真实侧视全身官方照；资料缺口未补前生成提示词可能复刻错误结构。
- 四角色无人工 `emission_points.json`；重画后若不按本人部位重取，束根会悬空或穿体。
- 三槽有原剧专名不等于已核逐帧影片；未核集数/时码/台词/光色的项保持内容缺口，不补写。

## 八、本轮没做的事

- 未生成任何图片；未改 `assets/`、未改 `content/`、未 git commit；未启动 Godot、未用 `tools/godot_lock.py` 录制，未做双朝向 720/1080 实机审片。
- 无录屏；未听审；用户未亲审；`root_delegated_by_user` 历史签署不等于 `user_approved`。
- 未复现同目录其它角色的诊断，未读写另外三个角色的制作文件；只读了公共规范、七角色审计表与联系表。
- 未把 57 项逻辑 PASS、722 条 phase3、effect id 齐备或文件数量写成美术通过。

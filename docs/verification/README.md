# 验证回执

用途：核对随干净仓库交付的历史验证结论时读本文件。这里只放摘要，原始日志在本机 `reports/verification`。

本目录保留可以随干净仓库交接的结果摘要；原始测试输出在本机忽略的 `reports/verification`，重新运行会生成自己的输出，不上传整套日志和截图副本。

## 2026-11-13 赛罗/盖亚 idle 返工、720/1080 实机与截窗参数

- 两角色上一批 11 张独立生成待机 raw 因近/远脚中心横向跨 12.5–36.1 px、冠顶行跨 34–45 px 拒收；11 帧 SHA 记录在 `reports/review/2026-11-13/seven-character-rework/rejected-idle-raws-20261112.json` 后删除，不备份。
- 新基线按 harden_alpha(≥128) 后实心高：赛罗 925 px→站高 172、比例 0.185946；盖亚 1015 px→站高 175、比例 0.172414。六帧整身 dy=[0,1,2,3,2,1]、第 232–255 行脚踝/鞋固定回贴；双脚固定、头纵幅 ≤4 px、相邻头位 ≤2 px、横漂 ≤2 px、站高偏差 ≤8%、≤32 色、二值 Alpha、单连通全部通过。相邻剪影 XOR/Union 0.0457–0.0499 未达 0.10，按规格登记为 gap，未改脚位或整人缩放凑门。
- 装机后 `assets/fighters/<id>/animations/idle/atlas.png` 1536×256，manifest idle 6 rects/ticks 10/loop true/anchor [128,248]，图集与 `stage1/cells/idle-0N-cell.png` 逐像素一致；非 idle clip 未变。锁内全量 `tools/verify.py` 59 项 PASS。
- 根因：主游戏 `app/game_app.gd::_size_window()` 启动时把窗口自动撑到屏幕能容纳的最大 640×360 整数倍，`--resolution` 被覆盖，720/1080 截图实际落到同一窗口纹理（本机 3840×2160）。新增审片参数 `--capture-size=WxH`，显式窗口尺寸优先；默认行为不变。
- 实机：镜像对战 1280×720 与 1920×1080 各四张（赛罗/盖亚），左右两个朝向同屏、人物完整接地、无 HUD 遮挡；训练模式六帧间隔 10 tick 双人待机联系表已实看。证据在 `reports/review/2026-11-13/seven-character-rework/ingame/evidence.json`（本机忽略目录）。
- 未做：录屏、人耳听审、用户亲审、逐动作实机；不把本回执写成听感或用户亲审通过。

## 2026-11-12 七角色整帧落格、招式重映射与全量验证

- 本轮把七角色（赛罗、杰斯提斯、盖亚、奥王、佐菲、奥父、奥母）已生成的纯人物整帧落格、装机并重映射招式数据。落格共用身份锚与全套固定比例：赛罗 0.158767/172、杰斯提斯 0.161972/161、盖亚 0.169182/175、奥王方形批次 0.185897/203、佐菲 0.102001312/158、奥父 0.163561/158、奥母 0.098674/140；根点与脚底行按各角色已装口径，逐 clip 记录在各自 `stage1/cells/cells.json`。
- 空中必杀等斜下前伸臂超宽的 clip 改用 288×288 格（赛罗/杰斯提斯/盖亚 air_special、奥父 light2），根点随格中心；其余保持 256/192。运行时按 clip 的 `cell`/`anchor`/`rects` 取图，未改渲染口径。
- 招式按已装机基线重映射：special 72（24/32/16）、special2 80（32/32/16）、special3 96（32/48/16）、air_special 24（10/1/13）；奥父基础招 light1/2/3 20（5/3/12）、heavy 28（9/4/15）、dash_heavy 12（4/3/5）、dash_throw 24（2/4/18）。重映射后命中 tick 只保留在声明的 active 窗口内，伤害/判定值与原数据一致；hurtboxes 全部按新图集重算。
- `tools/art/install_cells.py` 修复两类隐患：①单 clip 重装时沿用该 clip 的根点，不再回落到 `cells.json` 旧顶层值（曾把 256 格人物整体上移 64 px）；②同一批可含多种格宽，格尺寸按 clip 取，不再用第一组尺寸缩放其余组；根点优先按 `cells.json` 落格记录（直立帧脚底行 +1、x 取格中心）。`tools/art/remap_move_sprites.py` 与 `recalc_move_hurtboxes.py` 为展开后首 tick 补齐空 `events/cancel/hitboxes` 键，避免校验拒收整招。
- 门值复核（已落格图集重测）：本轮改动的 clip 均 26–32 色、二值 Alpha、主体单连通、四边留白、无裁切；相邻剪影差分 0.10 以上（例外：奥王 motion_22 06→07 为旧帧 0.085，已登记待返工）。腾空/深蹲帧高度变化按 AGENTS 姿态例外登记，未逐帧改比例。
- 锁内全量 `tools/verify.py` **57 项全部 PASS**，含 `roster_data_integrity`、`catalogue_animation`、`catalogue_assets`、`main-startup`、`audio_playback`。
- 未做：双朝向 720/1080 实机逐动作画面检查、人耳听审、硬件键盘逐键测试；无录屏。赛罗/杰斯提斯/奥父仍用 pending/共享特效 id（未接本角色特效家族），奥父 dash_throw 仍为旧人物帧。

### 2026-11-12 补：蓄气未登记、赛罗特效家族与发射点（同日续）

- 根因：`charge_overlay_policy.json` 已把盖亚/奥王/佐菲/奥母的 Q 蓄气替换为各自 `q-outline` 批次的 effect id，但 `phase3_projectiles.json` 没有对应条目；`presentation/side_view.gd` 查不到 clip 就静默跳过，Q 起势/保持/收势整段不可见，逻辑检查也不会报错。新增 `tools/rebuild/shared/q_charge_registry.py`：只从 policy 取 id、在角色目录找已核 atlas、按批次 provenance 的 W/H/AX/AY/count 生成逐帧 rects，SHA 不符拒绝登记；补登记 12 条（4 角色 × 3 态），未改像素。
- 赛罗三招原引用 `pending_*` effect id，同样因未登记而无束体/飞刃。新建 `tools/rebuild/ultraman-zero/fx-family-pixelfx-20261112-v1/`，PixelFX 离线烘焙 11 段自绘原创像素（wide beam/hit、emerium beam/hit、slugger flight/trail/hit/catch、Q 三态），硬 Alpha、≤8 色、逐段 provenance 与 atlas SHA；phase3 登记 11 条并接线 special/special2/special3/air_special 与 charge policy。人物帧未改、帧内无烘焙特效。
- 发射点复核发现 special3 双镖 [57,151]/[57,113] 距当帧手部 11.05/6.32 px，基础光弹 pulse/low_pulse/air_pulse/ranged_forward 距手 8.49/21.84/41.87/3.61 px。全部按当帧手部像素重取后九处距离 0.00 px。
- special3 另有数据缺陷：`integer_path` 只有 `[[0,0]]`，实体镖不会飞出；`return_anchor_by_tick` 只有 `"0"`，而运行时按 `owner.move_tick` 逐 tick 取锚，回收首 tick 查不到即以 `missing_current_return_anchor` 清除，接刃闪光永不出现。改为 31 点外飞折线（30 tick、双镖上下分开 ±8 px）+ `return_anchor` [12,118]/[0,120] + tick 32–95 逐 tick 双手锚，24 tick 回收。
- 新增 AGENTS 规则：招式/反馈/蓄气引用的每个 effect id 必须在 phase3 有条目，换贴图后补登记并核 SHA。
- 锁内全量 `tools/verify.py` 57 项 PASS。未实机、未听审、无录屏；赛罗基础光弹仍用通用 `pulse` 弹体。

### 2026-11-12 补：三套专属特效家族并入与 4 连通口径

- 奥父 16 段、杰斯提斯 9 段、赛罗基础光弹 2 段（`father_fx_*` / `justice_fx_*` / `zero_fx_pulse_*`）并入 `phase3_projectiles.json` 共 27 条，并接线对应招式；奥父、杰斯提斯的 Q 三态落点并入 `charge_overlay_policy.json`，同时 `UfeChargeEffectPolicy.filter` 在“只有落点、没有受限附件”时注入落点，不再要求每个角色先挂占位附件。
- 根独立复核发现赛罗 `zero_fx_pulse_hit` 的构建脚本用 **8 邻域**取最大连通块，三帧主体外仍有 2–6 px `alpha≥200`；按项目统一的 **4 邻域**门应为 0。已把 `tools/rebuild/ultraman-zero/basic-pulse-fx-20261112/build.py` 改为 4 邻域并重烘，atlas/effect/provenance/entries/build-report 的 SHA 同步更新。27 段逐段复核尺寸、SHA、二值 Alpha、4 连通主体与主体外 `alpha≥16 ≤100 / ≥200 = 0` 全部通过。
- `tests/effect_registration.gd` 增加逐帧 `attachments` 扫描，并覆盖赛罗/奥父/杰斯提斯三态蓄气注入与离开 Q 不遗留；`effect_registration`、`phase3_specials`、`phase3_air`、`phase3_supers`、`roster_data_integrity` 与全量 `tools/verify.py`（含 `main-startup`）全部 PASS。
- 奥父 Q 三态首版是红色竖条笼/门框、24 帧变化约 1.5%，已打回重做：改为椭圆火焰环（橙白亮芯、分层火身、外缘火舌、上升火星），相邻帧变化 start 32%–51%、charge 20%–29%、stop 42%–52%，94 帧主体外门限仍全为 0，8 色硬 Alpha，id/尺寸/锚点不变；重登记后 `effect_registration` 与 phase3 相关测试 PASS。未实机、未听审、无录屏。

### 2026-11-12 补：状态帧挂件漏登记与两道形态门

- 扫全部已实装角色的 `state_frames.json` 挂件时发现艾雷王 `air_special` 12 帧仍引用 `eleking_air_lightning`，共享表只有 `eleking_air_lightning_v2`（招式文件早已用 v2），空中放电挂件整段静默不显示。已把 12 处引用改为 v2。
- `tests/effect_registration.gd` 增加状态帧挂件登记检查。首版用 `DirAccess.get_files_at` 拿角色目录，返回为空，门实际什么都没扫；第二版逐份解析 state_frames 又超时 240 s。最终改为 `get_directories_at` + 只从原文提取 `"effect"` 字段，实测还原旧 id 会 FAIL、修正后 PASS。
- 新增复用硬门：不同角色/形态的专属特效不得共用同一图集 SHA（当前全仓 0 例外）。`tests/form_selection_consistency.gd` 增加：任何 `playable=true` 的形态定义不得把 `presentation.model` 指向 `/catalogue/`，招式里不得出现 `"pending_"` 特效 id。
- 预审发现光辉形态 8 段特效是基础赛罗图集逐字节副本、超限形态 Q 三态 252 级 Alpha 未做硬量化，均已退回重做；强壮日冕特效仍为空提案。未实机、未听审、无录屏。

### 2026-11-12 补：形态切换帧冻结与切换帧推进门

- 按 E 切换赛罗形态时人物整段不动。根因在 `content/catalogs/battle_form_rules/zero_form_switch.json`：60 帧的 `sprite` 全填 0，而目标 `form_switch` 片段有 6 张内容不同的帧（相邻帧剪影差分 37%–73%）。时间轴才是实际显示帧来源，片段帧数对得上、时长 60 tick 也对，唯独没有任何一帧指向第 1–5 张。已改为每 10 tick 推进一帧（0–5），其余字段未动。
- 门禁盲区同前次：`form_selection_consistency` 原只核对「切换动画总时长 == 时间轴帧数」，不核 `sprite` 取值与推进。更糟的是它跳过选人表里的 `default` 项（`if id == "default": continue`），而默认形态正是出问题的那一项，等于整条规则对默认形态从未生效。现把 `default` 纳入登记，并新增两条硬门：切换帧 `sprite` 必须落在目标片段帧数内、必须逐帧推进到全部帧。实测把修复回退后 FAIL（`ultraman-zero/default 切换帧逐帧推进（1/6）`），恢复后 PASS。
- 全表复核：泰罗 60 tick/10 帧、EX哥莫拉与 EX雷德王 72 tick/12 帧、赛罗 60 tick/6 帧，`sprite` 均覆盖全帧无越界；五个新形态目录尚无 manifest，未纳入。
- 未实机、未听审、无录屏。

## 2026-11-11 减速规则与事件语音接入

- core 新增招式字段 `chill`（`ticks` 正整数、`speed_percent` 1–99），由 `UfeMoveData.validate` 校验；只在未防住的命中由 `UfeHitResolver.apply` 写入受方 `stats.chill_ticks/chill_percent`，`UfeMatchDirector._advance` 每 tick 递减；`UfeState.move_speed` 对 walk/dash/backstep 位移按 `(base*percent+50)/100` 整数取整，最低 1 px。出招帧、硬直、受击状态与判定时序不变。content fingerprint 已包含 moves，旧回放不会混跑新数据。
- 新增 `tests/chill_effect.gd`：命中写入、防御不触发、更强档与更长时长取优、走/冲刺位移减半、到期恢复原速、字段合法性、佐菲 `special2` 实数据校验。锁内全量 `tools/verify.py` 57 项通过（含 `roster_data_integrity`、`audio-manifest`、`fx-audio-resources`、`main-startup`）。
- 同期接入 28 条事件语音（7 角色 × down/heavy/taunt/timeout）；首轮 −1.2 dBFS 峰值被 `fx_audio` 门拒绝，重归一化到 −10.0 dBFS 后 `fx-audio-resources` 与 `audio-manifest` PASS。`listening_reviewed=false`，未听审。
- 本轮未启动主游戏实机、无 720/1080 双向画面检查、无录屏；图像生成受服务商当日限额阻断，未新增动作帧。奥母/盖亚/奥父/奥王仍缺运行时状态 clip（7/6/34/19），不能写成已达泰罗完整度。

### 2026-11-10 奥王冠饰前后方向反向（同日第五起工序事故）

- 现象：用户在奥王待机锚上圈出冠顶尖角，指出「尖角反了，旋转 180 度做轴对称」。核对官方两个独立来源后确认：**我们的照片 v17、像素 raw-02、待机锚三级的冠球都在脑后、冠刃朝前，与官方前后颠倒**。
- 同口径实测（冠球＝最高 3 行内本体像素 x 均值，ref-02 先去蓝天；眼＝头部最大红连通块 x 均值；朝右时球 x>眼 x 为正确）：ref-02 官方皮套侧头 345.8 vs 286.0＝**+59.8 球在前**；ref-03 官方软胶侧身 464.6 vs 517.0＝−52.5（朝左，前＝左）＝**球在前**；v17 照片 615.3 vs 735.8＝**−120.5 球在后**；v17 像素 −100.5；v17 锚 −16.1。两个官方来源一致，我们三级一致地反。
- 根因（两层）：①照片提示词把**错误方向写成了规格**——原文写「银色后掠冠（后端小球、刃下纵向肋）」，等于直接指定模型把球画在脑后；②唯一参考 ref-03 matte 原图朝左、未先镜像为朝右，模型自行翻身后冠向没有跟着翻。像素阶段照抄照片，错误被逐级继承。
- 门禁盲区：照片门与像素门测的是站距、鞋底、头高、头宽、辉光、连通、色数、朝向左右——**没有任何一项在测标志结构的前后方向**。六项数值全过，方向错到底。此前 AGENTS 只写「对照官方图核头冠/头镖的轮廓、安装位置与转折」，被理解成只核形状不核方向。
- 处理：按 AGENTS「用户否决身份锚后下游动作整批撤销并删除」，锚、v17 照片、v17 像素、21 张动作帧与全部原始源共 **58 个文件逐个核 SHA 后删除**（21,060,704 bytes），不留副本、不建归档。不做像素级裁切镜像（冠与头壳接合点不同轴，原地镜像会把冠球推到眼外并在颈侧留缝）。
- 返工：参考先水平镜像为朝右（`ref03-matte-manual4-mirrored-right-20261110.png`，镜像后球 x 614.4 > 眼 x 562.0，冠向随镜像正确），提示词改写为「前额上方小银球、冠刃从球后方向后上方斜掠」。新照片 v18 一次过照片门（站距 0.6955、鞋底差 0.88 原生 px、头高 0.2148、辉光 0/0、冠球在前 +85.5）。
- 已写回：`AGENTS.md`「美术与资源」新增「标志结构的前后朝向是提示词规格的一部分」条；`art/fighters/ultraman-king/stage1/requests.json` 新增 `anchor_revocation_20261110`；`stage1/cells/cells.json` 状态改为 `identity_anchor_revoked_crown_orientation_defect`；`tools/rebuild/ultraman-king/README.md` 第二十一轮。诊断 `art/fighters/ultraman-king/stage1/diagnostics/crown-orientation-defect-20261110.png`（四联：官方两张 + 我们照片 + 我们锚）。
- 教训通用：**数值门全过不等于造型对**。标志结构（冠、角、头镖、面罩、肩甲朝向）必须逐项按官方来源目视核，且核的是「球／刃／尖在哪一侧」这类方向量，不是只看轮廓像不像。
- 未安装、未启动 Godot、未提交、无录屏；新像素锚与动作帧尚未做。

## 2026-11-10 奥王头高门与冠形判据的口径事故

- 现象：奥王 stage1 连续 6 张照片候选（v8–v13）被判不过，并得出“头高正确与站距正确互斥”“跨来源比例不稳定说明来源不可靠”两个结论。
- 根因（自查）：上一轮派生的头高门 0.2034 = 0.1883 × 1.08，其中 0.1883 取自 `identity-anchor.json` 的 `head_height_ratio`，定义是“12%–50% 高度区间**最窄行**→头顶”，该字段自带 `head_height_note`“头冠/角会让数值偏小，仅供报告参考”；而全部照片候选按**冠顶→白须底**测量。窄行落在颈部/领口收窄处，同一张图两种口径差 7–14%（图鉴 42 vs 49 px，ref-04 192 vs 207 px）。基准与候选口径不同，判据不成立。最直接的证据：把图鉴原图本身当候选、按候选用法测，得到 0.2197 > 0.2034，即**原图会被自己的门判死**。项目 `docs/STAGE1_STANDARD.md` 的 ±8% 原文是**头宽/站高**，头高绝对窗口是我自加的。
- 第二个根因：冠形判据“紧凑银高冠带纵向脊”取自 ref-04 **正面**轮廓；真实 90° 侧面奥王冠为**后掠刃 + 后端小球 + 刃下纵向肋**，ref-02（真实手办实拍侧视）与 ref-03（官方软胶侧视）两个独立来源一致。v10/v12/v13 被判“后弯长刃 fail”是误判，它们画的是正确侧面。
- 同口径重算（冠顶→白须底）：图鉴 49/223=0.2197、ref-04 官方正面 208/1073=0.1938（−11.8%）、ref-03 真实侧视 213/961=0.2216（+0.9%）；头宽侧图鉴 0.1300、ref-04 0.1295（−0.4%），未受影响。修正门 = **0.2021–0.2373**（0.2197 两侧各 ±8%），倍数仍是项目 ±8%。
- 按修正口径重评：v10 头 0.2127 过但鞋底 2.52 原生px/辉光 16,383/胸腹 3/4 不过；v11 头 0.278 不过；v12 头 0.2224 过但鞋底 1.58 不过；v13 头 0.2365、站距 0.755、鞋底 0.18、侧视、真 Alpha 全过，**唯一不过项是主体外辉光 36,868 px**。v13 原图已按规则删除，不回溯签收。
- 已写回：`AGENTS.md` 新增“比例核验两侧必须同口径”条；`docs/PROGRESS.md` 奥王节改为口径自查；`art/fighters/ultraman-king/stage1/requests.json` 新增 `metric_definition_audit_20261110`。诊断 `art/fighters/ultraman-king/stage1/diagnostics/head-metric-definition-audit-20261110.png`、`crown-side-vs-front-20261110.png`。
- 未改项目 ±8% 规则、未回溯签收、未生成新照片、未做像素候选、未安装、未启动 Godot、未提交、无录屏。

### 2026-11-10 奥王辉光门口径不一致（同日第三起口径事故）

- 现象：同一项“主体外辉光”在 v12/v13/v14/v15 四次记录里得出相反结论——v12 记 pass、v13 记 36,868 px fail、v14/v15 按 `alpha>0` 记 33,191 / 35,186 fail，而 v14/v15 的同一条记录又写明“主体+3px 外 alpha≥16 为 0”。
- 根因：没有统一口径。用“主体外 alpha>0”当门时，alpha=1 的尘点也被计入。
- 同口径实测（主体＝alpha≥200 最大连通块，外扩 3 px）9 个已签源：主体外 `alpha>0` 是 9,030–87,536 px（几乎全是 alpha=1 尘点），`alpha≥16` 照片源 0–1、像素源 17–60，`alpha≥200` 全部 0。**“外 alpha>0”当门会判死全部已签源。**
- 定门：主体外 `alpha≥16` ≤100 px、`alpha≥200` = 0；alpha 1–15 尘点只登记不计入。依据是已签源最大值 60，留 1.67 倍余量。写回 `AGENTS.md`“美术与资源”。
- 对既有结论的影响：只改口径，不回溯签收。v14 鞋底差 1.10 原生 px、v15 站距 0.6249 仍不过，刹车维持；v13 的 36,868 px 未写明口径且原图已删，不翻案也不作结论。奥王卡点仍是站距与鞋底同线，不是辉光。
- 记录：`art/fighters/ultraman-king/stage1/requests.json` 的 `halo_definition_audit_20261110`；`tools/rebuild/ultraman-king/README.md` 第十八轮；诊断 `art/fighters/ultraman-king/stage1/diagnostics/halo-definition-audit-20261110.png`。
- 未重出、未做像素候选、未回溯重判其它角色历史辉光结论、未安装、未启动 Godot、未提交、无录屏。

### 2026-11-10 奥母 air_fall-00 冠顶地标错位（同日第二起口径事故）

- 现象：`mother-of-ultra` 的 `air_fall-00` 连续 3 张在“冠顶→眼”门被拒（21 / 19 / 28，门 ≤18），按返工刹车停止，三张源图删除，该帧留人工。
- 根因：测量用的是**眼行 − 整帧 Alpha 最高行**。下落姿势把红披风甩到头顶以上，最高行是披风而不是头。用同一张既有诊断图复算，旧口径得 21 / 19 / 28，与记录逐值吻合，确认就是这个量法。身份锚本身披风不高过头顶，两口径同值（17 / 17），所以 44 张已签帧从未暴露该缺陷。
- 同口径重测（眼列 ±26 px 列带内、排除纯红披风取最上本体像素）：16 / 16 / 17，三张全部在 ≤18 门内。拒收是地标错位，不是模型把头画大。
- 未解决、未签通过：诊断图是 2× 缩略，头壳宽量得 29 / 29 / 27，与原记录 30 / 28 / 33 不一致；`raw-03` 记录值 33 即使只换冠顶口径仍 >30。缩略图不能判头壳宽，须按原图重测，因此只作废刹车依据，不为该帧签通过。三张原图已删不可追回，须重出一次再判。
- 对照组 `heavy-00`：按正确面板复算冠顶→眼 19 / 19 / 19、头壳 31 / 31 / 31，与记录一致；该组是站姿起手、披风在身后低于头顶，不受此缺陷影响，**拒收是真的，刹车维持，不翻案**。
- 已写回：`AGENTS.md`“美术与资源”与 `docs/STAGE1_STANDARD.md` 第 2 步新增“动作帧冠顶只取头部列带，不得用整帧 Alpha 最高行”；`art/fighters/mother-of-ultra/stage1/requests.json` 新增 `head_landmark_audit_2026_11_10`；`tools/rebuild/mother-of-ultra/README.md` 追加复查节。诊断 `art/fighters/mother-of-ultra/stage1/diagnostic/air_fall00-landmark-audit-2026-11-10.png`。
- 后续（同日）：`air_fall-00` 已按修正口径重出一次即过并落格自签（`image-65174-1158`，源 SHA `040badf4…`）：原生格冠顶→眼 **17**（门 ≤18）、眼行头壳 **29**（门 ≤30）；同一帧按旧口径仍量出 21，反证是量法而非画法。air 组 2/2 齐；`heavy-00` 未动、刹车维持。该帧未安装、未启动 Godot、未提交、无录屏。

### 2026-11-10 站姿导引的身体轮廓与标注线互相矛盾（同日第四起工序事故）

- 现象：奥王 `v16`（`image-65174-1162`）用“站距烘焙导引”，导引上洋红竖线标 0.72 站距，实得站距 **0.5354**，且人物**朝左**；奥父 `raw-14`（站距 0.7516 过、含双角头高 0.3021 不过）与 `raw-15`（头高 0.2390 过、站距 0.1330、双拳垂在髋侧）两张的失败项恰好互换。
- 根因：导引图自身的人物是**并脚站立**（奥王导引两靴外缘 140/892≈0.157；奥父导引 96px≈0.139），洋红/青线条只画在空白处，没有进入人物轮廓。模型照抄**身体姿态**，忽略空白线条。奥父 `raw-15` 还照抄了导引人物“双手垂在髋侧”，连护架都没做。奥王 `v16` 另叠加一层：matte 源朝左、导引未镜像，朝向随参考一并继承。
- 判据：同一导引上“线条说 0.72、身体画 0.157”，两个信号冲突时模型选身体；把站距与头高分别烘焙进不同通道（线条 vs 身体）不可能同时生效。
- 已写回：`AGENTS.md`“美术与资源”新增“站姿导引必须以身体轮廓承载姿势”条；`docs/PROGRESS.md` 奥王/奥父两节；`tools/rebuild/ultraman-king/README.md` 第十九轮、`tools/rebuild/father-of-ultra/README.md` 站距烘焙导引节。
- 后续（同日）：奥王改用**不带站距导引**的 v14 单参考配置重出 `v17`，照片门全过（站距 0.7308、鞋底 0.21 原生px、头高 0.2114/0.2199），并已落 256 格待机像素锚。奥父仍停，下轮导引须把人物本体画成 0.72 站距 + 双拳胸前护架，并先镜像朝右。
- 未放宽任何门限；两张奥父 raw 已按 SHA 删除；未安装、未启动 Godot、未提交、无录屏。

## 2026-11-10 杰斯提斯 motion_214 同项连拒 7 帧未及时刹车

- 现象：第 25 批 `motion_214`（突击光箭）8 帧里 7 帧被同一项检查拒收——提示词没写本招光色，模型自配了橙色火焰，而该招是青色贴手光箭。
- 根因：技能帧提示词只写动作、未写光色与“起手/蓄力/收势无光效”，模型按通用火焰补全；制作侧又按“逐帧定向重出”继续出图，未在连续第 3 帧同项不过时先停手诊断，属流程不合规。
- 处理：改为逐帧写明“无光效”或“青色贴手”后 7 帧一次重出通过；不合规过程在 `tools/rebuild/ultraman-justice/README.md` 记在案。
- 写回：`AGENTS.md`“美术与资源”新增“技能帧提示词必须写明本招光色，以及起手/蓄力/收势帧是否不带光效”。
- 本批最终 72 帧落格自签（`root_delegated_by_user`，`user_reviewed=false`），25 个被拒候选核 SHA 后删除。未安装、未启动 Godot、未提交、无录屏。

## 2026-11-10 四角色音频运行时接入

- 佐菲、赛罗、盖亚、杰斯提斯 4 条 30s BGM 循环、4 条战吼、16 条事件按用户委托自动批准接入（`runtime_approved=true`，`runtime_approval_basis=user_delegated_auto_approve_2026-11-10`；`listening_reviewed=false`，未听审）。BGM 转 48kHz 双声道 Vorbis 并登记 `battle_music.json`；事件/战吼登记 `runtime.json` 的 `voices`；导入清单 `reports/audio-runtime-import-20261110.md`（本机忽略）。
- 锁内 Godot 4.7.2 无头导入后 24 个 `.import` 侧车齐全；首轮 `audio_playback` PASS、`phase3_fx_audio` FAIL 37 项。根因：新 20 条 `sources.records` 的 id 与 `runtime.sounds` 的键不是 1:1（记录仍用 `*-event-*` / `*-action-roar-clean-*`），12 条纯源记录按缺省 installed 计入，且被否决的原创曲 `new-gen-battle` 仍在来源账本（状态、来源、峰值 4 项失败）。
- 修正：20 条运行记录改为 `{ch}_voice_*` / `{ch}_roar_intro_*` 并显式 installed，同步 `source_record`；12 条转载/loop 纯源记录标 `pending_install`；删除 `new-gen-battle` 记录、OGG、production v2 与生成脚本，无备份。最终 1239 条记录、1191 条 installed、1191 条 `sounds`，1:1 对齐；锁内 `audio_playback`、`phase3_fx_audio` 均 PASS，`audio_manifest`、`fx_audio` PASS。
- 未实机试听、未提交、未启动主游戏、无录屏；本条只到逻辑与资源检查。

## 2026-11-09 佐菲图鉴与已批准条目恢复

- 佐菲图鉴按用户指定流程重做：图片模型先生成真实皮套剧照（右侧视错步战斗架势，`reports/zoffy/catalogue/photo-side-01.png`，真 Alpha），再以该照片为底用图片模型转像素整帧（只把头顶尖角改矮），最后经 `catalogue_native` 确定性降采样到站高 173、宽 107、32 色、二值 Alpha。安装 SHA `2607b58f...`，已同步 display（`art_source: photo_to_pixel_from_official_suit_reference`）。旧 11-08 官方参考版与 11-09 站姿版保留对照，不覆盖。
- 恢复 13 条在 2026-11-08 图鉴重建时被覆盖的既有成品：12 条 `new_art_approved_pending_in_game_review` 与 1 条 `pixel_style_user_return_installed_pending_in_game_review`（`red_king__second_generation`、`jamila`、`alien_metron`、`alien_guts`、`sevenger`、`golza`、`twin_tail`、`kaiju_omega_2`、`varallon`、`kanata_asumi`、`wiki_3e1f1565b5c03c`、`kaiju_omega_9`、`wiki_38de959744a664`）。按 `47fe7ec05` 的成品 PNG 逐条恢复并核对 SHA，display 的 state / scale_basis / 审批字段回到原值。
- 同时确认 18 个已实机安装角色（含 EX 哥莫拉、EX 雷德王、亚刻、布莱泽、欧米伽、泰奥）的图鉴仍指回实机战斗图并带待机真帧条，未被本轮改动。

| 检查 | 结果 |
| --- | --- |
| `catalogue_assets` / `catalogue_animation` / `catalogue_identity_display` | 通过（1653 条） |
| `catalogue_idle` | 通过；待机真帧 46/1653 |
| `catalogue_references` | 通过；21 条低清提示 |

未做 720/1080 双朝向实机审片，无录屏；本轮结论只到资源与逻辑检查。

### 2026-11-09 动作锚误判与整批撤销

- 盖亚新待机脚外缘/站高复测 **0.5455**（旧近似记录 0.53），两鞋底高差约 6.31 原生像素，未过站姿门。此前同项连续三张拒收并已换两种路线，本轮只出诊断并暂停；撤销 selected 与动作锚，淘汰源和重复皮套照直接删除。[诊断](../../art/fighters/ultraman-gaia/stage1/diagnostic/stance-gate.png)
- 杰斯提斯根曾按 `root_delegated_by_user` 接受头宽校回、站距与像素硬门成立的待机锚，但忽略了手脚体量、肩甲厚度和最终原生观感。用户明确否决“**不对样子太丑了**”；SHA `5d7ece2c...` 的锚及全部下游直拳、格挡、受击原图、落格、联系表整批撤销并按 SHA 删除，不计新动作完成，不用旧硬门结果推翻用户否决。[造型诊断](../../art/fighters/ultraman-justice/stage1/diagnostic/rejected-anchor.png) 与同目录 JSON 留拒收范围，未保留 PNG 备份。
- 原流程使用 BOX 区域平均降采样，不等于原生像素网格还原；本机未找到 forge 完整检测依赖，不能声称旧网格检测失败或通过。返工只做新待机，全身比例先校准，再用项目内免费 kCentroid 兼容实现，先看原生格，不提前铺动作。
- MCP 相对输出曾误落另一工作目录；仅将本请求生成的已核 SHA 文件归回仓库，未清理其它项目。后续生图全部传本仓库绝对路径，并核实收尺寸（不是照抄请求尺寸）和真实 Alpha。
- 一次受击请求返回 EOF，未给图或生成 ID，远端状态与 usage 未知；MCP 重试图也随锚否决作废。不声称零费用。未改运行定义或安装资源；无主游戏双向 720/1080、实速或录屏验收。
- 杰斯提斯宽画布待机首请求 `image-55259-14` 再次 EOF，无实收图，远端与 usage 未知；同 MCP 唯一一次重试 `image-55259-15` 已返回1024×1536 RGBA照片，单参考转像素的 `image-55259-16` 也已返回同尺寸。两图实收 Alpha 都是0–254、255档，离线整图128硬化后的二值 Alpha 不冒称原生二值。
- 新待机落格发现**旧图鉴固定色板缺青绿，吞掉额灯与胸灯**：新像素源和 kCentroid 还原仍有灯色，问题在固定色板映射，不是生图或 Alpha。整图 MEDIANCUT32 修法未保住稀少识别色；换最远色种子＋频次加权 Lloyd32、整图RGB映射后双灯保留，未按身体区域重涂。跨角色色板规则已写回 AGENTS，完整本批色板与两种修法在 [候选回执](../../art/fighters/ultraman-justice/stage1/cells/cells.json)。
- 当前候选已看原生格与4×，全身体量、护架和双灯可辨；头宽24对旧定稿22仍偏大9.09%，略超现有8%门，**不签动作身份锚**，不恢复下游动作。已用完的窄站/留白输入按绝对路径与SHA直接删除，现用源保留；未安装，无主游戏双向720/1080或录屏验收。

### 2026-11-09 杰斯提斯头身比诊断与官方 Standard Mode 来源

- 阶段A复核：官方 ref-01 头高/站高 `157/899=0.1746`（5.73头身），旧图鉴 `30/154=0.1948`（5.13头身），照片05/06/07 为 `244/1051=0.2321`、`0.2157`、`226/1049=0.2154`；像素03原生格 `33/154=0.2143`。像素03银色头壳宽/高 `23/35=0.657`，照片05为 `160/244=0.656`，落格基本忠实保留照片比例；完整ROI 25px 比银色23px 多出的约2px是深色外轮廓。**结论：头宽偏大主要来自照片阶段的整体头身比，不是像素概括单独造成**；不局部缩头、不改ROI/阈值、不落格凑门。
- 照片06（1210×1300、SHA `62e70c27…`）站距0.6892，但双鞋底差39源px（约5.49原生px），人物外另有与主体连通的不透明红色涂块，拒收；照片07（1210×1300、SHA `77cbfb18…`）站距0.7302、双鞋底差6源px、双膝屈、双拳护架，姿势过门，但银色头壳宽/站高 `180/1049=0.1716` 对图鉴0.1429约+20.1%、头高/站高0.2154对0.1948约+10.6%，不转像素。头身比项已有三张不同照片未过，按返工刹车停止生成，先出诊断。
- 根从圆谷官方角色页 `https://tsuburaya-prod.com/heroes/ultraman-justice` 取 Standard Mode 四图（均1000×1500 RGBA、Alpha 0–255软边，不是原生二值Alpha），落到 `art/fighters/ultraman-justice/sources/tsuburaya-justice-2019/` 并写 `source.json`。实测：01正面直立全身，站高1325、头高247、头高/站高0.1864、头壳宽/站高0.1298；02官方格斗架势，站高1349、头高231、头高/站高0.1712；03三分之四侧身，只核头冠/面罩侧面轮廓；04正面跨步动作，头部测量受姿态影响（0.1491），仅作补充核验。阶段B照片08（SHA `21bd85ef…`，1210×1300 RGBA、Alpha0–255）站距 `786/1222=0.6432`，低于0.65；头壳宽/站高 `176/1222=0.1440` 对图鉴0.1429为+0.8%，已到位；但头高/站高 `268/1222=0.2193`，对官方01的0.1864高17.6%、对图鉴0.1948高12.6%，头冠过高、面罩偏长。拒收，未转像素；诊断 `stage-b-photo08-2026-11-09.png`、`stage-b-head-2026-11-09.png` 与 JSON 保留。下一张只改参考组合：official-01 全身体量＋official-03 头裁图（340×370，SHA `c3682cc6…`，只定头冠高度/后掠、面罩与进气口侧面）＋唯一一张已装机侧视姿态参考；若仍不过即停，等换路线或留人工。未签锚、无动作、未安装。
- 照片09（SHA `21378b61…`，1024×1536 RGBA、Alpha0–255）站距 `870/1270=0.6850` 已过，双拳胸前、屈膝；但双鞋底差32源px（折154约3.88原生px），头壳宽/站高 `196/1270=0.1543`（图鉴+8.03%，贴上限无余量），头高/站高 `265/1270=0.2087`（官方01 +11.9%、图鉴+7.1%，折154约32.1px对门30.8px）。**根实看还发现头与上身转成近正面3/4，失去固定侧视**：official-03 头裁图虽给出头冠结构，却把整身视角拉回3/4。拒收，不出像素。这条照片线按刹车停止，等真实侧视来源或人工决定。已把“参考图角度会主导生成视角，3/4头裁图会拉回3/4；固定侧视须用真实侧视来源”写回 [AGENTS](../../AGENTS.md)。

### 2026-11-09 赛罗头镖结构与侧视来源

- 用户先指出“赛罗的头标好像不对，你最好再重新看一下官方的剧照。”根实际对照圆谷官网完整皮套与斜侧剧照，确认双头镖是额侧左右并列弯刃，刃缘有转折、凹口及贴头壳基座；00待机照已简化成长直角状轮廓，像素化照抄。该照片曾被根按站距0.7435与体量接受转像素，现撤销；00链的源、清图、像素、候选锚、落格与4倍图按SHA、绝对范围、无活动消费者和无Git跟踪逐文件删除，无备份。[头镖对照诊断](../../art/fighters/ultraman-zero/stage1/diagnostic/zero-sluggers-official-review.png)
- 返工01出图后，完整头宽32对旧35为−8.57%、站距0.6862、32色、单连通、二值Alpha、无裁切，但用户第二次明确否定：“**赛罗的头还是不对呀，你直接找一个侧视图。**”该指令否定继续由正面官方图猜侧面；01照片、清图、像素源、落格与4倍图全部拒收并删除，头宽数字接近不能替代侧面造型核实。[侧视来源诊断](../../art/fighters/ultraman-zero/stage1/diagnostic/zero-sluggers-side-source-required.png)
- 侧视来源检索结果：圆谷官网只有正面皮套与正面/三分之四剧照；SciFi Japan 官方电影媒体资料页 `zero2.jpg`、`zero2a.jpg`、`0284a.jpg` 返回 HTTP 200 `image/jpeg` 但正文0字节，无法解码；Fandom 402、JFDB 403、m-78 400 content-blocked、Ultraman Connection 证书过期、Bing 图片结果不相关。**未找到**可下载、可解码、可确认角度的赛罗基本红蓝形态真实侧视原图，不以正面、三分之四或近景动作照冒充侧视，不捏造路径/SHA。
- 0字节伪图 `art/fighters/ultraman-zero/sources/revenge-belial-press-zero2/official-publicity.jpg` 与空目录已删除；官方源、诊断与共享初代姿态参考保留。
- 后续在圆谷官方15周年新闻页 `https://tsuburaya-prod.com/news/7732` 找到官方宣传图 `zero15_cheki_img.jpg`（1920×1279，SHA `226ca50e9ddb547580a87af8b318c54b9a91286f66685e7d7db8a352c2316464`），左侧为零本人清晰右侧近侧脸；裁头部 390×510（`stage1/idle/references/zero-side-head-official.png`，SHA `a44cce4451a1849d2f59016e22ee8d19d51fb02dcc4bb122defe8c3d87f54741`，原图裁剪框 [270,50,660,560]）作结构核验。读法：双头镖是贴头壳的弯刃，额侧宽基座、刃缘转折与凹口、刀尖向后上方折起，近侧遮挡远侧；不是长直角、羽片或第三根头冠。该图只有头部与上胸，不冒充全身侧视。
- 用官方正面全身＋该侧脸头部＋已装机站姿重定待机照片 `image-55259-28`：实收1024×1536 RGBA、Alpha 0–254（255档）、SHA `6d735b7e9feb7d9f4af7ef2c8ab88b383e9594b54491779775c7017bbfe72c36`，站距917/1362=0.6732；Alpha128硬化后统一缩到742×1100、透明画布[141,310]、鞋底1410，清图SHA `7ae38bc5cb00fbab35e263989cd170938590761a03e04bb4d905d0aa24e5b602`。单参考转像素 `image-55259-29`：实收1024×1536 RGBA、Alpha 0–254（255档）、SHA `5f4651673a90f08056a250fea9a6f68ad339501a615658a183a7d07d3791dec3`。用户实际看后明确认可：“**这个就非常不错，我很满意，就它了。**”
- 正式锚 `stage1/idle/frames/identity-idle-pixel.png`：256格、站高188、宽128、32色、二值Alpha、单连通、站距0.6809，SHA `c36397a86bff3f6e1469e7efd611dad20ff4938bec30b03c703c9095c0e5df0f`；严格4× SHA `fb5f5687dace8024638d258282c734d58325d54fc07e8143375d6d3a28803ebc`。动作帧只引同一帧的1024×1536像素源，不追加角度。基础动作集正在逐阶段制作。未安装、未启动Godot、无录屏。

## 2026-11-08 图鉴重建与佐菲

- 图鉴统一 384×256、根点 [192,248]、3.84 px/m；人类固定 96（原 140）。609 条按官方剧照/皮套照图生图重画并安装，图鉴图共 1075 个文件变动（1009 改、66 新增），另新增 28 条待机动画条；宽体条目以 376 px 宽度上限取可行站高，不拉伸姿态。旧 `new_art_approved` 与 `approval_evidence` 全部重置，等待实机复核。
- 参考图补齐到 1686 张（本轮新增 633 张）并改为仓库相对路径；21 条低清官方源保留原图、标注 `resolution_exception`，不放大、不替代；删除 9 张被替换的重复副本。`catalogue_references` 从 180 条错误降为 0 错误。
- 名称拆分为 title/主体名/form，17 条重复形态写入 `aliases` 并由 `canonical_id()` 归并；`selection.json` 全部 ID 可解析。
- 佐菲按圆谷官方页（45 米 / 45,000 吨 / 队长）与官方皮套剧照重做图鉴，站高 173 安装并同步 display；此前误装的 154 px 窄侧视已替换。战斗 154 与 M87 开掌关键帧只测量，未安装。2026-11-09 用户反馈 11-08 版体型仍不合格，改以圆谷官方全身皮套照 `art/fighters/zoffy/sources/ref-02.png`（2400×3607，官方直链）为第一参考重做，11 轮候选后选中 `ref02k`：站高 173、宽 43、32 色、二值 Alpha、蓝计时器保留，SHA `3865589d...`，当时安装并同步 display（该版已被 2026-11-09 的 `2607b58f` 替换）；旧 173 保留对照。未做双朝向 720/1080 实机审片，无录屏。
- 体力经济改为发力招硬门槛后，`tests/capture_mechanism.gd` 的体力不足用例改为每 tick 固定空体并断言 `move_denied`（reason=stamina）、无启动、无扣能。

| 检查 | 结果 |
| --- | --- |
| `tools/verify.py --keep-going` 全量 | 54 项全部通过（含 capture_mechanism 及其独立进程回放） |
| `catalogue_assets` / `catalogue_animation` / `catalogue_identity_display` | 通过（佐菲安装后复跑） |
| `catalogue-references` / `catalogue-idle` / `catalogue_facing` | 通过；参考图 1686 张、21 条低清提示；待机真帧 28/1653（11-08 当时；现为 46/1653） |

未做 720/1080 双朝向实机审片，无录屏；图鉴画面只做逐张静审与 contact sheet，不等于美术验收。

## 2026-11-08 动画帧尺度突变修复

- 新增 `tools/check/frame_scale_jumps.py`：以头骨顶到脚底站高、头宽和头部面积对同 clip 中位数比较（±8%；头宽与头面积同时偏大且站高也偏大才判确定突变），举起的武器和细特效在测量前用 3×3 开运算剔除；蹲姿、腾空收腿只影响站高，不按头部指标误判。
- 修复 8 名角色 11 个 clip 共 28 帧整帧放大：杰克 `burst`1、`crouch_light2`2、`motion_214`3（长矛投掷）、`special`6、`special2`7、`special3`3；哥莫拉 `heavy`2、`guard_counter`1；亚刻 `air_tech`1；布莱泽 `guardbreak`1；布莱克王 `vertical_light`1。以该帧脚底 anchor 为不动点做最近邻反向采样，Alpha 保持 0/255；逐帧像素核对只有目标帧变化、帧外 0 像素改动，manifest 只更新 `atlas_sha256`。
- 修复后复扫，被修帧全部转为 `ok`；导入与 `phase3_standing`、`phase3_air`、`pixel_pages` 通过。证据 JSON 在本机忽略的 `reports/frame-scale-jumps/`。
- 仍有 103 clip / 111 帧判确定突变、606 clip / 1124 帧待人工复核，多为击飞、翻滚、倒地、抓投、腾空和出场姿势；`gomora/guard_counter#5` 修完 #0 后转为待复核。未做双朝向 720/1080 实机检查，无录屏。

## 2026-11-08 文档合并与冗余清理

- `docs/` 由 11 份合并为 9 份：`ENGINE_CHOICE` 并入 `PROJECT_LAYOUT`；`AUDIO_API` + `MONSTER_MUSIC` 合并为 `AUDIO`；`FORMS` + `SUPER_MOVE_DIVERSITY` 合并为 `COMBAT_DESIGN`。`docs/README.md` 仍是唯一索引。
- 根目录只保留 `AGENTS.md`、`README.md`、`REBUILD_2D_PLAN.md` 三份 Markdown。
- 同步更新 `REBUILD_2D_PLAN.md`、`docs/PROGRESS.md`、`content/roster/selection.json`、`content/audio/battle_music.json` 中的文档路径；`REBUILD_2D_PLAN.md` 的输入表按现行规则改为 I 远程/方向技能，不再保留独立 H 技能键。
- 删除本机过期报告：`reports/music-research`（与旧 `docs/MONSTER_MUSIC.md` 字节相同，内容已并入 `docs/AUDIO.md`）、`reports/gdscript-warnings`（一次性警告清理回执，代码状态已生效）、`reports/windows-removal`（一次性平台迁移回执，改动已落地）、`reports/catalogue-pipeline-pilot`（旧图鉴试点，安装图 SHA 不同且现行流程改走 `reports/catalogue-ref`）、`reports/repository-cleanup` 与 `reports/cleanup-inventory.json`（2026-11-03 原始清理审计，摘要保留在本目录 `repository-cleanup.json`）；均确认无仓库内消费者。
- 删除 `tools/**/__pycache__` 25 个目录、`reports/godot-warnings` 空目录，以及 `tools/`、`reports/review` 下的空目录；删除无源文件的孤立 `generated-images/` 导入侧车。
- `tools/` 下一次性脚本经路径/模块名与生产回执核对后未删：日期批次仍被 `art/fighters/*` 回执或在制 README 引用，零导入的顶层脚本是人工入口。重复模块名（`audit.py`、`prepare.py`、`main_bundle.py` 等）违反 tools/README 的全局唯一约定，留待批次合并时处理。
- `content/fighters/**` 中指向旧 `docs/FORMS.md`、`docs/SUPER_MOVE_DIVERSITY.md` 的字符串已统一改为 `docs/COMBAT_DESIGN.md`，涉及 20 个文件；这些字段不被运行代码读取。
- `docs/verification/existing-skill-assets-audit.json` 是带 SHA 的历史快照，保留当时的旧路径，不回写。

## 2026-11-07 文档与结构清理

- 删除 91 个 `__pycache__` 目录（35.4 MB，未入库）。
- 删除 10 份 `content/fighters/*/PROGRESS.md`（66 条指向已清理报告的失效链接），未完成项收敛到 [PROGRESS](../PROGRESS.md)。
- `docs/` 由 11 份合并为 9 份：`ARCHITECTURE` 并入 `PROJECT_LAYOUT`，`MOVE_DATA` + `MELEE_HIT_GROUPS` 合并为 `DATA_FORMATS`，`WEAPON_COVERAGE` 并入 `ART_PIPELINE`；新增 [文档索引](../README.md)。
- 修正 6 处指向已删除 `docs/handover/` 的死链；删除自述"不代表上传成功"的过期检查点说明。
- 未改动 `art/source-index.json`、冻结来源收据、`content/fighters/*/MOVES.md`、`third_party/`。

验证环境：Godot `4.7.2.stable.official.ed1daf0bf`（Homebrew）、Python 3.13 venv、Pillow 13.0.0、NumPy 2.5.4、git-lfs 3.8.1，macOS arm64。

| 检查 | 结果 |
| --- | --- |
| 空缓存导入（`--editor --import --quit`） | exit 0 |
| `tools/maintenance/repository_audit.py` | passed，34610 文件 / 4.02 GB / 0 错误 |
| `tools/verify.py --keep-going` 全量 | 45 项全部通过 |

补充（同日）：`checkpoint/full-20261105-0020` 已 fast-forward 合入 `main`，261 个新增 LFS 对象逐一核对 SHA/大小并本地拉取完整，`git lfs fsck` 通过；两个远端 checkpoint 分支已删除。

补充（2026-11-07 修复）：`training_input_audit` 与 `training_lifecycle` 曾在进程退出时报 AudioStream/Playback 泄漏。根因是 headless 下帧循环极快，AudioServer 线程来不及按真实时间回收已停止的 playback。已在两处修复：`game_app.shutdown()` 先停播、断开流引用并清空两级音频缓存；两个测试退出前 `OS.delay_msec(120)` 让出真实时间。修复后各连跑 12 次与 4 次均无泄漏，`tools/verify.py` 已恢复严格判据（任何 `SCRIPT ERROR` 或 `ERROR` 都判失败）。

清理前基线（同一环境）：导入 exit 0、`logic_2d` PASS、`repository_audit` passed（33293 文件）。

首次全量回归出现 2 项失败（`fx-audio-resources`、`pixel-ui-resources`），原因是本机缺少 Pillow/numpy，与清理无关；建立 `.venv` 安装 `tools/requirements-checks.txt` 后两项单独重跑均 exit 0。

## 2026-11-03 清理回执

- [repository-cleanup.json](repository-cleanup.json)：清理范围、初始盘点、去重和最终全量源 SHA 审计。清理前记录的 4710 个运行二进制内容均可在原位置或 119 个合并目标中找到相同 SHA；没有重新编码或替换画帧/音频。
- [cleanup-regression.json](cleanup-regression.json)：空缓存导入、当前全部默认回归及定点补跑结果。
- [runtime-catalog.json](runtime-catalog.json)：清理时实际 definition 与三槽招式快照。列为可玩不代表全动作美术、声音和独立技能规范全部达标；后续改数据时须同步重导。
- [remote-lfs.json](remote-lfs.json)：首次 push 后用已认证 gh 接口逐项检查全部唯一 LFS 对象的远端下载可用性和大小。

## 关键错误记录

跨角色的返工规则写在 [AGENTS](../../AGENTS.md)“美术与资源”；单批次失败留在
`tools/rebuild/<id>/README.md`。这里只追加根因类事故。

- 2026-11-07 音频泄漏：`training_input_audit` 与 `training_lifecycle` 进程退出时
  报 AudioStream/Playback 泄漏。根因是 headless 下帧循环极快，AudioServer 线程
  来不及按真实时间回收已停止的 playback。修法：`game_app.shutdown()` 先停播、
  断开流引用并清空两级音频缓存；测试退出前 `OS.delay_msec(120)` 让出真实时间。
  修复后连跑 12 次与 4 次均无泄漏，`verify.py` 恢复“任何 SCRIPT ERROR 或 ERROR
  都判失败”的严格判据。

## 边界

没有进行全部人物双向 720/1080 逐动作审片、人耳听审或硬件键盘逐键测试，没有生成录屏。上述结果只说明资源、逻辑、回放及启动/退出验证结果，不表示游戏范围完成。接手步骤和已知余项见 [PROGRESS](../PROGRESS.md)。

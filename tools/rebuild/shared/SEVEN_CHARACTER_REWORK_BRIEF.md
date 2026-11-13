# 七角色整帧返工总提示词（2026-11-12）

用途：交给制作子代理，对 `ultraman-zero`、`ultraman-justice`、`ultraman-gaia`、`ultraman-king`、`zoffy`、`father-of-ultra`、`mother-of-ultra` 七个已装机角色的战斗表现做一次**按实测证据返工**。执行准则仍是根 `AGENTS.md`、`REBUILD_2D_PLAN.md`、`art/STYLE.md`、`docs/STAGE1_STANDARD.md`；本文是把这些规则落实到本批缺陷的可验收任务书，不另立规则。

## 0. 总指令（原文交给子代理）

你是本批七角色返工的制作代理。按 UFEneo 现有主游戏工程返工，不准另建研究场景、预览网页、独立测试项目、旧 worker 或批量安装器。用户对本批效果不满意；我已完成只读审计，缺陷不是“少几张特效”，而是**体型/姿态/身份/帧序/接线**同时失守。你的任务不是重新生成七套 500 帧来充数，而是按下面顺序找出所有导致画面不可用的帧，逐个修到一致、能连续播放、实机可见，并交完整证据。

先读根 `AGENTS.md`、`REBUILD_2D_PLAN.md`、`docs/PROGRESS.md`、`docs/STAGE1_STANDARD.md`、`art/STYLE.md`、`docs/ART_PIPELINE.md`、`docs/COMBAT_DESIGN.md`、本文件、`reports/review/2026-11-12/seven-character-defects/audit.json` 与同目录全部联系表，再读 `git log -5`。本批审计证据是只读基线，不直接覆盖；所有新产物先落在各角色 `art/fighters/<id>/stage1/` 的在制位置，通过门后才按明确 clip 安装。不得把“clip 数量 / 逻辑 PASS 数量”当美术完成；不得用逻辑门代替人眼看联系表。

### 工作边界

- 七个角色：`ultraman-zero`（赛罗）、`ultraman-justice`（杰斯提斯标准型）、`ultraman-gaia`（盖亚 V2）、`ultraman-king`（奥王）、`zoffy`（佐菲）、`father-of-ultra`（奥父）、`mother-of-ultra`（奥母）。按本人身份、具体形态、版本和原剧依据核动作；不得沿用别角色模板，也不得把角色没有的部件写进提示词。
- 只改这七角色相关 `art/`、`assets/fighters/<id>/animations/`、必要的 `content/fighters/<id>/` 与已登记特效配置；不得改 `core/` 的确定性模拟语义，不扩大判定，不靠改镜头/暂停/闪烁掩盖美术问题。
- 新人物帧只用 MCP `magpie-image`（`codex/gpt-image-2`，quality high，transparent，输出 `path` 传本仓库绝对路径）；生成前核返回路径、尺寸和真实 Alpha。后处理只用免费离线工具和 `tools/rebuild/shared/forge_backend.py`，历史颜色兼容 `palette_mode('rgb')`。不恢复旧直连 worker。
- 所有 Godot 导入、验证、录制经 `.venv/bin/python tools/godot_lock.py -- <命令>` 串行；不删活锁，不关用户进程。
- 一文件一正式位置。运行素材在 `assets`，当前制作源在 `art`，本机审片在 `reports`。确认废弃的缓存、历史副本、重复副本直接删除，不留归档；删除前核实际消费者、动态路径、SHA。二进制走 Git LFS，`.uid`/`.import` 要提交，`.godot` 不提交。
- 全程简体中文汇报，只报本轮新增，不重复已处理意见；不把检查数量冒充完成。制作代理不自签；根按 `root_delegated_by_user` 验收后继续，不冒称用户亲审或已听审；必要时短录屏，审后删除，无录屏就写无录屏。

## 1. 本轮只读审计：必须处理的真实缺陷

审片图和逐帧数值在 `reports/review/2026-11-12/seven-character-defects/`：

- `seven_idle.png`、`seven_walk_forward.png`、`seven_special.png`：七角色同尺度并排。角色之间站高 140–203 px，但这是各自锚尺度，**不是错误**；错误是同一角色不同动作之间的体型跳档。
- `grid_defects.png` + `cross_*.png` + 各角色 `*_A.png` / `*_B.png`：待机、前走、三槽必杀、投技、升击、受击/倒地/KO/胜利等实际装机图。
- `audit.json`：每 clip 的格尺寸、根点、ticks、逐帧主体高度、state_frames 越界记录；同目录诊断图为本机只读基线，当前未提供重建脚本或命令，不得写成“均可复现”。
- 复核命令：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/.venv/bin/python /Users/wurulan/Developer/Projects/Game/ultraman-neo/tools/godot_lock.py -- /Users/wurulan/Developer/Projects/Game/ultraman-neo/.venv/bin/python /Users/wurulan/Developer/Projects/Game/ultraman-neo/tools/verify.py --keep-going` 只能证明逻辑/资源登记，不证明体型、姿态、画面；逐帧门沿用现有正式入口，不新建独立测试项目或预览网页；逐 clip 联系表和双朝向 720/1080 在主游戏训练/F1 实机核。

### 1.1 体型一致性硬门未落实到已装机帧

`AGENTS.md` 规定：同一角色所有帧按待机锚站高推得的同一个固定 scale 落格，禁逐帧重标定；站姿类帧对锚站高偏差 >8%、相邻站姿帧高度突变 >10% 要重掷。本次计数使用的明文站姿集合是 `idle / walk_forward / walk_back / guard / block / blockstun / light1 / light2 / light3 / heavy / special / special2 / special3 / pulse / ranged_forward / charge / charge_start / charge_stop / intro / win / victory / taunt / turn / hit_high / hit_mid / guardbreak / stun / motion_236 / motion_214 / motion_623 / motion_41236 / motion_22 / dash_throw / throw / burst / guard_counter / back_counter / dodge_counter / launcher / diagonal_light / diagonal_heavy`；偏差＝`|h−锚站高|/锚站高`，突变＝`|h_i−h_{i−1}|/h_{i−1}`。对正式 `assets/fighters/<id>/animations/manifest.json` 逐帧实测（主体＝`alpha≥128` 本体轮廓，含本人披风/头镖/武器；另测头部列带稳定地标）：

| 角色 | 锚站高 | 站姿类偏差 >8% | 相邻站姿高度突变 >10% | 典型实测 |
| --- | ---: | ---: | ---: | --- |
| 赛罗 | 172 | 34 | 28 | `heavy` 130→165→128→155、`launcher#4` 213、`intro#0` 104 |
| 杰斯提斯 | 161 | 58 | 35 | `guard` 140→155、`diagonal_heavy` 152→113、`launcher#5→#6` 181→137 |
| 盖亚 | 175 | 54 | 31 | `dash_throw` 149→132→120→128、`motion_623#3` 227 |
| 奥王 | 203 | 50 | 24 | `diagonal_heavy` 138→116→114→105→165、`heavy#0` 157 |
| 佐菲 | 158 | 29 | 24 | `guardbreak#2` 92、`intro#0` 79、`back_counter#3` 108 |
| 奥父 | 158 | 79 | 45 | `motion_22` 153→132→167→149→150→118→133→151、`dash_throw#3` 106 |
| 奥母 | 140 | 35 | 19 | `diagonal_heavy#1` 86、`dash_throw#2/#3` 91/90、`motion_214` 154 |

这里**不是**把所有帧外框拉直同一高度：蹲、躺、被投、腾空、真实屈膝压低、披风展开是允许姿态变化，但必须按该姿势登记数值并用稳定头壳/骨长证明是姿势、不是整人缩放。直立、走、出拳、站立必杀、防御、胜利等站姿类不得整人忽大忽小。每角色冻结唯一源像素 `scale`；`baseline`、`anchor_x` 按各 clip 自身 `cell`/`anchor` 登记，逐 clip 安装时取该 clip 自己的 `cell`/`anchor`/`rects`；超宽帧允许 288 格，但不能用第一组格尺寸缩放其它组，也不得回落到旧顶层 `anchor`。

### 1.2 动作不是本人招式，而是通用模板/近似姿势

并排看 `grid_defects.png`、`cross_*.png` 与每角色 `*_A.png` / `*_B.png` / `*_mixed.png`（现均已补齐）：

- 七个角色的 `special / special2 / special3` 大量只是“双拳护架改单臂前伸/双手平推/举臂”，起手、发力、收势身体运动不足；三槽必须有本人原剧依据、各自独立动作与实际效果，不是同一束改粗细/颜色/伤害。
- `down / ko / win / launcher / hit_mid / dash_throw` 在多个角色间姿势模板化：`ultraman-zero` 与 `zoffy` 的 `down`/`win` 归一化轮廓 IoU 0.84、`father-of-ultra` 与 `mother-of-ultra` 0.72–0.74，属于可疑同源或模板复制；每个角色必须按本人身份、披风/角/头冠/体型重画，不把别的角色姿势改名冒充。
- 待机只有 1 帧的角色（赛罗、杰斯提斯、盖亚、奥王、奥父、奥母）不是呼吸待机；`art/STYLE.md` 要求双脚固定、仅呼吸，头部纵幅 ≤4 px、相邻含首尾 ≤2 px、横漂 ≤2 px、一次下沉再回升。佐菲有 2 帧也要核循环接续。
- 前走按 `art/STYLE.md` 核固定骨长、接地与逐帧位移；`art/STYLE.md` 的 8 相是步行引导/骨长计算，不是装机帧数硬门。装机 `walk_forward` 当前除佐菲 8 帧外均为 4 帧；当前许多前走帧是“同一护架换脚位”，要逐帧核支撑脚、髋/眼曲线、眼纵幅 ≤8 px、相邻 ≤4 px、支撑点世界坐标偏差 ≤8 px。不允许脚底悬空、长距离滑步或换腿瞬移。
- `air_special` 等关键空中帧必须按头部列带（眼列左右约 26 px）量冠顶，**不得用整帧 Alpha 最高行**；披风、举拳和头镖外伸展件高过头顶都是动作，不是“头变大”。

### 1.3 人物帧仍混入或重复运行时特效

- `AGENTS.md` 2026-11-11 规定：人物动作帧只画人物本体；整帧不得烘焙光束、光晕、颗粒、蓄气圈、贴掌光、能量球、光刃、飞行物。投射类 `pulse / low_pulse / air_pulse / ranged_forward` 手中不得画能量球/光刃。`special` 的光束、弹体、命中、Q 蓄气只在运行时 shots / impact / 特效层。
- 实际装机：赛罗 `light1#2` 有青白掌前光块，盖亚 `special3#9` 有橙红光刃、盖亚 `ranged_forward#4/#5` 有独立非人物连通块（8 邻域第二块 502 / 298 px），杰斯提斯 `special3#3` 有红色光刃。它们可能与人物手部连通，连通块=1 通过不代表画面合格；必须逐帧人眼核并删除烘焙特效，保留纯人物动作。重新生成时手型/身体运动要补齐，不能只把光擦掉留下空手。
- Q 周身蓄气圈只在真实 Q 起势/保持/收势出现，所有技能一律禁止。技能专属局部发射/弹束/刃路/命中/火焰按运行时规格保留。
- 特效本体：PixelFX 固定 MIT 版本、离线烘焙真透明像素、保留许可和来源；硬 Alpha、≤8 色、逐帧相位变化、像素亮芯/外焰/颗粒，不用连续椭圆/简单矢量线。辉光门统一为主体 `alpha≥200` 最大连通块外扩 3 px 后：主体外 `alpha≥16 ≤100 px`、`alpha≥200 = 0`；`alpha 1–15` 尘点登记不计入。人物帧整帧单连通，不得含独立颗粒或飞行物；该硬门只用于运行时特效层验收。

### 1.4 数据接线与帧序有静默冻结/错位

- 赛罗 `state_frames.json.idle` 60 行 `sprite` 0–5，但装机 `idle` 只有 1 帧；`walk_forward` 70 行 `sprite` 0–7，但装机 4 帧。奥父 `idle` 60 行 0–5 对 1 帧、`walk_back` 66 行 0–7 对 4 帧、`walk_forward` 70 行 0–7 对 4 帧、`turn` 6 行 0–2 对 1 帧。`presentation/side_view.gd:450` 中 `idle`、`turn` 等 `f.state!="walk"` 分支会 clamp 到末帧；`f.state=="walk"` 不进该分支，走路按 `clip.ticks` 循环，越界行只造成 state_frames 与 4 帧图集不对应，不是 clamp 冻结。必须让显示帧、时间轴与本角色 `state_frames` 一致，或明确重写时间轴且经真实输入/回放证明；不得靠 clamp 假通过，也不得为凑数复制同一姿势。
- 除杰斯提斯 `special` 为 14 帧 × 10 tick 外，七角色其余 `special / special2 / special3` 共 20 组 clip 图集都是 16 帧 × 10 tick，而 `docs/verification/README.md` 记录招式映射为 72/80/96 tick（24/32/16、32/32/16、32/48/16）。要核 `content/fighters/<id>/moves/*.json` 的 `frames` 是否实际逐 tick 推进到该组全部图集帧、发射 tick/active 落在可见动作上；任何 `sprite` 全 0、只推进前半、命中时人物还是护架，都按“切换帧冻结”同类根因返工。
- 逐帧位移必须可见：每帧手、臂、腿相对前一帧有可读变化；相邻剪影差分目标 ≥0.10（奥王 `motion_22 06→07` 旧值 0.085 已知待返工）；禁止同姿势复制凑帧。循环首尾要接得上。技能帧序要有起手、发力、收势身体运动，不是三张静止 pose 靠特效播完。
- 招式/反馈/蓄气引用的每个 effect id 必须在 `content/presentation/phase3_projectiles.json` 有条目，且已记录 `atlas_sha256` 的条目必须与字节一致；新增或换贴图后补登记。`charge_overlay_policy.json` 三态 placement 按 `tools/rebuild/shared/q_charge_registry.py` 口径；本轮只读核 722 条 phase3 条目、七角色 21 个 Q id 均登记且 Q 图集 SHA 相符，七角色引用的 120 个 effect id 均登记、已记录 `atlas_sha256` 的全部与字节相符，其中 6 个 id 未记录该字段，不写“均 SHA 相符”。**这项不是当前缺陷，不要重复“补登记”当返工成果**。
- 发射点按本人当帧实际发射部位重核，双向原生误差 ≤2 px、不悬空不穿体；已对齐的九处不要无谓改动，但重画帧后必须重新核。

### 1.5 身份锚与标志结构不能先错再让像素照抄

- 每个动作帧只引用一张已签的**待机像素整帧**作身份锚；不追加多角度参考，不把 4× 定稿锚单独作动作参考（原生宽 <60 px 的模型读不出肩宽/四肢粗细）。身份锚被用户否决则下游动作整批撤销；本批没有用户明确否决某个已签锚，先按比例/姿态/身份逐角色复核现用锚，只有发现错身份、标志结构反向、断肢/裁切才回锚阶段，不主动整批重做。
- 按官方真实侧视来源核冠球/角尖/刃根相对眼列 x 的前后朝向，先判图朝左还是朝右；不能用正面/3/4 图当固定侧视基准，不能凭印象写提示词。奥王冠球在前额上方、冠刃向后掠；奥父无胡子；盖亚 V2 无披风；赛罗双头镖为额侧左右并列弯刃、贴头壳宽基座、刀尖向后上方折起；杰斯提斯标准型、佐菲、奥母各按本人标志结构与色灯核。提示词不得写角色没有的部件。
- 头高/头宽/站距两侧必须同口径，冠顶/角尖→白须底或下颌、站高=顶→最低鞋底，逐字一致；`identity-anchor.json` 启发式值只供报告。银冠/白须/银甲近白时，白须只取面部正下方窄窗内最大近白连通块。
- 导引图若用于定站姿，人物本体本身必须画成目标站距（前后脚错步、屈膝、双拳胸前护架）并先镜像到所需朝向；空白处画洋红/青线条无效。仅定架势阶段可加 1 张已装机同风格成品，只借站姿画风、不抄造型；动作帧仍只引用一张待机像素整帧。
- 落格色板保住本人额灯、计时器、胸灯等识别色；缺色时从现用待机整图重新定 ≤32 色并保留完整色板，全套共用、整图统一映射，不按身体区域局部重涂。

## 2. 逐阶段制作提示词（每帧 150–250 字，只写该帧动作）

### 阶段 A：冻结身份与尺度卡片

逐角色产出 `art/fighters/<id>/stage1/rework-20261112/identity_card.json`，至少记录：待机像素整帧绝对路径与 SHA、官方皮套照/真实侧视来源及朝向、标志结构前后判据、格宽/根点/站高/唯一 scale、冻结 32 色板（含识别色）、四肢粗细基准、可允许姿态例外清单。按 `reports/review/2026-11-12/seven-character-defects/seven_idle.png` 与每角色 `*_A.png` 看本人造型、画风、头肩比例、手脚体量；站距、色数、Alpha 通过不等于造型通过。

### 阶段 B：动作分镜与帧规格，不先生图

先把七角色的 `idle / walk_forward / walk_back / light1 / light2 / light3 / heavy / special / special2 / special3 / air_special / dash_throw / launcher / hit_mid / down / ko / win / guard / turn / charge*` 以及现有 100+ clip 矩阵标成：保留、修尺度、修姿态、修身份、重画、数据帧序修复。对每个重画 clip 写完整分镜：每帧支撑脚、髋、肩、双拳、头、披风/角/镖、与前一帧的位移、起手/发力/收势、相邻差分与循环接续，技能还要写本人原剧依据和三槽差异。分镜未完成不得批量生图。

三槽原则：原则上不同技能、独立动作和实际效果，不以同束改粗细/颜色/伤害凑槽；原剧技能确实少的例外要写依据。动作设计按本人身份、形态、版本与原剧：赛罗、盖亚 V2、奥王、佐菲、奥父、奥母分别核 `content/fighters/<id>/MOVES.md`，杰斯提斯标准型核 `content/fighters/ultraman-justice__standard/MOVES.md`（不是不存在的 `content/fighters/ultraman-justice/MOVES.md`）；没有证据的招名不得编造，必要时标内容缺口而不画假招。

### 阶段 C：单帧重生成

每次只生成一帧；身份锚只引用阶段 A 那张待机像素整帧。提示词结构固定：

> 以唯一参考图的人物为同一人，绘制这一帧的【具体动作：哪一脚承重、髋与躯干如何转、近/远臂肩肘腕拳各在哪、另一臂护架位置、头朝哪、本人披风/角/头镖/灯如何随动作运动】。保持参考图的头壳、肩宽、躯干长度、手臂粗细、大腿饱满度、小腿厚度、靴子体积与像素块大小完全一致；只让关节位置和身体重心改变，不整人放大或缩小，不换身份、不换形态、不增删本人部件。四肢粗细必须和参考图完全一致——手臂粗壮、大腿饱满、小腿有厚度，不要画细长的手脚。固定 90° 右侧视，完整人物从头冠/角尖到鞋底不裁切，长披风/头镖/武器也完整；真透明背景，只画人物本体（含仍持在手中的武器），不画光束、光晕、颗粒、蓄气圈、贴掌光、能量球、飞行物、地面、文字、边框或任何特效；相邻帧的手、臂、腿必须有可见位移，不复制上一姿势。

固定尾串另写本人识别特征和“无地面文字边框特效”，但身份/配色/像素块大小交给参考图，不在文字重复造型。约 150–250 字；不得套用他角色模板，不得写角色没有的部件。技能帧不写光色，光色只在运行时特效规格定义。生成后核实收路径、尺寸、RGBA 真 Alpha（棋盘格不算），保留原图、请求、usage、SHA 与资源对应。同一检查连续拒收 3 个不同帧即暂停并出诊断图；同一问题最多 2 种修法，仍不过换思路或留人工，不无限重掷。

### 阶段 D：落格与硬门

用 `tools/art/stage_cells.py` 按阶段 A 的唯一 scale 落格；逐 clip 取自身格尺寸/根点，重装前核该 clip 现有 `cell` 是否一致，不用第一组尺寸缩放其它组。默认格容不下本人原生体量、完整头镖或披风伸展时，统一增大该 clip 格与根点并登记，不缩人物、不裁轮廓、不逐帧变比例。统一整图色板与二值 Alpha；后处理不局部重涂，不拿离线分离冒充原生 Alpha。

每帧硬门：单连通人物主体、二值 Alpha、≤32 色、四边留白不裁、脚底/根点按姿态、站姿类主体高度对锚 ≤8%、相邻站姿高度突变 ≤10%、头部稳定地标同口径、相邻剪影差分 ≥0.10、帧内无烘焙特效/独立颗粒/飞行物；腾空/蹲/躺/被投按姿势例外登记具体高度和骨长，不以“例外”两个字放行整人缩放。生成原生格与严格最近邻 4× 联系表，逐帧看本人造型、画风、头肩比例、手脚体量。

### 阶段 E：数据与运行时特效接线

- 修 `state_frames.json` / `moves/*.json` 的 `frames[].sprite` 与实际 clip `rects` 一一对应，逐 tick 推进到全部帧；记录 startup/active/recovery、发射 tick、命中 tick 对应实际身体动作。不改模拟伤害/取消逻辑去迁就美术；判定框、hurtbox、抓握点、发射原点按新图集重算，发射点距本人部位双向 ≤2 px。
- 技能帧只有人物；shots / projectile / impact / Q 三态按已登记 effect id 接线；换贴图后补 `phase3_projectiles.json` 并核 atlas SHA、effect.json 尺寸/rects/锚点、Q policy 三态。已登记、已记录 `atlas_sha256` 且与字节相符的部分不要重复补登记；未记录该字段的共享旧式条目按现状保留，不冒称 SHA 已核；若重画特效，按 PixelFX 许可、硬 Alpha、≤8 色、亮芯/外焰/颗粒/相位变化和辉光门验收。
- 逐 clip 用 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/tools/art/install_cells.py --fighter <id> --only <clip> --merge` 或明确路径安装；这是当前单 clip/merge 模式，不是旧批量安装器。禁止全量重装覆盖其它 clip；装后逐 clip 核 `manifest.json` 的 `cell`/`anchor`/`rects`/`ticks` 与 atlas SHA、`.import` 侧车、招式和状态引用。禁止未经核验直接覆盖 `assets/` 现存图集。
- 人物与 FX 分离后，逐招核两件事：帧内只有人物；运行时该招发射、飞行、命中、收势的特效都真实出现且位置对准本人部位。任何 `pending_` id、未登记 id、静默跳过都按失败，不拿“逻辑检查没报错”当可见。

### 阶段 F：实机验收（主管复核前先自验）

1. 每角色出：待机、前后走、轻/重/三槽必杀、空中必杀、投/被投、受击/倒地/KO/胜利、Q 三态的逐 clip 联系表（原生格、4×、相邻差分、脚底共同基线）；七角色同尺度并排表。根看联系表并留审片记录。
2. 主游戏入口 `开始游戏.command` / `app/scenes/main.tscn`，训练/F1 调试；锁内命令为 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/.venv/bin/python /Users/wurulan/Developer/Projects/Game/ultraman-neo/tools/godot_lock.py -- /Users/wurulan/Developer/Projects/Game/ultraman-neo/.venv/bin/python /Users/wurulan/Developer/Projects/Game/ultraman-neo/tools/verify.py --keep-going`，并另报本批逐帧美术门的独立结果，二者分开写。
3. 两个朝向、720/1080、真实输入、独立回放、原速逐动作看画面：待机循环、走路换腿接地、技能起手/发射/收势、Q 三态、击中与倒地、双方完整人物含披风/武器/长尾留在屏幕内，镜头按实际 Alpha 轮廓共同取景，不单独挪人物假造空间。必要时录短临时视频，审后直接删除；无录屏就写无录屏。逻辑 PASS 不能写成美术/听感通过，未听审就写未听审。
4. 交付 `art/fighters/<id>/stage1/rework-20261112/README.md`：本角色改了哪些 clip/帧、每帧 SHA、旧值→新值、重生成请求与 usage、拒收记录、诊断图、门值、装机 atlas SHA、实机证据路径；根因类事故由主管追加到 `docs/verification/README.md` 日期节，单批失败留在本批 README，不新建独立清单。

## 3. 完成定义

- 七角色同一动作内和相邻动作间不再整人忽大忽小；允许姿态压缩有数值和骨长证据。
- 待机是真呼吸循环；走路按 8 相骨长/引导生成连续换腿，不要求装机 8 帧；技能有本人依据的起手/发力/收势；down/ko/win 等不再模板化，各角色身份结构、前后朝向、色灯无误。
- 人物帧只剩人物；运行时特效完整可见、贴部位、不双重、不串用他人专属图集；effect id 全登记，已记录 `atlas_sha256` 的均相符。
- `state_frames` / move frames 与实际图集逐帧对齐，越界导致的 `idle`/`turn` clamp 冻结与 `walk` 帧序错位均消失；输入、回放、逻辑、资源、命中、取消通过；双朝向 720/1080 实际画面通过；无录屏、未听审、未用户亲审如实写。
- 没有用“新增 N 张 / 逻辑 PASS 数量 / 文件数量齐”冒充满意；交付的是逐角色逐 clip 可复核的审片证据和干净 diff。

## 4. 先做诊断，再动生成

第一步只准交：七角色缺陷逐 clip 清单（保留/修/重画/数据修复四类）、分镜表、身份卡片、现有资产 SHA 基线和返工顺序。根按 `root_delegated_by_user` 自签并继续，不设逐项主管门禁、不逐项等用户。任何未过阶段 A/B 的批量出图、整批覆盖安装、改 core 或改旧规则的行为都视为返工失败。

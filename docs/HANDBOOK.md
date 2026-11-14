# UFEneo 现行主题手册

用途：核对当前状态、目录架构、数据格式、美术流程、战斗设计、stage1 标准、音频和第三方规范时读本文件。根 [README](../README.md) 是项目总览与唯一文档索引；根 [AGENTS](../AGENTS.md) 是唯一执行准则；根 [REBUILD_2D_PLAN](../REBUILD_2D_PLAN.md) 保留设计规格与 2.5 节招式矩阵。

## 合订目录

本手册是 `docs/` 主题规范的唯一现行入口；各节按主题收录原规范，重复旧进度段与旧运行说明不复制。冻结回执 `docs/verification/*.json` 原位保留，不改旧路径文字。

- 状态 / 验证边界
  - PROGRESS.md → [第 1 节](#第-1-节--progressmd)：当前状态、成果索引、依赖复核、后续优先级、验证与发布边界
  - verification/README.md 现行说明：docs/verification/README.md 回执目录说明与边界
- 目录架构
  - PROJECT_LAYOUT.md → [第 2 节](#第-2-节--project_layoutmd)：目录归属、依赖方向、引擎选型、数据流与热点模块
- 数据格式
  - DATA_FORMATS.md → [第 3 节](#第-3-节--data_formatsmd)：招式 JSON、持续束发射点、独立实体攻击段
- 美术流程
  - ART_PIPELINE.md → [第 4 节](#第-4-节--art_pipelinemd)：生图流程、源库存储、图鉴与武器规范
- 战斗设计
  - COMBAT_DESIGN.md → [第 5 节](#第-5-节--combat_designmd)：战斗形态、变身、三个能量必杀槽
- stage1 标准
  - STAGE1_STANDARD.md → [第 6 节](#第-6-节--stage1_standardmd)：未实机奥特曼动作制作标准与验收
- 音频
  - AUDIO.md → [第 7 节](#第-7-节--audiomd)：Kits 接口、凭据与计费边界、怪兽配乐依据
- 第三方
  - THIRD_PARTY.md → [第 8 节](#第-8-节--third_partymd)：上游版本、来源、许可
- 索引维护
  - README.md → [第 9 节](#第-9-节--readmemd)：原索引表已并入根 README.md；维护规则与分散入口在本手册

## 收口说明

- 根 `README.md` 是项目总览、运行入口和唯一文档索引；根 `REBUILD_2D_PLAN.md` 仍是设计规格，2.5 节锚点不变。
- `docs/PROGRESS.md` 的“获取与运行”旧段、重复历史进度、重复验证边界按主题归到本手册对应原节；获取与运行的现行命令只保留在根 `README.md`。
- 原文中的路径、SHA、回执编号与当时结论均不回填改写；需要现行入口时按本手册顶部目录与根 `README.md` 查找。
- 其余现行文档入口按根 `README.md`“唯一文档入口”表；历史回执仍在 `docs/verification/`。
- 2026-11-14 起，`docs/PROGRESS.md`、`AUDIO.md`、`PROJECT_LAYOUT.md`、`STAGE1_STANDARD.md`、`ART_PIPELINE.md`、`DATA_FORMATS.md`、`COMBAT_DESIGN.md`、`THIRD_PARTY.md`、`docs/README.md` 的正文只留在本手册对应节。旧路径由 `tools/maintenance/layout_routes.json` 指回本手册或根 README，冻结回执里的旧路径文字不改。

## 内容流水线

手感先于美术。一条招式按这个顺序做，不反过来用生图结果决定逻辑时长。

1. **定帧数据。** 按 `REBUILD_2D_PLAN.md` 2.5 节和 `core/combat/feel_rules.gd` 的档位写下 startup / active / recovery，以及受击硬直、防御硬直、命中停顿、推退初速和取消路线。普通技对齐轻 / 中 / 重档；已经手写过的推退只换成等距初速。
2. **灰盒验手感。** 用占位帧或现有剪辑在主游戏训练模式打。看两个朝向：被防帧差、命中后能否接上下一招、推退是滑动而不是瞬移、转身 / 落地 / 起身按后能防。手感没过不生正式图。
3. **按帧时长生图落格。** 逻辑时长已经定死。美术帧数和每一帧的 tick 服从这份帧数据：打击动作要能看出起手、发力和收势，禁止把同一姿势拉长去填 tick。走路用等长帧，步幅和每 tick 位移匹配。受击不少于能分出受击与恢复的帧，不用 3 帧硬撑整段硬直。
4. **特效登记。** 人物帧不烘焙光束和粒子。新增或改换的 effect id 写入 `content/presentation/phase3_projectiles.json` 并核 atlas SHA。
5. **验证。** `tools/godot_lock.py` 跑确定性、回放和分层检查。改了手感数值，PR 里写改前 / 改后对比。画面还要看两个朝向和 720/1080。逻辑通过不等于美术或听感通过。

## 示范角色：赛文

以后每个角色按赛文这条做。赛文是当前素材最全的可玩角色（`assets/fighters/ultraseven/animations/`）。`docs/DEMO_CHARACTER.md` 由 `tools/maintenance/layout_routes.json` 指回本节，不另存一份正文。

照抄步骤：

1. 读 `core/combat/feel_rules.gd` 的档。把该角色每一招的起手、持续、收招改成命中框窗口的真实长度；受击硬直、防御硬直、命中停顿和推退初速按档写进招式 JSON。模板值（受击 20、防御 12、推退 8）加载时仍会被同一公式覆盖；已经写成档位初速的推退保持不变。投技不改硬直。
2. 走路循环的 `ticks` 必须等长，`state_frames` 里同一张走路图的重复次数和 `ticks` 相同。受击 `hit_high` / `hit_mid` / `hit_crouch` / `hit_air` 的状态帧长度不得短于本角色站立受击硬直的最大值，剪辑 `ticks` 之和等于这个长度。现有图不够就只重排、重复相邻已有帧；缺的新姿势写进 `tools/rebuild/<id>/` 的提示词清单，不在这里生图。
3. 近身命中框的宽和高至少为 `round(0.22 × target_height)`（赛文身高 144，即 32）。更小的拳脚框以中心为基准补到这个尺寸。受击框并集的高至少为身高的 0.90、宽至少为 0.46。光弹嘴部那种边长小于 16 的框不放大。
4. 蓄力超重击不用每个角色单独做逻辑。`UfeFeelRules.ensure_power_crush` 在加载时从重击复制三档。没有专属剪辑就播重击图，蓄力时表现层播已登记的 `impact_heavy`。赛文缺的蓄力姿势和出招姿势同样记在缺帧清单里。
5. 跑 `python3 tools/check/seven_demo_pipeline.py`。它检查走路帧时长方差、受击是否盖住硬直、命中框相对身高的比例，并核对缺帧清单。全量 `tools/verify.py` 会带上这项和 `tests/power_crush.gd`。

检查表：

- 轻击和重击的命中停顿、受击硬直、防御硬直、被防帧差、推退初速与手感基调表一致。
- `walk_forward` 与 `walk_back` 的 `ticks` 方差为 0。
- 四段受击的状态帧长度 ≥ 站立打击的最大受击硬直，且剪辑时长等于这个长度。
- 近身命中框短边 / 身高 ≥ 0.22。
- 蓄力 19 tick 松手是 1 档，20 tick 是 2 档，39 tick 仍是 2 档，40 tick 按住也自动出 3 档。
- 蓄力中防御或闪避会取消，被打会进入受击而不是出招。
- 同一输入跑两次，快照和内容指纹一致。
- 训练模式能看到当前档位。Q 蓄能仍然进 `charge`，不进 `power_charge`。

---

<a id="第-1-节--progressmd"></a>
## 第 1 节 · PROGRESS.md

### 当前状态

用途：核对当前可玩范围、各角色未完项、验证边界与接续优先级时读本节；历史清理交接保留在 `docs/verification/README.md`，不在此复制。

更新：2026-11-13。逐角色动作生产进行中（官方皮套照 → 格斗待机架势 → 待机像素整帧作动作身份锚 → 单帧动作 → 落格）；八装甲未齐，仍不开放。2026-11-03 清理交接只说明当时状态，完整历史摘要保留在 `docs/verification/README.md`，不在此复制。

当前执行状态以根 [AGENTS](../AGENTS.md) 和用户最新指令为准。


### 当前成果与历史证据索引

本节按日期倒序保留制作与验证回执；只有本节开头、根 `AGENTS.md`、
“后续优先级”和“验证与发布边界”是现行结论。2026-11-12 及更早的单条记录
只用于定位资源与历史证据，不另立文档，也不覆盖当前规则。

- 2026-11-13 仓库梳理：废弃临时脚本、Python/shader 缓存、过期本机日志与未被回执点名的历史验证 run 已按消费者、SHA 和动态路径核后直接删除；七角色在制诊断生成器归位到 `tools/rebuild/seven-character-rework-20261112/`，文档索引与依赖口径收口。锁内全量 59 项 PASS、仓库审计通过；详情见 [验证回执](verification/README.md)，无录屏、未听审。
- 2026-11-13 赛罗/盖亚 idle 返工与 720/1080 实机：两角色上一批 11 张独立生成待机 raw 因脚位/头位漂移拒收（SHA 已记录后删除，不备份）；改用与身份锚同站姿的新基线，按 172/925=0.185946、175/1015=0.172414 两套固定比例落格六帧，整身 dy=[0,1,2,3,2,1]、脚踝带固定，双脚/头幅/横漂/站高门通过，相邻剪影 0.046–0.050 低于 0.10 登记为 gap。idle 六帧已装机（256 格、[128,248]、6×10 tick），图集与六帧逐像素一致。主游戏新增 `--capture-size=WxH`，按 1280×720/1920×1080 各截镜像对战，左右朝向同屏，训练六帧间隔 10 tick 实看通过；无录屏、未听审。锁内全量 59 项 PASS。
- 2026-11-12 赛罗六形态选择与战斗切换基础：选人界面可按出场形态开局，战斗中形态键加方向随时切换六形态，不耗气、不限次数、切换中不无敌；回放记录并校验双方出场形态。基础赛罗 `form_switch` 六帧已装机（256 格、根点 [128,248]、6×10 tick，站高 186/174/179/172/173/178，均在中位站姿容差内），形态切换共用 60tick 时间轴；时间轴 `sprite` 原全填 0 导致切换时冻结在首帧，已改为每 10 tick 推进一帧。新增 `effect_registration` 与 `form_selection_consistency` 两个硬门，拦未登记特效与选人/战斗形态半开放。五个剩余形态的动作整帧生产中，selection 与 battle_forms 的 implemented 仍未开放；未实机、无录屏、未听审。
- 2026-11-12 七角色整帧落格与招式对齐：赛罗、杰斯提斯、盖亚、奥王、佐菲、奥父、奥母的纯人物整帧已按各自身份锚比例落格、装机并重映射招式；special/special2/special3 统一 72/80/96 tick（24/32/16、32/32/16、32/48/16），air_special 24（10/1/13），奥父基础招按初代模板 20/28/12，dash_throw 24。超宽空中/披风帧改用 288 格（赛罗/杰斯提斯/盖亚 air_special、奥父 light2），其余 256/192；根点与逐帧 bbox/SHA 见各角色 `stage1/cells/cells.json` 与 `tools/rebuild/<角色>/README.md` 2026-11-12 节。锁内全量验证 57 项 PASS。当前装机 clip：赛罗 113、杰斯提斯 108、盖亚 105、奥王 104、佐菲 108、奥父 104、奥母 105；仍不等于动作全齐。
- 2026-11-12 赛罗特效家族与发射点：赛罗三槽必杀、空中必杀与 Q 蓄气接入本角色 11 段 PixelFX 自绘特效（硬 Alpha、≤8 色，phase3 共 695 条）；盖亚/奥王/佐菲/奥母已烘焙但未登记的 Q 蓄气补登记 12 条，Q 蓄气不再整段不可见。special3 双镖发射点改 [59,132]/[33,133] 并补 31 点外飞折线与 tick 32–95 逐 tick 回收锚，pulse/low_pulse/air_pulse/ranged_forward 发射点改按当帧手部；九处发射点距本体均 0.00 px。
- 2026-11-12 奥父/杰斯提斯/赛罗基础光弹专属特效家族：奥父 16 段、杰斯提斯 9 段、赛罗基础 2 段 PixelFX 离线自绘（`father_fx_*`/`justice_fx_*`/`zero_fx_pulse_*`），已并入 `phase3_projectiles.json` 共 27 条并接线对应招式；奥父/杰斯提斯 Q 三态落点并入 `charge_overlay_policy.json`，配合只登记落点时注入显示的修复，无附件也能在真实 Q 起势/保持/收势显示。三套图集逐段复核尺寸、SHA、二值 Alpha、4 连通主体与主体外 `alpha≥16 ≤100 / ≥200 = 0`，27 段全部通过；赛罗命中段原按 8 邻域留了主体外 2–6 px 实心碎点，已改 4 邻域重烘并同步 SHA。奥父 Q 蓄气三态首版为红色竖条笼、24 帧变化约 1.5%，已打回改为椭圆火焰环（橙白亮芯、分层火身、外缘火舌与上升火星，相邻变化 20%–52%）并重登记。`effect_registration` PASS。未实机、无录屏、未听审。
- 2026-11-12 未完成：奥父 dash_throw 仍旧人物帧（只对齐节奏）；奥王 motion_22 06→07 相邻差分 0.085 未达 0.10；七角色均未做双朝向 720/1080 实机画面复检，无录屏。
- 2026-11-11 装机增量与语音补全：奥母、盖亚、奥父、奥王四名角色继续按 stage1 动作帧安装并重导数据，对照 `ultraman-taro`（100 通用 clip / 47 招 / 53 状态声）的当前覆盖为：杰斯提斯 108/50、赛罗 110/47、佐菲 96/35、奥母 93/42、奥王 82/40、盖亚 78/25、奥父 61/35（clip/招）。`roster_data_integrity` 登记仍缺的运行时状态 clip：奥母 7、盖亚 6、奥父 34、奥王 19（intro/victory/defeat/timeout/ko/win、hit/block/stun/guardbreak、投技与被投、charge/burst/chase_takeoff/vertical_jump/air_tech 等），未齐不等于完成。
- 2026-11-11 事件语音：7 角色各补 down/heavy/taunt/timeout 共 28 条，来源逐条登记并 1:1 接入 `sources.json`/`runtime.json`；因 `fx_audio` 峰值门把首轮 −1.2 dBFS 拒收，统一重归一化到 −10.0 dBFS 后两项音频检查 PASS。未听审，`listening_reviewed=false`。
- 2026-11-11 减速规则：core 新增招式字段 `chill`（`ticks`/`speed_percent`），只在未防住的命中写入受方，每 tick 递减；walk/dash/backstep 位移按档位取整缩放，出招、受击与硬直时序不变。佐菲 `special2` 超级冻霜接 120 tick / 50%；新增 `tests/chill_effect.gd`，全量验证 57 项通过。该数值为游戏编排，未实机校准。
- 图鉴重建：1653 条统一 384×256 画布、根点 [192,248]、按设定身高换算站高（3.84 px/m；人类固定 96）。609 条按官方剧照/皮套照图生图重画并安装，图鉴图 1075 个文件变动；参考图补齐到 1686 张，低清官方源保留原图并标例外。旧批准标记全部重置为待实机复核；17 条重复形态以 `aliases` 归并。图鉴 UI 改分页列表、固定画布不滚动。全量 54 项通过；未做 720/1080 双向实机审片。[验证回执](verification/README.md)

- 未实机奥特曼动作生产（2026-11-09 起）：74 个未实机 ultra 角色已生成 4× 定稿锚（`art/fighters/<id>/model/identity-anchor-x4.png`），逐张核过严格最近邻零插值、二值 Alpha、32 色、源 SHA 一致。制作标准写在 `本手册第 6 节`，落格工具 `tools/art/stage_cells.py`（全套共用一个源像素比例，硬门只判连通块/Alpha/色数）。
- 动作身份锚改口径（2026-11-09）：只引 4× 定稿锚生成动作帧的第一批（盖亚/杰斯提斯/赛罗）整批作废并删除——定稿裁到 bbox 后原生只有 27–38 px 宽，模型读不出肩宽与四肢粗细，自编了一套身材；且待机被画成并脚直立，脚外缘间距只有站高的 0.33–0.36，已装机 10 个角色实测 0.50–0.98、中位 0.71。新口径：先由官方皮套照定格斗待机架势（分脚、屈膝、双拳护架），再转待机像素整帧，此帧才是此后动作帧的唯一参考。盖亚新口径 `idle-00` 接续复测脚外缘间距/站高只有 0.5455，未过 0.65–0.80；已撤销候选、删除淘汰源及重复皮套照，保存 `art/fighters/ultraman-gaia/stage1/diagnostic/stance-gate.png`，按返工刹车暂停。未安装、未实机检查。
- 杰斯提斯标准型待机返工（2026-11-09）：用户否决新锚“样子太丑”；根此前只核站距、头宽和像素硬门而误签，手脚体量与厚重肩甲造成整体失衡。该锚及全部下游已删除，不计动作完成，拒收诊断在 `art/fighters/ultraman-justice/stage1/diagnostic/rejected-anchor.png`。返工仅新增待机照片与一张像素候选：正常握拳、靴子与贴身肩甲，原生格及4×已静审；`art/fighters/ultraman-justice/stage1/cells/idle-candidate-02-cell.png` 为站高154、宽113、32色、二值Alpha、单连通。旧图鉴色板吞掉双灯，已改用新待机整图色板保留本人青绿额灯与胸灯。候选02头宽24/22（+9.09%）、候选03头宽25/22（+13.64%），均未过8%门，**尚未签动作锚**，不铺动作、不安装；完整记录在同目录 `cells.json`。阶段A复核确认头身比偏大主要来自照片阶段：照片05/06/07头高/站高0.2321/0.2157/0.2154，官方ref-01为0.1746、图鉴0.1948，像素03忠实保留照片比例。圆谷官方角色页 `tsuburaya-prod.com/heroes/ultraman-justice` 的 Standard Mode 四图已落到 `art/fighters/ultraman-justice/sources/tsuburaya-justice-2019/` 并写 `source.json`；official-standard-01（正面直立全身）头高/站高0.1864、头壳宽/站高0.1298，official-standard-02（官方格斗架势）0.1712，03只核头冠侧面。阶段B首张照片08站距0.6432、头壳宽/站高0.1440（图鉴+0.8%）已到位，但头高/站高0.2193（官方01 0.1864，+17.6%），头冠过高、面罩偏长，拒收未转像素。第二张照片09（SHA `21378b61…`）站距0.6850已过，但双鞋底差32源px（约3.88原生px）、头高/站高0.2087（官方01 +11.9%、图鉴+7.1%），且头与上身转成近正面3/4，失去固定侧视；拒收，不出像素。照片线按刹车停止，等真实侧视来源或人工决定。未签锚。
- 盖亚/杰斯提斯并行续作（2026-11-09）：用户指定派子代理完成这两角色，已各派一个制作代理；角色已指定不等于旧候选获批准。两个代理只写各自角色的 art 与批次README，共享规则/进度由根维护。盖亚候选05（原生格192、站高154、站距0.6948、头宽22/22、32色、二值Alpha、单连通）已经根实际看原生格/4×/整图通过造型，并签为正式身份锚（`review_authority=root_delegated_by_user`）；动作集已按阶段完成 idle(2)、walk_forward(4)、walk_back(4)、dash_start(2)、dash(4)、takeoff(2)、air_rise(1)、air_fall(1)、land(2)、light1(3)、light2(3)、light3(4)、heavy(4)，每阶段联系表逐帧根看通过，hit 待放行。杰斯提斯候选03头宽25对22为+13.64%，仍未过8%门，未签锚、无动作；阶段A诊断与官方 Standard Mode 四图见上条。整套尚未完成，不安装、不提交。
- 赛罗基本红蓝形态（2026-11-09）：用户先指出“头标好像不对”，复核官方确认双头镖为额侧左右并列弯刃、有转折凹口与贴头壳基座；00链撤销删除。随后用户再次指出“头还是不对呀，你直接找一个侧视图”，01照片/清图/像素/落格/4倍图全部拒收并按SHA删除，无备份。后续在圆谷官方15周年新闻页 `tsuburaya-prod.com/news/7732` 找到官方宣传图 `zero15_cheki_img.jpg`（1920×1279，SHA `226ca50e…`），左侧为零本人右侧近侧脸；裁头部 390×510（SHA `a44cce44…`）作结构核验，确认弯刃贴头壳、宽基座、刃缘转折与凹口、刀尖向后上方折起。用官方正面全身＋该侧脸头部＋已装机站姿重定待机照片 `image-55259-28`（站距0.6732，SHA `6d735b7e…`），单参考转像素 `image-55259-29`（SHA `5f465167…`）。用户实际看后明确认可：“**这个就非常不错，我很满意，就它了。**”正式锚 `identity-idle-pixel.png`（256格、站高188、32色、二值Alpha、单连通、站距0.6809，SHA `c36397a8…`），动作帧唯一参考为同一帧的1024×1536像素源；动作集已按阶段完成 idle(2)、walk_forward(4)、walk_back(4)、dash_start(2)、dash(4)，每阶段联系表经根复审；dash-00 前倾已对齐、03→00 接续改善，但站高155对02的169低14px，记为已知差异留实速复审。takeoff(2)、air_rise(1)、air_fall(1)、land(2)、light1(3)、light2(3)、light3(4) 完成，heavy 待放行。未安装、未启动Godot、无录屏。
- 佐菲 stage1：16 帧候选（待机 2、前走 4、跑 1、起步 1、冲刺 1、起跳 1、上升 1、下落 1、落地 1、直拳 1、受击 1、格挡 1），全部单连通、二值 Alpha、29–32 色，站高 85–154。未安装、未接运行时、未做 720/1080 双向实机检查。记录在 `art/fighters/zoffy/stage1/requests.json`。
- 佐菲：图鉴 2026-11-09 按用户指定流程定稿——图片模型先生成真实皮套剧照（右侧视错步战斗架势），再以照片为底用图片模型转像素整帧，只把头顶尖角改矮，最后经 `catalogue_native` 与 `catalogue_rescale` 落到站高 173、32 色、二值 Alpha。HEAD 安装版 SHA `2607b58f`（宽 107）；工作树另有 1.5× 块化版 SHA `addd0bce`（宽 110），未提交。请求记录在 `art/fighters/zoffy/`。整套动作、声音、FX 与运行时接线未做。
- 图鉴既有成品恢复：13 条在 2026-11-08 重建时被覆盖的已批准条目（12 条 `new_art_approved`、1 条用户返修版）按原 PNG 与 SHA 逐条恢复；18 个已实机安装角色仍指回实机战斗图并带待机真帧条。

- 阿斯特拉 stage1（2026-11-10）：身份锚已签，`review_authority=root_delegated_by_user`（不是 user_approved）。旧照片 `stance-04` 已过照片门，但 pixel-00/01 把照片头高 25.94 放大到 31/32；pixel-02 用 8px 网格导引仍为 24×30，证明是照片→像素转换固定偏置，换照片源无法解决。pixel-03 改用 154 站高最近邻比例导引双输入，落格后 192×192、不透明 32 色、二值 Alpha、根点 [96,184]、脚底 183、站高 154、站距 0.6558、单连通，识别色绿 3/黄 13/蓝 4；亮银头 23×26（门 ≤25 宽、24–27 高）过，完整银 24×30 作旁注记录，未缩头、未改阈值。复制检测：与导引 Alpha IoU 0.7730、同坐标 RGB 完全相同像素 0.0、32 色对 3845 色，确认是模型自己的像素重建而非放大照抄。锚 SHA `0d0ea0b6…`，严格 4× SHA `ba930e1b…`；导引为一次性中间物已删除，只留 SHA。动作帧按最小集开始，未安装、未启动 Godot、未提交、无录屏。

- 杰斯提斯动作集（2026-11-10，第25批）：专属/必杀 8 组共 72 帧签署，累计 **449 帧**（`status=449_frames_signed_root_delegated_by_user`）。招式依据先落 `content/fighters/ultraman-justice__standard/MOVES.md`（2.5.7 逐格定案、三槽差异、命名登记），再按该文件逐格生成：command_40 `motion_236` 8、command_41 `motion_623` 8、command_42 `motion_214` 8、command_43 `motion_22` 8、command_44 `motion_41236` 10、command_45/46 与 special_1 共用 `special` 8、special_2 `special2` 10、special_3 `special3` 12。三槽起手/发射部位/光色不同（双手橙色宽束、右单臂青色破屏障、双手过顶经头部水晶），不是同束改粗细。我独立复检 2904 项 0 错误：192×192、二值 Alpha、≤32 色、脚底 183、root [96,184]、严格 4×、联系表 1460×808；非技能帧整帧单连通，技能帧只判人物主体。矩阵覆盖 已签 99 / 已签短版 2 / 未做 2 / 不适用 1（共 104），剩余仅 `air_tech`、`chase_takeoff` 刹车停。本批 25 个候选被拒并核 SHA 删除（橙色火焰误光、画进对手、正面/背面视角、光束出画截断、站高无法落格等），逐条在 `action_attempts`。头壳 70 帧 21–24×30–33；special3-05（16×28，头顶聚能球并入头冠连通块）与 special3-06（24×36，后仰透视）两帧例外保留原值，不据此判头变大。20 帧青色总数 13–1520 含技能光，标 `cyan_split_reliable: false`，不冒称分额灯/胸灯。未安装、未启动 Godot、未提交、无录屏；720/1080、实速、声音未验。
- 杰斯提斯动作集（2026-11-10）：第24批被投方 `thrown_forward` 3、`thrown_back` 4、`thrown_air` 4、`thrown_dash` 4 共 15 帧签署，累计 **377 帧**（`status=377_frames_signed_root_delegated_by_user`）。我独立复检 379 张原生格：192×192、二值 Alpha、≤32 色、**整帧单连通 0 例外**。矩阵覆盖 已签 89 / 已签短版 2 / 未做 12 / 不适用 1（共 104）。腾空帧最低可见行 = 183 − air_gap（0/24/0、0/20/28/0、30/24/14/0、全 0）。两处拒收已记 SHA：`thrown_air-02` 首版近白不透明底、`thrown_forward-01` 首版 Alpha128 以上 2 连通含 1 px 碎点。头壳测量由“最高连通块”改为“最上额灯所在银/金/青连通块”，旧自动值保留在 `auto_measure_superseded`，15 帧头壳 22–28×24–34（锚 23×32）。**未做 12 格**：command_40–46 与 special_1/2/3 共 10 格缺专属技/必杀原剧依据（无 MOVES.md、`skill_library.json` 里 Justice `skill_ids` 为空）；`air_tech`、`chase_takeoff` 仍刹车。未安装、未启动 Godot、未提交、无录屏；720/1080、实速、声音未验。

- 奥特之父 stage1 阻塞（2026-11-10）：**八张照片候选全未过，无身份锚**。门为含双角头高 ≤0.2382（＝官方主来源 ref-01 自身实测 0.2313 +3%；图鉴 4× 原生宽 58<60，按 AGENTS 不能单独作身材依据）、站距 0.65–0.80、双鞋底差 ≤1 原生px（173 口径）、严格 90° 右侧视。
  - 根因分三段：`stance-raw-08` 用 ref-01 正面 + ua-10 双参考 → 躯干/骨盆被正面图拉回 3/4；`stance-raw-09` 只留 ua-10 → 侧视正确，但模型按参考 258×768 窄幅返回 **727×2164**，画布宽/站高只有 0.418，站距门在该画幅下物理不可能，头高 0.2862；`stance-raw-10/11` 改用宽画幅参考（ua-10 原样居中贴进 1152×768，SHA `a5287732…`）→ 确实解除窄幅锁死（两次都返回横向 1536×1024，站距 0.5027/0.8174），但 raw-10 缺白须/蓝胸灯/胸甲铆钉/披风（ua-10 本身没有这四项），raw-11 靠提示词补齐却把双角画成近直锥，且头高 0.2714/0.2886、raw-11 站距 0.8174 超上限。
  - 结论：头高偏置 0.2714–0.2886 横跨三种参考设置，与画幅无关；单 ua-10 参考下“补身份”与“保双角”互相拉扯。改走按目标站高（173）做的比例导引第三工序（阿斯特拉已验证的方法），见 `tools/rebuild/father-of-ultra/README.md`。未生成像素候选、未安装、未启动 Godot、未提交、无录屏。
  - **本轮（比例导引两次尝试后仍停）**：导引 `stage1/idle/references/stance-guide-ua10-173x4.png`（SHA `5ed62819…9d1f`）。`raw-14` 站距 0.7516、双鞋底 0.55 原生px 均过，但含双角头高 0.3021 不过；`raw-15` 头高回到 0.2390 过，站距却掉到 **0.1330**（人物被画成双手叉腰、双脚并拢）。两张失败项互换，证明「头高」与「站距」在该工序下不能一次同帧成立；按返工刹车停，两张按 SHA 删除。**根因与奥王 v16 同一机制**：导引图自身的身体轮廓是并脚站立，只有空白处画了站距线，模型照抄身体、忽略线条。诊断 `stage1/diagnostic/stance-raw-14-measure-2026-11-10.png`（SHA `0495270b…c6e0`）、`…raw-15…`（SHA `78193a35…1d92`）。下轮导引必须把人物本体画成 0.72 站距 + 双拳胸前护架，并先镜像到朝右。

- 奥特之王 stage1（2026-11-10）：**256 待机身份锚已按 v18 重出并 `root_delegated_by_user` 自签**（冠向返工后新锚），动作帧未做——v17 锚与下游 21 帧因冠饰前后方向反向已被用户否决并整批撤销。
  - **冠饰反向（本轮，用户指出）**：用户圈出锚上冠顶尖角，指出“尖角反了”。同口径实测（冠球＝最高 3 行本体像素 x 均值、眼＝头部最大红块 x 均值，朝右时球 x>眼 x 为正确）：ref-02 官方皮套侧头 **+59.8 球在前**、ref-03 官方软胶侧身 −52.5（朝左，前＝左）**球在前**；v17 照片 −120.5、v17 像素 −100.5、v17 锚 −16.1，**三级一致地反**。根因两层：照片提示词把错误方向写成规格（原文“银色后掠冠（后端小球、刃下纵向肋）”），等于指定模型画反向；唯一参考 ref-03 matte 朝左且未先镜像，模型自行翻身后冠向没跟着翻。**门禁盲区**：站距、鞋底、头高、头宽、辉光、连通、色数、朝向左右全过，没有任何一项在测标志结构的前后方向。
  - **撤销**：按 AGENTS“用户否决身份锚后下游动作整批撤销并删除”，锚、v17 照片、v17 像素、21 张动作帧与全部原始源共 **58 个文件逐个核 SHA 后删除**（21,060,704 bytes），不留副本。不做像素级裁切镜像（冠与头壳接合点不同轴，原地镜像会把冠球推到眼外并在颈侧留缝）。诊断 `stage1/diagnostics/crown-orientation-defect-20261110.png`（四联：ref-02／ref-03／v17 照片／v17 锚，SHA `6d92bac3…ca5f5`）。
  - **v18 照片**（`image-65174-1199`，参考先镜像为朝右的 `ref03-matte-manual4-mirrored-right-20261110.png`，SHA `2815fe51…3679`；提示词改为“前额上方小圆球、冠刃从球后方向后上方斜掠”）：实收 1199×1312，源 SHA `08cf673d…f145b`。站距 **0.6955**、双鞋底差 **0.88 原生px**、头高 **0.2148**、辉光主体外 alpha≥16 **0** / ≥200 **0**、单连通、真 Alpha、全身不裁、严格右侧视、**冠球在前 +85.5**——照片门全过。诊断 `stage1/diagnostics/photo-v18-gates-20261110.png`。
  - **像素三代**：`raw-01`（`image-65174-1201`，SHA `1c577cf1…07d4`）站距 0.678、鞋底 0.95、头 52.1/30.0/22.1 原生px、球-眼 +93、辉光 1/0 → **采用**；`raw-02`（`image-65174-1203`，SHA `85c3a5bc…aa01`）白须底被压到 12 原生px（照片 21.4，−43.7%）、鞋底 1.11 → **拒收并按 SHA 删除**；`raw-03`（`image-65174-1205`，SHA `40873ca5…14bb`）数值全过但须形较薄、冠刃转折不如 raw-01 近官方 → 留作对照。头高同口径三处互核：照片 47.9 / 像素 52.1 / 落格 51 原生px；分段宽度比（0-20% 0.218 对 0.204、20-35% 0.356 对 0.352、50-80% 0.562 对 0.562）与照片一致。
  - **新锚落格**：`stage_cells.py --cell 256 --baseline 248 --anchor-x 128`，比例 `223/1413=0.158044`；`idle-candidate-v18-cell.png`（SHA `de1a9b8c…b8da`）、严格 4× `idle-candidate-v18-x4.png`（SHA `e8c3965c…1c3f`，逐像素相等已验证）。bbox [48,25,202,247]、站高 223、宽 155、脚底 247/247、站距 0.6865、32 色全属图鉴色板、二值 Alpha、单连通、**冠球在前 +15 px**；头口径 冠顶 y25 / 眼 (132,54) / 白须底 y76 → 51·29·22 原生px。签署 `review_authority=root_delegated_by_user`、`user_reviewed=false`。诊断 `stage1/diagnostics/idle-candidates-v18-20261110.png`（候选 A/B 的 4× 全身 + 8× 头部）。
  - 完整记录 `art/fighters/ultraman-king/stage1/cells/cells.json` 与 `tools/rebuild/ultraman-king/README.md` 第二十一轮；撤销清单在 `stage1/requests.json → anchor_revocation_20261110`。**动作帧未做**（下游整批已撤销，须在新锚上重做）、未安装、未启动 Godot、未提交、无录屏。
  - 以下为同日早前的口径修正史（结论仍有效，保留过程）：
  - 注：v9 站距 0.493 在已装机角色实测区间 0.50–0.98（中位 0.71）下限附近；站距门 0.65–0.80 未改。诊断图 `art/fighters/ultraman-king/stage1/diagnostics/photo-v13-gates-20261110.png`（SHA `c6c2c18b…`）与 v8–v12 诊断均在档；`stage1/idle/photo` 为空。未安装、未启动 Godot、未提交、无录屏。
  - **口径自查（2026-11-10，推翻上面两条的“门限自洽”）**：0.2034 不是项目规则，是我上一轮自己派生的数，而且两边口径不同。它取 `identity-anchor.json` 的 `head_height_ratio` 0.1883（定义＝12%–50% 区间**最窄行**→头顶，该文件自己注明“头冠会让数值偏小，仅供报告参考”），而所有照片候选一律按**冠顶→白须底**测量。窄行落在颈部/领口收窄处，比白须底高 6 px（图鉴）/15 px（ref-04），同一张图两种口径差 7–14%。项目 `本手册第 6 节` 的 ±8% 原文是**头宽/站高**，不是头高；`AGENTS.md` 只要求“核实际头身比例”。同口径重算（冠顶→白须底）：图鉴 49/223=**0.2197**、ref-04 官方正面 208/1073=**0.1938**（−11.8%）、ref-03 真实侧视 213/961=**0.2216**（+0.9%）；头宽侧未受影响（图鉴 29/223=0.1300、ref-04 139/1073=0.1295，−0.4%）。最直接的证据：把图鉴原图本身当候选、按候选用法测是 0.2197 > 0.2034，**原图会被自己的门判死**。**修正门 = 0.2021–0.2373**（0.2197 两侧各 ±8%；只设上限会放过缩头），倍数仍是项目 ±8%，不是放宽。
  - **冠形判据也错了**：原判据“紧凑银高冠带纵向脊”取自 ref-04 **正面**轮廓；真实 90° 侧面上奥王冠是**后掠刃 + 后端小球 + 刃下纵向肋**，ref-02（真实手办实拍侧视）与 ref-03（官方软胶侧视）两个独立来源一致。v10/v12/v13 被判“后弯长刃 fail”属误判。侧面改按 ref-02/ref-03 核，正面“紧凑高冠”不得当侧视判据。诊断 `stage1/diagnostics/crown-side-vs-front-20261110.png`、`head-metric-definition-audit-20261110.png`。
  - **按修正口径重评 6 张**：v10 头 0.2127 过但鞋底 2.52 原生px/辉光 16,383/胸腹 3/4 不过；v11 头 0.278 不过；v12 头 0.2224 过但鞋底 1.58 不过；v13 头 0.2365 过（余量仅 0.34%）、站距 0.755、鞋底 0.18、侧视、真 Alpha 全过，**唯一不过项是主体外辉光 36,868 px**。v13 原图已按规则删除，不回溯签收；按修正口径重出一张，见下条。
  - **辉光门口径也查了（同日第三起口径事故）**：同一项“主体外辉光”在 v12/v13/v14/v15 四次记录里结论相反——v12 记 pass、v13 记 36,868 px fail、v14/v15 按 `alpha>0` 记 33,191/35,186 fail，而同一条记录又写明“主体+3px 外 alpha≥16 为 0”。对 9 个已签源实测：主体外 `alpha>0` 是 9,030–87,536 px（几乎全是 alpha=1 尘点，拿它当门会判死全部已签源）；`alpha≥16` 照片源 0–1、像素源 17–60；`alpha≥200` 全 0。定门写回 `AGENTS.md`：主体外 alpha≥16 ≤100 px、alpha≥200 = 0、alpha 1–15 尘点只登记不计入。**只改口径不回溯**：v14 鞋底 1.10 原生px、v15 站距 0.6249 仍不过，卡点仍是站距与鞋底同线，不是辉光。诊断 `stage1/diagnostics/halo-definition-audit-20261110.png`。

- 奥特之母 stage1（2026-11-10）：**45 帧动作全部落格并 `root_delegated_by_user` 自签**（身份锚 idle-01；walk_forward 4、walk_back 4、dash_start 2、dash 4、takeoff 2、air_rise 1、air_fall 1、land 2、light1 3、light2 3、light3 4、heavy 4、hit 2、block 1、down 2、getup 2、win 2、ko 2），另有备选待机 `idle-candidate-01`（站距 0.5649，不属动作集）。全部 192×192、根点 [96,184]、脚底 183、同一 32 色板、二值 Alpha、严格 4×；独立脚本重读 47 个 PNG 复检硬门 **0 例外**，全帧联系表 `art/fighters/mother-of-ultra/stage1/cells/review-all-47-2026-11-10.png`（3180×2508，SHA `11cf3f96…`，无阻塞槽；落格前的 46 格红槽表已删）。各动作组均齐，`heavy-00` 起手已解卡（见下条）。
  - `air_fall-00` 的刹车依据**已作废**：三次“冠顶→眼 21/19/28 超门”复算逐值吻合，但那是“眼行 − 整帧 Alpha 最高行”；下落姿势把红披风甩到头顶以上，最高行是披风不是头。按锚同口径（眼列 ±26 px 内、排除红披风取冠顶）重测 16/16/17，三张全部 ≤18。三张原图已删不可追回，须重出一次再判。
  - `air_fall-00` 已按修正口径**重出并落格签署**（MCP `image-65174-1158`，实收 1024×1536，源 SHA `040badf4…8abcf1`，第一张即过、未用第二种修法）：原生格 bbox [47,14,134,174]、32 色、二值 Alpha、单连通 5,865 px；**冠顶→眼 17（门 ≤18）、眼行头壳 29（门 ≤30）**；旧口径在同一帧上仍会量出 21，证实是量法而非画法；披风高过头顶 4 px 属下落相正确画法，保留。
  - `heavy-00` 不受此缺陷影响：站姿起手、披风在身后低于头顶，按正确面板复算 19/19/19、头壳 31/31/31 与记录一致，**旧三次拒收是真的**。
  - `heavy-00` 已按换工序解卡并落格自签：改用**锚派生像素比例导引**（身份锚最近邻 9.396×=1447/154，按锚 raw 占位居中裁 1024×1536，洋红标眼行/冠顶行/头部列带、青色标头壳缘，仅此一张参考），MCP `image-65174-1163`，源 SHA `b846888a…f924`；落格后原生 bbox [47,43,139,183]、32 色、二值 Alpha、单连通 5,461 px、脚底 183；**冠顶→眼 16（门 ≤18）、眼行头壳 27（门 ≤30）**，cell SHA `f0f5a8fc…89f2`。导引 v1 按画面占比缩身（落格高 130/头壳 23）已拒收删除；heavy 组 4/4。
  - 规则写回 `AGENTS.md` 与 `本手册第 6 节`：动作帧冠顶只取头部列带，不得用整帧 Alpha 最高行。诊断 `art/fighters/mother-of-ultra/stage1/diagnostic/air_fall00-landmark-audit-2026-11-10.png`。
- 阿斯特拉 stage1 最小集（2026-11-10）：**46 帧动作**（原 44 + 本轮解卡 2）+ 1 身份锚全部落格并 `root_delegated_by_user` 自签。我独立复检 46 张原生格：192×192、二值 Alpha、≤32 色、帧 SHA 与记录一致、非技能帧单连通，0 例外；技能帧多连通 7 张（light1-01/02、light2-01/02、light3-01/02/03，最多 27 块）按“只判人物主体”成立。**`dash-03`、`getup-01` 已解卡**：先核姿态证明不是遮挡（两帧均严格右侧视、黄眼 11 px、亮银头完整、相邻 dash-02/getup-00 同角度均露灯 3–4 px），判定为模型漏画；第三种工序＝身份锚 192 画布最近邻 8× 后居中裁 1024×1536 作唯一参考（绿额灯在输入里 8×24，SHA `0befa803…`，验收后删除只留 SHA），提示词点名“绿额灯大小与参考完全一致”。两帧各一次即过：dash-03 绿 2/黄 11/蓝 3、亮银头 21×24、cell SHA `4d355977…`；getup-01 绿 3/黄 11/蓝 2、亮银头 23×24、cell SHA `d3017021…`。`on_brake` 已清空，新增 `batch-05`（SHA `60a85174…`），全套联系表重出 47 格（2374×3336，SHA `3689afed…`）。已知保留：dash-03 站高 118 比 dash-02 的 147 低 29 px，是前腿深屈、上身前俯的压缩相（头→胸灯 42 对锚 44，人物未缩小），按姿态记录；dash-03 头 21×24 略窄、getup-01 蓝胸灯 2 px 均已加标记、未局部重涂。以下为原 44 帧记录。统一源像素比例 `154/1231=0.125102`，不逐帧缩放；192×192、二值 Alpha、29–32 色、沿用锚冻结 32 色。分批 idle/walk/dash_start 11、dash/takeoff/air/land 9、light1–3/heavy 14、hit/block/down/getup/win/ko 10。接地相最低点 183，腾空相逐帧登记抬升（dash-start-01 8、dash-00 6、dash-01 4、takeoff-01 10、air-rise-00 24、air-fall-00 16）。非技能帧单连通；技能帧只判人物主体，脱手光束/颗粒为允许附加块（light3-03 最多 24 块），光束末列 Alpha 为 0，两帧触边已拒收重出。头口径固定亮银（max>130）24–27 高、≤25 宽，接受帧落 22–25 宽、24–27 高。**原刹车已解除**：`dash-03`、`getup-01` 经第三种工序解卡（见本节开头），`on_brake` 现为空。已标不返修：light2-01/win-00 绿 1 px、down-01/ko-00/ko-01 头横置贴地投影压缩、win-01 总高 159。全套联系表已重出为 47 格 `art/fighters/astra/stage1/actions/review/astra-stage1-actions-all.png`（2374×3336，SHA `3689afed…`）；本轮接触表 `art/fighters/astra/stage1/actions/review/batch-05-dash03-getup01-2026-11-10.png`（1968×814，SHA `6fc2e71a…`）。未安装、未启动 Godot、未提交、无录屏；双侧朝向与 720/1080 未验。

- 赛罗动作集（2026-11-10）：矩阵动作已补齐 **315 帧 / 78 组**，第八批拆投与被投 19 帧、第九批转身/后撤/闪避/眩晕/防御硬直/破防 28 帧均落格并 `root_delegated_by_user` 自签。机器门：256×256、冻结 32 色、二值 Alpha、`cropped_pixels=0`、接地 247 / 腾空 225；非技能帧单连通，技能帧多连通块（light1/2/3、air_special 共 8 帧）按“只判人物主体”规则成立。三槽必杀已核：light1=Wide Zero Shot（右前臂宽蓝束）、light2=Emerium Slash（额灯细绿束）、light3=Zero Slugger（拔镖掷出实体飞行刃），部位/颜色/形态不同，不是同束改粗细；air_special 3 帧腾空发射。**内容缺口**：`content/fighters/ultraman-zero/` 只有 `catalogue_profile.json`，无 MOVES.md、`moves/*.json`、`content/combat/skill_library.json` 条目，专属技 command_40–43 无可核实依据，未生成、未编造。拒收候选已改为覆盖前先记完整 SHA（第八批 2 个、第九批 1 个）。未安装、未启动 Godot、未提交、无录屏；720/1080、实速、声音、实机未验。
  - **内容数据已补（2026-11-10，仅数据、未接运行时）**：新增 `content/fighters/ultraman-zero/` 的 `MOVES.md`、`command_table.json`（40 条指令 / 37 招）、`moves/*.json`（39 个）、`SOUNDS.md`、`production_plan.json`（104 格，`integrated` 全部 false），以及批次说明 `tools/rebuild/ultraman-zero/CONTENT.md`；自检 PROBLEMS 0。三槽仍按 light1/2/3 区分（宽蓝束/额灯绿细束/实体飞镖），command_45/46 记为同一终结的 P 与 □+△ 等效入口。**角色仍不能加载**：缺 `definition.json` 与 `state_frames.json`，本批明确不生成图片、不合成或绑定声音、不改 `content/audio`、不改 `art/`、不安装、未启动 Godot、未提交、无录屏。另：`art/fighters/ultraman-zero/stage1/cells.json` 里的 `content_gaps` 因此已过时，本轮未改（art 目录不在该批授权内），下次动该文件时一并更正。

- 四角色音频（2026-11-10）：首轮 4 BGM 循环、4 战吼、16 事件按用户委托自动批准接入运行时（`runtime_approved=true`，`runtime_approval_basis=user_delegated_auto_approve_2026-11-10`；`listening_reviewed=false`，未听审）。4 条 30s 循环已转 48kHz 双声道 Vorbis 并登记到 `battle_music.json`；事件/战吼登记到 `runtime.json` 的 `voices`；导入清单在 `reports/audio-runtime-import-20261110.md`。`.import` 侧车已就位；20 条直连记录显式 `runtime_status=installed`，12 条转载/loop 记录标 `pending_install`。2026-11-10 锁内 `audio_playback`、`phase3_fx_audio` 均 PASS，未实机试听。

- 体力经济：基础拳脚/投技/追击/起身免费，远程/必杀/方向技/闪避/格挡付费，不足时不启动并提示；格挡费=伤害/4，30 tick 恢复延迟。捕获测试同步改为硬门槛断言。

- 动画帧尺度：新增逐帧尺度检查并修复 8 名角色 11 个 clip 共 28 帧整帧放大（含杰克长矛投掷 `motion_214`）；脚底锚点不变、帧外零改动，导入与三项定向回归通过。剩余 103 clip / 111 帧确定突变、606 clip / 1124 帧待人工复核。[验证回执](verification/README.md)

- 扫腿早回收新源已保存：1536×1024真RGBA，灰底合成证大片光晕为透明区隐藏RGB，非实体FX；身份/腿层及前伸远拳成立，不是晚相重复。远踝03→早→晚为807→358→302源px，仍偏晚；约1.10整图尺度解释可行但不消除主要足路跨度。仅候选，不安装、不自动再生。[完整来源与同尺审阅](../art/fighters/ultraman-arc__luna/stage2/sweep-early-recovery-session-candidate-20261105/review.md)

- 二拳→扫腿独立RAM探针：104语义/8逻辑/16主游戏headless通过；gap75/90三次命中195且受方未恢复，gap100二拳空后扫腿虽总130但有4帧中立，非真连。原v3内层事件盲点保留，外置逐tickHP/事件门拒绝六类变造并强制成功后签总回执。32组图形交验；旧扫腿回弹红灯、新回收图不混、不安装。[技术连接与失败记录](verification/luna-crouch-sweep-chain-session-resume.json)

- 扫腿新回收原源已保存：身份/真Alpha/近层承重与远层屈膝成立，接受晚回收静态候选；远鞋相对足底高差与06仅0.38逻辑px，不能据此判悬空。远踝相对支撑脚102.3→38.3→56.9，仍有大幅内收再外展；旧端点比例/根点漂移未过。根看同尺后已备03→新相早回收整相brief（model→03→晚回收），固定近层支撑，远脚在两端之间；不重复帧掩盖，不安装。[早回收完整方案](../art/fighters/ultraman-arc__luna/stage2/sweep-early-recovery-keyframe-brief-20261105-v1/brief.json)[原源与审查](../art/fighters/ultraman-arc__luna/stage2/sweep-recovery-session-candidate-20261105/review.md)

- 扫腿尾段源复核：03扫击与06低架的近/远腿层次可作端点；旧04变层落脚、05重新伸腿回弹仍未解决，12旧源SHA一致且无新增替代。已备单张低位屈膝回收整相brief（本人定稿→03→06），不把未知解剖左右当确定、不发明撑地手；一张尚不保证整招修复，未生成。二拳→扫腿尚缺技术连接，正独立RAM核查，正式装甲仍关。[最小回收相与来源](../art/fighters/ultraman-arc__luna/stage2/sweep-recovery-keyframe-brief-20261105-v1/brief.json)

- 蹲一二拳RAM已复用右拳v2并按最新core验证：原左3/3/12、右3/7/8与cancel保持；8逻辑、114输入语义及16主游戏回放通过。命中确认才取消，gap75两拳130；gap100二拳够不到仅65。格挡/空挥晚按可收招后缓存起右拳，非取消。新增32有效图形组/368原生PNG、16对180tick通过；窗口门一次暂态失败保留，只续6组。近/远拳可辨，换相头肩/足缘、共同取景和旧受方高硬直仍待实速，不安装。[二连候选与准确边界](verification/luna-crouch-chain-session-resume.json)、[图形终态与失败记录](verification/luna-crouch-chain-session-graphical-review.json)

- overhead恢复限定路径图形已完成：八组64原生PNG、四对180tick回放通过；双向720/1080完整56→57→58–61均低姿，tick57仍原crouch0、58仍guard0，不跳过逻辑中间tick。首次站入蹲/松防及旧低防恢复不回退；声音只程序键时点对照，无听感/实速验收。普通蹲较高资产另保留，两新blockstun仍RAM未安装。[准确图形回执](verification/hit-crouch-guard-recovery-graphical-review.json)

- overhead蹲姿受击恢复已采用保持语义方案：原hit→crouch→guard及state_tick/指令不变，限定上下文同步本人已有低防保持图与hurtboxes，原frame其它字段/推挤/声音入态键保留。52例红绿、7800tick非姿态字段一致与旧拒新接通过，原40例低防恢复不回退。v3八逻辑/十六headless通过，必要八组图形待核；新素材未安装，非纯显示且未验听感。[根因、被否方案及修复证据](verification/hit-crouch-guard-recovery-audit.json)

- 杰顿v2实际图形收尾：原32组自然完成，176原生PNG与16对180tick回放通过；720/1080双向low40→41、mid39→40直接低蹲保持，旧恢复站高闪回已在此限定路径消除。overhead受击后旧起架仍高，后震/脚缘与无实速/音频限制保留；正式core已修、新两图仍RAM未安装。环境重连未清锁/重启，唯一原批自然退出。[v2准确图形回执](verification/zetton-crouch-block-session-graphical-v2-review.json)

- 已最小修复低蹲受挡后持续下防重新起架：仅恢复进入本人crouch_guard末保持行，初次入架/松键不改；40例红绿、旧内容拒载/新录接受及既有回归通过。规则指纹新增版本，旧格式6录像不混跑新语义。候选v2八逻辑/十六主游戏headless通过，图形待核；overhead后的独立旧入架路径未动，新素材仍未安装。[恢复修复](verification/crouch-guard-resume-repair.json)、[v2阶段](verification/zetton-crouch-block-session-resume.json)

- 杰顿两相RAM图形32组/176原生PNG、16对180tick回放技术通过；硬直内新两相低髋成立，但持续下恢复时旧crouch_guard重新播放站高首相3tick，整回防链不通过。overhead后旧入架亦保留；有意松蹲站防正确。大后震/脚缘及未验实速音频仍在，未安装。下一步仅针对低蹲受挡恢复修逻辑，旧失败不覆盖。[实际图形与失败边界](verification/zetton-crouch-block-session-graphical-review.json)

- 杰顿低蹲硬直两整源已按共同尺度注册为RAM候选：仅新Alpha44/42条受击框与同名clip替换，原4/6比例及正式规则不变。八例180tick真实低/中防、overhead受击、松蹲双向独立回放通过；含hitstop实测两相8/7tick。正式主游戏16组headless及8对独立回放亦通过，32组图形已交验；大幅后震、近乎回正及后脚缘差保留，不安装。[阶段证据](verification/zetton-crouch-block-session-resume.json)

- 杰顿低蹲硬直第二相回缓方向成立：同尺脸灯由后震x99.64回x145.84，几乎回到原保持x145.27而非半程；两相低髋/深折支撑保留，原后脚缘差仍在。可仅RAM试排原4/6节拍，大幅后震与回正速度需实际画面，不安装。原字节/完整prompt与未知元数据已存。[第二相与试排边界](../art/fighters/zetton/stage3/crouch-block-posture-20261105/phase-01-review.json)

- 杰顿低蹲硬直v2形成明确上身后震，低髋/深折腿保留，透明背景明显改善；同尺脸灯左移约45.6px、上移9.6px，超过小幅目标，尚须两相及4/6tick实际评估。单独脚区核证前脚接近、后缘约8px差，已纠正以总bbox误推站距。未安装，第二回缓相仅brief。[完整来源与同尺证据](../art/fighters/zetton/stage3/crouch-block-posture-20261105/phase-00-v2-review.json)

- 杰顿低蹲硬直首候选已保存：本人低蹲完整，但姿态仍接近保持，未接受独立受挡动作。灰污背景是低alpha噪声（上方最大24），Alpha128诊断只剩单人物，可离线清理而非仅据背景重生成；原源未处理未安装，model/high/usage/费用未知。[原源、提示词与透明诊断](../art/fighters/zetton/stage3/crouch-block-posture-20261105/phase-00-review.json)

- 杰顿蹲防硬直站高已定位为实际源姿态缺口：模拟与表现均正确选crouch_blockstun，同动作raw/旧processed/正式两相本来高弓步，无可换回低蹲源；未改正确core或用蹲防保持冒充。新增8组正式低拳/双受方/双向/松蹲独立回放，状态和实际动画选择通过。完整低蹲参考及两相brief已备，未生成、未修复画面。[证据与修复依赖](verification/zetton-crouch-block-posture-review.json)

- 蹲左拳三槽RAM按原3/3/12试排：仅两独立图、65伤/30体力low和原二拳取消字段保留；8逻辑与16主游戏原输入/独立回放通过，站防受击、蹲防格挡、落空均双向一致。新增720/1080双向32组/256原生PNG技术核验、16对180tick五字段一致，16组original逐相静审完成；原批自然结束，无重跑。头肩/前脚换相、接触特效遮挡与受方蹲防硬直较高站姿保留；仅第一拳，二拳/站转蹲未验，无实速/音频/录屏验收，不安装。[运行候选](verification/luna-crouch-light-session-resume.json)、[图形终态与限制](verification/luna-crouch-light-session-graphical-review.json)

- 蹲左拳v3近肩跨胸出拳、远拳护颏已成立；近腕盘完整，远腕甲遮挡不能判缺失。实际蹲架→v3→蹲架同尺重复通过，接触头肩约低14px、前踝约收5.7px及直臂保留实速待核，无静态硬阻塞；可继续RAM试排，未宣称全招或安装。[第三版与候选边界](verification/luna-crouch-light-contact-v3-candidate-review.json)

- 蹲左拳第二版仍近侧护颏、远侧出拳，未解决肩臂归属；原源/实际prompt和四端点同尺对照已存，停止双参考盲重试。找到本人既有近侧跨胸整帧可限作第三拓扑参考，保留其原生Alpha拒收/站姿长拳限制；不改名掩盖左拳缺口、不安装。[第二版核验与可行策略](verification/luna-crouch-light-contact-v2-candidate-review.json)

- 蹲左拳新接触原源已保存：真Alpha、双脚低蹲及前伸拳成立，但近侧臂仍护胸，出拳沿远侧肩臂链；按原近侧=左约定实际打反，不通过左拳。三端点同胫尺保留足位/头身差与测点误差，已给整身纠正肩臂归属方案，未运行安装。[原源与核验](verification/luna-crouch-light-contact-candidate-review.json)

- crouch_light已完成单张完整接触brief：以本人定稿＋现用双脚蹲架为最小两图，近侧解剖左拳短促平出、右拳护架；旧低跪/站高护拳不作正例。腰腹目标明确为本轮设计解释，旧链接续仍待；未生成。[可复用brief与参考](../art/fighters/ultraman-arc__luna/stage2/crouch-light-keyframe-brief-20261105-v1/brief.json)

- crush之后去重核查：tackle已有八相共同尺度及历史输入/双向图形回执，31项引用SHA相符，本轮不重复生产或运行。下一明确素材缺口是crouch_light生效相仍护架、未画腰线左短拳；crouch_light2亦缺右拳前探。八原源SHA保持，只读提出最小完整接触相方向，未生成。[下一真实缺口](verification/luna-s2-next-gap-after-crush.json)

- crush七槽已进入主游戏RAM试排：原12/8/15、130伤/30体力不可防，远拳12×11真实Alpha框；逻辑六例与headless十二组通过，六对180tick原输入/独立回放五字段一致，GUARD按原规则同受130伤。正式资源未动；图形24组/384原生PNG及12对180tick通过，12original逐相静审完成。白闪遮接点、起收姿态/共同镜头影响保留，实速/音频/整招美术未验、不安装。[技术回执](verification/luna-crush-session-resume.json)、[图形终态与限制](verification/luna-crush-session-graphical-review.json)

- crush低位随势已保存并核同尺：双拳再下约8–11px、肘再下约9px，脚位差在标点误差内，未靠整身缩水。已组成七槽/五独立姿态候选，明确复用高护拳作屈肘回收、不强插旧06；独立审阅未见阻止RAM试排的硬几何矛盾。备原12/8/15时序建议，起手/8tick接触/回护实速仍待，未运行安装。[随势与完整候选](verification/luna-crush-followthrough-candidate-review.json)

- crush下降候选已保存并作六端点同尺比较：确有高护双拳外观，但近前臂−77→−18→+36.5度顺转、后段拳腕未再前推，存在可解释下降路径，保留试排而非仅凭护拳读法废图。肩肘提前到接触态、起手及低位随势仍待，未签桥接/整招；原五帧字节保持，不安装。[实际提示词与路径复核](verification/luna-crush-descent-candidate-review.json)

- crush新增双拳下砸接触原源已保存：两拳确实降至肩下胸腹前方、双臂连通。五端点完整整图同左后胫尺重复构建通过，举顶05→新接触前后踝差约2.4/0.8逻辑像素，支持足位相容，不以强制锚证明无滑步。最小待补是约80–96像素拳路的下降中相，旧06只护架不能冒充随势；未运行/安装，保留真实Alpha和未知生成元数据。[来源与候选整合](verification/luna-crush-contact-candidate-review.json)

- 月亮S2下项已按原计划核到crush双臂重砸（O/CRUSH）：旧九相所谓04/05接触仍双拳举顶，06已回护架，缺真正前下砸。已设计一张完整接触相，最小参考为本人定稿+旧05举顶/足位，明确禁复制高举和宽拳距；无生成/收费/运行/安装，spin仍待实速。[旧源核验](verification/luna-crush-existing-source-review.json)、[精确brief](../art/fighters/ultraman-arc__luna/stage2/crush-keyframe-brief-20261105-v1/brief.json)

- 回旋十槽已进入主游戏RAM候选：全相同权重头代理/支撑胫双尺整图试排，低收→左回摆02→实际idle直连；沿原4K 9/4/15共28tick、仅脚背20×16、100伤/30体力。逻辑六例、headless十二组及720/1080双向24有效图形组/480原生PNG通过，12对180tick原输入/独立回放一致；一例tick0稳定门超时保留并原门限续跑补齐。逐相静审保留跨身足路/鞋向/共同镜头影响，无实速/声音/真人键盘验收，单相idle亦仅对照，不安装。[运行候选与限制](verification/luna-spin-heavy-session-resume.json)

- 尾段第二版已补到有效左侧空中回摆位置：前层攻击腿左下伸、鞋离支撑底93源像素；同尺到idle脚尖约横移−2.6/下降16.3逻辑像素，值得优先直连试排，不强插旧backstep00制造反向脚路。拓扑相容不等于遮挡髋唯一证明，跨身时序/脚转向/尺度仍待，未安装。[两版差异与同尺核验](verification/luna-spin-heavy-tail-air2-candidate-review.json)

- 新尾段候选原源已保存：实际是攻击腿向右前下展开、鞋仍在承重脚右侧，未补指定向左回摆；同尺四相脚尖位置与目视相符，不因关节点误差机械否决。可保留下降/护架回位备选，但不插入冒充左回摆、不为用上它延长链，未安装。[来源与用途差异](verification/luna-spin-heavy-tail-air-candidate-review.json)

- 尾段新增可保留的旧源：backstep00近层腿左落脚、后层右承重，比当前landing更相容实际idle；三相同尺下到idle约18px差不作机械失败门。Alpha只证轮廓、不证髋或承重；最低待核是低收攻击腿空中回摆到原落点，已给一张完整过渡设计，未生成/安装。[事实与不确定分层](verification/luna-spin-heavy-tail-tracking-v7.json)

- 含新起手的十槽全现源已用同胫尺/同头部代理尺双方案整图评估：起手与中段有用，但两尺仍不能共同确认头胸/腿长；低收→落脚的原后层承重腿归属及回idle足路未锁定。另一landing映射可减小髋差，旧大位移不是必然缺陷。最小障碍是同腿落脚链和可靠运行尺度，故未虚设时序跑回放/安装。[全链评估](verification/luna-spin-heavy-full-evaluation-v6.json)

- 回旋卸重起手已保存并作三相同尺诊断：左侧低屈腿/右鞋承重与idle、蓄势骨盆拓扑相容，强化右鞋承重假设；髋/膝提供中间路径，攻击脚源离地109px。两臂已近蓄势终点，实际idle尺度与抬臂变化、后段腿映射仍待。实际生成参考为clean-model而非idle，未运行或安装。[完整来源与核验](verification/luna-spin-heavy-entry-candidate-review.json)

- 回旋腿映射/尺度复核：idle画面左腿与蓄势抬腿均在骨盆前层，支持另一种“idle右鞋承重”映射，尚不唯一；此前40/47位移只适用v3假设，不是无条件动作缺陷。头部代理尺与腿尺亦不一致。定向查turn/步行/backstep未有可直接采用桥接；只保留卸重低收设计草案，腿映射未定前不生成。[复核及既有源](verification/luna-spin-heavy-existing-bridge-review.json)

- 回旋全现源九槽诊断已建立（七动作相+实际idle首尾）：旧四相不变，中段展开/回收可读；同前掌锚下入蓄髋约移40、落地回idle髋约47/脚尖约42逻辑像素，缺起手移重和回宽站路径。低收/着地体量与腿遮挡仍待交叉核，运行前置门未满足，未虚设时序或跑Godot/安装。[统一配方与具体缺口](verification/luna-spin-heavy-chain-geometry-review.json)

- 回旋前掌初落地候选已保存：两鞋底差8源像素、右侧鞋跟抬起可读；下收→着地骨盆遮挡次序改变，尚不能严格签解剖腿锁定，也无足够证据直接判换腿。已实看实际idle原源，窄站→宽站及前拳回位仍待同尺核，未安装。[来源与接续审阅](verification/luna-spin-heavy-landing-candidate-review.json)

- 回旋下收整帧已保存：同腿拓扑未见交换，悬空腿屈膝下收、支撑脚跟接近放平，躯干/护拳趋向回架；攻击鞋仍比支撑鞋底高202源像素，不是落脚完成。原画布前掌位置变化需同尺核，不直接当游戏滑步。真实Alpha有触边低透明噪点，未运行或安装。[原源与审阅](verification/luna-spin-heavy-recover-low-candidate-review.json)

- 回旋踢后初收腿原源已保存：与接触版同尺寸下前掌比较锚约差−1.9源像素/高度不变，膝屈曲及踢脚内收可辨、双腿拓扑未见交换。脚尖回翘可属收踝，不单独判失败；胸肩仍近接触角，不能签继续转髋随势。真实Alpha有边噪，无新增大背甲；还缺下收落脚/回架，全链未运行或安装。[来源与审阅](verification/luna-spin-heavy-follow-candidate-review.json)

- 回旋转髋中相原源与四相同尺诊断已保存：攻击膝投影约121→160→189→195，新相确补跨身收膝；髋被遮挡，改用可见支撑胫骨交叉尺，不猜髋点。三/四相重复构建及旧帧保持通过；真实左右/时序与接触后随势回架仍待，不安装。[中相及同尺证据](verification/luna-spin-heavy-turn-mid-candidate-review.json)

- 回旋最小过中线brief已准备：右膝随右髋经身体前方/朝镜头转过，暂呈合理透视缩短，左前掌持续抬跟支撑；只补蓄势→展开含糊路径，不假称现有两端已证明该弧线。三项明确图像参考，不展示未知大背甲；未生成。[转髋中相brief](../art/fighters/ultraman-arc__luna/stage2/spin-heavy-keyframe-brief-20261105-v1/turn-through-brief.json)

- 回旋三关键相已按支撑股胫投影总长作统一整图尺度/前掌比较锚，提供可移植RAM几何配方，重复构建逐像素一致且原源不变。三相体量未见明显失配，脚上翘→下压可解释为绷踝，不单据此否决；但蓄势→展开髋膝路径及接触后随势/回架未成立，故未启动整招输入回放或安装。[几何复核与误差](verification/luna-spin-heavy-geometry-review.json)

- 回旋展开中相已保存：腰高大腿与屈膝分段可辨、支撑仍抬跟；但攻击脚尖上翘，与接触版脚尖下压形成新踝脚边界。胸肩较接触版接近，蓄势→展开转髋/骨长和同支撑点需统一尺度核，尚非连续整招，不安装。[展开相审阅](verification/luna-spin-heavy-unfold-candidate-review.json)

- 回旋接触关键候选已保存：腰高横展腿、绷脚尖向下、支撑脚抬跟可辨，大片外围光晕较蓄势减少；胸面比蓄势第三版展开且踢腿角跨度大，仍不能直连判回旋连续。原图尺寸不同须按骨长统一整图尺度，低Alpha边噪/解剖左右/后续随势回架待核，未安装。[接触相审阅](verification/luna-spin-heavy-contact-candidate-review.json)

- 回旋下一接触关键相brief已准备：右髋带动右腿腰高横扫、脚背/胫前接触，左前掌抬跟转轴持续；以本人定稿和第三版蓄腿为参考，排除旧侧踹。下一张关键图不等于可直接相邻播放，展开中相与背面随势仍待；必须露大面积背甲时参考不足即阻碍。未生成/收费/运行。[接触相brief](../art/fighters/ultraman-arc__luna/stage2/spin-heavy-keyframe-brief-20261105-v1/contact-brief.json)

- 回旋蓄腿第三版已保留：支撑脚跟明确高于前掌、胸甲缩为斜面，转体比前两版清楚；保留为较优蓄势候选，不再沿用前两版平脚结论。低Alpha光晕/触边、统一骨尺及全链左右腿跟踪仍待核，未配准/安装。[逐版比较](verification/luna-spin-heavy-session-candidates-review.json)

- 月亮4K回旋重击两版内置生成候选已保存，月亮身份、双拳双腿和整身可辨；支撑鞋仍近水平，未明确呈现前掌转轴/抬跟，单图不足证明肩髋真实回旋。真实Alpha存在但低透明噪点触边、外围可见光晕，均不签关键相合格；未配准、未运行、未安装。[两版逐项审阅](verification/luna-spin-heavy-session-candidates-review.json)

- 月亮下一项按原计划为4K回旋重击；已完成一张“转体收右膝”完整生成brief及参考SHA核验，排除旧侧踢/直腿骨架作为正确姿势参考。仅准备文字，未生成/收费/运行；背面随势参考与完整回旋链仍缺。[brief](../art/fighters/ultraman-arc__luna/stage2/spin-heavy-keyframe-brief-20261105-v1/brief.json)

- 月亮升击七相RAM候选：共同159/1254尺度、真实6K唯一12×12拳框/75伤/体力30；720/1080双向命中、格挡、落空的24组432原生PNG技术核验完成，12对180tick原输入/独立回放五字段一致。12原输入逐相静帧已审，入蓄头肩下降及回架腕甲转面保留为实速待判，不据静帧强制补相，也不签整招顺滑。命中白闪、站防与头形细差保留；无录屏、声音或真人键盘验收，不安装/不开放。[逻辑](verification/luna-launcher-session-resume.json)、[图形与边界](verification/luna-launcher-session-graphical-review.json)、[独立复核](verification/luna-launcher-session-evidence-recheck.json)

- 升击新增回收中相：同右闭拳由03高位降至上胸、双圆腕甲可辨，双鞋保持近似窄站；进入01仍需全身下沉与远腕遮挡变化，不将五张关键源当完整招式或默认以01替代正式护架。未配准安装，来源/Alpha与未知元数据据实保存。[回收相审阅](verification/luna-launcher-return-mid-candidate-review.json)

- 升击新增胸前渐伸中相：同右闭拳由腹侧向上至胸前、双圆腕甲可辨，可补01→02拳路；头冠/伸膝已接近02，全身分段与支撑脚、旧起收招仍须核，未宣布实速或整招通过。保留本会话原字节及未知model/high/usage。[来源与实测](verification/luna-launcher-rise-mid-candidate-review.json)

- 新增升击01蓄拳/03高位回收整帧候选：双闭拳蓄腹→同右臂上挑→高位回收方向可读，但01远腕圆面遮挡、近鞋底约9源像素漂移、缺渐伸及旧起收招接续仍在；真实alpha有低透明边缘噪点，未配准/安装/运行验证。保存原字节、提示词及未知model/high/usage/费用。[两相逐项审阅](verification/luna-launcher-neighbor-candidates-review.json)

- 月亮升击新单相：按用户本次要求使用本会话内置生图候选，原字节与提示词已保存；真实向上弯肘拳和本人形态可辨，但前鞋内收、旧01/03不能接续，低alpha噪点触边，仍未注册或安装。model/high/usage/费用均未提供，不冒称项目客户端来源；需完整蓄拳与回收链后再主游戏核验。[单帧来源、alpha及缺口](verification/luna-launcher-session-candidate-review.json)

- 完整需求依赖复核：按18c5305d对核心/输入回放/名册/哥莫拉/八装甲/三槽武器/声音/环境/交付逐类核对，未发现另一项可凭现有合格资源直接安装的关键功能，未制造新工具或改动。明确原生2P、目标引擎、本人声音与原速观察的不同依赖；哥莫拉最新候选沿既有流程收尾，不把工具缺失判动作失败。见下文“完整需求逐类依赖复核”

- 哥莫拉背掀第三版中间链：仅内存候选raw27换新完整相、raw28移第二版，捕获/费用/raw32后离背/raw68唯一490伤保持；双向命中、拆投1–4及落空12带原输入/format6回放与生产反馈审计通过。双向720/1080正常及诊断8组372原生PNG技术核验，26张选样已实看，raw26–29正常与诊断逐像素相同，中间双膝后摆分段可辨；不签1tick原速顺滑，旧首承重/近角等边界保留，仍未安装正式三级。无录屏、听感或真人键盘验收。[逻辑](verification/gomora-midlate-v3-20261105-logic.json)、[正常/诊断图形](verification/gomora-midlate-v3-20261105-graphical.json)、[八带主游戏回放](verification/gomora-midlate-v3-20261105-main-replay.json)。正常及诊断八带各760观察/685模拟tick的独立与format6二次回放通过。

- 回放输入复盘：修复F4播放时训练图标/F1历史停在录制末尾，以及成功加载残留旧上一招/反馈。仅成功装配后清显示、每tick沿实际录像输入更新，坏文件拒绝保留显示；不改模拟或录像格式。既有回放测试同一红绿通过，三带字节不变、逐tick模拟hash保持；5项相关回归及normal关闭通过；720/1080原生1P D/J/K历史清理/重建已验，19图与实际两带输入核对，不冒称精确截图tick或2P验收。[逻辑回执](verification/replay-input-display-review.json)、[实际画面](verification/replay-input-display-graphical.json)

- 屏障反射持续束：修复归属反转后误查新拥有者招式、下一tick清束的问题；初代真实Q→2H反杰克I，双向t43反射、t44回击65、t49原发射招中断撤束。6组150tick真实输入及独立回放通过，4组未反射束/普通火球对照旧hash保持；新增规则指纹，旧录像拒绝。导入及12项相关回归通过，四组720/1080双向48图实际反射/回击可辨；保留束超视口、白闪遮细节与t49撤束仅trace。图形为居中平移夹具，双反射/KO尾迹仅模型。未改素材/长度/寿命/速度或判定。[逻辑回执](verification/projectile-beam-reflection-review.json)、[实际画面](verification/projectile-beam-reflection-graphical.json)

- 旧弹体与新招隔离：默认470/750起点连续两次I，旧火球命中或被防不再吞掉已扣体力的第二发；保留confirmed、原判定与伤害。8组真实输入红绿及独立回放通过，11项相关回归通过；新增规则指纹，真实旧录像8组拒绝。蹲避对照逐tick hash保持，延迟对照connected残留清除会改变hash；无真人键盘、图形/录屏或声音验收。[回执](verification/projectile-move-isolation-review.json)

- 空中击倒弹体方向：补齐先前方向修复遗漏的knockdown空中vx分支。默认起点真实后走、杰顿火球/瞬移、雷德王闪避/投岩及跳跃273tick完整场景复现并修复；7组同输入回放与8相关回归通过，方向规则升2、真实v1录像拒绝。未改招式/素材，未另称图形通过。[回执](verification/projectile-air-knockdown-direction-review.json)

- 2P原生录制疑点：旧整局全零录像不含录制模式，无法判断箭头发生时是否仍在录制。已加入默认关闭、白名单、有界的主游戏被动观察，1017项证明不改输入/模式/hash；720真实两段及Sky对照已确认云桌面逻辑箭头与物理码不匹配，录制开启时亦为零；未改产品输入，默认2P有效物理箭头下非零录播仍未验。[仪器与边界](verification/training-input-audit-logic.json)、[原生辨因回执](verification/training-input-native-diagnosis.json)

- 换人回放加载：先读并验证录像人物，再按该组合创建当前规则模拟严格比指纹；同版本换角色/换边/EX不再假报规则改变，R再战保持录像双方，真实内容变化仍拒绝且不破坏现局。327项主游戏入口与相关回归通过，720/1080真实换赛文后载回初代/杰顿及R保持双方已验，未冒称EX/换边全图形通过；不扩大旧规则兼容。[修前红灯](verification/replay-match-loading-red.json)、[逻辑回执](verification/replay-match-loading-logic.json)、[实际菜单及关闭阶段限制](verification/replay-match-loading-graphical.json)

- 弹体方向：已修杰顿真实火球后瞬移越身导致反向击退/受击朝向及背后来弹误防；8组200tick原输入修前后完全相同，独立回放通过，4组普通未越身末hash保持。相关10项通过，另1项因缺历史contract未执行；全局方向规则指纹更新，旧回放明确拒绝。[证据与限制](verification/projectile-contact-direction-review.json)

- 训练生命周期：F4完整回放结束或播放中，菜单录制/循环现会先成功建立同人物真实训练，保留75tick开场；再战归零陪练游标、停止跨局录制但保留磁带。67项主游戏逻辑检查与训练/UI/关闭回归通过，真实720/1080已观察F4播完切录制恢复训练；2P箭头非零输入未取得，循环/游标及中途切换实机语义未接受；修前只有静态路径证据，不冒称旧版实测。[当前回执](verification/training-lifecycle-review.json)

- 追击中断规则：已修复双方升拳互中后跳键逃离launch硬直；自然收招后的合法追击保留。20组真实输入/独立回放与6项既有回归通过。此次确改全局规则，旧指纹回放明确拒绝；历史候选重跑须重封源码合同，不以旧回执冒称当前版本验证。[修复与证据边界](verification/chase-interrupt-review.json)

- 其他现源可用性：其余六装甲仍仅model；交叉核18正式角色清单后，剑技/八斩/EX等疑似旧缺项实际已装，未找到新的合格未接入整帧。四角色三槽区分及哥莫拉受方缺口仍在，不以重装或FX改名补数。本次是索引/现装核查，不冒称逐张审完历史源。[范围与证据](verification/other-existing-fullframe-availability.json)

- 银河后续现源核查：回旋踢方向、双砸接触、蹲拳回架、冲击换腿及后撤/后走等13项存在明确缺口；原地闪避虽可筛四相，但按支撑鞋测得头胸约48px跳与远鞋12–15px滑移，仍缺过渡，已停止候选。未跑已知失败图形、未新增功能，不重复扫这些源。[可复核原源SHA与缺口](verification/galaxion-following-source-review.json)

- 银河6K升拳：本人七完整相保序统一尺度，02同臂上挑拳面14×12有效，03降臂前伸仅后摇；真实75伤/可防/落空、完整挑空→落地→起身模拟与180tick回放通过。24组432PNG窗口与图形技术门通过，七相和双方顶点/倒地轮廓静帧带限制接受。保留缺渐伸、原腹部蓄力差异、白闪/旧站防/动态缩放；wake只有trace，未验起身动画，银河仍不开放。[源审](verification/galaxion-launcher-source-review.json)、[逻辑](verification/galaxion-launcher-resume.json)、[图形及旧失败](verification/galaxion-launcher-graphical-review.json)

- 银河单远侧直拳：同招完整帧重排“原04护架→00/01/02接触保持→03回护”，小拳框11–12px；真实J扣30体力，命中65、防御0、落空0与独立回放通过。24组264PNG技术全过，132原输入图实看，单远拳静帧带限制接受。没有补渐伸相，原brief近侧左拳和左右交替三连仍未完成；旧站防手位/白闪/长训练板保守缩放保留，银河不开放。[源缺口](verification/galaxion-standing-attack-source-review.json)、[逻辑](verification/galaxion-light1-resume.json)、[图形](verification/galaxion-light1-graphical-review.json)

- 银河S2：已用本人12张完整原源补齐待机／入蹲／保持／起身候选，真实Down两轮与240tick独立回放通过；8组352原生PNG技术全过，125张原输入选样覆盖全部12相，静帧可带观察接受。护拳回环、入蹲相间高度近似与起身头长细差保留，不称实速顺滑；装甲仍关闭。[逻辑与配准](verification/galaxion-crouch-resume.json)、[图形回执](verification/galaxion-crouch-graphical-review.json)

- 镜头/HUD：已按实际容器布局共同取景，保护双方完整Alpha轮廓（含尾巴、整帧武器）及仍持握独立实体，不单独移动人物、不改判定。正式训练/普通对战/二级持岩12组176PNG、原月亮遮脚回归8组152PNG完成双向720/1080核验。原1080左向跳跃顶点的杰顿脚底与底HUD已分离。详见[代码回执](verification/hud-safe-framing-code-review.json)与[主游戏最终回执](verification/hud-framing-main-review.json)。历史三级立绘遮物、候选接线遗漏和门禁失败均保留；不以数值边界代替实际画面。
- 月亮S2：轻击三连、heavy、tackle、sweep、dash_light、dash_heavy、垂直跳、前跳已建立现有整帧候选与真实输入/回放路径，但不是完整装甲完成。逐项历史证据见上方成果索引对应回执，尤其扫腿/飞踢/前跳的视觉缺帧仍未通过。
- 月亮后撤backstep五相已复用现存新03/04修复源，真实双后每次80px、两次触发与回放完成；8组192PNG技术通过，但02抬膝到03宽站仍缺落脚中间整帧，视觉未接受，不算动作完成。[回执](verification/luna-backstep-graphical-review.json)
- 哥莫拉三级背掀：通用root覆盖及显式空接保相机制有逻辑回执，18攻方/6受方现有整帧已离线配准；角臂关系/受方过渡仍缺合格整帧，未正式安装。不能把通用代码或配准数量当作招式完成。
- 已补电脑空中受身、格挡反击、保守两格爆气的真实输入策略，以及训练录制换边方向复现；未以增加无敌/扩大判定强保成功。回执在verification对应computer-*与training-tape-facing文件。


> 收口注：原“获取与运行”历史段与“已完成与未通过的具体动作”重复登记段已删除；现行运行命令只在根 `README.md`，逐项历史证据按上方“当前成果与历史证据索引”与各冻结回执查询，不复制事实。

### 完整需求逐类依赖复核

以18c5305d为本次读取基线，核对原计划、当前消费者及已有验收，不重扫被拒原图、不运行新测试，也不把未验收写成运行失败。本轮没有发现另一项证据充分、可仅靠现有资源直接安装的关键功能，故不额外修改战斗规则或新增辅助工具。

- **核心实战与对局闭环**：现有整数60tick、输入解析、投技/拆投、受身、追击、反制、爆气、形态与KO/再战均有实现和专项证据；上方追击中断、弹体方向/跨招隔离、持续束反射已修。此次静态复核未确认新缺陷，不声称全量无bug。只有出现具体可重现玩家路径才继续改，不能用扩大判定或增加无敌补表面成功。
- **输入、电脑、训练和回放**：Q/E/I 与原搓招共存，重绑/保存/冲突处理已在input/devices与正式设置中；电脑反制策略、训练磁带方向、F4生命周期/换人加载/输入显示已分别修复。仍待有效原生2P物理键环境核非零录带与循环游标；当前云桌面逻辑箭头/物理码不匹配不是产品bug定论，不通过改绑定或注入输入假验收。手柄硬件覆盖也不因路由代码存在而宣称完成。
- **正式名册与全动作矩阵**：按definition的playable/pilot_playable当前18角色可装配，不等于18角所有原剧动作和美术已完成。selection编辑清单是298身份、387形态，其中形态项18个implemented；不能当最终全集总数，coverage仍有作品/身份资料余项。新增角色依赖本人版本依据和完整动作/受击/被投/技能/声音，不把目录或静态模型计成可玩角色；图鉴新增继续暂停。
- **哥莫拉三级背掀**：最新第三版中间链已用现有完整源做12带逻辑与八带主游戏回放、正常/诊断图形，仍是内存候选、未安装。下一步仅沿现有[中晚承托记录](../tools/rebuild/gomora/back_lift_resume/MIDLATE_SUPPORT.md)完成可核实原速与首承重/近角等整招边界，不重复已做反馈锚点或盲目补相。缺可靠连续观看能力不证明动作失败，静帧也不能证明1tick原速顺滑；本次不替正在推进的候选作安装裁决。
- **八装甲**：月亮、银河仅部分候选及明确缺帧结果；太阳、法德兰、雷基尼斯、特莱加隆、瓦尔基涅斯、加美顿目前只有model，未有合格S2–S7源可直接接入。完整动作、技能/武器/声音及变身闭环未齐，不开放。现用变身登记为泰罗、哥莫拉/雷德王到EX，和八装甲完成度分开计算。
- **三槽与原剧武器**：初代、内隆嘎、布莱克王、杰顿独立三槽仍有明确同技分档缺口；其他重复招名只列待依据/实际差异核对，不仅凭名称判失败。欧米伽三级按近斩＋光线实际数据核，不称纯光线。亚刻剑、布莱泽剑、欧米伽八斩、提欧箭/盾/锯剑等已装，不重复安装。余项依赖具体本人/形态/作品武器清单与独立持武器整帧；本次未找到合格且未接入的新源。依据见[本手册第 5 节](#第-5-节--combat_designmd)、[第 4 节“武器覆盖与记录格式”](#第-4-节--art_pipelinemd)及[现源核查](verification/other-existing-fullframe-availability.json)。
- **本人声音**：runtime.voices中亚刻仅有合体前卢提昂登场对白，提欧无角色语音映射；布莱泽当前五状态语音来源记original，不冒称原剧原声；欧米伽当前五个独立语音ID记episode。关联记录未登记听审不等于实听失败。来源账本1207条与注册sound1171项都不是实际触发覆盖数。需本人正确声源、触发上下文及有效听审，不挪用别人声音或以拟音冒充；不为补数批量接线。
- **场景、镜头和表现**：十九场的天空/分层/ambient与选择/BGM已登记，纹理路径存在不等于材质、实速与全场画面验收。双方人物轮廓/HUD取景已修；持续束超视口、白闪遮接点、旧站防/低防姿势等分别保留原回执，不以重复镜头检查代替缺失动作。未发现新的合格未接入场景；场景来源、具体材质与声音需要逐项验收而不是重新制作已有十九场。
- **交付与环境验收**：原生截图、真实InputFrame回放、硬件输入、原速与听感是不同证据。缺少其中一种不能自动判游戏功能失败，也不能用其他检查代替。按实际远端核验保存；不新增备份仓库或复制私人存档。

依赖顺序：先收尾正在推进的哥莫拉既有候选；其他动作只在出现合格独立完整源后实施；声音和原速需相应来源/实际观察能力；有效2P及目标引擎属于验收环境依赖。没有新的真实缺陷证据时停止扩展扫描，不为了保持忙碌再建测试、UI便利项或重复审片。各项旧红灯与未通过范围继续保留。

### 后续优先级

音乐规则（2026-11-08 修正）：必杀不再切换曲目。原实现里每次放必杀、
且距上次切曲超过 10 秒，就会切到该角色的主题曲，一场对战被反复劫持、
音乐碎片化；非本人主题的角色每次必杀还会跳到通用怪兽曲。现在必杀只把
背景音量压到 0.55 突出技能声，曲目保持本回合选定。菜单、选人、回合开始
仍是唯一的三处切曲点。

声音缺口（2026-11-07 核对）：`ultraman-teo` 有 88 个招式音效且 71 个已接进
`frame_sounds`，但没有通用状态音（idle/guard/hit/down）和语音表；`ultraman-arc`
只有 10 个音效、无状态音；`ultraman-blazar` 有 30 个音效但 `state_events` 仅 2 条；
`ultraman-omega` 无音频文件、`state_events` 仅 5 条。其余 12 名可玩角色状态音完整。
补齐需要新录音或新分离轨。

图鉴（2026-11-09 核对）：`content/roster/index.json` 1611 条，`catalogue_display.json`
1653 条且全部有图；`selection.json` 的 298 个可选条目也全部有像素形象。
早先“1710 行 / 661 有图”的旧数字已无法从现有数据复现，作废。

新补条目均为待审候选：只验证了画布 384×256、二值 Alpha、32 色硬色阶、
脚底对齐 248 和 SHA 一致，**没有做身份与画面验收**，需要人眼过一遍。

继续以独立三槽和八装甲完整矩阵为目标，但不要重复把缺合格整帧的候选当成完成品。先复用本索引已有证据，明确需要新增的完整动作/过渡源。保持受身、爆气和防御反制，不扩判定凑命中。任何新增动作都需真实输入、独立回放、双向720/1080实际画面，逻辑通过与美术通过分开。完整月亮S2–S7、其余装甲、全名册独立三槽/武器/本人声音仍未完成。

### 验证与发布边界

镜头单元746项、相关pixel_ui/ui_facing/phase3_air及本批原输入/独立回放通过；不等于全项目全量或完整美术/声音通过。图形使用真实原生窗口与冻结tick截图，无录屏、无音频及真人硬件输入验收。月亮land→idle收脚、保守缩放、站/低防手位、三级必杀立绘遮普通world等限制仍在。


> 收口注：2026-11-03 历史清理交接只说明当时状态，完整历史摘要保留在 `docs/verification/README.md`，不在此复制。

<a id="第-2-节--project_layoutmd"></a>
## 第 2 节 · PROJECT_LAYOUT.md

### 项目目录与架构

本节定义目录表、依赖方向、模拟子系统、引擎选型与热点模块；现行入口见根 README。

2026-11-03 清理后采用下列结构，2026-11-07 合并架构说明，2026-11-08 合并引擎选型。本节原文保留当时架构口径；执行准则只在根 [AGENTS](../AGENTS.md)，游戏规格只在 [REBUILD_2D_PLAN](../REBUILD_2D_PLAN.md)，当前状态与验证边界只在本手册第 1 节，唯一文档入口只在根 [README](../README.md)。不要往多份文件追加同一条用户指令。

### 目录归属

| 目录 | 内容 |
| --- | --- |
| `app/`、`app/scenes/` | 主游戏装配、流程和入口场景 |
| `core/` | 整数 60 tick 确定性模拟、状态和规则 |
| `input/` | 设备输入与电脑控制；审片驱动另列 `tests/review` |
| `presentation/` | 只读画面、镜头、特效和声音 |
| `ui/kit/`、`ui/theme/` | 正式界面组件和像素主题 |
| `content/fighters/<id>/` | 本人运行定义、招式、状态帧、形态、资料 |
| `content/catalogs/`、`roster/`、`templates/` | 查询门面、名册、公共数据模板 |
| `assets/{fighters,effects,audio,ui,stages,app,fx}/` | 已装资源、动态路径使用的资源、来源和许可；`fx` 是仍被当前注册表引用的旧接口目录 |
| `art/fighters/<id>/model/` | 当前定稿与测量，不重复存历史定稿 |
| `art/fighters/<id>/sources/` | 已装资源仍有用的唯一源文件，SHA 文件名；用途由 source-index 和原始 metadata 说明 |
| `art/fighters/<id>/stage<N>/` | 当前未完成动作、请求、候选、帧规格和有效交接收据；只存数据，不存脚本 |
| `art/shared/sources/` | 无法归属单角的当前源材料 |
| `art/source-index.json` | 现用源 SHA、字节数和旧路径到唯一实体的索引；不是备份 |
| `tools/`（可执行入口只有 `verify.py`、`godot_lock.py`；另有 `README.md` 与 requirements 文本） | 验证入口与 Godot 锁 |
| `tools/check/` | 资源与像素质检门 |
| `tools/art/` | 生图、后处理、像素化、名册生产 |
| `tools/audio/` | Kits 客户端、语音转写、混音 |
| `tools/roster/` | 名册编译、图鉴身份、繁简转换、维基抓取 |
| `tools/media/` | 媒体证据提取与采样度量 |
| `tools/runtime/` | 启动、Godot 定位与短临时录制 |
| `tools/rebuild/shared/`、`tools/rebuild/<id>/`、跨角色批次目录 | 复用制作模块、仍需接续的动作处理器、PixelFX 烘焙脚本与在制诊断生成器；跨角色批次附 `README.md` 说明唯一入口 |
| `tools/maintenance/` | 只读仓库审计与冻结路径解析 |
| `tests/`、`tests/fixtures/`、`tests/review/` | 功能回归、必要输入夹具、主游戏内审片驱动 |
| `third_party/`、`addons/` | 实际采用的上游代码与许可 |
| `docs/` | 当前规范、交接、验证结果摘要 |
| `reports/` | 新运行产生的日志、截图、回放与临时视频；忽略上传 |

工具目录的分工、依赖与路径引导见 [tools/README](../tools/README.md)。

`art`、`tools`、`reports` 带 `.gdignore`，不进入 Godot 资源导入。二进制源与运行资源使用 Git LFS；Godot 的 `.uid` 和 `.import` 是源文件侧车，必须上传；`.godot` 导入缓存不上传。

原始来源收据内的旧路径保留字节。离线工具通过 `tools/maintenance/layout_runtime.py` 和 `art/source-index.json` 读取现有源；未列入索引的旧候选、审片、录屏和无用源已经删除，不能把这些历史文字当作运行依赖。实际主游戏仅加载 `assets`/`content` 等正式层。

本机环境、下载缓存和游戏个人存档不属于仓库。三个旧目录整理工作树及原 Git 历史直接清理，未新建备份。

### 分层与数据流

```
设备/回放 → InputFrame → 招式表解析 → 独立状态 → 帧数据
        → 命中结算 → 状态快照 → 表现（只读）
```

- `core`：纯整数、60 tick 确定性模拟，只包含 x 和离地高度；不依赖渲染、Input、随机数和系统时间。
- `input`：设备输入转换为 InputFrame。
- `presentation`：只读状态、招式、帧并播放整帧图像、特效和声音。
- `ui`：菜单和 HUD，以容器布局组合组件。
- `content`：规则、角色、招式、招式表。
- `assets`：运行时最终资源。

图片不进入模拟指纹。

#### 依赖方向（只允许向下）

实测的层间引用，无环：

```
tests ──→ app ──→ content
  │        │        ↑
  │        ↓        │
  └──→ presentation ─┘
          │
          ↓
        core   ←── input
```

| 层 | 允许依赖 | 禁止依赖 |
| --- | --- | --- |
| `core` | 无（只依赖 `content` 传入的数据） | 渲染、`Input`、`presentation`、`ui`、`app`、随机数、系统时间 |
| `input` | 无 | 同上（但要读设备，这是它的职责） |
| `presentation` | `core`、`content` | `ui`、`app`；不得写活模拟 |
| `ui` | `presentation`、`content` | `app` |
| `app` | `content`、`input`，装配时实例化 `presentation`/`ui`（只负责装配） | — |
| `content` | 无 | 任何代码层 |

三条硬约束，改动前必须自查：

1. `core/` 里不出现 `randi`/`randf`/`Time.`/`OS.get_ticks`/`Input.`，
   也不引用 `res://presentation`、`res://ui`、`res://app`。
2. `presentation/` 只读模拟，不写 `stats`、`state`、`tick`。
3. 图片、音频和字体不进入 `content_fingerprint` 和 `state_hash`。

这套分层与 Godot 官方推荐的"数据与表现分离"一致，也与 GGPO 的
"逐 tick 输入 + 可重放状态"模型同构：`core` 是唯一的状态权威，
`InputFrame` 是唯一的输入形态，回放记录是唯一的复现路径。

对应的通行规范：依赖倒置/分层架构（Martin Fowler 的
Presentation–Domain–DataSource 三层）在本项目是
`presentation`–`core`–`content`；确定性锁步模拟（GGPO/GGRS 的共同前提）
在本项目是 `core` 的整数 tick 约束；只读视图（Godot 的 data-driven
rendering 建议）在本项目是 `presentation` 只读 `UfeMatchDirector` 的状态快照。

#### 可执行的守卫

`tools/check/layering.py` 把这些规则变成检查，已接入 `tools/verify.py`：

- 层间反向引用 → 失败
- `core/` 出现 `randi`/`randf`/`Time.`/`OS.get_ticks`/`Input.` → 失败
- `presentation/` 写 `view.simulation`/`sim` 的角色状态 → 失败
- 指纹代码引用 `res://assets`/`res://art` 媒体路径 → 失败

演出副本（KO 慢放重建的 `scene`）属于表现层自己的数据，可以写，不算违规。

### 引擎选型结论

本节回答两个问题：底层格斗引擎该不该换成成熟方案；现在的分层是否符合通行规范。
结论：**不换引擎**。本项目继续使用 Godot 4.7 + 自研确定性模拟；
分层已符合通行做法，只需把规则变成可执行检查（见上一节）。

#### 成熟格斗引擎能不能直接用

| 名称 | 类型 | 语言 | 许可 | 能否用于本项目的 Godot 4.7 自研模拟 |
| --- | --- | --- | --- | --- |
| Ikemen GO | 整套引擎 | Go | MIT | 不能。Go 独立引擎，不可嵌入 |
| M.U.G.E.N | 整套引擎 | 闭源 C/C++ | 专有免费 | 不能。2013 起停更 |
| Night Sky Engine | 整套框架 | C++ | MIT | 不能。绑定 UE5 |
| Sakuga Engine | 整套框架 | C# | MIT | 不能直接调用，只可参考架构 |
| Castagne | 专用层 | GDScript（Godot 3） | MPL 2.0 | 不能。Godot 4 版未发布 |
| GGPO | 回滚库 | C++ | MIT | 不能。无 Godot 绑定，2019 停更 |
| GGRS | 回滚库 | Rust | MIT | 需自写 GDExtension；Godot 封装停在 Godot 3 |
| dsnopek godot-rollback-netcode | 回滚库 | GDScript | MIT | 理论可以，但实测在 4.7.2 加载失败 |
| Delta Rollback | 回滚库 | GDScript | MIT | 可尝试，同类调度层 |

以上没有一个是"能被一个已有自研确定性模拟的 Godot 项目直接调用"的。
整套引擎都要求重写游戏；可插拔的那几个都是**回滚网络**库，而本项目是单机。

#### 可插拔的只有回滚网络这一层

回滚库借的是"输入采集 + 状态快照/回滚调度 + 传输"这一层，不含模拟。
本项目 `core/` 已经是整数 60 tick 确定性模拟，恰好满足它们的全部前提
（固定 tick、逐 tick 可序列化、种子化随机、不读系统时间与渲染）。

但**现在不需要**：没有联机需求。若将来要做，优先考虑 dsnopek 或 Delta
的调度层，并预留可序列化状态接口，而不是改动 `core` 的语义。

#### 最值得借鉴的是什么

1. **GGPO 的"逐 tick 输入 + 状态快照 + 可重放"模型**。本项目已经是这个形状：
   `InputFrame` 是唯一输入形态，`replay_recorder` 逐 tick 记录，
   `state_hash` 可复现。回放既是功能也是自检手段，继续用它守确定性。
2. **MUGEN 的 `[Statedef]` + 控制器 + 触发器**写法，以及 **Skullgirls 的可调帧延迟**
   思路。本项目的招式 JSON（逐帧 `frames`、`cancel`、`events`、`shots`）与
   `core/states/<id>.gd` 一状态一文件，是同构的，只是用 GDScript 而非 DSL 表达。
   不建议改成 MUGEN 的 CNS 格式——那会引入一套外部解释器。
3. **Godot 官方推荐的"数据与表现分离"**。本项目 `core`/`presentation` 的边界
   就是这个模式，`presentation` 只读，图片不进模拟指纹。

#### 不做的事

- 不换引擎，不引入整套框架。
- 不改 `core` 的确定性语义去迁就外部库。
- 不把招式数据改成 MUGEN CNS 格式。
- 不在没有联机需求时引入回滚网络。

### 模拟子系统

**专属技**：`core/combat/projectile_resolver.gd` 统一读取逐帧 `shots`、`projectile_guard` 和 `counter_shot`。飞行物框随整数位置推进；正面盾框可销毁、反射或吸收，反射保留原招式数据来源并转移攻击归属，吸收记录进入快照，只有实际吸收到才能反击。瞬移坐标只在招式数据的消失帧改变，表现层读取整帧透明度与独立 GPT 涟漪，不修改模拟。

**投技**：`core/combat/throw_resolver.gd` 在双方推进后统一配对。攻击方逐 tick 的 `target` 指定被投姿势编号、朝向、手部抓点和释放路径；被投者的独立姿势数据提供腰胯被抓点。抱持时按两点的世界坐标相等计算根点，释放后按整数进度落地；没有按角色体型写配对偏移。靠墙时两人整体平移。被抓后第 1–3 个真实 tick（含停顿）可拆，双方各播拆投并弹开；伤害只在落地冲击帧结算一次。表现层只读取这些结果，F1 可看抓点。

**演出**：开场倒计时与回合结束后的表现时钟分别驱动登场、胜负及时间到动画；模拟结束后保持冻结，演出不推进战斗、不进入回放指纹。挑衅仍是普通招式表驱动的独立动作，训练和对局均用防御+投技触发。

当前运行入口为 `app/scenes/main.tscn`。旧骨骼、纵深、废弃 UI 和整理历史不属于当前仓库；审片驱动集中到 `tests/review`，但仍在正式主游戏中运行。

### 热点模块

按 `codebase-memory` 索引（353,648 节点 / 357,656 边）的实际调用量：

| 模块 | fan-in | 职责 |
| --- | --- | --- |
| `core/replay/replay_recorder.gd` | 307 | 逐 tick 回放记录 |
| `core/commands/input_frame.gd` | 108 | 输入帧构造 |
| `ui/front_end.gd` | 78 | 菜单流程 |
| `core/combat/match_director.gd` | 71 | 对局主循环 |
| `content/content_database.gd` | 65 | 内容读取 |
| `core/fighters/fighter.gd` | 59 | 角色状态机入口 |

修改上述模块须跑完整回归；`tools/` 不在索引范围内，制作工具链按文件系统直接核对。

<a id="第-3-节--data_formatsmd"></a>
## 第 3 节 · DATA_FORMATS.md

### 数据格式

本节定义招式 JSON、持续束发射点和独立实体攻击段；招式数据是模拟的唯一依据，表现层只读取结果，不自行推算。

本文合并招式数据补充格式与独立实体攻击段规范。

### 坐标与文件位置

每个招式位于 `content/fighters/<id>/moves/<move>.json`。`frames` 的下标是零起始模拟帧，`sprite` 是人物图集相位。脚底坐标原点为 `(0,0)`，x 朝角色前方为正，y 离地向上为正，单位为原生像素。

### 持续束跟随发射点

持续束可在单个 `shots[]` 对象中声明可选 `origin_by_frame`：

```json
{
  "beam": true,
  "spawn": [59, 115],
  "anchor": [59, 115],
  "speed": 0,
  "origin_by_frame": {
    "10": [59, 115],
    "13": [55, 113]
  }
}
```

- 键必须是本招 `frames` 的有效下标的规范十进制字符串，值必须是两个整数。
- 按人物**当前模拟帧** `move_tick` 查询，不是按弹体年龄或 sprite 编号查询。
- `shots` 在源帧消耗时出生，模拟随后推进人物帧，持续束的第一次更新读取推进后的帧。
- 未列出的帧使用该束自己的 `anchor`；有此字段的束不读取共用 `frames[].beam_origin`。
- 同一帧的两束可独立跟随各自的手，左右朝向只镜像 x。
- 速度、寿命、碰撞框、命中参数照常执行；持续贴身束应声明 `speed: 0`、`vy: 0`。

没有 `origin_by_frame` 的束保持既有 `frames[].beam_origin → shot.anchor` 回退行为，飞行物快照不增加新字段。表现层只读取每束模拟结果 `x/height`，不另算手位。

发射点依据表为逐束跟随增加可选标记：`frame` 仍为含有 `shots` 的源帧，`field` 为 `shots[n].origin_by_frame`，`follow_frame` 是要检查的人物当前帧，`point` 是该帧该手的依据点。统一门逐束比较，最大容差仍为 2 原生像素。

回放文件格式未因该字段改变。既有格式 5 的内容指纹包含完整模拟招式数据，新增此字段会改变相关对局的内容指纹；旧指纹由 `UfeReplayRecorder.load_file` 明确拒绝，不使用新数据静默播放旧回放。

### 独立实体攻击段

只有实际有独立挥击动作和可见接触区的多段实体招式才声明本数据。它不生成动作，不赋予必杀差异豁免，也不让同一束重复扣血。未声明的旧招继续整招最多接触一次，战斗快照不增加字段。

招式 `kind` 为 `strike`，在招式根的 `hit_groups` 中定义各段覆盖值，并在相应生效帧设置正整数 `hit_group`：

```json
{
  "kind": "strike",
  "hit_groups": {
    "1": {"damage": 35, "knockdown": false},
    "2": {"damage": 45, "knockdown": false}
  }
}
```

- 第一段生效帧填 `"hit_group": 1`，第二段填 `2`。每段必须有实际 `hitboxes`，空框帧不得声明段。
- 一次发动中，同一段只接触一次，包括防御、实体护屏和后续重复进入同段。
- 前段落空或被无敌避过不会消耗后段。再次发动、被打断或自然收招都清除记录。
- 每段可覆盖 `damage`、`chip_damage`、`stun`、`hitstun`、`blockstun`、`pushback`、`knockdown`、`launch`、`bounce`、`unblockable`、`level`。未覆盖的值继承本招。
- 整数不得填小数；伤害、削血、硬直、眩晕不得为负；击退允许有方向。`level` 使用 `mid`、`low` 或 `overhead`。
- 段编号必须与定义一致，禁止缺失或未引用的段定义，也不能覆盖招式类型、资源、成本或脚本。

连段后接飞行物时，用现有帧级 `shots`。弹体继续使用自己的接触记录、判定和寿命，不消耗实体攻击段。招式根值供最后一击或弹体读取，不能把总伤害重复分给每一段。非终结段通常不击倒，并按实际相间距给受击硬直；这些数值仍须在实际对战中验证，不能凭动画有两刀就认为连段成立。

真实段接触保存在角色 `combat.hit_groups`，参与状态哈希和原输入回放。`combat.connected` 继续表示本次发动曾有接触，`confirmed` 仍只表示命中确认，保持取消与落空分支语义。实体护屏按本段的不可防御属性判断。

`tests/melee_hit_groups.gd` 默认输出到用户缓存，可重复运行；传 `--report-dir=res://reports/review/<日期>/<主题>/` 保存本次输入和结果。`--replay` 在独立进程读取相同目录的原输入。`--baseline` / `--check-legacy` 是历史制作接口，不属于当前验证入口。

<a id="第-4-节--art_pipelinemd"></a>
## 第 4 节 · ART_PIPELINE.md

### 美术制作入口与武器规范

本节定义美术流程、存储位置和记录格式；当前完成度以本手册第 1 节和运行数据为准。

2026-11-09 起恢复逐角色动作生产。先读根 [AGENTS](../AGENTS.md) 的整帧、预算和验收规则；像素风格细则见 [art/STYLE.md](../art/STYLE.md)，动作帧的参考图与提示词口径也在那里。

### 制作流程

1. 定位本人当前 `model` 和具体动作；旧路径先查 `art/source-index.json`，不能因路径变化重发生图。
2. **生图**：经 MCP 生图服务（`magpie-image`）出整帧高分候选。不再通过脚本直连图像 API；
   `tools/art/pipeline.py` 里的网络层只为历史收据保留，新任务不使用。
3. 图像返回后实际检查身份、Alpha、完整四肢/武器、身体连续与大小。完整源只保留一份，当前拒收原因写在动作 metadata 中，不复制整个工程作为历史。
4. **像素化后处理**：整图处理经 `tools/rebuild/shared/forge_backend.py`（需外部 sprite-gen 技能）。
   图鉴静态形象用自带的 `tools/media/art/catalogue_native.py`：软 Alpha 生成图 → 二值 Alpha、
   32 色硬色阶、384×256 画布、脚底对齐 248。它不依赖外部技能。旧颜色兼容 `palette_mode('rgb')`，
   同一动作统一尺度和根点；禁止拼肢或以静止图加 FX 代替动作。
5. PixelFX 脚本在 `tools/rebuild/<id>`，上游固定代码和 MIT 许可在 `third_party/pixelfx`；只离线导出透明整帧。人物不使用库骨架。
6. 运行资源安装到 `assets`，招式/事件到 `content`。主游戏两个朝向、720/1080、实际输入和独立原 InputFrame 回放分开核验；逻辑检查不替代画面或听感。

#### 图鉴静态形象

图鉴（`ui/archive_panel.gd`）读取 `content/roster/catalogue_display.json` 的 `entries[id].image`，
缺图时显示"像素形象整理中"，不伪造候选。

一张图鉴图从生成到可见，五步（2026-11-09 用户确认的流程）：

```bash
# 1. 真实造型底图（MCP 生图，1024×1536，透明背景）：按官方皮套照生成真实照片质感的
#    整帧人物，严格右侧视、错步战斗架势，头身比按已实机角色复核（头高约占站高 0.20）
# 2. 像素整帧（MCP 生图）：以第 1 步照片为底图，让图片模型转成像素整帧；只按需微调
#    个别部位（例如头顶尖角），不重新设计造型
# 3. 转原生格式
.venv/bin/python tools/media/art/catalogue_native.py <raw.png> assets/fighters/<id>/catalogue/model-native.png
# 4. 写 display 条目（catalogue_id / image / image_sha256 / native_canvas / native_root）
# 5. 校验
.venv/bin/python tools/godot_lock.py -- godot --headless --path . --script res://tests/catalogue_identity_display.gd
```

第 1、2 步都必须由图片模型完成；不要用程序化滤镜、调色或重采样冒充“像素化”，
程序只负责第 3 步的确定性降采样与量化。**图鉴**参考图尽量多给几张、给不同角度：
本人官方皮套照、本人既有来源图，再加 1–2 张已实机安装的同风格成品作画风与头身比
基准（只借画风与比例，不抄造型）。色调以本人官方参考图为准，饱和度明显高于参考图
（红/主体色 `sat - refsat > 40`）判为不合格。这条“多给几张”只用于图鉴照片→像素，
动作帧相反，见下面的动作帧小节。

`catalogue_native.py` 先输出站高 192，再由 `tools/media/art/catalogue_rescale.py`
按 `content/roster/catalogue_scale.json` 落到设定身高（45m 档 173、人类固定 96 等）。
最终校验用重设后的站高，不把中间值 192 当成成品要求。输出必须满足
`binary_alpha: true`、`visible_colors <= 32`、`canvas: [384, 256]`、
`native_root: [192, 248]`。不满足就不要接线。长尾、宽背与背鳍等横卧体型
按三帧最大宽一次性等比缩入固定格，静帧与待机条共用该尺度、色板和根点，
`strip_width_fit` 登记缩前/缩后高度与最大宽；不得裁轮廓或逐帧重标定。
生成收据的 `fits_catalogue_cell` 只作报告，不进入辉光门。

#### 动作帧

1. **定架势**：以 `art/fighters/<id>/sources/ref-01.webp`（官方皮套照）为主参考，
   可加 1 张已装机同风格成品只借站姿与画风。要格斗待机架势，不是并脚站立：
   两脚分开、脚外缘间距约为站高的 0.65–0.80（已装机 10 个角色实测中位 0.71）、
   前后脚屈膝下沉、双拳抬到胸前护架。审过才往下走。
2. **待机像素整帧**：以第 1 步为底图转像素整帧，此帧即该角色的动作身份锚。
   `tools/art/identity_anchor.py <id>` 出的 4× 定稿锚只保证配色与像素块大小；
   原生宽度 <60 px 时模型读不出肩宽和四肢粗细、会自编身材，不得单独作动作参考。
3. **生图**：MCP `magpie-image`，`cpa/gpt-image-2.6-sunburst`（或留空 `model` 跟随 Magpie 设置）、quality high、background transparent。
   只引用第 2 步那一张待机像素帧，提示词只写该帧动作（约 150–250 字）加固定尾串。
4. **落格**：`tools/art/stage_cells.py` 统一比例缩放、二值 Alpha、32 色、脚底贴
   `baseline-1`、脚底段重心对到 anchor x。硬门只判连通块、Alpha、色数。
5. **比例由人核**：看联系表判头身比、四肢粗细、站高，`cells.json` 的 `notes` 只是
   提示，不冒充自动通过。

动作帧请求与淘汰记录写在 `art/fighters/<id>/stage1/requests.json`。

现用源库存储：`model` 保留当前人可读入口；`stage` 目录保留正在接续的动作；已装来源去重后在 `sources` 目录，SHA 文件名对应 `art/source-index.json`。冻结 JSON 仍可包含当时原路径；不要为了美化路径改写原始请求与 usage。

需要重新制作的未完成动作见本手册第 1 节。旧大规模生成 worker、历史审片安装器与废弃批次已经清理，不能把运行代码中的历史来源字符串当成它们仍然存在。

### 武器覆盖与记录格式

范围是所有已装英雄、怪兽、宇宙人及其具体形态在原剧中使用过的武器。本节只定义工作标准，不重复维护完成度；当前状态以本手册第 1 节和运行数据为准。

每条武器登记：本人/形态 ID、规范名称与别名、作品/版本/集数/时间点、来源 URL 及文件 SHA、完整轮廓与持手、召唤/握持/收纳、原剧攻击方式、本作输入/动作 ID/费用/取消窗口、人物/脱手物/FX/声音、双向命中/防御/落空与原输入回放、剩余问题。

人物与手持武器一起生成完整像素帧。脱手物使用本人专属资源和实际判定；不贴通用武器、不换色充数，不以图鉴装备图或静止人物加 FX 冒充完成。原剧动作和本作连招编排须分开注明，不虚构官方招名。

已有原剧依据的武器招缺触发位置时，用户已允许替换凑数的指令/派生技；记录旧招到新招、输入、费用和判定变化，基础移动/常用拳脚保持。执行前须等用户新的开发指令。

八套装甲分别核对本人武器与形态归属。赛文头镖、杰克手镯变形、亚刻之眼剑、布莱泽持剑、欧米伽头镖及装甲、提欧具体版本武器等均不能互借整帧。名称或集数未知时留待核，不把"尚未核实"写成"没有武器"。

<a id="第-5-节--combat_designmd"></a>
## 第 5 节 · COMBAT_DESIGN.md

### 战斗形态与必杀槽设计规范

本节是装甲/形态、变身流程和三个能量必杀槽的设计约束，不是完成度报告；具体现装招式以 `content` 数据为准，剩余工作见本手册第 1 节。

本文件合并原 `FORMS.md` 与 `SUPER_MOVE_DIVERSITY.md`。旧按日期追加的相互矛盾状态已移除。

### 一、战斗形态与变身

运行登记以 `content/catalogs/battle_forms.json` 及 `battle_form_rules` 为准；不得把静态图鉴或旧制作计划的状态当成正式变身可用状态。

- E 是独立形态键，旧 22+P 入口仍可兼容，具体费用和可用条件读当前数据。
- 本体到 EX 采用完整 definition 切换，要求 EX 自己的招式、整帧、技能和声音；EX 哥莫拉、EX 雷德王也可从正式选人页直选。
- EX 形态保持至 KO 和胜败结算，新局重新建立。表现慢放不得暗中恢复本体。
- 只有轮廓相同、纯配色变化才允许共用帧；新增装甲、武器、体型差异必须制作独立动作。
- 亚刻太阳/月亮/银河、布莱泽法德兰、欧米伽雷基尼斯/特莱加隆/瓦尔基涅斯/加美顿八套装甲，仍须各自完整 S2–S7 矩阵和正式变身闭环。
- 月亮装甲部分候选与未完项见本手册第 1 节；接受某动作不等于全套装甲开放。

不要重新运行已清理的旧安装器。扩展形态时使用通用路由和数据协议，不在模拟中按角色复制逻辑；验证费用、失败入口、旧输入、直选、KO、R 再战和原 InputFrame 回放。

### 二、三个能量必杀槽的技能差异

#### 三个槽分别交付什么

- 先核本人、作品、原剧版本和当前形态可用的技能。基础形态不得借其它装甲或合体形态的专属技能凑槽；旧技能库条目数不能证明技能数量。
- 三个槽分别记录规范名称、原剧依据、发射/攻击部位、人物动作、武器/飞行体、专属特效与声音，以及战斗用途。
- 实际区别需要落实到攻击方式和效果，例如实体近战/投摔、飞行切割武器、连续射击、持续光线、抓取爆炸等；不能仅靠改招名、伤害、消耗、蓄力时长、光束粗细、颜色、特效 ID 或镜头特写。
- 两招同为光线并非必然违规，但必须是本人原剧中确有的不同技能，发射姿态、部位和可见效果须实际还原；不得把同一光线的蓄力版硬算另一招。
- 每招使用本人的独立整帧动作和专属资源，继续遵守招式矩阵共帧限制；真实输入、判定、命中/防御/落空及确定性回放须与该招一致。
- 游戏编排的连招终结必须明确标注，落实真实连续动作和判定，不伪称原剧正式招名，也不能以改名包装同一发射动作。

#### 例外如何登记

例外必须绑定角色、形态及作品版本，并列出核过的原剧技能、证据和仍缺资料。能证明技能确实有限时可保留同技分档，并如实标注是强化变化；不能仅因未查资料、素材不足、工期紧、已有图片多或数据库只收录一两条而默认豁免。当前盘点未给任何角色授予例外。

<a id="第-6-节--stage1_standardmd"></a>
## 第 6 节 · STAGE1_STANDARD.md

### 未实机奥特曼 stage1 动作制作标准

本节是未实机奥特曼动作帧制作标准，为 `AGENTS.md`“美术与资源”和 `art/STYLE.md`“动作帧参考与提示词”的执行细则，不另立规则。

### 范围

只做 `selection.json` 里 `selection_category == "ultra"`、且**没有**
`assets/fighters/<id>/animations/manifest.json` 的角色。已实机安装的不再做。
佐菲由主会话手工制作，子代理不动。

当前 74 个待开发角色（身份锚已生成）。每个角色的交付是**一整套动作**，
不是一张图。

### 每一步

0. **判锚能不能当参考**

   `art/fighters/<id>/model/identity-anchor-x4.png` 是定稿 bbox 的严格 4×
   最近邻。它只保证配色和像素块大小对，**不保证图片模型能读出身材**：
   盖亚原生 27×154、杰斯提斯 38×154、赛罗 36×188，宽度太窄，模型会自己
   编一套肩宽和四肢粗细，出来配色对、体格不对（2026-11-09 用户判定作废）。
   原生宽度 **≥ 60 px**（佐菲 110、初代 31 但已装机）才可直接用；不足的
   走第 1 步，从真实皮套照起。

1. **真实皮套照 → 待机架势（身份锚不足时必须先做这一步）**
   - 工具与参数同上一步的 MCP 生图。
   - 参考图：`art/fighters/<id>/sources/ref-01.webp`（官方皮套照）为主，
     可加 1 张已装机同风格成品**只借画风与站姿**，不抄造型。
   - 要的是**格斗待机架势**，不是并脚站立：两脚前后分开、脚外缘间距约为
     站高的 **0.65–0.80**（已装机 10 个角色实测 0.50–0.98，中位 0.71）、
     前后脚都屈膝下沉、上身略侧、双拳抬到胸前护架、视线朝前。
     膝盖微屈，重心落在两脚之间，不要直立、不要八字脚、不要丁字步。
   - 这一步产出的是**姿势与身材基准**，允许还是照片质感；它决定后面所有
     动作帧的肩宽、四肢粗细和站姿。
   - 审这一张，通过了才往下走。

2. **待机像素整帧**
   - 以第 1 步的待机照为底图，让图片模型转成像素整帧（同一套 MCP 生图，
     quality high、transparent）。只按需微调，不重新设计造型。
   - 出来的这一帧就是**该角色的动作身份锚**：此后所有动作帧只引用它，
     不再引用 4× 定稿锚。
   - 落到本角色统一制作格（默认192×192）后核对：站宽0.65–0.80、
     头宽/站高与定稿相差≤8%、四肢粗细与第1步一致、双拳在胸前。
     不达标回第1步，不靠缩放掩盖。
   - 头高只作“核实际头身比例”的旁证，没有绝对窗口。要报头高比时，
     **基准与候选必须同一地标**：都用“冠顶/角尖→白须或下颌最低点”÷
     “冠顶/角尖→最低鞋底”，不得一边用 `identity-anchor.json` 的
     `head_height_ratio`（12%–50% 区间最窄行启发式，该字段注明只供报告）
     一边用白须底。奥王 2026-11-10 连判 6 张即因混用这两种口径。
   - 结构判据（冠形、角形、面罩）必须与视角一致：正面的“紧凑高冠”
     不能用来判 90° 侧视；侧视按真实侧视来源（皮套照或同版实物实拍）核。
   - 动作帧的“冠顶”只取**头部列带**（眼列左右各约 26 px）内最上方的本体
     像素，**不得用整帧 Alpha 最高行**。下落、腾空、举拳等姿势会把披风或
     举起的手臂甩到头顶以上，用整帧最高行量出的“冠顶→眼”就是披风高度，
     会把正常头判成头变大。奥母 air_fall-00 2026-11-10 的三次 21/19/28
     即此错，按头部列带重测为 16/16/17（门 ≤18）。头壳宽不受此影响，
     但仍须在原生格量，不能用诊断缩略图。

3. **其余动作帧**
   - 工具：MCP `magpie-image`，`cpa/gpt-image-2.6-sunburst`（或留空 `model` 跟随 Magpie 设置），quality high，
     background transparent，size 1024x1536。
   - 参考图：**只有**第 2 步那一张待机像素帧。
   - 提示词：150–250 字，只写这一帧的动作；必须带“四肢粗细必须和参考图
     完全一致——手臂粗壮、大腿饱满、小腿有厚度，不要画细长的手脚”；固定
     尾串写同样的识别特征、固定右侧视、完整不裁切、透明背景、无地面文字
     边框特效。身份、配色、像素块大小全部交给参考图，不在文字里重复描述。
   - 一次只生成一帧。移动/循环按单帧；攻击、受击、演出可按条带，但每条
     至多 8 帧，且条带里每帧的四肢粗细仍要逐帧核对。

4. **落格**
   ```bash
   .venv/bin/python tools/art/stage_cells.py --fighter <id> \
     --scale-source <该角色待机第0帧> --target-standing <站高> \
     --frame idle-00=... --frame walk-00=... --air jump-00
   ```
   - 色板通常取本人定稿 32 色，先核额灯、计时器等识别色。若旧定稿缺色，
     从现用待机整图重新定 ≤32 色，在本批 `cells.json` 保存完整色板，
     全套共用该同一色板；整图映射，不按身体区域局部重涂。
     `stage_cells.py` 默认仍取图鉴色板；缺色批次不得照跑默认，须通过
     `forge_backend` 独立接口还原并显式使用本批色板。
   - 全套共用一个源像素比例，**不按每帧外框归一身高**。默认192×192格
     脚底贴183、脚底段重心对到x=96；原生体量或完整伸展姿态容不下时，
     本角色统一增大制作格与根点并在 `cells.json` 登记。例如赛罗188原生高
     使用256×256格、根点[128,248]、脚底247；不裁头镖或缩人物凑默认格。
     此为制作格，不自动修改名册或运行时资源。
   - 硬门（必须过）：连通块 1、Alpha 二值、色数 ≤32。
   - `cells.json` 的 `notes` 里的头高/站高偏差只作提示，比例要人看联系表判。

5. **审片**
   每批出联系表（同角色全部帧并排、原大 2×），逐项看：身份、头身比、四肢
   粗细、近脚接地、两臂肩髋协调、相邻帧接续、循环首尾。两侧朝向和 720/1080
   属于实机验证，不在本阶段冒充完成。

6. **记录**
   每角色写 `art/fighters/<id>/stage1/requests.json`：policy、身份锚路径与
   SHA、每帧的模型/尺寸/参考/提示词/结果路径/SHA/状态、落格结果与 flags。
   淘汰的候选直接删除，只在 attempts 里留一条 `status: rejected` 与原因。

### 站高与动作清单

- 站高用该角色 `catalogue_display.json` 的 `visible_height_including_ornaments`，
  与已装战斗帧同档（奥特曼多在 143–153）。不要自己按比例猜。
- 动作清单按 `REBUILD_2D_PLAN.md` 的动作矩阵；最小可交付集：
  `idle`(2)、`walk_forward`(4)、`walk_back`(4)、`dash_start`(2)、`dash`(4)、
  `takeoff`(2)、`air_rise`/`air_fall`、`land`(2)、`light1`(3)、`light2`(3)、
  `light3`(4)、`heavy`(4)、`hit`(2)、`block`(1)、`down`(2)、`getup`(2)、
  `win`(2)、`ko`(2)。其余按角色技能另加。

### 硬约束

- 简体中文记录；不编造路径、SHA 或审片结论。
- 不修改 `content/roster/catalogue_display.json`、不安装到 `assets/`、不接运行时。
  本阶段只产出 `art/` 下的帧与记录。
- 不新建测试场景、预览网页、备份副本。
- 同一项检查连续拒收 3 个不同帧就停下出诊断图；同一问题最多 2 种修法。
- 遇到身份不符、断肢、裁切、缺资源：重生成，不要靠缩放/换色掩盖。
- 待机站姿门（每角色必过）：脚外缘间距 ÷ 站高 **0.65–0.80**、前后脚都屈膝、
  双拳在胸前护架。并脚直立、八字脚、丁字步一律判不合格。
- 原生宽度 <60 px 的像素锚不得单独作动作参考，必须先走第 1 步真实皮套照。

<a id="第-7-节--audiomd"></a>
## 第 7 节 · AUDIO.md

### 音频：接口与配乐依据

本节定义 Kits 音频接口的凭据、连通性、计费边界，以及 8 只怪兽的原剧主题曲核查结论。

### 一、Kits 音频接口

项目通过 Kits（`https://arpeggi.io/api/kits/v1`）做语音转换、人声分离和分轨。
客户端在 `tools/audio/kits_client.py`，命令行入口是 `tools/audio/pipeline.py`。

#### 凭据

密钥只在本机，**不进仓库、不打印、不复制**。按优先级：

1. 环境变量 `UFE_KITS_API_KEY`
2. macOS：`~/.codex/secrets/ufeneo-music.key`（纯文本，权限必须 `0600`）

密钥文件权限过宽（组或其他用户可读）时，客户端直接拒绝发送请求。

#### 连通性

```bash
.venv/bin/python tools/audio/pipeline.py doctor
.venv/bin/python tools/audio/pipeline.py models --per-page 3
```

`doctor` 只检查 ffmpeg、ffprobe 和凭据是否存在，不发网络请求。
`models` 会实际调用 API；返回模型列表说明接口打通。

2026-11-08 实测：`models` 返回 270 个音色模型、90 页，接口正常。

#### 能做什么

| 子命令 | 用途 |
| --- | --- |
| `doctor` | 本地环境与凭据检查 |
| `models` | 列出可用音色模型 |
| `extract` | 从媒体文件提取音轨 |
| `prepare-voice` | 准备语音转换的输入切片 |
| `cut-cue` | 按时间点切出短事件 |
| `submit` | 提交任务（**发收费请求**） |
| `poll` | 查询任务状态 |
| `download` | 下载结果 |
| `mix` | 混音 |

`submit` 会真实计费。按 [AGENTS](../AGENTS.md) 的规则，收费请求须先读本机最新账本，
新单预占 1 美元、按真实 usage 结算，未知单不释放、不重发。

#### 不在这个接口范围内

Kits 是**语音转换与分离**服务，不是文生音效或文生音乐。项目不声称任何音效是文本生成的。

`content/audio/sources.json` 的 `source_kind` 现有三类：

- `original`：项目自制（合成、录音或自制编曲）。
- `episode`：原剧/官方音源。公开转载的副本必须同时写 `reprint: true`，并登记 `platform`、`uploader`、`source_url`、`source_timecode`、`raw_sha256`、`captured_utc`；不得把转载写成官方发布。
- `derivative`：二创、翻奏、MAD 等；不得冒充原剧原声。

只接受公开可访问的副本；需要登录、付费或返回 403 的不绕过，换公开副本。旧记录不改写，缺失 `source_kind` 的历史参考仍可读；新参考若写 `source_kind`，`tools/audio/pipeline.py` 会校验取值，`episode` 必须带布尔 `reprint`。

#### 2026-11-10 四角色首轮公开副本

四名角色各取 1 条 BGM/角色曲和 1 条非语言战吼，均为 B 站公开转载/合集，登记为 `source_kind=episode`、`reprint=true`；剪辑在 `assets/audio/production/v3/<角色>/clips/v002/`，完整 SHA、上传者与采集时间见 `content/audio/sources.json` 的 `*-reprint-20261110` 记录。

| 角色 | 用途 | B 站 BV / 时间码 | 片段 |
| --- | --- | --- | --- |
| 佐菲 | 角色歌器乐 | BV1hd4y1o796 / 00:02:30.000–00:03:00.000 | `zoffy-bgm.wav` |
| 佐菲 | 非语言战吼 | BV1b44y1w7g6 / 00:00:02.500–00:00:04.300 | `zoffy-roar.wav` |
| 赛罗 | 主题纯音乐 | BV1sa411K7ij / 00:00:10.000–00:00:40.000 | `zero-bgm.wav` |
| 赛罗 | 非语言战吼 | BV1BdC3YjEGq / 00:00:02.000–00:00:05.000 | `zero-roar.wav` |
| 盖亚 | OST「激闘」M-38 | BV1Kt9ZYEEnK / 00:01:00.000–00:01:30.000 | `gaia-bgm.wav` |
| 盖亚 | 非语言战吼（第2P） | BV1GRFSeJEFd?p=2 / 00:00:06.600–00:00:08.300 | `gaia-roar.wav` |
| 杰斯提斯 | 剧场版 OST「コスモス&ジャスティス」 | BV1YnxXe8EQi / 00:01:35.000–00:02:05.000 | `justice-bgm.wav` |
| 杰斯提斯 | 非语言战吼 | BV15hE964E6u / 00:00:09.000–00:00:12.500 | `justice-roar.wav` |

这些片段只完成来源、时间码、哈希和峰值检查；首轮完成时未做听审、未做循环、未接入运行时。

2026-11-10 已完成 Kits 首轮：4 条 BGM 以 `stem-splits` 分离后做 30.000s 循环，4 条战吼以 `vocal-separations` 清理并静态归一；输出在 `assets/audio/production/v3/<角色>/kits/`，台账见 `reports/audio-kits-ledger-20261110.json`。首轮完成时所有输出 `runtime_approved=false`、`listening_reviewed=false`；Kits job detail 未返回 `usage` 与内部模型标识。仍未听审。当前接入状态见下节。

同一批源 WAV 已切出每角色 attack/special/hit/win 各 1 条，共 16 条事件候选；只做裁剪、淡入淡出与静态归一，未做 voice conversion。登记见 `content/audio/sources.json` 的 `*_voice_*_20261110` 记录（与运行时声音 ID 相同），听审清单见 `reports/audio-events-first-listen-20261110.md`；全部未听审。当前接入状态见下节。

#### 2026-11-10 自动评审与运行时接入

用户 2026-11-10 委托自动批准首轮 24 条（4 BGM 循环、4 战吼、16 事件）接入运行时。记录已标 `runtime_approved=true`，统一写 `runtime_approval_basis=user_delegated_auto_approve_2026-11-10`；`listening_reviewed` 全部保持 `false`。这只表示准予接入，不表示听审通过，也不把 B 站转载写成官方发布。

4 条 30.000s 循环已转为运行时 OGG（48kHz 双声道、Vorbis），放在 `assets/audio/music/stage-bgm/v003/`；`battle_music.json` 新增 `zoffy-battle`、`ultraman-zero-battle`、`ultraman-gaia-battle`、`ultraman-justice-battle` 四条 track，并映射 `zoffy`、`ultraman-zero`、`ultraman-gaia`、`ultraman-justice`。运行时 `UfeBattleMusicDirector` 对 OGG 设置 `loop=true`。转换台账见 `reports/audio-runtime-conversion-20261110.json`。

`runtime.json` 已新增 20 条 `character_voice` 记录和 4 个 `voices` 条目：`attack`/`super`/`hit`/`victory` 分别接事件攻击/special/hit/win，`intro` 接清理后的非语言战吼；`down`/`timeout` 没有已核片段，保持未映射，不拿 hit/win 冒充。事件槽位仍是按合集区段的时长、峰值与 RMS 候选分配，不是逐场原剧核对。

24 个已安装运行时文件的路径、SHA、格式与导入命令见 `reports/audio-runtime-import-20261110.md`；`.import` 侧车已就位。20 条事件/战吼来源记录的 `runtime_status=installed`，4 条 reprint BGM、4 条 reprint 战吼与 4 条 loop30 记录标 `runtime_status=pending_install`，暂不写入 `sounds`。2026-11-10 在 Godot 锁内复跑 `audio_playback` 与 `phase3_fx_audio` 均 PASS；本轮无听审、无实机试听、无录屏。

#### 2026-11-11 事件语音补齐（7 角色 × down/heavy/taunt/timeout）

从既有公开转载合集继续切出 7 名角色（佐菲、赛罗、盖亚、杰斯提斯、奥王、奥母、奥父）各 4 条事件声：`down` / `heavy` / `taunt` / `timeout`，共 28 条。逐条上传者、平台、URL、作品与集数、时间码、SHA、取得日期见 `art/audio/voices-events-20261111.json`，批次说明见 `art/audio/VOICES_EVENTS_REPORT.md`。

- 接入：`runtime.json` 新增 28 条 `character_voice` 与对应 `voices` 键，`heavy`/`taunt` 在有对应 clip 的角色上登记 `frame_sounds` 帧 0；`sources.json` 28 条记录 `runtime_status=installed`、`runtime_approved=true`、`runtime_approval_basis=root_delegated_by_user 2026-11-11`；`listening_reviewed=false`，未听审。
- 峰值口径：`fx_audio` 门要求 true_peak ≤ −1.8 dBFS，既有 v3 事件声约 −9.96 dBFS。新批首轮按 −1.2 dBFS 归一被门拒绝，统一重采样到 −10.0 dBFS 峰值并重算 SHA/true_peak/sample_peak/rms/integrated_lufs，`fx-audio-resources`、`audio-manifest` 均 PASS。
- 未实机试听、无录屏；只到资源与逻辑检查。

#### 当前声音缺口

见本手册第 1 节“后续优先级”：teo/arc/blazar/omega 缺通用状态音与语音表。
佐菲、赛罗、盖亚、杰斯提斯、奥王、奥母、奥父自 2026-11-11 起已有 attack/super/hit/victory/intro/down/heavy/taunt/timeout 本人声音（新增 28 条事件声，未听审）；语音仍按合集区段分配，不是逐场原剧核对。
补齐需要新录音或新分离轨，属收费操作，须用户明确授权后才能做。

#### 2026-11-14 图鉴试听选声

`ui/kit/catalogue_sound.gd` 在本作已装声音台账内扩大本人声覆盖：固定本人候选声优先；没有固定候选时只读 `content/audio/runtime.json` 的 `voices[base].intro`，核 `content/audio/sources.json` 同 id 为 installed 或 installed_pending_user_listening 且资源可载入，才作为本人声；仍无则回退项目自制 `catalogue_pick.wav`。不新增 `sounds` 键、不改 1:1 台账、不拿 `victory/attack` 顶替。`ultraman-arc` 的卢提昂对白与 `ultraman-omega` 的光线技能喊声按非本人试听排除。此改动只扩大既有合规音源复用，不是音乐模型生成，不是听审通过，`listening_reviewed` 仍为 `false`。

### 二、怪兽主题曲核查

核查对象：8 只奥特曼系列怪兽在原剧中是否有专属主题曲/专用战斗配乐。
核查方式：只查曲目表、官方商品页、官方新闻稿与可交叉验证的日文资料；**未下载、未生成、未调用任何音频**；未接触原始 CD 内页（booklet），凡属推断均标注。

#### 先说明三个容易混淆的点

1. **1966《奥特曼》的 BGM 当年没有曲名，只有管理编号（A-1、B-1、M-4T2 等）。** 现在的曲名是 1991 年《ウルトラマン 総音楽集》CD 化时首次赋予的，之后被官方沿用（包括《新·奥特曼》的片尾字幕与原声带）。所以"レッドキングの襲撃""恐怖のネロンガ"这类名字**不是剧中叫法**，不能据此判定为"怪兽专属曲"。
   - 来源：https://shu-yashiro.com/ultraman-ost-history/ 、https://artist.cdjournal.com/d/-/1192030402
2. **《怪獣大進撃》不是 1966《奥特曼》的曲目。** 1966 年剧集官方曲目（《ウルトラマン 主題歌・挿入歌 大全集》12CD 全 263 曲）里查不到这个名字。可能的混淆源有三个：1969 年东宝电影《ゴジラ・ミニラ・ガバラ オール怪獣大進撃》（音乐同为宮内國郎）、1968 年《怪獣総進撃》、以及《奥特曼80》里名为「怪獣軍団大進撃」的 BGM。原剧通用战斗曲应写「戦い」「怪獣対ウルトラマン」「勝利」「空中戦」等。
   - 来源：https://columbia.jp/prod-info/COCX-39801-12/ 、https://www.suruga-ya.jp/product/detail/120014367 、https://columbia.jp/prod-info/COCX-41138-42/ 、https://columbia.jp/prod-info/COCX-42285-6/
3. **怪兽吼声（SE）≠ 音乐。** 官方效果音集里确实有以怪兽命名的音轨（例如《帰ってきたウルトラマン》效果音集的「ブラックキング」），那是叫声/效果音，不是配乐。

---

#### gomora（哥莫拉）

- 专属主题：**无**
- 依据：第 26–27 话「怪獣殿下」使用全剧通用剧伴。第 26 话哥莫拉战可确认使用 **M-4T2**（CD 曲名「ミイラの叫び 出撃(M4T2)」），庵野秀明为 2022 年「庵野秀明セレクション《奥特曼》4K 特别上映」选片时明确提到"M-4T2 曲响起、彩色计时器闪烁音回荡中，奥特曼美丽地被打倒"；第 27 话则按粉丝逐集分析使用通用战斗曲「戦い」系（**中**可信度）。两话均无"哥莫拉主题曲"。
- 另有一项特殊物：1991 年《ウルトラマン 総音楽集》Disc 2 的「未発見楽曲（M.E.テープ抜粋）」区块收录了 16 秒的「怪獣殿下」；1995 年《TSUBURAYA PRODUCTION HISTORY OF MUSIC》将其复原重录为「怪獣殿下（未発見楽曲復元新録音／ジョンスン島）」。这是该两话录音期遗留的未发表/未确认使用片段，**不是播出用的专属主题**。
- 若为通用 BGM：M-4T2（第 26 话）／「戦い」（第 27 话分析），作品《奥特曼》第 26–27 话
- 官方 OST 收录：**有**。《シン・ウルトラマン音楽集》CDI-16「ミイラの叫び 出撃(M4T2)」；《絶体絶命！ウルトラ怪獣 バトル・ミュージック・コレクション 昭和編》Tr.27「戦い」；《ウルトラマン 総音楽集》Disc 2 Tr.13「怪獣殿下」（未発見楽曲）
- 来源：
  - https://www.value-press.com/pressrelease/297122/pwrz4oDW/40856 （圆谷官方新闻稿，庵野评论）
  - https://cinema-factory.net/contents/2428_shin-ultraman/preview.html
  - https://note.com/konton_fusion/n/n8fcc6544e781
  - https://artist.cdjournal.com/d/-/1192030402
  - https://www.oricon.co.jp/prof/183/products/71961/1/
  - https://www.kinokuniya.co.jp/f/dsg-10-4549767003580 （16 秒记载）
- 可信度：**高**（无专属主题这一点有官方评论＋曲目表双重支撑）；第 27 话具体曲目为**中**（仅有粉丝分析，无官方逐集表）。

#### zetton（杰顿）

- 专属主题：**无**
- 依据：第 39 话「さらばウルトラマン」没有任何"杰顿主题曲"。相反，杰顿战以**几乎无音乐、仅效果音**的演出著称（杰顿电子音、打击音），用沉默制造"奥特曼攻击无效"的绝望感；这一说法在多个资料中一致，但未找到制作者一次证言。该话可确认使用的剧伴是 M7「謎の円盤群」、M8「円盤群接近」（圆盘舰队接近场面，据粉丝分析属第 2 回录音的通用曲）。注意：第 39 话监督是**飯島敏宏**，不是实相寺昭雄（实相寺仅支援参与）。
- 另需区分：1996 年电影《甦れ!ウルトラマン》原声带（SRCL-3470）里有「ウルトラマンVSゼットン」「ゼットンをイデが倒した」，是 1996 年为该片**重新编曲/新录**的版本，不是 1966 年剧中曲；1978 年 LP《ウルトラ怪獣大百科》也有名为「ゼットン」的轨，但那是 BGM＋效果音＋剧情的组曲。
- 若为通用 BGM：M7「謎の円盤群」、M8「円盤群接近」（舰队接近）；杰顿战本身**未核实**具体曲目（多方资料指向"无音乐/仅 SE"）
- 官方 OST 收录：**有**（通用曲）。《シン・ウルトラマン音楽集》CDI-25/26「さらばウルトラマン 謎の円盤群(M7)」「円盤群接近(M8)」；《絶体絶命！…昭和編》Tr.40–41。1996 版编曲另见《ウルトラマンワンダフルワールド》SRCL-3470
- 来源：
  - https://detail.chiebukuro.yahoo.co.jp/qa/question_detail/q10126944920
  - https://mkb1978.hateblo.jp/entry/13446a0931b1c54ea563dc1aadab6748
  - https://note.com/shota_/n/ne3f55438fc9b
  - https://www.kingrecords.co.jp/cs/g/gKICA-92606/
  - https://www.suruga-ya.jp/product/detail/120013909
  - https://omimi.biz/products/detail/51153
- 可信度：**高**（无专属主题）；第 39 话"无音乐"为**中**（粉丝共识，无官方一手证言）。

#### red_king（雷德王）

- 专属主题：**无**（但有以它命名的登场曲）
- 依据：第 8–9 话使用的 **B1「怪獣無法地帯 レッドキングの襲撃」** 是第 1 回录音的通用"怪兽出现"剧伴，并非只服务雷德王；有粉丝资料称同一曲也用于第 1 话贝姆拉登场（**中**可信度，未获官方确认）。粉丝逐集分析认为该曲与通用战斗曲「戦い」在**第 9 话「電光石火作戦」后停止使用**。曲名系 1991 年 CD 化时按首次使用场景命名，不是剧中名称。
- 若为通用 BGM：「怪獣無法地帯 レッドキングの襲撃（B1）」＋「戦い」，用于《奥特曼》第 8–9 话
- 官方 OST 收录：**有**。《絶体絶命！…昭和編》Tr.26「レッドキングの襲撃(B1)」；《シン・ウルトラマン音楽集》CDI-06；《ウルトラマン ミュージックファイル》B-1
- 来源：
  - https://columbia.jp/prod-info/COCX-42285-6/
  - https://www.kingrecords.co.jp/cs/g/gKICA-92606/
  - https://www.cdjapan.co.jp/product/VPCD-81296
  - https://note.com/konton_fusion/n/n8fcc6544e781
  - https://shu-yashiro.com/ultraman-ost-history/
- 可信度：**高**（无专属主题）；使用范围（第 9 话后停用）为**中**（粉丝分析）。

#### eleking（艾雷王）

- 专属主题：**无**（但有以它命名、为登场场面写的曲子）
- 依据：赛文第 3 话「湖のひみつ」使用 **M17「エレキング出現」**，作曲冬木透，属第 1 回录音（M1–M24 系）的剧伴库，官方 CD 以"湖のひみつ::エレキング出現＜M17＞"标注。它仍是可跨集复用的 M 编号剧伴，不是独立主题曲；其他话的复用情况**未核实**（未找到逐集使用表）。
- 若为通用 BGM：「エレキング出現（M17）」，用于《赛文奥特曼》第 3 话
- 官方 OST 收录：**有**。《ウルトラセブン45周年 音楽大全集》COCX-37583-6（第 3 话区块 Tr.20）；《ウルトラセブン コンプリート・ミュージック・コレクション》；《ウルトラセブン サウンドライブラリー》COCX-40216-20 Disc1 Tr.34；《絶体絶命！…昭和編》Tr.45
- 来源：
  - https://tower.jp/item/3152919
  - https://www.suruga-ya.com/ja/product/120058842
  - https://www.tacto.jp/ost/tokusatsu-ultra-seven-sound-library.htm
  - https://columbia.jp/prod-info/COCX-40216-20/
  - https://columbia.jp/prod-info/COCX-42285-6/
- 可信度：**高**（曲目、作曲、首次使用话数均有官方商品页支撑）。

#### neronga（内隆嘎）

- 专属主题：**无**（但有以它命名的登场曲）
- 依据：第 3 话「科特隊出撃せよ」使用 **B3B「恐怖のネロンガ」**，作曲宮内国郎，属第 1 回录音（A–H）的通用"危机"类剧伴。原始曲目表按"危機"分组记为 **B-3B**；"恐怖のネロンガ"是后来 CD 按首次使用场景赋予的名字。该话还混用了本应第 12 话以后才用的第 2 回录音曲（如 M-6「死闘 二大怪獣」），属早期选曲的例外。B3B 在后续剧集的复用情况**未核实**。
- 若为通用 BGM：「恐怖のネロンガ（B3B）」＋「死闘 二大怪獣（M6）」，用于《奥特曼》第 3 话
- 官方 OST 收录：**有**。《絶体絶命！…昭和編》Tr.28；《ウルトラQ ウルトラマン 快獣ブースカ 宮内国郎の世界》COCX-39693-9 Disc3 Tr.17；《ウルトラマン ミュージックファイル》B-3B
- 来源：
  - https://columbia.jp/prod-info/COCX-39693-9/
  - https://columbia.jp/prod-info/COCX-42285-6/
  - https://www.cdjapan.co.jp/product/VPCD-81296
  - https://note.com/shota_/n/ne3f55438fc9b
  - https://shu-yashiro.com/ultraman-ost-history/
- 可信度：**高**（无专属主题）；后续复用为**中**（仅见"B-3 系后期用过约三次"的笼统说法）。

#### black_king（布莱克王）

- 专属主题：**无**
- 依据：《归来的奥特曼》第 37–38 话音乐为冬木透。第 38 话在官方 MUSIC COLLECTION 中有明确使用曲标注：**《赛文》M70「イヴの夜」**（流用）。第 37 话**在官方合集里没有标注使用曲**；粉丝资料称杰克败北场面用的是 **M-13「ウルトラマンのテーマ／夕陽に立つウルトラマン」的短调器乐版**，以及 M-14/M-20 系"危机"曲，属推测。以「ブラックキング」命名的条目只存在于**效果音集**（D3-46），是叫声，不是音乐。
- 若为通用 BGM：M-13「夕陽に立つウルトラマン」系（第 37 话，粉丝证言）／《赛文》M70「イヴの夜」（第 38 话，官方标注）
- 官方 OST 收录：**有**（通用曲）。《帰ってきたウルトラマン MUSIC COLLECTION》COCX-40735-7；《帰ってきたウルトラマン 総音楽集》收录以第 37 话标题命名的组曲「ウルトラマン夕陽に死す」（是整集组曲，不是角色主题）
- 来源：
  - https://columbia.jp/prod-info/COCX-40735-7/
  - https://www.suruga-ya.jp/product/detail/120126549
  - https://www.oricon.co.jp/prof/183/products/133790/1/
  - https://note.com/joyous_ibis9754/n/n60c4042cc9ba
  - https://iketail.com/sfx/ultra-series/the-return-of-ultraman/bgm-yuuhi-ni-tatsu-ultraman-tsukkomi/
- 可信度：**中**（无专属主题可判定；但第 37 话逐场曲目无官方表，M-13 说法来自粉丝）。

#### ex_gomora（EX 哥莫拉）

- 专属主题：**无**
- 依据：EX 哥莫拉影像初出为《奥特银河 大怪兽格斗》第 13 话「惑星脱出」（2008-02-23，BS11，全 13 话的最终话）。该作音乐为**佐橋俊彦**，官方原声带 COCX-34701（2008-01-23，47 曲）中**没有任何以怪兽命名的曲目**，战斗曲为「大怪獣の激突」「攻防戦」等通用曲。续篇《NEVER ENDING ODYSSEY》原声带（UMCC-1029，34 曲）中与哥莫拉相关的只有第 31 曲「倒れ伏すゴモラ」（场景曲），同样不是 EX 专属主题。后在《奥特曼 X》第 19 话（2015-12-01）再登场，该作音乐为小西貴雄，《X Complete Soundtrack》曲目亦无以哥莫拉命名的曲子。
- 若为通用 BGM：第 13 话具体曲目**未核实**；可用范围是 COCX-34701 中的「大怪獣の激突」「攻防戦」等通用战斗曲
- 官方 OST 收录：**有**（通用曲）。《ウルトラギャラクシー 大怪獣バトル オリジナル・サウンドトラック》COCX-34701；《NEVER ENDING ODYSSEY》UMCC-1029
- 来源：
  - https://columbia.jp/prod-info/COCX-34701/
  - https://www.billboard-japan.com/goods/detail/231371
  - https://artist.cdjournal.com/d/-/4108110831
  - https://cocreco.kodansha.co.jp/telemaga/news/feature/kaijubiyori/mNr8g （初出=第 13 话）
  - https://cal.syoboi.jp/tid/1279/time
  - https://w.atwiki.jp/mikuraio/pages/66.html
- 可信度：**高**（无专属主题，OST 曲目表可核）；第 13 话具体战斗曲为**未核实**。

#### ex_red_king（EX 雷德王）

- 专属主题：**无**
- 依据：EX 雷德王实拍初出为《NEVER ENDING ODYSSEY》第 13 话「惑星崩壊」（BS11 初回 2009-03-14；东京电视台页面标注的 2010-03-25 应为后续播出）。该作原声带 UMCC-1029 曲目表中**没有**「EXレッドキング」「レッドキング」命名的曲子，只有「大怪獣戦」「奇襲攻撃」等通用战斗曲。其更早出处是游戏《奥特曼 Fighting Evolution Rebirth》（2005）的"改造雷德王"（来源为粉丝维基，**中**可信度），游戏侧 BGM 不在电视原声带范围，**未核实**。
- 若为通用 BGM：「大怪獣戦」等 UMCC-1029 通用战斗曲（第 13 话具体用哪首**未核实**）
- 官方 OST 收录：**有**（通用曲）。《NEVER ENDING ODYSSEY オリジナル・サウンドトラック》UMCC-1029；电影《大怪獣バトル ウルトラ銀河伝説 THE MOVIE》BVCL-59 亦无 EX 雷德王曲目
- 来源：
  - https://www.billboard-japan.com/goods/detail/231371
  - https://artist.cdjournal.com/d/-/4108110831
  - https://www.tv-tokyo.co.jp/contents/ultra-galaxy/monster/neo13.html
  - https://ultraman.fandom.com/ja/wiki/ウルトラギャラクシー大怪獣バトル_NEVER_ENDING_ODYSSEY
  - https://tsuburaya.fandom.com/wiki/EX_Red_King
  - https://www.cdjapan.co.jp/product/BVCL-59
- 可信度：**中**（无专属主题可判定；第 13 话播出日期在不同站点有 2009/2010 两种记载，具体曲目未核实）。

---

#### 结论

**1. 真正意义上的"怪兽专属主题曲"：0 只。**
8 只怪兽在原剧中都没有为该怪兽单独创作、独立命名并作为"主题"使用的曲子。昭和期（1966/1967/1971）的做法是"全剧通用剧伴库 + 按场景选曲"；2007/2009 的《大怪兽格斗》系列也是"通用战斗曲 + 角色主题只给人类角色（レイ、ケイト、ダイル）"。

**2. 只有通用 BGM：5 只** —— `gomora`、`zetton`、`black_king`、`ex_gomora`、`ex_red_king`。
其中 `gomora` 另有一段 16 秒的"怪獣殿下"未发表/未确认使用片段（M.E. 磁带复原），但不构成主题曲；`zetton` 的最终战反而是"几乎无音乐、仅效果音"。

**3. 有"以怪兽命名的登场曲"但并非专属主题：3 只** —— `red_king`（B1「レッドキングの襲撃」）、`neronga`（B3B「恐怖のネロンガ」）、`eleking`（M17「エレキング出現」）。
这三首是 8 只里唯一可作"听感区分"的官方曲目；但曲名多为后期 CD 赋予，且仍属通用剧伴库，可跨集复用。

**4. 无法核实的具体项：3 只** —— `black_king`（第 37 话逐场曲目）、`ex_gomora`（第 13 话战斗曲）、`ex_red_king`（第 13 话战斗曲）。没有一只能拿到"官方逐集使用曲表"。

**对"8 个怪兽共用一首配乐"的资料判断：不反对，但会丢掉原剧的层次。**

- 资料上不支持"每只怪兽都有自己的主题曲"，所以共用一首**不会被原剧事实否定**。
- 但原剧的实际层次是三层：**通用战斗 BGM（共用）+ 怪兽登场曲（少数有名字）+ 怪兽吼声/效果音（各自不同）**。如果只做一首通用曲，最接近原剧的补法是给每只怪兽配**独立的登场音效/吼声**，而不是硬造 8 首"主题曲"。
- 若想做出区分度，可参考 `eleking` M17、`red_king` B1、`neronga` B3B 的"怪兽登场曲"思路，**自行原创**对应气质的短登场段；这些原曲是受版权保护的音乐作品，游戏不能直接取用原录音，需授权或自制。

**附：本次未做的核验**

- 未查证原始 CD booklet 的逐集使用曲注解（部分店铺曲目表已知存在标注错误）。
- 未查证《大怪兽格斗 ULTRA MONSTERS》街机/游戏侧 BGM（无公开原声带）。
- 未查证 2007/2009 两作第 13 话的逐场曲目。


<a id="第-8-节--third_partymd"></a>
## 第 8 节 · THIRD_PARTY.md

### 第三方来源与许可

本节只记录当前实际采用的第三方代码、素材和制作工具来源与许可。运行不依赖 API 密钥，外部制作环境和研究缓存不随仓库上传；角色、原剧画面和声音的权利不因工具开源而转移。

| 项目 | 当前使用方式 | 来源与本地许可 |
| --- | --- | --- |
| Shoto Fighter | 两个纯逻辑模块，项目类名前缀适配 | https://github.com/aminRX/shoto-fighter-godot ，MIT；third_party/shoto/LICENSE及UPSTREAM.json |
| Godot UI Components | Tween/过渡适配，固定22d2355690612978e58df559ddd4b6ba50c6887c | https://github.com/MrEliptik/godot_ui_components ，MIT；third_party/godot_ui_components |
| Godot AI | 编辑器 MCP 插件 4.4.1，开发期场景/节点/运行调试；游戏内 helper 仅在调试器通道激活时工作 | https://github.com/hi-godot/godot-ai ，MIT；addons/godot_ai/LICENSE |
| Controller Icons | Godot输入图标插件3.1.8 | https://github.com/rsubtil/controller_icons ，MIT；addons/controller_icons/LICENSE |
| PixelFX | 仅离线烘焙透明像素FX；固定a84159688af3ca37a4be05a0d422b94451b2e24e | https://github.com/patch-gg/pixelfx ，MIT；third_party/pixelfx/LICENSE、NOTICE.md、UPSTREAM.json。包含Patch及Hugo Duprez署名，人物骨架未采用 |
| Fusion Pixel Font | 正式简中12px单宽字体，最近邻显示 | https://github.com/TakWolf/fusion-pixel-font ，SIL OFL 1.1；assets/ui/fonts/LICENSE-OFL.txt及SOURCE.json |
| Kenney Pixel UI | 已注册的少量CC0组件；正式主体为本项目像素套件 | https://kenney.nl/assets/pixel-ui-pack ，assets/ui/kenney/LICENSE.txt |
| agent-sprite-forge | 可选离线整图处理，项目forge_backend统一适配 | 本机安装或UFENEO_FORGE_ROOT指定；不把技能/venv复制到仓库 |
| sprite-gen grid-range | 保留已采用提取器和显式格距覆盖层 | Apache-2.0；third_party/sprite_gen_grid_range内原文、NOTICE、UPSTREAM和补丁 |
| LibreSprite | 可选离线源稿工具，未捆绑可执行程序 | https://github.com/LibreSprite/LibreSprite ，GPL-2.0；third_party/libresprite |
| rtmlib / DWPose | 可选测量辅助，不做骨骼绑定 | https://github.com/Tau-J/rtmlib 、https://github.com/IDEA-Research/DWPose ，Apache-2.0；third_party/rtmlib |
| Pillow / NumPy | 本地图片和PCM检查 | HPND / BSD-3-Clause；tools/requirements-checks.txt，环境不入库 |
| FFmpeg | 离线媒体处理与 PCM 解码工具；本机 PATH 提供，不随仓库上传 | https://ffmpeg.org/ ；不分发本机程序和下载缓存 |
| Kits AI | 可选分离、分轨与转换服务 | https://docs.kits.ai/ ；凭据只在本机，不声称文生音效能力 |
| Wikipedia文字 | 游戏资料使用带来源的简体摘录/改写 | CC BY-SA 4.0；各profile/roster条目保留原页、版本和来源；图片/IP不自动适用文本许可 |

现用每份图片/声音的来源以assets中的provenance/manifest和content/audio/sources.json为准。source_kind=episode表示原剧来源；original或转换记录不能冒称本人原声。旧审片页和下载缓存已清理，不再将它们列为需要上传的依赖。

PixelFX制作脚本保留在tools/rebuild/<id>。赛文I、布莱克王Q/热束、初代束、提欧跃击、哥莫拉与EX哥莫拉已用效果各保留实际采用的烘焙入口；Godot只消费PNG帧，未引入运行时JS。简体使用说明：https://github.com/bayshier/pixelfx-zh/blob/836f545ed8946fffc6b911ff645cad5bd8c372aa/README.zh.md 。

<a id="第-9-节--readmemd"></a>
## 第 9 节 · README.md

### 原索引表收口说明

原 `docs/README.md` 的索引表已并入根 `README.md`“唯一文档入口”，此处不再重复。维护规则与分散规范入口按下列现行口径执行：

- 根目录只保留 `AGENTS.md`、`README.md`、`REBUILD_2D_PLAN.md` 三份 Markdown；根 README 是唯一文档索引。
- 每份现行文档开头用一句话说明“是什么、何时读”；主题事实只写入本手册对应节，不按日期追加互相矛盾的副本。
- 新增主题先判断能否并入本手册；确需拆分时同步更新根 README 与代码、数据中的现行链接。
- 历史回执只保留在 `docs/verification/` 或本机 `reports/`；冻结任务书按 SHA 绑定后不得中途改字。
- 单角色在制分镜与批次回执留在各自 `art/fighters/<id>/stageN/` 或 `tools/rebuild/<批次>/`，不复制成第二份进度文档。

### 分散规范入口（现行）

| 文件 | 内容 |
| --- | --- |
| [../AGENTS.md](../AGENTS.md) | 唯一执行准则 |
| [../REBUILD_2D_PLAN.md](../REBUILD_2D_PLAN.md) | 游戏设计规格与 2.5 节招式矩阵 |
| [../README.md](../README.md) | 项目总览、运行命令与唯一文档入口 |
| [verification/README.md](verification/README.md) | 可交付验证结果摘要与根因事故记录 |
| [../tools/README.md](../tools/README.md) | 工具目录归属、依赖与路径引导 |
| [../art/STYLE.md](../art/STYLE.md) | 像素风格、尺寸校验、远侧肢体、待机与走路 |
| `content/fighters/<id>/MOVES.md` | 单角色招式与原剧依据 |
| `content/fighters/<id>/SOUNDS.md` | 单角色声音台账 |
| `content/fighters/<id>/CANVAS.md` | 单角色画布与根点 |
| `art/fighters/<id>/model/CANVAS.md` | 定稿画布方案，被 `art/source-index.json` 记录 SHA |
| `reports/README.md` | 本机验证输出说明 |

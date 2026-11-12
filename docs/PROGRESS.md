# 当前状态

用途：接手、汇报或确认当前可玩范围、各角色未完项、验证入口与接续优先级时读本文件。历史清理交接保留在文末，只说明当时状态。

更新：2026-11-12。逐角色动作生产进行中（官方皮套照 → 格斗待机架势 → 待机像素整帧作动作身份锚 → 单帧动作 → 落格）；八装甲未齐，仍不开放。下面 2026-11-03 清理交接保留为历史，不再把当时“停止开发”误作现行状态。

当前执行状态以 [AGENTS](../AGENTS.md) 的“当前任务”为准。


## 当前成果与证据索引

- 2026-11-12 赛罗六形态选择与战斗切换基础：选人界面可按出场形态开局，战斗中形态键加方向随时切换六形态，不耗气、不限次数、切换中不无敌；回放记录并校验双方出场形态。基础赛罗 `form_switch` 六帧已装机（256 格、根点 [128,248]、6×10 tick，站高 186/174/179/172/173/178，均在中位站姿容差内），形态切换共用 60tick 时间轴。新增 `effect_registration` 与 `form_selection_consistency` 两个硬门，拦未登记特效与选人/战斗形态半开放。五个剩余形态的动作整帧生产中，selection 与 battle_forms 的 implemented 仍未开放；未实机、无录屏、未听审。
- 2026-11-12 七角色整帧落格与招式对齐：赛罗、杰斯提斯、盖亚、奥王、佐菲、奥父、奥母的纯人物整帧已按各自身份锚比例落格、装机并重映射招式；special/special2/special3 统一 72/80/96 tick（24/32/16、32/32/16、32/48/16），air_special 24（10/1/13），奥父基础招按初代模板 20/28/12，dash_throw 24。超宽空中/披风帧改用 288 格（赛罗/杰斯提斯/盖亚 air_special、奥父 light2），其余 256/192；根点与逐帧 bbox/SHA 见各角色 `stage1/cells/cells.json` 与 `tools/rebuild/<角色>/README.md` 2026-11-12 节。锁内全量验证 57 项 PASS。当前装机 clip：赛罗 113、杰斯提斯 108、盖亚 105、奥王 104、佐菲 108、奥父 104、奥母 105；仍不等于动作全齐。
- 2026-11-12 赛罗特效家族与发射点：赛罗三槽必杀、空中必杀与 Q 蓄气接入本角色 11 段 PixelFX 自绘特效（硬 Alpha、≤8 色，phase3 共 695 条）；盖亚/奥王/佐菲/奥母已烘焙但未登记的 Q 蓄气补登记 12 条，Q 蓄气不再整段不可见。special3 双镖发射点改 [59,132]/[33,133] 并补 31 点外飞折线与 tick 32–95 逐 tick 回收锚，pulse/low_pulse/air_pulse/ranged_forward 发射点改按当帧手部；九处发射点距本体均 0.00 px。
- 2026-11-12 奥父/杰斯提斯/赛罗基础光弹专属特效家族：奥父 16 段、杰斯提斯 9 段、赛罗基础 2 段 PixelFX 离线自绘（`father_fx_*`/`justice_fx_*`/`zero_fx_pulse_*`），已并入 `phase3_projectiles.json` 共 27 条并接线对应招式；奥父/杰斯提斯 Q 三态落点并入 `charge_overlay_policy.json`，配合只登记落点时注入显示的修复，无附件也能在真实 Q 起势/保持/收势显示。三套图集逐段复核尺寸、SHA、二值 Alpha、4 连通主体与主体外 `alpha≥16 ≤100 / ≥200 = 0`，27 段全部通过；赛罗命中段原按 8 邻域留了主体外 2–6 px 实心碎点，已改 4 邻域重烘并同步 SHA。`effect_registration` PASS。未实机、无录屏、未听审。
- 2026-11-12 未完成：奥父 dash_throw 仍旧人物帧（只对齐节奏）；奥王 motion_22 06→07 相邻差分 0.085 未达 0.10；七角色均未做双朝向 720/1080 实机画面复检，无录屏。
- 2026-11-11 装机增量与语音补全：奥母、盖亚、奥父、奥王四名角色继续按 stage1 动作帧安装并重导数据，对照 `ultraman-taro`（100 通用 clip / 47 招 / 53 状态声）的当前覆盖为：杰斯提斯 108/50、赛罗 110/47、佐菲 96/35、奥母 93/42、奥王 82/40、盖亚 78/25、奥父 61/35（clip/招）。`roster_data_integrity` 登记仍缺的运行时状态 clip：奥母 7、盖亚 6、奥父 34、奥王 19（intro/victory/defeat/timeout/ko/win、hit/block/stun/guardbreak、投技与被投、charge/burst/chase_takeoff/vertical_jump/air_tech 等），未齐不等于完成。
- 2026-11-11 事件语音：7 角色各补 down/heavy/taunt/timeout 共 28 条，来源逐条登记并 1:1 接入 `sources.json`/`runtime.json`；因 `fx_audio` 峰值门把首轮 −1.2 dBFS 拒收，统一重归一化到 −10.0 dBFS 后两项音频检查 PASS。未听审，`listening_reviewed=false`。
- 2026-11-11 减速规则：core 新增招式字段 `chill`（`ticks`/`speed_percent`），只在未防住的命中写入受方，每 tick 递减；walk/dash/backstep 位移按档位取整缩放，出招、受击与硬直时序不变。佐菲 `special2` 超级冻霜接 120 tick / 50%；新增 `tests/chill_effect.gd`，全量验证 57 项通过。该数值为游戏编排，未实机校准。
- 图鉴重建：1653 条统一 384×256 画布、根点 [192,248]、按设定身高换算站高（3.84 px/m；人类固定 96）。609 条按官方剧照/皮套照图生图重画并安装，图鉴图 1075 个文件变动；参考图补齐到 1686 张，低清官方源保留原图并标例外。旧批准标记全部重置为待实机复核；17 条重复形态以 `aliases` 归并。图鉴 UI 改分页列表、固定画布不滚动。全量 54 项通过；未做 720/1080 双向实机审片。[验证回执](verification/README.md)

- 未实机奥特曼动作生产（2026-11-09 起）：74 个未实机 ultra 角色已生成 4× 定稿锚（`art/fighters/<id>/model/identity-anchor-x4.png`），逐张核过严格最近邻零插值、二值 Alpha、32 色、源 SHA 一致。制作标准写在 `docs/STAGE1_STANDARD.md`，落格工具 `tools/art/stage_cells.py`（全套共用一个源像素比例，硬门只判连通块/Alpha/色数）。
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
  - **口径自查（2026-11-10，推翻上面两条的“门限自洽”）**：0.2034 不是项目规则，是我上一轮自己派生的数，而且两边口径不同。它取 `identity-anchor.json` 的 `head_height_ratio` 0.1883（定义＝12%–50% 区间**最窄行**→头顶，该文件自己注明“头冠会让数值偏小，仅供报告参考”），而所有照片候选一律按**冠顶→白须底**测量。窄行落在颈部/领口收窄处，比白须底高 6 px（图鉴）/15 px（ref-04），同一张图两种口径差 7–14%。项目 `docs/STAGE1_STANDARD.md` 的 ±8% 原文是**头宽/站高**，不是头高；`AGENTS.md` 只要求“核实际头身比例”。同口径重算（冠顶→白须底）：图鉴 49/223=**0.2197**、ref-04 官方正面 208/1073=**0.1938**（−11.8%）、ref-03 真实侧视 213/961=**0.2216**（+0.9%）；头宽侧未受影响（图鉴 29/223=0.1300、ref-04 139/1073=0.1295，−0.4%）。最直接的证据：把图鉴原图本身当候选、按候选用法测是 0.2197 > 0.2034，**原图会被自己的门判死**。**修正门 = 0.2021–0.2373**（0.2197 两侧各 ±8%；只设上限会放过缩头），倍数仍是项目 ±8%，不是放宽。
  - **冠形判据也错了**：原判据“紧凑银高冠带纵向脊”取自 ref-04 **正面**轮廓；真实 90° 侧面上奥王冠是**后掠刃 + 后端小球 + 刃下纵向肋**，ref-02（真实手办实拍侧视）与 ref-03（官方软胶侧视）两个独立来源一致。v10/v12/v13 被判“后弯长刃 fail”属误判。侧面改按 ref-02/ref-03 核，正面“紧凑高冠”不得当侧视判据。诊断 `stage1/diagnostics/crown-side-vs-front-20261110.png`、`head-metric-definition-audit-20261110.png`。
  - **按修正口径重评 6 张**：v10 头 0.2127 过但鞋底 2.52 原生px/辉光 16,383/胸腹 3/4 不过；v11 头 0.278 不过；v12 头 0.2224 过但鞋底 1.58 不过；v13 头 0.2365 过（余量仅 0.34%）、站距 0.755、鞋底 0.18、侧视、真 Alpha 全过，**唯一不过项是主体外辉光 36,868 px**。v13 原图已按规则删除，不回溯签收；按修正口径重出一张，见下条。
  - **辉光门口径也查了（同日第三起口径事故）**：同一项“主体外辉光”在 v12/v13/v14/v15 四次记录里结论相反——v12 记 pass、v13 记 36,868 px fail、v14/v15 按 `alpha>0` 记 33,191/35,186 fail，而同一条记录又写明“主体+3px 外 alpha≥16 为 0”。对 9 个已签源实测：主体外 `alpha>0` 是 9,030–87,536 px（几乎全是 alpha=1 尘点，拿它当门会判死全部已签源）；`alpha≥16` 照片源 0–1、像素源 17–60；`alpha≥200` 全 0。定门写回 `AGENTS.md`：主体外 alpha≥16 ≤100 px、alpha≥200 = 0、alpha 1–15 尘点只登记不计入。**只改口径不回溯**：v14 鞋底 1.10 原生px、v15 站距 0.6249 仍不过，卡点仍是站距与鞋底同线，不是辉光。诊断 `stage1/diagnostics/halo-definition-audit-20261110.png`。

- 奥特之母 stage1（2026-11-10）：**45 帧动作全部落格并 `root_delegated_by_user` 自签**（身份锚 idle-01；walk_forward 4、walk_back 4、dash_start 2、dash 4、takeoff 2、air_rise 1、air_fall 1、land 2、light1 3、light2 3、light3 4、heavy 4、hit 2、block 1、down 2、getup 2、win 2、ko 2），另有备选待机 `idle-candidate-01`（站距 0.5649，不属动作集）。全部 192×192、根点 [96,184]、脚底 183、同一 32 色板、二值 Alpha、严格 4×；独立脚本重读 47 个 PNG 复检硬门 **0 例外**，全帧联系表 `art/fighters/mother-of-ultra/stage1/cells/review-all-47-2026-11-10.png`（3180×2508，SHA `11cf3f96…`，无阻塞槽；落格前的 46 格红槽表已删）。各动作组均齐，`heavy-00` 起手已解卡（见下条）。
  - `air_fall-00` 的刹车依据**已作废**：三次“冠顶→眼 21/19/28 超门”复算逐值吻合，但那是“眼行 − 整帧 Alpha 最高行”；下落姿势把红披风甩到头顶以上，最高行是披风不是头。按锚同口径（眼列 ±26 px 内、排除红披风取冠顶）重测 16/16/17，三张全部 ≤18。三张原图已删不可追回，须重出一次再判。
  - `air_fall-00` 已按修正口径**重出并落格签署**（MCP `image-65174-1158`，实收 1024×1536，源 SHA `040badf4…8abcf1`，第一张即过、未用第二种修法）：原生格 bbox [47,14,134,174]、32 色、二值 Alpha、单连通 5,865 px；**冠顶→眼 17（门 ≤18）、眼行头壳 29（门 ≤30）**；旧口径在同一帧上仍会量出 21，证实是量法而非画法；披风高过头顶 4 px 属下落相正确画法，保留。
  - `heavy-00` 不受此缺陷影响：站姿起手、披风在身后低于头顶，按正确面板复算 19/19/19、头壳 31/31/31 与记录一致，**旧三次拒收是真的**。
  - `heavy-00` 已按换工序解卡并落格自签：改用**锚派生像素比例导引**（身份锚最近邻 9.396×=1447/154，按锚 raw 占位居中裁 1024×1536，洋红标眼行/冠顶行/头部列带、青色标头壳缘，仅此一张参考），MCP `image-65174-1163`，源 SHA `b846888a…f924`；落格后原生 bbox [47,43,139,183]、32 色、二值 Alpha、单连通 5,461 px、脚底 183；**冠顶→眼 16（门 ≤18）、眼行头壳 27（门 ≤30）**，cell SHA `f0f5a8fc…89f2`。导引 v1 按画面占比缩身（落格高 130/头壳 23）已拒收删除；heavy 组 4/4。
  - 规则写回 `AGENTS.md` 与 `docs/STAGE1_STANDARD.md`：动作帧冠顶只取头部列带，不得用整帧 Alpha 最高行。诊断 `art/fighters/mother-of-ultra/stage1/diagnostic/air_fall00-landmark-audit-2026-11-10.png`。
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
- 月亮S2：轻击三连、heavy、tackle、sweep、dash_light、dash_heavy、垂直跳、前跳已建立现有整帧候选与真实输入/回放路径，但不是完整装甲完成。各动作状态见本文“已完成与未通过的具体动作”，尤其扫腿/飞踢/前跳的视觉缺帧仍未通过。
- 月亮后撤backstep五相已复用现存新03/04修复源，真实双后每次80px、两次触发与回放完成；8组192PNG技术通过，但02抬膝到03宽站仍缺落脚中间整帧，视觉未接受，不算动作完成。[回执](verification/luna-backstep-graphical-review.json)
- 哥莫拉三级背掀：通用root覆盖及显式空接保相机制有逻辑回执，18攻方/6受方现有整帧已离线配准；角臂关系/受方过渡仍缺合格整帧，未正式安装。不能把通用代码或配准数量当作招式完成。
- 已补电脑空中受身、格挡反击、保守两格爆气的真实输入策略，以及训练录制换边方向复现；未以增加无敌/扩大判定强保成功。回执在verification对应computer-*与training-tape-facing文件。


## 获取与运行

- 2026-11-07：`checkpoint/full-20261105-0020` 已合入 `main`（fast-forward），`code-20261105-0011` 的 17 个文件内容已被 full 覆盖，两个远端分支均已删除。当前唯一开发分支是 `main`。
- 2026-11-07 本机环境：Godot `4.7.2.stable.official.ed1daf0bf`（Homebrew `/opt/homebrew/bin/godot`）、Python 3.13 venv、Pillow 13.0.0、NumPy 2.5.4、git-lfs 3.8.1，macOS arm64。全量回归 36→41 项，见 [verification](verification/README.md)。
- Godot AI MCP 插件已启用（`addons/godot_ai`，v4.4.1，上游 MIT）。它在 `project.godot` 注册 `[editor_plugins]` 和 `_mcp_game_helper` autoload；后者在编辑器内直接返回、在游戏进程内只在调试器通道激活时工作，不影响正式运行。
- Godot继续通过tools/godot_lock.py串行导入/运行，隔离XDG目录。未开放的月亮候选必须从已冻结审片入口装配，不修改正式选人开关。旧冻结合同在依赖变动后会按SHA拒绝，不能篡改旧合同假装可重放；需要时按现有工具新建当前合同并保留旧结果。
- 工作树可能出现已恢复LFS实体造成的大量PNG标M，不能整树暂存。仅按明确文件核SHA和diff提交。没有复制用户凭据或本机环境。

## 已完成与未通过的具体动作

下列逐条内容已在上节“当前成果与证据索引”登记，不重复。

- 银河待机／蹲起四状态族：12本人完整原帧按动作统一整图采样并脚底配准，不逐相按面积缩放。真实Down两轮、240tick与独立回放、21项检查通过；8组352PNG技术通过，125原输入选样覆盖全部12相与首轮边界/idle回环，静帧带观察接受。未验实速/音频，idle拳位回环与rise头长细差保留；银河仍不可选，不等于S2–S7齐备。[配准/逻辑](verification/galaxion-crouch-resume.json)、[图形](verification/galaxion-crouch-graphical-review.json)。下一项应继续查银河已有本人整帧；前走缺明确换腿、turn中相错头且无修复源已记录，不反复扫描月亮旧缺帧。

- 月亮轻击三连：现有16整相配准与1/2/3段真实输入候选，[逻辑/主游戏记录](verification/luna-light-chain-resume.json)。候选不等于全套装甲开放。
- heavy七相、tackle八相、dash_light五相：已做双向720/1080命中/防御/落空图形与回放，见[heavy](verification/luna-heavy-graphical-review.json)、[tackle](verification/luna-tackle-graphical-review.json)、[dash_light](verification/luna-dash-light-graphical-review.json)。保留站防高举手与较低接触点不一致；dash_light只验前置dash五相，未覆盖完整九相；白闪受表现时钟影响，不称跨运行FX确定。
- sweep七相：真实下段/倒地/蹲防规则已验证，但04→05换脚回弹的收腿过渡未过，蹲防受击切高防素材缺口仍在。[回执](verification/luna-sweep-graphical-review.json)
- dash_heavy六相：真实输入、空中轨迹与接触回放成立；03腾空→04低伏、05弓步→idle站立两处硬切未过，不通过拉长帧或换顺序伪补。[回执](verification/luna-dash-heavy-graphical-review.json)
- 垂直跳九相：真实起跳/空中/落地与回放已核，静帧落地屈膝起身可辨；land01→idle脚位一次收窄仍保留，未验实速顺滑。[动作回执](verification/luna-vertical-jump-graphical-review.json)。原对手脚底被HUD覆盖的问题已由本轮全局镜头及候选装配修复，最终结果以[HUD回执](verification/hud-framing-main-review.json)为准，不改写旧失败记录。
- 前跳八相：真实斜上输入与位移/回放通过；42→43骤收膝、48→49大角跨度、64→65倒置直切站立未过。[回执](verification/luna-forward-jump-graphical-review.json)
- 后跳、背身/闪避反击与空中攻击：已有后翻缺展开中间帧，背反缺收腿、闪反无实际击肋相；没有合格独立月亮空攻源，不用基础形态/别的装甲或飞踢改名冒充。见[后跳缺口](verification/luna-back-jump-source-gap.json)、[反击缺口](verification/luna-s2-counter-source-review.json)、[空攻缺口](verification/luna-air-attacks-source-gap.json)。
- 后撤backstep五相：复用已有新03/04消除旧三腿源，01整图下移4px接地；真实双后两轮各80px、独立回放及8组192PNG技术通过，但02末→03首抬膝直切宽站/立躯干，缺完整落脚中间相，视觉未接受。[回执](verification/luna-backstep-graphical-review.json)。后走缺腿交换、完整dash缺B/A换腿、dodge后仰→低跪→站立缺过渡，不能把旧offline-four当完整闪避。
- 哥莫拉三级背掀仍未安装：已有通用root与显式空接保相代码、离线18+6整帧配准，但受方角臂/离背过渡缺合格整帧，不用整人瞬移规避穿角。见[基础机制](verification/gomora-root-resume.json)、[离背候选拒绝](verification/gomora-departure-candidate.json)、[通用空接](verification/gomora-current-capture.json)。本轮不收费补画。

## 全局镜头修复的范围与验证

正式HUD提供真实布局安全区，考虑上下栏、变身提示和训练板；双方当帧Alpha与仍持握实体合并后只做共同世界缩放/平移。居中/镜像/缩放/旋转的真实Sprite轮廓参与取景，不改单人站位、模拟坐标或判定。单位边界746项及相关回归通过。

实际图形最终20组328PNG：正式far/near各4组、二级持岩4组、月亮垂直跳原带/回放8组。冻结tick/相位/尺寸/SHA和最终HUD安全区逐图核验；真实检查训练板、半血变身提示、长尾倒地/起身/挑空、持石最高位、原1080左向跳跃顶点脚底。Luna与旧v5模拟逐tick相同。[完整回执](verification/hud-framing-main-review.json)

保留三项真实历史：05三级持岩被固定屏幕必杀立绘遮盖，不能以world bounds通过自证可见；Luna hud-v1漏接provider而原遮脚不变；hud-v2漏接绘制前布局回调，首组19PNG被新门拒绝、余七组没跑。hud-v3补齐后才完成8组通过。三级立绘叠层本身未修，离手投射物/刀光/光束不纳人物取景，刻意Ready/Fight等覆盖不作全屏障碍。Luna旧审片入口隐藏训练板导致保守缩放，不能声称理想取景；正式far另保留训练板验过。无录屏、音频、实速或真人输入验收。

## 完整需求逐类依赖复核

以18c5305d为本次读取基线，核对原计划、当前消费者及已有验收，不重扫被拒原图、不运行新测试，也不把未验收写成运行失败。本轮没有发现另一项证据充分、可仅靠现有资源直接安装的关键功能，故不额外修改战斗规则或新增辅助工具。

- **核心实战与对局闭环**：现有整数60tick、输入解析、投技/拆投、受身、追击、反制、爆气、形态与KO/再战均有实现和专项证据；上方追击中断、弹体方向/跨招隔离、持续束反射已修。此次静态复核未确认新缺陷，不声称全量无bug。只有出现具体可重现玩家路径才继续改，不能用扩大判定或增加无敌补表面成功。
- **输入、电脑、训练和回放**：Q/E/I 与原搓招共存，重绑/保存/冲突处理已在input/devices与正式设置中；电脑反制策略、训练磁带方向、F4生命周期/换人加载/输入显示已分别修复。仍待有效原生2P物理键环境核非零录带与循环游标；当前云桌面逻辑箭头/物理码不匹配不是产品bug定论，不通过改绑定或注入输入假验收。手柄硬件覆盖也不因路由代码存在而宣称完成。
- **正式名册与全动作矩阵**：按definition的playable/pilot_playable当前18角色可装配，不等于18角所有原剧动作和美术已完成。selection编辑清单是298身份、387形态，其中形态项18个implemented；不能当最终全集总数，coverage仍有作品/身份资料余项。新增角色依赖本人版本依据和完整动作/受击/被投/技能/声音，不把目录或静态模型计成可玩角色；图鉴新增继续暂停。
- **哥莫拉三级背掀**：最新第三版中间链已用现有完整源做12带逻辑与八带主游戏回放、正常/诊断图形，仍是内存候选、未安装。下一步仅沿现有[中晚承托记录](../tools/rebuild/gomora/back_lift_resume/MIDLATE_SUPPORT.md)完成可核实原速与首承重/近角等整招边界，不重复已做反馈锚点或盲目补相。缺可靠连续观看能力不证明动作失败，静帧也不能证明1tick原速顺滑；本次不替正在推进的候选作安装裁决。
- **八装甲**：月亮、银河仅部分候选及明确缺帧结果；太阳、法德兰、雷基尼斯、特莱加隆、瓦尔基涅斯、加美顿目前只有model，未有合格S2–S7源可直接接入。完整动作、技能/武器/声音及变身闭环未齐，不开放。现用变身登记为泰罗、哥莫拉/雷德王到EX，和八装甲完成度分开计算。
- **三槽与原剧武器**：初代、内隆嘎、布莱克王、杰顿独立三槽仍有明确同技分档缺口；其他重复招名只列待依据/实际差异核对，不仅凭名称判失败。欧米伽三级按近斩＋光线实际数据核，不称纯光线。亚刻剑、布莱泽剑、欧米伽八斩、提欧箭/盾/锯剑等已装，不重复安装。余项依赖具体本人/形态/作品武器清单与独立持武器整帧；本次未找到合格且未接入的新源。依据见[三槽与形态规范](COMBAT_DESIGN.md)、[武器规范](ART_PIPELINE.md#武器覆盖与记录格式)及[现源核查](verification/other-existing-fullframe-availability.json)。
- **本人声音**：runtime.voices中亚刻仅有合体前卢提昂登场对白，提欧无角色语音映射；布莱泽当前五状态语音来源记original，不冒称原剧原声；欧米伽当前五个独立语音ID记episode。关联记录未登记听审不等于实听失败。来源账本1207条与注册sound1171项都不是实际触发覆盖数。需本人正确声源、触发上下文及有效听审，不挪用别人声音或以拟音冒充；不为补数批量接线。
- **场景、镜头和表现**：十九场的天空/分层/ambient与选择/BGM已登记，纹理路径存在不等于材质、实速与全场画面验收。双方人物轮廓/HUD取景已修；持续束超视口、白闪遮接点、旧站防/低防姿势等分别保留原回执，不以重复镜头检查代替缺失动作。未发现新的合格未接入场景；场景来源、具体材质与声音需要逐项验收而不是重新制作已有十九场。
- **交付与环境验收**：原生截图、真实InputFrame回放、硬件输入、原速与听感是不同证据。缺少其中一种不能自动判游戏功能失败，也不能用其他检查代替。按实际远端核验保存；不新增备份仓库或复制私人存档。

依赖顺序：先收尾正在推进的哥莫拉既有候选；其他动作只在出现合格独立完整源后实施；声音和原速需相应来源/实际观察能力；有效2P及目标引擎属于验收环境依赖。没有新的真实缺陷证据时停止扩展扫描，不为了保持忙碌再建测试、UI便利项或重复审片。各项旧红灯与未通过范围继续保留。

## 后续优先级

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

## 验证与发布边界

镜头单元746项、相关pixel_ui/ui_facing/phase3_air及本批原输入/独立回放通过；不等于全项目全量或完整美术/声音通过。图形使用真实原生窗口与冻结tick截图，无录屏、无音频及真人硬件输入验收。月亮land→idle收脚、保守缩放、站/低防手位、三级必杀立绘遮普通world等限制仍在。

2026-11-07：`checkpoint/full-20261105-0020` 已合入 `main`，261 个新增 LFS 对象已逐对象核对 SHA/大小并本地拉取完整，`git lfs fsck` 通过；两个 checkpoint 远端分支已删除。以下 2026-11-05 记录为历史。

## 2026-11-03 历史清理交接记录

更新：2026-11-03（当时状态，不代表现行）。用户当时停止此前开发，改为清理仓库、上传GitHub并交接；不自动续跑生图、图鉴、装甲或旧Goal。

本轮清理与验证已完成：旧工作树、历史Git/LFS、废弃审片/缓存/生产副本直接清理，未做备份；按实际引用保留现用资源与有效在制材料，合并完全相同的文件，统一规范与验证入口。修正现用声音台账的旧副本路径，合并两只EX的重复锁定选人格。

私有GitHub仓库：https://github.com/alanbulan/UFEneo 。清理基线f2709a7已上传，全部LFS对象的远端下载可用性与大小核对通过。本文作为最后的交接提交，交付分支main、标签clean-baseline-2026-11-03；验证回执见verification目录。

当前仍可运行正式主游戏：标题→对战/训练→选人→场景/BGM→对局。四新英雄本体、两EX及原角色的当前实现保持；目录清理不等于招式、美术和声音余项完成。

最先需要交接的未完工作：月亮装甲轻击三连、哥莫拉三级背掀与初代受方配对；八装甲完整战斗矩阵、全名册独立三槽/武器与本人声音仍未完成。当前具体运行数据优先于旧制作收据里的阶段字段。

没有费用上限。图鉴走 MCP 生图（Codex 订阅），不消耗旧脚本直连路线的美元账本。

少量本轮临时清单和Python缓存的删除被自动审批拦截，未给具体原因；它们仍在本机且已排除上传。

规则见根AGENTS，完整设计/招式矩阵见根REBUILD_2D_PLAN。

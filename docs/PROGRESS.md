# 当前状态

更新：2026-11-05。用户已明确恢复开发；本轮只利用现有素材，不发收费生成，不调用用户Codex。下面2026-11-03清理交接保留为历史，不再把当时“停止开发”误作本轮状态。八装甲未齐，仍不开放。

## 当前成果与证据索引

- 回放输入复盘：修复F4播放时训练图标/F1历史停在录制末尾，以及成功加载残留旧上一招/反馈。仅成功装配后清显示、每tick沿实际录像输入更新，坏文件拒绝保留显示；不改模拟或录像格式。既有回放测试同一红绿通过，三带字节不变、逐tick模拟hash保持；5项相关回归及normal关闭通过，原生画面待验。[回执](verification/replay-input-display-review.json)

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
- 月亮S2：轻击三连、heavy、tackle、sweep、dash_light、dash_heavy、垂直跳、前跳已建立现有整帧候选与真实输入/回放路径，但不是完整装甲完成。各动作状态看[接续索引](HANDOFF.md#2026-11-05-开发接续索引)，尤其扫腿/飞踢/前跳的视觉缺帧仍未通过。
- 月亮后撤backstep五相已复用现存新03/04修复源，真实双后每次80px、两次触发与回放完成；8组192PNG技术通过，但02抬膝到03宽站仍缺落脚中间整帧，视觉未接受，不算动作完成。[回执](verification/luna-backstep-graphical-review.json)
- 哥莫拉三级背掀：通用root覆盖及显式空接保相机制有逻辑回执，18攻方/6受方现有整帧已离线配准；角臂关系/受方过渡仍缺合格整帧，未正式安装。不能把通用代码或配准数量当作招式完成。
- 已补电脑空中受身、格挡反击、保守两格爆气的真实输入策略，以及训练录制换边方向复现；未以增加无敌/扩大判定强保成功。回执在verification对应computer-*与training-tape-facing文件。

## 验证与发布边界

本轮实际引擎为Godot4.6.3，项目要求的4.7未验。镜头单元746项、相关pixel_ui/ui_facing/phase3_air及本批原输入/独立回放通过；不等于全项目全量或完整美术/声音通过。图形使用真实原生窗口与冻结tick截图，无录屏、无音频及真人硬件输入验收。月亮land→idle收脚、保守缩放、站/低防手位、三级必杀立绘遮普通world等限制仍在。

2026-11-05 07:18 UTC已核验远端checkpoint/full-20261105-0020到10bd14fdb7ab3189aceea0410fd8b5cd89b31f77；远端main仍为99a084d8a03647d7c84546ba36cf0a4617f9c553。最新开发在checkpoint分支，不可只取main冒称最新。此前新增LFS已逐对象远端下载校验SHA/大小通过，GitHub已认证，不沿用早期限流/待登录结论。本次最终回执与文档另随后续检查点保存，以实际远端核验为准。

## 2026-11-03 历史清理交接记录

更新：2026-11-03。用户已明确停止此前开发，改为清理仓库、上传GitHub并交接；不自动续跑生图、图鉴、装甲或旧Goal。

本轮清理与验证已完成：旧工作树、历史Git/LFS、废弃审片/缓存/生产副本直接清理，未做备份；按实际引用保留现用资源与有效在制材料，合并完全相同的文件，统一规范与验证入口。修正现用声音台账的旧副本路径，合并两只EX的重复锁定选人格。

私有GitHub仓库：https://github.com/alanbulan/UFEneo 。清理基线f2709a7已上传，全部LFS对象的远端下载可用性与大小核对通过。本文与HANDOFF作为最后的交接提交，交付分支main、标签clean-baseline-2026-11-03；验证回执见verification目录。

当前仍可运行正式主游戏：标题→对战/训练→选人→场景/BGM→对局。四新英雄本体、两EX及原角色的当前实现保持；目录清理不等于招式、美术和声音余项完成。

最先需要交接的未完工作：月亮装甲轻击三连、哥莫拉三级背掀与初代受方配对；八装甲完整战斗矩阵、全名册独立三槽/武器与本人声音仍未完成。当前具体运行数据优先于旧制作收据里的阶段字段。

本机最后已记账占额53.384310/60美元（2026-11-02，含旧未知10美元），不是账户余额。此轮没有生图收费或新录屏。

少量本轮临时清单和Python缓存的删除被自动审批拦截，未给具体原因；它们仍在本机且已排除上传。旧素材与旧历史已清理，具体范围和接手限制见HANDOFF。

唯一接手文档：[HANDOFF.md](HANDOFF.md)。规则见根AGENTS，完整设计/招式矩阵见根REBUILD_2D_PLAN。

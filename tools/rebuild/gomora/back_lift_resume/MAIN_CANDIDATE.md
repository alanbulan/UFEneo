# 210背掀主游戏内存候选

## 范围

候选只在创建对局时替换内存special3、受方专用state_frames和表现clips，不写正式content/assets、不替换正式三级。实例化app/scenes/main.tscn，保留正式输入路由、模拟、HUD、镜头和完整Alpha取景。不创建独立预览场景，不设置开局位置、高度、能量、HP或朝向。

R02第五版、收臂过渡、展开R03统一210×105；先检查固定髋点名义解，保留各原源±50px估计不确定性。原32释放，32/33收臂，34–39展开R03；40/44分别用旧04/05完整相，再接现装thrown_back四完整相和down。根目标来自整数骨盆积分，不用线性release目标。唯一撞地impact68，伤害490。mode=root离背不等于已覆盖throw_released机制。

00/01仍是已知失败的旧完整帧，用来暴露实际入口至承重的缺相问题，不把整个动作美术标通过。倒立/翻滚后四相髋点也是待审估计，不能只据成功落地就签收接相。

## 生成候选合同

固定Forge环境下先运行review_builtin_bridge.py --width 210，再运行build_memory_candidate.py。输出reports/gomora-builtin/main-candidate210/contract.json及两幅整帧atlas，绑定源SHA。

可选--air-body-subregion只用于复现普通前跳入口诊断：原初代没有diagonal_air，添加现有flip_forward四完整帧的可见胸腹子区为索引1，同时完整保留原fallback索引0；子区全部包含于原框，hurtbox并集不扩大。正式数据不改，成功背后垂直路线不依赖此补丁。

## 真实输入路线

普通正面前跳路线已确认被当前几何拒绝：一条轨迹越背后太远，另一条因正式推挤留在前方；末下降高度45→31又跳过旧R00允许的36–39高度交集。保留失败回执，不宣称全局任何输入都不可能。

rear_vertical_hit路线全用真实物理键：哥莫拉持续Q蓄满并保持朝向，初代先斜跳越过、落地后从背后走近并转向，再作垂直跳；哥莫拉直接从charge按P，避免idle自动转身。原合同gap68、second-jump-delay16已有真实命中记录：相对根约[-44,45]，入口差[13,5]在14上限内；不用注入朝向或扩大捕获框。它证明背后垂直来者可抓，不代表普通前跳路线也通过。

## 主游戏与回放入口

全部Godot命令经tools/godot_lock.py。runtime_run.py负责隔离用户数据、冻结源SHA及检查引擎错误；main只支持真实云桌面图形显示，headless不冒充画面。

示例参数：main --contract reports/gomora-builtin/main-candidate210/contract.json --out reports/<新目录> --case rear_vertical_hit --owner 0 --gap 68 --jump-delay 16 --size 1280x720。反向owner1，1080使用1920x1080。输出目录必须不存在，不能覆盖旧结果。

独立replay进程不运行输入driver，读取已记录原始输入包逐tick比较hash；保存format6后另建模拟再次重放。拆投1/2/3/4使用rear_vertical_tech1等明确case，判据仍是正式3tick边界。

## 尚未验收

图形720/1080双向与完整接相结果以实际新回执为准，本入口本身不代表截图已产生或通过。前00/01头肩穿角、髋点敏感性及后相人工读点限制始终保留。未安装，无真人键盘验收；未生成录像时不得声称有录像。

## 现有完整帧整链：2026-11-05新增复核

当前新审查合同是reports/gomora-builtin/main-chain-20261105/contract-roi-corrected.json，SHA256为2cc33eb4669f79349a6f32226a3e639a7d55d3433ec966d733dd1fbc9fcb85bd。构建冻结dad21363，harness逐字节保持9918e376。原main-candidate210和本批初始8ac4合同及10case记录均保留，不以新结果覆盖旧失败。

- t20–23 R00第二版、t24 R01、t25早相、t26–27中相、t28–29晚相、t30–31 R02；每张整图仅固定一次共同体尺注册，受方256×320/anchor[128,288]，完整矩形入格。旧R02与离背后整格pad104，逐像素RGBA和世界偏移保持。
- 不改攻击方捕获框、14px入口门槛、t32之后离背/翻滚/落地逻辑或t68唯一伤害。新前段实体接点及骨盆路径见gomora-main-chain-registration.json。
- 两向hit、tech1–4共10case真实自动物理键与独立format6回放通过。中段ROI勘误只改变绑定review元数据，另存修正版合同并重新10case，逐项输入、hash和内容指纹相同；不是假称旧资源SHA仍有效。
- 两向720/1080真实main共144张原生图，实际窗口尺寸、帧、state/hash和PNG SHA核通过；四份实际main输入又各独立及format6重放通过，每组760观察、685模拟tick，t20–31实际sprite/root/anchor匹配新合同。费用3000能量/50体力，raw18捕获、raw68唯一490伤害，最终落地退出。

已知问题：正常主游戏FX下，R00头脸可辨，但胸髋被火焰挡住；R01/早/中/晚烟尘遮住接触及换腿，不能据这些图签承重或1–2tick连续顺滑。bridge胸颈仍贴角，R03之后明显离背；倒置及落地双方全身、长尾与HUD间隔可辨。云桌面无当前可用连续录屏接口且软件渲染慢于实速，因此无录屏、实速或听感验收。候选仍accepted=false、installed=false，正式三级未覆盖。

中段初次“下移1px造成2px头交叠”的标注已公开更正：原ROI误取下方躯干，非头；正确头区的重算与原错误来源均保存。此更正没有改变原源、图集或运行逻辑，不以头ROI名义0代替全头颈验收。

当前证据：
- docs/verification/gomora-main-chain-20261105-logic.json
- docs/verification/gomora-main-chain-20261105-graphical.json
- docs/verification/gomora-main-chain-20261105-main-replay.json

下一步不是继续盲目生成。先在能看清新前段的明确诊断观察及可核实的运动证据中检查接触与tick27→28抬腿，再决定是否需要素材或时序修改。当前没有修改/隐藏正常FX；任何诊断显示也不能替代正常显示验收。未过不安装。

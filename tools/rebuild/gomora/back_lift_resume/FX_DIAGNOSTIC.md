# 仅候选FX隐藏诊断

本轮授权仅创建候选诊断观察：视觉上暂隐藏FX，不改变真实模拟、正式显示或产品，不代替正常特效验收，不安装候选。

## 已核正常遮挡根因（尚未修复产品）

真实主游戏owner0普通显示trace在tick255/raw18产生hit事件，move=special3，坐标x451/height117，feedback.spark=impact_hit、flash=0、hitstop=4，尚不是raw68摔落伤害阶段。

presentation/combat_feedback.gd的sync在任意special3命中时调用finish(sim,e,fb,"hit")。当前候选feedback没有finish_effect，因此finish回退spawn("explosion")。这会在刚捕获时生成大爆炸及烟尘，覆盖R00至中晚相；不是这段受方动作本身绘有火焰。另flash赋值使用clampi(...,1,2)，所以flash=0也至少显示1tick白闪。

正常显示证据仍在reports/gomora-builtin/main-chain-20261105/gui/及docs/verification/gomora-main-chain-20261105-graphical.json，不能用诊断结果覆盖。

## 诊断边界

采用单独入口与runner，必须显式开启diagnostic_fx_hidden。只在渲染前隐藏attached_slots、weapon_trails、feedback.particles的独立视觉节点，并覆盖hit_flash shader参数以暂不显示白闪；不删除粒子、不跳过反馈更新、不改计数、模拟、镜头、双方纹理/坐标/层级或动画。正常harness不变，输出必须标明仅诊断。

额外保存raw20–32逐tick实际截图及frame/hash绑定，不能插值、补造中间图，也不能冒称原速录屏。诊断与正常同输入必须逐tick状态、事件、费用、捕获和落地一致。实际验证结果另附回执，不因本设计文档假称通过。

## 可评估的修复方向（未执行）

候选feedback显式设置空finish_effect可避免捕获hit自动回退大爆炸；若需要摔落终结反馈，应绑定实际throw_slam，而不是抓住瞬间。也可评估专属小范围抓取反馈，但不得擅自改全局special3反馈策略或删除其他招式终结效果。白闪0是否允许应作为独立显示规则决策，不因诊断而改正式shader或计数。

这些仅为源代码与真实trace支持的提议。必须先看清诊断中的真实接触与换相，再决定必要修复；即使正常FX不再挡视线，穿体或动作跳变仍需独立解决。

## 去FX后仍暴露的动作问题

首组owner0-720的真实逐tick截图已人工核对raw23、24、27、28、32。去FX只是移除了烟火和白闪，没有改变背甲对受方的实际遮挡；R00头脸可见，但背甲后方的髋腿接触并不能由此证明正确。

raw23→24同时切换A05→A06和R00→R01，受方躯干倾角与腿部显露出现单tick差异。raw27→28同时切换A06→A07和mid→late，腿从斜下延伸变成近水平屈膝后摆，明显差异不来自烟火。raw32离背bridge胸颈接近角尖，仍不能签完整角冠扫过净空。以上是实际静帧观察，不是实速运动结论，也不因名义髋点及局部头ROI通过而放宽。

下一步应先把受方可见膝点轨迹与承载方换相绑定，分别检查A05→A06的背面落差和A06→A07的腿摆时机。仅延长现有帧不能补出缺失姿态；仅移动整人又可能破坏腹侧承重或头角安全。若合理时序不能闭合，必须提出准确的完整帧缺口，不能用逐帧缩放、旋转、瞬移或改层级掩饰。当前不再盲目生成，不安装候选。四组图形及独立回放另由专用回执记录。

独立几何复核补充：raw24→25→26后摆方向及双腿逐渐露出可辨，未见明确换腿证据；raw23→24脚的突然显露仍无法区分正常绕出背甲轮廓与换相突现。不能仅凭遮挡断言穿体。raw29→30还有较小的屈膝上抬，需原速节奏检查。当前云桌面没有已提供的连续录屏能力，固定帧率软件渲染也不代表实际播放速度，故本批没有原速录屏或听感验收。

四组图形诊断已完成，共196张原生PNG（每组49张），每组760观察。专用回执：`docs/verification/gomora-main-chain-20261105-fx-diagnostic-graphical.json`。所有实际帧/状态绑定及正常模拟对照通过，双方body_node严格一致；序列化末位浮点差最大9.98e-18如实保留。技术通过不解除上述美术限制，正常144图保持原结论。

## 候选正常反馈修复及实际画面

后续已获明确授权，只修候选正常反馈，不再隐藏FX。最终合同为reports/gomora-builtin/main-midlate-feedback-local-20261105/contract.json，SHA c5fb548202e7b01bd440777af9d97a38a38c1f087500adf01174574cbddf30b7，逻辑冻结9924f3bc。

生产呈现原本已支持finish_trigger=throw_slam，因此无需修改生产代码。候选仅增加finish_effect=explosion和finish_trigger=throw_slam，并把spark改为已有impact_light。第三项不是随意换样式：实际审计发现旧impact_hit不在效果注册表，旧spawn调用根本不创建局部节点，捕获可见的大烟火来自默认explosion。原失败/未注册证据保留，不通过放松断言假称保留局部反馈。最终实际节点审计严格要求impact_light存在。其三相各2tick，未删捕获白闪、停顿、落地dust或其他角色反馈。

两向命中、tech1–4及真实落空共12case、独立format6二次回放和真实UfeCombatFeedback节点审计通过。capture tick255生成impact_light而非explosion；正常命中/tech4在真实slam tick309生成唯一explosion；tech1–3及whiff无爆炸。人物/比赛状态、费用和剥离三个显示字段后的事件与旧合同一致，flash/shake计数一致。内容指纹不同如实保留，不能宣称所有hash相同。正式core/presentation/content/app/assets均未在本次提交中变更。

正常命中双向720/1080四组、tech1双向720两组、whiff双向720两组已完成，182张原生PNG（4×37+2×7+2×10）。回执docs/verification/gomora-midlate-feedback-local-20261105-graphical.json。实看中段不再被捕获烟尘遮挡，t27上腹支撑和头角可以直接在正常显示观察；命中当帧仍有局部火花/白闪，真实摔落才出现地面亮芯和后续爆炸烟团。拆投/落空无slam，受方HP1000，未见误终结爆炸。

## 新显露的落地效果限制

落地explosion沿现有中心anchor[72,72]放在真实height=0。四相Alpha下缘108/121/125/129，使最大57像素落到地面以下，实际body-17原图显示下方火焰烟团被能量/体力HUD覆盖。人物本身完整，这不是人物/HUD交叠，但效果显示仍有问题，不能隐藏不报。

只读评估：落地专用效果别名复用同一完整图、采用地面锚点（例如y约120），可让最大下缘仅在地面下9像素；须再核实际位置、扩散起点和HUD。此方案尚未实施，不改当前冻结结果，不移动真实伤害事件或镜头来掩盖。当前反馈时机修复有效，但动作跳差、原速录屏/听感未验及落地效果HUD覆盖仍保留，未接受整个动作，未安装正式三级。

八份实际图形trace的独立及format6二次回放已通过；实际impact_nodes再次核捕获impact_light/无爆炸、slam唯一爆炸、tech/whiff全程无爆炸。回执docs/verification/gomora-midlate-feedback-20261105-main-replay.json（2d37689f及限制补记3a1578ec），含182图原尺寸SHA验证。

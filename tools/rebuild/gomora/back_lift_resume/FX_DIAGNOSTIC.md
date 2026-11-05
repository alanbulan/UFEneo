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

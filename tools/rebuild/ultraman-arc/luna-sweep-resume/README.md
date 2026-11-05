# 月亮装甲S2扫腿候选

按既有production-plan顺序，tackle之后的crouch_light接触相无腰线出拳，crouch_light2无清楚肋下探拳，保留素材缺口。sweep第2/3相确有撑地低扫腿，使用本人既有七张完整源继续候选注册；不收费生图、不改core、不开放未齐装甲。

## 来源、尺度和真实脚框

七张实际provider源1254×1254 RGBA逐项核旧frames.json的SHA；统一整张缩到159方，固定Forge模块、RGB32色色板、Alpha128，再仅平移到320方。x固定80，真实最低足底对齐280，不切肢、不旋转贴肢，不沿用旧0.097729～0.114720逐相面积缩放。

第2相旧客户端整源在rejected/raw.png，原因是透明角像素检查失败而非动作缺失。此处使用现存匹配SHA的provider源免费Alpha128净化，样本真透明、无碰边；不重发收费请求，不回写旧拒绝状态。

第2/3相样本实测脚面矩形[138,123,150,135]、[140,115,152,127]，平移[80,140]、[80,141]后局部攻击框[58,5,12,12]、[60,12,12,12]，实体Alpha约90.3%、89.6%。其他相无攻击框，不沿用本体26～27宽框保命中。原6/7/15 tick、65伤害、30体力、0能量、下段/倒地、推退8与取消位移均保留。

## 真实下蹲输入与主游戏

候选必须先保持下方向超过crouch_start的6tick，再按下+HEAVY（K），不能直接设置状态。下蹲开始、保持、起身使用本人crouch-family-repair-20261102-v1/offline-nine-registered-v1三条各2相完整图集；该旧依赖strict_size_passed仍为false，不冒称本轮重生成或严格比例通过。

对手蹲防采用下+GUARD；额外检查站防仍被下段击中。双向命中/蹲防/落空/站防共八逻辑案例，验证真实倒地起身与原InputFrame独立回放。正式main候选通过tests/review/fighters/ultraman-arc/luna_sweep/main_entry.gd进入，不建独立研究场景。图形沿用原生窗口稳定门、单tick暂停截图、训练板隐藏但正式HUD保留。

prepare.py/register.py拒绝覆盖已存在候选；test_check.py只读核源、整图保真、Alpha/色板、时序与框；main_bundle.py封存资源及代码SHA，新合同不得覆写旧报告。Godot必须经python tools/godot_lock.py串行并隔离用户数据。

## 验收边界

第3→4→5相收腿脚位接续须实际主游戏重点核验。逻辑通过不等于美术通过；严格头身比例、完整S2/S2–S7、本人声音、目标4.7和真人硬件不能据候选测试宣称完成。无录屏。

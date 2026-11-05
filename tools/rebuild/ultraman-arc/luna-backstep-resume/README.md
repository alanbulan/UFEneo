# 月亮S2后撤五相候选

只用现有本人完整源，不收费、不切肢、不改core或开放装甲。新注册在 `art/fighters/ultraman-arc__luna/stage2/backstep-registered-20261105-v1`。

`register.py` 用既有Forge RGB兼容配方重建1024→159整图，与旧offline-five逐像素一致后平移；仅01下移4px，五相实际鞋底bbox下边统一280。03/04用20261102 request002完整两腿源，原图弱Alpha和最高254保持；只派生128二值，不声称原生干净透明。根本轮签收限素材/配准，art/strict_size/installed/playable仍false。

`main_bundle.py freeze --root-review .../root-review.json --out reports/luna-backstep-resume/contract-vN.json --engine /opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64` 冻结当前依赖。`run --contract ... --out ... --headless` 验左右原带/独立回放；去掉headless跑左右720/1080实际原生窗口。所有Godot由工具内部经godot_lock串行。

入口仍实例化app/scenes/main.tscn，只替换首次定义工厂。真实双后InputFrame在38/40、78/80，两轮验证恢复后再次触发；建sim后不写状态/位置。每次首tap沿旧本人walk_back作单tick输入前导，仅移动2px，不代表后走八相动作已通过。40/80进入后撤tick0不移动，随后16次每次5px总80px，边界回idle；五相时钟[3,3,4,3,3]不改变规则、无敌或体力。

保留正式HUD和训练板，继承provider、overlay及frame_pre_draw接线。截图停模拟，post_draw核双方state/sprite/region及最终真实Alpha/HUD安全区，8稳定帧且至少500ms窗口验证。图形交专员串行实看02→03及04→idle，不预判顺滑。无录屏/音频/真人硬件输入验收，4.7未验。

本批按顺序跳过：walk_back无完整腿交换；dash02/04均近亮腿前、缺B/A交替；dodge后仰→低跪→全站硬切，旧offline-four并非六相。不得据现成图数宣称完整。

v1实际失败：共用旧walk异步截图触发cycle-0-phase-00缺新request；自己会话Ctrl-C停止（130），旧日志/合同保留。v2预先关闭共用walk旧截图键，自己的冻结backstep截图不受影响。

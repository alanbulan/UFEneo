# HUD安全取景回归

用途：修改镜头取景、HUD 安全区或相关回归时读本文件；记录该测试的边界与入口，不替代 720/1080 实际画面审查。

入口：`python tools/godot_lock.py -- godot --headless --path . --script tests/battle_framing.gd`。
使用独立 `XDG_DATA_HOME`、`XDG_CONFIG_HOME`、`XDG_CACHE_HOME`，不要污染真实存档。

正式装配由 `app/game_app.gd` 把 `hud.battle_safe_rect` 注入 `view.framing_safe_provider`。
HUD先更新内容；可用区由实际arena、上下栏和新最小高度共同限定，另避让训练信息板与顶部结算。
RenderingServer绘制前在布局变化时只收紧共同镜头，不重复更新模拟、输入、特效时钟或回近插值。
两个原生像素留白覆盖像素吸附；Ready/Fight、连击与暂停等有意叠层不是取景障碍。

保护双方当前整帧Alpha，含尾巴、倒地、击飞及烘入整帧的手持剑/矛。独立持握实体为经过图集核实的
`red_king_super1_held`、`red_king_super2_held`、`red_king_super3_held`、`red_king_rock_small`、`red_king_rock_large`。
未来独立持握实体可显式声明 `framing_entity`。本次不追逐离手飞行的头镖、剑、岩石或光束，
不声称自由投射物始终在画面内。刀光、拖尾、能量光效不按名字猜成实体。

测试覆盖动态安全区、震屏、宽尾/倒地/高跳边界、双方朝向、首次排版、两侧变身提示、训练信息、
上栏增高、结算切换当帧、Sprite居中/镜像/偏心Alpha/旋转缩放、雷德王7招逐帧实体与只读状态。
120tick相同真实InputFrame驱动双模拟，只有一侧读取HUD和镜头，逐tick比较输入和state_hash。
无研究场景。逻辑测试不替代720/1080正式主游戏图形审查；图形入口由独立主游戏审片合同提供。

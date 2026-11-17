# 月亮蹲身左短拳三端点 RAM 试排

仅本次第一拳；不改正式 content/assets、形态开关或冻结重砸链。三个槽为实际蹲架、第三版近侧左拳接触、同一实际蹲架，只有两个独立图像。3/3/12 = 18 tick 沿用正式 crouch_light，不通过延长停帧掩饰过渡缺口。

## 规则与边界

- 原第一拳全部玩法字段保持，伤害65、体力30、low、可蹲防，frame 3–17 的 crouch_light2 取消目标原样保留。第二拳未加载、未输入、未覆盖，不可称完整二连。
- 全程下方向，movie frame20只输入一次LIGHT，随后继续下方向，按正式模拟收回crouch。输入准备阶段idle/crouch_start暂用同一实际蹲架，不验收站转蹲素材。未直接赋move_id。
- 接触相拳ROI为原生像素[204,200,215,213)，Alpha紧框同值；runtime root [160,280]下为[44,67,11,13]。不含腕盘，不扩大命中框。几何比较使用的足锚[110,280]不是runtime root。
- 近距75：hit与stand_guard应各真实命中一次、65伤；block用下+GUARD应真实格挡一次、0伤；260距离whiff应不接触。均双向、原InputFrame独立进程回放。
- 本人hurtbox按各完整帧Alpha横带生成；没有位移、无敌、击飞或倒地强保连中。后胫投影归一和人工点误差只作几何诊断，不冒称骨长严格验收。

## 入口

使用环境变量UFENEO_FORGE_ROOT指向已有Forge安装。register.py从plan-v3.json重复采样整图，只写新候选目录；test_check.py独立重建并校验规则和像素。main_bundle.py freeze冻结运行依赖，run分别执行主游戏原录与独立回放。不得改已封存依赖后沿用旧合同。

本轮合同为reports/luna-crouch-light-resume/contract-v2.json。contract-first.json未执行模拟；其拳ROI为[203,199,215,213)，后按原生像素复核收紧到现值，因此第二次封存，不是失败后改玩法。离线test_check.py在v2后新增，不在运行依赖链；其SHA单独记入本轮技术收据。

所有Godot经tools/godot_lock.py串行，XDG数据/设置/缓存隔离到reports。run内部已使用锁，不应在整个run外再套同一把锁。Dummy声音驱动不是听审。图形截图捕捉期间只冻结采样，不改正式招式tick；无录屏。是否存在跳帧或静态相不足须由双向720/1080实际画面另审，不以逻辑通过替代。

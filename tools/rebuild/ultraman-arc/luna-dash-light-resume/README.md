# 月亮装甲S2冲刺直拳候选

按既有S2顺序，slide接触相03/04仍向背后伸腿，与02/05前伸相冲突；现存低姿替代源仍有同问题，站姿替代不构成滑铲，故保留缺口。下一dash_light有完整跑入→落脚蓄拳→远侧直拳→回架，可继续候选注册；不收费生图，不开放未齐装甲。

## 实际整帧与判定

五张本人provider源1254×1254 RGBA逐项核旧frames.json SHA；统一整张1254→159，固定Forge、RGB32色色板、Alpha128，整图仅平移到320方。x80，最低足底280，不按逐相面积缩放，不切肢或旋转贴肢。

仅第3相实际远侧拳伸出；第2相仍护拳，不把本体框留在空气里。拳面sample[140,50,150,58]、平移[80,131]后local[60,91,10,8]，Alpha100%。候选如实称“冲刺直拳”，不硬称旧profiles“左拳”。时序8起手/4有效/8收势，总20tick不变，原逐tick位移24、65伤害、30体力、0能量、推退8及取消反馈保留。

## 真实输入与主游戏

必须用原InputFrame双击前进入dash，再LIGHT（J），不直接设状态或挪位置。本人dash依赖已有dash-repair-20261102-v1/offline-nine-registered-v1，核原源、整帧和atlas SHA及图集字节；strict_size仍未验收，不借本体人物图。单招中途取消dash只算实际走过相位，不把它当完整9相冲刺验收，也不把缺少light2的单招候选算完整连段。

候选入口tests/review/fighters/ultraman-arc/luna_dash_light/main_entry.gd实例化正式main；左右命中/格挡/落空核真实指令、位移、65伤害、收势和独立原输入回放。图形使用原生720/1080稳定门和逐tick冻结截图，不遮训练人物，正式HUD保留。所有Godot调用经python tools/godot_lock.py串行并隔离XDG目录。

prepare/register拒绝覆写当前候选；test_check只读检查；main_bundle封新合同绑定SHA，不覆盖历史结果。03→04换前后腿回护架、严格头身尺寸须实际画面核查。逻辑通过不等于美术/声音/目标4.7通过；无录屏，不开放未齐S2–S7装甲。

## 实际图形结果

最终v2十二组720/1080双向hit/block/whiff、144张原生PNG尺寸/SHA/tick/相位/hash核对通过。实际前置dash只走00–04，tick35接直拳，tick42 height95真实接触；命中65一次、格挡0伤一次、落空无接触。03伸拳→04收臂回架未见扫腿式再伸回弹，但过渡短，静态逐相不等于原速连续性通过。

杰顿既有防御手位仍高于胸部火花；相同tick50的720右与1080右命中第4相白闪显隐不同，模拟hash正确，不能因此声称表现FX跨运行确定。未改FX或判定伪修。详见docs/verification/luna-dash-light-graphical-review.json，完整装甲仍未开放。

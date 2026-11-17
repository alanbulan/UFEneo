# 银河升拳候选

只在正式 app/scenes/main.tscn 训练装配中加载银河本人RAM定义。只使用现有完整源，不收费、不调用用户Codex；不修改core、正式招式、角色开关或用户设置，八装甲仍不开放。

保留00–06原序：00/01屈肘蓄势，02真实前上升拳，03降臂前伸但无攻击，04回护，05微蹲，06恢复。时序[3,3,5,3,3,3,3]，总23tick；Arc launcher的6/8/9仅候选调整为6/5/12，只有02本人小拳ROI有效。75伤害、30体力、launch=true、可防mid及其余正式规则保持。idle复用已验银河六相，视图复用银河crouch自己的candidate_view和真实HUD安全区/pre_draw。

## 合同与验证入口

main_bundle.py freeze --root-review PATH --out reports/galaxion-launcher-resume/新合同.json --engine GODOT_PATH

默认manifest：art/fighters/ultraman-arc__galaxion/stage2/launcher-registered-20261105-v1/manifest.json。必须有idle/launcher两组、source_order=[0,1,2,3,4,5,6]，launcher组含move、rule_reference、fist_boxes={"2":[x,y,w,h]}。源审须reviewer=root_delegated_by_user及accepted_for_formal_main_candidate=true，这只批准进入候选，不等于美术或运行已通过。

main_bundle.py run --contract 合同 --out reports/galaxion-launcher-resume/新目录 --headless

无头12组；移除--headless为双向、原生720/1080、hit/block/whiff及独立原输入回放24组。每组180tick，movie_frame=20同时发送相对本人朝向的前方向+HEAVY一次，随后neutral；block陪练全程真实GUARD。只允许tick0设位置，其后不改模拟。完整比较双方trace、原输入、状态hash、全部事件和投射物；事件两侧JSON规范化，非只比较子集。冻结controller_icons与Dummy仍加载的完整audio依赖。

每图形组基础16张：输入前idle、七相各可见首尾、归idle。起手首次可见move_tick=1，不能伪造tick0。hit另有6个动态观察点：首次launch、正高度、顶点、下降、落地down、起身后idle。同tick的多个key共享冻结状态，不推进模拟来凑图；共计划432PNG。实际轨迹必须包含正高度/最高点/下降/down/wake/idle，不接受只扣75血。保留双方真实整幅姿态、HUD和训练板，截图核实际原生尺寸及双方相位/区域/SHA/安全区。

python tools/rebuild/ultraman-arc/galaxion-launcher-resume/test_check.py

合成正负例仅检验门禁；GALAXION_LAUNCHER_TRACE_DIR可指向实际运行目录补验真实trace。独立逻辑入口tests/review/fighters/ultraman-arc/galaxion_launcher/logic_check.gd，也须tools/godot_lock.py串行包装。

本次contract-v1已完成Godot4.6.3导入、12组headless主游戏原输入/独立回放、6组逻辑和25项含实际trace的Python检查。两向均在tick26命中75或格挡0，落空0，扣30体力。真实受方轨迹：26进入launch，31首次正高度，48顶点171，50开始下降，67落地down，102起身wake，122回idle。结果见reports/galaxion-launcher-resume/headless-summary-v1.json。未提交、未启动图形，无录屏、真人硬件和声音验收。图形及美术结论以之后真实回执为准，旧light1记录不改。

## 最终实际回执

v1图形因入口观测499ms与第二次时钟读到500ms产生记录门不一致，停在18组324PNG；旧证据保留。入口已改成一次elapsed_ms同时供记录和500ms判断，未放宽8稳定帧门。合同v2经28项Python、6逻辑、12组180tick无头复验，全部模拟字段与v1一致。

graphical-v2完整24组432PNG、12对180tick回放通过，实际稳定等待501–2046ms；216原输入图的静帧覆盖完成（前162图与v1 SHA一致沿用已实看观察，新增54图实看），七相和双方升空/倒地HUD边界可带限制接受。02→03角度变化、缺渐伸相、腹部蓄力不完全符原brief、白闪/旧站防/动态缩放限制保留；tick102 wake仅trace，无专门起身动画截图。无录屏、声音、实速和真人键盘验收，八装甲仍不开放。

完整回执：docs/verification/galaxion-launcher-graphical-review.json；历史失败与最终结果不互相覆盖。

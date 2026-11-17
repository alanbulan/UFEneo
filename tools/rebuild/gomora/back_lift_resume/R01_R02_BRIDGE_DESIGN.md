# R01到R02：已有完整帧与最小过渡需求

## 本轮完成

只读核已有完整帧和现时序，没有生成、改运行合同或安装。新R01和R02v5大腿长度相近，差别主要是腿绕髋向后摆起，而不是全身平移。

## 已有帧排除范围

- registered192/00–03及candidate-179/unregistered179对应帧：头低、双臂垂下，腿虽后抬却重引角冠问题；04/05已翻转。
- assets/fighters/ultraman/animations下head-calibrated.png：vertical_jump、diagonal_light、diagonal_heavy以直立/前抬膝/前踢为主；thrown_back、thrown_air、thrown_forward、thrown_dash、hit_air、flip_back、flip_forward为仰身/团身/倒置且臂路不符。
- air_throw第0格最接近俯身收腿，但两臂前伸，不能直接插入。air_rise、air_apex、air_fall、air_tech、air_crush、air_pulse也未见满足条件的完整相。

这是明确范围内未找到替代，不冒称全库任何姿态均不可能。

## 为什么不能只调整时序

现A06/R01在t24–27，A07/R02在t28–31，A02上提及离背t32开始。延长R01保持只让静帧停更久，最终换相仍跳39/67px；不能把保持tick平均进位移假装逐tick平滑。即使近远腿对应互换，两膝仍约57/51px，不改变缺口判断。

近侧大腿约25→24px，摆向约106°；远侧约33→35px，摆向约160°。两端坐标直接平均会把大腿缩短。新相若需要，膝应先从髋右下经过左下，再到R02左上，保持自然腿长与完整连接；禁止程序旋转肢体、逐帧缩放或用根跳补腿路。

## 精确设计参考与限制

1. R01整源：art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r01-20261105/candidate.png。
2. R02第五版：art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r02-20261105/candidate-5.png。
3. 哥莫拉真实背面/角冠：art/fighters/gomora/stage4/super3-back-lift-registration/current/06.png与07.png。不能用05代替06，A05提前配R01已有头角问题。
4. 身份体尺：art/fighters/ultraman/model/model-reference-x4.png。
5. 实配位置参考：reports/gomora-builtin/r01-review/tick24-A06.png、tick27-A06.png，以及reports/gomora-builtin/bridge-review/trajectory-210/R02-final.png；都是离线配对，不称主游戏截图。

以下都是以头长约25原生像素、髋为原点、y向下的全身设计范围，不是精确骨点，也不授权程序插值：
- 若先验证一张真正中相，近膝约[-17,+18]、远膝约[-25,+23]，各约±6–8px人工范围。必须体现两膝已到左下方，不能仍在右下，也不能直接抬到R02左上。只有一张是否足够未知。
- 更细的两个相位候选：早中相近膝约[-11,+22]、远膝约[-12,+32]；晚中相近膝约[-22,+12]、远膝约[-33,+10]。此布局保持大腿长度，比直线中点合理，但不保证两张即可验收。
- 头颈保持抬高、两臂完整后收；胸腹继续被背部承接，小腿随膝被动后摆，不能主动画成飞行。肩髋与头身尺度沿两端整相保持，不能为了达到膝坐标拉长/压短身体。

## 可验证时序边界

优先不动t20入口和t32离背。若有两张合格全身过渡，可评估t24–25用R01、t26–27早中相配A06、t28–29晚中相配A07、t30–31用R02。这只是测试计划，未改合同。每相的真正腹边接点、髋/肩/膝/足连续性、近远腿遮挡与头角均须重核。

若推迟R02超过t32，就会冲突既有上提/bridge/R03和抛线，不能仅延长hold。任何时序或根轨迹改变都要重验独立回放、t68唯一伤害和最终退出。当前仍未闭合整段，未通过不安装。

量化复现：tools/rebuild/gomora/back_lift_resume/plan_r01_r02_bridge.py；回执docs/verification/gomora-r01-r02-existing-frame-gap.json。

## 下一次补相的清楚姿态设计（只设计，不生成）

### 优先反向设计晚中相

最新收腿候选的远侧膝仍在髋右下，说明从R01出发容易只改小腿。下一张建议以R02第五版为主要完整姿态参考，向前一瞬间反推：保留已经向左后摆的大腿，只把双膝从左上降低到左下，不把大腿恢复成垂直下挂。失败bridge不作为主姿态参考。

侧视草图的读法：头在右上，胸腹向右前方靠背，髋在左下；从髋出发，两条大腿都向画面左方伸，略向下，不得有任何一条大腿向右。近侧膝在髋左下较近处，远侧膝更靠左，二者高度接近但不能合成一个膝。近侧是前景完整腿，远侧是后景、最终接R02较高膝的完整腿，不能在换相时交换身份。两小腿继续弯着向左下，脚比膝更左、更低，绝不能只把脚摆到左边而膝仍在右侧。双臂完整向后收，拳沿肋部，不挡腹侧接触边。头颈保持抬高，不压向角冠；上腹被背部托住，不画主动飞行。

以约25px头长为统一身体尺度，髋为原点、y向下，晚中相目标近膝约[-22,+12]，远膝约[-33,+10]，允许约±6–8px人工观察范围；近侧大腿长度约24–26px、远侧约33–35px。数字只帮助识别摆向和骨段长度，不要求逐像素描点，更不能机械拉长腿或缩小髋。

晚中相建议真实图像参考顺序：
1. 主要整姿态：art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r02-20261105/candidate-5.png。
2. 实际位置/背角关系：reports/gomora-builtin/bridge-review/trajectory-210/R02-final.png。只以其朝右面板理解位置；这是离线两向两层配对，不是主游戏截图。
3. 较早端点（只理解前一阶段，不复制腿路）：art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r01-20261105/candidate.png。
4. 身份体尺：art/fighters/ultraman/model/model-reference-x4.png。

若需要独立哥莫拉单图而不是配对页，晚相用art/fighters/gomora/stage4/super3-back-lift-registration/current/07.png，不以05替代。

### 再决定是否补早中相

当前约160°远侧大腿摆动，只有一张中相仍会留下较大换相差，两个不同摆向更值得验证，但不能在未见整相前保证两张足够。执行顺序应先看晚中相是否真正形成双膝左下，再决定早中相，不能重复批量生成同一个下挂姿态。

早中相以通过几何检查的晚中相为主要姿态参考，再向R01反推：双大腿仍均朝左下，但比晚中相更陡、更接近向下。近膝约[-11,+22]、远膝约[-12,+32]；远膝在更低的位置，不再在髋右边。保持自然大腿长度，胸腹折身介于R01和晚中相，小腿和脚向左下，不伸直踢腿。

早中相的背角参考改用真实A06：art/fighters/gomora/stage4/super3-back-lift-registration/current/06.png，另可用reports/gomora-builtin/r01-review/tick24-A06.png理解配对。它必须在A06下沉几何里承接，不能套A07的接点。若晚相仍未达到要求，先报告失败，不自动发早相请求。

### 验证门槛

先核两膝是否都在髋左侧，再核腿长、肩髋/头身尺度、两臂两腿、真实Alpha；然后按真实腹侧轮廓在A06/A07实配，核髋、两膝、两脚与头角的每次实际换相。只有头框0交叠或髋小步不够。最终还需主游戏与独立回放，未过不安装。

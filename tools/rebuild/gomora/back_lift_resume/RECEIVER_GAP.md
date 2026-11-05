# 背掀承重完整相缺口

2026-11-05，root_delegated_by_user。只读复核现有源与完整帧，不收费，不调用用户Codex，不覆盖正式三级；无录屏。

## 实际发现

问题早于03卸重。现配准的A05/R00、A06/R01、A07/R02均让初代头、颈肩与哥莫拉大角根/脸颊占据同一区域。换整层绘制顺序会吞掉头肩或角，不能作为修复。tick40完整分离只证明晚段可避开，不代表首承重成立。

对A07/R02保持真实腹缘(112,90)共点，沿背部上缘比较：
- contact(205,224)→root[-67,-14]，contact(215,213)→root[-57,-3]：头退出角冠区域，但身体降至腰/尾根侧面，不能称背上承重。
- contact(250,187)→root[-22,23]，contact(260,183)→root[-12,27]：仍有头/角/颈拥挤。

所以接点误差0px不等于躯干贴合。上述不是所有可能配置的不可行证明，也不把全部Alpha交叠判作穿体。

原+6横向离背轨迹只作失败对照，不是正式抛向。保留合同描述为后抛/后方落地；同一初值改vx=-6、vy=15-n仍在tick40后零交叠，但00–03问题照旧。R03延迟1–4tick也仅降低交叠峰值，不能把错误承重起点变成正确动作。方向需随最终动作整段核实，不能因文件夹含front就改成前抛。

## 已有替代源核查

核查范围：art/source-index.json、六相原源/metadata、现装grabbed、thrown_forward/back/air/dash、flip_forward/back、hit_air、dive、launch_fall、bounce，以及原始grabbed/thrown_back整张。未声称全库全部普通攻击像素均已查遍。

六对candidate.provider/candidate的Alpha完全相同，alpha>0的RGB完全相同，只差透明RGB清零；179与registered192也是同姿势的处理版本，不是新增姿势。

- grabbed为直立后仰/提膝/坐姿。
- thrown_forward/air/dash、hit_air、launch_fall、bounce为仰面击飞、翻滚、落地。
- dive为主动俯冲踢。
- thrown_back首帧和flip系列部分完整倒立可作为离背后接续候选，但不能代替最低承重。
- ultraman/sources中存在旧p3throw_zetton_*来源；实看b2134b03846b316f1b30eb7923b6a9eb62a6d7ad76b457c00a9e55db6566dbef.png是杰顿倒立。不能按目录名判断身份。

本范围内没有找到可直接替换R00–03的初代C型腹侧承重整帧。

## 最小新增整帧方案（只说明，不执行）

先只设计R02最低承重完整母相，成功后才补00落背缓冲、01随俯压背、03卸重。不能先批量重做四相。04/05和现装thrown_back倒立继续保留候选，待与新母相实际接续后再判是否需要改。

母相参考：
1. 初代C型定稿：art/fighters/ultraman/model/model-reference-x4.png，SHA256 9e084ba7ff4f4ff2ed343e2d20650ebbec5b648156cddd066ad10165e68f0e71。
2. 实际哥莫拉最低承重07：art/fighters/gomora/stage4/super3-back-lift-registration/current/07.png，SHA256 359a96088d95e0a9dc29ad5e95db83f0ed72311f64e6f7f4fd57dba7a42d4114。必须用真实背缘、角冠与脸颊空间作配对约束，不能只看单人参考。
3. 现初代02原源：art/fighters/ultraman/stage5/gomora-super3-back-lift-receiver-20261102-v1/phase-02/request-001/candidate.png，SHA256 a1bd22871293a01b36c5b233280d8b409eef9c034ffb97fe0e79ee88f851b886。只作本人完整体尺参考，不继承未通过的头肩/下垂臂姿态。
4. 现装完整倒立：assets/fighters/ultraman/animations/thrown_back/head-calibrated.png，SHA256 5db5abdf1d0233ef07d7489248f01ff0577fdd60debc385d4a9a845fe5363bea。只约束离背后接续。

新母相必须同时解决：腹腰确实支撑在背上，头颈肩不穿角根，双臂为连贯真实全身反应，保持固定侧视、本人身份及共同体尺；不能靠整人抬高悬空、换绘制顺序、切肢、旋转旧帧或瞬移。输出仍为单个独立完整人物真透明源；哥莫拉只是几何参考，不烘焙进受方图。

当前没有发起任何新生成请求、没有恢复旧收费脚本。是否新增源及费用需另获用户授权；未以旧台账当当前可用余额。

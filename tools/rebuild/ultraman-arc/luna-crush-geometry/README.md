# 月亮crush端点整图比较

仅消费实际idle、旧05举顶、新双拳下砸接触、旧06护架和同一idle五槽。旧06只是回架端点比较，不当已经完成低位随势；没有编排35tick招式、攻击框或正式注册，也不运行Godot。

`build_frames()`在内存返回完整图像及几何结果。每相统一以画面左后腿膝踝投影归一到本人model近胫投影长度，整张等比采样；右前胫、头面代理点只作交叉观察。左右这里指画面位置，不套回旋单腿支撑命名。双髋遮挡，不猜测股长。关节点保守±18源像素；强制后前掌锚对齐不证明实际脚不滑。

处理使用既有固定Forge版本、RGB色板、Alpha128清理。原源真实RGBA保留低透明边噪原字节，处理后Alpha二值不冒称原生图已干净。不切肢、不局部缩放、不转贴手脚。

配置已批准Forge路径后运行：

    python tools/rebuild/ultraman-arc/luna-crush-geometry/geometry.py --out reports/luna-crush-new-check

输出必须新目录。程序重复构建两次，检查像素一致、首尾相同、整图无裁切、源SHA、固定后端和栅格取整误差<1%。结果不是整招连续性验收，真实输入/回放、双向720/1080均尚未运行。

## 下降候选v2

`--plan tools/rebuild/ultraman-arc/luna-crush-geometry/plan-descent-v2.json`只在举顶与接触之间加入新候选。原五帧像素不变，新增近肘/腕投影点供路径比较。其高护拳外观不自动判无效，拳高度处于中间也不自动通过；肩肘提前终态及真实下砸读感仍待。没有新增时序或运行判定。

## 低位随势与完整候选v3

`plan-followthrough-v3.json`包含七槽、五种独立原源姿态。新follow紧接contact继续下压；既有descent整图在回收阶段明确复用为高护拳候选，避免强插旧06开掌护架。复用不声称新相或整段倒放，也不能自动签回架通过。

`candidate-timing-proposal.json`仅提出保持原crush 12/8/15共35tick的后续RAM建议，尚未注册攻击框/运行。原招unblockable=true，未来真实GUARD测试必须按原规则受击，不能套回旋的格挡0伤。后脚比较锚[110,280]与建议运行人物root[160,280]不同。

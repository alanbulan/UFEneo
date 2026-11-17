# 蹲左拳整图同尺诊断

仅完整整图端点比较，不注册招式。plan-v3是actual crouch→v3近侧左拳→actual crouch。手工关节点约±18源像素，同后胫投影尺不等于精确骨长，固定比较锚不证明无滑步。

UFENEO_FORGE_ROOT=<已配置Forge目录> python tools/rebuild/ultraman-arc/luna-crouch-light-geometry/geometry.py --plan tools/rebuild/ultraman-arc/luna-crouch-light-geometry/plan-v3.json --out reports/luna-crouch-light-geometry-新目录

geometry.py复用既有完整图采样算法，但使用蹲拳专用schema和说明。早期v1/v2/v3临时回执来自原crush比较器，残留crush名及旧06文字不适用本动作；v3b已更正元数据且所有图字节与v3一致，没有改动被冻结crush工具。

v1/v2未满足近侧左拳，不放进左拳链。v3肩臂归属成立，仅可继续RAM几何/主游戏时序试排，不因单相宣布整招、图形或实速验收。未安装。

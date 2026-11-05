# 月亮蹲二拳接扫腿：旧整帧RAM技术探针

仅复用已有两拳与旧sweep注册整帧，不生成、不安装、不开放八装甲，不修改正式core/content/assets。旧sweep第04落脚后05再次伸腿回弹仍为美术红灯；跨招共同尺度亦未签收。此目录不混入后续新回收源。

使用当前core重新冻结，默认真实InputFrame为持续下方向，LIGHT零基20/27，HEAVY零基37。主游戏入口仍装配app/scenes/main.tscn，非新研究场景。固定输入覆盖命中、站防受低击、蹲防和落空双向，各独立重开180tick原输入回放；语义矩阵另覆盖早晚重击、持续按住、距离推退与逐tick受方状态。

运行（Godot通过godot_lock串行，运行器隔离XDG）：

    python tools/rebuild/ultraman-arc/luna-crouch-sweep-chain/main_bundle.py run --contract reports/luna-crouch-sweep-chain/contract-v3.json --out reports/luna-crouch-sweep-chain/headless-v3 --headless

图形入口去掉--headless，输出到全新目录；必须先由父协调专职图形worker，不得与其他Godot批次并行。图形合同要求双向720/1080原生窗口稳定、完整人物共同取景、HUD安全区、实际相位/哈希及独立回放一致；并非动作美术通过。

失败记录：初次freeze未设既有Forge位置；首次Godot未隔离XDG而崩溃，日志保留。v2逻辑错误为期望已取消二拳仍播放收招相，v3改为此输入下只要求二拳0/1相，扫腿仍要求全部七相。v1/v2为历史探索合同，后续源码已加强，禁止绕过SHA校验运行旧合同。最终以v3及后续回执为准。无录屏、音频或真人键盘验收。

## 必须补充的独立事件门

冻结v3内层事件检查只校验已有contact的一致性。不得以它独自签图形通过；每批完成必须额外运行：

    python tools/rebuild/ultraman-arc/luna-crouch-sweep-chain/test_check.py --run reports/luna-crouch-sweep-chain/graphical-v3

此门逐组要求命中顺序为左拳/右拳/扫腿各一次，总195；蹲防为左拳/扫腿各一次block且0伤；落空零contact零伤；命中才出现倒地；原输入独立回放五字段相同。默认无--run时核16组headless。该离线文件不改冻结合同、玩法或渲染。

## 最终强制编排入口（优先于上面旧入口）

后续图形只用以下入口，原main_bundle.py run仅历史内层，不具有最终验收资格：

    python tools/rebuild/ultraman-arc/luna-crouch-sweep-chain/run_strict.py --out reports/luna-crouch-sweep-chain/graphical-strict-v3

run_strict会先执行原冻结运行器，再无条件调用外部严格门；任一拒绝立即失败，不会产生strict-final-result.json。最终成功只看strict-final-result.json，不能以旧runner-result.json代替。该编排不修改v3内层盲点，也不签动作美术。test_negative_gate.py已对真实trace内存变造events/HP/重复contact/少block进行拒绝测试；test_strict_orchestration.py以mock证明外门拒绝不会被吞掉或写成功总回执，不代表已跑图形。

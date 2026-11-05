# 银河装甲蹲起主游戏候选

仅复用银河本人现有整帧，保持角色四旗标关闭。独立 `candidate_factory.gd` 和 `candidate_view.gd` 装配银河身份；入口仍实例化 `app/scenes/main.tscn`，继承正式主游戏、HUD及取景，不借月亮装甲人物资源，不新增攻击或修改core。

## 材料与冻结

`register.py` 由根负责配准；默认输入 `art/fighters/ultraman-arc__galaxion/stage2/crouch-registered-20261105-v1/manifest.json`，其中 actions 含 idle、crouch_start、crouch、crouch_rise，各组含 frames 与带SHA的clip引用。整图方形采样可按动作统一尺度；禁止按帧缩放或切片。导入前由根核对整帧，并另写 `reviewer=root_delegated_by_user`、`accepted_for_formal_main_candidate=true` 的评审JSON。

```
python tools/rebuild/ultraman-arc/galaxion-crouch-resume/main_bundle.py freeze --root-review reports/galaxion-crouch-resume/<新评审>.json --engine <Godot绝对路径> --out reports/galaxion-crouch-resume/<新合同>.json
python tools/rebuild/ultraman-arc/galaxion-crouch-resume/main_bundle.py run --contract reports/galaxion-crouch-resume/<新合同>.json --out reports/galaxion-crouch-resume/<新逻辑目录> --headless
python tools/rebuild/ultraman-arc/galaxion-crouch-resume/main_bundle.py run --contract reports/galaxion-crouch-resume/<新合同>.json --out reports/galaxion-crouch-resume/<新图形目录>
python tools/rebuild/ultraman-arc/galaxion-crouch-resume/test_check.py
```

所有Godot调用由runner内部走 `tools/godot_lock.py` 串行。改变被冻结文件后必须新建合同，不能复用旧合同。输出只在新reports目录，不写用户设置或last_replay。

## 实际验证协议

- 240tick；输入帧24–77、102–155仅 down，其余中立，陪练全程中立。每次6tick入蹲、48tick保持（两次24tick循环）、6tick起身，再回idle。
- idle六相每相10tick，入蹲和起身各两相每相3tick，保持两相每相12tick。末段idle覆盖六相与回环。
- 双朝向、原生1280×720和1920×1080、独立进程原输入回放，共八组图形运行。启动先等窗口连续8帧且至少500ms稳定，模拟保持tick0。
- 截图逐请求冻结process/physics，校对双方state/sprite/region、state hash与绘制前最终HUD安全区。不缩放截图，不隐去训练板；44张/组原生PNG。
- Dummy音频、gl_compatibility；仅精确白名单“不支持切换VSync”环境警告可通过，其他WARNING/ERROR一律失败。
- 脚本产生真实方向InputFrame，不声称真人键盘操作；独立回放重放原双方输入并对逐tick状态哈希/events/projectiles。

## 状态边界

Godot 4.6.3 headless主游戏双向原/独立回放四组各240tick通过，逐tick哈希、事件、弹体一致，检查器带真实trace 21项全过。合同为本机 `reports/galaxion-crouch-resume/contract-v1.json`，真实证据在 `logic-v1/`，检查汇总为 `verification-summary.json`。曾在第四组落盘前过早启动检查器，其真实trace项因只有3文件失败；等待runner完成后原样重跑全过，没有修改代码或失败记录。合成图形fixture仍只验证拒绝逻辑，不是图形证据。实际图形、截图目视和严格尺度结论由根跑完后记录；无录屏。

如已有真实运行目录，设置 `GALAXION_TRACE_DIR` 后运行 `test_check.py` 可验证其各组trace。整帧连续性、美术与尺度必须根目视判断，不以脚本数量代替。

## 完整运行依赖冻结补验

contract-v2额外冻结整个addons/controller_icons和assets/audio（排除缓存），覆盖autoload/preload及Dummy仍加载的音频。logic-v2四组真实headless各240tick与21项检查器全过，零警告/错误；运行后Godot锁已释放。v1历史逻辑通过保留，但不作为完整运行依赖冻结的最终合同。最终合同SHA256：`fb6649a891dae65ef7e74af31f7a1119a08259b30a0b10e4b52d49bc0b1a602c`。本机汇总 `reports/galaxion-crouch-resume/logic-v2/verification-summary.json`。仍未启动图形，不宣称图形/美术/声音验收。

## 整帧配准复现

每动作固定整图采样：idle 157、start 148、crouch 132、rise 153，原1254方图；依据本人头壳/颈髋近似测点，详见registration-plan.json。只做整图二值Alpha、k-centroid、本人色板和整体平移，不逐相缩放；同动作共同水平参考保留横向重心，真实靴底到280。12原图独立重复后与样本/终帧逐像素相等。register.py拒绝覆盖已有生产输出，重新检查用内存重建比对，不抹除旧源。

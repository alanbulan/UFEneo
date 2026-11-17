# 月亮双臂重砸 RAM 候选

七槽 `[3,5,4,8,4,5,6]` 共35 tick。原12/8/15、130伤害、30体力、不可防、不挑空不击倒保持。仅接触相3远拳Alpha小框；真实中立+CRUSH64（O），无直接写move_id。正式command有idle等地面入口和land入口；候选只载前者，未验land入口、后方向入口或真人键盘。

320画布原样保留后掌比较锚[110,280]，运行根点[160,280]，不另平移。回护相5明确复用下降相2同一完整源；无新生成。正式assets与解锁不变。单相idle仅作首尾对照，非六相循环验收。

先设置 UFENEO_FORGE_ROOT，再 register.py、test_check.py、main_bundle.py freeze。所有Godot经 tools/godot_lock.py；main_bundle.py run --headless 为12组主游戏原输入/独立回放，去掉 --headless 为720/1080双向hit/GUARD受击/whiff原输入与回放共24组。每组冻结16个截图点，headless不声称图形证据。技术通过不等于美术、实速、声音或真人键盘验收。

frames.json 仅记录基础几何行；完整接触ROI与回护同源说明以 manifest.json 的 actions.crush.frames 为权威。

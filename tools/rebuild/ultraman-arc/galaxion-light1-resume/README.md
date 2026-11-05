# 银河单直拳候选

只在正式 app/scenes/main.tscn 的训练装配中加载银河本人内存定义，正式角色仍关闭，不修改 core、正式招式、选人及用户设置。不调用用户 Codex，不发收费请求。

现有原04收势护架复用为起始护架，原00–02三张远侧水平伸拳是接触保持，原03回护，排列[04,00,01,02,03]。不声称连续起探、近侧左拳或左右交替三连。时序[2,2,2,2,12]，沿用正式 Arc light1 2/6/12、65伤害、30体力及可防规则，仅本人实体拳ROI小框、相位与受击框变化，移除不可用light2取消。idle只使用已验银河crouch配准六相。

## 冻结与运行

main_bundle.py freeze --root-review PATH --out reports/galaxion-light1-resume/合同.json --engine GODOT_PATH

根审JSON必须 reviewer=root_delegated_by_user、accepted_for_formal_main_candidate=true；仅表示源允许进入候选，不表示运行或美术验收。默认manifest在art/fighters/ultraman-arc__galaxion/stage2/light1-registered-20261105-v1/manifest.json。动作组含frames与clip引用，light1增加move引用与fist_boxes（字符串相号→单个[x,y,w,h]）。

main_bundle.py run --contract 合同 --out reports/galaxion-light1-resume/新的运行目录 --headless

移除--headless得到720/1080、双朝向、hit/block/whiff与独立原输入回放，共24组。无头12组。每组120tick，tick20仅一次J对应LIGHT，block陪练全程GUARD；距离只在tick0设定，运行中绝不修改模拟字段。独立回放逐tick核状态哈希、事件和投射物。

每个图形组11张原生PNG：输入前idle、五相各首尾模拟tick、归idle。正式模拟J启动当tick已推进move_tick=1，因此0相唯一可见tick同时覆盖首尾，不伪造缺失的tick0。其余相覆盖首尾，命中停顿不重复截同key。保留真实HUD及训练板，绘制前取安全区；截图期间暂停模拟并核双方相位/区域/冻结tick/SHA/尺寸。没有录屏、音频和真人键盘验收。

完整冻结controller_icons与Dummy仍实际加载的audio依赖。每次Godot运行由tools/godot_lock.py串行包装。已有输出禁止覆盖，冻结依赖变化必须重新生成新合同。

python tools/rebuild/ultraman-arc/galaxion-light1-resume/test_check.py 只验证合成正负例门禁，不代表主游戏成功。可设置GALAXION_LIGHT1_TRACE_DIR检查已有真实12或24组结果。

## 已发现并保留的门禁历史

headless-v1首个实际用例命中65，但新事件比较仅规范化一侧，造成tick21声音、tick22命中事件整数/浮点表示差异误报；这是门禁失败，原结果保留，不能改写为通过。修正为两侧JSON往返后完整比较全部事件/投射物字段。另据真实trace，J启动首个可见move_tick=1，因此去掉不可见tick0截图预期，0相唯一帧覆盖首尾，其余相不变。

contract-v2冻结后发现合成负例更改的帧值恰好等于更新后正确值，负例本身未能制造错误；改正负例后另建contract-v3，不覆写v2，不声称v2跑过主游戏。最终运行结果以对应新的runner-result与真实trace为准。

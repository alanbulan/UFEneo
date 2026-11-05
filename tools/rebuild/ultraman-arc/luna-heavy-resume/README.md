# 月亮装甲S2重击候选

本入口处理现有heavy七张独立完整人物源，不生图、不收费、不开放月亮装甲。候选保存在art，正式content/assets和旧收据不回写。普通亚刻的heavy仅作为时序/费用参考，不使用其人物图。

## 来源与注册

七张实际源文件均为1254×1254（以解码结果为准，不把brief请求的1024当实际尺寸）。先核保留SHA，再统一整张1254→159；使用既有固定Forge三模块SHA、RGB兼容32色色板和Alpha128。旧诊断包的逐相面积缩放0.1177–0.1253不用于本候选。整张159方只平移到320方，x固定80、各相支撑足底对齐y280，不切肢、不旋转、不逐相重缩放。

根已查看七张原源联系图、第3相完整大图、共同尺度双向静态格图和拳面像素网格，接受继续注册；这不是严格美术或主游戏画面验收。`registration-review.json`记录身份、全头全脚、接触相与限制，不改历史user_approved。

第3相是真实斜砸接触，拳面样本矩形[120,90,130,100]对应局部框[40,49,10,10]。第4相已经收拳，不能把本体参考框留在空处或腿侧。因此只保留第3相tick9–12四个攻击tick，第4相无攻击框；startup9、active4、recovery15、总28tick。伤害100、体力30、能量0、位移、取消和命中反馈均保留参考，不扩大判定强保命中。

## 工具

- `prepare.py`只在新候选目录生成七个共同尺度样本，严格拒绝覆盖。
- 人工实看后保存`registration-review.json`，再运行`register.py`产生完整整图/atlas、本人Alpha受击框和候选move/clip。
- `test_check.py`只读核来源、共同尺度、注册像素不变、Alpha/色板、图集时序、精确允许的规则差异、拳面Alpha及装甲关闭状态。
- `main_bundle.py --output reports/luna-heavy-resume/<新合同>.json`生成封存当前代码SHA的正式main内存候选合同，拒绝覆盖。源或代码变化必须重新封合同，不改旧结果。

当前候选已存在，不能再次执行prepare/register覆盖它。日常核查：

```sh
python tools/rebuild/ultraman-arc/luna-heavy-resume/test_check.py
python tools/rebuild/ultraman-arc/luna-heavy-resume/main_bundle.py --output reports/luna-heavy-resume/contract-new.json
```

## 主游戏候选验证

入口为`tests/review/fighters/ultraman-arc/luna_heavy/main_entry.gd`，实例化正式`app/scenes/main.tscn`并注入内存月亮定义，只有heavy和本人idle/turn，不是完整装甲。`logic_check.gd`使用同一候选定义检查左右命中/格挡/落空，共六组；每组仅tick20按一次HEAVY，覆盖七相和归idle，记录原InputFrame并逐tick独立重放。Godot必须经`tools/godot_lock.py`串行并隔离用户数据。

配准与逻辑通过不代表S2全部完成，更不代表S2–S7装甲可玩。严格头身尺寸、动作接续和真实720/1080双向主游戏画面须单独记录；无录屏就不声称有录屏。实际本轮结果在`docs/verification/luna-heavy-resume.json`，不借本候选开放角色或变身。

逻辑命令示例（合同和结果路径须换成未用的新名称）：

```sh
XDG_DATA_HOME="$PWD/reports/luna-heavy-resume/userdata" python tools/godot_lock.py -- timeout 60 godot --headless --path . --script tests/review/fighters/ultraman-arc/luna_heavy/logic_check.gd -- --contract=res://reports/luna-heavy-resume/contract-new.json --out=res://reports/luna-heavy-resume/logic-new.json
```

正式main入口同样传`--contract`和`--out`目录，另可传`--left`、`--kind=hit|block|whiff`；`--tape=<actual-input-tape.json>`进行独立主游戏回放。无头执行只证明主游戏装配/输入/逻辑，不产生或伪造窗口截图。图形执行须使用实际1280×720或1920×1080窗口，保存原尺寸PNG；不要将缩小截图写成720/1080验收。

## 原生窗口与逐相截图门（2026-11-05补充）

实际云桌面验收发现CLI分辨率曾被窗口布局改写，且旧deferred截图可能跨过多个physics tick，不能将旧输出当作相位/分辨率验收。新入口必须使用`--window-size=1280x720`或`--window-size=1920x1080`（默认720）；在主游戏_ready后冻结模拟，显式请求无边框窗口，等待窗口和根viewport至少连续8帧且500ms保持目标尺寸。5秒内未达到就写真实`window-setup.json`并在tick0退出，不重标尺寸。

每次需截图的physics tick立即停止后续physics，记录tick/相位/状态hash/图集区域；等待frame_post_draw后核对这些值未改变，才保存原尺寸PNG并恢复推进。图像仍需实际目视，不把程序相位检查当美术通过。无头入口只检查冻结门和输入/回放，截图明确captured=false。修改入口后必须重封新合同，旧05输出保持原样作为问题证据。

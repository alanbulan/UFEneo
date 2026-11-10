# 赛罗内容数据补齐与自检（2026-11-10）

范围：只补 `content/fighters/ultraman-zero/` 的内容数据。未生成图片、未合成或绑定声音、未改 `content/audio`、未改 `art/`、未安装资源、未启动 Godot、未提交/推送、无录屏。美术与声音记录仍以 `README.md` 与本目录既有文件为准。

本轮产物：

- `content/fighters/ultraman-zero/MOVES.md`：104 个矩阵格逐格表 + 三槽对照 + 发射点实测 + art 组到 clip 映射 + 数值口径 + 缺口。
- `content/fighters/ultraman-zero/command_table.json`：40 条（37 个 move id），覆盖矩阵中所有已交付/已制作的输入格。
- `content/fighters/ultraman-zero/moves/*.json`：39 个动作文件。
- `content/fighters/ultraman-zero/SOUNDS.md`：计划与门槛，无绑定。
- `content/fighters/ultraman-zero/production_plan.json`：104 格，`integrated` 全 false。

## 一、校验方式

用本机 `.venv/bin/python` 读仓库文件做只读校验，脚本放 `/tmp`，不写入仓库（项目规则不建测试脚本）。校验项：

1. **JSON 可解析**：`json.load` 读取 `command_table.json`、`production_plan.json`、`moves/*.json`。
2. **文件名与命令表对应**：命令表每个 `move` 都要有 `moves/<move>.json`；本地多出的文件（`special2`/`special3`）须由 `special` 的运行时分级路由命中。
3. **帧数等于交付数**：`len(move.frames)` 必须等于 `art/fighters/ultraman-zero/stage1/cells/cells.json` 的 `action_set_status[组].delivered`，并计入 art 组改名映射 `light1→light_combo1`、`light2→light_combo2`、`light3→light_combo3`、`special→light1`、`special2→light2`、`special3→light3`。
4. **声音 id 存在**：`audio` 字段与帧内 `events[kind=sound].id` 必须存在于 `content/audio/runtime.json` 的 `sounds` 或 `aliases`；不引用不存在的 id（如 `throw_slam`/`throw_lift`/`throw_grab`）。
5. **整数与确定性**：递归检查所有数值，除颜色分量（`feedback.color`/`block_color`、`shots[].color`，沿用泰罗同类字段）外不得有浮点；不得出现 `random`。
6. **帧结构与框**：`sprite` 等于帧序号；`startup+active+recovery == frames.size()`；每个框为 4 个整数且 `w>0, h>0`；`kind=projectile` 不得有帧内 `hitboxes`（引擎要求 projectile 帧有 `hitboxes` 才生成，二者会重复判定）；`kind=strike` 至少一帧有 `hitboxes`；`kind=throw` 每帧有 `target`，`hold` 带 `grip`/`grab_point`，`release` 带 `progress`。
7. **框落在实际像素内**：逐帧读 `stage1/cells/<组>-NN-cell.png`，取 Alpha>0 的包围盒，换算到根点局部坐标（`x-128`, `248-y`），要求受击框（以及除 `burst` 外的攻击框）完全落在该包围盒内。`burst` 第 2–4 相 `[-90,12,180,128]` 是对称爆气圈，按模板保留，登记为例外。
8. **计划与矩阵一致**：`production_plan.json` 的格集合等于 `content/roster/matrix.json`；`integrated` 全为 false；`delivered_frames` 与 `action_set_status` 一致（含 `art_group` 的 light_combo/light1→special 改名映射）。

复现方式（只读，不写仓库）：

```
.venv/bin/python - <<'EOF'
# 按上述 1–8 项逐条断言；本轮运行结果见下节
EOF
```

## 二、结果（2026-11-10 本轮最后一次运行）

```
JSON 可解析：command_table 1、production_plan 1、moves 39
command_table move id 37 个，全部有本地文件；本地文件 39 个，其中未被命令表直接引用（由运行时按能量格选择）: ['special2', 'special3']
frames 长度与 cells.json delivered 一致：39 个动作（special→light1 等映射已计）
audio 字段与帧事件声音 id 全部存在于 content/audio/runtime.json
全部动作 JSON 无浮点、无 random（颜色分量按泰罗同类字段保留）
帧结构：sprite 连续、框为 4 整数且 w/h>0、startup+active+recovery=帧数、projectile 无帧内 hitboxes、strike 有攻击框、throw 有 target
受击框（及除 burst 外的攻击框）逐帧落在该帧实际 Alpha bbox 内
production_plan：104 格与矩阵一致，integrated 全 false
PROBLEMS: 0
```

补充校验（同一轮运行）：

- `MOVES.md` 逐格表 104 行，覆盖 `matrix.json` 全部格，无缺行、无多余格；列数一致（6 列）。
- `command_table.json` 的 `states` 全部出现在矩阵状态集合中；无空 `states` 条目；无重复四元组。
- 帧内 `impact_effect`/`block_effect`、`feedback.spark`/`block_spark`、`shots[].effect` 全部存在于 `content/presentation/phase3_projectiles.json`（含 `pulse`、`beam_hit`、`impact_light`、`impact_heavy`、`impact_guard`）。
- `moves/*.json` 的 move id 全在 `content/templates/humanoid/move_manifest.json` 的 47 项内，`content_database.gd` 能按 id 找到本地文件。
- `production_plan.json` 与 `command_table.json` 无浮点。

## 三、命令表与矩阵的逐格核对

- 命令表 40 条，与矩阵逐格比对（move + states + directions + buttons 四元组）：所有已交付动作对应的矩阵格都有精确条目。
- 有意不写条目的格：`pulse`(command_10)、`ranged_forward`(command_11)、`crouch_light2`(command_16)、`crouch_light2` 态 `sweep`(command_17)、`motion_236`/`motion_623`/`motion_214`/`motion_22`/`motion_41236`(command_40–44)。这些格在 MOVES.md 与 production_plan.json 中均标“待制作/待依据”，动作留空。
- 覆盖语义：`merge_commands` 会删掉模板中同一 move id 的所有基础条目再追加本地条目，因此 `sweep`（crouch + land）、`crush`（idle-set + land）、`special`（P 与 □+△ 两个入口）在本地表里都完整重列；`command_17` 的 `sweep` 变体随之被移除，不会误触发站立低扫。
- 已知后果：模板仍保留 `pulse`、`ranged_forward`、`crouch_light2`、`motion_*` 的条目，这些输入仍会加载模板招式数据；要彻底关闭需在 `definition.json` 的 `unsupported_moves` 登记，属安装/定义层，本轮不做。

## 四、三格能量终结的独立性与数值

|槽|move|art 组|帧|伤害/削气|能量|命中|发射部位|
|---|---|---|---:|---:|---:|---|---|
|1|`special`|`light1`|3|180/18|1000|硬直 28、hitstop 10|右前臂外侧，宽蓝束|
|2|`special2`|`light2`|3|300/30|2000|硬直 28、击倒|额灯，细绿束|
|3|`special3`|`light3`|4|480/48|3000|硬直 28、击倒|双掌前，两枚实体飞刃|

三者动作、发射部位、颜色、形态、判定框与命中效果均不同；不是同一束改粗细/颜色/伤害。技能光效已烘焙在整帧里，故四招写 `kind=strike` + 帧内攻击框，不额外生成运行时投射物，避免同一招画两遍。`low_pulse`/`air_pulse` 的人物帧明确无 FX，写 `kind=projectile` 并在发射帧生成通用 `pulse`。

## 五、已知问题

1. 无 `content/fighters/ultraman-zero/definition.json`、`state_frames.json`、`move_manifest.json`，也无 `assets/fighters/ultraman-zero/animations/manifest.json`：角色当前不能加载进主游戏。本轮禁止安装，只记录。
2. 受方投技（`thrown_*`）、拆投 `throw_tech` 整帧已交付，但受方状态帧数据未建，攻击方 `target.pose` 指向的姿势在运行时取不到；`grabbed` 独立姿势未交付。
3. 状态类整帧缺 `state_frames.json` 接入（idle/walk/dash/hit/wake/guard 等 41 格）。
4. `content/combat/skill_library.json` 的 ultraman-zero 仍为 `skill_ids: []`，本轮未改。
5. 无声音绑定；赛罗 5 条语音已存在于运行时但来源为未逐集定位的 B站战吼合集（`reprint`），不能当已核原声。
6. 未安装、未启动 Godot、未提交、无录屏；因此没有任何画面/听感验证，只有数据与像素包围盒校验。
7. `art/fighters/ultraman-zero/stage1/cells/cells.json` 的 `action_expansion.content_gaps` 仍写着“无 MOVES.md、SOUNDS.md、moves/*.json、production_plan.json”，该条已过时；按本轮禁令未改 `art/`，留待美术侧下次记录时更新。

## 五、definition.json 与 state_frames.json 补齐（2026-11-10）

范围：只补 `content/fighters/ultraman-zero/definition.json` 与 `content/fighters/ultraman-zero/state_frames.json`。未生成图片、未合成或绑定声音、未改 `content/audio`、未改 `art/`、未安装资源、未启动 Godot、未提交/推送、无录屏。

### 本轮产物

- `content/fighters/ultraman-zero/definition.json`：字段按雷欧结构补齐；`presentation.cell=256`、`anchor=[128,248]`、`anchor_y=248`、`target_height=188`（取身份锚原生站高与 cells.json `target_standing_height`，非雷欧的 192/[96,184]）；`playable=false`、`pilot_playable=false`（资源尚未安装到 `assets/`，如实标注未安装）；`unsupported_moves` 登记 8 项（pulse/ranged_forward/crouch_light2/motion_236/motion_623/motion_214/motion_22/motion_41236）。
- `content/fighters/ultraman-zero/state_frames.json`：39 个主状态 + 11 个 documented 别名 = 50 个状态键，共 153 帧条目。主状态帧数与 `art/fighters/ultraman-zero/stage1/cells/` 实际 PNG 一一对应（315 帧中的状态类帧，不含招式帧；招式帧已在 `moves/*.json`）。别名帧数据复制自对应源状态，不编造不存在的 PNG：
  - guard ← block；wake ← getup；victory ← win；defeat ← ko；
  - hit_high/hit_mid ← hit；hit_air/launch_rise ← hit_air_rise；launch_fall ← hit_air_fall；
  - air_tech ← air_recover；roll_forward ← getup_forward；roll_back ← getup_back；getup/win/ko 保留原键并供别名使用。
- 判定框：state_frames 的 hurtboxes 为按实际 Alpha 落格整帧量取的三段占位受击框（头/躯干/腿），hitboxes 为空；技能帧攻击框仍在对应 `moves/*.json`。文件内 `definition.json.state_frames_note` 与本节均注明「按同类已装机角色换算的占位判定，未实机校准」。

### 自检（只读，脚本放 /tmp，未留在仓库）

`.venv/bin/python` 校验项：

1. JSON 可解析：`definition.json`、`state_frames.json` 均通过 `json.load`。
2. 每个 state_frames 状态键的帧数等于对应 art 组的 `cells.json action_set_status.delivered`，且等于该组实际 `-cell.png` 文件数（idle 组含 `idle-candidate-02-official-side-anchor-cell.png` 与 `idle-01-cell.png` 两帧）。
3. 每个 `sprite` 索引都能在对应组的 cell PNG 列表中找到文件。
4. 全部数值为整数，无浮点、无 `random`；每个框为 4 个整数且 `w>0, h>0`。
5. `presentation.cell=256`、`anchor=[128,248]`、`anchor_y=248`、`target_height=188`。

结果：states 50、total frame entries 153、errors 0。

### 仍缺（如实记录，未冒称可加载）

1. 未安装到 `assets/`，无 `animations/manifest.json`，Godot 无法实际加载渲染；本轮禁止安装，只记录。
2. state_frames 未覆盖的运行时状态（无对应已交付整帧）：crouch/crouch_start/crouch_rise/crouch_turn/crouch_guard、guard 持续帧（仅 block 1 帧作 guard 占位）、air/vertical_air/diagonal_air/chase_air/backward_air/air_apex、hit_crouch、grabbed、crouch_guard、crouch_blockstun 已有但 crouch_guard 缺失；chase_air 无整帧。运行时将回退到默认框，不冒称已接入。
3. 受方投技（thrown_*）整帧已交付并写入 state_frames，但运行时投技双方逐帧对位数据（抓点/保持/释放/落地）未建；`grabbed` 独立姿势未交付。
4. `content/combat/skill_library.json` 的 ultraman-zero 仍为 `skill_ids: []`，本轮未改。
5. 无声音绑定；赛罗 5 条语音来源为未逐集定位的 B 站战吼合集（reprint），不能当已核原声。
6. 未启动 Godot、未提交、无录屏；因此没有任何画面/听感验证，只有数据与像素包围盒校验。

# 奥母（mother-of-ultra）内容接线计划 · 2026-11-12

根按 `root_delegated_by_user` 自签；仅限计划验收，不是用户亲审，也不是美术、听感或实机通过。W1/W2 制作代理与 W3 只读复算均不自签。

## 本轮完成

- 本角色四份计划均在 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/mother-of-ultra/stage1/rework-20261112/wiring`：`state_frames_plan.json`、`moves_plan.json`、`emission_plan.json`、`wiring_report.md`。
- 已先核磁盘无既有 `wiring/` 产物；本轮只新增上述四文件，未覆盖 `asset_baseline.json`、`clip_diagnosis.json`、`storyboard.md` 等只读基线。
- 未改 `content/`、`core/`、`input/`、`presentation/`、`ui/`、`assets/`；未 commit，未跑 Godot/verify，不动锁。
- 根复核四份计划 JSON 均可解析；逐角色 source_files 中相关文件 SHA 与磁盘一致；`state_frames_plan.json` 的逐 tick `row_map` 与 `moves_plan.json` 的 `timeline_map` 均保留 `source_rows` / `source_frame_count` 长度和非 sprite 语义 SHA。

| 文件 | 绝对路径 | SHA256 前 12 |
|---|---|---|
| state_frames_plan.json | `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/mother-of-ultra/stage1/rework-20261112/wiring/state_frames_plan.json` | `b8a95ebf183e` |
| moves_plan.json | `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/mother-of-ultra/stage1/rework-20261112/wiring/moves_plan.json` | `fb59b3e8fbab` |
| emission_plan.json | `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/mother-of-ultra/stage1/rework-20261112/wiring/emission_plan.json` | `74990a8bc609` |

## 怎么看

- 时间轴：保持整数 60 tick、InputFrame 回放、逐 tick `hitboxes`/`hurtboxes`/`cancel`/`events`/`active`/发射 tick 语义；逐 clip 取该 clip 自己的 `cell`/`anchor`/`rects`/`ticks`，不回落到 manifest 顶层或 `cells.json` 旧顶层 `anchor`。
- state_frames 越界：无，共 `0` 行；`presentation/side_view.gd:450` 的 idle/turn clamp 冻结为 无，walk 按 `clip.ticks` 循环造成的帧序/受击框口径失配为 `walk_back`、`walk_forward`，两类分开登记。不得把 idle 60 行 sprite 0–5 压成全 0、walk 70 行 0–7 压成 4 帧来掩盖越界。
- moves：覆盖 `move_manifest.json` 的 `47` 招 / `1357` 行；W1 登记未用 rect 组 `0`、未用索引 `0`、全 0 组 `0`、仅前半推进组 `0`、后半冻结组 `0`、sprite 越界行 `0`。W1 较宽的“后半无任何 sprite 变化”口径与 W3 只读硬门口径并列保留：W3 只读硬门无未用 rect、无全 0、无前半漏帧；`taunt` 标量合计与 rows 不符按原值登记。
- 图集使用：direction quick 的 `motion_214/236/623/22/41236` 与 `special/special2/special3/air_special` 已核；杰斯提斯 `special` 14 帧、其余 20 组各 16 帧、七角色 `air_special` 各 8 帧。本角色上述组图集帧全部被使用。
- 发射点：人工依据表按当帧掌 / 角 / 胸灯 / 额灯四人部位口径，另把 Q 周身蓄气圈、状态占位附件、天顶光阵等非肢体落点明确标为“其它”，不冒充肢体发射。共 `157` 条，四类本人部位 `87` 条，其他锚点 `70` 条；`157` 条为 `pending_cell`，`point_right`/`point_left` 全为 null。双向原生误差 ≤2 px 是重画帧落格后的验收标准，不是本轮已通过结论。
- effect id：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/content/presentation/phase3_projectiles.json` 为 `722` 条，SHA256 `8ddce6876986cb1177ecb3d4608ede0ed2cee0c3122926cad6b34f00d7f030f2`；Q 三态 `21` 个 id、七角色引用 `120` 个 id 均登记，`registration_status=all_registered`；已记录 `atlas_sha256` 的 114 条按字节复算 114/114 相符，W3 报告不符 0、缺文件 0。6 个共享旧式 id 未记录该字段，按现状保留：`beam_hit`、`impact_guard`、`impact_heavy`、`impact_light`、`king_fx_ring_form_back`、`king_fx_ring_form_front`。本角色 `missing_ids` / `pending_ids` / `unregistered_ids` 均为 0；不重复补登记，只有新增或改换贴图后才按 `tools/rebuild/shared/q_charge_registry.py` 口径写 SHA 补登记计划。
- 投射类 `pulse/low_pulse/air_pulse/ranged_forward` 只保留手部与身体动作计划；运行时 move_fx 已生成投射物，人物帧不得再画能量球、光刃、飞行物。技能帧不设“周身蓄气圈”例外。

## 已知问题

- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/content/fighters/mother-of-ultra/emission_points.json` 缺失；本轮没有新帧，全部坐标 `pending_cell`，未写任何 `point_right`/`point_left`，不虚构坐标。
- `state_frames_plan.json` 登记待安装 `pending_frame` `0` 个；`moves_plan.json` 的未用帧与后半冻结帧按原 source rows 登记，未改写 `sprite_values` 或压缩 rows。
- blockers：
  - `command_table.json` 为空表，通用 `quick_commands.gd` 没有本角色 base motion 条目可 extend，I+方向快捷映射不能凭空生成。
  - rework-20261112 无新 PNG；state/moves 新增目标帧标 `pending_frame`，发射点全部 `pending_cell`，不虚构 cell/anchor/rect/atlas SHA 或坐标。
  - 分镜的 6 帧待机 / 8 帧步行与部分现行 `state_frames` 行数不一致；任何源时间轴变更须另有真实 InputFrame 回放证明，本计划不改写 rows。
  - 未安装、未实机、未跑 Godot/verify、未动锁、未 commit；无录屏、未听审、未用户亲审。
- 口径差异：W1 的 `only_first_half_used` 按“时间轴后半相邻 sprite 推进次数为 0”计，W3 的硬门只把未用 rect / 全 0 / 漏帧组列为返工；`chase_end` 等后半保持姿势组不写成“缺帧”，但不得用同一姿势复制凑帧。
- 内容依据：本角色 `MOVES.md` / `command_table.json` 仅作现有文字资料，原剧集数、时码、逐帧镜头缺口不补编；`command_table.json` 本身不提供原剧依据。

## 下一步

1. 先补本角色 `command_table.json` 的五组原搓招 base motion 条目，并核 `move_manifest.json` 与实际 `moves/*.json` 的 1:1 关系；否则 I+方向快捷别名无法从 `quick_commands.gd` 生成。
2. 按分镜逐 clip 生成并重画 `pending_frame`，落格后核 cell/anchor/rects/ticks、atlas SHA、`.import`、相邻差分与循环接续；安装前核该 clip 现有 `cell`。
3. 用新原生格按当帧掌 / 角 / 胸灯 / 额灯双向复核发射点，原生误差 ≤2 px、不悬空、不穿体；再把 `pending_cell` 替换成实测坐标并同步 `emission_points.json`。
4. 仅在新增或改换贴图后按 `q_charge_registry.py` 口径补登记 phase3 条目与 atlas SHA，并核 `charge_overlay_policy.json` 三态 placement；已登记、已记录 SHA 且相符的条目不重复补登记，6 个无字段旧式 id 不冒称已核。
5. 逐 clip 安装后用真实 InputFrame 回放核时间轴，再按项目规则做主游戏训练/F1、双朝向 720/1080 审片；本轮无录屏、未听审、未实机，不写成已验证。

# 佐菲 stage1 制作记录

本目录是佐菲 stage1 动作候选的制作源与验收记录；未安装到 `assets/`，未接运行时。

## 身份锚

- 图鉴定稿：`art/fighters/zoffy/model/catalogue-173.png`，SHA `addd0bcea67e5b7735f560b561bf028bf8e835662e22473f66fe17cd2eb6d9e4`。
- 动作唯一参考：`art/fighters/zoffy/stage1/idle/references/identity-pixel-x4.png`，SHA `2c4e85cbcc51ef5c011e724267de1be4859460a69f8b636339832a59b35c7da2`，440×692，是 catalogue-173 原生 bbox 110×173 的严格 4× 最近邻。

### 已知差异：站距 0.618

图鉴锚的脚外缘间距/站高 = 107/173 = **0.618**，低于 `docs/STAGE1_STANDARD.md` 第 1 步的 0.65–0.80。该值在已装机 10 个角色实测 0.50–0.98 范围内，视觉上是标准格斗护架（双脚错步、前后屈膝、双拳胸前）。根审（root_delegated_by_user）决定：不重做锚、不撤销 A 段 16 帧；此项作为已知差异保留。

## 落格参数

- 比例：0.099419（源：`idle/frames/raw-00-v3.png`，目标站高 154），全套共用，不按姿势外框归一身高。
- 格与根点：192×192，根点 [96,184]，脚底 183；腾空帧可抬高脚底行并记录。
- 色板：catalogue-173 的 32 色，整图统一映射，保留蓝计时器 `(4,179,230)`。
- 硬门：主体单连通、Alpha 二值、色数 ≤32、格内未裁切。

## 当前状态（2026-11-10）

- A 段 16 帧复落：15 帧根审通过；`run-00`（raw-00-v4）约 0.6× 拒收成立，raw、旧 cell、拒收联系表已删除，拒收记录与 SHA 保留在 `requests.json`。
- run 4 帧：根审通过，顺序 接触 A → 腾空 A → 接触 B → 腾空 B；腾空脚底 173，水平平移对齐头部中心，不缩放；腾空高度留给动画层根运动。
- walk_back 4 帧：根审通过（root_delegated_by_user），顺序 `walk-back-00` 第一次接触 → `walk-back-01` 承重 → `walk-back-02` 经过 → `walk-back-03` 第二次接触；支撑脚均 183，00 近腿后伸、03 远腿后伸且被支撑腿遮挡，构成近/远腿交替；不缩放。
- dash_start 2 帧：根审通过（root_delegated_by_user），`dash-start-00` 蹬地 → `dash-start-01` 前脚蹬伸、后脚离地；01 整帧 +18px，前脚底行中心 118.5 与 00 一致、计时器中心 111.8 对齐 111.5；不缩放。
- dash 4 帧：根审通过，顺序 `dash-01` 起速 → `dash-00` 低姿前冲 → `dash-02` 腾空 → `dash-03` 落地前一相；`dash-00` 低姿作为该组一相保留，垂直落差记入待实速复核。
- takeoff 2 帧：根审通过，`jump-01` 蹬地离地 → `jump-00` 收腿；脚底 183，腾空高度留给动画层根运动。
- land 2 帧：根审通过，`land-00` 触地 → `land-01` 落地压缩（深蹲、双臂前下方支撑）。
- hit 2 帧：根审通过，`hit-00` 后仰受击 → `hit-01` 退步收势回护架（无火花、无独立颗粒）。
- light1 3 帧：既有 `light1-00` 右直拳接触 + `light1-01` 蓄拳、`light1-02` 收拳；组内按 `light1-01 → light1-00 → light1-02` 播放；根审通过（root_delegated_by_user）。
- light2 3 帧：`light2-00` 起手 → `light2-01` 左勾拳接触 → `light2-02` 收势；`light2-01` 侧视下与直拳接近，按第二段轻击保留；根审通过（root_delegated_by_user）。
- light3 4 帧：`light3-00` 提膝 → `light3-01` 踢出 → `light3-02` 收腿 → `light3-03` 落地回护架；根审通过（root_delegated_by_user）。
- heavy 4 帧：`heavy-00` 蓄力 → `heavy-01` 双拳抡起 → `heavy-02` 下砸接触 → `heavy-03` 收势；根审通过（root_delegated_by_user）。
- down 2 帧：`down-00` 后仰失衡 → `down-01` 仰面倒地；仰卧帧按整身轮廓居中根点；根审通过（root_delegated_by_user）。
- getup 2 帧：`getup-00` 撑起 → `getup-01` 屈膝护架；根审通过（root_delegated_by_user）。
- win 2 帧：`win-00` 举拳 → `win-01` 收势；根审通过（root_delegated_by_user）。
- ko 2 帧：`ko-00` 仰面砸地 → `ko-01` 平躺败姿；仰卧帧按整身轮廓居中根点；根审通过（root_delegated_by_user）。
- 最小动作集 19 组 47 帧已齐（root_delegated_by_user，不是用户亲审）；`walk_back` 4 帧、`dash_start` 2 帧本轮补齐；`run` 4 帧为额外已审内容。
- 2026-11-10 状态帧批次 20 clip / 63 帧已落格并过硬门（root_delegated_by_user）：`guard` 2、`crouch` 2、`crouch_start` 2、`crouch_guard` 2、`crouch_rise` 2、`crouch_turn` 3、`hit_high` 3、`hit_mid` 3、`hit_crouch` 3、`air_tech` 4、`vertical_jump` 4、`flip_forward` 4、`flip_back` 4、`roll_forward` 5、`roll_back` 5、`wake` 5、`dash_stop` 3、`launch_rise` 3、`launch_fall` 3、`air_apex` 1。逐帧来源/生成 ID/提示词/落格见 `cells/cells.json` 的 `state_frames_20261110`，联系表 20 张在 `contact/`。
- guard 两帧按“进入守势/保持守势”新生成，未复用 `block-00`；`block-00` 仍为独立守势帧，未覆盖。淘汰 4 帧（guard-01-v1、crouch-01-v1、crouch-start-01-v1、crouch-turn-02-v1）raw 已删除，SHA 与原因保留。
- 未安装、未接运行时、未做 720/1080 与双向实机检查；上述状态帧只是美术帧，不等于实机通过。

## 状态帧第二批（2026-11-11）

补齐佐菲剩余非招式状态 clip，帧数按泰罗同键：27 clip / 115 帧，全部落格并过硬门（单连通、Alpha 二值、色数 ≤32、格内未裁切），逐帧在最终原生格与严格 4× 实看（root_delegated_by_user，不是用户亲审）。

| clip | 帧数 | 站高 / 脚底行 | 内容 |
| --- | --- | --- | --- |
| backstep | 5 | 149–152 / 183 | 前脚蹬地、后撤、落步回护架 |
| blockstun | 2 | 150–152 / 183 | 护架被冲击压向身体、复位 |
| bounce | 3 | 106/138/126，脚底 183/145/168 | 触地压缩、弹起、二次落地 |
| charge | 4 | 144–151 / 183 | 双拳收腰蓄势的循环四相 |
| charge_start | 3 | 139–150 / 183 | 由护架进入蓄势 |
| charge_stop | 2 | 151 / 183 | 蓄势收束回护架 |
| chase_takeoff | 3 | 94/115/103，脚底 183/150/120 | 追身起跳蹬地到离地 |
| crouch_blockstun | 2 | 128/151 / 183 | 蹲姿吃防、起身复位 |
| defeat | 4 | 95/61/65/47 / 183 | 跪地到仰卧败姿 |
| dodge | 6 | 147–152，脚底 183（02 为 170） | 侧闪一整段，含一次腾空 |
| grabbed | 3 | 130–151 / 183 | 被抓瞬间到被提起 |
| guardbreak | 4 | 90–150 / 183 | 破防后仰、踉跄、回架 |
| hit_air | 3 | 68–111，脚底 130/110/155 | 空中受击三连相 |
| intro | 8 | 77–151 / 183 | 登场落地、起身、摆架势 |
| stun | 7 | 149–152 / 183 | 眩晕左右摇晃循环 |
| takeoff | 2 | 107/125，脚底 183/145 | 起跳蹬地与收腿 |
| throw_tech | 4 | 133–151 / 183 | 被抓住后拆投挣脱 |
| thrown_air | 4 | 84–128，脚底 100–160 | 被抛空中受身 |
| thrown_back | 4 | 96–111，脚底 110–160 | 被向后方掷出 |
| thrown_dash | 4 | 74–107，脚底 120/130/183 | 被掷出后擦地滑行 |
| thrown_forward | 4 | 67–121，脚底 100–175 | 被向前方掷出 |
| timeout | 4 | 150–151 / 183 | 时间到收势 |
| turn | 3 | 138–152 / 183 | 转身三相 |
| victory | 8 | 133–151 / 183 | 胜利举拳到收势 |
| wake_low | 5 | 51–115 / 183 | 侧卧撑起到单膝跪 |
| wake_mid | 6 | 112–150 / 183 | 跪撑到站起护架 |
| walk_forward | 8 | 148–151 / 183 | 前走八相，两脚交替接触 |

- `thrown_*` 只画被投掷方的受身姿态，不是攻击方投技；`grabbed` 为被抓瞬间，`throw_tech` 为拆投，均只有佐菲一人。`wake_low`/`wake_mid` 与已签 `wake` 5 帧分段衔接（侧卧→跪→站起）。
- 全部状态帧无光效、无独立颗粒、整帧单连通；受击帧未加火花。
- 自动读数只报不凑：直立帧 148–152 属站姿压低，`crouch_blockstun-00` 128、`chase_takeoff-00` 94、`defeat` 47–95、`wake_low` 51–115 等为动作本身压低或倒地，按实际像素量脚底行。`crouch_blockstun-01` 151 为起身复位相，与同组 128 不同姿，保留。
- 淘汰 78 个候选 raw 已删除（方向/身材/整幅取景不合格，均用同序号 v3/v4 整帧重生成），SHA、路径与原因在 `cells/cells.json` 的 `state_frames_20261110_batch2.rejected` 与 `requests.json`；未做镜像、拉伸或逐帧变比例。
- 记录：`cells/cells.json` 的 `state_frames_20261110_batch2`（27 clip 元数据 + 115 帧来源/生成 ID/提示词/落格/验收）；联系表 27 张在 `contact/`（`*-20261111-sheet.png`，无同名旧表时用 `*-sheet.png`）。
- 已装清单里 `takeoff` 现由 `jump-00`/`jump-01` 提供（2 帧）、`walk_forward` 为 4 帧；本批 `takeoff` 2 帧与 `walk_forward` 8 帧为同键替代候选，安装时整组替换，不与旧组叠加或混帧。
- 未安装到 `assets/`、未改 `content/`、未运行 Godot；未做 720/1080 与双向实机检查，无录屏。

## 最小动作集核销（2026-11-10）

依据 `docs/STAGE1_STANDARD.md` 第 91–95 行，最小可交付集为 19 个动作组，共 47 帧。现 51 个活格中，`run` 4 帧为额外内容；扣除后最小集 47 帧齐。

| 动作 | 要求 | 现有 | 状态 |
| --- | --- | --- | --- |
| idle | 2 | 2 | 齐 |
| walk_forward | 4 | 4 | 齐 |
| walk_back | 4 | 4 | 齐 |
| dash_start | 2 | 2 | 齐 |
| dash | 4 | 4 | 齐 |
| takeoff | 2 | 2 | 齐 |
| air_rise | 1 | 1 | 齐 |
| air_fall | 1 | 1 | 齐 |
| land | 2 | 2 | 齐 |
| light1 | 3 | 3 | 齐 |
| light2 | 3 | 3 | 齐 |
| light3 | 4 | 4 | 齐 |
| heavy | 4 | 4 | 齐 |
| hit | 2 | 2 | 齐 |
| block | 1 | 1 | 齐 |
| down | 2 | 2 | 齐 |
| getup | 2 | 2 | 齐 |
| win | 2 | 2 | 齐 |
| ko | 2 | 2 | 齐 |

结论：最小动作集 **19 组 47 帧已齐、已标记完成**（root_delegated_by_user，不是用户亲审）。现有 20 张联系表为 19 个最小集动作加额外 `run`。

## 记录与联系表

- 请求、锚、色板、每帧提示词、SHA、落格、验收：`requests.json`、`cells/cells.json`。
- 原生格与严格 4×：`cells/`（`*-cell.png`、新增帧的 `*-x4.png`）。
- 每动作联系表（原生格 + 严格 4×）：`contact/`。
- 旧 `reports/zoffy/stage1/` 的 16 个重复 cell 已按无消费者规则删除；8 个更早候选 cell、37 个诊断图与旧 `cells.json` 经复核无引用后同样删除，SHA 全部保留在 `requests.json` 的 `reports_cleanup`。
- 上一轮落格临时目录 `reports/zoffy/stage1-tmp`（12 个位移前原生格 + 工具 `cells.json`，共 13 个文件）已记录 SHA 后删除；最终位移格 SHA 见 `requests.json` 的 `cells` 与 `cells/cells.json`。
- 本轮 walk_back/dash_start 的 7 个临时文件（未位移/未采用格 + 工具 `cells.json`）与 4 个淘汰 raw（walk_back-03 v1/v2、dash-start-01 v1/v2）已记录 SHA 后删除；最终格与严格 4× 保留。
- `tools/rebuild/zoffy/stage1_cells.py` 只写已删的 reports 路径且当前未使用，列入待根定，未删。

## 2026-11-12 air_special v2 落格与装机

- air_special 8 帧纯人物源（`air_special/frames/air-v2-00..07.png`）落格：比例 0.102001312、目标站高 158、256 格、根点 [128,248]、腾空脚底 237。
- 落格高 116–145（空中收腿/前伸，非直立），31–32 色、二值 Alpha、主体单连通、四边留白、无裁切；逐帧 bbox/SHA 见 `cells/cells.json`。
- 招式 24 tick（10/1/13）不变，发射 tick 10 落在新版前伸臂帧 sprite 03；hurtboxes 整招重算。安装 `--only air_special` 合成，manifest 108 clip，clip 根点保持 [128,248]（安装器曾回落到旧顶层 [96,184]，已修正后重装）。
- 全量 `tools/verify.py` 57 项 PASS。root_delegated_by_user；无录屏，720/1080 双向实机未验。

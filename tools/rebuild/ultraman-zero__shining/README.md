# ultraman-zero__shining 制作记录

## 2026-11-12 阶段 1：右侧视待机身份锚

### 来源与朝向规格

- 正面配色/甲片：`sources/ref-02-official-front.jpg`（BANDAI SPIRITS 魂ウェブ S.H.Figuarts 商品照，857×1140，SHA `2a7604e4…3874c`）。
- 右侧视头形与安装：`sources/ref-03-official-softvinyl-side.jpg`（万代 UHS 31 光辉赛罗软胶侧面实物照，1920×1920，SHA `bb18a591…26bab`）。实物只参考造型，不画关节/轴/插接缝/塑料高光。
- `sources/ref-01.webp` 为暗色身体金纹蓝眼渲染，用户判定不能定侧视锚、不符合官方银底金甲；保留 SHA 记录，不用于生成。
- 头冠/双镖朝向写死为：90° 右侧视、人物朝右；中央冠脊从额前蓝灯上方起低伏向后；双镖贴在耳上方头壳，刃根在前、刃尖向后上方，近镖压远镖、刃背有凹口，镖尖止于后脑附近；禁止一整片高羽冠、三根大尖角、向前伸的角。

### 照片门（4 次拒收后出诊断，见 `diagnostic-idle-20261112.png`）

| 候选 | 实收 | SHA-256 | 拒收原因 |
| --- | --- | --- | --- |
| 00 | 1477×1065 | `84e62b1a…93ba` | 冠脊与双镖断成三叉高角 |
| 01 | 1199×1312 | `44f57943…4df77f` | 冠脊与双镖根部连成一片高鳍 |
| 02 | 1263×1246 | `e320e6cb…17c372` | 站距 953/1136=0.839 超 0.65–0.80，头过小 |
| 03 | 1192×1320 | `a49af0e4…84ca3b` | 头形已接近官方，但冠顶→下颌 219/1203=0.182，比基础赛罗 0.207 小约 12%，肩胸偏厚、躯干偏 3/4 |
| 04（采用） | 1024×1536 | `2ea15452…b35898` | 通过 |

换策略（不再写“成年人头身比”）：第一图基础赛罗已装机待机只借站姿、画风、头身比与四肢粗细；第二图官方侧头定双镖结构；第三图官方正身定银底金甲。候选 04 指标：alpha bbox [89,215,917,1402]，站高 1188，冠顶→下颌 260（0.219，对基础赛罗 0.207 为 +5.5%），站距 829/1188=0.698，主体外 alpha≥16/≥200 = 0/0，alpha 1–15 尘点 23,545 不计，Alpha128 单连通，四边留白 89/106/215/133。

### 像素整帧与身份格

- 清图：Alpha128 硬化、裁到主体、缩到站高 1100，置 1024×1536 透明画布，bbox [128,311,895,1410]，脚底 1410，SHA `434a8153…52bb6`。
- 单参考转像素整帧：`stage1/idle/frames/pixel-raw-04-official-side-anchor.png`，1024×1536，SHA `6816181d…c19057`；站高 1100、站距 0.7036、主体外 alpha≥16/≥200=0/0、Alpha128 单连通。头部放大核过：蓝额灯在前、双镖根前尖后上、近远双刃与凹口可辨，银白底衣、金色甲片、蓝眼与蓝色五角胸核保留，无烘焙光效。
- 身份格：`stage1/cells/idle-00-cell.png`，256×256，SHA `b9810767…58f423`；bbox [54,60,185,247]，站高 188、宽 132、脚底 247、根点 [128,248]，头高启发式 36/188=0.1915（基础赛罗 39/188=0.2074，-7.7%，在 ±8% 内），站距 132/188=0.7021，色数 32、Alpha [0,255]、连通块 1。严格 4×：`stage1/cells/idle-00-x4.png`，SHA `1ea775d5…c6c5da`；已看原生格与 4×。
- 色板：本机未安装 agent-sprite-forge，`forge_backend` 报 ImportError；按项目记录的最远色种子＋频次加权 Lloyd32（16 轮，整图最近色映射）同法在 `build_idle_anchor.py` 自实现，色板取自本形态待机像素整帧，保住蓝额灯/蓝眼/蓝胸核与金色甲片。cells.json 记录完整 32 色与 `palette_source` SHA。

以上身份锚为 `root_delegated_by_user` 签署；未做实机、未录屏、未验双朝向 720/1080，不写成视觉/听感通过。

## 2026-11-12 阶段 2：内容数据派生（动作帧未制作）

- `tools/rebuild/ultraman-zero__shining/build_content.py` 从基础赛罗派生本形态内容：47 个招式文件、`command_table.json`、`move_manifest.json`、`state_frames.json`、`definition.json`、`profile.json`。逐招核对：帧数、启动/持续/收招、伤害、能量、受击框与判定数据与基础赛罗完全一致；只改 `data_source`、`production_note`、角色显示名与特效 id。
- 特效 id 全部改为 `pending_shining_*`：12 个招式/反馈 id + 3 个 Q 蓄气 id，清单在 `tools/rebuild/ultraman-zero__shining/fx-proposal.json`；Q 三态提案在 `tools/rebuild/ultraman-zero__shining/charge_policy.json`。共享 `content/presentation/phase3_projectiles.json` 与 `charge_overlay_policy.json` **未修改**，主会话登记前这些光效不可见。
- `definition.json` 如实标为 `stage1_identity_anchor_only`、`playable=false`、`select_visible=false`，`unsupported_moves` 列 47 项：本形态尚无任何状态帧、招式帧或 `form_switch`，不能冒充可开局。动作帧仍须逐段从本形态待机锚生成、装格、`recalc_move_hurtboxes` 重算受击框后才能置可玩。
- `state_frames.json` 的逐帧受击框是基础赛罗占位，已写入 `definition.state_frames_note`，安装本形态帧后必须重算。
- 未复制的历史文件：基础赛罗的 `production_plan.json`、`MOVES.md`、`SOUNDS.md` 不作为本形态正式内容；音频 id 暂沿用赛罗同角色条目。

## 2026-11-12 阶段 3：form_switch 六帧与运行特效家族

### form_switch 六帧（纯人物，无光效）

- 唯一动作参考仍是 `stage1/idle/frames/pixel-raw-04-official-side-anchor.png`（SHA `6816181d…c19057`），六帧逐帧生成，提示词只写本帧姿势，固定尾串要求右侧视、完整、透明、只画人物本体、无光束/光晕/颗粒/蓄气圈/贴掌光/飞行物。
- 姿势序列：深屈膝蓄势（00）→ 后腿再屈、双拳前收（01）→ 髋先转、左臂横胸（02）→ 躯干继续拧转、双臂随肩摆（03）→ 双脚落回、双拳抬护架（04）→ 与待机锚一致的护架落定（05）。相邻帧手/臂/腿均有可见位移；05 与锚同姿势属落定帧，不是复制凑帧。
- 00 首版（`switch-00-raw` v1，SHA `da5ade6b…7a2531`）姿势成立但提示词身份约束较弱；按同一姿势重生成 v2（SHA `bc89a8a6…2612ae`），头部结构与锚一致后采用。v1 已删除，SHA 留档。
- 最终 raw（1024×1536，实体站高 972/1049/1098/1094/1096/1100，SHA 依次 `bc89a8a6…`/`2fe1ab4e…`/`e24f5c75…`/`28a67215…`/`f6ca8688…`/`acebdf5b…`）。
- 头部原生像素对比 `stage1/form_switch/heads-raw.png`（SHA `6387e7e2…18bfaf`）：眼行脸宽 锚 203、00 203、01 208、02 209、03 221、04 214、05 203 px；03 为转身相、读数 +8.9% 属转头与前倾，按同一眼行口径登记，不做缩头。双镖根前尖后上、刃间凹口、蓝额灯/蓝眼/侧脸轮廓一致，没有单根高羽冠。
- 落格：`land_clip.py`，固定源比例 `188/1100=0.170909091`、256 格、根点 [128,248]、脚底 247、`cells.json` 冻结 32 色板。六帧实体高 166/179/188/187/187/188 px；00 为深蓄势蹲姿（−11.6%，登记不返修），01 −4.6%，02–05 在 ±0.5% 内；相邻站高变化最大 7.8%（00→01，蓄势起身），其余 ≤5.0%。逐帧 32 色、二值 Alpha、单连通 1、bbox 均在格内，脚底全部 247。
- 产出：`stage1/form_switch/cells/form_switch-00-cell.png`…`05-cell.png`（SHA `0e423396…`/`dc8a8074…`/`484e00f5…`/`22a7348a…`/`7e5d46dc…`/`0ef836ab…`），逐帧记录 `stage1/form_switch/cells/cells.json`（SHA `a55f37c7…`），联系表 `stage1/form_switch/contact-cells.png`（SHA `2518ba31…`）。
- **未装 assets**：本形态仍未完成全部 113 段动作，按硬点不得只装 form_switch 就切换 `presentation.model`；六帧留在 art，待全量动作装格时随 manifest 一起安装。

### 运行特效家族（15 个 pending id）

- 目录：`assets/effects/ultraman-zero__shining/fx-family-pixelfx-20261112-v1/`；提案 `tools/rebuild/ultraman-zero__shining/fx-proposal.json`（SHA `a33680a0…`），Q 三态提案 `charge_policy.json`（SHA `5c4538bc…`），逐帧核验 `fx-report.json`，联系表 `fx-contact.png`（SHA `94ad8fb8…`）。
- 8 个招式/命中段（wide_beam/wide_hit/emerium_beam/emerium_hit/slugger_flight/slugger_trail/slugger_hit/slugger_catch）：复制同角色基础赛罗 PixelFX 自绘图集，像素未改，只改路径与归属；每段 provenance 记录 `reused_from` 与原 atlas SHA。飞行 `slugger_flight` 与命中 `slugger_hit` 分开；`special3.feedback.projectile_impacts` 为 `{pending_shining_slugger_flight: pending_shining_slugger_hit}`。
- 4 个通用段（pulse/impact_light/impact_guard/impact_heavy）：复制项目共享图集到本形态目录，保留原 rects/ticks/anchor，不改共享文件。
- 3 个 Q 蓄气段：`bake_qcharge_hard.mjs` 沿用基础家族 `chargeAura` 形状，PixelFX 离线重烘为二值 Alpha（cutoff 32）并量化到青蓝 8 色；9/24/9 帧，384×256，anchor [192,246]，起势/收势首末帧加地面种子火花保证非空；亮芯、外焰、颗粒与相位变化保留。
- 15 段逐帧核验：真透明、Alpha 二值、色数 3–21（Q 7）、atlas SHA 与提案一致、rects 均在图内、Q 帧盒 9/24/9 与 policy 帧数一致。命中/头镖等多连通块是特效颗粒/分段，按 AGENTS“独立颗粒另行核”记录；二值 Alpha 已无半透明晕边。共享 `phase3_projectiles.json` 与 `charge_overlay_policy.json` 未修改。

### 未完与卡点（本轮如实记录）

- 动作本体仍缺 497 个唯一帧：基础 manifest 113 段共 498 帧（47 招 285 帧 + 66 个状态段 213 帧），idle 单帧由已签身份锚承担，form_switch 6 帧另计并已完成。
- 每帧须单独调用 MCP 生成并目视核；6 路并行实测约 5 分钟/6 帧（含一次重生成），497 帧按此约 7 小时并需 25–50 万 token 量级的提示与结果，单会话放不下。项目禁止复制姿势凑帧，也禁止拼图多姿势输出（基础赛罗历史已拒收 4×4 拼图），帧数不能压缩。
- 已试两种修法：①加强身份约束提示词（switch-00 v2）——身份通过，帧数不变；②6 路并行 MCP 批生成——可运行，但吞吐与上下文仍不足以在本轮完成。下一步须按 clip 分组分多轮续产，不能把阶段 2/3 当完成态。

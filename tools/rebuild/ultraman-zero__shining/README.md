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

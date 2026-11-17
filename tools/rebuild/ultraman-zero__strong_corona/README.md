# 强壮日冕赛罗（ultraman-zero__strong_corona）制作记录

分支：worktree-agent-aa55601035b8c40e7。只写本形态目录：
`art/fighters/ultraman-zero__strong_corona/`、`content/fighters/ultraman-zero__strong_corona/`、
`assets/fighters/ultraman-zero__strong_corona/`、`assets/effects/ultraman-zero__strong_corona/`、
`tools/rebuild/ultraman-zero__strong_corona/`。不改共享 phase3/policy、roster、AGENTS.md、docs、基础赛罗目录。

## 站高口径（2026-11-12 协调者更正）

基础赛罗现装身份锚 `art/fighters/ultraman-zero/model/identity-anchor.json` 的
standing_height=188（冠顶→鞋底；`idle-00-cell.png` 实测 186–188，脚底 247）。
本形态一律按 **188** 同口径对齐；此前简报中的 172 是另一张短冠候选，作废。
格 256、根点 [128,248]、接地脚底 247。体型一致性按 188 核。

## 源与朝向

- 主源：`art/fighters/ultraman-zero__strong_corona/sources/toyhaco-shfiguarts-2019/`，
  第三方拍摄的官方 S.H.Figuarts 强壮日冕赛罗（TAMASHII NATION 2019 限定）测评照片。
  source_kind=`official_figure_third_party_photo`，toy_reference=true。
  右全身 `strong-corona-side-right-full-01.jpg`（600×900，SHA eb3fa79b…）为唯一送图侧视源；
  右头肩 `…-head-01.jpg`（600×400，SHA 261a6ecc…）同角度补结构；
  左全身 `…-left-full-01.jpg` 只作镜像核对，不送图。明细见该目录 `source.json`。
- 朝向已按源图定死：人物面朝画面右。金色头冠宽根压前额/眼列上方，刃向后掠，后端尖角向上后方翘；
  右侧视冠顶 x=213 < 眼列 x=341（头特写 176 < 350），左侧视镜像 x=393 > 259。
  红肘红前臂红拳整段连拳背；金色 X 胸带在红胸正面、银腰上方；金边蓝芯胸计时器在胸前；
  前大腿金色人字甲、前小腿红条收尖、银靴、银面黄眼、前额边缘绿额灯。
- 玩具球关节、转轴、插接缝、塑料高光在生成时一律去掉；玩具只借侧视轮廓、结构位置与体量，
  不借材质、不借玩具身材。

## Phase 1（已完成，2026-11-12）

1. 格斗待机照片：MCP `codex/gpt-image-2` high，1024×1536，透明背景。
   参考＝右全身 + 右头肩 + 1 张已装机同风格成品（奥父 `art/fighters/father-of-ultra/stage1/cells/idle-00-cell.png`，
   SHA 63f51642…，只借前后错步、屈膝下沉、双拳胸前护架与画风，明确排除披风、角、红族造型）。
   要求纯右侧 90°、全身不裁切、脚外缘间距/站高 0.65–0.80、无 FX/地面/文字/边框。
2. 像素待机整帧：由该照片单参考转像素；落 256 格，站高 188、脚底 247、根点 [128,248]；
   ≤32 色且保住金冠、绿额灯、黄眼、红拳套、蓝芯计时器；二值 Alpha、主体单连通、四边留白。
   色板从本帧整图重定，不用 catalogue 旧板（旧板缺亮黄/绿/金）。
3. 通过原生格与 4× 最近邻核造型、画风、头肩比例、手脚体量后，再核站距/色数/Alpha；
   数值写入 `art/fighters/ultraman-zero__strong_corona/stage1/cells/cells.json` 与本文件。

### 落格数值与签署

- 待机照片：`art/fighters/ultraman-zero__strong_corona/stage1/idle/frames/stance-raw-01.png`
  实收 **1199×1312** RGBA（请求 1024×1536，按实收核），SHA `bdb91ed3…`；透明背景、无 FX/地面/文字；
  主体 Alpha16 bbox [182,34,998,1268]，站距 0.6615，双拳胸前护架，冠尖在眼后。
- 清边照：`…/stance-clean-01.png` 815×1233，SHA `7d4c9d2b…`；Alpha128 硬化+裁主体，未改人体。
- 像素整帧：`…/pixel-raw-01.png` 与 `…/pixel-raw-02.png` 拒收后已删；采用
  `…/pixel-raw-03.png` 1020×1542，SHA `2be6ecb8…`，站距 0.6566。
- 身份锚：`…/stage1/cells/idle-00-cell.png` **256×256**，SHA `91981850…`；
  严格 4× `idle-00-cell-x4.png` SHA `37524c66…`。
  格 256、站高 **188**（冠顶→鞋底）、脚底 **247**、根点 **[128,248]**；
  主体 bbox [69,60,191,247]，宽 123；**32 色、单连通、Alpha [0,255]**；
  脚外缘/站高 **0.6543**（123/188），左右脚底 247/245，差 2 px；
  head_height=43（启发式，只报告，不作门限）。
- 色板：32 色整图重定，强制保住金冠 244,182,28；金高光 253,236,152；黄眼 253,232,19；
  绿额灯 2,192,27；蓝芯计时器 0,73,216；亮红拳 243,64,71；主红 168,14,23；
  银亮 221,218,230；银中 156,152,168；臂甲蓝 88,175,240；黑描边 0,0,0。
  全套动作共用此板，不按身体区域重涂。
- 签署：**root_delegated_by_user**，`user_approved=false`；不冒充用户亲审。
- **已知问题**：待机为前弓步，前膝明显弯曲、后膝弯曲浅（近直）；数值门 0.65–0.80 与双脚接地通过，
  但未达基础赛罗双膝深屈的待机形态。诊断见
  `…/stage1/diagnostic/stance-reroll-2026-11-12.png` / `.json`。
  若用户否决后膝形态，整锚与下游动作撤销重定。
- 拒收记录（已删图，SHA/尺寸/原因留在 `stage1/requests.json`）：
  pixel-raw-01 站距 0.6387；pixel-raw-02 站距 0.710 但后腿拉直；
  stance-raw-02 站距 0.6236、背景不透明光晕、两脚不同底；
  stance-raw-03 站距 0.6086、背景不透明光晕、两脚不同底。
- 全部 MCP 请求、实收路径/尺寸/Alpha/SHA 与参考图 SHA：`…/stage1/requests.json`。

## Phase 2（待做）

- 复制基础赛罗 47 招（帧数、起止帧、伤害、能量、命中时序不变；只改 data_source/production_note/display_name），
  所有 effect id 改 `pending_corona_*`，清单写本目录 `fx-proposal.json`；不引用 `zero_fx_*`。
- 生成全部招式帧 + 基础赛罗现有全部状态片段 + 6 帧 `form_switch`（纯人物身体，蓄势→转身→落定，
  逐帧手脚可见位移，无光效）；全部只引本形态待机锚。投影类只画身体与手，不画能量球/飞行物。
- 同一固定比例落格；站姿帧与锚站高偏差 >8% 或相邻站姿帧 >10% 重掷并登记例外；
  `install_cells.py --fighter ultraman-zero__strong_corona --merge`，逐 clip 取自身格与根点；
  `recalc_move_hurtboxes.py` 重算受击框。
- 定义目录 `content/fighters/ultraman-zero__strong_corona/`：
  definition.json(playable=true)、state_frames.json、command_table.json、move_manifest.json，
  使该形态可选人独立开局；选人界面与 E 切换接线由主会话负责，本分支不改 roster/selection。
- 特效：PixelFX 离线烘焙真透明像素整帧，硬 Alpha、≤8 色、不引第三方图集；
  phase3 条目与 Q 蓄气三态只写本目录 `phase3_entries.json` / `charge_policy.json` 提案，等主会话合并。

## 刹车与签署

- 同一项连续拒收 3 帧即停，先出诊断图；同一问题最多 2 种修法。
- 自动评审按 root_delegated_by_user 签署，不写 user_approved，不把逻辑/资源检查写成画面或听感通过。

## 追加要求（协调者，2026-11-12）

- 本形态须能作为出场形态单独开局：manifest 必须包含基础赛罗现有全部状态片段，逐段用本形态待机锚重生成，
  禁止复用基础赛罗人物帧，不得用 model-native 静图顶替缺失片段。
- 另加 `form_switch` 6 帧纯人物身体（蓄势→转身→落定，手/臂/腿逐帧可见位移，无任何光效），
  格与根点同本形态，供战斗中按 E 切换形态播放。
- 特效仍全部 pending_*，不改共享 phase3/policy。

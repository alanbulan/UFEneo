# 盖亚奥特曼 · V2 返工诊断（2026-11-12）

本轮是只读复算与联系表抽样目视，未生成新帧、未改 assets/content、未安装、未提交、未跑 Godot/verify、无录屏、未听审。
基线：manifest 105 clip / 505 帧；现用待机站高 175；唯一 scale 0.169182；默认 cell/anchor {'width': 256, 'anchor': [96, 184], 'baseline': 248, 'foot_row': 247}。证据 SHA 见 `asset_baseline.json`。

## 本轮复算出的最严重 3 个根因

1. 身份门内容缺口：仓库没有本人 90° 真实侧视来源，金额刃/头壳侧视前后方向不能由正面或 3/4 图猜写；MOVES.md 开头仍写「未安装」，与当前装机数据不一致。
2. 人物帧仍含烘焙特效与双重特效：special3#9 橙红光刃、ranged_forward#4/#5 独立块 502/298 px；投射类手中不得画弹体。
3. 尺度与接线口径冲突：cells.json 顶层 anchor [96,184] 与装机 clip [128,248] 不一致，definition.json 也保留旧 [96,184]/target_height 184；motion_623#3 高度 227、special3 多帧 134–143；姿态感知偏差 42 帧、相邻跳变 26 组。

## 数值与目视证据

- 站姿类按姿态例外分开后：对锚偏差 >8% 共 42 帧，相邻站姿跳变 >10% 共 26 组；姿态例外 clip 67 个已逐帧登记高度，不以例外放行缩放。
- 待机装机 1 帧；前走/后走 {'walk_forward': 4, 'walk_back': 4}。待机需真呼吸循环；走路按 8 相骨长/引导核连续换腿，8 相不是装机帧数硬门，当前 4 帧仍需核接地与逐帧位移。
- state_frames 越界/冻结：[{"clip": "down", "rows": 35, "clip_frames": 2, "sprite_max": 1, "longest_same_sprite": 27, "frozen_segments": [{"sprite": 1, "ticks": 27}]}]。
- moves 未用满 sprite：[]。
- 联系表确认的烘焙 FX：special3#9 橙红光刃；单连通不等于无 FX，亮黄/红像素 1104 px、主体高 158；ranged_forward#4 4/8 邻域均 6 块，主体 6215 px，独立块 502 px；ranged_forward#5 4/8 邻域均 2 块，主体 5732 px，独立块 298 px。
- 高饱和亮色候选不单独判 FX（本人红银/深蓝本体颜色会误报）；独立连通块与联系表结论在 `clip_diagnosis.json` 分列。

## 逐 clip 分类统计

primary：{"fix_pose": 4, "fix_scale": 9, "keep": 64, "redraw": 28}；secondary：{"fix_identity": 1, "redraw": 1}。
任务书四类合并：{"保留": 64, "修尺度/姿态/身份": 13, "重画": 28, "数据帧序修复": 0}。
`keep` 只是未触发自动数值门；未逐帧目视的 clip 不写造型通过。全部逐 clip 数值在 `clip_diagnosis.json`。

## 重画优先级

P0（时间轴/身份门）：无 primary fix_timeline；身份与 anchor/色板缺口见 identity_card.json。
P1（纯人物重画，先去烘焙 FX 与双特效）：air_pulse, air_special, charge, charge_start, charge_stop, dash_throw, down, guard, heavy, hit_mid, idle, ko, launcher, light1, light2, light3, low_pulse, motion_214 …。
P2（修尺度/姿态/身份、补逐帧骨长证据）：见 `clip_diagnosis.json` 的 fix_scale / fix_pose / fix_identity 与 `storyboard.md` 的姿态例外登记。

## 三槽、发射点与特效登记

- 依据文件：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/content/fighters/ultraman-gaia/MOVES.md`。光子冰刀 Photon Edge：头部水晶聚能拉出光刃、鞭状横斩，V1/V2 可用。 量子流线 Quantum Stream：双臂 T 字转右臂 L 字发射，V2 威力 2 倍。 光子粉碎机 Photon Crusher：V2 继承自阿古茹的头部必杀光线，三段蓄能为游戏编排；光子流线是 SV 专用，不得借来凑槽。 空中量子流线是游戏改编，原剧无空中向下发射依据。
- 差异风险：special 为贴头 strike、special2 gaia_fx_stream_beam、special3 gaia_fx_crusher_beam；air_special 用通用 beam_loop 且为游戏改编。内容缺口：MOVES.md 写明光色均为次级资料游戏取色，未逐帧核对影片、未写集数/时码；当前 V2 不开放 SV 技能。
- emission_points.json 存在=False；运行时 spawn/anchor 样例见 `clip_diagnosis.json.emission.runtime_spawn_examples`。重画后必须新建人工依据表，双向误差 ≤2 px 才算过。
- phase3 722 条；未登记 id=[]；专属 SHA 不符=[]；Q 三态 placement 已登记。本轮 effect id 登记不是缺陷；不得重复补登记当返工成果。换贴图后才按 SHA 补登记

## 返工顺序

1. 先补本人 90° 真实侧视来源并定金额刃前后判据；同步清理 MOVES.md 旧草案与 cells/definition 顶层 anchor 冲突
2. 重画 special3#9、ranged_forward#4/#5 等含烘焙特效帧及全部投射类纯人物帧
3. 重画待机/按 8 相引导的走路/三槽本人动作，修 special3、motion_623、charge 等站姿跳档
4. 补 emission_points.json 并逐 clip 安装、实机双朝向验收

## 每阶段验收命令与门值

所有 Godot 导入/验证/录制经 `.venv/bin/python tools/godot_lock.py -- <命令>` 串行；不删活锁、不关用户进程。
- 阶段 A：核 `identity_card.json` 的锚 SHA、真实侧视来源、标志结构前后判据、唯一 scale、≤32 色板识别色、逐 clip cell/anchor；造型须看原生格与严格 4×，站距/色数/Alpha 不代替造型。
- 阶段 B：核 `storyboard.md` 每帧支撑脚/髋/肩/双拳/头/本人部件/位移/起手发力收势/相邻差分/循环；技能依据必须来自本人 MOVES.md 与 moves/*.json，无集数/时码标内容缺口。
- 复算证据：`.venv/bin/python art/fighters/ultraman-zero/stage1/rework-20261112/ufeneo_rework_diag_v1.py`（只读 assets/content/reports，重写三份 measurement_evidence.json）；另跑 `.venv/bin/python tools/check/frame_scale_jumps.py --fighter <id> --clip <clip> --verbose`。
- 阶段 D 硬门：主体 alpha≥128；4 邻域连通块=1、8 邻域辅助；二值 Alpha；≤32 色整图映射；四边不裁；站姿类高度偏差 ≤8%、相邻跳变 ≤10%；相邻剪影 XOR/Union ≥0.10；循环首尾目视可接（辅助门 <0.20）；姿态例外登记高度与骨长。
- 阶段 D 待机/走路：待机头纵幅 ≤4 px、相邻含首尾 ≤2 px、横漂 ≤2 px、一次下沉再回升；走路按 8 相骨长/引导核（不要求装机 8 帧）、眼纵幅 ≤8 px、相邻 ≤4 px、支撑点世界坐标偏差 ≤8 px。
- 阶段 D 特效分离：人物帧单连通，主体外 alpha≥16 ≤100 px、主体外 alpha≥200=0（外扩 3 px 口径），alpha 1–15 尘点只登记；独立颗粒/飞行物硬门另判；PixelFX 运行时层硬 Alpha、≤8 色、亮芯/外焰/颗粒/相位变化。
- 阶段 E：`.venv/bin/python tools/rebuild/shared/emission_check.py --characters <id>`（先建 emission_points.json，误差 ≤2 px）；`.venv/bin/python tools/art/install_cells.py --fighter <id> --only <clip> --merge --dry-run`，核 cell/anchor/rects/ticks/atlas SHA 后正式 `--only <clip> --merge`；禁止全量重装。
- 阶段 F：`.venv/bin/python tools/godot_lock.py -- .venv/bin/python tools/verify.py --keep-going` 只证明逻辑/资源登记；另报逐帧美术门独立结果。主游戏 `开始游戏.command` / `app/scenes/main.tscn` 训练/F1，两个朝向、720/1080、真实输入、独立回放、原速逐动作看画面；必要时短录屏审后删除，无录屏写无录屏。

## 风险

- 没有本人 90° 真实侧视来源；金额刃/头壳侧视前后方向禁止凭正面或 3/4 图写进生成规格。
- cells.json 顶层 anchor [96,184] 与全部装机 clip anchor [128,248] 不一致；definition.json 也保留 [96,184]/target_height 184。
- 图鉴 model-native.png 色板与冻结动作色板交集为 0；不可直接跑 stage_cells.py 默认色板。
- MOVES.md 开头仍写未生成动作/未写 moves/未安装，是旧草案，不作为当前状态证明。
- `stage_cells.py` 默认色板来自 `assets/fighters/<id>/catalogue/model-native.png`，与本批冻结动作色板不一致；返工必须显式传本人冻结色板或走 `forge_backend` 等价离线接口，不按身体区域局部重涂。
- 共享旧式 phase3 条目 impact_guard/impact_heavy/impact_light/beam_hit 未写 atlas_sha256 字段，不是未登记；不要为凑「补登记」改动已核资源。
- 逐 clip 安装不得用本批第一组 cell/anchor 缩放其余组；杰斯提斯 4 个 192 格 clip 与三角色 288 格 air_special 必须按自身值。
- 自动数值 keep 不等于造型通过；down/ko/win 等跨角色模板化仍须按本人身份看原生格联系表。

## 明确「本轮没做的事」

- 没有生成任何图片，没有改 `assets/`，没有改 `content/`，没有 git commit，没有安装或覆盖装机图集。
- 没有跑 Godot、tools/verify.py、主游戏双朝向 720/1080、真实输入/独立回放/原速画面；无录屏，未听审，未冒称用户亲审。
- 没有重建或补写 emission_points.json、没有重画任何帧、没有补编剧集/时码/原剧镜头；storyboard.md 是待制作规格，不是已完成动作。
- 没有把逻辑检查、色数、站距、Alpha、连通块或文件数量写成美术/听感通过；诊断图表未另生成（本轮只交 JSON 与 Markdown 及证据脚本）。

# 赛罗奥特曼 · 基本红蓝形态 返工诊断（2026-11-12）

本轮是只读复算与联系表抽样目视，未生成新帧、未改 assets/content、未安装、未提交、未跑 Godot/verify、无录屏、未听审。
基线：manifest 114 clip / 504 帧；现用待机站高 172；唯一 scale 0.158767；默认 cell/anchor {'width': 256, 'anchor': [128, 248], 'baseline': 248, 'foot_row': 247}。证据 SHA 见 `asset_baseline.json`。

## 本轮复算出的最严重 3 个根因

1. 时间轴接线错：state_frames.idle 60 行 sprite 0–5 对装机 1 帧、walk_forward 70 行 0–7 对装机 4 帧；side_view.gd:450 在 idle 等非 walk 状态 clampi 到末帧；walk 不走该分支，前走越界只造成 state_frames 与 4 帧图集不对应。
2. 站姿类整人缩放：heavy 高度 130/165/128/155、launcher#4 213、intro#0 104；对锚 172 的姿态感知偏差 32 帧、相邻跳变 24 组。
3. 人物帧与 FX 未分离、动作模板化：light1#2 青白掌前光块与 16 个独立连通块；三槽联系表仍是护架/单臂前伸/双掌前推近似姿势。

## 数值与目视证据

- 站姿类按姿态例外分开后：对锚偏差 >8% 共 32 帧，相邻站姿跳变 >10% 共 24 组；姿态例外 clip 72 个已逐帧登记高度，不以例外放行缩放。
- 待机装机 1 帧；前走/后走 {'walk_forward': 4, 'walk_back': 4}。待机需真呼吸循环；走路按 8 相骨长/引导核连续换腿，8 相不是装机帧数硬门，当前 4 帧仍需核接地与逐帧位移。
- state_frames 越界/冻结：[{"clip": "crouch", "rows": 24, "clip_frames": 2, "sprite_max": 1, "longest_same_sprite": 12, "frozen_segments": [{"sprite": 0, "ticks": 12}, {"sprite": 1, "ticks": 12}]}, {"clip": "down", "rows": 35, "clip_frames": 2, "sprite_max": 1, "longest_same_sprite": 27, "frozen_segments": [{"sprite": 1, "ticks": 27}]}, {"clip": "idle", "rows": 60, "clip_frames": 1, "sprite_max": 5, "longest_same_sprite": 10, "frozen_segments": [{"sprite": 0, "ticks": 10}, {"sprite": 1, "ticks": 10}, {"sprite": 2, "ticks": 10}, {"sprite": 3, "ticks": 10}, {"sprite": 4, "ticks": 10}, {"sprite": 5, "ticks": 10}]}, {"clip": "walk_forward", "rows": 70, "clip_frames": 4, "sprite_max": 7, "longest_same_sprite": 13, "frozen_segments": [{"sprite": 2, "ticks": 13}, {"sprite": 6, "ticks": 10}]}]。
- moves 未用满 sprite：[{"move": "motion_214", "clip_frames": 8, "sprite_unique": [0, 1, 2, 3, 7], "unused_sprites": [4, 5, 6]}, {"move": "motion_236", "clip_frames": 8, "sprite_unique": [0, 1, 2, 7], "unused_sprites": [3, 4, 5, 6]}, {"move": "motion_623", "clip_frames": 8, "sprite_unique": [0, 1, 2, 7], "unused_sprites": [3, 4, 5, 6]}]。
- 联系表确认的烘焙 FX：light1#2 青白掌前光块/碎块；4 邻域 16 块、8 邻域 15 块，(45,201,248) 954 px。
- 高饱和亮色候选不单独判 FX（本人红银/深蓝本体颜色会误报）；独立连通块与联系表结论在 `clip_diagnosis.json` 分列。

## 逐 clip 分类统计

primary：{"fix_pose": 2, "fix_scale": 12, "fix_timeline": 2, "keep": 72, "redraw": 26}；secondary：{"fix_timeline": 3, "redraw": 2}。
任务书四类合并：{"保留": 72, "修尺度/姿态/身份": 14, "重画": 26, "数据帧序修复": 2}。
`keep` 只是未触发自动数值门；未逐帧目视的 clip 不写造型通过。全部逐 clip 数值在 `clip_diagnosis.json`。

## 重画优先级

P0（时间轴/身份门）：idle, walk_forward。
P1（纯人物重画，先去烘焙 FX 与双特效）：air_pulse, air_special, charge, charge_start, charge_stop, dash_throw, down, guard, heavy, hit_mid, ko, launcher, light1, light2, light3, low_pulse, motion_214, motion_22 …。
P2（修尺度/姿态/身份、补逐帧骨长证据）：见 `clip_diagnosis.json` 的 fix_scale / fix_pose / fix_identity 与 `storyboard.md` 的姿态例外登记。

## 三槽、发射点与特效登记

- 依据文件：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/content/fighters/ultraman-zero/MOVES.md`。赛罗集束射线 Wide Zero Shot：右前臂宽青蓝束，24/32/16，72 tick。 艾梅利姆切割 Emerium Slash：额灯青绿细束带新月刃波，32/32/16，80 tick。 赛罗头镖 Zero Slugger：双实体飞刃、外飞回收，32/48/16，96 tick。 空中集束射线是游戏改编，原剧无空中发射依据，不冒称原剧。
- 差异风险：三槽分别 zero_fx_wide_beam / zero_fx_emerium_beam / zero_fx_slugger_flight+trail+catch，特效 id 已分化；仍须重画本人动作。内容缺口：MOVES.md 只记已装状态和名称，未给剧集/时码/逐帧镜头；原剧一级/二级/三级名称仍属内容依据缺口，制作代理不得补编镜头。
- emission_points.json 存在=False；运行时 spawn/anchor 样例见 `clip_diagnosis.json.emission.runtime_spawn_examples`。重画后必须新建人工依据表，双向误差 ≤2 px 才算过。
- phase3 722 条；未登记 id=[]；专属 SHA 不符=[]；Q 三态 placement 已登记。本轮 effect id 登记不是缺陷；不得重复补登记当返工成果。换贴图后才按 SHA 补登记

## 返工顺序

1. 先修赛罗 idle/walk_forward 时间轴与呼吸循环/走路 8 相引导的对应关系（不要求装机 8 帧）
2. 重画 light1 与三槽/投射类纯人物帧
3. 按唯一 scale 修 heavy/launcher/intro/win 等站姿跳档
4. 补 emission_points.json 并逐 clip 安装、实机双朝向验收

## 每阶段验收命令与门值

所有 Godot 导入/验证/录制经 `.venv/bin/python tools/godot_lock.py -- <命令>` 串行；不删活锁、不关用户进程。
- 阶段 A：核 `identity_card.json` 的锚 SHA、真实侧视来源、标志结构前后判据、唯一 scale、≤32 色板识别色、逐 clip cell/anchor；造型须看原生格与严格 4×，站距/色数/Alpha 不代替造型。
- 阶段 B：核 `storyboard.md` 每帧支撑脚/髋/肩/双拳/头/本人部件/位移/起手发力收势/相邻差分/循环；技能依据必须来自本人 MOVES.md 与 moves/*.json，无集数/时码标内容缺口。
- 复算证据：`.venv/bin/python tools/rebuild/seven-character-rework-20261112/ufeneo_rework_diag_v1.py`（只读 assets/content/reports，重写三份 measurement_evidence.json）；另跑 `.venv/bin/python tools/check/frame_scale_jumps.py --fighter <id> --clip <clip> --verbose`。
- 阶段 D 硬门：主体 alpha≥128；4 邻域连通块=1、8 邻域辅助；二值 Alpha；≤32 色整图映射；四边不裁；站姿类高度偏差 ≤8%、相邻跳变 ≤10%；相邻剪影 XOR/Union ≥0.10；循环首尾目视可接（辅助门 <0.20）；姿态例外登记高度与骨长。
- 阶段 D 待机/走路：待机头纵幅 ≤4 px、相邻含首尾 ≤2 px、横漂 ≤2 px、一次下沉再回升；走路按 8 相骨长/引导核（不要求装机 8 帧）、眼纵幅 ≤8 px、相邻 ≤4 px、支撑点世界坐标偏差 ≤8 px。
- 阶段 D 特效分离：人物帧单连通，主体外 alpha≥16 ≤100 px、主体外 alpha≥200=0（外扩 3 px 口径），alpha 1–15 尘点只登记；独立颗粒/飞行物硬门另判；PixelFX 运行时层硬 Alpha、≤8 色、亮芯/外焰/颗粒/相位变化。
- 阶段 E：`.venv/bin/python tools/rebuild/shared/emission_check.py --characters <id>`（先建 emission_points.json，误差 ≤2 px）；`.venv/bin/python tools/art/install_cells.py --fighter <id> --only <clip> --merge --dry-run`，核 cell/anchor/rects/ticks/atlas SHA 后正式 `--only <clip> --merge`；禁止全量重装。
- 阶段 F：`.venv/bin/python tools/godot_lock.py -- .venv/bin/python tools/verify.py --keep-going` 只证明逻辑/资源登记；另报逐帧美术门独立结果。主游戏 `开始游戏.command` / `app/scenes/main.tscn` 训练/F1，两个朝向、720/1080、真实输入、独立回放、原速逐动作看画面；必要时短录屏审后删除，无录屏写无录屏。

## 风险

- cells.json 早期字段 target_standing_height=188 是身份锚原生站高；2026-11-11 重标定后装机站高 172、scale 0.158767，本卡片以后者为唯一返工尺度。
- definition.json presentation.cell=288/target_height=188 是旧口径；装机 113 个 clip 为 256、air_special 为 288。
- assets/fighters/ultraman-zero/catalogue/model-native.png 的 32 色与冻结动作色板交集为 0；不可直接跑 stage_cells.py 默认色板。
- `stage_cells.py` 默认色板来自 `assets/fighters/<id>/catalogue/model-native.png`，与本批冻结动作色板不一致；返工必须显式传本人冻结色板或走 `forge_backend` 等价离线接口，不按身体区域局部重涂。
- 共享旧式 phase3 条目 impact_guard/impact_heavy/impact_light/beam_hit 未写 atlas_sha256 字段，不是未登记；不要为凑「补登记」改动已核资源。
- 逐 clip 安装不得用本批第一组 cell/anchor 缩放其余组；杰斯提斯 4 个 192 格 clip 与三角色 288 格 air_special 必须按自身值。
- 自动数值 keep 不等于造型通过；down/ko/win 等跨角色模板化仍须按本人身份看原生格联系表。

## 明确「本轮没做的事」

- 没有生成任何图片，没有改 `assets/`，没有改 `content/`，没有 git commit，没有安装或覆盖装机图集。
- 没有跑 Godot、tools/verify.py、主游戏双朝向 720/1080、真实输入/独立回放/原速画面；无录屏，未听审，未冒称用户亲审。
- 没有重建或补写 emission_points.json、没有重画任何帧、没有补编剧集/时码/原剧镜头；storyboard.md 是待制作规格，不是已完成动作。
- 没有把逻辑检查、色数、站距、Alpha、连通块或文件数量写成美术/听感通过；诊断图表未另生成（本轮只交 JSON 与 Markdown 及证据脚本）。

# 盖亚 stage1 第一批：作废

2026-11-09 用户判定作废：**形象不对**，且待机是“双脚像人一样站着”，不是已装机角色
那种屈膝分开、双拳护架的格斗架势。

## 根因

这批动作帧只引用了 `art/fighters/ultraman-gaia/model/identity-anchor-x4.png`。
该锚的原生尺寸只有 **27×154 像素**（图鉴定稿裁到 Alpha bbox），4× 后是 108×616。
图片模型从这个宽度拿不到肩宽、四肢粗细、胸甲结构，于是自己补了一套身材——
所以配色对、轮廓不对。对比：佐菲的定稿是 110×173，同样的流程就正常。

## 改法

动作帧不再只引像素锚，改走“真实皮套照 → 待机架势 → 像素整帧 → 该帧当身份锚”。
细则见 `docs/STAGE1_STANDARD.md`。

## 已删

`art/fighters/ultraman-gaia/stage1/*`（16 张 raw）与 `reports/ultraman-gaia/stage1/*`。
身份锚与 `sources/ref-01.webp`（官方皮套照）保留。

## 接续诊断：站距暂停（2026-11-09）

新路线的 `pixel-01` 曾被标成 selected，但脚外缘间距/站高复测只有 **0.5455**，
仍未过 0.65–0.80；两鞋底高差换算约 6.31 原生像素。照片 `stance-03` 则是宽比 0.93
的深蹲马步、脸正对镜头，不能作为固定右侧视待机基准。

本轮按 `root_delegated_by_user` 撤销这两张的 selected 标记与动作身份锚；
保存 [诊断图](../../../art/fighters/ultraman-gaia/stage1/diagnostic/stance-gate.png) 及同名 JSON。
同一站距问题此前已有连续三张拒收，且已换过两种路线，本轮不再重生成。
淘汰原图与落格图直接删除，仅在 requests 的 attempts 保留 SHA 和拒收原因；
重复皮套照也移除，引用归回 `sources/ref-01.webp`。未安装、未做实机验收。

## 新中立身体基准路线：照片门拒收（2026-11-09）

本轮审核口径为 `subagent_candidate_review`，不是用户或根已亲审。根允许本角色尝试新链，
不表示批准旧图；既有连续 3 张站距拒收和两种失败路线均保留，不清零。

- 新本人源：圆谷盖亚角色页直接引用的 `hero_gaia-1.png`，现存于
  `art/fighters/ultraman-gaia/sources/official-pose-20261109-hero/`，SHA
  `9c245f9d736271ce51bc9bbf602b6ac3ea6c6aae6059ebbee80b281feea24cb2`。
  实际黑金胸护纹、青蓝三角胸灯、金额饰和红银皮套与当前 V2 外形一致；它是
  **正面中立皮套照**，只定身份与正常身体体量，不冒称已有官方右侧护架。
- 与旧路线的区别：不用旧斜透视弓步照继续扭相机，也不直接把皮套照+初代转像素；
  改用中立本人基准，在**照片步**先锁画面水平方向分脚、同鞋底线与浅屈膝护架，
  原装机初代只借站姿。计划照片过门后才单参考转像素。
- 实际唯一生成请求：MCP `image-55259-18`，`codex/gpt-image-2` / high / transparent，
  请求和实收均 1024×1536，实收 RGBA 有 255 种 Alpha（0–254），usage/费用未知。
  原图 SHA `879f8b1fcd64aadab1bdd46bcbd84eee8d5b5a916d6fdf3fd9d534d8b5ef1a3e`。
- **照片门失败**：脚外缘跨度 786 / 站高 1390 = **0.56547**，未过 0.65–0.80；
  鞋底差约 **1.22 原生像素**，虽比旧 6.31 明显改善，也不能替站距通过。
  前腿屈膝可读，后腿接近直线；本人贴身肩部、正常拳靴、完整轮廓可读，但未签造型。
- 原生诊断统一按 154/1390 整图缩小：192×192、站高154、脚跨度87、底行183/182、
  32色、二值Alpha、单连通；4×最近邻逐像素重复一致。
  这些只为失败诊断，**不是 GPT 生成的待机像素锚**。通用32色照片缩小版吞掉青蓝胸灯
  与浅黄眼，不作为生产色板；完整forge依赖缺失，仅用独立kCentroid，未执行网格检测。
- 本轮硬姿态拒收新增1，连续计数 **3→4**，当前新路线只执行一次后再暂停；
  **未发像素化请求、无建议动作身份锚、未铺下游、未安装、未启动Godot、无录屏**。

诊断入口：
- `art/fighters/ultraman-gaia/stage1/diagnostic/stance-04-gate.png`（照片缩略+原生+严格4×）；
- `art/fighters/ultraman-gaia/stage1/diagnostic/stance-04-gate.json`（真实收据、prompt、SHA、比例、边界）；
- `stance-04-native-diagnostic.png` / `stance-04-native-diagnostic-x4.png`（同目录，明确非动作参考）。

拒收原图已核消费者、授权绝对路径与SHA后直接删除；同页下载的1个标题logo和3张裁脚/遮脚
原剧照也已核SHA直接删除。三张动作照个别胸型不可见，不沿用先前速读的“全为V1”判断。本角色旧ref-01、旧诊断、旧图鉴锚和原装机姿态参考均保留，
未触碰其它角色或共享/运行时文件，没有备份、提交或推送。

下一步最小可执行办法：根先审诊断；若明确允许新的构图方案，再用同一官方V2身体基准整帧
生成一张1536×1024横向透明照片，先核横向分脚和双膝浅屈，再单参考转像素。
本轮不执行，不拉宽现图、不拼腿、不改阈值；也可转人工选择可靠本人完整姿态源。

## 明确占画布比例的新构图：像素候选待根审（2026-11-09）

根实际看过 stance-04 拒收诊断后，另准许这项新构图一次；历史连续4次站距拒收和旧路线
不清零。本轮未找图、下载或恢复任何已删源，只使用保留的官网V2中立皮套。

- **方法差异**：把官网完整Alpha主体统一缩放为506×1100，置于1024×1536透明画布
  的[259,311]，底行1410；不改身体姿态，不切肢/拼片/拉宽。首参考是这张明确宽留白
  `neutral-v2-wide-canvas-05.png`，不是直接拿瘦中立原图撑满。
  输入SHA `db80fd68ed225bc72346a9b4dedcbd1883e6a5be12c89468bcccfe5a7dfa7c27`。
  初代现用参考仅借站法，原文件未改、未另存副本。
- **照片真实请求**：`image-55259-21`，实收1024×1536 RGBA、Alpha0–254，站高1045、
  脚距722/1045=**0.690909**，鞋底差约1.03原生px。本人V2、正常拳靴、贴身肩部及
  浅屈膝侧向护架可读；子代理静审后仅单参考转像素，生成照片不冒称原剧照。
  当前源 `stage1/idle/frames/stance-raw-05-explicit-canvas.png`，SHA
  `e391a1f2bd601291aa64d6f71871cbbb17d4fa337a51b6259a9a440d05f3ef88`。
- **像素真实请求**：`image-55259-23`，只引上张照片；实收1024×1536 RGBA、Alpha0–254，
  站高1048、脚距729/1048=**0.695611**。当前源 `pixel-raw-02-explicit-canvas.png`，SHA
  `d509c66381d5b3ede392b65f406bfe04d652a841be28019218e0851ec874fb7e`。
  两次均 `codex/gpt-image-2` / high / transparent，usage与费用均未知。
- **最终原生候选**：`stage1/cells/idle-candidate-05-cell.png`，192×192，站高154、脚距
  **107/154=0.694805**、鞋底183/182、单连通、二值Alpha、32色。
  人工稳定头壳最大行22，对旧定稿22；60–62行是颈肩扩张，不作头宽。
  正常拳靴与贴身肩部保持，未靠局部缩头签比例。青蓝胸灯与浅黄眼在原生/4×可辨。
- 落格只用一个比例154/1048。完整forge依赖仍缺失，使用独立kCentroid和全图色板量化，
  **未声称网格检测通过**。从当前像素整图保留全局青蓝/浅黄色类后学习完整32色，
  不按身体区域局部重涂；全套后续须共用 `stage1/cells/cells.json` 所存的同一比例与色板。
- **建议唯一动作参考（未签）**：`stage1/cells/idle-candidate-05-x4.png`，严格4×逐像素
  重复，主体原生宽107，非旧27px图鉴锚。原生SHA
  `24da22f59292e1bd16ac8aae6231ddceeaa70623161784ac65f616f6de294d00`；4×SHA
  `73f1690df4846b7e2b8a281dcc2fbc3fdf013cd12f25e5bb89829b6f08750fe9`。
- 审阅入口：`stage1/cells/idle-candidate-05-review.png`，源照片、生成护架、原生和严格4×。
  全部新审核仅 `subagent_candidate_review`，**尚未根审、无正式动作身份锚**；后靴略向镜头
  与近远读法交根看整体，不只凭站距/色数签造型。本轮不铺下游、不安装、不启动Godot。

本轮只新增这一张照片与一张像素候选及必要输入/落格/记录，未删除现用材料、未触碰其它角色
或共享文件，未提交/推送，无录屏。下一步仅交根复审，根通过后再在本代理上下文继续基础动作集。

## 最小集完成（2026-11-09）

本轮只更新记录：不改图、不重生成、不安装、不启动 Godot、不提交。

- **19 组 47 帧全部出格**：idle 2、walk_forward 4、walk_back 4、dash_start 2、dash 4、
  takeoff 2、air_rise 1、air_fall 1、land 2、light1 3、light2 3、light3 4、heavy 4、
  hit 2、block 1、down 2、getup 2、win 2、ko 2。
- **记录状态**：此前根已通过的 light1/2/3、heavy、hit、block、down、getup、win、ko
  在 `stage1/cells/cells.json` 的 `action_set_status` 中由 `review_pending` 改为
  `root_delegated_by_user`（不是 `user_approved`）。idle、walk_forward、walk_back、
  dash_start、dash、takeoff、air_rise、air_fall、land 保留 `selected`。
- `stage1/requests.json` 的 selected 帧状态与全部 SHA、尺寸、拒收记录未改；
  逐帧原图、原生格、严格 4× 与联系表路径见 `cells.json` 同目录。
- **未验项**：720/1080 双向、实速、循环接续、声音、主游戏实机；无录屏。

## 2026-11-12 air_special/heavy/light3 落格与重映射

- air_special 8 帧 288×288、根点 [128,248]、腾空脚底 239、比例 0.169182；heavy 7 帧、light3 6 帧，256 格、接地脚底 247、同一比例。逐帧记录见 `stage1/cells/cells.json`。
- 落格实测：air 高 163–188、heavy 168–177、light3 168–187；32 色、二值 Alpha、单连通、四边留白、无裁切。
- 招式：heavy 4→7 sprite，保持 28 tick 与 18/4/6，命中 tick 18–21 落在新连续直拳帧（sprite 3），判定框/伤害不动；light3 4→6 sprite，保持 20 tick 与 13/3/4，命中 13–15 落在上勾拳最高帧（sprite 4）。重映射后逐 tick 修剪越出 active 窗口的重复判定，只保留声明的命中 tick。
- 安装 `--only heavy,light3` 与 `--only air_special` 两次合成，clip 数与 SHA 见 manifest。hurtboxes 按图集重算。
- 全量 `tools/verify.py` 57 项 PASS。root_delegated_by_user；无录屏，720/1080 双向实机未验。

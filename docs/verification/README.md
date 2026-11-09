# 验证回执

用途：核对随干净仓库交付的历史验证结论时读本文件。这里只放摘要，原始日志在本机 `reports/verification`。

本目录保留可以随干净仓库交接的结果摘要；原始测试输出在本机忽略的 `reports/verification`，重新运行会生成自己的输出，不上传整套日志和截图副本。

## 2026-11-08 图鉴重建与佐菲

- 图鉴统一 384×256、根点 [192,248]、3.84 px/m；人类固定 96（原 140）。609 条按官方剧照/皮套照图生图重画并安装，图鉴图共 1075 个文件变动（1009 改、66 新增），另新增 28 条待机动画条；宽体条目以 376 px 宽度上限取可行站高，不拉伸姿态。旧 `new_art_approved` 与 `approval_evidence` 全部重置，等待实机复核。
- 参考图补齐到 1686 张（本轮新增 633 张）并改为仓库相对路径；21 条低清官方源保留原图、标注 `resolution_exception`，不放大、不替代；删除 9 张被替换的重复副本。`catalogue_references` 从 180 条错误降为 0 错误。
- 名称拆分为 title/主体名/form，17 条重复形态写入 `aliases` 并由 `canonical_id()` 归并；`selection.json` 全部 ID 可解析。
- 佐菲按圆谷官方页（45 米 / 45,000 吨 / 队长）与官方皮套剧照重做图鉴，站高 173 安装并同步 display；此前误装的 154 px 窄侧视已替换。战斗 154 与 M87 开掌关键帧只测量，未安装。2026-11-09 用户反馈 11-08 版体型仍不合格，改以圆谷官方全身皮套照 `art/fighters/zoffy/sources/ref-02.png`（2400×3607，官方直链）为第一参考重做，11 轮候选后选中 `ref02k`：站高 173、宽 43、32 色、二值 Alpha、蓝计时器保留，SHA `3865589d...`，已安装并同步 display；旧 173 保留对照。未做双朝向 720/1080 实机审片，无录屏。
- 体力经济改为发力招硬门槛后，`tests/capture_mechanism.gd` 的体力不足用例改为每 tick 固定空体并断言 `move_denied`（reason=stamina）、无启动、无扣能。

| 检查 | 结果 |
| --- | --- |
| `tools/verify.py --keep-going` 全量 | 54 项全部通过（含 capture_mechanism 及其独立进程回放） |
| `catalogue_assets` / `catalogue_animation` / `catalogue_identity_display` | 通过（佐菲安装后复跑） |
| `catalogue-references` / `catalogue-idle` / `catalogue_facing` | 通过；参考图 1686 张、21 条低清提示；待机真帧 28/1653 |

未做 720/1080 双朝向实机审片，无录屏；图鉴画面只做逐张静审与 contact sheet，不等于美术验收。

## 2026-11-08 动画帧尺度突变修复

- 新增 `tools/check/frame_scale_jumps.py`：以头骨顶到脚底站高、头宽和头部面积对同 clip 中位数比较（±8%；头宽与头面积同时偏大且站高也偏大才判确定突变），举起的武器和细特效在测量前用 3×3 开运算剔除；蹲姿、腾空收腿只影响站高，不按头部指标误判。
- 修复 8 名角色 11 个 clip 共 28 帧整帧放大：杰克 `burst`1、`crouch_light2`2、`motion_214`3（长矛投掷）、`special`6、`special2`7、`special3`3；哥莫拉 `heavy`2、`guard_counter`1；亚刻 `air_tech`1；布莱泽 `guardbreak`1；布莱克王 `vertical_light`1。以该帧脚底 anchor 为不动点做最近邻反向采样，Alpha 保持 0/255；逐帧像素核对只有目标帧变化、帧外 0 像素改动，manifest 只更新 `atlas_sha256`。
- 修复后复扫，被修帧全部转为 `ok`；导入与 `phase3_standing`、`phase3_air`、`pixel_pages` 通过。证据 JSON 在本机忽略的 `reports/frame-scale-jumps/`。
- 仍有 103 clip / 111 帧判确定突变、606 clip / 1124 帧待人工复核，多为击飞、翻滚、倒地、抓投、腾空和出场姿势；`gomora/guard_counter#5` 修完 #0 后转为待复核。未做双朝向 720/1080 实机检查，无录屏。

## 2026-11-08 文档合并与冗余清理

- `docs/` 由 11 份合并为 9 份：`ENGINE_CHOICE` 并入 `PROJECT_LAYOUT`；`AUDIO_API` + `MONSTER_MUSIC` 合并为 `AUDIO`；`FORMS` + `SUPER_MOVE_DIVERSITY` 合并为 `COMBAT_DESIGN`。`docs/README.md` 仍是唯一索引。
- 根目录只保留 `AGENTS.md`、`README.md`、`REBUILD_2D_PLAN.md` 三份 Markdown。
- 同步更新 `REBUILD_2D_PLAN.md`、`docs/PROGRESS.md`、`content/roster/selection.json`、`content/audio/battle_music.json` 中的文档路径；`REBUILD_2D_PLAN.md` 的输入表按现行规则改为 I 远程/方向技能，不再保留独立 H 技能键。
- 删除本机过期报告：`reports/music-research`（与旧 `docs/MONSTER_MUSIC.md` 字节相同，内容已并入 `docs/AUDIO.md`）、`reports/gdscript-warnings`（一次性警告清理回执，代码状态已生效）、`reports/windows-removal`（一次性平台迁移回执，改动已落地）、`reports/catalogue-pipeline-pilot`（旧图鉴试点，安装图 SHA 不同且现行流程改走 `reports/catalogue-ref`）、`reports/repository-cleanup` 与 `reports/cleanup-inventory.json`（2026-11-03 原始清理审计，摘要保留在本目录 `repository-cleanup.json`）；均确认无仓库内消费者。
- 删除 `tools/**/__pycache__` 25 个目录、`reports/godot-warnings` 空目录，以及 `tools/`、`reports/review` 下的空目录；删除无源文件的孤立 `generated-images/` 导入侧车。
- `tools/` 下一次性脚本经路径/模块名与生产回执核对后未删：日期批次仍被 `art/fighters/*` 回执或在制 README 引用，零导入的顶层脚本是人工入口。重复模块名（`audit.py`、`prepare.py`、`main_bundle.py` 等）违反 tools/README 的全局唯一约定，留待批次合并时处理。
- `content/fighters/**` 中指向旧 `docs/FORMS.md`、`docs/SUPER_MOVE_DIVERSITY.md` 的字符串已统一改为 `docs/COMBAT_DESIGN.md`，涉及 20 个文件；这些字段不被运行代码读取。
- `docs/verification/existing-skill-assets-audit.json` 是带 SHA 的历史快照，保留当时的旧路径，不回写。

## 2026-11-07 文档与结构清理

- 删除 91 个 `__pycache__` 目录（35.4 MB，未入库）。
- 删除 10 份 `content/fighters/*/PROGRESS.md`（66 条指向已清理报告的失效链接），未完成项收敛到 [PROGRESS](../PROGRESS.md)。
- `docs/` 由 11 份合并为 9 份：`ARCHITECTURE` 并入 `PROJECT_LAYOUT`，`MOVE_DATA` + `MELEE_HIT_GROUPS` 合并为 `DATA_FORMATS`，`WEAPON_COVERAGE` 并入 `ART_PIPELINE`；新增 [文档索引](../README.md)。
- 修正 6 处指向已删除 `docs/handover/` 的死链；删除自述"不代表上传成功"的过期检查点说明。
- 未改动 `art/source-index.json`、冻结来源收据、`content/fighters/*/MOVES.md`、`third_party/`。

验证环境：Godot `4.7.2.stable.official.ed1daf0bf`（Homebrew）、Python 3.13 venv、Pillow 13.0.0、NumPy 2.5.4、git-lfs 3.8.1，macOS arm64。

| 检查 | 结果 |
| --- | --- |
| 空缓存导入（`--editor --import --quit`） | exit 0 |
| `tools/maintenance/repository_audit.py` | passed，34610 文件 / 4.02 GB / 0 错误 |
| `tools/verify.py --keep-going` 全量 | 45 项全部通过 |

补充（同日）：`checkpoint/full-20261105-0020` 已 fast-forward 合入 `main`，261 个新增 LFS 对象逐一核对 SHA/大小并本地拉取完整，`git lfs fsck` 通过；两个远端 checkpoint 分支已删除。

补充（2026-11-07 修复）：`training_input_audit` 与 `training_lifecycle` 曾在进程退出时报 AudioStream/Playback 泄漏。根因是 headless 下帧循环极快，AudioServer 线程来不及按真实时间回收已停止的 playback。已在两处修复：`game_app.shutdown()` 先停播、断开流引用并清空两级音频缓存；两个测试退出前 `OS.delay_msec(120)` 让出真实时间。修复后各连跑 12 次与 4 次均无泄漏，`tools/verify.py` 已恢复严格判据（任何 `SCRIPT ERROR` 或 `ERROR` 都判失败）。

清理前基线（同一环境）：导入 exit 0、`logic_2d` PASS、`repository_audit` passed（33293 文件）。

首次全量回归出现 2 项失败（`fx-audio-resources`、`pixel-ui-resources`），原因是本机缺少 Pillow/numpy，与清理无关；建立 `.venv` 安装 `tools/requirements-checks.txt` 后两项单独重跑均 exit 0。

## 2026-11-03 清理回执

- [repository-cleanup.json](repository-cleanup.json)：清理范围、初始盘点、去重和最终全量源 SHA 审计。清理前记录的 4710 个运行二进制内容均可在原位置或 119 个合并目标中找到相同 SHA；没有重新编码或替换画帧/音频。
- [cleanup-regression.json](cleanup-regression.json)：空缓存导入、当前全部默认回归及定点补跑结果。
- [runtime-catalog.json](runtime-catalog.json)：清理时实际 definition 与三槽招式快照。列为可玩不代表全动作美术、声音和独立技能规范全部达标；后续改数据时须同步重导。
- [remote-lfs.json](remote-lfs.json)：首次 push 后用已认证 gh 接口逐项检查全部唯一 LFS 对象的远端下载可用性和大小。

## 边界

没有进行全部人物双向 720/1080 逐动作审片、人耳听审或硬件键盘逐键测试，没有生成录屏。上述结果只说明资源、逻辑、回放及启动/退出验证结果，不表示游戏范围完成。接手步骤和已知余项见 [PROGRESS](../PROGRESS.md)。

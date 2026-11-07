# 验证回执

本目录保留可以随干净仓库交接的结果摘要；原始测试输出在本机忽略的 `reports/verification`，重新运行会生成自己的输出，不上传整套日志和截图副本。

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

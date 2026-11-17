# 七角色返工诊断脚本（2026-11-12）

用途：继续七角色整帧返工、复算阶段 A/B 诊断或修改在制分镜时读本文件。这里只放本批唯一的复算脚本；规则以根 `AGENTS.md` 为准，当前状态以 [HANDBOOK](../../../docs/HANDBOOK.md) 的“当前状态与验证边界”为准。

| 脚本 | 职责 | 输出 |
| --- | --- | --- |
| `diagnostic_probe.py` | 复算奥王、佐菲、奥父、奥母的身份卡、资产基线与逐 clip 诊断 | 四个角色的 `art/fighters/<id>/stage1/rework-20261112/` |
| `write_reports.py` | 由上述四角色的只读 JSON 生成 `diagnosis.md`、`storyboard.md` | 同上 |
| `ufeneo_rework_diag_v1.py` | 复算赛罗、杰斯提斯、盖亚的逐帧测量与数据交叉核 | 三个角色的 `measurement_evidence.json` |
| `ufeneo_rework_finalize_v1.py` | 把三角色测量结果收口为身份卡、诊断、分镜和资产基线 | 三个角色的 `stage1/rework-20261112/` |

这些脚本是 2026-11-12 在制批次的冻结证据生成器，不是新任务的执行器，也不接入 `verify.py`。运行时一律用项目 `.venv/bin/python`，所有 Godot 操作仍经 `tools/godot_lock.py`。脚本用统一路径引导从 `project.godot` 推仓库根，不依赖脚本所在目录深度或本机绝对路径。

冻结任务书在 [SEVEN_CHARACTER_REWORK_BRIEF.md](../shared/SEVEN_CHARACTER_REWORK_BRIEF.md)；它的 SHA 被 14 份 wiring 回执绑定，本批结案前不得改字或移动。逐帧硬门在 `tools/check/seven_character_rework_hard_gate.py`，本目录不重复实现。

本批复算只写上述在制数据，不生成图片、不安装资源、不改 `core/` 语义、不改运行时；无录屏、未听审、未用户亲审。

# 奥特曼格斗进化Neo

用途：了解项目、获取运行方式或查找唯一文档入口时先读本文件。固定侧视的 2D 像素格斗游戏，使用 Godot 4.7；当前提供电脑对战、本地双人、训练、角色/场景选择和对局回放，全名册、装甲、武器与本人声音仍在制作中。

## 获取与运行

需要 Git、**Git LFS**、Godot 4.7 和 Python 3.12+。仓库内图片、声音和字体使用 LFS，克隆后必须补齐，否则拿到的是指针文本而不是图片。

```bash
git lfs install
git lfs pull
git lfs fsck --objects --pointers
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/requirements-checks.txt
export GODOT_PATH=/Applications/Godot.app/Contents/MacOS/Godot
.venv/bin/python tools/godot_lock.py -- "$GODOT_PATH" --headless --path . --editor --import --quit
```

macOS 用 `.venv/bin/python`、`export GODOT_PATH=...` 和 `开始游戏.command`。首次克隆不带 `.godot` 缓存，必须先导入。启动器依次使用 `UFENEO_PYTHON`、项目 `.venv`、PATH 中的 `python3`；本机已有的 Codex Godot 配置也可读取，不需要上传该配置。

启动 **开始游戏.command** → 电脑对战/本地双人/训练 → 选人 → 场景与 BGM → 开始。

1P：W/空格跳，S 蹲，AD 移动，J/K/L/O 攻击，U 防御，I 远程（I+方向直出原搓招），P 必杀，Q 蓄能，E 切已开放形态，N 闪避。2P 使用方向键与小键盘。正式设置可重绑和保存。Enter 暂停，F1 判定框，F2 招式表，F3 训练，F4 回放，F5 陪练，R 再战。

## 开发与验证

```bash
.venv/bin/python tools/maintenance/repository_audit.py
.venv/bin/python tools/godot_lock.py -- .venv/bin/python tools/verify.py --keep-going
```

验证输出在 `reports/verification`，测试使用隔离的用户数据目录。导入完成后可用 `tools/verify.py --skip-import --only logic_2d` 跑单项；仍须经 Godot 锁调用。工具按职责分组，顶层只留 `verify.py` 与 `godot_lock.py`。源图制作是可选工具链，运行游戏不需要 API 密钥或图像生成服务。逻辑检查通过不等于美术或听感通过。

## 唯一文档入口

| 文件 | 内容 | 何时读 |
| --- | --- | --- |
| [AGENTS.md](AGENTS.md) | 唯一执行准则、当前任务与不可回退规则 | 每轮开工前 |
| [REBUILD_2D_PLAN.md](REBUILD_2D_PLAN.md) | 游戏设计目标、完整招式矩阵（尤其 2.5 节）、阶段顺序 | 设计或规划招式时 |
| 本文件 | 项目总览、获取与运行、验证命令、文档入口 | 了解或启动项目时 |
| [docs/HANDBOOK.md](docs/HANDBOOK.md) | 当前状态与验证边界、目录架构、数据格式、美术流程、战斗设计、stage1 标准、音频、第三方 | 查现行主题规范、可玩范围或未完项时 |
| [docs/verification/README.md](docs/verification/README.md) | 可随仓库交付的验证结果摘要与根因事故记录 | 核对历史验证结论时 |
| [docs/verification/](docs/verification/) | 冻结历史回执，按原文件名和章节锚点保留 | 追查当时证据时 |
| [tools/README.md](tools/README.md) | 工具目录归属、依赖、路径引导 | 增加、移动或运行工具时 |
| [art/STYLE.md](art/STYLE.md) | 像素风格、尺寸校验、远侧肢体、待机与走路 | 绘制或验收像素帧时 |
| [tools/rebuild/seven-character-rework-20261112/README.md](tools/rebuild/seven-character-rework-20261112/README.md) | 七角色返工当前在制批次的复算脚本 | 续作七角色动作时 |

`REBUILD_2D_PLAN.md` 不移动、不改名，2.5 节章节编号及锚点保持不变；冻结回执中的旧路径文字一律不改写。当前状态不在设计文件重复维护，主题规范不按日期追加第二份副本。单角色在制材料留在 `art/fighters/<id>/stageN/` 或 `tools/rebuild/<批次>/`；历史回执只保留在 `docs/verification/` 或本机 `reports/`。

2026-11-03 按用户要求清理旧历史后建立新的 Git 基线，不包含旧工作树、缓存、录像或备份。现用运行素材与有效源稿保留；冻结来源中的旧路径通过 `art/source-index.json` 定位唯一文件。

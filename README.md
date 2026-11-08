# 奥特曼格斗进化Neo

固定侧视的 2D 像素格斗游戏，使用 Godot 4.7。当前提供电脑对战、本地双人、训练、角色/场景选择和对局回放；全名册、装甲、武器与本人声音仍在制作中。

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

1P：W/空格跳，S 蹲，AD 移动，J/K/L/O 攻击，U 防御，I 远程，P 必杀，Q 蓄能，H 方向快捷技能，E 切已开放形态，N 闪避。2P 使用方向键与小键盘。正式设置可重绑和保存。Enter 暂停，F1 判定框，F2 招式表，F3 训练，F4 回放，F5 陪练，R 再战。

## 开发与验证

```bash
python3 tools/maintenance/repository_audit.py
python3 tools/godot_lock.py -- python3 tools/verify.py --keep-going
```

工具目录按职责分组（`check`、`art`、`audio`、`roster`、`media`、`runtime`、`maintenance`、`rebuild`），顶层只留 `verify.py` 与 `godot_lock.py`；分工见 [tools/README.md](tools/README.md)。

验证输出在 `reports/verification`，测试使用隔离的用户数据目录。导入完成后可用 `tools/verify.py --skip-import --only logic_2d` 跑单项；仍须通过 Godot 锁调用。源图制作是可选工具链，运行游戏不需要 API 密钥或图像生成服务。

## 阅读入口

完整文档索引见 [docs/README.md](docs/README.md)。

| 文件 | 用途 |
| --- | --- |
| [AGENTS.md](AGENTS.md) | 唯一执行准则 |
| [REBUILD_2D_PLAN.md](REBUILD_2D_PLAN.md) | 设计目标、完整招式矩阵、阶段顺序 |
| [docs/PROGRESS.md](docs/PROGRESS.md) | 环境、验证入口、可玩范围、未完项与接续优先级 |
| [docs/PROJECT_LAYOUT.md](docs/PROJECT_LAYOUT.md) | 目录归属、分层、数据流、热点模块 |

2026-11-03 按用户要求清理旧历史后建立新的 Git 基线，不包含旧工作树、缓存、录像或备份。现用运行素材、有效源稿和当前未完成动作保留；冻结来源中的旧路径通过 `art/source-index.json` 定位唯一文件。

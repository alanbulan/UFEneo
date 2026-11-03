# 奥特曼格斗进化Neo

固定侧视的2D像素格斗游戏，使用Godot 4.7。当前提供电脑对战、本地双人、训练、角色/场景选择和对局回放；全名册、装甲、武器与本人声音仍在制作中。

## 获取与运行

需要Git、Git LFS、Godot 4.7和Python 3.12+。仓库内图片、声音和字体使用LFS，克隆后确认执行：

```powershell
git lfs install
git lfs pull
$env:GODOT_PATH = '你的Godot可执行文件绝对路径'
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r tools/requirements-checks.txt
.venv\Scripts\python.exe tools/godot_lock.py -- $env:GODOT_PATH --headless --path . --editor --import --quit
.\开始游戏.cmd
```

首次克隆先按上面步骤导入资源，再从同一终端启动 **开始游戏.cmd** → 选择电脑对战/本地双人/训练 → 选人 → 场景与BGM → 开始。已将Godot加入PATH或持久设置GODOT_PATH后可直接双击。启动器依次使用UFENEO_PYTHON、项目.venv或PATH中的Python；本机已有Codex Godot配置也可读取，不需要上传该配置。

1P：W/空格跳，S蹲，AD移动，J/K/L/O攻击，U防御，I远程，P必杀，Q蓄能，H方向快捷技能，E切已开放形态，N闪避。2P使用方向键与小键盘。正式设置可重绑和保存。Enter暂停，F1判定框，F2招式表，F3训练，F4回放，F5陪练，R再战。

## 开发与验证

```powershell
.venv\Scripts\python.exe tools/maintenance/repository_audit.py
.venv\Scripts\python.exe tools/godot_lock.py -- .venv\Scripts\python.exe tools/verify.py --keep-going
```

验证输出在reports/verification，测试使用隔离的用户数据目录。import完成后可用`tools/verify.py --skip-import --only logic_2d`运行单项回归；仍须通过Godot锁调用。源图制作是可选工具链，运行游戏不需要API密钥或图像生成服务。

| 阅读入口 | 用途 |
| --- | --- |
| [AGENTS.md](AGENTS.md) | 唯一执行准则 |
| [设计与招式矩阵](REBUILD_2D_PLAN.md) | 范围、输入和阶段 |
| [目录规范](docs/PROJECT_LAYOUT.md) | 文件归属 |
| [当前状态](docs/PROGRESS.md) | 本次进度 |
| [交接文档](docs/HANDOFF.md) | 最后提交写明的接手步骤、未完工作和验证边界 |
| [美术入口](docs/ART_PIPELINE.md) | 当前源库与制作接口 |
| [第三方说明](docs/THIRD_PARTY.md) | 上游版本、来源、许可 |

2026-11-03按用户要求清理旧历史后建立新的Git基线，不包含旧工作树、缓存、录像或备份。现用运行素材、有效源稿和当前未完成动作保留；冻结来源中的旧路径通过art/source-index.json定位唯一文件。

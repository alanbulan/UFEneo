# 奥特曼格斗进化Neo

用途：了解项目、获取运行方式、目录结构或查找四核心文档入口时先读本文件。固定侧视的 2D 像素格斗游戏，使用 Godot 4.7；当前提供电脑对战、本地双人、训练、角色/场景选择和对局回放，全名册、装甲、武器与本人声音仍在制作中。

## 获取与运行

需要 Git、Godot 4.7 和 Python 3.12+。GitHub 仓库仅托管源码、配置、JSON 数据、`.uid`/`.import` 文本侧车与文档（停用 Git LFS）；运行时图片/音频/字体（`assets/`）与制作源稿（`art/`）保存在本机磁盘并由 `.gitignore` 忽略。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/requirements-checks.txt
export GODOT_PATH=/Applications/Godot.app/Contents/MacOS/Godot
.venv/bin/python tools/godot_lock.py -- "$GODOT_PATH" --headless --path . --editor --import --quit
```

macOS 用 `.venv/bin/python`、`export GODOT_PATH=...` 和 `开始游戏.command`。首次克隆不带 `.godot` 缓存，必须先导入。启动器依次使用 `UFENEO_PYTHON`、项目 `.venv`、PATH 中的 `python3`；本机已有的环境配置不随仓库上传。

启动 **开始游戏.command** → 电脑对战/本地双人/训练 → 选人 → 场景与 BGM → 开始。

1P：W/空格跳，S 蹲，AD 移动，J/K/L/O 攻击，U 防御，I 远程（I+方向直出原搓招），P 必杀，Q 蓄能，E 切已开放形态，N 闪避。O 点按是超重击，按住 O 蓄力后再松开按档出招。2P 使用方向键与小键盘，超重击是小键盘 0。正式设置可重绑和保存。Enter 暂停，F1 判定框，F2 招式表，F3 训练，F4 回放，F5 陪练，R 再战。

## 目录结构

| 目录 | 职责 |
| --- | --- |
| `core/` | 纯整数 60 tick 确定性模拟、强类型角色组件、状态机与判定（零外部层依赖） |
| `content/` | 规则参数、状态映射、角色定义/招式/状态帧/形态与音频台账 |
| `input/` | 设备输入映射、电脑 AI 与 `UfeInputFrame` 构造（仅依赖 `core`） |
| `presentation/` | 只读表现层：侧视动画、相机取景、PixelFX 特效与声音播放 |
| `ui/` | 主菜单、HUD 安全区与像素套件界面 |
| `app/` | 主游戏装配与运行入口（`app/scenes/main.tscn`、`UfeAppHarness` 挂载接口） |
| `assets/` | 已安装运行时图集、音频、字体、场景资源（不入库，留本机） |
| `art/` | 制作源稿、身份锚、落格帧（仅跟踪 `art/.gdignore`，其余由 `.gitignore` 忽略） |
| `docs/` | 唯一技术与制作手册（仅 `docs/HANDBOOK.md`） |
| `tools/` | 顶层入口仅 `verify.py` 与 `godot_lock.py`；子包 `art`/`audio`/`check`/`maintenance`/`media`/`roster`/`runtime` |
| `tests/` | 核心回归、输入夹具与 `tests/review/` 审片挂载（含通用 `candidate_harness.gd`） |
| `third_party/`、`addons/` | 上游第三方源码许可声明与编辑器/输入图标插件 |

## 开发与验证

```bash
.venv/bin/python tools/maintenance/repository_audit.py
.venv/bin/python tools/check/layering.py
.venv/bin/python tools/godot_lock.py -- .venv/bin/python tools/check/gdscript_warnings.py
.venv/bin/python tools/godot_lock.py -- .venv/bin/python tools/verify.py --keep-going
```

验证输出在 `reports/verification`，测试使用隔离的用户数据目录。导入完成后可用 `tools/verify.py --skip-import --only logic_2d` 跑单项；所有 Godot 进程调用仍须经 `tools/godot_lock.py` 串行。源图/视频与音频制作是可选离线工具链（额外依赖见 `tools/requirements-art.txt`），运行游戏不需要 API 密钥或图像/音频生成服务。逻辑检查通过不等于美术或听感通过。

## 四核心文档索引

全仓现行规范收敛为以下四份核心文档，外加角色目录局部卡 `content/fighters/<id>/{MOVES.md,SOUNDS.md}`：

| 文件 | 内容 | 何时读 |
| --- | --- | --- |
| [README.md](README.md) | 项目总览、获取与运行、目录结构、验证命令、四核心索引（本文件） | 了解或启动项目时 |
| [AGENTS.md](AGENTS.md) | 唯一执行准则、手感基线、美术硬门与不可回退战斗规则 | 每轮开工前 |
| [REBUILD_2D_PLAN.md](REBUILD_2D_PLAN.md) | 游戏设计规格、完整招式矩阵（2.5 节）与工程阶段顺序 | 设计或规划招式时 |
| [docs/HANDBOOK.md](docs/HANDBOOK.md) | 六层 DAG 架构、仓库卫生硬门、数据契约、图/视频双模美术与音频流水线、工具链速查与第三方许可 | 查阅工程实现、数据格式、制作管线与工具命令时 |

`REBUILD_2D_PLAN.md` 不移动、不改名，2.5 节章节编号及锚点保持不变；纯源码 Git 基线停用 Git LFS，仅托管源码、配置、JSON 数据、Godot `.uid`/`.import` 侧车与规范文档。

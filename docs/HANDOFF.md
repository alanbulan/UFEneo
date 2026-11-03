# UFEneo 干净基线交接

交接日期：2026-11-03。本文专门随本轮最后一笔提交交付，接手人先按本文建立可运行环境，再按用户新指令开展工作。

## 1. 任务边界与发布位置

用户已停止原开发推进，本轮只负责清理、验证、上传GitHub和交接。不要自动恢复旧Goal、生图、图鉴、批量worker或装甲生产。历史收据中的“继续active Goal”“待用户验收”等文字只记录当时状态；现行执行准则是根目录[AGENTS.md](../AGENTS.md)。

- 私有仓库：https://github.com/alanbulan/UFEneo 。远端已用GitHub API核实为private。
- 分支：`main`。交付标记：`clean-baseline-2026-11-03`。
- 第一笔清理/代码/素材基线：`f2709a7a7f3b73461062dcf00e81ff1c222d4e64`，提交信息“清理冗余素材与旧历史，建立可运行的GitHub基线”。
- 发布状态：清理基线与全部LFS对象已经上传，并经已认证gh接口逐项核对远端下载可用性与大小。最终交付以`main`和上述tag指向的本文交接提交为准；不推送旧refs。
- 原Git历史、旧refs和三个目录整理worktree已直接删除，没有制作备份或历史镜像。旧来源记录内的提交SHA是历史标识，不能在这个新仓库中checkout。

## 2. 接手人首先要做什么

1. 阅读根AGENTS、根REBUILD_2D_PLAN、[PROGRESS](PROGRESS.md)及本文，查看`git log -5`。先确认用户下一项工作，再开始开发。
2. 获取全部LFS实体并导入Godot资源，确认主菜单、选人和对局可进入；不要把LFS指针文本当损坏PNG重新生成。
3. 运行当前验证入口，记录自己的引擎版本和输出。只有逻辑通过不能宣称外观、动作连续性或声音已经验收。
4. 若用户继续在制工作，优先按第6节接续已有月亮装甲和哥莫拉受方材料，先处理和配准已有源，不重复收费获取同一批图。

本机工程路径是`F:/Games/Godot/Project/UFEneo`；其它机器不需要复制这个绝对路径或本机Codex环境。

## 3. 新机器获取与启动

需要Git、Git LFS、已获私有仓库访问权限的GitHub账号、Godot 4.7及Python 3.12+。本轮实测Godot `4.7.2.stable.steam.ed1daf0bf`、Python `3.12.10`、Pillow `12.3.0`、NumPy `2.5.2`。

在PowerShell中执行；把Godot路径替换成本机实际位置：

```powershell
gh auth status
gh auth setup-git
git lfs install
git -c core.longpaths=true clone https://github.com/alanbulan/UFEneo.git
Set-Location UFEneo
git config core.longpaths true
git lfs pull
git lfs fsck --objects --pointers
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r tools/requirements-checks.txt
$env:GODOT_PATH = 'C:\你的Godot目录\Godot.exe'
.venv\Scripts\python.exe tools/godot_lock.py -- $env:GODOT_PATH --headless --path . --editor --import --quit
.\开始游戏.cmd
```

首次克隆不带`.godot`缓存，必须先完成导入。上面的GODOT_PATH只作用于当前终端；从同一终端启动，或将Godot加入PATH/持久设置环境变量后再双击启动器。启动器依次使用UFENEO_PYTHON、项目`.venv`、PATH中的Python；Godot依次读取GODOT_PATH、PATH，最后兼容本机Codex配置。运行游戏不需要生成接口密钥。

本机制作Python为`C:/Users/13080/.codex/venvs/ufeneo/Scripts/python.exe`，本机Godot为`F:/Games/Steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe`。这些程序未放进仓库。

正式路径：开始游戏.cmd → 对战电脑/本地双人/训练 → 选人 → 场景与BGM → 对局。1P为W/空格跳、S蹲、AD移动、J/K/L/O攻击、U防御、I远程、P必杀、Q蓄能、H方向快捷、E形态、N闪避；2P方向键与小键盘。正式设置可重绑。Enter暂停，F1判定框，F2招式表，F3训练，F4回放，F5陪练，R再战。

Godot导入、测试及录制都经`tools/godot_lock.py`。锁在`art/shared/locks/godot.lock`；不要删活锁或关闭用户进程。

## 4. 清理结果与文件归属

清理前旧art约36.25 GB、reports约40.12 GB、离线audio约17.50 GB、旧.git约65.33 GB。它们是当时逻辑文件规模，不是精确磁盘释放量。清理后有效上传树约3.97 GB，其中保留的唯一制作源约3.53 GB；Git LFS对象和本机重建缓存另计。

已直接清理旧候选/下载池/录屏与AVI、无用离线音频池、本机环境副本、私人测试存档、废弃脚本和重复规范。三个旧目录工作树`UFEneo_layout_baseline_2026-10-24`、`UFEneo_layout_dryrun_2026-10-24`、`UFEneo_layout_phase2_dryrun_2026-10-24`已删除。其它独立项目不在本次清理范围。

运行资源合并了119个完全相同副本，并同步引用。清理前记录的4710个运行二进制内容，在最终位置或合并目标上均匹配原SHA，没有重编码音频或重画帧。泰罗斯特利姆叫招的来源台账改指已有同SHA正式WAV；两只EX的重复锁定占位格已合并到正式直选身份。

| 归属 | 接手方式 |
| --- | --- |
| `app/` | 正式主游戏装配与入口`app/scenes/main.tscn` |
| `core/`、`input/` | 整数60 tick模拟与输入，不放美术制作/审片逻辑 |
| `presentation/`、`ui/` | 只读画面/声音/镜头与正式界面组件 |
| `content/` | 当前定义、招式、状态、名册和注册表，是实现状态的依据 |
| `assets/` | 当前运行素材、清单、来源与许可 |
| `art/fighters/<id>/model/` | 当前定稿和测量；重复实体可能映射到assets |
| `art/fighters/<id>/sources/` | 现装采用源的唯一实体，SHA文件名；用途由原收据与索引关联 |
| `art/fighters/<id>/stage<N>/` | 有效在制源、候选、测点和交接收据 |
| `tests/review/` | 供主游戏调用的审片驱动，已从运行数据/输入目录移出 |
| `tools/` | 当前通用工具、必要制作依赖和在制处理器；稳定入口保留 |
| `docs/verification/` | 本轮可随仓库交付的清理、回归及实际名册摘要 |
| `reports/` | 本机运行结果，除README/.gdignore外不上传 |

详细归属见[PROJECT_LAYOUT](PROJECT_LAYOUT.md)。PNG/JPG/WebP/WAV/OGG/MP3/ORA/字体走LFS；`.uid`、`.import`提交，`.godot`、环境、录像、凭据不提交。art/tools/reports含`.gdignore`，不进入Godot资源导入。

冻结源收据不改字节。旧路径用`art/source-index.json`解析，不能因路径现在不存在就恢复旧目录副本。例如：

```powershell
.venv\Scripts\python.exe tools/maintenance/source_lookup.py art/fighters/ultraman-arc/model/clean-model-source.png
```

制作脚本通过`tools/maintenance/layout_runtime.py`读取同一索引。未列入索引的废弃材料已删除；旧URL、SHA和剪辑参数不代表原混音/下载池仍在，也不保证旧生产过程能离线原样重跑。部分历史模块因当前处理器仍导入其函数而保留；不要直接重跑它们的install/apply/restore入口覆盖现装方案。

本轮自动审批拦截了删除`reports/repository-cleanup/`内临时JSON、`reports/cleanup-inventory.json`和Python缓存的命令，缩小为明确文件清单后仍被拦截，未给具体原因。这些少量本机工作文件保留且被忽略，不是备份、不在上传内容内。当前验证日志/输入证据及重建的Godot缓存也只保留本机。

## 5. 本轮验证结果及边界

当前默认回归及必要补跑均通过。覆盖空缓存导入、确定性和原输入回放、输入解析、投技/抓点/捕获、形态和KO、弹体边界、阶段动作、声音/FX资源、页面/身份显示、AI及正式主游戏启动/退出。图形主菜单截图已检查；自动注入S×5和J触发退出，外层进程返回0；重复退出回归通过。Git LFS本地对象与指针检查通过。

GitHub首次push只抽样验证了LFS对象，因此另外通过已认证gh的LFS batch接口逐项查询全部唯一OID，远端下载动作和大小全部匹配；见[远端LFS回执](verification/remote-lfs.json)。这次查询没有重新下载整份素材，也没有关闭TLS验证。早先独立Python查询因本机证书信任失败，不是远端缺文件；最终回执来自成功的gh查询。

结果见[验证说明](verification/README.md)、[回归回执](verification/cleanup-regression.json)及[清理回执](verification/repository-cleanup.json)。摘要按实际初跑和补跑合并，每项记录运行批次；本机详细日志不随仓库上传。

```powershell
.venv\Scripts\python.exe tools/maintenance/repository_audit.py
.venv\Scripts\python.exe tools/godot_lock.py -- .venv\Scripts\python.exe tools/verify.py --keep-going
```

已导入时可追加`--skip-import --only logic_2d`运行定点项目。测试用户数据隔离在reports/verification中，避免覆盖玩家设置/回放。

清理时修正了陈旧断言：KO/超时保持具体形态；标题按现行整幅群像检查；EX直选合法；声音检查允许现用双声道原剧整句。删除只依赖废弃历史文件的比对入口，保留现用机制、逐tick回放、指纹变化与资源校验。本轮没有为通过旧测试回退游戏规则。

本轮没有重新验收全部人物双向720/1080画面，没有人耳听审，没有物理键盘逐键亲测，没有新录屏。测试通过不代表全角色、全招式、全装甲或全部声音完成。历史`user_approved`不回改；后续根按用户委托自验收时记录`root_delegated_by_user`。

## 6. 若用户继续开发，优先接续这里

### 月亮装甲轻击三连

位置：`art/fighters/ultraman-arc__luna/stage2/`；收据入口是该目录`handoff/light-chain/README.md`与`root-source-production-review.json`。原retained12及新增五个缺相/替换完整源已保留，完整三连未正式接入。跳跃17相曾做主游戏RAM候选验收，也不等于装甲已经完整可玩。

下一步先统一159/1024整图尺度、Forge RGB兼容调色及Alpha128，核本人支撑/骨盆/拳足测点；补齐三连起手、首次接触、随势、收膝和落脚连续性，再做完整注册、实体判定、真实输入与独立回放，最后进正式main双向720/1080。处理入口在`tools/rebuild/ultraman-arc/luna-s2-light-chain*`和`luna-jump-resume*`。不得将本体人物贴甲、切肢或循环旧帧冒充新动作。

### 哥莫拉三级背掀与初代受方

本人18相、杰顿候选以及初代六张完整源/统一179候选仍保留。初代候选和测点位于`art/fighters/ultraman/stage5/gomora-back-lift-receiver/candidate-179/`、`measurements/`；原完整源在同级`gomora-super3-back-lift-receiver-20261102-v1/`。相关工具位于`tools/rebuild/gomora/super3_back_lift_contract_20261102_v1/`和`ultraman_receiver_root_override_candidate_20261102_v1/`。

先核初代实际腹腰与哥莫拉背部的root/grip/hurtbox逐相配对，不能抄杰顿坐标。再核空中接住、拆投、落空、离背和落地伤害，按当前正式代码建立新的前后回归。旧临时安装包/历史回滚路径不是本次可直接执行的安装依据。

**普通主游戏的哥莫拉三级仍是全力超振动波。背掀没有作为普通版本正式安装。**

### 其它未完成范围

- 八套装甲：亚刻太阳/月亮/银河、布莱泽法德兰、欧米伽雷基尼斯/特莱加隆/瓦尔基涅斯/加美顿的独立S2–S7动作、技能/武器、声音、变身和正式对局仍未整体完成，不打开未齐装甲可玩/变身。银河的有效在制源也保留。
- 全名册独立三槽仍有缺口。[runtime-catalog.json](verification/runtime-catalog.json)记录实际现装招名/费用；初代、内隆嘎、布莱克王、杰顿等仍可见同束分级，部分其它人物仍有重复或需要依据复核，不能写成已经全员整改。保留已装玩法，按用户重新授权的范围逐项处理。
- 泰罗保持一级泰罗切割、二级斯特利姆、三级奥特爆炸。欧米伽二级已是八段头镖；三级当前数据名为“欧米伽连斩终结”，含两段实体接触及`omega_special3_beam`光线。它与用户“三级保留光线”的表述应按实际表现进一步核对，本轮未改机制或冒称纯光线版本。
- 全原剧武器、本人声音及环境严格美术覆盖尚未全部完成。当前十九场场景/BGM选择已存在，不等于每场多层动画/材质已完成严格验收。
- 亚刻/提欧等本人声音仍有缺口。亚刻登场已装的是合体前卢提昂完整对白，不能冒称战斗战吼；数字拟音/转换不能称原剧原声。`listening_reviewed=false`仍须实际听审。
- 图鉴新增暂停。四新英雄本体及两EX现装能力以运行数据为准，不因旧制作收据的阶段字段重新做完一遍；完整动作的尺寸、手侧、接续和受方余项按实际画面记录。

## 7. 不得被旧工具覆盖的现行规则

Q只负责真实蓄能起势/保持/收势；所有技能禁止周身蓄气圈。独立爆气使用自己的冲击，局部发射点、实际弹束、刃路/命中和真实技能火焰按用途保留。布莱克王Q收在头躯干四肢周围，可排除尾巴。

镜头必须包含双方完整人物、长尾、武器和倒地/击飞，必要时缩放。2P能量格顺序和单格填充共同从右向左。EX直选与本体变身共存，形态保留至KO/结算，新局重建。E形态、H八方向快捷、N闪避及正式重绑设置保持。

所有人物是完整像素帧，禁止切肢拼片。PixelFX只作为已授权FX例外，MIT版本固定`a84159688af3ca37a4be05a0d422b94451b2e24e`，离线烘焙透明PNG；不引入人物骨架或运行时JS。详细制作规则见[ART_PIPELINE](ART_PIPELINE.md)，来源/许可见[THIRD_PARTY](THIRD_PARTY.md)。

## 8. 费用、凭据与下一次交付

本轮没有收费生成。2026-11-02最后已记账占额为53.384310/60美元，含未知请求`011ff77710ed49c9b441ed80f91733be`的10美元，未知不释放、不重发。新单预占1美元；40.94美元是用户当时提供的余额，没有API核实，也不是现在余额。用户明确恢复制作后，先读本机最新费用台账再决定可用额度，保留20美元余量目标，不以本文旧数字恢复预算。

生成只走项目`tools/art_pipeline.py`的generate_image和本机配置；密钥只在`~/.codex/secrets`，不复制、不打印、不入库。当前通用检查依赖可由requirements安装；Forge、FFmpeg、Kits等是按需制作工具，不能因缺少它们阻止用户运行游戏。

下一位接手者完成一个明确任务后，更新唯一PROGRESS及必要的对应规范，按明确路径做中文提交。最后一笔再更新本文的真实状态、验证证据、未完任务与接续步骤。只在确需看运行时录短临时视频，审后直接删除；录制器已取消AVI自动归档。不要再创建备份目录或把旧审片、旧素材和本机环境上传。

# 图鉴重建并行生图任务书

用途：给 2026-11-13 起每个图鉴生图子代理读。执行准则仍是 `AGENTS.md`；图鉴静帧与动作帧的参考规则见 `docs/HANDBOOK.md` 第 592–616 行；统一收据脚本与产物位置见本目录 `README.md`。本任务书不是第二套规则。

## 任务边界

- 只处理指定批次 `reports/catalogue-rebuild-20261113/batch<NN>-refs.txt` 列出的 20 个 ID；各 ID 的 `art/catalogue-rebuild-20261113/<id>/source.json` 已写本人唯一本地参考路径。
- 唯一合格风格基准是最初 `existing_runtime`：`reports/catalogue-rebuild-20261113/baseline-existing-runtime.png`、`baseline-dynamic-frames.png`。不要拿后来做的 8 个或别角色模板当基准。
- 先 `Read` 本文件、`README.md`、`docs/HANDBOOK.md` 第 592–616 行、对应批次 `batch<NN>-refs.png` 与 `batch<NN>-refs.txt`，再逐 ID `Read` 本人 `source.json`、本地参考图和 `reports/catalogue-rebuild-20261113/identity/<id>-native-x4.png`。

## 来源门（不能按旧错误口径一律拒收）

- 图鉴照片→像素**允许并鼓励**本人多张不同角度参考；不能用“正面/3/4 角度”单独判来源门拒收。
- 静帧 `still-00.png` 最多用 3 张参考：本人本地参考图、本人当前已装整图的 4× 最近邻放大（必要时水平镜像到右侧视）、1 张最初 existing_runtime 同风格成品仅借画风与头身比。提示词必须写死固定右侧视、格斗待机、完整全身、像素整帧、真透明背景；不要让正面/3/4 参考把整身视角拉回正面。
- 本地参考用于本人标志结构、配色与造型细节；现有 4× 整图用于真实侧视轮廓、头肩比例、四肢体量和朝向。标志结构前后朝向按官方来源定死，不从正面猜。实物只借造型，去掉球关节、轴、插接缝和塑料高光。
- 只有本地参考与现有 4× 整图都无法读本人结构（多人合影、演员肖像、文字页/玩具包装、错身份、局部裁到无法补全身）才来源门拒收。植物、四足、球体、机械等本人形态按实际结构生成，不套双足怪兽、双拳或披风模板。

## 生图

- 来源通过的 ID 每条目生成 3 张：`still-00.png`、`idle-01.png`、`idle-02.png`。
- 一切生图只经 MCP `mcp__magpie-image__generate_image`；工具未加载先 `ToolSearch` 加载 `mcp__magpie-image__generate_image` 与 `mcp__magpie-image__generation_result`。固定使用 Magpie 当前生图模型 `cpa/gpt-image-2.6-sunburst`（若工具枚举未刷新可留空 `model` 以跟随 Magpie 设置）、`quality=high`、`background=transparent`、`size=1536x1024`。
- `reference_images` 与输出 `path` 一律本仓库绝对路径，输出在 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/catalogue-rebuild-20261113/<id>/`。若返回生成 ID，用 `generation_result` 等真正落盘。核实收路径、尺寸、Alpha、SHA；请求尺寸不得冒充实收尺寸。
- `idle-01.png` 与 `idle-02.png` 各自只引用本 ID 的 `still-00-clean.png` 一张身份锚，不追加角度参考、不追加风格样本。
- 禁止 `generate_video`、旧 worker、旧 Goal、旧批量安装器、`tools/art/pipeline.py` 网络层；不读取、打印、复制或提交凭据；不生成音效；不搜新参考、不下载、不改 `source.json`。

## 提示词与动作

- 逐角色简体中文提示词约 150–250 字，只写该帧动作和本人确有的结构，显式要求四肢粗细与参考一致；角色没有的部件不得写进提示词。
- 固定尾串交代右侧视、完整全身不裁切、真透明背景、无地面/文字/边框/光束/光晕/颗粒/蓄气圈/能量球/飞行物。
- 静帧为两脚前后错步、屈膝下沉、双拳胸前护架；四足/植物/机械等按本人结构写等价的真实重心与护架姿态。
- 两待机帧分别有重心、头颈、双拳、肩背、腿脚或本人尾/背甲/枝叶的真实可见位移，不得复制、平移、局部变色或加特效凑帧。
- 同一帧同一问题最多 2 次重生成；连续拒收 3 个不同帧暂停该项并写诊断，不无限重生成。

## 清洁与收据

- 原始软 Alpha 保留为三张原始 PNG。用 `.venv/bin/python` + Pillow/numpy 另存对应 `*-clean.png`：Alpha `>=128` 置 255、其余置 0，按实体 bbox 裁切，保留 RGBA；离线硬化不得冒称原生二值 Alpha。
- 用 `Read` 实看三张原图与三张 clean 图；核本人标志结构、头肩比例、手脚体量、完整不裁切和三帧真实位移。数值通过不能写成造型通过。
- 把三份提示词、生成 ID/usage、实看结论分别写 `reports/catalogue-rebuild-20261113/receipts/<id>-prompts.json`、`*-generation-ids.json`、`*-visual-review.txt`。
- 正常完成对每个 ID 运行：
  `.venv/bin/python tools/rebuild/catalogue-rebuild-20261113/catalogue_rebuild_finalize.py <id> --prompts reports/catalogue-rebuild-20261113/receipts/<id>-prompts.json --generation-ids reports/catalogue-rebuild-20261113/receipts/<id>-generation-ids.json --visual-review reports/catalogue-rebuild-20261113/receipts/<id>-visual-review.txt --status accepted`
  明确不合格时改 `--status rejected --notes "<具体原因>"`。
- 来源门仍拒收时写 `{}`、`[]`、实看问题，并在上面命令加 `--source-gate-only --status rejected --notes "来源门拒收"`。
- `catalogue_rebuild_finalize.py` 核实际路径、尺寸、Alpha、bbox、SHA 与统一辉光门：`alpha>=200` 最大连通块外扩 3 px 后主体外 `alpha>=16 <=100 px`、`alpha>=200=0`，`alpha 1–15` 尘点只登记不计入；脚本不能代替本人造型实看。`fits_catalogue_cell` 只报告折算宽度，不判死；横卧长尾/宽背/背鳍由根会话统一缩入固定 384×256 格，不裁轮廓、不逐帧重标定。

## 写入边界

只写本批 20 个 ID 各自的 `art/catalogue-rebuild-20261113/<id>/` 与 `reports/catalogue-rebuild-20261113/receipts/<id>*`。不得写 `content/`、`assets/`、共享 README/任务书/脚本、其它候选目录；不得运行 `catalogue_install.py`、Godot 导入、git 操作或全量验证。完成后用简短中文列每 ID 状态、实际生图张数、辉光门结果、仍拒收原因，不粘贴大段图片或 JSON。

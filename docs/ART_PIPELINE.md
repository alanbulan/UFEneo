# 美术制作入口与武器规范

用途：制作或核对人物整帧、图鉴静态形象与武器资源时读本文件。这里定义流程、存储位置和记录格式；当前完成度以 [PROGRESS](PROGRESS.md) 和运行数据为准。

2026-11-09 起恢复逐角色动作生产。先读根 [AGENTS](../AGENTS.md) 的整帧、预算和验收规则；像素风格细则见 [art/STYLE.md](../art/STYLE.md)，动作帧的参考图与提示词口径也在那里。

## 制作流程

1. 定位本人当前 `model` 和具体动作；旧路径先查 `art/source-index.json`，不能因路径变化重发生图。
2. **生图**：经 MCP 生图服务（`magpie-image`）出整帧高分候选。不再通过脚本直连图像 API；
   `tools/art/pipeline.py` 里的网络层只为历史收据保留，新任务不使用。
3. 图像返回后实际检查身份、Alpha、完整四肢/武器、身体连续与大小。完整源只保留一份，当前拒收原因写在动作 metadata 中，不复制整个工程作为历史。
4. **像素化后处理**：整图处理经 `tools/rebuild/shared/forge_backend.py`（需外部 sprite-gen 技能）。
   图鉴静态形象用自带的 `tools/media/art/catalogue_native.py`：软 Alpha 生成图 → 二值 Alpha、
   32 色硬色阶、384×256 画布、脚底对齐 248。它不依赖外部技能。旧颜色兼容 `palette_mode('rgb')`，
   同一动作统一尺度和根点；禁止拼肢或以静止图加 FX 代替动作。
5. PixelFX 脚本在 `tools/rebuild/<id>`，上游固定代码和 MIT 许可在 `third_party/pixelfx`；只离线导出透明整帧。人物不使用库骨架。
6. 运行资源安装到 `assets`，招式/事件到 `content`。主游戏两个朝向、720/1080、实际输入和独立原 InputFrame 回放分开核验；逻辑检查不替代画面或听感。

### 图鉴静态形象

图鉴（`ui/archive_panel.gd`）读取 `content/roster/catalogue_display.json` 的 `entries[id].image`，
缺图时显示"像素形象整理中"，不伪造候选。

一张图鉴图从生成到可见，五步（2026-11-09 用户确认的流程）：

```bash
# 1. 真实造型底图（MCP 生图，1024×1536，透明背景）：按官方皮套照生成真实照片质感的
#    整帧人物，严格右侧视、错步战斗架势，头身比按已实机角色复核（头高约占站高 0.20）
# 2. 像素整帧（MCP 生图）：以第 1 步照片为底图，让图片模型转成像素整帧；只按需微调
#    个别部位（例如头顶尖角），不重新设计造型
# 3. 转原生格式
.venv/bin/python tools/media/art/catalogue_native.py <raw.png> assets/fighters/<id>/catalogue/model-native.png
# 4. 写 display 条目（catalogue_id / image / image_sha256 / native_canvas / native_root）
# 5. 校验
.venv/bin/python tools/godot_lock.py -- godot --headless --path . --script res://tests/catalogue_identity_display.gd
```

第 1、2 步都必须由图片模型完成；不要用程序化滤镜、调色或重采样冒充“像素化”，
程序只负责第 3 步的确定性降采样与量化。**图鉴**参考图尽量多给几张、给不同角度：
本人官方皮套照、本人既有来源图，再加 1–2 张已实机安装的同风格成品作画风与头身比
基准（只借画风与比例，不抄造型）。色调以本人官方参考图为准，饱和度明显高于参考图
（红/主体色 `sat - refsat > 40`）判为不合格。这条“多给几张”只用于图鉴照片→像素，
动作帧相反，见下面的动作帧小节。

`catalogue_native.py` 先输出站高 192，再由 `tools/media/art/catalogue_rescale.py`
按 `content/roster/catalogue_scale.json` 落到设定身高（45m 档 173、人类固定 96 等）。
最终校验用重设后的站高，不把中间值 192 当成成品要求。输出必须满足
`binary_alpha: true`、`visible_colors <= 32`、`canvas: [384, 256]`、
`native_root: [192, 248]`。不满足就不要接线。

### 动作帧

1. **定架势**：以 `art/fighters/<id>/sources/ref-01.webp`（官方皮套照）为主参考，
   可加 1 张已装机同风格成品只借站姿与画风。要格斗待机架势，不是并脚站立：
   两脚分开、脚外缘间距约为站高的 0.65–0.80（已装机 10 个角色实测中位 0.71）、
   前后脚屈膝下沉、双拳抬到胸前护架。审过才往下走。
2. **待机像素整帧**：以第 1 步为底图转像素整帧，此帧即该角色的动作身份锚。
   `tools/art/identity_anchor.py <id>` 出的 4× 定稿锚只保证配色与像素块大小；
   原生宽度 <60 px 时模型读不出肩宽和四肢粗细、会自编身材，不得单独作动作参考。
3. **生图**：MCP `magpie-image`，`codex/gpt-image-2`、quality high、background transparent。
   只引用第 2 步那一张待机像素帧，提示词只写该帧动作（约 150–250 字）加固定尾串。
4. **落格**：`tools/art/stage_cells.py` 统一比例缩放、二值 Alpha、32 色、脚底贴
   `baseline-1`、脚底段重心对到 anchor x。硬门只判连通块、Alpha、色数。
5. **比例由人核**：看联系表判头身比、四肢粗细、站高，`cells.json` 的 `notes` 只是
   提示，不冒充自动通过。

动作帧请求与淘汰记录写在 `art/fighters/<id>/stage1/requests.json`。

现用源库存储：`model` 保留当前人可读入口；`stage` 目录保留正在接续的动作；已装来源去重后在 `sources` 目录，SHA 文件名对应 `art/source-index.json`。冻结 JSON 仍可包含当时原路径；不要为了美化路径改写原始请求与 usage。

需要重新制作的未完成动作见 [PROGRESS](PROGRESS.md)。旧大规模生成 worker、历史审片安装器与废弃批次已经清理，不能把运行代码中的历史来源字符串当成它们仍然存在。

## 武器覆盖与记录格式

范围是所有已装英雄、怪兽、宇宙人及其具体形态在原剧中使用过的武器。这里定义工作标准，不重复维护完成度；当前实际状态以 [PROGRESS](PROGRESS.md) 和运行数据为准。

每条武器登记：本人/形态 ID、规范名称与别名、作品/版本/集数/时间点、来源 URL 及文件 SHA、完整轮廓与持手、召唤/握持/收纳、原剧攻击方式、本作输入/动作 ID/费用/取消窗口、人物/脱手物/FX/声音、双向命中/防御/落空与原输入回放、剩余问题。

人物与手持武器一起生成完整像素帧。脱手物使用本人专属资源和实际判定；不贴通用武器、不换色充数，不以图鉴装备图或静止人物加 FX 冒充完成。原剧动作和本作连招编排须分开注明，不虚构官方招名。

已有原剧依据的武器招缺触发位置时，用户已允许替换凑数的指令/派生技；记录旧招到新招、输入、费用和判定变化，基础移动/常用拳脚保持。执行前须等用户新的开发指令。

八套装甲分别核对本人武器与形态归属。赛文头镖、杰克手镯变形、亚刻之眼剑、布莱泽持剑、欧米伽头镖及装甲、提欧具体版本武器等均不能互借整帧。名称或集数未知时留待核，不把"尚未核实"写成"没有武器"。

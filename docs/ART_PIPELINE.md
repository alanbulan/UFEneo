# 美术制作入口与武器规范

本轮只有清理和交接，不恢复生产。收到用户新的开发指令后，先读根 [AGENTS](../AGENTS.md) 的整帧、预算和验收规则。像素风格细则见 [art/STYLE.md](../art/STYLE.md)。

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

一张图鉴图从生成到可见，四步：

```bash
# 1. 出图（MCP，1024 方图，透明背景）
# 2. 转原生格式
.venv/bin/python tools/media/art/catalogue_native.py <raw.png> assets/fighters/<id>/catalogue/model-native.png
# 3. 写 display 条目（catalogue_id / image / image_sha256 / native_canvas / native_root）
# 4. 校验
.venv/bin/python tools/godot_lock.py -- godot --headless --path . --script res://tests/catalogue_identity_display.gd
```

`catalogue_native.py` 的输出必须满足：`binary_alpha: true`、`visible_height: 192`、
`visible_colors <= 32`、`canvas: [384, 256]`、`native_root: [192, 248]`。
不满足就不要接线。

现用源库存储：`model` 保留当前人可读入口；`stage` 目录保留正在接续的动作；已装来源去重后在 `sources` 目录，SHA 文件名对应 `art/source-index.json`。冻结 JSON 仍可包含当时原路径；不要为了美化路径改写原始请求与 usage。

需要重新制作的未完成动作见 [PROGRESS](PROGRESS.md)。旧大规模生成 worker、历史审片安装器与废弃批次已经清理，不能把运行代码中的历史来源字符串当成它们仍然存在。

## 武器覆盖与记录格式

范围是所有已装英雄、怪兽、宇宙人及其具体形态在原剧中使用过的武器。这里定义工作标准，不重复维护完成度；当前实际状态以 [PROGRESS](PROGRESS.md) 和运行数据为准。

每条武器登记：本人/形态 ID、规范名称与别名、作品/版本/集数/时间点、来源 URL 及文件 SHA、完整轮廓与持手、召唤/握持/收纳、原剧攻击方式、本作输入/动作 ID/费用/取消窗口、人物/脱手物/FX/声音、双向命中/防御/落空与原输入回放、剩余问题。

人物与手持武器一起生成完整像素帧。脱手物使用本人专属资源和实际判定；不贴通用武器、不换色充数，不以图鉴装备图或静止人物加 FX 冒充完成。原剧动作和本作连招编排须分开注明，不虚构官方招名。

已有原剧依据的武器招缺触发位置时，用户已允许替换凑数的指令/派生技；记录旧招到新招、输入、费用和判定变化，基础移动/常用拳脚保持。执行前须等用户新的开发指令。

八套装甲分别核对本人武器与形态归属。赛文头镖、杰克手镯变形、亚刻之眼剑、布莱泽持剑、欧米伽头镖及装甲、提欧具体版本武器等均不能互借整帧。名称或集数未知时留待核，不把"尚未核实"写成"没有武器"。

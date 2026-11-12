# vertical_jump 扩产 raw 帧生成记录（2026-11-11）

范围：赛罗 stage1 普通动作/循环帧扩产；只写本 clip 目录，未落格、未安装、未改 assets/content、未运行 Godot、未提交。

## 身份与生成口径

- 唯一参考：`art/fighters/ultraman-zero/stage1/idle/frames/pixel-raw-02-official-side-anchor.png`（1024×1536，右侧视像素整帧），SHA256 `5f4651673a90f08056a250fea9a6f68ad339501a615658a183a7d07d3791dec3`；每帧只传这一张参考。
- 生图服务：MCP `magpie-image`，模型 `codex/gpt-image-2`，quality high，size 按帧记录，`background=transparent`，每次 1 张。
- 每帧提示词＝固定段＋下表“动作相位”＋固定尾串；未追加其它角色、角度或特效参考。
- 提示词固定段：参考图是唯一身份与画风来源；同一赛罗、右侧视；后掠鳍状银冠+额侧左右弯刃双头镖；四肢粗细与参考一致（手臂粗壮、大腿饱满、小腿有厚度）；固定尾串“右侧视，完整人物不裁切，透明背景，无地面、文字、边框；整帧只有人物，无任何光效、特效、光晕、粒子”。
- 2026-11-11 规则更正：动作帧与特效分开，新增帧一律无光效/光晕/粒子；旧帧自带 FX 不改。

## 新增帧

| 帧 | 动作相位 | 生成 ID | 实收尺寸 | 字节 | SHA256 | 主体高px | 辉光门 |
|---|---|---|---|---:|---|---:|---|
| `add-00.png` | 最高点：身体伸展、双膝微收、脚尖下绷、双拳护架 | image-3954-254 | 1024×1536 | 1141295 | `2ba9989ff906883889cec5cd8c890f8ff68fd382f84cfdc97de08e8d4f97f7f4` | 1205 | out16=5, out200=0, dust=13997 |

## 重掷历史

无重掷。

## 最终有序帧序列

`takeoff/frames/takeoff-00-raw.png` → `air_rise/frames/air_rise-00-raw.png` → `add-00.png` → `air_fall/frames/air_fall-00-raw.png` → `land/frames/land-01-raw.png`

## 门值与备注

- vertical_jump 无独立 raw 源目录；既有 4 相连同动画由 takeoff-00 / air_rise-00 / air_fall-00 / land-01 组成（assets/fighters/ultraman-zero/animations/vertical_jump/atlas.png 4 格实测）。
- 本轮新增最高点 add-00，h=1205 腾空例外；未改 assets 的 atlas。
- FX 复核：新增帧无光束、光球、蓄气圈、贴掌光或独立粒子；主体外 alpha≥16 组件均为 ≤50 px 边缘反光/尘点（light3 add-01 为两枚脱手实体头镖）。低 alpha 尘点轮廓与身份锚一致，按辉光门口径只登记。
- 每帧均核过实收路径/尺寸/字节、RGBA 真透明、主体外 alpha≥16 ≤100 px 且 alpha≥200=0；alpha 1–15 尘点只登记不计入。
- 未落格、未装机、未改 assets/、未改 content/、未运行 Godot、未提交 git、未删现有文件。


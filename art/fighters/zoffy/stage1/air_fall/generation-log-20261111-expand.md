# 佐菲 air_fall 帧补齐（2026-11-11）

- 身份锚（每帧唯一参考）：`art/fighters/zoffy/stage1/idle/frames/raw-01-v4.png`
- 参考 SHA256：`7461dafee882728eca0f194ddcf0b72eb9ffd39ef916a7234e2ba814b3937e0e`
- 生图：MCP magpie-image，模型 `codex/gpt-image-2`，quality high，background transparent，请求 1024×1536；实收尺寸逐张见下表。
- 每帧提示词固定含「整帧只有人物，无任何光效、特效、光晕、粒子」；站姿帧另写“总高度与参考图完全一致”，动作/腾空帧只写完整人物不裁切。
- 辉光门：主体＝alpha≥200 最大连通块，外扩 3 px；主体外 alpha≥16 ≤100 px、主体外 alpha≥200＝0；alpha 1–15 尘点只登记。
- 本文件对应 raw 帧：未落格、未装机、未改 assets/ 与 content/、未提交 git；无录屏。
- 体型基准：raw 待机锚 `art/fighters/zoffy/stage1/idle/frames/raw-01-v4.png`，body_h=1528（alpha≥200 bbox），8% 带 1406–1650；相邻站姿帧高度变化门 10%。

## 本轮新帧（全部 1024×1536 RGBA）

| 帧 | 生成 ID | 实收 | body_h（对锚偏差） | 辉光 outside16/200 | SHA256 | 提示词要点 |
|---|---|---|---|---|---|---|
| `add-00-clean` | image-3954-496 | 1024×1536 | 1391（−9.0%） | 0 / 0 | `bd21cbef5b4b46ee9ab1664d3e000acd9ad308c92c364cccb217b1340d6175e7` | 下落第二帧：身体继续下坠，双膝向前收，双臂抬起准备落地缓冲，手位上移，脚尖向下 |

## 重掷与标废

- 首帧一次通过，无重掷。

## 最终有序帧序列

1. `raw-00`（既有，h1442）
2. `add-00-clean`（本轮，h1391，腾空）

## 备注

- 腾空收膝，body_h 1391（对锚 −9.0%）属腾空例外；与前一帧相比双膝收得更高、双臂抬起，手位明显上移。
- 低 Alpha 尘点 21,677 px，只登记。

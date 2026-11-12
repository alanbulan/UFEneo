# 奥王 air_rise 帧补齐（2026-11-11）

- 身份锚（每帧唯一参考）：`art/fighters/ultraman-king/stage1/cells/idle-candidate-v18-x4.png`
- 参考 SHA256：`e8c3965c66b5bdf16bfc0a4a585a1cefbae7f496c101970d29a4ede0b8f61c3f`
- 生图：MCP magpie-image，模型 `codex/gpt-image-2`，quality high，background transparent，请求 1024×1536；实收尺寸逐张见下表。
- 每帧提示词固定含「整帧只有人物，无任何光效、特效、光晕、粒子」；站姿帧另写“总高度与参考图完全一致”，动作/腾空帧只写完整人物不裁切。
- 辉光门：主体＝alpha≥200 最大连通块，外扩 3 px；主体外 alpha≥16 ≤100 px、主体外 alpha≥200＝0；alpha 1–15 尘点只登记。
- 本文件对应 raw 帧：未落格、未装机、未改 assets/ 与 content/、未提交 git；无录屏。
- 体型基准：raw 待机锚 `art/fighters/ultraman-king/stage1/idle/frames/pixel-raw-01-v18.png`，body_h=1411（alpha≥200 bbox），8% 带 1298–1524；相邻站姿帧高度变化门 10%。

## 本轮新帧（全部 1024×1536 RGBA）

| 帧 | 生成 ID | 实收 | body_h（对锚偏差） | 辉光 outside16/200 | SHA256 | 提示词要点 |
|---|---|---|---|---|---|---|
| `add-00-clean` | image-3954-325 | 1024×1536 | 1432（+1.5%） | 0 / 0 | `5839997b9f53deb6bdd1e43562b56b71e6cf9586f8266384d969168910b7b11e` | 上升第二帧：身体继续向上伸展，双膝由胸前收拢改为向下伸，双拳仍护胸 |

## 重掷与标废

- 首帧一次通过，无重掷。

## 最终有序帧序列

1. `air_rise-00-raw-01`（既有，h1223）
2. `add-00-clean`（本轮，h1432）

## 备注

- 腾空伸腿姿势，body_h 较前一帧 +17.1%，属腾空伸展例外，登记数值。
- 低 Alpha 尘点 23,665 px，只登记。

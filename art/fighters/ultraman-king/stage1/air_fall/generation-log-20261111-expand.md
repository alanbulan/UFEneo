# 奥王 air_fall 帧补齐（2026-11-11）

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
| `add-00-clean` | image-3954-319 | 1024×1536 | 1140（−19.2%） | 17 / 0 | `e31a153649ea3a1f7cde277e9af6991000837f3a509c84414e80b6bc2fddbcea` | 下落第二帧：身体继续下坠，双膝向前收，双臂从两侧抬起，手位较前一帧上移，披风上翻 |

## 重掷与标废

- 首帧一次通过，无重掷。

## 最终有序帧序列

1. `air_fall-00-raw-01`（既有，h1363）
2. `add-00-clean`（本轮，h1140，腾空）

## 备注

- 腾空收腿姿势，body_h 1140 属腾空例外，登记数值；与前一帧手位/膝位均有可见位移。
- 低 Alpha 尘点 57,479 px，只登记。

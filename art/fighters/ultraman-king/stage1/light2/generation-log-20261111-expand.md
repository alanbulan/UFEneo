# 奥王 light2 帧补齐（2026-11-11）

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
| `add-00-clean` | image-3954-299 | 1024×1536 | 1317（−6.7%） | 0 / 0 | `e4ec4c41cbebcd19308c28ff9436153ec98767f3006f49f02fa7b38f074b809a` | 前踢启动：支撑腿微屈，右膝向前伸开一半、脚掌绷平，双拳护胸 |
| `add-01-clean` | image-3954-303 | 1024×1536 | 1371（−2.8%） | 0 / 0 | `e3e93bf5c872ab243835c6cc4224b7e5c9545dd2d9f0b6fc72a1fd9441b58adb` | 前踢收腿：小腿收回折叠成提膝、脚掌下压准备落地，支撑腿承重，膝位回收 |

## 重掷与标废

- 旧批 add 帧缺固定尾串、带晕影，新规后标废；clean 两帧一次通过，采用。

## 最终有序帧序列

1. `light2-00-raw-01`（既有，h1399）
2. `add-00-clean`（本轮，h1317）
3. `light2-01-raw-01`（既有，h1399）
4. `add-01-clean`（本轮，h1371）
5. `light2-02-raw-02`（既有，h1412）

## 备注

- 相邻站姿帧高度变化：−5.9%、+6.2%、−2.0%、+3.0%，均 <10%；新帧对锚偏差 −6.7%/−2.8%，在 8% 带内。
- 低 Alpha 尘点 32,417–34,213 px/帧，只登记。

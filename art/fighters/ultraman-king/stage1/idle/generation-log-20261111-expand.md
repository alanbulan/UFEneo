# 奥王 idle 帧补齐（2026-11-11）

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
| `add-00-clean` | image-3954-131 | 1024×1536 | 1317（−6.7%） | 9 / 0 | `ab5e2e74fbca8e3e3ae7e031d7c7fd284c70f0a43ea794739c9d3e8d86aad92e` | 吸气初段：胸口抬起、双肩下沉后展，双拳仍护胸，拳位较参考上移少许，站高不变 |
| `add-01-clean` | image-3954-142 | 1024×1536 | 1337（−5.2%） | 5 / 0 | `3fd815641bd40e9ee6627d533d5c8ab60fb6fb53c12aa50abe680e84cff17754` | 吸气顶点：胸腔打开、锁骨略升，护架双拳继续上提，前臂角度较前一帧可见变化 |
| `add-02-clean3` | image-3954-282 | 1024×1536 | 1349（−4.4%） | 7 / 0 | `087b8a29f47269a03f341ab52d68b0dc7007014978e4bdb969cdb73a9218ee6a` | 呼气回到参考站姿：双拳回护架基准位、肩背放松、脚位不变、站高不变 |

## 重掷与标废

- add-00.png：实收 1254×1254、body_h 1097（−22%），尺寸与站高门不过，标废。
- add-00-v2.png：1024×1536、h1512（+7.2%）数值过门，但带低 Alpha 光晕且无新规固定尾串，按规定标废。
- add-00-v3.png：h1373 数值过门，但冠形错误（冠刃朝前上、冠球在冠根），造型门不过，标废。
- add-00-clean.png：h1317，冠球在前额上方、冠刃向后掠复核通过，采用。
- add-01.png（旧批）：缺「整帧只有人物」固定尾串、带晕影，新规后标废；add-01-clean 重掷通过，采用。
- add-02-clean.png：h1280（−9.3%）不过 8% 带，标废；add-02-clean2.png h1277（−9.5%）仍不过，按返工刹车停止同思路重掷。
- add-02-clean3.png：改用“回到参考站姿”思路，h1349 过门，采用。


- 标废文件已删除。

### 已删除标废文件

| 文件 | SHA256 | 作废原因 |
|---|---|---|
| `add-00.png` | `89cb0bd4458f925e997461e0540f40be8a923ee489a0ebaa1275fa09976da88a` | 实收 1254×1254、body_h 1097（−22%），尺寸/站高门不过 |
| `add-00-v2.png` | `c5f8b1ab1bd22461d16f687af08ac5a13a7c7da09968485c372e975ddf319dbc` | h1512 数值过门但带低 Alpha 光晕，且缺新规固定尾串 |
| `add-00-v3.png` | `89c27636dc315dbb85305453e919bf571c16d3477dc190e6b0d9e2bbcca48c81` | h1373 但冠形错误（冠刃朝前上、冠球在冠根） |
| `add-01.png` | `eeb5db661b54923afb51192510ccca277f7e2098d06a11092f85224cc6232e5f` | 旧批，缺「整帧只有人物」固定尾串、带晕影 |
| `add-02.png` | `e8f50fff38da7f43fb5e1969c839b8b81337ca346ad24159722519b2c3b11e36` | 旧批，缺固定尾串、带晕影 |
| `add-02-clean.png` | `dc9882c740d4adc70428bf87a056a4357664953a26dafd317a09333db571b546` | body_h 1280（−9.3%）不过 8% 带 |
| `add-02-clean2.png` | `341348d0931c973e7a33a2072e66a33d4bc1c8b314072c44f07341414d28377b` | body_h 1277（−9.5%）仍不过 8% 带 |

- 保留的最终采用帧：`add-00-clean.png`、`add-01-clean.png`、`add-02-clean3.png`。

## 最终有序帧序列

1. `idle-01-raw-01`（既有装机帧）
2. `add-00-clean`（本轮）
3. `pixel-raw-01-v18`（既有 raw 身份基准帧）
4. `add-01-clean`（本轮）
5. `pixel-raw-03-v18`（既有候选帧）
6. `add-02-clean3`（本轮，循环回 idle-01-raw-01）

## 备注

- 本组新帧 body_h 1317–1349，均在同组既有帧 1409–1413 的 −4.4%～−6.7% 内，相邻变化 <10%，站高一致性通过。
- 低 Alpha 尘点 35,367–63,523 px/帧（alpha 1–15），按门只登记；落格时按阈值 16 清除。
- 旧尝试 add-00/‑v2/‑v3、add-01、add-02-clean、add-02-clean2 留在 frames/ 供追溯，不参与帧序。

# 奥王 walk_forward 帧补齐（2026-11-11）

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
| `add-00-clean2` | image-3954-193 | 1024×1536 | 1293（−8.4%） | 0 / 0 | `89ee433d44f57fb7fc982d9af7eae9c3d3a9fd81229d639f332bc831eb702d8e` | 走步第一中间帧：前腿抬膝前伸、脚掌将落地，后腿蹬直，双臂反向摆动 |
| `add-01-clean2` | image-3954-199 | 1024×1536 | 1326（−6.0%） | 1 / 0 | `bc4f86a117a7f23439bc5c2758606b5ba101df9459c4f2c7853a93f859938975` | 走步第二中间帧：前脚全掌落地、后脚跟抬起，髋部前送，支撑腿伸直保持站高 |
| `add-02-clean2` | image-3954-203 | 1024×1536 | 1294（−8.3%） | 0 / 0 | `65c301413d15185978092628c906dafa1b6471a74759d6b688b5105b1211d9ab` | 走步第三中间帧：后腿蹬地伸展、脚尖离地，重心升高，前腿支撑，双臂摆幅最大 |
| `add-03-clean2` | image-3954-207 | 1024×1536 | 1319（−6.5%） | 1 / 0 | `3f1050487bfb7e65ebf45531ea712aa0623516350393302b5f6d051d8379a75f` | 走步第四中间帧：后腿离地向前摆膝，前腿支撑，头顶保持参考站高，双臂摆回护架 |

## 重掷与标废

- 旧批 add-00/01/02/03.png：缺固定尾串、带晕影，新规后标废。
- clean 批（add-00…03-clean）：h1214/1236/1173/1280（−14%/−12%/−17%/−9%），整组低于 8% 带且尺寸跳变，整批标废。
- clean2 批：h1293/1326/1294/1319，采用。add-00（1293，−8.4%）与 add-02（1294，−8.3%）略超 8%，但同组既有 walk_forward-01-raw-01 为 1283（−9.1%），且相邻帧变化均 <10%，按组内一致性登记采用；同项已连续返工两轮，按刹车停止继续重掷。


- 标废文件已删除。

### 已删除标废文件

| 文件 | SHA256 | 作废原因 |
|---|---|---|
| `add-00.png` | `0f2c0ae4ae91a7161ff6d9b881c70654edd03cdd57e2937a2f95f7c9caa44e84` | 旧批，缺固定尾串、带晕影 |
| `add-00-clean.png` | `5e78fc4ef9f2e6c7ecf6087461c372bd3dda7708d55f9067cf62b6d126ee4f37` | clean 批 body_h 1214（−14%）不过门 |
| `add-01.png` | `533d2a53cad03fb0de9b6cb74b3ad7f09a6bd76bcf0037261f5111400fe5e26d` | 旧批，缺固定尾串、带晕影 |
| `add-01-clean.png` | `b524c4d0ab5e7d36a521607518f77c6b0d6248d883a1cc885894f3982a5710c5` | clean 批 body_h 1236（−12%）不过门 |
| `add-02.png` | `cfcb6635ff924055a7917ca0792499bfbd404cc9a05407898d8578b6297593c7` | 旧批，缺固定尾串、带晕影 |
| `add-02-clean.png` | `1afc543c15e3619f733842f1d72f52be6bb1167632b60ca232042021f8ef50c2` | clean 批 body_h 1173（−17%）不过门 |
| `add-03.png` | `e658401d0d0bd5647780d704b0d6c9a65642b5b2417eb1f4bd1c57c63938f45e` | 旧批，缺固定尾串、带晕影 |
| `add-03-clean.png` | `de5ebaef479d29abddb4129d10fd9d567ac9066ea8b8fe477463417e41be7c2e` | clean 批 body_h 1280（−9%）不过门 |

- 保留的最终采用帧：`add-00-clean2.png`、`add-01-clean2.png`、`add-02-clean2.png`、`add-03-clean2.png`。

## 最终有序帧序列

1. `walk_forward-00-raw-03`（既有，h1369）
2. `add-00-clean2`（本轮，h1293）
3. `walk_forward-01-raw-01`（既有，h1283）
4. `add-01-clean2`（本轮，h1326）
5. `walk_forward-02-raw-01`（既有，h1385）
6. `add-02-clean2`（本轮，h1294）
7. `walk_forward-03-raw-01`（既有，h1375）
8. `add-03-clean2`（本轮，h1319）

## 备注

- 整组相邻站姿帧高度变化：−5.6%、−0.8%、+3.4%、+4.5%、−6.6%、+6.3%、−4.1%，均 <10%。
- add-00/add-02 对锚偏差 −8.4%/−8.3%，属走步屈膝的姿态压低，不是逐帧缩放；验收按姿态例外登记，不计为体型门通过，落格后用统一 scale 并复测。
- 低 Alpha 尘点 32,645–91,546 px/帧，只登记。

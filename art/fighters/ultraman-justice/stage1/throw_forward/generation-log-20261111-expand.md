# 杰斯提斯 stage1 throw_forward 扩产记录（2026-11-11，raw 未落格）

本轮新增 **5 帧**（3→8）。只写 raw，不落格、不装机、不改 `assets/`、不改 `content/`、不运行 Godot、不提交 git。

身份参考：`art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-x4.png`（768×768，SHA `d13bcf04…`）；每帧只传这一张。生成：`magpie-image` / `codex/gpt-image-2`，quality high，background transparent，请求 1024×1536（实收尺寸见下表）。提示词 150–250 字，只写该帧动作，并写「四肢粗细与参考一致」+ 固定右侧视尾串；image-3954-151 起固定写「整帧只有人物，无任何光效、特效、光晕、粒子」，此前的帧用同义句「画面只有本人…不带任何光效」，收图后均按辉光门与目视复核无烘焙特效。

## 序列与插入位

1. `art/fighters/ultraman-justice/stage1/throw_forward/frames/throw_forward-00-raw.png`（既有）
2. `art/fighters/ultraman-justice/stage1/throw_forward/frames/add-00.png`（新增，前投相位）
3. `art/fighters/ultraman-justice/stage1/throw_forward/frames/add-01.png`（新增，前投相位）
4. `art/fighters/ultraman-justice/stage1/throw_forward/frames/add-02.png`（新增，前投相位）
5. `art/fighters/ultraman-justice/stage1/throw_forward/frames/throw_forward-01-raw.png`（既有）
6. `art/fighters/ultraman-justice/stage1/throw_forward/frames/add-03.png`（新增，前投相位）
7. `art/fighters/ultraman-justice/stage1/throw_forward/frames/add-04.png`（新增，前投相位）
8. `art/fighters/ultraman-justice/stage1/throw_forward/frames/throw_forward-02-raw.png`（既有）

## 新增帧门值

站高比＝主体 bbox 高÷图像高；锚同口径 0.8021（768×768，bbox 616）。站姿门 ±8%，同组相邻站姿突变 ≤10%。辉光门：主体＝α≥200 最大连通块外扩 3 px；外侧 α≥16 / α≥200 / α1–15 尘点，前两项须 ≤100 / =0，尘点只登记。全部帧 RGBA、α-min 0、四角 α=0、未触边。

| 序 | 文件 | 生成ID | 实收/字节 | SHA-256(前16) | Alpha | 辉光门 ≥16/≥200/尘点 | 站高比/对锚 | 动作相位与手/脚位置 | 例外 |
|---|---|---|---|---|---|---|---|---|---|
| 2 | `frames/add-00.png` | `image-3954-222` | 1254×1254 / 373,609 B | `9f306392fe780101…` | RGBA, α-min 0, 四角 0 | 18 / 0 / 14,467 | 0.7919 / -1.3% | 抓握回拉：双手由前伸改为抓握、十指扣紧，双臂屈肘把手拉到胸前偏前；双膝微屈、腰背收紧。 | — |
| 3 | `frames/add-01.png` | `image-3954-226` | 1254×1254 / 364,467 B | `2e16b7ec5bbb0e7f…` | RGBA, α-min 0, 四角 0 | 0 / 0 / 11,234 | 0.7911 / -1.4% | 屈膝上提：屈膝下沉、腰背发力，双臂抱紧把抓握点向上提到胸口高度；肘仍弯，头抬起。 | — |
| 4 | `frames/add-02.png` | `image-3954-232` | 1254×1254 / 406,845 B | `ef7eb72b4db5be47…` | RGBA, α-min 0, 四角 0 | 1 / 0 / 21,584 | 0.8198 / +2.2% | 举过头前段：双臂把抓握点举到额头高度、肘仍弯；腰背后仰、膝盖开始伸直，身体开始转向背侧。 | — |
| 6 | `frames/add-03.png` | `image-3954-264` | 1254×1254 / 424,590 B | `764b66cca79a5765…` | RGBA, α-min 0, 四角 0 | 19 / 0 / 19,046 | 0.7648 / -4.7% | 下挥到肩高：双臂从头顶向前下挥到肩高、肘微屈；上身前倾、腰向前拧转，身体转回右侧，重心移前脚。 | — |
| 7 | `frames/add-04.png` | `image-3954-246` | 1254×1254 / 385,345 B | `9db681b9e0513334…` | RGBA, α-min 0, 四角 0 | 4 / 0 / 14,397 | 0.7233 / -9.8% | 压腰松手：双臂继续压到腰前、手掌松开、指尖朝前下；上身前倾更深、前腿吃重，后脚脚跟离地。 | 掷出收势前压，站高比 -9.8%，动态例外。 |

## 被拒稿

| 文件 | 生成ID | 尺寸/字节 | SHA-256(前16) | 站高比 | 拒收原因 |
|---|---|---|---|---|---|
| `frames/add-03-rejected-01.png` | `image-3954-239` | 1254×1254 / 383,983 B | `7c46c82688eca376…` | 站高比 0.7249（-9.6%） | 读到收势蹲架、跳过下挥相位，站高比 0.725（-9.6%）；重掷为双臂在肩高、膝只微屈、身体转回右侧。 |

说明：以上被拒稿文件已按仓库无备份规则**文件已删除**；仅保留文件名、SHA 与拒收原因。

## 衔接检查

8帧前投：00前跨抓握→add-00回拉→add-01屈膝上提→add-02举至额前→01过顶→add-03下挥至肩高→add-04压腰松手→02前下方摔出。add-03首版读到收势蹲架、跳过下挥相位，已重掷。

站高衔接：播放序内相邻站高最大变化 9.4%（门限 10%）；站姿对锚偏差见上表。 相邻新帧与既有帧均有可见手/脚位移，未发现同姿势复制。

## 状态

raw 未落格、未装机；未改 assets/content；未运行 Godot；未提交 git；无录屏。

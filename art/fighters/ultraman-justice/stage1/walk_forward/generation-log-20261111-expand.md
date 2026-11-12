# 杰斯提斯 stage1 walk_forward 扩产记录（2026-11-11，raw 未落格）

本轮新增 **4 帧**（4→8）。只写 raw，不落格、不装机、不改 `assets/`、不改 `content/`、不运行 Godot、不提交 git。

身份参考：`art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-x4.png`（768×768，SHA `d13bcf04…`）；每帧只传这一张。生成：`magpie-image` / `codex/gpt-image-2`，quality high，background transparent，请求 1024×1536（实收尺寸见下表）。提示词 150–250 字，只写该帧动作，并写「四肢粗细与参考一致」+ 固定右侧视尾串；image-3954-151 起固定写「整帧只有人物，无任何光效、特效、光晕、粒子」，此前的帧用同义句「画面只有本人…不带任何光效」，收图后均按辉光门与目视复核无烘焙特效。

## 序列与插入位

1. `art/fighters/ultraman-justice/stage1/walk/frames/walk-forward-00-raw.png`（既有）
2. `art/fighters/ultraman-justice/stage1/walk_forward/frames/add-00.png`（新增，前行循环相位）
3. `art/fighters/ultraman-justice/stage1/walk/frames/walk-forward-01-raw-2.png`（既有）
4. `art/fighters/ultraman-justice/stage1/walk_forward/frames/add-01.png`（新增，前行循环相位）
5. `art/fighters/ultraman-justice/stage1/walk/frames/walk-forward-02-raw.png`（既有）
6. `art/fighters/ultraman-justice/stage1/walk_forward/frames/add-02.png`（新增，前行循环相位）
7. `art/fighters/ultraman-justice/stage1/walk/frames/walk-forward-03-raw.png`（既有）
8. `art/fighters/ultraman-justice/stage1/walk_forward/frames/add-03.png`（新增，前行循环相位）

## 新增帧门值

站高比＝主体 bbox 高÷图像高；锚同口径 0.8021（768×768，bbox 616）。站姿门 ±8%，同组相邻站姿突变 ≤10%。辉光门：主体＝α≥200 最大连通块外扩 3 px；外侧 α≥16 / α≥200 / α1–15 尘点，前两项须 ≤100 / =0，尘点只登记。全部帧 RGBA、α-min 0、四角 α=0、未触边。

| 序 | 文件 | 生成ID | 实收/字节 | SHA-256(前16) | Alpha | 辉光门 ≥16/≥200/尘点 | 站高比/对锚 | 动作相位与手/脚位置 | 例外 |
|---|---|---|---|---|---|---|---|---|---|
| 2 | `frames/add-00.png` | `image-3954-388` | 1254×1254 / 342,533 B | `e947c2b5c4d00d22…` | RGBA, α-min 0, 四角 0 | 0 / 0 / 13,179 | 0.7679 / -4.3% | 前行过渡：前脚全掌着地承重，后脚脚跟刚离地、屈膝准备前摆；护架随步伐轻摆，上身前倾。 | — |
| 4 | `frames/add-01.png` | `image-3954-393` | 1254×1254 / 373,802 B | `1d70bb3fdd5353ee…` | RGBA, α-min 0, 四角 0 | 0 / 0 / 15,272 | 0.7727 / -3.7% | 前行过渡：摆动腿前伸、脚跟将落地，后腿在后蹬直、脚跟抬起；重心在支撑腿，护架轻摆。 | — |
| 6 | `frames/add-02.png` | `image-3954-397` | 1254×1254 / 342,784 B | `6aa6a0d67027087e…` | RGBA, α-min 0, 四角 0 | 1 / 0 / 10,174 | 0.7807 / -2.7% | 反向过渡：换另一脚全掌承重，后脚脚跟刚离地、屈膝准备前摆；护架轻摆。 | — |
| 8 | `frames/add-03.png` | `image-3954-400` | 1254×1254 / 382,537 B | `568364a7455e7c5d…` | RGBA, α-min 0, 四角 0 | 4 / 0 / 16,298 | 0.7799 / -2.8% | 接循环：摆动腿前伸、脚跟将落地，后腿蹬直、脚跟抬起；动作接 walk-forward-00。 | — |

## 被拒稿

| 文件 | 生成ID | 尺寸/字节 | SHA-256(前16) | 站高比 | 拒收原因 |
|---|---|---|---|---|---|
| — | — | — | — | — | 本组无被拒稿 |

## 衔接检查

8帧循环：00接触→add-00承重/后跟离地→01后腿支撑、前腿收膝→add-01摆动腿前伸将落地→02反向接触→add-02承重/后跟离地→03后腿支撑→add-03摆动腿前伸将落地→回00。远侧红腿与近侧银板腿交替领先，无同腿连续领先。

站高衔接：播放序内相邻站高最大变化 4.0%（门限 10%）；站姿对锚偏差见上表。 循环首尾：add-03（接触前）→walk-forward-00（接触），同腿接续，非重复帧。

## 状态

raw 未落格、未装机；未改 assets/content；未运行 Godot；未提交 git；无录屏。

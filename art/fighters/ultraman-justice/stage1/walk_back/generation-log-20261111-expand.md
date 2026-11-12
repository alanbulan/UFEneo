# 杰斯提斯 stage1 walk_back 扩产记录（2026-11-11，raw 未落格）

本轮新增 **4 帧**（4→8）。只写 raw，不落格、不装机、不改 `assets/`、不改 `content/`、不运行 Godot、不提交 git。

身份参考：`art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-x4.png`（768×768，SHA `d13bcf04…`）；每帧只传这一张。生成：`magpie-image` / `codex/gpt-image-2`，quality high，background transparent，请求 1024×1536（实收尺寸见下表）。提示词 150–250 字，只写该帧动作，并写「四肢粗细与参考一致」+ 固定右侧视尾串；image-3954-151 起固定写「整帧只有人物，无任何光效、特效、光晕、粒子」，此前的帧用同义句「画面只有本人…不带任何光效」，收图后均按辉光门与目视复核无烘焙特效。

## 序列与插入位

1. `art/fighters/ultraman-justice/stage1/walk/frames/walk-back-00-raw.png`（既有）
2. `art/fighters/ultraman-justice/stage1/walk_back/frames/add-00.png`（新增，后退循环相位）
3. `art/fighters/ultraman-justice/stage1/walk/frames/walk-back-01-raw.png`（既有）
4. `art/fighters/ultraman-justice/stage1/walk_back/frames/add-01.png`（新增，后退循环相位）
5. `art/fighters/ultraman-justice/stage1/walk/frames/walk-back-02-raw.png`（既有）
6. `art/fighters/ultraman-justice/stage1/walk_back/frames/add-02.png`（新增，后退循环相位）
7. `art/fighters/ultraman-justice/stage1/walk/frames/walk-back-03-raw.png`（既有）
8. `art/fighters/ultraman-justice/stage1/walk_back/frames/add-03.png`（新增，后退循环相位）

## 新增帧门值

站高比＝主体 bbox 高÷图像高；锚同口径 0.8021（768×768，bbox 616）。站姿门 ±8%，同组相邻站姿突变 ≤10%。辉光门：主体＝α≥200 最大连通块外扩 3 px；外侧 α≥16 / α≥200 / α1–15 尘点，前两项须 ≤100 / =0，尘点只登记。全部帧 RGBA、α-min 0、四角 α=0、未触边。

| 序 | 文件 | 生成ID | 实收/字节 | SHA-256(前16) | Alpha | 辉光门 ≥16/≥200/尘点 | 站高比/对锚 | 动作相位与手/脚位置 | 例外 |
|---|---|---|---|---|---|---|---|---|---|
| 2 | `frames/add-00.png` | `image-3954-405` | 1254×1254 / 447,147 B | `904f6ecbf1c826a6…` | RGBA, α-min 0, 四角 0 | 10 / 0 / 70,836 | 0.7815 / -2.6% | 后退过渡：重心后坐，前脚脚跟抬起、脚尖点地，后脚全掌承重；护架轻摆。 | — |
| 4 | `frames/add-01.png` | `image-3954-410` | 1179×1334 / 369,037 B | `6821bc0fdb5bf8eb…` | RGBA, α-min 0, 四角 0 | 1 / 0 / 9,449 | 0.7534 / -6.1% | 后退过渡：前脚离地向支撑腿旁后摆、屈膝，后脚支撑；重心后坐、上身略后倾。 | — |
| 6 | `frames/add-02.png` | `image-3954-415` | 1254×1254 / 360,836 B | `8e55da2b6557b053…` | RGBA, α-min 0, 四角 0 | 5 / 0 / 8,797 | 0.7751 / -3.4% | 反向后退过渡：换另一脚在前，脚跟抬起、脚尖点地，后脚全掌承重。 | — |
| 8 | `frames/add-03.png` | `image-3954-422` | 1254×1254 / 341,921 B | `8cdac97166c4e5b7…` | RGBA, α-min 0, 四角 0 | 3 / 0 / 10,468 | 0.7648 / -4.7% | 接循环：后脚离地向支撑腿旁后摆、屈膝，前脚支撑；动作接 walk-back-00。 | — |

## 被拒稿

| 文件 | 生成ID | 尺寸/字节 | SHA-256(前16) | 站高比 | 拒收原因 |
|---|---|---|---|---|---|
| — | — | — | — | — | 本组无被拒稿 |

## 衔接检查

8帧循环：00接触→add-00重心后坐、前跟抬起→01后腿支撑、前腿后摆→add-01前脚离地后摆→02反向接触→add-02后坐、前跟抬起→03后腿支撑→add-03后脚离地后摆→回00。

站高衔接：播放序内相邻站高最大变化 6.0%（门限 10%）；站姿对锚偏差见上表。 循环首尾：add-03（后脚离地后摆）→walk-back-00（接触），同腿接续。

## 状态

raw 未落格、未装机；未改 assets/content；未运行 Godot；未提交 git；无录屏。

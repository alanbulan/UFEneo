# 杰斯提斯 stage1 light3 扩产记录（2026-11-11，raw 未落格）

本轮新增 **2 帧**（4→6）。只写 raw，不落格、不装机、不改 `assets/`、不改 `content/`、不运行 Godot、不提交 git。

身份参考：`art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-x4.png`（768×768，SHA `d13bcf04…`）；每帧只传这一张。生成：`magpie-image` / `codex/gpt-image-2`，quality high，background transparent，请求 1024×1536（实收尺寸见下表）。提示词 150–250 字，只写该帧动作，并写「四肢粗细与参考一致」+ 固定右侧视尾串；image-3954-151 起固定写「整帧只有人物，无任何光效、特效、光晕、粒子」，此前的帧用同义句「画面只有本人…不带任何光效」，收图后均按辉光门与目视复核无烘焙特效。

## 序列与插入位

1. `art/fighters/ultraman-justice/stage1/light3/frames/light3-00-raw.png`（既有）
2. `art/fighters/ultraman-justice/stage1/light3/frames/add-00.png`（新增，踢腿相位）
3. `art/fighters/ultraman-justice/stage1/light3/frames/light3-01-raw.png`（既有）
4. `art/fighters/ultraman-justice/stage1/light3/frames/light3-02-raw.png`（既有）
5. `art/fighters/ultraman-justice/stage1/light3/frames/add-01.png`（新增，踢腿相位）
6. `art/fighters/ultraman-justice/stage1/light3/frames/light3-03-raw.png`（既有）

## 新增帧门值

站高比＝主体 bbox 高÷图像高；锚同口径 0.8021（768×768，bbox 616）。站姿门 ±8%，同组相邻站姿突变 ≤10%。辉光门：主体＝α≥200 最大连通块外扩 3 px；外侧 α≥16 / α≥200 / α1–15 尘点，前两项须 ≤100 / =0，尘点只登记。全部帧 RGBA、α-min 0、四角 α=0、未触边。

| 序 | 文件 | 生成ID | 实收/字节 | SHA-256(前16) | Alpha | 辉光门 ≥16/≥200/尘点 | 站高比/对锚 | 动作相位与手/脚位置 | 例外 |
|---|---|---|---|---|---|---|---|---|---|
| 2 | `frames/add-00.png` | `image-3954-21` | 1254×1254 / 347,403 B | `fe042a4ce7f402ae…` | RGBA, α-min 0, 四角 0 | 0 / 0 / 14,981 | 0.7863 / -2.0% | 踢腿展开：抬起的膝向前送出、小腿前伸、脚尖勾起；支撑腿微屈，双拳胸前护架，上身直立。 | — |
| 5 | `frames/add-01.png` | `image-3954-24` | 1254×1254 / 356,315 B | `0acb0ac0a1b785ad…` | RGBA, α-min 0, 四角 0 | 0 / 0 / 12,317 | 0.8022 / +0.0% | 踢腿落地：踢出的腿屈膝落回身前，前脚掌先着地；后脚踩实，双拳回护架，重心回两脚之间。 | — |

## 被拒稿

| 文件 | 生成ID | 尺寸/字节 | SHA-256(前16) | 站高比 | 拒收原因 |
|---|---|---|---|---|---|
| — | — | — | — | — | 本组无被拒稿 |

## 衔接检查

6帧踢腿：00提膝→add-00小腿前伸→01踢尽→02收腿→add-01落脚→03回架。

站高衔接：播放序内相邻站高最大变化 4.4%（门限 10%）；站姿对锚偏差见上表。 相邻新帧与既有帧均有可见手/脚位移，未发现同姿势复制。

## 状态

raw 未落格、未装机；未改 assets/content；未运行 Godot；未提交 git；无录屏。

# 杰斯提斯 stage1 heavy 扩产记录（2026-11-11，raw 未落格）

本轮新增 **3 帧**（4→7）。只写 raw，不落格、不装机、不改 `assets/`、不改 `content/`、不运行 Godot、不提交 git。

身份参考：`art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-x4.png`（768×768，SHA `d13bcf04…`）；每帧只传这一张。生成：`magpie-image` / `codex/gpt-image-2`，quality high，background transparent，请求 1024×1536（实收尺寸见下表）。提示词 150–250 字，只写该帧动作，并写「四肢粗细与参考一致」+ 固定右侧视尾串；image-3954-151 起固定写「整帧只有人物，无任何光效、特效、光晕、粒子」，此前的帧用同义句「画面只有本人…不带任何光效」，收图后均按辉光门与目视复核无烘焙特效。

## 序列与插入位

1. `art/fighters/ultraman-justice/stage1/heavy/frames/heavy-00-raw.png`（既有）
2. `art/fighters/ultraman-justice/stage1/heavy/frames/add-00.png`（新增，踏步重拳相位）
3. `art/fighters/ultraman-justice/stage1/heavy/frames/heavy-01-raw.png`（既有）
4. `art/fighters/ultraman-justice/stage1/heavy/frames/add-01.png`（新增，踏步重拳相位）
5. `art/fighters/ultraman-justice/stage1/heavy/frames/heavy-02-raw.png`（既有）
6. `art/fighters/ultraman-justice/stage1/heavy/frames/add-02.png`（新增，踏步重拳相位）
7. `art/fighters/ultraman-justice/stage1/heavy/frames/heavy-03-raw.png`（既有）

## 新增帧门值

站高比＝主体 bbox 高÷图像高；锚同口径 0.8021（768×768，bbox 616）。站姿门 ±8%，同组相邻站姿突变 ≤10%。辉光门：主体＝α≥200 最大连通块外扩 3 px；外侧 α≥16 / α≥200 / α1–15 尘点，前两项须 ≤100 / =0，尘点只登记。全部帧 RGBA、α-min 0、四角 α=0、未触边。

| 序 | 文件 | 生成ID | 实收/字节 | SHA-256(前16) | Alpha | 辉光门 ≥16/≥200/尘点 | 站高比/对锚 | 动作相位与手/脚位置 | 例外 |
|---|---|---|---|---|---|---|---|---|---|
| 2 | `frames/add-00.png` | `image-3954-26` | 1254×1254 / 373,146 B | `e5ba9ee3b0e059ae…` | RGBA, α-min 0, 四角 0 | 0 / 0 / 12,372 | 0.7807 / -2.7% | 送步起手：后脚蹬地、重心前移，前脚刚离地迈出；后腿伸直支撑，双拳护架，上身前倾。 | — |
| 4 | `frames/add-01.png` | `image-3954-40` | 1254×1254 / 376,431 B | `d758eaf21604a57f…` | RGBA, α-min 0, 四角 0 | 3 / 0 / 14,017 | 0.7440 / -7.2% | 踏步重拳半程：前脚踏地成弓步、前膝约九十度；后拳收肩侧，前拳直线推出到一半；重心在前脚。 | 弓步命中，站高 -7.2%，门内。 |
| 6 | `frames/add-02.png` | `image-3954-170` | 1254×1254 / 373,314 B | `508ab8cfaf6b8a56…` | RGBA, α-min 0, 四角 0 | 3 / 0 / 12,351 | 0.8038 / +0.2% | 收拳过半：前拳停胸前偏前一拳、肘弯；前腿由弓步开始伸直，后拳回肩侧；上身开始直起。 | — |

## 被拒稿

| 文件 | 生成ID | 尺寸/字节 | SHA-256(前16) | 站高比 | 拒收原因 |
|---|---|---|---|---|---|
| `frames/add-01-rejected-01.png` | `image-3954-29` | 1254×1254 / 401,413 B | `8b7eb809d1bb1679…` | 站高比 0.6826（-14.9%） | 弓步过深、上身压得过低，站高比 0.683（-14.9%）；重掷为步幅适中、前膝约九十度、上身较高。 |
| `frames/add-02-rejected-01.png` | `image-3954-31` | 1254×1254 / 329,518 B | `a312006520093250…` | 站高比 0.8062（+0.5%） | 与 heavy-03 护架近重复，收拳无可见位移；重掷为「拳停胸前偏前一拳、前腿仍略弓」。 |

说明：以上被拒稿文件已按仓库无备份规则**文件已删除**；仅保留文件名、SHA 与拒收原因。

## 衔接检查

7帧踏步重拳：00蓄力→add-00送步→01踏地→add-01拳出半程→02直线命中→add-02收拳→03回架。add-01首版弓步过深被拒，add-02首版与护架重复被拒。

站高衔接：播放序内相邻站高最大变化 5.3%（门限 10%）；站姿对锚偏差见上表。 相邻新帧与既有帧均有可见手/脚位移，未发现同姿势复制。

## 状态

raw 未落格、未装机；未改 assets/content；未运行 Godot；未提交 git；无录屏。

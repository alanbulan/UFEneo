# 杰斯提斯 stage1 light2 扩产记录（2026-11-11，raw 未落格）

本轮新增 **2 帧**（3→5）。只写 raw，不落格、不装机、不改 `assets/`、不改 `content/`、不运行 Godot、不提交 git。

身份参考：`art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-x4.png`（768×768，SHA `d13bcf04…`）；每帧只传这一张。生成：`magpie-image` / `codex/gpt-image-2`，quality high，background transparent，请求 1024×1536（实收尺寸见下表）。提示词 150–250 字，只写该帧动作，并写「四肢粗细与参考一致」+ 固定右侧视尾串；image-3954-151 起固定写「整帧只有人物，无任何光效、特效、光晕、粒子」，此前的帧用同义句「画面只有本人…不带任何光效」，收图后均按辉光门与目视复核无烘焙特效。

## 序列与插入位

1. `art/fighters/ultraman-justice/stage1/light2/frames/light2-00-raw.png`（既有）
2. `art/fighters/ultraman-justice/stage1/light2/frames/add-00.png`（新增，上勾拳相位）
3. `art/fighters/ultraman-justice/stage1/light2/frames/light2-01-raw.png`（既有）
4. `art/fighters/ultraman-justice/stage1/light2/frames/light2-02-raw.png`（既有）
5. `art/fighters/ultraman-justice/stage1/light2/frames/add-01.png`（新增，上勾拳相位）

## 新增帧门值

站高比＝主体 bbox 高÷图像高；锚同口径 0.8021（768×768，bbox 616）。站姿门 ±8%，同组相邻站姿突变 ≤10%。辉光门：主体＝α≥200 最大连通块外扩 3 px；外侧 α≥16 / α≥200 / α1–15 尘点，前两项须 ≤100 / =0，尘点只登记。全部帧 RGBA、α-min 0、四角 α=0、未触边。

| 序 | 文件 | 生成ID | 实收/字节 | SHA-256(前16) | Alpha | 辉光门 ≥16/≥200/尘点 | 站高比/对锚 | 动作相位与手/脚位置 | 例外 |
|---|---|---|---|---|---|---|---|---|---|
| 2 | `frames/add-00.png` | `image-3954-18` | 1254×1254 / 384,022 B | `99b3338cab63fe72…` | RGBA, α-min 0, 四角 0 | 0 / 0 / 15,563 | 0.8014 / -0.1% | 勾拳蓄力：前侧拳收至腹前、后侧拳抬到脸旁；双膝微屈、双脚全掌踩地；肩后拉、腰胯轻拧。 | — |
| 5 | `frames/add-01.png` | `image-3954-165` | 1254×1254 / 373,520 B | `9c035fb0ca36f0c8…` | RGBA, α-min 0, 四角 0 | 3 / 0 / 12,265 | 0.8006 / -0.2% | 勾拳回收过半：出拳沿弧线降到肩高、拳停身前上方；护拳在脸旁；肩回正、重心落回两脚之间。 | — |

## 被拒稿

| 文件 | 生成ID | 尺寸/字节 | SHA-256(前16) | 站高比 | 拒收原因 |
|---|---|---|---|---|---|
| `frames/add-00-rejected-01.png` | `image-3954-7` | 1254×1254 / 390,406 B | `2e49ac3a7337d97f…` | 站高比 0.7321（-8.7%） | 读成抬膝深弓步、站高比 0.732（-8.7%）；重掷为双脚全掌踩地、身体直立。 |
| `frames/add-01-rejected-01.png` | `image-3954-9` | 1254×1254 / 331,323 B | `0b6cd0329f1bf0d1…` | 站高比 0.7743（-3.5%） | 与护架帧近重复，勾拳收手未离胸前；重掷为「沿弧线降到肩高、拳停身前上方」。 |

说明：以上被拒稿文件已按仓库无备份规则**文件已删除**；仅保留文件名、SHA 与拒收原因。

## 衔接检查

5帧上勾拳：00护架→add-00收拳蓄力→01勾拳→02收拳→add-01沿弧线回收。add-00首版读成抬膝深弓步，重掷为双脚全掌踩地；add-01首版与护架重复，重掷为拳停身前上方。

站高衔接：播放序内相邻站高最大变化 0.7%（门限 10%）；站姿对锚偏差见上表。 相邻新帧与既有帧均有可见手/脚位移，未发现同姿势复制。

## 状态

raw 未落格、未装机；未改 assets/content；未运行 Godot；未提交 git；无录屏。

# 杰斯提斯 stage1 vertical_light 扩产记录（2026-11-11，raw 未落格）

本轮新增 **1 帧**（3→4）。只写 raw，不落格、不装机、不改 `assets/`、不改 `content/`、不运行 Godot、不提交 git。

身份参考：`art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-x4.png`（768×768，SHA `d13bcf04…`）；每帧只传这一张。生成：`magpie-image` / `codex/gpt-image-2`，quality high，background transparent，请求 1024×1536（实收尺寸见下表）。提示词 150–250 字，只写该帧动作，并写「四肢粗细与参考一致」+ 固定右侧视尾串；image-3954-151 起固定写「整帧只有人物，无任何光效、特效、光晕、粒子」，此前的帧用同义句「画面只有本人…不带任何光效」，收图后均按辉光门与目视复核无烘焙特效。

## 序列与插入位

1. `art/fighters/ultraman-justice/stage1/vertical_light/frames/vertical_light-00-raw.png`（既有）
2. `art/fighters/ultraman-justice/stage1/vertical_light/frames/add-00.png`（新增，空中轻击相位）
3. `art/fighters/ultraman-justice/stage1/vertical_light/frames/vertical_light-01-raw.png`（既有）
4. `art/fighters/ultraman-justice/stage1/vertical_light/frames/vertical_light-02-raw.png`（既有）

## 新增帧门值

站高比＝主体 bbox 高÷图像高；锚同口径 0.8021（768×768，bbox 616）。站姿门 ±8%，同组相邻站姿突变 ≤10%。辉光门：主体＝α≥200 最大连通块外扩 3 px；外侧 α≥16 / α≥200 / α1–15 尘点，前两项须 ≤100 / =0，尘点只登记。全部帧 RGBA、α-min 0、四角 α=0、未触边。

| 序 | 文件 | 生成ID | 实收/字节 | SHA-256(前16) | Alpha | 辉光门 ≥16/≥200/尘点 | 站高比/对锚 | 动作相位与手/脚位置 | 例外 |
|---|---|---|---|---|---|---|---|---|---|
| 2 | `frames/add-00.png` | `image-3954-302` | 1199×1312 / 338,185 B | `20017a9615ec08cd…` | RGBA, α-min 0, 四角 0 | 17 / 0 / 13,055 | 0.6334 / -21.0% | 空中出拳过半：右拳从胸前向前推出约一半、肘仍弯；腰胯前拧、双膝收起、身体悬空，左拳护脸。 | 空中出拳，站高比不适用。 |

## 被拒稿

| 文件 | 生成ID | 尺寸/字节 | SHA-256(前16) | 站高比 | 拒收原因 |
|---|---|---|---|---|---|
| — | — | — | — | — | 本组无被拒稿 |

## 衔接检查

4帧空中轻击：00收膝起势→add-00出拳半程→01远侧右拳前击→02收拳下落。add-00插在00与01之间。

站高衔接：本组含倒地/腾空动态，不适用直立站高突变门；所有帧按头身与同组目视一致。

## 状态

raw 未落格、未装机；未改 assets/content；未运行 Godot；未提交 git；无录屏。

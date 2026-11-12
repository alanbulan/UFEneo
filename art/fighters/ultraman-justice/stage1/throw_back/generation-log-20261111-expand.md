# 杰斯提斯 stage1 throw_back 扩产记录（2026-11-11，raw 未落格）

本轮新增 **5 帧**（3→8）。只写 raw，不落格、不装机、不改 `assets/`、不改 `content/`、不运行 Godot、不提交 git。

身份参考：`art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-x4.png`（768×768，SHA `d13bcf04…`）；每帧只传这一张。生成：`magpie-image` / `codex/gpt-image-2`，quality high，background transparent，请求 1024×1536（实收尺寸见下表）。提示词 150–250 字，只写该帧动作，并写「四肢粗细与参考一致」+ 固定右侧视尾串；image-3954-151 起固定写「整帧只有人物，无任何光效、特效、光晕、粒子」，此前的帧用同义句「画面只有本人…不带任何光效」，收图后均按辉光门与目视复核无烘焙特效。

## 序列与插入位

1. `art/fighters/ultraman-justice/stage1/throw_back/frames/throw_back-00-raw.png`（既有）
2. `art/fighters/ultraman-justice/stage1/throw_back/frames/add-00.png`（新增，后投相位）
3. `art/fighters/ultraman-justice/stage1/throw_back/frames/throw_back-01-raw.png`（既有）
4. `art/fighters/ultraman-justice/stage1/throw_back/frames/add-01.png`（新增，后投相位）
5. `art/fighters/ultraman-justice/stage1/throw_back/frames/add-02.png`（新增，后投相位）
6. `art/fighters/ultraman-justice/stage1/throw_back/frames/add-03.png`（新增，后投相位）
7. `art/fighters/ultraman-justice/stage1/throw_back/frames/add-04.png`（新增，后投相位）
8. `art/fighters/ultraman-justice/stage1/throw_back/frames/throw_back-02-raw.png`（既有）

## 新增帧门值

站高比＝主体 bbox 高÷图像高；锚同口径 0.8021（768×768，bbox 616）。站姿门 ±8%，同组相邻站姿突变 ≤10%。辉光门：主体＝α≥200 最大连通块外扩 3 px；外侧 α≥16 / α≥200 / α1–15 尘点，前两项须 ≤100 / =0，尘点只登记。全部帧 RGBA、α-min 0、四角 α=0、未触边。

| 序 | 文件 | 生成ID | 实收/字节 | SHA-256(前16) | Alpha | 辉光门 ≥16/≥200/尘点 | 站高比/对锚 | 动作相位与手/脚位置 | 例外 |
|---|---|---|---|---|---|---|---|---|---|
| 2 | `frames/add-00.png` | `image-3954-270` | 1247×1261 / 352,090 B | `8b503efcb528adf5…` | RGBA, α-min 0, 四角 0 | 0 / 0 / 9,914 | 0.7922 / -1.2% | 抓握回拉：双手向前抓握、十指扣紧，双臂屈肘把手拉到胸前；双膝微屈、腰背收紧，保持右侧视。 | — |
| 4 | `frames/add-01.png` | `image-3954-275` | 1254×1254 / 402,731 B | `b181b7fa62f71ef6…` | RGBA, α-min 0, 四角 0 | 0 / 0 / 13,227 | 0.7974 / -0.6% | 半背身拧转：腰部向背侧拧、双手抱在胸前偏前，肩随转、髋仍朝原方向；膝盖弯曲，身体到半背侧。 | — |
| 5 | `frames/add-02.png` | `image-3954-280` | 1254×1254 / 464,013 B | `52bb330eeceac30e…` | RGBA, α-min 0, 四角 0 | 1 / 0 / 28,366 | 0.7719 / -3.8% | 转背下压：身体继续转向背侧、双臂把抓握点带到腰侧偏后；上身前压、双膝下沉、肩背拱起，背对镜头。 | — |
| 6 | `frames/add-03.png` | `image-3954-286` | 1254×1254 / 438,175 B | `41593ef3c7759d7e…` | RGBA, α-min 0, 四角 0 | 4 / 0 / 30,151 | 0.8437 / +5.2% | 背身提起：腰背发力向上提，双臂弯着把抓握点抬到肩后高度；上身前倾、膝盖渐伸直，背对镜头。 | — |
| 7 | `frames/add-04.png` | `image-3954-291` | 1254×1254 / 446,745 B | `c76ec4ea9fc1cf3a…` | RGBA, α-min 0, 四角 0 | 7 / 0 / 18,973 | 0.8397 / +4.7% | 背身甩出：双臂向身后上方甩出、手已松开、手掌朝后上；身体挺直略后仰、双腿蹬直，重心在前脚。 | — |

## 被拒稿

| 文件 | 生成ID | 尺寸/字节 | SHA-256(前16) | 站高比 | 拒收原因 |
|---|---|---|---|---|---|
| — | — | — | — | — | 本组无被拒稿 |

## 衔接检查

8帧后投：00抓握→add-00回拉→01左拧收臂→add-01半背身→add-02转背下压→add-03背身提起→add-04背身甩出→02身后上方甩出。

站高衔接：播放序内相邻站高最大变化 9.3%（门限 10%）；站姿对锚偏差见上表。 相邻新帧与既有帧均有可见手/脚位移，未发现同姿势复制。

## 状态

raw 未落格、未装机；未改 assets/content；未运行 Godot；未提交 git；无录屏。

# 杰斯提斯 stage1 intro 扩产记录（2026-11-11，raw 未落格）

本轮新增 **5 帧**（3→8）。只写 raw，不落格、不装机、不改 `assets/`、不改 `content/`、不运行 Godot、不提交 git。

身份参考：`art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-x4.png`（768×768，SHA `d13bcf04…`）；每帧只传这一张。生成：`magpie-image` / `codex/gpt-image-2`，quality high，background transparent，请求 1024×1536（实收尺寸见下表）。提示词 150–250 字，只写该帧动作，并写「四肢粗细与参考一致」+ 固定右侧视尾串；image-3954-151 起固定写「整帧只有人物，无任何光效、特效、光晕、粒子」，此前的帧用同义句「画面只有本人…不带任何光效」，收图后均按辉光门与目视复核无烘焙特效。

## 序列与插入位

1. `art/fighters/ultraman-justice/stage1/intro/frames/add-00.png`（新增，登场相位）
2. `art/fighters/ultraman-justice/stage1/intro/frames/intro-00-raw.png`（既有）
3. `art/fighters/ultraman-justice/stage1/intro/frames/add-01.png`（新增，登场相位）
4. `art/fighters/ultraman-justice/stage1/intro/frames/intro-01-raw.png`（既有）
5. `art/fighters/ultraman-justice/stage1/intro/frames/add-02.png`（新增，登场相位）
6. `art/fighters/ultraman-justice/stage1/intro/frames/add-03.png`（新增，登场相位）
7. `art/fighters/ultraman-justice/stage1/intro/frames/add-04.png`（新增，登场相位）
8. `art/fighters/ultraman-justice/stage1/intro/frames/intro-02-raw.png`（既有）

## 新增帧门值

站高比＝主体 bbox 高÷图像高；锚同口径 0.8021（768×768，bbox 616）。站姿门 ±8%，同组相邻站姿突变 ≤10%。辉光门：主体＝α≥200 最大连通块外扩 3 px；外侧 α≥16 / α≥200 / α1–15 尘点，前两项须 ≤100 / =0，尘点只登记。全部帧 RGBA、α-min 0、四角 α=0、未触边。

| 序 | 文件 | 生成ID | 实收/字节 | SHA-256(前16) | Alpha | 辉光门 ≥16/≥200/尘点 | 站高比/对锚 | 动作相位与手/脚位置 | 例外 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `frames/add-00.png` | `image-3954-71` | 1247×1261 / 294,411 B | `1aece5c81ac85bcc…` | RGBA, α-min 0, 四角 0 | 2 / 0 / 10,525 | 0.7819 / -2.5% | 起势：双拳从体侧收向胸前，身体直立只微低头，双膝几乎不弯；双脚原位踩实，准备抬头亮相。 | — |
| 3 | `frames/add-01.png` | `image-3954-47` | 1024×1536 / 1,200,750 B | `6056a6f603837e21…` | RGBA, α-min 0, 四角 0 | 1 / 0 / 27,876 | 0.7728 / -3.7% | 抬臂过半：抬头挺胸，近侧手臂从胸前向前上方抬起一半、手掌张开；远侧拳在腰侧；双膝微屈。 | — |
| 5 | `frames/add-02.png` | `image-3954-51` | 1254×1254 / 386,630 B | `ccd6f56e3dbf0444…` | RGBA, α-min 0, 四角 0 | 0 / 0 / 15,557 | 0.8022 / +0.0% | 收臂过半：前伸手臂屈肘收回、手掌放松；肩回落，上身仍挺胸；远侧拳在腰侧，双脚站定。 | — |
| 6 | `frames/add-03.png` | `image-3954-55` | 1024×1536 / 1,092,236 B | `86cc80d39e2763b9…` | RGBA, α-min 0, 四角 0 | 6 / 0 / 18,221 | 0.7467 / -6.9% | 收臂到胸前：前臂来到胸前、手掌收成拳，另一拳仍在腰侧；低头幅度收回，双膝微屈。 | — |
| 7 | `frames/add-04.png` | `image-3954-176` | 1254×1254 / 340,355 B | `2db09497ecd45705…` | RGBA, α-min 0, 四角 0 | 0 / 0 / 11,095 | 0.7544 / -5.9% | 收势：双拳刚收到胸前、两拳间留一拳空隙、拳心相对；双脚收回半步，膝盖微屈，尚未回标准护架。 | — |

## 被拒稿

| 文件 | 生成ID | 尺寸/字节 | SHA-256(前16) | 站高比 | 拒收原因 |
|---|---|---|---|---|---|
| `frames/add-00-rejected-01.png` | `image-3954-43` | 1254×1254 / 363,193 B | `7c64d9af7d2ddeb4…` | 站高比 0.7376（-8.0%） | 低头/屈膝过深，站高比 0.738（-8.0%），读成鞠躬；重掷为身体直立、只微低头、双膝几乎不弯。 |
| `frames/add-04-rejected-01.png` | `image-3954-58` | 1254×1254 / 335,142 B | `c4075cf6aa3211a0…` | 站高比 0.7974（-0.6%） | 与 intro-02 护架近重复；重掷为双拳刚收到胸前、两拳留一拳空隙、双脚收回半步。 |

说明：以上被拒稿文件已按仓库无备份规则**文件已删除**；仅保留文件名、SHA 与拒收原因。

## 衔接检查

8帧登场：add-00起势→00贴胸礼→add-01抬臂半程→01宣言伸臂→add-02收臂半程→add-03收至胸前→add-04回架前→02标准护架。add-00插在既有00之前；add-00首版低头过深、add-04首版与护架重复，均已重掷。

站高衔接：播放序内相邻站高最大变化 6.9%（门限 10%）；站姿对锚偏差见上表。 相邻新帧与既有帧均有可见手/脚位移，未发现同姿势复制。

## 状态

raw 未落格、未装机；未改 assets/content；未运行 Godot；未提交 git；无录屏。

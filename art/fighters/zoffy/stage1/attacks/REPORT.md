# 佐菲 stage1 基础攻击 108 帧结案

日期：2026-11-10。范围：`light1` … `dive` 共 18 个基础攻击 clip，只做美术整帧；未安装进 `assets/` 或 `content/`，未改 manifest/JSON（含 `cells.json`），未运行 Godot，未提交 Git。

## 本轮完成

- 18 个 clip、108 帧全部生成、落格并逐帧审片。逐 clip 硬要求相加为 **108**；任务标题写 106，本批按逐 clip 要求执行 108，差异 2 帧在此注明。
- 身份锚唯一：`art/fighters/zoffy/stage1/cells/idle-00-cell.png`（192×192，银头部 23×32）。全部动作帧只引用这一张，没有引用其它角色、其它角度或 4× 锚。
- 生图：MCP `magpie-image`，`codex/gpt-image-2`，quality high，transparent，逐帧单独请求；提示词 150–250 字，只写该帧动作，显式要求头大小、肩宽、肩甲体量和四肢粗细与参考一致；固定右侧视、完整人物不裁切、透明背景、无地面/文字/边框/光效/特效。普通攻击帧没有光效或飞行物。
- 落格：`tools/art/stage_cells.py`，`--scale-source art/fighters/zoffy/stage1/idle/frames/raw-00-v3.png`、`--target-standing 154`、`--cell 192`、`--anchor-x 96`、`--baseline 184`；全套共用同一个源像素比例与同一个 32 色色板（`assets/fighters/zoffy/catalogue/model-native.png`）。
- 生成图原生高度约 718–1171 px，与旧锚 raw-00-v3 的 1549 px 不同；对全部 108 帧统一做 `G = 1.575` 的 NEAREST 预放大，再乘锚定比例 0.099419，等效源→格比例 0.15658。没有逐帧归一化，屈膝与腾空压低保留。
- 成品目录：`art/fighters/zoffy/stage1/cells/`，命名 `<clip>-NN-cell.png`，全部 192×192。被拒候选已删除（见「重生成」）。

### 逐 clip 帧数

| clip | 动作 | 要求 | 实产 | 帧名 |
|---|---|---:|---:|---|
| `light1` | 前手短直拳 | 5 | 5 | `light1-00`–`light1-04` |
| `light2` | 后手直拳 | 5 | 5 | `light2-00`–`light2-04` |
| `light3` | 进身上勾拳 | 6 | 6 | `light3-00`–`light3-05` |
| `heavy` | 踏步重拳 | 7 | 7 | `heavy-00`–`heavy-06` |
| `launcher` | 升龙上勾拳 | 7 | 7 | `launcher-00`–`launcher-06` |
| `spin_heavy` | 回身横扫肘 | 7 | 7 | `spin_heavy-00`–`spin_heavy-06` |
| `crush` | 双拳破甲砸击 | 9 | 9 | `crush-00`–`crush-08` |
| `tackle` | 沉肩突进 | 8 | 8 | `tackle-00`–`tackle-07` |
| `crouch_light` | 蹲姿下段直拳 | 4 | 4 | `crouch_light-00`–`crouch_light-03` |
| `sweep` | 低扫脚跟 | 7 | 7 | `sweep-00`–`sweep-06` |
| `slide` | 低身滑铲 | 8 | 8 | `slide-00`–`slide-07` |
| `crouch_light2` | 蹲姿二段直拳 | 4 | 4 | `crouch_light2-00`–`crouch_light2-03` |
| `dash_light` | 冲刺直拳 | 5 | 5 | `dash_light-00`–`dash_light-04` |
| `dash_heavy` | 冲刺飞踢 | 6 | 6 | `dash_heavy-00`–`dash_heavy-05` |
| `vertical_light` | 垂直跳短拳 | 4 | 4 | `vertical_light-00`–`vertical_light-03` |
| `vertical_heavy` | 垂直跳下砸拳 | 5 | 5 | `vertical_heavy-00`–`vertical_heavy-04` |
| `air_crush` | 空中双拳下砸 | 6 | 6 | `air_crush-00`–`air_crush-05` |
| `dive` | 俯冲脚跟踢 | 5 | 5 | `dive-00`–`dive-04` |
| **合计** |  | **108** | **108** |  |

## 硬门与逐帧数值

统一结论：108/108 帧均为 192×192；连通块 1；Alpha 只有 `{0,255}`；色数 31–32（≤32）；包围盒 x 2–189、y 1–183、脚底 183，无裁切。以下逐帧列出实测值。`块`=连通块数，`Alpha`=出现的 Alpha 值。

### light1（5 帧，前手短直拳）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `light1-00` | `art/fighters/zoffy/stage1/cells/light1-00-cell.png` | `art/fighters/zoffy/stage1/light1/frames/light1-00-raw-2.png` | (57,32,135,183) | 152×79 | 32 | 1 | 0/255 | 直立护架 |
| `light1-01` | `art/fighters/zoffy/stage1/cells/light1-01-cell.png` | `art/fighters/zoffy/stage1/light1/frames/light1-01-raw-3.png` | (50,40,142,183) | 144×93 | 32 | 1 | 0/255 | 屈膝蓄力 |
| `light1-02` | `art/fighters/zoffy/stage1/cells/light1-02-cell.png` | `art/fighters/zoffy/stage1/light1/frames/light1-02-raw.png` | (44,29,158,183) | 155×115 | 32 | 1 | 0/255 | 直立直拳 |
| `light1-03` | `art/fighters/zoffy/stage1/cells/light1-03-cell.png` | `art/fighters/zoffy/stage1/light1/frames/light1-03-raw.png` | (63,34,130,183) | 150×68 | 32 | 1 | 0/255 | 直立收拳 |
| `light1-04` | `art/fighters/zoffy/stage1/cells/light1-04-cell.png` | `art/fighters/zoffy/stage1/light1/frames/light1-04-raw.png` | (57,29,134,183) | 155×78 | 32 | 1 | 0/255 | 直立护架 |

### light2（5 帧，后手直拳）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `light2-00` | `art/fighters/zoffy/stage1/cells/light2-00-cell.png` | `art/fighters/zoffy/stage1/light2/frames/light2-00-raw-2.png` | (52,27,140,183) | 157×89 | 32 | 1 | 0/255 | 直立护架 |
| `light2-01` | `art/fighters/zoffy/stage1/cells/light2-01-cell.png` | `art/fighters/zoffy/stage1/light2/frames/light2-01-raw-2.png` | (56,38,134,183) | 146×79 | 31 | 1 | 0/255 | 屈膝蓄拳 |
| `light2-02` | `art/fighters/zoffy/stage1/cells/light2-02-cell.png` | `art/fighters/zoffy/stage1/light2/frames/light2-02-raw-2.png` | (31,32,172,183) | 152×142 | 31 | 1 | 0/255 | 直立直拳 |
| `light2-03` | `art/fighters/zoffy/stage1/cells/light2-03-cell.png` | `art/fighters/zoffy/stage1/light2/frames/light2-03-raw.png` | (61,26,133,183) | 158×73 | 32 | 1 | 0/255 | 直立收拳 |
| `light2-04` | `art/fighters/zoffy/stage1/cells/light2-04-cell.png` | `art/fighters/zoffy/stage1/light2/frames/light2-04-raw.png` | (57,31,134,183) | 153×78 | 32 | 1 | 0/255 | 直立护架 |

### light3（6 帧，进身上勾拳）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `light3-00` | `art/fighters/zoffy/stage1/cells/light3-00-cell.png` | `art/fighters/zoffy/stage1/light3/frames/light3-00-raw.png` | (57,28,135,183) | 156×79 | 32 | 1 | 0/255 | 直立护架 |
| `light3-01` | `art/fighters/zoffy/stage1/cells/light3-01-cell.png` | `art/fighters/zoffy/stage1/light3/frames/light3-01-raw.png` | (51,47,140,183) | 137×90 | 32 | 1 | 0/255 | 屈膝蓄力 |
| `light3-02` | `art/fighters/zoffy/stage1/cells/light3-02-cell.png` | `art/fighters/zoffy/stage1/light3/frames/light3-02-raw.png` | (50,24,132,183) | 160×83 | 32 | 1 | 0/255 | 起身上勾 |
| `light3-03` | `art/fighters/zoffy/stage1/cells/light3-03-cell.png` | `art/fighters/zoffy/stage1/light3/frames/light3-03-raw.png` | (41,5,132,183) | 179×92 | 32 | 1 | 0/255 | 腾空上勾 |
| `light3-04` | `art/fighters/zoffy/stage1/cells/light3-04-cell.png` | `art/fighters/zoffy/stage1/light3/frames/light3-04-raw.png` | (59,36,134,183) | 148×76 | 32 | 1 | 0/255 | 收势 |
| `light3-05` | `art/fighters/zoffy/stage1/cells/light3-05-cell.png` | `art/fighters/zoffy/stage1/light3/frames/light3-05-raw.png` | (60,31,132,183) | 153×73 | 32 | 1 | 0/255 | 直立护架 |

### heavy（7 帧，踏步重拳）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `heavy-00` | `art/fighters/zoffy/stage1/cells/heavy-00-cell.png` | `art/fighters/zoffy/stage1/heavy/frames/heavy-00-raw.png` | (62,36,145,183) | 148×84 | 32 | 1 | 0/255 | 直立护架 |
| `heavy-01` | `art/fighters/zoffy/stage1/cells/heavy-01-cell.png` | `art/fighters/zoffy/stage1/heavy/frames/heavy-01-raw.png` | (40,39,142,183) | 145×103 | 32 | 1 | 0/255 | 屈膝蓄力 |
| `heavy-02` | `art/fighters/zoffy/stage1/cells/heavy-02-cell.png` | `art/fighters/zoffy/stage1/heavy/frames/heavy-02-raw.png` | (32,49,144,183) | 135×113 | 32 | 1 | 0/255 | 屈膝蓄力 |
| `heavy-03` | `art/fighters/zoffy/stage1/cells/heavy-03-cell.png` | `art/fighters/zoffy/stage1/heavy/frames/heavy-03-raw.png` | (36,24,163,183) | 160×128 | 32 | 1 | 0/255 | 直立重拳 |
| `heavy-04` | `art/fighters/zoffy/stage1/cells/heavy-04-cell.png` | `art/fighters/zoffy/stage1/heavy/frames/heavy-04-raw.png` | (41,39,131,183) | 145×91 | 32 | 1 | 0/255 | 收势 |
| `heavy-05` | `art/fighters/zoffy/stage1/cells/heavy-05-cell.png` | `art/fighters/zoffy/stage1/heavy/frames/heavy-05-raw.png` | (61,29,133,183) | 155×73 | 32 | 1 | 0/255 | 直立护架 |
| `heavy-06` | `art/fighters/zoffy/stage1/cells/heavy-06-cell.png` | `art/fighters/zoffy/stage1/heavy/frames/heavy-06-raw.png` | (55,31,136,183) | 153×82 | 32 | 1 | 0/255 | 直立护架 |

### launcher（7 帧，升龙上勾拳）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `launcher-00` | `art/fighters/zoffy/stage1/cells/launcher-00-cell.png` | `art/fighters/zoffy/stage1/launcher/frames/launcher-00-raw.png` | (49,50,142,183) | 134×94 | 31 | 1 | 0/255 | 屈膝起手 |
| `launcher-01` | `art/fighters/zoffy/stage1/cells/launcher-01-cell.png` | `art/fighters/zoffy/stage1/launcher/frames/launcher-01-raw.png` | (45,52,136,183) | 132×92 | 32 | 1 | 0/255 | 屈膝蓄力 |
| `launcher-02` | `art/fighters/zoffy/stage1/cells/launcher-02-cell.png` | `art/fighters/zoffy/stage1/launcher/frames/launcher-02-raw.png` | (56,21,130,183) | 163×75 | 32 | 1 | 0/255 | 起身上勾 |
| `launcher-03` | `art/fighters/zoffy/stage1/cells/launcher-03-cell.png` | `art/fighters/zoffy/stage1/launcher/frames/launcher-03-raw-2.png` | (57,33,132,183) | 151×76 | 32 | 1 | 0/255 | 升龙顶点 |
| `launcher-04` | `art/fighters/zoffy/stage1/cells/launcher-04-cell.png` | `art/fighters/zoffy/stage1/launcher/frames/launcher-04-raw.png` | (64,41,131,183) | 143×68 | 32 | 1 | 0/255 | 收势屈膝 |
| `launcher-05` | `art/fighters/zoffy/stage1/cells/launcher-05-cell.png` | `art/fighters/zoffy/stage1/launcher/frames/launcher-05-raw.png` | (56,28,136,183) | 156×81 | 32 | 1 | 0/255 | 直立护架 |
| `launcher-06` | `art/fighters/zoffy/stage1/cells/launcher-06-cell.png` | `art/fighters/zoffy/stage1/launcher/frames/launcher-06-raw.png` | (54,27,138,183) | 157×85 | 31 | 1 | 0/255 | 直立护架 |

### spin_heavy（7 帧，回身横扫肘）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `spin_heavy-00` | `art/fighters/zoffy/stage1/cells/spin_heavy-00-cell.png` | `art/fighters/zoffy/stage1/spin_heavy/frames/spin_heavy-00-raw.png` | (56,30,136,183) | 154×81 | 32 | 1 | 0/255 | 直立护架 |
| `spin_heavy-01` | `art/fighters/zoffy/stage1/cells/spin_heavy-01-cell.png` | `art/fighters/zoffy/stage1/spin_heavy/frames/spin_heavy-01-raw.png` | (47,30,130,183) | 154×84 | 32 | 1 | 0/255 | 蓄力 |
| `spin_heavy-02` | `art/fighters/zoffy/stage1/cells/spin_heavy-02-cell.png` | `art/fighters/zoffy/stage1/spin_heavy/frames/spin_heavy-02-raw.png` | (43,29,133,183) | 155×91 | 32 | 1 | 0/255 | 回身 |
| `spin_heavy-03` | `art/fighters/zoffy/stage1/cells/spin_heavy-03-cell.png` | `art/fighters/zoffy/stage1/spin_heavy/frames/spin_heavy-03-raw.png` | (46,30,133,183) | 154×88 | 32 | 1 | 0/255 | 回身 |
| `spin_heavy-04` | `art/fighters/zoffy/stage1/cells/spin_heavy-04-cell.png` | `art/fighters/zoffy/stage1/spin_heavy/frames/spin_heavy-04-raw.png` | (52,24,153,183) | 160×102 | 32 | 1 | 0/255 | 横扫肘 |
| `spin_heavy-05` | `art/fighters/zoffy/stage1/cells/spin_heavy-05-cell.png` | `art/fighters/zoffy/stage1/spin_heavy/frames/spin_heavy-05-raw.png` | (60,23,133,183) | 161×74 | 32 | 1 | 0/255 | 收势 |
| `spin_heavy-06` | `art/fighters/zoffy/stage1/cells/spin_heavy-06-cell.png` | `art/fighters/zoffy/stage1/spin_heavy/frames/spin_heavy-06-raw.png` | (51,27,138,183) | 157×88 | 32 | 1 | 0/255 | 直立护架 |

### crush（9 帧，双拳破甲砸击）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `crush-00` | `art/fighters/zoffy/stage1/cells/crush-00-cell.png` | `art/fighters/zoffy/stage1/crush/frames/crush-00-raw.png` | (57,27,143,183) | 157×87 | 32 | 1 | 0/255 | 直立护架 |
| `crush-01` | `art/fighters/zoffy/stage1/cells/crush-01-cell.png` | `art/fighters/zoffy/stage1/crush/frames/crush-01-raw.png` | (64,33,129,183) | 151×66 | 32 | 1 | 0/255 | 屈膝蓄力 |
| `crush-02` | `art/fighters/zoffy/stage1/cells/crush-02-cell.png` | `art/fighters/zoffy/stage1/crush/frames/crush-02-raw-2.png` | (55,30,133,183) | 154×79 | 31 | 1 | 0/255 | 举拳过头 |
| `crush-03` | `art/fighters/zoffy/stage1/cells/crush-03-cell.png` | `art/fighters/zoffy/stage1/crush/frames/crush-03-raw.png` | (34,29,133,183) | 155×100 | 32 | 1 | 0/255 | 举拳过头 |
| `crush-04` | `art/fighters/zoffy/stage1/cells/crush-04-cell.png` | `art/fighters/zoffy/stage1/crush/frames/crush-04-raw.png` | (42,51,148,183) | 133×107 | 32 | 1 | 0/255 | 砸击屈膝 |
| `crush-05` | `art/fighters/zoffy/stage1/cells/crush-05-cell.png` | `art/fighters/zoffy/stage1/crush/frames/crush-05-raw.png` | (46,42,140,183) | 142×95 | 32 | 1 | 0/255 | 砸击屈膝 |
| `crush-06` | `art/fighters/zoffy/stage1/cells/crush-06-cell.png` | `art/fighters/zoffy/stage1/crush/frames/crush-06-raw.png` | (57,31,137,183) | 153×81 | 31 | 1 | 0/255 | 收势 |
| `crush-07` | `art/fighters/zoffy/stage1/cells/crush-07-cell.png` | `art/fighters/zoffy/stage1/crush/frames/crush-07-raw.png` | (67,27,127,183) | 157×61 | 32 | 1 | 0/255 | 直立护架 |
| `crush-08` | `art/fighters/zoffy/stage1/cells/crush-08-cell.png` | `art/fighters/zoffy/stage1/crush/frames/crush-08-raw.png` | (58,30,136,183) | 154×79 | 32 | 1 | 0/255 | 直立护架 |

### tackle（8 帧，沉肩突进）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `tackle-00` | `art/fighters/zoffy/stage1/cells/tackle-00-cell.png` | `art/fighters/zoffy/stage1/tackle/frames/tackle-00-raw.png` | (54,43,151,183) | 141×98 | 32 | 1 | 0/255 | 屈膝起手 |
| `tackle-01` | `art/fighters/zoffy/stage1/cells/tackle-01-cell.png` | `art/fighters/zoffy/stage1/tackle/frames/tackle-01-raw.png` | (31,43,158,183) | 141×128 | 32 | 1 | 0/255 | 前冲 |
| `tackle-02` | `art/fighters/zoffy/stage1/cells/tackle-02-cell.png` | `art/fighters/zoffy/stage1/tackle/frames/tackle-02-raw.png` | (59,29,189,183) | 155×131 | 31 | 1 | 0/255 | 前冲腾跃 |
| `tackle-03` | `art/fighters/zoffy/stage1/cells/tackle-03-cell.png` | `art/fighters/zoffy/stage1/tackle/frames/tackle-03-raw.png` | (47,44,176,183) | 140×130 | 32 | 1 | 0/255 | 前冲 |
| `tackle-04` | `art/fighters/zoffy/stage1/cells/tackle-04-cell.png` | `art/fighters/zoffy/stage1/tackle/frames/tackle-04-raw.png` | (39,39,162,183) | 145×124 | 31 | 1 | 0/255 | 前冲 |
| `tackle-05` | `art/fighters/zoffy/stage1/cells/tackle-05-cell.png` | `art/fighters/zoffy/stage1/tackle/frames/tackle-05-raw.png` | (49,63,173,183) | 121×125 | 32 | 1 | 0/255 | 低姿 |
| `tackle-06` | `art/fighters/zoffy/stage1/cells/tackle-06-cell.png` | `art/fighters/zoffy/stage1/tackle/frames/tackle-06-raw.png` | (62,29,132,183) | 155×71 | 32 | 1 | 0/255 | 直立护架 |
| `tackle-07` | `art/fighters/zoffy/stage1/cells/tackle-07-cell.png` | `art/fighters/zoffy/stage1/tackle/frames/tackle-07-raw.png` | (56,32,138,183) | 152×83 | 32 | 1 | 0/255 | 直立护架 |

### crouch_light（4 帧，蹲姿下段直拳）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `crouch_light-00` | `art/fighters/zoffy/stage1/cells/crouch_light-00-cell.png` | `art/fighters/zoffy/stage1/crouch_light/frames/crouch_light-00-raw.png` | (50,48,139,183) | 136×90 | 32 | 1 | 0/255 | 蹲姿护架 |
| `crouch_light-01` | `art/fighters/zoffy/stage1/cells/crouch_light-01-cell.png` | `art/fighters/zoffy/stage1/crouch_light/frames/crouch_light-01-raw.png` | (40,58,143,183) | 126×104 | 32 | 1 | 0/255 | 蹲姿蓄力 |
| `crouch_light-02` | `art/fighters/zoffy/stage1/cells/crouch_light-02-cell.png` | `art/fighters/zoffy/stage1/crouch_light/frames/crouch_light-02-raw.png` | (53,43,160,183) | 141×108 | 31 | 1 | 0/255 | 蹲姿直拳 |
| `crouch_light-03` | `art/fighters/zoffy/stage1/cells/crouch_light-03-cell.png` | `art/fighters/zoffy/stage1/crouch_light/frames/crouch_light-03-raw.png` | (54,39,137,183) | 145×84 | 32 | 1 | 0/255 | 蹲姿护架 |

### sweep（7 帧，低扫脚跟）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `sweep-00` | `art/fighters/zoffy/stage1/cells/sweep-00-cell.png` | `art/fighters/zoffy/stage1/sweep/frames/sweep-00-raw.png` | (39,47,149,183) | 137×111 | 32 | 1 | 0/255 | 低姿护架 |
| `sweep-01` | `art/fighters/zoffy/stage1/cells/sweep-01-cell.png` | `art/fighters/zoffy/stage1/sweep/frames/sweep-01-raw.png` | (53,45,146,183) | 139×94 | 32 | 1 | 0/255 | 低姿蓄力 |
| `sweep-02` | `art/fighters/zoffy/stage1/cells/sweep-02-cell.png` | `art/fighters/zoffy/stage1/sweep/frames/sweep-02-raw.png` | (34,61,154,183) | 123×121 | 32 | 1 | 0/255 | 低扫 |
| `sweep-03` | `art/fighters/zoffy/stage1/cells/sweep-03-cell.png` | `art/fighters/zoffy/stage1/sweep/frames/sweep-03-raw.png` | (31,62,148,183) | 122×118 | 32 | 1 | 0/255 | 低扫 |
| `sweep-04` | `art/fighters/zoffy/stage1/cells/sweep-04-cell.png` | `art/fighters/zoffy/stage1/sweep/frames/sweep-04-raw.png` | (29,53,152,183) | 131×124 | 32 | 1 | 0/255 | 低扫 |
| `sweep-05` | `art/fighters/zoffy/stage1/cells/sweep-05-cell.png` | `art/fighters/zoffy/stage1/sweep/frames/sweep-05-raw.png` | (64,48,141,183) | 136×78 | 32 | 1 | 0/255 | 低姿收势 |
| `sweep-06` | `art/fighters/zoffy/stage1/cells/sweep-06-cell.png` | `art/fighters/zoffy/stage1/sweep/frames/sweep-06-raw.png` | (51,41,145,183) | 143×95 | 32 | 1 | 0/255 | 低姿护架 |

### slide（8 帧，低身滑铲）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `slide-00` | `art/fighters/zoffy/stage1/cells/slide-00-cell.png` | `art/fighters/zoffy/stage1/slide/frames/slide-00-raw.png` | (51,41,156,183) | 143×106 | 32 | 1 | 0/255 | 低姿起手 |
| `slide-01` | `art/fighters/zoffy/stage1/cells/slide-01-cell.png` | `art/fighters/zoffy/stage1/slide/frames/slide-01-raw.png` | (51,62,134,183) | 122×84 | 32 | 1 | 0/255 | 下潜 |
| `slide-02` | `art/fighters/zoffy/stage1/cells/slide-02-cell.png` | `art/fighters/zoffy/stage1/slide/frames/slide-02-raw.png` | (22,69,154,183) | 115×133 | 32 | 1 | 0/255 | 滑铲 |
| `slide-03` | `art/fighters/zoffy/stage1/cells/slide-03-cell.png` | `art/fighters/zoffy/stage1/slide/frames/slide-03-raw.png` | (18,65,166,183) | 119×149 | 32 | 1 | 0/255 | 滑铲 |
| `slide-04` | `art/fighters/zoffy/stage1/cells/slide-04-cell.png` | `art/fighters/zoffy/stage1/slide/frames/slide-04-raw.png` | (26,67,160,183) | 117×135 | 32 | 1 | 0/255 | 滑铲 |
| `slide-05` | `art/fighters/zoffy/stage1/cells/slide-05-cell.png` | `art/fighters/zoffy/stage1/slide/frames/slide-05-raw.png` | (62,65,136,183) | 119×75 | 32 | 1 | 0/255 | 滑铲收势 |
| `slide-06` | `art/fighters/zoffy/stage1/cells/slide-06-cell.png` | `art/fighters/zoffy/stage1/slide/frames/slide-06-raw.png` | (53,37,138,183) | 147×86 | 32 | 1 | 0/255 | 起身 |
| `slide-07` | `art/fighters/zoffy/stage1/cells/slide-07-cell.png` | `art/fighters/zoffy/stage1/slide/frames/slide-07-raw-2.png` | (51,37,138,183) | 147×88 | 32 | 1 | 0/255 | 直立护架 |

### crouch_light2（4 帧，蹲姿二段直拳）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `crouch_light2-00` | `art/fighters/zoffy/stage1/cells/crouch_light2-00-cell.png` | `art/fighters/zoffy/stage1/crouch_light2/frames/crouch_light2-00-raw.png` | (55,51,140,183) | 133×86 | 31 | 1 | 0/255 | 蹲姿护架 |
| `crouch_light2-01` | `art/fighters/zoffy/stage1/cells/crouch_light2-01-cell.png` | `art/fighters/zoffy/stage1/crouch_light2/frames/crouch_light2-01-raw.png` | (50,55,140,183) | 129×91 | 32 | 1 | 0/255 | 蹲姿蓄力 |
| `crouch_light2-02` | `art/fighters/zoffy/stage1/cells/crouch_light2-02-cell.png` | `art/fighters/zoffy/stage1/crouch_light2/frames/crouch_light2-02-raw.png` | (61,40,184,183) | 144×124 | 32 | 1 | 0/255 | 蹲姿直拳 |
| `crouch_light2-03` | `art/fighters/zoffy/stage1/cells/crouch_light2-03-cell.png` | `art/fighters/zoffy/stage1/crouch_light2/frames/crouch_light2-03-raw.png` | (56,34,137,183) | 150×82 | 32 | 1 | 0/255 | 蹲姿护架 |

### dash_light（5 帧，冲刺直拳）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `dash_light-00` | `art/fighters/zoffy/stage1/cells/dash_light-00-cell.png` | `art/fighters/zoffy/stage1/dash_light/frames/dash_light-00-raw.png` | (47,30,152,183) | 154×106 | 32 | 1 | 0/255 | 直立护架 |
| `dash_light-01` | `art/fighters/zoffy/stage1/cells/dash_light-01-cell.png` | `art/fighters/zoffy/stage1/dash_light/frames/dash_light-01-raw.png` | (74,29,189,183) | 155×116 | 32 | 1 | 0/255 | 前冲 |
| `dash_light-02` | `art/fighters/zoffy/stage1/cells/dash_light-02-cell.png` | `art/fighters/zoffy/stage1/dash_light/frames/dash_light-02-raw.png` | (17,44,152,183) | 140×136 | 32 | 1 | 0/255 | 前冲低姿 |
| `dash_light-03` | `art/fighters/zoffy/stage1/cells/dash_light-03-cell.png` | `art/fighters/zoffy/stage1/dash_light/frames/dash_light-03-raw.png` | (35,34,189,183) | 150×155 | 32 | 1 | 0/255 | 冲拳 |
| `dash_light-04` | `art/fighters/zoffy/stage1/cells/dash_light-04-cell.png` | `art/fighters/zoffy/stage1/dash_light/frames/dash_light-04-raw.png` | (58,34,135,183) | 150×78 | 32 | 1 | 0/255 | 直立护架 |

### dash_heavy（6 帧，冲刺飞踢）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `dash_heavy-00` | `art/fighters/zoffy/stage1/cells/dash_heavy-00-cell.png` | `art/fighters/zoffy/stage1/dash_heavy/frames/dash_heavy-00-raw.png` | (42,35,144,183) | 149×103 | 32 | 1 | 0/255 | 直立护架 |
| `dash_heavy-01` | `art/fighters/zoffy/stage1/cells/dash_heavy-01-cell.png` | `art/fighters/zoffy/stage1/dash_heavy/frames/dash_heavy-01-raw.png` | (91,1,189,183) | 183×99 | 32 | 1 | 0/255 | 起跳 |
| `dash_heavy-02` | `art/fighters/zoffy/stage1/cells/dash_heavy-02-cell.png` | `art/fighters/zoffy/stage1/dash_heavy/frames/dash_heavy-02-raw.png` | (18,55,189,183) | 129×172 | 32 | 1 | 0/255 | 飞踢 |
| `dash_heavy-03` | `art/fighters/zoffy/stage1/cells/dash_heavy-03-cell.png` | `art/fighters/zoffy/stage1/dash_heavy/frames/dash_heavy-03-raw.png` | (9,72,183,183) | 112×175 | 32 | 1 | 0/255 | 飞踢 |
| `dash_heavy-04` | `art/fighters/zoffy/stage1/cells/dash_heavy-04-cell.png` | `art/fighters/zoffy/stage1/dash_heavy/frames/dash_heavy-04-raw.png` | (53,61,153,183) | 123×101 | 32 | 1 | 0/255 | 落地 |
| `dash_heavy-05` | `art/fighters/zoffy/stage1/cells/dash_heavy-05-cell.png` | `art/fighters/zoffy/stage1/dash_heavy/frames/dash_heavy-05-raw.png` | (58,28,135,183) | 156×78 | 32 | 1 | 0/255 | 直立护架 |

### vertical_light（4 帧，垂直跳短拳）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `vertical_light-00` | `art/fighters/zoffy/stage1/cells/vertical_light-00-cell.png` | `art/fighters/zoffy/stage1/vertical_light/frames/vertical_light-00-raw.png` | (48,52,130,183) | 132×83 | 32 | 1 | 0/255 | 蹲姿起手 |
| `vertical_light-01` | `art/fighters/zoffy/stage1/cells/vertical_light-01-cell.png` | `art/fighters/zoffy/stage1/vertical_light/frames/vertical_light-01-raw.png` | (80,10,154,183) | 174×75 | 32 | 1 | 0/255 | 起跳 |
| `vertical_light-02` | `art/fighters/zoffy/stage1/cells/vertical_light-02-cell.png` | `art/fighters/zoffy/stage1/vertical_light/frames/vertical_light-02-raw.png` | (75,21,167,183) | 163×93 | 32 | 1 | 0/255 | 空中短拳 |
| `vertical_light-03` | `art/fighters/zoffy/stage1/cells/vertical_light-03-cell.png` | `art/fighters/zoffy/stage1/vertical_light/frames/vertical_light-03-raw.png` | (65,45,131,183) | 139×67 | 32 | 1 | 0/255 | 落地 |

### vertical_heavy（5 帧，垂直跳下砸拳）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `vertical_heavy-00` | `art/fighters/zoffy/stage1/cells/vertical_heavy-00-cell.png` | `art/fighters/zoffy/stage1/vertical_heavy/frames/vertical_heavy-00-raw.png` | (57,61,135,183) | 123×79 | 32 | 1 | 0/255 | 蹲姿起手 |
| `vertical_heavy-01` | `art/fighters/zoffy/stage1/cells/vertical_heavy-01-cell.png` | `art/fighters/zoffy/stage1/vertical_heavy/frames/vertical_heavy-01-raw-2.png` | (81,43,131,183) | 141×51 | 31 | 1 | 0/255 | 起跳 |
| `vertical_heavy-02` | `art/fighters/zoffy/stage1/cells/vertical_heavy-02-cell.png` | `art/fighters/zoffy/stage1/vertical_heavy/frames/vertical_heavy-02-raw.png` | (44,15,139,183) | 169×96 | 32 | 1 | 0/255 | 空中蓄力 |
| `vertical_heavy-03` | `art/fighters/zoffy/stage1/cells/vertical_heavy-03-cell.png` | `art/fighters/zoffy/stage1/vertical_heavy/frames/vertical_heavy-03-raw.png` | (64,22,124,183) | 162×61 | 32 | 1 | 0/255 | 下落 |
| `vertical_heavy-04` | `art/fighters/zoffy/stage1/cells/vertical_heavy-04-cell.png` | `art/fighters/zoffy/stage1/vertical_heavy/frames/vertical_heavy-04-raw.png` | (53,69,136,183) | 115×84 | 32 | 1 | 0/255 | 落地 |

### air_crush（6 帧，空中双拳下砸）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `air_crush-00` | `art/fighters/zoffy/stage1/cells/air_crush-00-cell.png` | `art/fighters/zoffy/stage1/air_crush/frames/air_crush-00-raw.png` | (76,1,136,183) | 183×61 | 31 | 1 | 0/255 | 起跳 |
| `air_crush-01` | `art/fighters/zoffy/stage1/cells/air_crush-01-cell.png` | `art/fighters/zoffy/stage1/air_crush/frames/air_crush-01-raw-2.png` | (80,48,132,183) | 136×53 | 32 | 1 | 0/255 | 空中蓄力 |
| `air_crush-02` | `art/fighters/zoffy/stage1/cells/air_crush-02-cell.png` | `art/fighters/zoffy/stage1/air_crush/frames/air_crush-02-raw.png` | (76,2,165,183) | 182×90 | 32 | 1 | 0/255 | 空中下砸 |
| `air_crush-03` | `art/fighters/zoffy/stage1/cells/air_crush-03-cell.png` | `art/fighters/zoffy/stage1/air_crush/frames/air_crush-03-raw.png` | (75,31,136,183) | 153×62 | 31 | 1 | 0/255 | 空中下压 |
| `air_crush-04` | `art/fighters/zoffy/stage1/cells/air_crush-04-cell.png` | `art/fighters/zoffy/stage1/air_crush/frames/air_crush-04-raw.png` | (50,58,140,183) | 126×91 | 32 | 1 | 0/255 | 落地 |
| `air_crush-05` | `art/fighters/zoffy/stage1/cells/air_crush-05-cell.png` | `art/fighters/zoffy/stage1/air_crush/frames/air_crush-05-raw.png` | (57,30,137,183) | 154×81 | 32 | 1 | 0/255 | 直立护架 |

### dive（5 帧，俯冲脚跟踢）

| 帧 | 成品 PNG | 源 raw | bbox | 高×宽 | 色数 | 块 | Alpha | 姿势 |
|---|---|---|---|---|---:|---:|---|---|
| `dive-00` | `art/fighters/zoffy/stage1/cells/dive-00-cell.png` | `art/fighters/zoffy/stage1/dive/frames/dive-00-raw.png` | (61,38,132,183) | 146×72 | 32 | 1 | 0/255 | 起跳 |
| `dive-01` | `art/fighters/zoffy/stage1/cells/dive-01-cell.png` | `art/fighters/zoffy/stage1/dive/frames/dive-01-raw.png` | (66,61,189,183) | 123×124 | 32 | 1 | 0/255 | 俯冲 |
| `dive-02` | `art/fighters/zoffy/stage1/cells/dive-02-cell.png` | `art/fighters/zoffy/stage1/dive/frames/dive-02-raw.png` | (2,14,156,183) | 170×155 | 32 | 1 | 0/255 | 俯冲脚跟踢 |
| `dive-03` | `art/fighters/zoffy/stage1/cells/dive-03-cell.png` | `art/fighters/zoffy/stage1/dive/frames/dive-03-raw.png` | (27,59,189,183) | 125×163 | 32 | 1 | 0/255 | 踢击接触 |
| `dive-04` | `art/fighters/zoffy/stage1/cells/dive-04-cell.png` | `art/fighters/zoffy/stage1/dive/frames/dive-04-raw.png` | (59,39,134,183) | 145×76 | 32 | 1 | 0/255 | 落地护架 |

## 比例与造型核验

银头部按同一口径量：主体内近白（RGB 各 >135、通道差 <40）最大连通块，取人物上部 28% 区域；锚与候选同法。锚为 23×32。直立护架抽样：

| 帧 | 银头部宽×高 | 与锚差 |
|---|---:|---|
| idle-00（锚） | 23×32 | 基准 |
| light1-00 | 24×33 | +1/+1 |
| light2-00 | 23×32 | 0/0 |
| light3-00 | 16×33 | 16 为冠/耳分割读数，目视头宽正常 |
| heavy-00 | 23×32 | 0/0 |
| spin_heavy-00 | 23×32 | 0/0 |
| crush-00 | 25×34 | +2/+2 |
| tackle-00 | 24×32 | +1/0 |
| dash_light-00 | 24×35 | +1/+3 |
| dash_heavy-00 | 24×33 | +1/+1 |
| air_crush-05 | 24×33 | +1/+1 |
| dive-04 | 25×34 | +2/+2 |

- 结论：直立护架头宽 23–25 px、头高 32–35 px，与锚 23×32 同档；没有只缩头、保留肥大手脚或厚重肩甲的迹象。四肢粗细、肩甲体量与锚目视一致。`light3-00` 的 16 px 是银色面部被红色冠脊分割造成的读数，原大目视为正常头宽。
- 站高：攻击帧的屈膝、跨步、腾空会自然改变外框高度；同一比例下直立护架约 148–157，低姿/腾空帧 112–183。没有逐帧拉伸，未把压低姿势拉回 154。`stage_cells.py` 的 `head_height` 启发式在护架/举拳帧会失真（读数 9–54），本报告不拿它当门限，只用上面的银头部同口径测量和目视审片。

### 横向最小平移

7 帧的伸展姿势按脚底带对齐会越出 192 格；仅做水平平移（不缩放、不改基线），保留 2 px 边距。其余 101 帧按 standard 脚底带对齐在原位。

| 帧 | 终宽 | 原偏移 | 平移后 | 原因 |
|---|---:|---:|---:|---|
| `tackle-02` | 131 | 87 | 59 | 前冲腾跃，前伸轮廓越过右缘 |
| `dash_light-01` | 116 | 84 | 74 | 前冲直拳，右缘超出 8 px |
| `dash_heavy-02` | 172 | 21 | 18 | 飞踢，右缘超出 1 px |
| `dive-01` | 124 | 89 | 66 | 横向俯冲，右缘超出 21 px |
| `dive-02` | 155 | -38 | 2 | 俯冲踢，底部脚带偏右导致左缘超出 38 px |
| `dive-03` | 163 | 31 | 27 | 踢击接触，右缘超出 2 px |
| `dash_light-03` | 155 | 37 | 35 | 冲拳贴右缘，留 2 px 边距 |

- 这 7 帧的根点 x 与 96 的偏差是刻意的完整性修正，逐帧登记；没有用缩小人物或裁轮廓换取入格。运行时若需要严格固定根点，由安装时的根点偏移/动作位移吸收。
- 腾空帧全部按脚底 183 落格（与已签 `jump`/`air` 格一致）；竖直腾空高度不由画面烘焙，留给动画层。`--air` 只影响站高提示，不改变像素；本报告按姿势列标注非直立帧。

## 重生成与淘汰

共 11 个候选被淘汰，均已删除；下表保留尺寸、实心高、SHA256 前 16 位与原因。被拒文件不在 `cells.json`、manifest 或其它工具的动态路径中。

| 文件（`art/fighters/zoffy/stage1/` 下） | 画布 | 实心高 | SHA256 前 16 | 原因 |
|---|---|---:|---|---|
| `light1/frames/light1-00-raw.png` | 1254×1254 | 921 | `8d78e001e5036fa3` | 护架站高偏低（落格约 144），重生成 v2 972 |
| `light1/frames/light1-01-raw.png` | 1246×1262 | 958 | `5dfa47c6313645b4` | 头肩/四肢比例与锚不符，重生成 |
| `light1/frames/light1-01-raw-2.png` | 1247×1261 | 872 | `615fb0ba11213bba` | 头肩/四肢比例与锚不符，重生成 v3 921 |
| `light2/frames/light2-00-raw.png` | 1199×1312 | 1033 | `be78ddec92db6485` | 护架偏高（落格约 162），重生成 v2 1005 |
| `light2/frames/light2-01-raw.png` | 1199×1312 | 1014 | `aa1f16381d81d023` | 头肩/四肢比例与锚不符，重生成 v2 934 |
| `light2/frames/light2-02-raw.png` | 1199×1312 | 989 | `6abd87541f3abeed` | 头肩/四肢比例与锚不符，重生成 v2 972 |
| `launcher/frames/launcher-03-raw.png` | 1024×1536 | 1236 | `1832043101fa11a5` | 实心高 1236，落格约 194 px 超出 192 格，重生成 v2 965 |
| `crush/frames/crush-02-raw.png` | 1024×1536 | 1340 | `a656663cd24bedd7` | 实心高 1340，落格约 210 px 超出 192 格，重生成 v2 986 |
| `vertical_heavy/frames/vertical_heavy-01-raw.png` | 1024×1536 | 1291 | `5b87d52cac7079f1` | 实心高 1291，落格约 202 px 超出 192 格，重生成 v2 900 |
| `air_crush/frames/air_crush-01-raw.png` | 1024×1536 | 1232 | `d869636423c760c3` | 实心高 1232，落格约 193 px 超出 192 格，重生成 v2 868 |
| `slide/frames/slide-07-raw.png` | 1199×1312 | 1015 | `57dfd14f9789a4b7` | 回架偏高（落格约 159），重生成 v2 939 |

另有 3 帧为本轮新增而非替换：`dive-02`、`dive-03`、`dive-04`（俯冲后三帧）。`light1-00`、`light2-00`、`slide-07` 的旧候选也计入上表。淘汰后每 clip 只保留选定 raw 与成品 cell。

## 怎么看

- 直接打开 `art/fighters/zoffy/stage1/cells/`，按 clip 顺序看 `<clip>-00-cell.png` 起，首尾护架应与相邻 clip 的护架衔接；全部为 192×192 原大，未缩放。
- 对照身份锚 `art/fighters/zoffy/stage1/cells/idle-00-cell.png` 看头宽、肩甲体量、手臂和大腿粗细；站高会随屈膝/腾空变化，不拿站高当比例尺。
- 逐帧路径、bbox、色数、连通块、Alpha 和姿势见上表；被拒候选的原因和尺寸见「重生成」。
- 本轮无录屏；没有 Godot 实机、720/1080 或双朝向验证（本批只做美术帧）。

## 已知问题

1. `art/fighters/zoffy/stage1/cells/cells.json` 未修改（任务禁止改 JSON）。它仍记录旧的 light1/light2/light3/heavy 帧与旧 SHA；同名新 PNG 已覆盖。安装/接运行时前必须由后续任务统一更新 `cells.json`、manifest 与动画数据，不能把现在的 JSON 当新帧清单。
2. 108 与 106 的差异：逐 clip 要求为 5+5+6+7+7+7+9+8+4+7+8+4+5+6+4+5+6+5=108；本批按逐 clip 执行，未删减到 106。
3. 7 帧做了水平最小平移（见上表），根点 x 与 96 有 2–40 px 偏差；这是为了完整人物不裁切。若后续要求严格固定根点，需在安装层用根点偏移吸收，或把这 7 帧改成更紧凑的姿势重生成。
4. 腾空帧的竖直高度未烘焙，全部脚底 183；运行时需由动画层给跳跃高度。若安装层不抬升，画面会像贴地，这是已知约定，不是本批漏做。
5. 银头部自动测量对冠脊分割、举臂遮挡敏感；本报告用直立护架抽样 + 目视审片，未把自动头高读数写成硬门通过。
6. 未做实机验证：没有 Godot 导入、没有 720/1080、没有双朝向检查。旧 `raw-00.png`、`raw-01-v1.png` 等 11 月 9 日前的历史候选未动，不属于本批。

## 下一步

- 由安装任务把这 108 帧接入 `content/fighters/zoffy` 的动作/manifest，更新 `cells.json` 与动画根点；处理 7 帧水平偏移和腾空帧竖直偏移。
- 接入后用主游戏训练/F1 做一次实机检查（两个朝向、720/1080），确认护架接续、命中相位与镜头；本轮不冒充已完成实机。


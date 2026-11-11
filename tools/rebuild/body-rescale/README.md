# 体型重落格（2026-11-11）

任务：七名新装角色屏幕可见站高偏离官方身高设定，按官方身高重推 scale
重落全部已装 stage1 战斗格。纯数据修复，不重新生成美术。

## 官方身高来源（2026-11-11 查证，円谷官方页直接复核）

| 角色 | 官方身高 | 来源 |
| --- | --- | --- |
| 奥特之王 | 58m | https://m-78.jp/character/king 、https://en.tsuburaya-prod.co.jp/heroes/ultraman-king |
| 奥特之父 | 45m | https://m-78.jp/character/father 、https://en.tsuburaya-prod.co.jp/heroes/father-of-ultra |
| 赛罗 | 49m | https://tsuburaya-prod.com/heroes/ultraman-zero |
| 杰斯提斯 | 46m | https://tsuburaya-prod.com/heroes/ultraman-justice |
| 佐菲 | 45m | https://tsuburaya-prod.com/heroes/zoffy |
| 盖亚（V2 同 V1 身高） | 50m | https://tsuburaya-prod.com/heroes/ultraman-gaia |
| 奥特之母 | 40m | https://m-78.jp/ultraheros/mother/ 、https://tsuburaya-prod.com/heroes/mother-of-ultra |

基线锚：初代 ultraman 140px=40m（m-78.jp/character/ultraman），即 3.5 px/m。
注意：任务背景原给 zero 47m / justice 47m / gaia 43m 与官方页不符，按官方
页为准（zero 49m、justice 46m、gaia 50m）；justice/zoffy/gaia 实际是放大
不是缩小。

## 推导

新 scale = 旧 scale × (目标站高 / 现测站高)。目标 = official_m × 3.5，
现测为重落前 idle 帧 1:1 native 屏幕可见站高。

## 落格口径

- 每角色沿用原批次缩放算法：king/zero/justice/mother = forge_backend
  `_kcentroid_downscale`（oracle 逐像素 99.7% 一致实测），father/gaia/zoffy = BOX。
- 放置统一按旧 cell 内容绕根点等比映射：新 bbox 中心 = 锚 + (旧中心−锚)×ratio；
  新脚行 = baseline−1 − (旧 baseline−1 − 旧脚行)×ratio。旧 cell 已编码各批次
  放置决策（脚带重心/主体中心/胸灯对齐/横卧居中），等比映射对所有口径通用。
  oracle 实测 king 490/495、其余角色见各 oracle-*.txt。
- 格：justice/zoffy/gaia 192→256（放大后部分帧超 192，按 AGENTS「本角色统一
  增大格并登记」）；king/zero 保持 256；father/mother 保持 192。
- 源帧解析：json 显式映射（SHA+尺寸±2px 校验；json 记录的主仓库绝对路径
  自动映射到本仓库根）→ 组内 IoU≥0.97 反查 → 0.90–0.97 近似源（登记 flags）→
  <0.90 无源帧：对旧 cell 可见内容本身按 ratio 绕根点等比变换（升格角色
  必须如此，否则 install 的 build_atlas 会把旧 192 格拉伸到 256 造成错位；
  同格角色原样保留）。
  少量帧旧源被后续重掷覆盖且未回填记录，按无源处理。
- 缩放产生的 <3px 孤点残粒（与主体断连）在非技能帧落格后清理
  （father air_rise-00/back_counter-00 各 1px）。
- 节奏配合：state_frames 的节奏展开（74f99d6f5）条目数/sprite 序列/dx/dy/
  cancel/events 一律保留，仅逐 sprite 按重落图集重算 hurtboxes
  （recalc_hurtboxes.py，同 sprite 重复条目原值一致，复用安全）；
  不得用 derive --states-only 覆盖（会把节奏版打回「每 rect 一条目」）。

## 用法

```bash
.venv/bin/python tools/rebuild/body-rescale/rescale_cells.py --list
.venv/bin/python tools/rebuild/body-rescale/rescale_cells.py --fighter ultraman-king --oracle
.venv/bin/python tools/rebuild/body-rescale/rescale_cells.py --fighter ultraman-king
```

逐角色报告在同目录 `<fighter>-rescale.json`（含逐帧 bbox/脚行/腾空量/连通块/色数
与 flags）。重落后按组重装并重算受击框：

```bash
.venv/bin/python tools/art/install_cells.py --fighter <角色> --merge
.venv/bin/python tools/rebuild/body-rescale/recalc_hurtboxes.py --fighter <角色> --write
```

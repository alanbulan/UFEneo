# 赛罗基本红蓝形态 · 来源审计（2026-11-12，I1 新增）

本轮只新增身份色板总控交付与本审计；不改 `identity_card.json`、`cells.json`、assets 或运行时资源。无录屏、未听审、未冒称用户亲审；`root_delegated_by_user` 由根自签。未 commit，未跑 Godot/verify，未动锁，未打印/复制/提交凭据。

## 侧视来源与前后判据

- 圆谷官方 Zero15 新闻页：`https://tsuburaya-prod.com/news/7732`，2026-11-09 原下载、2026-11-12 复检，页面 HTTP 200；原图 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-zero/sources/tsuburaya-zero15-2024/official-cheki.jpg`，图片直链 `https://tsuburaya-prod.com/wp-content/uploads/2024/09/zero15_cheki_img.jpg`，SHA `226ca50e9ddb547580a87af8b318c54b9a91286f66685e7d7db8a352c2316464`，1920×1279 RGB。
- 头部近侧脸裁图：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-zero/stage1/idle/references/zero-side-head-official.png`，SHA `a44cce4451a1849d2f59016e22ee8d19d51fb02dcc4bb122defe8c3d87f54741`，390×510 RGB，290390 bytes。来源类型 `official_press_photo_crop`；facing=朝右；angle 是右侧近侧脸（头部与上胸），不是全身 90° 侧视，只核双头镖前后结构，不取全身比例或站姿。
- 本机网格审片：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/reports/review/2026-11-12/I1-zero-side-grid-20261112.png`，SHA `3a733940a5ac7a04f6507628c81778f08bffeac61582601ea30e736073db5e22`，780×1020；另有本机侧视搜索联系表 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/reports/review/2026-11-12/I1-zero-side-search-02-contact-20261112.jpg`，SHA `356cf79edb7dfaa879895f89cca708655bc1dce48726a1247d72ec92a27e2244`。
- 同口径 x 判据：朝右时 x 大为前、x 小为后；黄色眼亮块 x 均值约 276.8（bbox x258–300），两枚后上掠刃尖 x 均值约 136.1 / 165.3，宽刃根/前缘 x 均值约 290.5，银刃后缘约 308.3。刃尖 x < 眼列 x，刃根/前缘约在眼列附近且不低于眼；不得取整帧 Alpha 最高行、不得混入正面/3/4 图。`identity_card.json` 原 `front_back_criterion` 未把眼列/刃尖/刃根定义写成同一口径，已在 `identity_ready.json` 修正，未改只读卡片。
- 侧视来源限制：官方头部近侧脸，不是全身 90° 侧视；任务允许如实标为近侧视。此来源只用于标志结构前后判据。

## 待机像素整帧、审片与色板

- 现用锚：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-zero/stage1/idle/frames/identity-idle-pixel.png`，SHA `c36397a86bff3f6e1469e7efd611dad20ff4938bec30b03c703c9095c0e5df0f`，7425 bytes，256×256 RGBA，Alpha 仅 `[0,255]`，32 个可见颜色；RGB 棋盘格不算透明，本文件为真透明。
- 严格 4×：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-zero/stage1/idle/frames/identity-idle-pixel-x4.png`，SHA `fb5f5687dace8024638d258282c734d58325d54fc07e8143375d6d3a28803ebc`，1024×1024；16 个 block offset 逐像素一致，最近邻降采样与锚 RGBA 完全相同。
- 本机原生格/4× 审片：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/reports/review/2026-11-12/I1-three-anchor-native-and-x4-20261112.png`，SHA `ffe43c753ea9544465785b73a7cc4577680d9d7cc247189e73479b59ae852929`。实看格斗待机：分脚、屈膝、双拳胸前护架；头肩比例与手脚体量可读，无裁切/断肢。站距 0.6809（bbox `[57,60,185,248]`、站高 188、脚外缘 128 px）在区间 0.65–0.80；站距/色数/Alpha 不冒充造型通过。
- `model/identity-anchor-x4.png` 实测 144×752、原生宽 36 px <60 px，登记为不得单独作动作参考。
- 冻结色板来自现用待机整图 alpha>0 颜色，恰好 32 色；`identity_card.json` 的 `frozen_palette.colors` 与实际文件集合一致（顺序不同）。识别色逐项像素数与位置见 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-zero/stage1/rework-20261112/frozen_palette.json`：蓝额灯/计时器四色在胸灯区、黄眼五色在面罩黄眼区、绿色额灯候选四色在头部区；不把胸前蓝色误写成头部灯。装机 idle/atlas.png SHA `1e2ce6a7ec46f21de0b981d6f001d54ae401b47cd53b76aedd3a334e7b75ffd7` 为同色板 31 色子集，不是缺口。

## 尺度与逐 clip 口径

- 唯一 scale `0.158767`，装机站高 172；`cells.json` 早期 `target_standing_height=188` 是锚原生站高，不作返工尺度。
- 只读 `assets/fighters/ultraman-zero/animations/manifest.json` 实际 113 clips 为 256 格 / anchor `[128,248]`，`air_special` 1 clip 为 288 格 / `[128,248]`；manifest 顶层 `[288,288]` 不是全部 clip 的共同尺寸。逐 clip 取自身 `cell/anchor/rects/ticks`，不用第一组缩放其余组，不回落顶层旧 anchor。

## 本轮新增文件

- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-zero/stage1/rework-20261112/identity_ready.json`
- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-zero/stage1/rework-20261112/frozen_palette.json`
- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-zero/stage1/rework-20261112/source_audit.md`
- 未新增赛罗 `sources/` 文件；沿用已核官方来源与既有 `source.json`。本轮未调用 MCP 生图。

## 结论与已知限制

`ready=true`，但仅代表身份色板总控三项硬条件在本机复算和本机审片中闭合。官方侧视是头部近侧脸而非全身 90°；无实机双朝向/720/1080 画面、无录屏、未听审、未用户亲审；不能以本文件代替实机验收。

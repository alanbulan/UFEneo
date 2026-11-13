# 杰斯提斯标准型 · 来源审计（2026-11-12，I1 新增）

本轮只新增身份色板总控交付、独立侧视复检目录与 `source.json`、以及本审计；不改只读诊断 `identity_card.json`、`cells.json`、assets 或运行时资源。无录屏、未听审、未冒称用户亲审；`root_delegated_by_user` 由根自签。未 commit，未跑 Godot/verify，未动锁，未打印/复制/提交凭据。

## 侧视检索与来源复检

- Animage Plus 文章页 `https://animageplus.jp/articles/detail/34533` 与分页 `https://animageplus.jp/articles/detail/34533/2/1/1`：2026-11-09 原记录与 2026-11-12 WebFetch 复检均 HTTP 403，不绕过、不冒充圆谷官网页面可读。
- 图片直链 `https://images.animageplus.jp/articles/34000/34533/OG/a66241cd533e6a733a6312a188b214b4.jpg`：HTTP 200 `image/jpeg`，2026-11-12 重下并逐字节核对。
- 新独立来源目录：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-justice/sources/side-verify-2026-11-12/`，含 `justice-standard-ugf-tac-group-right-profile-01.jpg` SHA `99562412d2203bf29525b450105f3eac3a008ff961af4c7c6e9a1bb5ac37c6a4`、1244732 bytes、5679×3189 RGB，及 `source.json`。`source_type=official_production_still_media_reprint`：带 ©TSUBURAYA PRODUCTIONS 水印的媒体转载官方剧照，文章页不是圆谷官方页面。响应头旧记录 `last-modified 2020-12-10`；文章发布日期未由 403 页面核出，写 `article_date=null`，不虚构。
- 圆谷官方角色页 `https://tsuburaya-prod.com/heroes/ultraman-justice` 四张 Standard Mode 图只作身份交叉核：`official-standard-01` 正面直立、`02` 正面偏 3/4 格斗架势、`03` 3/4 侧身动作（只核头冠/面罩侧面轮廓）、`04` 正面大跨步；均不冒充 90° 侧视。WebSearch `site:tsuburaya-prod.com` 与英文 Standard Mode side view 检索未找到可替代的圆谷官方 90° 侧视。
- 头颈裁图：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-justice/stage1/idle/references/justice-side-head-ugf-head-neck.png`，SHA `01742fc9ff59ff458a7884aa7a30483014adf23ffd0558c208133833ea2e4073`，710×830 RGBA，原图裁框 `[950,420,1660,1250]`；facing=朝右，头部近纯 90° 右侧视，身体仍略向镜头转 20–30°，脚/靴被原图下缘裁掉，不取全身比例/站姿/颜色。
- 本机网格审片：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/reports/review/2026-11-12/I1-justice-side-grid-20261112.png`，SHA `1e09b3438af9cd326f0a707b714c58aea440af2ac5cf1543cec1118e625989b1`。另本机三角色锚审片 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/reports/review/2026-11-12/I1-three-anchor-native-and-x4-20261112.png`，SHA `ffe43c753ea9544465785b73a7cc4577680d9d7cc247189e73479b59ae852929`。
- 同口径 x 判据：朝右时 x 大为前、x 小为后；眼列取过曝眼亮块 x 均值约 504.9（只取轮廓），冠尖/冠顶亮区 x 约 284.5、冠中部约 267.5、冠后缘约 181.7，面罩/下颌前缘 x 约 538.2。冠尖与冠后缘 x < 眼列 x，冠体从眼列后方向上伸展，面罩/下颌前缘 x > 眼列 x；眼过曝不取颜色，额灯蓝/青绿颜色不从该侧视裁图读取，不取整帧最高行，不混入正面/3/4 图。

## 待机像素整帧、SHA 链与色板链

- `identity_card.json` 当前引用 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-cell.png`：SHA `f9de9f2d193bc0dd57a5eee3bb9402647ca444e98b6fd47368040897a6ba628b`，5924 bytes，256×256 RGBA，Alpha 仅 `[0,255]`，32 个可见颜色；站距 0.6832（bbox `[70,87,180,248]`、站高 161、脚外缘 110 px），格斗待机架势可读。它是后续重标定/落格件，不是 README 签署的 192×192 原生像素锚。
- 严格 4× `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-x4.png`：SHA `d13bcf04d4b3211d73bd63147facd76b44652fb172c68f19b9968e4fad352d2d`，10626 bytes，768×768，26 色，含青绿三色共 128 个 4× 像素；对该 4× 最近邻降采样到 192×192 并保存 PNG，得到 README 所记 SHA `e1dbeeabb86a8256de833b92b5f24b30fffc45a8b91b121ff06d5594156df00d`（4707 bytes）。全仓按 SHA 查找没有该字节文件，故签署 192 原生锚可重建但磁盘链断。
- 当前 256 与 4× 色板交集为 0，Alpha IoU 约 0.2421；当前 256 严格上/下采样与 4× 推导 192 的 Alpha IoU 约 0.2403，不是同一锚的缩放件。
- `cells.json approved_sha256=924c2aab9395217364600579ffdd23f44fc262f2865f3ec44ef2ebe539991989` 实测为 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/assets/fighters/ultraman-justice/catalogue/model-native.png`，384×256、6919 bytes，是图鉴件，不是动作身份锚。`cells.json` 也未保存完整 32 色板数组。
- 装机 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/assets/fighters/ultraman-justice/animations/idle/atlas.png` SHA `d2ab7f803efb15b8ef92fc2ab92a2ca10ab9d369791054db9be99850b7c1c34b`，与 `idle-01-cell.png` 同 SHA，28 色，青绿三色像素数 0；当前 256 锚青绿三色像素数也为 0。旧图鉴色板吞掉青绿额灯/胸灯，不满足 ready 条件 (c)。
- 修复候选：从 449 张仍含青绿三色的签署动作 4× 图（768×768）取 alpha>0 颜色并集，复算完整 32 色（含 `(2,177,172)`、`(14,204,199)`、`(15,143,127)`）。该色板只登记为候选，不是当前现用待机整图的冻结色板；未执行新映射、未改图、未局部重涂。完整列表、签署 4× 26 色与逐项像素数见 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-justice/stage1/rework-20261112/frozen_palette.json`。
- `model/identity-anchor-x4.png` 实测 152×616、原生宽 38 px <60 px，不得单独作动作参考。

## 尺度与逐 clip 口径

- 唯一 scale `0.161972`，装机站高 161。只读 `assets/fighters/ultraman-justice/animations/manifest.json`：103 clips 为 256/[128,248]，1 clip `air_special` 为 288/[128,248]，4 clips（`chase_takeoff`、`defeat`、`vertical_jump`、`victory`）为 192/[96,184]；manifest 顶层 `[288,288]` 不作共同尺寸。逐 clip 取自身 `cell/anchor/rects/ticks`。

## 本轮新增文件

- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-justice/sources/side-verify-2026-11-12/justice-standard-ugf-tac-group-right-profile-01.jpg`
- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-justice/sources/side-verify-2026-11-12/source.json`
- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-justice/stage1/rework-20261112/identity_ready.json`
- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-justice/stage1/rework-20261112/frozen_palette.json`
- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-justice/stage1/rework-20261112/source_audit.md`
- 本轮未调用 MCP 生图，未恢复或生成新待机帧。

## 结论与 blockers

`ready=false`。必须先恢复 `e1dbee…` 192×192 签署原生文件，或从新待机整图回源重建；以含青绿双灯的完整 ≤32 色板整图统一映射，核锚 SHA、字节、尺寸、真 Alpha、青绿像素数、严格 4× 与逐 clip 尺度后，才重判 ready。无录屏、未听审、未用户亲审；不能把本机审片写成实机验收。

# 盖亚奥特曼 V2 · 来源审计（2026-11-12，I1 新增）

本轮只新增真实侧视检索来源目录与 `source.json`、身份色板总控交付及本审计；不改只读 `identity_card.json`、`cells.json`、assets 或运行时资源。无录屏、未听审、未冒称用户亲审；`root_delegated_by_user` 由根自签。未 commit，未跑 Godot/verify，未动锁，未打印/复制/提交凭据。

## 侧视检索过程与采用来源

- 起点：`identity_card.json` 的 `official_side` 全为 null；圆谷官方 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/sources/official-pose-20261109-hero/hero_gaia-1.png` SHA `9c245f9d736271ce51bc9bbf602b6ac3ea6c6aae6059ebbee80b281feea24cb2` 是 V2 正面中立；`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/sources/ref-01.webp` SHA `a8657c4e6c2df00574b64f3ed1141d6e1aea67b9918a3683c1f1db4a8dd514ee` 是正面偏 3/4 格斗架势，均不可作 90° 侧视。
- WebSearch/WebFetch 首先检索 `site:tsuburaya-prod.com` 盖亚 V2 侧视及圆谷官方角色页；未找到可读的真实 90° 侧视。圆谷官网角色页 `https://tsuburaya-prod.com/heroes/ultraman-gaia` 只提供 V2 正面身份照。
- 万代魂官方商品页 `https://tamashiiweb.com/item/14684/?wovn=en`（Release Date 2024-06-22）8 张商品图全部 HTTP 200、逐张下载做联系表 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/reports/review/2026-11-12/gaia-v2-tamashii-contact-20261112.jpg`（SHA `6c026a7828034d1d615969b9acab0833da25a29a421e0b91986916105ad0eeb1`）；实看均为正面/3/4/动作/头部近景，无严格 90° 侧视。目录只留一张身份互证图 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/sources/tamashii-gaia-v2-2024/item_0000014684_s9394MN8_05.jpg`，SHA `df4b6e799ba78264257415b40e49b609878c514e5f3184e1fabf4ae08f321537`，1200×1107；其余 7 张为本请求自生成且未采用，按已核 SHA 逐一删除，未清理其它项目或历史来源。
- Kakaku.com 2021-03-29 海洋堂盖亚 V2 新闻页 `http://news.kakaku.com/prdnews/cd=pc/ctcd=0030/id=104743` 8 张图全部 HTTP 200 并做联系表 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/reports/review/2026-11-12/gaia-v2-kaiyodo-contact-20261112.jpg`（SHA `eaa2e72e074a84f3d2243873a18536623064df5dee1bc04ef7837c0504878d46`）；`kakaku-20210329-101.jpg` 为头部/上胸近侧视但额刃顶端被画幅裁掉，不能作完整刃尖前后判据。只留该辅助核图 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/sources/kakaku-kaiyodo-gaia-v2-2021/kakaku-20210329-101.jpg`，SHA `e590f2baaef5ac8b1b74638d7d248ad98a79fde08a6947dec76a87bdb0528e98`，900×675；其余 7 张按已核 SHA 删除。来源类型 `third_party_news_figure_photo`，不冒充官方皮套照。
- My Shiny Toy Robots 第三方评测页 `https://www.myshinytoyrobots.com/2024/08/SHF-Shinkocchou-Seihou-Ultraman-Gaia-V2.html`（2024-08-22）HTTP 200；解析 50 个大图 URL，下载 01–10 原尺寸图做角度联系表 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/reports/review/2026-11-12/gaia-v2-review-angle-scan-20261112.jpg`（SHA `85ba7c7dc987089d780839f52956395fd657f28a3737c76bc6649dfc890f9304`）。05 为真实 90° 全身/头部右侧视，金额刃、银头壳前缘、眼列、下颌及 V 字胸甲轮廓完整可读。
- 采用来源：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/sources/myshinytoyrobots-gaia-v2-2024/SH-Figuarts-Shinkocchou-Seihou-Ultraman-Gaia-v2-05.jpg`，SHA `68fac466d5835ccfc3b7eafab0714240e2639c9077dedd6c1feb2931b6f5fc47`，498922 bytes，1667×2500 RGB，facing=朝右，angle=真实 90° 右侧视；直链为 Blogger `.../s0/SH-Figuarts-Shinkocchou-Seihou-Ultraman-Gaia-v2-05.jpg`（完整 URL 写在该目录 `source.json`，2026-11-12 重下 HTTP 200 且 SHA 一致）。`source_type=third_party_figure_review_photo`、`official_provenance=false`：这是第三方评测拍摄的万代真骨雕商品，不是圆谷官方皮套照/剧照；只借金额刃与头壳前后轮廓，不取颜色、全身比例，球关节/插接缝/塑料高光不进入人物帧。
- 本机网格审片：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/reports/review/2026-11-12/I1-gaia-v2-side-grid-20261112.png`，SHA `01309455156c4c66339b6942ac02da63e79385e29b03c33ee9b7409b98586ed1`，700×800；本机三角色锚审片 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/reports/review/2026-11-12/I1-three-anchor-native-and-x4-20261112.png`，SHA `ffe43c753ea9544465785b73a7cc4577680d9d7cc247189e73479b59ae852929`。
- 同口径 x 判据：朝右时 x 大为前、x 小为后；同一 1667×2500 原图中，金色额刃 y100–160 / 160–220 / 220–280 三层可见金色像素 x 均值约 775.2 / 796.3 / 822.4，银前刃/刃根亮银像素 x 均值约 833.2，眼列浅黄/亮块 ROI x781–959,y281–419 的 x 均值约 885.2，面罩/下颌前缘约 x950–960。金额刃尖端/后掠端与银前刃 x 均小于眼列 x，额刃从眼列后方向后上掠；面罩/下颌前缘 x 大于眼列 x。不缩图换口径，不用整帧最高行，不拿正面或 3/4 图判侧视。
- `official_side` 旧卡片的「侧视 x 方向只作待核项，不写进生成规格」已由本轮真实 90° 侧视来源闭合；新判据写入 `identity_ready.json`，只读 `identity_card.json` 不覆盖。V2 无披风，已写入 `prompt_tail`，不得把披风写进生成提示词。

## 待机像素整帧、审片与色板

- 现用锚：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/stage1/idle/frames/identity-idle-pixel.png`，SHA `24da22f59292e1bd16ac8aae6231ddceeaa70623161784ac65f616f6de294d00`，8437 bytes，192×192 RGBA，Alpha 仅 `[0,255]`，32 个可见颜色；真透明，不是 RGB 棋盘格。
- 严格 4×：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/stage1/idle/frames/identity-idle-pixel-x4.png`，SHA `73f1690df4846b7e2b8a281dcc2fbc3fdf013cd12f25e5bb89829b6f08750fe9`，768×768；16 个 block offset 逐像素一致，最近邻降采样与锚 RGBA 完全相同。
- 本机原生格/4× 实看格斗待机：分脚、屈膝、双拳胸前护架；金额刃、浅黄眼、青蓝三角胸灯、黑金 V 字胸甲与红银 V2 躯体可读，无披风，无裁切/断肢。站距 0.6948（bbox `[37,30,144,184]`、站高 154、脚外缘 107 px），在区间 0.65–0.80；站距/色数/Alpha 不冒充造型通过。
- `model/identity-anchor-x4.png` 实测 108×616、原生宽 27 px <60 px，不得单独作动作参考。
- 冻结色板来自现用待机整图 alpha>0 颜色，恰好 32 色；`identity_card.json` 的 `frozen_palette.colors` 与实际文件集合一致（顺序不同）。识别色逐项像素数与位置见 `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/stage1/rework-20261112/frozen_palette.json`：金色额刃、浅黄眼、青蓝三角胸灯、黑金 V 字胸甲均保留；暗色全帧多处复用，胸甲位置按头部下方/胸前 V 区说明，不把全帧 bbox 当胸甲。装机 idle/atlas.png SHA `63c718e43140464c7142eefdc1513f907a4f575237033b8de7e498ad5f0ad418` 与锚同为 32 色。

## 尺度与逐 clip 口径

- 唯一 scale `0.169182`，装机站高 175。只读 `assets/fighters/ultraman-gaia/animations/manifest.json` 实际 104 clips 为 256 格 / anchor `[128,248]`，`air_special` 1 clip 为 288 格 / `[128,248]`；`cells.json` 与 manifest 顶层 `[96,184]` 是旧口径，与全部装机 clip 冲突。逐 clip 取自身 `cell/anchor/rects/ticks`，不得用顶层旧 anchor 或第一组尺寸缩放其余组。

## 本轮新增文件

- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/sources/tamashii-gaia-v2-2024/item_0000014684_s9394MN8_05.jpg`
- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/sources/tamashii-gaia-v2-2024/source.json`
- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/sources/kakaku-kaiyodo-gaia-v2-2021/kakaku-20210329-101.jpg`
- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/sources/kakaku-kaiyodo-gaia-v2-2021/source.json`
- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/sources/myshinytoyrobots-gaia-v2-2024/SH-Figuarts-Shinkocchou-Seihou-Ultraman-Gaia-v2-05.jpg`
- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/sources/myshinytoyrobots-gaia-v2-2024/source.json`
- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/stage1/rework-20261112/identity_ready.json`
- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/stage1/rework-20261112/frozen_palette.json`
- `/Users/wurulan/Developer/Projects/Game/ultraman-neo/art/fighters/ultraman-gaia/stage1/rework-20261112/source_audit.md`
- 本轮未调用 MCP 生图，未新增待机照片或像素整帧。

## 结论与 blockers

`ready=true`：真实 90° 右侧视来源、待机像素整帧锚与 ≤32 色板三项硬条件在本机复算及本机审片中闭合。已知限制是侧视来源为第三方手办评测实拍，不是圆谷官方；已如实标源类型、不冒充官方。`cells.json`/manifest 顶层旧 anchor 冲突只登记，不在本分片改运行时数据。无实机双朝向/720/1080 画面、无录屏、未听审、未用户亲审；不能以本文件代替实机验收。

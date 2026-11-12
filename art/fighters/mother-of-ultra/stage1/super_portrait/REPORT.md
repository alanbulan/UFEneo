# 奥特之母超必杀三级 CUT-IN 立绘报告

- fighter：`mother-of-ultra`
- 日期：2026-11-10
- 状态：`portrait-256.png` 已过硬门并由根安装到 `assets/effects/mother-of-ultra/super_portrait/atlas.png`。未做实机 720/1080 检查。

## 身份锚与官方来源

- 身份锚：`art/fighters/mother-of-ultra/stage1/cells/idle-candidate-01-cell.png`，192×192 RGBA，32色，Alpha 0/255，SHA `96ab6aa6cf19ca26b2ca9ce5981067e558f7e2d3f629e6655f9230d800ddcdf4`；cells.json 的 identity_anchor_for_actions，状态 `identity_anchor_signed_root_delegated_by_user`，`user_reviewed: false`。
- 生成用镜像 4× 锚：`super_portrait/references/anchor-x4-left.png`，768×768，SHA `fd7bc2e3fd15172ef2d05bc8006773a7a23ecf0fe66045b1577f7283f10f2e75`。
- 官方来源：`sources/official-figure-20261109/05-side-right.jpg`（1669×2500，SHA `9b5c1519683f9ebfd56a9a3e91072b0136ec36484f836ebbb250d6ea7ad3ed0d`，官方 S.H.Figuarts 第三方实拍真实右侧视，只取轮廓/角度，去球关节/接缝/塑料高光）；头胸裁图 `stage1/idle/references/figure-side-head-chest-05-right.png`（700×850，SHA `14bbb333cf4722be501b2f513e6ff3b1fa292e4f84b0eef6885d9cfb8db8de3f`），镜像后 `references/official-head-side-left.png`（SHA `f33d528397d562563d5392cad594d1a58e3f10bae34020a46106582d47b4e76d`）。`sources/official-tsuburaya-20261109/UT_Hero_mother02.png`（932×1400，SHA `c09674db1d049d0b4d16480ef7b50fad0f568072f67715eb02938f343dc21ab8`，官方正面全身，核女性体型/头冠/双辫）；`sources/ref-01.webp`（378×854，SHA `80f8a3f7719d18d5a19f8571dbcb9320de0041c69b78d7e59790ed0499210012`）。
- 方向：面朝左时头冠从额前向脑后上方掠起、尖端在后，额前冠缘有小红色三角饰，双辫自耳后垂下。

## 提示词（实际发送）

> 把参考图转成像素画腰部以上3/4胸像，面向画面左侧，双拳抬到胸前护架。奥特之母：女性肩胸体型，银色头冠从额前向脑后上方掠起、尖端在后方，额前有小红色三角饰，两条银色长辫自耳后垂下；黄眼、蓝胸灯、银红紧身衣与红披肩/裙摆；头身比例、手臂与拳头粗细同参考，不增肌不缩头。像素画硬边、有限色阶、保留识别色，透明背景，无地面、文字、边框、光效，人物完整不裁切。

参考图 2 张：镜像待机 4× 锚 + 镜像官方侧头裁图。

## 实收与 Alpha

- `image-65174-1467`，请求 1024×1024；实收 **1254×1254 RGBA**，Alpha 256 级、四角 0；raw SHA `0f7d33a37f0742799c452069ca6091ea451dc16662b818b81f911e4b974f6c9a`。真 Alpha；低 Alpha 光雾按 128 阈值剔除，非棋盘格。

## 后处理与硬门

- 命令：`.venv/bin/python -I tools/art/super_portrait_256.py --raw art/fighters/mother-of-ultra/stage1/super_portrait/portrait-1024-raw.png --palette-image art/fighters/mother-of-ultra/stage1/cells/idle-candidate-01-cell.png --out art/fighters/mother-of-ultra/stage1/super_portrait/portrait-256.png`
- 色板用现行待机锚 32 色：旧图鉴色板缺黄眼/蓝灯，映射会失去识别色，按 AGENTS 落格色板规则不硬套旧图鉴色板；整图统一映射。
- 硬门：256×256；Alpha `{0,255}`；可见 32 色；4 连通 1 块，最大 24160 px；bbox `[42,8,212,247]`，边距 42/8/43/8；冠、双辫、双拳、披肩完整，底边 8 px 透明。成品 SHA `d1789bf768af05e498df226e14de1296472e9b45a0f280741182a8c5d7321cb5`。识别色：黄眼 `(249,206,25)/(214,152,8)`，蓝灯 `(26,158,226)/(24,76,148)`。

## 方向核验

成品眼列 x=103.5；冠尖/后缘 x=113.5（后）；红三角 x=121.0、y=41.7（冠前缘上方，略在眼列后上方）；头部列带中心 114.5。已签锚（镜像左）：眼 328.9，冠顶带 325.5–339.5（横跨眼列并向脑后延伸），红三角 352.7。官方 05-side-right 原图朝右、镜像后与此同向；结论：头冠后掠、无前折，通过。

## 重生成与已知问题

- 1 次，0 次重生成；无剩余问题。
- 已安装 `assets/effects/mother-of-ultra/super_portrait/atlas.png`；未做实机 720/1080；无录屏、无听审。

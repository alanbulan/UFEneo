# 奥特之王超必杀三级 CUT-IN 立绘报告

- fighter：`ultraman-king`
- 日期：2026-11-10
- 状态：`portrait-256.png` 已过硬门并由根安装到 `assets/effects/ultraman-king/super_portrait/atlas.png`。未做实机 720/1080 检查。

## 身份锚与官方来源

- 身份锚：`art/fighters/ultraman-king/stage1/cells/idle-candidate-v18-cell.png`，256×256 RGBA，32色，Alpha 0/255，SHA `6914725c7cf01e0126432d403d30ffb1ff607db8070e6ebd03065dc72858f0c4`；cells.json 的 idle-candidate-v18-cell；签发依据见 `tools/rebuild/ultraman-king/README.md` 第二十一轮落新锚记录。
- 图鉴定稿：`assets/fighters/ultraman-king/catalogue/model-native.png`，384×256，32色，SHA `28e6491b9c4eaafa508dd087eb9e2d7d175d5ca375946da1bed3085dd886fae2`，与锚逐色一致。
- 生成用镜像 4× 锚：`super_portrait/references/anchor-x4-left.png`，1024×1024，SHA `15e6ea61dbabeaa76a269c380792b3f92e03d523d2710e084daaa721ec9b1200`。
- 官方来源：`sources/ref-02-side-head-upper.png`（440×450，SHA `aa2e2b7f014d926e1db90aa76b444e6cab1e8e0d17568c99ed10a45cbfdc0c26`，真实侧头近照，原图朝右，镜像后作生成参考 `references/official-head-side-left.png`，SHA `a05e33c0aba51bf38d17cba99489a4c883a30cda79858f4e8e2e073084c795e0`）；`sources/ref-03-side-full-uhs.jpg`（1080×1080，SHA `55d82250e03c0fe4ea2307b7b52010cd7b7b922c2dd38b861c034f21cfe44d5f`）；`sources/ref-04-front-full-official.png`（799×1200，SHA `7368fcc0f051bdcd14e4381917d884907331b959c04a29d709d8bf5c9c9a7237`）；`sources/ref-01.webp`（960×1558，SHA `cccc07b7333046c6671f2f29121168d7e7bcb534ac6ef8baa6802078a675a1e4`）。
- 方向规格（先按来源定死）：面朝左时冠球在额前上方前侧、梳齿朝前、冠刃向右后方后掠；已排除此前“后端小球”的反向写法。

## 提示词（实际发送）

> 把参考图转成像素画腰部以上3/4胸像，面向画面左侧，双拳抬到胸前护架。奥特之王：银色高冠，冠球在前额上方前侧、梳齿朝前，冠刃向画面右后方后掠；红色单眼、银白长须、金色肩甲、胸前红宝石、紫臂与红披风；头身比例、手臂与拳头粗细同参考，不增肌不缩头。像素画硬边、有限色阶、保留识别色，透明背景，无地面、文字、边框、光效，人物完整不裁切。

参考图 2 张：镜像待机 4× 锚 + 镜像官方侧头。

## 实收与 Alpha

- `image-65174-1445`，codex/gpt-image-2，high，请求 1024×1024；实收 **1254×1254 RGBA**，Alpha 256 级、四角 0；raw SHA `1682a55b0adee6839c9da45c345dff1a089bad9d22a73c9672265b2f405dc5a7`。真 Alpha；背景低 Alpha 光雾按 128 阈值剔除，非棋盘格，未作离线分离。

## 后处理与硬门

- 命令：`.venv/bin/python -I tools/art/super_portrait_256.py --raw art/fighters/ultraman-king/stage1/super_portrait/portrait-1024-raw.png --palette-image assets/fighters/ultraman-king/catalogue/model-native.png --out art/fighters/ultraman-king/stage1/super_portrait/portrait-256.png`
- 步骤：Alpha≥128 → bbox 裁切 → 最近邻缩到 240 px 高 → 256 画布水平居中、底边 8 px → 32 色整图最近邻映射（无抖动）→ 4 连通最大主体。
- 硬门：256×256；Alpha `{0,255}`；可见 29 色（色板 32）；4 连通 1 块，最大 26666 px；bbox `[36,8,219,247]`，边距 36/8/36/8；冠、球、须、双拳、肩甲、披风完整，底边为腰部终点并留 8 px 透明。成品 SHA `a04ae0ff184860e40565514d4079aa98a349823359bef7aa0cca28fe0cd802c1`。

## 方向核验

成品眼列 x=102.7；冠球 x=72.0（前）；冠刃后缘 x=114.0（后）；头部列带中心 115.0。已签锚同号（眼 492.7，球 433.5，刃后 646.5）。ref-02/ref-03 侧视与 ref-04 正面一致，结论通过。

## 重生成与已知问题

- 1 次，0 次重生成。冠球略大于官方小球，属局部细节差，不影响方向/身份/硬门。
- 已安装 `assets/effects/ultraman-king/super_portrait/atlas.png`；未做实机 720/1080；无录屏、无听审。

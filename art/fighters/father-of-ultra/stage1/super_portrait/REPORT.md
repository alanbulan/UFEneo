# 奥特之父超必杀三级 CUT-IN 立绘报告

- fighter：`father-of-ultra`
- 日期：2026-11-10
- 状态：`portrait-256.png` 已过硬门并由根安装到 `assets/effects/father-of-ultra/super_portrait/atlas.png`。未做实机 720/1080 检查。

## 身份锚与官方来源

- 身份锚：`art/fighters/father-of-ultra/stage1/cells/idle-candidate-01-cell.png`，192×192 RGBA，32色，Alpha 0/255，SHA `63f51642c1a67169843a186be7d3547890406dfe98558a5d4d5add10e1ec1248`；cells.json 的 identity_anchor_for_actions，状态 `identity_anchor_signed_root_delegated_by_user`，`user_reviewed: false`。
- 生成用镜像 4× 锚：`super_portrait/references/anchor-x4-left.png`，768×768，SHA `fa8f06c502ebfb297bc4e8eed72742d127ed0ea05a17c5bbaf588f4c5bac3258`。
- 官方来源：`sources/head-side-real-suit-01.jpg`（673×456，SHA `789c410ddedaee99b949d506b5886f7870dae98c6045f74ea627faba687a4a25`，真实皮套侧头/上胸）；repo 镜像裁图 `stage1/idle/references/head-side-ref-mirrored.png`（390×320，SHA `194b9a372fbdac462ddaa128224b37621ca688165acc998bde5abbfa9eb708db`），再镜像朝左作生成参考 `references/official-head-side-left.png`（SHA `75cbf40b3281e72edbee6ba6c22ad3c81d5c897bdca0b717718704859564d9f2`）；`sources/side-figure-toybox-05.png`（570×2370，SHA `412e2b0f53abe1ab8b07069f9bbb75abb3c52b381bb577f96bd467d51906af9b`，真 90° 右侧视，只取轮廓/比例）；`sources/ultra-act-ua-10-original.jpg`（258×768，SHA `baf1ee75f37821d9249ca1cde8c8c4c5bdb67e3d2e9d0c15e91bef5b407a64a7`，真 90° 右侧视交叉核验）；`sources/ref-01.webp`（971×1971，SHA `43852a3dae1c511f8b87e137b805a661f227ad411a0f3f2ed2cc887fe6cefed6`，官方正面全身，核双角/白须/中央竖鳍/配色）。
- 方向：面朝左时近侧大角在左前方向上弯、远侧角在右后方后掠，额中央有银色竖鳍，白色长须至胸前。

## 提示词（第二次，实际发送）

> 把参考图转成像素画腰部以上3/4胸像，面向画面左侧，双拳抬到胸前护架。奥特之父：近侧大角在左前方向上弯，远侧角在右后方后掠，额中央有银色竖鳍；下颌至胸前有浓密白色长须，连成完整白胡子，不只小胡子；黄眼、银红身体、蓝胸灯、红披风；头身比例、手臂与拳头粗细同参考，不增肌不缩头。像素画硬边、有限色阶、保留识别色，透明背景，四周留透明边距，无地面、文字、边框、光效，人物完整不裁切。

参考图 2 张：镜像待机 4× 锚 + 镜像官方侧头。

## 实收与 Alpha

- 第一次 `image-65174-1476` 返回 `portrait-1024-raw.png`，1254×1254，raw SHA `6b25b18802be462568729b68834799bd428cff5d9ca628ccf9c493bd4b346cde`；仅小胡子、无完整白须，拒收删除。
- 第二次 `image-65174-1506` 服务实际返回 `portrait-1024-raw-2.png`（防覆盖改名），1254×1254 RGBA，Alpha 256 级、四角 0，raw SHA `c0691239dfe02dce3855a3ee5852d74d0e62584bfd6266fb2bea9ac11034acb8`；核 SHA 后改名为约定的 `portrait-1024-raw.png`。真 Alpha；低 Alpha 光雾按 128 阈值剔除，非棋盘格。

## 后处理与硬门

- 命令：`.venv/bin/python -I tools/art/super_portrait_256.py --raw art/fighters/father-of-ultra/stage1/super_portrait/portrait-1024-raw.png --palette-image art/fighters/father-of-ultra/stage1/cells/idle-candidate-01-cell.png --out art/fighters/father-of-ultra/stage1/super_portrait/portrait-256.png`
- 色板用现行待机锚 32 色：旧图鉴色板缺金眼/蓝灯，映射会失去识别色，按 AGENTS 落格色板规则不硬套旧图鉴色板；整图统一映射。
- 硬门：256×256；Alpha `{0,255}`；可见 32 色；4 连通 1 块，最大 27952 px；bbox `[31,8,223,247]`，边距 31/8/32/8；双角、中央竖鳍、白须、双拳、披风完整，底边 8 px 透明。成品 SHA `e6fc25ce5512326884324fe8005d68a02392b09f736b2a679eca0607de71dd0f`。识别色：金眼 `(199,154,85)/(165,117,53)`，蓝灯 `(0,150,251)/(0,90,208)`。

## 方向核验

成品眼列 x=118.9；近侧角尖 x=96.0（前）；远侧角尖 x=155.2（后）；头部列带中心 120.0。已签锚（镜像左）：眼 323.9，近角 297.5，远角 367.5，左右前后关系同号。官方 head-side/ref-01 与两张真 90° 侧视确认近角在前、远角后掠、中央竖鳍；结论通过。两角尖高度次序与锚不同（成品近角最高、锚远角最高），属姿势差，不是方向反转。

## 重生成与已知问题

- 2 次生成，1 次重生成（白须不足）；无剩余问题。
- 已安装 `assets/effects/father-of-ultra/super_portrait/atlas.png`；未做实机 720/1080；无录屏、无听审。

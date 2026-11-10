# 盖亚（V2）超必杀三级 CUT-IN 立绘报告

- fighter：`ultraman-gaia`（V2）
- 日期：2026-11-10
- 状态：`portrait-256.png` 已过硬门并由根安装到 `assets/effects/ultraman-gaia/super_portrait/atlas.png`。未做实机 720/1080 检查。

## 身份锚与官方来源

- 已签待机像素整帧：`art/fighters/ultraman-gaia/stage1/idle/frames/identity-idle-pixel.png`，SHA `24da22f59292e1bd16ac8aae6231ddceeaa70623161784ac65f616f6de294d00`；cells.json 的 identity_anchor_for_actions，`review_authority=root_delegated_by_user`；192×192、二值 Alpha、单连通、站高154。
- 传入生图锚：`references/anchor-bust-left-x4.png`，SHA `f07771678a2ac0272017914d90dd9be3107eed36fdb689e5909723691075f8fe`，480×440，头胸段 4× 最近邻、水平镜像朝左。
- 官方结构来源：`sources/ref-01.webp`，SHA `a8657c4e6c2df00574b64f3ed1141d6e1aea67b9918a3683c1f1db4a8dd514ee`；官方 3/4 朝左格斗照，核头冠、额饰、面罩与 V2 胸甲。
- 传入生图官方参考：`references/official-3q-left.png`，SHA `d3cb8149c2490fe75029f4ab19eaa18298374d5556955379e9fba652be0ab380`，294×331。
- 另用官方 V2 正面 `sources/official-pose-20261109-hero/hero_gaia-1.png`，SHA `9c245f9d736271ce51bc9bbf602b6ac3ea6c6aae6059ebbee80b281feea24cb2`，只核身份/配色/黑金胸甲，未传入生图。

## 提示词（实际发送）

> 透明背景真 RGBA 像素画，按 256×256 像素网格绘制后最近邻放大到 1024。画《UFEneo》超必杀三级 CUT-IN：盖亚奥特曼 V2 单人、腰部以上四分之三正面胸像，脸朝画面左侧，双拳抬到胸前格斗护架。两张参考都已朝左：输入1是本人已签待机像素锚，只取头身比例、四肢粗细、红银配色和像素块大小；输入2是官方头胸照，只核头冠、额饰与面罩结构，不要照抄照片质感。头冠是高而窄的冠鳍，沿头顶中线竖立并略向后倾；冠前缘银色，冠前内侧金色，冠后与两侧红色。银面、浅黄眼、银色嘴部、金色额饰、黑金胸甲与青蓝三角计时器，红银身躯。像素块清晰、阶梯轮廓、色阶有限；不要照片质感、柔焦、3D、玩具关节、拼缝。人物完整不裁切，四边留透明安全边；无文字、边框、地面、光效、其他角色、棋盘格。

## 实收与 Alpha

- 请求 `codex/gpt-image-2`、high、1024×1024、transparent；实收 **1254×1254 RGBA**，SHA `294489e0cf86e87caba4ed19c5a31cd1bdaeacb17d5a6c95bf1686b1b9aa93b2`。
- 原生真透明，256 级软 Alpha；按 128 二值化。

## 后处理与色板

- Alpha 128 二值化 → 最大 8 连通主体（原本 1 块）→ bbox `[182,79,1063,1202]` → 最近邻 0.2137132680 至 188×240 → 居中 256×256（偏移 `[34,8]`）→ 整图最近色映射。
- 色板基底图鉴 32 色；补入 `(18,225,240)` 青蓝三角计时器、`(245,224,36)` 浅黄眼，移除 `(167,156,156)`、`(135,124,125)`。
- 输出：`art/fighters/ultraman-gaia/stage1/super_portrait/portrait-256.png`，SHA `c3923957b0ca357b1059f50b18310c25953d5f5e2e3a945269502fb85f7bb7f1`。

## 硬门

| 检查 | 实测 | 门 | 结论 |
| --- | --- | --- | --- |
| 尺寸 | 256×256 | 256×256 | 过 |
| Alpha | `{0,255}` | 只有 0/255 | 过 |
| 色数 | 32 | ≤32 | 过 |
| 连通块 | 1（22,230 px） | 1 | 过 |
| bbox | `[34,8,222,248]` | 画布内 | 过 |
| 四边透明边距 | 左34/上8/右34/下8 | >0 | 过 |
| 胸像完整 | 头顶到腰腹完整 | 不裁切 | 过 |
| 识别色 | 青蓝65px、亮黄569px | 保留 | 过 |
| 文字/边框/地面/光效 | 无 | 无 | 过（目视） |

## 方向核验

成图朝左：冠鳍最上点 x=129–135（均值132），眼列均值 x=115.9，头框中心 x=115.5，冠后缘到 x=157；冠尖与后缘都在眼列/头部中线之后，即向后倾，与官方同构。已看头胸放大图。

## 重生成与已知问题

- 1 次，首张过门，无其它候选。
- 为保住青蓝三角计时器与浅黄眼，色板 2 换 2。
- 已安装 `assets/effects/ultraman-gaia/super_portrait/atlas.png`；未做实机 720/1080；无录屏。

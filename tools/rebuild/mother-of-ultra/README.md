# mother-of-ultra stage1 批次记录

日期：2026-11-09。范围：待机架势照片 + 待机像素候选。stance-00/01/02 gate 拒收；stance-03 gate 拒收后经根审按 `root_delegated_by_user` 接受为已知差异（非用户亲审），但其原图在根审前已删且不可恢复；根审随后授权用同一三参考/同一提示词重生成 stance-04，新照片不继承 stance-03 验收。stance-04 初测站距 0.560、鞋底 8 源px、头高 0.2040；根审最终接受 stance-04 为已知差异并保留原图，不重生成。已据此做待机像素候选 01 并落格：192 格、站高 154、脚底 183、32 色、二值 Alpha、单连通；头壳 28px、头高按头顶 y30→颈线 y58 = 28px；红领同口径 32 含颈/领 4px 经根审不计入头高。根审已签署 idle-candidate-01 为标准型待机身份锚（`root_delegated_by_user`，非用户亲审）。原生格 + 严格 4× + 联系表已出。动作批 idle-01、walk_forward-00、walk_forward-01 已落格；walk_forward-02 换腿触地连续 3 张未交换前后腿，按返工刹车停止；walk_forward-03 未生成。轻击 10 帧、重击 3/4 帧已根审签署；最小集 7 帧已根审签署，down/win 组各缺 1 帧、保持 incomplete/pending，down-00/win-00 刹车待人工。未安装、未启动 Godot、未提交、无录屏。

## 来源核验

- `art/fighters/mother-of-ultra/sources/ref-01.webp`：378×854，RGBA，SHA `80f8a3f7719d18d5a19f8571dbcb9320de0041c69b78d7e59790ed0499210012`；来源 `https://ultra.fandom.com/wiki/Mother_of_Ultra` 的 `Mother_Infobox.png`。目视为真实官方皮套照：正面全身，双辫、头冠、黄眼、蓝胸灯、红披风可辨；不是玩具、同人、AI 或游戏截图。
- 圆谷官方角色页 `https://tsuburaya-prod.com/heroes/mother-of-ultra`（HTTP 200）人物图 `UT_Hero_mother02.png`：932×1400，RGBA，SHA `c09674db1d049d0b4d16480ef7b50fad0f568072f67715eb02938f343dc21ab8`；已保存到 `sources/official-tsuburaya-20261109/` 并写 `source.json`。无披风正面全身，用于体量/头身比/肩宽/四肢粗细核对，并作 stance-03/stance-04 的全身比例参考。
- 官方宣传图转载（SciFi Japan，Courtesy of Tsuburaya Productions）：700×450，RGB，SHA `eeb02669dc02d8a07ab1a3e5eba11803c8849846111b5b5bc453e6a5429d9613`；Marie 为带披风 3/4 站姿，不是侧视，未作参考、未保存副本。
- 官方照片级真实侧视：本轮可访问范围内没有取得。`m-78.jp/ultraheros/mother/` 与 `/galaxy-fight/tac/` 返回 HTTP 202、0 字节（机器人挑战）；`ultramanconnection.com/news/ultra-spotlight-mother-of-ultra/` TLS 证书过期；Internet Archive 快照抓取 HTTP 429。均未绕过、未反复重试。没有用正面或 3/4 图冒充侧视。
- 同版官方手办右侧视（根决定新增）：S.H.Figuarts ウルトラの母（官方商品页 `https://tamashiiweb.com/item/15384`，HTTP 200；作品 ウルトラマンタロウ，发售 2025-09，8,800 日元；页面未读到具体全高/材质，不写 140mm/PVC/ABS）。使用第三方实拍 Toybox REVIEW `https://www.myshinytoyrobots.com/2026/01/sh-figuarts-mother-of-ultra.html`（HTTP 200）第 05 图：1669×2500，RGB，SHA `9b5c1519683f9ebfd56a9a3e91072b0136ec36484f836ebbb250d6ea7ad3ed0d`；已存 `sources/official-figure-20261109/05-side-right.jpg`，来源 JSON 同目录。裁头/上胸 700×850，SHA `14bbb333cf4722be501b2f513e6ff3b1fa292e4f84b0eef6885d9cfb8db8de3f`，存 `stage1/idle/references/figure-side-head-chest-05-right.png`。人物面朝画面右，头冠侧面与近侧发辫连接/长度可读。只作发辫/头冠/领口轮廓与角度补充，不作材质/颜色来源；生成时去掉球关节、轴、插接缝与塑料高光。手办为官方发售款，第三方实拍，未独立鉴定实物真伪。
- 侧视像素锚 `stage1/idle/references/side-head-from-anchor-x4-right.png`（304×258，SHA `5aa87e9763204a00713fc7015e669840187f9e024bb621c7be50056465f37c46`）：根决定后只作核验，不再作生成输入；不借其像素画风，不单独作动作参考。

## 根决定 2026-11-09

- 图鉴侧视像素锚只作核验，不再作生成输入；它是此前头大、四肢细的来源之一。
- 固定三张生成参考：官方无披风全身照（体量/头身比/肩宽/四肢粗细）+ 同版官方手办右侧视头/上胸（发辫分段/长度/连接与头冠侧视）+ Gaia 站姿（只借站姿与画风）。
- 披风按 `ref-01` 文字描述：红色，肩部银边高领连接，前开，后垂至脚踝，不裁切。
- 写死门限：右侧视、上胸侧向、蓝胸灯只露侧缘、双肩前后重叠；头壳宽/站高对图鉴 28/154 不超 +8%（≤0.1966）；头高同口径；发辫不得省略或改短发；站距 0.65–0.80；双膝屈；双拳护架；双鞋底同线；全身不裁切；透明背景；四肢粗细与无披风全身照一致。任一门不过即拒收、记录、停；不缩头、不改阈值、不出像素。

## 根审 2026-11-09

- 根按 `root_delegated_by_user` 接受 stance-03：造型、头身、四肢、右侧视、发辫、披风、鞋底同线均过；站距 0.602 低于 0.65，但落在已装机 0.50–0.98 实测区间、与佐菲 0.618 同量级，接受为已知差异。不是用户亲审；不缩头、不改阈值。
- 根要求继续一张待机像素候选：192 格、根点 [96,184]、脚底 183、站高 154、≤32 色、二值 Alpha、单连通；头壳 ≤30px、头高 ≤31px；保黄眼与蓝胸灯；原生格 + 严格 4× + 联系表后停。不安装、不启动 Godot、不提交、不录屏。
- stance-03 原图在根审前已按上一轮 gate 拒收规则删除；repo、MCP 返回路径、Trash、APFS 本地快照、打开文件句柄、Magpie/Claude 缓存均未找到同 SHA 原图，确认不可恢复。不能把带测量线的灰底诊断图当原图。
- 根随后授权用同一三参考（官方无披风全身 + 同版 S.H.Figuarts 右侧视头/上胸 + Gaia 站姿）和同一提示词重生成 stance-04；这是新照片，不继承 stance-03 的验收，必须重新过全门：右侧视、全身不裁、透明；站距 0.60–0.80（目标 0.70）；双鞋底 ≤1 原生px；头高/站高 ≤图鉴 0.1883 +8%（≤0.2034）；头壳宽 ≤图鉴 0.1818 +8%（≤0.1963）；发辫、头冠、披风到踝、四肢粗细目视。全过后做像素；任一门不过即停并记录，不连续重生成、不缩头、不改阈值。
- 根最终审决定：接受 stance-04，原图保留，不重生成。记录口径：站距 0.560 低于 0.60 目标，但在已装机 0.50–0.98 实测区间内，姿态仍是屈膝、前后脚、双拳护架，按 `root_delegated_by_user` 接受为已知差异（不是用户亲审）；头高 0.2040 对 +8% 门 0.2034 仅高 0.0006（约 1 源px，测量级），头壳 0.164 在门内、未放大；鞋底差按原生px 计：8 源px × 154/1431 = 0.86 原生px ≤1，门过；右侧视、全身、透明、发辫、头冠、披风到踝、四肢粗细均过。据此做一张待机像素候选，像素门不过即停。

## 五次尝试（stance-00/01/02 拒收；stance-03/04 根审接受）

| ID | 生成 ID | 实收 | SHA | 站距 | 鞋底差 | 头高/站 | 头壳/站 | 结论 |
|---|---|---|---|---|---|---|---|---|
| stance-00 | image-65174-108 | 1063×1480 RGBA | `9ff5280e8766c59911dd0aaa65ce2934395527f0cb164cd813b5115beaf5d50e` | 约 0.648（网格目视） | 49 源px | 0.206 | 约 0.136（偏窄长） | 拒收：站距低于 0.65；鞋底不平；头冠粗、发辫厚、四肢细 |
| stance-01 | image-65174-114 | 1129×1393 RGBA | `f14a94ad8c8f6598111b7ee5349fe99efc625cb4c52b8a440af9dfdfdfef6425` | 0.681 | 13 源px | 0.244 | 0.214（+17.8%） | 拒收：Gaia 头部参考把本人头冠带成后掠弯角；头壳超 8% 门；四肢仍细 |
| stance-02 | image-65174-117 | 1146×1372 RGBA | `9087d25ecf3efa1bfb891168c286aebd3a9d3168f259f5ee704e3d277cdf78c5` | 0.697 | 2 源px | 0.231 | 0.220（+21.0%） | 拒收：姿态门已过，但头身比仍超图鉴/官方档；头冠仍厚、四肢仍细；背景红/品红噪点 |
| stance-03 | image-65174-137 | 1024×1536 RGBA，Alpha 0–254（255 级） | `4f83e5c6f0587d43223abb75e98a41d21b1a12759d20d32b92a2119ed95648f1` | 829/1377=0.602 | 0 源px | 254/1377=0.1845 | 约 230/1377=0.167（范围 220–240→0.160–0.174） | gate 拒收：站距 0.602 低于 0.65；其余姿态门与头身比/四肢门通过。根审接受为已知差异；原图已删且不可恢复 |
| stance-04 | image-65174-156 | 1024×1536 RGBA，Alpha 0–254（255 级） | `92eb7df38be2b6e41ae3d43476d7f0cfcdac3f408229a3f9a9c27b8f5742a3a6` | 801/1431=0.560（已知差异） | 8 源px = 0.86 原生px（门过） | 292/1431=0.2040（+0.0006 测量级） | 约 235/1431=0.164（门内） | 根审接受为已知差异：站距在已装机 0.50–0.98 区间内且姿态成立；头高仅 +0.0006；头壳未放大；其余门过；原图保留 |

图鉴同口径基准：站高 154，头壳宽 28px（`28/154=0.1818`，+8% 上限 0.1966），头高/站高 `0.1883`。

### stance-03 详情

- 三参考：官方无披风全身 `UT_Hero_mother02.png` + 同版手办右侧视头/上胸 `figure-side-head-chest-05-right.png` + Gaia 站姿 `stance-ref-gaia-body-x4.png`（无头）。
- 提示词 241 字，已写入 `stage1/requests.json` 的 `generation_plan` 与 `attempts[stance-03]`。
- 实测：站高 1377（头顶 y=100，脚底 y=1476）；脚外缘 829（后靴 x=124，前靴 x=953）；站距 0.602。即使把披风外缘 x=79 误当后脚外缘，874/1377=0.635，仍低于 0.65。鞋底差 0；头高 254（红领首行 y=354），0.1845；头壳宽约 230（范围 220–240），0.160–0.174，低于 0.1966 上限；头未放大，四肢体量较旧批改善，发辫/头冠/披风结构目视通过。
- 结论：唯站距门不过，原按 gate 拒收并停止；根审 2026-11-09 接受为已知差异。原图在根审前已删除且不可恢复，不能把诊断图当原图；根审随后授权用同一三参考/同一提示词重生成 stance-04，新照片不继承 stance-03 验收。
- 诊断图：`art/fighters/mother-of-ultra/stage1/diagnostic/stance-03-gates-2026-11-09.png`，1560×1740，SHA `62d47a50bbc91d89ad1ef4e22693d3fd240eb4e276f79bcb9aa546a2277e2633`。

### stance-04 详情

- 授权：stance-03 原图不可恢复，不能把带测量线的灰底诊断图当原图；用同一三参考与同一提示词重生成 stance-04。新照片，不继承 stance-03 验收。
- 实测：站高 1431（头顶 y=60；后底 y=1490、前底 y=1482）；脚外缘 801（后靴 x=131、前靴 x=932），站距 0.560；鞋底差 8 源px；头高 292/1431=0.2040；头壳宽约 235/1431=0.164，低于 0.1963；右侧视/全身不裁/透明/发辫/头冠/披风到踝/四肢粗细目视通过。
- 即使把披风左缘 x=71 误当后脚外缘，861/1431=0.602；披风不是脚，按脚外缘判 0.560。
- 根审接受为已知差异（不是用户亲审）：站距 0.560 低于 0.60 目标，但在已装机 0.50–0.98 实测区间内，姿态仍是屈膝、前后脚、双拳护架；头高 0.2040 对 +8% 门 0.2034 仅高 0.0006（约 1 源px，测量级）；头壳 0.164 在门内、未放大；鞋底差 8 源px × 154/1431 = 0.86 原生px ≤1，门过；其余目视门均过。
- 原图保留 `art/fighters/mother-of-ultra/stage1/idle/frames/stance-raw-04.png`，作待机像素唯一参考；不重生成、不缩头、不改阈值。诊断图 `art/fighters/mother-of-ultra/stage1/diagnostic/stance-04-gates-2026-11-09.png`，1560×1740，SHA `6e0e11e30ba07150e8085a7834b2652d5f7980a9f4b4de6df13c708753d45bb1`。

## 待机像素候选 01（已签身份锚）

- 请求：MCP `image-65174-179`，`codex/gpt-image-2` / high / transparent，请求与实收 1024×1536 RGBA，Alpha 0–254（255 级），1,496,431 bytes，SHA `0d5b6bc69784eb67542265d4243159f01c9faae332b399601d2cb1d3b3e2de3d`；唯一参考 `stance-raw-04.png`（SHA `92eb7df38be2b6e41ae3d43476d7f0cfcdac3f408229a3f9a9c27b8f5742a3a6`）。提示词 169 字：“把参考待机整身转为像素画整帧…”。usage/费用未知。
- 落格：α≥128 主体 bbox [62,51,933,1497]，源站高 1447，单比例 `154/1447=0.10642709`，整图 kCentroid 到 93×154；192 格、根点 [96,184]、脚底 183、offset [53,30]；脚底段重心 95.699。
- 色板：从本张像素源重定 32 色，保留全局青蓝两组 `(24,76,148)` / `(26,158,226)` 与亮浅黄两组 `(249,206,25)` / `(214,152,8)`，其余 MEDIANCUT 28 色；整图 RGB 最近色映射，不按区域重涂；完整色板见 `stage1/cells/cells.json`，后续动作共用。
- 硬门：192 格、根点 [96,184]、脚底 183（另一脚 182）、站高 154、色数 32、Alpha 二值 0/255、连通块 1；头壳最宽行 28px（≤30；含近侧发辫的保守上限，头壳本身更窄）；黄眼 19px、蓝胸灯 11px 色类计数，原生/4×目视可辨。
- 头高口径交叉核：像素头高标尺（头顶 y30→颈线最窄行 y58）为 28≤31；若按 stance 照片“红领首行−头顶”同口径，62−30=32，含颈/领 4px，超 1px。根审裁决：采用像素头高标尺 28；红领同口径 32 含颈/领 4px，不计入头高；不改阈值、不缩头。
- 输出：原生 `stage1/cells/idle-candidate-01-cell.png`，10,025 bytes，SHA `96ab6aa6cf19ca26b2ca9ce5981067e558f7e2d3f629e6655f9230d800ddcdf4`；严格 4× `stage1/cells/x4/idle-candidate-01-x4.png`，768×768，19,112 bytes，SHA `9a28b5a746b9ca21bf51c8d678587ac5d4120fd7a4b2a77ec3d079d642a7c82a`，逐像素重复、加色 0；联系表 `stage1/cells/idle-candidate-01-review.png`，2280×1100，633,765 bytes，SHA `419076668165a9f98bfcf83e8b3cc3cb2b0a7d3ff823bb5d6d781b416443fd23`。
- 头高诊断：`stage1/diagnostic/idle-candidate-01-head-ruler-2026-11-09.png`，900×620，86,790 bytes，SHA `f99de18eca7f2f2728c084bb2bc32965f78c9543ecd95778d2143f88b9661386`；标出头顶 y30、颈线 y58、红领首行 y62、头壳最宽 y48–50，只作测量，不改像素。
- 方法说明：完整 forge 依赖缺失，未执行网格检测；使用 `forge_backend._kcentroid_downscale` 与独立整图最近色映射，不冒称完整 forge 通过。stance-04 实测 Alpha 0–254，四角为 0、人物周围有低 Alpha 暗红光雾；落格按 128 阈值剔除光雾，未切人物。
- 状态：根审已签署为标准型待机身份锚（`root_delegated_by_user`，非用户亲审）；头高口径已裁决；动作帧只引 `pixel-raw-01`。未安装、未接运行时、未启动 Godot、未提交、无录屏；720/1080、实速、声音未验。

## 根审签署 2026-11-09

- 根审通过 `idle-candidate-01`，签为奥特之母标准型待机身份锚（`root_delegated_by_user`，非用户亲审）。
- 头高裁决：头顶 y30→颈线 y58 = 28px；头壳最宽 28px，均在门内（≤31/≤30）；红领同口径 32 含颈/领 4px，不计入头高；不改阈值、不缩头。
- 站距 0.565 沿用 stance-04 已接受的已知差异；脚底 183/182、32 色、二值 Alpha、单连通、黄眼与蓝胸灯保留均过。
- 身份锚：`stage1/cells/idle-candidate-01-cell.png`，SHA `96ab6aa6cf19ca26b2ca9ce5981067e558f7e2d3f629e6655f9230d800ddcdf4`；严格 4× `stage1/cells/x4/idle-candidate-01-x4.png`，SHA `9a28b5a746b9ca21bf51c8d678587ac5d4120fd7a4b2a77ec3d079d642a7c82a`。动作帧唯一参考 `stage1/idle/frames/pixel-raw-01.png`，SHA `0d5b6bc69784eb67542265d4243159f01c9faae332b399601d2cb1d3b3e2de3d`；不追加其它角色或角度。
- 下一步：继续 `idle-01` + `walk_forward`（4 帧），同 192 格、根点 [96,184]、脚底 183、站高 154、同 32 色板、二值 Alpha、非技能帧整帧单连通；出原生格、严格 4×、逐帧联系表与动作条后停。不安装、不启动 Godot、不提交、不录屏。

## 动作批 2026-11-09（部分完成，walk-02 刹车）

- 口径：只引 `pixel-raw-01`（SHA `0d5b6bc69784eb67542265d4243159f01c9faae332b399601d2cb1d3b3e2de3d`）；固定比例 `154/1447=0.10642709`；192 格、根点 [96,184]、脚底 183；同一 32 色板；二值 Alpha；非技能帧整帧单连通；不逐帧归一、不局部缩头。已落格三帧为子代理门检（`subagent_gate_checked_pending_root`），不是根审；未安装、未启动 Godot、未提交、无录屏。

### 已落格

- `idle-01`（呼吸下沉相）：`image-65174-199`，1024×1536 RGBA，Alpha 0–254（255 级），1,518,598 bytes，源 SHA `b0d471f5803feffdbd9d7d387d303b1f87a2c43a9d454439de1e8b9044e37266`；提示词 151 字，唯一参考 `pixel-raw-01`。源 α≥128 bbox [62,74,933,1496]（872×1423），同比例到 93×151，offset [52,33]。原生格 bbox [52,33,144,183]，站高 151、宽 93、32 色、二值 Alpha、单连通；头高 27≤31、头壳 29≤30；脚底 183/183、脚底带重心 95.63；黄眼 17px、蓝胸灯 17px。输出：`stage1/cells/idle-01-cell.png`，9,618 bytes，SHA `109bffca6981a52e4f3ad94912e6bbc3aae5f8d46d4161499922deb1f7ef6594`；严格 4× `stage1/cells/x4/idle-01-x4.png`，18,338 bytes，SHA `7d6c1fe1de9a05ac8a9bb5a2d0e731a94bd1ab82aac31df71dfec8339b53c951`，逐像素重复、加色 0；联系表 `stage1/cells/review-idle-01-2026-11-09.png`，1840×1000，386,321 bytes，SHA `68a6b1ccccec8d13680f291059aeff3246d570631773f4b26b313a5713caab07`。
- `walk_forward-00`（触地）：`image-65174-200`，1,558,529 bytes，源 SHA `a10b5ff504efb885d0a13bcf13f331c0c62b9ab0794bf2dd83f18645379d60f1`；提示词 154 字。源 α≥128 bbox [32,50,954,1491]（923×1442）→ 98×153，offset [49,31]。原生格 bbox [49,31,146,183]，站高 153、宽 98、32 色、二值 Alpha、单连通；头高 27、头壳 29；脚底 183/183、脚底带重心 95.902；黄眼 18px、蓝胸灯 24px。输出：`stage1/cells/walk_forward-00-cell.png`，9,817 bytes，SHA `1a2188bfbd19d635b31f2b824ec6c7bd0b48e1fa3bbeaa2c24862acf1db8c64d`；4× `stage1/cells/x4/walk_forward-00-x4.png`，18,761 bytes，SHA `90ff7bbfa9dd9aa7746511db40e62270fe450270c9837b391e9100614dad04a9`，逐像素重复、加色 0；联系表 `stage1/cells/review-walk_forward-00-2026-11-09.png`，1840×1000，399,578 bytes，SHA `f7e47f2bb22205eac240d33fb13801ed8ebf6f9d3d01af2585655a30e7856912`。
- `walk_forward-01`（交错）：`image-65174-201`，1,503,265 bytes，源 SHA `b00e86eb12a07dee3fbe984cec501838ce5d4ef7ab0b0d5494fc6dacd87c7af4`；提示词 151 字。源 α≥128 bbox [64,48,840,1491]（777×1444）→ 83×154，offset [50,30]。原生格 bbox [50,30,132,183]，站高 154、宽 83、32 色、二值 Alpha、单连通；头高 27、头壳 29；仅支撑脚触底 183、脚底带重心 95.74；黄眼 18px、蓝胸灯 16px。身体左移是支撑脚质心对 96 的既有口径，与盖亚 `walk_forward-01` bbox 54–120 同型；摆动脚离地，不计脚底。输出：`stage1/cells/walk_forward-01-cell.png`，9,295 bytes，SHA `a21c7b5525e84d8f6c34c1fbbea2f60ca644a5e630aaecd59bdabcffe1d79bcb`；4× `stage1/cells/x4/walk_forward-01-x4.png`，18,176 bytes，SHA `802fc58ad5584041de60fcbfc5fc526136fec9d7a06bbacf28e7215a54ee187b`，逐像素重复、加色 0；联系表 `stage1/cells/review-walk_forward-01-2026-11-09.png`，1840×1000，376,348 bytes，SHA `c984ee6d5b279bed8a55c4d3548650f62916f36ab3016b3419b8c4871d0b1dbf`。

### walk_forward-02 拒收与刹车

- 目标：换腿触地，远侧腿在前、近侧腿在后；仍只引 `pixel-raw-01`。
- `raw-01`：`image-65174-202`，1024×1536 RGBA，Alpha 0–254，1,531,827 bytes，SHA `c6ec5e66bc0c3efaff4d28bcfd7365b453f7051a19b2e69559bb293b2db24426`；bbox [33,51,959,1471]（927×1421）；提示词 158 字（“另一脚前脚跟着地…”）。拒收：近侧腿仍在前、远侧腿在后，未换腿。
- `raw-02`：`image-65174-203`，1,576,738 bytes，SHA `6dd99b0e0296dc5aa4a891854dfc1d503e18787bc5294a69d769da627173e40f`；bbox [62,50,941,1482]（880×1433）；提示词 190 字（修法 1：“两条腿交换前后位置…”）。拒收：仍近侧腿在前。
- `raw-03`：`image-65174-204`，1,560,397 bytes，SHA `ecb04cf5f7a24a69034e1431ace90cfdeec1f071b36ae1341a4f0a40e559220d`；bbox [33,59,973,1478]（941×1420）；提示词 190 字（修法 2：“原先在后的腿现在伸到画面右前方…”）。拒收：仍近侧腿在前。
- 按 AGENTS 返工刹车：同一动作门连续 3 张不同帧拒收 → 停止；同一问题 2 种修法已用完；未落格、刹车后不再重生成；`walk_forward-03` 未生成。三张拒收源图在诊断图完成后删除，SHA 与尺寸保留在 `stage1/requests.json` 的 `action_batch_2026_11_09.walk_forward_02_attempts` 与本记录。
- 诊断图：`stage1/diagnostic/walk02-brake-2026-11-09.png`，1500×900，607,325 bytes，SHA `0288311526a01bacf11f9818fec1a34cd24a3c7779b9e878fbaf5de0cae6f03e`；红圈标近侧前脚、蓝圈标远侧后脚，三张都仍近侧在前，附参考与完整 SHA。
- 动作条：`stage1/cells/strip-idle-walk-2026-11-09.png`，2504×700，137,089 bytes，SHA `0532d67290918c724bfeee53b5770a201e3f74205c5f8a13b375bc44734d5f0e`；含身份锚、idle-01、walk-00、walk-01，walk-02/03 为红色阻塞槽，不是角色帧。
- 结论：已落格三帧经 2026-11-10 根审签署；walk-02 不过，按刹车停，根决定保留三帧、不再同一思路重生成 walk_02/03，留人工。

### 本批未做

- `walk_forward-02` 换腿触地、`walk_forward-03` 换腿交错、`walk_forward` 循环接续、其余动作集；安装/运行时/720/1080/实速/声音/录屏均未做。
- 未安装、未启动 Godot、未提交、无录屏。

## 动作批根审签署 2026-11-10

- 根审通过并签署 `idle-01`、`walk_forward-00`、`walk_forward-01`（`root_delegated_by_user`，非用户亲审）：头高 27/头壳 29（≤31/≤30）、脚底 183/183、支撑脚 183、32 色/二值 Alpha/单连通/严格 4× 一致均过。
- `walk_forward-01` 身体偏左按支撑脚质心对 x=96 的既有口径接受，不是新偏差。
- `walk_forward-02` 换腿连续 3 张未过，按返工刹车停；保留 `idle-01`/`walk-00`/`walk-01`，不再同一思路重生成 `walk_02/03`，留人工。
- 下一步：继续 `light1`(3)、`light2`(3)、`light3`(4)，同身份锚、同 192 格/根点 [96,184]/脚底 183/同 32 色板/二值 Alpha；非技能帧整帧单连通，技能帧含独立颗粒只判主体；出原生格、严格 4×、联系表后停。

## 轻击批 2026-11-10（light1 3 / light2 3 / light3 4，已根审签署）

- 口径：只引 `pixel-raw-01`（SHA `0d5b6bc69784eb67542265d4243159f01c9faae332b399601d2cb1d3b3e2de3d`）；固定比例 `154/1447=0.10642709`；192 格、根点 [96,184]、脚底 183；同一 32 色板；二值 Alpha；本组为近身轻击、无独立颗粒，10 帧均整帧单连通；不逐帧归一、不局部缩头。子代理门检（`subagent_gate_checked_pending_root`），不是根审。未安装、未启动 Godot、未提交、无录屏。
- 动作语义：按 `REBUILD_2D_PLAN` 2.5.1 的站立 `5□ → □ → □` 通用轻击链，`light1` 为第一段右直拳、`light2` 为第二段左勾拳、`light3` 为第三段右重直拳终结；帧数按 `STAGE1_STANDARD` 最小集 3/3/4。未找到本角色专属 brief（`art/shared/briefs/characters/hero/mother-of-ultra/base.json` 不存在），故不命名光线/必杀、不加光效或独立颗粒，不冒充专属技能。
- `light1-00`（起手）：`image-65174-214`，1,536,442 bytes，源 SHA `09c1a66b12482a9fb8baa5674988e89f6b9becf4d377aca933fb83420341063a`；源 bbox [40,49,921,1500]（882×1452）→ 94×155，offset [51,29]；提示词 157 字。原生 bbox [51,29,144,183]，155×94，32 色，脚底 183/182，重心 95.899，眼行头壳 29、冠顶→眼 17；输出 SHA `6079eaa87c6a65f901eccb499660320df91d131bbc662df4652713a237684a57`（10,068 bytes），4× `d019033915241fa76456d022c88b589c2e981ce9cad9a2fd37bb9a44662059b5`（19,589 bytes），联系表 `1b235788c2f5826b4c4ce1db6dafc364db1e7370ef14828d4aea031fc15538a4`。
- `light1-01`（命中）：`image-65174-226`，1,591,243 bytes，源 SHA `f8a48572c301c4ccf8b58a080a2bfbad19ae45923bf13f2ddec1b96a5b5e38ba`；源 bbox [29,49,988,1499]（960×1451）→ 102×154，offset [52,30]；提示词 160 字。原生 bbox [52,30,153,183]，154×102，32 色，脚底 183/182，重心 95.571，眼行头壳 28、冠顶→眼 17；输出 SHA `f358d7dfe5c9a96329b0339c47a86bdd157887efca0d6644af3c34925049c6f5`（9,997 bytes），4× `a468fece412af191edcce855ebc57f88b678eb31a235673602694bda404a8a24`（18,956 bytes），联系表 `d02737be6a00e3c96f107fbdd0ed9a4faff351b44a717444c043237fcdbf56c5`。
- `light1-02`（收招）：`image-65174-229`，1,471,973 bytes，源 SHA `6eda3cfb5d77c760386628c8df9c837f718a1f02156dcb39523171655736f61e`；源 bbox [96,50,817,1496]（722×1447）→ 77×154，offset [57,30]；提示词 153 字。原生 bbox [57,30,133,183]，154×77，31 色，脚底 183/183，重心 95.782，眼行头壳 28、冠顶→眼 17；输出 SHA `694e82a9654b2347f4c85ab61caba1f3e9770a0e1b1df363e1ca21178cbcc6ad`（9,105 bytes），4× `b923b8be5e135acb980d00f1557417228f4a4977a94ff1f277050cbbb3b3a780`（17,780 bytes），联系表 `8290a65b94a08a52611b6cffd9aa213530ae53d623dfdd9bf610c60c554fec36`。
- `light2-00`（起手）：`image-65174-230`，1,525,687 bytes，源 SHA `e8a3c8a539a160c05782e2a28d203b02e6a987925bce07e71fb6925f61afc36a`；源 bbox [68,50,894,1498]（827×1449）→ 88×154，offset [54,30]；提示词 156 字。原生 bbox [54,30,141,183]，154×88，32 色，脚底 183/182，重心 95.759，眼行头壳 28、冠顶→眼 17；输出 SHA `ff7979160bf61c9aa91280a9a7af7a3c309a2a72b4f18e2d50444b3da4e47567`（9,276 bytes），4× `88543302eb6f486775e4793519f127b3dbd157b064f29e8cf65f0430d052fc08`（17,960 bytes），联系表 `1dec67340805ac0b2eb77d2817beb7ad63431f86c8d1e33e00a7325a8fb58b9f`。
- `light2-01`（命中）：`image-65174-231`，1,523,736 bytes，源 SHA `3ab22d06bb1decdbf293cdd69e557a52c3a70371e8fb35690b02253468c7c44b`；源 bbox [59,50,932,1496]（874×1447）→ 93×154，offset [53,30]；提示词 160 字。原生 bbox [53,30,145,183]，154×93，31 色，脚底 183/183，重心 96.182，眼行头壳 28、冠顶→眼 17；输出 SHA `ad6324a1336907b940bbd5b7667102c1eda546a6089a849e1c7c83d261be1dfc`（9,702 bytes），4× `6df06120e3bced4bdb5c9250b6c66234240f62648fc9c1346475516f8ccb9e73`（18,593 bytes），联系表 `e4853f2fa4556090885dc4c2ed20c9c29aad7a46e024be971228380543b1c86d`。
- `light2-02`（收招）：`image-65174-232`，1,521,230 bytes，源 SHA `7b7c705439c21441a1dd23e38f23997955eb741ebff00d59d4877102c573b42a`；源 bbox [78,48,846,1496]（769×1449）→ 82×154，offset [55,30]；提示词 155 字。原生 bbox [55,30,136,183]，154×82，32 色，脚底 183/183，重心 95.853，眼行头壳 29、冠顶→眼 17；输出 SHA `1b9ff30861e5bdb6e03754db445aa24fdb957bec92f11aead31d32e77fa3ba62`（9,422 bytes），4× `ecb83986b5e30978dc86da3f37d764f55b2a94d07c85712ef0c58a037a243474`（18,367 bytes），联系表 `362ad2a53df89dd087963bcfd4b24cf7c1fadd59a5b3894af9cbd8f545b35d54`。
- `light3-00`（起手）：`image-65174-234`，1,467,360 bytes，源 SHA `2661fd71a925e688fac7b55ea3499b1d3760131073098551aa5ee586e3d86f7f`；源 bbox [63,136,925,1479]（863×1344）→ 92×143，offset [51,41]；提示词 158 字。原生 bbox [51,41,142,183]，143×92，31 色，脚底 183/183，重心 95.804，眼行头壳 29、冠顶→眼 17；站高 143 为深蹲姿势，未逐帧归一；输出 SHA `2fcc9ba4693371847670def970d79bb0ae3c712361d8c18bb9fa38982b5b6707`（9,167 bytes），4× `a26d4b3dfb4ac1463edbe8938eed03e1fac34bdd30a0466e65199b4dca06a2a5`（17,755 bytes），联系表 `6bfaf7a3b2e19ec7ea974a3ff33daf86775a88e38dac69d14ffe73f68f8c0b54`。
- `light3-01`（蓄势）：`image-65174-235`，1,556,485 bytes，源 SHA `5f7d3c77e0ef5742d23e9c4a21690ed62623eaacfdb48e1f73b95ae9e135acb1`；源 bbox [14,106,930,1495]（917×1390）→ 98×148，offset [43,36]；提示词 154 字。原生 bbox [43,36,140,183]，148×98，32 色，脚底 183/183，重心 96.37，眼行头壳 29、冠顶→眼 17；披风左缘 43，未裁切；输出 SHA `9530558fdcc84f550b6105f78f2a211bf451a87f474f5a20be8dc75534b03946`（9,836 bytes），4× `cfe535f2442d333153c362c072b7d67554a7cf1f5095c02d12679c4777b53c49`（18,466 bytes），联系表 `fbca701e0f0038de50870fa3070504b6cfeca5bb5900725d59923ae185312456`。
- `light3-02`（命中）：`image-65174-236`，1,555,946 bytes，源 SHA `5ca54154ca9fad76e434502f2507dfdce0a58ebe3aa7dc40b2c55c2445f1f484`；源 bbox [15,67,1006,1489]（992×1423）→ 106×151，offset [43,33]；提示词 156 字。原生 bbox [43,33,148,183]，151×106，32 色，脚底 183/183，重心 96.205，眼行头壳 29、冠顶→眼 18（锚 17，1px 姿势差）；拳峰距右缘 44px，未裁切；输出 SHA `03b75f3266887eece500c7b6171671f82b40c18c1cc0dcec7d0edda55d2e7574`（9,385 bytes），4× `3ad33c3a87238f8296e7089c52d8f65de3abe5c8f7b86dc521c283dfd5048485`（17,595 bytes），联系表 `75bf83a28cc3a14560a39a8557304fa3d3fefb374b615f3a6a507a19f7f40e26`。
- `light3-03`（收招）：`image-65174-237`，1,432,706 bytes，源 SHA `ad398f01a4dfa89870f5d273a85afe35a96794e8d5e29324562bacd825e84fd6`；源 Alpha 0–255（256 级），源 bbox [174,48,833,1497]（660×1450）→ 70×154，offset [62,30]；提示词 153 字。原生 bbox [62,30,131,183]，154×70，32 色，脚底 183/182，重心 95.5，眼行头壳 28、冠顶→眼 17；输出 SHA `c8e78c6c7059ee163e5a440af7cd9dc75ba551320034cd64b2ef1972aab8f767`（8,330 bytes），4× `fc120e8643cd47319978db67c1676533173fcd55aa62298835ab2cfc26904390`（16,391 bytes），联系表 `eb5da9bdb72bd8102318315bd172125857af6d55489007f2f946369a536a038e`。
- 联系表：`stage1/cells/contact-light1-2026-11-10.png`，1700×760，98,955 bytes，SHA `b00db97fb48426c690747bd06f73fb60c7e54e9cecb79d2eddf0ca61bd308c4e`；`contact-light2`，1700×760，98,239 bytes，SHA `b821d6e3653af8a165c4ee12debf5d9dabcfd0d005d93b0ee11293e4500edfaf`；`contact-light3`，2112×760，114,419 bytes，SHA `26e764021ae3a4e7b7c57cc19d14053298c66e6f541fddfdf6a46075231be928`。均含身份锚与各帧原生 2×，逐帧标 bbox/色数/连通/脚底。
- 头高口径：10 帧眼行头壳 28–29（≤30），冠顶→眼 17（light3-02 为 18）；与已签锚的 17 一致。`stage_cells.head_height` 自动颈线标尺在护架/披风轮廓下帧间为 22–40（light1-00 32、light1-01 37、light1-02 37、light2-00 22、light2-01 27、light2-02 22、light3-00 31、light3-01 32、light3-02 40、light3-03 36），不稳定，只登记作提示，不据此判头高、不缩头。
- 未做：安装、运行时、Godot 启动、提交/推送、录屏；720/1080、双朝向、实速、声音、待机循环首尾、轻击链取消窗口与判定均未验。`walk_forward-02/03` 仍留人工，本批未重生成。

## 轻击批根审签署 2026-11-10

- 根审通过并签署 `light1-00/01/02`、`light2-00/01/02`、`light3-00/01/02/03` 共 10 帧（`root_delegated_by_user`，非用户亲审）：192 格/根点 [96,184]/脚底 183/31–32 色同一色板/二值 Alpha/整帧单连通/严格 4× 逐像素一致均过；眼行头壳 28–29≤30、冠顶→眼 17（`light3-02` 为 18，1px 姿势差），未缩头。
- `light2-01` 侧视勾拳弧线偏直、肘部弯曲有限，按已知差异记录，不重生成；整条仍读作第二段打击。
- 下一步：继续 `heavy`(4)，同身份锚 `pixel-raw-01`、192 格/根点 [96,184]/脚底 183/同一 32 色板/二值 Alpha/非技能帧整帧单连通；出联系表后停等根审。`walk_forward-02/03` 仍留人工。不安装、不启动 Godot、不提交、不录屏。

## 重击批 2026-11-10（heavy 3/4 已根审签署，heavy-00 刹车）

- 口径：只引 `pixel-raw-01`（SHA `0d5b6bc69784eb67542265d4243159f01c9faae332b399601d2cb1d3b3e2de3d`）；固定比例 `154/1447=0.10642709`；192 格、根点 [96,184]、脚底 183；同一 32 色板；二值 Alpha；本组为近身重击、无独立颗粒，落格 3 帧均整帧单连通；不逐帧归一、不局部缩头。子代理门检（`subagent_gate_checked_pending_root`），不是根审。未安装、未启动 Godot、未提交、无录屏。
- 动作语义：按 `REBUILD_2D_PLAN` 2.5.1 的 `5△` 重击与 `STAGE1_STANDARD` 最小集 heavy(4)：起手→蓄势→命中→收招。未找到本角色专属 brief，按通用重击制作，不命名光线/必杀、不加光效或独立颗粒。
- `heavy-01`（蓄势）：`image-65174-248`，1,558,021 bytes，源 SHA `984c7e26723f268429bed91223b9917e1d7346a20908924f848a48c2ed75f218`；源 bbox [7, 148, 990, 1462]（984×1315）→ 105×140，offset [39, 44]；提示词 161 字。原生 bbox [39, 44, 143, 183]，140×105，32 色，脚底 183/182，重心 95.527，眼行头壳 29、冠顶→眼 18（锚 17，1px 姿势差）；输出 SHA `337751f7c30b6eb1c5ede2f106a099e691751bb58f9b841918d5ee8c78f51e9c`（9,569 bytes），4× `bafca2214039e87b1d8c31696a7ddc7371e09bd6b5d6d3ea20fd34cfa845cd61`（17,706 bytes），复核图 `b6b2091c314c348c0ff8454091cef285bc23229a45da84e915f19a3f3d990f00`。
- `heavy-02`（命中）：`image-65174-250`，1,648,341 bytes，源 SHA `5b91c99b9e806e2af454f40e6382c880ce00916e7b11dd88f0b396b44f1751cf`；源 bbox [10, 51, 1006, 1494]（997×1444）→ 106×154，offset [42, 30]；提示词 158 字。原生 bbox [42, 30, 147, 183]，154×106，32 色，脚底 183/182，重心 95.698，眼行头壳 30、冠顶→眼 17；眼行另有一拳峰 run 10px（x138–147），头壳按头部 run 30 计；输出 SHA `be1827e122dac939c7007994373e6950cd1b4c20bec54aab88b07cf653a0310c`（10,121 bytes），4× `55f82978c463e0458c9a5b055948b38fc314e1feddc2aa500751c01e218d907b`（18,841 bytes），复核图 `c9e2f788f5c212a29b950915490d9907a0d9a8e6ca7981d6e9b55aa668aee56e`。
- `heavy-03`（收招）：`image-65174-251`，1,427,730 bytes，源 SHA `9d1bfe0834bad45e5f56dc513414eb4e1af234d19dcb69679080699e2aacd1c4`；源 bbox [187, 48, 817, 1498]（631×1451）→ 67×154，offset [62, 30]；提示词 151 字。原生 bbox [62, 30, 128, 183]，154×67，31 色，脚底 183/182，重心 96.1，眼行头壳 28、冠顶→眼 17；输出 SHA `9bdd6046ce625cc48b7c31402c63c95d53995aeffa73fa24a0a963da456c45e5`（7,906 bytes），4× `51355284c0515d4ac83144b1cf3af95856bbd2fc64a02a261886550358e0486e`（15,835 bytes），复核图 `015e0ce399edcced854c8f044ea616659433b109f38ce3ca2495cfe43321bce5`。
- 联系表：`art/fighters/mother-of-ultra/stage1/cells/contact-heavy-2026-11-10.png`，2112×760，136,377 bytes，SHA `bb2a754ec6c30036043ab6490a010e8499078614f5175d07c81711960c9440b6`；含身份锚、heavy-00 红色阻塞槽与 3 帧原生 2×，逐帧标 bbox/色数/连通/脚底。
- `heavy-00` 起手刹车：raw-01（`image-65174-244`，SHA `218c46eb0cc51886788a696d835f96dba3bd10d0e17cb33b96c6ba3b3b492e4a`，1,598,619 bytes，源 bbox [79,94,948,1491]，头壳 31、冠顶→眼 19）、raw-02（`image-65174-254`，SHA `79dae5cfb27ff52b45ad688e9dc6b8eb4246e562a44d68a150cc9386e8d45bc0`，1,545,571 bytes，源 bbox [85,57,938,1501]，头壳 30、冠顶→眼 19）、raw-03（加入“头部保持正侧、视线朝前、不低头”，`image-65174-255`，SHA `2439e209223b7571aef761c2ab663a2870d9c5cc4807bb2425c8a02d0dbd53f3`，1,578,531 bytes，源 bbox [38,63,968,1502]，头壳 31、冠顶→眼 19）连续 3 张在头部比例门未过。已用同提示词重掷与加头部姿态两种修法，按返工刹车停止，不用第 3 种修法；源图已删，未落格，留人工。诊断图 `art/fighters/mother-of-ultra/stage1/diagnostic/heavy00-brake-2026-11-10.png`，1660×360，53,984 bytes，SHA `819fc137d623b547e49b3f90474f03d3a4fa2f7da81be59a7ecfdbeeda221c2b`。
- 头高口径：落格 3 帧眼行头壳 28–30（≤30），冠顶→眼 17–18；与已签锚一致。自动颈线标尺 11/12/39（heavy-01/02/03），受护架与颈部轮廓影响不稳定，只登记作提示，不据此判头高、不缩头。
- 未做：`heavy-00` 起手落格；安装、运行时、Godot 启动、提交/推送、录屏；720/1080、双朝向、实速、声音、重击命中/取消/击退判定均未验。

## 重击批根审签署 2026-11-10

- 根审通过并签署 `heavy-01/02/03` 共 3 帧（`root_delegated_by_user`，不是 `user_approved`，非用户亲审）：192 格/根点 [96,184]/脚底 183/31–32 色同一色板/二值 Alpha/整帧单连通/严格 4× 逐像素一致均过；眼行头壳 28–30≤30、冠顶→眼 17–18，未缩头。
- 已知差异保留、不重生成：`heavy-01` 冠顶→眼 18（锚 17，1px 姿势差）；`heavy-03` 31 色（≤32，同一色板）。
- `heavy-00` 起手保持红色阻塞槽，不重生成、不拿其它帧冒充，留人工。
- 下一步：继续最小集剩余 `hit`(2)、`block`(1)、`down`(2)、`getup`(2)、`win`(2)、`ko`(2)，逐组出联系表后报根审；遇返工刹车即停。`walk_forward-02/03` 不动。不安装、不启动 Godot、不提交、不录屏。

## 最小集 2026-11-10（hit/block/down/getup/win/ko 六组联系表；down-00、win-00 刹车）

- 口径：只引 `pixel-raw-01`（SHA `0d5b6bc69784eb67542265d4243159f01c9faae332b399601d2cb1d3b3e2de3d`）；固定比例 `154/1447=0.10642709`；192 格、根点 [96,184]、脚底 183；同一 32 色板；二值 Alpha；本批均为近身受击/格挡/倒地/起身/胜负，无独立颗粒，落格 9 帧均整帧单连通；不逐帧归一、不局部缩头。落格时子代理硬门检（`subagent_gate_checked_pending_root`）；hit-00/01、block-00、getup-00/01、ko-00/01 已于 2026-11-10 根审签署（见下节），down-01/win-01 仍属 group incomplete/pending。未安装、未启动 Godot、未提交、无录屏。
- 动作语义：按 `REBUILD_2D_PLAN` 2.5.8 与 `STAGE1_STANDARD` 最小集；hit 后仰→回稳、block 站立交叉格挡、down 触地→躺稳、getup 撑起→站定、win 举拳→收势、ko 跪伏→前伏。未找到本角色专属 brief，按通用动作制作，不命名光线/必杀，不加特效。提示词全文与 `generation_id` 见 `stage1/requests.json` 的 `minimal_rest_batch_2026_11_10`。
- `hit-00`（受击后仰）：`image-65174-283`，1,632,400 bytes，源 SHA `148f48cdc4059e7b7e63904c9f7f68bf09e2d1e9779bbcf9eb4dff26f2246ce4`，1024×1536；源 bbox [14,72,938,1496]（925×1425）→ 98×152，offset [57,32]；原生 bbox [57,32,154,183]，152×98，32 色，脚底 183，眼行头壳 29、冠顶→眼 17；输出 `stage1/cells/hit-00-cell.png`，9,998 bytes，SHA `2592c414004ef82c71be5cee62dd0894adceb06fd133e0fab0be664dbfef849e`；严格 4× `87ae826d4ed2495798326aca86492c7320afcbc9d80dc5b2d5173a1602eff919`（18,765 bytes）；复核 `fd8b6219d1aecbca43f1a88b449f24723b20c076612035131ff442f4cd9c03bc`（540,466 bytes）。
- `hit-01`（受击回稳）：`image-65174-278`，1,505,312 bytes，源 SHA `65fa800f787b0361b0f90af0ec41f76fd46a6b6f10388868bb080b495248f61a`，1024×1536；源 bbox [105,64,924,1495]（820×1432）→ 87×152，offset [55,32]；原生 bbox [55,32,141,183]，152×87，31 色，脚底 183，眼行头壳 27、冠顶→眼 17；输出 `stage1/cells/hit-01-cell.png`，9,209 bytes，SHA `a6796fc3b82851a7fc659f62795f394b72eeea40bcc6c1a46dcfbabd87541b49`；严格 4× `8a0ac763c6946941f55c8c4dc4dfc439a1fc62e03274183bfd1a5d4113cbe198`（17,799 bytes）；复核 `a8a1d3236b8c37cbbe5a01ceb0ce74eae32debc82a33e7397dcec0be99008d9a`（538,387 bytes）。
- `block-00`（站立格挡）：`image-65174-285`，1,513,570 bytes，源 SHA `f5e49b8c40d6886cf99f0789b8e98f517fb80afc9dea0297e712137c1b847539`，1024×1536，源 Alpha 0–254（255 级）；源 bbox [106,48,931,1500]（826×1453）→ 88×155，offset [56,29]；原生 bbox [56,29,143,183]，155×88，31 色，脚底 183，眼行头壳 29、冠顶→眼 17；输出 `stage1/cells/block-00-cell.png`，9,256 bytes，SHA `0dc03bbf3896658cc3215f7814b9dd24dc213f1134c8acb00b2c59f6d128d5d2`；严格 4× `32e73eca952ee00d095ae92b6429897b484de9ed8c0bcc59ed269eaf53a1e025`（17,513 bytes）；复核 `e56fc63871388256323c9ac269f1e5a0beebbe8959669675d91f1d641eaddad3`（538,055 bytes）。
- `down-01`（躺稳）：`image-65174-297`，1,314,361 bytes，源 SHA `0020739cda0231099d695b1ad9c28f6bb00fe1379fdc73d0cde8473fd49b4c82`，1774×887；源 bbox [70,51,1693,861]（1624×811）→ 173×86，offset [10,98]；横卧按可见轮廓 bbox 水平中心对 x=96，最低轮廓 183；原生 bbox [10,98,182,183]，86×173，32 色；头部横置且与手臂连通，站立头壳/冠顶→眼标尺不适用，按头部轮廓/双辫/头冠/四肢对锚目视核验；输出 `stage1/cells/down-01-cell.png`，11,399 bytes，SHA `c326f44a3a4c742ba35b25f910515e339e5ff705676daf1a72ccd8c39b27dfb6`；严格 4× `0108055624fd20d969f1b6662850907404f35443ef0a8920d15426892a0fa4d7`（20,022 bytes）；复核 `5b820fb73be9a27e5be1a91344fc07ceb00d272564489a95434951cb5ae83441`（567,705 bytes）。
- `getup-00`（撑起）：`image-65174-292`，1,393,534 bytes，源 SHA `344b0fddbbbb478584babbe943c84342da2140f6c4eb09bc20f85f08f145e9b0`，1024×1536，源 Alpha 0–254（255 级）；源 bbox [12,257,981,1281]（970×1025）→ 103×109，offset [47,75]；原生 bbox [47,75,149,183]，109×103，32 色，脚底 183，眼行头壳 29、冠顶→眼 18（锚 17，1px 姿势差；根审保留为已知差异，不返修）；输出 `stage1/cells/getup-00-cell.png`，7,731 bytes，SHA `8bd74421018cbbab7d74245dcb01b60d4f83af5fefee0b2e0006671046f31007`；严格 4× `8b163d6ffc464f6cb323e96dc05faba920aff0f1078d01b4e7468e897f9e0a8e`（14,685 bytes）；复核 `f66366c08692c7b199b2645bce016812751fe89b59372b4a05bc59305cdc71ca`（534,428 bytes）。
- `getup-01`（站定）：`image-65174-294`，1,448,918 bytes，源 SHA `01d0407f3522de453a1dc9fd3c644137e70e52373d2cb33cddaa1035fecd3b9b`，1024×1536，源 Alpha 0–254（255 级）；源 bbox [172,48,794,1498]（623×1451）→ 66×154，offset [63,30]；原生 bbox [63,30,128,183]，154×66，31 色，脚底 183，眼行头壳 28、冠顶→眼 17；输出 `stage1/cells/getup-01-cell.png`，8,742 bytes，SHA `98ccda24d19eaafb022e3cafc75d453c035d0e063bf82436209a18d9219a719e`；严格 4× `bdc68d840caa9e1ef2de407b292968402d8b121defbbc6540ccc2e609f71cfac`（17,047 bytes）；复核 `1bb145dbb276635e09c08b3e4368129a5fd531597a462411794dc47577cd494f`（537,487 bytes）。
- `win-01`（收势）：`image-65174-301`，1,520,214 bytes，源 SHA `df1031cba9db3dca82b0231f3a519416517a25374705d66c4558e7d9cadb1df0`，1024×1536，源 Alpha 0–254（255 级）；源 bbox [77,50,903,1497]（827×1448）→ 88×154，offset [55,30]；原生 bbox [55,30,142,183]，154×88，32 色，脚底 183，眼行头壳 29、冠顶→眼 16；输出 `stage1/cells/win-01-cell.png`，9,684 bytes，SHA `895d3d69d1448c6a1efa947dcb2b07c2899b83bf17c76ac1bed6778362dae8c8`；严格 4× `88ea884853a78676858d98599a86865df526d9980fa735e9fdf050f0926fbc17`（18,631 bytes）；复核 `2bb053e9b7f4f7dde30f66ac719353471969c6e42f24d61e00c475d6d2d83a71`（541,579 bytes）。
- `ko-00`（跪伏）：`image-65174-302`，1,373,096 bytes，源 SHA `4b4727db1163fc82a214ada2e9b118636d37f115a05d332d7c69745b349d42c0`，1024×1536，源 Alpha 0–254（255 级）；源 bbox [77,336,973,1416]（897×1081）→ 95×115，offset [50,69]；原生 bbox [50,69,144,183]，115×95，32 色，脚底 183；低头，站立头壳/冠顶→眼标尺不适用，按头部轮廓/双辫/头冠/四肢对锚目视核验；输出 `stage1/cells/ko-00-cell.png`，7,951 bytes，SHA `31b8649d71fbb9674e1e549567909a6c222959fd4ff3a191fc09320d8cd6431b`；严格 4× `1ae7dc4bd849d20631bace440852b763253e46ea74d73197a6d4f91e093b86f1`（15,733 bytes）；复核 `137764960dc5b76c8e07dd76b5583fe10428b9dc67168b7abef8bcf97a63b2cf`（545,784 bytes）。
- `ko-01`（前伏）：`image-65174-303`，1,140,616 bytes，源 SHA `cf2bbf7549fb139b89ed374e4685c5dc66d6907f0769bdeadb0891a2c1191b8a`，1774×887；源 bbox [52,119,1718,837]（1667×719）→ 177×77，offset [8,107]；横卧按可见轮廓 bbox 水平中心对 x=96，最低轮廓 183；原生 bbox [8,107,184,183]，77×177，32 色；头部横置，站立头标尺不适用，按头部轮廓/双辫/头冠/四肢对锚目视核验；输出 `stage1/cells/ko-01-cell.png`，9,840 bytes，SHA `3fc6adc8a848b3f63e631b394583f72090a4e9441699d3f741e61d162ae6ef24`；严格 4× `c4877671fa2038ec706a3eb22239e20dc95b5e27c5b12444dc999158d0159840`（17,369 bytes）；复核 `afc16cf907e519307a52d91e17600b19db95e0356ae84179c5f0f50d9f57b226`（559,528 bytes）。
- 联系表：`contact-hit` 1276×760，89,844 bytes，SHA `87313f65d2be3f5ec6906db9980017d9e8821b9c613202da4b9fcf9f92614f1d`；`contact-block` 1200×760，82,158 bytes，SHA `016e11cee46129b3d90a657acc3396bc3bf53bed3c4b2354b9f4092ea003a8f3`；`contact-down` 1276×760，112,869 bytes，SHA `06a1711934310090e3df2c34cc97f1952ba454f1da4359fe172697c47245238e`；`contact-getup` 1276×760，89,941 bytes，SHA `75d12e6b1215d4e29006b438b5c65e029319f4d89754734578d841c297f37caf`；`contact-win` 1276×760，102,700 bytes，SHA `2090d92e13f07ac5bd5824051f8b2aa54aa85ce04da31b64824818f9c7038ecf`；`contact-ko` 1276×760，104,223 bytes，SHA `5cae41ddff722ea45a1a376ebc93ebf0da5a02b0d82f6d2b1344317eb1949b63`。均含身份锚与各帧原生 2×，逐帧标 bbox/色数/连通/脚底。
- `down-00` 触地刹车：raw-01（`image-65174-287`，SHA `fce528c5879e55379728ab3bb5f011ef42d29cba8c86368ac5f629c8fec9ff71`，1,576,028 bytes，实收 1536×1024，落格 bbox [22,87,179,183]，头壳 33、冠顶→眼 19）、raw-02（`image-65174-296`，SHA `ed5cb66e5aafa74929322235521fb49c5b71f5d53cfbd8a4b7f223b0ac4650b0`，1,571,167 bytes，实收 1536×1024，落格 bbox [33,91,172,183]，头壳 31、冠顶→眼 18）、raw-03（加强“严格按参考大小、头冠不加宽”，`image-65174-299`，SHA `fbad63fa45784ec8fc1a93f22ceadf4bb57103427022d93bf1652a1c1c46d4a4`，937,467 bytes，实收 1774×887，落格 bbox [8,94,187,183]，头壳 31、冠顶→眼 18）连续 3 帧在眼行头壳门未过。已用同提示词重掷与两种头部尺寸措辞，按返工刹车停止，不第 4 次重生成；源图已删，未落格，联系表留红色阻塞槽。诊断图 `stage1/diagnostic/down00-brake-2026-11-10.png`，1660×360，62,520 bytes，SHA `0cf0c88d989a3257570261678b4eee9db9dc0cfd829e1cf5b84b2f5d7dc8fba3`。
- `win-00` 举拳刹车：raw-01（`image-65174-300`，SHA `538af420c60d9a0287889946b4136034d4a784ad3b199935085648a22ce622c9`，1,543,544 bytes，1024×1536，落格 bbox [55,26,142,183]，头壳 28、冠顶→眼 19）、raw-02（加“头部保持正侧、视线朝前、不仰头”，`image-65174-304`，SHA `7fc41f341fe679a3c2825fb9683989a0a4c9025bbdd2a86fe34efca71f8ad6e7`，1,576,422 bytes，1024×1536，落格 bbox [53,26,145,183]，头壳 28、冠顶→眼 20）、raw-03（再加“头冠高度与参考一致、不拉高，眼睛位置与参考一致”，`image-65174-308`，SHA `9b0ebab5d26f95e5f5d7e514b0f93dc3a2b9c0fa48054ff7006ea2f21a00bbe3`，1,531,820 bytes，1024×1536，落格 bbox [52,26,144,183]，头壳 28、冠顶→眼 21）连续 3 帧在冠顶→眼门未过（锚 17，容差 18）。已用同提示词重掷与两种头部高度/视线措辞，按返工刹车停止，不第 4 次重生成；源图已删，未落格，联系表留红色阻塞槽。诊断图 `stage1/diagnostic/win00-brake-2026-11-10.png`，1660×570，107,876 bytes，SHA `2523ca01e67984508e972a5cda4ec6e0808482ec76444f129420d8a9ff4844c3`。
- 横卧落格口径：`down-01`、`ko-01` 按可见轮廓 bbox 水平中心对 x=96，最低轮廓 183，比例仍为 154/1447；`down-01` offset [10,98]、`ko-01` offset [8,107]。此前站立底带重心落格会把横卧帧按头部/手臂侧重心偏移（`ko-01` 初测左裁 21px），已改用 bbox 中心并重出两张复核图与 down/ko 联系表；站立帧仍用脚底带重心。未改比例、未缩头。
- 头高口径：站立落格帧眼行头壳 27–29（≤30），冠顶→眼 16–18；`getup-00` 的 18 为 1px 姿势差，待根审，未缩头。`ko-00` 低头、`down-01`/`ko-01` 横卧，站立头标尺不适用；按头部轮廓、双辫、头冠与四肢粗细对锚目视核验，不伪报数值通过。自动颈线标尺 6–39，受姿势影响不稳定，只登记作提示。
- 已知差异：`hit-01`、`block-00`、`getup-01` 为 31 色（≤32，同一色板）；`getup-00` 冠顶→眼 18（锚 17，1px 姿势差）；`win` 组只剩收势帧，单独不能完整读出胜利举拳；`down` 组 1/2、`win` 组 1/2，组不完整。
- 未做：`down-00`、`win-00` 落格；安装、运行时、Godot 启动、提交/推送、录屏；720/1080、双朝向、实速、声音、受击/格挡/倒地/起身/胜负的模拟判定均未验。`walk_forward-02/03` 仍留人工。

## 最小集根审签署 2026-11-10

- 根审通过并签署 `hit-00`、`hit-01`、`block-00`、`getup-00`、`getup-01`、`ko-00`、`ko-01` 共 7 帧（`root_delegated_by_user`，不是 `user_approved`，非用户亲审）：192 格/根点 [96,184]/脚底 183/31–32 色同一色板/二值 Alpha/整帧单连通/严格 4× 逐像素一致均过；站立帧眼行头壳 27–29≤30、冠顶→眼 16–18；`ko-00` 低头、`ko-01` 横卧，站立头标尺不适用，按头部轮廓、双辫、头冠与四肢对锚目视核验，未伪报数值通过、未缩头。
- 已知差异保留、不返修：`getup-00` 冠顶→眼 18（锚 17，1px 姿势差）；`hit-01`、`block-00`、`getup-01` 为 31 色（≤32，同一色板）。
- `down-01`、`win-01` 单帧保留；`down` 组缺 `down-00`、`win` 组缺 `win-00`，组状态不签通过，保持 incomplete/pending；`contact-down`、`contact-win` 的红色阻塞槽保留。
- `down-00`、`win-00` 不沿用本次思路重生成，留人工；`walk_forward-02/03` 不动。
- 未安装、未启动 Godot、未提交、无录屏；720/1080、双朝向、实速、声音、实际判定未验。
- 下一步：`down`/`win` 组保持 incomplete/pending，`down-00`/`win-00` 留人工；`walk_forward-02/03` 不动。不安装、不启动 Godot、不提交、不录屏。

## 刹车与处置

- 旧批“头身比/四肢体量”连续拒收 3 张（stance-00/01/02），按返工刹车停止；诊断图 `stage1/diagnostic/stance-brake-2026-11-09.png`，1170×1460，SHA `44c12438f66f60356ec93caf2c4fd39fd45062defcf51fd033d212fdeb57c581`。
- 根决定 2026-11-09 更换侧视来源策略；stance-03 属新来源方案，不是继续重复旧提示词。该张头身比/四肢项通过，但站距 0.602 低于 0.65，按 gate 拒收；根审随后按 `root_delegated_by_user` 接受为已知差异（非用户亲审）。
- stance-03 原图在根审前已删且不可恢复；根审授权 stance-04 重生成，新照片不继承验收。stance-04 初测站距 0.560、鞋底 8 源px、头高 0.2040；根审最终接受为已知差异并保留原图，不重生成。
- stance-00/01/02/03 原图已删；stance-04 原图保留（`kept: true`），作待机像素唯一参考。
- 动作批 `walk_forward-02` 换腿门连续 3 张拒收（raw-01/02/03），按返工刹车停止；诊断图 `stage1/diagnostic/walk02-brake-2026-11-09.png`，SHA `0288311526a01bacf11f9818fec1a34cd24a3c7779b9e878fbaf5de0cae6f03e`；三张源图已删，SHA/尺寸见 `stage1/requests.json`。
- 重击批 `heavy-00` 起手头部比例门连续 3 张拒收（raw-01/02/03），按返工刹车停止；诊断图 `stage1/diagnostic/heavy00-brake-2026-11-10.png`，1660×360，53,984 bytes，SHA `819fc137d623b547e49b3f90474f03d3a4fa2f7da81be59a7ecfdbeeda221c2b`；三张源图已删，SHA/尺寸见 `stage1/requests.json`；未落格，联系表留红色阻塞槽。
- 最小集 `down-00` 触地眼行头壳门连续 3 张拒收（33/31/31；冠顶→眼 19/18/18），按返工刹车停止；诊断图 `stage1/diagnostic/down00-brake-2026-11-10.png`，1660×360，62,520 bytes，SHA `0cf0c88d989a3257570261678b4eee9db9dc0cfd829e1cf5b84b2f5d7dc8fba3`；三张源图已删，SHA/尺寸见 `stage1/requests.json`；未落格，`contact-down` 留红色阻塞槽。
- 最小集 `win-00` 举拳冠顶→眼门连续 3 张拒收（19/20/21，锚 17，容差 18），按返工刹车停止；诊断图 `stage1/diagnostic/win00-brake-2026-11-10.png`，1660×570，107,876 bytes，SHA `2523ca01e67984508e972a5cda4ec6e0808482ec76444f129420d8a9ff4844c3`；三张源图已删，SHA/尺寸见 `stage1/requests.json`；未落格，`contact-win` 留红色阻塞槽。
- 未做：`walk_forward-02/03`、`walk_forward` 循环接续、`down-00`/`win-00` 阻塞帧、其余动作集、安装、720/1080、实速、声音、录屏。
- 下一步：最小集 `hit-00/01`、`block-00`、`getup-00/01`、`ko-00/01` 共 7 帧已根审签署（`root_delegated_by_user`，非用户亲审）；`down-01`、`win-01` 单帧保留，但 `down`/`win` 组各缺 `down-00`/`win-00`，组状态保持 incomplete/pending，红色阻塞槽保留；`down-00`/`win-00` 不沿用本次思路重生成，留人工；`walk_forward-02/03` 不动。不安装、不启动 Godot、不提交、不录屏。

## 新思路补做 2026-11-10（down/win 补齐，walk_forward 4/4，自签）

- 用户 2026-11-10 指令：评审自动通过，不再逐项等人工；机器门通过后直接按 `root_delegated_by_user` 签署并继续；同一检查连续 3 帧不过仍按返工刹车出诊断停。本批四帧均由子代理自动评审自签，`user_reviewed=false`，不是 `user_approved`，不是用户亲审。
- 四帧仍只引 `pixel-raw-01`（SHA `0d5b6bc69784eb67542265d4243159f01c9faae332b399601d2cb1d3b3e2de3d`）；固定比例 `154/1447=0.10642709`；192 格、根点 [96,184]、最低轮廓 183；同一 32 色板；二值 Alpha；整帧单连通；严格 4× 逐像素重复。四帧均未逐帧归一、未局部缩头、未裁切。
- `down-00`（倒地起始·后仰触地）：`image-65174-596`，请求 1536×1024，实收 1024×1536（按实收落格），1,506,521 bytes，源 SHA `5ebbadafc54719c21c27ab02561d31c28bfcaaeb4c0376b96081b5f54c307620`；源 α≥128 bbox [14,193,980,1377]（967×1185）→ 103×126，offset [46,58]；原生 bbox [46,58,148,183]，126×103，32 色，最低轮廓 183；头后仰非站立，眼行头壳 31 含姿势倾斜、冠顶→眼 17，站立头壳门不适用；输出 `stage1/cells/down-00-cell.png`，9,398 bytes，SHA `a1df1a9a9c254062b7f32d18103b4b846459f092fe58a3f27d8ecf74e34a4350`；严格 4× SHA `f3b683ac6f438377f4d59682e819a88885cbd1cbbc4a4b72da877da7ef585403`（17,880 bytes）；复核 `848bd57207589ecf91ac6d0bca2acec568fb184760c14aebc8007cfb1d20e705`（343,246 bytes）。
- `win-00`（举拳护胸）：`image-65174-598`，1024×1536，1,558,933 bytes，源 SHA `4ea45d3e72635ae3f0b7d275e7eca343343a97688db3b47ffd17d368bdc526e0`；源 α≥128 bbox [60,50,933,1497]（874×1448）→ 93×154，offset [53,30]；原生 bbox [53,30,145,183]，154×93，32 色，脚底 183，眼行头壳 28、冠顶→眼 17；输出 `stage1/cells/win-00-cell.png`，9,593 bytes，SHA `dd28cc34a2d784805a9885051eaa8136b3a3ca7531298745beba9c9f8d78109f`；严格 4× SHA `9342a4eae6fc88a3e87439fe31a624e41c940fb55159ba63386d47accac45ff0`（18,415 bytes）；复核 `39fecde246e5f084477257e20710ec37cc6c41259cb006a47391a0ee0cec1941`（346,547 bytes）。
- `walk_forward-02`（远侧腿前跨触地，改步幅/脚位）：`image-65174-600`，1024×1536，1,525,618 bytes，源 SHA `b0189a32d4cb07b0b3c56f5424e78bb63cdc35898b2410af9b010d4d76a6a259`；源 α≥128 bbox [25,58,999,1452]（975×1395）→ 104×148，offset [37,36]；原生 bbox [37,36,140,183]，148×104，32 色，最低轮廓 183（两脚均触底），眼行头壳 28、冠顶→眼 17；输出 `stage1/cells/walk_forward-02-cell.png`，9,217 bytes，SHA `cef3d9179dc40ed98d9cf2c1c2443b61d0ddb1dff26795178602bf614da65f99`；严格 4× SHA `f6ae857231972eb4c5b1c13703056e69a473017acf56db95b258f6badbd21f57`（17,987 bytes）；复核 `19cf779a590b44f8829d9461611f6cd7d8475d8e69a4d0bb507ef605a29da183`（340,293 bytes）。
- `walk_forward-03`（近侧腿屈膝抬摆，改步幅/脚位）：`image-65174-602`，1024×1536，1,502,520 bytes，源 SHA `be804859d6990241e49792c5c02dcf04d9fc3fa0f675ac505c4295b21d6661cd`；源 α≥128 bbox [60,49,895,1495]（836×1447）→ 89×154，offset [72,30]；原生 bbox [72,30,160,183]，154×89，31 色，支撑脚最低轮廓 183，眼行头壳 29、冠顶→眼 17；输出 `stage1/cells/walk_forward-03-cell.png`，9,749 bytes，SHA `a7363cd2a8d10965f41d9ab91b1117f5f48b82ad10a81a7c098b89e5b0b00ee8`；严格 4× SHA `ba7875d7b110133628bda1e057ba5289d212875b3c91c6afd122a568a4e1ae21`（18,529 bytes）；复核 `dac5a433622f3ddaabf669ca7a39333dbd4c350a7947fb058fceb04935ce511b`（345,030 bytes）。
- 组状态：`down` 2/2（down-00+down-01）、`win` 2/2（win-00+win-01）、`walk_forward` 4/4（00–03）均已补齐并自签；down-01、win-01 由“单帧保留、组 incomplete/pending”转入完成组，旧记录保留在 `root_signing_2026_11_10` 历史字段。`minimal_rest` 最小集共 11 帧全部自签。
- 联系表：`contact-down-2026-11-10-rework.png` 1254×760，103,535 bytes，SHA `6cbbe04c689505969f7ce265433abd43939f2b2b58edf2630aa9d0ce3a215890`；`contact-win-2026-11-10-rework.png` 1254×760，89,861 bytes，SHA `65e47b1515b27a800d3ac98e129c90def92aaf728a12b20e612ec70bdc31f050`；`contact-walk-2026-11-10.png` 2070×760，133,829 bytes，SHA `183041c72f3f03708fcb1e5330ed4acebfefeade623168226c91164c6575c92c`。旧 `contact-down/win` 与红色阻塞槽保留为历史，不删除、不冒充当前状态。
- 已知差异（保留、不返修）：`walk_forward-02` 前脚为脚尖先触地、脚跟未落（提示词要求脚跟着地，实际脚尖触地）；`walk_forward-03` 抬膝偏高；`down-00` 后仰非站立，眼行头壳 31 含姿势倾斜，站立头壳标尺不适用，冠顶→眼 17；`getup-00` 冠顶→眼 18、`hit-01`/`block-00`/`getup-01` 31 色等旧差异不变。
- 未做：安装、运行时、Godot 启动、提交/推送、录屏；720/1080、双朝向、实速、声音、walk_forward 循环接续、down/win 实际判定均未验；最小集其余动作组（walk_back、dash_start、dash、takeoff、air、land）未做。
- 下一步：按自动评审规则继续最小集后续动作组；同身份锚、192 格/根点 [96,184]/脚底 183/同一 32 色板/二值 Alpha/整帧单连通；不安装、不启动 Godot、不提交、不录屏。

## walk_back 4/4 落格与自签 2026-11-10

- 按用户 2026-11-10 自动评审指示，`walk_back` 四帧只引 `pixel-raw-01`（SHA `0d5b6bc69784eb67542265d4243159f01c9faae332b399601d2cb1d3b3e2de3d`），固定比例 `154/1447=0.10642709`，192 格、根点 [96,184]、最低轮廓 183、同一 32 色板、二值 Alpha、整帧单连通、严格 4× 逐像素重复；未逐帧归一、未局部缩头、未裁切。机器门与目视造型核对通过，按 `auto_pass_2026_11_10` 自签为 `root_delegated_by_user`，`user_reviewed=false`，不是 `user_approved`、不是用户亲审。
- `walk_back-00`（后退触地）：`image-65174-658`，1024×1536，1,537,009 bytes，源 SHA `a56240c7dddb92e6273d4eff741e07081282b03caf5fd1fafabdae058eed4a07`；源 α≥128 bbox [50,50,930,1490]（881×1441）→ 94×153，offset [48,31]；原生 bbox [48,31,141,183]，94×153，32 色，脚底 183，眼行头壳 28、冠顶→眼 17；输出 `stage1/cells/walk_back-00-cell.png`，9,907 bytes，SHA `f19ec5e3bb460498c90b63fc400ffd7d2007455a7451ffa82183d878d683828c`；严格 4× SHA `8c0f0b1507d193272ee1bf13e0990e049776a6971c7f6a38869f4d2f3c631872`（18,948 bytes）；复核 `fa219706e2c92d94a1255e66e08ed960d196f88e85ac1ea951eee01000f7b281`（349,018 bytes）。
- `walk_back-01`（交错经过）：`image-65174-659`，1024×1536，1,495,877 bytes，源 SHA `b975fc8c4f8d3719e91781e76eca8db523165133da589af8870fb544907dc50e`；源 α≥128 bbox [71,51,805,1484]（735×1434）→ 78×153，offset [56,31]；原生 bbox [56,31,133,183]，78×153，31 色，脚底 183，眼行头壳 28、冠顶→眼 17；输出 `stage1/cells/walk_back-01-cell.png`，9,282 bytes，SHA `f9db9db94c8b5b96b7d76cd9f81e8ce459db5b268d71b7bcea76cbad03541525`；严格 4× SHA `317daa1cf1c839b1ff7e12f65359a3a1aa0a85255f99cb093187315c0a488852`（18,352 bytes）；复核 `df8e1eefcc19a6971bd7ef4db82c2311b53275508bfcaf41e8e5c55025255b5b`（333,881 bytes）。
- `walk_back-02`（换步触地）：`image-65174-661`，1024×1536，1,584,748 bytes，源 SHA `eda9d904ea977d1a2436880cd1f2c0cf152822dbbebdedab803ce6c2b8a85019`；源 α≥128 bbox [41,49,941,1493]（901×1445）→ 96×154，offset [46,30]；原生 bbox [46,30,141,183]，96×154，32 色，脚底 183，眼行头壳 28、冠顶→眼 17；输出 `stage1/cells/walk_back-02-cell.png`，9,801 bytes，SHA `7d69fad0d341aedeba9d7bc7f7d15f1f133a938d6aea610cba44dd66790f989b`；严格 4× SHA `c61e0a9e4f3c0640e20cbdf68add5b5e5bf7ad2669500c6928c37697e840e288`（19,042 bytes）；复核 `49729001b6bb0d33c1833c96d5d076cfaf6b6a8b885cf15c4e6c47c7a471809f`（349,654 bytes）。
- `walk_back-03`（抬腿交错）：`image-65174-663`，1024×1536，1,504,422 bytes，源 SHA `4f91062550b195efddc4bd2e87ea4f33898ce68802020ed3d9782de8bd6711e9`；源 α≥128 bbox [63,48,790,1502]（728×1455）→ 77×155，offset [72,29]；原生 bbox [72,29,148,183]，77×155，32 色，脚底 183，眼行头壳 28、冠顶→眼 17；输出 `stage1/cells/walk_back-03-cell.png`，9,116 bytes，SHA `2315d806316b90a63e5ce1eb0726e1c561eefd621e734f79c7db9621988bd6d1`；严格 4× SHA `b27297e52e15d1c92d146278dd74fc0be9b0b297c5fae2a948727a22fca4cd58`（17,618 bytes）；复核 `6b4602585f6f93970de75ab9f7becc27337307e8f285f2a0ada18f90800a8b09`（329,666 bytes）。
- 组状态：`walk_back` 4/4（00–03）自签完成；`action_frames` 现含 idle-01、walk_forward-00–03、walk_back-00–03 共 9 帧；`walk_back_set_status=walk_back_00_03_root_signed_complete_4of4`。
- 联系表：`stage1/walk_back/contact-walk_back-2026-11-10.png`，2076×760，133,340 bytes，SHA `1392f8f6d97a1642740885d42bebd54d8cd9b3c490947348a344eb25acbd723a`；内容为 idle-01 身份锚 + walk_back-00–03。
- 已知差异（保留、不返修）：`walk_back-03` 抬膝偏高；四帧披风按角色朝向垂落，未按后退运动方向向右前飘；`walk_back-00/02` 均为宽步触地、步幅差有限；自动头高标尺 31/31/37/31 仅登记，02 的 37 受抬腿姿势影响，站立头门仍以眼行头壳 28、冠顶→眼 17 为准；底带重心实测 95.56–95.93（对 x=96±0.5）。
- 未做：`walk_back` 循环接续、实速、双朝向未验；安装、运行时、Godot 启动、提交/推送、录屏；720/1080、声音未验；最小集其余动作组（dash_start、dash、takeoff、air、land）未做。
- 下一步：继续 `dash_start(2)`、`dash(4)`、`takeoff(2)`、`air_rise/air_fall`、`land(2)`；同身份锚、192 格/根点 [96,184]/脚底 183/同一 32 色板/二值 Alpha/整帧单连通；不安装、不启动 Godot、不提交、不录屏。

## dash_start 2/2 落格与自签 2026-11-10

- `dash_start` 两帧只引 `pixel-raw-01`（SHA `0d5b6bc69784eb67542265d4243159f01c9faae332b399601d2cb1d3b3e2de3d`），固定比例 `154/1447=0.10642709`，192 格、根点 [96,184]、脚底 183、同一 32 色板、二值 Alpha、整帧单连通、严格 4× 逐像素重复；未逐帧归一、未局部缩头、未裁切。机器门与目视造型核对通过，按 `auto_pass_2026_11_10` 自签为 `root_delegated_by_user`，`user_reviewed=false`，不是 `user_approved`、不是用户亲审。
- 第一张 `dash_start-00-raw-01` 拒收：`image-65174-679`，1024×1536，1,542,136 bytes，源 SHA `15e407d05bb954cc12c2e33e769ca0184426e15c7c43c7e41e2626bb2a56524e`；落格后眼行头壳 33>30、冠顶→眼 19>18，头部偏大且姿态偏跪。按第一修法重生成 `raw-02`；该废稿 SHA/尺寸已写入 `dash_start_batch_2026_11_10.attempts`，源文件已删除。
- `dash_start-00`（起势，raw-02）：`image-65174-686`，1024×1536，1,561,568 bytes，源 SHA `28f78634732f6ac3027564400a72af03587277141729fb0536b91a99dae54a1d`；源 α≥128 bbox [22,100,942,1470]（921×1371）→ 98×146，offset [49,38]；原生 bbox [49,38,146,183]，98×146，32 色，脚底 183，眼行头壳 30、冠顶→眼 18（锚 17，1px 姿势差），底带重心 96.22；输出 `stage1/cells/dash_start-00-cell.png`，10,167 bytes，SHA `44337b1971c8290cb257b765ff002e11551da08f456fa60971b8a6d32f41432a`；严格 4× SHA `784bc683d5b835494257677691bd5c64bbbb0d58a6e376e099051e2206d29e1c`（19,136 bytes）；复核 `a81280cd445ae84143332e25ed86ffa5b6f419e76a0a570637eb1e132e5a8eb8`（353,834 bytes）。
- `dash_start-01`（蹬出，raw-01）：`image-65174-681`，1024×1536，1,568,248 bytes，源 SHA `7a38b43da171d7ff14d4fe9283a10c198e0d3df43279eb730311c4cd4736c1e7`；源 α≥128 bbox [20,154,978,1465]（959×1312）→ 102×140，offset [86,44]；原生 bbox [86,44,187,183]，102×140，32 色，脚底 183，眼行头壳 28、冠顶→眼 17，底带重心 95.76；输出 `stage1/cells/dash_start-01-cell.png`，9,085 bytes，SHA `041a8e314140257f8f61231a1b719b07fbded5713d39cd35f75305fd0f1c1dfc`；严格 4× SHA `706ef50a1ecbe55b2a749df1e080a37566e76f9eee80a5d7f0f770adc3a7fadc`（17,159 bytes）；复核 `4f6d597876cbaad86207750203fd4fca4dcfd05244f260b49109a6af5d010623`（338,044 bytes）。
- 联系表：`stage1/dash_start/contact-dash_start-2026-11-10.png`，1260×760，95,083 bytes，SHA `e92914466f377c1a47a34560874387554442841b8cd9d5c1a684ce1cd4df35f5`；内容为 idle-01 身份锚 + dash_start-00/01。组状态 `dash_start_00_01_root_signed_complete_2of2`。
- 已知差异（保留、不返修）：`dash_start-00` 冠顶→眼 18（锚 17，1px 姿势差）、头壳 30 接近门限；`dash_start-01` 身体前倾幅度大、近似腾跃，蹬地感不完整；两帧仍可读作低蹲起势→蹬出。
- 未做：`dash_start→dash` 接续、实速、双朝向未验；安装、运行时、Godot 启动、提交/推送、录屏；720/1080、声音未验；最小集其余动作组（dash、takeoff、air、land）未做。
- 下一步：继续 `dash(4)`、`takeoff(2)`、`air_rise/air_fall`、`land(2)`；同身份锚、192 格/根点 [96,184]/脚底 183/同一 32 色板/二值 Alpha/整帧单连通；不安装、不启动 Godot、不提交、不录屏。

## dash 4/4 落格与自签 2026-11-10

- `dash` 四帧只引 `pixel-raw-01`，固定比例 `154/1447=0.10642709`，192 格、根点 [96,184]、脚底 183（每帧至少一脚触地）、同一 32 色板、二值 Alpha、整帧单连通、严格 4× 逐像素重复；未逐帧归一、未局部缩头、未裁切。机器门与目视造型核对通过，按 `auto_pass_2026_11_10` 自签为 `root_delegated_by_user`，`user_reviewed=false`，不是 `user_approved`、不是用户亲审。
- 第一张 `dash-00-raw-01` 拒收：`image-65174-696`，实收 1536×1024（横向），1,553,262 bytes，源 SHA `31ccf2239f456776befc8ca8577ee76c239082c1b6f328d5ac23c996cc1d7a50`；源 α≥128 bbox [48,20,1300,1001]（1253×982）→ 133×105，offset [0,79]；落格 bbox [0,79,132,183]，高 105，组内其余 126–148，且左缘贴格边，属同组尺度不一致。按第一修法竖幅重生成 `raw-02`；废稿 SHA/尺寸已写入 `dash_batch_2026_11_10.attempts`，源文件已删除。
- `dash-00`（触地，raw-02）：`image-65174-710`，1024×1536，1,543,783 bytes，源 SHA `1cd7d1ab1bfc106edacaa50787c11ad84338dcacb7850003f9543321972db7da`；源 α≥128 bbox [15,141,966,1393]（952×1253）→ 101×133，offset [39,51]；原生 bbox [39,51,139,183]，101×133，32 色，脚底 183，眼行头壳 30、冠顶→眼 17，底带重心 96.39；输出 `stage1/cells/dash-00-cell.png`，8,808 bytes，SHA `2926b19d68eeacd31556409e5d1197cbbdf93d0587fb65e8e2e04a19aa5a3604`；严格 4× SHA `e4259cfe340da8a1748c6f0a9dd155991aa7fb26b541c7d28d78056913086b4b`（16,623 bytes）；复核 `d6974f75d872ca79191dcd7b64e20217d05986f15878ce83f0c948aaf781f236`（329,551 bytes）。
- `dash-01`（交错，raw-01）：`image-65174-698`，1024×1536，1,514,128 bytes，源 SHA `9005bf7cb4c9ce3665dab1cfe22a5612090d9da9a08191f47d54cf99e7634698`；源 α≥128 bbox [16,157,917,1485]（902×1329）→ 96×141，offset [72,43]；原生 bbox [72,43,167,183]，96×141，32 色，脚底 183，眼行头壳 28、冠顶→眼 17，底带重心 96.27；输出 `stage1/cells/dash-01-cell.png`，8,908 bytes，SHA `212dcb628a0520559b6ba7dee5fb37e3c79aa7d945dda23e3f16f6f12288a5f4`；严格 4× SHA `e931c1750561a5534fe7bcbd638339ba9867823df4cc0067183d3d91964f6fe0`（16,706 bytes）；复核 `4ff8a4da17f6708d69be2edc099ce264a4e2371b355212553a2d305f573c515a`（328,527 bytes）。
- `dash-02`（换步触地，raw-01）：`image-65174-700`，1024×1536，1,565,831 bytes，源 SHA `79ca49eec4301783753c067ba610def85f704ef9b7133f84bf2ed17f74ec0d92`；源 α≥128 bbox [12,173,963,1358]（952×1186）→ 101×126，offset [19,58]；原生 bbox [19,58,119,183]，101×126，32 色，脚底 183，眼行头壳 27、冠顶→眼 16（锚 17，1px 姿势差），底带重心 96.26；输出 `stage1/cells/dash-02-cell.png`，8,418 bytes，SHA `124307d75025a502126e1e7348c938c29dd80d8ec9b7a4f5d23afea9c5c9c407`；严格 4× SHA `ad4d635f2fa797327d8952d3e97a2aa3c72a12b7808441dded7a0fad7adbcbc8`（16,062 bytes）；复核 `4260d15511a420615558948d05e44bc43d790de7ebaf146bca744043f1cb10a9`（324,935 bytes）。
- `dash-03`（换步交错，raw-01）：`image-65174-702`，1024×1536，1,545,724 bytes，源 SHA `b7d465c66d5bf6273b8672e979e24cc27013a9a07782a525009b9b3bcca3f2be`；源 α≥128 bbox [10,79,902,1470]（893×1392）→ 95×148，offset [59,36]；原生 bbox [59,36,153,183]，95×148，32 色，脚底 183，眼行头壳 29、冠顶→眼 17，底带重心 95.89；输出 `stage1/cells/dash-03-cell.png`，9,229 bytes，SHA `d49984e99b276a151b63bea037d197f60d3feb848f1d32413197e7c8cf67a4dc`；严格 4× SHA `abb237b9d3b7c3a82fdbea2968d5da9c4c5c15f9cfd65c5297757872b2091a33`（17,471 bytes）；复核 `1f68d710d2abf6e8cbf175c9c3f053f66fb46080b493b7fee3c486983ecd5562`（339,151 bytes）。
- 联系表：`stage1/dash/contact-dash-2026-11-10.png`，2076×760，119,806 bytes，SHA `0ca0bb14c18cb2e8c23058fa5a3849031d106741442d3fd0d4fa7604aa566e19`；内容为 idle-01 身份锚 + dash-00/01/02/03。组状态 `dash_00_03_root_signed_complete_4of4`。
- 已知差异（保留、不返修）：`dash-00` 头壳 30 接近门限；`dash-02` 冠顶→眼 16（锚 17，1px 姿势差）；`dash-03` 抬膝偏高、交错相身体较直；四帧高度 126–148，差异来自姿势，比例未逐帧归一。
- 未做：`dash` 循环接续、`dash_start→dash` 接续、实速、双朝向未验；安装、运行时、Godot 启动、提交/推送、录屏；720/1080、声音未验；最小集其余动作组（takeoff、air、land）未做。
- 下一步：继续 `takeoff(2)`、`air_rise/air_fall`、`land(2)`；同身份锚、192 格/根点 [96,184]/脚底 183/同一 32 色板/二值 Alpha/整帧单连通；不安装、不启动 Godot、不提交、不录屏。

## takeoff / air_rise / land 落格与 air_fall 刹车 2026-11-10

- 仍只引 `pixel-raw-01`（SHA `0d5b6bc69784eb67542265d4243159f01c9faae332b399601d2cb1d3b3e2de3d`），固定比例 `154/1447=0.10642709`，192 格、根点 [96,184]、同一 32 色板、二值 Alpha、整帧单连通、严格 4× 逐像素重复；未逐帧归一、未局部缩头、未裁切。接地帧脚底 183；腾空帧按最低轮廓 174/160，根点仍 [96,184]，水平按蓝胸灯中心对齐锚的约 114.35，并在记录中登记。通过帧按 `auto_pass_2026_11_10` 自签为 `root_delegated_by_user`，`user_reviewed=false`，不是 `user_approved`、不是用户亲审。
- `takeoff-00`（屈膝蓄力）：`image-65174-721`，1024×1536，1,536,715 bytes，源 SHA `dabfd1f0ffd917c111e76b2ec4b796ad27beb5e18e44bbf4e60798737f9bb343`；源 α≥128 bbox [65,211,916,1484]（852×1274）→ 91×136，offset [53,48]；原生 bbox [53,48,143,183]，91×136，32 色，脚底 183，眼行头壳 29、冠顶→眼 17，底带重心 95.98；输出 `stage1/cells/takeoff-00-cell.png`，9,327 bytes，SHA `589660fe89f8f5d7be7b72cf76bf4c36af119b7063aceb46cf35711e98b84920`；严格 4× SHA `f032922a50b8db65d8b8aafc7a01dd1299a609c8db452efea6808482d3d24773`（17,795 bytes）；复核 `236fbe51471aa180a6ad0ca742b3d7c819893324845cdd177ff2e0d1627079ad`（344,122 bytes）。
- `takeoff-01`（蹬地离地）：`image-65174-722`，1024×1536，1,496,610 bytes，源 SHA `35c6ded21331cd1f1dac37d60026ab9db550cebb0a95e4b6454d8f4a776297bb`；源 α≥128 bbox [26,47,967,1495]（942×1449）→ 100×154，offset [42,21]；原生 bbox [42,21,141,174]，100×154，32 色，最低轮廓 174，眼行头壳 29、冠顶→眼 16（锚 17，1px 姿势差），蓝胸灯中心 114.40；输出 `stage1/cells/takeoff-01-cell.png`，8,959 bytes，SHA `cd66a99bfa029d1f1df9da231b6da433c42bf0c0f7fa0c5d3c3d18a80e0d9c64`；严格 4× SHA `70aa98bd152b34c4219a125ec3d2f7988b5d30b2b7c1a5b7847ed52ab02be22a`（16,941 bytes）；复核 `f1156205272c6b1285dd9d2171a8d7ab020fc7d82812cf6f95b1989e31459487`（331,250 bytes）。
- `air_rise-00`（上升）：`image-65174-723`，1024×1536，1,481,646 bytes，源 SHA `7b42264e741e6bfee345ec8e9a97ac9555aa9ef25b712a0282081e5479709734`；源 α≥128 bbox [97,47,838,1479]（742×1433）→ 79×153，offset [57,8]；原生 bbox [57,8,135,160]，79×153，32 色，最低轮廓 160，眼行头壳 29、冠顶→眼 17，蓝胸灯中心 114.62；输出 `stage1/cells/air_rise-00-cell.png`，8,996 bytes，SHA `267cf260944685285859338c0bd1df20de917fba97308e9df893042f6b62fea7`；严格 4× SHA `3efd93668fb2fd7357dbdff9d57d8dff50371249831a4bf80285fa87845a9fde`（17,485 bytes）；复核 `3bde9c0fbce8520f6185eaad3e3794631a1be59f1f45fbdfc7e13289ffe5eb29`（322,871 bytes）。
- `land-00`（触地）：`image-65174-729`，1024×1536，1,562,997 bytes，源 SHA `7297959fed03a828af7042ccb09775da0239eeedb7a218a4835d3f81a80d99b0`；源 α≥128 bbox [24,194,972,1440]（949×1247）→ 101×133，offset [53,51]；原生 bbox [53,51,153,183]，101×133，32 色，脚底 183，眼行头壳 28、冠顶→眼 18（1px 姿势差），底带重心 96.39；输出 `stage1/cells/land-00-cell.png`，10,133 bytes，SHA `4045ef4be26cb7b32a534163b48424abb0868b87cd20c088570d2f8d00acf59b`；严格 4× SHA `b706d34c7e620a82e505939d206cbc0ed60bd1a0b3943fd10c6a7360fd18bce0`（18,758 bytes）；复核 `d7a44a6271b9095ad52b0d0431863084ff2ee5a27d15bd7b03b79b7ef2096736`（361,502 bytes）。
- `land-01`（屈膝缓冲，raw-03）：`image-65174-756`，1024×1536，1,442,322 bytes，源 SHA `53ee6402b664a73c0c92a417116cb9dbc8215ce31da3555172575bef95b0354f`；源 α≥128 bbox [52,293,956,1446]（905×1154）→ 96×123，offset [62,61]；原生 bbox [62,61,157,183]，96×123，32 色，脚底 183，眼行头壳 30、冠顶→眼 18，底带重心 95.74；输出 `stage1/cells/land-01-cell.png`，8,944 bytes，SHA `292280235f67886f7b9b77a449dfe44042ee47d2f671a106514ebf03a3fbb200`；严格 4× SHA `bf6ec4ed06ebc5551a1eab346556cf791f33a0c7f427e61f1d2f3d85ab2eb1b4`（16,965 bytes）；复核 `81963b5ee041b4b7f4d3b7157226217c572274dbd189cedebe60c3a5fecaddf0`（326,831 bytes）。此帧前两张：raw-01 `image-65174-732`，1,538,918 bytes，源 SHA `e89f4c0b2d2eabf2973e9906fab78ed0478a6161e494310770da101440dc153b`，头壳 32/冠眼 19；raw-02 `image-65174-743`，1,471,256 bytes，源 SHA `3983ba2a134ccbc2b4bd15c426d62d6c5a2ebd04917178249e73b959b0efe0da`，头壳 31/冠眼 18；均拒收并删除，SHA/尺寸在 `land_batch_2026_11_10.attempts`。
- `air_fall-00` 阻塞（不签署）：三次尝试均为下落相头部后仰、冠顶→眼超门。raw-01 `image-65174-727`，1,531,882 bytes，源 SHA `83597e4bbdca6b695194b4f11a822d9d2d4cc8c8579d5ced8f0595258059bcc8`，bbox [38,15,923,1474]→94×155，offset [45,20]，细胞 bbox [45,20,138,174]，头壳 30/冠眼 21；raw-02 `image-65174-740`，1,539,514 bytes，源 SHA `3eb4794a93351abaaedef9e19bf2cfb941df523cbbac953ec247758010894fcb`，bbox [13,26,919,1492]→97×156，offset [44,19]，细胞 bbox [44,19,140,174]，头壳 28/冠眼 19；raw-03 `image-65174-753`，1,525,843 bytes，源 SHA `34ba9919010bef31e4f946328fc2d0575182516fae20965b57906996acf2a553`，bbox [12,4,907,1501]→95×159，offset [43,16]，细胞 bbox [43,16,137,174]，头壳 33/冠眼 28。已用满两种修法，停止重生成；三张废稿按 SHA/尺寸核验后删除，诊断图 `stage1/diagnostic/air_fall00-brake-2026-11-10.png`，1668×680，91,940 bytes，SHA `a980e3face33432b527d7ac8e48cbd1855581edfb9b65cddff506d7a36529373`。红色阻塞槽保留在联系表，不用其它帧冒充。
- 联系表：`contact-takeoff-2026-11-10.png` 1260×760，90,305 bytes，SHA `c8e8a164b5b84038a969da428e54aae55143a464a7073fef6965802692dd5836`；`contact-air-2026-11-10.png` 1260×760，104,495 bytes，SHA `cf9d3cc69ba24eef52ecf33f67a3a6c642a135bd2bb2bf6db1ed76b0b0e36afc`（含 air_fall 红色阻塞槽）；`contact-land-2026-11-10.png` 1260×760，87,004 bytes，SHA `3dd10683791ef436082d2b6e9626af8e317ecb804efc8aea49977f583c3de713`。组状态：`takeoff` 2/2、`air_rise` 1/1、`air_fall` blocked、`land` 2/2。
- 已知差异（保留、不返修）：`takeoff-01` 身体前倾幅度大、双臂后摆、向上伸展不足，冠顶→眼 16（锚 17，1px 姿势差）；`land-00` 冠顶→眼 18（1px 姿势差）；`land-01` 眼行头壳 30 接近门限、深蹲站高 123；`air_rise-00` 一臂上举、姿态不对称，腾空最低轮廓 160。
- 未做：`air_fall-00` 留人工换下落姿势/参考；起飞—空中—落地接续、实速、双朝向未验；安装、运行时、Godot 启动、提交/推送、录屏；720/1080、声音未验；`heavy-00` 旧阻塞仍在。
- 下一步：最小集除 `air_fall-00`、`heavy-00` 外已落格；不安装、不启动 Godot、不提交、不录屏。

## air_fall-00 头门口径复查 2026-11-10（刹车依据作废，heavy-00 维持）

- 起因：奥王同日“基准/候选不同口径”事故写回 AGENTS.md 后，回头自查奥母两处刹车。只用已留存的诊断图重算，不重建已删原图。
- 发现：`air_fall-00` 三次拒收的“冠顶→眼 21 / 19 / 28（门 ≤18）”复算逐值吻合，但那是**眼行减整帧 Alpha 最高行**。下落姿势把红披风甩到头顶以上，最高行是披风，不是头。锚本身两口径同值（17 / 17），所以已签帧从未暴露这个缺陷，只有披风高过头顶的姿势会踩到。
- 按锚同口径（眼列 ±26 px 内、排除红披风取冠顶）重测：raw-01 16、raw-02 16、raw-03 17，**三张全部在 ≤18 门内**。三次拒收是地标错位，不是模型把头画大。
- 未解决项：诊断图是 2× 缩略，头壳宽量得 29 / 29 / 27，与原记录 30 / 28 / 33 不一致；raw-03 记录值 33 即使只换冠顶口径仍 >30。缩略图不能判头壳宽，须按原图重测。因此本次审计**不为 air_fall-00 签通过**，只作废刹车依据。
- `heavy-00` 对照组：按正确面板复算，冠顶→眼 19 / 19 / 19、头壳 31 / 31 / 31，与记录一致（raw-02 头壳记录 30 对复算 31 为 3× 缩略量化误差）。该组是站姿起手、披风在身后低于头顶，整帧最高行即冠顶，**不受此缺陷影响；拒收是真的，刹车维持，不翻案**。
- 代价：`air_fall-00` 三张源图已按错误结论删除，不可追回，须重出一次再判。
- 诊断图：`stage1/diagnostic/air_fall00-landmark-audit-2026-11-10.png`，1668×800，220,657 bytes，SHA `6c68622e1564628233712dbf7357749ad0dc25e4de542d5f20b7ef1d3cf26653`。记录见 `stage1/requests.json` 的 `head_landmark_audit_2026_11_10`。
- 规则写回：AGENTS.md“美术与资源”、docs/HANDBOOK.md 第 6 节，新增“冠顶只取头部列带，不得用整帧 Alpha 最高行”。
- 未做：`air_fall-00` 重出、落格、签署；安装、Godot 启动、提交、录屏、720/1080、双朝向均未做。

## air_fall-00 重出、落格与自签 2026-11-10（air 组 2/2）

- 口径：只引 `pixel-raw-01`（SHA `0d5b6bc69784eb67542265d4243159f01c9faae332b399601d2cb1d3b3e2de3d`），固定比例 `154/1447=0.10642709`，192 格、根点 [96,184]、同一 32 色板、二值 Alpha（源 α≥128）、非技能帧整帧单连通、严格 4× 逐像素重复；未逐帧归一、未局部缩头、未裁切。`heavy-00` 未动，旧刹车维持。
- 请求：`image-65174-1158`，`codex/gpt-image-2` / high / transparent，请求与实收 1024×1536 RGBA，1,600,094 bytes，源 SHA `040badf49960a60c1aa07375278bd48458d55e2f15b9ca6e28db7d26ba8abcf1`；提示词 184 字，未写“头不要变大/压低披风”一类措辞（披风上飘是本帧正确画法）。
- 落格：源 α≥128 bbox [21,13,845,1521]（825×1509）→ 88×161，offset [47,14]；原生 bbox [47,14,134,174]，161×88，32 色，整帧单连通（1 块 5,865px）；最低轮廓 174（同组 takeoff-01=174 先例），蓝胸灯中心 114.40（对锚约 114.35）。
- 头门（本帧关键，按修正口径）：眼列 108，头部列带 [82,134]，冠顶 18，眼行 35，**冠顶→眼 17（门 ≤18）**；眼行头壳 29（门 ≤30，在原生 192 格 PNG 上量，各行 run 29/29/29/29/28）。整帧 Alpha 最高行 14，冠顶 18，**差 4**——本帧红披风确实高过头顶，按旧口径会量出 21（>18），即此前误判的成因。
- 输出：原生 `stage1/cells/air_fall-00-cell.png`，9,528 bytes，SHA `1ae9870d71bb97f5845f24ac39356e615782b560c7844dfe37b19e8e80ebcecd`；严格 4× `stage1/cells/x4/air_fall-00-x4.png`，768×768，18,242 bytes，SHA `105e4b76a457de9403976cbcf51e4e101522ecbe5c47ed77036655ed5bc494c9`，逐像素重复、加色 0；复核图 `stage1/cells/review-air_fall-00-2026-11-10.png`，1840×1000，523,231 bytes，SHA `e03356ae9a4f696a1ff8bb07ba4be4f2a56e740b99e728f10d4a7de5e944a655`。
- 联系表：`stage1/air_rise/contact-air-2026-11-10-rework.png`，1260×760，120,248 bytes，SHA `b3b751e9a12491369e0469adb77160060f5ebe6ff81bcefb2dd3c71dde8d10d8`；含身份锚 + air_rise-00 + air_fall-00。旧 `contact-air-2026-11-10.png` 的红色阻塞槽保留为历史，不代表当前状态。
- 签署：机器门与目视造型核对通过，按 `auto_pass_2026_11_10` 自签为 `root_delegated_by_user`，`user_reviewed=false`，不是 `user_approved`、不是用户亲审。第一次生成即通过，未用第二种修法、未触发刹车。组状态 `air_rise_00_air_fall_00_root_signed_complete_2of2`。
- 已知差异：披风高过头顶 4px（正确画法，保留）；自动颈线头高标尺本帧未运行，不填猜测值。
- 未做：`air_rise→air_fall→land` 接续、实速、双朝向未验；安装、运行时、Godot 启动、提交/推送、录屏；720/1080、声音未验。
- 下一步：继续后续动作组；不安装、不启动 Godot、不提交、不录屏。

## 全 46 格并排复核与联系表 2026-11-10（air 组收口后；历史，已被下下节 47 格表取代）

- 触发：`air_fall-00` 重出落格后，按 `docs/HANDBOOK.md` 第 6 节把本角色全部已落格帧并排看一次，确认没有因重出而出现比例/尺度漂移。
- 独立硬门复检（不引用旧记录，直接读 46 个 PNG）：192×192 全部一致；Alpha 仅 0/255；≤32 色；最低轮廓 ≤183；非技能帧整帧单连通（技能帧 light1-00…light3-03 只判人物主体）。**0 例外**。`heavy-00` 无落格文件，未计入。
- 联系表：`art/fighters/mother-of-ultra/stage1/cells/review-all-46-2026-11-10.png`，3162×2764，644,512 bytes，SHA `a17693a419dda78dd9c3e66a39955d3f894a102dce7ae7da86a975830dfb5071`；46 格原生 2× 并排、逐格标帧名，另留 `heavy-00` 红色阻塞槽。该表为 heavy-00 落格前版本，已由下节 47 格表取代并删除。
- 目视：同一固定比例、同一根点，idle→walk→dash→takeoff→air→land→light→heavy→受击/倒地/起身/胜负/KO 的头壳宽、肩宽、四肢粗细无逐帧漂移；`air_fall-00` 与 `air_rise-00`、`takeoff-01` 的腾空高度分层合理（最低轮廓 160 / 174 / 174）。
- 保留的已知差异（不返修）：`takeoff-01` 前倾大、`land-00` 冠顶→眼 18、`land-01` 头壳 30 与深蹲站高 123、`air_rise-00` 单臂上举不对称、`idle-candidate-01` 站距 0.5649。
- 未做：实机双朝向、720/1080、实速接续、声音；安装、Godot 启动、提交/推送、录屏均未做。

## heavy-00 换工序重做 2026-11-10（锚派生像素比例导引，heavy 组 4/4）

- 起因：`heavy-00` 旧工序三次在头部比例门未过（raw-01 冠顶→眼 19/头壳 31、raw-02 19/30、raw-03 19/31；锚 17/28–29），同提示词重掷与“头部保持正侧、不低头”两种修法已用完，按返工刹车停。本轮不退回改提示词措辞，改工序。
- 工序：身份锚 `stage1/cells/idle-candidate-01-cell.png`（SHA `96ab6aa6cf19ca26b2ca9ce5981067e558f7e2d3f629e6655f9230d800ddcdf4`，192×192）按锚 raw 占位最近邻放大 → 居中裁 1024×1536 → 叠加辅助标记作**唯一参考**：洋红细线标眼行、冠顶行、头部列带边界；青色竖线标头壳左右缘；线外空白写小字“冠顶→眼 17 像素 / 头壳宽 28 像素”。
  - 导引 v1（已删）：192 画布严格 8×（1536²）后水平居中裁 1024×1536。人物只占画面宽 744/1024，模型按画面占比把人物缩小。`raw-01` 落格后整体高 130、冠顶→眼 14、头壳 23，属工序占位错误，拒收；未在同一导引上重掷。文件删除，SHA `0ea7c7b2d5d6da8b79cdf44909a610b4a9487b430162eb319e09001f6dd066cc`、63,406 bytes 保留在记录。
  - 导引 v2（现用）：192 画布 9.396×（=1447/154）最近邻到 1804²，按人物 bbox 居中裁 1024×1536；人物占画面高 1447、宽 874，与锚 raw 占位一致。文件 `stage1/heavy/references/heavy-guide-anchor-8x-2026-11-10.png`（沿用本轮任务指定文件名；实际放大 9.396×，倍率以记录为准），1024×1536 RGBA，68,844 bytes，SHA `200dc54b74633b73a49086e726cd41fd62597217ed31e77656b5c8744d03bb80`。导引自测：冠顶 y30、眼行 y47、冠顶→眼 17、眼行头壳 27（最宽 28，行 48）、眼列 109、头部列带 x83–135。
- 生成：MCP `magpie-image`，`codex/gpt-image-2`，quality high，background transparent，size 1024x1536，n=1；生成 ID `image-65174-1163`；实收 1024×1536 RGBA，Alpha 0–254（255 级），1,404,861 bytes，SHA `b846888a944b3729ea76c8d091afe793aad2092b82b454b54312dd1e0c62f924`。参考图只有导引 v2 一张；提示词 176 字，只写本帧动作并显式写“头部尺寸与参考完全一致：冠顶到眼 17 像素、眼行头壳宽 28 像素，不得拉长头冠或放大头部；不画导引辅助线、网格、文字、边框”。未追加其它角色、旧动作帧或第二张参考；生成图未复制洋红/青色辅助线（0 px）。
- 落格：源 α≥128 bbox [65,152,942,1475]（878×1324）→ 93×141，offset [47,43]；原生 bbox [47,43,139,183]，站高 141（屈膝起手姿势）、宽 93、32 色、Alpha [0,255]、整帧单连通（1 块 5,461px）、脚底 183（181/182/183 靴底轮廓）、脚底带重心 96.057、脚外缘间距 93（/141=0.6596）。
- 头门（头部列带口径）：眼列 104，头部列带 [78,130]，冠顶 43，眼行 59，**冠顶→眼 16（门 ≤18，锚 17）**；眼行头壳 27（门 ≤30），全头最宽 27（行 55）。整帧 Alpha 最高行 43，与冠顶同；本帧披风未高过头顶，仍按头部列带量。未局部缩头。
- 输出：原生 `stage1/cells/heavy-00-cell.png`，9,476 bytes，SHA `f0f5a8fc6dc3cf8037f2ce5834c7af1fea1092a1860added49a83cd47b4689f2`；严格 4× `stage1/cells/x4/heavy-00-x4.png`，768×768，17,894 bytes，SHA `bf25ce48071680911d65d7f9b6314ae3dcbceccf7a35a1747d06cf86aa42275f`，逐像素重复、加色 0；复核图 `stage1/cells/review-heavy-00-2026-11-10.png`，1840×1000，365,507 bytes，SHA `f89e4d9a97bcb92c0e1206e2011b0f85aa67e673aaf98bd9f49e108569c4eec0`。
- 联系表：`stage1/cells/contact-heavy-2026-11-10-rework.png`，2112×780，159,053 bytes，SHA `5aa2ffe1756b2d8ea01115a50ad132192371164d85d2040ae41ad0be708d686e`；含身份锚 + heavy-00…03。旧 `contact-heavy-2026-11-10.png`（heavy-00 红色阻塞槽）仍被 `requests.json` 的 heavy 请求收据引用，按请求对应关系保留，不代表当前状态；`review-all-46-2026-11-10.png` 是 heavy-00 落格前版本，已被下节 47 格表取代并删除。
- 诊断图：`stage1/diagnostic/heavy00-guide-rework-2026-11-10.png`，1660×1400，270,773 bytes，SHA `f94d1b13c0e41bf259b270cbb44fb1cd260bb20187a2123c4e178a0c6bbb4e33`；含导引 v2、实收 raw-02、raw-02 落格 2×、raw-01 落格 2×（缩身，已删源）、锚与 heavy-00 头部 8× 对照。
- 签署：机器门与目视造型核对通过，按 `auto_pass_2026_11_10` 自签为 `root_delegated_by_user`，`user_reviewed=false`，不是 `user_approved`、不是用户亲审。组状态 `heavy_00_04_root_signed_complete_4of4`；`cells.json` 的 `action_frames` 追加 heavy-00，`heavy_batch_2026_11_10.frames[0]` 已改为落格记录，旧三次 attempts 保留在 `attempts_heavy_00` 与 `blocked_frames` 历史字段。
- 已知差异（保留、不返修）：冠顶→眼 16 比锚 17 少 1px（同口径量化/姿势差，未缩头）；站高 141 为屈膝起手姿势，与 heavy-01 的 140 同档，未逐帧归一。
- 未做：安装、运行时、Godot 启动、提交/推送、录屏；720/1080、双朝向、实速、声音、重击命中/取消/击退判定均未验。
- 下一步：heavy 组 4/4 自签完成；继续其余动作组或按用户新指令；不安装、不启动 Godot、不提交、不录屏。

## 全 47 格并排复核与联系表 2026-11-10（heavy-00 落格后）

- 触发：`heavy-00` 补落格并自签后，重出全帧联系表，替换 heavy-00 落格前的 46 格表；同时按 `docs/HANDBOOK.md` 第 6 节重跑一次整角色并排复核。
- 独立硬门复检（直接读 47 个 PNG，不引用旧记录）：192×192 全部一致；Alpha 仅 0/255；≤32 色；最低轮廓 ≤183；非技能帧整帧单连通（技能帧 light1-00…light3-03 只判人物主体）；`x4/` 47 个文件逐一与原图最近邻 4× 逐像素相等。**0 例外**。
- 联系表：`art/fighters/mother-of-ultra/stage1/cells/review-all-47-2026-11-10.png`，3180×2508，559,576 bytes，SHA `11cf3f9644d57231798ca1fff3c5a55e17ef97210ce7c179ac7c0ce3bcd701d1`；47 格原生 2× 并排（8 列×6 行，末格空），逐格标帧名，无阻塞槽。记录写入 `stage1/cells/cells.json` 的 `all_frames_review_sheet_2026_11_10`。
- 目视：idle→walk→dash→takeoff→air→land→light→heavy→受击/倒地/起身/胜负/KO 的头壳宽、肩宽、四肢粗细无逐帧漂移；`heavy-00` 与 heavy-01…03 接续（起手沉身→蓄势→命中→收招），脚底同为 183。
- 保留的已知差异（不返修）：`takeoff-01` 前倾大、`land-00` 冠顶→眼 18、`land-01` 头壳 30 与深蹲站高 123、`air_rise-00` 单臂上举不对称、`idle-candidate-01` 站距 0.5649、`heavy-00` 冠顶→眼 16。
- 未做：实机双朝向、720/1080、实速接续、声音；安装、Godot 启动、提交/推送、录屏均未做。

## 2026-11-12 special2 落格与招式重算

- special2 16 帧沿用身份锚比例 0.098674、目标站高 140、192 格、根点 [96,184]、接地脚底 183；落格高 133–144、32 色、二值 Alpha、单连通、无裁切。逐帧 bbox/SHA 见 `stage1/cells/cells.json`。
- special2 招式保持 80 tick（32/32/16），按新图集重算 hurtboxes 并补齐重映射后缺失的空键；伤害、判定、发射 tick 不动。
- 全量 `tools/verify.py` 57 项 PASS（含此前修复的 mother/special2 规则校验）。root_delegated_by_user；无录屏，720/1080 双向实机未验。

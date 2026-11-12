# 佐菲 画布与根点

状态：图鉴已安装到 `assets/fighters/zoffy/catalogue/model-native.png` 并同步 `content/roster/catalogue_display.json`。2026-11-09 最终版按用户指定流程重做：先用图片模型生成真实皮套剧照（右侧视战斗架势），再以该照片为底用图片模型转像素整帧，最后经 `catalogue_native` 确定性降采样。战斗图仍未安装，未接运行时。

## 零、真实剧照→像素整帧（2026-11-09，当前安装）

- 流程（用户指定，不再用程序化滤镜替代图片模型）：
  1. 图片模型生成真实皮套剧照 `reports/zoffy/catalogue/photo-side-01.png`（1065×1476，真 Alpha，SHA-256 `623dd828916c3ac0e3d59b877a16ac5aa2fc6bdfbe2747dd5257b5e071cf82b6`），严格右侧视、错步战斗架势、头身比与官方剧照一致。
  2. 以该照片为底，图片模型转像素整帧 `reports/zoffy/catalogue/candidate-sprite-06.png`（SHA-256 `e2013fd4de8b3c1c35b419ad36b5af42d6a943889a54cb155ff5557469ab38a4`）。只按用户要求把头顶尖角改矮，其余不动。
  3. `catalogue_native` 降采样到 173 并落 384×256 画布：`reports/zoffy/catalogue/model-native-sprite-06-173.png`。
- 成品（HEAD 安装版）：bbox [136,75,243,248]；站高 173；宽 107；32 色；Alpha [0,255]；右侧视；脚底最后一行 247，基线 248；蓝计时器 18px 保留。
- 安装 SHA-256 `2607b58fd0a8a5d2c582f1cb9d821a6b5cde502189c6b23fd8e5b0f442a79fd8`。
- 工作树另有 1.5× 块化版：bbox [137,75,247,248]、宽 110、站高 173、32 色、二值 Alpha，SHA `addd0bcea67e5b7735f560b561bf028bf8e835662e22473f66fe17cd2eb6d9e4`，display 已指向它但尚未提交。提交前须先定用哪一版。
- 候选与淘汰理由见 `art/fighters/zoffy/sources/draft-20261108/requests.json` attempts 31–50（pose-n…z、photo-side-01、sprite-01…06）。
- 对比图：`reports/zoffy/catalogue/zoffy-*` 系列；最终版与已装初代/杰克/艾斯/泰罗同高对比见本机 reports（未入库）。

## 零·补、官方参考版重做（2026-11-08，已被 11-09 版替换）

- 规则（11-08 版，已被 11-09 版取代，仅存档对照）：图鉴、战斗待机、M87 姿势的基础生成必须以 `art/fighters/zoffy/sources/ref-01.webp` 为第一参考图；该图为官方剧照/皮套照（431×900，`reference_kind=official_still`，SHA-256 `0bcdab23478fb8645c8486ca8cc988df7dda911646b77e8bd6febafeef8fb37f`）。旧 draft-v2、旧 173、旧 154 只作第二参考与对照，不得覆盖。
- 请求记录：`art/fighters/zoffy/sources/draft-20261108/requests.json` 顶部 `reference_policy` / `reference_correction`；旧 attempts 7/8/15 已标 `superseded`，旧 selected 条目已标 `comparison_only`；新 attempts 16–18 均记录官方参考第一、旧 draft 第二、raw/成品 SHA 与选中理由。

### 1. 图鉴（官方参考版）

- `reports/zoffy/catalogue/model-native-officialref-173.png`
  - bbox [170,75,212,247]；站高 173；宽 43；26 色；8 连通单轮廓；Alpha [0,255]；右侧视；脚底最后一行 247，基线 248。
  - 头顶 75；颈 112；头高 37；头身比 4.68；头最大宽 27。
  - 蓝计时器 15px（0,101,210 + 2,78,150）；淡黄眼 18px（253,242,173）。
  - SHA-256 `1ee145e94364ee6cfb357babd9279f6333cde48f4fc52f7ccabaec780b18c514`。
  - raw：`.../official-ref/raw/catalogue-raw-01.png`，SHA `301a4c93b9733eb54626bdb79ba602b931c6afdd6c84f2efd1504db76b0e8a44`。
  - 白底 3×：`reports/zoffy/catalogue/model-native-officialref-173-x3-white.png`，SHA `8619f0eaf27db8081330799a24a12cd5dc3964fd244d92c1c41a7afa2f5929d9`。

### 2. 战斗待机（官方参考版 154）

- `reports/zoffy/battle/model-native-officialref-154.png`
  - bbox [52,30,141,183]；站高 154；宽 90；25 色；单连通；Alpha [0,255]；脚底 183 / anchor [96,184]；cell 192。
  - 头顶 30；颈 61；头高 31；头身比 4.97；头最大宽 26。
  - 蓝计时器 5px；淡黄眼 20px。
  - SHA-256 `1e2669c97a313227e71bbdecb41ce4f3280a4a717265902f27ece22985b3f4e2`。
  - raw：`.../official-ref/raw/battle-idle-raw-01.png`，SHA `1a6c330003f0648b41ba25610c335a3a83998ead2334c30ddbd4d8a3528514a1`。
  - 白底 3×：`reports/zoffy/battle/model-native-officialref-154-x3-white.png`，SHA `6142794e51fc44ab4c3e29c17dce669a3e290144aae3841f57239a85c424689b`。

### 3. M87 A 型姿势（官方参考版 154，开掌/指尖）

- `reports/zoffy/battle/m87-firing-pose-officialref-154.png`
  - bbox [51,30,168,183]；站高 154；宽 118；21 色；单连通；Alpha [0,255]；脚底 183 / anchor [96,184]。
  - 头顶 30；颈 61；头高 31；头身比 4.97；手部 bbox [153,64,168,76]。
  - 蓝计时器 6px；淡黄眼 26px。
  - SHA-256 `ae5c5b1596d2479157a6f1e6cb796452be42dd223ebec62cfac3999d04c06564`。
  - raw：`.../official-ref/raw/m87-pose-raw-01.png`，SHA `00777a56977e6f9f24129620b1f52a01de4c34c963566c495770ba420b37ba83`。
  - 白底 3×：`reports/zoffy/battle/m87-firing-pose-officialref-154-x3-white.png`，SHA `66e896ce19c68eb77fbb256343efcf55e2faed437fda002daf7c50f5ebe4c206`。
- 发射点：右手指尖前缘中心 cell (168,69)；前缘 y68–70，中心 69.0；局部（脚底根点，x 前/y 上）(72,115)；容差 2px，纵向误差 0。
- 镜像：按 anchor 镜像 cell (24,69)；局部 (−72,115)；实际像素镜像 x=23，差 1px，≤2px。
- 手部 6× 网格：`reports/zoffy/battle/near-hand-grid-officialref-154-x6.png`，SHA `bb122c1634ca8c1cb7bc67ae7b41908d23ce853709e0e64077fcc326d797eb5b`。
- 束根+命中场景：`reports/zoffy/fx/m87-scene-beam-impact-officialref-154.png`，SHA `6ffb9f8615e7b67e1752cf9915e5173d1a750965d8384f44ba21bdd027f547d1`。

### 4. 对比与保留

- 图鉴对比：`reports/zoffy/compare/zoffy-catalogue-officialref-173-vs-peers-native.png`（x2 同名 `-x2.png`）；SHA `84a6abc2139b332e7666201fbe51e5be36be1f0b40e59ee3680f2be1c3fd9b4c` / `d96ff34bfa82607d2d7dc97400f510991fc376198c1ff26d97b6fa195cc9c38f`。
- 战斗对比：`reports/zoffy/compare/zoffy-battle-officialref-154-vs-peers-native.png`（x2 同名 `-x2.png`）；SHA `fdca10add9e5c00506266ebc6a0b81a168bcce3aadacc1c491983a139a4a018e` / `bc9dc701480d54d7f69ee3d5867b3f9ec612f836037e63971eda7582caee2f2c`。
- 待机 vs M87：`reports/zoffy/compare/zoffy-officialref-idle-vs-m87-154-native.png`（x2 同名 `-x2.png`）；SHA `429f66171d7a58dffcaeb33694b25a5be6dbc483c31b15b67de7bfff34a95e54` / `a7f5a2765f8f222ec6ecb750317279b8363e36458ca8fa0cbe29910f1ca411f5`。
- 旧文件全部保留对照：图鉴 draft-v2 `8f9ff7...`、战斗 173 `cc57ef...`、M87 173 `20b8d61...`、旧 154 `ddd933...` / `f04fff...`；未覆盖。
- 原分片代理误装的 154px 窄侧视图（SHA `458b1f5c2edc91be1af17540f5fd1b0460e5069502a59923ac82d2d5df2fd1dd`）已由官方参考版 173 替换，display 的 SHA/站高/来源同步为 173 与 `mcp_image_to_image_from_official_reference`。
- 状态：图鉴已安装并通过 `catalogue_assets`、`catalogue-references`、`catalogue-idle`；战斗图未安装、未接运行时、未继续 7 张 FX、未做声音。

## 一、图鉴（旧 draft-v2，对照）

- 画布 384×256；根点 [192,248]；脚底基线 y=248（不透明最后一行 247）。
- 巨人标尺 3.84 px/m；45m → 173px（45×3.84=172.8，四舍五入 173；40m=154、50m=192）。
- 图鉴定稿：`reports/zoffy/catalogue/model-native-draft-v2.png`
  - bbox [170,75,213,247]；站高 173；宽 44；8 连通单轮廓；共享 32 色板实际用 27 色；Alpha [0,255]；朝向右侧。
  - 蓝计时器 6px（0,101,210 + 2,78,150）；淡黄眼 28px（253,242,173）。
  - 水平：bbox 中心 191.5，根点 192；脚底 247，差 1px 为基线留边。
  - SHA-256：`8f9ff7b56e8b9b377f850cceda5c75a7cd1796fbb0a2e6a02649a0989e5f564c`。
- 处理链：MCP 原图 → `tools/media/art/catalogue_native.py` 出 192 原生 → `tools/media/art/catalogue_rescale.py` 按 `content/roster/catalogue_scale.json` 的 45m→173 重新落位。
  - 不是拿整张 384 画布当分母；先用 Alpha 轮廓裁切，再按目标站高 NEAREST 缩放，脚底贴 248。
  - `catalogue_native.py` 默认 192 只是中间态；最终定稿以 173 为准。
  - 首版量化丢失蓝计时器；修正版从同一 raw 重新降采样，用共享 32 色板保留蓝/眼黄，几何与 Alpha 未变。
  - `tools/rebuild/shared/forge_backend.py` 本机缺 `~/.codex/skills/generate2dsprite`，本轮未用 forge，未冒称。
- 图鉴轮廓测量方法：头顶取 Alpha bbox 顶边；颈取头宽峰值行与肩起点之间最小宽度行；头高=颈相对行号；头身比=站高/头高。冠鳍计入头顶，与赛文同法。
- 该旧 draft-v2 只作对照，未安装；图鉴已改用官方参考版 173。

## 二、战斗（旧 173 draft，对照）

- cell 192×192；anchor [96,184]；脚底最后一行 183；1× 原生，不运行时缩放。
- 待机：`reports/zoffy/battle/model-native-draft-192.png`
  - bbox [47,11,144,183]；站高 173；宽 98；共享 32 色板实际用 29 色；单连通；蓝计时器 14px；眼黄 31px。
  - SHA-256 `cc57efc91bda5bde6668ff9115083befe0e0d0e36b7d056c0830bc6e68d31beb`。
- M87 姿势：`reports/zoffy/battle/m87-firing-pose-draft-192.png`
  - bbox [42,11,150,183]；站高 173；宽 109；共享 32 色板实际用 30 色；单连通；蓝计时器 12px；眼黄 30px。
  - 开掌版：右掌五指并拢前指，左掌开掌靠计时器；旧握拳版已覆盖删除。
  - SHA-256 `20b8d61b4e5d54f1bda406919b344f07a0601bc033308114f43b87a650d29c18`。
- 发射点：右手指尖前缘中心 cell (150,57)；前缘 y56–59，中心 57.5；局部（脚底根点，x 前/y 上）(54,127)；容差 2px。
- 镜像：按 anchor 镜像 cell (42,57)；局部 (−54,127)；实际像素镜像轮廓在 x=41，差 1px，仍 ≤2px 容差。
- 束/特效在 192 cell 之外由 attachment 层绘制；不裁人物、不缩人物、不为塞进 cell 改根点。

## 二·补 旧 154 身高对比（NEAREST 缩放，对照）

- 图鉴 173 保留（45m×3.84 标尺）；战斗另出 154 版，由 173 版 Alpha bbox 最近邻缩放，不重新生成、不重绘。
- 战斗待机 154：`reports/zoffy/battle/model-native-draft-192-h154.png`
  - bbox [52,30,138,183]；站高 154；宽 87；29 色；蓝计时器 14px；眼黄 20px；单连通；Alpha [0,255]。
  - SHA-256 `ddd933b99be0b01be1005d82463ca4ca7e14e04c95300d9df1f8807f3ce67a34`。
- M87 姿势 154：`reports/zoffy/battle/m87-firing-pose-draft-192-h154.png`
  - bbox [48,30,144,183]；站高 154；宽 97；29 色；蓝计时器 11px；眼黄 19px；单连通；Alpha [0,255]。
  - SHA-256 `f04fffa7a41b69fd3af062a652a9f7c5c13d823c735d8a58b428975b2c874093`。
  - 开掌/左掌靠计时器不变；手部 bbox [132,66,144,75]。
- 154 发射点：右手指尖前缘 cell (144,71)；前缘 y70–73，中心 71.5；局部（脚底根点）(48,113)；容差 2px，纵向误差 0.5px。
- 154 镜像：按 anchor cell (48,71)；局部 (−48,113)；实际像素镜像 x=47，差 1px，≤2px。
- 154 头身比：5.13（173 版 5.09；等比缩放后像素取整差，不是重新造型）。
- 对比图：`reports/zoffy/compare/zoffy-height-173-154-vs-peers-native.png`（x2 同名 `-x2.png`）；五格为佐菲173 / 佐菲154 / 初代140 / 艾斯145 / 赛文153，脚底同一行 183。
- 154 白底 3×：`reports/zoffy/battle/m87-firing-pose-draft-192-h154-x3-white.png`；手部 6× 网格：`reports/zoffy/battle/near-hand-grid-h154-x6.png`；154 束根场景：`reports/zoffy/fx/m87-scene-beam-impact-h154.png`。
- 建议：战斗用 154，图鉴保留 173；战斗 154 仅对比，未安装、未接线。

## 三、M87 特效原生尺寸

| 资产 | 原生 cell | 锚点 | 计划帧数 | 本轮关键帧 |
|---|---|---|---|---|
| muzzle | 128×64 | (32,32) | 4 | 蓄势、出膛 |
| beam | 448×64 | (0,32) | 4 | 主束、消散 |
| impact | 96×96 | (48,48) | 4 | 命中 |

- 主束实际 Alpha bbox 445×48（cell 448×64）；消散 441×48；均为 1×。
- 命中爆点由模拟给出；FX 锚点 (48,48) 只是命中帧内部的构图中心，不是固定屏幕坐标。
- Alpha：五帧均 [0,255]；≤32 色；无半透明边、无黑底、无棋盘格假透明。
- 与已装光线同档：塔罗 448×64（实际约 407×50）、艾斯 600×64（实际 443×42）；佐菲 448×64（实际 445×48）。
- 不循环平铺、不拉伸；光束是完整原生长束。若实际镜头宽度不足，按镜头方案处理，不偷偷缩放光效。

## 四、比较基准（已装角色）

- 图鉴站高：佐菲 173；初代 157；艾斯 154；赛文 154；杰克 154。
- 图鉴头身比：佐菲 4.81；初代 5.23；艾斯 4.81；赛文 4.05；杰克 5.31。
- 战斗站高：佐菲 173；初代 140；艾斯 145；赛文 153；杰克 140。
- 战斗头身比：佐菲 5.09；初代 5.19；艾斯 5.00；赛文 4.94；杰克 5.60。
- 脚底：图鉴全部 247（基线 248）；战斗全部 183（anchor 184）。
- 已装角色的战斗待机因屈膝低于其图鉴站高；比较时看头身比、脚底基线和像素密度，不把屈膝差当身高差。
- 以上数值为任务开始时已装成品基准，与 `reports/zoffy/compare/ultra-five-*-native.png` 第 2–5 格一致。
- 当前战斗 peers 为 140（初代/杰克）/145（艾斯）/153（赛文）；佐菲 173 会明显偏高。本轮已另出 154 对比版（见二·补），建议战斗用 154、图鉴保留 173；等图鉴分片跑完、peers 按 `catalogue_scale` 重缩放后，再做最终同屏身高判断。
- 2026-11-08 22:12–22:27，peers 的 `catalogue/model-native.png` 与根目录图被并发重画：catalogue 子目录出现 192px 站高，根目录出现窄侧视；本表未据此改写，也未改其素材。
- 杰克图鉴/根目录当时已是窄侧视（SHA `4302129906354ddcdc5a4fa2cceb76e71fca084b56ad1bb424406296987b35db`）；对比图第 5 格为任务开始时面板，头身比 5.31 按当时文件。

## 五、规则

- 固定右侧视、2D 像素整帧；不切肢、不骨骼拼片、不 IK、不旋转贴肢。
- 图鉴与战斗各自用原生画布；图鉴按 3.84 px/m 换算，战斗按同一 45m 站高 173 与已装角色比较。
- 图鉴/战斗/M87 三图共用一套 32 色板（实际用 27/29/30 色），保留蓝计时器与淡黄眼；不再分属两套红色。
- 不因局部 1px 细差反复拖住项目；错身份、断肢/开放缝、裁切、缺资源、不能运行仍须处理。
- 本轮未做 720/1080 实机检查、未做双向实机检查；只做了原生像素测量与左向镜像图的几何核对。

# 佐菲 specials 2026-11-10 制作报告

## 本轮完成

- 范围：佐菲 stage1 四个必杀动作共 **56 帧**：`special`（Z光线）16 帧、`special2`（超级冻霜）16 帧、`special3`（M87 A型）16 帧、`air_special`（空中 M87 改编）8 帧。
- 结果：**56/56 帧通过执行自检并落格**；本批只写 `art/`，未安装 `assets/`、未改 `content/`、未运行 Godot、未 git commit。
- 全部帧唯一参考为待机像素锚 `art/fighters/zoffy/stage1/idle/references/identity-pixel-x4.png`（440×692，SHA `2c4e85cbcc51ef5c011e724267de1be4859460a69f8b636339832a59b35c7da2`）。
- 56 帧均无光束、无气浪、无独立颗粒、无贴体光焰；出招帧最多有紧贴掌/指尖的微光，且光不外扩。实际光束与命中由运行时 FX 承载。
- 无录屏；未做 720/1080 与双向实机检查；不是用户亲审，root 签收待办。

## 生成与来源

- 生图：MCP `magpie-image`，模型 `codex/gpt-image-2`，quality `high`，请求尺寸 `1024x1536`；实收尺寸以逐帧为准（常见 `1000x1573`，`special3-02` 为 `1001x1572`，`air_special-00` 为 `1037x1517`，`air_special-02` 为 `1034x1520`），均为 RGBA。
- 请求数 **62**：通过 56 帧 + 淘汰 6 次；淘汰项与 SHA 见下文“拒收帧”。
- 每帧只附身份锚一张参考；没有追加其它角度、角色或成品。
- 提示词 150–250 字，只写该帧动作与光效，并显式要求“四肢粗细必须和参考图完全一致”，固定尾串交代头冠/眼睛/肩章/胸纹/蓝计时器、右侧视、完整不裁切、透明背景、无地面文字边框。

## 落格参数

- 工具：`tools/art/stage_cells.py`；全套共用比例 **0.099419**，源 `art/fighters/zoffy/stage1/idle/frames/raw-00-v3.png`（SHA `2d0392b089550e04142309a8770c2e4aab0f149e8e46509ad3fe1153b0a832ef`），目标站高 154。
- 制作格 192×192，根点 [96, 184]，脚底 183；腾空帧脚底行 **173**（沿用佐菲既有腾空帧脚底行 173（run-01/03、dash-02），不猜）。
- 色板取 `assets/fighters/zoffy/catalogue/model-native.png` 的 32 色（SHA `addd0bcea67e5b7735f560b561bf028bf8e835662e22473f66fe17cd2eb6d9e4`），整图统一映射。
- 硬门结果：56 帧全部主体单连通、Alpha 二值、色数 ≤32、格内未裁切；逐帧 bbox 见 JSON。

## 通过帧清单

### special（16 帧，光色 蓝白（Z光线））

通过：`special-00`、`special-01`、`special-02`、`special-03`、`special-04`、`special-05`、`special-06`、`special-07`、`special-08`、`special-09`、`special-10`、`special-11`、`special-12`、`special-13`、`special-14`、`special-15`。

- `art/fighters/zoffy/stage1/cells/special-00-cell.png`
- `art/fighters/zoffy/stage1/cells/special-01-cell.png`
- `art/fighters/zoffy/stage1/cells/special-02-cell.png`
- `art/fighters/zoffy/stage1/cells/special-03-cell.png`
- `art/fighters/zoffy/stage1/cells/special-04-cell.png`
- `art/fighters/zoffy/stage1/cells/special-05-cell.png`
- `art/fighters/zoffy/stage1/cells/special-06-cell.png`
- `art/fighters/zoffy/stage1/cells/special-07-cell.png`
- `art/fighters/zoffy/stage1/cells/special-08-cell.png`
- `art/fighters/zoffy/stage1/cells/special-09-cell.png`
- `art/fighters/zoffy/stage1/cells/special-10-cell.png`
- `art/fighters/zoffy/stage1/cells/special-11-cell.png`
- `art/fighters/zoffy/stage1/cells/special-12-cell.png`
- `art/fighters/zoffy/stage1/cells/special-13-cell.png`
- `art/fighters/zoffy/stage1/cells/special-14-cell.png`
- `art/fighters/zoffy/stage1/cells/special-15-cell.png`

### special2（16 帧，光色 淡青白（超级冻霜））

通过：`special2-00`、`special2-01`、`special2-02`、`special2-03`、`special2-04`、`special2-05`、`special2-06`、`special2-07`、`special2-08`、`special2-09`、`special2-10`、`special2-11`、`special2-12`、`special2-13`、`special2-14`、`special2-15`。

- `art/fighters/zoffy/stage1/cells/special2-00-cell.png`
- `art/fighters/zoffy/stage1/cells/special2-01-cell.png`
- `art/fighters/zoffy/stage1/cells/special2-02-cell.png`
- `art/fighters/zoffy/stage1/cells/special2-03-cell.png`
- `art/fighters/zoffy/stage1/cells/special2-04-cell.png`
- `art/fighters/zoffy/stage1/cells/special2-05-cell.png`
- `art/fighters/zoffy/stage1/cells/special2-06-cell.png`
- `art/fighters/zoffy/stage1/cells/special2-07-cell.png`
- `art/fighters/zoffy/stage1/cells/special2-08-cell.png`
- `art/fighters/zoffy/stage1/cells/special2-09-cell.png`
- `art/fighters/zoffy/stage1/cells/special2-10-cell.png`
- `art/fighters/zoffy/stage1/cells/special2-11-cell.png`
- `art/fighters/zoffy/stage1/cells/special2-12-cell.png`
- `art/fighters/zoffy/stage1/cells/special2-13-cell.png`
- `art/fighters/zoffy/stage1/cells/special2-14-cell.png`
- `art/fighters/zoffy/stage1/cells/special2-15-cell.png`

### special3（16 帧，光色 蓝白（M87 A型））

通过：`special3-00`、`special3-01`、`special3-02`、`special3-03`、`special3-04`、`special3-05`、`special3-06`、`special3-07`、`special3-08`、`special3-09`、`special3-10`、`special3-11`、`special3-12`、`special3-13`、`special3-14`、`special3-15`。

- `art/fighters/zoffy/stage1/cells/special3-00-cell.png`
- `art/fighters/zoffy/stage1/cells/special3-01-cell.png`
- `art/fighters/zoffy/stage1/cells/special3-02-cell.png`
- `art/fighters/zoffy/stage1/cells/special3-03-cell.png`
- `art/fighters/zoffy/stage1/cells/special3-04-cell.png`
- `art/fighters/zoffy/stage1/cells/special3-05-cell.png`
- `art/fighters/zoffy/stage1/cells/special3-06-cell.png`
- `art/fighters/zoffy/stage1/cells/special3-07-cell.png`
- `art/fighters/zoffy/stage1/cells/special3-08-cell.png`
- `art/fighters/zoffy/stage1/cells/special3-09-cell.png`
- `art/fighters/zoffy/stage1/cells/special3-10-cell.png`
- `art/fighters/zoffy/stage1/cells/special3-11-cell.png`
- `art/fighters/zoffy/stage1/cells/special3-12-cell.png`
- `art/fighters/zoffy/stage1/cells/special3-13-cell.png`
- `art/fighters/zoffy/stage1/cells/special3-14-cell.png`
- `art/fighters/zoffy/stage1/cells/special3-15-cell.png`

### air_special（8 帧，光色 蓝白（空中M87改编））

通过：`air_special-00`、`air_special-01`、`air_special-02`、`air_special-03`、`air_special-04`、`air_special-05`、`air_special-06`、`air_special-07`。

- `art/fighters/zoffy/stage1/cells/air_special-00-cell.png`
- `art/fighters/zoffy/stage1/cells/air_special-01-cell.png`
- `art/fighters/zoffy/stage1/cells/air_special-02-cell.png`
- `art/fighters/zoffy/stage1/cells/air_special-03-cell.png`
- `art/fighters/zoffy/stage1/cells/air_special-04-cell.png`
- `art/fighters/zoffy/stage1/cells/air_special-05-cell.png`
- `art/fighters/zoffy/stage1/cells/air_special-06-cell.png`
- `art/fighters/zoffy/stage1/cells/air_special-07-cell.png`

## 逐帧记录

### special

#### special-00

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-00.png`，SHA-256 `18c9c3a85be3df192b9c3bb1146426709c8ec052cd70ab648f1e4a446f035ce7`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-00-cell.png`，SHA-256 `bf0be144d18e8de71bae0c3e4703c36aa64e86111aa2841d9c7b631e73c5e4a6`。
- 落格：scale 0.099419，bbox [53, 30, 142, 183]，站高/内容高 154，头高 34（ratio 0.2208），色数 31，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌从护架抬起，在胸前掌心相对，两掌之间留约一掌宽的距离，双肘弯曲下沉，掌心朝向内侧，五指并拢张开，重心落在前后脚之间。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：胸前合掌蓄势起手，脸型、头鳍、勋章、蓝计时器与四肢粗细同锚；无光效。

#### special-01

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-01.png`，SHA-256 `6ec5f627f39ec6f80d41ff1cd1fca7a40e36aef1a1267a4cc58a16944087a658`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-01-cell.png`，SHA-256 `9f93c7f379de4b7ac914f9972b7639249f1c4b331b54264e612842bee6324a9d`。
- 落格：scale 0.099419，bbox [51, 34, 138, 183]，站高/内容高 150，头高 34（ratio 0.2267），色数 31，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌在胸前继续相对合拢，两掌间距收窄到半掌，双肘夹紧，上身略向前倾，五指并拢张开，前后脚屈膝，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：双掌相对收窄，造型同锚；无光效。

#### special-02

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-02.png`，SHA-256 `c7bf8ab3ba120cb9cc22e42dc342569134cb7d58e138c11b3baf9584c2cc3137`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-02-cell.png`，SHA-256 `50c247d3d39ea23552620ff285a1d29bd19c863a3ff71642bee36c2213705413`。
- 落格：scale 0.099419，bbox [49, 30, 142, 183]，站高/内容高 154，头高 34（ratio 0.2208），色数 31，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌几乎贴在一起，掌心相对，指尖朝前上方，双肘收紧，肩背下沉，五指并拢张开，重心稳定，前后脚屈膝，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：双掌近合，蓄势成立；造型同锚；无光效。

#### special-03

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-03.png`，SHA-256 `4dd2091c36ce9a5bc5b1eb392453288c56faf625622d8ea2e9893bf0531de02a`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-03-cell.png`，SHA-256 `ead43e1f876d5cad44e05ba48fe681a8d337ab646f7eeddac2154a847756e3e2`。
- 落格：scale 0.099419，bbox [50, 31, 142, 183]，站高/内容高 153，头高 34（ratio 0.2222），色数 30，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌在胸前正中合拢蓄势到最紧，掌心相对，双肘夹紧，上身微微前压，双膝下沉，五指并拢张开，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：胸前合掌蓄势到位；造型同锚；无光效。

#### special-04

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-04.png`，SHA-256 `f7f86a2884a017a8b0345de1b39c53ca62152a3a75bb390c190cdb2c3ee902a1`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-04-cell.png`，SHA-256 `3af766e0aad951c776c1b60c8f3bb5344fed748ac7ff5c90d0214b758895e8a4`。
- 落格：scale 0.099419，bbox [51, 41, 142, 183]，站高/内容高 143，头高 27（ratio 0.1888），色数 31，连通块 1，脚底行 183，腾空 否。
- 自动提示：special-04: 头高 29 偏离参考帧换算的 34 超过 ±8%，须目视核对；special-04: 站高 147 偏离目标 154 达 5%，若为屈膝压低可保留，否则须目视核对；special-04: 头高 27 偏离参考帧换算的 34 超过 ±8%，须目视核对；special-04: 站高 143 偏离目标 154 达 7%，若为屈膝压低可保留，否则须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌在胸前合十并拢，掌心相贴不分开，像推开一扇门一样一起向前伸出约半个前臂，双手明显离开胸口，双肘弯曲，重心下沉，前后脚屈膝，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：双掌并拢前推约一半；手位略高于05–07，作过渡帧保留；头高27系前伸手臂干扰，头部与锚一致。

#### special-05

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-05.png`，SHA-256 `3b652a9e7414ea8e248965f227cd4b01137baadf5cd4b5e04d42260eefc7f33d`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-05-cell.png`，SHA-256 `7e49ccba1b81fa82879fdecf41f35a730fd0008e0b4d9374470f20fd25f82a1b`。
- 落格：scale 0.099419，bbox [49, 42, 142, 183]，站高/内容高 142，头高 11（ratio 0.0775），色数 30，连通块 1，脚底行 183，腾空 否。
- 自动提示：special-05: 头高 29 偏离参考帧换算的 34 超过 ±8%，须目视核对；special-05: 头高 11 偏离参考帧换算的 34 超过 ±8%，须目视核对；special-05: 站高 142 偏离目标 154 达 8%，若为屈膝压低可保留，否则须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌保持并拢，掌心相对贴合，不分开，继续一起向前推出，双臂向前伸至约一半多，肘部仍微屈，双手离开胸前，肩背前送，重心下沉，前后脚蹬稳，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：双掌并拢前推，掌根朝右前；头高自动值受前伸手臂干扰，头部与锚一致。

#### special-06

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-06.png`，SHA-256 `5ae561879806ee9017f55b31cad1494b885397c666a610a3815de65e944fd7b4`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-06-cell.png`，SHA-256 `ad654eb46c83c8fb8e6a9ba99c744b8df8f560c9359fc96cdbe68f70900ea2d3`。
- 落格：scale 0.099419，bbox [52, 30, 147, 183]，站高/内容高 154，头高 60（ratio 0.3896），色数 31，连通块 1，脚底行 183，腾空 否。
- 自动提示：special-06: 头高 28 偏离参考帧换算的 34 超过 ±8%，须目视核对；special-06: 头高 60 偏离参考帧换算的 34 超过 ±8%，须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌保持并拢，掌心相对贴合，不分开，前推到接近伸直，双臂近水平向前伸出，肘部微屈，双手远离胸口，上身略前压，前后脚蹬稳，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：双掌并拢前推接近伸直；头高自动值受前伸手臂干扰，头部与锚一致。

#### special-07

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-07.png`，SHA-256 `bfeb44e4045339b5edd301fe8c940115200d5877fe2d60d94318a113dd021492`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-07-cell.png`，SHA-256 `a7eef778f8ea492d6462c7a9c16a91f6ed015d3b7fb64a294725046afa3570f1`。
- 落格：scale 0.099419，bbox [49, 30, 143, 183]，站高/内容高 154，头高 29（ratio 0.1883），色数 32，连通块 1，脚底行 183，腾空 否。
- 自动提示：special-07: 头高 29 偏离参考帧换算的 34 超过 ±8%，须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌并拢，掌心相对贴合，继续向前推至约六成，双臂向前半伸，手腕绷直，双肘微屈蓄力，双手离开胸前，准备完全前推，重心压在前脚，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：双掌并拢前推约六成，准备发射；造型同锚。

#### special-08

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-08.png`，SHA-256 `06993f6b82ab11b6837a4492b07c74ca834cbe59179fb2d895197035b1a704f8`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-08-cell.png`，SHA-256 `b39aafcd839fd7d680830a8d09f15b42a922f64cc64340f46331c93c13293b49`。
- 落格：scale 0.099419，bbox [48, 37, 141, 183]，站高/内容高 147，头高 33（ratio 0.2245），色数 31，连通块 1，脚底行 183，腾空 否。
- 自动提示：special-08: 站高 147 偏离目标 154 达 5%，若为屈膝压低可保留，否则须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双臂完全前伸，双掌并拢向前推出，掌根朝右，掌心朝右前方，腰身后坐，前后脚蹬稳，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。掌心有紧贴掌心的蓝白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：双臂前伸、双掌并拢发射相；贴掌蓝白光未外扩成束；造型同锚。

#### special-09

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-09.png`，SHA-256 `650fe1cd516f5873d5781846f24e449e78c89ab77a4a9c3315685bde4fd824b6`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-09-cell.png`，SHA-256 `351377593213aedf2045267728f832becb5ee7b6db016f7fd47c99b44ea1b6ca`。
- 落格：scale 0.099419，bbox [52, 30, 145, 183]，站高/内容高 154，头高 29（ratio 0.1883），色数 32，连通块 1，脚底行 183，腾空 否。
- 自动提示：special-09: 头高 29 偏离参考帧换算的 34 超过 ±8%，须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：保持双臂前伸、双掌并拢前推的发射姿势，掌根朝右，肩背稳定，腰身后坐，前后脚蹬稳，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。掌心有紧贴掌心的蓝白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：保持发射相；头高自动值受前伸手臂干扰，头部与锚一致。

#### special-10

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-10.png`，SHA-256 `9c2295e5c8dae6c991d40118fd4031009a19cc7d549da4c45d20d8097e8cafbb`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-10-cell.png`，SHA-256 `68607737ee4ab4064f4ae0a6a8ac7273e2aced3269a9561633850e1aac4712f2`。
- 落格：scale 0.099419，bbox [50, 30, 145, 183]，站高/内容高 154，头高 28（ratio 0.1818），色数 31，连通块 1，脚底行 183，腾空 否。
- 自动提示：special-10: 头高 28 偏离参考帧换算的 34 超过 ±8%，须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：保持前推发射，双臂伸直，双掌并拢，掌根朝右，腰身稳定，前后脚不离地，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。掌心有紧贴掌心的蓝白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：保持发射相；头高自动值受前伸手臂干扰，头部与锚一致。

#### special-11

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-11.png`，SHA-256 `82bd8a54e11d58ae596defc31e3595fc5a9151f22d694a1248180ee320a70aec`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-11-cell.png`，SHA-256 `363f94da9934342522e44a2e20083bf44663898be5f64d94f504851fa186e795`。
- 落格：scale 0.099419，bbox [49, 30, 143, 183]，站高/内容高 154，头高 60（ratio 0.3896），色数 31，连通块 1，脚底行 183，腾空 否。
- 自动提示：special-11: 头高 60 偏离参考帧换算的 34 超过 ±8%，须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：保持前推发射，双臂伸直，双掌并拢，掌根朝右，肩背平稳，前后脚蹬稳，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。掌心有紧贴掌心的蓝白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：保持发射相；头高60系前伸手臂干扰，头部与锚一致。

#### special-12

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-12.png`，SHA-256 `126e36189eddce5da07b6be4cf653dac9f30036f77d8caac83dc756ea222388e`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-12-cell.png`，SHA-256 `541040c5ae748fd5d7e6758ef69006325efe6f4a1cfe44b6f82f2d9e8276f022`。
- 落格：scale 0.099419，bbox [64, 32, 129, 183]，站高/内容高 152，头高 33（ratio 0.2171），色数 31，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双臂开始回收，双掌分开到约一掌宽，掌心相对，肘部弯曲，重心开始回升，五指并拢张开，前后脚站稳，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：开始回收，双掌分开；造型同锚。

#### special-13

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-13.png`，SHA-256 `bd338ddfb90f60e54e764db73e2d94666c342bf4c190a577e575a84b430b5a79`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-13-cell.png`，SHA-256 `852d96cdc124864ecdd0c553439550cc2c590906a892208a08b7f39ba7155945`。
- 落格：scale 0.099419，bbox [54, 30, 140, 183]，站高/内容高 154，头高 33（ratio 0.2143），色数 31，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌收回到胸前，掌心相对但不再贴合，肘部下沉，肩背放松，前后脚站稳，五指并拢张开，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：双掌回胸前；造型同锚。

#### special-14

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-14.png`，SHA-256 `2c78bf25ca4d8f22db8a9cd32c0de0f272fecad88c6eec880325a1c07a30b8c4`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-14-cell.png`，SHA-256 `6100ea660de383ee9bddf04e1b6e34973c9a6feac3836127fc0e0ad9ff4cb16c`。
- 落格：scale 0.099419，bbox [69, 31, 126, 183]，站高/内容高 153，头高 34（ratio 0.2222），色数 30，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌回落到护架前方，手指开始收拢，重心回到两脚之间，双膝微屈，准备回到待机，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：回落护架前；造型同锚。

#### special-15

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special/frames/raw-15.png`，SHA-256 `1b3f90a2ff921cfe60c8eefebff32a55577fbbbee45dce9369f72e4e30f906e9`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special-15-cell.png`，SHA-256 `ad4e488e170d89aaa83b2e1432f6f57555fc0ab606d5844be3de2375eb5ce0c6`。
- 落格：scale 0.099419，bbox [59, 31, 135, 183]，站高/内容高 153，头高 34（ratio 0.2222），色数 31，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：回到双拳抬到胸前的格斗护架，双脚错步屈膝，双拳护在胸前，重心落在两脚之间，视线朝前，与参考图的待机架势一致。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：回到双拳护架，与待机锚一致。

### special2

#### special2-00

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-00.png`，SHA-256 `a0334292a59a3f46213c3491bd73eee42b8fb916f28bd6f61dc666cbaaaa2d78`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-00-cell.png`，SHA-256 `37be6736f8b5ab583acaaec034a054ce19fa4589807fc2c44cd1ecdf981aa738`。
- 落格：scale 0.099419，bbox [50, 30, 143, 183]，站高/内容高 154，头高 34（ratio 0.2208），色数 31，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌从护架抬到胸前，指尖相对，掌心朝内，双肘自然弯曲，五指并拢张开，重心落在前后脚之间，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：胸前指尖相对起手；造型同锚；无光效。

#### special2-01

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-01.png`，SHA-256 `d73dd7cba83be67d81ec8db064480aed49c2af98366fe72bf8036bad7fe3bd26`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-01-cell.png`，SHA-256 `7e1c7c0d60b385200ec0e1574a5202d772afd772405df4dd9cd837b637a956de`。
- 落格：scale 0.099419，bbox [50, 30, 142, 183]，站高/内容高 154，头高 28（ratio 0.1818），色数 32，连通块 1，脚底行 183，腾空 否。
- 自动提示：special2-01: 头高 28 偏离参考帧换算的 34 超过 ±8%，须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌在胸前靠拢，指尖相对，两掌间距收窄，肘部外展，上身略前倾，五指并拢张开，前后脚屈膝，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：双掌靠拢；头高28系姿势干扰，头部与锚一致。

#### special2-02

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-02.png`，SHA-256 `0af6239aadb22f0b7252e938919535ba080c18836c518b32f581bb3aa8464e05`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-02-cell.png`，SHA-256 `52c7f43358da7eda1c4e5188a5556908984ae2c339bbde6407e187302d205689`。
- 落格：scale 0.099419，bbox [50, 30, 143, 183]，站高/内容高 154，头高 34（ratio 0.2208），色数 32，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌指尖在胸前相触，掌心朝内，肘部抬起，肩背下沉，前后脚屈膝，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：指尖相触；造型同锚；无光效。

#### special2-03

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-03.png`，SHA-256 `14032af08b1fe61f2b915daa32d3af04d6331398a994cd9c6d0ebddfb947cf5c`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-03-cell.png`，SHA-256 `6c2066cba78061320c7aa2a4006d00303c8bb5350411ef56383a03b78fbddaa0`。
- 落格：scale 0.099419，bbox [50, 30, 142, 183]，站高/内容高 154，头高 34（ratio 0.2208），色数 31，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌在胸前合拢蓄势，指尖相对，手腕绷直，上身微微前压，双膝下沉，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：胸前合拢蓄势；造型同锚；无光效。

#### special2-04

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-04.png`，SHA-256 `ce6d2e500aa5928c4cceeb2cb217b15e87634e4716fbd5007efc13f8d95dc226`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-04-cell.png`，SHA-256 `c814f67e78a5fc190217ec8b2c25fdaebf75bdff721697c42751c9c4087aa7ac`。
- 落格：scale 0.099419，bbox [64, 50, 130, 183]，站高/内容高 134，头高 34（ratio 0.2537），色数 32，连通块 1，脚底行 183，腾空 否。
- 自动提示：special2-04: 站高 134 偏离目标 154 达 13%，若为屈膝压低可保留，否则须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌合拢，从胸前向腹前下沉，屈膝下蹲，肘部贴身，掌心朝内，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：合拢下沉，深蹲为设计内；站高134为屈膝压低，头部与锚一致。

#### special2-05

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-05.png`，SHA-256 `ba39994cbe312bdb34e3f222be9a615fba20b7e84c5d3960afa87a1a9c49dcf9`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-05-cell.png`，SHA-256 `b1196d332070e90ffb3ecfa1e1eca5ca45992a89b79c1fb02b9b8e64c2d77d99`。
- 落格：scale 0.099419，bbox [51, 49, 136, 183]，站高/内容高 135，头高 29（ratio 0.2148），色数 32，连通块 1，脚底行 183，腾空 否。
- 自动提示：special2-05: 头高 29 偏离参考帧换算的 34 超过 ±8%，须目视核对；special2-05: 站高 135 偏离目标 154 达 12%，若为屈膝压低可保留，否则须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌合拢沉到胸腹之间，指尖相对，肩背下沉，双膝继续弯曲，上身略前倾，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：继续下沉；站高135为屈膝压低，头高29系姿势干扰。

#### special2-06

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-06.png`，SHA-256 `4c0282c7cf8cea9930072b450e647f9cbbc3a41f6c88ae5ea0208353bf833bc0`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-06-cell.png`，SHA-256 `b03bf532b8d1f863776e19eb57878f45a36bfd85ad0f12c38b45fffc839c3150`。
- 落格：scale 0.099419，bbox [46, 60, 137, 183]，站高/内容高 124，头高 9（ratio 0.0726），色数 31，连通块 1，脚底行 183，腾空 否。
- 自动提示：special2-06: 头高 9 偏离参考帧换算的 34 超过 ±8%，须目视核对；special2-06: 站高 124 偏离目标 154 达 19%，若为屈膝压低可保留，否则须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌在腹前合拢蓄势，指尖相对，重心压得更低，前后脚蹬稳，双掌准备向上推出，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：腹前蓄势最低点，深蹲为设计内；头高9为姿势干扰，头部与锚一致。

#### special2-07

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-07.png`，SHA-256 `db541325e76e8e26ce8f2b24fa404fcce897775ae6ac5a1959d82741a77ab804`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-07-cell.png`，SHA-256 `53cdf6648a553ada3fc7b559b02e6e191000d6703ffc9c685f6bde1a4cb91f08`。
- 落格：scale 0.099419，bbox [50, 30, 143, 183]，站高/内容高 154，头高 35（ratio 0.2273），色数 31，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌在腹前开始翻转，掌心转向前方，肘部抬起，上身随之上抬，双膝仍屈，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：起身翻掌，接08推掌；造型同锚。

#### special2-08

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-08.png`，SHA-256 `37f17dfbdb41d2d24d4dab48754b2c51c3c023b5714e40df298d6e61af2ae93c`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-08-cell.png`，SHA-256 `dde6865378301c76b6f1b97df67870f7aaf76d135812415952e81ac1d7d59dad`。
- 落格：scale 0.099419，bbox [52, 30, 146, 183]，站高/内容高 154，头高 60（ratio 0.3896），色数 31，连通块 1，脚底行 183，腾空 否。
- 自动提示：special2-08: 头高 60 偏离参考帧换算的 34 超过 ±8%，须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌由腹前向前上方推出，双臂半伸，掌心朝前，掌根略高，指尖朝上，重心开始回升，前后脚蹬稳，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。掌心有紧贴掌心的淡青白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：由腹前向前上方推出；掌心朝前；贴掌淡青白光未外扩。

#### special2-09

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-09.png`，SHA-256 `375cc77e625ac00ac843dd70aefb43bf886dfed56288f077419804569a751958`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-09-cell.png`，SHA-256 `51814cf459b9dc6d89fd3efe92c03d2c177e72a3245d96259a4d534917b4d01d`。
- 落格：scale 0.099419，bbox [52, 30, 148, 183]，站高/内容高 154，头高 60（ratio 0.3896），色数 32，连通块 1，脚底行 183，腾空 否。
- 自动提示：special2-09: 头高 60 偏离参考帧换算的 34 超过 ±8%，须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌推至前上方，双臂伸展，掌心朝前，指尖朝上，肩背前送，前后脚蹬稳，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。掌心有紧贴掌心的淡青白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：推至前上方；掌心朝前；头高60系前伸手臂干扰，头部与锚一致。

#### special2-10

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-10.png`，SHA-256 `03e296bd4a74a1ab801a9844919febc10decdced8cb582f1f370aa3a8682db2b`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-10-cell.png`，SHA-256 `8ac06dbfde6d33573dab06d4cfb7c794491715efcd0ff0b31fabcb0c5939464f`。
- 落格：scale 0.099419，bbox [49, 30, 145, 183]，站高/内容高 154，头高 60（ratio 0.3896），色数 31，连通块 1，脚底行 183，腾空 否。
- 自动提示：special2-10: 头高 60 偏离参考帧换算的 34 超过 ±8%，须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：保持双掌前上方推出的发射姿势，掌心朝前，指尖朝上，肩背稳定，前后脚蹬稳，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。掌心有紧贴掌心的淡青白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：保持发射相；头高60系前伸手臂干扰，头部与锚一致。

#### special2-11

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-11.png`，SHA-256 `8b04a13fa09a8ceb901b72254e2fa0665cba9120f380dbbc0c2a293756d1c659`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-11-cell.png`，SHA-256 `1e487ef062ba71c4ad8e642863d58b60b7e54ab5c90883dd98cf5b8dd1020f5b`。
- 落格：scale 0.099419，bbox [49, 30, 145, 183]，站高/内容高 154，头高 27（ratio 0.1753），色数 31，连通块 1，脚底行 183，腾空 否。
- 自动提示：special2-11: 头高 27 偏离参考帧换算的 34 超过 ±8%，须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：保持前上方推掌，双臂伸直，掌心朝前，指尖朝上，双肩平稳，前后脚蹬稳，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。掌心有紧贴掌心的淡青白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：保持发射相；头高27系前伸手臂干扰，头部与锚一致。

#### special2-12

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-12.png`，SHA-256 `96d18fb03a68dc48226abe76320e45e470f8641ed0fbe1e9fc4053e7c90e9c91`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-12-cell.png`，SHA-256 `32cfd82700db064936d7ad1477e07522959da8bbd917a00ac94fe8537f8a3d06`。
- 落格：scale 0.099419，bbox [51, 29, 147, 183]，站高/内容高 155，头高 58（ratio 0.3742），色数 32，连通块 1，脚底行 183，腾空 否。
- 自动提示：special2-12: 头高 58 偏离参考帧换算的 34 超过 ±8%，须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：保持前上方推掌，双臂伸直，掌心朝前，指尖朝上，腰身稳定，前后脚不离地，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。掌心有紧贴掌心的淡青白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：保持发射相；头高58系前伸手臂干扰，头部与锚一致。

#### special2-13

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-13.png`，SHA-256 `27d0c577d696686df1a989dd146638b2f7274077030e6674f950dd7ec3b267db`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-13-cell.png`，SHA-256 `782ab0e685a1d5ce5408ad88d8a5386606d2ffa885517a6dc60cf630c3e2f253`。
- 落格：scale 0.099419，bbox [51, 32, 142, 183]，站高/内容高 152，头高 34（ratio 0.2237），色数 32，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双臂开始回收，双掌降到胸前，掌心相对，肘部弯曲，重心回落，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：收臂回胸前；造型同锚。

#### special2-14

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-14.png`，SHA-256 `cc9462f6d8deffaa73a9a9851741d4528aa76ffaf2b5a74d77cfb39c32811d0c`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-14-cell.png`，SHA-256 `cb8047816a2f748ca7226f9c74ac70b78c1940458e1e073422e4b78accaddf14`。
- 落格：scale 0.099419，bbox [69, 31, 124, 183]，站高/内容高 153，头高 34（ratio 0.2222），色数 30，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌收在胸前，指尖相对，肘部下沉，肩背放松，脚步站稳，五指并拢，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：双掌收胸前；造型同锚。

#### special2-15

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special2/frames/raw-15.png`，SHA-256 `93a8cfd089b62943560fe390cdd7661985efebfd84bf47f0f5efe1d89b54c49a`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special2-15-cell.png`，SHA-256 `2b3573367bbf1d811fffa219ecfdf5664e77496e43954622ab04004e96a2d9b3`。
- 落格：scale 0.099419，bbox [60, 33, 134, 183]，站高/内容高 151，头高 34（ratio 0.2252），色数 32，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：回到双拳抬到胸前的格斗护架，双脚错步屈膝，双拳护在胸前，重心落在两脚之间，视线朝前，与参考图的待机架势一致。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：回到双拳护架，与待机锚一致。

### special3

#### special3-00

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-00.png`，SHA-256 `2b8bdf5778f6089c03fdd7483297ee675c2da764990048ffbb678f4fd5b53350`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-00-cell.png`，SHA-256 `f234a1fc7e5593590b6b06b7a26e90c413dc6fc4e07798aa105feddf0ce6315b`。
- 落格：scale 0.099419，bbox [49, 30, 145, 183]，站高/内容高 154，头高 36（ratio 0.2338），色数 32，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双臂抬到胸前平举，双掌相对，掌心相距约一掌，五指并拢张开，双肘弯曲，重心稳定，前后脚屈膝，视线朝前，全程不握拳横胸。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：胸前双掌相对蓄力；全程未握拳横胸；造型同锚。

#### special3-01

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-01.png`，SHA-256 `d58323139ba10b764f25e2fc64d63b595346f1c12e0c98d8370aee49155f5458`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-01-cell.png`，SHA-256 `ecfee9b2c13741163a2d10d1f17667758f770914c2ed438f8ffd99e95b93d421`。
- 落格：scale 0.099419，bbox [49, 30, 142, 183]，站高/内容高 154，头高 35（ratio 0.2273），色数 31，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌在胸前相对靠近，掌心相对，肘部抬起，肩背稳定，前后脚屈膝，五指并拢张开，视线朝前，全程不握拳横胸。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：双掌相对靠近；全程未握拳横胸；造型同锚。

#### special3-02

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-02.png`，SHA-256 `ad1ad15eabd9133c929036b9bc07ddaddb12bef91345b341415d7e82d4e4076f`；实收 1001×1572。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-02-cell.png`，SHA-256 `7b89846d95ab57c77cc2295c865c2fdc777897b0d988259fc0c3ebce919bef62`。
- 落格：scale 0.099419，bbox [49, 43, 139, 183]，站高/内容高 141，头高 27（ratio 0.1915），色数 30，连通块 1，脚底行 183，腾空 否。
- 自动提示：special3-02: 头高 27 偏离参考帧换算的 34 超过 ±8%，须目视核对；special3-02: 站高 141 偏离目标 154 达 8%，若为屈膝压低可保留，否则须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌在胸前相对蓄力，掌距收窄，指尖朝前，上身略前倾，前后脚屈膝，五指并拢张开，视线朝前，全程不握拳横胸。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：相对蓄力，屈膝下沉；站高141为设计内压低；头高27系姿势干扰。

#### special3-03

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-03.png`，SHA-256 `852c2311040f9825f32cdea284628fa44b9e5c352890d76c84ca59da7af75886`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-03-cell.png`，SHA-256 `991c703e583ba63cfe26f3732353492457444001448e58ddb8cefeeef0fc6658`。
- 落格：scale 0.099419，bbox [49, 30, 143, 183]，站高/内容高 154，头高 34（ratio 0.2208），色数 31，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌相对几乎贴合，掌心相对，手腕绷直，肩背下沉，前后脚屈膝，五指并拢，视线朝前，全程不握拳横胸。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：双掌近乎贴合；全程未握拳横胸；造型同锚。

#### special3-04

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-04.png`，SHA-256 `691cd4e926102496680105f2350f0a5f6e2620ee860000bb4b74a5973a1b7fd1`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-04-cell.png`，SHA-256 `101e1e7bcce6cd98cdd10fd630ca10263b0e3cea27d725242084512619aa11b6`。
- 落格：scale 0.099419，bbox [52, 32, 141, 183]，站高/内容高 152，头高 29（ratio 0.1908），色数 31，连通块 1，脚底行 183，腾空 否。
- 自动提示：special3-04: 头高 29 偏离参考帧换算的 34 超过 ±8%，须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌在胸前相对蓄力到位，掌心相距一拳，上身微微前压，双膝下沉，准备伸出右臂，五指并拢，视线朝前，全程不握拳横胸。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：蓄力到位；头高29系姿势干扰，头部与锚一致。

#### special3-05

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-05.png`，SHA-256 `071f20904ab90625b5df1766068fa19ef47c9c68d9cc08202dbb63c4c8222f6c`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-05-cell.png`，SHA-256 `b5e9864ee5ded746da35402e051120d4085e3e32cc22dd73071e56fa2ab9c395`。
- 落格：scale 0.099419，bbox [49, 30, 144, 183]，站高/内容高 154，头高 35（ratio 0.2273），色数 31，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：右臂开始向前伸直，右掌五指并拢，掌心朝前，左掌仍停在胸前，左肘弯曲，前后脚屈膝，视线朝前，全程不握拳横胸。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：右臂开始伸出，左掌在胸前；全程未握拳横胸；造型同锚。

#### special3-06

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-06.png`，SHA-256 `7c2cc443248cd750048fd072287e459adda995ee08547d2b448a60b62ee914f4`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-06-cell.png`，SHA-256 `9b42b74d16ea67becffbad3cfb171a40e61085bb8b08d41ee7a095d184002cd5`。
- 落格：scale 0.099419，bbox [50, 30, 147, 183]，站高/内容高 154，头高 33（ratio 0.2143），色数 32，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：右臂伸至七成，右掌五指并拢前指，左掌开掌靠近彩色计时器，腰身稳定，前后脚蹬稳，视线朝前，全程不握拳横胸。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：右臂伸至七成、五指并拢前指，左掌靠近计时器；造型同锚。

#### special3-07

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-07.png`，SHA-256 `592e65bdc610781b2f4fdf94b9da2caa6dd1bc2a6000797adf7af2e969379a7c`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-07-cell.png`，SHA-256 `9785d391a3639d42a2c3fb7cda6904432febbc95dedcdff640d21eea6483ff60`。
- 落格：scale 0.099419，bbox [50, 30, 147, 183]，站高/内容高 154，头高 36（ratio 0.2338），色数 31，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：右臂接近完全伸直，右掌五指并拢前指，左掌开掌贴到彩色计时器旁，前后脚蹬稳，肩背稳定，视线朝前，全程不握拳横胸。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：右臂接近伸直，左掌贴计时器；指尖完整未裁切；造型同锚。

#### special3-08

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-08.png`，SHA-256 `15877bfae2b999ebbfc0d86855fd9d0a9f28283370e11fe94e9922f5c618d424`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-08-cell.png`，SHA-256 `ec4bdf5deeaa055de53fd11163f718029d45a4ae58e4d4e5c14dcff897fb424f`。
- 落格：scale 0.099419，bbox [50, 30, 147, 183]，站高/内容高 154，头高 35（ratio 0.2273），色数 32，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：右臂完全伸直，右掌五指并拢前指，左掌开掌靠近彩色计时器，肩背稳定，腰身后坐，前后脚蹬稳，视线朝前，全程不握拳横胸。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。指尖有紧贴指尖的蓝白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：右臂伸直前指发射相，左掌靠计时器；贴指尖蓝白光未外扩；造型同锚。

#### special3-09

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-09.png`，SHA-256 `6bd5ee3607cbc9e1d4d478eb47872eeedcbf615ee950676c67e7e61b7a2d63ec`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-09-cell.png`，SHA-256 `eef1f353b4230a34434e509a67f28ebd55ff55f11d8fe8bfa51cb9a2a75f6ff9`。
- 落格：scale 0.099419，bbox [49, 29, 145, 183]，站高/内容高 155，头高 37（ratio 0.2387），色数 32，连通块 1，脚底行 183，腾空 否。
- 自动提示：special3-09: 头高 37 偏离参考帧换算的 34 超过 ±8%，须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：保持右臂完全伸直、右掌五指并拢前指的发射姿势，左掌开掌靠近彩色计时器，肩背稳定，前后脚蹬稳，视线朝前，全程不握拳横胸。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。指尖有紧贴指尖的蓝白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：保持发射相；头高37为前伸手臂干扰，头部与锚一致。

#### special3-10

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-10.png`，SHA-256 `7a63af12e012558fef73ece126e22d2a974ddd98813061c7a8491d02c38624fd`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-10-cell.png`，SHA-256 `8cd36f1229dda6ee19f5a13dd28d506532e38eb3a7be7690d9d459d27a04f5aa`。
- 落格：scale 0.099419，bbox [51, 30, 146, 183]，站高/内容高 154，头高 36（ratio 0.2338），色数 31，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：保持右掌前指发射，右臂伸直，左掌开掌靠近彩色计时器，肩背平稳，前后脚蹬稳，视线朝前，全程不握拳横胸。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。指尖有紧贴指尖的蓝白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：保持发射相；造型同锚。

#### special3-11

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-11.png`，SHA-256 `aff56db4863ef117cd754ce171638ad1bbd0c85f06862cf3dfffc0fe708d6242`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-11-cell.png`，SHA-256 `ad11d3c58090fa0c831ae667b87853a6897859dd5782ac440fb82d27c0dbf2cf`。
- 落格：scale 0.099419，bbox [50, 30, 147, 183]，站高/内容高 154，头高 38（ratio 0.2468），色数 31，连通块 1，脚底行 183，腾空 否。
- 自动提示：special3-11: 头高 38 偏离参考帧换算的 34 超过 ±8%，须目视核对
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：右臂水平向前伸直，与肩同高，右掌五指并拢平直前指，掌心朝下，左掌开掌平贴在彩色计时器旁，腰身稳定，前后脚蹬稳，视线朝前，全程不握拳横胸。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。指尖有紧贴指尖的蓝白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：修正后右臂水平前指，与08–10接续；头高38为前伸手臂干扰，头部与锚一致。

#### special3-12

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-12.png`，SHA-256 `db9506bce609ca1803df00c7c98fc5d5045a1e8199c91004f92b98d43f3954f3`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-12-cell.png`，SHA-256 `25652c85e15b21b0765d7a9d30c17e89cd7f601aee7184a3030b39b017773fc6`。
- 落格：scale 0.099419，bbox [49, 29, 142, 183]，站高/内容高 155，头高 35（ratio 0.2258），色数 30，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：右臂开始回收，右掌降到胸前，五指并拢，左掌离开计时器回到胸前，肘部弯曲，重心回落，视线朝前，全程不握拳横胸。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：收臂回胸前；造型同锚。

#### special3-13

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-13.png`，SHA-256 `3cc9a5cc5d9f2d747a71f6094a4d23bce8df58b83e6773a81b3b999ed3daba35`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-13-cell.png`，SHA-256 `34807fb482d02caa18fe8e916fd6c5e52f0070ceadb22136c89dd7828b087f56`。
- 落格：scale 0.099419，bbox [50, 30, 142, 183]，站高/内容高 154，头高 34（ratio 0.2208），色数 32，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双臂收回到胸前，双掌开掌，掌心相对，肘部下沉，肩背放松，前后脚站稳，视线朝前，全程不握拳横胸。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：双掌回胸前；造型同锚。

#### special3-14

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-14.png`，SHA-256 `52a478d755f5467ab03aaaa34a24269b04286c44eee2ef954fbff4af2d416e1f`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-14-cell.png`，SHA-256 `7e52f1ff80c38c01ab65209d710b208ab06298ff0656de414d72bd3af81967ac`。
- 落格：scale 0.099419，bbox [69, 31, 125, 183]，站高/内容高 153，头高 33（ratio 0.2157），色数 31，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：双掌回落到护架前方，手指开始收拢，重心回到两脚之间，双膝微屈，准备回到待机，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：回落护架前；造型同锚。

#### special3-15

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/special3/frames/raw-15.png`，SHA-256 `7b1b9f8f1ae0db71d060df1209be9fcd721fdbabeb4fa5539b2070fe27ccf0aa`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/special3-15-cell.png`，SHA-256 `3fb6863b2146b2bc4c4ff8c3b5a92274e6de442daab4b3593064660d93e5af90`。
- 落格：scale 0.099419，bbox [56, 31, 137, 183]，站高/内容高 153，头高 33（ratio 0.2157），色数 32，连通块 1，脚底行 183，腾空 否。
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：回到双拳抬到胸前的格斗护架，双脚错步屈膝，双拳护在胸前，重心落在两脚之间，视线朝前，与参考图的待机架势一致。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：回到双拳护架，与待机锚一致。

### air_special

#### air_special-00

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/air_special/frames/raw-00.png`，SHA-256 `b597f92de4ffdcfa456d6bb209fdea2d87585fc501b33f8b7bb6e54d019a52d1`；实收 1037×1517。
- 输出 cell：`art/fighters/zoffy/stage1/cells/air_special-00-cell.png`，SHA-256 `d2ce741ad969fb101d571b61fd1106a5637e734e24b1fbe791b7c57b0ad6d5aa`。
- 落格：scale 0.099419，bbox [60, 56, 147, 173]，站高/内容高 118，头高 9（ratio 0.0763），色数 31，连通块 1，脚底行 173，腾空 是。
- 自动提示：air_special-00: 非直立帧，头高 9、站高 118 仅供参考，需目视核对比例
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：全身腾空，双膝收起，双脚离地，右臂向后拉蓄势，右肘弯曲，右掌在肩后，左掌开在胸前，上身略前倾，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：腾空收腿、右臂后拉蓄势；脚底离地；造型同锚。

#### air_special-01

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/air_special/frames/raw-01.png`，SHA-256 `581fbd8353e9a70cfda1f44d8276d625a342af41dcf0a237f7fecb3eb181bc51`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/air_special-01-cell.png`，SHA-256 `449d25679f224baad95a05aa2ab9eab27a800cd940362cf52ecc1f93f277df1e`。
- 落格：scale 0.099419，bbox [56, 44, 135, 173]，站高/内容高 130，头高 10（ratio 0.0769），色数 31，连通块 1，脚底行 173，腾空 是。
- 自动提示：air_special-01: 非直立帧，头高 10、站高 130 仅供参考，需目视核对比例
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：全身腾空，双膝继续收起，双脚离地，右臂后拉蓄势更满，右肘后引，右掌在肩后，左掌开在胸前，腰身稳定，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：腾空后拉更满；脚底离地；造型同锚。

#### air_special-02

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/air_special/frames/raw-02.png`，SHA-256 `eb0952270b0643e09d0c09f936e49e1cf46563f6f85ef95227217970f3bf03ae`；实收 1034×1520。
- 输出 cell：`art/fighters/zoffy/stage1/cells/air_special-02-cell.png`，SHA-256 `a829e6e791dea2d7d7c1c0424d50bb1ff06aece6a0bc00c57d6b587da62275ca`。
- 落格：scale 0.099419，bbox [59, 58, 131, 173]，站高/内容高 116，头高 9（ratio 0.0776），色数 30，连通块 1，脚底行 173，腾空 是。
- 自动提示：air_special-02: 非直立帧，头高 9、站高 116 仅供参考，需目视核对比例
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：全身腾空，双膝收起，双脚离地，右臂后拉到最大蓄势，右肘后引，右掌在肩后，左掌开在胸前，上身略前压，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：腾空蓄势顶点；脚底离地；造型同锚。

#### air_special-03

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/air_special/frames/raw-03.png`，SHA-256 `d4c4019589334ce2a6bfbbe14031c8f79639349220d9be5daba2c3f1cdd4f87c`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/air_special-03-cell.png`，SHA-256 `c4377322f48c32ca5b04c35c60b9a6d4bfaafde6ff4baf5bf443635476749e7d`。
- 落格：scale 0.099419，bbox [80, 43, 162, 173]，站高/内容高 131，头高 34（ratio 0.2595），色数 32，连通块 1，脚底行 173，腾空 是。
- 自动提示：air_special-03: 非直立帧，头高 34、站高 131 仅供参考，需目视核对比例
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：全身腾空，双脚离地，右臂向前伸直，右掌五指并拢前指，左掌开掌靠近彩色计时器，双膝收起，肩背稳定，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。指尖有紧贴指尖的蓝白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：空中右掌前指发射相，左掌靠计时器；双脚离地；造型同锚。

#### air_special-04

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/air_special/frames/raw-04.png`，SHA-256 `c05a77324f479a0388ece96a5799959cbb2431e52a21355f3c4ee974e6804b55`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/air_special-04-cell.png`，SHA-256 `4d90aa2f05e5f46ef114f7d10b02dfee17a7e095d07fd48c85ccfebf8ba5e0c6`。
- 落格：scale 0.099419，bbox [88, 41, 166, 173]，站高/内容高 133，头高 34（ratio 0.2556），色数 31，连通块 1，脚底行 173，腾空 是。
- 自动提示：air_special-04: 非直立帧，头高 34、站高 133 仅供参考，需目视核对比例
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：保持空中右掌前指的发射姿势，全身腾空，双脚离地，右臂伸直，左掌开掌靠近彩色计时器，双膝收起，腰身稳定，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。指尖有紧贴指尖的蓝白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：保持空中前指；双脚离地；造型同锚。

#### air_special-05

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/air_special/frames/raw-05.png`，SHA-256 `b0c5c5559ca35adb38c2f50b3bf28b4c624a435c33ef69b34ac764d4db010ed2`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/air_special-05-cell.png`，SHA-256 `23beefaf1ee33bca6dc19f9647609de93e53d95771ca13a94c12e18db8c55f65`。
- 落格：scale 0.099419，bbox [84, 46, 158, 173]，站高/内容高 128，头高 34（ratio 0.2656），色数 31，连通块 1，脚底行 173，腾空 是。
- 自动提示：air_special-05: 非直立帧，头高 34、站高 128 仅供参考，需目视核对比例
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：保持空中右掌前指的发射姿势，全身腾空，双脚离地，右臂伸直，左掌开掌靠近彩色计时器，双膝收起，肩背平稳，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。指尖有紧贴指尖的蓝白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：保持空中前指；贴指尖蓝白光未外扩；造型同锚。

#### air_special-06

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/air_special/frames/raw-06.png`，SHA-256 `fe188c805c279b25e6102b04e3f03a361d90a4e94cf2dcd23ae73c96f514b253`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/air_special-06-cell.png`，SHA-256 `57650cc4da6821dced303d0bf139da5e62f1b11184e26f28634c3f08073935e5`。
- 落格：scale 0.099419，bbox [92, 42, 177, 173]，站高/内容高 132，头高 35（ratio 0.2652），色数 31，连通块 1，脚底行 173，腾空 是。
- 自动提示：air_special-06: 非直立帧，头高 35、站高 132 仅供参考，需目视核对比例
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：保持空中前指发射，全身腾空，双脚离地，右掌五指并拢，右臂伸直，左掌开掌靠近彩色计时器，双膝仍收起，上身略前倾，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。指尖有紧贴指尖的蓝白色微光，光不外扩、不成束。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：保持空中前指；双脚离地；造型同锚。

#### air_special-07

- 来源 raw（实收尺寸见行末）：`art/fighters/zoffy/stage1/air_special/frames/raw-07.png`，SHA-256 `d7fb987c9d4513062520d08389033bf6f0ffc0975654cacf86cf35310e164895`；实收 1000×1573。
- 输出 cell：`art/fighters/zoffy/stage1/cells/air_special-07-cell.png`，SHA-256 `2b2d1914fd93d73341ca1d34b466235fb8ab56d45a1c08b4e98b6ad1fb22a75a`。
- 落格：scale 0.099419，bbox [75, 36, 131, 173]，站高/内容高 138，头高 29（ratio 0.2101），色数 30，连通块 1，脚底行 173，腾空 是。
- 自动提示：air_special-07: 非直立帧，头高 29、站高 138 仅供参考，需目视核对比例
- 提示词：参考图是同一位佐菲的已定稿像素形象，是唯一身份与画风来源。动作：空中收臂回护架，右掌收回胸前，左掌离开计时器回到胸口，双膝仍收起，全身腾空，双脚离地，身体准备落地，视线朝前。手臂粗壮、大腿饱满、小腿有厚度，四肢粗细必须和参考图完全一致，不要画细长的手脚。本帧无光效。保持同样的头冠、眼睛、肩章、胸纹、蓝计时器和像素块大小。固定右侧视，全身完整不裁切，透明背景，无地面、无文字、无边框。
- 审图结论：4×目视：空中收臂回护架；双脚仍离地；造型同锚。

## 拒收帧与原因

- 诊断图：`art/fighters/zoffy/stage1/diagnostic/special-push-20261110.png`（special-04/05/06/07 第一轮：双掌分开、停在胸前，未形成并拢前推）。

- `special-04` 第 1 次：raw SHA `ebdd59eaf64560608c252f36c68bfdcb2ed34835c2fd7e3b7732ae8e687dee56`；cell SHA `b05425f3072611730a4a4359e8e18f1922186bbd26e312692af39ff72c55dab6`。原因：双掌分开停在胸前高度，未形成“并拢前推一半”；与逐帧规格不符。 处理：rejected_deleted，文件已删除，SHA 保留。
- `special-04` 第 2 次：raw SHA `08b78bd347fdfdf26a5a14b50dc7a96fc6dc2754f7307a44ce5eddd8aeef3921`；cell SHA `未落格`。原因：仍双掌分开停在胸前；按返工刹车出诊断图后改用“合十前伸”描述。 处理：rejected_deleted，文件已删除，SHA 保留。
- `special-05` 第 1 次：raw SHA `35ee0e23e5f7ceae81856b60ee28fafb5b362904966e14c6c6a80f45c3d2e42e`；cell SHA `4f49a1460e026500d5d45b19397921052ac9731a57febf13fa7bae5a400c6475`。原因：双掌分开、肘部高抬，未向前推出；与逐帧规格不符。 处理：rejected_deleted，文件已删除，SHA 保留。
- `special-06` 第 1 次：raw SHA `5d619942417607e5fabf5542a3cd1ef35b5badf04602f79339c6197b5f6eeb9f`；cell SHA `5dede723e291f94abe861cb39f664b63658505a934e9dc85655823b29a49797e`。原因：双掌分开、停在胸前高度；与逐帧规格不符。 处理：rejected_deleted，文件已删除，SHA 保留。
- `special-07` 第 1 次：raw SHA `90f04bdee9c60994da3a4efc0c8b634e1098165cc1c0256ac0f55c738a17dcfb`；cell SHA `d4c57703f62afe0706fcd3a438bfbd59a8e0923b763aba7dbdbd599fd718ac73`。原因：双掌回撤到胸前，打断04–07的推出过程。 处理：rejected_deleted，文件已删除，SHA 保留。
- `special3-11` 第 1 次：raw SHA `b3124d7e3188f24611c18281287e3818bb5ccd13b95d6d888541799fd84fd444`；cell SHA `da4ef01b91a711f4122cab0bca4dab39aaa18d205848e69cedd6fa72fa73fbea`。原因：右臂上扬约20°、手形收拢，与08–10的水平前指发射相不接续。 处理：rejected_deleted，文件已删除，SHA 保留。

返工刹车执行情况：special-04/05/06/07 第一轮 4 帧同一问题，先出诊断图，再按“双掌并拢、向前推出”修一次；special-04 第二次仍双掌分开，按第 2 种修法改用“合十前伸”后通过。special3-11 第一版右臂上扬，按第 1 种修法改为水平前指后通过。special-04 手位略高不再重生成，留作过渡帧。

## 已知问题与未解项

- 实收尺寸不统一：special3-02 1001×1572、air_special-00 1037×1517、air_special-02 1034×1520；落格按各自实收 Alpha 轮廓与统一源比例处理，不把请求尺寸当实收尺寸。
- special-04 前推手位略高于05–07，作为过渡帧保留；未再重生成（同一问题已用2种修法）。
- 前伸手臂使多帧自动头高失真（special-04/05/06/07/09/10/11、special2-01/05/06/08/09/10/11/12、special3-02/04/09/11、air_special-00/01/02/07）；均按头部列带与4×目视复核，头部与锚一致，不用缩头凑门。
- 屈膝/后坐帧站高低于154：special-04/05（143/142）、special-08（147）、special2-04/05/06（134/135/124）、special3-02（141）；按姿势保留，不拉直。
- 出招帧的贴掌/贴指尖微光在32色量化后多数不可见；无光束、无独立颗粒，运行时光束由FX承载。
- 未安装 assets/、未接运行时、未跑Godot、未做720/1080与双向实机检查、无录屏。
- 本批为执行自检，尚未由 root 签署 root_delegated_by_user，也不是用户亲审。

## 验收状态

- 执行代理已逐帧检查最终原生格与严格 4× 最近邻放大图：脸型、头鳍、勋章、蓝计时器、四肢粗细与身份锚一致；脚底/格边未裁切。
- 头高自动测量在前伸手臂或深蹲姿势下多次失真，报告中保留原值并逐帧目视复核，没有为凑门缩头或改比例。
- 本批只完成美术帧与落格记录；未实机、未安装、未接线。听审/实机审片仍待人工。
- root 签收：待签署 `root_delegated_by_user`；本报告不冒充用户亲审。


# 图鉴重建首派批次

用途：记录 2026-11-13 起图鉴重建首批并行生图的统一口径、产物位置与收据格式。当前制作源在 `art/catalogue-rebuild-20261113/<id>/`，本机收据在 `reports/catalogue-rebuild-20261113/receipts/<id>.json`；根会话负责安装到 `assets/` 与 `content/`，子代理不写共享文件。

## 生图

- 只经 MCP `mcp__magpie-image__generate_image`；模型 `cpa/gpt-image-2.6-sunburst`（若工具枚举未刷新可留空 `model` 跟随 Magpie 设置），`quality=high`，`background=transparent`，`size=1536x1024`，输出 `path` 一律传本仓库绝对路径。若工具未加载，先 `ToolSearch` 加载 `mcp__magpie-image__generate_image` 与 `mcp__magpie-image__generation_result`。
- 每条目三张图：`still-00.png` 由图鉴静帧规格转成像素整图（本人本地参考 + `reports/catalogue-rebuild-20261113/identity/<id>-native-x4.png` 现有整图侧视身份参考，最多 3 张）；`idle-01.png` 与 `idle-02.png` 只引用该条目 `still-00-clean.png` 一张身份锚，不追加角度参考。图鉴静帧允许按 `docs/HANDBOOK.md` 第 612–616 行多给本人不同角度参考，多角度规则不适用于动作帧。
- 提示词逐角色单独写，约 150–250 字，只写该帧动作；固定右侧视、完整全身不裁切、真透明背景、无地面/文字/边框/光晕/能量球/颗粒/飞行物、四肢粗细与参考一致、无玩具球关节/轴/插接缝/塑料高光。角色没有的部件不得写进提示词。
- 待机两帧必须是真实身体位移：屈膝、双拳护架、头颈/肩/尾/背甲或腿脚相对静帧有可见变化；不得复制、平移、局部变色或加特效凑帧。
- 不恢复旧 worker、旧 Goal、旧批量安装器；不直连 `tools/art/pipeline.py` 网络层；不生成音效；不读取、复制或提交凭据。

## 实收核验

- 请求尺寸不等于实收尺寸。每张图必须核实际返回路径、RGBA、实际宽高、Alpha 档位、主体 bbox、`>=128` 硬化后 bbox、SHA256、bytes。
- 生图前先实际 `Read` 本人本地参考图、联系人对应格与 `reports/catalogue-rebuild-20261113/identity/<id>-native-x4.png`。图鉴静帧允许多角度参考，不能仅因正面/3/4 拒收；现有 4× 已装整图若读得出完整侧视结构，可作为本人身份与朝向参考。若本人侧视整图朝左，先水平镜像再传入，标志结构按官方来源定前后朝向，不从正面猜。只有本人原始参考与现有整图都无法读结构（多人、演员肖像、文字页、玩具包装、植物纹样、错身份、局部裁到无法补全身）才写 `rejected` 收据，不消耗生图。来源门拒收时用 `--source-gate-only --status rejected`，`--prompts` / `--generation-ids` 传空 JSON 文件路径即可。
- 原始软 Alpha 保留为 `still-00.png` / `idle-01.png` / `idle-02.png`；另生成 `*-clean.png`：Alpha `>=128` 置 255、其余置 0，按实体 bbox 裁切，保留 RGBA。不得把离线硬化冒称原生二值 Alpha。
- 统一辉光门口径：主体为 `alpha>=200` 最大连通块，外扩 3 px 后主体外 `alpha>=16` ≤100 px、主体外 `alpha>=200` 必须为 0；`alpha 1–15` 尘点只登记不计入。独立光斑/飞行物按连通块硬门另记，不得烘焙进人物帧。`fits_catalogue_cell` 只报告按 192 px 名义站高折算的宽度，不进入 `glow_gate.pass`。
- 宽体落格口径（2026-11-13）：图鉴 UI 与检查固定 384×256 格；长尾、宽背、背鳍不裁、不逐帧缩放。根会话安装时由 `catalogue_rebuild_repack.py` 以三帧最大宽求一次统一比例，静态图与三帧 strip 一起落格，登记 `strip_width_fit`、`visible_height_including_ornaments` 与磁盘 SHA。`catalogue_rebuild_install.py` 不再用旧 `catalogue_anim.py` 的脚底重心拼条。
- 同一帧连续拒收 3 个不同生成结果即暂停该项并写诊断说明；同一问题最多 2 种修法，不无限重生成。明确不合格时把状态写 `rejected`，不要静默跳过。

## 每个 ID 的产物

```
art/catalogue-rebuild-20261113/<id>/still-00.png
art/catalogue-rebuild-20261113/<id>/still-00-clean.png
art/catalogue-rebuild-20261113/<id>/idle-01.png
art/catalogue-rebuild-20261113/<id>/idle-01-clean.png
art/catalogue-rebuild-20261113/<id>/idle-02.png
art/catalogue-rebuild-20261113/<id>/idle-02-clean.png
reports/catalogue-rebuild-20261113/receipts/<id>.json
```

收据字段：`catalogue_id`、`name`、`reference_file`、`reference_sha256`、`reference_size`、`model`、`quality`、`prompt` 三份、`generation_ids`、`files`（每个文件的 path、sha256、bytes、width、height、mode、alpha_levels、alpha_ge128_bbox）、`glow_gate`、`visual_review`、`status`。`visual_review` 必须写明本人标志结构、头肩比例、手脚体量、完整不裁切、三帧真实位移；逻辑数值不能写成造型通过。

## 来源门口径更正记录（本批）

首派 20 个 ID 曾因“正面/3/4 角度”被一律拒收，未消耗生图；该判定误把动作帧的单锚规格套到图鉴静帧。按 `docs/HANDBOOK.md` 第 612–616 行与 `AGENTS.md`，图鉴照片→像素允许本人多角度参考；已用 `SendMessage` 纠正四个仍在运行的续派子代理，并另派四个重做子代理处理首派 20 个 ID。本批现在通过本人本地参考与 `identity/<id>-native-x4.png` 现有侧视整图组合定静帧，仍只有动作帧坚持单身份锚。此记录只说明本批返工原因，不改现行规则。

## 声音接口边界（2026-11-13）

用户要求图鉴带音效，并指定“那个音乐模型的接口”。本轮只读复核：本机 `~/.claude.json` 的 MCP 服务只有 `context7`、`codebase-memory`、`magpie-image`；`magpie-image` 工具集只有图像/视频生成，没有音乐或音效生成工具；`ListMcpResourcesTool` 无资源；本机 Magpie 配置和模型目录无音乐生成端点；音频相关环境变量数量为 0。项目本机音频客户端 `tools/audio/kits_client.py` / `tools/audio/pipeline.py` 只提供 Kits 语音转换、分离与分轨，`doctor --check-api` 实测仍是 `Kits HTTP 403：当前密钥无访问权限；未自动重试`；未读取/打印/复制密钥内容，未下发收费任务。

因此本批不能声称已用音乐模型生成音效，也不伪造 Kits 输出。图鉴现有可播放链路在 `ui/kit/catalogue_sound.gd`：本人固定候选声优先；没有固定候选时只读查 `content/audio/runtime.json` 的 `voices[base].intro` 与 `sources.json` 的 installed 记录，复用已装本人登场声；仍无则回退项目自制 `catalogue_pick.wav`。不新增 `sounds` 键、不改 `sources.json`、不拿 `victory/attack` 顶替，不把合体前卢提昂对白或技能喊声当本人试听。新增运行时声音若以后接入，必须同步维护 `sources.json` 与 `runtime.json` 的 1:1、SHA、来源、`source_kind`、`listening_reviewed=false`，不得把数字合成/转换/分离结果写成原剧原声或文生音效。本批无录屏、未听审。

## 根会话后续

根会话集中把 `still-00-clean.png` 复制到 `reports/catalogue-ref/<id>/raw.png`，经 `tools/media/art/catalogue_install.py` 落静态格，再用本批 `catalogue_rebuild_install.py` 调 `catalogue_rebuild_repack.py` 从三张 clean 源统一落格、拼条、回写磁盘 SHA，最后用 `tools/check/catalogue_idle.py` 复核。子代理不得运行 `catalogue_install.py`、不得写 `content/roster/catalogue_display.json`、不得写 `assets/`、不得跑 Godot 导入或全量验证。

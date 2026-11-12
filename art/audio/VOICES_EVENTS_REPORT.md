# 七名角色战吼事件补声素材报告（2026-11-11）

对象：zoffy、ultraman-zero、ultraman-gaia、ultraman-justice、ultraman-king、mother-of-ultra、father-of-ultra，每人 down / taunt / heavy / timeout 四个事件，共 28 条。light 事件直接复用已有 attack 素材，不另生成、不另登记。

**本报告只做素材层筛选，未做人耳听审。** 所有“判断依据”来自源视频标题与简介、合集分段结构、时长/峰值/RMS/包络统计，不等于听感通过，也不等于角色归属已由人耳确认。

## 一、交付与硬门自检

- 28 个 WAV 已落盘：`assets/audio/production/v3/<slug>/events/<slug>-<event>.wav`。
- 格式：48 kHz、双声道、16-bit PCM；每条 5 ms 淡入淡出，样本峰值归一到 -1.20 dBFS。
- 时长 0.560–2.500 s，均在 0.2–2.5 s 内；0 个削波样本。
- 收据 `art/audio/voices-events-20261111.json` 中 28 条 SHA-256 与仓库内文件逐条一致。
- 本轮未修改 `content/audio/` 下任何 JSON；运行时接线与批准由根完成。
- 临时下载在 `/tmp/ufeneo-voices-events-20261111/`，任务结束后删除；仓库内不保留源视频/源 m4a。

## 二、来源与分配

| 角色 | down | taunt | heavy | timeout |
| --- | --- | --- | --- | --- |
| zoffy | P9 4.00–4.68s（通用 roar，归属未确认） | P9 10.06–10.80s | P9 25.12–26.26s | 原源 2.78–4.04s |
| ultraman-zero | 7.82–8.38s | 9.46–10.62s | 2.18–3.34s | 53.76–55.56s |
| ultraman-gaia | P4 4.08–4.64s（吃瘪） | P2 6.96–8.02s | P3 30.98–33.48s（长战吼） | P3 36.58–37.80s |
| ultraman-justice | 5.22–6.26s | 1.32–2.54s | 6.84–8.50s | 17.20–18.74s |
| ultraman-king | king2 27.62–29.22s | king2 33.56–35.26s | king2 56.80–59.22s | king2 59.46–61.96s |
| mother-of-ultra | 原源 2.80–3.56s | 原源 6.20–7.10s | 原源 7.56–8.36s | 合集母半 91.90–94.40s |
| father-of-ultra | 合集父半 3.84–4.42s | 合集父半 0.98–1.92s | 合集父半 6.52–9.02s | 合集父半 13.94–16.44s |

来源说明：
- zoffy 原源：B 站 `BV1b44y1w7g6`，UP 主“一清二水”，合集「佐菲奥特曼的怒吼声」；P9 来源：`BV1WKuDz9Evb` 第 9P「佐菲/奥父/王——战吼（通用）」，UP 主“番茄蓝莓水”。
- ultraman-zero：`BV1BdC3YjEGq`，UP 主“夕阳的勇者”，合集「赛罗奥特曼部分战吼」。
- ultraman-gaia：`BV1GRFSeJEFd`，UP 主“番茄蓝莓水”，第 2/3/4P。
- ultraman-justice：`BV15hE964E6u`，UP 主“郭圣耀”，合集「杰斯提斯奥特曼的战吼」。
- ultraman-king：`BV1kzVG63ESK`，UP 主“郭圣耀”，合集「奥特之王的战吼」（与既有 king 五条所用 `BV1i25TzNEri` 不同上传者/声优版本）。
- mother-of-ultra：前三条 `BV1STEc6wEwe`（UP 主“郭圣耀”）；timeout 条 `BV1GfV5zjE14` 母半段（UP 主“泰罗教官宝岛Stars”）。
- father-of-ultra：四条均来自 `BV1GfV5zjE14` 父半段（UP 主“泰罗教官宝岛Stars”）。

## 三、事件语义说明

- down：倒地/战败吼，优先按时长较短、RMS 较低的段落候选。
- taunt：挑衅吼，优先中短段落。
- heavy：重攻击吼，优先较长/能量较高的段落。
- timeout：超时/力竭，优先较长或包络衰减明显的段落。

以上仅为素材层候选分配，未听审，不能保证语义正确；同一角色内部存在语义互换的可能。

## 四、存疑项

1. **未做人耳听审**：无法确认每段是不是干净单人声、有没有伴奏/旁人声残留、剪辑拼接感。
2. **zoffy P9 通用 roar**：第 9P 标题为「佐菲/奥父/王——战吼（通用）」，三角色共用，角色归属未由人耳确认；不能声称该段仅属于佐菲。
3. **king 来源切换**：既有 king 五条来自 `BV1i25TzNEri`（三位声优），本轮 king 四条来自 `BV1kzVG63ESK`（郭圣耀），声优版本可能不同；如项目要求统一声线，需听审后替换。
4. **mother/father 合集**：`BV1GfV5zjE14` 为父/母合集，父半段/母半段内为连续吼段（部分段落时长 5–10 s），本轮从其中切取 2.5 s 窗口，起止不是自然句界；且该合集 voice actor 多于单一上传者源，声线可能混用。
5. **B 站素材属性**：番茄蓝莓水的「战吼素材」系列命名含版本号（3.0/4.0/5.0），可能为游戏音效提取而非原剧现场声；本轮仍按 `source_kind=episode`、`reprint=true` 登记为转载，不声称具体原剧集数或原剧原声。
6. **未生成 Godot `.import`**：本轮只落盘 WAV，`.import` 由根在 Godot 导入时生成；未运行导入以避免牵动其它任务文件。
7. **light 复用**：light 事件直接复用既有 attack 素材（如 `zoffy-attack.wav`），不另生成；运行时接线由根完成。

## 五、文件清单与 SHA-256

| # | id | 文件 | SHA-256 | 时长(s) | 峰值(dBFS) | LUFS | 真峰值(dBTP) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | zoffy_voice_down_20261111 | assets/audio/production/v3/zoffy/events/zoffy-down.wav | 93703938fd9bc6afc9fb0c0d2f601b2ab21cb70ddc5c9ebec2e9d90f8029b6f6 | 0.680 | -1.20 | -14.0 | -1.2 |
| 2 | zoffy_voice_taunt_20261111 | assets/audio/production/v3/zoffy/events/zoffy-taunt.wav | b45371c54c961b6870304fc47f2b472884ef54afc078b711b71b8929ed21f32d | 0.740 | -1.20 | -13.9 | -1.2 |
| 3 | zoffy_voice_heavy_20261111 | assets/audio/production/v3/zoffy/events/zoffy-heavy.wav | 2e1ba6208a73a442fcf56338df354d011e917391006a1d55db9a570b12190146 | 1.140 | -1.20 | -9.4 | -1.2 |
| 4 | zoffy_voice_timeout_20261111 | assets/audio/production/v3/zoffy/events/zoffy-timeout.wav | 0e7ddc761d9405fc261cf5a36b73875d3829dd9429925e032a886f53777228f8 | 1.260 | -1.20 | -8.1 | -1.2 |
| 5 | zero_voice_down_20261111 | assets/audio/production/v3/zero/events/zero-down.wav | 98d5dca47005966a13c5514d5c1e177727dca838ea41a3f993c501e4f0c3b7f7 | 0.560 | -1.20 | -12.6 | -1.2 |
| 6 | zero_voice_taunt_20261111 | assets/audio/production/v3/zero/events/zero-taunt.wav | 6947767459fdbe038e86356a066fc0a9aaea1f72ae3c538a7c786f8e5f857e89 | 1.160 | -1.20 | -11.0 | -1.2 |
| 7 | zero_voice_heavy_20261111 | assets/audio/production/v3/zero/events/zero-heavy.wav | 3e502137385f93fcb7709e2695429e0ae15b4dcd31db3dc034dbcc73a39d5407 | 1.160 | -1.20 | -10.7 | -1.0 |
| 8 | zero_voice_timeout_20261111 | assets/audio/production/v3/zero/events/zero-timeout.wav | b9e221dd3d2eac39dba65c4d278c8d78831ab475dcf871af1c7a0cf1969b2916 | 1.800 | -1.20 | -11.2 | -1.2 |
| 9 | gaia_voice_down_20261111 | assets/audio/production/v3/gaia/events/gaia-down.wav | b045eb4c2ef265b7290d7cc2a4703bd83e51cfccd326f9cdf3a82979b4ed9f37 | 0.560 | -1.20 | -12.9 | -1.2 |
| 10 | gaia_voice_taunt_20261111 | assets/audio/production/v3/gaia/events/gaia-taunt.wav | de3cb3e950cc81803bbb49835846ce48215f4c5337cc63fc65103ba9cdc014a9 | 1.060 | -1.20 | -13.7 | -1.2 |
| 11 | gaia_voice_heavy_20261111 | assets/audio/production/v3/gaia/events/gaia-heavy.wav | 87b6a589cf5482b56d69eb4948fa16ba06aeabe56b3ec7905af1f0465ac71cb9 | 2.500 | -1.20 | -8.1 | -1.2 |
| 12 | gaia_voice_timeout_20261111 | assets/audio/production/v3/gaia/events/gaia-timeout.wav | e2a388fe97be6aa81361956b6bd3d432b2aeedf0844fc53e143b9aabdb66c893 | 1.220 | -1.20 | -8.2 | -1.2 |
| 13 | justice_voice_down_20261111 | assets/audio/production/v3/justice/events/justice-down.wav | 656854222fc6cde4de288fab10de568301db78d6c4f3a8f0e00161c7ede6638b | 1.040 | -1.20 | -8.3 | -1.2 |
| 14 | justice_voice_taunt_20261111 | assets/audio/production/v3/justice/events/justice-taunt.wav | 44d4d5ce01d15ebe1e6241aea9837079e4c87bd4427f87bcb411c829084ae2fa | 1.220 | -1.20 | -8.0 | -1.2 |
| 15 | justice_voice_heavy_20261111 | assets/audio/production/v3/justice/events/justice-heavy.wav | ee9ef9939f75c953853a3dca84c90a9a0a1b78bc332d93d3571fdd57b6c37cd6 | 1.660 | -1.20 | -8.2 | -1.2 |
| 16 | justice_voice_timeout_20261111 | assets/audio/production/v3/justice/events/justice-timeout.wav | ef954e2185ab259e8db9831917e1eaa5c44f882fac01d1367a98d30e6dde8c63 | 1.540 | -1.20 | -6.9 | -1.2 |
| 17 | king_voice_down_20261111 | assets/audio/production/v3/king/events/king-down.wav | afc24a851a82c4ebe67cda71280cf156012b5b90f8a94c7ba9c51d08c5902cf2 | 1.600 | -1.20 | -12.6 | -1.2 |
| 18 | king_voice_taunt_20261111 | assets/audio/production/v3/king/events/king-taunt.wav | 0b01801b92c74cad209d0378d40b413fef8b5c542a086fe41838149f619eda8f | 1.700 | -1.20 | -10.0 | -1.2 |
| 19 | king_voice_heavy_20261111 | assets/audio/production/v3/king/events/king-heavy.wav | d03b664f5606a76a59bfa73f31b96c0f78178bcb1369f89d8a9b1697ae91f28b | 2.420 | -1.20 | -9.4 | -1.2 |
| 20 | king_voice_timeout_20261111 | assets/audio/production/v3/king/events/king-timeout.wav | 87a2a5e815c9fdc04f654bdc6c2104a9ac6752c62a75312a84eb5e475bc3b709 | 2.500 | -1.20 | -9.8 | -1.2 |
| 21 | mother_voice_down_20261111 | assets/audio/production/v3/mother/events/mother-down.wav | 6bc5e506b37817694663fbab87a13b4e02bc46ebf1b8c03ccd01a801b08aa44e | 0.760 | -1.20 | -8.0 | -1.2 |
| 22 | mother_voice_taunt_20261111 | assets/audio/production/v3/mother/events/mother-taunt.wav | bc9e09a0a54b894e78d414cb58a96b52163cd03be3e83a1936fcc9839cab329e | 0.900 | -1.20 | -10.8 | -1.2 |
| 23 | mother_voice_heavy_20261111 | assets/audio/production/v3/mother/events/mother-heavy.wav | 55ea457e65caf3dc23dd5227446a347ab2fddcacbc041b79b43802acea17accc | 0.800 | -1.20 | -7.4 | -1.1 |
| 24 | mother_voice_timeout_20261111 | assets/audio/production/v3/mother/events/mother-timeout.wav | 7695332ef02b05735b91974a7067514fea1ca5fb37cf7ce518685141619a7829 | 2.500 | -1.20 | -12.6 | -1.2 |
| 25 | father_voice_down_20261111 | assets/audio/production/v3/father/events/father-down.wav | 730b8ecd82134180526f74f35a9e7b37b1966b510154eeba4a03b914791fd9ab | 0.580 | -1.20 | -11.9 | -1.2 |
| 26 | father_voice_taunt_20261111 | assets/audio/production/v3/father/events/father-taunt.wav | e946b0cb1a13b823fd996953a2cab06729c2efbe2eb1e536f8edebf0225328a0 | 0.940 | -1.20 | -10.9 | -1.2 |
| 27 | father_voice_heavy_20261111 | assets/audio/production/v3/father/events/father-heavy.wav | 9050b554d2b4078cb37957f1943cd98341edb9d309138c2f469b165d7078bb6f | 2.500 | -1.20 | -8.4 | -1.2 |
| 28 | father_voice_timeout_20261111 | assets/audio/production/v3/father/events/father-timeout.wav | 3360edaa36ab8bb9ea97f0fd795feb638f0485aefd3a24ff5918999cd8148736 | 2.500 | -1.20 | -8.2 | -1.2 |

## 六、状态

- 28 条全部 `runtime_status=pending_install`、`listening_reviewed=false`、`metadata_reviewed=true`。
- 本轮不修改 `content/audio/` 下任何现有 JSON；运行时接线、批准与听审由根完成。
- 临时下载与中间文件在 `/tmp/ufeneo-voices-events-20261111`，任务结束后删除；仓库内不保留 B 站视频或源 m4a。

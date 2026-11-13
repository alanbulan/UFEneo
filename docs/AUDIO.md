# 音频：接口与配乐依据

用途：制作、核对或分配游戏声音与配乐时读本文件。Kits 音频接口的凭据、连通性、计费边界，以及 8 只怪兽的原剧主题曲核查结论都以此为准。

2026-11-13 收口：本文件原文已并入 [HANDBOOK](HANDBOOK.md) 的“第 7 节”，现行入口以根 [README](../README.md) 与手册为准。

## 一、Kits 音频接口

项目通过 Kits（`https://arpeggi.io/api/kits/v1`）做语音转换、人声分离和分轨。
客户端在 `tools/audio/kits_client.py`，命令行入口是 `tools/audio/pipeline.py`。

### 凭据

密钥只在本机，**不进仓库、不打印、不复制**。按优先级：

1. 环境变量 `UFE_KITS_API_KEY`
2. macOS：`~/.codex/secrets/ufeneo-music.key`（纯文本，权限必须 `0600`）

密钥文件权限过宽（组或其他用户可读）时，客户端直接拒绝发送请求。

### 连通性

```bash
.venv/bin/python tools/audio/pipeline.py doctor
.venv/bin/python tools/audio/pipeline.py models --per-page 3
```

`doctor` 只检查 ffmpeg、ffprobe 和凭据是否存在，不发网络请求。
`models` 会实际调用 API；返回模型列表说明接口打通。

2026-11-08 实测：`models` 返回 270 个音色模型、90 页，接口正常。

### 能做什么

| 子命令 | 用途 |
| --- | --- |
| `doctor` | 本地环境与凭据检查 |
| `models` | 列出可用音色模型 |
| `extract` | 从媒体文件提取音轨 |
| `prepare-voice` | 准备语音转换的输入切片 |
| `cut-cue` | 按时间点切出短事件 |
| `submit` | 提交任务（**发收费请求**） |
| `poll` | 查询任务状态 |
| `download` | 下载结果 |
| `mix` | 混音 |

`submit` 会真实计费。按 [AGENTS](../AGENTS.md) 的规则，收费请求须先读本机最新账本，
新单预占 1 美元、按真实 usage 结算，未知单不释放、不重发。

### 不在这个接口范围内

Kits 是**语音转换与分离**服务，不是文生音效或文生音乐。项目不声称任何音效是文本生成的。

`content/audio/sources.json` 的 `source_kind` 现有三类：

- `original`：项目自制（合成、录音或自制编曲）。
- `episode`：原剧/官方音源。公开转载的副本必须同时写 `reprint: true`，并登记 `platform`、`uploader`、`source_url`、`source_timecode`、`raw_sha256`、`captured_utc`；不得把转载写成官方发布。
- `derivative`：二创、翻奏、MAD 等；不得冒充原剧原声。

只接受公开可访问的副本；需要登录、付费或返回 403 的不绕过，换公开副本。旧记录不改写，缺失 `source_kind` 的历史参考仍可读；新参考若写 `source_kind`，`tools/audio/pipeline.py` 会校验取值，`episode` 必须带布尔 `reprint`。

### 2026-11-10 四角色首轮公开副本

四名角色各取 1 条 BGM/角色曲和 1 条非语言战吼，均为 B 站公开转载/合集，登记为 `source_kind=episode`、`reprint=true`；剪辑在 `assets/audio/production/v3/<角色>/clips/v002/`，完整 SHA、上传者与采集时间见 `content/audio/sources.json` 的 `*-reprint-20261110` 记录。

| 角色 | 用途 | B 站 BV / 时间码 | 片段 |
| --- | --- | --- | --- |
| 佐菲 | 角色歌器乐 | BV1hd4y1o796 / 00:02:30.000–00:03:00.000 | `zoffy-bgm.wav` |
| 佐菲 | 非语言战吼 | BV1b44y1w7g6 / 00:00:02.500–00:00:04.300 | `zoffy-roar.wav` |
| 赛罗 | 主题纯音乐 | BV1sa411K7ij / 00:00:10.000–00:00:40.000 | `zero-bgm.wav` |
| 赛罗 | 非语言战吼 | BV1BdC3YjEGq / 00:00:02.000–00:00:05.000 | `zero-roar.wav` |
| 盖亚 | OST「激闘」M-38 | BV1Kt9ZYEEnK / 00:01:00.000–00:01:30.000 | `gaia-bgm.wav` |
| 盖亚 | 非语言战吼（第2P） | BV1GRFSeJEFd?p=2 / 00:00:06.600–00:00:08.300 | `gaia-roar.wav` |
| 杰斯提斯 | 剧场版 OST「コスモス&ジャスティス」 | BV1YnxXe8EQi / 00:01:35.000–00:02:05.000 | `justice-bgm.wav` |
| 杰斯提斯 | 非语言战吼 | BV15hE964E6u / 00:00:09.000–00:00:12.500 | `justice-roar.wav` |

这些片段只完成来源、时间码、哈希和峰值检查；首轮完成时未做听审、未做循环、未接入运行时。

2026-11-10 已完成 Kits 首轮：4 条 BGM 以 `stem-splits` 分离后做 30.000s 循环，4 条战吼以 `vocal-separations` 清理并静态归一；输出在 `assets/audio/production/v3/<角色>/kits/`，台账见 `reports/audio-kits-ledger-20261110.json`。首轮完成时所有输出 `runtime_approved=false`、`listening_reviewed=false`；Kits job detail 未返回 `usage` 与内部模型标识。仍未听审。当前接入状态见下节。

同一批源 WAV 已切出每角色 attack/special/hit/win 各 1 条，共 16 条事件候选；只做裁剪、淡入淡出与静态归一，未做 voice conversion。登记见 `content/audio/sources.json` 的 `*_voice_*_20261110` 记录（与运行时声音 ID 相同），听审清单见 `reports/audio-events-first-listen-20261110.md`；全部未听审。当前接入状态见下节。

### 2026-11-10 自动评审与运行时接入

用户 2026-11-10 委托自动批准首轮 24 条（4 BGM 循环、4 战吼、16 事件）接入运行时。记录已标 `runtime_approved=true`，统一写 `runtime_approval_basis=user_delegated_auto_approve_2026-11-10`；`listening_reviewed` 全部保持 `false`。这只表示准予接入，不表示听审通过，也不把 B 站转载写成官方发布。

4 条 30.000s 循环已转为运行时 OGG（48kHz 双声道、Vorbis），放在 `assets/audio/music/stage-bgm/v003/`；`battle_music.json` 新增 `zoffy-battle`、`ultraman-zero-battle`、`ultraman-gaia-battle`、`ultraman-justice-battle` 四条 track，并映射 `zoffy`、`ultraman-zero`、`ultraman-gaia`、`ultraman-justice`。运行时 `UfeBattleMusicDirector` 对 OGG 设置 `loop=true`。转换台账见 `reports/audio-runtime-conversion-20261110.json`。

`runtime.json` 已新增 20 条 `character_voice` 记录和 4 个 `voices` 条目：`attack`/`super`/`hit`/`victory` 分别接事件攻击/special/hit/win，`intro` 接清理后的非语言战吼；`down`/`timeout` 没有已核片段，保持未映射，不拿 hit/win 冒充。事件槽位仍是按合集区段的时长、峰值与 RMS 候选分配，不是逐场原剧核对。

24 个已安装运行时文件的路径、SHA、格式与导入命令见 `reports/audio-runtime-import-20261110.md`；`.import` 侧车已就位。20 条事件/战吼来源记录的 `runtime_status=installed`，4 条 reprint BGM、4 条 reprint 战吼与 4 条 loop30 记录标 `runtime_status=pending_install`，暂不写入 `sounds`。2026-11-10 在 Godot 锁内复跑 `audio_playback` 与 `phase3_fx_audio` 均 PASS；本轮无听审、无实机试听、无录屏。

### 2026-11-11 事件语音补齐（7 角色 × down/heavy/taunt/timeout）

从既有公开转载合集继续切出 7 名角色（佐菲、赛罗、盖亚、杰斯提斯、奥王、奥母、奥父）各 4 条事件声：`down` / `heavy` / `taunt` / `timeout`，共 28 条。逐条上传者、平台、URL、作品与集数、时间码、SHA、取得日期见 `art/audio/voices-events-20261111.json`，批次说明见 `art/audio/VOICES_EVENTS_REPORT.md`。

- 接入：`runtime.json` 新增 28 条 `character_voice` 与对应 `voices` 键，`heavy`/`taunt` 在有对应 clip 的角色上登记 `frame_sounds` 帧 0；`sources.json` 28 条记录 `runtime_status=installed`、`runtime_approved=true`、`runtime_approval_basis=root_delegated_by_user 2026-11-11`；`listening_reviewed=false`，未听审。
- 峰值口径：`fx_audio` 门要求 true_peak ≤ −1.8 dBFS，既有 v3 事件声约 −9.96 dBFS。新批首轮按 −1.2 dBFS 归一被门拒绝，统一重采样到 −10.0 dBFS 峰值并重算 SHA/true_peak/sample_peak/rms/integrated_lufs，`fx-audio-resources`、`audio-manifest` 均 PASS。
- 未实机试听、无录屏；只到资源与逻辑检查。

### 当前声音缺口

见 [手册当前状态](HANDBOOK.md#第-1-节--progressmd) 的“后续优先级”：teo/arc/blazar/omega 缺通用状态音与语音表。
佐菲、赛罗、盖亚、杰斯提斯、奥王、奥母、奥父自 2026-11-11 起已有 attack/super/hit/victory/intro/down/heavy/taunt/timeout 本人声音（新增 28 条事件声，未听审）；语音仍按合集区段分配，不是逐场原剧核对。
补齐需要新录音或新分离轨，属收费操作，须用户明确授权后才能做。

## 二、怪兽主题曲核查

核查对象：8 只奥特曼系列怪兽在原剧中是否有专属主题曲/专用战斗配乐。
核查方式：只查曲目表、官方商品页、官方新闻稿与可交叉验证的日文资料；**未下载、未生成、未调用任何音频**；未接触原始 CD 内页（booklet），凡属推断均标注。

### 先说明三个容易混淆的点

1. **1966《奥特曼》的 BGM 当年没有曲名，只有管理编号（A-1、B-1、M-4T2 等）。** 现在的曲名是 1991 年《ウルトラマン 総音楽集》CD 化时首次赋予的，之后被官方沿用（包括《新·奥特曼》的片尾字幕与原声带）。所以"レッドキングの襲撃""恐怖のネロンガ"这类名字**不是剧中叫法**，不能据此判定为"怪兽专属曲"。
   - 来源：https://shu-yashiro.com/ultraman-ost-history/ 、https://artist.cdjournal.com/d/-/1192030402
2. **《怪獣大進撃》不是 1966《奥特曼》的曲目。** 1966 年剧集官方曲目（《ウルトラマン 主題歌・挿入歌 大全集》12CD 全 263 曲）里查不到这个名字。可能的混淆源有三个：1969 年东宝电影《ゴジラ・ミニラ・ガバラ オール怪獣大進撃》（音乐同为宮内國郎）、1968 年《怪獣総進撃》、以及《奥特曼80》里名为「怪獣軍団大進撃」的 BGM。原剧通用战斗曲应写「戦い」「怪獣対ウルトラマン」「勝利」「空中戦」等。
   - 来源：https://columbia.jp/prod-info/COCX-39801-12/ 、https://www.suruga-ya.jp/product/detail/120014367 、https://columbia.jp/prod-info/COCX-41138-42/ 、https://columbia.jp/prod-info/COCX-42285-6/
3. **怪兽吼声（SE）≠ 音乐。** 官方效果音集里确实有以怪兽命名的音轨（例如《帰ってきたウルトラマン》效果音集的「ブラックキング」），那是叫声/效果音，不是配乐。

---

### gomora（哥莫拉）

- 专属主题：**无**
- 依据：第 26–27 话「怪獣殿下」使用全剧通用剧伴。第 26 话哥莫拉战可确认使用 **M-4T2**（CD 曲名「ミイラの叫び 出撃(M4T2)」），庵野秀明为 2022 年「庵野秀明セレクション《奥特曼》4K 特别上映」选片时明确提到"M-4T2 曲响起、彩色计时器闪烁音回荡中，奥特曼美丽地被打倒"；第 27 话则按粉丝逐集分析使用通用战斗曲「戦い」系（**中**可信度）。两话均无"哥莫拉主题曲"。
- 另有一项特殊物：1991 年《ウルトラマン 総音楽集》Disc 2 的「未発見楽曲（M.E.テープ抜粋）」区块收录了 16 秒的「怪獣殿下」；1995 年《TSUBURAYA PRODUCTION HISTORY OF MUSIC》将其复原重录为「怪獣殿下（未発見楽曲復元新録音／ジョンスン島）」。这是该两话录音期遗留的未发表/未确认使用片段，**不是播出用的专属主题**。
- 若为通用 BGM：M-4T2（第 26 话）／「戦い」（第 27 话分析），作品《奥特曼》第 26–27 话
- 官方 OST 收录：**有**。《シン・ウルトラマン音楽集》CDI-16「ミイラの叫び 出撃(M4T2)」；《絶体絶命！ウルトラ怪獣 バトル・ミュージック・コレクション 昭和編》Tr.27「戦い」；《ウルトラマン 総音楽集》Disc 2 Tr.13「怪獣殿下」（未発見楽曲）
- 来源：
  - https://www.value-press.com/pressrelease/297122/pwrz4oDW/40856 （圆谷官方新闻稿，庵野评论）
  - https://cinema-factory.net/contents/2428_shin-ultraman/preview.html
  - https://note.com/konton_fusion/n/n8fcc6544e781
  - https://artist.cdjournal.com/d/-/1192030402
  - https://www.oricon.co.jp/prof/183/products/71961/1/
  - https://www.kinokuniya.co.jp/f/dsg-10-4549767003580 （16 秒记载）
- 可信度：**高**（无专属主题这一点有官方评论＋曲目表双重支撑）；第 27 话具体曲目为**中**（仅有粉丝分析，无官方逐集表）。

### zetton（杰顿）

- 专属主题：**无**
- 依据：第 39 话「さらばウルトラマン」没有任何"杰顿主题曲"。相反，杰顿战以**几乎无音乐、仅效果音**的演出著称（杰顿电子音、打击音），用沉默制造"奥特曼攻击无效"的绝望感；这一说法在多个资料中一致，但未找到制作者一次证言。该话可确认使用的剧伴是 M7「謎の円盤群」、M8「円盤群接近」（圆盘舰队接近场面，据粉丝分析属第 2 回录音的通用曲）。注意：第 39 话监督是**飯島敏宏**，不是实相寺昭雄（实相寺仅支援参与）。
- 另需区分：1996 年电影《甦れ!ウルトラマン》原声带（SRCL-3470）里有「ウルトラマンVSゼットン」「ゼットンをイデが倒した」，是 1996 年为该片**重新编曲/新录**的版本，不是 1966 年剧中曲；1978 年 LP《ウルトラ怪獣大百科》也有名为「ゼットン」的轨，但那是 BGM＋效果音＋剧情的组曲。
- 若为通用 BGM：M7「謎の円盤群」、M8「円盤群接近」（舰队接近）；杰顿战本身**未核实**具体曲目（多方资料指向"无音乐/仅 SE"）
- 官方 OST 收录：**有**（通用曲）。《シン・ウルトラマン音楽集》CDI-25/26「さらばウルトラマン 謎の円盤群(M7)」「円盤群接近(M8)」；《絶体絶命！…昭和編》Tr.40–41。1996 版编曲另见《ウルトラマンワンダフルワールド》SRCL-3470
- 来源：
  - https://detail.chiebukuro.yahoo.co.jp/qa/question_detail/q10126944920
  - https://mkb1978.hateblo.jp/entry/13446a0931b1c54ea563dc1aadab6748
  - https://note.com/shota_/n/ne3f55438fc9b
  - https://www.kingrecords.co.jp/cs/g/gKICA-92606/
  - https://www.suruga-ya.jp/product/detail/120013909
  - https://omimi.biz/products/detail/51153
- 可信度：**高**（无专属主题）；第 39 话"无音乐"为**中**（粉丝共识，无官方一手证言）。

### red_king（雷德王）

- 专属主题：**无**（但有以它命名的登场曲）
- 依据：第 8–9 话使用的 **B1「怪獣無法地帯 レッドキングの襲撃」** 是第 1 回录音的通用"怪兽出现"剧伴，并非只服务雷德王；有粉丝资料称同一曲也用于第 1 话贝姆拉登场（**中**可信度，未获官方确认）。粉丝逐集分析认为该曲与通用战斗曲「戦い」在**第 9 话「電光石火作戦」后停止使用**。曲名系 1991 年 CD 化时按首次使用场景命名，不是剧中名称。
- 若为通用 BGM：「怪獣無法地帯 レッドキングの襲撃（B1）」＋「戦い」，用于《奥特曼》第 8–9 话
- 官方 OST 收录：**有**。《絶体絶命！…昭和編》Tr.26「レッドキングの襲撃(B1)」；《シン・ウルトラマン音楽集》CDI-06；《ウルトラマン ミュージックファイル》B-1
- 来源：
  - https://columbia.jp/prod-info/COCX-42285-6/
  - https://www.kingrecords.co.jp/cs/g/gKICA-92606/
  - https://www.cdjapan.co.jp/product/VPCD-81296
  - https://note.com/konton_fusion/n/n8fcc6544e781
  - https://shu-yashiro.com/ultraman-ost-history/
- 可信度：**高**（无专属主题）；使用范围（第 9 话后停用）为**中**（粉丝分析）。

### eleking（艾雷王）

- 专属主题：**无**（但有以它命名、为登场场面写的曲子）
- 依据：赛文第 3 话「湖のひみつ」使用 **M17「エレキング出現」**，作曲冬木透，属第 1 回录音（M1–M24 系）的剧伴库，官方 CD 以"湖のひみつ::エレキング出現＜M17＞"标注。它仍是可跨集复用的 M 编号剧伴，不是独立主题曲；其他话的复用情况**未核实**（未找到逐集使用表）。
- 若为通用 BGM：「エレキング出現（M17）」，用于《赛文奥特曼》第 3 话
- 官方 OST 收录：**有**。《ウルトラセブン45周年 音楽大全集》COCX-37583-6（第 3 话区块 Tr.20）；《ウルトラセブン コンプリート・ミュージック・コレクション》；《ウルトラセブン サウンドライブラリー》COCX-40216-20 Disc1 Tr.34；《絶体絶命！…昭和編》Tr.45
- 来源：
  - https://tower.jp/item/3152919
  - https://www.suruga-ya.com/ja/product/120058842
  - https://www.tacto.jp/ost/tokusatsu-ultra-seven-sound-library.htm
  - https://columbia.jp/prod-info/COCX-40216-20/
  - https://columbia.jp/prod-info/COCX-42285-6/
- 可信度：**高**（曲目、作曲、首次使用话数均有官方商品页支撑）。

### neronga（内隆嘎）

- 专属主题：**无**（但有以它命名的登场曲）
- 依据：第 3 话「科特隊出撃せよ」使用 **B3B「恐怖のネロンガ」**，作曲宮内国郎，属第 1 回录音（A–H）的通用"危机"类剧伴。原始曲目表按"危機"分组记为 **B-3B**；"恐怖のネロンガ"是后来 CD 按首次使用场景赋予的名字。该话还混用了本应第 12 话以后才用的第 2 回录音曲（如 M-6「死闘 二大怪獣」），属早期选曲的例外。B3B 在后续剧集的复用情况**未核实**。
- 若为通用 BGM：「恐怖のネロンガ（B3B）」＋「死闘 二大怪獣（M6）」，用于《奥特曼》第 3 话
- 官方 OST 收录：**有**。《絶体絶命！…昭和編》Tr.28；《ウルトラQ ウルトラマン 快獣ブースカ 宮内国郎の世界》COCX-39693-9 Disc3 Tr.17；《ウルトラマン ミュージックファイル》B-3B
- 来源：
  - https://columbia.jp/prod-info/COCX-39693-9/
  - https://columbia.jp/prod-info/COCX-42285-6/
  - https://www.cdjapan.co.jp/product/VPCD-81296
  - https://note.com/shota_/n/ne3f55438fc9b
  - https://shu-yashiro.com/ultraman-ost-history/
- 可信度：**高**（无专属主题）；后续复用为**中**（仅见"B-3 系后期用过约三次"的笼统说法）。

### black_king（布莱克王）

- 专属主题：**无**
- 依据：《归来的奥特曼》第 37–38 话音乐为冬木透。第 38 话在官方 MUSIC COLLECTION 中有明确使用曲标注：**《赛文》M70「イヴの夜」**（流用）。第 37 话**在官方合集里没有标注使用曲**；粉丝资料称杰克败北场面用的是 **M-13「ウルトラマンのテーマ／夕陽に立つウルトラマン」的短调器乐版**，以及 M-14/M-20 系"危机"曲，属推测。以「ブラックキング」命名的条目只存在于**效果音集**（D3-46），是叫声，不是音乐。
- 若为通用 BGM：M-13「夕陽に立つウルトラマン」系（第 37 话，粉丝证言）／《赛文》M70「イヴの夜」（第 38 话，官方标注）
- 官方 OST 收录：**有**（通用曲）。《帰ってきたウルトラマン MUSIC COLLECTION》COCX-40735-7；《帰ってきたウルトラマン 総音楽集》收录以第 37 话标题命名的组曲「ウルトラマン夕陽に死す」（是整集组曲，不是角色主题）
- 来源：
  - https://columbia.jp/prod-info/COCX-40735-7/
  - https://www.suruga-ya.jp/product/detail/120126549
  - https://www.oricon.co.jp/prof/183/products/133790/1/
  - https://note.com/joyous_ibis9754/n/n60c4042cc9ba
  - https://iketail.com/sfx/ultra-series/the-return-of-ultraman/bgm-yuuhi-ni-tatsu-ultraman-tsukkomi/
- 可信度：**中**（无专属主题可判定；但第 37 话逐场曲目无官方表，M-13 说法来自粉丝）。

### ex_gomora（EX 哥莫拉）

- 专属主题：**无**
- 依据：EX 哥莫拉影像初出为《奥特银河 大怪兽格斗》第 13 话「惑星脱出」（2008-02-23，BS11，全 13 话的最终话）。该作音乐为**佐橋俊彦**，官方原声带 COCX-34701（2008-01-23，47 曲）中**没有任何以怪兽命名的曲目**，战斗曲为「大怪獣の激突」「攻防戦」等通用曲。续篇《NEVER ENDING ODYSSEY》原声带（UMCC-1029，34 曲）中与哥莫拉相关的只有第 31 曲「倒れ伏すゴモラ」（场景曲），同样不是 EX 专属主题。后在《奥特曼 X》第 19 话（2015-12-01）再登场，该作音乐为小西貴雄，《X Complete Soundtrack》曲目亦无以哥莫拉命名的曲子。
- 若为通用 BGM：第 13 话具体曲目**未核实**；可用范围是 COCX-34701 中的「大怪獣の激突」「攻防戦」等通用战斗曲
- 官方 OST 收录：**有**（通用曲）。《ウルトラギャラクシー 大怪獣バトル オリジナル・サウンドトラック》COCX-34701；《NEVER ENDING ODYSSEY》UMCC-1029
- 来源：
  - https://columbia.jp/prod-info/COCX-34701/
  - https://www.billboard-japan.com/goods/detail/231371
  - https://artist.cdjournal.com/d/-/4108110831
  - https://cocreco.kodansha.co.jp/telemaga/news/feature/kaijubiyori/mNr8g （初出=第 13 话）
  - https://cal.syoboi.jp/tid/1279/time
  - https://w.atwiki.jp/mikuraio/pages/66.html
- 可信度：**高**（无专属主题，OST 曲目表可核）；第 13 话具体战斗曲为**未核实**。

### ex_red_king（EX 雷德王）

- 专属主题：**无**
- 依据：EX 雷德王实拍初出为《NEVER ENDING ODYSSEY》第 13 话「惑星崩壊」（BS11 初回 2009-03-14；东京电视台页面标注的 2010-03-25 应为后续播出）。该作原声带 UMCC-1029 曲目表中**没有**「EXレッドキング」「レッドキング」命名的曲子，只有「大怪獣戦」「奇襲攻撃」等通用战斗曲。其更早出处是游戏《奥特曼 Fighting Evolution Rebirth》（2005）的"改造雷德王"（来源为粉丝维基，**中**可信度），游戏侧 BGM 不在电视原声带范围，**未核实**。
- 若为通用 BGM：「大怪獣戦」等 UMCC-1029 通用战斗曲（第 13 话具体用哪首**未核实**）
- 官方 OST 收录：**有**（通用曲）。《NEVER ENDING ODYSSEY オリジナル・サウンドトラック》UMCC-1029；电影《大怪獣バトル ウルトラ銀河伝説 THE MOVIE》BVCL-59 亦无 EX 雷德王曲目
- 来源：
  - https://www.billboard-japan.com/goods/detail/231371
  - https://artist.cdjournal.com/d/-/4108110831
  - https://www.tv-tokyo.co.jp/contents/ultra-galaxy/monster/neo13.html
  - https://ultraman.fandom.com/ja/wiki/ウルトラギャラクシー大怪獣バトル_NEVER_ENDING_ODYSSEY
  - https://tsuburaya.fandom.com/wiki/EX_Red_King
  - https://www.cdjapan.co.jp/product/BVCL-59
- 可信度：**中**（无专属主题可判定；第 13 话播出日期在不同站点有 2009/2010 两种记载，具体曲目未核实）。

---

### 结论

**1. 真正意义上的"怪兽专属主题曲"：0 只。**
8 只怪兽在原剧中都没有为该怪兽单独创作、独立命名并作为"主题"使用的曲子。昭和期（1966/1967/1971）的做法是"全剧通用剧伴库 + 按场景选曲"；2007/2009 的《大怪兽格斗》系列也是"通用战斗曲 + 角色主题只给人类角色（レイ、ケイト、ダイル）"。

**2. 只有通用 BGM：5 只** —— `gomora`、`zetton`、`black_king`、`ex_gomora`、`ex_red_king`。
其中 `gomora` 另有一段 16 秒的"怪獣殿下"未发表/未确认使用片段（M.E. 磁带复原），但不构成主题曲；`zetton` 的最终战反而是"几乎无音乐、仅效果音"。

**3. 有"以怪兽命名的登场曲"但并非专属主题：3 只** —— `red_king`（B1「レッドキングの襲撃」）、`neronga`（B3B「恐怖のネロンガ」）、`eleking`（M17「エレキング出現」）。
这三首是 8 只里唯一可作"听感区分"的官方曲目；但曲名多为后期 CD 赋予，且仍属通用剧伴库，可跨集复用。

**4. 无法核实的具体项：3 只** —— `black_king`（第 37 话逐场曲目）、`ex_gomora`（第 13 话战斗曲）、`ex_red_king`（第 13 话战斗曲）。没有一只能拿到"官方逐集使用曲表"。

**对"8 个怪兽共用一首配乐"的资料判断：不反对，但会丢掉原剧的层次。**

- 资料上不支持"每只怪兽都有自己的主题曲"，所以共用一首**不会被原剧事实否定**。
- 但原剧的实际层次是三层：**通用战斗 BGM（共用）+ 怪兽登场曲（少数有名字）+ 怪兽吼声/效果音（各自不同）**。如果只做一首通用曲，最接近原剧的补法是给每只怪兽配**独立的登场音效/吼声**，而不是硬造 8 首"主题曲"。
- 若想做出区分度，可参考 `eleking` M17、`red_king` B1、`neronga` B3B 的"怪兽登场曲"思路，**自行原创**对应气质的短登场段；这些原曲是受版权保护的音乐作品，游戏不能直接取用原录音，需授权或自制。

**附：本次未做的核验**

- 未查证原始 CD booklet 的逐集使用曲注解（部分店铺曲目表已知存在标注错误）。
- 未查证《大怪兽格斗 ULTRA MONSTERS》街机/游戏侧 BGM（无公开原声带）。
- 未查证 2007/2009 两作第 13 话的逐场曲目。

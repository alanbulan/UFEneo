# 赛罗奥特曼声音来源计划（draft 2026-11-10）

状态：本轮未生成、未截取、未分离、未绑定任何声音；未改 `content/audio/*.json`，未改运行时，未安装。以下只是计划与来源门槛，不伪造。逐格动作数据见 `MOVES.md` 与 `moves/*.json`。

## 一、原则

- `source_kind=episode` 只用于原剧/电影实际音轨；数字拟音、转换、合成一律标 `original`；二创/翻奏标 `derivative`；转载原剧标 `episode` 并注明 `reprint`。不把二创或转载写成原剧原声。
- 本人喊声、叫招、受击、胜利逐项核归属（声优、作品、集数/时间码）。未核到就留空，不用相似声音冒充。
- 来源记录逐项写明上传者/平台、URL、作品与集数、时间码、SHA、取得日期；共享音效可用，但标 `original`/`shared`，不当作赛罗专属原声。
- 质量门槛沿用项目：SNR ≥ 12 dB，约 −20 LUFS，真峰值 ≤ −1 dBTP；不裁连续 ≥0.3 秒半音内稳定音乐音高、≥0.5 秒平直段、节拍或纯噪声。
- 一个动作至少一个声音事件；蓄力、发射、持续、命中、终结分开挂，不用一条长音盖完整段。
- 声音来源记录与运行时按 1:1 对 id：`sources.json` 中 `installed` 记录的 id 必须是 `runtime.json` `sounds` 的键，`sounds` 的 `source_record` 必须指回记录；纯源、未装或仅作 OGG 母带的记录标 `pending_install`。本轮不做任何注册，故不改这两份文件。

## 二、本角色已存在但本轮未绑定的运行时声音（事实）

`content/audio/runtime.json` 已有 5 条赛罗语音，`voices["ultraman-zero"]` 也已把 attack/super/hit/victory/intro 指向它们；这些是既有注册，不是本轮新增，也不是本轮绑定：

|id|用途|来源性质|
|---|---|---|
|`zero_roar_intro_20261110`|登场战吼|episode（B站转载战吼合集，`reprint`）|
|`zero_voice_attack_20261110`|攻击|episode（同上，`reprint`）|
|`zero_voice_hit_20261110`|受击|episode（同上，`reprint`）|
|`zero_voice_special_20261110`|必杀|episode（同上，`reprint`）|
|`zero_voice_win_20261110`|胜利|episode（同上，`reprint`）|

以上均为“未逐集定位”的战吼合集来源，未核到具体作品/集数/时码，不能当作已核实的原剧台词或叫招。本轮 `moves/*.json` 的 `audio` 字段只引用已存在的通用 id，不引用这 5 条，也不新增声音 id。

## 三、事件表（计划，未绑定）

|事件|计划来源|source_kind|当前状态|备注|
|---|---|---|---|---|
|普攻挥空|共享 `whiff_light` / `whiff_heavy`（别名 `light`/`heavy`/`sweep`/`launcher`/`throw`）|original|未绑定|原创数字音效，不是赛罗原声|
|普攻命中|共享 `hit_light` / `hit_heavy`|original|未绑定|0.12s / 0.23s，约 −20 LUFS|
|被防|共享 `guard`|original|未绑定|0.12s|
|投技抓取/摔落|共享 `land` 作落地摔击；抓取与提起待做|original / TBD|未绑定|`throw_slam`/`throw_lift`/`throw_grab` 在运行时不存在，本轮不引用；抓取声未核|
|爆气|共享冲击/爆发类；本角色独立爆气声待做|original / TBD|未绑定|爆气冲击是独立运行时效果，人物帧不含 FX|
|集束射线蓄光|共享 `charge`（loop）或原剧蓄能音轨|original / episode|未绑定|若用原剧须核集数与时码|
|集束射线发射|共享 `beam_start`|original|已写入 `special` 第 0 相事件|0.35s；CC0-1.0 原创，不是赛罗原声|
|集束射线持续|共享 `beam_loop`|original|未绑定|0.6s loop；赛罗整帧仅 3 tick，本轮不挂持续段|
|集束射线命中|共享 `hit_heavy` + `beam_hit` 命中特效|original|已写入 `audio.hit`|不扩判定|
|艾梅利姆切割蓄光|额灯蓄光专用声待做|TBD|未绑定|不能拿集束射线声冒充|
|艾梅利姆切割发射|细锐绿束专用声待做|TBD|未绑定|与集束射线宽束分开|
|赛罗头镖掷出|双刃破空专用声待做|TBD|未绑定|实体飞刃，不用光束声顶替|
|赛罗头镖回收|双镖装回头上的归位声待做|TBD|未绑定|收势相挂，不与命中声合并|
|低姿光弹 / 空中光弹|共享 `fireball`|original|已写入两招第 3 相事件|0.6s；运行时通用 pulse 特效配套|
|受击|共享 `hit_light` / `hit_heavy`，或本人受击战吼|original / episode|未绑定|逐动作选力度，不全部只挂通用命中|
|防御硬直 / 破防|共享 `guard`；破防另做|original / TBD|未绑定|破防不拿普通格挡声冒充|
|登场|本人登场战吼 `zero_roar_intro_20261110`|episode（`reprint`）|已注册、未在本轮绑定|来源未逐集定位|
|胜利|本人胜利声 `zero_voice_win_20261110`|episode（`reprint`）|已注册、未在本轮绑定|同上|
|挑衅|本人挑衅/招手声待做|TBD|未绑定|未核到就留空|
|叫招“赛罗集束射线”|原剧/电影本人叫招音轨|episode|未核|须核实是否叫招、声优与具体时码；不凭印象写集数|

## 四、已核实的共享音源（事实，非本轮新增）

|id|文件|时长|响度|来源性质|
|---|---|---:|---:|---|
|`beam_start`|`assets/audio/production/v1/beam_start.wav`|0.35s|−20.0 LUFS|原创数字音效，CC0-1.0|
|`beam_loop`|`assets/audio/production/v1/beam_loop.wav`|0.6s loop|−20.04 LUFS|原创数字音效，CC0-1.0|
|`hit_light`|`assets/audio/production/v1/hit_light.wav`|0.12s|−20.0 LUFS|原创数字音效，CC0-1.0|
|`hit_heavy`|`assets/audio/production/v1/hit_heavy.wav`|0.23s|−20.0 LUFS|原创数字音效，CC0-1.0|
|`guard`|`assets/audio/production/v1/guard.wav`|0.12s|−20.02 LUFS|原创数字音效，CC0-1.0|
|`fireball`|`assets/audio/production/v1/fireball.wav`|0.6s|−20.0 LUFS|原创数字音效，CC0-1.0|
|`land`|`assets/audio/production/v1/land.wav`|0.3s|−20.83 LUFS|原创数字音效，CC0-1.0|

以上 `true_peak_dbtp` 在 `sources.json` 中为空，属未测项；数值测量不等于人耳通过，正式启用前须按门槛复听并补测真峰值。以上均为共享原创音效，不是赛罗原声。

## 五、原声/拟音边界

- 若找到赛罗本人集束射线/艾梅利姆切割/头镖的干净原剧音轨：登记作品与集数、时码、`source_kind=episode`、SHA、响度与峰值；与音乐/旁白/其他角色重叠的段不得直接当本人音效。B站转载须标 `reprint` 并记上传者、URL、取得日期。
- 若找不到干净原声：用原创数字拟音，登记 `source_kind=original`、工具、参数、许可；不得写成“原剧赛罗音效”。
- 叫招/喊声必须与画面动作同源核对；不能用其他奥特曼（含赛文、泰罗）的喊声或光束声替代。
- 二创/翻奏如采用，标 `derivative`，记原曲与二创作者、平台、URL；不冒称官方原声。

## 六、未做

- 未截取任何原剧/电影音轨；未生成任何拟音；未做 Kits 分离；未改共享音频注册；未做试听。
- 未绑定集束射线/艾梅利姆切割/头镖/投技/受击/登场/胜利等任何事件到本角色新 id。
- 未生成或安装声音文件到 `assets/audio/characters/ultraman-zero/`；未改 `content/audio/sources.json`、`runtime.json`、`battle_music.json`。

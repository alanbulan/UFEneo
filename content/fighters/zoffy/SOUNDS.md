# 佐菲声音卡

截至 2026-11-21，佐菲已有运行语音、状态声、脚步声和招式声音绑定。下列 9 个语音 ID 对应 `voices` 的 10 个事件槽（`light` 复用 `attack`）；已逐项核对 [runtime.json](../../audio/runtime.json)、[sources.json](../../audio/sources.json)、本机文件路径与输出 SHA。9 条来源记录均为 `runtime_status=installed`、`listening_reviewed=false`。这取代旧草案的“声音均未绑定”，不代表本人原声归属或听感通过。

## 已安装语音

| 事件槽 | 运行 ID | 来源 / 合集内时间码 |
| --- | --- | --- |
| 登场 `intro` | `zoffy_roar_intro_20261110` | A / 00:00:02.500–00:00:04.300 |
| 攻击 `attack` / `light` | `zoffy_voice_attack_20261110` | A / 00:00:00.150–00:00:01.010 |
| 必杀 `super` | `zoffy_voice_special_20261110` | A / 00:00:01.350–00:00:02.350 |
| 受击 `hit` | `zoffy_voice_hit_20261110` | A / 00:00:04.490–00:00:05.090 |
| 胜利 `victory` | `zoffy_voice_win_20261110` | A / 00:00:05.370–00:00:06.870 |
| 倒地 `down` | `zoffy_voice_down_20261111` | B / 00:00:04.000–00:00:04.680 |
| 挑衅 `taunt` | `zoffy_voice_taunt_20261111` | B / 00:00:10.060–00:00:10.800 |
| 重击 `heavy` | `zoffy_voice_heavy_20261111` | B / 00:00:25.120–00:00:26.260 |
| 超时 `timeout` | `zoffy_voice_timeout_20261111` | A / 00:00:02.780–00:00:04.040 |

- A：Bilibili 上传者一清二水的[「佐菲奥特曼的怒吼声」](https://www.bilibili.com/video/BV1b44y1w7g6)，台账取得日期 2026-11-10，登记作品为《奥特曼》1966 原剧战吼，未逐集定位。登场段经 Kits 人声分离，未做声线转换。
- B：Bilibili 上传者番茄蓝莓水的[初代/佐菲/杰克音效素材第 9 P](https://www.bilibili.com/video/BV1WKuDz9Evb?p=9)，台账取得日期 2026-11-11。该分 P 标为「佐菲/奥父/王——战吼（通用）」；原台账明确标注角色归属和语义未听审，不能把 `down` / `heavy` / `taunt` 写成已经确认的佐菲本人原声。

两源均登记为 `source_kind=episode`、`reprint=true`。表内时间码是合集位置，不是原剧时间码；事件槽按片段长度和能量等特征作候选分配，尚未核定台词、叫招或对应动作。完整原始 SHA、输出 SHA、处理参数和取得时间保留在 `sources.json`，不在本卡复制第二份台账。

## 当前声音接线

- [state_events.json](../../audio/state_events.json) 登记 53 个状态键，前后走入口留空，其余 51 个状态入口引用 11 个共享原创音效 ID。前后走脚步表已按各自 clip 改为 32 tick、接触点 `[0,16]`、`step`，由脚步相位调度；已移除重复的入态 `step`。冲刺 sprite 1/3 另接 `step`。
- 受击、重击、挑衅通过 `frame_sounds` 的 sprite 0 接对应语音；挑衅默认 `U+L`（防御+投技）的真实输入到语音恰一次已通过 `phase3_fx_audio` 回归，范围为 `root_delegated_by_user`，未听审。该回归只确认当前候选被调度，不确认 B 源的角色归属。
- Z光线 `special`、超级冻霜 `special2`、M87光线 A型 `special3`、空中Z光线 `air_special` 均已声明共享原创 `beam_start`，命中/被防接 `hit_heavy` / `guard`。四招没有显式 `audio_loop`，不能写成四套本人技能原声或完整持续声已经齐备。
- 队长过顶摔 `motion_41236` 使用原创 `taro_motion_41236_charge`、`taro_throw_grab`、`taro_motion_41236_contact`、`taro_guard`；这些沿用项目拟音 ID，不是泰罗演员语音或佐菲原剧投技声。普通拳脚、格挡、跳跃和落地也已有共享原创音效。

## 待完成与验收边界

- 前后走图像和脚步周期现为各 32 tick；移除重复入态步声后，已通过 `phase3_fx_audio` 双朝向逐 tick 两周期回归（`root_delegated_by_user`）。该检查只确认接线相位和发声次数，真实触地观感与听感仍需复核。
- Z光线、冻霜、M87 与斯派修姆的原剧音效、准确作品/集数/时码及独立起势/持续/尾音仍待核实；共用原创拟音不等于本人技能声音还原。
- 9 条语音的演员归属、事件语义、分离残留和整体听感均未签收。来源许可台账为转载仅个人研究、未登记商业再分发授权。
- 本轮同步接线与文档，没有采集、生成或替换音频，没有修改 `listening_reviewed`；无录屏。资源和逻辑调度检查不等于美术或听审通过。

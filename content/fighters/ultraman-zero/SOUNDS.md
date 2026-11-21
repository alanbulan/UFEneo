# 赛罗声音卡

截至 2026-11-21，赛罗已有运行语音、状态声、脚步声和招式声音绑定。下列 9 个语音 ID 对应 `voices` 的 10 个事件槽（`light` 复用 `attack`）；已逐项核对 [runtime.json](../../audio/runtime.json)、[sources.json](../../audio/sources.json)、本机文件路径与输出 SHA。9 条来源记录均为 `runtime_status=installed`、`listening_reviewed=false`。旧计划中的“未安装、均未绑定”已经不适用，逐集定位和听审仍未完成。

## 已安装语音

| 事件槽 | 运行 ID | 合集内时间码 |
| --- | --- | --- |
| 登场 `intro` | `zero_roar_intro_20261110` | 00:00:02.000–00:00:05.000 |
| 攻击 `attack` / `light` | `zero_voice_attack_20261110` | 00:00:06.330–00:00:07.190 |
| 必杀 `super` | `zero_voice_special_20261110` | 00:00:12.770–00:00:14.210 |
| 受击 `hit` | `zero_voice_hit_20261110` | 00:00:20.050–00:00:20.510 |
| 胜利 `victory` | `zero_voice_win_20261110` | 00:01:04.510–00:01:06.390 |
| 倒地 `down` | `zero_voice_down_20261111` | 00:00:07.820–00:00:08.380 |
| 挑衅 `taunt` | `zero_voice_taunt_20261111` | 00:00:09.460–00:00:10.620 |
| 重击 `heavy` | `zero_voice_heavy_20261111` | 00:00:02.180–00:00:03.340 |
| 超时 `timeout` | `zero_voice_timeout_20261111` | 00:00:53.760–00:00:55.560 |

来源为 Bilibili 上传者夕阳的勇者的[「赛罗奥特曼部分战吼」](https://www.bilibili.com/video/BV1BdC3YjEGq)，台账取得日期 2026-11-10，登记 `source_kind=episode`、`reprint=true`，作品只定位到《奥特曼》系列，未逐集定位。表内时间码是合集位置，不是原剧时间码。登场段经 Kits 人声分离，各事件槽仍是按片段特征作候选分配，不是已经核实的本人叫招或台词。

## 当前声音接线

- [state_events.json](../../audio/state_events.json) 登记 53 个状态键，前后走入口留空，其余 51 个状态入口引用 11 个共享原创音效 ID。前走脚步表已按 clip 改为 72 tick、接触点 `[0,36]`；后走为 40 tick、`[0,20]`，均用 `step` 并由脚步相位调度。已移除重复的入态 `step`；冲刺 sprite 1/3 另接 `step`。
- 受击、重击、挑衅通过 `frame_sounds` 的 sprite 0 接对应语音；挑衅默认 `U+L`（防御+投技）的真实输入到语音恰一次已通过 `phase3_fx_audio` 回归，范围为 `root_delegated_by_user`，未听审。
- 集束射线、艾梅利姆切割、赛罗头镖和空中集束射线均声明共享原创 `beam_start`，命中/被防接 `hit_heavy` / `guard`；四招没有显式 `audio_loop`。头镖起手目前也复用 `beam_start`，不能写成双刃专属掷出声已经完成。
- `special3` 的两枚实体头镖已把 `return_sound` 接到 `omega_super1_catch`，由真实 `weapon_return` 事件消费；回接专项已通过。该 ID 对应 `assets/audio/fighters/ultraman-omega/super1/catch.wav`，是 0.22 秒项目原创机械拟音，来源记录为 `original`、`installed_pending_user_listening`、`listening_reviewed=false`。它不是欧米伽演员语音，也不是赛罗原剧回接音；没有固定时间播放的伪回接事件。
- 赛罗过顶摔 `motion_41236` 使用原创 `taro_motion_41236_charge`、`taro_throw_grab`、`taro_motion_41236_contact`、`taro_guard`；基础光弹使用原创 `fireball`。这些均为已有项目拟音，不作为本人原剧声音证明。

## 待完成与验收边界

- 前后走图像和脚步周期现分别为 72 / 40 tick；移除重复入态步声后，已通过 `phase3_fx_audio` 双朝向逐 tick 两周期回归（`root_delegated_by_user`）。该检查只确认接线相位和发声次数，真实触地观感与听感仍需复核。
- 集束射线、艾梅利姆切割、双头镖的独立起势/持续/终结声音和原剧镜头来源仍待核实；新增回接绑定不代表整套头镖声音已还原。
- 语音角色版本、事件语义、分离残留与总体听感仍待听审。来源许可台账为转载仅个人研究、未登记商业再分发授权；原创回接拟音按现有 CC0-1.0 来源记录复用。
- 本轮同步接线与文档，没有采集、生成或替换音频，没有修改 `listening_reviewed`；无录屏。资源和逻辑调度检查不等于听审通过。

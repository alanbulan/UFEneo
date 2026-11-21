# 奥特之父声音卡

截至 2026-11-21，角色已有运行语音、状态声、脚步声和招式声音绑定。下列 9 个语音 ID 对应 `voices` 的 10 个事件槽（`light` 复用 `attack`）；已逐项核对 [runtime.json](../../audio/runtime.json)、[sources.json](../../audio/sources.json)、本机文件路径与输出 SHA。9 条来源记录均为 `runtime_status=installed`、`listening_reviewed=false`，未完成逐集定位和听审。

## 已安装语音

| 事件槽 | 运行 ID | 来源 / 合集内时间码 |
| --- | --- | --- |
| 登场 `intro` | `father_voice_intro_20261110` | A / 00:00:00.228–00:00:01.340 |
| 攻击 `attack` / `light` | `father_voice_attack_20261110` | A / 00:00:02.128–00:00:03.212 |
| 必杀 `super` | `father_voice_special_20261110` | A / 00:00:04.200–00:00:05.680 |
| 受击 `hit` | `father_voice_hit_20261110` | A / 00:00:03.446–00:00:04.020 |
| 胜利 `victory` | `father_voice_win_20261110` | A / 00:00:06.121–00:00:07.760 |
| 倒地 `down` | `father_voice_down_20261111` | B / 00:00:03.840–00:00:04.420 |
| 挑衅 `taunt` | `father_voice_taunt_20261111` | B / 00:00:00.980–00:00:01.920 |
| 重击 `heavy` | `father_voice_heavy_20261111` | B / 00:00:06.520–00:00:09.020 |
| 超时 `timeout` | `father_voice_timeout_20261111` | B / 00:00:13.940–00:00:16.440 |

- A：Bilibili 上传者郭圣耀的[「奥特之父的战吼」](https://www.bilibili.com/video/BV1SNEc6YEy7)，台账取得日期 2026-11-10。
- B：Bilibili 上传者泰罗教官宝岛Stars的[「奥特之父，奥特之母的战吼」](https://www.bilibili.com/video/BV1GfV5zjE14)，台账取得日期 2026-11-11；四槽取自台账所称“父半段”，角色与事件语义尚未听审。

两源均登记 `source_kind=episode`、`reprint=true`，作品只定位到《奥特曼》系列，未逐集定位。表内时间码是合集位置，不是原剧时间码；事件槽为候选分配，不能当作已核实的本人叫招。旧来源 `note` 中残留的“未接入”不覆盖当前 `installed` 状态及实际运行映射。

## 当前声音接线

- [state_events.json](../../audio/state_events.json) 登记 53 个状态键，前后走入口留空，其余 51 个状态入口引用 11 个共享原创音效 ID。前走脚步表已按 clip 改为 72 tick、接触点 `[0,36]`；后走为 64 tick、`[0,32]`，均用 `step` 并由脚步相位调度。已移除重复的入态 `step`；冲刺 sprite 1/3 另接 `step`。
- 受击、重击、挑衅通过 `frame_sounds` 的 sprite 0 接对应语音；挑衅默认 `U+L`（防御+投技）的真实输入到语音恰一次已通过 `phase3_fx_audio` 回归，范围为 `root_delegated_by_user`，未听审。
- 父亲射击、奥特之角·力量光束、能量充填和空中父亲射击均声明共享原创 `beam_start`，命中/被防接 `hit_heavy` / `guard`。四招没有显式 `audio_loop`，不能写成专属起势/持续/终结声齐备。
- 基础光弹使用原创 `fireball` 或其 `pulse` 别名；抱腰过顶掷 `motion_41236` 当前只有 `whiff_heavy` 帧事件，没有独立的 `audio.throw_slam` 声明。普通拳脚、格挡和落地仍用项目共享原创音效。

## 待完成与验收边界

- 前后走图像和脚步周期现分别为 72 / 64 tick；移除重复入态步声后，已通过 `phase3_fx_audio` 双朝向逐 tick 两周期回归（`root_delegated_by_user`）。该检查只确认接线相位和发声次数，真实触地观感与听感仍需复核，不能仅凭周期倍数推定触地。
- 三槽技能的原剧音轨、具体作品/集数与镜头时码、专属声音分段仍待核定；语音角色归属和听感也未通过。来源许可台账为转载仅个人研究、未登记商业再分发授权。
- 本轮同步接线与文档，没有采集、生成或替换音频，没有修改 `listening_reviewed`；无录屏。逻辑调度与资源校验不等于听审通过。

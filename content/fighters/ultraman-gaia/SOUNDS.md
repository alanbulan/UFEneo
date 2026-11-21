# 盖亚声音卡

截至 2026-11-21，角色已有运行语音、状态声、脚步声和招式声音绑定。下列 9 个语音 ID 对应 `voices` 的 10 个事件槽（`light` 复用 `attack`）；已逐项核对 [runtime.json](../../audio/runtime.json)、[sources.json](../../audio/sources.json)、本机文件路径与输出 SHA。9 条来源记录均为 `runtime_status=installed`、`listening_reviewed=false`，未完成逐集定位和听审。

## 已安装语音

| 事件槽 | 运行 ID | 来源 / 合集内时间码 |
| --- | --- | --- |
| 登场 `intro` | `gaia_roar_intro_20261110` | P2 / 00:00:06.600–00:00:08.300 |
| 攻击 `attack` / `light` | `gaia_voice_attack_20261110` | P2 / 00:00:27.990–00:00:28.890 |
| 必杀 `super` | `gaia_voice_special_20261110` | P2 / 00:01:52.030–00:01:53.270 |
| 受击 `hit` | `gaia_voice_hit_20261110` | P2 / 00:00:03.910–00:00:04.410 |
| 胜利 `victory` | `gaia_voice_win_20261110` | P2 / 00:01:58.030–00:01:59.250 |
| 倒地 `down` | `gaia_voice_down_20261111` | P4 / 00:00:04.080–00:00:04.640 |
| 挑衅 `taunt` | `gaia_voice_taunt_20261111` | P2 / 00:00:06.960–00:00:08.020 |
| 重击 `heavy` | `gaia_voice_heavy_20261111` | P3 / 00:00:30.980–00:00:33.480 |
| 超时 `timeout` | `gaia_voice_timeout_20261111` | P3 / 00:00:36.580–00:00:37.800 |

来源为 Bilibili 上传者番茄蓝莓水的盖亚战吼素材：[P2「战吼（3.0）」](https://www.bilibili.com/video/BV1GRFSeJEFd?p=2)、[P3「长战吼（3.0）」](https://www.bilibili.com/video/BV1GRFSeJEFd?p=3)、[P4「吃瘪战吼（3.0）」](https://www.bilibili.com/video/BV1GRFSeJEFd?p=4)。台账取得日期分别为 2026-11-10（P2）、2026-11-11（P3/P4），均登记 `source_kind=episode`、`reprint=true`、作品《盖亚奥特曼》，尚未逐集定位。表内时间码是各分 P 的素材位置，不是原剧时间码。

登场段经 Kits 人声分离，台账记录静态增益 `+15.89 dB` 并注明可能抬高噪声底；没有听审结果可以消除该未决项。各事件槽仍是按片段特征分配的候选，不是已核实的台词或叫招。

## 当前声音接线

- [state_events.json](../../audio/state_events.json) 登记 53 个状态键，前后走入口留空，其余 51 个状态入口引用 11 个共享原创音效 ID；前后走的脚步表均为 40 tick、接触点 `[0,20]`、`step`，与现用行走 clip 总时长一致。已移除重复的入态 `step`，走路仅由脚步相位调度；已通过 `phase3_fx_audio` 双朝向逐 tick 两周期回归（`root_delegated_by_user`），未听审。冲刺 sprite 1/3 另接 `step`。
- 受击、重击、挑衅通过 `frame_sounds` 的 sprite 0 接对应语音；挑衅默认 `U+L`（防御+投技）的真实输入到语音恰一次已通过 `phase3_fx_audio` 回归，范围为 `root_delegated_by_user`，未听审。
- 光子冰刀、量子流线、光子粉碎机和空中量子流线均声明共享原创 `beam_start`，命中/被防接 `hit_heavy` / `guard`。四招没有显式 `audio_loop`，尚未形成三槽专属的完整声音表现。
- 大地抱摔 `motion_41236` 使用原创 `taro_motion_41236_charge`、`taro_throw_grab`、`taro_motion_41236_contact`、`taro_guard`；这些沿用项目拟音 ID，不是泰罗演员语音或盖亚原剧投技声。普通拳脚和落地仍复用共享原创音效。

## 待完成与验收边界

- 各技能的原剧声音、集数与镜头时码、独立起势/持续/尾音尚未逐项核实；不能把共用音效或战吼候选当作完整原声还原。
- 语音事件语义、分离残留、噪声底与总体听感仍待听审。来源许可台账为转载仅个人研究、未登记商业再分发授权。
- 本轮同步接线与文档，没有采集、生成或替换音频，没有修改 `listening_reviewed`；无录屏。逻辑调度与资源校验不等于听审通过。

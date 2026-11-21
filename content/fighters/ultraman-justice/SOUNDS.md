# 杰斯提斯声音卡

截至 2026-11-21，角色已有运行语音、状态声、脚步声和招式声音绑定。下列 9 个语音 ID 对应 `voices` 的 10 个事件槽（`light` 复用 `attack`）；已逐项核对 [runtime.json](../../audio/runtime.json)、[sources.json](../../audio/sources.json)、本机文件路径与输出 SHA。9 条来源记录均为 `runtime_status=installed`、`listening_reviewed=false`。本卡记录装机事实，不代表原剧归属或听感通过。

## 已安装语音

| 事件槽 | 运行 ID | 合集内时间码 |
| --- | --- | --- |
| 登场 `intro` | `justice_roar_intro_20261110` | 00:00:09.000–00:00:12.500 |
| 攻击 `attack` / `light` | `justice_voice_attack_20261110` | 00:00:00.270–00:00:01.190 |
| 必杀 `super` | `justice_voice_special_20261110` | 00:00:14.790–00:00:16.430 |
| 受击 `hit` | `justice_voice_hit_20261110` | 00:00:12.750–00:00:13.910 |
| 胜利 `victory` | `justice_voice_win_20261110` | 00:00:19.950–00:00:21.610 |
| 倒地 `down` | `justice_voice_down_20261111` | 00:00:05.220–00:00:06.260 |
| 挑衅 `taunt` | `justice_voice_taunt_20261111` | 00:00:01.320–00:00:02.540 |
| 重击 `heavy` | `justice_voice_heavy_20261111` | 00:00:06.840–00:00:08.500 |
| 超时 `timeout` | `justice_voice_timeout_20261111` | 00:00:17.200–00:00:18.740 |

来源为郭圣耀在 Bilibili 上传的[「杰斯提斯奥特曼的战吼」](https://www.bilibili.com/video/BV15hE964E6u)，台账取得时间为 2026-11-10，登记作品《高斯奥特曼VS杰斯提斯奥特曼 THE FINAL BATTLE》。这些是 `source_kind=episode`、`reprint=true` 的转载合集切片，尚未逐场定位；表内时间码是合集位置，不是电影原片时间码。登场片段经 Kits 人声分离，其余事件槽按时长等特征作候选分配，未核定具体叫招或语义。

## 当前声音接线

- [state_events.json](../../audio/state_events.json) 登记 53 个状态键，前后走入口留空，其余 51 个状态入口引用 11 个共享原创音效 ID；前后走的脚步表均为 40 tick、接触点 `[0,20]`、`step`，与现用行走 clip 总时长一致。已移除重复的入态 `step`，走路仅由脚步相位调度；已通过 `phase3_fx_audio` 双朝向逐 tick 两周期回归（`root_delegated_by_user`），未听审。冲刺 sprite 1/3 另接 `step`。
- 受击、重击、挑衅通过 `frame_sounds` 的 sprite 0 接对应语音；挑衅入口为默认键 `U+L`（防御+投技）。真实输入到挑衅语音恰一次的调度已通过 `phase3_fx_audio` 回归，验收范围为 `root_delegated_by_user`，未听审。
- `special` / `special2` / `special3` / `air_special` 已声明共享原创 `beam_start`，并在实际命中/被防时使用 `hit_heavy` / `guard`。它们没有显式 `audio_loop`，不能写成已安装四套本人光线原声或完整持续声。
- `motion_41236` 已接原创 `taro_motion_41236_charge`、`taro_motion_41236_cast`、`taro_throw_grab`、`taro_motion_41236_contact`、`taro_guard`。这些是沿用已有项目拟音 ID，不是泰罗演员语音或杰斯提斯原剧投技声。
- 基础光弹引用原创 `fireball`；普通拳脚引用 `light` / `heavy` / `launcher` / `sweep` 等已登记别名。声音资源和来源 SHA 已核，不代表逐动作音画同步已验收。

## 待完成与验收边界

- 闪光效应、杰斯提斯粉碎、比库托流姆光线的本人原剧音效、独立起势/持续/尾音尚未逐场定位；当前共享拟音不能写成专属还原。
- 9 条候选语音的演员归属、事件语义、分离残留和整体听感仍待听审。来源许可台账为原权利人保留权利、转载仅个人研究，未登记商业再分发授权。
- 本轮同步接线与文档，没有采集、生成或替换音频，没有修改 `listening_reviewed`；无录屏。逻辑调度与资源校验不等于听审通过。

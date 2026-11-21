# 奥特之母声音卡

截至 2026-11-21，角色已有运行语音、状态声、脚步声和招式声音绑定。下列 9 个语音 ID 对应 `voices` 的 10 个事件槽（`light` 复用 `attack`）；已逐项核对 [runtime.json](../../audio/runtime.json)、[sources.json](../../audio/sources.json)、本机文件路径与输出 SHA。9 条来源记录均为 `runtime_status=installed`、`listening_reviewed=false`，未完成逐集定位和听审。

## 已安装语音

| 事件槽 | 运行 ID | 来源 / 合集内时间码 |
| --- | --- | --- |
| 登场 `intro` | `mother_voice_intro_20261110` | A / 00:00:00.202–00:00:01.056 |
| 攻击 `attack` / `light` | `mother_voice_attack_20261110` | A / 00:00:01.465–00:00:02.418 |
| 必杀 `super` | `mother_voice_special_20261110` | A / 00:00:03.860–00:00:04.780 |
| 受击 `hit` | `mother_voice_hit_20261110` | A / 00:00:05.100–00:00:05.714 |
| 胜利 `victory` | `mother_voice_win_20261110` | A / 00:00:08.670–00:00:09.920 |
| 倒地 `down` | `mother_voice_down_20261111` | A / 00:00:02.800–00:00:03.560 |
| 挑衅 `taunt` | `mother_voice_taunt_20261111` | A / 00:00:06.200–00:00:07.100 |
| 重击 `heavy` | `mother_voice_heavy_20261111` | A / 00:00:07.560–00:00:08.360 |
| 超时 `timeout` | `mother_voice_timeout_20261111` | B / 00:01:31.900–00:01:34.400 |

- A：Bilibili 上传者郭圣耀的[「奥特之母的战吼」](https://www.bilibili.com/video/BV1STEc6wEwe)，台账取得日期 2026-11-10。
- B：Bilibili 上传者泰罗教官宝岛Stars的[「奥特之父，奥特之母的战吼」](https://www.bilibili.com/video/BV1GfV5zjE14)，台账取得日期 2026-11-11。`timeout` 仅按台账的“母半段”窗口作候选分配，未由人耳确认角色与语义。

两源均登记为 `source_kind=episode`、`reprint=true`，作品只定位到《奥特曼》系列，未逐集定位。表内时间码是合集位置，不是原剧时间码；当前安装不代表这些片段是已核实的叫招。旧来源 `note` 中残留的“未接入”不覆盖当前 `installed` 状态及实际运行映射。

## 当前声音接线

- [state_events.json](../../audio/state_events.json) 登记 53 个状态键，前后走入口留空，其余 51 个状态入口引用 11 个共享原创音效 ID；前后走的脚步表均为 40 tick、接触点 `[0,20]`、`step`，与现用行走 clip 总时长一致。已移除重复的入态 `step`，走路仅由脚步相位调度；已通过 `phase3_fx_audio` 双朝向逐 tick 两周期回归（`root_delegated_by_user`），未听审。冲刺 sprite 1/3 另接 `step`。
- 受击、重击、挑衅通过 `frame_sounds` 的 sprite 0 接对应语音；挑衅默认 `U+L`（防御+投技）的真实输入到语音恰一次已通过 `phase3_fx_audio` 回归，范围为 `root_delegated_by_user`，未听审。
- 母亲光线、母亲破坏光线、母亲淋浴与空中母亲破坏光线均已声明共享原创 `beam_start`，数据中的命中/被防映射为 `hit_heavy` / `guard`；只有发生对应接触事件才消费，治疗技不会因此凭空播放命中声。四招均没有显式 `audio_loop`。
- 抱腰过顶掷 `motion_41236` 使用原创 `taro_motion_41236_charge`、`taro_throw_grab`、`taro_motion_41236_contact`、`taro_guard`；这些是项目现有拟音，不是泰罗演员语音或奥母原剧音效。普通拳脚和落地仍复用共享原创音效。

## 待完成与验收边界

- 治疗、破坏光线、再生光雨的专属声音及各自起势/持续/收势尚未逐项核定；共用 `beam_start` 不代表三种技能听觉差异已经完成。
- 语音角色归属、事件语义、合集残留及整体听感仍待听审。来源许可台账为转载仅个人研究、未登记商业再分发授权。
- 本轮同步接线与文档，没有采集、生成或替换音频，没有修改 `listening_reviewed`；无录屏。逻辑调度与资源校验不等于听审通过。

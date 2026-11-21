# 奥特之王声音卡

截至 2026-11-21，角色已有运行语音、状态声、脚步声和招式声音绑定。下列 9 个语音 ID 对应 `voices` 的 10 个事件槽（`light` 复用 `attack`）；已逐项核对 [runtime.json](../../audio/runtime.json)、[sources.json](../../audio/sources.json)、本机文件路径与输出 SHA。9 条来源记录均为 `runtime_status=installed`、`listening_reviewed=false`，未完成逐集定位和听审。

## 已安装语音

| 事件槽 | 运行 ID | 来源 / 合集内时间码 |
| --- | --- | --- |
| 登场 `intro` | `king_voice_intro_20261110` | A / 00:00:01.470–00:00:03.070 |
| 攻击 `attack` / `light` | `king_voice_attack_20261110` | A / 00:00:07.603–00:00:09.173 |
| 必杀 `super` | `king_voice_special_20261110` | A / 00:00:16.010–00:00:17.810 |
| 受击 `hit` | `king_voice_hit_20261110` | A / 00:00:09.840–00:00:11.460 |
| 胜利 `victory` | `king_voice_win_20261110` | A / 00:00:22.380–00:00:24.180 |
| 倒地 `down` | `king_voice_down_20261111` | B / 00:00:27.620–00:00:29.220 |
| 挑衅 `taunt` | `king_voice_taunt_20261111` | B / 00:00:33.560–00:00:35.260 |
| 重击 `heavy` | `king_voice_heavy_20261111` | B / 00:00:56.800–00:00:59.220 |
| 超时 `timeout` | `king_voice_timeout_20261111` | B / 00:00:59.460–00:01:01.960 |

- A：Bilibili 上传者泰罗教官宝岛Stars的[「奥特之王的战吼（中曾根雅夫，小泉纯一郎，桧山修之）」](https://www.bilibili.com/video/BV1i25TzNEri)，台账取得日期 2026-11-10。台账把登场段描述为捷德胶囊音效，其余槽来自不同声优段；不能写成同一影视版本的一套声音。
- B：Bilibili 上传者郭圣耀的[「奥特之王的战吼」](https://www.bilibili.com/video/BV1kzVG63ESK)，台账取得日期 2026-11-11。

两源均登记为 `source_kind=episode`、`reprint=true`；作品只定位到《奥特曼》系列，未逐集定位。表内时间码为合集位置，事件槽按片段特征作候选分配，未确认台词、叫招或实际动作语义。旧来源 `note` 中残留的“未接入”不覆盖当前 `installed` 状态及实际运行映射。

## 当前声音接线

- [state_events.json](../../audio/state_events.json) 登记 53 个状态键，前后走入口留空，其余 51 个状态入口引用 11 个共享原创音效 ID；前后走的脚步表均为 40 tick、接触点 `[0,20]`、`step`，与现用行走 clip 总时长一致。已移除重复的入态 `step`，走路仅由脚步相位调度；已通过 `phase3_fx_audio` 双朝向逐 tick 两周期回归（`root_delegated_by_user`），未听审。冲刺 sprite 1/3 另接 `step`。
- 受击、重击、挑衅通过 `frame_sounds` 的 sprite 0 接对应语音；挑衅默认 `U+L`（防御+投技）的真实输入到语音恰一次已通过 `phase3_fx_audio` 回归，范围为 `root_delegated_by_user`，未听审。
- 王者闪光、洗礼光线、王者再生光线和空中王者闪光的数据已声明共享原创 `beam_start`；命中/被防接 `hit_heavy` / `guard`。四招没有显式 `audio_loop`，尚不能称为本人技能的完整专属声场。
- 念力过顶投 `motion_41236` 使用原创 `taro_motion_41236_charge`、`taro_throw_grab`、`taro_motion_41236_contact`、`taro_guard`；这些沿用已有项目拟音 ID，不是泰罗演员语音或奥王原剧投技声。普通拳脚和落地仍复用共享原创音效。

## 待完成与验收边界

- 三槽技能的原剧音轨、具体作品/集数、独立起势/持续/终结声尚未逐项核定；现用共享音效不代表技能还原完成。
- 跨声优候选的角色版本一致性、事件语义和听感仍待审核。来源许可台账为转载仅个人研究、未登记商业再分发授权。
- 本轮同步接线与文档，没有采集、生成或替换音频，没有修改 `listening_reviewed`；无录屏。装机、SHA 和逻辑调度通过不等于听审通过。

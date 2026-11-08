# 佐菲 声音来源计划（draft 2026-11-08）

状态：本轮未生成、未截取、未绑定任何声音；未改 `content/audio/*.json`，未改运行时。以下为计划与来源门槛，不伪造。

## 一、原则

- `source_kind=episode` 只用于原剧/电影的实际音轨；数字拟音、转换、合成一律标 `original` 或 `generated`，不冒称原声。
- 本人喊声、叫招、受击/胜利等逐项核归属；未核到就留空，不用相似声音冒充。
- 共享音效可用，但必须标 `shared`/`original`，不当作佐菲专属原声。
- 质量门槛沿用项目：SNR ≥ 12 dB，约 −20 LUFS，真峰值 ≤ −1 dBTP；不裁连续≥0.3秒半音内稳定音乐音高、≥0.5秒平直段、节拍或纯噪声。
- 一个动作至少一个声音事件；蓄力、发射、持续、命中、终结分开挂，不用一条长音盖完整段。

## 二、事件表

| 事件 | 计划来源 | source_kind | 当前状态 | 备注 |
|---|---|---|---|---|
| M87 蓄势 | 共享 `charge.wav`，或原剧 M87 起势音轨 | original / episode | 未绑定 | 若用共享，标 original，不称原声 |
| M87 出膛 | 共享 `assets/audio/production/v1/beam_start.wav` | original | 未绑定 | 0.35s；CC0-1.0 原创数字音效，不是佐菲原声 |
| M87 持续 | 共享 `assets/audio/production/v1/beam_loop.wav` | original | 未绑定 | 0.6s loop；−20.04 LUFS；真峰值 −9.51 dBFS |
| M87 命中 | 共享 contact/special 命中 | shared | 未绑定 | 按真实命中事件挂；不扩判定 |
| M87 消散 | 共享 `beam_tail` 类尾音 | original / shared | 未绑定 | 不与命中声混为一条 |
| 叫招“M87” | 原剧/电影本人音轨 | episode | 未核 | 先核实是否叫招、声优与具体时码 |
| Z光线 | 待做 | TBD | 未核 | 独立电流声，不拿 M87 声冒充 |
| 超级冻霜 | 待做 | TBD | 未核 | 冷冻气体/结冰声 |
| 受击/防御/投摔 | 共享 contact，或原剧本人喘息 | shared / episode | 未绑定 | 逐动作选力度，不全部只挂通用命中 |
| 登场/胜利/挑衅 | 原剧本人喊声 | episode | 未核 | 逐项核归属；未核到留空 |

## 三、已核实的共享音源（事实）

- `assets/audio/production/v1/beam_start.wav`
  - `source_kind=original`，CC0-1.0，0.35s，48 kHz，−20.0 LUFS，真峰值 −7.49 dBFS。
  - 来源：`assets/audio/shared/actions/v001/beam_release/sound.wav`；原文件 SHA 与处理参数见 `content/audio/sources.json`。
  - 是共享原创数字音效，不是佐菲原声；如用于 M87，须在运行记录中标 `original`。
- `assets/audio/production/v1/beam_loop.wav`
  - `source_kind=original`，CC0-1.0，0.6s loop，−20.04 LUFS，真峰值 −9.51 dBFS。
  - 来源：`assets/audio/shared/actions/v001/beam_sustain/sound.wav`。
- 以上文件当前 `listening_reviewed=false`；数值测量不等于人耳通过。若要用于 M87，需按项目门槛复听并记录。

## 四、原声/拟音边界

- 若找到 1984 年电影《ZOFFY》或《梅比斯》中佐菲本人 M87 的干净音轨：截取后登记集/话、时码、`source_kind=episode`、SHA、响度与峰值；与音乐/旁白重叠的段不得直接当本人音效。
- 若找不到干净原声：用原创数字拟音，登记 `source_kind=original`、工具、参数、CC0 许可；不得写成“原剧 M87 音效”。
- 叫招/喊声必须与画面动作同源核对；不能用其他奥特曼的喊声替代。

## 五、未做

- 未截取任何原剧/电影音轨；未生成任何拟音；未做 Kits 分离；未改共享音频注册；未做试听。
- 未绑定 M87/Z光线/冻霜/受击/胜利等任何事件。
- 未生成或安装声音文件到 `assets/audio/characters/zoffy/`。

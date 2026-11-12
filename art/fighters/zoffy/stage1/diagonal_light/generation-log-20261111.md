# diagonal_light 生成记录（2026-11-11）

authority: root_delegated_by_user。模型 `codex/gpt-image-2`（MCP magpie-image），quality high，请求尺寸 1024×1536，透明背景。唯一身份参考：`art/fighters/zoffy/stage1/idle/frames/raw-01-v4.png`（佐菲待机像素整帧，每帧仅传这一张）。

动作：斜下轻攻击——斜向下切掌，4 帧。纯体术，提示词明确「不带任何光效」（佐菲无元素属性）。

## 自检门

同 back_counter 组（见 `../back_counter/generation-log-20261111.md`）：实收 1024×1536、Alpha、宽高比 0.3–2.6、红像素≥150、站姿帧主体高 1375–1681 px（锚 ±10%）、相邻站姿帧突变超 10% 重掷。自检脚本 `tools/art/zoffy_20261111_selfcheck.py`。

## 重掷历史

无重掷，提示词带「竖版 2:3 画幅」头，4 帧一次全部通过。

## 以此为准（4 帧）

| 文件 | SHA256 | 实收尺寸 | 主体 w×h | 红像素 | 生成 ID |
|---|---|---|---|---|---|
| raw-00.png | 55b55819f64831db7f220a2b5ce741aaccbe0def830839fb4da135f0159424fd | 1024×1536 | 982×1510 | 99770 | image-35600-183 |
| raw-01.png | ff80aff3448e04ffd6d40f7c4f8b89b3dfc32c1f9d567cc17132d4e1f189bf0d | 1024×1536 | 975×1516 | 79981 | image-35600-185 |
| raw-02.png | af8b092679d12b90efb5cc041c9aab1ef2400a180ea57066c119efd7c3ecc599 | 1024×1536 | 994×1519 | 95032 | image-35600-187 |
| raw-03.png | d35d57336b7354276f34bc117cbff9b4d347d20626a9bd65ff87fa092a51d82b | 1024×1536 | 943×1516 | 79996 | image-35600-190 |

相邻帧主体高最大差 9 px（0.6%），小于 10% 门。

## 帧内容

- raw-00：右手举至头侧立掌蓄力。
- raw-01：右掌沿斜下弧线开始下切，重心前移。
- raw-02：发力——切至胸前腰腹高度，掌缘斜朝右下。
- raw-03：收势——右掌回收，回落格斗护架站姿。

未落格、未安装、未提交。

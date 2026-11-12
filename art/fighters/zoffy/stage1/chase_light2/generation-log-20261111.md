# chase_light2 生成记录（2026-11-11）

authority: root_delegated_by_user。模型 `codex/gpt-image-2`（MCP magpie-image），quality high，请求尺寸 1024×1536，透明背景。唯一身份参考：`art/fighters/zoffy/stage1/idle/frames/raw-01-v4.png`（佐菲待机像素整帧，每帧仅传这一张）。

动作：追击二段——上段勾拳（衔接 chase_light1 之后），4 帧。纯体术，提示词明确「不带任何光效」。

## 自检门

同 back_counter 组（见 `../back_counter/generation-log-20261111.md`）：实收 1024×1536、Alpha、宽高比 0.3–2.6、红像素≥150、站姿帧主体高 1375–1681 px（锚 ±10%）、相邻站姿帧突变超 10% 重掷。自检脚本 `tools/art/zoffy_20261111_selfcheck.py`。

## 重掷历史

无重掷，提示词带「竖版 2:3 画幅」头，4 帧一次全部通过。

## 以此为准（4 帧）

| 文件 | SHA256 | 实收尺寸 | 主体 w×h | 红像素 | 生成 ID |
|---|---|---|---|---|---|
| raw-00.png | 9f4ced397dbeff10e9aed96c995a61b8557c76ab6214bd401055c8a1952e566e | 1024×1536 | 910×1513 | 88984 | image-35600-161 |
| raw-01.png | 6e5c5f02a146f71a65b9a13ad1117bff575f38f92895faeed3723e6a8007c4fe | 1024×1536 | 956×1521 | 101753 | image-35600-163 |
| raw-02.png | e03699751ae6adffbfb5188d7024f24f94b3487800ae7318c0dbfdcd1eda179f | 1024×1536 | 968×1529 | 98756 | image-35600-164 |
| raw-03.png | bbb55859112c2d8ab6814d0e5394b7f5e42943f4e9d2c5b0c354744ce9d077db | 1024×1536 | 937×1507 | 98679 | image-35600-168 |

相邻帧主体高最大差 22 px（1.4%），小于 10% 门。

## 帧内容

- raw-00：左脚进身，右拳下沉后拉蓄力。
- raw-01：右拳自下向上扬起启动勾拳，重心升起。
- raw-02：发力——勾拳弧线打至头部高度，前臂竖起。
- raw-03：收势——右拳回落收架，格斗护架站姿。

未落格、未安装、未提交。

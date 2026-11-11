# taunt（抚胸招手·挑衅，6 帧） 生成记录（2026-11-11）

- 模型：codex/gpt-image-2（MCP magpie-image），quality high，size 1024x1536，每次 1 张
- 唯一身份参考：`art/fighters/mother-of-ultra/stage1/idle/frames/pixel-raw-01.png`（SHA256 `0d5b6bc69784eb67542265d4243159f01c9faae332b399601d2cb1d3b3e2de3d`，1024×1536 RGBA），与已验收的 intro/victory/bounce 批次同一配方
- 自检口径：尺寸 1024×1536、RGBA、alpha 0–255、身体（alpha≥128）宽高比 0.35–0.95（被投帧放宽至 0.35–2.6，水平摔投姿势固有宽比）、黄（R>180,G>140,B<90）≥300、蓝（B>150,R<90）≥150；thrown_air 腾空帧脚底不在画布底属正常
- 本帧均无光效、无伤害演出；每帧生成后立即过自检


## 逐帧记录

| 文件 | SHA256（前 16 位，完整值见文末索引） | 尺寸 | 黄色像素 | 蓝色像素 | 身体 bbox (alpha≥128) | 生成 ID |
|---|---|---|---|---|---|---|
| taunt-00-raw-01.png | `3bf73270078d2f72` | 1024×1536 | 1086 | 672 | 9,50-934,1499 | image-83856-4 |
| taunt-01-raw-01.png | `86b1bcb825fcaa73` | 1024×1536 | 966 | 524 | 25,74-934,1498 | image-83856-5 |
| taunt-02-raw-01.png | `5297d8d6e3f63cd2` | 1024×1536 | 1071 | 884 | 14,50-957,1497 | image-83856-6 |
| taunt-03-raw-01.png | `57066a3d837ef1e2` | 1024×1536 | 1117 | 627 | 18,50-934,1496 | image-83856-9 |
| taunt-04-raw-01.png | `99fdf464271172db` | 1024×1536 | 1235 | 479 | 13,63-933,1498 | image-83856-11 |
| taunt-05-raw-01.png | `e3c210f4e9cfe51a` | 1024×1536 | 1158 | 604 | 57,108-933,1496 | image-83856-14 |

## 重掷与备注

- 全组零重掷，一次通过。
- taunt-05（回护架帧）实得姿势与参考待机略有差异，属正常落格前的整帧重绘。

## 完整 SHA256 索引

- `3bf73270078d2f725d6ef1d6fee86a8bce2ee61d29890d554caaeb87b7b32ba5`  taunt/taunt-00-raw-01.png
- `86b1bcb825fcaa73d124d13a70b665397a569be50231d1d4686da36ce747c1fe`  taunt/taunt-01-raw-01.png
- `5297d8d6e3f63cd24f114ea548bc8c412d4c3002d929b2e2c2d8fbf6ec600035`  taunt/taunt-02-raw-01.png
- `57066a3d837ef1e26f9a2efbf0ff240f25b9077b72750385e10b21f08b688344`  taunt/taunt-03-raw-01.png
- `99fdf464271172db360644bd2901222cca2ba50f5542a07067de023dfc61da1a`  taunt/taunt-04-raw-01.png
- `e3c210f4e9cfe51a33d40f62770cc06bec1c536c45d122dd6093bd88f557acd8`  taunt/taunt-05-raw-01.png
- `2b677529b72c75bde1532494dacdaad160404ba42f6d7301764668f65c1d2f7c`  thrown_forward/thrown_forward-00-raw-01.png
- `a08609a0a716d87b1f007d3a936326b684b8e67dba24b339ab9a9a7772019c53`  thrown_forward/thrown_forward-01-raw-01.png
- `fae6046204c41a7093e1dff690cfa4024801622f02d2526ec92802481a162d71`  thrown_forward/thrown_forward-02-raw-01.png
- `5f8982ba12180d7f82ddd54e24997846143980c1d6e668f67cffbe1af5110571`  thrown_forward/thrown_forward-03-raw-01.png
- `ee3058d4c88757b62b244ff401fbf19096fc8cff5f66fd263d140a024cc43033`  thrown_back/thrown_back-00-raw-01.png
- `71e8800e8b9af37fd05fbca340174a34e4d72fd596b310bc4b132bbfbd2c68c2`  thrown_back/thrown_back-01-raw-01.png
- `0542f68f7b55328ae063cd975fa5bd58e48db7fecc3de32b4de94d37a953edb8`  thrown_back/thrown_back-02-raw-01.png
- `efce5f1af79b3a39cf906d96cdf0bade40d54092494a01d7c163fbcae4f8711d`  thrown_back/thrown_back-03-raw-01.png
- `298f05a8976aa7b9615e338c8491e58c5476d27fc1048d5393611f4f30b1b2b5`  thrown_air/thrown_air-00-raw-01.png
- `bde9c4282247b51b123bec7e4260fdc4e20ba060ba292665b62dcde6e4811a75`  thrown_air/thrown_air-01-raw-01.png
- `1549dc0e0532889ed874c99f5107d29012154ea25a73b11dd6ac94a9fe1a82ca`  thrown_air/thrown_air-02-raw-01.png
- `d618def8409c3ffd00c6f34b6215024d815d60b54ad5adc7215c06243c74090d`  thrown_air/thrown_air-03-raw-01.png
- `91c0cc8e26bce6328694663f90d31721e7b9a80bfb2c720a518bebe802f6975b`  thrown_dash/thrown_dash-00-raw-01.png
- `f549e45f81c2755befc23978e5e45fc7fbe5e2b43caa1fdc81f646aa177db5b6`  thrown_dash/thrown_dash-01-raw-01.png
- `8754407d949a48d14e277591c0d2585af27dafec373d604e40a188a48b611301`  thrown_dash/thrown_dash-02-raw-01.png
- `482f67756411d466f7e56f2db0c6d6f2ad86f0484674076384e3a9455fcee840`  thrown_dash/thrown_dash-03-raw-01.png
# 背掀土尘PixelFX v2（待根看图）

v1保全，未作为最终效果接收。本批重新用固定MIT PixelFX `a84159688af3ca37a4be05a0d422b94451b2e24e`实际Painter调用烘焙完整帧，主候选`bake-a`、独立重复`bake-b`，没有读取旧PNG或改色放大旧帧。

| 效果 | 相数 | 自身完整格 / 根 | 实际最大实体范围 | atlas SHA-256 |
| --- | --- | --- | --- | --- |
| capture_contact | 5 | 40×36 / [20,18] | 11×4，最多16可见像素 | f86399ffc42e86a273829007e716a643ef80b2268a795b888167143dbb0a45a7 |
| release_dust | 7 | 96×64 / [72,46] | 52×18，5级颜色 | 153915d29366c702cabd9d47002cd4cf00058516cfac44394d1bbb546d56a186 |
| landing_dust | 8 | 128×64 / [64,48] | 88×27，5–6级颜色 | 2400e29315c52ec3e63e5c7bb90cb3bb7678a80fa594fde48b36ec5d9453ec3b |

capture继续短促轻接触；release改为三层向后拖散土尘；landing改为低地两翼体积尘，范围从压缩24宽到56→80→88，再分散消退，首两相含中央短接触闪和石粒。上方中央留空，体积层推荐在受方后面，尚未挂真实角色，不宣称不会遮挡的实机验收已通过。没有外圆、Q光环、魔法波或地震伤害判定。

全部PNG真RGBA、Alpha仅0/255、透明RGB零、实体不触格边、末相空白；a/b全部PNG和RGBA逐字节一致。capture候选每相1表现tick，release/landing每相2表现tick，后两套分别约0.23/0.27秒；仅候选时长，不影响真实60tick模拟。实际成套图已离线打开查看，但根尚未签最终效果。

三张完整深浅页均在`review-v1/`：`gomora_back_lift_capture_contact-all-phases-dark-light.jpg`、`gomora_back_lift_release_dust-all-phases-dark-light.jpg`、`gomora_back_lift_landing_dust-all-phases-dark-light.jpg`。页面标明整格尺寸/最近邻显示倍数/自身根；无剪裁局部图。

各分支`bundle.json`绑定生成源、冻结合同、参数、上游子集SHA与MIT许可/NOTICE。`parameters.json`保存全部seed、palette、宽高/fade曲线与相时长；检查见`review-v1/fx-audit.json`、`v2-envelope-measurement.json`。来源为PixelFX，Copyright (c) 2026 Patch、Hugo Duprez；分发需保留许可证声明。

触发保持：capture只新special3真实throw捕获hit；release只成功受方`throw_released`从false变true的真实脱手一次，不伪称已有同名事件；landing只该招唯一`throw_slam`。独立根尚不等于本人/受方世界挂点。未写assets/content/presentation，未Godot、POST或Git。

# ultraman-zero · idle 返工记录（2026-11-13）

- 范围：`idle` clip，6 帧；本轮含重生成、落格、安装与静态门复算。
- 权威：`root_delegated_by_user`（根本机复算与目视）；不是 user_approved，不是用户亲审，不是听审；实机只做本机画面截图核验。

## 1. 上一批 raw 拒收

- 拒收 6 帧；近脚中心横向跨 12.5 px、远脚 20.4 px、冠顶行跨 34 px、头横向重心跨 11.0 px。六帧为独立生成，脚位与头位不构成静态呼吸；不满足双脚固定/头纵幅≤4px。
- 两角色共 11 帧的 SHA/尺寸清单：`reports/review/2026-11-13/seven-character-rework/rejected-idle-raws-20261112.json`；联系表：`rejected-idle-raws-20261112.png`。raw 已按已核 SHA 删除，不备份。

## 2. 新基线

- 新生成 raw：`art/fighters/ultraman-zero/stage1/rework-20261112/raw/idle-base-00.png`，1254×1254，SHA `006df823481ae280276c017ca845c2359a2d1be2aa6947333a80da573e77ef3b`；harden_alpha(≥128) 后实心轮廓高 925 px、宽 633 px。
- 唯一参考：`art/fighters/ultraman-zero/stage1/idle/frames/identity-idle-pixel.png`（SHA 见 identity_ready.json）。
- 生成参数：`codex/gpt-image-2`、quality high、background transparent；提示词要求与参考图同一站姿、身体直立、双脚前后分开、双拳胸前护架、完整右侧视、真透明、无特效。
- 生成原始图另存 `raw/idle-base-00.png`；未被后续帧复用为参考。
- 落格基线帧：`art/fighters/ultraman-zero/stage1/rework-20261112/cells/idle/idle-00-cell.png`，SHA `3e6a45b3cfb940335f97ac461f6eedb74c7c195077bf2eb8ce40c35bba999f33`；六帧由它整身位移派生。

## 3. 比例与落格

- 生产站高目标 172 px（2026-11-11 官方身高重标定后的装机基线），本批 raw 实心高 925 px。
- 本批统一 scale = 172/925 = 0.185946；六帧共用，未逐帧重标定。
- 注：identity_ready.json 的 `unique_scale` 对应旧 raw 分辨率，不适用于本批新 raw；已在 identity_ready 增补 `rework_batch_scale_2026_11_13` 登记，不改历史值。
- 落格：stage_cells.py，cell 256、anchor [128,248]、baseline 248、`--palette-json` 冻结 32 色板；未使用图鉴旧色板。

## 4. 六帧呼吸循环

方法：以落格后的 idle-00 为唯一基线，整身向下平移 dy 像素，底部第 232–255 行（脚踝/鞋）固定回贴；一次下沉再回升。非逐帧独立生成。

| 帧 | dy | SHA256 | bbox | 高度 | 头高 | 色数 | 连通 |
|---:|---:|---|---|---:|---:|---:|---:|
| idle-00-cell | 0 | `3e6a45b3cfb94033…` | [62, 76, 179, 247] | 172 | 36 | 28 | 1 |
| idle-01-cell | 1 | `4044a7023dab476e…` | [62, 77, 179, 247] | 171 | 36 | 28 | 1 |
| idle-02-cell | 2 | `31d8512e1ccc60ba…` | [62, 78, 179, 247] | 170 | 36 | 28 | 1 |
| idle-03-cell | 3 | `45ea76b8881c9435…` | [62, 79, 179, 247] | 169 | 36 | 28 | 1 |
| idle-04-cell | 2 | `31d8512e1ccc60ba…` | [62, 78, 179, 247] | 170 | 36 | 28 | 1 |
| idle-05-cell | 1 | `4044a7023dab476e…` | [62, 77, 179, 247] | 171 | 36 | 28 | 1 |

## 5. 静态门

- 双脚固定：True；头纵幅 ≤4 px：True（实测 3）；相邻头位 ≤2 px：True；横漂 ≤2 px：True（实测 0.13）。
- 站高偏差 ≤8%：True（实测 max 1.7%）；色数/单连通/二值 Alpha：全部通过。
- 相邻剪影 XOR/Union：[0.0499, 0.0498, 0.0498, 0.0498, 0.0498, 0.0499]；目标 ≥0.10 未达，按规格登记为 gap，不用改脚位或整人缩放凑门。

## 6. 安装与验证

- 已安装：`assets/fighters/ultraman-zero/animations/idle/atlas.png` 为 1536×256 六帧；manifest idle clip cell 256、anchor [128,248]、ticks [10]*6、loop true。
- 非 idle clip 语义未变（逐 clip 对比 HEAD 仅 idle 变化）；`tools/verify.py --only logic_2d` 通过，全量回归 59 项 PASS（`tools/verify.py --keep-going`）。
- `content/fighters/ultraman-zero/definition.json` 的 presentation cell/anchor 随安装更新。

## 7. 目视与未做

- 根本机实看：六帧联系表 `reports/review/2026-11-13/seven-character-rework/ultraman-zero-idle-loop-x2.png`、脚踝接缝对比 `ultraman-zero-idle-ankle-compare-x6.png`；身份、朝向、站姿与装机 idle 一致，未见裁切、断肢、断缝或多余部件。
- 主游戏实机（root_delegated_by_user）：`reports/review/2026-11-13/seven-character-rework/ingame/ultraman-zero-mirror-1280x720.png`、`ultraman-zero-mirror-1920x1080.png`，双方同角色镜像，左右两个朝向同屏；窗口与截图同为 1280×720 / 1920×1080，人物完整、接地、未被 HUD 遮挡。
- 六帧训练待机：`idle-training-720-t150..t200.png` 与联系表 `idle-training-720-sheet.png`，赛罗 1P、盖亚陪练 2P 站立，覆盖六个待机帧。
- 未做：录屏、听审、用户亲审；不把本报告写成听感通过或用户亲审。


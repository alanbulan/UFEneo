# 奥父专属运行时特效家族（2026-11-12）

范围：只替换 `father-of-ultra` 招式里复用的共享/他角色特效，不动任何人物整帧 PNG、不改共享登记文件。
所有形状由 `bake.mjs` 的原创绘制函数离线烘焙（PixelFX，MIT），没有调用 MCP 生图，也没有读取赛罗/泰罗/共享特效图集。

## 接线结果

| 招式 | 原共享/他角色引用 | 新特效 |
| --- | --- | --- |
| `pulse` / `low_pulse` / `air_pulse` | `pulse` | `father_fx_pulse_flight`，命中映射 `father_fx_pulse_hit` |
| `special` / `special2` / `air_special` | `beam_loop` + `beam_hit` | `father_fx_beam`，命中 `father_fx_beam_hit` |
| `motion_236` / `ranged_forward` | `special_arrow` | `father_fx_arrow_flight`，命中映射 `father_fx_arrow_hit` |
| `motion_623` | `special_spiral` | `father_fx_spiral`，命中映射 `father_fx_spiral_hit` |
| `motion_22` | `special_barrier` 挂件 | `father_fx_barrier`（挂件颜色改为原色 `[1,1,1,1]`，保住红银） |
| `motion_214` | `special_rings` + `ultraman_catch_ring_form_front/back` | `father_fx_rings`（命中映射 `father_fx_rings_hit`）+ `father_fx_catch_front/back` |

通用接触反馈 `impact_light` / `impact_heavy` / `impact_guard` 保持共享库不动；5 个投射招都补了 `feedback.projectile_impacts`，命中改走本角色命中段。

## 图集、SHA 与硬门

逐帧指标（alpha 取值、最大 4 连通块、主体外 `alpha>=16` / `alpha>=200`、bbox、逐帧相位变化率）在 `build-report.json` 的 `effects[*].frame_gate` / `phase_change_ratio` 中。全部图集满足：

- 真透明 RGBA，Alpha 只有 `0/255`（硬 Alpha）。
- 主体＝`alpha>=200` 最大 4 连通块；**主体外 `alpha>=16` 与 `alpha>=200` 全部为 0**（门限分别是 ≤100 与 =0）。
- 每段相邻帧可见像素变化率最低 22.7%（Q 蓄气循环段），均非复制凑帧；亮芯、外焰/披风锯齿、颗粒状短焰随相位推进。

Q 蓄气三态（2026-11-12 根审拒收后重做）为以身体为中心的椭圆环状红银火焰：径向分层火身（橙白内缘→朱红→深红）、外缘 11 处尖峰火舌、内缘短火舌、橙白亮芯与 7 条宽短焰、5 条 S 形上升火星。start 由小到大（env 0.16→1.0，9 帧），charge 24 帧持续起伏循环，stop 收束（env 1.0→0.12，9 帧）。原「红色竖条笼/门框」造型已全部移除，无矩形或等宽竖条结构。

| effect id | atlas | 尺寸 | 帧 | 色数 | SHA256 |
| --- | --- | --- | --- | --- | --- |
| `father_fx_pulse_flight` | `assets/effects/father-of-ultra/fx-family-20261112-v1/pulse_flight/atlas.png` | 256×64 | 4 | 6 | `e75af35284d053c2a14f94668cab41a88c03d39a1ca7ea6e0dabc6ed9423b6a3` |
| `father_fx_pulse_hit` | `assets/effects/father-of-ultra/fx-family-20261112-v1/pulse_hit/atlas.png` | 384×96 | 4 | 5 | `50e629b3a26b720016c80864ca79313677650cd3eea77e92fc4f43993c8ccb76` |
| `father_fx_beam` | `assets/effects/father-of-ultra/fx-family-20261112-v1/beam/atlas.png` | 1680×96 | 4 | 6 | `236531daff61a6c2e30ff1d5dab7ab5367460bf914bdeac2a981731c8f93ea20` |
| `father_fx_beam_hit` | `assets/effects/father-of-ultra/fx-family-20261112-v1/beam_hit/atlas.png` | 416×104 | 4 | 5 | `4e446c92d818d88f5f2e1748c034218f409755e69b1d5606e878e3ae8654a036` |
| `father_fx_arrow_flight` | `assets/effects/father-of-ultra/fx-family-20261112-v1/arrow_flight/atlas.png` | 256×64 | 4 | 6 | `071f23f1105d14d89b84948dd3b178e08783eda6e31e666f09e054f7b20d5e16` |
| `father_fx_arrow_hit` | `assets/effects/father-of-ultra/fx-family-20261112-v1/arrow_hit/atlas.png` | 384×96 | 4 | 4 | `f66b6d61b24d8f3a4f4d6cdae217038faf777e8a02996b02722454871bee7297` |
| `father_fx_spiral` | `assets/effects/father-of-ultra/fx-family-20261112-v1/spiral/atlas.png` | 384×96 | 4 | 5 | `1bb9e75b44a1c7f2c59f239cd63d82d98460c3da9f3e9efe5b0b448860eb811b` |
| `father_fx_spiral_hit` | `assets/effects/father-of-ultra/fx-family-20261112-v1/spiral_hit/atlas.png` | 384×96 | 4 | 5 | `d673bcdc67e1a5359f161f0920e26b26d71ba885120af453b6be52f2a1f9305b` |
| `father_fx_rings` | `assets/effects/father-of-ultra/fx-family-20261112-v1/rings/atlas.png` | 512×128 | 4 | 5 | `35aecc67b2500437c473570f40d89b8b03b688da2f2c1afe47d8bd8d7c532eaa` |
| `father_fx_rings_hit` | `assets/effects/father-of-ultra/fx-family-20261112-v1/rings_hit/atlas.png` | 384×96 | 4 | 5 | `0df4fd85274b622d2c9caef12d26d146c2355b4044dc0c3bfa95b15ea22f01f4` |
| `father_fx_barrier` | `assets/effects/father-of-ultra/fx-family-20261112-v1/barrier/atlas.png` | 640×160 | 4 | 5 | `912ff2d8ecff8256be88fd9c7bb4515a719744e1b813805564a492efdfdff6fc` |
| `father_fx_catch_back` | `assets/effects/father-of-ultra/fx-family-20261112-v1/catch_back/atlas.png` | 512×128 | 4 | 4 | `631a0ae83baace1d92b0d816a6bdea60eb35132f0a2d1135637a498c0c16fdb7` |
| `father_fx_catch_front` | `assets/effects/father-of-ultra/fx-family-20261112-v1/catch_front/atlas.png` | 512×128 | 4 | 4 | `c831006bf32af5d80670655996bd9c94bc810b27a1b9ed783037db4aa7f45f3c` |
| `father_fx_q_charge_start` | `assets/effects/father-of-ultra/fx-family-20261112-v1/q_charge_start/atlas.png` | 2304×512 | 9 | 8 | `1ac698681d2d514e962bcf602dd6b0cacb5c71fcc31256d87edeffe19a2f73a8` |
| `father_fx_q_charge` | `assets/effects/father-of-ultra/fx-family-20261112-v1/q_charge/atlas.png` | 2304×1024 | 24 | 8 | `181824066fe6e92ce7093e7fc633ffd2e14e0a05d9db60a6a9212a5187c8db4c` |
| `father_fx_q_charge_stop` | `assets/effects/father-of-ultra/fx-family-20261112-v1/q_charge_stop/atlas.png` | 2304×512 | 9 | 8 | `3b1b26697ee58c6cf80c05bf48b69c5d27f3a741977c1a0c49e437649264353a` |

每段另有 `effect.json`（完整 phase3 clip 对象）与 `provenance.json`（逐帧数值、形状来源、上游、许可）。全套色板按本人红银（深红→朱红→暖白）与金色角部光束；载入图集为硬边像素整帧，不含人物。

## 提案（等根会话合并，未改共享登记）

- `phase3_entries.json`：16 条完整 clip 对象，直接并入 `content/presentation/phase3_projectiles.json`。
- `charge_policy.json`：`father-of-ultra` 三态 placements（9/24/9，`behind_fighter: true`，`charge` 循环）；
  另需把三个 `father_fx_q_charge*` 加入 `charge_only_effects`。
- **已知接线缺口**：`father-of-ultra` 的 `charge_start/charge/charge_stop` 状态帧目前没有 `attachments`；
  `UfeChargeEffectPolicy.filter` 只替换已存在的受限附件，所以只合并 placements 不会显示蓄气图。
  根会话需要在三个蓄气状态帧各挂一个 `charge_aura` 占位附件（与 zoffy/gaia 同口径）才能让本家族三态生效；
  本任务只允许改 `moves/*.json`，未改 `state_frames.json`。

## 来源与许可

- 形状来源：`bake.mjs` 原创绘制函数，`shape_source` 不是任何他人图集。
- 上游：PixelFX `https://github.com/patch-gg/pixelfx/tree/a84159688af3ca37a4be05a0d422b94451b2e24e`，MIT。
- 许可文件：`third_party/pixelfx/LICENSE`，SHA256 `0a77565a50c3462831244452f129c38d2adc4fd07897cbeba8adc943f958604e`；
  安装副本 `assets/effects/father-of-ultra/fx-family-20261112-v1/PIXELFX-LICENSE.txt`。
- 所有 effect 条目 `source_kind=art_source=pixelfx_code_baked`，`user_approved=false`，待指挥目视终审。

## 复现

```bash
# install.py 只需 Python 3.12+ 标准库与 node；工作树没有 .venv，用主仓库的 .venv 或任意 python3。
/Users/wurulan/Developer/Projects/Game/ultraman-neo/.venv/bin/python tools/rebuild/father-of-ultra/fx-family-20261112/install.py
# gate_check.py 需要项目 .venv 的 numpy/Pillow。
/Users/wurulan/Developer/Projects/Game/ultraman-neo/.venv/bin/python tools/rebuild/father-of-ultra/fx-family-20261112/gate_check.py
/Users/wurulan/Developer/Projects/Game/ultraman-neo/.venv/bin/python tools/godot_lock.py -- /Users/wurulan/Developer/Projects/Game/ultraman-neo/.venv/bin/python tools/verify.py --skip-import --only roster_data_integrity phase3_specials phase3_air phase3_supers
```

`install.py` 每次重烘到 `reports/fx_father_family` 并重算 SHA；`build-report.json` 是本次实跑结果。
`contact_sheet.py` 与 `gate_check.py` 是审阅辅助，只读 staging。

## 验证与边界

- 已跑：`roster_data_integrity`、`phase3_specials`、`phase3_air`、`phase3_supers` 全 PASS。
- 新 id 在根会话合并前尚未登记，`presentation` 会静默跳过，这与任务边界一致；没有改共享登记绕过。
- 未做 720/1080 双朝向实机画面复检，无录屏、无听审；不冒充用户亲审。
- `content/fighters/father-of-ultra/MOVES.md` 仍写旧共享 id（本任务只允许改 `moves/*.json`），合并后需随文档一起更新。
- `motion_22` 的挂件颜色从蓝色 `[0.6,0.9,1,1]` 改为原色 `[1,1,1,1]`，否则新增红银屏障会被染蓝。

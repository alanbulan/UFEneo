# 杰斯提斯专属运行时特效家族（2026-11-12）

## 范围

只新增/接线杰斯提斯（`ultraman-justice`）的弹体、光线、光箭与 Q 蓄气特效，
替换原先借用的共享 id；不改人物整帧 PNG、不改人物动作数据、不改共享特效登记。
通用接触反馈 `impact_light` / `impact_heavy` / `impact_guard` 保持原条目不动。

招式接线：

| 招式 | 原引用 | 现引用 | 命中映射 |
| --- | --- | --- | --- |
| `pulse` / `low_pulse` / `air_pulse` | `pulse` | `justice_fx_pulse_flight` | `justice_fx_pulse_hit` |
| `special` / `special2` / `air_special` | `beam_loop`、`beam_hit` | `justice_fx_beam`、`justice_fx_beam_hit` | `justice_fx_beam` → `justice_fx_beam_hit` |
| `special3` | `beam_loop` | `justice_fx_beam` | `justice_fx_beam` → `justice_fx_beam_hit` |
| `motion_214` | `special_arrow` | `justice_fx_arrow_flight` | `justice_fx_arrow_flight` → `justice_fx_arrow_hit` |

`special3` 与 `motion_214` 的 `feedback.spark` 仍保留通用 `impact_heavy`，只把
`projectile_impacts` 指向本人命中特效；人物招式的非投射接触反馈不另造一套。
`motion_214` 另补 `block_color` 保留原青绿防御火花染色，`feedback.color` 转白只
作用于投射命中，避免给本人固定色板的命中段套旧青色。
`air_special` 的 `adaptation` 同步改为“人物帧不含光束，束体由运行时承载”，
去掉原先与运行时 shot 矛盾的“已烘焙贴手光束”表述。

## 产出

全部为 4 帧技能段（Q 蓄气 9/24/9 帧），原生 1:1，硬 Alpha，逐帧单连通。
尺寸、逐帧 Alpha/连通块/主体外数值见 [build-report.json](build-report.json)。

| id | 图集 | 帧 | 尺寸 | 色数 | SHA256 |
| --- | --- | --- | --- | --- | --- |
| `justice_fx_pulse_flight` | `assets/effects/ultraman-justice/fx-family-20261112-v1/pulse_flight/atlas.png` | 4 | 384×64 | 8 | `e4135a61f5a19e47e4783ee2833bc0204333356fb3a26a6ed5bc14c662d42729` |
| `justice_fx_pulse_hit` | `.../pulse_hit/atlas.png` | 4 | 512×128 | 7 | `8d79d044c984abebe8a3edcfd42d7dde04fe9a8f95ba7cb3e481c6eb3fa58e41` |
| `justice_fx_beam` | `.../beam/atlas.png` | 4 | 768×112 | 6 | `06a5823c5e1ae4615be7d23e9d437840fc98dbd6a47c8d4425d00d74ed0d7c12` |
| `justice_fx_beam_hit` | `.../beam_hit/atlas.png` | 4 | 512×128 | 7 | `02b818d9009f410ea92e36b98821bfa874adc8e7791370f24059058b66087a22` |
| `justice_fx_arrow_flight` | `.../arrow_flight/atlas.png` | 4 | 448×64 | 7 | `035feb670e235df2cf70d12aa9582d6bc43ed37aa8ae3d0d59aba3c4d6d9d340` |
| `justice_fx_arrow_hit` | `.../arrow_hit/atlas.png` | 4 | 512×128 | 7 | `30d1e57d935d1b7bbf7f541e8ae03af050987868660a91098e99c7ee16cbd71f` |
| `justice_fx_q_charge_start` | `.../q_charge_start/atlas.png` | 9 | 2304×512 | 8 | `6969f44f98eac9d1427e950fdec9b067cf28ac6d7c365995fbb53e8a5d4316d7` |
| `justice_fx_q_charge` | `.../q_charge/atlas.png` | 24 | 2304×1024 | 8 | `c447a091ddebf2a6fac61207bc5d4aebc14b85bd5eff2bf25119c696848a2e2e` |
| `justice_fx_q_charge_stop` | `.../q_charge_stop/atlas.png` | 9 | 2304×512 | 8 | `d948200a38841f485f493f019fe7a342d84b68356b695da79a645f16ea778ffa` |

每段另有 `effect.json`（完整 clip 对象）与 `provenance.json`（绘制来源、帧 SHA、
图集 SHA）。`beam` 为 192×112 可平铺横段，白芯始终连续、外焰带推进缺口与亮结；
飞行段与命中段分开，命中为白热核＋放射刃＋刃间蛛网弧。

## 硬门结果

落盘图集实测（不是请求尺寸）：

- 真透明 RGBA；每帧 Alpha 仅 `{0,255}`。
- 主体＝Alpha≥200 最大 4 连通块；每帧主体数恰为 1。
- 主体外 Alpha≥16 像素数：每帧 0；主体外 Alpha≥200：每帧 0。
- 帧内相位变化：技能段逐帧变化 ≥ 主体像素 1%，蓄气段 ≥ 0.6%，无复制帧。
- 烘焙时被去掉的游离碎点（主体外预过滤像素）逐帧记录在 `build-report.json`；
  图集本身已无主体外像素。

逐帧数值、`frame_boxes`、色数、`rects`、`anchor`、`ticks`、`loop` 均在
`build-report.json`；9 段的完整 phase3 条目在 [phase3_entries.json](phase3_entries.json)。

## 共享登记提案（本任务不改共享文件）

- [phase3_entries.json](phase3_entries.json)：9 个新 id 的完整 clip 对象，合并进
  `content/presentation/phase3_projectiles.json`。
- [charge_policy.json](charge_policy.json)：`ultraman-justice` 的
  `charge_start` / `charge` / `charge_stop` 落点与三个 `charge_only_effects`，
  合并进 `content/presentation/charge_overlay_policy.json`。

本批前后共享文件 SHA256 未变（见 build-report 的 `shared_registry_policy`）：

- `phase3_projectiles.json`：`b5a78402…6c608`
- `charge_overlay_policy.json`：`f3e350e1…1cc871`

**合并前**：新 id 在运行时查不到，弹体、命中与蓄气会被静默跳过；
`tests/effect_registration.gd` 也会按设计报未登记，这是提案未合并的预期状态。

**Q 蓄气还有一个激活依赖**：杰斯提斯 `state_frames.json` 与动画 manifest 的
三个 Q 状态当前都没有 `attachments`，而 `UfeChargeEffectPolicy.filter` 只替换已有
挂件、不会凭空追加。合并 placements 后仍需根会话把通用 `charge_aura` 挂件补进
这三个状态帧（不在本任务允许改动范围），否则 Q 三态仍不显示。

## 来源与许可

- 形状：本批 [bake.mjs](bake.mjs) 绘制函数原创，未读取任何他人特效图集轮廓。
- 烘焙：PixelFX（MIT），upstream commit
  `a84159688af3ca37a4be05a0d422b94451b2e24e`，许可文件
  `assets/effects/ultraman-justice/PIXELFX-LICENSE.txt`（SHA256
  `0a77565a50c3462831244452f129c38d2adc4fd07897cbeba8adc943f958604e`）。
- 未使用 PixelFX 的骨架人物/stock dummy；未引入运行时 JS。
- 本轮特效走离线代码烘焙，没有调用 MCP 生图；落盘后按实际 PNG 复核尺寸与 Alpha。

## 复现

```sh
# 只烘焙与检查，不写 assets/content
.venv/bin/python tools/rebuild/ultraman-justice/fx-family-20261112/install.py --dry-run

# 安装图集、写提案、接线 8 个招式 JSON
.venv/bin/python tools/rebuild/ultraman-justice/fx-family-20261112/install.py
```

`install.py` 每次重新烘焙到 `reports/fx_justice_family/`（该目录不提交），
复制到 `assets/effects/ultraman-justice/fx-family-20261112-v1/`，再以落盘图集
实测生成条目与报告。烘焙是确定性的；图集 SHA 可直接复核。

## 验证

已通过（经 `tools/godot_lock.py` 串行）：

```sh
.venv/bin/python tools/godot_lock.py -- \
  .venv/bin/python tools/verify.py --skip-import \
  --only roster_data_integrity phase3_specials phase3_air phase3_supers
```

四个检查均 PASS。未跑 `effect_registration`：它要求提案先合并，属根会话合并后的门。

## 未做 / 已知

- 未改任何人物整帧 PNG、动画 manifest、roster/selection/battle_forms/audio/其它角色。
- 无录屏；未做 720/1080、双朝向与实机目视终审，不冒称用户亲审。
- Q 蓄气在合并登记并补 attachments 前不可见（见上节）。
- `special3` / `motion_214` 的非投射接触仍用通用 `impact_heavy`；其投射命中已指向
  本人命中特效。若将来要统一接触反馈，需另立任务。

# 赛罗奥特曼招式表（2026-11-12 已安装状态）

本文件只记当前实际装机内容。赛罗默认形态 47 招全部有 `content/fighters/ultraman-zero/moves/*.json`、`assets/fighters/ultraman-zero/animations/` 图集与 `definition.json`，不再有“美术已交付未安装”的旧状态。

## 身份锚与落格

- 身份锚：待机像素整帧 `art/fighters/ultraman-zero/stage1/idle/frames/pixel-raw-02-official-side-anchor.png`（用户 2026-11-09 认可）。
- 通用落格：256×256、根点 `[128,248]`、接地行 247、腾空行 225，站高 172；`stage1/cells/cells.json` 的 `scale` 为 0.158767。
- 空中必杀 `air_special` 用 288×288 格、根点仍 `[128,248]`，帧内腾空行 225；安装时逐 clip 取自身格宽与根点，未回落到 `cells.json` 顶层旧值。
- 人物帧只画身体，光束、头镖、拖尾、接刃闪光、Q 蓄气全部由运行时特效层承载。逐帧手/臂/腿都有位移，不复制同姿势凑帧。

## 三格能量终结与空中必杀

| 槽 | move | 技能 | 帧数 | 起手/持续/收势 | 运行时特效 | 发射点（根点局部） | 伤害/能量 |
|---|---|---|---:|---|---|---|---:|
| 1 格 | `special` | 赛罗集束射线（Wide Zero Shot） | 72 | 24/32/16 | `zero_fx_wide_beam`，命中 `zero_fx_wide_hit` | `[18,138]`，贴右前臂前缘 | 180 / 1000 |
| 2 格 | `special2` | 艾梅利姆切割（Emerium Slash） | 80 | 32/32/16 | `zero_fx_emerium_beam`，命中 `zero_fx_emerium_hit` | `[22,158]`，贴额灯右缘 | 300 / 2000 |
| 3 格 | `special3` | 赛罗头镖（Zero Slugger） | 96 | 32/48/16 | `zero_fx_slugger_flight` + `zero_fx_slugger_trail`，回收 `zero_fx_slugger_catch`，命中 `zero_fx_slugger_hit` | 双镖 `[59,132]` / `[33,133]`，外飞 30 tick 后 24 tick 回收，回收锚逐 tick 跟双手 | 480 / 3000 |
| 空中 | `air_special` | 空中集束射线（游戏改编） | 24 | 10/1/13 | `zero_fx_wide_beam`，命中 `zero_fx_wide_hit` | `[126,162]`，贴 air_special-03 手部中心 | 60 / 1000 |

- 三招动作、发射部位、颜色、判定与特效均不同，不是同一束改粗细/颜色凑槽。1 格宽青蓝束；2 格青绿细束带新月刃波；3 格双实体飞刃（`weapon_id` 分别为 `zero_slugger_a` / `zero_slugger_b`，带 `return_ticks` 回收与 `max_hits`）。
- `air_special` 是游戏改编，原剧无空中发射依据，不冒称原剧。
- 所有技能帧的 `kind` 均为 `projectile`，由运行时弹体结算；人物帧内没有烘焙光束或刀刃。

## 赛罗专属特效家族（PixelFX 离线烘焙）

来源：`tools/rebuild/ultraman-zero/fx-family-pixelfx-20261112-v1/bake.mjs` + `install.py`；上游 PixelFX 固定 commit `a8415968`，MIT，素材在 `assets/effects/ultraman-zero/fx-family-pixelfx-20261112-v1/`。

- 技能段：`zero_fx_wide_beam` / `zero_fx_wide_hit`、`zero_fx_emerium_beam` / `zero_fx_emerium_hit`、`zero_fx_slugger_flight` / `_trail` / `_hit` / `_catch`。硬 Alpha、≤8 色板，亮芯 + 外焰/刃波 + 颗粒相位。
- Q 蓄气：`zero_fx_q_charge_start`（9 帧）/ `zero_fx_q_charge`（24 帧）/ `zero_fx_q_charge_stop`（9 帧），已在 `content/presentation/charge_overlay_policy.json` 登记；只在真实 Q 起势/保持/收势出现，招式期间不出现周身蓄气圈。
- 基础光弹 `pulse` / `low_pulse` / `air_pulse` / `ranged_forward` 仍用运行时通用 `pulse` 弹体（与已装机角色同一通用池），不是他人角色专属家族。

## 方向快捷与投技

| 输入 | move | 名称 | 帧数 | 起手/持续/收势 | 说明 |
|---|---|---|---:|---|---|
| 214I | `motion_214` | 赛罗突进拳 | 40 | 13/16/11 | 游戏编排：前踏送肩、双臂前推 |
| 236□ | `motion_236` | 赛罗连步掌 | 40 | 13/16/11 | 游戏编排：垫步后双掌前推 |
| 623△ | `motion_623` | 赛罗升膝 | 40 | 13/16/11 | 游戏编排：屈膝上顶截击 |
| 22○ | `motion_22` | 赛罗能量壁 | 40 | 13/16/11 | 游戏改编：双臂交叠能量壁反震 |
| 41236× | `motion_41236` | 赛罗过顶摔 | 40 | 4/4/32 | 游戏编排：扣臂、背起、过顶摔 |

以上名称均为游戏编排/改编，不冒称原剧招式；数值沿用已装机同体型模板。

## 全部招式清单

| move | 名称 | 类型 | 帧 | 起手/持续/收势 | 伤害 | 能量 |
|---|---|---|---:|---|---:|---:|
| light1 | 前手短直拳 | strike | 20 | 5/3/12 | 65 | 0 |
| light2 | 后手直拳 | strike | 20 | 5/3/12 | 65 | 0 |
| light3 | 进身上勾拳 | strike | 20 | 5/3/12 | 65 | 0 |
| heavy | 踏步重拳 | strike | 28 | 9/4/15 | 100 | 0 |
| launcher | 升龙上勾拳 | strike | 23 | 8/3/12 | 75 | 0 |
| spin_heavy | 回身横扫肘 | strike | 28 | 9/4/15 | 100 | 0 |
| crush | 双拳破甲砸击 | strike | 33 | 10/8/15 | 130 | 0 |
| tackle | 沉肩突进 | strike | 26 | 7/6/13 | 100 | 0 |
| sweep | 低扫脚跟 | strike | 28 | 6/12/10 | 65 | 0 |
| slide | 低身滑铲 | strike | 26 | 4/9/13 | 65 | 0 |
| crouch_light | 蹲姿下段直拳 | strike | 18 | 6/4/8 | 65 | 0 |
| crouch_light2 | 蹲姿二段直拳 | strike | 18 | 6/4/8 | 65 | 0 |
| vertical_light | 垂直跳短拳 | strike | 18 | 6/4/8 | 65 | 0 |
| vertical_heavy | 垂直跳下砸拳 | strike | 21 | 6/6/9 | 90 | 0 |
| diagonal_light | 斜跳膝撞 | strike | 20 | 6/5/9 | 65 | 0 |
| diagonal_heavy | 斜跳飞踢 | strike | 23 | 8/3/12 | 90 | 0 |
| air_crush | 空中双拳下砸 | strike | 20 | 4/3/13 | 110 | 0 |
| dive | 俯冲脚跟踢 | strike | 19 | 4/9/6 | 65 | 0 |
| chase_light1 | 追击前刺拳 | strike | 20 | 5/3/12 | 65 | 0 |
| chase_light2 | 追击横肘 | strike | 16 | 4/4/8 | 65 | 0 |
| chase_end | 追击双掌砸地 | strike | 16 | 4/12/0 | 65 | 0 |
| dash_light | 冲刺直拳 | strike | 20 | 4/4/12 | 65 | 0 |
| dash_heavy | 冲刺飞踢 | strike | 12 | 4/3/5 | 65 | 0 |
| back_counter | 后闪反击 | strike | 22 | 4/3/15 | 65 | 0 |
| dodge_counter | 闪避反击 | strike | 20 | 4/4/12 | 65 | 0 |
| wake_low | 起身下段拳 | strike | 22 | 6/5/11 | 65 | 0 |
| wake_mid | 起身中段拳 | strike | 24 | 9/5/10 | 65 | 0 |
| guard_counter | 防御反击 | strike | 24 | 8/5/11 | 65 | 1000 |
| burst | 爆气 | strike | 18 | 5/8/5 | 30 | 2000 |
| pulse | 光弹 | projectile | 27 | 7/4/16 | 65 | 0 |
| low_pulse | 低姿光弹 | projectile | 23 | 7/4/12 | 65 | 0 |
| air_pulse | 空中斜下光弹 | projectile | 20 | 6/4/10 | 65 | 0 |
| ranged_forward | 专属远程 | projectile | 32 | 14/4/14 | 95 | 0 |
| special | 赛罗集束射线 | projectile | 72 | 24/32/16 | 180 | 1000 |
| special2 | 艾梅利姆切割 | projectile | 80 | 32/32/16 | 300 | 2000 |
| special3 | 赛罗头镖 | projectile | 96 | 32/48/16 | 480 | 3000 |
| air_special | 空中集束射线（游戏改编） | projectile | 24 | 10/1/13 | 60 | 1000 |
| throw_forward | 前投·扣臂过肩摔 | throw | 32 | 2/4/26 | 65 | 0 |
| throw_back | 后投·抱腰回身摔 | throw | 32 | 2/4/26 | 65 | 0 |
| air_throw | 空投·空中揽肩翻摔 | throw | 24 | 2/4/18 | 65 | 0 |
| dash_throw | 冲步抱身摔 | throw | 24 | 2/4/18 | 65 | 0 |
| taunt | 挑衅 | gesture | 30 | 0/0/30 | 0 | 0 |

## 输入与状态

- 三格能量终结：`P` 与 `□+△` 为同一终结点，运行时按能量格选 `special` / `special2` / `special3`。
- `E` 切换已开放形态（当前仅默认形态可玩）；`Q` 蓄能，`N` 闪避，`I` 方向快捷技能；方向快捷与原搓招共存。
- 状态帧（idle/turn/walk/dash/backstep/dodge/land/crouch/guard/hit/launch/down/wake/roll/air_tech/stun/blockstun/guardbreak/intro/victory/defeat/timeout/charge_* 等）已随 `assets/fighters/ultraman-zero/animations/manifest.json` 安装，`state_frames.json` 与 manifest 同名 clip 对齐。

## 已知缺口

- 真正机 720/1080、双朝向画面检查未做；听审未做；无录屏。不能把逻辑检查当成画面或听感通过。
- 赛罗其它形态（超限、月神奇迹、光辉、强壮日冕、究极）仍未实现：选人界面 `implemented=false`，无独立整帧、招式与声音；默认形态不受影响。
- 基础光弹仍用通用 `pulse` 弹体；赛罗专属基础弹家族未另建。三格终结与 Q 蓄气已用专属家族。

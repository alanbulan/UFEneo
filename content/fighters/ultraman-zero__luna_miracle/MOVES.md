# ultraman-zero__luna_miracle MOVES（骨架，未装机）

- 角色/形态：赛罗奥特曼（月神奇迹），`fighter_id: ultraman-zero__luna_miracle`。
- 数据来源：`content/fighters/ultraman-zero__luna_miracle/command_table.json`、`move_manifest.json`、`state_frames.json`、`moves/*.json` 从基础赛罗 `content/fighters/ultraman-zero/` 同步骨架；招式数值、tick、帧结构、输入与 cancel 语义保持一致。
- 身份锚：`art/fighters/ultraman-zero__luna_miracle/stage1/idle/frames/identity-idle-pixel.png`（256×256，站高 188，根点 [128,248]，脚底 247，32 色冻结色板）。
- 特效命名：赛罗专属 `zero_fx_*` 已改写为 `zero_luna_miracle_fx_*`（wide/emerium/slugger/pulse 及命中/飞行/回收等引用）；不得引用其他形态图集，不得保留 `pending_` id。专属 FX 资产与 `phase3_entries.json` / `charge_policy.json` 提案待本形态自绘并登记。
- 状态：**未装机、不可实装**（`playable=false`）。动作整图/atlas、66 状态 clip 与 47 招 sprite、form_switch 6 帧 60 tick、特效资产与运行时接线尚未完成。
- 约束：技能帧只画人物本体，不烘焙特效；每帧需满足站高 188±8%（相邻站姿 ≤10%）、单连通主体、二值 Alpha、≤32 色、256 格锚 [128,248]。

## 待完成

1. 逐条生成 66 个状态 clip 与 47 招所需 sprite，按身份锚单参考落格并安装到 `assets/fighters/ultraman-zero__luna_miracle/animations/`。
2. `form_switch` 6 帧 60 tick（256 格，锚 [128,248]）落格并写入 manifest/state。
3. 自绘 PixelFX：wide/emerium/slugger 系列、pulse 飞行与命中、impact_*、Q 蓄气三态（硬 Alpha ≤16 色、4 连通主体外 alpha≥200=0），产出 `phase3_entries.json` 与 `charge_policy.json` 提案供根登记。
4. 重算受击/攻击框、补齐 `SOUNDS.md` 与 `production_plan.json`、验证后再将 `playable` 改 true（selection/battle_forms implemented 由根统一开启）。

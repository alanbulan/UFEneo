# 强壮日冕赛罗动作帧分包说明

只做分配给你的 clip；不改共享文件（`content/roster/**`、`content/presentation/**`、
`content/fighters/ultraman-zero/**`、AGENTS.md、docs/**）、不提交、不动其它 clip。
工作树：`/Users/wurulan/Developer/Projects/Game/ultraman-neo/.claude/worktrees/agent-aa55601035b8c40e7`。

## 唯一身份参考

每一帧只传这一张：`art/fighters/ultraman-zero__strong_corona/stage1/idle/frames/pixel-raw-03.png`。
不要引基础赛罗或其它形态人物帧，不要引多张参考。

## 计划

`tools/rebuild/ultraman-zero__strong_corona/frame_plan.json` 已给出每个 clip 的帧数、
逐帧动作文字、脚底行、身高类别。提示词 = `prompt_prefix` + `frames[i].action` + `prompt_suffix`。
分配 clip 的 raw 目录与 cell 前缀也在计划里。

## 生图参数

MCP `mcp__magpie-image__generate_image`：
- model `codex/gpt-image-2`，quality `high`，size `1024x1536`，background `transparent`
- `reference_images` 只放上面那一张绝对路径
- `path` 用计划里的 raw_dir 绝对路径，文件名 `<clip>-<NN>-raw.png`
- 每次可并行 6–10 帧；拿到 id 后调用 `mcp__magpie-image__generation_result` 取实际路径
- 必须核实际返回路径、尺寸、Alpha；请求尺寸不等于实收尺寸

## 硬要求

- 人物帧只画本体：不得烘焙光束、光晕、颗粒、能量球、飞行物、地面、文字、边框、网格。
- 投影类（pulse/low_pulse/air_pulse/ranged_forward/special/special2/special3/air_special）
  只画手与身体动作，手里不得有能量球或飞行物。
- 单个完整人物，不拼多格；固定右侧视（form_switch 以外）；保持参考的头身比、四肢粗细、配色。
- 逐帧手/臂/腿要有可见位移，不许同一姿势复制凑帧。
- 生成后运行：
  `.venv/bin/python tools/rebuild/ultraman-zero__strong_corona/promote_clip.py <clip>`
- `flags` 为空的帧才通过。地面站立帧落格后高度须 188±8%；蹲/空中/倒地帧允许高度变化但要登记。
  连通块必须 1、Alpha 必须 [0,255]、色数 ≤32。
- 失败帧最多改 2 种提示词修法；同一帧连续 3 次拒收就停该帧并在报告里写清。
- 删掉拒收 raw 前先记录 SHA 与原因到 `stage2/<group>/<clip>/rejects.json`；不留副本。

## 报告

只报：分配的 clip 名、实际生成帧数、通过帧数、flags 未清项、拒收原因、未完成项。
不要写“已看画面通过”除非真的逐帧看过联系表；无录屏就写无录屏。

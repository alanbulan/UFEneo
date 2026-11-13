# ultraman-zero__luna_miracle 声音来源计划（骨架，未装机）

- 状态：骨架阶段，未新增、未绑定 Luna Miracle 专属声音；未改 `content/audio/runtime.json` / `content/audio/sources.json`。
- 口径：沿用基础赛罗 `content/fighters/ultraman-zero/SOUNDS.md` 的事件/来源门槛与 1:1 注册原则；招式音频事件与 `moves/*.json` 中 `audio` 字段当前保持基础赛罗同款引用（共享 id），不伪造 Luna 专属原声。
- 来源性质：`episode` 仅用于经核实原剧/电影音轨；数字拟音/转换/合成标 `original`；转载注明 reprint；未核实作品/集数/时码的素材不得冒充本人原声。
- 待办（装机后）：逐招核对命中/挥空/发射/蓄力/持续/落地等事件，按运行时可用 id 绑定并补 `sources.json`/`runtime.json` 记录与 SHA；quality gate（SNR ≥ 12 dB、约 −20 LUFS、峰值 ≤ −1 dBTP）与听审通过后再登记。
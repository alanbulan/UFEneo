# 主游戏 HUD 安全区图形回归

唯一图形入口仍为 `app/scenes/main.tscn`。`tests/review/app/hud_framing/main_entry.gd` 实例化正式场景，继承正式游戏，仅装配 tick0 初始条件、真实 InputFrame 和冻结取图；不建替代场景，不改 core/角色定义/资源。

## 实际覆盖

- far：正式亚刻对哥莫拉，初距540；双方依次垂直跳、同时相向前跳；保留训练板。哥莫拉初始半血和满能，真实显示变身提示，随后不写任何模拟状态。
- near：正式亚刻对哥莫拉，初距70；2K真实扫腿使长尾受方倒地/起身，6→2→3+K真实光剑挑空；普通对战布局保留完整HUD。剑为人物整帧的一部分，不冒称独立持握附件。
- held_rock：正式雷德王对哥莫拉，初距540；满能P真实三级碎岩连掷，独立持握岩石实体进入镜头取景；离手投射物与光束不作为随身轮廓。

所有场景双方满能，HP由冻结合同明确声明。初始条件只在创建tick0时设置；之后只注入原始输入。每组190tick，方向镜像只改变输入和tick0朝向/站位。

## 使用

先按仓库约定锁内导入。冻结前确认所有生产代码稳定：

```
python tools/rebuild/shared/hud_framing_review/main_bundle.py freeze --engine /absolute/path/to/godot --out reports/hud-framing/contracts-new
python tools/rebuild/shared/hud_framing_review/main_bundle.py run --contract reports/hud-framing/contracts-new/far.json --out reports/hud-framing/headless-far-new --headless
python tools/rebuild/shared/hud_framing_review/main_bundle.py run --contract reports/hud-framing/contracts-new/far.json --out reports/hud-framing/graphical-far-new
```

near、held_rock分别替换合同/输出名。输出只能使用新目录，不覆盖旧证据。headless每案双向原带+独立回放四组；图形每案双向720/1080四组。每个进程通过Godot锁，Dummy音频、gl_compatibility及独立XDG目录。只接受已确认的完整VSync警告文字，其余error/warning拒绝。

冻结资源SHA在每组进程入口及批次前后验证。headless不产生图形证据。图形窗口必须连续8帧且至少500ms保持指定尺寸，期间模拟不得前进。截图等待post_draw时停止模拟；验证tick/hash/双方sprite和render region，并在布局最终刷新后重算完整Alpha bounds及实际HUD安全区，记录原尺寸PNG及SHA，不缩放截图。

每一实际main运行结束都用新建sim按原带重放、逐tick比较state_hash；headless另有独立主游戏进程回放。训练/普通模式、跳高、真实倒地、剑技、实体岩石与变身提示均有覆盖门禁；通过不等于美术质量验收。无录屏。

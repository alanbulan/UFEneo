# 月亮装甲垂直跳九相候选

只复用已有完整159采样，来源注册由register.py生成。takeoff2、vertical_jump5、land2，共9相；land01整幅上移4像素，其余8相像素不变。保留旧收据，不修改core/content/assets，不开放装甲，不包含前后翻。

main_bundle.py freeze --root-review art/fighters/ultraman-arc__luna/stage2/vertical_jump-registered-20261105-v1/root-review.json --out reports/luna-vertical-jump-resume/candidate-runtime-v5.json

main_bundle.py run --contract reports/luna-vertical-jump-resume/candidate-runtime-v5.json --out reports/luna-vertical-jump-resume/headless-v5 --headless

图形验证用同一run命令移除--headless，更换新输出目录graphical-v5。运行器逐个通过tools/godot_lock.py启动正式app/scenes/main.tscn；双向720/1080各原输入及独立回放，共8组。XDG数据/配置/缓存隔离于reports输出目录。没有硬件键盘输入，不录屏。

120tick在frame40输入一个8方向InputFrame，其余双方中立。自然轨迹、落地、回架、9相覆盖、全身边界、双方HP/体力不变、无攻击事件/弹体、独立逐tick hash/events/projectiles全部核对。截图等待真实窗口稳定至少8帧且500ms，冻结主节点process/physics后等待frame_post_draw核tick/hash/sprite/region，屏蔽旧idle异步截图。仅隐藏训练板，保留HUD。

每组19张：开始/后续稳态idle；相对输入n=0,1,2,7,8,14,15,17,18,25,26,32,33,34,35,36,37。包括所有9相首末及空中末→落地首、落地00末→01首、落地末→idle首。首末同tick的单tick相不额外推进。

python tools/rebuild/ultraman-arc/luna-vertical-jump-resume/test_check.py 使用headless-v5实际trace做正例及错误高度/phase/sprite/tick/漏相/训练板/HP/体力/事件/弹体/截图尺寸/冻结tick/hash/边界缺图的拒绝测试。可设LUNA_VERTICAL_TRACE指定另一份实际trace。图形解析器单元测试中的截图SHA是明确mock，不作为图形证据。

历史合同缺少22项已清理依赖，仅报告，不冒称原处理流程可重现。strict_size_accepted、jump_art_accepted始终false；技术检查不替代主游戏逐图视觉验收。v2首次运行因clip缺anchor_y失败；v3因处理脚本SHA变化在启动前被门禁阻止。仅最终成功合同可供交付。

## v5环境诊断修正

v5图形首组进程code0，但ALSA ERR_CANT_OPEN与audio fallback导致严格诊断检查失败，剩7组未运行。v5显式使用--audio-driver Dummy与--rendering-method gl_compatibility，不代表声音听审。仅完整匹配已实证的unsupported V-Sync原句列为环境警告，逐日志保留source/行号/原文/classification到engine-log-review.json；其它WARNING、ERROR和Parse Error仍阻止通过。Python回归含未知警告、ALSA错误、音频fallback、相似但扩展V-Sync警告、脚本/解析错误拒绝测试。

图形v4首组Godot正常退出但出现VSync不支持及ALSA音频初始化/回退诊断，runner拒绝，余7组未运行。v5显式使用Dummy音频和gl_compatibility；仅精确匹配已证实VSync原句为环境警告，每组保存engine-log-review.json，未知警告及所有错误仍失败。没有声音验收。v5共24项正负例，headless输入、hash和模拟指纹逐tick与v4一致。

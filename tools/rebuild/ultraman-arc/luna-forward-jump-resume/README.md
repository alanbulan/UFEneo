# 月亮装甲前跳八相候选

只复用已有整帧源：takeoff2、flip_forward4、land2，共8相。起落完整引用 vertical_jump-registered-20261105-v1（land01已整幅上移4px，不再二次修正），翻转四相沿用candidate02。register.py生成新JSON，不复制PNG；不改core/content/assets，不开放装甲。

冻结合同：

python tools/rebuild/ultraman-arc/luna-forward-jump-resume/main_bundle.py freeze --root-review art/fighters/ultraman-arc__luna/stage2/forward_jump-registered-20261105-v1/root-review.json --out reports/luna-forward-jump-resume/candidate-runtime-v1.json

无图形验证：

python tools/rebuild/ultraman-arc/luna-forward-jump-resume/main_bundle.py run --contract reports/luna-forward-jump-resume/candidate-runtime-v1.json --out reports/luna-forward-jump-resume/headless-v1 --headless

图形验证使用相同run命令移除--headless并改新目录graphical-v1；双向720/1080及独立原输入回放，共8组。每次Godot通过tools/godot_lock.py串行调用，Dummy音频/gl_compatibility，XDG数据配置缓存隔离reports。代码或源改动必须另封新版本，已有失败保留，不覆盖合同或结果。

120tick只在frame40输入相对9（世界x=facing、y=1）一个InputFrame，余tick双方中立。保持现有自然高度和水平4×33=132位移，不在已启动模拟中改状态/坐标。初始站位沿用既有main候选setup。takeoff2→air31→land4→idle；diagonal_air有33个轨迹时钟槽，flip_forward时长8/8/8/9，真实air从轨迹n2开始，首相实际显示6tick，不修改模拟凑时长。左右使用整帧镜像，不反序。

每组17张冻结图：稳态idle frame0/100；相对n=0,1,2,7,8,15,16,23,24,32,33,34,35,36,37。覆盖所有8相实际首末及takeoff01→flip00、flip00→01、01→02、02→03、03→land00、land01→idle。窗口至少8稳定帧且500ms后启动；冻结process/physics，等待frame_post_draw核tick/hash/sprite/region。禁止继承旧idle/walk未冻结截图。仅隐藏训练板，HUD保留，不动镜头、不隐藏HUD或挪单人位置。

独立回放逐tick检查原输入、state_hash、simulation_fingerprint、事件/弹体；检查自然高度/位移/落地、相号、双方HP/体力不变、全身viewport边界。日志仅精确已知unsupported V-Sync警告允许，其余警告/错误失败并保存逐行分类。Python正负例：python tools/rebuild/ultraman-arc/luna-forward-jump-resume/test_check.py；可用LUNA_FORWARD_TRACE指定实际trace。图形解析fixture的SHA为mock，不是图形证据。

技术通过不等于视觉、严格骨尺、实速或声音验收。strict_size_accepted/jump_art_accepted始终false；HUD潜在遮挡及回架衔接留待真实图形审查。无录屏。

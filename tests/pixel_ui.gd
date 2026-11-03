extends SceneTree
## 只验证正式资源、菜单状态和像素倍率；画面质量交给审片。
func _initialize() -> void: call_deferred("run")
func require(value: bool, message: String) -> void:
	if not value:
		push_error(message)
		quit(1)
func run() -> void:
	var hud:=UfeMatchUI.new()
	root.add_child(hud)
	await process_frame
	require(not hud.menu.visible and not hud.debug_label.visible,"默认HUD应隐藏暂停及调试文字")
	hud.show_pause(true)
	require(hud.menu.visible,"暂停菜单必须可显示")
	var sim:=UfeContentDatabase.match_for("ultraman","zetton")
	hud.show_commands(sim.fighters[0].definition)
	require(hud.commands.visible and not hud.menu.visible,"招式/提示页互斥显示")
	hud.show_commands(sim.fighters[0].definition)
	require(not hud.commands.visible,"提示页可以关闭")
	hud.close_overlays()
	hud.update_match(sim,"",0,false)
	for i in range(2):
		require(hud.portraits[i].picture.texture!=null,"头像资源应接入")
	sim.fighters[0].stats.hp=700
	hud.update_match(sim,"",0,false)
	require(hud.health[0].delayed>hud.health[0].bar.value,"受伤先留白色残影")
	for i in range(90):hud.update_match(sim,"",0,false)
	require(absf(hud.health[0].delayed-0.7)<0.001,"白色残影应回落到当前生命值")
	print("像素HUD资源和菜单状态验证完成")
	quit()

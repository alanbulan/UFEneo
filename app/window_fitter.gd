class_name UfeWindowFitter
extends RefCounted
## 窗口整数倍初始化与 640x360 原生视口等比缩放适应。


static func size_window(app: Control) -> void:
	if DisplayServer.get_name() == "headless":
		return
	var window := app.get_window()
	if window == null or window.mode != Window.MODE_WINDOWED:
		return
	# 审片显式指定的窗口尺寸优先于按屏幕自动放大，便于逐项核 720/1080。
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--capture-size="):
			var parts := arg.trim_prefix("--capture-size=").split("x")
			if parts.size() == 2 and parts[0].is_valid_int() and parts[1].is_valid_int():
				window.size = Vector2i(int(parts[0]), int(parts[1]))
				window.move_to_center()
			return
	var usable := DisplayServer.screen_get_usable_rect(window.current_screen).size
	var factor := 1
	for candidate in [6, 5, 4, 3, 2]:
		if 640 * candidate <= usable.x and 360 * candidate <= usable.y:
			factor = candidate
			break
	var target := Vector2i(640, 360) * factor
	if target.x == window.size.x and target.y == window.size.y:
		return
	window.size = target
	window.move_to_center()


static func fit(viewport_size: Vector2, image: Control, frame_holder: Control) -> void:
	if not is_instance_valid(image) or not is_instance_valid(frame_holder):
		return
	var factor := minf(viewport_size.x / 640.0, viewport_size.y / 360.0)
	if factor <= 0.0:
		factor = 1.0
	frame_holder.custom_minimum_size = Vector2(640, 360) * factor
	frame_holder.size = frame_holder.custom_minimum_size
	image.size = Vector2(640, 360)
	image.scale = Vector2(factor, factor)

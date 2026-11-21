extends SceneTree
## 逐角色核对已装机招式与状态帧能实际加载：每个本地招式通过规则校验，
## 帧 sprite 不越出 clip 帧数，状态 clip 都有 state_frames 条目。
## 只做数据自洽检查，不代表美术/听感通过。
var failures: Array[String] = []
var fighters := ["zoffy", "mother-of-ultra", "ultraman-gaia", "father-of-ultra", "ultraman-king", "ultraman-zero", "ultraman-justice"]
# 运行时可能读取的状态键（fighter.gd / side_view.gd 的 animation_key 与分派）。
const RUNTIME_STATE_KEYS := [
	"idle", "walk_forward", "walk_back", "crouch", "crouch_start", "crouch_rise", "crouch_turn",
	"crouch_guard", "guard", "dash_start", "dash_stop", "takeoff", "chase_takeoff",
	"vertical_jump", "flip_forward", "flip_back", "air_apex", "air_tech",
	"hit_high", "hit_mid", "hit_crouch", "hit_air", "launch_rise", "launch_fall",
	"blockstun", "crouch_blockstun", "guardbreak", "stun", "down", "wake", "wake_low", "wake_mid",
	"dodge", "backstep", "bounce", "roll_forward", "roll_back", "getup", "land",
	"charge", "charge_start", "charge_stop", "burst",
	"throw_tech", "grabbed", "thrown_forward", "thrown_back", "thrown_air", "thrown_dash",
	"intro", "victory", "defeat", "timeout", "turn", "ko", "win",
]

func check(ok: bool, label: String) -> void:
	if not ok:
		failures.append(label)
		printerr("FAIL " + label)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	# 已实装形态各自有独立定义与动作清单，必须与本体的七角色同口径核对。
	for row in UfeContentDatabase.read_json("res://content/roster/selection.json").entries:
		for form in row.get("forms",[]):
			if not bool(form.get("implemented",false)) or str(form.get("id","")) in fighters:continue
			if not FileAccess.file_exists("res://content/fighters/%s/definition.json"%str(form.id)):continue
			fighters.append(str(form.id))
	var required_moves: Array = UfeContentDatabase.read_json("res://content/templates/humanoid/move_manifest.json")
	# 变身/形态切换动画是招式片段，不是状态帧。
	var transform_clips: Dictionary = {}
	for source in UfeBattleFormCatalog.registry().values():
		for row in [source] + source.get("choices", []):
			var key := str(row.get("transform_animation", ""))
			if not key.is_empty(): transform_clips[key] = true
	for id in fighters:
		var definition := UfeContentDatabase.fighter(id, true)
		var manifest: Dictionary = UfeContentDatabase.read_json(
			"res://assets/fighters/%s/animations/manifest.json" % id)
		var clips: Dictionary = manifest.get("clips", {})
		check(not clips.is_empty(), id + " 有动画清单")
		if id == "zoffy": check_zoffy_data(definition, clips)
		else: check_air_runtime(id, definition, manifest)
		var local: Dictionary = {}
		var local_manifest := "res://content/fighters/%s/move_manifest.json" % id
		if FileAccess.file_exists(local_manifest):
			for move_id in UfeContentDatabase.read_json(local_manifest):
				local[move_id] = true
		for move_id in definition.moves:
			var data: Dictionary = definition.moves[move_id]
			check(UfeMoveData.validate(data), "%s/%s 规则校验" % [id, move_id])
			check(data.frames.size() > 0, "%s/%s 帧数非空" % [id, move_id])
			if clips.has(move_id):
				var frames: int = clips[move_id].rects.size()
				var overflow := 0
				for frame in data.frames:
					if int(frame.sprite) < 0 or int(frame.sprite) >= frames:
						overflow += 1
				check(overflow == 0, "%s/%s 帧 sprite 在 %d 帧内" % [id, move_id, frames])
		for move_id in local:
			check(definition.moves.has(move_id), "%s/%s 本地招式已加载" % [id, move_id])
			var local_json := "res://content/fighters/%s/moves/%s.json" % [id, move_id]
			check(required_moves.has(move_id) or FileAccess.file_exists(local_json),
				"%s/%s 属通用招式清单或有本地招式文件" % [id, move_id])
		for clip_id in clips:
			if required_moves.has(clip_id):
				continue
			if local.has(clip_id) or transform_clips.has(clip_id):
				continue
			check(definition.state_frames.has(clip_id), "%s/%s 状态帧已登记" % [id, clip_id])
		for move_id in definition.moves:
			var path := "res://content/fighters/%s/moves/%s.json" % [id, move_id]
			if FileAccess.file_exists(path):
				continue
			check(not clips.has(move_id) or not required_moves.has(move_id),
				"%s/%s 无本地招式文件" % [id, move_id])
		# 运行时状态键缺 clip 时 _animation 返回空字典，人物会停在上一帧；
		# 这里只登记缺口供排期，不当作美术通过。
		var missing_states: Array = []
		for key in RUNTIME_STATE_KEYS:
			if not clips.has(key):
				missing_states.append(key)
		if not missing_states.is_empty():
			print("  %s 缺运行时状态 clip(%d): %s" % [id, missing_states.size(), ", ".join(missing_states)])
	print("ROSTER_DATA_INTEGRITY " + ("PASS" if failures.is_empty() else str(failures)))
	print("  checked " + str(fighters.size()) + " fighters / " + str(required_moves.size()) + " required moves")
	quit(0 if failures.is_empty() else 1)

func check_air_runtime(id: String, definition: UfeFighterDefinition, manifest: Dictionary) -> void:
	var clips: Dictionary = manifest.clips
	var pairs := {"vertical": "vertical_jump", "diagonal": "flip_forward", "backward": "flip_back", "chase": "chase_takeoff"}
	var view := UfeSideView.new()
	for kind in pairs:
		var alias: String = str(kind) + "_air"
		var clip_key: String = pairs[kind]
		var rows: Array = definition.state_frames.get(alias, [])
		var source: Array = definition.state_frames.get(clip_key, [])
		var clip: Dictionary = clips.get(clip_key, {})
		check(not rows.is_empty() and not source.is_empty() and not clip.is_empty(), "%s/%s 本人空中轨迹与源姿势存在" % [id, alias])
		if rows.is_empty() or source.is_empty() or clip.is_empty():continue
		if kind != "chase":check(rows.size() == definition.jump_speed * 2, "%s/%s 保持完整普通跳跃周期" % [id, alias])
		var facing_samples: Array = []
		for player in range(2):
			var sim := UfeContentDatabase.match_for(id, id, true)
			var actor := sim.fighters[player]
			if kind == "chase":
				actor.enter("air")
				actor.motion.jump_kind = "chase"
				actor.vy = 18
			var seen: Dictionary = {}
			var samples: Array = []
			var last_air_age := -1
			var last_air_sprite := -1
			var landed := false
			for tick in range(80):
				var inputs: Array = [UfeInputFrame.make(), UfeInputFrame.make()]
				if tick == 0 and kind != "chase":
					var direction: int = 1 if kind == "diagonal" else -1 if kind == "backward" else 0
					inputs[player] = UfeInputFrame.make(direction * actor.facing, 0, UfeInputFrame.JUMP)
				sim.step(inputs)
				if actor.state == "air":
					var frame := actor.frame()
					var shown := view._animation(actor, manifest)
					var age := actor.definition.jump_speed - actor.vy
					var sprite := int(frame.get("sprite", -1))
					check(int(shown.get("index", -1)) == sprite - int(clip.get("simulation_sprite_offset", 0)), "%s/%s/%d/%d 双向显示帧与受击姿势一致" % [id, alias, player, tick])
					check(source.any(func(pose): return int(pose.sprite) == sprite and pose.hurtboxes == frame.hurtboxes), "%s/%s/%d/%d 复用本人同姿势受击框" % [id, alias, player, tick])
					if kind == "chase":
						check(age < rows.size(), "%s/%s/%d/%d 追击轨迹覆盖实际下降索引" % [id, alias, player, tick])
						check(sprite == int(source[-1].sprite), "%s/%s 保持本人追击末姿势" % [id, alias])
					seen[sprite] = true
					samples.append([age, sprite, frame.hurtboxes])
					last_air_age = age
					last_air_sprite = sprite
				elif actor.state == "land":
					landed = true
					break
			check(landed and not samples.is_empty(), "%s/%s/%d 从实际飞行落地" % [id, alias, player])
			check(last_air_sprite == int(source[-1].sprite), "%s/%s/%d 落地前最后tick使用末姿势" % [id, alias, player])
			if kind != "chase":
				check(last_air_age == definition.jump_speed * 2, "%s/%s/%d 不改变普通跳跃物理时长" % [id, alias, player])
				check(seen.size() == clip.rects.size(), "%s/%s/%d 整条本人空中图均可达" % [id, alias, player])
			facing_samples.append(samples)
		check(facing_samples[0] == facing_samples[1], "%s/%s 原生左右朝向共用相同姿势与受击框" % [id, alias])
	view.free()

# 佐菲连贯性契约：计时表按 tick 展开，受投表仍按姿势索引；不作美术验收。
func zoffy_clip_sprites(clip: Dictionary, offset: int = 0) -> Array[int]:
	var result: Array[int] = []
	var durations: Array = clip.get("ticks", [])
	for sprite in range(durations.size()):
		for _tick in range(int(durations[sprite])):
			result.append(sprite + offset)
	return result

func check_zoffy_data(definition: UfeFighterDefinition, clips: Dictionary) -> void:
	var dash_sprites: Array[int] = []
	var dash_sizes := [2, 4, 3]
	var dash_offset := 0
	for part in range(3):
		var key: String = ["dash_start", "dash", "dash_stop"][part]
		var clip: Dictionary = clips.get(key, {})
		check(clip.get("rects", []).size() == dash_sizes[part], "zoffy/%s 九图冲刺分段" % key)
		check(not bool(clip.get("loop", true)), "zoffy/%s 冲刺分段不循环" % key)
		check(int(clip.get("simulation_sprite_offset", -1)) == dash_offset, "zoffy/%s 模拟全局 sprite 偏移" % key)
		for duration in clip.get("ticks", []):
			check(int(duration) >= 2 and int(duration) <= 4, "zoffy/%s 每格 2..4 tick" % key)
		dash_sprites.append_array(zoffy_clip_sprites(clip, dash_offset))
		dash_offset += int(dash_sizes[part])
	check(dash_sprites.size() == 22, "zoffy/dash 三段总长仍为 22 tick")
	for key in definition.state_frames:
		if not clips.has(key): continue
		var rows: Array = definition.state_frames[key]
		var clip: Dictionary = clips[key]
		check(clip.get("ticks", []).size() == clip.rects.size(), "zoffy/%s 图片与时长一一对应" % key)
		for duration in clip.get("ticks", []):
			check(int(duration) > 0, "zoffy/%s 每张图时长为正" % key)
		var actual: Array[int] = []
		for row in rows: actual.append(int(row.get("sprite", -1)))
		if str(key) == "grabbed" or str(key).begins_with("thrown_"):
			check(rows.size() == clip.rects.size(), "zoffy/%s 每姿势一行，不按 ticks 扩展" % key)
			for index in range(rows.size()):
				check(int(rows[index].get("sprite", -1)) == index, "zoffy/%s 保留姿势编号 %d" % [key, index])
				var points: Dictionary = rows[index].get("grab_points", {})
				check(points.has("waist"), "zoffy/%s/%d 有旧式 hold 腰抓点" % [key, index])
				for point in points:
					check(UfeThrowResolver.HoldPoints.point_valid(points[point]), "zoffy/%s/%d/%s 抓点为合法整数坐标" % [key, index, point])
			continue
		var expected := dash_sprites if str(key) == "dash" else zoffy_clip_sprites(clip, int(clip.get("simulation_sprite_offset", 0)))
		check(actual == expected and not expected.is_empty(), "zoffy/%s sprite 逐 tick 展开等于 clip.ticks" % key)
	check(definition.state_frames.get("idle", []).size() == 60, "zoffy/idle 完整周期为 60 tick 而不是 6 tick")
	# 这里只覆盖普通跳跃；chase_takeoff/追击空中不使用此轨迹协议。
	for pair in [["vertical_air", "vertical_jump"], ["diagonal_air", "flip_forward"], ["backward_air", "flip_back"]]:
		var clip: Dictionary = clips.get(pair[1], {})
		check(bool(clip.get("trajectory_driven", false)), "zoffy/%s 按轨迹驱动" % pair[1])
		check(zoffy_clip_sprites(clip).size() == 32, "zoffy/%s 普通跳跃总长 32 tick" % pair[1])
		var trajectory: Array = definition.state_frames.get(pair[0], [])
		check(trajectory.size() == 32 and trajectory == definition.state_frames.get(pair[1], []), "zoffy/%s 轨迹表与跳跃姿势及受击框一致" % pair[0])
	check_zoffy_normals(definition, clips)

func check_zoffy_normals(definition: UfeFighterDefinition, clips: Dictionary) -> void:
	# 重设计只重排真实 sprite，锁住本轮修复前的总时长、有效窗与伤害。
	for baseline in [["light1", 10, 3, 7, 65], ["light2", 10, 3, 7, 65], ["light3", 11, 3, 6, 65], ["heavy", 14, 4, 10, 100]]:
		var key := str(baseline[0])
		var move: Dictionary = definition.moves[key]
		var clip: Dictionary = clips.get(key, {})
		var sprite_count: int = clip.get("rects", []).size()
		check(sprite_count > 1 and sprite_count <= 8, "zoffy/%s 使用 2..8 张真实图" % key)
		check(clip.get("ticks", []).size() == sprite_count, "zoffy/%s 图片与时长一一对应" % key)
		for duration in clip.get("ticks", []):
			check(int(duration) > 0, "zoffy/%s 每张攻击图均可达" % key)
		check([int(move.startup), int(move.active), int(move.recovery), int(move.damage)] == baseline.slice(1), "zoffy/%s 帧数据与伤害不变" % key)
		check(move.frames.size() == int(baseline[1]) + int(baseline[2]) + int(baseline[3]), "zoffy/%s 总时长不变" % key)
		var sprites: Array[int] = []
		for tick in range(move.frames.size()):
			var row: Dictionary = move.frames[tick]
			sprites.append(int(row.sprite))
			check((not row.hitboxes.is_empty()) == (tick >= int(baseline[1]) and tick < int(baseline[1]) + int(baseline[2])), "zoffy/%s/%d active 窗口不变" % [key, tick])
			var expected_cancel: Array = ["light2"] if key == "light1" and tick >= 10 and tick <= 18 else ["light3", "launcher"] if key == "light2" and tick >= 10 and tick <= 18 else []
			var cancel: Array = row.cancel
			check(cancel.size() == expected_cancel.size() and expected_cancel.all(func(target: String) -> bool: return cancel.has(target)), "zoffy/%s/%d 仅在原取消窗添加 launcher" % [key, tick])
		check(sprites == zoffy_clip_sprites(clip), "zoffy/%s 招式 sprite 与真实图时长逐 tick 对应" % key)

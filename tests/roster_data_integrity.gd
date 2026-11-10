extends SceneTree
## 逐角色核对已装机招式与状态帧能实际加载：每个本地招式通过规则校验，
## 帧 sprite 不越出 clip 帧数，状态 clip 都有 state_frames 条目。
## 只做数据自洽检查，不代表美术/听感通过。
var failures: Array[String] = []
var fighters := ["zoffy", "mother-of-ultra", "ultraman-gaia", "father-of-ultra", "ultraman-king", "ultraman-zero"]
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
	var required_moves: Array = UfeContentDatabase.read_json("res://content/templates/humanoid/move_manifest.json")
	for id in fighters:
		var definition := UfeContentDatabase.fighter(id, true)
		var manifest: Dictionary = UfeContentDatabase.read_json(
			"res://assets/fighters/%s/animations/manifest.json" % id)
		var clips: Dictionary = manifest.get("clips", {})
		check(not clips.is_empty(), id + " 有动画清单")
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
			check(required_moves.has(move_id), "%s/%s 属通用招式清单" % [id, move_id])
		for clip_id in clips:
			if required_moves.has(clip_id):
				continue
			if local.has(clip_id):
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

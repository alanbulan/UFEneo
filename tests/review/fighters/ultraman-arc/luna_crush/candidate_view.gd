extends "res://presentation/side_view.gd"
## 正式侧视显示/Alpha取景照常继承；仅在首次_ready用候选月亮本人资源装配。
var candidate_contract: Dictionary = {}
var candidate_contract_path: String = ""

func _ready() -> void:
	# 自建候选资源仍须继承正式绘制前HUD布局刷新。
	RenderingServer.frame_pre_draw.connect(_refresh_layout_framing)
	assert(not candidate_contract.is_empty() and not candidate_contract_path.is_empty())
	assert(bool(candidate_contract.get("root_runtime_ready", false)))
	assert(simulation.fighters[0].definition.id == "ultraman-arc__luna")
	walk_review_clip = candidate_contract_path # 显式候选通道允许只读开发目录绝对PNG。
	if FileAccess.file_exists("res://content/presentation/camera_follow.json"):
		camera_config = UfeContentDatabase.read_json("res://content/presentation/camera_follow.json")
	if FileAccess.file_exists("res://content/presentation/phase3_projectiles.json"):
		projectile_clips = UfeContentDatabase.read_json("res://content/presentation/phase3_projectiles.json")
	layered_stage = UfeLayeredBattleStage.new()
	add_child(layered_stage)
	layered_stage.set_as_top_level(true)
	layered_stage.set_stage(selected_stage)
	backdrop = layered_stage.sky
	for fighter in simulation.fighters:
		var own := fighter.definition.id == "ultraman-arc__luna"
		var data: Dictionary = candidate_contract.presentation if own else UfeContentDatabase.read_json("res://content/fighters/%s/definition.json" % fighter.definition.id).presentation
		var sprite := Sprite2D.new()
		sprite.z_index = 2
		var model_path: String = str(data.model)
		sprite.texture = ImageTexture.create_from_image(Image.load_from_file(model_path)) if own else load(model_path)
		sprite.centered = false
		var palette_material := ShaderMaterial.new()
		palette_material.shader = preload("res://presentation/timer_palette.gdshader")
		sprite.material = palette_material
		models.append(sprite.texture)
		view_configs.append(data)
		loaded_fighter_ids.append(fighter.definition.id)
		fighters.append(sprite)
		manifests.append(data.manifest_data.duplicate(true) if own else UfeContentDatabase.read_json(str(data.manifest)))
		add_child(sprite)
		var effect := Sprite2D.new()
		var effect_material := ShaderMaterial.new()
		effect_material.shader = preload("res://presentation/effect_palette.gdshader")
		effect.material = effect_material
		effect.visible = false
		add_child(effect)
		attached_effects.append(effect)
		attached_slots[fighters.size()-1].append(effect)
	debug_overlay = Node2D.new()
	debug_overlay.z_index = 10
	add_child(debug_overlay)
	debug_overlay.draw.connect(_draw_boxes)
	feedback = UfeCombatFeedback.new()
	add_child(feedback)
	cinematic = UfeSuperCinematic.new()
	add_child(cinematic)
	super_state = UfeSuperStateView.new()
	add_child(super_state)
	super_state.setup(self)
	capture_view.setup()

func bind_match(value: UfeMatchDirector, preserve_feedback: bool = false) -> void:
	assert(value.fighters[0].definition.id == "ultraman-arc__luna")
	assert(value.fighters[1].definition.id == str(candidate_contract.opponent))
	# 候选入口只建同一对；禁止换定义后触发正式数据库的未开放装甲加载。
	super.bind_match(value, preserve_feedback)

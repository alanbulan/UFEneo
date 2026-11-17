extends SceneTree
## 只验证整数模拟和兼容性；画面仍由主游戏实录审阅。
const OUT := "res://reports/review/2026-10-27/projectile-ground-expiry/"
var errors: Array = []

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok:
		errors.append(label)
		printerr("FAIL " + label)

func write_json(path: String, value: Variant) -> void:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(value, "\t", true) + "\n")

func legacy_snapshots() -> Dictionary:
	var rows := {}
	# 原有反射、吸收、盾、光束、实体回旋武器和普通飞行物全部保留真实输入路径。
	for part in range(9):
		var driver := UfePhase3SpecialReview.new()
		driver.review_frame = driver.S_STARTS[part]
		var ids: Array = driver.matchup()
		var sim := UfeContentDatabase.match_for(str(ids[0]), str(ids[1]))
		driver.prepare_match(sim)
		var hashes: Array = []; var events: Array = []
		for age in range(driver.S_STARTS[part+1] - driver.S_STARTS[part]):
			if driver.wants_intro() and age < 75: continue
			var tick: int = driver.S_STARTS[part] + age
			sim.step([driver.sample(tick, sim), driver.second_sample(tick)])
			hashes.append(sim.state_hash()); events.append(sim.events.duplicate(true))
		rows["legacy-special-%s" % part] = {"hashes":hashes, "events":events, "fingerprint":sim.content_fingerprint}
	for id in ["ultraseven", "ultraman-taro", "gomora", "ultraman-teo", "ultraman-blazar"]:
		for facing in [-1, 1]:
			var sim := UfeContentDatabase.match_for(id, "zetton", true)
			var f := sim.fighters[0]
			f.x = 850 if facing < 0 else 400; f.facing = facing; f.stats.energy = 3000
			sim.fighters[1].x = 400 if facing < 0 else 850; sim.fighters[1].facing = -facing
			var hashes: Array = []; var events: Array = []; var projectiles_seen := 0
			for tick in range(600):
				var input := UfeInputFrame.make()
				if tick == 10: input = UfeInputFrame.make(0, 0, UfeInputFrame.RANGED)
				if tick == 90: input = UfeInputFrame.make(facing, 0, UfeInputFrame.RANGED)
				if tick == 190: input = UfeInputFrame.make(0, 1)
				if tick == 198: input = UfeInputFrame.make(0, 0, UfeInputFrame.RANGED)
				if tick == 300: input = UfeInputFrame.make(0, -1)
				if tick == 301: input = UfeInputFrame.make(facing, -1)
				if tick == 302: input = UfeInputFrame.make(facing, 0, UfeInputFrame.LIGHT)
				if tick == 430: input = UfeInputFrame.make(0, 0, UfeInputFrame.SPECIAL)
				sim.step([input, UfeInputFrame.make()])
				projectiles_seen += sim.projectiles.size()
				hashes.append(sim.state_hash()); events.append(sim.events.duplicate(true))
			rows["%s/%s" % [id, facing]] = {"hashes":hashes, "events":events, "fingerprint":sim.content_fingerprint, "projectile_ticks":projectiles_seen}
	return rows

func fixture() -> UfeMatchDirector:
	var sim := UfeContentDatabase.match_for()
	sim.fighters[0].x = 300; sim.fighters[1].x = 1000
	return sim

func shot(height: int, expiry: Variant = null) -> Dictionary:
	var data := {"spawn":[0,height], "box":[-4,-4,8,8], "speed":0, "vy":-4, "life":10}
	if expiry != null: data.expire_below_height = expiry
	return data

func test_boundaries() -> void:
	var sim := fixture(); var contacts: Array = []
	UfeProjectileResolver.spawn(sim, 0, shot(57, 53), "pulse")
	check(sim.projectiles[0].expire_below_height is int, "显式阈值保存为整数")
	UfeProjectileResolver.advance(sim, contacts)
	check(sim.projectiles.size() == 1 and int(sim.projectiles[0].height) == 53, "阈值相等时保留弹体")
	UfeProjectileResolver.advance(sim, contacts)
	check(sim.projectiles.is_empty(), "移动后低于阈值即清除")
	var legacy := fixture()
	UfeProjectileResolver.spawn(legacy, 0, shot(4), "pulse")
	check(not legacy.projectiles[0].has("expire_below_height"), "旧弹体字典不新增缺省键")
	UfeProjectileResolver.advance(legacy, contacts)
	check(legacy.projectiles.size() == 1 and int(legacy.projectiles[0].height) == 0, "旧弹体零高度仍保留")
	UfeProjectileResolver.advance(legacy, contacts)
	check(legacy.projectiles.is_empty(), "旧弹体负高度清除")
	for threshold in [null, 53]:
		var hit := fixture(); hit.fighters[1].x = hit.fighters[0].x
		var found: Array = []
		UfeProjectileResolver.spawn(hit, 0, shot(54, threshold), "pulse")
		UfeProjectileResolver.advance(hit, found)
		check(found.size() == (1 if threshold == null else 0), "清除先于同tick伤害接触/%s" % threshold)
	# 粘地弹仍先执行既有ground_height夹取；不能被到地前的暂时负坐标误杀。
	var clamped := fixture(); var data := shot(55, 53); data.ground_height = 53
	UfeProjectileResolver.spawn(clamped, 0, data, "pulse")
	UfeProjectileResolver.advance(clamped, contacts)
	check(clamped.projectiles.size() == 1 and int(clamped.projectiles[0].height) == 53 and int(clamped.projectiles[0].vy) == 0, "地面夹取先于显式阈值")

func test_validation() -> void:
	var move: Dictionary = UfeContentDatabase.fighter("ultraman").moves.pulse.duplicate(true)
	for value in [0, 53, 53.0]:
		var copy := move.duplicate(true); copy.projectile.expire_below_height = value
		check(UfeMoveData.validate(copy), "合法非负整数阈值/%s" % value)
	for value in [-1, 2.5, "53", true, INF, NAN]:
		var copy := move.duplicate(true); copy.projectile.expire_below_height = value
		check(not UfeMoveData.validate(copy), "非法阈值被拒/%s" % value)
		copy = move.duplicate(true); copy.frames[0].shots = [shot(60, value)]
		check(not UfeMoveData.validate(copy), "逐帧shots非法阈值被拒/%s" % value)

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if "--baseline" in args:
		write_json(OUT + "legacy-before.json", legacy_snapshots())
		print("PROJECTILE_GROUND_BASELINE_SAVED"); quit(0); return
	test_boundaries(); test_validation()
	if "--compare" in args:
		var baseline: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(OUT + "legacy-before.json"))
		var current := legacy_snapshots()
		for key in baseline:
			# 双方均经JSON解析统一数字类型；原状态哈希仍逐项原文比较。
			check(baseline[key] == JSON.parse_string(JSON.stringify(current[key])), "旧招逐tick/事件/指纹保持/" + key)
		write_json(OUT + "legacy-after.json", current)
	write_json(OUT + "logic-result.json", {"errors":errors, "passed":errors.is_empty(), "legacy_compared":"--compare" in args})
	print("PROJECTILE_GROUND_EXPIRY " + ("PASS" if errors.is_empty() else str(errors)))
	quit(0 if errors.is_empty() else 1)

extends SceneTree
const Tape=preload("res://input/training_tape.gd")
const App=preload("res://app/game_app.gd")
var errors: Array=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	if not ok:errors.append(label);printerr(label)
func match_at(facing: int) -> UfeMatchDirector:
	var sim:=UfeContentDatabase.match_for("zetton","ultraman")
	sim.fighters[1].x=400 if facing==1 else 800
	sim.fighters[0].x=800 if facing==1 else 400
	sim.fighters[1].facing=facing;sim.fighters[0].facing=-facing
	return sim
func run() -> void:
	for recorded in [-1,1]:
		for current in [-1,1]:
			for relative in [false,true]:
				var original: Array=[recorded,-1,UfeInputFrame.LIGHT|UfeInputFrame.GUARD]
				var copy:=original.duplicate()
				var result:=Tape.sample(original,recorded,current,relative)
				check(result.x==(current if relative else recorded),"前方向按模式还原")
				check(result.y==-1 and result.buttons==original[2] and original==copy,"上下/按钮/原磁带保持")
	check(Tape.sample([1,0,1],0,-1,true).x==1,"无元数据旧磁带保持绝对方向")
	var app:=App.new();app.simulation=match_at(-1);app.dummy=4;app.dummy_relative=true
	app.dummy_tape=[[1,0,1],[-1,-1,0]];app.dummy_facings=[1,-1]
	check(app._dummy_input().pack()==[-1,0,1],"真实陪练入口使用录制朝向")
	check(app._dummy_input().pack()==[-1,-1,0],"逐帧朝向支持录制中换边")
	check(app._dummy_input().pack()==[-1,0,1] and app.dummy_cursor==3,"循环播放索引保持")
	app.dummy_tape.clear();check(app._dummy_input().pack()==[0,0,0],"空磁带中立")
	app.dummy_facings.clear();app.dummy_recording=true;app.training=true
	app._record_dummy_input(UfeInputFrame.make(1,-1,UfeInputFrame.HEAVY))
	check(app.dummy_tape==[[1,-1,UfeInputFrame.HEAVY]] and app.dummy_facings==[-1],"录制入口保存原始帧及模拟前朝向")
	app.training=false;app._record_dummy_input(UfeInputFrame.make())
	check(app.dummy_tape.size()==1 and app.dummy_facings.size()==1,"离开训练不污染磁带")
	app.free()
	for facing in [-1,1]:
		var sim:=match_at(facing);var repeated:=match_at(facing)
		var recorder:=UfeReplayRecorder.new();var seen:=false
		var motion: Array=[[0,-1,0],[1,-1,0],[1,0,UfeInputFrame.LIGHT]]
		for tick in range(60):
			var packed: Array=motion[tick] if tick<3 else [0,0,0]
			var adapted:=Tape.sample(packed,1,facing,true)
			var pair: Array=[UfeInputFrame.make(),adapted]
			sim.step(pair);recorder.append(pair,sim)
			if sim.fighters[1].move_id=="motion_236":seen=true
		check(seen,"换边后原236轻击仍真实触发切割光线/%s"%facing)
		var path:="user://training-tape-%s.json"%facing
		check(recorder.save_file(path)==OK,"写隔离实际对局回放")
		var loaded:=UfeReplayRecorder.load_file(path,repeated.content_fingerprint)
		check(loaded!=null,"加载适配后原始InputFrame回放")
		if loaded!=null:
			for pair in loaded.frames:repeated.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
			check(repeated.state_hash()==sim.state_hash() and loaded.final_hash==sim.state_hash(),"持久回放不依赖陪练适配模式/%s"%facing)
	print("TRAINING_TAPE ",JSON.stringify({"errors":errors}));quit(0 if errors.is_empty() else 1)

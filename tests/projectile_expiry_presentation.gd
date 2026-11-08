extends SceneTree
const PROJECTILE_EXPIRY = preload("res://presentation/projectile_expiry.gd")
var errors: Array[String] = []

func check(ok: bool, message: String) -> void:
	if not ok: errors.append(message)

func _initialize() -> void:
	call_deferred("run")

func make_match() -> UfeMatchDirector:
	return UfeMatchDirector.new(UfeContentDatabase.fighter("ultraman",true),UfeContentDatabase.fighter("zetton",true),load("res://content/rules/neo.tres"),UfeContentDatabase.states())

func run() -> void:
	check(load("res://presentation/combat_feedback.gd").can_instantiate(),"特效消费脚本可加载")
	check(load("res://presentation/side_audio.gd").can_instantiate(),"声音消费脚本可加载")
	var bindings := {"expiry_fixture":{"expiry_effect":"expiry_visual","expiry_ticks":3}}
	for facing in [-1,1]:
		var sim := make_match()
		sim.fighters[0].facing = facing
		UfeProjectileResolver.spawn(sim,0,{"effect":"expiry_fixture","spawn":[0,220],"life":3,"speed":5},"pulse")
		var observed: Array = sim.projectiles.duplicate()
		var projectile: Dictionary = observed[0]
		for age in range(3):
			var age_contacts: Array = []
			UfeProjectileResolver.advance(sim,age_contacts)
			check(age_contacts.is_empty(),"高空自然到期用例不得接触")
			var before := projectile.duplicate(true)
			var effects := PROJECTILE_EXPIRY.collect(observed,sim.projectiles,bindings,false)
			check(projectile==before,"呈现读取不能改弹体")
			check(effects.size()==(1 if age==2 else 0),"只在真实到期移除时出一次消散")
			if not effects.is_empty():
				check(effects[0].x==sim.fighters[0].x+facing*15 and effects[0].facing==facing,"左右沿最终整数位置消散")
			observed=sim.projectiles.duplicate()
		check(PROJECTILE_EXPIRY.collect(observed,sim.projectiles,bindings,false).is_empty(),"下一呈现tick不得重复")
		check(PROJECTILE_EXPIRY.collect([projectile],[],{},false).is_empty(),"旧弹体未声明绑定保持静默")
		check(PROJECTILE_EXPIRY.collect([projectile],[],bindings,true).is_empty(),"终局静默")
		projectile.connected=true
		check(PROJECTILE_EXPIRY.collect([projectile],[],bindings,false).is_empty(),"命中或被防已接触者不叠到期演出")
		projectile.connected=false
		projectile.age=1
		check(PROJECTILE_EXPIRY.collect([projectile],[],bindings,false).is_empty(),"护盾等提前移除不冒充自然到期")
		var contact_sim := make_match()
		UfeProjectileResolver.spawn(contact_sim,0,{"effect":"expiry_fixture","spawn":[280,80],"life":3,"speed":0,"box":[-12,-12,24,24]},"pulse")
		var contact_observed: Array=contact_sim.projectiles.duplicate()
		var contacts: Array=[]
		UfeProjectileResolver.advance(contact_sim,contacts)
		check(not contacts.is_empty() and bool(contact_observed[0].get("connected",false)),"真实命中接触标记")
		check(PROJECTILE_EXPIRY.collect(contact_observed,contact_sim.projectiles,bindings,false).is_empty(),"真实接触移除只走接触反馈")
	print("PROJECTILE_EXPIRY_PRESENTATION "+JSON.stringify({"errors":errors,"simulation_fields_added":false}))
	quit(0 if errors.is_empty() else 1)

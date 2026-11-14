extends UfeState
## 按住蓄力超重击。防御、后方向或闪避取消；松手按档出手；满档自动出手。
func step(f: UfeFighter, input: UfeInputFrame, _command: Dictionary) -> void:
	if input.held(UfeInputFrame.GUARD) or (input.y < 0 and input.x * f.facing < 0):
		_cancel(f, "crouch_guard" if input.y < 0 else "guard")
		return
	if input.held(UfeInputFrame.DODGE):
		var paid := UfeStaminaRules.spend(f, UfeStaminaRules.DODGE_COST)
		f.motion.dodge_tired = paid < UfeStaminaRules.DODGE_COST
		_cancel(f, "dodge", 18)
		f.combat.invulnerable = UfeStaminaRules.TIRED_DODGE_INVULNERABLE if bool(f.motion.dodge_tired) else 12
		return
	var hold := int(f.motion.get("power_crush_hold", 0))
	if not input.held(UfeInputFrame.POWER_CRUSH):
		_fire(f, UfeFeelRules.power_crush_tier(hold))
		return
	hold += 1
	f.motion.power_crush_hold = hold
	f.motion.power_crush_tier = UfeFeelRules.power_crush_tier(hold)
	if hold >= UfeFeelRules.POWER_HOLD_AUTO:
		_fire(f, 3)

func _cancel(f: UfeFighter, id: String, duration: int = 0) -> void:
	f.motion.erase("power_crush_hold")
	f.enter(id, duration)

func _fire(f: UfeFighter, tier: int) -> void:
	var id := "power_crush_%d" % tier
	f.motion.power_crush_tier = tier
	f.motion.erase("power_crush_hold")
	if not f.definition.moves.has(id):
		f.enter("idle")
		return
	f.clear_move()
	f.motion.push_vx = 0
	f.clear_input_buffer()
	f.combat.power = 1
	f.move_id = id
	f.move_tick = 0
	f.enter("attack")

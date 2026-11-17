extends UfeState
## 站立 O 按住满 4 tick 后的蓄力。松手按档出原超重击或其加强档，满 40 tick 自动出手。
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
	var hold := int(f.motion.get("crush_hold", 0))
	if not input.held(UfeInputFrame.CRUSH):
		f.motion.crush_tier = UfeFeelRules.crush_charge_tier(hold)
		f.motion.crush_fire = f.motion.crush_tier
		return
	hold += 1
	f.motion.crush_hold = hold
	f.motion.crush_tier = UfeFeelRules.crush_charge_tier(hold)
	if hold >= UfeFeelRules.CRUSH_HOLD_AUTO:
		f.motion.crush_fire = 3

func _cancel(f: UfeFighter, id: String, duration: int = 0) -> void:
	f.motion.erase("crush_hold")
	f.motion.erase("crush_fire")
	f.enter(id, duration)

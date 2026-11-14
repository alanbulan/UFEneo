class_name UfeTrainingOverlay
extends HBoxContainer
@warning_ignore("unused_signal")
signal action_requested(action: String)
var history: Array=[[],[]]
var info: Array=[]
var lists: Array=[]
var frame_names: Array=[]
var previous: Array=["",""]
var last_moves: Array=[{},{}]
var feedback: Array=["", ""]
var feedback_ticks: Array=[0,0]
const STATE_NAMES={"idle":"待机","turn":"站立转身","crouch_turn":"蹲姿转身","walk":"移动","crouch":"蹲姿保持","crouch_start":"下蹲","crouch_rise":"起身","guard":"站防","crouch_guard":"蹲防","blockstun":"站防硬直","crouch_blockstun":"蹲防硬直","guardbreak":"破防","stun":"眩晕","air":"空中","takeoff":"起跳","land":"落地","dash":"冲刺","backstep":"后撤","dodge":"闪避","hit":"受击","launch":"击飞","bounce":"弹地","down":"倒地","wake":"起身","roll_forward":"前滚起身","roll_back":"后滚起身","air_tech":"空中受身","thrown":"被投","throw_tech":"拆投","burst":"爆气","charge_start":"蓄能起手","charge":"蓄能","charge_stop":"蓄能收势","power_charge":"蓄力超重击","intro":"登场","victory":"胜利","defeat":"失败","timeout":"时间到","attack":"攻击","air_attack":"空中攻击"}
func _ready() -> void:
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	for i in range(2):
		var panel:=PixelPanel.new();panel.custom_minimum_size.x=184;add_child(panel)
		var column:=VBoxContainer.new();panel.add_child(column)
		var title:=Label.new();title.text=str(i+1)+"P 输入 / 帧数据";column.add_child(title)
		var label:=Label.new();label.custom_minimum_size.x=1;label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;column.add_child(label);info.append(label)
		var list:=HBoxContainer.new();column.add_child(list);lists.append(list)
		if i==0:
			var spacer:=Control.new();spacer.size_flags_horizontal=Control.SIZE_EXPAND_FILL;spacer.mouse_filter=Control.MOUSE_FILTER_IGNORE;add_child(spacer)
func reset_display() -> void:
	history=[[],[]]
	previous=["",""]
	last_moves=[{},{}]
	feedback=["",""]
	feedback_ticks=[0,0]
	for list in lists:
		for child in list.get_children():list.remove_child(child);child.queue_free()
	for label in info:label.text=""
func record(inputs: Array) -> void:
	for i in range(2):
		var f: UfeInputFrame=inputs[i]
		var direction:=UfeShotoMotionParser.to_numpad(f.x,f.y)
		var key:="%d:%d"%[direction,f.buttons]
		if key==previous[i]:continue
		previous[i]=key
		history[i].append([direction,f.buttons])
		if history[i].size()>4:history[i].pop_front()
		for child in lists[i].get_children():lists[i].remove_child(child);child.queue_free()
		for entry in history[i]:
			var glyph:=InputGlyphs.new();glyph.show_input(entry[0],entry[1]);lists[i].add_child(glyph)
func update_match(sim: UfeMatchDirector) -> void:
	for event in sim.events:
		if str(event.get("kind",""))=="move_denied" and str(event.get("reason",""))=="energy":
			var player:=int(event.player)
			feedback[player]="能量不足：需要%d，现有%d"%[int(event.required),int(event.available)]
			feedback_ticks[player]=90
		elif str(event.get("kind",""))=="move_denied" and str(event.get("reason",""))=="capture_receiver":
			var player:=int(event.player)
			feedback[player]="此对手暂时无法捕获，未消耗资源"
			feedback_ticks[player]=90
		elif str(event.get("kind",""))=="move_denied" and str(event.get("reason",""))=="stamina":
			var player:=int(event.player)
			feedback[player]="体力不足：需要%d，现有%d"%[int(event.required),int(event.available)]
			feedback_ticks[player]=90
	for i in range(2):
		var f:=sim.fighters[i]
		var state_name: String=STATE_NAMES.get(f.state,f.state)
		var phase:="上一招"
		if not f.move_id.is_empty():
			var move: Dictionary=f.definition.moves[f.move_id]
			last_moves[i]=move
			state_name=str(move.get("display_name",f.move_id))
			phase="起手" if f.move_tick<int(move.get("startup",0)) else "攻击" if f.move_tick<int(move.get("startup",0))+int(move.get("active",0)) else "收招"
		var last: Dictionary=last_moves[i]
		info[i].text="%s · 连段%d\n"%[state_name,f.combat.combo]
		if last.is_empty():info[i].text+="起手 — / 攻击 — / 收招 —"
		else:info[i].text+="%s %s\n起手%d 攻击%d 收招%d"%[phase,str(last.get("display_name","")) if f.move_id.is_empty() else str(f.move_tick),int(last.startup),int(last.active),int(last.recovery)]
		var delay:=int(f.combat.get("stamina_delay",0))
		var recovery:=UfeStaminaRules.rate(f)
		info[i].text+="\n体力%d / 1000 · 远程%s"%[int(f.stats.stamina),UfeInputRouter.binding_label(i,"ranged")]
		if not f.move_id.is_empty() and int(last.get("stamina_cost",0))>0:info[i].text+=" · 本招消耗%d"%int(last.get("stamina_cost",0))
		if recovery==0:info[i].text+="\n攻防动作中暂停恢复"
		elif delay>0:info[i].text+="\n恢复等待%.1f秒"%(float(delay)/60.0)
		else:info[i].text+="\n每秒恢复%d"%(recovery*60)
		if f.state=="dodge" and bool(f.motion.get("dodge_tired",false)):info[i].text+="\n体力不足：闪避无敌缩短"
		if f.state=="power_charge" or str(f.move_id).begins_with("power_crush"):
			info[i].text+="\n蓄力超重击 %d档"%int(f.motion.get("power_crush_tier",1))
			if f.state=="power_charge":info[i].text+=" · 按住%d tick"%int(f.motion.get("power_crush_hold",0))
		if int(feedback_ticks[i])>0:
			info[i].text+="\n"+str(feedback[i])
			feedback_ticks[i]=int(feedback_ticks[i])-1

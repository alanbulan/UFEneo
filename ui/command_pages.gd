class_name UfeCommandPages
extends PixelPanel
const TITLES=["站立","下蹲","跳跃","空连","状态","投技","专属","必杀","体力"]
var entries: Array=[]
var rows:=PixelList.new()
var page: int=0
var fighter_data: UfeFighterDefinition
var title: Label
var fighter_choice: FighterName
var fighter_ids: Array=[]
var form_note: RichTextLabel
var clips: Dictionary={}
var tabs: PixelTabBar
var table_headers: HBoxContainer
func _init() -> void:
	theme=PixelPanel.NEO_THEME
	theme_type_variation="PixelPanel"
	custom_minimum_size=Vector2(596,292)
	var column:=VBoxContainer.new();add_child(column)
	var heading:=HBoxContainer.new();column.add_child(heading)
	title=Label.new();title.text="招式表 · F2关闭";title.size_flags_horizontal=Control.SIZE_EXPAND_FILL;heading.add_child(title)
	var roster:=UfeRosterModel.new()
	for entry in roster.entries:
		if UfeRosterModel.implemented(str(entry.id)):fighter_ids.append(str(entry.id))
	var previous:=PixelButton.new("上一位");heading.add_child(previous)
	previous.pressed.connect(func():cycle_fighter(-1))
	fighter_choice=FighterName.new(12,true);fighter_choice.custom_minimum_size.x=136;heading.add_child(fighter_choice)
	var next:=PixelButton.new("下一位");heading.add_child(next)
	next.pressed.connect(func():cycle_fighter(1))
	form_note=RichTextLabel.new();form_note.bbcode_enabled=true;form_note.fit_content=false;form_note.scroll_active=true;form_note.custom_minimum_size.y=28;column.add_child(form_note)
	tabs=PixelTabBar.new();column.add_child(tabs);tabs.set_tabs(TITLES)
	tabs.tab_changed.connect(show_page)
	var headers:=HBoxContainer.new();table_headers=headers;column.add_child(headers)
	for cell in [["输入",132],["招式",220],["起手",40],["攻击",40],["收招",40],["伤害",40]]:
		var label:=Label.new();label.text=cell[0];label.custom_minimum_size.x=cell[1];headers.add_child(label)
	rows.custom_minimum_size.y=72;rows.size_flags_vertical=Control.SIZE_EXPAND_FILL;column.add_child(rows)
	var help:=Label.new();help.text="技能：1P %s / 2P %s；形态：1P %s / 2P %s\n蓄能%s　闪避%s　必杀%s；方向+技能直出，设置可自定义。"%[UfeInputRouter.binding_label(0,"skill"),UfeInputRouter.binding_label(1,"skill"),UfeInputRouter.binding_label(0,"transform"),UfeInputRouter.binding_label(1,"transform"),UfeInputRouter.binding_label(0,"charge"),UfeInputRouter.binding_label(0,"dodge"),UfeInputRouter.binding_label(0,"special")];help.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;column.add_child(help)
static func category(entry: Dictionary) -> int:
	var id:=str(entry.move)
	if id.begins_with("special") or id in ["air_special","battle_transform","super_special3"]:return 7
	if id=="motion_41236":return 5
	if id.begins_with("motion_"):return 6
	if "throw" in id or id=="dash_grab":return 5
	if id.begins_with("chase_"):return 3
	for state in entry.states:
		if "air" in str(state):return 2
	if "crouch" in entry.states and not "idle" in entry.states:return 1
	if id.begins_with("crouch_") or id in ["sweep","slide","low_pulse"]:return 1
	if not "idle" in entry.states and not "light" in id:return 4
	return 0
func set_fighter(data: UfeFighterDefinition, form_id: String="") -> void:
	if UfeBattleFormCatalog.battle_playable(data.id) and not data.moves.has("battle_transform"):
		data = UfeBattleFormCatalog.prepare(data.id,true).definition
	fighter_data=data;entries=data.command_table.duplicate(true)
	# P按现有能量格数选择等级；表中的每个等级读取自己的数据，不用一级数值代表全部必杀。
	for entry in data.command_table:
		if entry.move!="special":continue
		for level in [2,3]:
			var id:="special%d"%level
			if data.moves.has(id):
				var variant: Dictionary=entry.duplicate(true);variant.move=id;entries.append(variant)
		if data.moves.has("super_special3"):
			var super_entry: Dictionary=entry.duplicate(true); super_entry.move="super_special3"; entries.append(super_entry)
	clips=UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%data.id).clips
	if data.moves.has("battle_transform"):
		var form: Dictionary=UfeBattleFormCatalog.registry().get(data.id,{})
		var transform_clips: Dictionary=clips
		if str(form.get("mode",""))=="definition":
			transform_clips=UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%str(form.target)).clips
		clips.battle_transform=transform_clips.get(str(form.get("transform_animation","super_transform")),{})
	fighter_choice.set_fighter(data.id,"","",form_id)
	var notes: PackedStringArray=[]
	var enabled_form: Dictionary=UfeBattleFormCatalog.registry().get(data.id,{})
	for form in UfeFighterDisplay.battle_forms(data.id):
		var identity:=UfeFighterDisplay.resolved_id(data.id,str(form.id))
		var registered_identity:=UfeFighterDisplay.resolved_id(data.id,str(enabled_form.get("id","")))
		var implemented: bool=bool(form.get("implemented",false))
		if not enabled_form.is_empty():implemented=bool(enabled_form.get("enabled",false)) and identity==registered_identity
		var color:=UfeFighterDisplay.name_color(identity).to_html(false)
		notes.append("[color=#"+color+"]"+str(form.name).replace("[","[lb]")+"[/color] · 战斗中切换"+("" if implemented else "（未实装）"))
	if data.moves.has("battle_transform"):
		var suffix: String="宇宙奇迹光线后恢复普通泰罗。" if data.id=="ultraman-taro" else "EX形态持续至本局结束。"
		notes.append("形态键%s（手柄键位见设置，原↓↓+P）：满3格且生命≤一半，本局一次；演出无敌。"%UfeInputRouter.binding_label(0,"transform")+suffix)
	form_note.text="\n".join(notes);form_note.visible=not notes.is_empty()
	show_page(page)
func show_page(index: int) -> void:
	page=index
	for i in range(tabs.tabs.size()):tabs.tabs[i].set_pressed_no_signal(i==index)
	for child in rows.rows.get_children():rows.rows.remove_child(child);child.queue_free()
	if table_headers!=null:table_headers.visible=index!=8
	if index==8:
		var current_shortcuts: String="方向+技能（1P %s / 2P %s）直出原搓招；形态单按%s，方向选已开放形态；手柄键位见设置。原输入和全部原招保留。"%[UfeInputRouter.binding_label(0,"skill"),UfeInputRouter.binding_label(1,"skill"),UfeInputRouter.binding_label(0,"transform")]
		for value in ["能量：用于必杀与标注能量费用的招式；不足时不能释放。", "体力：1000上限的短时攻防韧性。每招按表消耗，体力不足仍可攻击或释放能量技。", "防御会消耗体力，耗尽会破防约0.6秒，结束恢复至350，避免连续空体破防。", "攻击、防御、受击、闪避中暂停恢复；结束后等待0.3秒，移动每秒回720、站蹲600、蓄能180。", "闪避消耗120体力；足额保留12帧无敌，不足仍可闪避、无敌缩为4帧。", current_shortcuts]:
			var explanation:=Label.new();explanation.text=value;explanation.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;explanation.size_flags_horizontal=Control.SIZE_EXPAND_FILL;rows.rows.add_child(explanation)
		return
	for entry in entries:
		if category(entry)!=index:continue
		if bool(entry.get("quick_skill",false)) or bool(entry.get("quick_transform",false)):continue
		var row:=HBoxContainer.new();rows.rows.add_child(row)
		var input:=InputGlyphs.new();input.custom_minimum_size.x=132
		var quick := _quick_entry(entry)
		if not quick.is_empty():
			input.custom_minimum_size.x=0
			var inputs:=VBoxContainer.new();inputs.custom_minimum_size.x=132;row.add_child(inputs)
			var quick_line:=HBoxContainer.new();inputs.add_child(quick_line)
			var quick_label:=Label.new();quick_label.text="快捷";quick_line.add_child(quick_label)
			input.show_input(int(quick.directions[0]),int(quick.buttons),quick.directions,quick.directions.size()>1);quick_line.add_child(input)
			var original:=HBoxContainer.new();inputs.add_child(original)
			var original_label:=Label.new();original_label.text="原";original.add_child(original_label)
			var original_glyph:=InputGlyphs.new();original_glyph.show_input(int(entry.directions[0]),int(entry.buttons),entry.motion,false);original.add_child(original_glyph)
		else:
			input.show_input(int(entry.directions[0]),int(entry.buttons),entry.motion if not entry.motion.is_empty() else entry.directions,entry.motion.is_empty() and entry.directions.size()>1);row.add_child(input)
		var move: Dictionary=fighter_data.moves.get(entry.move,{}) if fighter_data!=null else {}
		var ready: bool=not move.is_empty() and clips.has(entry.move) and not clips[entry.move].is_empty()
		var details:=VBoxContainer.new();details.custom_minimum_size.x=220;row.add_child(details)
		var label:=Label.new();label.text=move_title(entry,move,ready);label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;details.add_child(label)
		var costs:=Label.new();costs.text=move_costs(move) if ready else "费用待实装核验";costs.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;details.add_child(costs)
		for key in ["startup","active","recovery","damage"]:
			var number:=Label.new();number.text=str(int(move.get(key,0))) if ready else "—";number.custom_minimum_size.x=40;row.add_child(number)

static func move_title(entry: Dictionary, move: Dictionary, ready: bool) -> String:
	var move_name:=str(move.get("display_name",entry.get("display_name",entry.get("move","未命名招式"))))
	return move_name if ready else "待制作："+move_name

static func move_costs(move: Dictionary) -> String:
	var energy:=int(move.get("energy_cost",0))
	var energy_text:="0"
	if energy>0:
		energy_text=("%d格"%(energy/1000) if energy%1000==0 else "%d点"%energy)
	return "能量 %s · 体力 %d"%[energy_text,int(move.get("stamina_cost",0))]

func _quick_entry(entry: Dictionary) -> Dictionary:
	for candidate in entries:
		if str(candidate.move)!=str(entry.move):continue
		if bool(candidate.get("quick_skill",false)) or bool(candidate.get("quick_transform",false)):return candidate
	return {}

func cycle_fighter(direction: int) -> void:
	if fighter_ids.is_empty():return
	var index:=fighter_ids.find(fighter_data.id) if fighter_data!=null else 0
	set_fighter(UfeContentDatabase.fighter(str(fighter_ids[posmod(index+direction,fighter_ids.size())]),true))

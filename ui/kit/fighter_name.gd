class_name FighterName
extends MarginContainer
## 所有正式角色名称共用：称号与姓名分别取主题颜色。
var title_label:=Label.new()
var name_label:=Label.new()
var fighter_id: String=""
var line: BoxContainer
var text: String:
	get:return (title_label.text+" "+name_label.text).strip_edges()

func _init(font_size: int=12, stacked: bool=false) -> void:
	theme=PixelPanel.NEO_THEME
	custom_minimum_size.x=1
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	if stacked:
		line = VBoxContainer.new()
	else:
		line = HBoxContainer.new()
	line.add_theme_constant_override("separation",0 if stacked else 4)
	line.mouse_filter=Control.MOUSE_FILTER_IGNORE
	add_child(line)
	title_label.theme_type_variation="FighterTitle"
	title_label.add_theme_font_size_override("font_size",maxi(10,font_size-2))
	title_label.mouse_filter=Control.MOUSE_FILTER_IGNORE
	name_label.theme_type_variation="FighterName"
	name_label.add_theme_font_size_override("font_size",font_size)
	name_label.mouse_filter=Control.MOUSE_FILTER_IGNORE
	name_label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	line.add_child(title_label)
	line.add_child(name_label)

func set_fighter(id: String, prefix: String="", suffix: String="", form_id: String="") -> void:
	id=UfeFighterDisplay.resolved_id(id,form_id)
	if fighter_id==id and name_label.get_meta("prefix","")==prefix and name_label.get_meta("suffix","")==suffix:return
	var data:=UfeFighterDisplay.entry(id)
	set_name_and_title(prefix+str(data.name)+suffix,UfeFighterDisplay.title(id),id)
	name_label.set_meta("prefix",prefix)
	name_label.set_meta("suffix",suffix)
	tooltip_text=UfeFighterDisplay.full_name(id)

func set_name_and_title(display_name: String, display_title: String, identity_id: String="") -> void:
	fighter_id=identity_id
	name_label.theme_type_variation=UfeFighterDisplay.name_variation(identity_id)
	title_label.text=UfeDisplayText.text(display_title)
	title_label.visible=not title_label.text.is_empty()
	name_label.text=UfeDisplayText.text(display_name)
	var font:=name_label.get_theme_font("font")
	var width:=font.get_string_size(name_label.text,HORIZONTAL_ALIGNMENT_LEFT,-1,name_label.get_theme_font_size("font_size")).x
	name_label.custom_minimum_size.x=minf(width,160.0)
	tooltip_text=(title_label.text+" "+name_label.text).strip_edges()

func align_right(value: bool) -> void:
	line.alignment=BoxContainer.ALIGNMENT_END if value else BoxContainer.ALIGNMENT_BEGIN
	name_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_RIGHT if value else HORIZONTAL_ALIGNMENT_LEFT
	title_label.horizontal_alignment=name_label.horizontal_alignment

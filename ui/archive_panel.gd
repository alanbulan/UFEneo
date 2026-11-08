class_name UfeArchivePanel
extends VBoxContainer
## 全名册分页图鉴；主UI640×360，静态展示不改变战斗开放状态。
var catalog := UfeCatalogueDisplayCatalog.new()
var fighters: Array = []
var filtered: Array = []
var category := ""
var selected_id := "ultraman"
var page := 0
var pages := 1
var list_scroll := ScrollContainer.new()
var list := VBoxContainer.new()
var art := PixelCatalogueArt.new()
var heading := FighterName.new(16, true)
var description := Label.new()
var description_scroll := ScrollContainer.new()
var empty := Label.new()
var category_tabs := PixelTabBar.new()
var search := LineEdit.new()
var page_label := Label.new()
var previous := PixelButton.new("上页")
var next := PixelButton.new("下页")
var category_choice := PixelChoice.new()
var info_button := PixelButton.new("资料")
var expand_button := PixelButton.new("展开")
var toolbar := HBoxContainer.new()
var description_panel := PixelPanel.new()
var forms_scroll := ScrollContainer.new()
var info_mode := false
var expanded := false
var form_links := HFlowContainer.new()
var buttons: Array = []

func _ready() -> void:
	theme = PixelPanel.NEO_THEME
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_theme_constant_override("separation", 2)
	add_child(toolbar)
	search.placeholder_text = "搜索角色或形态"
	search.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	search.custom_minimum_size.x = 80
	toolbar.add_child(search)
	category_choice.custom_minimum_size.x = 92
	for category_name in ["全部", "奥特战士", "怪兽宇宙人", "黑暗巨人", "形态", "剧情人物"]: category_choice.add_item(category_name)
	toolbar.add_child(category_choice)
	category_choice.item_selected.connect(_category_changed)
	toolbar.add_child(previous); toolbar.add_child(page_label); toolbar.add_child(next)
	previous.pressed.connect(func(): page -= 1; filter_characters(false))
	next.pressed.connect(func(): page += 1; filter_characters(false))
	search.text_changed.connect(func(_text): page = 0; filter_characters(false))
	category_tabs.set_tabs(["全部", "奥特战士", "怪兽与宇宙人", "黑暗巨人", "形态", "剧情人物"])
	toolbar.add_child(category_tabs); category_tabs.hide()
	category_tabs.tab_changed.connect(_category_changed)
	var row := HBoxContainer.new()
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_child(row)
	list_scroll.custom_minimum_size.x = 148
	list_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	list_scroll.follow_focus = true
	list_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.add_child(list_scroll)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list_scroll.add_child(list)
	var detail := VBoxContainer.new()
	detail.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(detail)
	detail.add_theme_constant_override("separation", 2)
	var heading_row := HBoxContainer.new()
	detail.add_child(heading_row)
	heading.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	heading_row.add_child(heading)
	heading_row.add_child(info_button); heading_row.add_child(expand_button)
	info_button.pressed.connect(func(): set_info_mode(not info_mode))
	expand_button.pressed.connect(func(): set_expanded(not expanded))
	detail.add_child(art)
	forms_scroll.custom_minimum_size.y = 28
	forms_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	detail.add_child(forms_scroll)
	form_links.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	forms_scroll.add_child(form_links)
	description_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	detail.add_child(description_panel)
	description_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	description_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	description_panel.add_child(description_scroll)
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	description.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	description.custom_minimum_size.x = 1
	description_scroll.add_child(description)
	empty.text = "没有匹配的角色。"
	detail.add_child(empty)
	set_info_mode(false)
	filter_characters()

func _category_changed(index: int) -> void:
	category = ["", "hero", "kaiju", "dark_ultra", "form", "story"][index]
	category_choice.select(index)
	page = 0
	filter_characters(false)

func set_info_mode(value: bool) -> void:
	info_mode = value
	art.visible = not value
	description_panel.visible = value
	info_button.text = "形象" if value else "资料"
	expand_button.visible = not value

func set_expanded(value: bool) -> void:
	expanded = value
	toolbar.visible = not value
	list_scroll.visible = not value
	forms_scroll.visible = not value
	expand_button.text = "收起" if value else "展开"
	set_info_mode(false)

func filter_characters(keep_selected: bool = true) -> void:
	if keep_selected:
		var location := catalog.page_for_id(selected_id, search.text, category)
		if location >= 0: page = location
	var result := catalog.query_page(search.text, category, page)
	page = int(result.page); pages = int(result.pages)
	filtered = result.rows; fighters = filtered
	page_label.text = "%d/%d · %d" % [page + 1, pages, int(result.total)]
	previous.disabled = page == 0; next.disabled = page >= pages - 1
	for child in list.get_children(): list.remove_child(child); child.queue_free()
	buttons.clear()
	for data in filtered:
		var id := str(data.id)
		var button := PixelButton.new("")
		button.toggle_mode = true
		button.custom_minimum_size = Vector2(140, 28)
		button.tooltip_text = str(data.name)
		list.add_child(button)
		var margin := MarginContainer.new()
		margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
		for side in ["left", "right", "top", "bottom"]: margin.add_theme_constant_override("margin_" + side, 5)
		button.add_child(margin)
		var label := Label.new()
		label.text = str(data.name)
		label.theme_type_variation = UfeFighterDisplay.name_variation(id)
		label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		margin.add_child(label)
		button.pressed.connect(func(): show_character(id))
		button.set_meta("fighter_id", id)
		buttons.append(button)
	empty.visible = filtered.is_empty()
	heading.visible = not filtered.is_empty()
	if not filtered.is_empty():
		if not filtered.any(func(data): return str(data.id) == catalog.canonical_id(selected_id)): selected_id = str(filtered[0].id)
		show_character(selected_id)

func jump_to(id: String) -> void:
	id = catalog.canonical_id(id)
	if catalog.row_for(id).is_empty(): return
	search.set_block_signals(true); search.text = ""; search.set_block_signals(false)
	category = ""
	category_choice.select(0)
	category_tabs.tabs[0].set_pressed_no_signal(true)
	page = maxi(0, catalog.page_for_id(id, "", ""))
	selected_id = id
	filter_characters()

func show_character(id: String) -> void:
	id = catalog.canonical_id(id)
	var row := catalog.row_for(id)
	if row.is_empty(): return
	selected_id = id
	var profile := catalog.profile_for(id)
	heading.set_name_and_title(str(row.name), catalog.title_for(id), id)
	art.set_display(catalog.display_for(id))
	var detail := catalog.detail_for(id)
	var works := UfeDisplayText.text(catalog.roster.work_names(row))
	var text := "作品：" + (works if not works.is_empty() else "待核实")
	text += "\n\n" + str(profile.get("text", "角色详细资料正在整理。"))
	if not profile.has("facts") and not text.contains("身高") and not text.contains("体重"): text += "\n\n身高、体重：资料待核实。"
	text += catalog.source_lines(profile)
	text += catalog.title_source_lines(profile)
	if not str(detail.get("official_url", "")).is_empty(): text += "\n官方页面：" + str(detail.official_url)
	description.text = text
	description_scroll.scroll_vertical = 0
	for child in form_links.get_children(): form_links.remove_child(child); child.queue_free()
	for form in catalog.forms_for(id):
		var caption := str(form.relation) + "：" + str(form.name)
		var button := PixelButton.new(caption.left(14) + ("…" if caption.length() > 14 else ""))
		button.tooltip_text = str(form.name)
		form_links.add_child(button)
		var target := str(form.id)
		button.caption.add_theme_color_override("font_color", UfeFighterDisplay.name_color(target))
		button.pressed.connect(func(): jump_to(target))
	for button in buttons: button.set_pressed_no_signal(str(button.get_meta("fighter_id")) == id)

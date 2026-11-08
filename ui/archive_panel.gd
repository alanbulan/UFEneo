class_name UfeArchivePanel
extends VBoxContainer
## 全名册分页图鉴；主 UI 固定 640×360，静态展示不改变战斗开放状态。
##
## 布局约束（用户要求）：整页必须收在固定边框里，底部边框不能掉出画面，
## 任何位置都不出现滚动条。因此：
## - 左边列表按页装下，翻页而不是滚动；
## - 右边形象按 384×256 原生画布 1 倍显示，外框刚好包住画布；
## - 资料改成分页文本，同样不用滚动条。
signal back_requested
var catalog := UfeCatalogueDisplayCatalog.new()
var fighters: Array = []
var filtered: Array = []
var category := ""
var selected_id := "ultraman"
var page := 0
var pages := 1
var list := VBoxContainer.new()
var art := PixelCatalogueArt.new()
## 称号 + 主体名称两行显示，形态接在名字后面，三项分开取色。
var heading := FighterName.new(13, true)
var empty := Label.new()
var category_tabs := PixelTabBar.new()
var search := LineEdit.new()
var page_label := Label.new()
var previous := PixelButton.new("上页")
var next := PixelButton.new("下页")
var back := PixelButton.new("返回")
var category_choice := PixelChoice.new()
var info_button := PixelButton.new("资料")
var toolbar := HBoxContainer.new()
var description_panel := PixelPanel.new()
var art_center := CenterContainer.new()
var pager := PixelTextPager.new()
var info_mode := false
var buttons: Array = []
## 图鉴试听：有本人声音的角色放自己的登场声，其余用像素界面提示音。
var voice := AudioStreamPlayer.new()
var last_sound_ms := -100000

func _ready() -> void:
	theme = PixelPanel.NEO_THEME
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_theme_constant_override("separation", 2)
	voice.volume_db = PixelCatalogueSound.PICK_VOLUME_DB
	add_child(voice)
	_build_toolbar()
	var row := HBoxContainer.new()
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.add_theme_constant_override("separation", 6)
	add_child(row)
	_build_list(row)
	_build_detail(row)
	set_info_mode(false)
	filter_characters()

func _build_toolbar() -> void:
	# 顶栏分两行：第一行页面名与返回各占一角，第二行搜索与翻页，
	# 左上角不再挤成一团。
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 4)
	add_child(header)
	var page_title := Label.new()
	page_title.text = "角色图鉴"
	page_title.theme_type_variation = "FighterName"
	page_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	page_title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	header.add_child(page_title)
	back.custom_minimum_size = Vector2(56, 24)
	header.add_child(back)
	back.pressed.connect(func(): back_requested.emit())
	add_child(toolbar)
	toolbar.add_theme_constant_override("separation", 4)
	search.placeholder_text = "搜索角色或形态"
	search.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	search.custom_minimum_size = Vector2(80, 24)
	toolbar.add_child(search)
	category_choice.custom_minimum_size = Vector2(88, 24)
	for category_name in ["全部", "奥特战士", "怪兽宇宙人", "黑暗巨人", "形态", "剧情人物"]: category_choice.add_item(category_name)
	toolbar.add_child(category_choice)
	category_choice.item_selected.connect(_category_changed)
	for button in [previous, next]: button.custom_minimum_size.y = 24
	toolbar.add_child(previous); toolbar.add_child(page_label); toolbar.add_child(next)
	page_label.add_theme_font_size_override("font_size", 11)
	previous.pressed.connect(func(): page -= 1; filter_characters(false))
	next.pressed.connect(func(): page += 1; filter_characters(false))
	search.text_changed.connect(func(_text): page = 0; filter_characters(false))
	category_tabs.set_tabs(["全部", "奥特战士", "怪兽与宇宙人", "黑暗巨人", "形态", "剧情人物"])
	category_tabs.hide()
	# 必须挂进树里：未入树的节点不会随面板释放，会带着主题纹理一起泄漏。
	toolbar.add_child(category_tabs)
	category_tabs.tab_changed.connect(_category_changed)

func _build_list(row: HBoxContainer) -> void:
	# 列表自带底板，超长名字不会和右侧形象混在一起。
	var list_panel := PixelPanel.new()
	list_panel.custom_minimum_size.x = 150
	list_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.add_child(list_panel)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	list.add_theme_constant_override("separation", 2)
	list_panel.add_child(list)

func _build_detail(row: HBoxContainer) -> void:
	var detail := VBoxContainer.new()
	detail.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	detail.size_flags_vertical = Control.SIZE_EXPAND_FILL
	detail.add_theme_constant_override("separation", 2)
	row.add_child(detail)
	var heading_row := HBoxContainer.new()
	heading_row.add_theme_constant_override("separation", 2)
	detail.add_child(heading_row)
	heading.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	heading_row.add_child(heading)
	info_button.custom_minimum_size = Vector2(52, 24)
	info_button.pressed.connect(func(): set_info_mode(not info_mode))
	heading_row.add_child(info_button)
	# 形象区透明：用户要求人物背后不要纯蓝色块，直接透出页面背景。
	art_center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	art_center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	detail.add_child(art_center)
	art_center.add_child(art)
	description_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	detail.add_child(description_panel)
	pager.size_flags_vertical = Control.SIZE_EXPAND_FILL
	description_panel.add_child(pager)
	empty.text = "没有匹配的角色。"
	detail.add_child(empty)

func _category_changed(index: int) -> void:
	category = ["", "hero", "kaiju", "dark_ultra", "form", "story"][index]
	category_choice.select(index)
	page = 0
	filter_characters(false)

func set_info_mode(value: bool) -> void:
	# 形象页与资料页互斥：形象页要把整张 384×256 画布按 1 倍完好放出，
	# 不跟长资料抢高度；资料页才显示分页文本。
	info_mode = value
	art_center.visible = not value
	description_panel.visible = value
	info_button.text = "形象" if value else "资料"

func set_expanded(value: bool) -> void:
	# 展开只隐藏搜索行，列表与形象始终保持在固定框内。
	toolbar.visible = not value
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
		button.custom_minimum_size = Vector2(138, 22)
		# 行高随面板等分：每页装 10 条时把列表底板填满，底部不留空白。
		button.size_flags_vertical = Control.SIZE_EXPAND_FILL
		button.tooltip_text = str(data.get("display_name", data.name))
		list.add_child(button)
		var margin := MarginContainer.new()
		margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
		for side in ["left", "right", "top", "bottom"]: margin.add_theme_constant_override("margin_" + side, 4)
		button.add_child(margin)
		var label := Label.new()
		# 列表显示主体名 + 形态，避免同一角色的多个形态在列表里长得一样。
		label.text = str(data.get("display_name", data.name))
		label.theme_type_variation = UfeFighterDisplay.name_variation(id)
		label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		margin.add_child(label)
		button.pressed.connect(func(): _select(id))
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
	_play_entry_sound(id)
	search.set_block_signals(true); search.text = ""; search.set_block_signals(false)
	category = ""
	category_choice.select(0)
	category_tabs.tabs[0].set_pressed_no_signal(true)
	page = maxi(0, catalog.page_for_id(id, "", ""))
	selected_id = id
	filter_characters()

func sound_for(id: String) -> Dictionary:
	"""该条目该放什么声：有本人登场声就用它，否则用像素界面提示音。"""
	var row := catalog.row_for(id)
	var base := ""
	if not row.is_empty():
		base = str(row.get("base_character", ""))
	return PixelCatalogueSound.for_entry(catalog.canonical_id(id), base)

func _play_entry_sound(id: String) -> void:
	var now := Time.get_ticks_msec()
	# 连续翻列表时只留最后一声，避免叠成噪音。
	if now - last_sound_ms < 260: return
	last_sound_ms = now
	var picked := sound_for(id)
	var path := str(picked.path)
	if not ResourceLoader.exists(path): return
	voice.stream = load(path)
	voice.volume_db = float(picked.volume_db)
	voice.play()

func _plain(text: String) -> String:
	"""去掉来源类行，只留人物介绍。"""
	var kept: Array[String] = []
	for line in text.split("\n"):
		var bare := line.strip_edges()
		if bare.begins_with("来源") or bare.begins_with("许可") or bare.begins_with("官方页面") \
				or bare.begins_with("称号性质") or bare.begins_with("称号来源") or bare.begins_with("http"):
			continue
		kept.append(line)
	return "\n".join(kept).strip_edges()

func _select(id: String) -> void:
	_play_entry_sound(id)
	show_character(id)

func show_character(id: String) -> void:
	id = catalog.canonical_id(id)
	var row := catalog.row_for(id)
	if row.is_empty(): return
	selected_id = id
	var profile := catalog.profile_for(id)
	heading.set_name_and_title(str(row.name), catalog.title_for(id), id, str(row.get("form", "")))
	art.set_display(catalog.display_for(id))
	var works := UfeDisplayText.text(catalog.roster.work_names(row))
	var text := "作品：" + (works if not works.is_empty() else "待核实")
	text += "\n\n" + str(profile.get("text", "角色详细资料正在整理。"))
	if not profile.has("facts") and not text.contains("身高") and not text.contains("体重"): text += "\n\n身高、体重：资料待核实。"
	# 用户要求资料页只留介绍：来源、链接、维基、称号性质一律不展示。
	pager.set_text(_plain(text))
	for button in buttons: button.set_pressed_no_signal(str(button.get_meta("fighter_id")) == id)

class_name PixelTextPager
extends VBoxContainer
## 分页文本：图鉴资料不再用滚动条，超长文字按页翻。
## 用户要求界面里不要出现滚动条，所以这里用页码 + 上/下页代替滚动。
signal page_changed(page: int, pages: int)
const CHARS_PER_PAGE := 300
var label := Label.new()
var bar := HBoxContainer.new()
var previous := PixelButton.new("上页")
var next := PixelButton.new("下页")
var counter := Label.new()
var pages: Array[String] = []
var page := 0
var source := ""

func _ready() -> void:
	theme = PixelPanel.NEO_THEME
	add_theme_constant_override("separation", 1)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	label.custom_minimum_size = Vector2(1, 1)
	add_child(label)
	bar.add_theme_constant_override("separation", 2)
	add_child(bar)
	previous.pressed.connect(func(): _go(page - 1))
	next.pressed.connect(func(): _go(page + 1))
	counter.add_theme_font_size_override("font_size", 10)
	counter.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	counter.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	bar.add_child(previous)
	bar.add_child(counter)
	bar.add_child(next)
	_refresh()

func set_text(value: String) -> void:
	source = value
	_paginate()
	page = 0
	_refresh()
	label.text = pages[0] if not pages.is_empty() else ""

func page_text(value: int) -> String:
	return pages[clampi(value, 0, maxi(0, pages.size() - 1))] if not pages.is_empty() else ""

func _paginate() -> void:
	pages.clear()
	if source.strip_edges().is_empty():
		return
	var current := ""
	for block in source.split("\n"):
		if current.length() + block.length() + 1 > CHARS_PER_PAGE and not current.is_empty():
			pages.append(current.strip_edges())
			current = ""
		current += block + "\n"
	if not current.strip_edges().is_empty():
		pages.append(current.strip_edges())

func _go(value: int) -> void:
	page = clampi(value, 0, maxi(0, pages.size() - 1))
	label.text = page_text(page)
	_refresh()
	page_changed.emit(page, pages.size())

func _refresh() -> void:
	var total := maxi(1, pages.size())
	previous.disabled = page <= 0
	next.disabled = page >= total - 1
	counter.text = "%d/%d" % [page + 1, total]
	bar.visible = pages.size() > 1

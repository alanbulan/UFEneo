class_name RosterGrid
extends ScrollContainer
signal picked(index: int)
const COLS=10
const ROW_HEIGHT=36
var model: UfeRosterModel
var cursors: Array=[0,1]
var selected_ids: Array=["ultraman","zetton"]
var column:=VBoxContainer.new()
var before:=Control.new()
var grid:=GridContainer.new()
var after:=Control.new()
var first_row: int=-1
var loaded_cells: int=0
var cells: Array=[]
var pictures: Array=[]
var markers: Array=[]
func _init() -> void:
	theme=PixelPanel.NEO_THEME
	horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED
	custom_minimum_size=Vector2(0,80)
	clip_contents=true
	size_flags_vertical=Control.SIZE_EXPAND_FILL
	column.add_theme_constant_override("separation",0)
	column.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	add_child(column)
	column.add_child(before)
	grid.columns=COLS
	grid.add_theme_constant_override("h_separation",2)
	grid.add_theme_constant_override("v_separation",2)
	column.add_child(grid)
	column.add_child(after)
func bind(value: UfeRosterModel) -> void:
	model=value
	first_row=-1
	scroll_vertical=0
	refresh()
func _process(_delta: float) -> void:
	@warning_ignore("integer_division")
	if model!=null and first_row!=scroll_vertical/ROW_HEIGHT:refresh()
func make_cell() -> void:
	var cell:=PixelButton.new()
	cell.custom_minimum_size=Vector2(56,34)
	cell.clip_contents=true
	grid.add_child(cell)
	var picture:=PixelArt.new("",Vector2(32,26))
	cell.add_child(picture)
	picture.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var cursors_for_cell: Array=[]
	for player in range(2):
		var cursor:=SelectCursor.new(player)
		cell.add_child(cursor)
		cursor.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		var tag:=Label.new()
		tag.text=str(player+1)+"P"
		tag.theme_type_variation="PlayerOneLabel" if player==0 else "PlayerTwoLabel"
		tag.mouse_filter=Control.MOUSE_FILTER_IGNORE
		cursor.add_child(tag)
		tag.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT if player==0 else Control.PRESET_TOP_RIGHT)
		cursors_for_cell.append(cursor)
	cell.pressed.connect(func():picked.emit(int(cell.get_meta("index"))))
	cell.mouse_entered.connect(func():
		if PixelChoice.allows_hover_selection():picked.emit(int(cell.get_meta("index"))))
	cells.append(cell)
	pictures.append(picture)
	markers.append(cursors_for_cell)
func refresh() -> void:
	var total:=ceili(model.filtered.size()/float(COLS))
	@warning_ignore("integer_division")
	first_row=clampi(scroll_vertical/ROW_HEIGHT,0,maxi(0,total-1))
	var count:=mini(maxi(0,total-first_row),ceili(maxf(size.y,80)/ROW_HEIGHT)+1)
	before.custom_minimum_size.y=first_row*ROW_HEIGHT
	after.custom_minimum_size.y=maxi(0,total-first_row-count)*ROW_HEIGHT
	var start:=first_row*COLS
	var end:=mini(model.filtered.size(),(first_row+count)*COLS)
	UfeFighterDisplay.warm_visible(model.filtered.slice(start,end))
	loaded_cells=end-start
	while cells.size()<loaded_cells:make_cell()
	for slot in range(cells.size()):
		var cell: PixelButton=cells[slot]
		cell.visible=slot<loaded_cells
		if slot>=loaded_cells:continue
		var index:=start+slot
		var entry: Dictionary=model.filtered[index]
		cell.set_meta("index",index)
		cell.set_meta("fighter_id",str(entry.id))
		cell.tooltip_text=UfeFighterDisplay.full_name(str(entry.id))+("" if UfeRosterModel.implemented(str(entry.id)) else " · 未实装")
		pictures[slot].texture=UfeFighterDisplay.portrait(str(entry.id))
	update_selection()
func update_selection() -> void:
	for slot in range(loaded_cells):
		var id:=str(cells[slot].get_meta("fighter_id"))
		for player in range(2):markers[slot][player].visible=id==selected_ids[player]
func reveal(index: int) -> void:
	@warning_ignore("integer_division")
	var row:=index/COLS
	if row*ROW_HEIGHT<scroll_vertical:scroll_vertical=row*ROW_HEIGHT
	elif (row+1)*ROW_HEIGHT>scroll_vertical+size.y:scroll_vertical=(row+1)*ROW_HEIGHT-int(size.y)
	@warning_ignore("integer_division")
	if first_row!=scroll_vertical/ROW_HEIGHT:refresh()
	else:update_selection()

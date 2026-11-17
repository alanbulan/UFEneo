class_name PixelTextBounds
extends RefCounted
## 九宫格边框是不可放文字的区域；同时覆盖常态、悬停、按下、选中。
static func insets(button: Button) -> Vector4:
	var result:=Vector4.ZERO
	for state in ["normal","hover","pressed","disabled","focus"]:
		var box:=button.get_theme_stylebox(state)
		if not box is StyleBoxTexture:continue
		result.x=maxf(result.x,maxf(box.texture_margin_left,box.content_margin_left))
		result.y=maxf(result.y,maxf(box.texture_margin_top,box.content_margin_top))
		result.z=maxf(result.z,maxf(box.texture_margin_right,box.content_margin_right))
		result.w=maxf(result.w,maxf(box.texture_margin_bottom,box.content_margin_bottom))
	return result

static func layout(button: Button, caption: Label) -> void:
	var margin:=insets(button)
	# 2px描边也必须在内容区内。下拉箭头另留空间，不能覆盖末字。
	caption.offset_left=margin.x+2
	caption.offset_right=-margin.z-2-(12 if button is OptionButton else 0)
	caption.offset_top=margin.y+2
	caption.offset_bottom=-margin.w-2

static func violations(button: Button, caption: Label) -> Array[String]:
	var errors: Array[String]=[]
	if caption==null or caption.text.is_empty():return errors
	var margin:=insets(button)
	var safe:=Rect2(button.global_position+Vector2(margin.x,margin.y),button.size-Vector2(margin.x+margin.z,margin.y+margin.w))
	var text_rect:=caption.get_global_rect().grow(2)
	if not safe.encloses(text_rect):errors.append("文字矩形与九宫格边框重叠："+caption.text)
	if caption.get_minimum_size().y>caption.size.y+0.1:errors.append("文字高度超出内容区："+caption.text)
	return errors

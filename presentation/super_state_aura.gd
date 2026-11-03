class_name UfeSuperStateAura
extends RefCounted
## 只裁已有GPT火焰纹理。BitMap在本机缓存当前整帧Alpha外缘，绝不生成描边或补色。
var body_cache: Dictionary = {}
var aura_cache: Dictionary = {}
var fields: Array[Image] = []
var valid_pixels: Array = []
var anchor := Vector2i(128,248)

func _init(clip: Dictionary) -> void:
	anchor = Vector2i(int(clip.anchor[0]), int(clip.anchor[1]))
	var image: Image = load(str(clip.texture)).get_image()
	if image.is_compressed(): image.decompress()
	for r in clip.rects:
		var field := image.get_region(Rect2i(int(r[0]),int(r[1]),int(r[2]),int(r[3])))
		fields.append(field)
		var pixels: Array[Vector2i] = []
		for y in range(field.get_height()):
			for x in range(field.get_width()):
				if field.get_pixel(x,y).a > 0: pixels.append(Vector2i(x,y))
		valid_pixels.append(pixels)

func body_masks(sprite: Sprite2D, key: String) -> Array:
	if body_cache.has(key): return body_cache[key]
	var image: Image = sprite.texture.get_image()
	if image.is_compressed(): image.decompress()
	var body := Image.create(fields[0].get_width(), fields[0].get_height(), false, Image.FORMAT_RGBA8)
	var region := Rect2i(sprite.region_rect) if sprite.region_enabled else Rect2i(Vector2i.ZERO,image.get_size())
	body.blit_rect(image, region, Vector2i(sprite.offset) + anchor)
	var mask := BitMap.new()
	mask.create_from_image_alpha(body, 0.1)
	var one := dilate(body,1)
	var three := dilate(body,3)
	body_cache[key] = [mask,one,three]
	return body_cache[key]

func dilate(body: Image, radius: int) -> BitMap:
	# 原生Image合成只用于Alpha集合并集，方形邻域与离线DIST_C逐像素一致。
	var expanded := Image.create(body.get_width(),body.get_height(),false,Image.FORMAT_RGBA8)
	for dy in range(-radius,radius+1):
		for dx in range(-radius,radius+1): expanded.blend_rect(body,Rect2i(Vector2i.ZERO,body.get_size()),Vector2i(dx,dy))
	var mask := BitMap.new(); mask.create_from_image_alpha(expanded,0.1)
	return mask

func texture_for(sprite: Sprite2D, phase: int) -> Texture2D:
	var key := sprite.texture.resource_path + str(sprite.region_rect) + str(sprite.offset)
	var cache_key := key + ":" + str(phase)
	if aura_cache.has(cache_key): return aura_cache[cache_key]
	var masks := body_masks(sprite,key)
	var body: BitMap = masks[0]; var one: BitMap = masks[1]; var three: BitMap = masks[2]
	var size := fields[phase].get_size()
	var core := BitMap.new(); core.create(size)
	var candidates := BitMap.new(); candidates.create(size)
	var bright := BitMap.new(); bright.create(size)
	for pos in valid_pixels[phase]:
		if body.get_bitv(pos): continue
		var color := fields[phase].get_pixelv(pos)
		var gold := color.r8>=235 and color.g8>=205 and color.b8>=120
		bright.set_bitv(pos,gold)
		if three.get_bitv(pos) and (not one.get_bitv(pos) or gold): core.set_bitv(pos,true)
		for dy in range(1,13):
			if pos.y+dy<size.y and body.get_bit(pos.x,pos.y+dy):
				candidates.set_bitv(pos,true)
				break
	var seen := BitMap.new(); seen.create(size)
	var tongues := BitMap.new(); tongues.create(size)
	for pos in valid_pixels[phase]:
		if not candidates.get_bitv(pos) or seen.get_bitv(pos): continue
		var queue: Array[Vector2i] = [pos]
		seen.set_bitv(pos,true)
		var cursor := 0
		var low: Vector2i = pos; var high: Vector2i = pos
		var root_y := -1; var outer_y := size.y
		while cursor < queue.size():
			var at := queue[cursor]; cursor += 1
			low = Vector2i(mini(low.x,at.x),mini(low.y,at.y))
			high = Vector2i(maxi(high.x,at.x),maxi(high.y,at.y))
			if core.get_bitv(at): root_y = maxi(root_y,at.y)
			if not three.get_bitv(at): outer_y = mini(outer_y,at.y)
			for dy in range(-1,2):
				for dx in range(-1,2):
					var next := at+Vector2i(dx,dy)
					if next.x<0 or next.y<0 or next.x>=size.x or next.y>=size.y: continue
					if candidates.get_bitv(next) and not seen.get_bitv(next):
						seen.set_bitv(next,true); queue.append(next)
		var height := high.y-low.y+1; var width := high.x-low.x+1
		if height>=5 and height*10>=width*12 and root_y>=0 and outer_y<root_y-3:
			for at in queue: tongues.set_bitv(at,true)
	var result := Image.create(size.x,size.y,false,Image.FORMAT_RGBA8)
	for pos in valid_pixels[phase]:
		if (core.get_bitv(pos) or tongues.get_bitv(pos)) and (not one.get_bitv(pos) or bright.get_bitv(pos)):
			result.set_pixelv(pos,fields[phase].get_pixelv(pos))
	var texture := ImageTexture.create_from_image(result)
	aura_cache[cache_key] = texture
	return texture

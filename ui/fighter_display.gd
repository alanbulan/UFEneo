class_name UfeFighterDisplay
extends RefCounted
## 界面元数据和纹理缓存；不读写战斗模拟。
static var entries: Dictionary={}
static var portraits: Dictionary={}
static var models: Dictionary={}
static var profiles: Dictionary={}
static var form_entries: Dictionary={}
static var unlisted_form_displays: Dictionary={}
static var identity_displays: Dictionary={}

static func identity_id(id: String) -> String:
	if identity_displays.is_empty():identity_displays=UfeContentDatabase.read_json("res://content/roster/identity_display.json")
	var aliases: Dictionary=identity_displays.get("aliases",{})
	var visited: Dictionary={}
	while aliases.has(id) and not visited.has(id):
		visited[id]=true
		id=str(aliases[id])
	return id

static func identity_entry(id: String) -> Dictionary:
	var canonical:=identity_id(id)
	return identity_displays.get("entries",{}).get(canonical,{})

static func resolved_id(id: String, form_id: String="") -> String:
	if form_id.is_empty() or form_id=="default":return identity_id(id)
	if not identity_entry(form_id).is_empty():return identity_id(form_id)
	var combined:=id+"__"+form_id
	return combined if not identity_entry(combined).is_empty() else identity_id(id)

static func name_variation(id: String) -> String:
	return str(identity_entry(id).get("name_variation","FighterName"))

static func name_color(id: String) -> Color:
	return PixelPanel.NEO_THEME.get_color("font_color",name_variation(id))

static func portrait_material(id: String) -> ShaderMaterial:
	if str(identity_entry(id).get("palette_state",""))!="super-taro":return null
	# 复用本作已装超级状态的整图色板；每个头像实例持自己的材质。
	var config: Dictionary=UfeContentDatabase.read_json("res://content/fighters/ultraman-taro/super_state.json")
	var material:=ShaderMaterial.new()
	material.shader=preload("res://presentation/super_state_palette.gdshader")
	var sources:=PackedVector3Array()
	var targets:=PackedVector3Array()
	for mapping in config.palette_mapping:
		sources.append(Vector3(float(mapping.source[0]),float(mapping.source[1]),float(mapping.source[2]))/255.0)
		targets.append(Vector3(float(mapping.target[0]),float(mapping.target[1]),float(mapping.target[2]))/255.0)
	var count:=sources.size()
	while sources.size()<32:sources.append(Vector3.ZERO);targets.append(Vector3.ZERO)
	material.set_shader_parameter("mapping_count",count)
	material.set_shader_parameter("palette_sources",sources)
	material.set_shader_parameter("palette_targets",targets)
	return material

static func entry(id: String) -> Dictionary:
	if entries.is_empty():
		var catalog: Dictionary=UfeContentDatabase.read_json("res://content/roster/catalog.json")
		for row in catalog.entries:entries[str(row.id)]=row.duplicate(true)
		var selection: Dictionary=UfeContentDatabase.read_json("res://content/roster/selection.json")
		for row in selection.entries:
			var merged: Dictionary=entries.get(str(row.id),{}).duplicate(true)
			merged.merge(row,true)
			entries[str(row.id)]=merged
	var result: Dictionary=entries.get(id,{}).duplicate(true)
	if result.is_empty():result=_unlisted_battle_form(id).duplicate(true)
	if result.is_empty():result={"id":id,"name":id,"title":""}
	result.merge(identity_entry(id),true)
	return result

static func full_name(id: String) -> String:
	var data:=entry(id)
	var form:=str(data.get("form","")).strip_edges()
	return (title(id)+" "+str(data.name)+(" · "+form if not form.is_empty() else "")).strip_edges()

static func title(id: String) -> String:
	var identity:=identity_entry(id)
	if identity.has("title"):return str(identity.title)
	var approved:=str(profile(id).get("title",""))
	if not approved.is_empty():return approved
	var data:=entry(id)
	var recorded:=str(data.get("title",""))
	if not recorded.is_empty():return recorded
	# 没有可靠独有称号时只显示已知分类徽记，不编造民间绰号。
	return {"ultra":"奥特战士","kaiju":"怪兽","alien":"宇宙人"}.get(str(data.get("selection_category","")),"")

static func portrait(id: String) -> Texture2D:
	if not portraits.has(id):
		var data:=entry(id)
		var path:=str(data.get("hud_portrait",""))
		var key:="portrait_"+id.replace("-","_")
		if not path.is_empty() and ResourceLoader.exists(path):
			portraits[id]=load(path)
		elif PixelPanel.NEO_THEME.has_icon(key,"NeoKit"):
			portraits[id]=PixelPanel.NEO_THEME.get_icon(key,"NeoKit")
		else:
			portraits[id]=PixelPanel.NEO_THEME.get_icon("locked","NeoKit")
	return portraits[id]

static func _unlisted_battle_form(id: String) -> Dictionary:
	if not unlisted_form_displays.has(id):
		unlisted_form_displays[id]={}
		var path:="res://content/fighters/%s/definition.json"%id
		if not FileAccess.file_exists(path):return {}
		var definition:Dictionary=UfeContentDatabase.read_json(path)
		if str(definition.get("form_of","")).is_empty() or str(definition.get("switch",""))!="battle":return {}
		var display:Dictionary={}
		var display_path:="res://content/fighters/%s/training_display.json"%id
		if FileAccess.file_exists(display_path):display=UfeContentDatabase.read_json(display_path)
		var candidates:Array=[str(display.get("hud_portrait",definition.get("hud_portrait",""))),
			"res://assets/fighters/%s/portraits/hud.png"%id,
			"res://assets/fighters/%s/portraits/portrait.png"%id,
			"res://assets/fighters/%s/portraits/special3.png"%id]
		var supers:Dictionary=UfeContentDatabase.read_json("res://content/presentation/supers.json")
		candidates.append(str(supers.get(id,{}).get("portrait","")))
		var portrait_path:=""
		for candidate in candidates:
			if not str(candidate).is_empty() and ResourceLoader.exists(str(candidate)):
				portrait_path=str(candidate);break
		unlisted_form_displays[id]={"id":id,
			"name":str(display.get("display_name",display.get("name",definition.get("display_name",definition.get("name",id))))),
			"title":str(display.get("title","")),
			"selection_category":str(display.get("selection_category",definition.get("selection_category",""))),
			"hud_portrait":portrait_path}
	return unlisted_form_displays[id]

static func model(id: String) -> Texture2D:
	if not models.has(id):
		var path:="res://assets/fighters/%s/model-native.png"%id
		models[id]=load(path) if ResourceLoader.exists(path) else null
	return models[id]

static func profile(id: String) -> Dictionary:
	if not profiles.has(id):
		var path:="res://content/fighters/%s/profile.json"%id
		profiles[id]=UfeContentDatabase.read_json(path) if FileAccess.file_exists(path) else {}
	return profiles[id]

static func warm_visible(rows: Array) -> void:
	for data in rows:
		if UfeRosterModel.implemented(str(data.id)):
			portrait(str(data.id))
			model(str(data.id))

static func forms(id: String) -> Array:
	if not form_entries.has(id):
		var overrides: Dictionary={}
		var aliases: Dictionary={}
		var path:="res://content/fighters/%s/forms"%id
		var files:=DirAccess.get_files_at(path) if DirAccess.dir_exists_absolute(path) else PackedStringArray()
		files.sort()
		for file in files:
			if not file.ends_with(".json"):continue
			var local: Dictionary=UfeContentDatabase.read_json(path+"/"+file)
			# forms目录也保留变身/必杀时间轴；MoveData不是可显示的身份形态。
			if not local.has("id") or local.has("frames"):continue
			overrides[str(local.id)]=local
			for alias in local.get("legacy_ids",[]):aliases[str(alias)]=str(local.id)
		var resolved: Array=[]
		var seen: Dictionary={}
		for listed in entry(id).get("forms",[]):
			var canonical: String=str(aliases.get(str(listed.id),listed.id))
			if seen.has(canonical):continue
			var merged: Dictionary=listed.duplicate(true)
			merged.merge(overrides.get(canonical,{}),true)
			resolved.append(merged)
			seen[canonical]=true
		for canonical in overrides:
			if not seen.has(canonical):resolved.append(overrides[canonical])
		form_entries[id]=resolved
	return form_entries[id]

static func select_forms(id: String) -> Array:
	return forms(id).filter(func(form):return str(form.get("switch","select"))=="select" and bool(form.get("select_visible",true)))

static func battle_forms(id: String) -> Array:
	# 既可在选人界面选出场、也可在战斗中按E切换的形态，两处都要列出。
	return forms(id).filter(func(form):return str(form.get("switch","select"))=="battle" or bool(form.get("battle_switch",false)))

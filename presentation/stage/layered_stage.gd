class_name UfeLayeredBattleStage
extends Node2D
## 只读世界镜头。所有最终图形来自已登记PNG，禁止任意画景repeat。
var stage_id: String=""
var layer_nodes: Array=[]
var ambient_nodes: Array=[]
var sky: Sprite2D
var age: float=0.0
var frozen: bool=false
var current_camera_x: int=320
var current_camera_y: int=0
var world_zoom: float=1.0
var world_origin := Vector2.ZERO
var cinematic_active: bool=false
var texture_cache: Dictionary={}
var configuration: Dictionary={}

func _texture(path: String) -> Texture2D:
	if not texture_cache.has(path):texture_cache[path]=load(path)
	return texture_cache[path] as Texture2D

func set_stage(id: String) -> void:
	var selected:=UfeBattleStageCatalog.valid_id(id)
	if selected==stage_id:return
	stage_id=selected
	configuration=UfeBattleStageCatalog.get_stage(stage_id)
	for child in get_children():remove_child(child);child.queue_free()
	layer_nodes.clear();ambient_nodes.clear();age=0.0
	if configuration.is_empty():return
	sky=Sprite2D.new();sky.centered=false
	sky.texture=_texture(str(configuration.sky));sky.z_index=-10
	add_child(sky)
	for item in configuration.get("layers",[]):
		var node:=Sprite2D.new();node.centered=false
		node.texture=_texture(str(item.texture));node.scale=Vector2.ONE*float(item.scale)
		node.z_index=int(item.get("z_index",-5))
		add_child(node)
		layer_nodes.append({"node":node,"data":item})
	for item in configuration.get("ambient",[]):
		var node:=Sprite2D.new();node.centered=true
		node.texture=_texture(str(item.texture));node.region_enabled=true
		node.scale=Vector2.ONE*float(item.get("scale",1.0))
		node.z_index=int(item.get("z_index",-2))
		node.modulate.a=float(item.get("opacity",0.5))
		add_child(node);ambient_nodes.append({"node":node,"data":item})
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	sync(current_camera_x,current_camera_y,cinematic_active)

func restart() -> void:
	age=0.0;frozen=false
	sync(320,0,false)

func sync(camera_x: int,camera_y: int,cinematic: bool,zoom: float=1.0,origin: Vector2=Vector2.ZERO) -> void:
	current_camera_x=camera_x;current_camera_y=camera_y;cinematic_active=cinematic
	world_zoom=zoom;world_origin=origin
	if sky==null:return
	for row in layer_nodes:
		var item: Dictionary=row.data
		var node: Sprite2D=row.node
		var base_scale: float=float(item.scale)
		var width: int=roundi(node.texture.get_width()*base_scale)
		var offset: int=clampi(roundi((camera_x-320)*float(item.parallax)),0,maxi(0,width-640))
		node.scale=Vector2(maxf(base_scale*zoom,640.0/node.texture.get_width()),base_scale*zoom)
		var rendered_width: float=node.texture.get_width()*node.scale.x
		node.position=origin+Vector2(-offset,int(item.y)+roundi(camera_y*float(item.parallax)))*zoom
		node.position.x=clampf(node.position.x,640.0-rendered_width,0.0)
		if str(item.id)=="ground":node.scale.y=maxf(node.scale.y,(360.0-node.position.y)/node.texture.get_height())
		node.visible=not cinematic
	for row in ambient_nodes:
		(row.node as Sprite2D).visible=not cinematic
	_update_ambient()

func _process(delta: float) -> void:
	if not is_visible_in_tree() or frozen:return
	age+=minf(delta,0.1)
	_update_ambient()

func _update_ambient() -> void:
	for row in ambient_nodes:
		var item: Dictionary=row.data
		var node: Sprite2D=row.node
		var frame_count: int=int(item.get("frames",4))
		var frame: int=posmod(floori(age*float(item.get("fps",6.0)))+int(item.get("phase",0)),frame_count)
		var cell: Array=item.get("cell",[64,64])
		var source_row: int=int(item.get("row",0))
		node.region_rect=Rect2(frame*int(cell[0]),source_row*int(cell[1]),int(cell[0]),int(cell[1]))
		var point: Array=item.get("position",[320,200])
		var parallax: float=float(item.get("parallax",0.5))
		node.position=Vector2(float(point[0])-(current_camera_x-320)*parallax,float(point[1])+current_camera_y*parallax)
		# 环境图集本身有四个实际画相；这里只作缓慢整体位移，不用几何画粒子。
		var drift: Array=item.get("drift",[0.0,0.0])
		var rate: float=float(item.get("drift_rate",0.15))
		node.position+=Vector2(float(drift[0]),float(drift[1]))*sin(age*rate+float(item.get("phase",0)))
		node.position=world_origin+node.position*world_zoom
		node.scale=Vector2.ONE*float(item.get("scale",1.0))*world_zoom

func snapshot() -> Dictionary:
	var ambient: Array=[]
	var layers: Array=[]
	for row in ambient_nodes:
		var node: Sprite2D=row.node
		ambient.append({"rect":[node.region_rect.position.x,node.region_rect.position.y,node.region_rect.size.x,node.region_rect.size.y],"position":[node.position.x,node.position.y],"visible":node.visible,"texture":node.texture.resource_path})
	for row in layer_nodes:
		var node: Sprite2D=row.node
		layers.append({"id":row.data.id,"position":[node.position.x,node.position.y],"visible":node.visible,"texture":node.texture.resource_path})
	return {"stage":stage_id,"age":age,"frozen":frozen,"camera":current_camera_x,"ambient":ambient,"layers":layers,"cinematic":cinematic_active,"child_count":get_child_count()}

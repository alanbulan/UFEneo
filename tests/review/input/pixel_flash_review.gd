class_name UfePixelFlashReview
extends UfePixelHudReview
var ko_at: int=-1
var beam_at: int=-1
var evidence: Array=[]
func _init() -> void:profile="phase3_flash_present_frames"
func drive_controls(frame: int,app: Node) -> void:
	if frame in [205,225]:
		var button: Button=app.hud.menu.get_child(0).get_child(1)
		button.release_focus()
		var point: Vector2=button.get_global_rect().get_center() if frame==205 else Vector2(2,2)
		point=app.image.get_global_rect().position+point*app.image.stretch_shrink
		var event:=InputEventMouseMotion.new();event.position=point;event.global_position=point;app.get_viewport().push_input(event)
	if frame in [190,210,230]:snapshot(app.view,"pause-"+{190:"selected",210:"hover",230:"normal"}[frame])
func snapshot(view: UfeSideView,name: String) -> void:
	await RenderingServer.frame_post_draw
	view.get_tree().root.get_texture().get_image().save_png("res://reports/review/2026-10-22-pixel-pages/"+name+".png")
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	for event in sim.events:
		if event.kind=="hit" and str(event.get("move","")).begins_with("special") and beam_at<0:
			beam_at=frame;snapshot(view,"super-hit")
	if sim.finished and ko_at<0:ko_at=frame;snapshot(view,"ko-hit")
	if frame==beam_at+2 and beam_at>=0:snapshot(view,"super-hit-plus2")
	if frame==ko_at+2 and ko_at>=0:snapshot(view,"ko-plus2")
	if frame==ko_at+20 and ko_at>=0:snapshot(view,"ko-defeat")
	if (beam_at>=0 and frame<beam_at+10) or (ko_at>=0 and frame<ko_at+30):
		evidence.append({"frame":frame,"render_frame":Engine.get_frames_drawn(),"sim_tick":sim.tick,"remaining_flash":view.feedback.flash.duplicate(),"finished":sim.finished,"states":[sim.fighters[0].state,sim.fighters[1].state],"clips":[view._animation(sim.fighters[0],view.manifests[0]).key,view._animation(sim.fighters[1],view.manifests[1]).key]})
	if frame==length_frames()-2:
		var file:=FileAccess.open("res://reports/review/2026-10-22-pixel-pages/flash-evidence.json",FileAccess.WRITE)
		file.store_string(JSON.stringify({"ko_frame":ko_at,"super_hit_frame":beam_at,"frames":evidence},"\t"))

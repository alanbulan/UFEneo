class_name UfeEffectTimeline
extends RefCounted
## 只读图集时钟；既有图集不声明ticks时保持4tick一相。
static func durations(clip:Dictionary) -> Array:
	var count:int=clip.get("rects",[]).size()
	var value:Variant=clip.get("clip",{}).get("ticks",clip.get("ticks",4))
	var result:Array=[]
	for i in range(count):
		result.append(maxi(1,int(value[i] if value is Array and i<value.size() else 4 if value is Array else value)))
	return result
static func length(clip:Dictionary) -> int:
	var total:int=0
	for ticks in durations(clip):total+=int(ticks)
	return total
static func phase(clip:Dictionary,age:int,loop:bool=true) -> int:
	var ticks:=durations(clip)
	if ticks.is_empty():return 0
	var total:=length(clip)
	var at:int=posmod(age,total) if loop else clampi(age,0,total-1)
	for i in range(ticks.size()):
		if at<int(ticks[i]):return i
		at-=int(ticks[i])
	return ticks.size()-1

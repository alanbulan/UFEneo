class_name UfeControllerSlots
extends RefCounted
## Keep a connected player's slot when the other controller disconnects.
var devices := PackedInt32Array([-1, -1])

func update(connected: PackedInt32Array) -> PackedInt32Array:
	for player in range(devices.size()):
		if devices[player] not in connected:
			devices[player] = -1
	for device in connected:
		if device in devices:
			continue
		var available := devices.find(-1)
		if available == -1:
			break
		devices[available] = device
	return devices.duplicate()

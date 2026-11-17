class_name UfeInputFrame
extends RefCounted
const LIGHT := 1
const HEAVY := 2
const THROW := 4
const GUARD := 8
const CHARGE := 16
const SPECIAL := 32
const CRUSH := 64
const RANGED := 128
const DODGE := 256
const JUMP := 512
const TRANSFORM := 1024
const ALL_BUTTONS := 2047
var x: int = 0
var y: int = 0
var buttons: int = 0

static func make(horizontal: int = 0, vertical: int = 0, mask: int = 0) -> UfeInputFrame:
	var value := UfeInputFrame.new()
	value.x = clampi(horizontal, -1, 1)
	value.y = clampi(vertical, -1, 1)
	value.buttons = mask & ALL_BUTTONS
	return value

func held(mask: int) -> bool:
	return (buttons & mask) == mask

func pack() -> Array:
	return [x, y, buttons]

static func unpack(data: Array) -> UfeInputFrame:
	return make(int(data[0]), int(data[1]), int(data[2]))

shader_type canvas_item;
uniform bool red_timer = false;
uniform bool hit_flash = false;
uniform int mapping_count = 0;
uniform vec3 palette_sources[32];
uniform vec3 palette_targets[32];
varying vec4 vertex_tint;
void vertex() { vertex_tint = COLOR; }
void fragment() {
	vec4 pixel = texture(TEXTURE, UV);
	ivec3 original = ivec3(round(pixel.rgb * 255.0));
	for (int i = 0; i < mapping_count; i++) {
		if (all(equal(original, ivec3(round(palette_sources[i] * 255.0))))) {
			pixel.rgb = palette_targets[i];
			break;
		}
	}
	if (hit_flash) pixel.rgb = vec3(1.0);
	COLOR = pixel * vertex_tint;
}

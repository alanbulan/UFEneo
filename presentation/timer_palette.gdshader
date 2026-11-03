shader_type canvas_item;
uniform bool red_timer = false;
uniform bool hit_flash = false;
varying vec4 vertex_tint;
void vertex() { vertex_tint=COLOR; }
void fragment() {
	vec4 pixel = texture(TEXTURE, UV);
	if (red_timer && pixel.b > pixel.r + 0.16 && pixel.g > 0.38) {
		pixel.rgb = vec3(1.0, 0.12 + pixel.g * 0.12, 0.12);
	}
	if (hit_flash) pixel.rgb=vec3(1.0);
	COLOR = pixel * vertex_tint;
}

shader_type canvas_item;
uniform vec4 palette_tint : source_color = vec4(1.0);
varying vec4 vertex_tint;
void vertex() { vertex_tint=COLOR; }
void fragment() {
	vec4 pixel=texture(TEXTURE,UV);
	if (palette_tint.rgb!=vec3(1.0)) {
		float value=max(pixel.r,max(pixel.g,pixel.b));
		pixel.rgb=mix(palette_tint.rgb*value,vec3(value),smoothstep(0.85,1.0,value)*0.65);
	}
	COLOR=pixel*vertex_tint*vec4(1.0,1.0,1.0,palette_tint.a);
}

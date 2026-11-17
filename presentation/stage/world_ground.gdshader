shader_type canvas_item;
render_mode unshaded;

// The shader samples GPT artwork; it does not draw replacement vector scenery.
uniform sampler2D ground_texture : filter_nearest, repeat_enable;
uniform vec2 logical_origin;
uniform vec2 logical_size;
uniform vec2 world_origin;
uniform vec2 world_extent;
uniform float camera_distance;
uniform float camera_height;
uniform float camera_scale;
uniform float floor_y;
uniform float center_x;
uniform vec4 art_tint : source_color = vec4(1.0);

void fragment() {
	// Logical UV is independent of window resolution and viewport stretching.
	vec2 screen = logical_origin + UV * logical_size;
	float perspective = 1.0 + (screen.y - floor_y) / (camera_height * camera_scale);
	vec2 world = vec2(center_x + (screen.x - center_x) / (perspective * camera_scale),
		camera_distance * (1.0 - 1.0 / perspective));
	vec2 sample_uv = (world - world_origin) / world_extent;
	// Mirror the existing texture at tile boundaries; no painted seam or overlay.
	sample_uv = 1.0 - abs(mod(sample_uv, vec2(2.0)) - 1.0);
	COLOR = texture(ground_texture, sample_uv) * art_tint;
}

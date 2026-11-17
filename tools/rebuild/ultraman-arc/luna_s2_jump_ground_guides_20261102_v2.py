"""月亮起跳/落地四张新完整抽象guide；不是最终人物，不POST/Godot/产品写入。"""
from pathlib import Path
import copy
import hashlib
import json
import math
import sys

sys.dont_write_bytecode = True
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/rebuild/shared'))
from forge_backend import build_layout_guide

OWN = ROOT / 'art/fighters/ultraman-arc__luna'
OLD = OWN / 'stage2/jump-preparation-20261102-v1'
ART = OWN / 'stage2/jump-ground-guides-20261102-v2'
OUT = ROOT / 'reports/review/2026-11-02/arc-luna-jump-ground-four-guides-v2'
MEASURES = OWN / 'model/measurements.json'
IDENTITY = OWN / 'stage2/walk-forward-repair-20261102-v1/references/identity.png'
SCALE = 1024 / 159
FONT = '/System/Library/Fonts/Hiragino Sans GB.ttc'

PLANS = [
    {'action': 'takeoff', 'phase': 0, 'label': '同脚序压膝，双臂及肩胸髋共同加载', 'hip': [130, 187], 'torso_degrees': 9, 'head_degrees': 4,
     'near_arm_angles': [115, -10], 'far_arm_angles': [55, -60], 'toe_off': False, 'input_relative_n': [0], 'simulation_height': [0],
     'root_note': '实际n0尚在0高；起跳双脚承重的整姿，不画地线或冲刺腿序。'},
    {'action': 'takeoff', 'phase': 1, 'label': '胸髋蹬伸，双臂上提，踝伸展接离地', 'hip': [128, 174.3], 'torso_degrees': 1, 'head_degrees': -1,
     'near_arm_angles': [109, -26], 'far_arm_angles': [64, -78], 'toe_off': True, 'input_relative_n': [1], 'simulation_height': [16],
     'root_note': '实际n1已经整体升高16。guide根线只是虚拟注册线，不能要求源中两鞋再贴实际地面，也不另烘焙第二次升高。'},
    {'action': 'land', 'phase': 0, 'label': '触地双膝吸震，胸髋前收，双臂随震守护', 'hip': [129, 189], 'torso_degrees': 12, 'head_degrees': 5,
     'near_arm_angles': [121, 14], 'far_arm_angles': [65, -48], 'toe_off': False, 'input_relative_n': [33, 34], 'simulation_height': [0, 0],
     'root_note': '新独立吸震整相；不复用起跳压膝、蹲姿或侧闪。近后/远前两靴支点和下一相保持。'},
    {'action': 'land', 'phase': 1, 'label': '双膝伸回，胸髋起回，双臂接本人idle护架', 'hip': [128.5, 176.5], 'torso_degrees': 2, 'head_degrees': 1,
     'near_arm_angles': [113, 9], 'far_arm_angles': [56, -44], 'toe_off': False, 'input_relative_n': [35, 36], 'simulation_height': [0, 0],
     'root_note': '回idle前保留很小真实屈膝/双臂收势差；近亮后左、远暗前右全程不换脚。'},
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text('utf-8-sig'))


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def ref(path):
    return {'path': rel(path), 'sha256': sha(path)}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def add(a, b):
    return [a[0] + b[0], a[1] + b[1]]


def sub(a, b):
    return [a[0] - b[0], a[1] - b[1]]


def vector(length, degrees):
    t = math.radians(degrees)
    return [math.cos(t) * length, math.sin(t) * length]


def rotate(v, degrees):
    x, y = vector(1, degrees)
    return [v[0] * x - v[1] * y, v[0] * y + v[1] * x]


def distance(a, b):
    return math.dist(a, b)


def planned_knee(hip, ankle, thigh, shin):
    """仅抽象新guide的定长几何约束，完全不采样/切割/旋转人物像素。"""
    delta = sub(ankle, hip)
    d = math.hypot(*delta)
    assert abs(thigh - shin) < d < thigh + shin, (hip, ankle, thigh, shin)
    a = (thigh * thigh - shin * shin + d * d) / (2 * d)
    h = math.sqrt(max(0, thigh * thigh - a * a))
    base = add(hip, [delta[0] * a / d, delta[1] * a / d])
    candidates = [add(base, [-delta[1] * h / d, delta[0] * h / d]), add(base, [delta[1] * h / d, -delta[0] * h / d])]
    return max(candidates, key=lambda p: p[0])  # 朝右屈膝；近远身份不因此互换。


def prepare_points(master, plan):
    result = {'hip_center': list(plan['hip'])}
    hip = result['hip_center']
    for name in ['neck_base', 'near_shoulder', 'far_shoulder', 'near_hip', 'far_hip']:
        result[name] = add(hip, rotate(sub(master[name], master['hip_center']), plan['torso_degrees']))
    for name in ['skull_top', 'chin', 'eye', 'ear']:
        result[name] = add(result['neck_base'], rotate(sub(master[name], master['neck_base']), plan['head_degrees']))
    for side in ['near', 'far']:
        for suffix in ['toe', 'ankle']:
            result[side + '_' + suffix] = list(master[side + '_' + suffix])
        foot_length = distance(master[side + '_toe'], master[side + '_ankle'])
        if plan['toe_off']:
            angle = 60 if side == 'near' else 30
            result[side + '_ankle'] = sub(result[side + '_toe'], vector(foot_length, angle))
        thigh = distance(master[side + '_hip'], master[side + '_knee'])
        shin = distance(master[side + '_knee'], master[side + '_ankle'])
        result[side + '_knee'] = planned_knee(result[side + '_hip'], result[side + '_ankle'], thigh, shin)
        upper = distance(master[side + '_shoulder'], master[side + '_elbow'])
        forearm = distance(master[side + '_elbow'], master[side + '_wrist'])
        upper_degrees, fore_degrees = plan[side + '_arm_angles']
        result[side + '_elbow'] = add(result[side + '_shoulder'], vector(upper, upper_degrees))
        result[side + '_wrist'] = add(result[side + '_elbow'], vector(forearm, fore_degrees))
        result[side + '_fist'] = add(result[side + '_wrist'], vector(7, -35 if side == 'near' else -45))
    return result


def xy(point):
    return [round(512 + (point[0] - 128) * SCALE), round(960 + (point[1] - 248) * SCALE)]


def make_guide(path, points, title, note):
    image = build_layout_guide(1, 1, 1024, 1024, 48, 48).convert('RGB')
    # 空白layout仅作背景，不包含任何人物像素。
    image.paste((100, 112, 128), (0, 0, 1024, 1024))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT, 21)
    small = ImageFont.truetype(FONT, 18)
    draw.text((48, 12), title, fill='white', font=font)
    draw.text((48, 43), '完整新抽象姿态：白=近亮左肢；暗=远暗右肢；绝非最终人物', fill='#ffe780', font=small)
    for line, start in enumerate(range(0, len(note), 22)):
        draw.text((48, 104 + line * 25), note[start:start + 22], fill='#ffe780', font=small)
    draw.line((56, 960, 968, 960), fill='#b6c5d4', width=2)
    draw.text((52, 986), '虚拟注册根 [512,960]；不等于空中人物的实际地面，不画进最终PNG', fill='white', font=small)
    at = lambda key: xy(points[key])
    torso = [at(k) for k in ['near_shoulder', 'far_shoulder', 'far_hip', 'near_hip']]
    draw.polygon(torso, fill='#647f82', outline='#57e2da', width=4)
    for side, color in [('far', '#242424'), ('near', '#ffffff')]:
        for chain in [['_hip', '_knee', '_ankle', '_toe'], ['_shoulder', '_elbow', '_wrist', '_fist']]:
            draw.line([at(side + suffix) for suffix in chain], fill=color, width=15, joint='curve')
        for suffix in ['_hip', '_knee', '_ankle', '_shoulder', '_elbow', '_wrist']:
            x, y = at(side + suffix)
            draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=color)
        x, y = at(side + '_fist')
        draw.ellipse((x - 15, y - 15, x + 15, y + 15), outline=color, width=4)
        x, y = at(side + '_wrist')
        draw.ellipse((x - 20, y - 20, x + 20, y + 20), outline=color, width=3)
    draw.line([at(k) for k in ['hip_center', 'neck_base']], fill='#57e2da', width=11)
    draw.line([at('neck_base'), at('chin')], fill='#57e2da', width=7)
    skull, chin = points['skull_top'], points['chin']
    mid = [(skull[0] + chin[0]) / 2, (skull[1] + chin[1]) / 2]
    delta = sub(chin, skull)
    major = distance(chin, skull) / 2
    direction = [delta[0] / (major * 2), delta[1] / (major * 2)]
    perpendicular = [-direction[1], direction[0]]
    outline = []
    for n in range(49):
        t = n * math.tau / 48
        outline.append(xy([mid[0] + math.cos(t) * major * direction[0] + math.sin(t) * major * 0.68 * perpendicular[0], mid[1] + math.cos(t) * major * direction[1] + math.sin(t) * major * 0.68 * perpendicular[1]]))
    draw.line(outline, fill='#ffe780', width=5)
    for name in ['skull_top', 'chin']:
        x, y = at(name)
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill='#ffe780')
    x, y = at('eye')
    draw.line((x + 12, y, x + 58, y), fill='#ffe780', width=5)
    draw.polygon([(x + 58, y), (x + 43, y - 9), (x + 43, y + 9)], fill='#ffe780')
    x, y = xy([128, 248])
    draw.line((x - 10, y, x + 10, y), fill='#ff9f72', width=3)
    draw.line((x, y - 10, x, y + 10), fill='#ff9f72', width=3)
    assert not path.exists()
    image.save(path)
    return image


def jpeg(path, picture):
    assert picture.width <= 768 and not path.exists()
    picture.convert('RGB').save(path, quality=80, optimize=True)
    assert path.stat().st_size <= 150000
    return {**ref(path), 'dimensions': list(picture.size), 'bytes': path.stat().st_size, 'quality': 80}


def clocks():
    """源码顺序的静态算术推演，绝不是Godot或真实输入结果。"""
    tables = {'vertical_jump': [8, 7, 3, 8, 7], 'flip_forward': [8, 8, 8, 9], 'flip_back': [8, 8, 8, 9]}
    cases = []
    for key, durations in tables.items():
        table = [phase for phase, ticks in enumerate(durations) for _ in range(ticks)]
        assert len(table) == 33
        air = [{'n': n, 'table_index': n, 'phase': table[n], 'vy': 16 - n, 'height': sum(range(16, 16 - n, -1))} for n in range(2, 33)]
        counts = [sum(row['phase'] == p for row in air) for p in range(len(durations))]
        assert sum(counts) == 31
        assert [r['n'] for r in air if r['height'] == 136] == [16, 17]
        cases.append({'clip': key, 'simulation_state_key': {'vertical_jump': 'vertical_air', 'flip_forward': 'diagonal_air', 'flip_back': 'backward_air'}[key], 'trajectory_driven_required': True, 'loop': False, 'absolute_table_ticks': durations, 'actual_air_consumption_prediction_ticks': counts, 'predicted_air_rows': air})
    return {'status': 'source_order_arithmetic_only_not_Godot', 'jump_speed_candidate': 16, 'gravity_per_tick': 1, 'horizontal_speed': 4, 'takeoff_display': [{'n': 0, 'state_tick': 0, 'height': 0, 'vy': 16, 'phase': 0}, {'n': 1, 'state_tick': 1, 'height': 16, 'vy': 15, 'phase': 1}], 'first_air': {'n': 2, 'state_tick': 0, 'height': 31, 'vy': 14, 'index': 2}, 'cases': cases, 'landing': [{'n': n, 'state_tick': n - 33, 'height': 0, 'phase': (n - 33) // 2} for n in range(33, 37)], 'n37_prediction': 'idle', 'full_state_observation_prediction': 'takeoff2 + air31 + land4 = 37 visible ticks before idle n37', 'not_additional_33_ticks_after_takeoff': True, 'no_actual_states_or_positions_injected': True}


def main():
    assert not ART.exists() and not OUT.exists()
    assert sha(IDENTITY) == 'd70d0f5fba22d54281b50703158ac2ba8ff1d29624f3020b4bdbe7c20992a6da'
    assert sha(OLD / 'preparation-plan.json') == '4b2dac56eb7d9512d9cff415b64f60dabf67640212f6d44795d791890960930b'
    protected = {rel(p): sha(p) for p in OLD.rglob('*') if p.is_file()}
    bound = [MEASURES, IDENTITY, ROOT / 'core/states/state.gd', ROOT / 'core/states/takeoff.gd', ROOT / 'core/states/air.gd', ROOT / 'core/states/land.gd', ROOT / 'core/fighters/fighter.gd', ROOT / 'core/combat/match_director.gd', ROOT / 'presentation/side_view.gd', ROOT / 'content/fighters/ultraman-arc__luna/definition.json']
    protected.update({rel(p): sha(p) for p in bound})
    production = read(bound[-1])
    assert all(production[k] is False for k in ['playable', 'implemented', 'select_visible'])
    measures = read(MEASURES)
    source = measures['normalized_1024_landmarks']
    master = {key: [128 + (p[0] - 522) / SCALE, 248 + (p[1] - 980) / SCALE] for key, p in source.items()}
    segments = [('skull_top', 'chin'), ('neck_base', 'hip_center')]
    segments += [(s + a, s + b) for s in ['near', 'far'] for a, b in [('_shoulder', '_elbow'), ('_elbow', '_wrist'), ('_hip', '_knee'), ('_knee', '_ankle'), ('_ankle', '_toe')]]
    gauge = {'_'.join(keys): distance(master[keys[0]], master[keys[1]]) for keys in segments}
    OUT.mkdir(parents=True)
    prepared = []
    all_points = {}
    for plan in PLANS:
        action, phase = plan['action'], plan['phase']
        points = prepare_points(master, plan)
        actual_lengths = {'_'.join(keys): distance(points[keys[0]], points[keys[1]]) for keys in segments}
        deviations = {key: actual_lengths[key] - value for key, value in gauge.items()}
        assert max(abs(z) for z in deviations.values()) < 1e-10
        assert points['near_toe'][0] < points['hip_center'][0] < points['far_toe'][0]
        assert all(48 < xy(p)[0] < 976 and 48 < xy(p)[1] < 976 for p in points.values())
        folder = ART / action / f'phase-{phase:02}'
        folder.mkdir(parents=True)
        image = make_guide(folder / 'pose-guide.png', points, f'{action} {phase:02} / FACE RIGHT / {plan["label"]}', plan['root_note'])
        preview = jpeg(OUT / f'{action}-{phase:02}-complete-guide.jpg', image.resize((768, 768), Image.Resampling.LANCZOS))
        old_brief = OLD / 'drafts' / action / f'phase-{phase:02}/brief.json'
        brief = copy.deepcopy(read(old_brief))
        prefix = ('IMAGE 1 is the NEW COMPLETE ABSTRACT POSE GUIDE. IMAGE 2 is the accepted LUNA IDENTITY MASTER. '
                  'White chains are the bright NEAR left limbs; dark chains are the dark FAR right limbs. Cyan/yellow lines, joints, floor/root marks, circles, arrows, text and the canvas are instructions ONLY and must NEVER appear in the final person image. '
                  'The guide is freshly authored full-pose geometry, not a cut or rotated person. Draw one natural COMPLETE PERSON in the pose, with the identity, armor, head-shell size and body mass of image 2. '
                  'Preserve the near bright rear/LEFT leg and far dark front/RIGHT leg order through loading, extension and landing. '
                  'Both lower legs are plain red/silver suit: NO BLUE shin fins, calf plates, greaves or blue boot armor. '
                  + plan['root_note'] + '\n')
        brief.update({'id': f'arc_luna_{action}_{phase:02}_whole_guided_draft_20261102', 'prompt': prefix + brief['prompt'].replace('IMAGE 1', 'IMAGE 2'), 'references': [ref(folder / 'pose-guide.png'), ref(IDENTITY)], 'guide_only_not_final_art': True, 'root_POST_decision_pending': True, 'supersedes_only_for_future_root_review': ref(old_brief)})
        save(folder / 'brief.json', brief)
        with (folder / 'prompt.txt').open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(brief['prompt'])
        pose = {'action': action, 'phase': phase, 'authored_plan': plan, 'native_planned_points': points, 'client1024_planned_points': {k: xy(v) for k, v in points.items()}, 'same_master_uniform_scale': SCALE, 'source_to_guide_native_scale': 159 / 1024, 'virtual_root_client1024': [512, 960], 'runtime_root_candidate': [160, 280], 'abstract_guide_not_final_art': True, 'actual_source_landmarks_known': False, 'master_surface_proxy_not_anatomical_bone_measurement': True, 'strict_size_accepted': False, 'new_source_actual_Alpha_and_pivot_must_be_measured_after_return': True, 'master_segment_lengths_native': gauge, 'planned_segment_lengths_native': actual_lengths, 'planned_minus_master_segment_lengths_native': deviations, 'foot_contact_note': '复用同一master的近/远完整靴方向代理与脚序；近脚趾基准248、远脚趾245.6708984375有投影深度差，不冒称两点为真实世界地面或实际鞋底。n1踝伸展但根不另增高度。'}
        save(folder / 'pose-target.json', pose)
        prepared.append({'action': action, 'phase': phase, 'brief': ref(folder / 'brief.json'), 'prompt': ref(folder / 'prompt.txt'), 'guide': ref(folder / 'pose-guide.png'), 'pose_target': ref(folder / 'pose-target.json'), 'JPEG_preview': preview, 'same_master_projected_segment_lengths': True, 'original_draft_preserved': ref(old_brief), 'POST_submitted': False, 'root_acceptance': 'pending actual root review'})
        all_points[(action, phase)] = points
    for side in ['near', 'far']:
        for name in ['toe', 'ankle']:
            assert all_points[('land', 0)][side + '_' + name] == all_points[('land', 1)][side + '_' + name] == master[side + '_' + name]
        for suffix in ['shoulder', 'elbow', 'wrist', 'fist']:
            assert all_points[('takeoff', 0)][side + '_' + suffix] != all_points[('takeoff', 1)][side + '_' + suffix]
            assert all_points[('land', 0)][side + '_' + suffix] != all_points[('land', 1)][side + '_' + suffix]
    # 完整master仅用于审阅的缩小合成，不切割/改造/旋转人物。
    with Image.open(IDENTITY) as full:
        full = full.convert('RGBA')
        page = Image.new('RGB', (768, 800), '#364250')
        scaled = full.resize((704, 704), Image.Resampling.LANCZOS)
        page.paste(scaled, (32, 64), scaled)
        draw = ImageDraw.Draw(page)
        draw.text((18, 12), '同一完整LUNA身份master；只缩小审阅，不生成/拆肢/改图', fill='white', font=ImageFont.truetype(FONT, 18))
        master_preview = jpeg(OUT / 'same-complete-identity-master.jpg', page)
    clock = clocks()
    save(OUT / 'absolute-clock-and-state-key-map.json', {'bound_core_sources': [ref(p) for p in bound[2:-1]], **clock})
    save(ART / 'four-guide-contract.json', {'schema': 'ufeneo.arc-luna.s2.jump-ground-four-guides.v1', 'fighter': 'ultraman-arc__luna', 'prepared_by': '/root/teo_leapblade_runtime', 'root_explicit_scope': '先takeoff00/01与landing00/01免费完整新guide，核真实源码顺序时钟/同一完整master比例/近远脚序；禁POST，Godot根占用', 'prior_17_draft_plan': ref(OLD / 'preparation-plan.json'), 'same_identity_master': ref(IDENTITY), 'master_measurements': ref(MEASURES), 'master_projected_planning_points': master, 'master_segment_lengths_native': gauge, 'measurement_limit': measures['bone_reading_quality'], 'same_complete_master_JPEG': master_preview, 'requests_preparation_only': prepared, 'absolute_clock_source_only': ref(OUT / 'absolute-clock-and-state-key-map.json'), 'candidate_air_table_consumption_note': '起跳实际n0/n1；air只读n2..32：垂直实消耗[6,7,3,8,7]、前后翻[6,8,8,9]，源表分别仍[8,7,3,8,7]/[8,8,8,9]。trajectory_driven必须true且loop false。不是新Godot结果。', 'allowed_sharing': '三种基础跳跃共用本人takeoff2/land2，前后空翻独立，追击起跳不混入', 'planned_leg_order': '近亮后左、远暗前右；落地两相完整靴代理不动，n1只脚踝伸展，不能通过额外角色平移假造接地', 'abstract_geometric_constraints_not_pixel_person_rig': True, 'person_pixels_used_for_guides': False, 'planned_points_are_not_returned_source_bones': True, 'root_review_pending': True, 'POST_count': 0, 'candidate_person_frames_written': False, 'product_written': False, 'Godot_started': False, 'playable_or_transform_opened': False, 'old_drafts_preserved': True})
    assert all(sha(ROOT / p) == digest for p, digest in protected.items())
    save(OUT / 'preparation-receipt.json', {'contract': ref(ART / 'four-guide-contract.json'), 'protected_originals_unchanged': [{'path': p, 'sha256': digest} for p, digest in protected.items()], 'new_guide_previews': [row['JPEG_preview'] for row in prepared], 'same_complete_master_preview': master_preview, 'generated_person_art': False, 'pose_guides_are_abstract_constraints_only': True, 'POST_count': 0, 'Godot_started': False, 'product_write': False, 'Git_commit': False, 'root_actual_visual_review_pending': True})
    print(json.dumps({'contract': ref(ART / 'four-guide-contract.json'), 'receipt': ref(OUT / 'preparation-receipt.json'), 'POST_count': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()

"""复用已有完整像素注册月亮前跳八相；不重存PNG、不生图、不启动Godot。"""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / 'art/fighters/ultraman-arc__luna/stage2'
OUT = BASE / 'forward_jump-registered-20261105-v1'
VERTICAL = BASE / 'vertical_jump-registered-20261105-v1/manifest.json'
OLD = BASE / 'jump-whole-offline-registration-20261102-v2'
TICKS = [8, 8, 8, 9]
FLAGS = dict(strict_size_accepted=False, art_passed=False, installed=False, playable=False)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path))


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def check(value):
    path = ROOT / value['path']
    assert sha(path) == value['sha256'], path
    return path


def put(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    if path.exists():
        assert path.read_bytes() == data, f'拒绝覆盖不同内容：{path}'
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)


def validate_group(group):
    clip = read(check(group['clip']))
    atlas_path = ROOT / clip['texture'].removeprefix('res://')
    assert sha(atlas_path) == clip['atlas_sha256']
    atlas = Image.open(atlas_path).convert('RGBA')
    for row in group['frames']:
        source = ROOT / row['source']
        image = ROOT / row['image']
        assert sha(source) == row['source_sha256']
        assert sha(image) == row['image_sha256']
        whole = Image.open(check(row['whole_source_sample'])).convert('RGBA')
        check(row['previous_receipt'])
        check(row['previous_frame'])
        assert whole.size == (159, 159)
        frame = Image.open(image).convert('RGBA')
        expected = Image.new('RGBA', (320, 320))
        expected.paste(whole, tuple(row['whole_source_destination_offset'][:2]))
        assert frame.tobytes() == expected.tobytes()
        x, y, w, h = clip['rects'][row['phase']]
        assert atlas.crop((x, y, x+w, y+h)).tobytes() == frame.tobytes()
        assert set(frame.getchannel('A').tobytes()) == {0, 255}
        box = frame.getbbox()
        assert 0 < box[0] < box[2] < 320 and 0 < box[1] < box[3] < 320
    return len(group['frames'])


def main():
    vertical = read(VERTICAL)
    rows = []
    for phase, duration in enumerate(TICKS):
        receipt_path = OLD / 'flip_forward' / f'{phase:02d}/candidate-02/phase-receipt.json'
        old = read(receipt_path)
        source = ROOT / old['source']
        image = ROOT / old['image']
        assert sha(source) == old['source_sha256']
        assert sha(image) == old['image_sha256']
        rows.append(dict(phase=phase, ticks=duration, image=old['image'], image_sha256=old['image_sha256'],
                         source=old['source'], source_sha256=old['source_sha256'],
                         whole_source_sample=old['whole_source_sample'], previous_frame=ref(image),
                         previous_receipt=ref(receipt_path),
                         whole_source_destination_offset=old['whole_source_destination_offset'][:2],
                         whole_image_shift=[0, 0], root=[160, 280], whole_image_only=True,
                         pixel_comparison_passed=True, **FLAGS))
    atlas = OLD / 'assembled-selected-candidate02-v1/flip_forward/atlas.png'
    clip = dict(fighter='ultraman-arc__luna', source_fighter='ultraman-arc__luna', action='flip_forward',
                texture='res://' + ref(atlas)['path'], atlas_sha256=sha(atlas), cell=320,
                anchor=[160, 280], anchor_y=280, anchors=[[160, 280] for _ in TICKS],
                rects=[[320*i, 0, 320, 320] for i in range(4)], ticks=TICKS, loop=False,
                simulation_sprite_offset=0, trajectory_driven=True, root_approved=False, **FLAGS)
    clip_path = OUT / 'flip_forward/clip.json'
    put(clip_path, clip)
    actions = dict(takeoff=vertical['actions']['takeoff'], flip_forward=dict(frames=rows, clip=ref(clip_path)),
                   land=vertical['actions']['land'])
    assert sum(validate_group(group) for group in actions.values()) == 8
    land = actions['land']['frames'][1]
    assert land['whole_image_shift'] == [0, -4]
    assert land['whole_source_destination_offset'] == [80, 127]
    assert Image.open(ROOT / land['image']).getbbox()[3] == 280
    manifest = dict(schema='ufeneo.arc-luna.forward-jump-registration.v1', fighter='ultraman-arc__luna',
                    actions=actions, reused_ground_manifest=ref(VERTICAL),
                    common_full_source_raster=[159, 159], source_dimensions=[1024, 1024],
                    source_scale=159/1024, runtime_canvas=[320, 320], runtime_root=[160, 280],
                    per_phase_scale_or_area_fitting=False, transform_enabled=False, **FLAGS)
    manifest_path = OUT / 'manifest.json'
    put(manifest_path, manifest)
    review = dict(schema='ufeneo.arc-luna.forward-jump-registration-review.v1', reviewer='root_delegated_by_user',
                  manifest=ref(manifest_path), accepted_for_registration=True, accepted_for_formal_main_candidate=True,
                  approval_scope='仅当前主游戏前跳八相候选注册和验证，不是美术验收或正式开放',
                  admission_basis='源审者实看4张完整raw.provider原源、4张完整源审图及起跳2→前翻4→修正落地2完整图集；核四原源SHA、八相整159注册及atlas逐像素',
                  ground_reuse='原样复用垂直跳已注册takeoff/land；land01整图上移4px，支撑底280，不恢复旧284版本',
                  air_root_caveat='空中髋表面粗代理约±20源像素≈±3.1运行像素；未严格骨尺验收',
                  pending=['00→01及02→03旋转角跨度大，8/8/8/9 tick须实际图形核节奏',
                           'takeoff01伸腿→00深收膝与03展开→land00屈膝的起落接续待核',
                           '双向前跳须按相对朝向斜上输入，真实输入和独立回放待验',
                           '当前主游戏双向720/1080图形与回架严格核验'],
                  source_artifacts_unchanged=True, PNG_written=False, Godot_started=False, POST_count=0, **FLAGS)
    review_path = OUT / 'root-review.json'
    put(review_path, review)
    print(json.dumps(dict(manifest=ref(manifest_path), review=ref(review_path), frames=8,
                          pixel_comparison_passed=True, PNG_written=False), ensure_ascii=False))


if __name__ == '__main__':
    main()

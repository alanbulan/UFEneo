"""离线注册月亮垂直跳九相；整图平移，不生图、不启动Godot、不改旧审批。"""
from pathlib import Path
import hashlib
import io
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / 'art/fighters/ultraman-arc__luna/stage2'
OUT = BASE / 'vertical_jump-registered-20261105-v1'
TICKS = {'takeoff': [1, 1], 'vertical_jump': [8, 7, 3, 8, 7], 'land': [2, 2]}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def png(image):
    stream = io.BytesIO()
    image.save(stream, format='PNG')
    return stream.getvalue()


def put(path, value):
    data = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    if path.exists():
        assert path.read_bytes() == data, f'拒绝覆盖不同内容：{path}'
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)


def main():
    flags = dict(strict_size_accepted=False, art_passed=False, installed=False, playable=False)
    actions = {}
    for action, ticks in TICKS.items():
        rows = []
        atlas = Image.new('RGBA', (320 * len(ticks), 320))
        for phase, duration in enumerate(ticks):
            air = action == 'vertical_jump'
            folder = 'jump-whole-offline-registration-20261102-v2' if air else 'jump-whole-offline-resume-20261102-v1'
            prior = BASE / folder / action / f'{phase:02d}' / ('candidate-02' if air else 'candidate-01')
            receipt_path = prior / 'phase-receipt.json'
            receipt = read(receipt_path)
            source = ROOT / receipt['source']
            previous = ROOT / receipt['image']
            sample = ROOT / receipt['whole_source_sample']['path']
            assert sha(source) == receipt['source_sha256']
            assert sha(previous) == receipt['image_sha256']
            assert sha(sample) == receipt['whole_source_sample']['sha256']
            assert Image.open(source).size == (1024, 1024)
            whole = Image.open(sample).convert('RGBA')
            assert whole.size == (159, 159)
            old_offset = receipt['whole_source_destination_offset'][:2]
            old_expected = Image.new('RGBA', (320, 320))
            old_expected.paste(whole, tuple(old_offset))
            old_image = Image.open(previous).convert('RGBA')
            assert old_image.tobytes() == old_expected.tobytes()
            shift = [0, -4] if action == 'land' and phase == 1 else [0, 0]
            offset = [old_offset[i] + shift[i] for i in range(2)]
            image = Image.new('RGBA', (320, 320))
            image.paste(whole, tuple(offset))
            assert set(image.getchannel('A').tobytes()) == {0, 255}
            bbox = image.getbbox()
            assert 0 < bbox[0] < bbox[2] < 320 and 0 < bbox[1] < bbox[3] < 320
            assert image.getchannel('A').histogram() == old_image.getchannel('A').histogram()
            if shift == [0, 0]:
                assert image.tobytes() == old_image.tobytes()
            else:
                assert image.crop((0, 0, 320, 316)).tobytes() == old_image.crop((0, 4, 320, 320)).tobytes()
                assert bbox[3] == 280
            frame_path = OUT / action / f'frame-{phase:02d}.png'
            put(frame_path, png(image))
            assert Image.open(frame_path).tobytes() == image.tobytes()
            atlas.paste(image, (320 * phase, 0))
            rows.append(dict(phase=phase, ticks=duration, image=ref(frame_path)['path'], image_sha256=sha(frame_path),
                             source=ref(source)['path'], source_sha256=sha(source), whole_source_sample=ref(sample),
                             previous_frame=ref(previous), previous_receipt=ref(receipt_path),
                             previous_whole_source_destination_offset=old_offset,
                             whole_source_destination_offset=offset, whole_image_shift=shift,
                             root=[160, 280], alpha_bbox=list(bbox), whole_image_only=True,
                             pixel_comparison_passed=True, **flags))
        atlas_path = OUT / action / 'atlas.png'
        put(atlas_path, png(atlas))
        clip = dict(fighter='ultraman-arc__luna', source_fighter='ultraman-arc__luna', action=action,
                    texture='res://' + ref(atlas_path)['path'], atlas_sha256=sha(atlas_path), cell=320,
                    anchor=[160, 280], anchor_y=280, anchors=[[160, 280] for _ in ticks],
                    rects=[[320*i, 0, 320, 320] for i in range(len(ticks))], ticks=ticks,
                    loop=False, simulation_sprite_offset=0, trajectory_driven=action == 'vertical_jump',
                    root_approved=False, **flags)
        clip_path = OUT / action / 'clip.json'
        put(clip_path, clip)
        actions[action] = dict(frames=rows, clip=ref(clip_path))
    manifest = dict(schema='ufeneo.arc-luna.vertical-jump-registration.v1', fighter='ultraman-arc__luna',
                    actions=actions, common_full_source_raster=[159,159], source_dimensions=[1024,1024],
                    source_scale=159/1024, runtime_canvas=[320,320], runtime_root=[160,280],
                    per_phase_scale_or_area_fitting=False, transform_enabled=False, **flags)
    manifest_path = OUT / 'manifest.json'
    put(manifest_path, manifest)
    review = dict(schema='ufeneo.arc-luna.vertical-jump-registration-review.v1', reviewer='root_delegated_by_user',
                  manifest=ref(manifest_path), accepted_for_registration=True,
                  accepted_for_formal_main_candidate=True, approval_scope='仅当前主游戏候选注册和验证，不是美术验收或正式开放',
                  admission_basis='源审者实看4张完整原源审图及17相完整atlas，核对全部17张原件SHA；当前9相核159整图逐像素注册；非继承旧审批',
                  ground_change='land01近侧后脚支撑底由284到280，整图上移4px；takeoff01已离地，保持不动；其余8相同像素',
                  air_root_caveat='空中髋表面粗代理约±20源像素≈±3.1运行像素；未严格骨尺验收',
                  pending=['真实输入与独立回放', '当前主游戏双向720/1080图形', '起落及回架接续、头身比例严格核验'],
                  source_artifacts_unchanged=True, Godot_started=False, POST_count=0, **flags)
    put(OUT / 'root-review.json', review)
    print(json.dumps({'manifest': ref(manifest_path), 'frames': 9, 'pixel_comparison_passed': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()

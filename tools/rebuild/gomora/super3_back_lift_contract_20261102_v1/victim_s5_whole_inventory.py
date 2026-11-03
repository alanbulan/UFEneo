"""只读九对象S5完整格；报告缩略图不生成或安装任何运行资源。"""
from pathlib import Path
import argparse
import hashlib
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'reports/review/2026-11-02/gomora-super3-victim-s5-whole-inventory-v1'
FIGHTERS = ['zetton', 'ultraseven', 'ultraman-arc', 'ultraman-blazar',
            'ultraman-omega', 'ultraman-teo', 'ex_gomora', 'ex_red_king', 'gomora']
GROUPS = {
    'hit': ['hit_high', 'hit_mid', 'hit_crouch', 'hit_air'],
    'flight-floor': ['launch_rise', 'launch_fall', 'bounce', 'down', 'defeat'],
    'throw': ['grabbed', 'thrown_forward', 'thrown_back', 'thrown_air', 'thrown_dash'],
}

def rec(path):
    return {'path': path.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def read(path):
    return json.loads(path.read_text('utf-8-sig'))

def run(fighter):
    dest = OUT / fighter
    assert not dest.exists(), dest
    dest.mkdir(parents=True)
    mp = ROOT / f'assets/fighters/{fighter}/animations/manifest.json'
    sp = ROOT / f'content/fighters/{fighter}/state_frames.json'
    manifest, states = read(mp), read(sp)
    keys = [key for group in GROUPS.values() for key in group]
    max_w = max(manifest['clips'][key]['rects'][0][2] for key in keys)
    scale = 192 / max_w
    records, pages = [], []
    for group, group_keys in GROUPS.items():
        row_heights = [round(max(r[3] for r in manifest['clips'][key]['rects']) * scale) + 24
                       for key in group_keys]
        page = Image.new('RGB', (768, 30 + sum(row_heights)), '#242934')
        draw = ImageDraw.Draw(page)
        draw.text((4, 7), f'{fighter} / {group} / full manifest cells / uniform scale {scale:.4f}', fill='white')
        top = 30
        for key, row_h in zip(group_keys, row_heights):
            clip = manifest['clips'][key]
            ap = ROOT / clip['texture'].removeprefix('res://')
            atlas = Image.open(ap).convert('RGBA')
            assert len(clip['rects']) <= 4
            offset = int(clip.get('simulation_sprite_offset', 0))
            for index, rect in enumerate(clip['rects']):
                x, y, w, h = map(int, rect)
                frame = atlas.crop((x, y, x + w, y + h))
                small = frame.resize((round(w * scale), round(h * scale)), Image.Resampling.NEAREST)
                page.paste(small, (index * 192, top + 24), small)
                draw.text((index * 192 + 4, top + 5), f'{key}:{index}', fill='white')
                actual = [dict(tick=tick, data=data) for tick, data in enumerate(states.get(key, []))
                          if max(0, min(len(clip['rects']) - 1, int(data.get('sprite', 0)) - offset)) == index]
                records.append(dict(clip=key, frame=index, source_atlas=rec(ap), source_rect=rect,
                    anchor=clip.get('anchors', [])[index] if clip.get('anchors') else
                    [int(clip.get('cell', w)) // 2, int(clip.get('anchor_y', h))],
                    simulation_sprite_offset=offset, state_frames_consumers=actual,
                    ending_clip_uses_presentation_tick=(key == 'defeat'),
                    ending_ticks=clip.get('ticks', []) if key == 'defeat' else [],
                    image_bbox=frame.getbbox(), actual_visual_review_pending=True))
            top += row_h
        image_path = dest / f'{fighter}-{group}-whole-cells.jpg'
        page.save(image_path, quality=80, optimize=True)
        assert image_path.stat().st_size <= 150000
        pages.append(rec(image_path))
    result = dict(fighter=fighter, manifest=rec(mp), state_frames=rec(sp), pages=pages,
        report_uniform_scale=scale, records=records,
        absent_requested_clips=[key for key in ['air_hit', 'trip'] if key not in manifest['clips']],
        excluded_attack_clip='launcher',
        runtime_contract_sources=[rec(ROOT / p) for p in ['core/fighters/fighter.gd', 'presentation/side_view.gd']],
        runtime_consumption='animation_key与同名state_frames；sprite减simulation_sprite_offset后clamp到manifest索引；defeat按presentation结束时钟消费clip.ticks。此为只读文件绑定，未运行Godot。',
        transformations='完整manifest rect裁格；整对象统一nearest缩放；无bbox归中、旋转、变形、改色或拼件。',
        actual_visual_review_pending=True, runtime_changed=False, godot_run=False)
    with (dest / 'inventory.json').open('x', encoding='utf-8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(json.dumps({'fighter': fighter, 'pages': pages}, ensure_ascii=False))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fighters', nargs='+', choices=FIGHTERS)
    for name in parser.parse_args().fighters:
        run(name)

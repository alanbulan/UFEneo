"""亚刻22+O旋身双肘：按实际整帧画布接入纯物理近战，无新特效。"""
from __future__ import annotations

import argparse
import copy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / 'art/fighters/ultraman-arc/stage6/elbow-runtime-20261030-v1'
OUT = ROOT / 'reports/review/2026-10-30/arc-s6-elbow-v1'
CONTENT = ROOT / 'content/fighters/ultraman-arc'
ASSETS = ROOT / 'assets/fighters/ultraman-arc/animations'
CONTRACT = ART / 'runtime-contract.json'
MOVE = 'motion_22'


def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rel(path): return Path(path).resolve().relative_to(ROOT).as_posix()


def local(path):
    result = (ROOT / str(path).removeprefix('res://')).resolve()
    assert result.is_relative_to(ROOT)
    return result


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name + '.arc-elbow.pending')
    assert not pending.exists(), '保留未决写入：' + str(pending)
    pending.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    pending.replace(path)


def boxes(values, required=False):
    assert isinstance(values, list) and (values or not required)
    for box in values:
        assert len(box) == 4 and all(type(v) is int for v in box) and box[2] > 0 and box[3] > 0


def build():
    assert read(CONTENT / 'production_plan.json')['stage6_authorized'] is True
    selection, contract = read(ART / 'sources.json'), read(CONTRACT)
    assert sha(local(selection['candidate'])) == selection['candidate_sha256']
    assert len(selection['frames']) == 12 and [r['frame'] for r in selection['frames']] == list(range(12))
    canvas, anchor, ticks = contract['canvas'], contract['anchor'], contract['ticks']
    assert len(canvas) == 2 and canvas[0] == canvas[1] and len(anchor) == 2
    assert len(ticks) == 12 and all(type(v) is int and v > 0 for v in ticks)
    assert [f['frame'] for f in contract['frames']] == list(range(12))
    atlas = Image.new('RGBA', (canvas[0] * 12, canvas[1]))
    for i, row in enumerate(selection['frames']):
        assert all(sha(local(row[key])) == row[key + '_sha256'] for key in ['source', 'image'])
        with Image.open(local(row['image'])) as image:
            assert image.mode == 'RGBA' and list(image.size) == canvas
            colors = image.getchannel('A').getcolors(256)
            assert colors is not None and {value for _, value in colors} == {0, 255}
            assert image.getchannel('A').getbbox()[3] == anchor[1]
            atlas.paste(image, (i * canvas[0], 0))
            assert atlas.crop((i * canvas[0], 0, (i + 1) * canvas[0], canvas[1])).tobytes() == image.tobytes()
    output = BytesIO()
    atlas.save(output, format='PNG')
    atlas_bytes = output.getvalue()
    template_path = ROOT / 'content/templates/humanoid/moves/motion_22.json'
    template = read(template_path)
    assert len(template['frames']) == 23 and [template[k] for k in ['startup', 'active', 'recovery', 'damage', 'stamina_cost', 'energy_cost', 'kind', 'launch']] == [8, 3, 12, 115, 30, 0, 'strike', False]
    move = copy.deepcopy(template)
    move.update(display_name='旋身双肘震退', **{k: int(contract[k]) for k in ['startup', 'active', 'recovery']})
    assert sum(move[k] for k in ['startup', 'active', 'recovery']) == sum(ticks)
    move['feedback'].update(copy.deepcopy(contract.get('feedback', {})))
    assert move['feedback']['spark'] == 'impact_heavy' and move['feedback']['block_spark'] == 'impact_guard'
    audio = copy.deepcopy(contract.get('audio', {'hit': 'heavy', 'block': 'block'}))
    assert audio == {'hit': 'heavy', 'block': 'block'}
    # 接触自定义路由不走cue(contact=true)，必须用实际声音ID，不能把heavy挥空别名当命中声。
    move['audio'] = {'hit': 'hit_heavy', 'block': 'guard'}
    move['review_fixture_gap'] = int(contract.get('fixture_gap', 60))
    move['review_whiff_gap'] = int(contract.get('whiff_gap', 400))
    move['review_still_tick'] = int(contract.get('still_tick', move['startup'] + 1))
    move['frames'] = []
    for sprite, duration in enumerate(ticks):
        geometry = contract['frames'][sprite]
        boxes(geometry['hurtboxes'], True)
        boxes(geometry['hitboxes'])
        for _ in range(duration):
            tick = len(move['frames'])
            move['frames'].append(dict(sprite=sprite, dx=0, dy=0, velocity=[0, 0],
                hitboxes=copy.deepcopy(geometry['hitboxes']), hurtboxes=copy.deepcopy(geometry['hurtboxes']),
                cancel=[], events=copy.deepcopy(contract.get('events_by_tick', {}).get(str(tick), template['frames'][0]['events'] if tick == 0 else [])),
                attachments=[], impact_effect='impact_heavy', block_effect='impact_guard'))
    assert any(f['hitboxes'] for f in move['frames'])
    assert all(e['kind'] == 'sound' and e['id'] == 'heavy' for f in move['frames'] for e in f['events'])
    move['production_note'] = '本人12独立纯物理整帧，22+O旋身双肘；按真实肘缘有前后两个挥击窗口，同敌同次沿既有connected最多一次115伤，无屏障/弹体/额外FX。'
    clip = dict(texture='res://assets/fighters/ultraman-arc/animations/motion_22/atlas.png', cell=canvas[0],
        anchor=anchor, anchor_y=anchor[1], anchors=[anchor[:] for _ in ticks],
        rects=[[i * canvas[0], 0, *canvas] for i in range(12)], ticks=ticks, loop=False,
        atlas_sha256=hashlib.sha256(atlas_bytes).hexdigest(), curation=rel(ART / 'sources.json'), audio_events=[],
        motion_review=dict(executor_approved=True, user_approved=False, art_passed=False,
            verdict='training_installed_with_known_visual_issues', all_frames_independent=True, review=rel(OUT / 'README.md')))
    command = copy.deepcopy(next(c for c in read(ROOT / 'content/templates/humanoid/command_table.json') if c['move'] == MOVE))
    assert command['buttons'] == 64 and command['motion'] == [2, 5, 2]
    command['display_name'] = '旋身双肘震退'
    changes = dict(template=rel(template_path), template_sha256=sha(template_path), original_ticks=23, installed_ticks=len(move['frames']),
        original_windows=[8, 3, 12], installed_windows=[move[k] for k in ['startup', 'active', 'recovery']],
        preserved_values={k: template[k] for k in ['damage', 'stamina_cost', 'energy_cost', 'kind', 'level', 'launch']},
        actual_canvas=canvas, actual_anchor=anchor, shared_core_changed=False)
    return dict(move=move, clip=clip, command=command, atlas_bytes=atlas_bytes, contract=contract, changes=changes)


def install():
    assert (ROOT / 'art/shared/locks/godot.lock').is_file(), '安装须由根持唯一Godot锁'
    assert OUT.is_dir() and not (OUT / 'installed.json').exists(), '原安装记录不覆盖'
    bundle = build()
    paths = [ASSETS / 'manifest.json', CONTENT / 'definition.json', CONTENT / 'command_table.json']
    original = [read(p) for p in paths]
    manifest, definition, commands = copy.deepcopy(original)
    assert definition['playable'] is False and definition.get('pilot_playable') is True
    assert MOVE in definition['unsupported_moves'] and MOVE not in manifest['clips'] and not any(c['move'] == MOVE for c in commands)
    assert not (CONTENT / 'moves/motion_22.json').exists() and not (ASSETS / MOVE).exists()
    archive = (ROOT.parent / 'UFEneo_archive/2026-10-30/arc-s6-elbow-v1').resolve()
    assert archive.is_relative_to((ROOT.parent / 'UFEneo_archive').resolve()) and not archive.exists()
    protected = {rel(p): sha(p) for base in [CONTENT, ASSETS, ROOT / 'assets/effects/ultraman-arc']
        for p in base.rglob('*') if p.is_file() and p.suffix in ['.json', '.png']}
    protected[rel(ROOT / 'content/presentation/phase3_projectiles.json')] = sha(ROOT / 'content/presentation/phase3_projectiles.json')
    backups = []
    for path in paths:
        backup = archive / path.relative_to(ROOT)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        assert sha(path) == sha(backup)
        backups.append(dict(path=rel(path), sha256=sha(path), archive=str(backup)))
    manifest['clips'][MOVE] = bundle['clip']
    definition['unsupported_moves'].remove(MOVE)
    commands.append(bundle['command'])
    assert {k: v for k, v in manifest['clips'].items() if k != MOVE} == original[0]['clips']
    restored = copy.deepcopy(definition)
    restored['unsupported_moves'] = original[1]['unsupported_moves']
    assert restored == original[1] and commands[:-1] == original[2]
    texture = ASSETS / MOVE / 'atlas.png'
    texture.parent.mkdir(parents=True, exist_ok=False)
    texture.write_bytes(bundle['atlas_bytes'])
    save(CONTENT / 'moves/motion_22.json', bundle['move'])
    for path, value in zip(paths, [manifest, definition, commands]): save(path, value)
    allowed = {rel(p) for p in paths}
    assert all(sha(ROOT / p) == h for p, h in protected.items() if p not in allowed)
    save(OUT / 'installed.json', dict(backups=backups, before=protected, changed_files=[rel(p) for p in paths + [texture, CONTENT / 'moves/motion_22.json']],
        template_changes=bundle['changes'], runtime_contract_sha256=sha(CONTRACT), source_selection_sha256=sha(ART / 'sources.json'),
        old_resources_unchanged=True, shared_core_untouched=True, playable=False, stage6_authorized=True,
        user_approved=False, new_image_requests_by_this_installer=0, generated_videos=0, git_operations=0))
    print('亚刻22+O旋身双肘已接训练；待真实物理肘击与原输入回放', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['check', 'install'], nargs='?', default='check')
    args = parser.parse_args()
    if args.command == 'install': install()
    else:
        bundle = build()
        print(json.dumps(dict(read_only=True, command=bundle['command'], changes=bundle['changes'], generated_videos=0), ensure_ascii=False))


if __name__ == '__main__': main()

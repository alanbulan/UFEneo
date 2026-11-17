"""亚刻214I回身二连与6I掷返：仅本人整帧、两拍刃缘及独立返剑的有限安装。"""
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
ART = ROOT / 'art/fighters/ultraman-arc/stage6/sword-followups-runtime-20261030-v1'
OUT = ROOT / 'reports/review/2026-10-30/arc-s6-sword-followups-v1'
CONTENT = ROOT / 'content/fighters/ultraman-arc'
ASSETS = ROOT / 'assets/fighters/ultraman-arc/animations'
EFFECTS = ROOT / 'content/presentation/phase3_projectiles.json'
CONTRACT = ART / 'runtime-contract.json'
MOVES = ['motion_214', 'ranged_forward']
COUNTS = {'motion_214': 12, 'ranged_forward': 8}
NAMES = {'motion_214': '回身光剑二连', 'ranged_forward': '光剑掷返'}
FX_FILES = ['atlas.png', 'effect.json', 'provenance.json', 'island-whitelist.json']


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def local(path):
    result = (ROOT / str(path).removeprefix('res://')).resolve()
    assert result.is_relative_to(ROOT)
    return result


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name + '.arc-sword-followups.pending')
    assert not pending.exists(), '保留未决写入：' + str(pending)
    pending.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    pending.replace(path)


def rgba(path, size=None):
    with Image.open(path) as opened:
        assert opened.mode == 'RGBA', '不把RGB原件伪标透明'
        image = opened.copy()
    assert size is None or image.size == size
    colors = image.getchannel('A').getcolors(256)
    assert colors is not None and {value for _, value in colors} == {0, 255}, '须真透明二值Alpha'
    return image


def boxes(value, required=False):
    assert isinstance(value, list) and (value or not required)
    for box in value:
        assert isinstance(box, list) and len(box) == 4 and all(type(v) is int for v in box)
        assert box[2] > 0 and box[3] > 0


def body(selection, identity):
    assert sha(local(selection['candidate'])) == selection['candidate_sha256']
    rows = selection['frames']
    assert len(rows) == COUNTS[identity] and [r['frame'] for r in rows] == list(range(COUNTS[identity]))
    atlas = Image.new('RGBA', (320 * len(rows), 320))
    for i, row in enumerate(rows):
        assert all(sha(local(row[key])) == row[key + '_sha256'] for key in ['source', 'image'])
        image = rgba(local(row['image']), (320, 320))
        assert image.getchannel('A').getbbox()[3] == 280
        atlas.paste(image, (i * 320, 0))
        assert atlas.crop((i * 320, 0, (i + 1) * 320, 320)).tobytes() == image.tobytes()
    output = BytesIO()
    atlas.save(output, format='PNG')
    return output.getvalue()


def build():
    assert read(CONTENT / 'production_plan.json').get('stage6_authorized') is True
    selections, contract = read(ART / 'sources.json'), read(CONTRACT)
    assert set(selections['actions']) == set(MOVES) and set(contract['actions']) == set(MOVES)
    effects = copy.deepcopy(read(EFFECTS))
    new_effects = list(contract.get('new_effects', []))
    for action in contract['actions'].values(): new_effects += action.get('new_effects', [])
    additions, known = [], set()
    for item in new_effects:
        identity, source = item['id'], local(item['source_directory'])
        assert identity.startswith('arc_') and source.is_dir()
        if identity in known: continue
        known.add(identity)
        assert all((source / name).is_file() for name in FX_FILES)
        effect = copy.deepcopy(read(source / 'effect.json'))
        destination = local(effect['texture']).parent
        assert destination.is_relative_to((ROOT / 'assets/effects/ultraman-arc').resolve())
        assert local(effect['texture']).name == 'atlas.png'
        assert sha(source / 'atlas.png') == effect['atlas_sha256'] and effect['display_scale'] == [1, 1]
        rgba(source / 'atlas.png')
        effect['not_installed'] = False
        assert identity not in effects or effects[identity] == effect, '同名既有FX不得替换'
        effects[identity] = effect
        additions.append(dict(id=identity, source=source, destination=destination, effect=effect))
    actions, used_ids = {}, set()
    for identity in MOVES:
        spec = contract['actions'][identity]
        template_path = ROOT / f'content/templates/humanoid/moves/{identity}.json'
        template = read(template_path)
        assert [template[k] for k in ['startup', 'active', 'recovery', 'stamina_cost', 'energy_cost']] == [8, 3, 12, 30, 0]
        assert template['damage'] == (115 if identity == 'motion_214' else 95)
        assert len(template['frames']) == 23 and template['launch'] is False
        ticks = spec['ticks']
        assert len(ticks) == COUNTS[identity] and all(type(v) is int and v > 0 for v in ticks)
        assert [f['frame'] for f in spec['frames']] == list(range(COUNTS[identity]))
        move = copy.deepcopy(template)
        move.update(display_name=NAMES[identity], **{key: int(spec[key]) for key in ['startup', 'active', 'recovery']})
        assert sum(move[key] for key in ['startup', 'active', 'recovery']) == sum(ticks)
        move['feedback'].update(copy.deepcopy(spec.get('feedback', {})))
        move['audio'] = copy.deepcopy(spec['audio'])
        assert all(move['audio'].get(key, '').startswith('arc_') for key in ['hit', 'block'])
        move['review_fixture_gap'] = int(spec.get('fixture_gap', 80))
        move['review_whiff_gap'] = int(spec.get('whiff_gap', 600))
        move['review_still_tick'] = int(spec.get('still_tick', sum(ticks[:8]) + 1 if identity == 'motion_214' else int(spec['release_tick']) + 5))
        shots_by_tick = copy.deepcopy(spec.get('shots_by_tick', {}))
        if identity == 'ranged_forward':
            projectile = copy.deepcopy(spec['projectile'])
            release = int(spec['release_tick'])
            assert str(release) not in shots_by_tick and 0 < release < sum(ticks)
            shots_by_tick[str(release)] = [projectile]
            assert projectile['integer_path'] and all(len(p) == 2 and all(type(v) is int for v in p) for p in projectile['integer_path'])
            assert projectile['speed'] == 0 and projectile['return_ticks'] > 0 and projectile['max_hits'] == 1
            assert identity in projectile['locked_moves'] and len(projectile['return_anchor']) == 2
            assert projectile['life'] > len(projectile['integer_path']) + projectile['return_ticks']
            assert release + len(projectile['integer_path']) + projectile['return_ticks'] < sum(ticks), '回剑须在本招独立接柄收势内完成'
            move['projectile'] = projectile
        else:
            assert not shots_by_tick, '回身二连须真实近战，不以弹体替代挥剑'
            assert {f['frame'] for f in spec['frames'] if f['hitboxes']} == {4, 5, 7, 8, 9}
        frames = []
        for sprite, duration in enumerate(ticks):
            geometry = spec['frames'][sprite]
            boxes(geometry['hurtboxes'], True)
            boxes(geometry['hitboxes'])
            assert identity != 'ranged_forward' or not geometry['hitboxes'], '投剑只由唯一脱手物判定'
            for _ in range(duration):
                tick = len(frames)
                frame = dict(sprite=sprite, dx=0, dy=0, velocity=[0, 0], hitboxes=copy.deepcopy(geometry['hitboxes']),
                    hurtboxes=copy.deepcopy(geometry['hurtboxes']), cancel=[],
                    events=copy.deepcopy(spec.get('events_by_tick', {}).get(str(tick), [])),
                    attachments=copy.deepcopy(spec.get('attachments_by_tick', {}).get(str(tick), [])),
                    impact_effect=move['feedback']['spark'], block_effect=move['feedback']['block_spark'])
                if str(tick) in shots_by_tick: frame['shots'] = copy.deepcopy(shots_by_tick[str(tick)])
                if str(tick) in spec.get('weapon_return_anchor_by_tick', {}):
                    frame['weapon_return_anchor'] = list(spec['weapon_return_anchor_by_tick'][str(tick)])
                for attachment in frame['attachments']:
                    fx = effects[attachment['effect']]
                    assert 0 <= attachment['sprite'] < len(fx['rects']) and len(attachment['anchor']) == 2
                    used_ids.add(attachment['effect'])
                for shot in frame.get('shots', []):
                    assert shot['effect'] in effects and len(shot['spawn']) == 2
                    boxes([shot['box']], True)
                    for phase in shot.get('frame_hitboxes', []): boxes(phase, True)
                    used_ids.add(shot['effect'])
                    if shot.get('trail_effect'): used_ids.add(shot['trail_effect'])
                frames.append(frame)
        assert all(0 <= int(key) < len(frames) for key in shots_by_tick)
        move['frames'] = frames
        move['production_note'] = ('本人12独立持剑整帧；214I回身二连，4/5相背侧与7/8/9相前侧各有真实刃缘近战框。沿既有connected规则，同次招式对同敌最多接触一次115伤，不承诺两次伤害；无弹体替代或共享核心改动。'
            if identity == 'motion_214' else '本人8独立投剑整帧，6I；脱手独立GPT完整剑体及逐tick整数外飞/回程，回到真实接柄点后weapon_return，不以过期消失冒充回收。')
        atlas_bytes = body(selections['actions'][identity], identity)
        clip = dict(texture=f'res://assets/fighters/ultraman-arc/animations/{identity}/atlas.png', cell=320,
            anchor=[160, 280], anchor_y=280, anchors=[[160, 280] for _ in ticks],
            rects=[[i * 320, 0, 320, 320] for i in range(len(ticks))], ticks=ticks, loop=False,
            atlas_sha256=hashlib.sha256(atlas_bytes).hexdigest(), curation=rel(ART / 'sources.json'), audio_events=[],
            motion_review=dict(executor_approved=True, user_approved=False, art_passed=False,
                verdict='training_installed_with_known_visual_issues', all_frames_independent=True, review=rel(OUT / 'README.md')))
        command = copy.deepcopy(next(c for c in read(ROOT / 'content/templates/humanoid/command_table.json') if c['move'] == identity))
        assert command['buttons'] == 128 and command['motion'] == ([2, 1, 4] if identity == 'motion_214' else [])
        assert identity != 'ranged_forward' or command['directions'] == [6]
        command['display_name'] = NAMES[identity]
        used_ids.update([move['feedback']['spark'], move['feedback']['block_spark']])
        changes = dict(template=rel(template_path), template_sha256=sha(template_path), original_ticks=23, installed_ticks=len(frames),
            original_windows=[8, 3, 12], installed_windows=[move[k] for k in ['startup', 'active', 'recovery']],
            preserved_values={k: template[k] for k in ['damage', 'stamina_cost', 'energy_cost', 'kind', 'level', 'launch']},
            shot_ticks=sorted(int(t) for t in shots_by_tick), shared_core_changed=False)
        actions[identity] = dict(move=move, clip=clip, command=command, atlas_bytes=atlas_bytes, changes=changes)
    used = {}
    for key in sorted(used_ids):
        assert key in effects
        addition = next((r for r in additions if r['id'] == key), None)
        texture = addition['source'] / 'atlas.png' if addition else local(effects[key]['texture'])
        used[key] = dict(effect=effects[key], atlas_sha256=sha(texture))
    return dict(actions=actions, effects=effects, additions=additions, used_effects=used, contract=contract)


def install():
    assert (ROOT / 'art/shared/locks/godot.lock').is_file(), '安装须由根持唯一Godot锁'
    assert OUT.is_dir() and not (OUT / 'installed.json').exists(), '原安装记录不覆盖'
    bundle = build()
    paths = [ASSETS / 'manifest.json', CONTENT / 'definition.json', CONTENT / 'command_table.json']
    if bundle['additions']: paths.append(EFFECTS)
    original = [read(p) for p in paths]
    manifest, definition, commands = copy.deepcopy(original[:3])
    assert definition['playable'] is False and definition.get('pilot_playable') is True
    assert all(move in definition['unsupported_moves'] and move not in manifest['clips'] for move in MOVES)
    assert not any(c['move'] in MOVES for c in commands)
    assert all(not (CONTENT / f'moves/{move}.json').exists() and not (ASSETS / move).exists() for move in MOVES)
    assert all(not item['destination'].exists() for item in bundle['additions'])
    archive = (ROOT.parent / 'UFEneo_archive/2026-10-30/arc-s6-sword-followups-v1').resolve()
    assert archive.is_relative_to((ROOT.parent / 'UFEneo_archive').resolve()) and not archive.exists()
    protected = {rel(p): sha(p) for base in [CONTENT, ASSETS, ROOT / 'assets/effects/ultraman-arc']
                 for p in base.rglob('*') if p.is_file() and p.suffix in ['.json', '.png']}
    protected[rel(EFFECTS)] = sha(EFFECTS)
    backups = []
    for path in paths:
        backup = archive / path.relative_to(ROOT)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        assert sha(path) == sha(backup)
        backups.append(dict(path=rel(path), sha256=sha(path), archive=str(backup)))
    changed = list(paths)
    for identity, action in bundle['actions'].items():
        manifest['clips'][identity] = action['clip']
        definition['unsupported_moves'].remove(identity)
        commands.append(action['command'])
        texture = ASSETS / identity / 'atlas.png'
        texture.parent.mkdir(parents=True, exist_ok=False)
        texture.write_bytes(action['atlas_bytes'])
        save(CONTENT / f'moves/{identity}.json', action['move'])
        changed += [texture, CONTENT / f'moves/{identity}.json']
    assert {k: v for k, v in manifest['clips'].items() if k not in MOVES} == original[0]['clips']
    restored = copy.deepcopy(definition)
    restored['unsupported_moves'] = original[1]['unsupported_moves']
    assert restored == original[1] and commands[:-len(MOVES)] == original[2]
    for item in bundle['additions']:
        item['destination'].mkdir(parents=True, exist_ok=False)
        for filename in FX_FILES:
            shutil.copy2(item['source'] / filename, item['destination'] / filename)
            assert sha(item['source'] / filename) == sha(item['destination'] / filename)
            changed.append(item['destination'] / filename)
        save(item['destination'] / 'effect.json', item['effect'])
        for filename in ['provenance.json', 'island-whitelist.json']:
            value = read(item['destination'] / filename)
            value.update(not_installed=False, runtime_review=rel(OUT / 'README.md'))
            save(item['destination'] / filename, value)
    values = [manifest, definition, commands] + ([bundle['effects']] if bundle['additions'] else [])
    for path, value in zip(paths, values): save(path, value)
    allowed = {rel(p) for p in paths}
    assert all(sha(ROOT / path) == digest for path, digest in protected.items() if path not in allowed)
    save(OUT / 'installed.json', dict(backups=backups, before=protected, changed_files=[rel(p) for p in changed],
        template_changes={key: value['changes'] for key, value in bundle['actions'].items()}, used_effects=bundle['used_effects'],
        runtime_contract=rel(CONTRACT), runtime_contract_sha256=sha(CONTRACT), source_selection_sha256=sha(ART / 'sources.json'),
        old_resources_unchanged=True, shared_core_untouched=True, playable=False, stage6_authorized=True,
        user_approved=False, new_image_requests_by_this_installer=0, generated_videos=0, git_operations=0))
    print('亚刻214I回身二连与6I光剑掷返已接训练；待真实两拍/返剑与独立回放', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['check', 'install'], nargs='?', default='check')
    args = parser.parse_args()
    if args.command == 'install': install()
    else:
        bundle = build()
        print(json.dumps(dict(read_only=True, actions={key: value['changes'] for key, value in bundle['actions'].items()},
            new_effects=[row['id'] for row in bundle['additions']], generated_videos=0), ensure_ascii=False))


if __name__ == '__main__':
    main()

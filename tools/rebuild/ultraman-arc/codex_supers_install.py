"""亚刻三级及空中Arc Finalize：完整本人RGBA、既有GPT特效的有限安装。"""
from __future__ import annotations

import argparse
import copy
import hashlib
from io import BytesIO
from pathlib import Path
import shutil

from PIL import Image

from codex_sword_followups_install import FX_FILES, boxes, local, read, rel, rgba, sha
from codex_elbow_install import save

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / 'art/fighters/ultraman-arc/stage6/supers-runtime-20261030-v1'
OUT = ROOT / 'reports/review/2026-10-30/arc-s6-supers-v1'
CONTENT = ROOT / 'content/fighters/ultraman-arc'
ASSETS = ROOT / 'assets/fighters/ultraman-arc/animations'
EFFECTS = ROOT / 'content/presentation/phase3_projectiles.json'
SUPERS = ROOT / 'content/presentation/supers.json'
CONTRACT = ART / 'runtime-contract.json'
MOVES = ['special', 'special2', 'special3', 'air_special']
COUNTS = dict(zip(MOVES, [14, 16, 16, 8]))
NAMES = dict(zip(MOVES, ['亚刻光线·一级', '亚刻光线·二级', '亚刻光线·三级', '空中亚刻光线短束']))
VALUES = dict(zip(MOVES, [(36, 24, 24, 180, 40, 1000), (48, 24, 24, 300, 50, 2000),
                         (48, 24, 24, 480, 60, 3000), (12, 18, 18, 145, 30, 1000)]))


def body(selection, identity, canvas, anchor):
    assert sha(local(selection['candidate'])) == selection['candidate_sha256']
    rows = selection['frames']
    assert len(rows) == COUNTS[identity] and [r['frame'] for r in rows] == list(range(COUNTS[identity]))
    atlas = Image.new('RGBA', (canvas[0] * len(rows), canvas[1]))
    for i, row in enumerate(rows):
        assert all(sha(local(row[key])) == row[key + '_sha256'] for key in ['source', 'image'])
        image = rgba(local(row['image']), tuple(canvas))
        if identity != 'air_special': assert image.getchannel('A').getbbox()[3] == anchor[1]
        atlas.paste(image, (i * canvas[0], 0))
        assert atlas.crop((i * canvas[0], 0, (i + 1) * canvas[0], canvas[1])).tobytes() == image.tobytes()
    output = BytesIO()
    atlas.save(output, format='PNG')
    return output.getvalue()


def build():
    assert read(CONTENT / 'production_plan.json').get('stage6_authorized') is True
    selections, contract = read(ART / 'sources.json'), read(CONTRACT)
    assert set(selections['actions']) == set(contract['actions']) == set(MOVES)
    effects = copy.deepcopy(read(EFFECTS))
    additions, known = [], set()
    new_effects = list(contract.get('new_effects', []))
    for spec in contract['actions'].values(): new_effects += spec.get('new_effects', [])
    for item in new_effects:
        identity, source = item['id'], local(item['source_directory'])
        assert identity.startswith('arc_') and source.is_dir()
        if identity in known: continue
        known.add(identity)
        assert all((source / name).is_file() for name in FX_FILES)
        effect = copy.deepcopy(read(source / 'effect.json'))
        destination = local(effect['texture']).parent
        assert destination.is_relative_to((ROOT / 'assets/effects/ultraman-arc').resolve())
        assert local(effect['texture']).name == 'atlas.png' and effect['display_scale'] == [1, 1]
        assert sha(source / 'atlas.png') == effect['atlas_sha256']
        rgba(source / 'atlas.png')
        effect['not_installed'] = False
        assert identity not in effects or effects[identity] == effect, '同名既有FX不得替换'
        effects[identity] = effect
        additions.append(dict(id=identity, source=source, destination=destination, effect=effect))
    mapping = copy.deepcopy(contract['supers_mapping'])
    assert set(mapping) <= {'portrait', 'background', 'background_z_index'} and {'portrait', 'background'} <= set(mapping)
    for key in ['portrait', 'background']:
        texture = local(mapping[key])
        addition = next((r for r in additions if local(r['effect']['texture']) == texture), None)
        assert (addition['source'] / 'atlas.png' if addition else texture).is_file(), '三级演出贴图缺失'
    template_path = ROOT / 'content/templates/humanoid/moves/special.json'
    template = read(template_path)
    sounds = read(ROOT / 'content/audio/runtime.json')['sounds']
    commands = copy.deepcopy([c for c in read(ROOT / 'content/templates/humanoid/command_table.json')
                              if c['move'] in ['special', 'air_special']])
    assert [(c['move'], c['buttons']) for c in commands] == [('special', 32), ('special', 3), ('air_special', 32)]
    for command in commands: command['display_name'] = '亚刻光线（按能量分级）' if command['move'] == 'special' else NAMES['air_special']
    actions, used_ids, sound_ids = {}, set(known), set()
    for identity in MOVES:
        spec = contract['actions'][identity]
        canvas, anchor = spec.get('canvas', contract.get('canvas', [320, 320])), spec.get('anchor', contract.get('anchor', [160, 280]))
        assert canvas == [320, 320] and anchor == [160, 280]
        ticks = spec['ticks']
        assert len(ticks) == COUNTS[identity] and all(type(v) is int and v > 0 for v in ticks)
        assert [f['frame'] for f in spec['frames']] == list(range(COUNTS[identity]))
        scalars = ['startup', 'active', 'recovery', 'damage', 'stamina_cost', 'energy_cost']
        assert tuple(spec[key] for key in scalars) == VALUES[identity]
        assert sum(spec[key] for key in scalars[:3]) == sum(ticks)
        move = copy.deepcopy(template)
        move.update(id=identity, display_name=spec.get('display_name', NAMES[identity]),
                    **{key: int(spec[key]) for key in scalars})
        move.update(kind='projectile', manual_projectiles=True, air_allowed=identity == 'air_special',
                    super_level=1 if identity == 'air_special' else MOVES.index(identity) + 1)
        for key in ['chip_damage', 'hitstun', 'blockstun', 'pushback', 'stun', 'knockdown', 'launch', 'bounce', 'unblockable', 'stamina_regen']:
            if key in spec: move[key] = copy.deepcopy(spec[key])
        if identity == 'air_special': move['finish_on_landing'] = bool(spec.get('finish_on_landing', True))
        move['feedback'].update(copy.deepcopy(spec.get('feedback', {})))
        move['audio'] = copy.deepcopy(spec.get('audio', {'hit': 'hit_heavy', 'block': 'guard'}))
        assert all(key in sounds for key in move['audio'].values()), '接触声须用真实声音ID'
        sound_ids.update(move['audio'].values())
        move['review_fixture_gap'] = int(spec.get('fixture_gap', 180 if identity != 'air_special' else 220))
        move['review_whiff_gap'] = int(spec.get('whiff_gap', 700))
        move['review_still_tick'] = int(spec.get('still_tick', 1 if identity == 'special3' else spec['startup'] + 1))
        maps = {key: spec.get(key, {}) for key in ['events_by_tick', 'attachments_by_tick', 'shots_by_tick',
                'beam_origin_by_tick', 'cinematic_by_tick', 'velocity_by_tick', 'audio_loop_by_tick']}
        assert all(str(int(key)) == key and 0 <= int(key) < sum(ticks) for values in maps.values() for key in values)
        move['projectile'] = copy.deepcopy(spec['projectile'])
        frames, shots = [], []
        for sprite, duration in enumerate(ticks):
            geometry = spec['frames'][sprite]
            boxes(geometry['hurtboxes'], True)
            assert geometry['hitboxes'] == [], '必杀只由唯一真实束判定'
            for _ in range(duration):
                key = str(len(frames))
                frame = dict(sprite=sprite, dx=0, dy=0, hitboxes=[], hurtboxes=copy.deepcopy(geometry['hurtboxes']), cancel=[],
                    events=copy.deepcopy(maps['events_by_tick'].get(key, [])), attachments=copy.deepcopy(maps['attachments_by_tick'].get(key, [])),
                    impact_effect=move['feedback']['spark'], block_effect=move['feedback']['block_spark'])
                if identity != 'air_special': frame['velocity'] = [0, 0]
                if key in maps['velocity_by_tick']:
                    velocity = maps['velocity_by_tick'][key]
                    assert len(velocity) == 2 and all(type(v) is int for v in velocity)
                    frame['velocity'] = copy.deepcopy(velocity)
                if key in maps['beam_origin_by_tick']: frame['beam_origin'] = copy.deepcopy(maps['beam_origin_by_tick'][key])
                cinematic = maps['cinematic_by_tick'].get(key, {})
                assert set(cinematic) <= {'pause_clock', 'freeze_opponent', 'cinematic_stage', 'audio_loop'}
                assert cinematic.get('freeze_opponent', False) is False
                frame.update(copy.deepcopy(cinematic))
                if key in maps['audio_loop_by_tick']: frame['audio_loop'] = maps['audio_loop_by_tick'][key]
                if frame.get('audio_loop'): sound_ids.add(frame['audio_loop'])
                for event in frame['events']:
                    assert event['kind'] == 'sound' and event['id'] in sounds
                    sound_ids.add(event['id'])
                for attached in frame['attachments']:
                    fx = effects[attached['effect']]
                    assert 0 <= attached['sprite'] < len(fx['rects']) and len(attached['anchor']) == 2
                    used_ids.add(attached['effect'])
                if key in maps['shots_by_tick']:
                    frame['shots'] = copy.deepcopy(maps['shots_by_tick'][key])
                    shots += frame['shots']
                frames.append(frame)
        assert len(shots) == 1 and shots[0] == move['projectile'], '每招只生一束，不以多次发射叠伤'
        shot = shots[0]
        assert shot['beam'] is True and shot['speed'] == 0 and int(shot.get('vy', 0)) == 0
        assert shot['effect'] in effects and shot['effect'].startswith('arc_') and len(shot['spawn']) == len(shot['anchor']) == 2
        assert shot['length'] == effects[shot['effect']]['rects'][0][2], '持续束必须整格原生显示，不平铺重复'
        boxes([shot['box']], True)
        for value in shot.get('frame_hitboxes', []): boxes(value)
        assert shot['origin_by_frame'] and all(str(int(k)) == k and 0 <= int(k) < len(frames)
            and len(v) == 2 and all(type(n) is int for n in v) for k, v in shot['origin_by_frame'].items())
        if identity == 'air_special': assert shot.get('clip_below_ground') is True and shot.get('frame_hitboxes')
        used_ids.update([shot['effect'], move['feedback']['spark'], move['feedback']['block_spark']])
        move['frames'] = frames
        move['production_note'] = spec.get('production_note', '本人独立整帧Arc Finalize，专属GPT原生束逐相跟随实际前臂；真实H攒能后P，费用与三级各自定义。能量声明确复用，专属原声仍属S7缺项；美术与用户门未放行。')
        atlas_bytes = body(selections['actions'][identity], identity, canvas, anchor)
        clip = dict(texture=f'res://assets/fighters/ultraman-arc/animations/{identity}/atlas.png', cell=canvas[0],
            anchor=anchor, anchor_y=anchor[1], anchors=[anchor[:] for _ in ticks],
            rects=[[i * canvas[0], 0, *canvas] for i in range(len(ticks))], ticks=ticks, loop=False,
            atlas_sha256=hashlib.sha256(atlas_bytes).hexdigest(), curation=rel(ART / 'sources.json'), audio_events=[],
            motion_review=dict(executor_approved=True, user_approved=False, art_passed=False,
                verdict='training_installed_with_known_visual_issues', all_frames_independent=True, review=rel(OUT / 'README.md')))
        changes = dict(template=rel(template_path), template_sha256=sha(template_path), installed_ticks=len(frames),
            installed_windows=[move[k] for k in scalars[:3]], damage=move['damage'], stamina_cost=move['stamina_cost'],
            energy_cost=move['energy_cost'], shot_ticks=sorted(int(t) for t in maps['shots_by_tick']), shared_core_changed=False)
        actions[identity] = dict(move=move, clip=clip, atlas_bytes=atlas_bytes, changes=changes)
    assert sound_ids <= set(sounds)
    used = {}
    for key in sorted(used_ids):
        assert key in effects
        item = next((r for r in additions if r['id'] == key), None)
        used[key] = dict(effect=effects[key], atlas_sha256=sha(item['source'] / 'atlas.png' if item else local(effects[key]['texture'])))
    return dict(actions=actions, commands=commands, effects=effects, additions=additions, used_effects=used,
                supers_mapping=mapping, sound_ids=sorted(sound_ids), contract=contract)


def install():
    assert (ROOT / 'art/shared/locks/godot.lock').is_file(), '安装须由根持唯一Godot锁'
    assert OUT.is_dir() and not (OUT / 'installed.json').exists(), '原安装记录不覆盖'
    bundle = build()
    paths = [ASSETS / 'manifest.json', CONTENT / 'definition.json', CONTENT / 'command_table.json', EFFECTS, SUPERS]
    original = [read(p) for p in paths]
    manifest, definition, commands, _, supers = copy.deepcopy(original)
    assert definition['playable'] is False and definition.get('pilot_playable') is True
    assert all(move in definition['unsupported_moves'] and move not in manifest['clips'] for move in MOVES)
    assert not any(c['move'] in MOVES for c in commands) and 'ultraman-arc' not in supers
    assert all(not (CONTENT / f'moves/{move}.json').exists() and not (ASSETS / move).exists() for move in MOVES)
    assert all(not item['destination'].exists() for item in bundle['additions'])
    archive = (ROOT.parent / 'UFEneo_archive/2026-10-30/arc-s6-supers-v1').resolve()
    assert archive.is_relative_to((ROOT.parent / 'UFEneo_archive').resolve()) and not archive.exists()
    protected = {rel(p): sha(p) for base in [CONTENT, ASSETS, ROOT / 'assets/effects/ultraman-arc', ROOT / 'core']
                 for p in base.rglob('*') if p.is_file() and p.suffix in ['.json', '.png']}
    protected.update({rel(p): sha(p) for p in (ROOT / 'core').rglob('*.gd')})
    protected.update({rel(p): sha(p) for p in paths})
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
        texture = ASSETS / identity / 'atlas.png'
        texture.parent.mkdir(parents=True, exist_ok=False)
        texture.write_bytes(action['atlas_bytes'])
        save(CONTENT / f'moves/{identity}.json', action['move'])
        changed += [texture, CONTENT / f'moves/{identity}.json']
    commands += bundle['commands']
    supers['ultraman-arc'] = bundle['supers_mapping']
    assert {k: v for k, v in manifest['clips'].items() if k not in MOVES} == original[0]['clips']
    restored = copy.deepcopy(definition)
    restored['unsupported_moves'] = original[1]['unsupported_moves']
    assert restored == original[1] and commands[:-3] == original[2]
    assert {k: v for k, v in bundle['effects'].items() if k not in {r['id'] for r in bundle['additions']}} == original[3]
    assert {k: v for k, v in supers.items() if k != 'ultraman-arc'} == original[4]
    for item in bundle['additions']:
        item['destination'].mkdir(parents=True, exist_ok=False)
        for name in FX_FILES:
            shutil.copy2(item['source'] / name, item['destination'] / name)
            assert sha(item['source'] / name) == sha(item['destination'] / name)
            changed.append(item['destination'] / name)
        save(item['destination'] / 'effect.json', item['effect'])
        for name in ['provenance.json', 'island-whitelist.json']:
            value = read(item['destination'] / name)
            value.update(not_installed=False, runtime_review=rel(OUT / 'README.md'))
            save(item['destination'] / name, value)
    for path, value in zip(paths, [manifest, definition, commands, bundle['effects'], supers]): save(path, value)
    assert all(sha(ROOT / p) == h for p, h in protected.items() if p not in {rel(p) for p in paths})
    save(OUT / 'installed.json', dict(backups=backups, before=protected, changed_files=[rel(p) for p in changed],
        template_changes={key: value['changes'] for key, value in bundle['actions'].items()}, used_effects=bundle['used_effects'],
        supers_mapping=bundle['supers_mapping'], reused_sound_ids=bundle['sound_ids'], dedicated_voice_pending_stage7=True,
        runtime_contract=rel(CONTRACT), runtime_contract_sha256=sha(CONTRACT), source_selection_sha256=sha(ART / 'sources.json'),
        old_resources_unchanged=True, shared_core_untouched=True, playable=False, stage6_authorized=True, user_approved=False,
        new_image_requests_by_this_installer=0, generated_videos=0, git_operations=0))
    print('亚刻三级及空中Arc Finalize已接训练；待真实H/P、持续束及原输入回放', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['check', 'install'], nargs='?', default='check')
    args = parser.parse_args()
    if args.command == 'install': install()
    else:
        bundle = build()
        print(dict(read_only=True, actions={k: v['changes'] for k, v in bundle['actions'].items()},
                   new_effects=[r['id'] for r in bundle['additions']], supers_mapping=bundle['supers_mapping'], generated_videos=0))


if __name__ == '__main__': main()

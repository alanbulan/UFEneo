"""亚刻四必杀：真实H/P、自动档位、原生持续束与原InputFrame独立回放。"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

from codex_supers_install import (ART, ASSETS, CONTENT, CONTRACT, EFFECTS, MOVES, OUT, ROOT,
    SUPERS, build, local, read, rel, save, sha)
from codex_sword_followups_runtime import check_effect_node, intersections, phase

PREFIX = 'res://content/fighters/ultraman-arc/codex_supers_review_'
SPAN, SECTIONS = 320, 52
OBSERVATIONS = SPAN * SECTIONS


def layout(section):
    if section >= 48: return MOVES[section - 48], 'low_energy', 'zetton', 1
    combination = (section % 12) // 3
    return MOVES[section // 12], ['hit', 'stand_guard', 'whiff'][section % 3], 'zetton' if combination < 2 else 'ultraseven', -1 if combination % 2 else 1


def preflight():
    bundle = build()
    manifest, definition, commands = read(ASSETS / 'manifest.json'), read(CONTENT / 'definition.json'), read(CONTENT / 'command_table.json')
    assert definition['playable'] is False and definition.get('pilot_playable') is True
    installed = read(OUT / 'installed.json')
    assert installed['runtime_contract_sha256'] == sha(CONTRACT) and installed['source_selection_sha256'] == sha(ART / 'sources.json')
    changed = {row['path'] for row in installed['backups']}
    assert all(sha(ROOT / p) == h for p, h in installed['before'].items() if p not in changed)
    assert [c for c in commands if c['move'] in MOVES] == bundle['commands']
    assert read(SUPERS)['ultraman-arc'] == bundle['supers_mapping']
    paths = [Path(__file__), CONTRACT, ART / 'sources.json', OUT / 'installed.json', EFFECTS, SUPERS,
        ROOT / 'tools/rebuild/ultraman-arc/codex_supers_install.py', ROOT / 'tools/rebuild/ultraman-arc/codex_elbow_install.py',
        ROOT / 'tools/rebuild/ultraman-arc/codex_sword_followups_install.py', ROOT / 'tools/rebuild/ultraman-arc/codex_sword_followups_runtime.py']
    for identity, action in bundle['actions'].items():
        assert identity not in definition['unsupported_moves']
        assert manifest['clips'][identity] == action['clip'] and read(CONTENT / f'moves/{identity}.json') == action['move']
        texture = local(action['clip']['texture'])
        assert sha(texture) == action['clip']['atlas_sha256']
        paths.append(texture)
    effects = read(EFFECTS)
    for key, used in bundle['used_effects'].items():
        assert effects[key] == used['effect'] and sha(local(effects[key]['texture'])) == used['atlas_sha256']
        texture = local(effects[key]['texture'])
        paths += [p for p in [texture, texture.with_name('effect.json'), texture.with_name('provenance.json')] if p.is_file()]
    sounds = read(ROOT / 'content/audio/runtime.json')['sounds']
    paths += [local(sounds[key]['path']) for key in bundle['sound_ids']]
    paths += [local(bundle['supers_mapping'][key]) for key in ['portrait', 'background']]
    paths += [CONTENT / f'codex_supers_review_{kind}.gd' for kind in ['driver', 'entry', 'game', 'replay']]
    for identity in ['ultraman-arc', 'zetton', 'ultraseven']:
        paths += [ROOT / f'content/fighters/{identity}/{name}' for name in ['definition.json', 'production_plan.json', 'command_table.json', 'state_frames.json']
                  if (ROOT / f'content/fighters/{identity}/{name}').is_file()]
        paths += list((ROOT / f'content/fighters/{identity}/moves').glob('*.json'))
        paths += [ROOT / f'assets/fighters/{identity}/animations/manifest.json']
    for base in ['core', 'content/templates/humanoid']:
        paths += [p for p in (ROOT / base).rglob('*') if p.is_file() and p.suffix in ['.gd', '.json']]
    paths += [ROOT / p for p in ['app/scenes/main.tscn', 'app/game_app.gd', 'tests/review/input/review_driver.gd',
        'presentation/side_view.gd', 'presentation/side_audio.gd', 'presentation/super_cinematic.gd',
        'presentation/combat_feedback.gd', 'presentation/impact_feedback_policy.gd', 'presentation/effect_geometry.gd',
        'presentation/effect_timeline.gd', 'content/content_database.gd', 'content/catalogs/battle_form_catalog.gd',
        'content/catalogs/battle_forms.json', 'content/rules/neo.tres', 'content/audio/runtime.json', 'content/presentation/impact_effects.json']]
    return dict(observations=OBSERVATIONS, sections=SECTIONS, actions={k: a['changes'] for k, a in bundle['actions'].items()},
                fingerprints={rel(p): sha(p) for p in sorted(set(paths))}, generated_videos=0)


def shot_boxes(shot):
    phases = shot.get('frame_hitboxes', [[shot['box']]])
    values = phases[(int(shot['age']) // 4) % len(phases)]
    result = []
    for x, y, width, height in values:
        left = int(shot['x']) + x if int(shot['facing']) > 0 else int(shot['x']) - x - width
        bottom, top = int(shot['height']) + y, int(shot['height']) + y + height
        if shot.get('clip_below_ground'): bottom = max(0, bottom)
        if top > bottom: result.append([left, bottom, width, top - bottom])
    return result


def nodes(row, bundle, effects, need, tag):
    own, camera = row['pair'][0], row['camera']
    facing, identity = int(own['facing']), own['move']
    if identity in MOVES:
        move, clip = bundle['actions'][identity]['move'], bundle['actions'][identity]['clip']
        index, body, animation = int(own['sprite']), own['body_node'], own['animation']
        need(animation.get('key') == identity and int(animation.get('index', -1)) == index, tag + '本人整帧时钟不符')
        need(body['visible'] and not body['centered'] and body['texture'] == clip['texture'] and body['region'] == clip['rects'][index], tag + '本人独立图集不符')
        need(body['offset'] == [-v for v in clip['anchor']] and body['scale'] == [1, 1] and body['flip_h'] == (facing < 0)
             and float(body['rotation']) == 0 and body['position'] == [own['x'] - camera[0] + 320, 304 - own['height'] + camera[1]], tag + '本人根点/朝向/比例不符')
        frame = move['frames'][int(own['move_tick'])]
        need(own['hitboxes'] == [] and own['hurtboxes'] == frame['hurtboxes'] and own['beam_origin'] == frame.get('beam_origin', [])
             and own['attachments'] == frame.get('attachments', []), tag + '实际身体框/发射点/前后层不符')
    need(row['active_attachments'] == own['attachments'], tag + '实际挂件声明不符')
    for i, node in enumerate(row['attached_nodes']):
        if i >= len(row['active_attachments']):
            need(not node['visible'], tag + '过期挂件未隐藏')
            continue
        attached = row['active_attachments'][i]
        position = [own['x'] + facing * attached['anchor'][0] - camera[0] + 320, 304 - own['height'] - attached['anchor'][1] + camera[1]]
        check_effect_node(node, effects[attached['effect']], int(attached['sprite']), position, int(attached.get('facing', facing)), need, tag)
        need(node['z_index'] == int(attached.get('z_index', 1 if attached.get('behind_fighter', effects[attached['effect']].get('behind_fighter', False)) else 3)), tag + '本人特效前后层不符')
    need(not any(n['visible'] for key in ['projectile_nodes', 'trail_nodes'] for n in row[key]), tag + '持续束误入普通弹体/拖尾节点')
    visible = [n for n in row['beam_nodes'] if n['visible']]
    need(len(visible) == len(row['projectiles']) <= 1, tag + '唯一持续束节点不符')
    for shot, node in zip(row['projectiles'], visible):
        spec = effects[shot['effect']]
        durations = spec['ticks'] if isinstance(spec['ticks'], list) else [spec['ticks']] * len(spec['rects'])
        index = phase(spec, int(shot['age']) % sum(durations))
        expected = dict(spec)
        rect = list(spec['rects'][index])
        if shot.get('clip_below_ground'):
            rect[3] = max(0, min(rect[3], int(shot['height']) + int(spec['anchor'][1]) + 1))
        expected['rects'] = [rect]
        position = [shot['x'] - camera[0] + 320, 304 - shot['height'] + camera[1]]
        check_effect_node(node, expected, 0, position, int(shot['facing']), need, tag, False)
        need(float(node['rotation']) == 0, tag + '原生束被运行时旋转')
    for particle in row['impact_nodes']:
        if particle['id'] not in effects: continue
        # 本批dust来自落地/down，默认终结explosion也未声明finish_effect；两者spawn缺省朝右。
        # 专属命中/防御才沿事件effect_facing或出招方朝向；不从实际node.flip_h反推期望。
        particle_facing = 1 if particle['id'] in ['dust', 'explosion'] else facing
        for event in row['events']:
            feedback = event.get('feedback', {})
            if event.get('kind') not in ['hit', 'block'] or (event.get('x'), event.get('height')) != (particle['x'], particle['height']): continue
            expected_ids = {feedback.get('spark'), feedback.get('block_spark'), *feedback.get('projectile_impacts', {}).values()}
            if particle['id'] in expected_ids:
                particle_facing = int(event.get('effect_facing', row['pair'][int(event['player'])]['facing']))
        check_effect_node(particle['node'], effects[particle['id']], phase(effects[particle['id']], int(particle['age'])),
            [particle['x'] - camera[0] + 320, 304 - particle['height'] + camera[1]], particle_facing, need, tag, False)
    hierarchy = row['main_nodes']
    active = identity == 'special3'
    portrait = active and own['cinematic_stage'] == 'portrait'
    need(all(hierarchy.get(k) for k in ['root', 'view', 'feedback', 'super_cinematic'])
         and hierarchy['super_active'] == active and hierarchy['super_background_visible'] == active
         and hierarchy['super_portrait_visible'] == portrait, tag + '主游戏三级背景/特写显示不符')
    if active: need(row['cinematic_background_node']['texture'] == bundle['supers_mapping']['background'], tag + '三级背景资源不符')
    if portrait: need(row['cinematic_portrait_node']['texture'] == bundle['supers_mapping']['portrait']
                      and row['cinematic_portrait_node']['flip_h'] == (facing < 0), tag + '本人三级特写资源/朝向不符')
    for loop in row.get('audio_loops', []):
        if int(loop['owner']) != 0: continue
        wanted = own['audio_loop'] or ('charge' if own['state'] == 'charge' else '')
        need(loop['wanted'] == wanted and bool(loop['playing']) == bool(wanted) and (not wanted or loop['stream_matches']), tag + '实际能量循环声节点不符')


def audit(runtime, stills, replay_dir=None, audit_dir=None):
    replay_dir = runtime if replay_dir is None else replay_dir
    audit_dir = replay_dir if audit_dir is None else audit_dir
    assert replay_dir.resolve().is_relative_to(runtime.resolve()) and audit_dir.resolve().is_relative_to(runtime.resolve())
    originals = {rel(p): sha(p) for base in [runtime, stills] for p in base.rglob('*') if p.is_file()} if audit_dir != replay_dir else {}
    preflight()
    preparation, data, bundle = read(runtime / 'preflight.json'), read(runtime / 'main-trace.json'), build()
    effects = read(EFFECTS)
    effects.update(read(ROOT / 'content/presentation/impact_effects.json'))
    rows, errors, groups = data['trace'], [], []

    def need(value, reason):
        if not value and reason not in errors: errors.append(reason)

    validators = {rel(Path(__file__))}
    if replay_dir != runtime: validators.add(rel(CONTENT / 'codex_supers_review_replay.gd'))
    need(all(sha(ROOT / p) == h for p, h in preparation['fingerprints'].items() if p not in validators), '原运行后玩法/资源/驱动指纹变化')
    need([int(r['movie_frame']) for r in rows] == list(range(OBSERVATIONS)), '原主游戏观察不完整连续')
    for section in range(SECTIONS):
        requested, kind, opponent, facing = layout(section)
        actual = {'special': '', 'special2': 'special', 'special3': 'special2', 'air_special': ''}[requested] if kind == 'low_energy' else requested
        group = [r for r in rows if int(r['section']) == section]
        tag = f'{section}:{requested}:{kind}:{opponent}:{facing}：'
        need([int(r['age']) for r in group] == list(range(SPAN)), tag + '组内观察不完整')
        if not group: continue
        need(all(r['action'] == requested and r['case'] == kind and [p['fighter'] for p in r['pair']] == ['ultraman-arc', opponent]
                 and r['simulation_stepped'] and r['hud_label_visible'] and not r['finished'] for r in group), tag + '主游戏实际分组/模拟步不符')
        goal = bundle['actions'][requested]['move']['energy_cost'] - (20 if kind == 'low_energy' else 0)
        own_initial = group[0]['pre']['pair'][0]
        need(own_initial['energy'] == 0 and own_initial['stamina'] == 1000 and own_initial['move'] == '' and own_initial['height'] == 0, tag + '初始费用/高度被摆夹具')
        cast = [r for r in group if int(r['inputs'][0][2]) in [32, 3]]
        need(len(cast) == 1, tag + 'P或J+K请求不是唯一一次')
        cast_age = int(cast[0]['age']) if cast else -1
        if cast:
            need(cast[0]['pre']['pair'][0]['energy'] == goal and cast[0]['inputs'][0] == [0, 0, 3 if kind == 'stand_guard' and requested != 'air_special' else 32], tag + '真实蓄能量/P或轻重同按不符')
            need(cast[0]['pre']['pair'][0]['height'] > 0 if requested == 'air_special' else cast[0]['pre']['pair'][0]['state'] == 'idle', tag + '未自然释放H后发招')
        jumps = [r for r in group if int(r['inputs'][0][1]) == 1]
        need(len(jumps) == (1 if requested == 'air_special' else 0) and all(r['inputs'][0] == [0, 1, 0] for r in jumps), tag + '真实W起跳不符')
        if jumps: need(int(jumps[0]['age']) < cast_age and jumps[0]['pre']['pair'][0]['state'] == 'idle', tag + '空中P未来自自然起跳')
        consumed = [r for r in group if int(r['consumed_move_tick']) >= 0]
        move = bundle['actions'][actual]['move'] if actual else None
        need([int(r['consumed_move_tick']) for r in consumed] == (list(range(len(move['frames']))) if move else [])
             and all(r['consumed_move'] == actual for r in consumed), tag + '能量档位/完整消费tick不符；hitstop不凑tick')
        shown = [r for r in group if r['pair'][0]['move'] == actual] if actual else []
        if move:
            need([int(r['consumed_phase']) for r in consumed] == [f['sprite'] for f in move['frames']], tag + '整帧消费相位不符')
            need({int(r['pair'][0]['sprite']) for r in shown} == set(range(len(bundle['actions'][actual]['clip']['ticks']))), tag + '本人全部独立整帧未显示')
        need(group[-1]['pair'][0]['move'] == '' and group[-1]['pair'][0]['state'] == 'idle' and group[-1]['pair'][0]['height'] == 0
             and not group[-1]['projectiles'], tag + '未自然收势落地返回待机')
        contacts, intercepts, geometry, sounds, previous_hash = [], [], [], [], None
        shot_ages = []
        for row in group:
            pre, own, other = row['pre'], row['pair'][0], row['pair'][1]
            need(int(row['tick']) == int(row['age']) + 1 and (previous_hash is None or pre['state_hash'] == previous_hash), tag + 'pre/post或tick不连续')
            previous_hash = row['state_hash']
            need(own['move'] in ['', actual] and other['move'] == '' and own['facing'] == facing and other['facing'] == -facing, tag + '实际档位/双向朝向不符')
            need(row['inputs'][1] == [0, 0, 8 if kind == 'stand_guard' else 0]
                 and row['inputs'][0] in [[0, 0, 0], [0, 0, 16], [0, 0, 32], [0, 0, 3], [0, 1, 0]], tag + '组内存在H/W/P以外输入')
            hp, stamina, energy = ([int(f[k]) for f in pre['pair']] for k in ['hp', 'stamina', 'energy'])
            if int(pre['hitstop']) == 0:
                if move and own['move'] == actual and pre['pair'][0]['move'] != actual:
                    stamina[0] -= int(move['stamina_cost'])
                    energy[0] -= int(move['energy_cost'])
                    need(int(row['age']) == cast_age, tag + '发招脱离真实P输入')
                for i, fighter in enumerate(row['pair']):
                    if fighter['state'] == 'charge': energy[i] = min(3000, energy[i] + 20)
                    regen = int(move.get('stamina_regen', 4)) if i == 0 and move and row['consumed_move_tick'] >= 0 else 1 if fighter['state'] == 'charge' else 4
                    stamina[i] = min(1000, stamina[i] + regen)
            remaining = int(pre['remaining']) - (1 if int(pre['hitstop']) == 0 and not any(f['pause_clock'] for f in pre['pair']) else 0)
            need(row['remaining'] == remaining and not own['freeze_opponent'], tag + '三级停表/无对手冻结规则不符')
            for event in row['events']:
                if event.get('kind') == 'sound': sounds.append(dict(age=row['age'], id=event['id'], tick=row['consumed_move_tick']))
                if event.get('kind') in ['projectile_block', 'projectile_absorb', 'projectile_reflect']:
                    intercepts.append(event)
                    need(kind == 'stand_guard' and event['kind'] == 'projectile_block', tag + '非预期屏障拦截/反射')
                if event.get('kind') not in ['hit', 'block']: continue
                need(move is not None and event.get('move') == actual and event.get('player') == 0 and event.get('projectile') is True, tag + '必杀错误沿用近战/其它档位')
                if move is None: continue
                contacts.append(dict(age=row['age'], kind=event['kind'], x=event['x'], height=event['height']))
                if event['kind'] == 'hit':
                    hp[1] = max(0, hp[1] - move['damage'])
                    energy[0], energy[1] = min(3000, energy[0] + 90), min(3000, energy[1] + 40)
                else:
                    stamina[1] = max(0, stamina[1] - move['damage'])
                    hp[1] = max(0, hp[1] - move.get('chip_damage', 0))
                fx = move['feedback']['spark' if event['kind'] == 'hit' else 'block_spark']
                need(sum(p['id'] == fx and p['age'] == 0 and p['x'] == event['x'] and p['height'] == event['height'] for p in row['impact_nodes']) == 1, tag + '实际命中/防御专属火花缺失')
                need(any(p['id'] == move['audio']['hit' if event['kind'] == 'hit' else 'block'] for p in row.get('audio_played', [])), tag + '实际接触声音未播放')
            need([int(f['hp']) for f in row['pair']] == hp and [int(f['stamina']) for f in row['pair']] == stamina
                 and [int(f['energy']) for f in row['pair']] == energy, tag + '实际费用/伤害/格挡/回体回能不符')
            for shot in row['projectiles']:
                need(move is not None and shot['move'] == actual and shot['owner'] == 0 and shot.get('beam') is True, tag + '持续束归属不符')
                if move is None: continue
                authored = move['projectile']
                for key in ['effect', 'length', 'anchor', 'origin_by_frame', 'frame_hitboxes']:
                    need(shot.get(key) == authored.get(key), tag + '原生束资源/发射序列/Alpha判定不符')
                origin = shot['origin_by_frame'].get(str(own['move_tick']), shot['anchor'])
                need(shot['x'] == own['x'] + facing * origin[0] and shot['height'] == own['height'] + origin[1]
                     and shot['age'] + shot['life'] == authored['life'] and shot['world_hitboxes'] == shot_boxes(shot), tag + '实际持续束跟随/寿命/分条世界框不符')
                if authored.get('clip_below_ground'): need(all(b[1] >= 0 for b in shot['world_hitboxes']), tag + '斜下束判定穿过地线')
                if int(pre['hitstop']) == 0: shot_ages.append(int(shot['age']))
                geometry.append(dict(age=row['age'], shot_age=shot['age'], intersections=intersections(shot['world_hitboxes'], other['world_hurtboxes'])))
            nodes(row, bundle, effects, need, tag)
        need(sounds == [dict(age=r['age'], id=e['id'], tick=r['consumed_move_tick']) for r in consumed
                       for e in bundle['actions'][r['consumed_move']]['move']['frames'][int(r['consumed_move_tick'])]['events'] if e['kind'] == 'sound'], tag + '实际出束声帧事件不符')
        need(len(contacts) + len(intercepts) <= 1, tag + '唯一持续束对同敌重复接触')
        hits, blocks = [c for c in contacts if c['kind'] == 'hit'], [c for c in contacts if c['kind'] == 'block']
        if kind == 'hit': need(len(hits) == 1 and not blocks, tag + '实际站姿未命中')
        if kind == 'stand_guard': need(not hits, tag + '站防错误命中')
        if kind == 'whiff': need(not contacts and not intercepts, tag + '远落空出现接触')
        natural_dodge = kind == 'stand_guard' and not contacts and not intercepts
        if natural_dodge or kind == 'whiff':
            need(bool(geometry) and all(not item['intersections'] for item in geometry), tag + '自然姿势躲避/远落空缺无交集依据')
        if move and not intercepts: need(shot_ages == list(range(1, int(move['projectile']['life']))), tag + '唯一持续束实际寿命不完整')
        if actual == 'special3': need(any(r['main_nodes']['super_portrait_visible'] for r in group) and any(r['main_nodes']['super_background_visible'] for r in group), tag + '三级特写/背景从未显示')
        pictures = [p for p in data.get('stills', []) if int(p['section']) == section]
        need(len(pictures) == 1 and all(local(p['path']).is_file() and local(p['path']).is_relative_to(stills.resolve()) for p in pictures), tag + '每组唯一JPG缺失或越目录')
        groups.append(dict(section=section, requested=requested, actual=actual, case=kind, opponent=opponent, facing=facing,
            result='insufficient_energy' if not actual else 'automatic_lower_tier' if kind == 'low_energy' else 'natural_guard_pose_dodge' if natural_dodge else 'hit' if hits else 'blocked' if blocks or intercepts else 'whiff',
            goal_energy=goal, cast_age=cast_age, consumed_ticks=len(consumed), body_phases=sorted({int(r['pair'][0]['sprite']) for r in shown}),
            contacts=contacts, intercepts=intercepts, sounds=sounds, projectile_ages=shot_ages, contact_geometry=geometry))
    replay_path = replay_dir / 'actual-replay.json'
    replay = read(replay_path)
    need(replay.get('trace_sha256') == sha(runtime / 'main-trace.json') and replay.get('observations') == OBSERVATIONS and bool(replay.get('event_comparison')), '独立回放未绑定原输入及完整事件')
    exits = {key: read((replay_dir if key == 'actual-replay' else runtime) / (key + '-exit.json')) for key in ['import-atlas', 'main-game', 'actual-replay']}
    need(all(e['exit_code'] == 0 and not e['errors'] for e in exits.values()), '引擎/脚本未正常退出')
    need(not any(p.suffix.lower() in ['.mp4', '.webm', '.avi', '.mov'] for p in runtime.rglob('*')), '本次意外生成视频')
    result = dict(sections=groups, observations=len(rows), logic_errors=errors, replay_errors=replay['errors'], engine_exits=exits,
        source_trace=rel(runtime / 'main-trace.json'), trace_sha256=sha(runtime / 'main-trace.json'), replay=rel(replay_path), replay_sha256=sha(replay_path),
        generated_videos=0, playable=False, stage6_authorized=True, user_approved=False,
        changed_validation_sources={p: dict(original=h, current=sha(ROOT / p)) for p, h in preparation['fingerprints'].items() if p in validators and sha(ROOT / p) != h})
    if replay_dir != runtime:
        preservation = read(replay_dir / 'source-preservation.json')
        need(preservation['original_files_unchanged'] and all(sha(ROOT / p) == h for p, h in preservation['original_file_sha256'].items()), '原trace/首次证据变化')
        result['source_preservation'] = preservation
    if audit_dir != replay_dir:
        unchanged = all((ROOT / p).is_file() and sha(ROOT / p) == h for p, h in originals.items())
        need(unchanged, '审计改变原运行/JPG/首次验证')
        result['audit_only'] = dict(original_file_sha256=originals, original_files_unchanged=unchanged, reran_main_game=False, reran_import=False, reran_replay=False)
        audit_dir.mkdir(parents=True, exist_ok=False)
    assert not (audit_dir / 'validation.json').exists(), '原验证报告拒绝覆盖'
    save(audit_dir / 'validation.json', result)
    assert not errors and not replay['errors'], '本次逻辑/独立回放失败，原证据保留'
    print('亚刻三级/空中真实输入、实际束节点及原输入回放齐；美术与用户门仍待', flush=True)


def run_engine(runtime, label, argv):
    assert (ROOT / 'art/shared/locks/godot.lock').is_file(), '根须持唯一Godot锁'
    sys.path.insert(0, str(ROOT / 'tools'))
    from verify import godot_path
    log = runtime / (label + '.log')
    assert not log.exists() and not (runtime / (label + '-exit.json')).exists(), '原运行证据拒绝覆盖'
    with log.open('xb') as output:
        result = subprocess.run([str(godot_path()), '--path', str(ROOT), *argv], cwd=ROOT,
            stdout=output, stderr=subprocess.STDOUT, creationflags=0x08000000, timeout=480)
    errors = [s for s in log.read_text('utf-8', errors='replace').splitlines() if 'SCRIPT ERROR:' in s or 'Parse Error:' in s or s.lstrip().startswith('ERROR:')]
    save(runtime / (label + '-exit.json'), dict(exit_code=result.returncode, errors=errors, generated_videos=0))
    print(label, result.returncode, errors[:3], flush=True)
    assert result.returncode == 0 and not errors, '引擎/脚本失败，原日志保留'


def run(runtime, stills):
    assert (ROOT / 'art/shared/locks/godot.lock').is_file() and OUT.is_dir()
    preparation = preflight()
    runtime.mkdir(parents=True, exist_ok=False)
    stills.mkdir(parents=True, exist_ok=False)
    save(runtime / 'preflight.json', preparation)
    run_engine(runtime, 'import-atlas', ['--headless', '--editor', '--import', '--quit'])
    trace = runtime / 'main-trace.json'
    run_engine(runtime, 'main-game', ['--script', PREFIX + 'entry.gd', '--rendering-method', 'gl_compatibility', '--rendering-driver', 'opengl3',
        '--fixed-fps', '60', '--resolution', '1280x720', '--disable-vsync', '--quit-after', str(OBSERVATIONS + 5), '--',
        '--review-trace=' + str(trace), '--arc-supers-stills-dir=' + str(stills)])
    run_engine(runtime, 'actual-replay', ['--headless', '--script', PREFIX + 'replay.gd', '--', '--arc-supers-trace=' + str(trace),
        '--arc-supers-output=' + str(runtime / 'actual-replay.json')])
    audit(runtime, stills)


def replay_only(runtime, stills, replay_dir):
    assert replay_dir != runtime and replay_dir.resolve().is_relative_to(runtime.resolve())
    originals = {rel(p): sha(p) for base in [runtime, stills] for p in base.rglob('*') if p.is_file()}
    replay_dir.mkdir(parents=True, exist_ok=False)
    trace = runtime / 'main-trace.json'
    try:
        run_engine(replay_dir, 'actual-replay', ['--headless', '--script', PREFIX + 'replay.gd', '--', '--arc-supers-trace=' + str(trace),
            '--arc-supers-output=' + str(replay_dir / 'actual-replay.json')])
    finally:
        unchanged = all((ROOT / p).is_file() and sha(ROOT / p) == h for p, h in originals.items())
        save(replay_dir / 'source-preservation.json', dict(original_file_sha256=originals, original_files_unchanged=unchanged,
            trace_sha256=sha(trace), replay_script_sha256=sha(CONTENT / 'codex_supers_review_replay.gd'), reran_main_game=False, reran_import=False))
        assert unchanged


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['check', 'run', 'replay', 'audit'])
    parser.add_argument('--run-id', default='runtime')
    parser.add_argument('--replay-id')
    parser.add_argument('--audit-id')
    args = parser.parse_args()
    for value in [args.run_id, args.replay_id, args.audit_id]: assert value is None or re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', value)
    assert args.audit_id is None or args.command == 'audit'
    runtime = OUT / args.run_id
    stills = OUT / ('stills' if args.run_id == 'runtime' else args.run_id + '-stills')
    replay_dir = runtime / args.replay_id if args.replay_id else runtime
    audit_dir = runtime / args.audit_id if args.audit_id else replay_dir
    if args.command == 'check': print({k: v for k, v in preflight().items() if k != 'fingerprints'})
    elif args.command == 'run':
        assert args.replay_id is None
        run(runtime, stills)
    elif args.command == 'replay':
        assert args.replay_id is not None
        replay_only(runtime, stills, replay_dir)
    else: audit(runtime, stills, replay_dir, audit_dir)


if __name__ == '__main__': main()

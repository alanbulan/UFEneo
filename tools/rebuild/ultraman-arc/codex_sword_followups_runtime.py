"""亚刻回身双侧剑斩/光剑掷返：有限实战、真实节点与原输入独立回放。"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

from codex_sword_followups_install import (ART, ASSETS, CONTENT, CONTRACT, EFFECTS, MOVES,
    OUT, ROOT, build, local, read, rel, rgba, save, sha)

PREFIX = 'res://content/fighters/ultraman-arc/codex_sword_followups_review_'
SPAN, SECTIONS = 120, 28
OBSERVATIONS = SPAN * SECTIONS


def layout(section):
    identity = 'motion_214' if section < 16 else 'ranged_forward'
    cases = ['hit', 'stand_guard', 'whiff', 'rear_hit'] if section < 16 else ['hit', 'stand_guard', 'whiff']
    offset = section if section < 16 else section - 16
    combination = offset // len(cases)
    return identity, cases[offset % len(cases)], 'zetton' if combination < 2 else 'ultraseven', -1 if combination % 2 else 1


def preflight():
    bundle = build()
    manifest, definition = read(ASSETS / 'manifest.json'), read(CONTENT / 'definition.json')
    assert definition['playable'] is False and definition.get('pilot_playable') is True
    installed = read(OUT / 'installed.json')
    assert installed['runtime_contract_sha256'] == sha(CONTRACT) and installed['source_selection_sha256'] == sha(ART / 'sources.json')
    changed = {row['path'] for row in installed['backups']}
    assert all(sha(ROOT / p) == h for p, h in installed['before'].items() if p not in changed)
    paths = [Path(__file__), ROOT / 'tools/rebuild/ultraman-arc/codex_sword_followups_install.py',
        CONTRACT, ART / 'sources.json', OUT / 'installed.json', ASSETS / 'manifest.json', EFFECTS]
    commands = read(CONTENT / 'command_table.json')
    sounds = read(ROOT / 'content/audio/runtime.json')['sounds']
    for identity, action in bundle['actions'].items():
        assert identity not in definition['unsupported_moves']
        assert manifest['clips'][identity] == action['clip'] and read(CONTENT / f'moves/{identity}.json') == action['move']
        assert [row for row in commands if row['move'] == identity] == [action['command']]
        texture = local(action['clip']['texture'])
        assert sha(texture) == action['clip']['atlas_sha256']
        paths.append(texture)
        audio_ids = [e['id'] for f in action['move']['frames'] for e in f['events'] if e['kind'] == 'sound']
        audio_ids += [action['move']['audio'][key] for key in ['hit', 'block']]
        paths += [local(sounds[key]['path']) for key in audio_ids]
    effects = read(EFFECTS)
    for identity, used in bundle['used_effects'].items():
        assert effects[identity] == used['effect'] and sha(local(effects[identity]['texture'])) == used['atlas_sha256']
        texture = local(effects[identity]['texture'])
        paths += [texture, texture.with_name('effect.json'), texture.with_name('provenance.json')]
    paths += [CONTENT / f'codex_sword_followups_review_{kind}.gd' for kind in ['driver', 'entry', 'game', 'replay']]
    for identity in ['ultraman-arc', 'zetton', 'ultraseven']:
        paths += [ROOT / f'content/fighters/{identity}/{name}' for name in ['definition.json', 'production_plan.json', 'command_table.json', 'state_frames.json']
                  if (ROOT / f'content/fighters/{identity}/{name}').is_file()]
        paths += list((ROOT / f'content/fighters/{identity}/moves').glob('*.json'))
        paths += [ROOT / f'assets/fighters/{identity}/animations/manifest.json']
    for base in ['core', 'content/templates/humanoid']:
        paths += [p for p in (ROOT / base).rglob('*') if p.is_file() and p.suffix in ['.gd', '.json']]
    paths += [ROOT / p for p in ['app/scenes/main.tscn', 'app/game_app.gd', 'tests/review/input/review_driver.gd',
        'presentation/side_view.gd', 'presentation/side_audio.gd', 'presentation/super_cinematic.gd',
        'presentation/combat_feedback.gd', 'presentation/effect_geometry.gd', 'presentation/effect_timeline.gd',
        'content/content_database.gd', 'content/catalogs/battle_form_catalog.gd', 'content/catalogs/battle_forms.json',
        'content/rules/neo.tres', 'content/audio/runtime.json']]
    return dict(observations=OBSERVATIONS, sections=SECTIONS,
        actions={key: value['changes'] for key, value in bundle['actions'].items()}, generated_videos=0,
        fingerprints={rel(p): sha(p) for p in sorted(set(paths))})


def run_engine(runtime, label, argv):
    assert (ROOT / 'art/shared/locks/godot.lock').is_file(), '根须持有唯一Godot串行锁'
    sys.path.insert(0, str(ROOT / 'tools'))
    from verify import godot_path
    log = runtime / (label + '.log')
    assert not log.exists() and not (runtime / (label + '-exit.json')).exists(), '原运行证据拒绝覆盖'
    with log.open('xb') as output:
        result = subprocess.run([str(godot_path()), '--path', str(ROOT), *argv], cwd=ROOT,
            stdout=output, stderr=subprocess.STDOUT, timeout=180)
    errors = [line for line in log.read_text('utf-8', errors='replace').splitlines()
              if 'SCRIPT ERROR:' in line or 'Parse Error:' in line or line.lstrip().startswith('ERROR:')]
    save(runtime / (label + '-exit.json'), dict(exit_code=result.returncode, errors=errors, generated_videos=0))
    print(label, result.returncode, errors[:3], flush=True)
    assert result.returncode == 0 and not errors, '引擎/脚本失败，原日志保留'


def intersections(hits, hurts):
    result = []
    for hit in hits:
        for hurt in hurts:
            x, y = max(hit[0], hurt[0]), max(hit[1], hurt[1])
            right, top = min(hit[0] + hit[2], hurt[0] + hurt[2]), min(hit[1] + hit[3], hurt[1] + hurt[3])
            if x < right and y < top: result.append([x, y, right - x, top - y])
    return result


def phase(spec, age):
    ticks = spec.get('ticks', 4)
    values = ticks if isinstance(ticks, list) else [ticks] * len(spec['rects'])
    age = min(max(0, age), sum(values) - 1)
    for i, duration in enumerate(values):
        if age < duration: return i
        age -= duration
    return len(values) - 1


def check_effect_node(node, spec, index, position, facing, need, tag, centered=None):
    rect, pivot = spec['rects'][index], spec['anchor']
    half = [rect[2] / 2, rect[3] / 2] if node['centered'] else [0, 0]
    offset = [half[0] + (-pivot[0] if facing > 0 else pivot[0] - rect[2]), half[1] - pivot[1]]
    need(node['visible'] and node['texture'] == spec['texture'] and node['region'] == rect, tag + '实际本人FX图集/相位不符')
    need(node['position'] == position and node['offset'] == offset and node['scale'] == [1, 1]
         and node['flip_h'] == (facing < 0), tag + '实际本人FX锚点/朝向/比例不符')
    if centered is not None: need(node['centered'] == centered, tag + '实际FX中心模式不符')


def audit_nodes(row, clip, move, effects, need):
    own, camera = row['pair'][0], row['camera']
    facing = int(own['facing'])
    tag = f'{int(row["section"])}:{int(row["age"])}：'
    if own['move'] == row['action']:
        body, index, animation = own['body_node'], int(own['sprite']), own['animation']
        need(animation.get('key') == row['action'] and int(animation.get('index', -1)) == index, tag + '实际独立人物相位不符')
        need(body['visible'] and not body['centered'] and body['texture'] == clip['texture'] and body['region'] == clip['rects'][index], tag + '实际身体图集裁片不符')
        need(body['flip_h'] == (facing < 0) and body['scale'] == [1, 1] and float(body['rotation']) == 0
             and body['offset'] == [-160, -280]
             and body['position'] == [own['x'] - camera[0] + 320, 304 - own['height'] + camera[1]], tag + '实际人物比例/根点/朝向不符')
    attachments = row['active_attachments']
    need(attachments == own['attachments'] and len(row['attached_nodes']) >= len(attachments), tag + '实际本人挂件/槽数不符')
    for i, node in enumerate(row['attached_nodes']):
        if i >= len(attachments):
            need(not node['visible'], tag + '过期挂件未隐藏')
            continue
        item = attachments[i]
        position = [own['x'] + facing * item['anchor'][0] - camera[0] + 320, 304 - own['height'] - item['anchor'][1] + camera[1]]
        check_effect_node(node, effects[item['effect']], int(item['sprite']), position, facing, need, tag)
    need(not any(node['visible'] for node in row['beam_nodes']), tag + '普通剑技误出持续束')
    need(sum(bool(node['visible']) for node in row['projectile_nodes']) == len(row['projectiles']), tag + '唯一投剑实际节点数量不符')
    for i, node in enumerate(row['projectile_nodes']):
        if i >= len(row['projectiles']):
            need(not node['visible'], tag + '过期脱手物仍可见')
            continue
        shot = row['projectiles'][i]
        spec = effects[shot['effect']]
        index = (int(shot['age']) // int(spec['ticks'])) % len(spec['rects'])
        position = [shot['x'] - camera[0] + 320, 304 - shot['height'] + camera[1]]
        check_effect_node(node, spec, index, position, int(shot['facing']), need, tag)
        need(float(node['rotation']) == 0, tag + '脱手剑被运行时旋转')
    impact_ids = {move['feedback']['spark'], move['feedback']['block_spark']}
    for particle in row['impact_nodes']:
        if particle['id'] not in impact_ids: continue
        check_effect_node(particle['node'], effects[particle['id']], phase(effects[particle['id']], int(particle['age'])),
            [particle['x'] - camera[0] + 320, 304 - particle['height'] + camera[1]], facing, need, tag, False)
    for event in row['events']:
        if event.get('kind') in ['hit', 'block']:
            identity = move['feedback']['spark' if event['kind'] == 'hit' else 'block_spark']
            need(sum(p['id'] == identity and int(p['age']) == 0 and p['x'] == event['x'] and p['height'] == event['height']
                     for p in row['impact_nodes']) == 1, tag + '真实接触未唯一生成本人接触FX')
    hierarchy = row['main_nodes']
    need(all(hierarchy.get(key) for key in ['root', 'view', 'feedback', 'super_cinematic'])
         and not hierarchy['super_active'] and not hierarchy['super_background_visible'] and not hierarchy['super_portrait_visible'], tag + '主场景节点或普通剑技演出状态不符')


def audit(runtime, stills, replay_dir=None, audit_dir=None):
    replay_dir = runtime if replay_dir is None else replay_dir
    audit_dir = replay_dir if audit_dir is None else audit_dir
    assert replay_dir.resolve().is_relative_to(runtime.resolve()) and audit_dir.resolve().is_relative_to(runtime.resolve())
    originals = {}
    if audit_dir != replay_dir:
        assert not audit_dir.exists(), '独立审计目录拒绝覆盖'
        originals = {rel(p): sha(p) for base in [runtime, stills] for p in base.rglob('*') if p.is_file()}
    preflight()
    preparation = read(runtime / 'preflight.json')
    validators = {rel(Path(__file__))}
    replay_source = CONTENT / 'codex_sword_followups_review_replay.gd'
    if replay_dir != runtime: validators.add(rel(replay_source))
    errors, groups = [], []

    def need(value, reason):
        if not value and reason not in errors: errors.append(reason)

    need(all(sha(ROOT / p) == h for p, h in preparation['fingerprints'].items() if p not in validators), '运行后资源/玩法驱动/共享源码变化')
    data = read(runtime / 'main-trace.json')
    rows = data['trace']
    need([int(r['movie_frame']) for r in rows] == list(range(OBSERVATIONS)), '主游戏观察不完整连续')
    effects, contract = read(EFFECTS), read(CONTRACT)
    for section in range(SECTIONS):
        identity, kind, opponent, facing = layout(section)
        group = [r for r in rows if int(r['section']) == section]
        move = read(CONTENT / f'moves/{identity}.json')
        clip = read(ASSETS / 'manifest.json')['clips'][identity]
        spec = contract['actions'][identity]
        tag = f'{section}:{identity}:{kind}:{opponent}:{facing}：'
        need([int(r['age']) for r in group] == list(range(SPAN)), tag + '组内观察不完整')
        if not group: continue
        need(all(r['action'] == identity and r['case'] == kind and [f['fighter'] for f in r['pair']] == ['ultraman-arc', opponent]
                 and r['simulation_stepped'] and r['hud_label_visible'] and not r['finished'] for r in group), tag + '本人/对手/分组/实际步不符')
        expected_inputs = []
        for age in range(SPAN):
            if identity == 'motion_214':
                own = [0, -1, 0] if age == 0 else [-facing, -1, 0] if age == 1 else [-facing, 0, 128] if age == 2 else [0, 0, 0]
            else: own = [facing, 0, 128] if age == 20 else [0, 0, 0]
            expected_inputs.append([own, [0, 0, 8] if kind == 'stand_guard' else [0, 0, 0]])
        need([r['inputs'] for r in group] == expected_inputs, tag + '真实214I/6I或对手输入不符')
        consumed = [r for r in group if int(r['consumed_move_tick']) >= 0]
        need([int(r['consumed_move_tick']) for r in consumed] == list(range(len(move['frames'])))
             and all(r['consumed_move'] == identity for r in consumed), tag + '未完整消费一次本招；hitstop不凑tick')
        need([int(r['consumed_phase']) for r in consumed] == [int(f['sprite']) for f in move['frames']], tag + '独立帧时钟不符')
        shown = [r for r in group if r['pair'][0]['move'] == identity]
        need({int(r['pair'][0]['sprite']) for r in shown} == set(range(len(clip['ticks']))), tag + '独立人物相位未全部显示')
        need(all(int(r['pair'][0]['facing']) == facing for r in shown), tag + '攻击中朝向未保持真实输入方向')
        need(all(r['pair'][0]['move'] == '' and int(r['pair'][0]['height']) == 0 for r in group if int(r['age']) >= 85), tag + '末段未完成收招')
        contacts, sounds, returns, geometry, flight = [], [], [], [], []
        previous_hash = None
        for row in group:
            pre, pair = row['pre'], row['pair']
            own, other = pair
            need(int(row['tick']) == int(row['age']) + 1, tag + '组内tick不连续')
            if previous_hash is not None: need(pre['state_hash'] == previous_hash, tag + '组内pre/post状态不连续')
            previous_hash = row['state_hash']
            need(own['move'] in ['', identity] and other['move'] == '' and all(int(f['height']) == 0 for f in pair), tag + '意外其它招式或挑空')
            hp, stamina, energy = ([int(f[key]) for f in pre['pair']] for key in ['hp', 'stamina', 'energy'])
            if int(pre['hitstop']) == 0:
                if own['move'] == identity and pre['pair'][0]['move'] != identity:
                    need(int(row['age']) == (2 if identity == 'motion_214' else 20), tag + '未由真实末输入发动')
                    stamina[0] -= int(move['stamina_cost'])
                    energy[0] -= int(move['energy_cost'])
                stamina = [min(1000, value + 4) for value in stamina]
            for event in row['events']:
                if event.get('kind') == 'sound': sounds.append(dict(age=row['age'], id=event['id'], tick=row['consumed_move_tick']))
                if event.get('kind') == 'weapon_return':
                    returns.append(dict(age=row['age'], event=event, move_tick=own['move_tick'], sprite=own['sprite']))
                    anchor = own['weapon_return_anchor'] or move['projectile']['return_anchor']
                    need(identity == 'ranged_forward' and event.get('move') == identity and int(event['player']) == 0
                         and event['x'] == own['x'] + facing * anchor[0] and event['height'] == own['height'] + anchor[1], tag + '真实返剑事件未回到接柄点')
                if event.get('kind') not in ['hit', 'block']: continue
                need(event.get('move') == identity and int(event.get('player', -1)) == 0
                     and bool(event.get('projectile')) == (identity == 'ranged_forward'), tag + '近战/脱手物实际接触类型不符')
                contacts.append(dict(age=row['age'], kind=event['kind'], sprite=own['sprite'], tick=own['move_tick'], x=event['x'], height=event['height']))
                if event['kind'] == 'hit':
                    hp[1] = max(0, hp[1] - int(move['damage']))
                    energy[0], energy[1] = min(3000, energy[0] + 90), min(3000, energy[1] + 40)
                else:
                    stamina[1] = max(0, stamina[1] - int(move['damage']))
                    hp[1] = max(0, hp[1] - int(move.get('chip_damage', 0)))
            need([int(f['hp']) for f in pair] == hp, tag + '实际115/95伤害或防御扣血不符')
            need([int(f['stamina']) for f in pair] == stamina and [int(f['energy']) for f in pair] == energy, tag + '实际30体/0能/回体回能不符')
            if own['move'] == identity:
                frame = move['frames'][int(own['move_tick'])]
                need(own['hitboxes'] == frame['hitboxes'] and own['hurtboxes'] == frame['hurtboxes'], tag + '本人真实框与合同不符')
                if own['hitboxes']:
                    geometry.append(dict(age=row['age'], sprite=own['sprite'], world_hitboxes=own['world_hitboxes'],
                        world_hurtboxes=other['world_hurtboxes'], intersections=intersections(own['world_hitboxes'], other['world_hurtboxes'])))
            need(len(row['projectiles']) <= (1 if identity == 'ranged_forward' else 0), tag + '回身斩意外弹体或重复飞剑')
            for shot in row['projectiles']:
                expected = move['projectile']
                need(shot['effect'] == expected['effect'] and int(shot['owner']) == 0 and int(shot['source_owner']) == 0
                     and int(shot['facing']) == facing and shot['integer_path'] == expected['integer_path'], tag + '脱手剑身份/方向/整数路径不符')
                need(shot['origin_x'] == own['x'] + facing * expected['spawn'][0]
                     and shot['origin_height'] == own['height'] + expected['spawn'][1], tag + '脱手剑未从真实松指点产生')
                if int(shot['return_age']) == 0:
                    point = expected['integer_path'][int(shot['age']) - 1]
                    need(shot['x'] == shot['origin_x'] + facing * point[0] and shot['height'] == max(0, shot['origin_height'] + point[1]), tag + '脱手剑外飞不是原生整数路径')
                else:
                    duration, age = int(expected['return_ticks']), int(shot['return_age'])
                    anchor = expected['return_anchor']
                    expected_position = [int((int(shot['return_x']) * (duration - age) + (own['x'] + facing * anchor[0]) * age) / duration),
                        int((int(shot['return_height']) * (duration - age) + (own['height'] + anchor[1]) * age) / duration)]
                    need([shot['x'], shot['height']] == expected_position, tag + '回程未真实追向掌点')
                geometry.append(dict(age=row['age'], projectile_age=shot['age'], world_hitboxes=shot['world_hitboxes'],
                    world_hurtboxes=other['world_hurtboxes'], intersections=intersections(shot['world_hitboxes'], other['world_hurtboxes'])))
                if int(pre['hitstop']) == 0: flight.append(dict(age=shot['age'], x=shot['x'], height=shot['height'], return_age=shot['return_age'], hits=shot['hits']))
            audit_nodes(row, clip, move, effects, need)
        need(sounds == [dict(age=r['age'], id=event['id'], tick=r['consumed_move_tick']) for r in consumed
             for event in move['frames'][int(r['consumed_move_tick'])]['events'] if event['kind'] == 'sound'], tag + '本人实际声音帧事件不符')
        hits, blocks = [c for c in contacts if c['kind'] == 'hit'], [c for c in contacts if c['kind'] == 'block']
        need(len(contacts) <= 1, tag + '同次招式同敌重复伤害')
        if kind in ['hit', 'rear_hit']:
            need(len(hits) == 1 and not blocks, tag + '前/背侧实际站姿未命中')
            if identity == 'motion_214': need(all(c['sprite'] in ([4, 5] if kind == 'rear_hit' else [7, 8, 9]) for c in hits), tag + '首/次挥刃真实命中相位不符')
        if kind == 'stand_guard': need(not hits, tag + '站防错误受伤')
        if kind == 'whiff': need(not contacts, tag + '远落空出现接触')
        natural_dodge = kind == 'stand_guard' and not contacts
        if natural_dodge or kind == 'whiff':
            need(bool(geometry) and all(not item['intersections'] for item in geometry), tag + '无接触却有真实框交集')
            need(all(r['pair'][1]['hp'] == group[0]['pre']['pair'][1]['hp'] for r in group), tag + '自然躲过/远落空扣血')
        if identity == 'ranged_forward':
            need(len(returns) == 1 and not group[-1]['projectiles'], tag + '缺真实返剑/唯一回收闭环')
            need(all(c['sprite'] != 3 for c in returns), tag + '仍在脱手整帧时重复回剑')
            if flight and not any(r['events'] and any(e.get('kind') == 'projectile_block' for e in r['events']) for r in group):
                need([int(p['age']) for p in flight] == list(range(1, len(move['projectile']['integer_path']) + move['projectile']['return_ticks'])), tag + '投剑外飞/回程实际推进不完整')
        else: need(not returns and not flight, tag + '近战二连误用飞剑')
        pictures = [p for p in data.get('stills', []) if int(p['section']) == section]
        need(len(pictures) == 1 and all(local(p['path']).is_file() and local(p['path']).is_relative_to(stills.resolve()) for p in pictures), tag + '必要JPG缺失或路径不符')
        groups.append(dict(section=section, action=identity, case=kind, opponent=opponent, facing=facing,
            result='natural_guard_pose_dodge' if natural_dodge else 'hit' if hits else 'blocked' if blocks else 'whiff',
            actual_body_phases=sorted({int(r['pair'][0]['sprite']) for r in shown}), consumed_ticks=[r['consumed_move_tick'] for r in consumed],
            contacts=contacts, sounds=sounds, weapon_return=returns, flight=flight, contact_geometry=geometry))
    replay_path = replay_dir / 'actual-replay.json'
    replay = read(replay_path)
    need(replay.get('trace_sha256') == sha(runtime / 'main-trace.json') and int(replay.get('observations', -1)) == OBSERVATIONS
         and bool(replay.get('event_comparison')), '独立回放未绑定完整原输入/完整事件')
    exits = {key: read((replay_dir if key == 'actual-replay' else runtime) / (key + '-exit.json')) for key in ['import-atlas', 'main-game', 'actual-replay']}
    need(all(value['exit_code'] == 0 and not value['errors'] for value in exits.values()), '引擎/脚本未正常退出')
    need(not any(p.suffix.lower() in ['.mp4', '.avi', '.webm', '.mov'] for p in runtime.rglob('*')), '本次意外生成视频')
    result = dict(sections=groups, observations=len(rows), logic_errors=errors, replay_errors=replay['errors'], engine_exits=exits,
        source_trace=rel(runtime / 'main-trace.json'), trace_sha256=sha(runtime / 'main-trace.json'), replay=rel(replay_path),
        replay_sha256=sha(replay_path), generated_videos=0, playable=False, stage6_authorized=True, user_approved=False,
        changed_validation_sources={p: dict(original=h, current=sha(ROOT / p)) for p, h in preparation['fingerprints'].items() if p in validators and sha(ROOT / p) != h},
        timing_note='完整消费逻辑tick；实际显示推进后1..末tick前。214真双侧挥剑，同次招式对同敌沿既有connected仅接触一次；姿势避开按世界框记录。')
    if replay_dir != runtime:
        preservation = read(replay_dir / 'source-preservation.json')
        need(preservation['original_files_unchanged'] and all(sha(ROOT / p) == h for p, h in preservation['original_file_sha256'].items()), '原输入/首证据变化')
        result['source_preservation'] = preservation
    if audit_dir != replay_dir:
        unchanged = all((ROOT / p).is_file() and sha(ROOT / p) == h for p, h in originals.items())
        need(unchanged, '独立审计改变原运行/JPG/首验证证据')
        result['audit_only'] = dict(original_file_sha256=originals, original_files_unchanged=unchanged,
            reran_import=False, reran_main_game=False, reran_replay=False, generated_stills=0)
        audit_dir.mkdir(parents=True, exist_ok=False)
    assert not (audit_dir / 'validation.json').exists(), '原验证报告拒绝覆盖'
    save(audit_dir / 'validation.json', result)
    assert not errors and not replay['errors'], '本次逻辑/独立回放失败，原证据保留'
    print('亚刻214I双侧挥刃、6I实际脱手/回收及原输入独立回放齐；用户与美术门仍待', flush=True)


def run(runtime, stills):
    assert (ROOT / 'art/shared/locks/godot.lock').is_file() and OUT.is_dir()
    preparation = preflight()
    runtime.mkdir(parents=True, exist_ok=False)
    stills.mkdir(parents=True, exist_ok=False)
    save(runtime / 'preflight.json', preparation)
    run_engine(runtime, 'import-atlas', ['--headless', '--editor', '--import', '--quit'])
    trace = runtime / 'main-trace.json'
    run_engine(runtime, 'main-game', ['--script', PREFIX + 'entry.gd', '--rendering-method', 'gl_compatibility',
        '--rendering-driver', 'opengl3', '--fixed-fps', '60', '--resolution', '1280x720', '--disable-vsync',
        '--quit-after', str(OBSERVATIONS + 5), '--', '--review-trace=' + str(trace), '--arc-sword-followups-stills-dir=' + str(stills)])
    run_engine(runtime, 'actual-replay', ['--headless', '--script', PREFIX + 'replay.gd', '--',
        '--arc-sword-followups-trace=' + str(trace), '--arc-sword-followups-output=' + str(runtime / 'actual-replay.json')])
    audit(runtime, stills)


def replay_only(runtime, stills, replay_dir):
    assert runtime.is_dir() and replay_dir != runtime and replay_dir.resolve().is_relative_to(runtime.resolve())
    originals = {rel(p): sha(p) for base in [runtime, stills] for p in base.rglob('*') if p.is_file()}
    replay_dir.mkdir(parents=True, exist_ok=False)
    trace = runtime / 'main-trace.json'
    try:
        run_engine(replay_dir, 'actual-replay', ['--headless', '--script', PREFIX + 'replay.gd', '--',
            '--arc-sword-followups-trace=' + str(trace), '--arc-sword-followups-output=' + str(replay_dir / 'actual-replay.json')])
    finally:
        unchanged = all((ROOT / p).is_file() and sha(ROOT / p) == h for p, h in originals.items())
        save(replay_dir / 'source-preservation.json', dict(trace_sha256=sha(trace), original_file_sha256=originals,
            original_files_unchanged=unchanged, replay_script_sha256=sha(CONTENT / 'codex_sword_followups_review_replay.gd'),
            reran_main_game=False, reran_import=False, generated_stills=0, generated_videos=0))
        assert unchanged


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['check', 'run', 'replay', 'audit'])
    parser.add_argument('--run-id', default='runtime')
    parser.add_argument('--replay-id')
    parser.add_argument('--audit-id')
    args = parser.parse_args()
    for value in [args.run_id, args.replay_id, args.audit_id]:
        assert value is None or re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', value)
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


if __name__ == '__main__':
    main()

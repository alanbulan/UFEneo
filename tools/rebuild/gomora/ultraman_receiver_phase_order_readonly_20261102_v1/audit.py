"""只读核既有throw_hold_variants的初代六相方案；仅输出符号相序，不造运行资源或接触点。"""
from pathlib import Path
import hashlib
import json
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'reports/review/2026-11-02/gomora-back-lift-ultraman-six-phase-order-readonly-v1'
CANDIDATE = ROOT / 'reports/review/2026-11-02/gomora-super3-resume-front-v1/product'
POSE = 'gomora_back_lift_receiver'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rec(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path), bytes=path.stat().st_size)


def read(path):
    return json.loads(path.read_text('utf-8-sig'))


def save(name, value):
    with (OUT/name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def function(path, name):
    text = path.read_text('utf-8-sig')
    pattern = re.compile(r'(?m)^(?:static )?func '+re.escape(name)+r'\(')
    match = pattern.search(text)
    assert match, (path, name)
    next_function = re.search(r'(?m)^(?:static )?func ', text[match.end():])
    end = match.end()+next_function.start() if next_function else len(text)
    source = text[match.start():end].rstrip()+'\n'
    return dict(file=rec(path), function=name, start=text[:match.start()].count('\n')+1,
        end=text[:end].count('\n'), normalized_lf_source_sha256=hashlib.sha256(source.encode()).hexdigest(), source=source)


def same_phase(frame, target):
    other = frame.get('target',{})
    return other.get('mode','') == 'hold' and other.get('pose','') == target.get('pose','') and int(other.get('sprite',0)) == int(target.get('sprite',0))


def state_index(frames, states, tick):
    target = frames[tick]['target']
    fallback = int(target.get('sprite',0))
    if target.get('mode') != 'hold' or not 0 <= fallback < len(states):
        return fallback, None
    variants = states[fallback].get('throw_hold_variants',[])
    if not variants:
        return fallback, None
    first = last = tick
    while first>0 and same_phase(frames[first-1],target):
        first -= 1
    while last+1<len(frames) and same_phase(frames[last+1],target):
        last += 1
    # 这里的值全为非负整数；对应GDScript两int相除的截断，不用浮点时间。
    variant = min(len(variants)-1,(tick-first)*len(variants)//(last-first+1))
    return max(0,min(len(states)-1,int(variants[variant]))), dict(first=first,last=last,variant_slot=variant)


def main():
    assert not OUT.exists()
    paths = [ROOT/'core/combat/throw_resolver.gd', CANDIDATE/'core/combat/throw_resolver.gd',
        ROOT/'core/combat/throw_hold_points.gd', CANDIDATE/'core/combat/throw_current_capture.gd',
        CANDIDATE/'core/fighters/fighter.gd', CANDIDATE/'presentation/side_view.gd',
        ROOT/'core/fighters/fighter_definition.gd', ROOT/'content/content_database.gd',
        CANDIDATE/'core/combat/match_director.gd', ROOT/'core/replay/replay_recorder.gd',
        CANDIDATE/'content/fighters/gomora/moves/special3.json',
        ROOT/'content/fighters/ultraman/state_frames.json',ROOT/'assets/fighters/ultraman/animations/manifest.json',
        ROOT/'content/fighters/gomora/moves/special3.json',ROOT/'assets/fighters/zetton/animations/manifest.json',
        ROOT/'reports/review/2026-11-02/gomora-back-lift-next-receiver-readonly-v1/ultraman-c-whole-frame-contract.json']
    before = {row['path']:row['sha256'] for row in map(rec,paths)}
    shared=[]
    for name in ['same_hold_phase','floor_safe_hold_sprite','victim_sprite']:
        production = function(paths[0],name)
        candidate = function(paths[1],name)
        assert production['source'] == candidate['source'], name
        shared.append(dict(function=name,production=production,candidate=candidate,exact_normalized_lf_match=True))
    hold_point = function(paths[2],'point')
    precheck = function(paths[2],'can_capture')
    assert 'pose.get("sprite",null)' in hold_point['source']
    assert 'for index in [fallback]+variants+floor_variants:' in precheck['source']
    assert 'if choices.is_empty():return preferred' in shared[1]['candidate']['source']
    move = read(paths[10]); frames=move['frames']
    assert len(frames)==72 and move['throw_current_capture']['target_ids']==['zetton']
    ultra = read(paths[11]); assert POSE not in ultra
    # 这里只是只读符号表，故意不写hit/hurtboxes、抓点或root，不是可加载的state_frames片段。
    states = [dict(state_index=index,semantic_phase=phase,sprite=phase,
        throw_hold_variants=[1,4,5] if index==1 else [],
        throw_hold_floor_variants=[], grip=None,root=None,actor_contact_point=None,
        hurtboxes_pending_actual_source=True) for index,phase in enumerate([0,1,4,5,2,3])]
    timeline=[]
    for tick in range(16,72):
        target = frames[tick]['target']
        mode = target['mode']; key = target.get('pose')
        if mode == 'capture_current':
            timeline.append(dict(raw_tick=tick,mode=mode,source='真实空中当前整相快照',state_index=None,clip_sprite=None,semantic_phase=None))
            continue
        if key == POSE:
            selected,variants = state_index(frames,states,tick)
            entry=states[selected]
            timeline.append(dict(raw_tick=tick,mode=mode,pose=key,target_fallback=int(target.get('sprite',0)),
                selected_state_index=selected,actual_clip_sprite=entry['sprite'],semantic_phase=entry['semantic_phase'],
                variant_run=variants, geometry_accepted=False, root=None, grip=None))
        else:
            selected = int(target.get('sprite',0))
            assert 0 <= selected < len(ultra[key])
            timeline.append(dict(raw_tick=tick,mode=mode,pose=key,target_state_index=selected,
                actual_clip_sprite=ultra[key][selected]['sprite'],semantic_phase=None,
                impact=bool(target.get('impact',False)),existing_target_reference_only=True,
                geometry_accepted=False))
    for row in timeline:
        if 20<=row['raw_tick']<=43:
            assert row['semantic_phase']==(row['raw_tick']-20)//4
    assert [(row['raw_tick'],row['actual_clip_sprite']) for row in timeline if row.get('impact')]==[(52,3)]
    assert all(row['actual_clip_sprite']==1 and row['target_state_index']==8 for row in timeline if row['raw_tick']>=68)
    # can_capture预检只覆盖hold/fallback及variants；phase04/05是root，几何仍须另核。
    required_state_indices=set()
    for frame in frames:
        target=frame.get('target',{})
        if target.get('mode')!='hold': continue
        fallback=int(target.get('sprite',0)); row=states[fallback]
        required_state_indices.update([fallback]+row['throw_hold_variants']+row['throw_hold_floor_variants'])
    assert sorted(required_state_indices)==[0,1,4,5]
    required_sprites=sorted(states[index]['sprite'] for index in required_state_indices)
    assert required_sprites==[0,1,2,3]
    loader=function(paths[7],'fighter')
    simulation_data=function(paths[6],'simulation_data')
    fingerprint=function(paths[8],'_init')
    replay=function(paths[9],'load_file')
    assert 'result.state_frames = read_json(posture_path)' in loader['source']
    assert 'moves, state_frames]' in simulation_data['source']
    assert 'first.simulation_data(), second.simulation_data()' in fingerprint['source']
    assert 'data.get("content") != expected' in replay['source']
    OUT.mkdir(parents=True)
    save('six-phase-state-order-contract.json',dict(schema=1,status='readonly_symbolic_contract_not_runtime_data',
        old_contract=rec(paths[-1]), pose=POSE, state_index_order=states,
        new_atlas_frame_order=[dict(sprite=i,semantic_phase=i) for i in range(6)],
        target_fallback_values_unchanged=[0,1,2,3],
        raw_phase_mapping=[dict(raw=[20+i*4,23+i*4],phase=i,state_index=[0,1,4,5,2,3][i],clip_sprite=i) for i in range(6)],
        root_or_contact_point_values=None, copied_zetton_coordinates=False,
        apply_to_runtime=False, post_requests=0, product_writes=0,godot_run=False,git_write=False))
    save('per-raw-tick-static-resolution.json',dict(
        source_move=rec(paths[10]),candidate_state_symbolic_only=True,timeline=timeline,
        exact_variant_run=[24,35],run_length=12,variant_state_indices=[1,4,5],
        variant_intervals=[[24,27],[28,31],[32,35]],actual_clip_sprites=[1,2,3],
        operation='按已核相同GDScript源码的非负整数公式静态复算；没有启动Godot，不冒称引擎/回放测试。'))
    save('existing-mechanism-source-proof.json',dict(
        unchanged_shared_functions=shared,point_lookup=hold_point,capture_precheck=precheck,
        actual_frame_lookup=function(paths[4],'frame'),presentation_sprite_lookup=function(paths[5],'_animation'),
        content_loader=loader,simulation_data=simulation_data,fingerprint=fingerprint,replay_rejection=replay,
        need_new_core_branch_for_this_index_order=False,
        release_pose_state_indices_are_existing_and_unchanged=True,
        presentation_atlas_sha_not_in_simulation_fingerprint=True))
    save('remaining-data-and-geometry-gates.json',dict(
        current_candidate_allows_ultraman=False,current_target_ids=move['throw_current_capture']['target_ids'],
        current_ultraman_has_receiver_pose=False,
        required_future_hold_point_state_indices=sorted(required_state_indices),
        required_future_override_keys_are_actual_sprite=[str(value) for value in required_sprites],
        all_six_art_semantic_points_must_be_measured=True,
        all_points_root_scale_hurtboxes_null_or_pending=True,
        current_zetton_root_offsets_not_accepted_for_ultraman=True,
        root_mode_phases=[dict(raw=[36,39],phase=4,source_target_reference=frames[36]['target'],accepted_ultraman_root=None),
                          dict(raw=[40,43],phase=5,source_target_reference=frames[40]['target'],accepted_ultraman_root=None)],
        required_data_updates=['新六个本人完整源、统一整图倍率和正常manifest顺序0–5；当前只准先生产phase02。',
            '根另审state_frames顺序0/1/4/5/2/3和state[1].throw_hold_variants=[1,4,5]；不装本符号表。',
            '实际新源测量后补ultraman本人override真实sprite0/1/2/3点，保留杰顿旧点；绝不填null或复制杰顿冒充有效。',
            '根另审target_ids加入ultraman；当前只有zetton，单装图/状态不会让初代可抓。',
            'phase04/05为root模式，不经过hold点预检；既有root常量来自杰顿，初代必须实际测量检查，当前不认兼容。若统一配准仍不合，不暗换技能或改捕框，根再审最小方案。',
            '保持capture_current真实空中起相、entry有限14px双门、拆投/费用/唯一raw52撞地及完整后段，不为适配点位造姿态。'],
        fingerprint_findings=['state_frames整对象经simulation_data参与内容指纹，重排、variants、实际点/框都自然入指纹。',
            'moves整对象也参与；未来target_ids/override变化会使哥莫拉与杰顿对局新指纹也变化。旧证据原样留存，不承诺旧文件跨内容直接F4。',
            'Atlas/manifest纯美术并不自动进入该模拟指纹；必须另以来源/资源SHA锁定，不能用指纹冒称图已审。',
            '没有在Python伪造Godot JSON.stringify的实际最终指纹；新资源和数据完成后需正式main新指纹/原输入独立回放。'],
        new_core_rule_implemented=False,dynamic_test_done=False,contact_accepted=False,installable=False))
    after={name:sha(ROOT/name) for name in before}; assert after==before
    save('readonly-byte-verification.json',dict(before=before,after=after,unchanged=True,
        all_old_contract_contact_fields_unchanged_null=True,post_requests=0,product_writes=0,godot_runs=0,git_writes=0))
    (OUT/'README.md').write_text('''# 初代六相：既有variants机制的只读精确相序

父代理指出的方案在现有索引机制上成立，无需为这段相序新增核心分支。state_frames按[B0(sprite0), B1(sprite1, variants=[1,4,5]), B4(sprite4), B5(sprite5), B2(sprite2), B3(sprite3)]排列。same_hold_phase只比hold/pose/target fallback，不比grip，所以raw24–35是连续12tick，既有victim_sprite用三项variants分成24–27、28–31、32–35。实际state索引1/4/5经Fighter.frame和表现层frame.sprite读取atlas1/2/3；raw36/40的root模式直接取state2/3，读atlas4/5。前后共20→B0、24→B1、28→B2、32→B3、36→B4、40→B5，每相四tick。

正式与未装候选的same_hold_phase、floor_safe_hold_sprite、victim_sprite逐函数归一LF源码相同。方案未登记floor_variants，因此既有floor_safe直接保preferred；没有藏另一个改相分支。hold_points.point取实际pose.sprite，不误取state索引；can_capture捕入前检查fallback和所有variants，对应state0/1/4/5与实际sprite0/1/2/3点都要齐。phase04/05是root模式，不受这个抓点预检保护。

后段严格按冻结候选：raw44–47 thrown_back state0→clip0，48–49 state1→clip1，50–51 thrown_forward state2→clip2，52–59 state3→clip3（仅52撞地），60–67 down state0→clip0，68–71 down state8→clip1；不混state索引与clip索引，不改唯一490撞地。新相只解决20–43；16–19仍是真实空中当前整相。

相序成立尚不代表几何或实际捕获成立：当前目标列表仍只准杰顿，初代没有这套state；hold overrides无初代点，所有新source/root/grip/接触/受击框都待实际源。raw36/40的root常量亦来自杰顿，不能抄给初代当成已校准。若新源按统一整图配准后无法与共有root兼容，须根另审最小数据/规则方案，不能暗换旧波、吸附或改框补假接触。

state_frames及moves整对象已进入simulation_data与内容指纹，所以新增variants/重排/实际点及未来target_ids/override都会自然改指纹；未来包含哥莫拉的杰顿对局也会受moves变化影响。旧证据冻结，不假称跨内容F4兼容。纯美术atlas/manifest不自动入模拟指纹，另保来源SHA。这里没有算一个伪Godot指纹或启动引擎；最终必须根按新资源实际main和原输入独立回放。

本目录只有符号合同、逐tick静态复算及源码/字节证据；不是可装state_frames片段。0 POST、产品写、Godot、Git。原六相合同及初代首母相brief均未回改。
''',encoding='utf-8')
    files=sorted(p for p in OUT.rglob('*') if p.is_file())+[Path(__file__).resolve()]
    save('owned-paths.json',dict(paths=[rec(p) for p in files],frozen_for_root_review=True))
    print(json.dumps(dict(report=OUT.relative_to(ROOT).as_posix(),
        contract_sha256=sha(OUT/'six-phase-state-order-contract.json'),owned_sha256=sha(OUT/'owned-paths.json'),
        index_order_established_statically=True,contact_accepted=False,godot_run=False),ensure_ascii=False))


if __name__=='__main__':
    main()

"""哥莫拉主会话：按指挥审批增量安装ready；候选分支保持只读。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import argparse
import copy
import datetime
import json; json = _LayoutJson
import shutil
import subprocess
import time
from pathlib import Path
Path = _LayoutProjectPath

import numpy as np
from PIL import Image

from gomora_qa import ROOT, WORK, read, save, sha, rel, islands
from gomora_revision import AIR, MANIFEST

OUT = ROOT / 'reports/review/2026-10-23/gomora-installed'
FIGHTER = ROOT / 'content/fighters/gomora'
PLAN = FIGHTER / 'production_plan.json'
STATES = FIGHTER / 'state_frames.json'
RECORD = FIGHTER / 'installation-2026-10-23.json'
STATE_AUDIO = ROOT/'content/audio/state_events.json'


def clean_shared(path):
    assert subprocess.run(['git','diff','--quiet','--',rel(path)],cwd=ROOT).returncode == 0, \
        f'共享路径有未提交改动，停止写入：{rel(path)}'


def checked_save(path, data, expected):
    assert sha(path) == expected, f'读取后文件已被其他会话修改：{path}'
    save(path, data)


def fingerprint_source(path):
    assert sha(path) == baseline()['source_fingerprints'][rel(path)], f'已审包改变：{path}'


def baseline():
    path = OUT / 'baseline.json'
    if path.exists():
        return read(path)
    files = {}
    for directory in [ROOT/'assets/fighters/gomora', FIGHTER]:
        for p in directory.rglob('*'):
            if p.is_file():
                files[rel(p)] = sha(p)
    shared = ['content/audio/runtime.json', 'content/audio/state_events.json',
              'content/presentation/phase3_projectiles.json', 'content/presentation/supers.json']
    data = dict(date='2026-10-23', git_head=subprocess.check_output(
        ['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        inherited_status=subprocess.check_output(['git','status','--short'], cwd=ROOT, text=True),
        manifest=read(MANIFEST), state_frames=read(STATES), production_plan=read(PLAN),
        runtime_sha256=files, shared={p:read(ROOT/p) for p in shared},
        source_fingerprints={rel(p):sha(p) for branch in ['batch3','specials']
                             for p in (WORK/branch/'ready').rglob('*') if p.is_file()},
        main_ledger_sha256=sha(WORK/'ledger.json'),
        main_ledger_requests=len(read(WORK/'ledger.json')['requests']),
        generation_requests_this_round=0)
    save(path, data)
    return data


def review(clip, note):
    path = ROOT / clip['texture'].removeprefix('res://')
    assert sha(path) == clip['atlas_sha256'], path
    return dict(user_approved=True, commander_approved=True, date='2026-10-23',
                verdict=note, atlas_sha256=clip['atlas_sha256'],
                authority='本轮用户转达指挥复核：空中通过、第三批和必杀已经指挥审过，授权安装')


def approve_air():
    before = baseline()
    manifest = read(MANIFEST)
    plan = read(PLAN)
    records = {}
    note = '指挥已审；15个独立空中动作与待机同比例大小一致；vertical_jump为上升/顶点/下落组合'
    for action in AIR:
        clip = manifest['clips'][action]
        verdict = note
        if action in ['air_fall','vertical_jump']:
            verdict += '；air_fall末帧剪影1.076为尾巴后伸，指挥目视确认正常'
        clip['motion_review'] = review(clip, verdict)
        records[action] = copy.deepcopy(clip['motion_review'])
        for cell in plan['cells']:
            if cell['action'] == action:
                cell.update(completed=True, implemented=True, reviewed=True, integrated=True,
                            review_date='2026-10-23', review_note=verdict,
                            review_atlas_sha256=clip['atlas_sha256'])
    # 审批只写元数据，原图和逐tick保持已审状态。
    for p, digest in before['runtime_sha256'].items():
        assert sha(ROOT/p) == digest, p
    save(MANIFEST, manifest)
    save(PLAN, plan)
    save(OUT/'air-approvals.json', records)
    path = FIGHTER/'PROGRESS.md'
    with path.open('a', encoding='utf-8') as stream:
        stream.write('\n## 2026-10-23 指挥复核登记与两批安装\n\n'
                     '- 指挥已审15个独立空中动作；vertical_jump为上升/顶点/下落组合。前后空翻和俯冲不再忽大忽小。审批绑定当前图集SHA256，已审像素和判定保持不变。\n'
                     '- air_fall末帧剪影1.076为尾巴后伸，指挥目视确认正常；解除旧报告对此帧的待审标记。此前章节均为历史截点。\n'
                     '- 第三批与必杀已获本轮安装授权；第四批仍返工，等待通知。\n')
    with (FIGHTER/'MOVES.md').open('a', encoding='utf-8') as stream:
        stream.write('\n### 2026-10-23 空中审批\n\n15个独立空中动作与vertical_jump组合已获指挥复核通过；air_fall末帧1.076是尾巴后伸，目视正常。当前图集指纹审批见 `reports/review/2026-10-23/gomora-installed/air-approvals.json`。旧待审与阻塞记录为历史。\n')
    print('已绑定空中审批指纹；正式像素与逐tick保持不变')


def get_package(branch):
    ready = WORK/branch/'ready'
    clips = read(ready/('manifest.merge.json' if branch=='batch3' else 'manifest-merge.json'))['clips']
    moves = read(ready/'moves.merge.json') if branch=='batch3' else {
        k:read(ready/'moves'/f'{k}.json') for k in clips}
    states = read(ready/'state_frames.merge.json') if branch=='batch3' else {}
    return ready, clips, moves, states


def with_audio(action, seq, move=None):
    hooks = read(WORK/'audio/hooks.json')
    for frame in seq:
        frame['events'] = [e for e in frame.get('events',[]) if e.get('kind')!='sound']
    if move is None:
        if action=='charge':
            for frame in seq:
                frame['audio_loop'] = 'gomora_charge_loop'
        # 受击、发射上升/下落吼由真实命中voice负责，避免重复。
        cues = [] if action.startswith(('hit_','launch_')) else hooks['states'][action].get('events',[])
        return copy.deepcopy(cues)
    hook = hooks['moves'][action]
    if action=='air_special':
        # 旧音频包编写时能力未定；本轮已明确审定并授权空中P。
        hook = dict(cues=dict(start='gomora_charge_start',release='gomora_vibration_cast1',
                             loop='gomora_vibration_loop1'),
                    audio=dict(hit='gomora_vibration_hit',block='gomora_guard_scrape'))
    cues = hook['cues']
    move['audio'] = copy.deepcopy(hook['audio'])
    seq[0]['events'].append(dict(kind='sound',id=cues['start']))
    release = int(move['startup'])
    if cues.get('release') and release < len(seq):
        seq[release]['events'].append(dict(kind='sound',id=cues['release']))
    if cues.get('loop'):
        for frame in seq[release:release+int(move['active'])]:
            frame['audio_loop'] = cues['loop']
    if action=='motion_41236':
        move['audio'].update(lift='gomora_throw_lift',lift_sprite=2)
    return [dict(kind='sound',id=cues['start'],at='move_start')]


def audit_clip(action, clip, seq):
    atlas = Image.open(ROOT/clip['texture'].removeprefix('res://')).convert('RGBA')
    assert sha(ROOT/clip['texture'].removeprefix('res://')) == clip['atlas_sha256']
    assert len(clip['rects']) == len(clip['ticks']) == len(clip['anchors'])
    counts = [sum(int(f['sprite'])==i for f in seq) for i in range(len(clip['rects']))]
    assert counts == clip['ticks'], (action, counts, clip['ticks'])
    frames = []
    for i,(x,y,w,h) in enumerate(clip['rects']):
        assert 0<=x<x+w<=atlas.width and 0<=y<y+h<=atlas.height
        image = atlas.crop((x,y,x+w,y+h))
        a = np.array(image)
        assert set(np.unique(a[:,:,3])) == {0,255}, (action,i,'真透明二值Alpha')
        assert len(np.unique(a[a[:,:,3]>0,:3],axis=0)) <= 32, (action,i,'32色')
        assert not islands(image), (action,i,'孤岛')
        anchor = clip['anchors'][i]
        sample = next(f for f in seq if int(f['sprite'])==i)
        hurt = sample['hurtboxes']
        # 框从候选成品实测；每个受击框必须实际覆盖实体像素。
        for bx,by,bw,bh in hurt:
            left=max(0,anchor[0]+bx);top=max(0,anchor[1]-by-bh)
            right=min(w,anchor[0]+bx+bw);bottom=min(h,anchor[1]-by)
            assert right>left and bottom>top and a[top:bottom,left:right,3].any(), (action,i,'受击框悬空')
        # 接触招式取框中心；投射/震地/斜束按其独立特效Alpha审计。
        contact = action in ['wake_low','wake_mid','dash_light','dash_heavy','back_counter',
                             'dodge_counter','guard_counter','motion_236','motion_623','motion_214','motion_41236']
        if contact:
            for bx,by,bw,bh in sample['hitboxes']:
                cx=anchor[0]+bx+bw//2;cy=anchor[1]-by-bh//2
                assert 0<=cx<w and 0<=cy<h and a[cy,cx,3]>0, (action,i,'攻击点不在实体部位')
        frames.append(dict(sprite=i,ticks=counts[i],anchor=anchor,alpha_bbox=list(image.getbbox()),
                           hurtboxes=len(hurt),hitboxes=len(sample['hitboxes'])))
    return dict(atlas_sha256=clip['atlas_sha256'],frames=frames,tick_count=len(seq),
                state_frames_consistent=True,alpha='0/255',palette_max=32,isolated_pixels=False)


def install_action(branch, action):
    baseline()
    ready, clips, moves, source_states = get_package(branch)
    assert action in clips
    manifest = read(MANIFEST); expected = {p:sha(p) for p in [MANIFEST,STATES,PLAN]}
    assert action not in manifest['clips'], f'禁止覆盖已装动作：{action}'
    old_clips=copy.deepcopy(manifest['clips'])
    states = read(STATES); old_states=copy.deepcopy(states)
    plan = read(PLAN)
    clip=copy.deepcopy(clips[action])
    source=ready/action/'atlas.png' if branch=='batch3' else ready/'animations'/action/'atlas.png'
    fingerprint_source(source)
    target=ROOT/clip['texture'].removeprefix('res://')
    assert not target.exists(), target
    target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)
    move=copy.deepcopy(moves.get(action))
    seq=move['frames'] if move else copy.deepcopy(source_states[action])
    events=with_audio(action,seq,move)
    clip['audio_events']=events
    clip['motion_review']=review(clip,'指挥已审、已安装；本轮按已审ready增量合并，图集像素未改变')
    if 'reviewed' in clip:clip['reviewed']=True
    clip['review_status']='指挥已审、已安装'
    manifest['clips'][action]=clip
    states[action]=copy.deepcopy(seq)
    paths=[target,MANIFEST,STATES,PLAN,RECORD]
    if move:
        move['production_note']=str(move.get('production_note','')).replace('仅候选','指挥已审、已安装').replace('不安装','已安装')
        move_path=FIGHTER/'moves'/f'{action}.json';assert not move_path.exists(),move_path
        save(move_path,move);paths.append(move_path)
    else:
        clean_shared(STATE_AUDIO)
        state_audio=read(STATE_AUDIO);old_audio=copy.deepcopy(state_audio);audio_sha=sha(STATE_AUDIO)
        state_audio.setdefault('gomora',{})[action]=events
        assert {k:v for k,v in old_audio.items() if k!='gomora'}=={k:v for k,v in state_audio.items() if k!='gomora'}
        checked_save(STATE_AUDIO,state_audio,audio_sha);paths.append(STATE_AUDIO)
    definition_path=FIGHTER/'definition.json';definition=read(definition_path)
    if action in definition.get('unsupported_moves',[]):
        definition['unsupported_moves'].remove(action);save(definition_path,definition);paths.append(definition_path)
    commands_path=FIGHTER/'command_table.json';commands=read(commands_path);changed=False
    for command in commands:
        if command['move']==action and move and command['display_name']!=move['display_name']:
            command['display_name']=move['display_name'];changed=True
    if changed:save(commands_path,commands);paths.append(commands_path)
    for cell in plan['cells']:
        if cell['action']==action:
            cell.update(completed=True,implemented=True,reviewed=True,integrated=True,animation=True,
                        frames=len(clip['rects']),duration_ticks=sum(clip['ticks']),hitboxes=True,hurtboxes=True,
                        audio=True,review_date='2026-10-23',review_note='指挥已审、已安装',
                        review_atlas_sha256=clip['atlas_sha256'],report=rel(OUT/'installation-audit.json'))
            if move:cell['planned_name']=move['display_name']
    audit=audit_clip(action,clip,seq)
    checked_save(MANIFEST,manifest,expected[MANIFEST]);checked_save(STATES,states,expected[STATES]);checked_save(PLAN,plan,expected[PLAN])
    assert all(read(MANIFEST)['clips'][k]==v for k,v in old_clips.items())
    assert all(read(STATES)[k]==v for k,v in old_states.items())
    record=read(RECORD) if RECORD.exists() else dict(date='2026-10-23',generation_requests=0,actions={})
    record['actions'][action]=dict(branch=branch,status='指挥已审、已安装',source=rel(source),
        source_sha256=sha(source),runtime=rel(target),audit=audit,review=clip['motion_review'])
    save(RECORD,record)
    return paths


def install_effects():
    baseline();ready=WORK/'specials/ready'
    effects_path=ROOT/'content/presentation/phase3_projectiles.json'
    supers_path=ROOT/'content/presentation/supers.json'
    for path in [effects_path,supers_path]:clean_shared(path)
    effects=read(effects_path);supers=read(supers_path)
    expected={p:sha(p) for p in [effects_path,supers_path]}
    new=read(ready/'effects-merge.json');cinema=read(ready/'cinematic-merge.json');paths=[]
    for action in (ready/'effects').iterdir():
        if not action.is_dir():continue
        source=action/'atlas.png';fingerprint_source(source)
        dest=ROOT/'assets/effects/gomora'/action.name/'atlas.png'
        assert not dest.exists(),dest
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest);paths.append(dest)
    for key,value in new.items():
        assert key not in effects,key
        value['approved']=True;value['review_status']='指挥已审、已安装'
        assert sha(ROOT/value['texture'].removeprefix('res://'))==value['atlas_sha256']
        effects[key]=value
    assert 'gomora' not in supers
    supers.update(cinema)
    checked_save(effects_path,effects,expected[effects_path]);checked_save(supers_path,supers,expected[supers_path])
    paths += [effects_path,supers_path]
    print('必杀独立特效与三级演出已增量合并')
    return paths


def align_air_special():
    action='air_special';index=3
    manifest=read(MANIFEST);clip=manifest['clips'][action]
    move_path=FIGHTER/'moves/air_special.json';move=read(move_path);states=read(STATES)
    assert clip['anchors'][index]==[384,304]
    # 主游戏before实录确认：模拟x固定430，索引3躯干突然左跳约136px。
    # 本帧尾根原图换算x242，相邻有效发射帧约378；只修整帧锚点，像素不动。
    old=list(clip['anchors'][index]);new=[248,304];shift=old[0]-new[0]
    clip['anchors'][index]=new
    for frame in move['frames']:
        if int(frame['sprite'])!=index:continue
        for field in ['hurtboxes','hitboxes']:
            for box in frame[field]:box[0]+=shift
    states[action]=copy.deepcopy(move['frames'])
    correction=dict(date='2026-10-23',sprite_index=index,human_frame_number=4,
                    user_reference='用户所指偏左第3帧经0/1起始编号共同复核：实机异常位于索引3',
                    before=old,after=new,world_x_correction=shift,
                    reason='主游戏模拟根点x不动，画中躯干在索引3左跳；按尾根/躯干中心对齐邻帧',
                    before_movie=rel(OUT/'runtime/air-special-anchor-before.mp4'),
                    image_pixels_unchanged=True,boxes_shifted_with_anchor=True)
    clip['anchor_revision']=correction
    save(MANIFEST,manifest);save(move_path,move);save(STATES,states)
    record=read(RECORD);record['actions'][action]['anchor_revision']=correction
    record['actions'][action]['audit']=audit_clip(action,clip,move['frames']);save(RECORD,record)
    save(OUT/'air-special-anchor-correction.json',correction)
    return [MANIFEST,move_path,STATES,RECORD,OUT/'air-special-anchor-correction.json',Path(__file__)]


def commit_paths(message, paths):
    names=list(dict.fromkeys(rel(p) for p in paths))
    def git(args):
        for attempt in range(20):
            result=subprocess.run(['git',*args],cwd=ROOT,capture_output=True,text=True)
            if result.returncode==0:return result
            if 'index.lock' not in result.stderr:raise RuntimeError(result.stderr[-1600:])
            time.sleep(3)
        raise RuntimeError('index.lock仍由其他会话占用；保留改动，不删除锁')
    git(['add','-f','--',*names])
    result=git(['-c','core.quotepath=false','commit','-m',message,'--',*names])
    print(result.stdout.splitlines()[0],flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['baseline','approve-air','install-batch3','install-specials','effects','align-air-special'])
    parser.add_argument('--action')
    args = parser.parse_args()
    if args.command == 'baseline':
        baseline()
        print('接手基线已保存')
    elif args.command=='approve-air':
        approve_air()
    elif args.command=='effects':
        commit_paths('安装哥莫拉已审必杀特效与三级演出资源',install_effects()+[Path(__file__)])
    elif args.command=='align-air-special':
        commit_paths('按主游戏实录对齐哥莫拉空中必杀第四张躯干锚点',align_air_special())
    else:
        branch='batch3' if args.command=='install-batch3' else 'specials'
        actions=[args.action] if args.action else list(get_package(branch)[1])
        for action in actions:
            if RECORD.exists() and action in read(RECORD)['actions']:
                continue
            paths=install_action(branch,action)
            commit_paths('安装哥莫拉已审动作'+action,paths+[Path(__file__)])

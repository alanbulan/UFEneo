"""哥莫拉第四批主会话安装；只读候选，逐动作增量合并并提交。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import argparse
import copy
import subprocess
from pathlib import Path
Path = _LayoutProjectPath

import numpy as np
from PIL import Image, ImageDraw

from gomora_qa import ROOT, WORK, read, save, sha, rel, islands, font
from gomora_ready_install import commit_paths, checked_save, clean_shared

OUT = ROOT/'reports/review/2026-10-23/gomora-fourth-installed'
FIGHTER = ROOT/'content/fighters/gomora'
MANIFEST = ROOT/'assets/fighters/gomora/animations/manifest.json'
STATES = FIGHTER/'state_frames.json'
PLAN = FIGHTER/'production_plan.json'
RECORD = FIGHTER/'installation-fourth-2026-10-23.json'
STATE_AUDIO = ROOT/'content/audio/state_events.json'
ACTIONS = 'throw_forward throw_back air_throw dash_throw throw_tech grabbed thrown_forward thrown_back thrown_air thrown_dash intro victory defeat timeout taunt'.split()
VICTIMS = ACTIONS[5:10]
PENDING = ['intro', 'dash_throw', 'timeout']


def package(action):
    folder = WORK/'batch4'/('rework/pending-director-head' if action in PENDING else 'ready')/action
    clip = read(folder/'clip.json')
    move = read(folder/'move.json') if (folder/'move.json').exists() else None
    seq = move['frames'] if move else read(folder/'state_frames.merge.json')[action]
    return folder, clip, move, seq


def baseline():
    path = OUT/'baseline.json'
    if path.exists():
        return read(path)
    sources = {rel(p): sha(p) for a in ACTIONS for p in package(a)[0].rglob('*') if p.is_file()}
    data = dict(git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                inherited_status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),
                manifest=read(MANIFEST), states=read(STATES), plan=read(PLAN),
                protected={rel(p):sha(p) for d in [ROOT/'assets/fighters/gomora',FIGHTER/'moves']
                           for p in d.rglob('*') if p.is_file()},
                source_fingerprints=sources, ledger={rel(p):dict(sha256=sha(p),requests=len(read(p)['requests']))
                    for p in [WORK/'ledger.json',WORK/'batch3/ledger.json',WORK/'batch4/ledger.json',WORK/'specials/ledger.json']},
                authority='本轮用户转达指挥已审15动作，明确授权安装；旧pending三动作按对应完整交接包安装，旧审批不重写。',
                generation_requests_this_round=0)
    save(path,data)
    return data


def audit_clip(action, clip, seq):
    path = ROOT/clip['texture'].removeprefix('res://')
    assert sha(path)==clip['atlas_sha256'], action
    assert len(clip['rects'])==len(clip['ticks'])==len(clip['anchors'])
    if action in VICTIMS:
        assert [f['sprite'] for f in seq]==list(range(len(clip['rects'])))
    else:
        assert [sum(f['sprite']==i for f in seq) for i in range(len(clip['ticks']))]==clip['ticks']
    atlas=Image.open(path).convert('RGBA');rows=[]
    for i,(x,y,w,h) in enumerate(clip['rects']):
        image=atlas.crop((x,y,x+w,y+h));alpha=np.asarray(image)[:,:,3]
        assert set(np.unique(alpha))=={0,255}
        assert not islands(image), (action,i,'孤立像素')
        frame=next(f for f in seq if f['sprite']==i);anchor=clip['anchors'][i]
        for bx,by,bw,bh in frame['hurtboxes']:
            l=max(0,anchor[0]+bx);r=min(w,anchor[0]+bx+bw)
            t=max(0,anchor[1]-by-bh);b=min(h,anchor[1]-by)
            assert r>l and b>t and alpha[t:b,l:r].any(),(action,i,'受击框悬空')
        for bx,by,bw,bh in frame['hitboxes']:
            cx=anchor[0]+bx+bw//2;cy=anchor[1]-by-bh//2
            assert 0<=cx<w and 0<=cy<h and alpha[cy,cx],(action,i,'攻击点悬空')
        target=frame.get('target',{})
        if target.get('mode')=='hold':
            gx,gy=target['grip'];px=anchor[0]+gx;py=anchor[1]-gy
            assert 0<=px<w and 0<=py<h and alpha[py,px],(action,i,'抓点悬空')
        rows.append(dict(sprite=i,hurtboxes=len(frame['hurtboxes']),hitboxes=len(frame['hitboxes']),
                         grip=target.get('grip') if target.get('mode')=='hold' else None,
                         alpha_bbox=list(image.getbbox())))
    return dict(atlas_sha256=clip['atlas_sha256'],frames=rows,pose_rows=len(seq),
                duration_ticks=sum(clip['ticks']),state_frames_consistent=True)


def prepare():
    baseline()
    # 审片原件保持四倍联系表/八倍头条带；会话只读这个宽1024缩略索引。
    sheet=Image.new('RGB',(1024,165*len(ACTIONS)), '#202632');d=ImageDraw.Draw(sheet)
    for j,a in enumerate(ACTIONS):
        folder,clip,_,_=package(a);atlas=Image.open(folder/'atlas.png').convert('RGBA')
        d.text((6,j*165+2),a,font=font(16),fill='white')
        for i,(x,y,w,h) in enumerate(clip['rects']):
            frame=atlas.crop((x,y,x+w,y+h));frame.thumbnail((120,110),Image.Resampling.NEAREST)
            sheet.paste(frame,(i*128,j*165+26),frame)
    OUT.mkdir(parents=True,exist_ok=True);sheet.save(OUT/'approved-contact-index-1024.png')
    print('接手基线及宽1024审片索引已保存')


def install_action(action):
    base=baseline();folder,clip,move,seq=package(action)
    for p in folder.rglob('*'):
        if p.is_file():assert sha(p)==base['source_fingerprints'][rel(p)]
    manifest=read(MANIFEST);states=read(STATES);plan=read(PLAN)
    assert action not in manifest['clips'] and action not in states
    old_clips=copy.deepcopy(manifest['clips']);old_states=copy.deepcopy(states)
    expected={p:sha(p) for p in [MANIFEST,STATES,PLAN]}
    hooks=read(WORK/'audio/hooks.json');clip=copy.deepcopy(clip);seq=copy.deepcopy(seq)
    cues=[]
    for f in seq:f['events']=[e for e in f.get('events',[]) if e.get('kind')!='sound']
    if move:
        move=copy.deepcopy(move);move['frames']=seq
        if action=='taunt':
            seq[0]['events'].append(dict(kind='sound',id='gomora_roar_threat'))
        else:
            # 空抓用挥爪；接触抓握、提拉、摔地均只由真实捕获/撞地触发。
            seq[0]['events'].append(dict(kind='sound',id='gomora_claw_swing'))
            move['audio']=copy.deepcopy(hooks['moves'][action]['audio'])
            move['audio'].update(lift='gomora_throw_lift',lift_sprite=2)
        cues=copy.deepcopy(seq[0]['events'])
    else:
        cues=copy.deepcopy(hooks['states'].get(action,{}).get('events',[]))
        if action in VICTIMS or action in ['victory','defeat']:cues=[]
    clip.update(audio_events=cues,review_status='指挥已审、已安装')
    clip['motion_review']=dict(user_approved=True,commander_approved=True,date='2026-10-23',
        verdict='指挥已审、已安装',authority=base['authority'],atlas_sha256=clip['atlas_sha256'])
    target=ROOT/clip['texture'].removeprefix('res://');assert not target.exists()
    target.parent.mkdir(parents=True,exist_ok=True)
    import shutil
    shutil.copy2(folder/'atlas.png',target)
    audit=audit_clip(action,clip,seq)
    manifest['clips'][action]=clip;states[action]=seq
    paths=[MANIFEST,STATES,PLAN,RECORD,target,Path(__file__),FIGHTER/'PROGRESS.md']
    if move:
        path=FIGHTER/'moves'/f'{action}.json';assert not path.exists();save(path,move);paths.append(path)
        if action=='taunt':
            commands_path=FIGHTER/'command_table.json';commands=read(commands_path)
            assert not any(c['move']=='taunt' for c in commands)
            entry=copy.deepcopy(next(c for c in read(ROOT/'content/fighters/ultraseven/command_table.json') if c['move']=='taunt'))
            entry['display_name']='挑衅招爪（防御+投技）';commands.append(entry)
            save(commands_path,commands);paths.append(commands_path)
    else:
        clean_shared(STATE_AUDIO);audio=read(STATE_AUDIO);digest=sha(STATE_AUDIO)
        assert action not in audio['gomora'];audio['gomora'][action]=cues
        checked_save(STATE_AUDIO,audio,digest);paths.append(STATE_AUDIO)
    for cell in plan['cells']:
        if cell['action']==action:
            cell.update(completed=True,implemented=True,reviewed=True,integrated=True,animation=True,
                frames=len(clip['rects']),duration_ticks=sum(clip['ticks']),hitboxes=True,hurtboxes=True,audio=True,
                review_date='2026-10-23',review_note='指挥已审、已安装',review_atlas_sha256=clip['atlas_sha256'],
                report=rel(OUT/'README.md'))
    definition=read(FIGHTER/'definition.json')
    if action in definition['unsupported_moves']:
        definition['unsupported_moves'].remove(action);save(FIGHTER/'definition.json',definition);paths.append(FIGHTER/'definition.json')
    checked_save(MANIFEST,manifest,expected[MANIFEST]);checked_save(STATES,states,expected[STATES]);checked_save(PLAN,plan,expected[PLAN])
    assert all(read(MANIFEST)['clips'][k]==v for k,v in old_clips.items())
    assert all(read(STATES)[k]==v for k,v in old_states.items())
    record=read(RECORD) if RECORD.exists() else dict(generation_requests=0,actions={})
    record['actions'][action]=dict(status='指挥已审、已安装',source=rel(folder/'atlas.png'),
        runtime=rel(target),source_sha256=sha(folder/'atlas.png'),audit=audit)
    save(RECORD,record)
    with (FIGHTER/'PROGRESS.md').open('a',encoding='utf-8') as f:
        f.write(f'\n- 2026-10-23 第四批 `{action}`：指挥已审、已安装；正式图集与已审交接SHA一致，状态/判定和音效同步。\n')
    commit_paths('安装哥莫拉第四批已审动作'+action,paths)


def finalize():
    base=baseline();record=read(RECORD);clips=read(MANIFEST)['clips'];states=read(STATES)
    assert list(record['actions'])==ACTIONS
    assert all(sha(ROOT/p)==h for p,h in base['protected'].items() if p!=rel(MANIFEST))
    assert all(read(MANIFEST)['clips'][k]==v for k,v in base['manifest']['clips'].items())
    assert all(states[k]==v for k,v in base['states'].items())
    assert all(sha(ROOT/p)==h for p,h in base['source_fingerprints'].items())
    for p,data in base['ledger'].items():assert sha(ROOT/p)==data['sha256']
    coverage_path=FIGHTER/'coverage.json';coverage=read(coverage_path)
    for action in ACTIONS:
        row=record['actions'][action];assert audit_clip(action,clips[action],states[action])==row['audit']
        coverage['actions'][action]=dict(status='指挥已审、已安装',frames=len(clips[action]['rects']),
            ticks=sum(clips[action]['ticks']),atlas_sha256=clips[action]['atlas_sha256'],runtime_observed=False,
            report=rel(OUT/'README.md'))
    save(coverage_path,coverage)
    audio_path=FIGHTER/'audio_install.json';audio=read(audio_path)
    audio['installed_moves']=list(dict.fromkeys(audio['installed_moves']+[a for a in ACTIONS if (FIGHTER/'moves'/f'{a}.json').exists()]))
    audio['installation_2026_10_23']['fourth_batch']='指挥已审、已安装'
    audio['fourth_batch']=dict(actions=ACTIONS,contact_policy='挥空仅挥爪；真实抓中才播放抓握/提拉，真实撞地才播放投技落地。被投姿势不提前播放摔地声。')
    save(audio_path,audio)
    with (FIGHTER/'MOVES.md').open('a',encoding='utf-8') as f:
        f.write('\n## 2026-10-23 第四批已审安装\n\n'
                '本轮用户转达指挥已审全部15动作；旧交接中intro、dash_throw、timeout的待审字段为历史。三动作从pending-director-head完整包按原指纹安装，其余从ready安装；候选文件只读。\n\n'
                '前投：L；后投：后+L；空投：空中L；冲刺擒抱：冲刺中L；抱起压摔：41236+L（上轮已装）。拆投：被抓后三个真实tick内L；挑衅：U+L。\n\n'
                '前后投各8整帧；空投、冲刺投各6整帧；拆投4帧；被抓及四种被投各4独立姿势；登场/胜利8帧，战败/时间到4帧，挑衅6帧。抓握点沿用已审实际爪点，受方腰抓点与分层受击框同步。\n\n'
                '投技只有起手挥爪声可在空抓播放；抓握、提拉、摔地分别由捕获和撞地触发。演出接入已安装原创吼声；听感仍由用户判断。图集像素与已审包逐文件SHA一致。\n')
    save(OUT/'installation-audit.json',dict(actions=record['actions'],old_clips_preserved=True,
        old_states_preserved=True,old_pixels_preserved=True,candidates_read_only=True,ledgers_unchanged=True,
        generation_requests_this_round=0))
    commit_paths('同步哥莫拉第四批安装覆盖与音效交接记录',
                 [coverage_path,audio_path,FIGHTER/'MOVES.md',Path(__file__)])


def unlock():
    clips=read(MANIFEST)['clips'];record=read(RECORD)['actions']
    assert all(clips[a]['motion_review']['commander_approved'] and a in record for a in ACTIONS)
    assert all(a in clips for a in ['walk_forward','walk_back'])
    path=FIGHTER/'definition.json';data=read(path);digest=sha(path)
    assert not data['playable']
    data.update(playable=True,pilot_manual_ready=True,pilot_lock_reason='',walks_installed=True,
        selection_authorization='用户2026-10-23明确授权：第四批安装后解除试制选人锁，训练和对战自由选择；未制作的air_pulse继续禁用')
    checked_save(path,data,digest)
    selection_path=ROOT/'content/roster/selection.json';clean_shared(selection_path)
    selection=read(selection_path);selection_sha=sha(selection_path)
    for entry in selection['entries']:
        if entry['id']=='gomora':
            for form in entry['forms']:
                if form['id']=='default':form.update(implemented=True,production_status='pilot_partial_free_selection')
    checked_save(selection_path,selection,selection_sha)
    with (FIGHTER/'PROGRESS.md').open('a',encoding='utf-8') as f:
        f.write('\n- 2026-10-23 按用户明确授权解除哥莫拉试制选人锁：训练、对战电脑及本地双人可自由选择；未制作的air_pulse保留禁用。准备检查器按授权与安装状态验证，不再强制已开放角色上锁。\n')
    commit_paths('按授权开放哥莫拉训练与对战自由选人',[path,selection_path,FIGHTER/'PROGRESS.md',Path(__file__),
        ROOT/'tools/check_stage4_preparation.py',ROOT/'tools/check_stage4_pilot.py',ROOT/'tools/rebuild/gomora/gomora_verify.py'])


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['prepare','install','finalize','unlock']);ap.add_argument('--action');args=ap.parse_args()
    if args.command=='prepare':prepare()
    elif args.command=='finalize':finalize()
    elif args.command=='unlock':unlock()
    else:
        for action in ([args.action] if args.action else ACTIONS):
            if RECORD.exists() and action in read(RECORD)['actions']:continue
            install_action(action)

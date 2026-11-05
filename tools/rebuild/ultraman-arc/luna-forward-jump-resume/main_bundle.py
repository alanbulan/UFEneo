"""八相前跳当前主游戏RAM合同；旧收据只读，不恢复历史reports，不开放装甲。"""
from functools import lru_cache
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np
from PIL import Image

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
REVIEW = ROOT / 'tests/review/fighters/ultraman-arc/luna_forward_jump'
REPORT = ROOT / 'reports/luna-forward-jump-resume'
STAGE = ROOT / 'art/fighters/ultraman-arc__luna/stage2'
DEFAULT_MANIFEST = STAGE / 'forward_jump-registered-20261105-v1/manifest.json'
FID = 'ultraman-arc__luna'
CLOCKS = {'takeoff':[1,1], 'flip_forward':[8,8,8,9], 'land':[2,2]}
STATE_KEYS = {'takeoff':'takeoff', 'flip_forward':'diagonal_air', 'land':'land'}
CAPTURE_N = [0,1,2,7,8,15,16,23,24,32,33,34,35,36,37]
KNOWN_VSYNC_WARNING = 'WARNING: Could not set V-Sync mode, as changing V-Sync mode is not supported by the graphics driver.'

def classify_diagnostics(logs):
    result={'policy':'Only the exact confirmed unsupported-V-Sync warning is permitted; every other WARNING/ERROR/Parse Error is fatal.',
            'known_environment_warnings':[], 'fatal_diagnostics':[], 'audio_driver':'Dummy', 'rendering_method':'gl_compatibility'}
    for source,contents in logs.items():
        for number,line in enumerate(contents.splitlines(),1):
            if not any(marker in line for marker in ['SCRIPT ERROR:','Parse Error:','ERROR:','WARNING:']):continue
            item={'source':source,'line_number':number,'text':line}
            if line.strip()==KNOWN_VSYNC_WARNING:
                item['classification']='confirmed_unsupported_vsync_environment_warning'
                result['known_environment_warnings'].append(item)
            else:result['fatal_diagnostics'].append(item)
    result['passed']=not result['fatal_diagnostics']
    return result

def read(path): return json.loads(Path(path).read_text('utf-8'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path): return {'path':Path(path).resolve().as_posix(),'sha256':sha(path)}
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)

@lru_cache(maxsize=1)
def aliases(): return read(ROOT/'art/source-index.json')['aliases']

def resolve(value):
    value=str(value).removeprefix('res://')
    p=Path(value)
    if p.is_absolute(): return p.resolve()
    mapping=aliases();seen=set()
    while value in mapping:
        assert value not in seen,'来源别名循环'
        seen.add(value);value=mapping[value]
    p=Path(value)
    return (p if p.is_absolute() else ROOT/p).resolve()

def checked(value):
    p=resolve(value['path']);assert p.is_file(),str(p)
    assert sha(p)==value['sha256'],'SHA改变：'+str(p)
    return p

def state_frames(rows):
    result=[]
    for row in rows:
        with Image.open(resolve(row['image'])) as im:
            assert im.size==(320,320) and im.mode=='RGBA'
            a=np.asarray(im)[:,:,3];assert set(np.unique(a))=={0,255}
            assert not any([a[0].any(),a[-1].any(),a[:,0].any(),a[:,-1].any()])
            ys,_=np.where(a);top,bottom=int(ys.min()),int(ys.max())+1;boxes=[]
            for n in range(3):
                y0,y1=top+(bottom-top)*n//3,top+(bottom-top)*(n+1)//3;_,xs=np.where(a[y0:y1])
                if len(xs):boxes.append([int(xs.min())-160,280-y1,int(xs.max()-xs.min()+1),y1-y0])
        result.extend({'sprite':row['phase'],'dx':0,'dy':0,'hitboxes':[],'hurtboxes':copy.deepcopy(boxes),'cancel':[],'events':[]} for _ in range(row['ticks']))
    return result

def build(manifest_path,review_path,out,engine):
    out=out.resolve();out.relative_to(REPORT);assert not out.exists()
    manifest=read(manifest_path);review=read(review_path)
    assert review['reviewer']=='root_delegated_by_user' and review['accepted_for_formal_main_candidate'] is True
    assert set(manifest['actions'])==set(CLOCKS)
    resources={manifest_path.resolve(),review_path.resolve(),ROOT/'art/source-index.json',ROOT/'project.godot',ROOT/'tools/godot_lock.py',engine}
    clips={};states={};source_shas=[]
    for action,ticks in CLOCKS.items():
        group=manifest['actions'][action];rows=group['frames'];clip_path=checked(group['clip']);clip=read(clip_path);resources.add(clip_path)
        assert [r['phase'] for r in rows]==list(range(len(ticks))) and [r['ticks'] for r in rows]==ticks
        atlas=resolve(clip['texture']);assert sha(atlas)==clip['atlas_sha256'];resources.add(atlas)
        assert clip['ticks']==ticks and clip['anchors']==[[160,280]]*len(ticks) and clip['anchor_y']==280
        assert clip['source_fighter']==FID and not clip['loop'] and clip['cell']==320
        if action=='flip_forward':assert clip['trajectory_driven'] is True
        with Image.open(atlas) as atlas_im:
            for row in rows:
                for key in ['source','image']:
                    p=checked({'path':row[key],'sha256':row[key+'_sha256']});resources.add(p)
                for key in ['whole_source_sample','previous_frame','previous_receipt']:
                    if key in row:resources.add(checked(row[key]))
                source_shas.append(row['source_sha256'])
                with Image.open(resolve(row['image'])) as im:
                    x,y,w,h=clip['rects'][row['phase']]
                    assert atlas_im.crop((x,y,x+w,y+h)).tobytes()==im.tobytes()
                    if 'whole_source_sample' in row:
                        with Image.open(checked(row['whole_source_sample'])) as sample:
                            assert sample.size==(159,159)
                            expected=Image.new('RGBA',(320,320));expected.paste(sample,tuple(row['whole_source_destination_offset']))
                            assert expected.tobytes()==im.tobytes(),'必须完整159采样整体平移，不能切片或修身体'
        clip['texture']=atlas.as_posix();clips[action]=clip;states[STATE_KEYS[action]]=state_frames(rows)
    assert len(source_shas)==8 and len(set(source_shas))==8
    prior=STAGE/'movement-contract-20261101-v1';bundle=read(prior/'bundle.json');old_states=read(prior/'state_frames.json');resources.update([prior/'bundle.json',prior/'state_frames.json'])
    for action in ['idle','turn']:
        folder=STAGE/'goal-closeout-20261101-v1'/action;clip=copy.deepcopy(bundle['clips'][action]);atlas=folder/'atlas.png'
        assert sha(atlas)==clip['atlas_sha256'];clip.update(texture=atlas.as_posix(),source_fighter=FID);clips[action]=clip;states[action]=old_states[action];resources.update([atlas,folder/'frames.json'])
        for row in read(folder/'frames.json')['frames']:
            for key in ['source','image']:resources.add(checked({'path':row[key],'sha256':row[key+'_sha256']}))
    flags_path=ROOT/f'content/fighters/{FID}/definition.json';flags=read(flags_path)
    assert all(flags[k] is False for k in ['implemented','playable','select_visible'])
    model=ROOT/f'art/fighters/{FID}/model/model-native.png';resources.update([flags_path,model])
    for name in ['core','input','content','presentation','app','ui','third_party/shoto','tests/review/fighters/ultraman-arc/luna_forward_jump','tools/rebuild/ultraman-arc/luna-forward-jump-resume','tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1']:
        resources.update(p for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix in {'.gd','.json','.tres','.tscn','.gdshader','.py'})
    for name in ['assets/ui','assets/fonts','assets/stages','assets/backgrounds','assets/fighters/zetton']:
        resources.update(p for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix in {'.png','.wav','.ogg','.ttf','.otf','.json','.tres'})
    old_registration=STAGE/'jump-whole-offline-registration-20261102-v2/assembled-selected-candidate02-v1/registration-contract.json';resources.add(old_registration)
    missing=[p for p in read(old_registration)['frozen_inputs'] if not resolve(p).is_file()]
    bound=[ref(p) for p in sorted(resources)]
    fingerprint=hashlib.sha256(json.dumps(bound,sort_keys=True).encode()).hexdigest()
    cfg={'schema':'ufeneo.luna.forward_jump-main-candidate.v1','root_runtime_ready':True,'fighter':FID,'opponent':'zetton',
         'playable':False,'implemented':False,'select_visible':False,'transform_enabled':False,'jump_art_accepted':False,'strict_size_accepted':False,
         'definition':{'id':FID,'display_name':'亚刻奥特曼 · 月亮装甲 · 前跳候选','max_health':1000,'walk_speed':2,'jump_speed':16,'body_radius':18,'moves':{},'command_table':[],'state_frames':states},
         'presentation':{'model':model.as_posix(),'native':True,'anchor_y':280,'manifest_data':{'fighter':FID,'clips':clips}},
         'initial_positions':{'right':{'p1_x':360,'p2_x':900},'left':{'p1_x':920,'p2_x':380}},
         'input_contract':{'length_frames':120,'starts':[40],'inputs':'单tick 相对9（世界x=facing,y=1）InputFrame，陪练中立；非真人键盘','post_sim_mutation':False},
         'bound_resources':bound,'source_fingerprint':fingerprint,'engine':ref(engine),'root_native_review':ref(review_path),'manifest':ref(manifest_path),
         'legacy_provenance':{'unavailable_frozen_inputs':missing,'historical_full_reproduction_claimed':False},
         'write_policy':{'user_settings':False,'last_replay':False,'only_new_reports':True}}
    write(out,cfg);return cfg

def check(contract):
    cfg=read(contract)
    for resource in cfg['bound_resources']:checked(resource)
    assert hashlib.sha256(json.dumps(cfg['bound_resources'],sort_keys=True).encode()).hexdigest()==cfg['source_fingerprint']
    return cfg

def check_trace(data,graphical=False,size=None):
    assert not data['failures'],data['failures'];assert len(data['trace'])==120
    seen=set()
    for i,row in enumerate(data['trace']):
        assert row['movie_frame']==i and row['tick']==i+1
        assert [(f['hp'],f['stamina']) for f in row['pair']]==[(f['hp'],f['stamina']) for f in data['trace'][0]['pair']]
        assert not row['projectiles']
        assert not row['events']
        assert row['simulation_fingerprint']==data['trace'][0]['simulation_fingerprint']
        assert row['original_inputs']==[[data['direction'],1,0],[0,0,0]] if i==40 else row['original_inputs']==[[0,0,0],[0,0,0]]
    for n,row in enumerate(data['trace'][40:78]):
        f=row['pair'][0];assert row['input_relative_n']==n
        state='takeoff' if n<2 else 'air' if n<33 else 'land' if n<37 else 'idle'
        assert f['state']==state
        assert f['state_tick']==(n if n<2 else n-2 if n<33 else n-33 if n<37 else 0)
        assert f['height']==(n*(33-n)//2 if n<33 else 0) and f['vy']==(16-n if n<33 else 0)
        assert f['x']==data['trace'][39]['pair'][0]['x']+data['direction']*4*min(n,33)
        assert f['jump_kind']=='diagonal'
        if n<37:
            key='takeoff' if n<2 else 'flip_forward' if n<33 else 'land';age=n if n<33 else n-33
            phase=[p for p,t in enumerate(CLOCKS[key]) for _ in range(t)][age]
            assert f['animation']['key']==key and f['animation']['index']==phase and f['frame_sprite']==phase
            seen.add((key,phase))
    assert len(seen)==8
    for row in data['trace']:
        assert row.get('training_overlay_visible') is False
        for f in row['pair']:
            x,y,w,h=f['full_alpha_viewport_bounds'];assert x>=0 and y>=0 and x+w<=640 and y+h<=360
    if graphical:
        assert len(data['stills'])==len(CAPTURE_N)+2
        assert {s['movie_frame'] for s in data['stills']}=={0,100,*[40+n for n in CAPTURE_N]}
        for still in data['stills']:
            assert still['dimensions']==size and still['window_dimensions']==size and not still['resized']
            assert sha(still['path'])==still['sha256']
            assert still['request']['tick']==still['captured_tick'] and still['request']['sprite']==still['captured_sprite']
            row=data['trace'][still['movie_frame']]
            assert still['request']['movie_frame']==row['movie_frame'] and still['captured_tick']==row['tick']
            assert still['request']['state_hash']==row['state_hash']==still['captured_state_hash'] and still['captured_sprite']==row['pair'][0]['frame_sprite']
            assert still['simulation_frozen_during_capture'] is True
            assert still['captured_render_rect']==still['request']['render_rect']==row['pair'][0]['animation']['rect']

def run(contract,out,headless):
    cfg=check(contract);out=out.resolve();out.relative_to(REPORT);assert not out.exists();out.mkdir(parents=True)
    env=os.environ.copy();env['XDG_DATA_HOME']=str(out/'user-data');env['XDG_CONFIG_HOME']=str(out/'user-config');env['XDG_CACHE_HOME']=str(out/'user-cache')
    results=[]
    for size in (['1280x720'] if headless else ['1280x720','1920x1080']):
        for direction in ['right','left']:
            original=None
            for replay in [False,True]:
                check(contract);folder=out/(size+'-'+direction+('-replay' if replay else '-original'));folder.mkdir()
                cmd=[cfg['engine']['path'],'--path',str(ROOT),'--audio-driver','Dummy','--rendering-method','gl_compatibility','--windowed','--resolution',size,'--fixed-fps','60','--log-file',str(folder/'engine.log'),'--script','res://tests/review/fighters/ultraman-arc/luna_forward_jump/main_entry.gd']
                if headless:cmd.append('--headless')
                cmd+=['--','--contract='+str(contract),'--out='+str(folder),'--window-size='+size]
                if direction=='left':cmd.append('--left')
                if replay:cmd.append('--tape='+str(original/'actual-input-tape.json'))
                wrapped=[sys.executable,str(ROOT/'tools/godot_lock.py'),'--']+cmd
                started=time.time()
                with (folder/'stdout.log').open('x') as log:result=subprocess.run(wrapped,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
                write(folder/'process.json',{'command':wrapped,'exit_code':result.returncode,'elapsed_seconds':time.time()-started})
                logs={name:(folder/name).read_text() if (folder/name).is_file() else '' for name in ['stdout.log','engine.log']}
                diagnostics=classify_diagnostics(logs)
                write(folder/'engine-log-review.json',diagnostics)
                assert result.returncode==0,str(folder/'stdout.log')
                assert diagnostics['passed'],diagnostics['fatal_diagnostics']
                trace=read(folder/'main-trace.json');check_trace(trace,not headless,[int(n) for n in size.split('x')])
                assert not read(folder/'auxiliary-fresh-sim-replay.json')['errors']
                window=read(folder/'window-setup.json');assert window['simulation_tick_before']==window['simulation_tick_after']==window['trace_count_before_start']==0
                if not headless:assert window['status']=='native_window_stable' and window['stable_frames']>=8 and window['observations'][-1]['elapsed_ms']>=500
                if replay:
                    before=read(original/'main-trace.json')
                    for key in ['state_hash','simulation_fingerprint','events','projectiles','original_inputs','pair']:assert [r[key] for r in before['trace']]==[r[key] for r in trace['trace']],key
                else:original=folder
                results.append({'folder':folder.as_posix(),'headless':headless,'direction':direction,'size':size,'replay':replay,'trace_ticks':120,'graphical_evidence':not headless})
    check(contract)
    write(out/'runner-result.json',{'completed':True,'parts':results,'art_accepted':False,'strict_size_accepted':False,'no_product_install':True,'script_InputFrame_not_human_keyboard':True})

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('freeze');p.add_argument('--manifest',type=Path,default=DEFAULT_MANIFEST);p.add_argument('--root-review',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--engine',type=Path,default=os.environ.get('GODOT_PATH') or shutil.which('godot'))
    p=sub.add_parser('run');p.add_argument('--contract',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--headless',action='store_true')
    p=sub.add_parser('check');p.add_argument('--contract',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='freeze':build(args.manifest.resolve(),args.root_review.resolve(),args.out.resolve(),args.engine.resolve())
    elif args.command=='run':run(args.contract.resolve(),args.out.resolve(),args.headless)
    else:check(args.contract.resolve())

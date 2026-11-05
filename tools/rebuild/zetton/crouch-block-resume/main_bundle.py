"""杰顿低蹲硬直两整帧RAM合同：正式main、原命令、双向独立输入回放；绝不安装。"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import numpy as np
from PIL import Image

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
REVIEW = ROOT/'tests/review/fighters/zetton/crouch_block'
REPORT = ROOT/'reports/zetton-crouch-block-resume'
DEFAULT_MANIFEST = ROOT/'art/fighters/zetton/stage3/crouch-block-registered-20261105-v1/manifest.json'
CASES = ['low','mid','overhead','release_down']
ACTION = 'crouch_blockstun'
LENGTH = 180
KNOWN_VSYNC_WARNING = 'WARNING: Could not set V-Sync mode, as changing V-Sync mode is not supported by the graphics driver.'

def read(path):return json.loads(Path(path).read_text('utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path):return {'path':Path(path).resolve().as_posix(),'sha256':sha(path)}
def resolve(path):
    path=Path(str(path).removeprefix('res://'))
    return (path if path.is_absolute() else ROOT/path).resolve()
def checked(value):
    path=resolve(value['path']);assert path.is_file(),str(path)
    assert sha(path)==value['sha256'],'SHA改变：'+str(path)
    return path
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)
def classify_diagnostics(logs):
    result={'known_environment_warnings':[],'fatal_diagnostics':[],'audio_driver':'Dummy'}
    for source,content in logs.items():
        for number,line in enumerate(content.splitlines(),1):
            if not re.search(r'\b(?:error|warning)\b',line,re.I):continue
            row={'source':source,'line_number':number,'text':line}
            result['known_environment_warnings' if line.strip()==KNOWN_VSYNC_WARNING else 'fatal_diagnostics'].append(row)
    result['passed']=not result['fatal_diagnostics'];return result

def alpha_hurts(image,root):
    alpha=np.asarray(image)[:,:,3]>0;rects=[]
    for y in range(0,image.height,4):
        occupied=[bool(alpha[y:y+4,x:x+4].any()) for x in range(0,image.width,4)];start=None
        for index,on in enumerate(occupied+[False]):
            if on and start is None:start=index
            if not on and start is not None:
                rects.append([start*4-root[0],root[1]-y-4,(index-start)*4,4]);start=None
    return rects

def build(manifest_path,review_path,out,engine):
    out=out.resolve();out.relative_to(REPORT);assert not out.exists()
    manifest=read(manifest_path);review=read(review_path)
    assert review['reviewer']=='root_delegated_by_user' and review['accepted_for_formal_main_candidate'] is True
    assert review['manifest_sha256']==sha(manifest_path)
    assert manifest['fighter']=='zetton' and manifest['action']==ACTION
    assert not manifest['installed'] and not manifest['art_passed'] and not manifest['main_game_accepted']
    canvas=manifest['canvas'];root=manifest['root'];assert len(canvas)==len(root)==2
    assert all(type(v) is int and v>0 for v in canvas+root) and all(v%4==0 for v in canvas)
    clip_path=checked(manifest['clip']);clip=read(clip_path)
    frames_path=checked(manifest['state_frames']);frames=read(frames_path)
    original_path=checked(manifest['reference_state_frames']);original=read(original_path)[ACTION]
    assert original_path==ROOT/'content/fighters/zetton/state_frames.json'
    rows=manifest['frames'];assert len(rows)==2 and [r['phase'] for r in rows]==[0,1] and [r['ticks'] for r in rows]==[4,6]
    assert clip['ticks']==[4,6] and clip['anchors']==[root,root] and clip['anchor_y']==root[1]
    assert clip['source_fighter']=='zetton' and clip['loop'] is False and clip['cell']==canvas[0]==canvas[1]
    atlas_path=resolve(clip['texture']);assert sha(atlas_path)==clip['atlas_sha256']
    resources={manifest_path.resolve(),review_path.resolve(),clip_path,frames_path,original_path,atlas_path,checked(manifest['palette']),checked(manifest['processing_tools']['register']),ROOT/'project.godot',ROOT/'tools/godot_lock.py',engine}
    resources.update(checked(item) for item in manifest['source_reviews'])
    assert manifest['alpha_threshold']==128
    with Image.open(atlas_path) as atlas:
        assert atlas.mode=='RGBA' and atlas.size==(canvas[0]*2,canvas[1])
        for row in rows:
            source_path=checked(row['source']);sample_path=checked(row['sample']);image_path=checked(row['image'])
            resources.update([source_path,sample_path,image_path])
            with Image.open(source_path) as source,Image.open(sample_path) as sample,Image.open(image_path) as image:
                assert image.mode==sample.mode=='RGBA' and image.size==tuple(canvas)
                assert source.size==tuple(row['source_dimensions']) and sample.size==tuple(row['sample_dimensions'])
                assert abs(sample.width/source.width-sample.height/source.height)<0.00001
                assert abs(sample.width/source.width-manifest['common_full_source_scale'])<0.00001
                alpha=np.asarray(image)[:,:,3];assert set(np.unique(alpha))=={0,255}
                assert not any([alpha[0].any(),alpha[-1].any(),alpha[:,0].any(),alpha[:,-1].any()])
                offset=row['whole_source_destination_offset'];assert len(offset)==2 and all(type(n) is int for n in offset)
                assert all(0<=offset[i]<=canvas[i]-sample.size[i] for i in range(2))
                expected=Image.new('RGBA',tuple(canvas));expected.paste(sample,tuple(offset))
                assert expected.tobytes()==image.tobytes(),'只许完整样本整体平移，禁止切片/局部修复'
                assert row['root']==root and row['whole_image_only'] is True
                assert list(image.getbbox())==row['alpha_bbox']
                assert row['hurtboxes']==alpha_hurts(image,root),'新Alpha占格受击框不匹配'
                x,y,w,h=clip['rects'][row['phase']]
                assert (w,h)==tuple(canvas) and atlas.crop((x,y,x+w,y+h)).tobytes()==image.tobytes()
    assert len(frames)==len(original)==10
    for tick,frame in enumerate(frames):
        expected=copy.deepcopy(original[tick]);assert expected['sprite']==(0 if tick<4 else 1)
        expected['hurtboxes']=rows[expected['sprite']]['hurtboxes']
        assert frame==expected,'禁止改变正式状态时序、事件、位移或其它规则'
    # 核真实继承命令表，不能伪造一个仅供测试的招式表。
    commands=read(ROOT/'content/templates/humanoid/command_table.json')
    overrides=read(ROOT/'content/fighters/ultraman/command_table.json')
    commands=[entry for entry in commands if entry['move'] not in {e['move'] for e in overrides}]+overrides
    attack_rules={}
    for action,level,buttons,direction,state in [('crouch_light','low',1,2,'crouch'),('light1','mid',1,5,'idle'),('spin_heavy','overhead',2,4,'idle')]:
        assert any(e['move']==action and e['buttons']==buttons and direction in e['directions'] and state in e['states'] and not e['motion'] for e in commands)
        move=read(ROOT/f'content/fighters/ultraman/moves/{action}.json')
        assert move['level']==level and move['blockstun']==12 and not move['unblockable']
        assert not move['launch'] and not move['knockdown']
        attack_rules[action]={k:move.get(k,0) for k in ['damage','chip_damage','blockstun','hitstun','stamina_cost','level','feedback']}
    # 冻结运行依赖和实际处理后端；保留可见窗口、HUD、音频Dummy的完整加载链。
    for name in ['app','core','input','content','presentation','ui','third_party/shoto','tests/review','tools/rebuild/shared','tools/rebuild/zetton/crouch-block-resume']:
        resources.update(p for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix in {'.gd','.json','.tres','.tscn','.gdshader','.py'})
    for name in ['assets/fighters/ultraman','assets/fighters/zetton','assets/ui','assets/fonts','assets/stages','assets/backgrounds','assets/audio','addons/controller_icons']:
        resources.update(p for p in (ROOT/name).rglob('*') if p.is_file() and not any(part in {'.godot','.git','__pycache__'} for part in p.relative_to(ROOT/name).parts) and p.suffix not in {'.pyc','.pyo'} and p.name!='.DS_Store')
    sys.path.insert(0,str(ROOT/'tools/rebuild/shared'))
    try:
        import forge_backend
        with forge_backend.palette_mode('rgb'):backend=forge_backend.backend_info()
    finally:sys.path.pop(0)
    assert {k:v for k,v in backend.items() if k not in ['scripts','python']}==manifest['backend']
    for name,digest in backend['files'].items():resources.add(checked({'path':str(Path(backend['scripts'])/name),'sha256':digest}))
    clip['texture']=atlas_path.as_posix()
    bound=[ref(p) for p in sorted(resources)]
    cfg={'schema':'ufeneo.zetton.crouch-block-main-candidate.v1','root_runtime_ready':True,'fighter':'zetton','attacker':'ultraman','action':ACTION,
         'state_frames':frames,'clip':clip,'root':root,'canvas':canvas,'animation_ticks':[4,6],'attack_rules':attack_rules,
         'initial_gaps':manifest.get('initial_gaps',{'low':65,'mid':65,'overhead':95,'release_down':65}),
         'input_contract':{'length_frames':LENGTH,'single_attack_frame':20,'release_down':'仅首次真实block后的下一tick起松下，继续U；独立回放不重采样自适应输入','post_sim_mutation':False},
         'timing':'10行源表4/6按正式blockstun duration映射，含原hitstop；静帧不证明实速动作通过',
         'bound_resources':bound,'source_fingerprint':hashlib.sha256(json.dumps(bound,sort_keys=True).encode()).hexdigest(),
         'engine':ref(engine),'root_native_review':ref(review_path),'manifest':ref(manifest_path),
         'write_policy':{'user_settings':False,'last_replay':False,'only_new_reports':True},'art_accepted':False,'real_speed_art_accepted':False,'installed':False}
    write(out,cfg);return cfg

def check(contract):
    cfg=read(contract)
    for resource in cfg['bound_resources']:checked(resource)
    assert hashlib.sha256(json.dumps(cfg['bound_resources'],sort_keys=True).encode()).hexdigest()==cfg['source_fingerprint']
    return cfg

def move_for(kind):return 'spin_heavy' if kind=='overhead' else 'light1' if kind=='mid' else 'crouch_light'
def capture_keys(kind):
    return {'before-input-crouch-guard','returned-guard'}|({'overhead-hit-first','overhead-hit-last'} if kind=='overhead' else {f'stun-phase-{phase}-{edge}' for phase in range(2) for edge in ['first','last']})

def check_trace(data,cfg,graphical=False,size=None):
    assert not data['failures'],data['failures'];assert len(data['trace'])==LENGTH
    kind=data['kind'];direction=data['direction'];assert kind in CASES and direction in [-1,1]
    trace=data['trace'];contacts=[];phases=set();ages=set();moves=set();first_block=None
    rule=cfg['attack_rules'][move_for(kind)]
    for i,row in enumerate(trace):
        assert row['movie_frame']==i and row['tick']==i+1 and not row['projectiles']
        attack=([0,-1,1 if i==20 else 0] if kind in ['low','release_down'] else [0,0,1 if i==20 else 0] if kind=='mid' else [-direction if i==20 else 0,0,2 if i==20 else 0])
        assert row['original_inputs']==[attack,[0,0 if kind=='release_down' and first_block is not None else -1,8]]
        for event in row['events']:
            if event.get('kind') in ['hit','block']:
                contacts.append(event)
                if event['kind']=='block' and first_block is None:first_block=i
        own,target=row['pair']
        assert own['id']=='ultraman' and target['id']=='zetton' and own['hp']==1000
        if own['move_id']:moves.add(own['move_id'])
        assert target['height']==0 and target['state'] not in ['launch','down','wake']
        for fighter in row['pair']:
            assert fighter['animation']['index']==fighter['frame_sprite']
            assert fighter['render_texture']==fighter['animation']['texture'] and fighter['render_region']==fighter['animation']['rect'] and fighter['render_region_enabled']
            x,y,w,h=fighter['full_alpha_viewport_bounds'];assert x>=0 and y>=0 and x+w<=640 and y+h<=360
        if target['state']==ACTION:
            assert kind!='overhead' and target['duration']==rule['blockstun']
            age=int(target['state_tick']);phase=cfg['state_frames'][min(age*10//int(target['duration']),9)]['sprite']
            assert target['frame_sprite']==phase and target['animation']['key']==ACTION and target['animation']['texture']==cfg['clip']['texture']
            phases.add(phase);ages.add(age)
        else:assert target['animation']['texture']!=cfg['clip']['texture']
        assert row['training_overlay_visible'] is True
    assert moves=={move_for(kind)} and len(contacts)==1
    assert contacts[0]['kind']==('hit' if kind=='overhead' else 'block') and contacts[0]['player']==0 and contacts[0]['move']==move_for(kind)
    if kind!='overhead':assert phases=={0,1} and ages==set(range(rule['blockstun']))
    assert trace[0]['pair'][1]['hp']-trace[-1]['pair'][1]['hp']==(rule['damage'] if kind=='overhead' else rule['chip_damage'])
    assert trace[19]['pair'][1]['state']=='crouch_guard'
    assert trace[-1]['pair'][1]['state']==('guard' if kind=='release_down' else 'crouch_guard')
    assert {s['key'] for s in data['stills']}==capture_keys(kind) and len(data['stills'])==len(capture_keys(kind))
    if graphical:
        for still in data['stills']:
            assert still['dimensions']==still['window_dimensions']==size and not still['resized'] and still['simulation_frozen_during_capture']
            assert sha(still['path'])==still['sha256']
            request=still['request'];row=trace[still['movie_frame']]
            assert request['pair']==row['pair'] and request['state_hash']==row['state_hash']
            assert request['tick']==still['captured_tick']==row['tick'] and request['sprite']==still['captured_sprite']==row['pair'][1]['frame_sprite']
            assert request['final_safe_rect']==request['hud_safe_rect'] and request['hud_visible'] and request['training_overlay_visible']
            sx,sy,sw,sh=request['hud_safe_rect'];assert len(request['final_render_bounds'])>=2
            for x,y,w,h in request['final_render_bounds']:assert x>=sx-.1 and y>=sy-.1 and x+w<=sx+sw+.1 and y+h<=sy+sh+.1
    return {'duration':rule['blockstun'] if kind!='overhead' else rule['hitstun'],
            'observed_stun_tick_count':sum(r['pair'][1]['state']==ACTION for r in trace),
            'phase_observed_ticks':{str(p):sum(r['pair'][1]['state']==ACTION and r['pair'][1]['frame_sprite']==p for r in trace) for p in [0,1]},
            'includes_hitstop':True,'wall_clock_art_timing_claimed':False}

def environment(out):
    env=os.environ.copy()
    for key,folder in [('XDG_DATA_HOME','user-data'),('XDG_CONFIG_HOME','user-config'),('XDG_CACHE_HOME','user-cache')]:env[key]=str(out/folder)
    return env

def execute(cfg,folder,command,env):
    wrapped=[sys.executable,str(ROOT/'tools/godot_lock.py'),'--']+command;started=time.time()
    with (folder/'stdout.log').open('x') as log:result=subprocess.run(wrapped,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
    write(folder/'process.json',{'command':wrapped,'exit_code':result.returncode,'elapsed_seconds':time.time()-started})
    diagnostics=classify_diagnostics({name:(folder/name).read_text() if (folder/name).is_file() else '' for name in ['stdout.log','engine.log']})
    write(folder/'engine-log-review.json',diagnostics)
    assert result.returncode==0,str(folder/'stdout.log')
    assert diagnostics['passed'],diagnostics['fatal_diagnostics']

def run(contract,out,headless,kinds=None,directions=None,sizes=None):
    cfg=check(contract);out=out.resolve();out.relative_to(REPORT);assert not out.exists();out.mkdir(parents=True)
    env=environment(out);results=[]
    for size in (sizes or (['1280x720'] if headless else ['1280x720','1920x1080'])):
        assert size in ['1280x720','1920x1080']
        for direction in (directions or ['right','left']):
            assert direction in ['right','left']
            for kind in (kinds or CASES):
                assert kind in CASES;original=None
                for replay in [False,True]:
                    check(contract);folder=out/(size+'-'+direction+'-'+kind+('-replay' if replay else '-original'));folder.mkdir()
                    cmd=[cfg['engine']['path'],'--path',str(ROOT),'--audio-driver','Dummy','--rendering-method','gl_compatibility','--windowed','--resolution',size,'--fixed-fps','60','--log-file',str(folder/'engine.log'),'--script','res://tests/review/fighters/zetton/crouch_block/main_entry.gd']
                    if headless:cmd.append('--headless')
                    cmd+=['--','--contract='+str(contract),'--out='+str(folder),'--window-size='+size,'--kind='+kind]
                    if direction=='left':cmd.append('--left')
                    if replay:cmd.append('--tape='+str(original/'actual-input-tape.json'))
                    execute(cfg,folder,cmd,env)
                    data=read(folder/'main-trace.json');timing=check_trace(data,cfg,not headless,[int(n) for n in size.split('x')])
                    assert not read(folder/'auxiliary-fresh-sim-replay.json')['errors']
                    window=read(folder/'window-setup.json');assert window['simulation_tick_before']==window['simulation_tick_after']==window['trace_count_before_start']==0
                    if not headless:assert window['status']=='native_window_stable' and window['stable_frames']>=8 and window['observations'][-1]['elapsed_ms']>=500
                    if replay:
                        before=read(original/'main-trace.json')
                        for key in ['state_hash','events','projectiles','original_inputs','pair','hitstop']:assert [r[key] for r in before['trace']]==[r[key] for r in data['trace']],key
                    else:original=folder
                    results.append({'folder':folder.as_posix(),'headless':headless,'direction':direction,'kind':kind,'size':size,'replay':replay,'trace_ticks':LENGTH,'graphical_evidence':not headless,'timing':timing})
    check(contract);write(out/'runner-result.json',{'completed':True,'parts':results,'art_accepted':False,'real_speed_art_accepted':False,'no_product_install':True,'script_InputFrame_not_human_keyboard':True})

def logic(contract,out):
    cfg=check(contract);out=out.resolve();out.relative_to(REPORT);assert not out.exists();out.mkdir(parents=True)
    command=[cfg['engine']['path'],'--headless','--path',str(ROOT),'--audio-driver','Dummy','--log-file',str(out/'engine.log'),'--script','res://tests/review/fighters/zetton/crouch_block/logic_check.gd','--','--contract='+str(contract),'--out='+str(out/'logic-result.json')]
    execute(cfg,out,command,environment(out))
    result=read(out/'logic-result.json');assert not result['errors'] and len(result['cases'])==8
    check(contract)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('freeze');p.add_argument('--manifest',type=Path,default=DEFAULT_MANIFEST);p.add_argument('--root-review',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--engine',type=Path,default=os.environ.get('GODOT_PATH') or shutil.which('godot'))
    p=sub.add_parser('run');p.add_argument('--contract',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--headless',action='store_true');p.add_argument('--kind',action='append',choices=CASES);p.add_argument('--direction',action='append',choices=['right','left']);p.add_argument('--size',action='append',choices=['1280x720','1920x1080'])
    p=sub.add_parser('logic');p.add_argument('--contract',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p=sub.add_parser('check');p.add_argument('--contract',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='freeze':
        assert args.engine is not None,'需要--engine或GODOT_PATH'
        build(args.manifest.resolve(),args.root_review.resolve(),args.out.resolve(),args.engine.resolve())
    elif args.command=='run':run(args.contract.resolve(),args.out.resolve(),args.headless,args.kind,args.direction,args.size)
    elif args.command=='logic':logic(args.contract.resolve(),args.out.resolve())
    else:check(args.contract.resolve())

"""月亮蹲两拳新规则合同：保留原65/65伤及确认取消，不保证第二拳连中。"""
import argparse,copy,hashlib,importlib.util,json,os,sys,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;REPORT=ROOT/'reports/luna-crouch-chain-resume'
spec=importlib.util.spec_from_file_location('first_bundle',HERE.parent/'luna-crouch-light-resume/main_bundle.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
read=base.read;sha=base.sha;write=base.write;check=base.check
MANIFEST=ROOT/'art/fighters/ultraman-arc__luna/stage2/crouch-chain-registered-20261105-v1/manifest.json'

def freeze(out,engine):
 out=out.resolve();out.relative_to(REPORT);assert not out.exists()
 manifest=read(MANIFEST);first=base.checked(manifest['first_manifest'])
 base.REPORT=REPORT
 cfg=base.build(first,first.parent/'registration-review.json',out.with_name(out.stem+'-first-base.json'),engine)
 group=manifest['actions']['crouch_light2'];move=read(base.checked(group['move']));original=read(base.checked(group['rule_reference']));expected=copy.deepcopy(original)
 expected['production_source']=move['production_source'];expected['display_name']=move['display_name']
 timeline=[phase for phase,t in enumerate([3,7,8]) for _ in range(t)]
 hurts=base.state_frames(group['frames'])
 for i,phase in enumerate(timeline):
  expected['frames'][i]['sprite']=phase;expected['frames'][i]['hurtboxes']=hurts[i]['hurtboxes'];expected['frames'][i]['hitboxes']=[group['fist_boxes']['1']] if phase==1 else []
 assert move==expected,'只准整图sprite/hurt与小拳Alpha框变化，取消/规则不改'
 assert (move['startup'],move['active'],move['recovery'])==(3,7,8)
 clip=read(base.checked(group['clip']));clip['texture']=str(base.resolve(clip['texture']))
 assert clip['ticks']==[3,7,8] and sha(Path(clip['texture']))==clip['atlas_sha256']
 from PIL import Image
 import numpy as np
 with Image.open(clip['texture']) as atlas:
  for row in group['frames']:
   with Image.open(base.resolve(row['image'])) as im,Image.open(base.checked(row['whole_source_sample'])) as sample:
    expected_im=Image.new('RGBA',(320,320));expected_im.paste(sample,tuple(row['whole_source_destination_offset']))
    assert im.tobytes()==expected_im.tobytes()==atlas.crop((320*row['phase'],0,320*(row['phase']+1),320)).tobytes()
    assert set(np.unique(np.asarray(im)[:,:,3]))=={0,255}
 cfg['schema']='ufeneo.luna.crouch_chain-main-candidate.v1';cfg['definition']['moves']['crouch_light2']=move
 cfg['definition']['display_name']='蹲左/右拳候选'
 commands=read(ROOT/'content/fighters/ultraman-arc/command_table.json');command=next(r for r in commands if r['move']=='crouch_light2')
 assert command['states']==['crouch_light'] and command['directions']==[0] and command['buttons']==1
 cfg['definition']['command_table'].append(command)
 cfg['presentation']['manifest_data']['clips']['crouch_light2']=clip;cfg['animation_ticks']['crouch_light2']=[3,7,8]
 cfg['second_fist_boxes']=group['fist_boxes'];cfg['manifest']=base.ref(MANIFEST)
 cfg['input_contract']={'length_frames':180,'light_press_frames':[20,27],'direction':[0,-1],'post_sim_mutation':False,'scope':'两个独立按沿，命中可取消；格挡/落空不confirmed，早按缓存耗尽。后续独立语义矩阵核晚按招末buffer后起。'}
 cfg['receiver_policy']='正式杰顿图/状态；含最新恢复规则，不混入新RAM blockstun图。旧硬直高姿保留。'
 cfg['limitations']=manifest['limitations'];cfg['first_base_contract']=base.ref(out.with_name(out.stem+'-first-base.json'))
 resources={Path(r['path']) for r in cfg['bound_resources']};resources.add(MANIFEST)
 for key in ['geometry','plan','processing_tool']:resources.add(base.checked(manifest[key]))
 for key in ['clip','move','rule_reference']:resources.add(base.checked(group[key]))
 resources.add(Path(clip['texture']))
 for row in group['frames']:
  for key in ['source','image']:resources.add(base.checked({'path':row[key],'sha256':row[key+'_sha256']}))
  resources.add(base.checked(row['whole_source_sample']))
 for tree in [HERE,ROOT/'tests/review/fighters/ultraman-arc/luna_crouch_chain']:
  resources.update(p for p in tree.rglob('*') if p.is_file() and p.suffix in ['.py','.gd','.json'] and not p.name.startswith('test_'))
 cfg['bound_resources']=[base.ref(p) for p in sorted(resources)];cfg['source_fingerprint']=hashlib.sha256(json.dumps(cfg['bound_resources'],sort_keys=True).encode()).hexdigest()
 write(out,cfg);print(out,sha(out))

def check_trace(data,graphical=False,size=None,idle_ticks=None):
 assert not data['failures'],data['failures'];trace=data['trace'];assert len(trace)==180
 kind=data['kind'];moves=set();contacts=[]
 for i,row in enumerate(trace):
  assert row['tick']==i+1 and row['movie_frame']==i
  assert row['original_inputs']==[[0,-1,1 if i in [20,27] else 0],[0,-1 if kind=='block' else 0,8 if kind in ['block','stand_guard'] else 0]]
  assert not row['projectiles'] and row['training_overlay_visible']
  own=row['pair'][0]
  if own['move_id']:
   action=own['move_id'];moves.add(action);phases=[p for p,n in enumerate(data['animation_ticks'][action]) for _ in range(int(n))]
   assert own['frame_sprite']==own['animation']['index']==phases[int(own['move_tick'])]
  assert own['x']==trace[0]['pair'][0]['x'] and own['height']==0
  contacts.extend(e for e in row['events'] if e.get('kind') in ['hit','block'] and e.get('player')==0)
  for f in row['pair']:
   x,y,w,h=f['full_alpha_viewport_bounds'];assert x>=0 and y>=0 and x+w<=640 and y+h<=360
 assert moves==({'crouch_light','crouch_light2'} if kind in ['hit','stand_guard'] else {'crouch_light'})
 assert trace[-1]['pair'][0]['state']=='crouch'
 if graphical:
  expected={'before-input-crouch','returned-crouch'}
  for row in trace:
   f=row['pair'][0]
   if f['move_id'] and f['move_tick'] in [1,2,3,5,6,9,10,17]:expected.add(f"{f['move_id']}-tick-{int(f['move_tick']):02d}-phase-{int(f['frame_sprite']):02d}")
  assert {s['key'] for s in data['stills']}==expected and len(data['stills'])==len(expected)
  for still in data['stills']:
   assert still['dimensions']==still['window_dimensions']==size and not still['resized'] and sha(Path(still['path']))==still['sha256']
   req=still['request'];row=trace[still['movie_frame']]
   assert req['tick']==still['captured_tick']==row['tick'] and req['state_hash']==row['state_hash'] and still['captured_sprite']==row['pair'][0]['frame_sprite']
   assert req['pair']==row['pair'] and req['hud_visible'] and req['training_overlay_visible'] and req['final_safe_rect']==req['hud_safe_rect']
   sx,sy,sw,sh=req['hud_safe_rect']
   for x,y,w,h in req['final_render_bounds']:assert x>=sx-.1 and y>=sy-.1 and x+w<=sx+sw+.1 and y+h<=sy+sh+.1
 base.check_grounded_receiver(trace,kind)

LENGTH=180
classify_diagnostics=base.classify_diagnostics
def run(contract,out,headless):
    cfg=check(contract);out=out.resolve();out.relative_to(REPORT);assert not out.exists();out.mkdir(parents=True)
    env=os.environ.copy();env['XDG_DATA_HOME']=str(out/'user-data');env['XDG_CONFIG_HOME']=str(out/'user-config');env['XDG_CACHE_HOME']=str(out/'user-cache')
    results=[]
    for size in (['1280x720'] if headless else ['1280x720','1920x1080']):
        for direction in ['right','left']:
            for kind in ['hit','stand_guard','block','whiff']:
                original=None
                for replay in [False,True]:
                    check(contract);folder=out/(size+'-'+direction+'-'+kind+('-replay' if replay else '-original'));folder.mkdir()
                    cmd=[cfg['engine']['path'],'--path',str(ROOT),'--audio-driver','Dummy','--rendering-method','gl_compatibility','--windowed','--resolution',size,'--fixed-fps','60','--log-file',str(folder/'engine.log'),'--script','res://tests/review/fighters/ultraman-arc/luna_crouch_chain/main_entry.gd']
                    if headless:cmd.append('--headless')
                    cmd+=['--','--contract='+str(contract),'--out='+str(folder),'--window-size='+size,'--kind='+kind]
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
                    trace=read(folder/'main-trace.json');check_trace(trace,not headless,[int(n) for n in size.split('x')],cfg['animation_ticks']['idle'])
                    assert not read(folder/'auxiliary-fresh-sim-replay.json')['errors']
                    window=read(folder/'window-setup.json');assert window['simulation_tick_before']==window['simulation_tick_after']==window['trace_count_before_start']==0
                    if not headless:assert window['status']=='native_window_stable' and window['stable_frames']>=8 and window['observations'][-1]['elapsed_ms']>=500
                    if replay:
                        before=read(original/'main-trace.json')
                        for key in ['state_hash','events','projectiles','original_inputs','pair']:assert [r[key] for r in before['trace']]==[r[key] for r in trace['trace']],key
                    else:original=folder
                    results.append({'folder':folder.as_posix(),'headless':headless,'direction':direction,'kind':kind,'size':size,'replay':replay,'trace_ticks':LENGTH,'graphical_evidence':not headless})
    check(contract)
    write(out/'runner-result.json',{'completed':True,'parts':results,'art_accepted':False,'strict_size_accepted':False,'no_product_install':True,'script_InputFrame_not_human_keyboard':True})


if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','run','check']);p.add_argument('--contract',type=Path);p.add_argument('--out',type=Path);p.add_argument('--engine',type=Path);p.add_argument('--headless',action='store_true');a=p.parse_args()
 if a.command=='freeze':freeze(a.out,a.engine.resolve())
 elif a.command=='check':check(a.contract)
 else:run(a.contract.resolve(),a.out,a.headless)

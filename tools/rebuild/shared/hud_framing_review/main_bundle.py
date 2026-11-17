"""正式main的HUD避让回归；只驱动真实InputFrame，tick0夹具后不写模拟。"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time,importlib.util,re
ROOT=Path(__file__).resolve().parents[4]
REPORT=ROOT/'reports/hud-framing'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2)
def freeze(out,engine):
 paths=[]
 for base in ['app','core','input','content','presentation','ui','tests/review/app/hud_framing','tools/rebuild/shared/hud_framing_review','assets']:
  paths += [p for p in (ROOT/base).rglob('*') if p.is_file() and p.suffix in {'.gd','.json','.tscn','.tres','.gdshader','.png','.wav','.ogg','.ttf','.otf','.py'}]
 bound=[{'path':str(p),'sha256':sha(p)} for p in sorted(paths)]
 for case in ['far','near','held_rock']:
  inputs=[[[0,0,0],[0,0,0]] for _ in range(190)]
  if case=='far':
   inputs[25][0]=[0,1,0];inputs[65][1]=[0,1,0];inputs[110][0]=[1,1,0];inputs[110][1]=[-1,1,0]
   captures=[0,25,32,39,48,65,71,76,110,118,125,145,175]
  elif case=='near':
   inputs[25][0]=[0,-1,2]
   inputs[100][0]=[1,0,0];inputs[101][0]=[0,-1,0];inputs[102][0]=[1,-1,2]
   captures=[0,25,31,37,45,54,65,102,106,110,114,120,130,175]
  else:
   inputs[25][0]=[0,0,32]
   captures=[0,25,30,35,40,45,46,47,48,50,53,55,60,70,85,100,150]
  write(out/(case+'.json'),{'schema':'ufeneo.hud_framing.v1','case':case,'training':case=='far','fighter':'red_king' if case=='held_rock' else 'ultraman-arc','opponent':'gomora','initial_energy':[2000,3000] if case=='held_rock' else [3000,3000],'initial_hp':[1000,500] if case=='far' else [1000,1000],'gap':540 if case!='near' else 70,'length_frames':190,'inputs':inputs,'capture_frames':captures,'engine':str(engine),'engine_sha256':sha(engine),'bound_resources':bound})
def diagnostics(logs):
 source=ROOT/'tools/rebuild/ultraman-arc/luna-forward-jump-resume/main_bundle.py'
 spec=importlib.util.spec_from_file_location('prior_bundle',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 d=m.classify_diagnostics(logs)
 for source,contents in logs.items():
  for n,line in enumerate(contents.splitlines(),1):
   if re.search(r'\b(error|warning)\b',line,re.I) and line.strip()!=m.KNOWN_VSYNC_WARNING and not any(x['source']==source and x['line_number']==n for x in d['fatal_diagnostics']):d['fatal_diagnostics'].append({'source':source,'line_number':n,'text':line})
 d['passed']=not d['fatal_diagnostics'];return d
def check_contract(p):
 c=read(p)
 for r in c['bound_resources']:assert sha(r['path'])==r['sha256'],r['path']
 assert sha(c['engine'])==c['engine_sha256']
 return c
def run(contract,out,headless):
 c=check_contract(contract);out=out.resolve();out.relative_to(REPORT);out.mkdir(parents=True,exist_ok=False)
 env=os.environ.copy()
 for k,v in [('XDG_DATA_HOME','user-data'),('XDG_CONFIG_HOME','user-config'),('XDG_CACHE_HOME','user-cache')]:env[k]=str(out/v);(out/v).mkdir()
 results=[]
 for size in (['1280x720'] if headless else ['1280x720','1920x1080']):
  for direction in ['right','left']:
   original=None
   for replay in [False,True] if headless else [False]:
    folder=out/(size+'-'+direction+('-replay' if replay else '-original'));folder.mkdir()
    cmd=[sys.executable,str(ROOT/'tools/godot_lock.py'),'--',c['engine'],'--path',str(ROOT),'--audio-driver','Dummy','--rendering-method','gl_compatibility','--windowed','--resolution',size,'--fixed-fps','60','--log-file',str(folder/'engine.log'),'--script','res://tests/review/app/hud_framing/main_entry.gd']
    if headless:cmd+=['--headless']
    cmd+=['--','--contract='+str(contract),'--out='+str(folder),'--window-size='+size]
    if direction=='left':cmd+=['--left']
    if replay:cmd+=['--tape='+str(original/'actual-input-tape.json')]
    start=time.time()
    with (folder/'stdout.log').open('x') as log:r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
    write(folder/'process.json',{'command':cmd,'exit_code':r.returncode,'seconds':time.time()-start})
    d=diagnostics({n:(folder/n).read_text() if (folder/n).exists() else '' for n in ['stdout.log','engine.log']});write(folder/'engine-log-review.json',d)
    assert r.returncode==0 and d['passed'],str(folder/'stdout.log')
    data=read(folder/'main-trace.json');assert not data['failures'],data['failures'][:5]
    assert len(data['trace'])==c['length_frames']
    if c['case']=='far':
     assert all(max(r['pair'][i]['height'] for r in data['trace'])>40 for i in range(2))
     assert any(h['visible'] for r in data['trace'] for h in r['hud_layout']['transform_hints']), '真实变身提示未显示'
    if c['case']=='near':
     assert any(r['pair'][0]['move']=='motion_623' for r in data['trace'])
     assert any(r['pair'][1]['state'] in ['knockdown','down','wake'] for r in data['trace']), sorted({r['pair'][1]['state'] for r in data['trace']})
    if c['case']=='held_rock':
     assert any(r['entities'] for r in data['trace']), '真实独立持握实体未覆盖'
     assert any(r['pair'][0]['move']=='special2' for r in data['trace']), '未触发二级真实持石'
     assert not any(r['pair'][0]['move']=='special3' for r in data['trace']), '三级立绘遮挡案例不能替代二级持物证明'
    assert all(row['hud_visible'] and row['training_overlay_visible']==c['training'] for row in data['trace'])
    assert len(data['stills'])==len(c['capture_frames'])
    if not headless:
     for s in data['stills']:
      assert s['dimensions']==s['window_dimensions']==list(map(int,size.split('x')))
      row=data['trace'][s['movie_frame']]
      assert s['request']['tick']==s['captured_tick']==row['tick']
      assert s['request']['state_hash']==s['captured_state_hash']==row['state_hash']
      assert s['request']['sprite']==s['captured_sprite']==row['pair'][0]['frame_sprite']
      assert s['captured_render_rect']==s['request']['render_rect']
      assert sha(s['path'])==s['sha256']
    if replay:assert [x['state_hash'] for x in read(original/'main-trace.json')['trace']]==[x['state_hash'] for x in data['trace']]
    else:original=folder
    results.append({'folder':str(folder),'graphical':not headless,'replay':replay,'states':[sorted({x['pair'][i]['state'] for x in data['trace']}) for i in range(2)]})
 check_contract(contract);write(out/'runner-result.json',{'completed':True,'parts':results})
if __name__=='__main__':
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
 q=sub.add_parser('freeze');q.add_argument('--out',type=Path,required=True);q.add_argument('--engine',type=Path,required=True)
 q=sub.add_parser('run');q.add_argument('--out',type=Path,required=True);q.add_argument('--contract',type=Path,required=True);q.add_argument('--headless',action='store_true')
 a=p.parse_args()
 if a.cmd=='freeze':freeze(a.out.resolve(),a.engine.resolve())
 else:run(a.contract.resolve(),a.out.resolve(),a.headless)

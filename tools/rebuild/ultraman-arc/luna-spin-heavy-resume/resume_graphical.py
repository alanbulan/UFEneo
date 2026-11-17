"""原合同图形续跑：保留17组成功与1组窗口门失败，只跑未完成七组，不改门限。"""
import argparse,os,subprocess,sys,time
from pathlib import Path
import main_bundle as b

def main():
 p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 contract=a.contract.resolve();base=a.base.resolve();out=a.out.resolve();base.relative_to(b.REPORT);out.relative_to(b.REPORT)
 assert not out.exists();cfg=b.check(contract)
 # 失败只在窗口启动，模拟尚未开始，不能把不确定已运行的输入盲目重复。
 failed=base/'1920x1080-right-whiff-replay';process=b.read(failed/'process.json');window=b.read(failed/'window-setup.json')
 assert process['exit_code']!=0 and not (failed/'main-trace.json').exists()
 assert window['simulation_tick_before']==window['simulation_tick_after']==0
 previous=[]
 for folder in sorted(base.iterdir()):
  if not folder.is_dir() or not (folder/'process.json').exists() or folder==failed:continue
  assert b.read(folder/'process.json')['exit_code']==0
  size=[int(x) for x in folder.name.split('-')[0].split('x')]
  trace=b.read(folder/'main-trace.json');b.check_trace(trace,True,size,cfg['animation_ticks']['idle'])
  previous.append({'folder':str(folder),'trace':b.ref(folder/'main-trace.json')})
 assert len(previous)==17
 out.mkdir(parents=True)
 b.write(out/'resume-plan.json',{'script':b.ref(Path(__file__).resolve()),'contract':b.ref(contract),'previous_valid_groups':previous,'preserved_failure':b.ref(failed/'process.json'),'window_failure':b.ref(failed/'window-setup.json'),'reason':'4次观察尺寸均1920x1080但稳定次数不足8即超时，模拟未开始；原门限不变，新目录续跑','new_groups':7})
 env=os.environ.copy()
 for key,dirname in [('XDG_DATA_HOME','user-data'),('XDG_CONFIG_HOME','user-config'),('XDG_CACHE_HOME','user-cache')]:env[key]=str(out/dirname)
 jobs=[('right','whiff',True)]+[('left',kind,replay) for kind in ['hit','block','whiff'] for replay in [False,True]]
 results=[]
 for direction,kind,replay in jobs:
  b.check(contract);folder=out/('1920x1080-'+direction+'-'+kind+('-replay' if replay else '-original'));folder.mkdir()
  original=(base/'1920x1080-right-whiff-original') if direction=='right' else out/('1920x1080-left-'+kind+'-original')
  cmd=[cfg['engine']['path'],'--path',str(b.ROOT),'--audio-driver','Dummy','--rendering-method','gl_compatibility','--windowed','--resolution','1920x1080','--fixed-fps','60','--log-file',str(folder/'engine.log'),'--script','res://tests/review/fighters/ultraman-arc/luna_spin_heavy/main_entry.gd','--','--contract='+str(contract),'--out='+str(folder),'--window-size=1920x1080','--kind='+kind]
  if direction=='left':cmd.append('--left')
  if replay:cmd.append('--tape='+str(original/'actual-input-tape.json'))
  wrapped=[sys.executable,str(b.ROOT/'tools/godot_lock.py'),'--']+cmd;started=time.time()
  with (folder/'stdout.log').open('x') as log:r=subprocess.run(wrapped,cwd=b.ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
  b.write(folder/'process.json',{'command':wrapped,'exit_code':r.returncode,'elapsed_seconds':time.time()-started})
  diagnostics=b.classify_diagnostics({n:(folder/n).read_text() if (folder/n).exists() else '' for n in ['stdout.log','engine.log']});b.write(folder/'engine-log-review.json',diagnostics)
  assert r.returncode==0,str(folder/'stdout.log');assert diagnostics['passed'],diagnostics
  trace=b.read(folder/'main-trace.json');b.check_trace(trace,True,[1920,1080],cfg['animation_ticks']['idle'])
  assert not b.read(folder/'auxiliary-fresh-sim-replay.json')['errors']
  window=b.read(folder/'window-setup.json');assert window['simulation_tick_before']==window['simulation_tick_after']==window['trace_count_before_start']==0
  assert window['status']=='native_window_stable' and window['stable_frames']>=8 and window['observations'][-1]['elapsed_ms']>=500
  if replay:
   before=b.read(original/'main-trace.json')
   for key in ['state_hash','events','projectiles','original_inputs','pair']:assert [x[key] for x in before['trace']]==[x[key] for x in trace['trace']],key
  results.append({'folder':str(folder),'direction':direction,'kind':kind,'replay':replay,'size':'1920x1080','headless':False,'trace_ticks':180,'graphical_evidence':True})
 b.check(contract);b.write(out/'runner-result.json',{'completed':True,'previous_valid_groups':17,'parts':results,'total_valid_groups':24,'preserved_failed_attempts':1,'art_accepted':False,'strict_size_accepted':False,'no_product_install':True,'script_InputFrame_not_human_keyboard':True})
if __name__=='__main__':main()

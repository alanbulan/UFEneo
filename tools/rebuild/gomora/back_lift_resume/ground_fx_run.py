"""持项目Godot锁运行地面FX别名候选；不安装正式资产，不读取或恢复用户存档。"""
from pathlib import Path
import argparse, hashlib, json, os, re, subprocess, sys
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from runtime.environment import godot_path, isolated_test_environment

def save(path,data):
    with path.open('x',encoding='utf-8') as stream:json.dump(data,stream,ensure_ascii=False,indent=2)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['main','replay','search','blocked-replay','input-replay'])
    parser.add_argument('--contract',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--trace',type=Path)
    parser.add_argument('--search-gaps',default='56,64,68,72,80')
    parser.add_argument('--search-delays',default='10,12,13,14,16')
    parser.add_argument('--case',default='hit_p')
    parser.add_argument('--owner',type=int,choices=[0,1],default=0)
    parser.add_argument('--gap',type=int,default=68)
    parser.add_argument('--jump-delay',type=int,default=13)
    parser.add_argument('--size',choices=['1280x720','1920x1080'],default='1280x720')
    args=parser.parse_args()
    assert (ROOT/'art/shared/locks/godot.lock').is_file(),'必须从tools/godot_lock.py调用'
    out=args.out.resolve();out.relative_to(ROOT/'reports');assert not out.exists();out.mkdir(parents=True)
    contract=args.contract.resolve();cfg=json.loads(contract.read_text('utf-8'))
    assert cfg['schema']=='ufeneo.gomora.back-lift-main-candidate.v1' and cfg['installed'] is False
    paths={contract,*HERE.glob('runtime/*.gd'),Path(__file__)}
    for folder in ['core','input','app','presentation','content']:
        paths.update(p for p in (ROOT/folder).rglob('*') if p.suffix in {'.gd','.json','.tres','.tscn','.gdshader'})
    for item in cfg['bound_resources']:
        p=ROOT/item['path'][6:] if item['path'].startswith('res://') else Path(item['path'])
        assert sha(p)==item['sha256'];paths.add(p)
    before={str(p):sha(p) for p in sorted(paths)};save(out/'sources-before.json',before)
    legacy_case='hit_p' if args.case.startswith('rear_vertical_') else args.case
    user=['--contract='+str(contract)]
    if args.case.startswith('rear_vertical_'):user.append('--candidate-case='+args.case)
    if args.mode=='main':
        script='ground_fx_entry.gd'
        user += ['--review-trace='+str(out/'main-trace.json'),'--back-lift-stills='+str(out/'stills'),
                 '--back-lift-size='+args.size,'--back-lift-case='+legacy_case,'--back-lift-owner='+str(args.owner),
                 '--back-lift-gap='+str(args.gap),'--back-lift-jump-delay='+str(args.jump_delay)]
        display=['--windowed','--resolution',args.size,'--fixed-fps','60','--max-fps','60','--disable-vsync']
    elif args.mode=='search':
        script='search.gd';display=['--headless']
        user += ['--search-output='+str(out/'search-result.json'),'--search-gaps='+args.search_gaps,
                 '--search-delays='+args.search_delays,'--back-lift-owner='+str(args.owner),'--back-lift-case='+legacy_case]
    else:
        assert args.trace and args.trace.is_file()
        script='blocked_replay.gd' if args.mode=='blocked-replay' else 'input_replay.gd' if args.mode=='input-replay' else 'replay.gd';display=['--headless']
        user += ['--back-lift-trace='+str(args.trace.resolve()),'--back-lift-replay-output='+str(out/'replay-result.json')]
    command=[godot_path(),'--audio-driver','Dummy',*display,'--path',str(ROOT),'--script','res://'+(HERE/'runtime'/script).relative_to(ROOT).as_posix(),'--',*user]
    save(out/'command.json',command)
    env=isolated_test_environment(out)
    for key,name in [("XDG_CACHE_HOME","xdg-cache"),("XDG_CONFIG_HOME","xdg-config")]:
        folder=out/name;folder.mkdir();env[key]=str(folder)
    status='not_started'
    try:
        with (out/'engine.log').open('xb') as log:
            result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900 if args.mode=='search' else 300)
        status=result.returncode
    except subprocess.TimeoutExpired:status='timeout'
    finally:
        after={str(p):sha(p) for p in sorted(paths)}
        log=(out/'engine.log').read_text('utf-8',errors='replace')
        diagnostics=[line for line in log.splitlines() if re.search(r'SCRIPT ERROR:|^ERROR:|Parse Error:',line)]
        save(out/'run-result.json',dict(exit=status,diagnostics=diagnostics,sources_unchanged=before==after,
             isolated_user_data=True,installed=False,visual_accepted=False,audio_driver='Dummy',audible_audio_validated=False))
    assert status==0 and not diagnostics and before==after
    if args.mode=='search':
        evidence=json.loads((out/'search-result.json').read_text('utf-8'))
        assert all(int(row['owner'])==args.owner and row['case']==args.case for row in evidence['rows']), 'case/owner与请求不符'
    elif args.mode=='main':
        evidence=json.loads((out/'main-trace.json').read_text('utf-8'))
        assert int(evidence['owner'])==args.owner and evidence['case']==args.case, 'main case/owner与请求不符'
    print(out)
if __name__=='__main__':main()

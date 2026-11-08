"""仅供根持唯一锁运行；临时main候选，原用户设置/上次回放始终逐字节恢复。"""
from pathlib import Path
import argparse, hashlib, json, re, subprocess, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
PLAN = ROOT/'reports/review/2026-11-02/gomora-super3-main-candidate-v1/install-plan.json'
sys.path.insert(0, str(ROOT/'tools'))
sys.path.insert(0, str(ROOT/'tools/rebuild/shared'))
from verify import godot_path
import codex_ex_direct_selection_runtime as common

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x',encoding='utf8',newline='\n') as f:
        json.dump(x,f,ensure_ascii=False,indent=2); f.write('\n')

def sources(plan):
    paths = {ROOT/'project.godot', PLAN, Path(common.__file__), ROOT/'tools/verify.py', ROOT/'tools/godot_lock.py',
             ROOT/'tests/review/fighters/ultraman-teo/codex_super1_arrow_review_driver.gd',
             ROOT/'tools/rebuild/shared/stamina_quick_input_common.gd'}
    for folder in ['app','core','content','input','presentation','ui']:
        paths.update(p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in {'.gd','.json','.tres','.tscn','.gdshader'})
    paths.update(p for p in HERE.rglob('*') if p.is_file() and p.suffix in {'.py','.gd'})
    paths.update(ROOT/row['path'] for row in plan['entries'])
    for folder in ['assets/fighters/gomora','assets/fighters/zetton','assets/fighters/ultraseven','assets/effects/gomora/back_lift']:
        paths.update(p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix != '.import')
    return {p.relative_to(ROOT).as_posix():sha(p) if p.is_file() else None for p in sorted(paths)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('mode',choices=['baseline','import','legacy-after','logic','main','replay'])
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--baseline-file',type=Path);ap.add_argument('--trace',type=Path)
    ap.add_argument('--case',default='hit_p');ap.add_argument('--owner',type=int,choices=[0,1],default=0)
    ap.add_argument('--jump-delay',type=int,default=13);ap.add_argument('--gap',type=int,default=68)
    ap.add_argument('--size',choices=['1280x720','1920x1080'],default='1280x720')
    args=ap.parse_args()
    assert (ROOT/'art/shared/locks/godot.lock').is_file(),'根须持Godot唯一锁'
    out=args.out.resolve();assert out.is_relative_to(ROOT) and not out.exists();out.mkdir(parents=True)
    plan=json.loads(PLAN.read_text('utf8'))
    for row in plan['entries']:
        p=ROOT/row['path'];expected=row['before_sha256' if args.mode=='baseline' else 'after_sha256']
        assert (sha(p) if p.exists() else None)==expected,row['path']
    before=sources(plan);save(out/'source-before.json',before)
    user=[];script='throw_target_step_regression.gd';headless=True
    if args.mode in ['baseline','legacy-after']:
        user=['--throw-target-out='+str(out)]
        if args.mode=='baseline':user.append('--baseline')
        else:
            assert args.baseline_file and args.baseline_file.is_file()
            user.append('--throw-target-baseline='+str(args.baseline_file.resolve()))
    elif args.mode=='logic':
        script='main_candidate_logic.gd';user=['--back-lift-logic-output='+str(out/'logic-result.json')]
    elif args.mode=='main':
        script='main_candidate_entry.gd';headless=False
        user=['--review-trace='+str(out/'main-trace.json'),'--back-lift-stills='+str(out/'stills'),
              '--back-lift-case='+args.case,'--back-lift-owner='+str(args.owner),'--back-lift-jump-delay='+str(args.jump_delay),
              '--back-lift-gap='+str(args.gap),'--back-lift-size='+args.size]
    elif args.mode=='replay':
        assert args.trace and args.trace.is_file();script='main_candidate_replay.gd'
        user=['--back-lift-trace='+str(args.trace.resolve()),'--back-lift-replay-output='+str(out/'replay-result.json')]
    command=[str(godot_path()),*(['--headless'] if headless else ['--windowed','--resolution',args.size,'--fixed-fps','60','--max-fps','60','--disable-vsync']), '--path',str(ROOT)]
    if args.mode=='import':command+=['--editor','--import','--quit']
    else:command+=['--script','res://'+(HERE/script).relative_to(ROOT).as_posix(),'--',*user]
    save(out/'command.json',command)
    user_data,original=common.preserve_user_data(out)
    exit_code='not_started';diagnostics=[];exception=None;after={}
    try:
        with (out/'engine.log').open('xb') as log:
            result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=180 if headless else 240)
            exit_code=result.returncode
    except subprocess.TimeoutExpired:
        exit_code='timeout';exception='Godot进程超时；subprocess已终止本次子进程'
    except Exception as error:
        exception=type(error).__name__+': '+str(error)
    finally:
        try:
            common.restore_user_data(out,user_data,original)
        finally:
            if (out/'engine.log').exists():
                diagnostics=[s for s in (out/'engine.log').read_text('utf8',errors='replace').splitlines() if re.search(r'SCRIPT ERROR:|Parse Error:|ERROR:|\bFAIL\b|\bWARN(?:ING)?\b',s)]
            after=sources(plan);save(out/'source-after.json',after)
            restored=(out/'user-data-restoration.json').is_file() and json.loads((out/'user-data-restoration.json').read_text('utf8'))['restored_exact_bytes']
            save(out/'root-run-result.json',dict(exit_code=exit_code,diagnostics=diagnostics,exception=exception,source_bytes_preserved=before==after,user_data_restored_exact_bytes=restored,mode=args.mode,generated_videos=0))
    print(json.dumps(dict(output=str(out),exit_code=exit_code,diagnostics=diagnostics,exception=exception),ensure_ascii=False))
    assert exit_code==0 and not diagnostics and not exception and before==after and restored
if __name__=='__main__':main()

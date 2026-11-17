"""持项目锁审计候选真实反馈模块，不改生产代码或输出旧证据。"""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools'))
from runtime.environment import godot_path,isolated_test_environment
BASE=ROOT/'reports/gomora-builtin/main-midlate-groundfx-20261105'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert (ROOT/'art/shared/locks/godot.lock').is_file()
    out=BASE/'feedback-audit-v2';assert not out.exists();out.mkdir()
    paths=set(p for folder in ['core','input','app','presentation','content'] for p in (ROOT/folder).rglob('*') if p.suffix in {'.gd','.json','.tres','.tscn','.gdshader'})
    paths.update((ROOT/'tools/rebuild/gomora/back_lift_resume/runtime').glob('*.gd'));paths.add(Path(__file__))
    for p in [BASE/'contract.json',ROOT/'reports/gomora-builtin/main-midlate-feedback-local-20261105/contract.json']:
        paths.add(p)
        for r in json.loads(p.read_text())['bound_resources']:
            bound=Path(r['path']);assert sha(bound)==r['sha256'];paths.add(bound)
    before={str(p):sha(p) for p in sorted(paths)}
    (out/'sources-before.json').write_text(json.dumps(before,indent=2))
    cmd=[godot_path(),'--headless','--audio-driver','Dummy','--path',str(ROOT),'--script','res://tools/rebuild/gomora/back_lift_resume/runtime/ground_feedback_audit.gd','--','--contract='+str(BASE/'contract.json'),'--baseline='+str(ROOT/'reports/gomora-builtin/main-midlate-feedback-local-20261105/contract.json'),'--traces='+str(BASE),'--output='+str(out/'audit-result.json')]
    (out/'command.json').write_text(json.dumps(cmd,indent=2));env=isolated_test_environment(out)
    for key,name in [('XDG_CACHE_HOME','xdg-cache'),('XDG_CONFIG_HOME','xdg-config')]:
        folder=out/name;folder.mkdir();env[key]=str(folder)
    with (out/'engine.log').open('wb') as log:result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
    diagnostics=[x for x in (out/'engine.log').read_text().splitlines() if re.search(r'SCRIPT ERROR:|^ERROR:|Parse Error:',x)]
    after={str(p):sha(p) for p in sorted(paths)}
    (out/'run-result.json').write_text(json.dumps(dict(exit=result.returncode,diagnostics=diagnostics,sources_unchanged=before==after,installed=False),indent=2))
    assert result.returncode==0 and not diagnostics and before==after
    assert not json.loads((out/'audit-result.json').read_text())['errors']
    print(out)
if __name__=='__main__':main()

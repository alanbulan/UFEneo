"""第二反馈候选：使用已注册impact_light，保留首版及未注册impact_hit失败证据。"""
import copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'reports/gomora-builtin/main-midlate-feedback-20261105/contract.json'
OUT=ROOT/'reports/gomora-builtin/main-midlate-feedback-local-20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists()
    original=json.loads(BASE.read_text());cfg=copy.deepcopy(original)
    for r in cfg['bound_resources']:assert sha(Path(r['path']))==r['sha256']
    assert cfg['move']['feedback']['spark']=='impact_hit'
    registry=json.loads((ROOT/'content/presentation/impact_effects.json').read_text());assert 'impact_light' in registry and 'impact_hit' not in registry
    cfg['move']['feedback']['spark']='impact_light'
    restored=copy.deepcopy(cfg);restored['move']['feedback']['spark']='impact_hit';assert restored==original
    cfg['local_feedback_correction']={'prior_contract':str(BASE),'prior_sha256':sha(BASE),'old_spark':'impact_hit','new_spark':'impact_light','reason':'旧impact_hit未注册，使用现装局部火花；不改全局注册或其它角色。','installed':False}
    for p in [BASE,Path(__file__)]:cfg['bound_resources'].append({'path':str(p.resolve()),'sha256':sha(p)})
    OUT.mkdir(parents=True);p=OUT/'contract.json';p.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');print(str(p),sha(p))
if __name__=='__main__':main()

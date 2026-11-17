"""仅候选feedback定向到真实摔落；不改正式战斗或共享反馈实现。"""
import copy
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'reports/gomora-builtin/main-midlate-a-20261105/contract.json'
OUT=ROOT/'reports/gomora-builtin/main-midlate-feedback-20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists()
    original=json.loads(BASE.read_text());cfg=copy.deepcopy(original)
    for r in cfg['bound_resources']:assert sha(Path(r['path']))==r['sha256']
    assert 'finish_effect' not in cfg['move']['feedback'] and 'finish_trigger' not in cfg['move']['feedback']
    cfg['move']['feedback'].update(finish_effect='explosion',finish_trigger='throw_slam')
    stripped=copy.deepcopy(cfg);stripped['move']['feedback'].pop('finish_effect');stripped['move']['feedback'].pop('finish_trigger');assert stripped==original
    cfg['feedback_candidate']={'base_contract':str(BASE),'base_sha256':sha(BASE),'only_move_changes':{'feedback.finish_effect':'explosion','feedback.finish_trigger':'throw_slam'},'production_code_changed':False,'installed':False}
    for p in [BASE,Path(__file__)]:cfg['bound_resources'].append({'path':str(p.resolve()),'sha256':sha(p)})
    OUT.mkdir(parents=True);p=OUT/'contract.json';p.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');print(str(p),sha(p))
if __name__=='__main__':main()

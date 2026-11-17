"""仅候选地面爆炸别名：完整现装图固定anchor120，不移动战斗事件。"""
import copy,hashlib,json
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'reports/gomora-builtin/main-midlate-feedback-local-20261105/contract.json'
OUT=ROOT/'reports/gomora-builtin/main-midlate-groundfx-20261105'
ALIAS='gomora_candidate_ground_explosion'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists()
    original=json.loads(BASE.read_text());cfg=copy.deepcopy(original)
    for r in cfg['bound_resources']:assert sha(Path(r['path']))==r['sha256']
    registry_path=ROOT/'content/presentation/impact_effects.json';registry=json.loads(registry_path.read_text());assert ALIAS not in registry
    fx=copy.deepcopy(registry['explosion']);assert fx['anchor']==[72,72] and fx['display_scale']==[1,1]
    fx['anchor']=[72,120]
    assert cfg['move']['feedback']['finish_effect']=='explosion'
    cfg['move']['feedback']['finish_effect']=ALIAS
    restored=copy.deepcopy(cfg);restored['move']['feedback']['finish_effect']='explosion';assert restored==original
    cfg['feedback_effect_aliases']={ALIAS:fx}
    texture=ROOT/fx['texture'].removeprefix('res://');assert sha(texture)==fx['atlas_sha256']
    image=Image.open(texture).convert('RGBA');bounds=[]
    for x,y,w,h in fx['rects']:
        a=np.asarray(image.crop((x,y,x+w,y+h)))[...,3];ys,xs=np.where(a>0)
        bounds.append({'alpha_bbox_inclusive':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],'lower_below_event_y':int(ys.max())-120})
    cfg['ground_fx_candidate']={'base_contract':str(BASE),'base_sha256':sha(BASE),'alias':ALIAS,'old_anchor':[72,72],'new_anchor':[72,120],'phase_bounds':bounds,'event_coordinates_unchanged':True,'installed':False}
    for p in [BASE,Path(__file__),registry_path,texture]:cfg['bound_resources'].append({'path':str(p.resolve()),'sha256':sha(p)})
    OUT.mkdir(parents=True);p=OUT/'contract.json';p.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');print(str(p),sha(p),bounds)
if __name__=='__main__':main()

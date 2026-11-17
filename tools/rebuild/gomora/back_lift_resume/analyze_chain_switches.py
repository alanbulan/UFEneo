"""只读整帧换相分解：固定髋点，对比承载方遮挡贡献；不生成/修改素材。"""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
d=json.loads((ROOT/'docs/verification/gomora-main-chain-registration.json').read_text())
frames={r['tick']:r for r in d['frames']}
actors={i:np.asarray(Image.open(ROOT/f'art/fighters/gomora/stage4/super3-back-lift-registration/current/{i:02}.png').convert('RGBA'))[...,3]>=128 for i in (5,6,7)}
def mask(label, hip):
 s=d['sources'][label]; im=Image.open(ROOT/s['path']).convert('RGBA').resize(s['fixed_whole_size'],Image.Resampling.NEAREST)
 a=np.asarray(im)[...,3]>=128; out=np.zeros_like(actors[5]); x,y=[hip[j]-s['local_pelvis'][j] for j in (0,1)];out[y:y+a.shape[0],x:x+a.shape[1]]=a;return out
rows=[]
for t in (23,27):
 a,b=frames[t],frames[t+1]; hip=a['pelvis_canvas']; am,bm=actors[a['actor']],actors[b['actor']]; m,n=mask(a['receiver'],hip),mask(b['receiver'],hip)
 lower=np.indices(m.shape)[0]>=hip[1]
 def count(r,actor):return {'all_visible':int((r&~actor).sum()),'below_hip_visible':int((r&~actor&lower).sum()),'below_hip_opaque':int((r&lower).sum())}
 cp=a['contact_canvas']; np_=b['contact_canvas']
 rows.append({'contact_cross_check':{'old_point':cp,'old_point_alpha_old_new_actor':[int(am[cp[1],cp[0]]),int(bm[cp[1],cp[0]])],'new_point':np_,'new_point_alpha_old_new_actor':[int(am[np_[1],np_[0]]),int(bm[np_[1],np_[0]])]},'ticks':[t,t+1],'fixed_pelvis_for_counterfactual':hip,'actual_pelvis_step':[b['pelvis_canvas'][j]-hip[j] for j in (0,1)],'old_receiver_old_actor':count(m,am),'old_receiver_new_actor':count(m,bm),'new_receiver_old_actor':count(n,am),'new_receiver_new_actor':count(n,bm),'actor_only_newly_exposed_old_receiver_pixels':int((m&am&~bm).sum()),'actor_only_newly_hidden_old_receiver_pixels':int((m&~am&bm).sum())})
print(json.dumps({'schema':1,'method':'整图固定现用尺寸和Alpha128，以旧髋点固定四种组合；仅分解轮廓遮挡，不代表合法承重配对。below_hip为髋点水平线下全部Alpha，并非解剖分割。','rows':rows,'accepted':False,'installed':False},ensure_ascii=False,indent=2))

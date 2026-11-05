"""按实看签收与真实扫腿脚面装配月亮sweep候选，禁止自动开放装甲。"""
import copy
from pathlib import Path
import numpy as np
from PIL import Image
import prepare as P

def hurtboxes(im):
 a=np.asarray(im)[:,:,3]>0;ys,_=np.where(a);top,bottom=int(ys.min()),int(ys.max())+1;boxes=[]
 for n in range(3):
  y0,y1=top+(bottom-top)*n//3,top+(bottom-top)*(n+1)//3;_,xs=np.where(a[y0:y1])
  if len(xs):boxes.append([int(xs.min())-160,280-y1,int(xs.max()-xs.min()+1),y1-y0])
 return boxes

def build():
 samples=P.read(P.OUTPUT/'samples.json');review_path=P.OUTPUT/'registration-review.json';review=P.read(review_path)
 if review.get('reviewer')!='root_delegated_by_user' or not review.get('accepted_for_registration'):raise ValueError('缺实看签收')
 if (P.OUTPUT/'manifest.json').exists():raise ValueError('禁止覆盖已配准候选')
 base=P.ROOT/'content/fighters/ultraman-arc/moves/sweep.json';move=copy.deepcopy(P.read(base))
 move['production_source']='月亮装甲独立完整源共同159/1254缩放；第2/3相实测扫腿脚面；保留原时序、下段倒地规则、伤害费用取消位移。'
 atlas=Image.new('RGBA',(320*7,320));frames=[]
 if len(samples['phases'])!=7 or len(review['phases'])!=7:raise ValueError('必须七相')
 for row,approved in zip(samples['phases'],review['phases']):
  phase=row['phase'];sample_path=P.ROOT/row['sample']['path']
  if approved['phase']!=phase or approved['sample_sha256']!=P.sha(sample_path):raise ValueError('签收样本变化')
  x,y=approved['translation']
  if [x,y]!=row['proposed_translation'] or not(0<=x<=161 and 0<=y<=161):raise ValueError('签收平移不符/越界')
  with Image.open(sample_path) as sample:
   full=Image.new('RGBA',(320,320));full.paste(sample,(x,y))
   if full.crop((x,y,x+159,y+159)).tobytes()!=sample.tobytes():raise ValueError('整图像素未保留')
  boxes=hurtboxes(full);path=P.OUTPUT/f'frame-{phase:02}.png';full.save(path);atlas.paste(full,(phase*320,0))
  for frame in move['frames']:
   if int(frame['sprite'])==phase:
    frame['hurtboxes']=copy.deepcopy(boxes)
    frame['hitboxes']={2:[[58,5,12,12]],3:[[60,12,12,12]]}.get(phase,[])
  frames.append({**row,'image':P.ref(path),'translation':[x,y],'hurtboxes':boxes})
 atlas_path=P.OUTPUT/'atlas.png';atlas.save(atlas_path)
 clip={'texture':'res://'+atlas_path.relative_to(P.ROOT).as_posix(),'atlas_sha256':P.sha(atlas_path),'source_fighter':'ultraman-arc__luna',
       'cell':320,'anchor_y':280,'rects':[[n*320,0,320,320] for n in range(7)],'ticks':[r['ticks'] for r in frames],
       'anchors':[[160,280]]*7,'loop':False,'simulation_sprite_offset':0}
 P.write(P.OUTPUT/'move.json',move);P.write(P.OUTPUT/'clip.json',clip)
 result={'schema':'ufeneo.luna.sweep-registered-candidate.v1','fighter':'ultraman-arc__luna','action':'sweep','samples':P.ref(P.OUTPUT/'samples.json'),
         'registration_review':P.ref(review_path),'rule_reference':P.ref(base),'clip':P.ref(P.OUTPUT/'clip.json'),'move':P.ref(P.OUTPUT/'move.json'),'frames':frames,
         'processing_tools':{'prepare':P.ref(Path(P.__file__).resolve()),'register':P.ref(Path(__file__).resolve())},
         'canvas':[320,320],'root':[160,280],'per_phase_rescale':False,'limb_editing':False,'installed':False,'playable':False,'main_game_accepted':False}
 P.write(P.OUTPUT/'manifest.json',result)
 return result
if __name__=='__main__':build()

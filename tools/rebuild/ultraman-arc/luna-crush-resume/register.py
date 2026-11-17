"""重砸完整七槽整图RAM候选登记；统一后胫投影尺，不安装正式资源。"""
from pathlib import Path
import sys,json,hashlib,copy
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
GEOM=HERE.parent/'luna-crush-geometry'
sys.path.insert(0,str(GEOM))
from geometry import build_frames
OUT=ROOT/'art/fighters/ultraman-arc__luna/stage2/crush-registered-20261105-v1'
PLAN=GEOM/'plan-followthrough-v3.json'
TICKS=[3,5,4,8,4,5,6]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def read(p):return json.loads(p.read_text())
def put(p,v):
 assert not p.exists(),str(p)
 p.parent.mkdir(parents=True,exist_ok=True)
 if isinstance(v,Image.Image):v.save(p)
 else:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def hurts(im):
 a=np.asarray(im)[:,:,3];ys,_=np.where(a);top,bottom=int(ys.min()),int(ys.max())+1;out=[]
 for n in range(3):
  y0,y1=top+(bottom-top)*n//3,top+(bottom-top)*(n+1)//3;_,xs=np.where(a[y0:y1])
  if len(xs):out.append([int(xs.min())-160,280-y1,int(xs.max()-xs.min()+1),y1-y0])
 return out

def main():
 assert not OUT.exists(),'禁止覆盖旧登记'
 images,geometry=build_frames(plan_path=PLAN)
 again,other=build_frames(plan_path=PLAN)
 assert geometry==other and all(a.tobytes()==b.tobytes() for a,b in zip(images,again))
 assert images[0].tobytes()==images[-1].tobytes()
 put(OUT/'geometry.json',geometry)
 actions={}
 for action,ims,gs,ticks in [('idle',[images[0]],[geometry['frames'][0]],[10]),('crush',images,geometry['frames'],TICKS)]:
  atlas=Image.new('RGBA',(320*len(ims),320));rows=[]
  for i,(im,g,duration) in enumerate(zip(ims,gs,ticks)):
   offset=g['whole_image_translation'];w,h=g['sample_size'];sample=im.crop((offset[0],offset[1],offset[0]+w,offset[1]+h))
   check=Image.new('RGBA',(320,320));check.paste(sample,tuple(offset));assert check.tobytes()==im.tobytes()
   sample_path=OUT/'samples'/action/f'phase-{i:02}.png';frame_path=OUT/action/f'frame-{i:02}.png'
   put(sample_path,sample);put(frame_path,im);atlas.paste(im,(i*320,0))
   rows.append({'phase':i,'source_phase':i,'key':g['key'],'ticks':duration,'source':g['source'],'source_sha256':g['source_sha256'],'image':ref(frame_path)['path'],'image_sha256':sha(frame_path),'whole_source_sample':ref(sample_path),'whole_source_destination_offset':offset,'root':[160,280],'alpha_bbox':list(im.getbbox()),'whole_image_only':True,'pixel_comparison_passed':True,'uniform_scale':g['scale'],'scale_ruler':'rear_shin_model_projection'})
  atlas_path=OUT/action/'atlas.png';put(atlas_path,atlas)
  clip={'fighter':'ultraman-arc__luna','source_fighter':'ultraman-arc__luna','action':action,'texture':'res://'+ref(atlas_path)['path'],'atlas_sha256':sha(atlas_path),'cell':320,'anchor':[160,280],'anchor_y':280,'anchors':[[160,280]]*len(ims),'rects':[[320*i,0,320,320] for i in range(len(ims))],'ticks':ticks,'loop':action=='idle','simulation_sprite_offset':0}
  clip_path=OUT/action/'clip.json';put(clip_path,clip);put(OUT/action/'frames.json',{'fighter':'ultraman-arc__luna','action':action,'frames':rows})
  group={'frames':rows,'clip':ref(clip_path)}
  if action=='crush':
   roi=[205,205,217,216];tight=ims[3].getchannel('A').crop(roi).getbbox();assert tight; bbox=[roi[0]+tight[0],roi[1]+tight[1],roi[0]+tight[2],roi[1]+tight[3]];box=[bbox[0]-160,280-bbox[3],bbox[2]-bbox[0],bbox[3]-bbox[1]]
   rows[3]['fist_roi_native']=roi;rows[3]['fist_alpha_bbox_native']=bbox
   rows[5]['reused_source_phase']=2;rows[5]['reuse_note']='同一descent01完整源用于屈肘回护，不是新生成相'
   reference=ROOT/'content/fighters/ultraman-arc/moves/crush.json';move=copy.deepcopy(read(reference));move['display_name']='双臂重砸候选';move['production_source']='七槽五独立整帧；后胫统一尺；仅接触相远拳Alpha框，原12/8/15与130伤30体力不可防，不安装。'
   timeline=[(im,row) for im,row in zip(ims,rows) for _ in range(row['ticks'])];assert len(timeline)==len(move['frames'])==35
   for f,(im,r) in zip(move['frames'],timeline):
    f['sprite']=r['phase'];f['hurtboxes']=hurts(im);f['hitboxes']=[box] if r['phase']==3 else [];f['cancel']=[]
   move_path=OUT/action/'move.json';put(move_path,move);group.update(move=ref(move_path),rule_reference=ref(reference),fist_boxes={'3':box})
  actions[action]=group
 manifest={'schema':'ufeneo.arc-luna.crush-registration.v1','fighter':'ultraman-arc__luna','actions':actions,'source_order':list(range(7)),'registration_plan':ref(PLAN),'geometry':ref(OUT/'geometry.json'),'geometry_tool':ref(GEOM/'geometry.py'),'runtime_canvas':[320,320],'runtime_root':[160,280],'processing_tools':{'register':ref(Path(__file__).resolve())},'backend':geometry['backend'],'palette':ref(ROOT/'art/fighters/ultraman-arc__luna/model/palette.json'),'alpha_threshold':128,'native_clean_alpha_claimed':False,'art_passed':False,'installed':False,'playable':False,'transform_enabled':False,'scale_method':'全相后胫统一model近胫投影，整图等比缩放，无局部修图；投影不冒称骨长已确证','idle_limit':'实际idle00单相对照用于本次动作首尾；不是六相idle循环验收'}
 put(OUT/'manifest.json',manifest)
 put(OUT/'registration-review.json',{'reviewer':'root_delegated_by_user','accepted_for_formal_main_candidate':True,'art_passed':False,'installed':False,'manifest_sha256':sha(OUT/'manifest.json'),'date_utc':'2026-11-05','sequence':[r['key'] for r in geometry['frames']],'ticks':TICKS,'limits':['七槽仅为RAM候选；非原速、美术、声音或真人键盘验收','回护明确复用下降同源；后掌比较锚110不等于运行root160']})
 print(OUT)
if __name__=='__main__':main()

"""月亮升拳七完整源统一尺度与唯一上挑拳面配准；不切肢、不改原源。"""
from pathlib import Path
import hashlib,json,sys,copy,math
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/rebuild/shared'))
from forge_backend import backend_info,binarize_alpha,_kcentroid_downscale,apply_palette,palette_mode
BASE=ROOT/'art/fighters/ultraman-arc__luna/stage2'
OUT=BASE/'launcher-registered-20261105-v1'
CLOCKS={'idle':[10]*6,'launcher':[3,3,3,5,3,3,3]}
SOURCE_ORDER=[0,1,2,3,4,5,6]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def read(p):return json.loads(p.read_text('utf-8-sig'))
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),str(p)
 if isinstance(v,Image.Image):v.save(p)
 else:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
 plan=read(Path(__file__).with_name('registration-plan.json'));actions={}
 with palette_mode('rgb'):
  backend={k:v for k,v in backend_info().items() if k not in {'scripts','python'}}
  frozen=read(BASE/'heavy-registered-20261105-v1/samples.json')['backend']['files']
  assert backend['files']==frozen, 'Forge实现与既有月亮流程不同'
  for action,ticks in CLOCKS.items():
   recipe=plan['actions'][action];size=recipe['sample_size'];rows=[];atlas=Image.new('RGBA',(320*len(ticks),320))
   for phase,duration in enumerate(ticks):
    source_phase=phase
    source=ROOT/recipe['sources'][phase]
    assert sha(source)==recipe['source_sha256'][str(source_phase)]
    im=Image.open(source).convert('RGBA');assert im.size==(1254,1254)
    small=_kcentroid_downscale(binarize_alpha(im.copy()),size,size,detail_bias=True)
    apply_palette(small,read(ROOT/'art/fighters/ultraman-arc__luna/model/palette.json')['colors']);binarize_alpha(small)
    bbox=small.getbbox();hip_x=None
    offset=[80,280-bbox[3]]
    image=Image.new('RGBA',(320,320));image.paste(small,tuple(offset))
    assert image.getbbox()[3]==280
    assert image.getchannel('A').histogram()[255]==small.getchannel('A').histogram()[255]
    assert image.crop((*offset,offset[0]+size,offset[1]+size)).tobytes()==small.tobytes()
    sample=OUT/'samples'/action/f'phase-{phase:02}.png';frame=OUT/action/f'frame-{phase:02}.png'
    put(sample,small);put(frame,image);atlas.paste(image,(320*phase,0))
    rows.append(dict(phase=phase,source_phase=source_phase,ticks=duration,source=ref(source)['path'],source_sha256=sha(source),image=ref(frame)['path'],image_sha256=sha(frame),whole_source_sample=ref(sample),whole_source_destination_offset=offset,root=[160,280],alpha_bbox=list(image.getbbox()),whole_image_only=True,pixel_comparison_passed=True,source_hip_x=hip_x))
   fist_boxes={}
   for row in rows:
    original=row['source_phase']
    if str(original) not in recipe['source_fist_rois']:continue
    roi=recipe['source_fist_rois'][str(original)];r=[math.floor(roi[0]*size/1254),math.floor(roi[1]*size/1254),math.ceil(roi[2]*size/1254),math.ceil(roi[3]*size/1254)]
    sample=Image.open(ROOT/row['whole_source_sample']['path']).convert('RGBA');tight=sample.getchannel('A').crop(tuple(r)).getbbox();assert tight
    offset=row['whole_source_destination_offset'];full=[r[0]+tight[0]+offset[0],r[1]+tight[1]+offset[1],r[0]+tight[2]+offset[0],r[1]+tight[3]+offset[1]]
    box=[full[0]-160,280-full[3],full[2]-full[0],full[3]-full[1]];assert box[2]<=18 and box[3]<=18
    row['source_fist_roi']=roi;row['whole_frame_fist_bbox']=full;row['fist_box']=box;fist_boxes[str(row['phase'])]=box
   if action=='launcher':
    reference=ROOT/'content/fighters/ultraman-arc/moves/launcher.json';move=copy.deepcopy(read(reference))
    move['display_name']='升拳候选';move['startup']=9;move['active']=5;move['recovery']=9;move['production_source']='本人idle00/新蓄拳/渐伸/上挑/高位回收/回收中相/idle00七相候选；只有上挑接触相，9/5/9共23tick，未安装或艺术验收。'
    timeline=[r for r in rows for _ in range(r['ticks'])];assert len(move['frames'])==len(timeline)==23
    for index,(frame,row) in enumerate(zip(move['frames'],timeline)):
     im=Image.open(ROOT/row['image']).convert('RGBA');a=np.asarray(im)[:,:,3]>0;ys,_=np.where(a);top,bottom=int(ys.min()),int(ys.max())+1;boxes=[]
     for n in range(3):
      y0,y1=top+(bottom-top)*n//3,top+(bottom-top)*(n+1)//3;_,xs=np.where(a[y0:y1])
      if len(xs):boxes.append([int(xs.min())-160,280-y1,int(xs.max()-xs.min()+1),y1-y0])
     frame['sprite']=row['phase'];frame['hurtboxes']=boxes;frame['hitboxes']=[fist_boxes[str(row['phase'])]] if str(row['phase']) in fist_boxes else [];frame['cancel']=[]
     assert int(frame['dx'])==0 and int(frame['dy'])==0
    move_path=OUT/action/'move.json';put(move_path,move)
   atlas_path=OUT/action/'atlas.png';put(atlas_path,atlas)
   clip=dict(fighter='ultraman-arc__luna',source_fighter='ultraman-arc__luna',action=action,texture='res://'+ref(atlas_path)['path'],atlas_sha256=sha(atlas_path),cell=320,anchor=[160,280],anchor_y=280,anchors=[[160,280]]*len(ticks),rects=[[320*i,0,320,320] for i in range(len(ticks))],ticks=ticks,loop=action in ['idle','crouch'],simulation_sprite_offset=0)
   cp=OUT/action/'clip.json';put(cp,clip);put(OUT/action/'frames.json',{'fighter':'ultraman-arc__luna','action':action,'frames':rows})
   actions[action]={'frames':rows,'clip':ref(cp),'common_full_source_raster':[size,size],'source_scale':size/1254}
   if action=='launcher':actions[action].update(move=ref(move_path),rule_reference=ref(reference),fist_boxes=fist_boxes)
 idle_manifest=BASE/'goal-closeout-20261101-v1/idle/frames.json'
 manifest=dict(schema='ufeneo.arc-luna.launcher-registration.v1',fighter='ultraman-arc__luna',actions=actions,source_order=SOURCE_ORDER,idle_source_manifest=ref(idle_manifest),registration_plan=ref(Path(__file__).with_name('registration-plan.json')),source_dimensions=[1254,1254],runtime_canvas=[320,320],runtime_root=[160,280],processing_tools={'register':ref(Path(__file__).resolve())},backend=backend,palette=ref(ROOT/'art/fighters/ultraman-arc__luna/model/palette.json'),per_phase_scale_or_area_fitting=False,alpha_threshold=128,native_clean_alpha_claimed=False,art_passed=False,installed=False,playable=False,transform_enabled=False)
 put(OUT/'manifest.json',manifest)
 print(json.dumps({a:[r['alpha_bbox'] for r in g['frames']] for a,g in actions.items()}))
if __name__=='__main__':main()

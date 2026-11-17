"""杰顿低蹲硬直两完整源共同尺度RAM配准，不修改正式资源。"""
from pathlib import Path
import sys,json,hashlib,copy
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/rebuild/shared'))
from forge_backend import binarize_alpha,_kcentroid_downscale,apply_palette,palette_mode,backend_info
SOURCE=ROOT/'art/fighters/zetton/stage3/crouch-block-posture-20261105'
OUT=ROOT/'art/fighters/zetton/stage3/crouch-block-registered-20261105-v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def put(p,data):
 assert not p.exists(),str(p);p.parent.mkdir(parents=True,exist_ok=True)
 if isinstance(data,Image.Image):data.save(p)
 else:p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def hurts(image):
 # 与正式旧硬直相同4px栅格精度。只取有Alpha的格，再横向合并；不填满整身空白。
 a=np.asarray(image)[:,:,3]>0;rects=[]
 for y in range(0,320,4):
  occupied=[bool(a[y:y+4,x:x+4].any()) for x in range(0,320,4)];start=None
  for n,on in enumerate(occupied+[False]):
   if on and start is None:start=n
   if not on and start is not None:rects.append([start*4-160,280-y-4,(n-start)*4,4]);start=None
 return rects

def main():
 assert not OUT.exists(),'禁止覆盖已注册候选'
 palette=ROOT/'content/fighters/zetton/palette.json';rows=[];atlas=Image.new('RGBA',(640,320))
 with palette_mode('rgb'):
  backend={k:v for k,v in backend_info().items() if k not in ['scripts','python']}
  frozen=read(ROOT/'art/fighters/ultraman-arc__luna/stage2/heavy-registered-20261105-v1/samples.json')['backend']['files']
  assert backend['files']==frozen
  for phase,name in enumerate(['phase-00-v2.raw.png','phase-01.raw.png']):
   source=SOURCE/name;raw=Image.open(source).convert('RGBA');assert raw.size==(1254,1254)
   sample=_kcentroid_downscale(binarize_alpha(raw.copy()),256,256,detail_bias=True);apply_palette(sample,read(palette)['colors']);binarize_alpha(sample)
   box=sample.getbbox();offset=[32,280-box[3]];assert 0<=offset[1]<=64
   full=Image.new('RGBA',(320,320));full.paste(sample,tuple(offset));assert full.crop((offset[0],offset[1],offset[0]+256,offset[1]+256)).tobytes()==sample.tobytes()
   sp=OUT/'samples'/f'phase-{phase:02}.png';fp=OUT/f'frame-{phase:02}.png';put(sp,sample);put(fp,full);atlas.paste(full,(320*phase,0))
   rows.append({'phase':phase,'ticks':[4,6][phase],'source':ref(source),'sample':ref(sp),'image':ref(fp),'whole_source_destination_offset':offset,'source_dimensions':[1254,1254],'sample_dimensions':[256,256],'root':[160,280],'alpha_bbox':list(full.getbbox()),'hurtboxes':hurts(full),'whole_image_only':True})
 atlas_path=OUT/'atlas.png';put(atlas_path,atlas)
 clip={'source_fighter':'zetton','texture':'res://'+atlas_path.relative_to(ROOT).as_posix(),'atlas_sha256':sha(atlas_path),'cell':320,'anchor_y':280,'anchors':[[160,280],[160,280]],'rects':[[0,0,320,320],[320,0,320,320]],'ticks':[4,6],'loop':False}
 put(OUT/'clip.json',clip)
 original=ROOT/'content/fighters/zetton/state_frames.json';frames=copy.deepcopy(read(original)['crouch_blockstun']);assert [f['sprite'] for f in frames]==[0]*4+[1]*6
 for frame in frames:frame['hurtboxes']=copy.deepcopy(rows[int(frame['sprite'])]['hurtboxes'])
 put(OUT/'state_frames.json',frames)
 manifest={'schema':'ufeneo.zetton.crouch-block-registration.v1','fighter':'zetton','action':'crouch_blockstun','frames':rows,'clip':ref(OUT/'clip.json'),'state_frames':ref(OUT/'state_frames.json'),'reference_state_frames':ref(original),'source_reviews':[ref(SOURCE/'phase-00-v2-review.json'),ref(SOURCE/'phase-01-review.json')],'palette':ref(palette),'backend':backend,'processing_tools':{'register':ref(Path(__file__).resolve())},'canvas':[320,320],'root':[160,280],'common_full_source_scale':256/1254,'alpha_threshold':128,'native_clean_alpha_claimed':False,'geometry_policy':'new actual Alpha occupied 4px cells, horizontal runs; no arbitrary standing hurtbox copied','installed':False,'art_passed':False,'main_game_accepted':False,'rule_change':'only candidate posture hurtboxes; no high-low/input/state/duration/cost/damage change; candidate content fingerprint differs naturally'}
 put(OUT/'manifest.json',manifest);print(json.dumps({'frames':[{k:r[k] for k in ['phase','alpha_bbox','whole_source_destination_offset']} for r in rows],'boxes':[len(r['hurtboxes']) for r in rows]}))
if __name__=='__main__':main()

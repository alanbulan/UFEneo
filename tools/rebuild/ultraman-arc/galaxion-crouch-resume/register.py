"""银河蹲起完整源统一动作尺度与真实脚底配准；不切肢、不改原源。"""
from pathlib import Path
import hashlib,json,sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/rebuild/shared'))
from forge_backend import binarize_alpha,_kcentroid_downscale,apply_palette,palette_mode
BASE=ROOT/'art/fighters/ultraman-arc__galaxion/stage2'
OUT=BASE/'crouch-registered-20261105-v1'
CLOCKS={'idle':[10]*6,'crouch_start':[3]*2,'crouch':[12]*2,'crouch_rise':[3]*2}
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
  for action,ticks in CLOCKS.items():
   recipe=plan['actions'][action];size=recipe['sample_size'];rows=[];atlas=Image.new('RGBA',(320*len(ticks),320))
   for phase,duration in enumerate(ticks):
    source=BASE/'ground-codex-20261027'/action/f'phase-{phase:02}'/'request-001/raw.provider.png'
    im=Image.open(source).convert('RGBA');assert im.size==(1254,1254)
    small=_kcentroid_downscale(binarize_alpha(im.copy()),size,size,detail_bias=True)
    apply_palette(small,read(ROOT/'art/fighters/ultraman-arc__galaxion/model/palette.json')['colors']);binarize_alpha(small)
    bbox=small.getbbox();hip_x=recipe['hip_x'][phase]
    offset=[160-round(hip_x*size/1254),280-bbox[3]]
    image=Image.new('RGBA',(320,320));image.paste(small,tuple(offset))
    assert image.getbbox()[3]==280
    assert image.getchannel('A').histogram()[255]==small.getchannel('A').histogram()[255]
    assert image.crop((*offset,offset[0]+size,offset[1]+size)).tobytes()==small.tobytes()
    sample=OUT/'samples'/action/f'phase-{phase:02}.png';frame=OUT/action/f'frame-{phase:02}.png'
    put(sample,small);put(frame,image);atlas.paste(image,(320*phase,0))
    rows.append(dict(phase=phase,ticks=duration,source=ref(source)['path'],source_sha256=sha(source),image=ref(frame)['path'],image_sha256=sha(frame),whole_source_sample=ref(sample),whole_source_destination_offset=offset,root=[160,280],alpha_bbox=list(image.getbbox()),whole_image_only=True,pixel_comparison_passed=True,source_hip_x=hip_x))
   atlas_path=OUT/action/'atlas.png';put(atlas_path,atlas)
   clip=dict(fighter='ultraman-arc__galaxion',source_fighter='ultraman-arc__galaxion',action=action,texture='res://'+ref(atlas_path)['path'],atlas_sha256=sha(atlas_path),cell=320,anchor=[160,280],anchor_y=280,anchors=[[160,280]]*len(ticks),rects=[[320*i,0,320,320] for i in range(len(ticks))],ticks=ticks,loop=action in ['idle','crouch'],simulation_sprite_offset=0)
   cp=OUT/action/'clip.json';put(cp,clip);put(OUT/action/'frames.json',{'fighter':'ultraman-arc__galaxion','action':action,'frames':rows})
   actions[action]={'frames':rows,'clip':ref(cp),'common_full_source_raster':[size,size],'source_scale':size/1254}
 manifest=dict(schema='ufeneo.arc-galaxion.crouch-registration.v1',fighter='ultraman-arc__galaxion',actions=actions,registration_plan=ref(Path(__file__).with_name('registration-plan.json')),source_dimensions=[1254,1254],runtime_canvas=[320,320],runtime_root=[160,280],per_phase_scale_or_area_fitting=False,alpha_threshold=128,native_clean_alpha_claimed=False,art_passed=False,installed=False,playable=False,transform_enabled=False)
 put(OUT/'manifest.json',manifest)
 print(json.dumps({a:[r['alpha_bbox'] for r in g['frames']] for a,g in actions.items()}))
if __name__=='__main__':main()

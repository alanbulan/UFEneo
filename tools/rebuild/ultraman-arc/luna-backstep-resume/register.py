"""复用旧五相整帧；验证共同159采样，按实际支撑鞋底整图平移到280。"""
from pathlib import Path
import hashlib,json,sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/rebuild/shared'))
from forge_backend import binarize_alpha,_kcentroid_downscale,apply_palette,palette_mode
BASE=ROOT/'art/fighters/ultraman-arc__luna/stage2'
OUT=BASE/'backstep-registered-20261105-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def read(p):return json.loads(p.read_text('utf-8-sig'))
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),str(p)
 if isinstance(v,Image.Image):v.save(p)
 else:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
 receipt=BASE/'backstep-repair-20261102-v1/offline-five-registered-v1/frames.json'
 old=read(receipt);rows=[];atlas=Image.new('RGBA',(1600,320))
 with palette_mode('rgb'):
  for r in old['frames']:
   phase=r['phase'];source=ROOT/r['source'];previous=ROOT/r['image']
   assert sha(source)==r['source_sha256'] and sha(previous)==r['image_sha256']
   im=Image.open(source).convert('RGBA');assert im.size==(1024,1024)
   small=_kcentroid_downscale(binarize_alpha(im.copy()),159,159,detail_bias=True)
   apply_palette(small,read(ROOT/'art/fighters/ultraman-arc__luna/model/palette.json')['colors']);binarize_alpha(small)
   prior=Image.open(previous).convert('RGBA');old_offset=r['whole_integer_translation']
   expected=Image.new('RGBA',(320,320));expected.paste(small,tuple(old_offset))
   assert expected.tobytes()==prior.tobytes(),f'旧159整图配方不符phase{phase}'
   shift=[0,280-prior.getbbox()[3]];offset=[old_offset[i]+shift[i] for i in range(2)]
   image=Image.new('RGBA',(320,320));image.paste(small,tuple(offset))
   assert image.getbbox()[3]==280 and image.getchannel('A').histogram()==prior.getchannel('A').histogram()
   assert image.crop((*offset,offset[0]+159,offset[1]+159)).tobytes()==small.tobytes()
   sample=OUT/'samples'/f'phase-{phase:02}.png';frame=OUT/'backstep'/f'frame-{phase:02}.png'
   put(sample,small);put(frame,image);atlas.paste(image,(320*phase,0))
   rows.append(dict(phase=phase,ticks=r['ticks'],source=ref(source)['path'],source_sha256=sha(source),image=ref(frame)['path'],image_sha256=sha(frame),whole_source_sample=ref(sample),previous_frame=ref(previous),previous_receipt=ref(receipt),previous_whole_source_destination_offset=old_offset,whole_source_destination_offset=offset,whole_image_shift=shift,root=[160,280],alpha_bbox=list(image.getbbox()),whole_image_only=True,pixel_comparison_passed=True))
 atlas_path=OUT/'backstep/atlas.png';put(atlas_path,atlas)
 ticks=[3,3,4,3,3];clip=dict(fighter='ultraman-arc__luna',source_fighter='ultraman-arc__luna',action='backstep',texture='res://'+ref(atlas_path)['path'],atlas_sha256=sha(atlas_path),cell=320,anchor=[160,280],anchor_y=280,anchors=[[160,280]]*5,rects=[[320*i,0,320,320] for i in range(5)],ticks=ticks,loop=False,simulation_sprite_offset=0)
 cp=OUT/'backstep/clip.json';put(cp,clip)
 manifest=dict(schema='ufeneo.arc-luna.backstep-registration.v1',fighter='ultraman-arc__luna',actions={'backstep':dict(frames=rows,clip=ref(cp))},common_full_source_raster=[159,159],source_dimensions=[1024,1024],source_scale=159/1024,runtime_canvas=[320,320],runtime_root=[160,280],per_phase_scale_or_area_fitting=False,alpha_threshold=128,native_clean_alpha_claimed=False,art_passed=False,installed=False,playable=False,transform_enabled=False)
 put(OUT/'manifest.json',manifest)
 print(json.dumps([{'phase':r['phase'],'shift':r['whole_image_shift'],'offset':r['whole_source_destination_offset'],'bbox':r['alpha_bbox']} for r in rows]))
if __name__=='__main__':main()

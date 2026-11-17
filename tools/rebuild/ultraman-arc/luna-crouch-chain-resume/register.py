"""现有完整02远侧右拳注册；第一拳沿已审v3，不安装、不改玩法。"""
import sys,json,copy,hashlib,importlib.util
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('first_register',HERE.parent/'luna-crouch-light-resume/register.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
OUT=ROOT/'art/fighters/ultraman-arc__luna/stage2/crouch-chain-registered-20261105-v1'
def ref(p):return base.ref(p)
def main():
 assert not OUT.exists()
 images,geometry=base.build_frames(HERE/'plan.json');again,g2=base.build_frames(HERE/'plan.json')
 assert geometry==g2 and all(a.tobytes()==b.tobytes() for a,b in zip(images,again))
 first=base.read(ROOT/'art/fighters/ultraman-arc__luna/stage2/crouch-light-registered-20261105-v1/manifest.json')
 with Image.open(ROOT/first['actions']['crouch']['frames'][0]['image']) as im:assert images[0].tobytes()==im.tobytes()
 base.put(OUT/'geometry.json',geometry)
 rows=[];atlas=Image.new('RGBA',(960,320));ticks=[3,7,8]
 for i,(im,g,t) in enumerate(zip(images,geometry['frames'],ticks)):
  p=OUT/'crouch_light2'/f'frame-{i:02}.png';base.put(p,im);atlas.paste(im,(320*i,0))
  offset=g['whole_image_translation'];w,h=g['sample_size'];sample=im.crop((offset[0],offset[1],offset[0]+w,offset[1]+h));sp=OUT/'samples'/f'phase-{i:02}.png';base.put(sp,sample)
  rows.append(dict(phase=i,ticks=t,source=g['source'],source_sha256=g['source_sha256'],image=ref(p)['path'],image_sha256=base.sha(p),whole_source_sample=ref(sp),whole_source_destination_offset=offset,alpha_bbox=list(im.getbbox()),uniform_scale=g['scale']))
 ap=OUT/'crouch_light2/atlas.png';base.put(ap,atlas)
 roi=[212,197,225,211];tight=images[1].getchannel('A').crop(roi).getbbox();assert tight
 bbox=[roi[0]+tight[0],roi[1]+tight[1],roi[0]+tight[2],roi[1]+tight[3]];box=[bbox[0]-160,280-bbox[3],bbox[2]-bbox[0],bbox[3]-bbox[1]]
 rows[1]['fist_roi_native']=roi;rows[1]['fist_alpha_bbox_native']=bbox
 cp=OUT/'crouch_light2/clip.json';base.put(cp,dict(fighter=base.read(HERE/'plan.json').get('fighter','ultraman-arc__luna'),source_fighter='ultraman-arc__luna',action='crouch_light2',texture='res://'+ref(ap)['path'],atlas_sha256=base.sha(ap),cell=320,anchor=[160,280],anchor_y=280,anchors=[[160,280]]*3,rects=[[320*i,0,320,320] for i in range(3)],ticks=ticks,loop=False,simulation_sprite_offset=0))
 rp=ROOT/'content/fighters/ultraman-arc/moves/crouch_light2.json';move=copy.deepcopy(base.read(rp));move['display_name']='蹲右拳完整端点候选';move['production_source']='现有远侧右拳02完整源，原3/7/8规则和sweep取消保持；无独立随势相，仅RAM。'
 for f,(im,i) in zip(move['frames'],[(im,i) for i,(im,t) in enumerate(zip(images,ticks)) for _ in range(t)]):f['sprite']=i;f['hurtboxes']=base.hurts(im);f['hitboxes']=[box] if i==1 else []
 mp=OUT/'crouch_light2/move.json';base.put(mp,move)
 manifest=dict(schema='ufeneo.luna.crouch-chain-registration.v1',fighter='ultraman-arc__luna',first_manifest=ref(ROOT/'art/fighters/ultraman-arc__luna/stage2/crouch-light-registered-20261105-v1/manifest.json'),actions=dict(first['actions'],crouch_light2=dict(frames=rows,clip=ref(cp),move=ref(mp),rule_reference=ref(rp),fist_boxes={'1':box})),geometry=ref(OUT/'geometry.json'),plan=ref(HERE/'plan.json'),processing_tool=ref(Path(__file__).resolve()),installed=False,playable=False,art_accepted=False,limitations=['两拳各只有蹲架/独立接触/回同蹲架三槽，二拳3/7/8保持，无独立随势相','原错左拳02仅在独立审图确认远侧右拳后用于第二拳','受方使用正式杰顿状态与图，旧crouch_blockstun高姿保留，新RAM低蹲图不混入'])
 base.put(OUT/'manifest.json',manifest);print(json.dumps({'out':str(OUT),'fist':box},ensure_ascii=False))
if __name__=='__main__':main()

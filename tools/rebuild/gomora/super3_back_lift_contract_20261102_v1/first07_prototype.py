"""根已接首源的整图1/4原型；只写报告，不改源/资源/请求。"""
from pathlib import Path
import sys, json, hashlib, math, runpy
import numpy as np
from PIL import Image, ImageDraw
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/rebuild/shared'))
import forge_backend as forge
OUT=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-first07-prototype-v1'
SRC=ROOT/'art/fighters/gomora/stage4/super3-back-lift-20261102-v1/phase-07/request-001/candidate.png'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,d):
 with p.open('x',encoding='utf8') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 assert not OUT.exists();OUT.mkdir()
 acceptance=SRC.with_name('root-actual-source-review-v1.json');gate=read(acceptance)
 assert gate['accepted_for_whole_action_processing'] and gate['source']['sha256']==sha(SRC)
 frozen={SRC:sha(SRC),acceptance:sha(acceptance)}
 im=Image.open(SRC).convert('RGBA');mask=np.asarray(im)[...,3]>=128
 # Anatomical observation, not a hard skull ruler. Points remain on complete source coordinate page.
 points={'eye':[936,545],'nose_tip':[1012,540], 'chin_proxy':[936,619],
  'near_hip_proxy':[590,719],'near_knee_proxy':[631,800],'near_ankle_proxy':[491,903],
  'far_hip_occluded_proxy':[809,774],'far_knee_proxy':[838,807],'far_ankle_proxy':[801,891],
  'back_ramp_rear':[557,561],'back_ramp_front':[731,465]}
 feet=[dict(name='near_lighter_rear_LEFT',window_x=[430,641],sole_probe_y=947,claw_search_xyxy=[530,914,646,964]),
       dict(name='far_darker_front_RIGHT',window_x=[770,975],sole_probe_y=941,claw_search_xyxy=[880,909,976,964])]
 for f in feet:
  y=f['sole_probe_y'];l,r=f['window_x'];xs=np.flatnonzero(mask[y,l:r])+l
  f['solid_row_endpoints']=[int(xs.min()),int(xs.max())] if xs.size else None
  x0,y0,x1,y1=f['claw_search_xyxy'];ys=np.flatnonzero(mask[y0:y1,x0:x1].any(axis=1))+y0
  f['lowest_visible_claw_or_outline_y']=int(ys.max())
 bg=Image.new('RGBA',im.size,'#242934');bg.alpha_composite(im);d=ImageDraw.Draw(bg)
 for x in range(0,1024,128):d.line((x,0,x,1023),fill='#555b66');d.text((x+3,3),str(x),fill='white')
 for y in range(128,1024,128):d.line((0,y,1023,y),fill='#555b66');d.text((3,y+3),str(y),fill='white')
 for name,(x,y) in points.items():
  d.ellipse((x-3,y-3,x+3,y+3),fill='#ff6582');d.text((max(5,x-150),y-16),name,fill='white')
 for f in feet:
  y=f['sole_probe_y'];l,r=f['window_x'];d.line((l,y,r,y),fill='#6bffd1',width=2)
 page=Image.new('RGB',(768,768),'#242934');page.paste(bg.convert('RGB').resize((720,720),Image.Resampling.LANCZOS),(24,32))
 ImageDraw.Draw(page).text((8,8),'07 FULL SOURCE / 128px grid / pink = proxy points, green = sole probes',fill='white')
 page.save(OUT/'source-full-coordinate-points.jpg',quality=80,optimize=True)
 # Same full-image transform as accepted tail/palm tool. No local image mask or limb operation.
 down=forge.binarize_alpha(im.copy());down=forge._kcentroid_downscale(down,256,256);forge.binarize_alpha(down)
 palette=ROOT/'content/fighters/gomora/palette.json'
 with forge.palette_mode('rgb'):forge.apply_palette(down,read(palette)['colors'])
 root=[700,947];quarter=[int(math.floor(v/4+.5)) for v in root];origin=[256-quarter[0],304-quarter[1]]
 native=Image.new('RGBA',(512,320));native.paste(down,tuple(origin))
 assert np.sum(np.asarray(native)[...,3]>0)==np.sum(np.asarray(down)[...,3]>0)
 native.save(OUT/'phase-07.png')
 mp=ROOT/'assets/fighters/gomora/animations/manifest.json';manifest=read(mp);clip=manifest['clips']['idle']
 atlas=ROOT/clip['texture'].removeprefix('res://');x,y,w,h=clip['rects'][0]
 idle=Image.open(atlas).convert('RGBA').crop((x,y,x+w,y+h));assert idle.size==(512,320)
 compare=Image.new('RGB',(768,544),'#242934');d=ImageDraw.Draw(compare)
 for j,color in enumerate(['#242934','#d6d4c9']):
  top=j*272;d.rectangle((0,top,767,top+271),fill=color)
  for i,(label,f) in enumerate([('IDLE actual installed frame0',idle),('07 same scale 1/4, prototype',native)]):
   d.text((i*384+8,top+8),label,fill='white' if j==0 else '#242934')
   f=f.resize((384,240),Image.Resampling.NEAREST);compare.paste(f,(i*384,top+28),f)
   d.line((i*384,top+256,i*384+383,top+256),fill='#af6993')
 compare.save(OUT/'idle-07-full-cells-dark-light.jpg',quality=80,optimize=True)
 # Only auxiliary eye->nasal-tip ruler; ear horns obscure long skull ruler here.
 ruler=runpy.run_path(str(ROOT/'tools/rebuild/gomora/gomora_head_v2.py'))
 ref=ruler['reference']();eye=ruler['eye'](im,hint=(936,545))
 eye_point=eye['center'] if eye else points['eye'];length=math.dist(eye_point,points['nose_tip'])/4
 area=int(np.sum(np.asarray(native)[...,3]>0));idlearea=int(np.sum(np.asarray(idle)[...,3]>0))
 result=dict(source=rec(SRC),root_acceptance=rec(acceptance),backend=forge.backend_info(),palette=rec(palette),
  whole_image_only=True,common_scale=[1,4],cell=[512,320],anchor=[256,304],
  registration_root_source=root,root_reason='两足之间约x700，近侧宽足底约y947；整图平移，脚爪可低于宽足底数像素。后续相须核相同支撑解剖点，不能仅逐帧bbox最低点。',
  quarter_root=quarter,paste_origin=origin,native=rec(OUT/'phase-07.png'),native_bbox=native.getbbox(),
  feet=feet,points=points,head_auxiliary=dict(eye=eye_point,nasal_tip=points['nose_tip'],native_length=length,
    legacy_reference=ref,deviation_percent=100*(length/ref['length']-1),strict_skull_ruler_passed=False,
    limitation='眼鼻辅尺仅代理；本相双大耳角遮挡颅顶，未得到不含角的长颅尺，不能据辅尺宣布严格尺寸通过。'),
  torso_read='屈髋双膝弯曲，近侧较亮腿在画面LEFT/后方，远侧较暗腿在RIGHT/前方；完整两臂、胸髋共同俯身。头角高点不是颅顶。',
  back_receiving_surface=dict(source_observed_ramp=[[557,561],[731,465]],
    limitation='上背斜面真实可见；07是负重深相而非04捕获，不能拿07读点直接安装04捕获框，尚无受方接触验证。'),
  silhouette_area=area,idle=dict(manifest=rec(mp),atlas=rec(atlas),area=idlearea),
  sqrt_area_ratio=math.sqrt(area/idlearea),area_fitting_used=False,strict_size_passed=False,
  runtime_installed=False,godot_run=False,complete_action_accepted=False)
 for p,digest in frozen.items():assert sha(p)==digest
 for p in OUT.glob('*.jpg'):assert Image.open(p).width<=768 and p.stat().st_size<=150000
 save(OUT/'first07-readpoints-and-prototype.json',result)
 print(json.dumps(dict(report=str(OUT),head_aux_native=length,area_ratio=result['sqrt_area_ratio']),ensure_ascii=False))
if __name__=='__main__':main()

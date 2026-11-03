"""05根接源的宽足底/髋读点与整图1/4原型，不改产品。"""
from pathlib import Path
import json,hashlib,math
import numpy as np
from PIL import Image,ImageDraw
import three_key_prototype as shared
ROOT=shared.ROOT
OUT=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-phase05-prototype-v1'
def main():
 assert not OUT.exists();OUT.mkdir()
 source=shared.ART/'phase-05/request-001/candidate.png';gate_path=source.with_name('root-actual-source-review-v1.json');gate=shared.read(gate_path)
 assert gate['accepted_for_whole_action_processing'] and gate['source']['sha256']==shared.sha(source)
 frozen={source:shared.sha(source),gate_path:shared.sha(gate_path)}
 im=Image.open(source).convert('RGBA');mask=np.asarray(im)[...,3]>=128
 feet=[dict(name='near_light_LEFT_rear',x=[425,645],sole_y=958),dict(name='far_dark_RIGHT_front',x=[765,966],sole_y=948)]
 points=dict(near_hip_proxy=[600,735],near_knee_proxy=[632,807],near_ankle_proxy=[487,919],
  near_shoulder_proxy=[675,551],eye=[921,487],nasal_tip=[1007,467],chin_proxy=[926,559],back_rear=[529,563],back_front=[707,424])
 for f in feet:
  l,r=f['x'];y=f['sole_y'];xs=np.flatnonzero(mask[y,l:r])+l;ys=np.flatnonzero(mask[y:y+24,l:r].any(axis=1))+y
  f['solid_row_endpoints']=[int(xs.min()),int(xs.max())];f['lowest_claw_or_outline_y']=int(ys.max())
 bg=Image.new('RGBA',(1024,1024),'#242934');bg.alpha_composite(im);d=ImageDraw.Draw(bg)
 for v in range(0,1024,128):
  d.line((v,0,v,1023),fill='#535963');d.text((v+3,3),str(v),fill='white')
  if v:d.line((0,v,1023,v),fill='#535963');d.text((3,v+3),str(v),fill='white')
 for name,(x,y) in points.items():
  d.ellipse((x-3,y-3,x+3,y+3),fill='#ff6780');d.text((max(2,x-150),y-14),name,fill='white')
 for f in feet:d.line((f['x'][0],f['sole_y'],f['x'][1],f['sole_y']),fill='#63f7c9',width=2)
 page=Image.new('RGB',(768,768),'#242934');page.paste(bg.convert('RGB').resize((720,720),Image.Resampling.LANCZOS),(24,32))
 ImageDraw.Draw(page).text((6,7),'05 FULL SOURCE / wide soles and anatomical proxy points',fill='white')
 page.save(OUT/'phase-05-full-source-points.jpg',quality=80,optimize=True)
 down=shared.forge.binarize_alpha(im.copy());down=shared.forge._kcentroid_downscale(down,256,256);shared.forge.binarize_alpha(down)
 palette=ROOT/'content/fighters/gomora/palette.json'
 with shared.forge.palette_mode('rgb'):shared.forge.apply_palette(down,shared.read(palette)['colors'])
 root=[700,958];quarter=[int(math.floor(v/4+.5)) for v in root];origin=[256-quarter[0],304-quarter[1]]
 native=Image.new('RGBA',(512,320));native.paste(down,tuple(origin))
 assert np.sum(np.asarray(native)[...,3]>0)==np.sum(np.asarray(down)[...,3]>0)
 path=OUT/'phase-05.png';native.save(path)
 previous=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-four-key-prototype-v2'
 f04=Image.open(previous/'native/04.png').convert('RGBA');f07=Image.open(previous/'native/07.png').convert('RGBA')
 shared.full_page([f04,native,f07],['04 RECEIVE','05 ABSORB','07 LOW LOAD'],OUT/'04-05-07-full-cells-one-row-dark-light.jpg')
 shared.pair_page(f04,native,['04 RECEIVE','05 ABSORB'],OUT/'04-05-full-cells-dark-light.jpg')
 shared.pair_page(native,f07,['05 ABSORB','07 LOW LOAD'],OUT/'05-07-full-cells-dark-light.jpg')
 for p in OUT.glob('*.jpg'):assert Image.open(p).width<=768 and p.stat().st_size<=150000
 for p,digest in frozen.items():assert shared.sha(p)==digest
 shared.save(OUT/'phase05-readpoints-and-prototype.json',dict(source=shared.rec(source),root_acceptance=shared.rec(gate_path),
  source_points=points,feet=feet,common_scale=[1,4],cell=[512,320],anchor=[256,304],root=root,quarter_root=quarter,
  paste_origin=origin,native=shared.rec(path),native_bbox=native.getbbox(),near_hip_proxy_height=304-(735/4+origin[1]),
  note='腰髋为皮肤遮挡下的人工代理，不是长骨尺。足底958/948与爪尖974/964分开；不把脚爪最低点当平足底。',
  actual_palette_mode='rgb',whole_image_only=True,strict_size_passed=False,full_motion_accepted=False,runtime_installed=False,godot_run=False))
 print(json.dumps(dict(report=str(OUT),root=root),ensure_ascii=False))
if __name__=='__main__':main()

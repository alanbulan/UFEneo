"""只读06/08整源及可能重排06→07→09→08→11，不签顺序、不改源/产品。"""
from pathlib import Path
import math,json
import numpy as np
from PIL import Image,ImageDraw
import three_key_prototype as shared
ROOT=shared.ROOT
OUT=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-06-08-order-prototype-v1'
SPECS={
6:dict(expected_sha='e95794efb7b1407b87a76bc3b11c6adee46d36ee97e5047116b6e9ab3b790061',root=[712,912],
 feet=[dict(name='near_light_LEFT_rear',x=[420,628],sole_y=912),dict(name='far_dark_RIGHT_front',x=[785,987],sole_y=912)],
 points=dict(near_hip_proxy=[606,704],near_shoulder_proxy=[701,540],near_knee_proxy=[628,773],near_ankle_proxy=[484,878],eye=[939,487],nasal_tip=[1011,475],chin_proxy=[940,563],back_rear=[529,533],back_front=[738,406])),
8:dict(expected_sha='6f06c51dc0ef69692dde9e63f19229fd53024763da8316342504e98941eb4813',root=[720,920],
 feet=[dict(name='near_light_LEFT_rear',x=[445,678],sole_y=920),dict(name='far_dark_RIGHT_front',x=[770,980],sole_y=914)],
 points=dict(near_hip_proxy=[611,625],near_shoulder_proxy=[670,409],near_knee_proxy=[633,728],near_ankle_proxy=[511,874],eye=[907,307],nasal_tip=[997,290],chin_proxy=[908,390],back_rear=[526,426],back_front=[682,256]))}
def main():
 assert not OUT.exists();OUT.mkdir();(OUT/'native').mkdir();rows=[];frozen={};frames={}
 palette=ROOT/'content/fighters/gomora/palette.json';colors=shared.read(palette)['colors'];frozen[palette]=shared.sha(palette)
 for phase,spec in SPECS.items():
  source=shared.ART/f'phase-{phase:02d}/request-001/candidate.png';assert shared.sha(source)==spec['expected_sha'];frozen[source]=shared.sha(source)
  gate=source.with_name('root-actual-source-review-v1.json')
  if phase==6:
   assert shared.read(gate)['accepted_for_whole_action_processing'] is True;frozen[gate]=shared.sha(gate)
  im=Image.open(source).convert('RGBA');assert im.size==(1024,1024);mask=np.asarray(im)[...,3]>=128
  assert not(mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any())
  feet=[]
  for f in spec['feet']:
   l,r=f['x'];y=f['sole_y'];xs=np.flatnonzero(mask[y,l:r])+l;ys=np.flatnonzero(mask[y:y+24,l:r].any(axis=1))+y
   feet.append(dict(**f,solid_row_endpoints=[int(xs.min()),int(xs.max())],lowest_claw_or_outline_y=int(ys.max())))
  bg=Image.new('RGBA',(1024,1024),'#242934');bg.alpha_composite(im);d=ImageDraw.Draw(bg)
  for v in range(0,1024,128):
   d.line((v,0,v,1023),fill='#535963');d.text((v+3,3),str(v),fill='white')
   if v:d.line((0,v,1023,v),fill='#535963');d.text((3,v+3),str(v),fill='white')
  for name,(x,y) in spec['points'].items():
   d.ellipse((x-3,y-3,x+3,y+3),fill='#ff6780');d.text((max(2,x-150),y-14),name,fill='white')
  for f in feet:d.line((f['x'][0],f['sole_y'],f['x'][1],f['sole_y']),fill='#63f7c9',width=2)
  page=Image.new('RGB',(768,768),'#242934');page.paste(bg.convert('RGB').resize((720,720),Image.Resampling.LANCZOS),(24,32))
  ImageDraw.Draw(page).text((6,7),f'{phase:02d} FULL SOURCE / complete feet / proxies; no order approval',fill='white')
  page.save(OUT/f'phase-{phase:02d}-full-source-points.jpg',quality=80,optimize=True)
  down=shared.forge.binarize_alpha(im.copy());down=shared.forge._kcentroid_downscale(down,256,256);shared.forge.binarize_alpha(down)
  with shared.forge.palette_mode('rgb'):shared.forge.apply_palette(down,colors)
  quarter=[int(math.floor(v/4+.5)) for v in spec['root']];origin=[256-quarter[0],304-quarter[1]]
  native=Image.new('RGBA',(512,320));native.paste(down,tuple(origin))
  assert np.sum(np.asarray(native)[...,3]>0)==np.sum(np.asarray(down)[...,3]>0)
  path=OUT/f'native/{phase:02d}.png';native.save(path);frames[phase]=native
  npts={k:[v[0]/4+origin[0],v[1]/4+origin[1]] for k,v in spec['points'].items()}
  rows.append(dict(source_phase=phase,source=shared.rec(source),source_request_unchanged=True,
   root_source_acceptance=shared.rec(gate) if phase==6 else None,
   root_instruction_for_08='根允许08完整源离线共同1/4比较，暂不接受其原整动作位置；本工具不把比较权限写成动作顺序接受。',
   source_points=spec['points'],feet=feet,root=spec['root'],quarter_root=quarter,paste_origin=origin,
   native=shared.rec(path),native_bbox=native.getbbox(),native_points=npts,
   near_hip_proxy_height=304-npts['near_hip_proxy'][1],near_shoulder_proxy_height=304-npts['near_shoulder_proxy'][1],
   shoulder_hip_proxy_angle_from_vertical_degrees=math.degrees(math.atan2(abs(npts['near_shoulder_proxy'][0]-npts['near_hip_proxy'][0]),npts['near_hip_proxy'][1]-npts['near_shoulder_proxy'][1])),
   whole_image_only=True,common_scale=[1,4],strict_size_passed=False,runtime_installed=False,order_accepted=False))
 prior=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-four-key-prototype-v2';old=shared.read(prior/'four-key-common-scale-prototype.json')
 for phase in [7,9,11]:
  row=next(r for r in old['phases'] if r['phase']==phase);p=ROOT/row['native']['path'];assert shared.sha(p)==row['native']['sha256'];frozen[p]=shared.sha(p)
  frames[phase]=Image.open(p).convert('RGBA');npts=row['native_points'];hip=npts['near_hip_proxy'];shoulder=npts['near_shoulder_proxy']
  rows.append(dict(source_phase=phase,source=row['source'],root_source_acceptance=row['root_acceptance'],native=row['native'],
   root=row['root'],native_bbox=row['native_bbox'],native_points=npts,
   near_hip_proxy_height=304-hip[1],near_shoulder_proxy_height=304-shoulder[1],
   shoulder_hip_proxy_angle_from_vertical_degrees=math.degrees(math.atan2(abs(shoulder[0]-hip[0]),hip[1]-shoulder[1])),
   strict_size_passed=False,runtime_installed=False,order_accepted=False))
 order=[6,7,9,8,11]
 shared.full_page([frames[p] for p in order],[f'SRC {p:02d}' for p in order],OUT/'06-07-09-08-11-full-cells-one-row-dark-light.jpg')
 for a,b in zip(order,order[1:]):shared.pair_page(frames[a],frames[b],[f'SOURCE {a:02d}',f'SOURCE {b:02d}'],OUT/f'{a:02d}-{b:02d}-full-cells-dark-light.jpg')
 # Original source-phase order retained for comparison; never rewrite request phase names or authored raw ticks.
 shared.pair_page(frames[7],frames[8],['SOURCE 07','SOURCE 08 original'],OUT/'07-08-original-order-full-cells-dark-light.jpg')
 shared.pair_page(frames[8],frames[9],['SOURCE 08 original','SOURCE 09'],OUT/'08-09-original-order-full-cells-dark-light.jpg')
 for p in OUT.glob('*.jpg'):assert Image.open(p).width<=768 and p.stat().st_size<=150000
 for p,digest in frozen.items():assert shared.sha(p)==digest
 ordered=[next(r for r in rows if r['source_phase']==phase) for phase in order]
 shared.save(OUT/'06-08-readpoints-and-order-prototype.json',dict(phases=ordered,preview_order=order,common_scale=[1,4],cell=[512,320],anchor=[256,304],
  actual_palette_mode='rgb',whole_image_only=True,local_fit=False,area_fit=False,source_request_numbers_preserved=True,
  strict_skull_ruler_passed=False,full_order_accepted=False,runtime_installed=False,godot_run=False,post_submitted=False))
 shared.save(OUT/'proposed-selection-not-approved.json',dict(status='preview_only_not_accepted',
  preview_sequence=[dict(preview_rank=i+1,source_phase=phase,source=next(r for r in rows if r['source_phase']==phase)['source'],
   original_request_raw_ticks=[phase*4,phase*4+3],selected_runtime_raw_ticks=None) for i,phase in enumerate(order)],
  remaining_source10_pending_context=True,root_approval_required_for_runtime_selection=True,
  note='仅把完整整相在预览中按姿态候选重排。源相号/原brief/原请求raw tick一律保全，未设置新运行槽位。'))
 print(json.dumps(dict(report=str(OUT),preview_order=order,order_approved=False),ensure_ascii=False))
if __name__=='__main__':main()

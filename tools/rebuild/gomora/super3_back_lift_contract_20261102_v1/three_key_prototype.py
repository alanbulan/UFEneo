"""根接04/07/09完整源共同1/4整图候选。只写报告。"""
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
from PIL import Image,ImageDraw
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/rebuild/shared'))
import forge_backend as forge
ART=ROOT/'art/fighters/gomora/stage4/super3-back-lift-20261102-v1'
OUT=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-three-key-prototype-v1'
SPECS={
4:dict(root=[712,863],feet=[dict(name='near_light_LEFT_rear',x=[470,676],sole_y=862),dict(name='far_dark_RIGHT_front',x=[750,947],sole_y=856)],
 points=dict(near_hip_proxy=[623,623],near_knee_proxy=[651,709],near_ankle_proxy=[521,815],near_shoulder_proxy=[705,449],eye=[940,410],nasal_tip=[1010,401],chin_proxy=[940,490],back_rear=[557,435],back_front=[737,331])),
7:dict(root=[700,947],feet=[dict(name='near_light_LEFT_rear',x=[430,646],sole_y=947),dict(name='far_dark_RIGHT_front',x=[770,976],sole_y=941)],
 points=dict(near_hip_proxy=[590,719],near_knee_proxy=[631,800],near_ankle_proxy=[491,903],near_shoulder_proxy=[697,583],eye=[935,544],nasal_tip=[1012,540],chin_proxy=[936,619],back_rear=[557,561],back_front=[731,465])),
9:dict(root=[724,894],feet=[dict(name='near_light_LEFT_rear',x=[470,690],sole_y=894),dict(name='far_dark_RIGHT_front',x=[774,973],sole_y=892)],
 points=dict(near_hip_proxy=[610,636],near_knee_proxy=[639,727],near_ankle_proxy=[536,842],near_shoulder_proxy=[683,411],eye=[876,336],nasal_tip=[959,319],chin_proxy=[879,407],back_rear=[535,424],back_front=[684,287]))}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,d):
 with p.open('x',encoding='utf8') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def full_page(frames,labels,path):
 # Each column is an ENTIRE 512x320 cell; common review scale across every cell.
 width=768//len(frames);height=width*320//512;row_height=height+32
 page=Image.new('RGB',(768,row_height*2),'#242934');d=ImageDraw.Draw(page)
 for j,color in enumerate(['#242934','#d6d4c9']):
  top=j*row_height;d.rectangle((0,top,767,top+row_height-1),fill=color)
  for i,(frame,label) in enumerate(zip(frames,labels)):
   x=i*width;d.text((x+5,top+5),label+' / full cell',fill='white' if j==0 else '#242934')
   small=frame.resize((width,height),Image.Resampling.NEAREST);page.paste(small,(x,top+24),small)
   ground=top+24+304*height//320;d.line((x,ground,x+width-1,ground),fill='#aa6699')
 page.save(path,quality=80,optimize=True)
def pair_page(a,b,labels,path):
 page=Image.new('RGB',(768,544),'#242934');d=ImageDraw.Draw(page)
 for j,color in enumerate(['#242934','#d6d4c9']):
  top=j*272;d.rectangle((0,top,767,top+271),fill=color)
  for i,(im,label) in enumerate(zip([a,b],labels)):
   x=i*384;d.text((x+7,top+7),label+' / whole cell 3/4',fill='white' if j==0 else '#242934')
   small=im.resize((384,240),Image.Resampling.NEAREST);page.paste(small,(x,top+28),small)
   d.line((x,top+256,x+383,top+256),fill='#aa6699')
 page.save(path,quality=80,optimize=True)
def main(out_override=None,specs_override=None):
 global OUT
 if out_override is not None:OUT=out_override
 specs=SPECS if specs_override is None else specs_override
 assert not OUT.exists();OUT.mkdir();(OUT/'native').mkdir()
 palette=ROOT/'content/fighters/gomora/palette.json';colors=read(palette)['colors'];frozen={palette:sha(palette)}
 mp=ROOT/'assets/fighters/gomora/animations/manifest.json';clip=read(mp)['clips']['idle'];atlas=ROOT/clip['texture'].removeprefix('res://')
 x,y,w,h=clip['rects'][0];idle=Image.open(atlas).convert('RGBA').crop((x,y,x+w,y+h));idle_area=int(np.sum(np.asarray(idle)[...,3]>0))
 rows=[];frames=[]
 for phase,spec in specs.items():
  source=ART/f'phase-{phase:02d}/request-001/candidate.png';gate_path=source.with_name('root-actual-source-review-v1.json');gate=read(gate_path)
  assert gate['accepted_for_whole_action_processing'] and gate['source']['sha256']==sha(source)
  frozen[source]=sha(source);frozen[gate_path]=sha(gate_path)
  im=Image.open(source).convert('RGBA');assert im.size==(1024,1024);mask=np.asarray(im)[...,3]>=128
  assert not(mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any())
  feet=[]
  for f in spec['feet']:
   l,r=f['x'];y=f['sole_y'];xs=np.flatnonzero(mask[y,l:r])+l
   ys=np.flatnonzero(mask[y:y+24,l:r].any(axis=1))+y
   feet.append(dict(**f,solid_row_endpoints=[int(xs.min()),int(xs.max())],lowest_foot_claw_or_outline_y=int(ys.max())))
  bg=Image.new('RGBA',(1024,1024),'#242934');bg.alpha_composite(im);d=ImageDraw.Draw(bg)
  for v in range(0,1024,128):
   d.line((v,0,v,1023),fill='#535963');d.text((v+3,3),str(v),fill='white')
   if v:d.line((0,v,1023,v),fill='#535963');d.text((3,v+3),str(v),fill='white')
  for name,(x,y) in spec['points'].items():
   d.ellipse((x-3,y-3,x+3,y+3),fill='#ff6780');d.text((max(2,x-150),y-14),name,fill='white')
  for f in feet:d.line((f['x'][0],f['sole_y'],f['x'][1],f['sole_y']),fill='#63f7c9',width=2)
  p=Image.new('RGB',(768,768),'#242934');p.paste(bg.convert('RGB').resize((720,720),Image.Resampling.LANCZOS),(24,32))
  ImageDraw.Draw(p).text((7,7),f'{phase:02d} FULL SOURCE / 128px grid / proxies, no hard skull measurement',fill='white')
  p.save(OUT/f'phase-{phase:02d}-full-source-points.jpg',quality=80,optimize=True)
  down=forge.binarize_alpha(im.copy());down=forge._kcentroid_downscale(down,256,256);forge.binarize_alpha(down)
  with forge.palette_mode('rgb'):forge.apply_palette(down,colors)
  quarter=[int(math.floor(v/4+.5)) for v in spec['root']];origin=[256-quarter[0],304-quarter[1]]
  native=Image.new('RGBA',(512,320));native.paste(down,tuple(origin))
  assert np.sum(np.asarray(native)[...,3]>0)==np.sum(np.asarray(down)[...,3]>0)
  path=OUT/f'native/{phase:02d}.png';native.save(path);frames.append(native)
  native_points={k:[round(v[0]/4+origin[0],3),round(v[1]/4+origin[1],3)] for k,v in spec['points'].items()}
  rows.append(dict(phase=phase,source=rec(source),root_acceptance=rec(gate_path),source_points=spec['points'],feet=feet,
   root=spec['root'],quarter_root=quarter,paste_origin=origin,native=rec(path),native_bbox=native.getbbox(),native_points=native_points,
   near_hip_proxy_height=304-native_points['near_hip_proxy'][1],
   sqrt_area_ratio_to_actual_idle=math.sqrt(int(np.sum(np.asarray(native)[...,3]>0))/idle_area),
   eye_nasal_aux_native=math.dist(spec['points']['eye'],spec['points']['nasal_tip'])/4,
   strict_size_passed=False,root_support_continuity_passed=False,runtime_installed=False))
 names={4:'04 RECEIVE',7:'07 LOW LOAD',9:'09 BACK RISE',11:'11 RELEASE'}
 sequence='-'.join(f'{p:02d}' for p in specs)
 full_page(frames,[names[p] for p in specs],OUT/f'{sequence}-full-cells-one-row-dark-light.jpg')
 pair_page(frames[0],frames[1],['04 RECEIVE','07 LOW LOAD'],OUT/'04-07-full-cells-dark-light.jpg')
 pair_page(frames[1],frames[2],['07 LOW LOAD','09 BACK RISE'],OUT/'07-09-full-cells-dark-light.jpg')
 pair_page(idle,frames[2],['IDLE actual installed','09 BACK RISE'],OUT/'idle-09-full-cells-dark-light.jpg')
 if 11 in specs:
  pair_page(frames[2],frames[3],['09 BACK RISE','11 RELEASE'],OUT/'09-11-full-cells-dark-light.jpg')
  pair_page(idle,frames[3],['IDLE actual installed','11 RELEASE'],OUT/'idle-11-full-cells-dark-light.jpg')
 for p in OUT.glob('*.jpg'):assert p.stat().st_size<=150000 and Image.open(p).width<=768
 for p,digest in frozen.items():assert sha(p)==digest
 name='four-key-common-scale-prototype.json' if 11 in specs else 'three-key-common-scale-prototype.json'
 save(OUT/name,dict(phases=rows,common_scale=[1,4],cell=[512,320],anchor=[256,304],
  actual_palette_mode='rgb',backend=forge.backend_info(),palette=rec(palette),idle_manifest=rec(mp),idle_atlas=rec(atlas),
  whole_image_only=True,source_alpha_not_rewritten=True,source_scale_per_phase_fitted=False,area_fitting_used=False,
  root_policy='整图按两足之间支撑根平移。宽足底和爪尖分开，髋为被皮肤遮挡的代理点；不能由同比例格直接宣布足底无滑动。',
  strict_size_passed=False,super3_accepted=False,godot_run=False,post_submitted=False,runtime_installed=False))
 print(json.dumps(dict(report=str(OUT),phases=[r['phase'] for r in rows],near_hip_proxy_heights=[r['near_hip_proxy_height'] for r in rows]),ensure_ascii=False))
if __name__=='__main__':main()

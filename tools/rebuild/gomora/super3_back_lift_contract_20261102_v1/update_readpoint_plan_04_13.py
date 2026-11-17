"""只整理04–13新增实际读点与未齐18相计划；不跑统一注册、不写产品。"""
from pathlib import Path
import math,json
import numpy as np
from PIL import Image,ImageDraw
import three_key_prototype as shared
ROOT=shared.ROOT
OUT=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-04-13-readpoint-plan-v2'
SPECS={
10:dict(root=[724,928],feet=[dict(name='near_light_LEFT_rear',x=[450,679],sole_y=928),dict(name='far_dark_RIGHT_front',x=[776,991],sole_y=922)],
 points=dict(near_hip_proxy=[616,644],near_shoulder_proxy=[678,382],near_knee_proxy=[633,752],near_ankle_proxy=[517,881],eye=[891,271],nasal_tip=[982,251],chin_proxy=[898,358],back_rear=[532,428],back_front=[655,263])),
12:dict(root=[700,900],feet=[dict(name='near_light_LEFT_rear',x=[430,641],sole_y=900),dict(name='far_dark_RIGHT_front',x=[755,955],sole_y=896)],
 points=dict(near_hip_proxy=[608,673],near_shoulder_proxy=[713,468],near_knee_proxy=[628,755],near_ankle_proxy=[491,853],eye=[932,415],nasal_tip=[1010,413],chin_proxy=[939,495],back_rear=[538,460],back_front=[733,342])),
13:dict(root=[700,902],feet=[dict(name='near_light_LEFT_rear',x=[430,653],sole_y=902),dict(name='far_dark_RIGHT_front',x=[758,956],sole_y=898)],
 points=dict(near_hip_proxy=[600,647],near_shoulder_proxy=[682,451],near_knee_proxy=[624,746],near_ankle_proxy=[493,857],eye=[919,402],nasal_tip=[999,398],chin_proxy=[920,479],back_rear=[527,438],back_front=[709,321]))}
def main():
 if OUT.exists():assert not any(OUT.iterdir()),'不覆盖已存在读点报告'
 else:OUT.mkdir()
 frozen={};prior={};records=[]
 four_path=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-four-key-prototype-v2/four-key-common-scale-prototype.json'
 for row in shared.read(four_path)['phases']:
  prior[row['phase']]=dict(source=row['source'],root=row['root'],source_points=row['source_points'],feet=row['feet'],readpoint_provenance=shared.rec(four_path))
 five_path=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-phase05-prototype-v1/phase05-readpoints-and-prototype.json';five=shared.read(five_path)
 prior[5]=dict(source=five['source'],root=five['root'],source_points=five['source_points'],feet=five['feet'],readpoint_provenance=shared.rec(five_path))
 six_path=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-06-08-order-prototype-v1/06-08-readpoints-and-order-prototype.json'
 for row in shared.read(six_path)['phases']:
  if row['source_phase'] in [6,8]:prior[row['source_phase']]=dict(source=row['source'],root=row['root'],source_points=row['source_points'],feet=row['feet'],readpoint_provenance=shared.rec(six_path))
 for phase in range(4,14):
  request_dir=shared.ART/f'phase-{phase:02d}/request-001';gate_path=request_dir/'root-actual-source-review-v1.json'
  gate=shared.read(gate_path) if gate_path.exists() else None
  accepted=bool(gate and gate.get('accepted_for_whole_action_processing') is True)
  source=ROOT/gate['source']['path'] if accepted else request_dir/'candidate.png'
  assert source.exists()
  if accepted:assert shared.sha(source)==gate['source']['sha256'];frozen[gate_path]=shared.sha(gate_path)
  frozen[source]=shared.sha(source);im=Image.open(source).convert('RGBA');arr=np.asarray(im);mask=arr[...,3]>=128
  assert im.size==(1024,1024) and not(mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any())
  if phase in SPECS:
   spec=SPECS[phase].copy();spec['points']={k:v for k,v in spec['points'].items() if not k.startswith('back_')};feet=[]
   for f in spec['feet']:
    l,r=f['x'];y=f['sole_y'];xs=np.flatnonzero(mask[y,l:r])+l;ys=np.flatnonzero(mask[y:y+24,l:r].any(axis=1))+y
    feet.append(dict(**f,solid_row_endpoints=[int(xs.min()),int(xs.max())],lowest_claw_or_outline_y=int(ys.max())))
   data=dict(root=spec['root'],source_points=spec['points'],feet=feet,readpoint_provenance=None)
   bg=Image.new('RGBA',(1024,1024),'#242934');bg.alpha_composite(im);d=ImageDraw.Draw(bg)
   for v in range(0,1024,128):
    d.line((v,0,v,1023),fill='#535963');d.text((v+3,3),str(v),fill='white')
    if v:d.line((0,v,1023,v),fill='#535963');d.text((3,v+3),str(v),fill='white')
   for name,(x,y) in spec['points'].items():
    d.ellipse((x-3,y-3,x+3,y+3),fill='#ff6780');d.text((max(2,x-150),y-14),name,fill='white')
   for f in feet:d.line((f['x'][0],f['sole_y'],f['x'][1],f['sole_y']),fill='#63f7c9',width=2)
   page=Image.new('RGB',(768,768),'#242934');page.paste(bg.convert('RGB').resize((720,720),Image.Resampling.LANCZOS),(24,32))
   ImageDraw.Draw(page).text((6,7),f'{phase:02d} FULL SOURCE / actual foot probes + body proxies / no registration run',fill='white')
   path=OUT/f'phase-{phase:02d}-full-source-readpoints.jpg';page.save(path,quality=80,optimize=True)
   assert path.stat().st_size<=150000;data['coordinate_page']=shared.rec(path)
  else:
   data=prior[phase];assert data['source']['sha256']==shared.sha(source),'旧读点与根当前源不符，不能沿用'
   frozen[ROOT/data['readpoint_provenance']['path']]=data['readpoint_provenance']['sha256']
  data={k:v for k,v in data.items() if k!='source'}
  data['source_points']={k:v for k,v in data['source_points'].items() if not k.startswith('back_')}
  quarter=[int(math.floor(v/4+.5)) for v in data['root']];origin=[256-quarter[0],304-quarter[1]]
  npts={k:[v[0]/4+origin[0],v[1]/4+origin[1]] for k,v in data['source_points'].items()}
  hip=npts['near_hip_proxy'];shoulder=npts.get('near_shoulder_proxy')
  records.append(dict(source_phase=phase,request=1,source=shared.rec(source),request_brief=shared.rec(request_dir/'brief.json'),
   root_acceptance=shared.rec(gate_path) if accepted else None,root_accepted_for_processing=accepted,
   original_in_alpha_quarantine='rejected' in source.parts,original_alpha_range=[int(arr[...,3].min()),int(arr[...,3].max())],
   alpha128_bbox=Image.fromarray(mask).getbbox(),**data,quarter_root=quarter,proposed_paste_origin=origin,proposed_native_points=npts,
   near_hip_proxy_height=304-hip[1],near_shoulder_proxy_height=304-shoulder[1] if shoulder else None,
   shoulder_hip_proxy_angle_from_vertical_degrees=math.degrees(math.atan2(abs(shoulder[0]-hip[0]),hip[1]-shoulder[1])) if shoulder else None,
   source_to_native_scale=[1,4],new_native_png_created=False,strict_size_passed=False))
 shared.save(OUT/'04-13-readpoints-candidate.json',dict(records=records,common_scale=[1,4],cell=[512,320],anchor=[256,304],
  preserved_suggested_lift_source_order=[7,9,8,10,11],whole_source_coordinate_reading_only=True,
  hip_shoulder_uncertainty_source_px=16,not_a_skull_or_bone_length_ruler=True,full18_registration_executed=False,
  final_runtime_order_accepted=False,runtime_installed=False,godot_run=False,post_submitted=False))
 plan_rows=[];lookup={r['source_phase']:r for r in records}
 for phase in range(18):
  row=lookup.get(phase)
  plan_rows.append(dict(phase=phase,request=1,source=row['source'] if row else None,root_acceptance=row['root_acceptance'] if row else None,
   registration_root_source=row['root'] if row else None,
   support_readpoint_note='完整源宽足底与爪尖分开，髋肩是皮肤遮挡下的代理；候选根尚待根在18相全链中审核。' if row else None,
   readpoint_candidate=shared.rec(OUT/'04-13-readpoints-candidate.json') if row else None,per_phase_scale=None,area_fit=None))
 shared.save(OUT/'incomplete18-registration-plan-candidate.json',dict(root_all18_sources_accepted=False,
  root_full_action_registration_authorized=False,root_readpoint_plan_accepted=False,root_preview_order_accepted=False,
  common_scale=[1,4],cell=[512,320],anchor=[256,304],output='reports/review/2026-11-02/gomora-super3-back-lift-registration-v1/registered18-v1',
  preview_source_order=[0,1,2,3,4,5,6,7,9,8,10,11,12,13,14,15,16,17],phases=plan_rows,
  original_source_phase_numbers_preserved=True,runtime_slot_mapping_created=False,template_not_runnable=True))
 for p,digest in frozen.items():assert shared.sha(p)==digest
 print(json.dumps(dict(report=str(OUT),new_phases=[10,12,13],root_processing_accepted={r['source_phase']:r['root_accepted_for_processing'] for r in records}),ensure_ascii=False))
if __name__=='__main__':main()

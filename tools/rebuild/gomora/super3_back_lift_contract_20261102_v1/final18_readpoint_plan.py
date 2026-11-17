"""全18完整源足底/髋肩代理读点候选；四执行布尔均保持false，不注册。"""
from pathlib import Path
import json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[4]
ART=ROOT/'art/fighters/gomora/stage4/super3-back-lift-20261102-v1'
OUT=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-full18-readpoint-plan-candidate-v1'
PRIOR=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-04-13-readpoint-plan-v2/04-13-readpoints-candidate.json'
SPECS={
 0:dict(root=[704,918],soles=[918,918],points=dict(near_hip_proxy=[632,650],near_shoulder_proxy=[675,429])),
 1:dict(root=[712,930],soles=[930,920],points=dict(near_hip_proxy=[634,641],near_shoulder_proxy=[667,413])),
 2:dict(root=[692,922],soles=[922,914],points=dict(near_hip_proxy=[630,715],near_shoulder_proxy=[677,517])),
 3:dict(root=[704,930],soles=[930,926],points=dict(near_hip_proxy=[630,713],near_shoulder_proxy=[699,509])),
14:dict(root=[704,942],soles=[942,934],points=dict(near_hip_proxy=[627,680],near_shoulder_proxy=[673,463])),
15:dict(root=[716,912],soles=[912,902],points=dict(near_hip_proxy=[635,634],near_shoulder_proxy=[681,412])),
16:dict(root=[720,926],soles=[926,918],points=dict(near_hip_proxy=[641,634],near_shoulder_proxy=[690,406])),
17:dict(root=[724,934],soles=[934,928],points=dict(near_hip_proxy=[637,663],near_shoulder_proxy=[691,448]))}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,data):
 with p.open('x',encoding='utf8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')

def annotated(im,points,feet,root):
 bg=Image.new('RGBA',im.size,'#242934');bg.alpha_composite(im);d=ImageDraw.Draw(bg)
 for n in range(0,1024,128):
  d.line((n,0,n,1023),fill='#535963');d.text((n+3,3),str(n),fill='white')
  d.line((0,n,1023,n),fill='#535963');d.text((3,n+3),str(n),fill='white')
 for name,(x,y) in points.items():
  if name not in ['near_hip_proxy','near_shoulder_proxy']:continue
  d.ellipse((x-4,y-4,x+4,y+4),fill='#ff6780')
  d.text((max(2,x-180),y-16),name+f' {x},{y}',fill='white')
 for f in feet:
  l,r=f['solid_row_endpoints'];y=f['sole_y'];d.line((l,y,r,y),fill='#63f7c9',width=3)
  d.text((l,y-15),f"sole {y} / claw {f.get('lowest_claw_or_outline_y',f.get('lowest_foot_claw_or_outline_y'))}",fill='#b0ffe5')
 x,y=root;d.line((x-12,y,x+12,y),fill='#ffe26c',width=2);d.line((x,y-12,x,y+12),fill='#ffe26c',width=2)
 d.text((x-50,y+13),f'ROOT {x},{y}',fill='#ffe26c')
 return bg.convert('RGB')

def main():
 assert OUT.exists() and not (OUT/'full18-readpoints-candidate.json').exists()
 prior={r['source_phase']:r for r in read(PRIOR)['records']};records=[];frozen={PRIOR:sha(PRIOR)}
 for phase in range(18):
  rd=ART/f'phase-{phase:02d}/request-001';gp=rd/'root-actual-source-review-v1.json';gate=read(gp)
  assert gate['accepted_for_whole_action_processing'] is True
  source=ROOT/gate['source']['path'];assert sha(source)==gate['source']['sha256']
  frozen[source]=sha(source);frozen[gp]=sha(gp)
  im=Image.open(source).convert('RGBA');arr=np.asarray(im);mask=arr[...,3]>=128
  assert im.size==(1024,1024)
  if phase in SPECS:
   spec=SPECS[phase];feet=[];root=spec['root'];points=spec['points']
   for name,(l,r),y in zip(['near_light_LEFT_rear','far_dark_RIGHT_front'],[(425,685),(750,995)],spec['soles']):
    xs=np.flatnonzero(mask[y,l:r])+l;ys=np.flatnonzero(mask[y:y+32,l:r].any(axis=1))+y
    feet.append(dict(name=name,x=[l,r],sole_y=y,solid_row_endpoints=[int(xs.min()),int(xs.max())],lowest_claw_or_outline_y=int(ys.max())))
   provenance=None
   root_rule='源根x按两只宽足底端点中心的中点取最近4px；y采用近亮后足宽底行，爪尖另记不当脚底。'
  else:
   old=prior[phase];assert old['source']==rec(source)
   root=old['root'];points=old['source_points'];feet=old['feet'];provenance=rec(PRIOR)
   root_rule='保留此前04–13已实际读过的源根/宽底窗，不因新八相而再拟合旧相。'
  assert all(mask[points[name][1],points[name][0]] for name in ['near_hip_proxy','near_shoulder_proxy'] if name in points)
  bg=annotated(im,points,feet,root)
  full=Image.new('RGB',(768,768),'#242934');full.paste(bg.resize((720,720),Image.Resampling.LANCZOS),(24,32))
  ImageDraw.Draw(full).text((6,7),f'{phase:02d} FULL SOURCE / ACTUAL SOLE + HIP-SHOULDER PROXY / CANDIDATE ONLY',fill='white')
  pp=OUT/f'phase-{phase:02d}-full-source-readpoints.jpg';full.save(pp,quality=80,optimize=True)
  foot=Image.new('RGB',(768,542),'#242934');foot.paste(bg.crop((256,512,1024,1024)),(0,30))
  ImageDraw.Draw(foot).text((4,7),f'{phase:02d} NATIVE FOOT READ WINDOW x256..1024 y512..1024 / NOT REGISTERED',fill='white')
  fp=OUT/f'phase-{phase:02d}-foot-readpoints-native.jpg';foot.save(fp,quality=85,optimize=True)
  assert pp.stat().st_size<=150000 and fp.stat().st_size<=150000
  quarter=[int(math.floor(v/4+.5)) for v in root];origin=[256-quarter[0],304-quarter[1]]
  native={k:[v[0]/4+origin[0],v[1]/4+origin[1]] for k,v in points.items()}
  hip=native['near_hip_proxy'];shoulder=native.get('near_shoulder_proxy')
  records.append(dict(source_phase=phase,request=1,source=rec(source),root_acceptance=rec(gp),
   root_accepted_for_processing_observed=True,request_brief=rec(rd/'brief.json'),
   original_in_alpha_quarantine='rejected' in source.parts,original_alpha_range=[int(arr[...,3].min()),int(arr[...,3].max())],
   alpha128_bbox=Image.fromarray(mask).getbbox(),root=root,source_points=points,feet=feet,
   readpoint_provenance=provenance,registration_root_rule=root_rule,
   quarter_root=quarter,proposed_paste_origin=origin,proposed_native_points=native,
   near_hip_proxy_height=304-hip[1],near_shoulder_proxy_height=304-shoulder[1] if shoulder else None,
   coordinate_page=rec(pp),native_foot_read_window=rec(fp),new_native_png_created=False,
   strict_size_passed=False,readpoint_accepted_by_root=False))
 rp=OUT/'full18-readpoints-candidate.json'
 save(rp,dict(records=records,common_scale=[1,4],cell=[512,320],anchor=[256,304],
  observed_all18_sources_have_root_acceptance=True,root_readpoint_plan_accepted=False,
  preserved_suggested_lift_source_order=[7,9,8,10,11],
  hip_shoulder_uncertainty_source_px=16,not_a_skull_or_bone_length_ruler=True,
  full18_registration_executed=False,runtime_installed=False,godot_run=False,post_submitted=False))
 rows=[dict(phase=r['source_phase'],request=1,source=r['source'],root_acceptance=r['root_acceptance'],
  registration_root_source=r['root'],support_readpoint_note='宽足底与爪尖分开；整图共同1/4；髋肩为皮肤遮挡下人工体积代理，不能用来当实体抓点或受方腰点。',
  readpoint_candidate=rec(rp),per_phase_scale=None,area_fit=None) for r in records]
 save(OUT/'full18-registration-plan-candidate.json',dict(root_all18_sources_accepted=False,
  root_full_action_registration_authorized=False,root_readpoint_plan_accepted=False,root_preview_order_accepted=False,
  observed_all18_source_acceptance_records_present=True,common_scale=[1,4],cell=[512,320],anchor=[256,304],
  output='reports/review/2026-11-02/gomora-super3-back-lift-registration-v1/registered18-v1',
  preview_source_order=[0,1,2,3,4,5,6,7,9,8,10,11,12,13,14,15,16,17],phases=rows,
  original_source_phase_numbers_preserved=True,runtime_slot_mapping_created=False,template_not_runnable=True))
 lines=['# 全18源根点计划候选：等待根亲看读窗后授权','',
 '已逐张实际看新增00–03/14–17完整根接收源及原生足窗，04–13沿v2读点与源SHA复核。每相另给完整源标点页和原生1:1足部读窗，所有原请求/source相号保持。共同1/4、整格512×320、运行根[256,304]；没有生成注册PNG或运行槽映射。','',
 '| 原源相 | 候选源根 | 近宽足底/最低爪y | 远宽足底/最低爪y | 原生近髋/近肩高度代理 |',
 '| --- | --- | --- | --- | --- |']
 for r in records:
  fs=r['feet'];claw=lambda f:f.get('lowest_claw_or_outline_y',f.get('lowest_foot_claw_or_outline_y'))
  shoulder=r['near_shoulder_proxy_height'];sh='缺旧代理' if shoulder is None else f'{shoulder:.2f}'
  lines.append(f"| {r['source_phase']:02d} | {r['root']} | {fs[0]['sole_y']}/{claw(fs[0])} | {fs[1]['sole_y']}/{claw(fs[1])} | {r['near_hip_proxy_height']:.2f}/{sh} |")
 lines+=['','髋/肩约±16源像素，为皮肤遮挡下体积代理，不是骨长、长颅尺或实体承重点。新增八相源根x取两宽足底中心中点最近4px，y采用近亮后足宽底；04–13不重新拟合。共同1/4并不意味着尺寸偏差已过严格门，原生髋/肩高度和源图面积仍可能存在整人尺寸小差，根已允许共同处理后看全链。',
 '', '12继续精确指向根接受的request-001/rejected/candidate.png与SHA，保留弱Alpha隔离事实，仅准Forge整图派生，不变更原Alpha门。',
 '', '预览候选顺序0→1→2→3→4→5→6→7→9→8→10→11→12→13→14→15→16→17，保留07→09→08→10→11建议链；原源序号/原请求raw tick未改，运行顺序仍待根认可。',
 '', 'full18-registration-plan-candidate.json中root_all18_sources_accepted、root_full_action_registration_authorized、root_readpoint_plan_accepted继续false；root_preview_order_accepted也false。已观察18接收文件齐不代替这三执行门授权。未自行执行full18_registration.py，未POST、Godot、Git、产品改动。']
 (OUT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
 for p,digest in frozen.items():assert sha(p)==digest
 print(OUT)

if __name__=='__main__':main()

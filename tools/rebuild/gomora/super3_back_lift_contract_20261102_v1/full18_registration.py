"""18相整图注册候选。全部根接收+根读点计划具备前拒绝执行；无POST/Godot/产品写入。"""
from pathlib import Path
import argparse,json,hashlib,math,sys
import numpy as np
from PIL import Image
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/rebuild/shared'))
import forge_backend as forge
import three_key_prototype as preview
ART=ROOT/'art/fighters/gomora/stage4/super3-back-lift-20261102-v1'
ALLOWED=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-registration-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,d):
 with p.open('x',encoding='utf8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def exact(record):
 assert isinstance(record,dict) and set(['path','sha256'])<=set(record),'源/根接受记录不完整'
 p=(ROOT/record['path']).resolve();assert p.is_relative_to(ROOT.resolve()) and sha(p)==record['sha256'];return p
def register(plan_path):
 plan=read(plan_path)
 assert plan.get('root_all18_sources_accepted') is True,'18源未全部根接收，拒绝处理'
 assert plan.get('root_full_action_registration_authorized') is True,'等待根明确整动作处理授权'
 assert plan.get('root_readpoint_plan_accepted') is True,'等待根接收18相完整读点/支撑根计划'
 assert plan['common_scale']==[1,4] and plan['cell']==[512,320] and plan['anchor']==[256,304]
 rows=plan['phases'];assert len(rows)==18 and sorted(r['phase'] for r in rows)==list(range(18))
 order=plan.get('preview_source_order',list(range(18)))
 assert isinstance(order,list) and len(order)==18 and sorted(order)==list(range(18)),'预览顺序必须保留18个原源相号'
 out=(ROOT/plan['output']).resolve();assert out.is_relative_to(ALLOWED.resolve()) and out!=ALLOWED.resolve() and not out.exists()
 accepted=[];frozen={plan_path:sha(plan_path)}
 for row in sorted(rows,key=lambda r:r['phase']):
  source=exact(row['source']);acceptance=exact(row['root_acceptance']);gate=read(acceptance)
  assert source.is_relative_to(ART.resolve()) and source.name=='candidate.png'
  assert gate['accepted_for_whole_action_processing'] is True and gate['source']['sha256']==sha(source)
  assert (ROOT/gate['source']['path']).resolve()==source
  request_dir=ART/f"phase-{row['phase']:02d}/request-{int(row['request']):03d}"
  # Root may explicitly accept a quarantined weak-Alpha original for Forge-only derivation.
  # Exact source path/SHA above must match its separate root acceptance; directory alone never authorizes it.
  assert source in [request_dir/'candidate.png',request_dir/'rejected/candidate.png']
  assert acceptance==request_dir/'root-actual-source-review-v1.json'
  root=row['registration_root_source'];assert isinstance(root,list) and len(root)==2
  assert all(type(v)is int and 0<=v<1024 for v in root)
  assert isinstance(row.get('support_readpoint_note'),str) and row['support_readpoint_note'].strip()
  assert row.get('per_phase_scale') is None and row.get('area_fit') is None,'禁止逐相拟合'
  im=Image.open(source).convert('RGBA');assert im.size==(1024,1024);mask=np.asarray(im)[...,3]>=128
  assert mask.any() and not(mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any())
  frozen[source]=sha(source);frozen[acceptance]=sha(acceptance);accepted.append((row,source,acceptance))
 # Only now, after all18 acceptance/point/source gates, create output or process any runtime-scale frame.
 palette=ROOT/'content/fighters/gomora/palette.json';colors=read(palette)['colors'];frozen[palette]=sha(palette)
 out.mkdir(parents=True);(out/'native').mkdir();results=[];frames=[]
 for row,source,acceptance in accepted:
  im=Image.open(source).convert('RGBA');down=forge.binarize_alpha(im.copy())
  down=forge._kcentroid_downscale(down,256,256);forge.binarize_alpha(down)
  with forge.palette_mode('rgb'):forge.apply_palette(down,colors)
  quarter=[int(math.floor(v/4+.5)) for v in row['registration_root_source']]
  origin=[256-quarter[0],304-quarter[1]];canvas=Image.new('RGBA',(512,320));canvas.paste(down,tuple(origin))
  assert np.sum(np.asarray(canvas)[...,3]>0)==np.sum(np.asarray(down)[...,3]>0),'整图画布裁切，拒绝'
  assert set(np.unique(np.asarray(canvas)[...,3]))<={0,255}
  phase=row['phase'];path=out/f'native/{phase:02d}.png';canvas.save(path);frames.append(canvas)
  results.append(dict(phase=phase,source=rec(source),root_acceptance=rec(acceptance),native=rec(path),
   original_in_alpha_quarantine='rejected' in source.parts,original_alpha_range=list(map(int,[np.asarray(im)[...,3].min(),np.asarray(im)[...,3].max()])),
   registration_root_source=row['registration_root_source'],quarter_root=quarter,paste_origin=origin,
   support_readpoint_note=row['support_readpoint_note'],native_bbox=canvas.getbbox(),strict_size_passed=False,runtime_installed=False))
 for i in range(17):
  a,b=order[i],order[i+1]
  preview.pair_page(frames[a],frames[b],[f'SOURCE {a:02d}',f'SOURCE {b:02d}'],out/f'seam-{a:02d}-{b:02d}-full-cells.jpg')
 for start in [0,4,8,12,16]:
  ids=order[start:start+4];group=[frames[p] for p in ids]
  preview.full_page(group,[f'SOURCE {p:02d}' for p in ids],out/f'preview-ranks-{start:02d}-{start+len(group)-1:02d}-full-cells.jpg')
 for p in out.glob('*.jpg'):assert Image.open(p).width<=768 and p.stat().st_size<=150000
 for p,digest in frozen.items():assert sha(p)==digest,'冻结输入变化'
 save(out/'registration-candidate.json',dict(plan=rec(plan_path),phases=results,common_scale=[1,4],cell=[512,320],anchor=[256,304],
  actual_palette_mode='rgb',palette=rec(palette),backend=forge.backend_info(),whole_image_only=True,
  original_source_phase_numbers_preserved=True,preview_source_order=order,
  runtime_slot_mapping_created=False,preview_order_accepted_by_root=plan.get('root_preview_order_accepted') is True,
  original_source_bytes_preserved=True,per_phase_scale_fit=False,area_fit=False,root_readpoint_plan_only=True,
  strict_size_passed=False,full_motion_accepted=False,hitboxes_or_grips_created=False,runtime_installed=False,
  godot_run=False,post_submitted=False,super3_playable_approval=False))
 print(json.dumps(dict(output=str(out),phases=18,installed=False),ensure_ascii=False))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--plan',required=True,type=Path)
 register(parser.parse_args().plan.resolve())

"""冻结SHA白名单产品候选。build仅写报告；apply仅供持Godot锁的根明确运行。"""
from pathlib import Path
import argparse,copy,difflib,hashlib,json,math,shutil,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'reports/review/2026-11-02/gomora-super3-main-candidate-v1'
REG=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-registration-v1/registered18-v1/registration-candidate.json'
THIRD=ROOT/'reports/review/2026-11-02/gomora-super3-zetton-third-scale-static-pairs-v2/third-scale-static-pair-plan.json'
FX=ROOT/'art/fighters/gomora/stage4/super3-back-lift-pixelfx-v2/bake-a/catalog-candidate.json'
POSE='gomora_back_lift_receiver'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8',newline='\n')as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def nearest(v):return int(math.floor(v+.5))
def boxes(im,anchor,band=16):
 a=np.asarray(im)[...,3]>0;result=[]
 for bottom in range(im.height,0,-band):
  top=max(0,bottom-band);occupied=a[top:bottom].any(axis=0);starts=np.flatnonzero(occupied&~np.r_[False,occupied[:-1]]);ends=np.flatnonzero(occupied&~np.r_[occupied[1:],False])+1
  for l,r in zip(starts,ends):
   ys,xs=np.nonzero(a[top:bottom,int(l):int(r)])
   result.append([int(l)+int(xs.min())-anchor[0],anchor[1]-(top+int(ys.max())+1),int(xs.max()-xs.min()+1),int(ys.max()-ys.min()+1)])
 return result
def replace_once(text,old,new,label):
 assert text.count(old)==1,(label,text.count(old));return text.replace(old,new,1)
def build():
 assert not OUT.exists();(OUT/'product').mkdir(parents=True);(OUT/'diffs').mkdir();frozen={};entries=[]
 def freeze(p):frozen[p]=sha(p);return p
 def stage(rel,data=None,source=None,text=None,image=None):
  p=OUT/'product'/rel;p.parent.mkdir(parents=True,exist_ok=True);old=ROOT/rel
  before=sha(old)if old.exists()else None
  if old.exists():freeze(old)
  if source:freeze(source);shutil.copyfile(source,p)
  elif image is not None:image.save(p)
  elif text is not None:p.write_text(text,encoding='utf8',newline='\n')
  else:save(p,data)
  entries.append(dict(path=rel,before_sha256=before,after_sha256=sha(p),candidate=rec(p),new_file=before is None))
  if old.exists()and p.suffix in['.gd','.json','.md']:
   diff=''.join(difflib.unified_diff(old.read_text('utf-8-sig').splitlines(True),p.read_text('utf-8-sig').splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
   (OUT/'diffs'/rel.replace('/','__')).with_suffix('.diff').write_text(diff,encoding='utf8',newline='\n')
 def patch(rel,changes):
  text=freeze(ROOT/rel).read_text('utf-8-sig')
  for old,new in changes:text=replace_once(text,old,new,rel)
  stage(rel,text=text)
 stage('core/combat/throw_current_capture.gd',source=HERE/'throw_current_capture.template.gd')
 patch('core/combat/hit_resolver.gd',[
  ('const THROW_TARGET_RULE_REVISION := 1','const THROW_TARGET_RULE_REVISION := 1\nconst THROW_CURRENT_CAPTURE_REVISION := 1\nconst CurrentCapture = preload("res://core/combat/throw_current_capture.gd")'),
  ('\t\tif not UfeThrowResolver.can_capture(target,throw_move):return false','\t\tif not UfeThrowResolver.can_capture(target,throw_move):return false\n\t\tif not CurrentCapture.eligible(attacker,target,throw_move):return false'),
  ('\tif str(move.kind)=="throw":\n\t\ta.combat.confirmed=true','\tif str(move.kind)=="throw":\n\t\tCurrentCapture.remember(b,move) # 清招前保存真实当前整相；无参数时不新增motion数据。\n\t\ta.combat.confirmed=true')])
 patch('core/combat/move_data.gd',[
  ('const HoldPoints = preload("res://core/combat/throw_hold_points.gd")','const HoldPoints = preload("res://core/combat/throw_hold_points.gd")\nconst CurrentCapture = preload("res://core/combat/throw_current_capture.gd")'),
  ('\tif move.has("air_only"):', '\tif not CurrentCapture.valid_move(move):return false\n\tif move.has("air_only"):')])
 patch('core/combat/throw_resolver.gd',[
  ('const HoldPoints = preload("res://core/combat/throw_hold_points.gd")','const HoldPoints = preload("res://core/combat/throw_hold_points.gd")\nconst CurrentCapture = preload("res://core/combat/throw_current_capture.gd")'),
  ('\t\tvar target: Dictionary=frame.target\n\t\tif str(target.get("mode","root"))=="hold"', '\t\tvar target: Dictionary=frame.target\n\t\tif CurrentCapture.preserve(b,target):continue\n\t\tif str(target.get("mode","root"))=="hold"')])
 patch('core/fighters/fighter.gd',[
  ('func frame() -> Dictionary:\n','func frame() -> Dictionary:\n\tif state=="thrown" and bool(motion.get("throw_current_capture",{}).get("active",false)):\n\t\treturn motion.throw_current_capture.frame\n'),
  ('func animation_key() -> String:\n','func animation_key() -> String:\n\tif state=="thrown" and bool(motion.get("throw_current_capture",{}).get("active",false)):\n\t\treturn str(motion.throw_current_capture.animation)\n')])
 patch('core/combat/match_director.gd',[
  ('["throw_target_air", UfeHitResolver.THROW_TARGET_RULE_REVISION]],','["throw_target_air", UfeHitResolver.THROW_TARGET_RULE_REVISION], ["throw_current_capture", UfeHitResolver.THROW_CURRENT_CAPTURE_REVISION]],')])
 patch('presentation/side_view.gd',[
  ('\tvar clips: Dictionary = manifest.get("clips", {})\n\tif intro_tick>=0:',
   '\t# 仅只读显式空中起相快照；不移动模拟、不按像素做碰撞。\n\tvar current_capture: Dictionary=f.motion.get("throw_current_capture",{}) if f.state=="thrown" else {}\n\tif not bool(current_capture.get("active",false)):current_capture={}\n\tif not current_capture.is_empty():\n\t\tkey=str(current_capture.animation)\n\t\ttick=int(current_capture.state_tick)\n\t\tif str(current_capture.state)=="air":\n\t\t\tvar jump_kind: String=str(current_capture.jump_kind)\n\t\t\tvar saved_vy: int=int(current_capture.vy)\n\t\t\tkey="flip_forward" if jump_kind=="diagonal" else "flip_back" if jump_kind=="backward" else "chase_takeoff" if jump_kind=="chase" else "vertical_jump"\n\t\t\ttick=clampi((16-saved_vy-2)/8,0,3)*8 if key=="flip_back" else clampi((16-saved_vy-2)/8,0,3)*3 if key=="flip_forward" else 16-saved_vy\n\t\t\tif bool(manifest.get("clips",{}).get(key,{}).get("trajectory_driven",false)):tick=f.definition.jump_speed-saved_vy\n\tvar clips: Dictionary = manifest.get("clips", {})\n\tif intro_tick>=0:'),
  ('\tif not grounded_pose.is_empty():index=clampi(int(grounded_pose.sprite)',
   '\tif not current_capture.is_empty() and str(current_capture.state)=="air":\n\t\tif key in ["vertical_jump","flip_back"]:index=clampi(int(current_capture.frame.sprite)-int(clip.get("simulation_sprite_offset",0)),0,clip.rects.size()-1)\n\t\telif key=="chase_takeoff":index=clip.rects.size()-1\n\tif not grounded_pose.is_empty():index=clampi(int(grounded_pose.sprite)')])
 reg=read(freeze(REG));third=read(freeze(THIRD));byid={r['phase']:r for r in reg['phases']};order=reg['preview_source_order'];assert order==[0,1,2,3,4,5,6,7,9,8,10,11,12,13,14,15,16,17]
 atlas=Image.new('RGBA',(3072,960));gframes={};backpoints={}
 for rank,phase in enumerate(order):
  r=byid[phase];p=freeze(ROOT/r['native']['path']);assert sha(p)==r['native']['sha256'];im=Image.open(p).convert('RGBA');assert im.size==(512,320)
  atlas.paste(im,((rank%6)*512,(rank//6)*320));gframes[rank]=im
  source=freeze(ROOT/r['source']['path']);assert sha(source)==r['source']['sha256'];a=np.asarray(Image.open(source));ys=np.flatnonzero(a[:,640,3]>=128)
  native=[160+r['paste_origin'][0],nearest((int(ys[0])+2)/4)+r['paste_origin'][1]]
  assert im.getpixel(tuple(native))[3]==255,(phase,native)
  backpoints[rank]=[native[0]-256,304-native[1]]
 stage('assets/fighters/gomora/animations/special3-back-lift/atlas.png',image=atlas)
 gm=read(freeze(ROOT/'assets/fighters/gomora/animations/manifest.json'))
 gm['clips']['special3']=dict(texture='res://assets/fighters/gomora/animations/special3-back-lift/atlas.png',cell=512,anchor_y=304,
  rects=[[(i%6)*512,(i//6)*320,512,320]for i in range(18)],ticks=[4]*18,anchors=[[256,304]for _ in order],loop=False,
  source_phase_order=order,production_note='根授权最小main动态候选；18独立整相；严格尺寸/配对动态待根实看')
 stage('assets/fighters/gomora/animations/manifest.json',gm)
 vframes={};vatlas=Image.new('RGBA',(1024,256));vstates=[];points={}
 for i,r in enumerate(third['phases']):
  name=r['cell'];p=freeze(ROOT/r['native']['path']);assert sha(p)==r['native']['sha256'];im=Image.open(p).convert('RGBA');vatlas.paste(im,(i*256,0));vframes[name]=im
  pt=r['integer_visible_surface_native'];points[name]=[pt[0]-128,248-pt[1]]
  vstates.append(dict(sprite=i,dx=0,dy=0,hitboxes=[],hurtboxes=boxes(im,[128,248]),cancel=[],events=[]))
 stage('assets/fighters/zetton/animations/gomora-back-lift-receiver/atlas.png',image=vatlas)
 zm=read(freeze(ROOT/'assets/fighters/zetton/animations/manifest.json'));assert POSE not in zm['clips']
 zm['clips'][POSE]=dict(texture='res://assets/fighters/zetton/animations/gomora-back-lift-receiver/atlas.png',cell=256,anchor_y=248,
  rects=[[i*256,0,256,256]for i in range(4)],ticks=[4]*4,anchors=[[128,248]]*4,loop=False)
 stage('assets/fighters/zetton/animations/manifest.json',zm)
 zs=read(freeze(ROOT/'content/fighters/zetton/state_frames.json'));assert POSE not in zs;zs[POSE]=vstates;stage('content/fighters/zetton/state_frames.json',zs)
 fx=read(freeze(FX));fxcatalog=read(freeze(ROOT/'content/presentation/phase3_projectiles.json'))
 for id,r in fx.items():
  dest=f'assets/effects/gomora/back_lift/{id}/atlas.png';source=freeze(ROOT/r['atlas_candidate']);stage(dest,source=source)
  fxcatalog[id]=dict(texture='res://'+dest,rects=r['rects'],ticks=r['ticks'],anchor=r['anchor'],loop=False,display_scale=[1,1],source_kind='pixelfx_code_baked',collision=False)
 stage('content/presentation/phase3_projectiles.json',fxcatalog)
 portrait=Image.open(ROOT/byid[1]['native']['path']).convert('RGBA');cropped=portrait.crop((52,0,372,320));assert np.sum(np.asarray(portrait)[...,3]>0)==np.sum(np.asarray(cropped)[...,3]>0)
 stage('assets/fighters/gomora/cinematic/back-lift-portrait.png',image=cropped)
 supers=read(freeze(ROOT/'content/presentation/supers.json'));supers['gomora']['portrait']='res://assets/fighters/gomora/cinematic/back-lift-portrait.png';stage('content/presentation/supers.json',supers)
 old=read(freeze(ROOT/'content/fighters/gomora/moves/special3.json'));move=copy.deepcopy(old)
 for key in list(move):
  if key not in ['id','display_name','startup','active','recovery','damage','hitstun','blockstun','pushback','stun','stamina_cost','energy_cost','kind','level','unblockable','launch','bounce','knockdown','frames','feedback','chip_damage','manual_projectiles','super_level','air_allowed','cancel_rule','production_note','audio']:move.pop(key)
 move.update(display_name='背掀震落（三级·本作编排）',startup=16,active=4,recovery=52,damage=490,stamina_cost=50,energy_cost=3000,
  kind='throw',level='mid',unblockable=True,launch=False,bounce=False,knockdown=True,chip_damage=0,manual_projectiles=True,super_level=3,air_allowed=False,
  throw_target_air=True,throw_schema=2,whiff_branch_tick=20,whiff_recovery_tick=56,
  throw_current_capture=dict(target_ids=['zetton'],states=['air'],body_hurtbox_index=1,first_tick=16,entry_tick=20,max_entry_root_delta=[14,14]),
  cancel_rule='不可取消；未捕中在raw20跳至raw56，36tick空抓；捕后原1/2/3真实tick可拆',
  production_note='根授权最小main动态候选，仅杰顿受方；全组1/3尺寸偏差/C远臂遮挡未作严格通过；其它目标空抓不适用',
  feedback=dict(spark='gomora_back_lift_capture_contact',block_spark='impact_guard',hitstop=4,blockstop=3,shake=0,flash=1,
   color=[1,1,1,1],slam_spark='gomora_back_lift_landing_dust',finish_effect='',finish_trigger='throw_slam'),
  audio=dict(hit='gomora_throw_grab',block='gomora_guard_scrape',throw_slam='gomora_throw_slam',lift='gomora_throw_lift',lift_sprite=6))
 move['frames']=[];overrides={'zetton':{POSE:{str(i):points[n]for i,n in enumerate('ABCD')}}}
 for t in range(72):
  rank=t//4;frame=dict(sprite=rank,dx=0,dy=0,hitboxes=[],hurtboxes=boxes(gframes[rank],[256,304],24),cancel=[],events=[])
  if t<4:frame.update(pause_clock=True,freeze_opponent=True,cinematic_stage='portrait')
  if t==0:frame['events']=[dict(kind='sound',id='gomora_roar_attack')]
  if 16<=t<=19:
   # 实图背甲斜面范围；另由显式受方中躯干框+首承重根邻域双门确认，绝不读Alpha进模拟。
   bp=backpoints[rank];frame['hitboxes']=[[bp[0]-20,bp[1]-12,28,12]];frame['target']=dict(mode='capture_current')
  elif 20<=t<=35:
   n='A'if t<24 else'B';frame['target']=dict(mode='hold',pose=POSE,sprite='ABCD'.index(n),facing=1,root=[0,0],grip=backpoints[rank],hold_point_overrides=overrides)
  elif 36<=t<=43:
   n='C'if t<40 else'D';gap=[-6,14]if n=='C'else[-20,30];bp=backpoints[rank];pt=points[n]
   frame['target']=dict(mode='root',pose=POSE,sprite='ABCD'.index(n),facing=1,root=[bp[0]+gap[0]-pt[0],bp[1]+gap[1]-pt[1]])
  elif t>=44:
   pose='thrown_back'if t<50 else'thrown_forward'if t<60 else'down'
   sprite=0 if t<48 else 1 if t<50 else 2 if t<52 else 3 if t<60 else 0 if t<68 else 8
   frame['target']=dict(mode='release',pose=pose,sprite=sprite,facing=1,root=[-290,0],progress=[min(9,t-43),9],ground=True)
   if t==52:frame['target']['impact']=True
  if 36<=t<50:
   frame['attachments']=[dict(effect='gomora_back_lift_release_dust',sprite=min(6,(t-36)//2),anchor=backpoints[rank],color=[1,1,1,1],z_index=4)]
  move['frames'].append(frame)
 assert sum(bool(f.get('target',{}).get('impact',False))for f in move['frames'])==1
 stage('content/fighters/gomora/moves/special3.json',move)
 moves=freeze(ROOT/'content/fighters/gomora/MOVES.md').read_text('utf-8-sig')
 moves+='\n\n## 2026-11-02 背掀震落最小动态候选\n\n三级3000能/50体；Q蓄至三格后P或J+K。地面本人只在raw16–19以真实上背实体接住空中躯干；当前仅杰顿完整受方适用，其它角色不适用而空抓。不是对地指令投，也不追踪/吸附；起手可打断，捕后原第1/2/3真实tick可L拆。raw52仅一次490伤，落空36tick收势。A落背、B横伏至35、C36离背、D40后翻，属于本作时序；原剧只支持负重挺背后抛题材。候选严格尺/整段动态/主游戏回放仍待根验收。\n'
 stage('content/fighters/gomora/MOVES.md',text=moves)
 for p,digest in frozen.items():assert sha(p)==digest,str(p)
 save(OUT/'install-plan.json',dict(schema=1,status='root_review_required_not_installed',entries=entries,frozen_inputs=[rec(p)for p in frozen],
  restricted_target_ids=['zetton'],no_source_bytes_changed=True,strict_size_passed=False,dynamic_accepted=False,godot_run=False,post_submitted=False,
  baseline_required_before_apply=True,root_only_apply=True))
 print(json.dumps(dict(report=str(OUT),product_paths=[e['path']for e in entries],installed=False),ensure_ascii=False,indent=2))
def apply():
 plan=read(OUT/'install-plan.json');receipt=OUT/'root-install-receipt.json';assert not receipt.exists(),'拒绝重复安装'
 # Root must explicitly provide the source-locked review acceptance and real before-regression result.
 gate=read(OUT/'root-patch-acceptance.json');assert gate.get('accepted_exact_install_plan_sha256')==sha(OUT/'install-plan.json')and gate.get('root_holds_godot_lock')is True
 assert gate.get('temporary_main_candidate_only')is True,'杰顿限制候选不得作为普通发行默认'
 baseline=ROOT/gate['legacy_baseline_result']['path'];assert sha(baseline)==gate['legacy_baseline_result']['sha256'];assert read(baseline).get('errors')==[]
 assert (ROOT/'art/shared/locks/godot.lock').exists(),'根必须持唯一Godot锁'
 allowed={e['path']for e in plan['entries']};assert all(not(Path(p).is_absolute()or'..'in Path(p).parts)for p in allowed)
 for e in plan['entries']:
  p=ROOT/e['path'];candidate=ROOT/e['candidate']['path'];assert sha(candidate)==e['after_sha256'];assert (sha(p)if p.exists()else None)==e['before_sha256'],e['path']
 for r in plan['frozen_inputs']:
  assert sha(ROOT/r['path'])==r['sha256'],r['path']
 # All preconditions checked before the first write; keep a byte-exact rollback pack.
 for e in plan['entries']:
  p=ROOT/e['path']
  if p.exists():b=OUT/'rollback'/e['path'];b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,b)
 for e in plan['entries']:
  p=ROOT/e['path'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/e['candidate']['path'],p);assert sha(p)==e['after_sha256']
 save(receipt,dict(installed=[dict(path=e['path'],sha256=sha(ROOT/e['path']))for e in plan['entries']],root_acceptance=rec(OUT/'root-patch-acceptance.json'),godot_run_by_installer=False,temporary_main_candidate_only=True,ordinary_release_requires_restore=True))
 print(str(receipt))
def restore():
 plan=read(OUT/'install-plan.json');receipt=OUT/'root-install-receipt.json';assert receipt.is_file()
 output=OUT/'root-restore-receipt.json';assert not output.exists()
 gate=read(OUT/'root-restore-acceptance.json');assert gate.get('accepted_install_receipt_sha256')==sha(receipt)and gate.get('root_holds_godot_lock')is True
 assert(ROOT/'art/shared/locks/godot.lock').is_file()
 archive=(ROOT.parent/'UFEneo_archive/2026-11-02/project-cleanup/gomora-super3-main-candidate-v1').resolve()
 intended=(ROOT.parent/'UFEneo_archive/2026-11-02/project-cleanup').resolve();assert archive.is_relative_to(intended)and archive!=intended and not archive.exists()
 # Complete preflight: another branch's edits must never be overwritten or partly restored.
 for e in plan['entries']:
  p=(ROOT/e['path']).resolve();assert p.is_relative_to(ROOT.resolve())and sha(p)==e['after_sha256'],e['path']
  if e['before_sha256']is not None:assert sha(OUT/'rollback'/e['path'])==e['before_sha256']
 archive.mkdir(parents=True);archived=[];restored=[]
 for e in plan['entries']:
  p=ROOT/e['path']
  if e['before_sha256']is None:
   dst=archive/e['path'];assert dst.resolve().is_relative_to(archive);dst.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(p),str(dst));archived.append(rec(dst)if dst.is_relative_to(ROOT)else dict(path=str(dst),sha256=sha(dst)))
   # Only deterministic import/UID sidecars belonging to this exact newly-created target.
   for sidecar in [p.with_suffix(p.suffix+'.uid'),p.with_suffix(p.suffix+'.import')]:
    if sidecar.exists():
     dest=archive/sidecar.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);digest=sha(sidecar);shutil.move(str(sidecar),str(dest));archived.append(dict(path=str(dest),sha256=digest,generated_sidecar=True))
  else:
   shutil.copyfile(OUT/'rollback'/e['path'],p);assert sha(p)==e['before_sha256'];restored.append(rec(p))
 save(archive/'sha256-index.json',dict(files=archived,reason='根授权临时杰顿main候选结束，新增产品文件保全到工程外'))
 save(output,dict(restored=restored,archived_new_files=archived,old_super3_beam_restored=True,ordinary_release_candidate_removed=True,shared_catalog_exact_preimage_restored=True))
 print(str(output))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('command',choices=['build','apply','restore']);args=parser.parse_args();globals()[args.command]()

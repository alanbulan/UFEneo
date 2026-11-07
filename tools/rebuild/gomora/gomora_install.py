"""哥莫拉数据安装与审片材料。只安装已逐帧自检的完整人物，不借其他角色帧。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import argparse,copy,math,shutil,csv
from gomora_qa import *
from loop_qa import evaluate
import gomora_batch as batch

ATTACKS=['light1','light2','light3','heavy','launcher','spin_heavy','crush','tackle','crouch_light','crouch_light2','sweep','slide','vertical_light','vertical_heavy','diagonal_light','diagonal_heavy','air_crush','dive','chase_light1','chase_light2','chase_end']

def collect(action,allow_unreviewed=False):
 profiles=read(WORK/'profiles.json');s=profiles[action];registry=read(WORK/'asset-registry.json')['assets'];images=[];heads=[];sources=[]
 complete=WORK/action/'complete-selection.json'
 if complete.exists():
  for pick in read(complete)['frames']:
   source=ROOT/pick['folder'];local=pick['frame'];q=read(source/'head-qa.json');h=copy.deepcopy(next(r for r in q['frames'] if r['frame']==local));path=source/h['image']
   if any(not issue.startswith('frame ') or issue.startswith(f'frame {local}:') for issue in hard_issues(q['issues'])):raise ValueError(action+'选中的单帧有未解决硬门')
   visual=source/'visual-review.json'
   if not allow_unreviewed and (not visual.exists() or not read(visual).get('approved')):raise ValueError(action+'选帧未逐帧视觉复核')
   assert sha(path)==h['image_sha256'];h['source_folder']=rel(source);images.append(Image.open(path).convert('RGBA'));heads.append(h);sources.append(path)
  assert len(images)==s['frames'];return images,heads,sources,s
 for key,entry in registry.items():
  if entry['action']!=action or entry.get('replacement'):continue
  selected=WORK/key/'selected.json'
  if not selected.exists():return None
  source=ROOT/read(selected)['folder'];q=read(source/'head-qa.json')
  if hard_issues(q['issues']):raise ValueError(key+'存在未解决的硬门错误')
  visual=source/'visual-review.json'
  if not allow_unreviewed and (not visual.exists() or not read(visual).get('approved')):raise ValueError(key+'尚未逐帧视觉复核')
  for h in q['frames']:
   p=source/h['image'];assert sha(p)==h['image_sha256'];images.append(Image.open(p).convert('RGBA'));h=copy.deepcopy(h);h['source_folder']=rel(source);heads.append(h);sources.append(p)
 assert len(images)==s['frames']
 replacements=WORK/action/'frame-selections.json'
 if replacements.exists():
  for index,pick in read(replacements).items():
   i=int(index);source=ROOT/pick['folder'];local=int(pick.get('frame',0));q=read(source/'head-qa.json');h=copy.deepcopy(q['frames'][local])
   if hard_issues(q['issues']):raise ValueError(action+'补帧有硬门错误')
   visual=source/'visual-review.json'
   if not allow_unreviewed and (not visual.exists() or not read(visual).get('approved')):raise ValueError(action+'补帧未视觉复核')
   path=source/h['image'];assert sha(path)==h['image_sha256'];h['source_folder']=rel(source);images[i]=Image.open(path).convert('RGBA');heads[i]=h;sources[i]=path
 order_path=WORK/action/'playback-order.json'
 if order_path.exists():
  order=read(order_path)['order'];assert sorted(order)==list(range(len(images)))
  images=[images[i] for i in order];heads=[heads[i] for i in order];sources=[sources[i] for i in order]
 return images,heads,sources,s

def hurtboxes(im):
 """Alpha分层实体框。尾巴也有受击框，不能只给人形躯干框。"""
 a=np.array(im)[:,:,3]>0;boxes=[]
 for y in range(0,im.height,24):
  mask=a[y:min(im.height,y+24)];cols=np.flatnonzero(mask.any(0))
  if not len(cols):continue
  groups=np.split(cols,np.where(np.diff(cols)>5)[0]+1)
  for xs in groups:
   left,right=int(xs[0]),int(xs[-1])+1;yy,xx=np.where(mask[:,left:right]);top=y+int(yy.min());bottom=y+int(yy.max())+1
   boxes.append([left-ANCHOR[0],ANCHOR[1]-bottom,right-left,bottom-top])
 return boxes

def prepare_annotations(action):
 data=collect(action,True)
 if not data:return
 images,heads,sources,s=data;sheet=Image.new('RGB',(min(4,len(images))*CELL[0],math.ceil(len(images)/4)*(CELL[1]+40)),'#202632');d=ImageDraw.Draw(sheet)
 for i,im in enumerate(images):
  ox=(i%4)*CELL[0];oy=(i//4)*(CELL[1]+40);sheet.paste(im,(ox,oy+40),im);d.text((ox+5,oy+4),f'{action} #{i}',font=font(18),fill='white')
  for x in range(0,CELL[0],20):d.line((ox+x,oy+40,ox+x,oy+40+CELL[1]),fill='#455065');d.text((ox+x,oy+40),str(x),font=font(10),fill='white')
  for y in range(0,CELL[1],20):d.line((ox,oy+40+y,ox+CELL[0],oy+40+y),fill='#455065');d.text((ox,oy+40+y),str(y),font=font(10),fill='white')
 sheet.save(OUT/f'{action}-annotate.png')

def timeline(action,images,ticks,s):
 pp=WORK/action/'hit-points.json';points=read(pp) if pp.exists() else {};move=None
 if action in ATTACKS:
  if not points:raise ValueError(action+'缺少实际爪/尾/角攻击位置标注')
  base=ROOT/f'content/templates/biped_tail/moves/{action}.json'
  if not base.exists():base=ROOT/f'content/templates/humanoid/moves/{action}.json'
  move=read(base)
 seq=[]
 for i,(im,t) in enumerate(zip(images,ticks)):
  hit=[]
  if str(i) in points:
   for p in points[str(i)]:
    x,y,r=p;assert im.getpixel((round(x),round(y)))[3]>0,(action,i,p,'攻击点不在实体出招部位上')
    hit.append([round(x)-ANCHOR[0]-r,ANCHOR[1]-round(y)-r,2*r,2*r])
  for j in range(t):
   cancel=['light2'] if action=='light1' and i>=2 else ['light3'] if action=='light2' and i>=2 else ['crouch_light2'] if action=='crouch_light' and i>=2 else ['sweep'] if action=='crouch_light2' and i>=2 else ['chase_light2'] if action=='chase_light1' and i>=1 else ['chase_end'] if action=='chase_light2' and i>=1 else []
   dx=3 if action=='tackle' and i in [2,3,4] else 2 if action=='slide' and i in [2,3,4] else 0
   heavy=action not in ['light1','light2','light3','crouch_light','crouch_light2'];sound='heavy' if heavy else 'light'
   row=dict(sprite=i,dx=dx,dy=0,hitboxes=copy.deepcopy(hit),hurtboxes=hurtboxes(im),cancel=cancel,events=[dict(kind='sound',id=sound)] if i==j==0 and move else [],impact_effect='impact_heavy' if heavy else 'impact_light',block_effect='impact_guard')
   if hit and j==0 and action=='dive':row['velocity']=[6,-12]
   if hit and j==0 and action=='chase_end':row['velocity']=[1,-22]
   seq.append(row)
 if move:
  active=[int(k) for k in points];first=min(active);last=max(active)
  move.update(display_name=s['name'],startup=sum(ticks[:first]),active=sum(ticks[first:last+1]),recovery=sum(ticks[last+1:]),frames=seq,
    feedback=dict(spark='impact_light' if action in ['light1','light2','light3','crouch_light','crouch_light2'] else 'impact_heavy',block_spark='impact_guard',hitstop=4 if action.startswith('light') else 7,blockstop=3,shake=2 if action in ['heavy','crush','tackle'] else 0,flash=2,color=[1,1,1,1]))
  if action in ['spin_heavy','sweep']:move['attack_anatomy']='实际尾巴；逐帧尾部攻击点来自hit-points.json，不借人体攻击框'
  if action in ['air_crush','chase_end']:move.update(bounce=True,bounce_velocity=8 if action=='chase_end' else 6,level='overhead')
  if action in ['vertical_heavy','dive']:move['level']='overhead'
  if action in ['chase_light1','chase_light2']:move.update(pushback=0,hitstun=30)
  if action=='chase_end':move['pushback']=0
 return seq,move

def previews(action,data,ticks,seq=None):
 images,heads,sources,s=data;folder=OUT/action;folder.mkdir(parents=True,exist_ok=True);cw,ch=CELL[0]*4,CELL[1]*4+80
 sheet=Image.new('RGB',(min(4,len(images))*cw,math.ceil(len(images)/4)*ch),'#202632');d=ImageDraw.Draw(sheet)
 headstrip=Image.new('RGB',(896*len(images),956),'#202632');hd=ImageDraw.Draw(headstrip)
 for i,(im,h,t) in enumerate(zip(images,heads,ticks)):
  ox=(i%4)*cw;oy=(i//4)*ch;a=im.resize((cw,CELL[1]*4),Image.Resampling.NEAREST);sheet.paste(a,(ox,oy+80),a);legacy=h['measurement'];review=head_v2_review(im,legacy,facing='left' if action=='turn' and i==0 else 'right',hidden=h.get('head_hidden',False));m=review['measurement'];headtext=(f'v2 {review["deviation_percent"]:+.1f}% / '+review['marker']) if m else 'v2不可测 / 人工复核'
  d.text((ox+10,oy+5),f'#{i}  {t}tick | 头{headtext} | 站高{h["standing_height"]}px',font=font(25),fill='white')
  if seq:
   fr=seq[sum(ticks[:i])]
   for k,c in [('hurtboxes','#50d8ef'),('hitboxes','#ff5e76')]:
    for x,y,w,hh in fr[k]:d.rectangle((ox+(ANCHOR[0]+x)*4,oy+80+(ANCHOR[1]-y-hh)*4,ox+(ANCHOR[0]+x+w)*4,oy+80+(ANCHOR[1]-y)*4),outline=c,width=3)
  if m:cx,cy=m['center'];box=(round(cx)-64,round(cy)-64,round(cx)+48,round(cy)+48)
  elif legacy:
   # v2不可测时只借历史中心取审片裁框，不拿历史标尺冒充v2合格。
   cx,cy=legacy['center'];box=(round(cx)-64,round(cy)-64,round(cx)+48,round(cy)+48)
  else:
   b=im.getbbox();top=np.array(im)[:,:,3]>0;yy,xx=np.where(top & (np.indices(top.shape)[0]<b[1]+65));cx=float(np.median(xx)) if len(xx) else ANCHOR[0];box=(round(cx)-56,b[1]-2,round(cx)+56,b[1]+110)
  a=im.crop(box).resize((896,896),Image.Resampling.NEAREST);headstrip.paste(a,(i*896,60),a);hd.text((i*896+10,5),f'#{i}: {headtext}',font=font(21),fill='white')
  if m:
   points=[((p[0]-box[0])*8+i*896,(p[1]-box[1])*8+60) for p in [m['eye'],m['nose_tip']]]
   hd.line(points,fill='#63e6ee',width=2)
   for (px,py),color in zip(points,['#ff6479','#75efaa']):hd.ellipse((px-4,py-4,px+4,py+4),outline=color,width=2)
 sheet.save(folder/'contact-x4.png');headstrip.save(folder/'heads-x8.png')
 frames=[]
 for _ in range(3):
  for im in images:
   canvas=Image.new('RGBA',(CELL[0]*2,CELL[1]*2),'#202632');a=im.resize(canvas.size,Image.Resampling.NEAREST);canvas.alpha_composite(a);frames.append(canvas.convert('RGB'))
 frames[0].save(folder/'3cycles.gif',save_all=True,append_images=frames[1:],duration=[round(t*1000/60) for t in ticks]*3,loop=0,disposal=2)
 if s['loop']:
  centers=[h['measurement']['eye'] for h in heads];q=evaluate(centers,action);save(folder/'loop-qa.json',q);curve(q,folder/'eye-curve.png')
 return folder

def curve(q,path):
 im=Image.new('RGB',(1000,450),'#202632');d=ImageDraw.Draw(im);points=q['centers'];y=np.array(points)[:,1];lo,hi=float(y.min())-2,float(y.max())+2
 d.text((20,15),f'{q["action"]} 眼高 总幅 {q["vertical_range"]:.2f}px / 相邻最大 {max(q["adjacent_y"]):.2f}px / 水平 {q["horizontal_range"]:.2f}px',font=font(22),fill='white')
 coords=[(65+i*110,370-(v-lo)/(hi-lo)*280) for i,v in enumerate(np.r_[y,y[0]])];d.line(coords,fill='#63d8ed',width=3)
 for i,(x,yy) in enumerate(coords):d.ellipse((x-5,yy-5,x+5,yy+5),fill='#ffca55');d.text((x-25,yy-32),f'{np.r_[y,y[0]][i]:.2f}',font=font(17),fill='white');d.text((x,392),str(i%len(y)),font=font(18),fill='white')
 im.save(path)

def walk_manual_release(action, qa, sources):
 """只接受本轮明确授权且绑定确切帧、时长和实测值的前走脚掌例外。"""
 path=WORK/action/'manual-release.json'
 if action!='walk_forward' or not path.exists():return False
 release=read(path)
 return (release.get('user_authorized') is True
  and release.get('reason')=='人工复核放行：重型怪兽大脚掌，撑地9.36px'
  and release.get('frame_sha256')==[sha(p) for p in sources]
  and release.get('ticks')==qa['ticks'] and sum(qa['ticks'])==80
  and abs(qa['max_foot_deviation']-9.36)<1e-6
  and qa['issues']==['脚步偏差超±8px'])


def install(action):
 data=collect(action)
 if not data:return dict(action=action,status='待人工：未形成完整已自检条带')
 images,heads,sources,s=data;ticks=read(WORK/action/'timing.json') if (WORK/action/'timing.json').exists() else s['ticks']
 if s['loop']:
  q=evaluate([h['measurement']['eye'] for h in heads],action)
  if q['issues']:raise ValueError('循环未通过：'+'；'.join(q['issues']))
 if action.startswith('walk_'):
  if not (WORK/action/'walk-qa.json').exists():raise ValueError('走路缺少实测脚步数据')
  walk=read(WORK/action/'walk-qa.json')
  if walk['issues'] and not walk_manual_release(action,walk,sources):raise ValueError('走路还未通过实测脚步门')
 seq,move=timeline(action,images,ticks,s);target=ROOT/f'assets/fighters/gomora/animations/{action}/atlas.png';target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():raise ValueError('已安装，不覆盖；有返工应先工程外归档')
 cols=min(4,len(images));atlas=Image.new('RGBA',(cols*CELL[0],math.ceil(len(images)/cols)*CELL[1]));rects=[]
 for i,im in enumerate(images):x=(i%cols)*CELL[0];y=(i//cols)*CELL[1];atlas.alpha_composite(im,(x,y));rects.append([x,y,*CELL])
 atlas.save(target);mp=ROOT/'assets/fighters/gomora/animations/manifest.json';m=read(mp) if mp.exists() else dict(schema=1,cell=list(CELL),anchor=list(ANCHOR),reviewed=False,clips={})
 m['clips'][action]=dict(texture='res://'+rel(target),cell=list(CELL),anchor=list(ANCHOR),anchor_y=ANCHOR[1],anchors=[list(ANCHOR)]*len(images),rects=rects,ticks=ticks,loop=s['loop'],atlas_sha256=sha(target),head_qa=rel(WORK/action/'head-qa.json'),curation=rel(WORK/action/'curation.json'),motion_review=dict(user_approved=False,verdict='本分支逐帧自检，待用户审片'),audio_events=[dict(kind='sound',id='step' if action in ['idle','turn','walk_forward','walk_back','crouch_start','crouch','crouch_rise'] else 'dash' if action.startswith('dash') else 'heavy' if action in ['heavy','launcher','spin_heavy','crush','tackle','sweep','slide'] else 'light',at='state_entry')])
 if action in ['takeoff','chase_takeoff','air_rise','air_apex','air_fall','flip_forward','flip_back']:m['clips'][action]['audio_events']=[dict(kind='sound',id='jump',at='state_entry')]
 if action=='land':m['clips'][action]['audio_events']=[dict(kind='sound',id='land',at='state_entry')]
 if action=='walk_forward' and walk_manual_release(action,walk,sources):m['clips'][action]['rhythm_review']=read(WORK/action/'manual-release.json')
 # 合并记录仍保留各原始帧路径；公共循环/资源扫描通过同一个head-qa入口读取。
 assembled=[]
 for i,h in enumerate(heads):
  h=copy.deepcopy(h);h['image']=str(Path(h['source_folder'])/h['image']);h['image']=str((ROOT/h['image']).relative_to(WORK/action));h['frame']=i
  h['hint']=h['measurement']['eye'] if h['measurement'] else [ANCHOR[0],130];assembled.append(h)
 save(mp,m);save(WORK/action/'head-qa.json',dict(reference=prepare_ruler(),frames=assembled,issues=[]));save(WORK/action/'curation.json',dict(sources=[rel(p) for p in sources],ticks=ticks,loop=s['loop'],reviewed=False))
 if move:save(ROOT/f'content/fighters/gomora/moves/{action}.json',move)
 else:
  p=ROOT/'content/fighters/gomora/state_frames.json';states=read(p) if p.exists() else {};states[{'flip_forward':'diagonal_air','flip_back':'backward_air'}.get(action,action)]=seq;save(p,states)
 if action in ['flip_forward','flip_back']:
  m['clips'][action]['trajectory_driven']=True;save(mp,m)
 if action in ['dash_start','dash','dash_stop']:
  from gomora_dash import assemble
  assemble()
 definition=read(ROOT/'content/fighters/gomora/definition.json');base_moves=read(ROOT/'content/templates/humanoid/move_manifest.json');definition.update(production_status='pilot_partial',playable=False,pilot_playable='idle' in m['clips'],pilot_manual_ready=False,pilot_lock_reason='哥莫拉首批仅审片入口，不开放自由选人',unsupported_moves=[a for a in base_moves if not (ROOT/f'content/fighters/gomora/moves/{a}.json').exists()])
 model=ROOT/'assets/fighters/gomora/model-native.png';model.parent.mkdir(parents=True,exist_ok=True)
 if not model.exists():shutil.copy2(MODEL,model)
 definition['presentation'].update(model='res://'+rel(model),manifest='res://'+rel(mp),cell=list(CELL),anchor=list(ANCHOR),anchor_y=248,target_height=192,native=True)
 save(ROOT/'content/fighters/gomora/definition.json',definition)
 p=ROOT/'content/fighters/gomora/production_plan.json';plan=read(p);plan['status']='pilot_batch1_partial'
 for r in plan['cells']:
  if r['action']==action:r.update(completed=False,implemented=True,reviewed=False,frames=len(images),duration_ticks=sum(ticks),animation=True,hitboxes=bool(move) or action not in ATTACKS,hurtboxes=True,audio=True,integrated=True,report=rel(OUT/action/'contact-x4.png'))
 save(p,plan);previews(action,data,ticks,seq);return dict(action=action,status='installed_pending_user_review',frames=len(images))

def scan():
 results=[]
 for action in batch.ACTIONS:
  data=collect(action,True)
  if data:
   images,heads,sources,s=data;previews(action,data,s['ticks']);results.append(dict(action=action,frames=len(images),head_deviation=[None if not h['measurement'] else (h['measurement']['scale']-1)*100 for h in heads]))
 save(OUT/'candidate-summary.json',results)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['install','annotate','scan']);p.add_argument('--action',nargs='*');a=p.parse_args()
 if a.command=='scan':scan()
 else:
  for action in a.action:
   try:print(install(action) if a.command=='install' else prepare_annotations(action))
   except Exception as exc:print(action,type(exc).__name__,str(exc))

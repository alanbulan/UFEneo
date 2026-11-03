"""哥莫拉第二批骨长引导，仅供GPT姿势参考；不生成运行时人物。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import copy,math
from gomora_qa import *

ACTIONS=['takeoff','air_rise','air_apex','air_fall','land','flip_forward','flip_back','vertical_light','vertical_heavy','diagonal_light','diagonal_heavy','air_crush','dive','chase_takeoff','chase_light1','chase_light2','chase_end']
DESCRIPTIONS={
 'takeoff':'两帧低跳起跳：深屈膝收爪蓄力、双脚重蹬地伸展；这是屈膝动作，不是缩小的站姿。',
 'air_rise':'两帧低跳上升：膝盖弯曲收腿，粗长尾下垂卷起平衡；头身比例不变。',
 'air_apex':'低跳顶点一帧：双膝收于腹前，双爪护架，尾巴完整卷曲，不能缩短身体。',
 'air_fall':'两帧低跳下落：双腿向下伸开准备重落地，爪护胸，头不缩。',
 'land':'两帧重落地缓冲：屈膝深压、抬身回护架，角与尾巴完整。烟尘另由游戏特效显示，不画进人物。',
 'flip_forward':'四帧前跳空翻关键姿势，顺序严格为：前倾收腿、斜倒立、完全倒立、回正下落。全身旋转，头大小不变，长尾随身体转并卷曲收在安全画布内。',
 'flip_back':'四帧后跳空翻，顺序严格为：后仰收腿、斜倒立、完全倒立、站直下落。不要翻过去又倒着翻回来；尾巴完整卷曲，不缩短。',
 'vertical_light':'四帧垂直跳近侧爪拍击：收爪、向前探爪、最大伸展打胸、收爪。双膝悬空，不能站在地上。',
 'vertical_heavy':'五帧垂直跳重爪下拍：收臂、抬粗臂、向前下劈、随势、收爪。保留起中收，头不随挥臂变大。',
 'diagonal_light':'四帧斜跳膝撞：收膝、近侧膝向前顶、膝撞最大伸展、收腿护架。远侧腿整条暗色，不能两条腿都亮。',
 'diagonal_heavy':'五帧斜跳重蹬：收腿、伸近腿、脚爪向前下方踹出、收腿、准备落地。粗长尾在身后平衡。',
 'air_crush':'六帧空中双爪下砸：双臂后收、抬起、双爪向前下猛砸、双臂压到底、随势、回护架。不可改成地面动作。',
 'dive':'五帧俯冲角撞：空中收腿、头胸转向右下、鼻角朝右下俯冲、保持冲撞角度、收头伸腿准备重落地。用鼻角出招，不冒用后作超振动波。',
 'chase_takeoff':'三帧追击跳：深屈膝、双脚重蹬地前倾、空中收腿举爪追上被击飞对手。追击跳是街机规则，非原剧专名。',
 'chase_light1':'四帧追击空中近爪一段：收近爪、近爪前拍、最大伸展、回收。保持悬空收腿，不改变头部比例。',
 'chase_light2':'四帧追击空中远爪二段：换暗色远爪、向前拍出、最大伸展、回收。必须和一段不同手臂且连贯。',
 'chase_end':'六帧追击终结双臂砸地：收双爪、双臂举起、向前下猛砸、压到底、屈身随势、伸腿落地。用双爪砸落对手触发弹地，不画火光。'}

def setup():
 profiles=read(WORK/'profiles.json');reg=read(WORK/'asset-registry.json');plan=read(ROOT/'content/fighters/gomora/production_plan.json');names={c['action']:c for c in plan['cells']}
 counts={'takeoff':2,'air_rise':2,'air_apex':1,'air_fall':2,'land':2,'flip_forward':4,'flip_back':4,'vertical_light':4,'vertical_heavy':5,'diagonal_light':4,'diagonal_heavy':5,'air_crush':6,'dive':5,'chase_takeoff':3,'chase_light1':4,'chase_light2':4,'chase_end':6}
 ticks={'takeoff':[1,2],'air_rise':[3,3],'air_apex':[2],'air_fall':[4,8],'land':[3,4],'flip_forward':[4,5,5,8],'flip_back':[4,5,5,8],'chase_takeoff':[1,1,1]}
 for a in ACTIONS:
  if a in profiles:continue
  n=counts[a];category='跳跃' if a in ACTIONS[:7]+['chase_takeoff'] else '空中攻击'
  profiles[a]=dict(name=names[a]['planned_name'] if a!='dive' else '俯冲角撞',frames=n,ticks=ticks.get(a,[3]*n),loop=False,category=category,single=False)
  reg['assets'][a]=dict(action=a,indices=list(range(n)),category=category)
  if a in names:names[a]['reference_frames']=n
 save(WORK/'profiles.json',profiles);save(WORK/'asset-registry.json',reg);save(ROOT/'content/fighters/gomora/production_plan.json',plan)

def pose(action,i,n):
 r=prepare_ruler();p={k:[x+64,y+56] for k,(x,y) in r['landmarks'].items()};p.update(elbow_near=[266,199],hand_near=[284,201],elbow_far=[296,197],hand_far=[318,210]);center=np.array([254.,223.])
 # 骨长不变，尾巴以定稿各节长度做圆弧卷曲，绝不截断骨链。
 segments=np.linalg.norm(np.diff(np.array(r['tail_centerline']),axis=0),axis=1);tail=[np.array([241.,231.])]
 for j,length in enumerate(segments):
  angle=math.pi+.22*j
  tail.append(tail[-1]+length*np.array([math.cos(angle),math.sin(angle)]))
 if action in ['takeoff','land','chase_takeoff']:
  bob=([24,6] if action=='takeoff' else [20,2] if action=='land' else [27,13,0])[i]
  for k in ['eye','nose_root','ear_root','skull_top','jaw','shoulder','neck','head','elbow_near','hand_near','elbow_far','hand_far']:p[k][1]+=bob
  p['hip'][1]+=bob*.65;p['knee_near']=[231,281];p['ankle_near']=[214,296];p['knee_far']=[294,280];p['ankle_far']=[305,296]
 else:
  p['knee_near']=[264,254];p['ankle_near']=[235,267];p['knee_far']=[285,248];p['ankle_far']=[278,276]
  for k in p:p[k]=[p[k][0],p[k][1]-20]
  tail=[v-[0,20] for v in tail];center-=np.array([0,20])
  if action in ['air_fall'] or (action in ['diagonal_heavy','vertical_heavy','dive'] and i==n-1):p['ankle_near']=[244,291];p['ankle_far']=[289,286]
 active={'vertical_light':{1:[316,185],2:[344,193]},'vertical_heavy':{1:[282,128],2:[343,210],3:[328,233]},'diagonal_light':{1:[300,230],2:[326,222]},'diagonal_heavy':{1:[291,252],2:[357,255],3:[314,266]},'air_crush':{1:[285,119],2:[339,200],3:[343,232]},'chase_light1':{1:[322,182],2:[345,193]},'chase_light2':{1:[325,184],2:[349,192]},'chase_end':{1:[283,117],2:[338,201],3:[343,239]}}
 if action in active and i in active[action]:
  target=active[action][i]
  if action=='diagonal_light':p['knee_near']=target;p['ankle_near']=[target[0]-25,target[1]+20]
  elif action=='diagonal_heavy':p['ankle_near']=target;p['knee_near']=[target[0]-26,target[1]-19]
  else:
   side='far' if action=='chase_light2' else 'near';p['hand_'+side]=target;p['elbow_'+side]=[(p['shoulder'][0]+target[0])/2,(p['shoulder'][1]+target[1])/2+6]
   if action in ['air_crush','chase_end']:p['hand_far']=[target[0]-6,target[1]-4];p['elbow_far']=[p['elbow_near'][0]-8,p['elbow_near'][1]-4]
 # 引导图先满足真实骨长；远目标不能把膝/爪画到两倍肢长外让GPT猜。
 def solve(start,end,a,b,hint):
  start=np.array(start,float);end=np.array(end,float);v=end-start;length=float(np.linalg.norm(v));u=v/max(.001,length)
  length=min(a+b-.05,max(abs(a-b)+.05,length));end=start+u*length
  along=(a*a-b*b+length*length)/(2*length);height=math.sqrt(max(0,a*a-along*along));base=start+along*u;normal=np.array([-u[1],u[0]])
  joint=min([base+height*normal,base-height*normal],key=lambda x:np.linalg.norm(x-np.array(hint)))
  return joint.tolist(),end.tolist()
 hip=np.array(p['hip']);shoulder=np.array(p['shoulder']);delta=shoulder-hip;desired=hip+delta/np.linalg.norm(delta)*r['bones']['torso'];shift=desired-shoulder
 for k in ['shoulder','neck','head','eye','nose_root','ear_root','skull_top','jaw','elbow_near','hand_near','elbow_far','hand_far']:p[k]=(np.array(p[k])+shift).tolist()
 for side in ['far','near']:
  if action=='diagonal_light' and side=='near' and i in active.get(action,{}):
   direction=np.array(p['knee_near'])-np.array(p['hip']);knee=np.array(p['hip'])+direction/np.linalg.norm(direction)*r['bones']['thigh'];v=np.array(p['ankle_near'])-knee;p['knee_near']=knee.tolist();p['ankle_near']=(knee+v/np.linalg.norm(v)*r['bones']['shin']).tolist()
  else:p['knee_'+side],p['ankle_'+side]=solve(p['hip'],p['ankle_'+side],r['bones']['thigh'],r['bones']['shin'],p['knee_'+side])
  p['elbow_'+side],p['hand_'+side]=solve(p['shoulder'],p['hand_'+side],32,28,p['elbow_'+side])
 tail_shift=np.array(p['hip'])+[-13,-1]-np.array(tail[0]);tail=[np.array(v)+tail_shift for v in tail]
 angle=([25,130,180,0][i] if action=='flip_forward' else [-25,-130,-180,0][i] if action=='flip_back' else [0,20,45,45,10][i] if action=='dive' else 0)
 theta=math.radians(angle);mat=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
 if angle:
  transform=lambda q:(mat@(np.array(q)-center)+[260,167]).tolist()
  p={k:transform(v) for k,v in p.items()};tail=[transform(v) for v in tail]
 # 引导也不能先把尾巴裁掉。完整骨架仅平移入格，不改变任何骨长。
 extrema=[]
 for k,v in p.items():
  radius=23 if k in ['hip','shoulder'] else 18 if k=='head' else 12 if 'knee' in k or 'elbow' in k else 9
  extrema.extend([np.array(v)-radius,np.array(v)+radius])
 for v in tail:extrema.extend([np.array(v)-8,np.array(v)+8])
 for polygon in r['horn_polygons'].values():
  horn=(np.array(polygon)+[64,56]-[293,159])@mat.T+np.array(p['head']);extrema.extend(horn)
 lo=np.array(extrema).min(0);hi=np.array(extrema).max(0);assert np.all(hi-lo<np.array(CELL)-8),(action,i,'完整骨架过大，不能裁尾')
 shift=np.maximum(4-lo,0)-np.maximum(hi-(np.array(CELL)-4),0)
 p={k:(np.array(v)+shift).tolist() for k,v in p.items()};tail=[np.array(v)+shift for v in tail]
 return p,[np.array(v).tolist() for v in tail],angle

def guide(action,indices,path):
 n=read(WORK/'profiles.json')[action]['frames'];cols=min(3,len(indices));rows=math.ceil(len(indices)/cols);im=Image.new('RGB',(512*cols,320*rows),'#f3f1e9');d=ImageDraw.Draw(im);records=[]
 for j,i in enumerate(indices):
  p,tail,angle=pose(action,i,n);ox=j%cols*512;oy=j//cols*320;tr=lambda q:(q[0]+ox,q[1]+oy)
  d.line([tr(q) for q in tail],fill='#584535',width=16)
  for a,b,w in [('hip','shoulder',45),('shoulder','neck',26),('neck','head',20),('hip','knee_far',22),('knee_far','ankle_far',16),('hip','knee_near',27),('knee_near','ankle_near',18),('shoulder','elbow_far',18),('elbow_far','hand_far',14),('shoulder','elbow_near',21),('elbow_near','hand_near',17)]:d.line((tr(p[a]),tr(p[b])),fill='#514638' if 'far' in b else '#ac8051',width=w)
  theta=math.radians(angle);mat=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
  for side in ['far','near']:
   poly=np.array(prepare_ruler()['horn_polygons'][side])+[64,56]-[293,159]
   poly=poly@mat.T+p['head'];d.polygon([tr(q) for q in poly],fill='#624735' if side=='far' else '#d4b47c')
  x,y=tr(p['head']);d.ellipse((x-18,y-17,x+18,y+17),fill='#ae8a5a');x,y=tr(p['eye']);d.ellipse((x-2,y-2,x+2,y+2),fill='#f9cc39')
  for k in ['hip','knee_near','ankle_near','knee_far','ankle_far']:
   x,y=tr(p[k]);d.ellipse((x-3,y-3,x+3,y+3),fill='#28b5c5')
  records.append(dict(frame=i,joints=p,tail_centerline=tail,rotation=angle))
 im.save(path);save(path.with_name('poses.json'),dict(action=action,frames=records,bones=prepare_ruler()['bones'],note='定稿骨长的完整骨架引导；不进运行资源'))
 return cols,rows

if __name__=='__main__':setup()

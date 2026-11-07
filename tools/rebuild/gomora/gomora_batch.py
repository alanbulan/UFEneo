"""哥莫拉独立分支：固定资产预记账 → GPT整帧 → 免费后处理 → 校准/选稿。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import argparse,copy,math,sys,time
from pathlib import Path
Path = _LayoutProjectPath
import numpy as np
from PIL import Image,ImageDraw
from gomora_qa import *
sys.path[:0]=[str(ROOT/'tools'),str(Path.home()/'.codex/skills/sprite-gen')]
import stage4_pilot as pilot,art_pipeline as art,process_phase2 as proc
from sprite_gen.frames.extract import _kcentroid_downscale,apply_palette,binarize_alpha
from qa_brake import Brake
import art.produce_character
produce_character.BRAKE_PATH=WORK/'brake.json'
pilot.RUN=WORK;pilot.LEDGER=WORK/'ledger.json'

ACTIONS=['idle','turn','walk_forward','walk_back','dash_start','dash','dash_stop','crouch_start','crouch','crouch_rise','light1','light2','light3','heavy','launcher','spin_heavy','crush','tackle','crouch_light','crouch_light2','sweep','slide']
TRIALS=[f'idle/frame-{i:02}' for i in range(5)]

def requires_standing(action,i,n):
 return action in ['idle','walk_forward','walk_back','turn','dash_start','dash','dash_stop'] or (action in ['light1','light2','light3','heavy','launcher','spin_heavy','crush','tackle'] and i in [0,n-1]) or action=='crouch_rise' and i==n-1

def standing_target(action,i,n):
 # 只取骨架中的角尖到脚底。身体前倾/呼吸允许改变投影，不把蹲姿硬拉成站姿。
 if action.startswith('walk_'):return 192-[2,0,-2,0,2,0,-2,0][i]
 if action=='idle':return 192-[0,1,2,2,1,0][i]
 if action in ['dash_start','dash','dash_stop']:
  lean={'dash_start':[10,22],'dash':[24,20,24,20],'dash_stop':[16,6,0]}[action][i]
  return round(192-lean*.45)
 return 192

def setup():
 ruler=prepare_ruler();WORK.mkdir(parents=True,exist_ok=True)
 if not pilot.LEDGER.exists():
  old=read(ROOT/'art/shared/production/stage4-pilot/ledger.json');rows=[r for r in old['requests'] if r['fighter']=='gomora']
  for r in rows:r['imported_from_shared_ledger']=True;r['original_ledger_sequence']=r['ledger_sequence'];r['ledger_sequence']=rows.index(r)+1
  save(pilot.LEDGER,dict(schema=1,authorization='用户哥莫拉分支第一批授权：无总预算；固定素材最多10次；只记本分支，导入历史定稿一次供累计。',limits=dict(per_asset=10),counting='真实提交前落账；失败/Alpha拒收/远端未知均计数；不按改名重置',requests=rows))
 if (WORK/'profiles.json').exists():return
 plan={r['action']:r for r in read(ROOT/'content/fighters/gomora/production_plan.json')['cells']}
 profiles={};registry={}
 for action in ACTIONS:
  r=plan[action];n=r['reference_frames'];loop=action in ['idle','walk_forward','walk_back','crouch']
  category='站立' if action in ['light1','light2','light3','heavy','launcher','spin_heavy','crush','tackle'] else '下蹲' if action.startswith('crouch') or action in ['sweep','slide'] else '移动'
  ticks=[8]*n if action=='idle' else [6]*n if action.startswith('walk_') else [2]*n if action in ['turn','dash_start','dash_stop'] else [3]*n if action=='dash' else [4]*n
  profiles[action]=dict(name=r['planned_name'],frames=n,ticks=ticks,loop=loop,category=category,single=loop or action in ['dash_start','dash','dash_stop'])
  # 最多八帧一条。crush九帧分明确起收两条，不改资产身份。
  groups=[(f'{action}/frame-{i:02}',[i]) for i in range(n)] if profiles[action]['single'] else [(action,list(range(n)))] if n<=8 else [(action+'/start',list(range(4))),(action+'/finish',list(range(4,n)))]
  for key,indices in groups:
   registry[key]=dict(action=action,indices=indices,category='标尺试跑' if key in TRIALS else category)
 save(WORK/'profiles.json',profiles);save(WORK/'asset-registry.json',dict(batch='gomora-batch1',fighters=['gomora'],assets=registry))
 # 定稿不动，只完善本角色运行画布和依据文件。
 p=ROOT/'content/fighters/gomora/palette.json';v=read(p);v['side_view_roles']['policy']='远侧整条手臂、整条腿、远侧月牙耳角由GPT原生画暗；肢体交叠处1px深轮廓；后处理仅全图量化，禁止区域换色。';v['side_view_roles']['far_side']['ear_horn_rgb']=[[118,83,51],[82,57,38]];save(p,v)
 (ROOT/'content/fighters/gomora/CANVAS.md').write_text('# 哥莫拉运行画布\n\n已审定稿384×256，脚底(192,248)，身高192像素（含月牙耳角）。运行格512×320，脚底(256,304)，定稿平移(64,56)进入格子，显示scale=1，绝不改变四人身高比例。所有尾尖和角都保留至少2像素透明余量；越界就拒收，不压缩尾长。图集最多四列，manifest.rects与每帧anchors为唯一采样依据。\n\n标尺、骨长、尾中轴及试跑记录见art/fighters/gomora/stage4/pilot/gomora/ruler.json。\n','utf-8')

def pose(action,i,n):
 """以定稿实测骨长作完整姿态引导；只是GPT输入，不进assets。"""
 r=prepare_ruler();p=copy.deepcopy(r['landmarks']);p={k:[x+64,y+56] for k,(x,y) in p.items()}
 p.update(elbow_near=[266,199],hand_near=[284,201],elbow_far=[296,197],hand_far=[318,210])
 phase=i/max(1,n-1);bob=0
 if action=='idle':bob=[0,1,2,2,1,0][i]
 elif action.startswith('walk_'):
  bob=[2,0,-2,0,2,0,-2,0][i];direction=1 if action=='walk_forward' else -1
  # 支撑脚匀速后移，摆动脚抬起；两段腿通过固定骨长IK求膝。
  near=[40,20,0,-20,-40,-20,0,20][i]*direction;far=-near
  calibrated=WORK/action/f'frame-{i:02}'/'skeleton-target.json'
  if calibrated.exists():
   measured_target=read(calibrated);near=measured_target['near_stride'];far=measured_target['far_stride']
  hip=np.array([254.,232.+bob]);p['hip']=hip.tolist()
  for side,x,ph in [('near',near,i),('far',far,(i+4)%8)]:
   ankle=np.array([254+x,295.-([0,0,0,0,0,9,15,8][ph])]);diff=ankle-hip;d=np.linalg.norm(diff);a=r['bones']['thigh'];b=r['bones']['shin']
   base=hip+diff/d*((a*a-b*b+d*d)/(2*d));h=math.sqrt(max(0,a*a-((a*a-b*b+d*d)/(2*d))**2));perp=np.array([-diff[1],diff[0]])/d
   p['knee_'+side]=(base+perp*h).tolist();p['ankle_'+side]=ankle.tolist()
 elif action in ['crouch_start','crouch','crouch_rise','crouch_light','crouch_light2','sweep','slide']:
  bob=25 if action not in ['crouch_start','crouch_rise'] else (12 if i==(0 if action=='crouch_start' else 1) else 25)
  p['knee_near']=[234,278];p['ankle_near']=[212,296];p['knee_far']=[295,277];p['ankle_far']=[300,296]
  for k in ['hand_near','hand_far','elbow_near','elbow_far']:p[k][1]+=bob
  p['hand_near']=[300,235+bob*.3];p['hand_far']=[322,237+bob*.3]
 for k in ['eye','nose_root','ear_root','skull_top','jaw','shoulder','neck','head']:
  p[k][1]+=bob
 p['hip'][1]+=0 if action.startswith('walk_') else bob*.4
 tail=np.array(r['tail_centerline'],dtype=float)+[64,56];tail[:,1]+=bob*.25
 active={
 'light1':{1:[279,194],2:[342,202],3:[326,210]},
 'light2':{1:[283,198],2:[343,198],3:[330,204]},
 'light3':{1:[269,202],2:[324,199],3:[341,202],4:[311,209]},
 'heavy':{1:[265,177],2:[278,152],3:[346,185],4:[331,216],5:[296,221]},
 'launcher':{1:[285,248],2:[302,241],3:[342,182],4:[318,152],5:[298,181]},
 'crush':{1:[268,169],2:[282,141],3:[294,124],4:[340,172],5:[347,219],6:[312,237],7:[296,222]},
 'crouch_light':{1:[277,247],2:[341,264]},
 'crouch_light2':{1:[282,250],2:[347,273]},
 }
 if action in active and i in active[action]:
  target=active[action][i];side='far' if action in ['light2','crouch_light2'] else 'near';p['hand_'+side]=target;p['elbow_'+side]=[(p['shoulder'][0]+target[0])/2,(p['shoulder'][1]+target[1])/2+5]
  if action in ['light3','launcher','crush']:p['hand_far']=[target[0]-5,target[1]-7];p['elbow_far']=[p['elbow_near'][0]-8,p['elbow_near'][1]-8]
 if action in ['tackle','slide','dash_start','dash','dash_stop']:
  lean={'tackle':[0,12,23,29,33,24,10,0],'slide':[0,12,23,29,33,24,10,0],'dash_start':[10,22],'dash':[24,20,24,20],'dash_stop':[16,6,0]}[action][i]
  for k in ['eye','nose_root','ear_root','skull_top','jaw','shoulder','neck','head']:p[k][0]+=lean;p[k][1]+=lean*.45
  if action=='dash':
   stride=[22,28,-22,-28][i];p['ankle_near']=[254+stride,291 if i%2==0 else 296];p['ankle_far']=[254-stride,287 if i%2==0 else 296]
 if action in ['spin_heavy','sweep']:
  if i in [3,4]:
   # 逐段保留定稿尾骨中轴长度；重排朝向，不能把旋转后越地面的整条尾移离尾根。
   segments=np.linalg.norm(np.diff(np.array(r['tail_centerline']),axis=0),axis=1);tail=[np.array(p['hip'],dtype=float)]
   for j,length in enumerate(segments):
    theta=(.18-.24*j/len(segments)) if action=='sweep' else (-.35-.25*j/len(segments))
    tail.append(tail[-1]+length*np.array([math.cos(theta),math.sin(theta)]))
   tail=np.array(tail)
 if action=='crouch':
  # 保持姿势必须接已合格crouch_start末帧，不能退回半蹲。
  # 仅姿势引导：最终仍由GPT完整生成，不裁切或复用该末帧作保持动画。
  p.update(eye=[315,219+i],head=[307,219+i],nose_root=[324,226+i],ear_root=[297,214+i],skull_top=[306,210+i],jaw=[314,236+i],neck=[298,234+i],shoulder=[285,240+i],hip=[249,269],knee_near=[225,285],ankle_near=[215,296],knee_far=[291,281],ankle_far=[303,296],elbow_near=[278,249],hand_near=[292,252],elbow_far=[311,249],hand_far=[329,260])
 return p,tail.tolist()

def guide(action,indices,path):
 from gomora_air import ACTIONS as AIR,guide as air_guide
 if action in AIR:return air_guide(action,indices,path)
 n=read(WORK/'profiles.json')[action]['frames'];cols=min(4,math.ceil(len(indices)/2)) if len(indices)>1 else 1;rows=math.ceil(len(indices)/cols)
 im=Image.new('RGB',(CELL[0]*cols,CELL[1]*rows),'#f3f1e9');d=ImageDraw.Draw(im);records=[]
 for j,i in enumerate(indices):
  ox=(j%cols)*CELL[0];oy=(j//cols)*CELL[1];p,tail=pose(action,i,n)
  transform=lambda q:(q[0]+ox,q[1]+oy)
  d.line([transform(t) for t in tail],fill='#584535',width=16)
  for a,b,w in [('hip','shoulder',45),('shoulder','neck',26),('neck','head',20),('hip','knee_far',22),('knee_far','ankle_far',16),('hip','knee_near',27),('knee_near','ankle_near',18),('shoulder','elbow_far',18),('elbow_far','hand_far',14),('shoulder','elbow_near',21),('elbow_near','hand_near',17)]:
   d.line((transform(p[a]),transform(p[b])),fill='#514638' if 'far' in b else '#ac8051',width=w)
  for k in ['hip','knee_near','ankle_near','knee_far','ankle_far']:
   x,y=transform(p[k]);d.ellipse((x-3,y-3,x+3,y+3),fill='#28b5c5')
  if action.startswith('walk_'):
   # 明确整只脚的朝向/足长；只画给GPT的骨长引导，不进入运行素材。
   # 交错时足部上下经过，不能把抬起脚朝下的爪尖误画成另一条大跨腿。
   for side in ['far','near']:
    x,y=p['ankle_'+side];foot=[(x-6,y-1),(x+7,y-1),(x+23,y+7),(x+23,y+10),(x-6,y+10)]
    d.polygon([transform(q) for q in foot],fill='#514638' if side=='far' else '#ac8051')
  x,y=transform(p['head']);d.ellipse((x-18,y-17,x+18,y+17),fill='#ae8a5a');x,y=transform(p['eye']);d.ellipse((x-2,y-2,x+2,y+2),fill='#f9cc39')
  delta=np.array(p['head'])-np.array([293,159]);ruler=prepare_ruler()
  for side in ['far','near']:
   poly=np.array(ruler['horn_polygons'][side])+[64,56]+delta
   d.polygon([transform(v) for v in poly],fill='#624735' if side=='far' else '#d4b47c')
  nose=np.array([[246,110],[260,98],[254,114],[248,117]])+[64,56]+delta
  d.polygon([transform(v) for v in nose],fill='#e4d1a3')
  records.append(dict(frame=i,joints=p,tail_centerline=tail))
 im.save(path);save(path.with_name('poses.json'),dict(action=action,frames=records,bones=prepare_ruler()['bones'],source='按哥莫拉定稿量骨长；仅姿势引导，不作最终素材'))
 return cols,rows

DESCRIPTIONS={
 'idle':'站在原地的重怪兽呼吸；六帧脚完全固定，眼部起伏仅0,1,2,2,1,0原生像素，尾巴轻摆但曲线长度不变。',
 'turn':'三帧真实转身：左侧前方、正背面、右侧前方。中间背面两耳角按透视，身体站高保持；不是镜像复制。',
 'walk_forward':'八帧沉重前走：接触A、下沉A、交错A、上升A、接触B、下沉B、交错B、上升B。腿骨长度固定，交错时两腿经过胯下，前倾护架，尾巴摆动平衡。',
 'walk_back':'八帧沉重后走：接触A、下沉A、交错A、上升A、接触B、下沉B、交错B、上升B。面朝右向左退，微后仰双爪护架，脚向后迈，腿长不缩，尾巴随步平衡。',
 'dash_start':'两帧冲刺起步，屈膝前倾蓄力然后后脚重蹬地，尾巴拖后。',
 'dash':'四帧跑步关键姿势：远腿前腾空、远腿前着地、近腿前腾空、近腿前着地；两腿交替，腾空帧两脚离地。',
 'dash_stop':'三帧制动：前脚插地、上身后仰、重心回到原待机护架。',
 'crouch_start':'两帧屈膝下蹲，尾巴向后拉平保持长度；半蹲到深蹲，头不缩。',
 'crouch':'两帧低蹲保持，只有1像素呼吸起伏，脚固定，不出击。',
 'crouch_rise':'两帧从低蹲伸腿起身，半蹲到原始站姿，头不缩。',
 'light1':'近侧亮色手爪向前快速拍击对手胸部：预备、抬臂、向前拍出、随势、收回。',
 'light2':'换远侧暗色手臂向前横拍：收肩、抬暗手、暗手拍出、随势、收回；近手保持护架。',
 'light3':'双臂从两侧合拢向前推砸：双肩后收、蓄势、双爪猛推、最大伸展、回收、护架。',
 'heavy':'前臂重砸：近侧粗臂后收、屈肘蓄力、抬至肩、前下劈砸到对手肩胸、随势、回臂、待机。不能和轻拍一样。',
 'launcher':'双臂上挑：屈膝、双爪下收、蹬腿、双臂自下向上挑起对手、抬至胸上、收臂、回护架。',
 'spin_heavy':'七帧转身甩尾：向前护架、反扭蓄势、背面对手、整条长尾横向甩向右侧对手腰胸、尾尖扫过最远、转回、待机。必须用尾巴打人，不用拳脚冒充。',
 'crush':'九帧双臂猛砸：准备、双臂后收、双臂抬起、举至头上、双臂猛砸向前下、最大砸击、屈膝随势、收臂、待机。',
 'tackle':'八帧鼻角与肩部冲锋：下沉、前倾、头角对准前方、蹬地冲撞、鼻角前伸、刹步、抬头、待机。身体冲撞不能画成出拳。',
 'crouch_light':'四帧低位近爪拍击：低蹲、近爪后收、向右前小腿高度拍出、回低蹲。',
 'crouch_light2':'四帧低位远爪二段：低蹲换手、暗远爪后收、向前脚踝高度拍出、回低蹲；与近爪一段区分。',
 'sweep':'七帧低位转身扫尾：低蹲、尾巴后卷蓄势、躯干转背、长尾贴地扫向右侧对手脚踝、尾尖达到最远、回转、回低蹲。保持尾中轴长度，不可用脚扫代替。',
 'slide':'八帧低身滑撞：低蹲、前倾、近腿前伸、低头鼻角朝右下冲出、低位最大伸展、刹停、起胯、回蹲。不是扫尾或普通冲锋。'}

def figures(im,expected):
 """组件行提取：完整人物连通域决定格子，容许GPT把两行排成一行。"""
 a=np.array(im);n,labels,stats,centers=cv2.connectedComponentsWithStats((a[:,:,3]>=200).astype('uint8'),8)
 maximum=int(stats[1:,4].max()) if n>1 else 0
 main=[i for i in range(1,n) if stats[i,4]>=maximum*.25]
 if len(main)!=expected:raise ValueError(f'完整人物连通域{len(main)}，请求{expected}；不裁断或拼接人物')
 # 只按实际整行聚类，头/尾姿态的细小重心变化不能改变帧序。
 order=[];remaining=sorted(main,key=lambda k:centers[k,1]);height=float(np.median(stats[main,3]))
 while remaining:
  cy=centers[remaining[0],1];row=[k for k in remaining if centers[k,1]-cy<height*.45];order.extend(sorted(row,key=lambda k:centers[k,0]));remaining=[k for k in remaining if k not in row]
 owned={i:[i] for i in main}
 for k in range(1,n):
  if k in main:continue
  if stats[k,4]<=3:continue # 原始分辨率≤3px的Alpha散点；不是原生人物的独立部件。
  # Alpha散点不默默删除；归给最近整帧，后面的孤岛门仍会报错。
  target=min(main,key=lambda m:np.linalg.norm(centers[k]-centers[m]));owned[target].append(k)
 result=[]
 for k in order:
  group=owned[k];x0=min(int(stats[g,0]) for g in group);y0=min(int(stats[g,1]) for g in group);x1=max(int(stats[g,0]+stats[g,2]) for g in group);y1=max(int(stats[g,1]+stats[g,3]) for g in group)
  if x0<1 or y0<1 or x1>=im.width or y1>=im.height:raise ValueError('GPT原图人物触边，角/尾可能已经裁切，不入库')
  # 极低Alpha噪点已由>=200二值标准排除；可见独立块保留并质检。
  cut=im.crop((x0,y0,x1,y1));mask=np.isin(labels[y0:y1,x0:x1],group).astype('uint8')*255;cut.putalpha(Image.fromarray(mask));result.append((cut,(x0,y0,x1,y1)))
 return result

def make_brief(key,feedback=''):
 entry=read(WORK/'asset-registry.json')['assets'][key];action=entry['action'];s=read(WORK/'profiles.json')[action];indices=entry['indices'];folder=WORK/key;folder.mkdir(parents=True,exist_ok=True)
 cols,rows=guide(action,indices,folder/'guide.png');cw,ch=768,512
 # 同样原生密度，生成时以2倍绘制。单格768×512；单帧用1152×768满足API最小面积。
 width,height=(1152,768) if len(indices)==1 else (cols*cw,rows*ch)
 # 三列单行的追击跳也须满足Image接口3:1上限；只增加透明留白，不改人物比例。
 height=max(height,math.ceil(width/3/16)*16)
 width=max(width,math.ceil(height/3/16)*16)
 from gomora_air import DESCRIPTIONS as AIR_DESCRIPTIONS
 prompt=f'''绘制已通过定稿的1966哥莫拉完整像素动作【{s['name']}】。{DESCRIPTIONS.get(action,AIR_DESCRIPTIONS.get(action,''))}
参考1=已审定稿全身；参考2=头部八倍特写；参考3=骨长姿势引导，仅用于姿势，绝不把关节圆点/背景画进成品。
本图按{cols}列{rows}行，不画网格，按行恰好{len(indices)}个完整人物，对应完整动作的帧号{indices}（从0开始），其余格透明。{('这是一个独立待机/移动帧，保持参考的头、胯、脚比例和相对位置。' if len(indices)==1 else '每格只画一个完整人物，人物间完全分离。')}
固定侧视朝右，转背仅在转身/甩尾规定相位。鼻角、左右月牙大耳角、褐色鳞甲、长尾全部完整。定稿原生含耳角身高192px，颅骨不含角长约34px；本图按该比例约2倍像素尺寸（单帧约3倍），头不能随蹲姿缩小，尾根至尖沿曲线约{prepare_ruler()['tail_length']:.0f}原生像素，卷起来也不能缩短。
每次整帧生成就画好远侧整条手臂、整条腿、远侧耳角暗色102,66,43/70,46,34，远侧甲片118,83,51/82,57,38；近侧亮褐171,121,76/134,87,53，近侧甲片206,161,103/160,116,72。远侧经过近胯/躯干后方处画1原生像素深色轮廓，近侧和躯干不被压暗，不画矩形暗块。亮暗身份跟同一肢体，不随换腿互换。
左上光源，1原生像素深色轮廓，硬边像素簇，≤32色，不要抗锯齿，不要文字、帧号、格线、烟尘、光效、残影、地面、投影。透明背景，真正PNG Alpha。保留耳角、鼻角与整条尾巴的安全边距。
比例硬要求：原生大腿{prepare_ruler()['bones']['thigh']:.1f}px、小腿{prepare_ruler()['bones']['shin']:.1f}px、胯到肩{prepare_ruler()['bones']['torso']:.1f}px、颈{prepare_ruler()['bones']['neck']:.1f}px；头壳面积约484原生像素，不含耳角。直立时脚底到眼中心约145px，脚底到最高耳角192px，脚底到颅骨顶154px。不能画成大头短腿、缩躯干的Q版怪兽。整条起止必须与参考4同一身高和眼高，不能小15%。'''+feedback
 refs=[rel(MODEL),rel(WORK/'head-reference-x8.png'),rel(folder/'guide.png')]
 idle=WORK/'idle/frame-00/selected.json'
 if idle.exists() and not action.startswith('walk_'):refs.append(rel(ROOT/read(idle)['folder']/'frame-0.png'))
 if action.startswith('walk_'):
  frame=indices[0];joints,_=pose(action,frame,s['frames']);near=joints['ankle_near'];far=joints['ankle_far']
  prompt+=f'\n本帧是步行相位{frame}，绝不能复制参考1的分腿站姿。以参考3为最高优先级的完整骨架，近侧亮腿脚踝在原生({near[0]:.0f},{near[1]:.0f})，远侧暗腿脚踝在({far[0]:.0f},{far[1]:.0f})；脚踝到脚尖只有{prepare_ruler()["bones"]["foot"]:.0f}px。两条腿的前后位置要真正交换，近腿有时在前，远腿有时在前，不得八帧都保持近腿后/远腿前。保持头身比例，双爪护架。'
  phase_text=(['近侧亮腿向右跨在前方落地，远侧暗腿在左后方；亮腿在右、暗腿在左。','近侧亮腿支撑在胯右下方，远侧暗腿从后方蹬离地，绝不能亮腿仍拉在左后。','近侧亮腿竖直撑在胯下；远侧暗腿抬膝经过近腿，双脚靠拢。','近侧亮腿撑在胯左下方；远侧暗腿向右前伸出，准备着地。','远侧暗腿向右前方落地，近侧亮腿拉在左后方。','远侧暗腿支撑在胯右下方；近侧亮腿蹬离地并向前摆，脚要靠拢。','远侧暗腿竖直撑在胯下，近侧亮腿抬膝经过暗腿；双脚靠拢不分腿。','远侧暗腿支撑在胯左下方，近侧亮腿向右前伸出准备落地。'] if action=='walk_forward' else ['近侧亮腿跨在左后方落地，远侧暗腿在右前方，身体面朝右向左退。','近侧亮腿支撑在胯左下方，远侧暗腿从右前方收脚。','近侧亮腿竖直撑在胯下，远侧暗腿抬膝从前方往后经过，双脚靠拢。','近侧亮腿支撑在胯右下方，远侧暗腿向左后伸出准备落地。','远侧暗腿在左后方落地，近侧亮腿在右前方；暗腿在左，亮腿在右。','远侧暗腿支撑在胯左下方，近侧亮腿从前方收脚，脚要靠拢。','远侧暗腿竖直撑在胯下，近侧亮腿抬膝经过暗腿往后摆，双脚靠拢。','远侧暗腿支撑在胯右下方，近侧亮腿向左后伸出准备着地。'])[frame]
  prompt+='\n最重要的脚位和远近身份：'+phase_text
 if action=='crouch' and (WORK/'crouch_start/selected.json').exists():
  source=ROOT/read(WORK/'crouch_start/selected.json')['folder']/'frame-1.png';refs.append(rel(source));prompt+='\n最后一张参考为本角色已合格下蹲末帧。保持它的深蹲高度、脚位、头颈朝向和护架，只做1原生像素呼吸；绝不能重新站成半蹲。'
 target=WORK/key/'pose-target.json'
 if target.exists():prompt+='\n本帧目标：'+read(target)['prompt']
 extra=WORK/key/'extra-references.json'
 if extra.exists():
  refs.extend(read(extra)['references']);prompt+='\n'+read(extra).get('prompt','')
 category='移动' if (WORK/'calibration-approved.json').exists() and key in TRIALS else entry['category']
 v=dict(model='gpt-image-2.5-sunburst',fighter='gomora',asset_key=key,quality='high',asset_kind='character',size=f'{width}x{height}',asset_registry=rel(WORK/'asset-registry.json'),category=category,references=refs,prompt=prompt,columns=cols,rows=rows)
 save(folder/'brief.json',v);return folder/'brief.json'

def process(key,row):
 entry=read(WORK/'asset-registry.json')['assets'][key];action=entry['action'];s=read(WORK/'profiles.json')[action];brief=read(ROOT/row['brief']);raw=ROOT/row['output'];dest=WORK/key/f'take-{row["sequence"]:02}';dest.mkdir(parents=True,exist_ok=True)
 if not raw.exists():save(dest/'qa.json',dict(issues=['无透明成品（失败/Alpha拒收/远端未知）']));return dest
 im=Image.open(raw).convert('RGBA');art.require_transparency(im)
 cells=figures(im,len(entry['indices']))
 source_views={}
 overrides=WORK/'source-curation.json'
 if overrides.exists():
  source_views=read(overrides).get(sha(raw),{});order=source_views.get('order')
  if order:
   assert sorted(order)==list(range(len(cells)));cells=[cells[i] for i in order]
 heads=[];issues=[];measurements=[]
 is_hidden=lambda fi:False if entry.get('head_visible') else fi in source_views['hidden_head_frames'] if 'hidden_head_frames' in source_views else (action=='turn' and fi==1) or (action in ['spin_heavy','sweep'] and fi==2)
 for i,(cell,bounds) in enumerate(cells):
  fi=entry['indices'][i];hidden=is_hidden(fi)
  from gomora_air import ACTIONS as AIR
  angles=list(range(-180,181,15)) if action in AIR else [-20,-10,0,10,20] if action in ['idle','walk_forward','walk_back','crouch'] else None
  h=None if hidden else facing_head(cell,cell.height/192,angles,'left' if action=='turn' and fi==0 else 'right')
  measurements.append(h)
 palette=read(ROOT/'content/fighters/gomora/palette.json')['colors']
 for i,(cell,bounds) in enumerate(cells):
  # 临时测量图约原生密度；仅搜索头部，最终比例由稳定颅骨决定。
  approx=cell.height/192
  # 定稿的头只有几十像素：先缩临时图会改变角根，必须在原始像素上测。
  hm=measurements[i];fi=entry['indices'][i];hidden=is_hidden(fi)
  angles=list(range(-180,181,15)) if action in AIR else None
  standing=requires_standing(action,fi,s['frames'])
  if hm is None and not hidden:issues.append(f'frame {i}: head: 头部不可测');continue
  target_height=standing_target(action,fi,s['frames'])
  if standing:factor=target_height/cell.height
  elif hidden:
   before=next((j for j in range(i-1,-1,-1) if measurements[j]),None);after=next((j for j in range(i+1,len(cells)) if measurements[j]),None)
   if before is None or after is None:issues.append(f'frame {i}: head: 遮挡缺少前后比例');continue
   t=(i-before)/(after-before);factor=(1-t)/measurements[before]['scale']+t/measurements[after]['scale']
  else:factor=1/hm['scale']
  # 仅明确直立帧同时满足站高门：在头部允许区间内选站高基准，再独立复测成品头。
  # 下蹲、攻击生效、起跳/躺姿绝不走这条，不能按所有姿态的外框归一。
  # 原始裁片上的粗测和原生量化后的头壳测量有取样误差，尤其是低蹲。
  # 反馈只重算整个人物的统一比例，每次从GPT原图重新网格还原，不缩放局部/旧成品。
  feedback=[];scale_bracket={}
  for normalization_pass in range(7):
   snapped,pitch,phase=proc.snap_for_scale(cell,factor)
   logical=_kcentroid_downscale(snapped,max(1,round(cell.width*factor)),max(1,round(cell.height*factor)));binarize_alpha(logical);logical=apply_palette(logical,palette)
   measured=None if hidden else facing_head(logical,angles=angles,facing='left' if action=='turn' and fi==0 else 'right',hint=(np.array(hm['eye'])*factor).tolist() if hm else None)
   if not measured or abs(measured['scale']-1)<=.075:break
   # 直立按站高缩放后只核对头，不为过头部门改变站高比例。
   if standing:break
   scale_bracket['small' if measured['scale']<1 else 'large']=factor
   proposed=factor/measured['scale']
   # 原生网格量化会使尺度反馈在一大一小间跳动。只对整个GPT人物二分取样，
   # 不缩放局部，也不在直立站高流程里为了头部门改变比例。
   if 'small' in scale_bracket and 'large' in scale_bracket:
    proposed=(scale_bracket['small']+scale_bracket['large'])/2
   feedback.append(dict(before_factor=factor,measured_scale=measured['scale'],new_factor=proposed,method='整帧尺度反馈/量化跳变时二分'))
   if abs(proposed-factor)<.00001:break
   if normalization_pass==6:break # 最终record.scale必须是实际生成logical所用比例。
   factor=proposed
  if logical.width>CELL[0]-4 or logical.height>CELL[1]-4:issues.append(f'frame {i}: layout: 原生画布不足，不缩尾');continue
  # 以两只脚低处的接地区间中心定水平锚；长尾不参加根锚测量。
  a=np.array(logical);mask=a[:,:,3]>0;ys,xs=np.where(mask);low=np.flatnonzero(mask[-24:].any(0));split=np.split(low,np.where(np.diff(low)>8)[0]+1)
  # 脚趾间透明缝不能被误数为多只脚；取两只脚的完整落足带中点。
  spans=[v for v in split if len(v)>=8];spans=spans[-2:];foot_x=float(np.mean([(v[0]+v[-1])/2 for v in spans])) if spans else float(np.median(low))
  origin=foot_origin(logical,facing='left' if action=='turn' and fi==0 else 'right')
  manual_origin=WORK/key/f'foot-origin-{sha(raw)}.json'
  if manual_origin.exists():
   mark=read(manual_origin);assert mark['source_sha256']==sha(raw)
   frame_mark=mark.get('frames',{}).get(str(fi),mark)
   if 'logical_x' in frame_mark:origin=dict(x=frame_mark['logical_x'],method='实帧双足趾爪人工标点；远足被阴影压暗时不能只取亮足',marks=frame_mark)
  if origin:foot_x=origin['x']
  offset=(round(ANCHOR[0]-foot_x),ANCHOR[1]-logical.height);canvas=Image.new('RGBA',CELL)
  if offset[0]<2 or offset[0]+logical.width>CELL[0]-2 or offset[1]<2:issues.append(f'frame {i}: layout: 尾/角越界');continue
  canvas.alpha_composite(logical,offset);p=dest/f'frame-{i}.png';canvas.save(p)
  # 保存未经任何区域换色的量化结果作为逐像素基线。
  canvas.save(dest/f'color-source-{i}.png');h=None if hidden else facing_head(canvas,angles=angles,facing='left' if action=='turn' and fi==0 else 'right',hint=(np.array(hm['eye'])*factor+offset).tolist() if hm else None)
  q=validate_frame(canvas,h,standing,hidden,target_height);issues.extend(f'frame {i}: {x}' for x in q['issues'])
  if s['loop'] and h and not h.get('eye_detected',True):issues.append(f'frame {i}: loop_target: 循环必须用成品可见黄眼实测，不能用原图定位提示当眼高')
  target=WORK/key/'pose-target.json'
  if target.exists() and h:
   for axis,(lo,hi) in read(target).get('eye_bounds',{}).items():
    v=h['eye'][int(axis)]
    if not lo<=v<=hi:issues.append(f'frame {i}: loop_target: 眼部{axis}坐标{v:.3f}不在保留帧组成的{lo}–{hi}平滑区间')
  tail=dict(status='纯人工复核；见tail-landmarks.json的尾根/尾尖，废弃自动尾中轴',root=None,tip=None)
  record=dict(frame=i,action_frame=entry['indices'][i],image=p.name,image_sha256=sha(p),source=rel(raw),source_sha256=sha(raw),source_bounds=list(bounds),scale=factor,normalization_feedback=feedback,offset=list(offset),foot_anchor=list(ANCHOR),foot_origin=origin,raw_head=hm,measurement=h,tail=tail,head_hidden=hidden,head_policy='背面直立站高' if hidden and action=='turn' else '前后可测头部尺度插值，需人工复核' if hidden else '固定颅骨',**{k:v for k,v in q.items() if k not in ['head','issues']})
  heads.append(record)
 save(dest/'head-qa.json',dict(fighter='gomora',reference=prepare_ruler(),frames=heads,issues=issues,scale_policy='upright-skeleton-standing-primary-head-secondary; non-upright-fixed-skull'))
 save(dest/'qa.json',dict(asset=key,request=row['ledger_sequence'],issues=issues,frames=len(heads),raw=rel(raw),direct_gpt_output=True,manual_review='远侧身份/角/尾长/动作连续性待整条目视'))
 return dest

def generate(key,once=False):
 setup();folder=WORK/key
 if (folder/'selected.json').exists() or (folder/'blocked.json').exists():return
 own=lambda:[r for r in read(pilot.LEDGER)['requests'] if r['action']==key]
 def used():
  reg=read(WORK/'asset-registry.json')['assets'];entry=reg[key];counts={i:0 for i in entry['indices']}
  for row in read(pilot.LEDGER)['requests']:
   e=reg.get(row['action'],{})
   if e.get('action')==entry['action']:
    for i in set(e['indices'])&counts.keys():counts[i]+=1
  return max(counts.values())
 while used()<10:
  brake=Brake(WORK/'brake.json')
  entry=read(WORK/'asset-registry.json')['assets'][key];profile=read(WORK/'profiles.json')[entry['action']]
  checks=['layout','island','alpha','palette']+(['standing'] if any(requires_standing(entry['action'],fi,profile['frames']) for fi in entry['indices']) else [])
  from gomora_revision import AIR as SIZE_REWORK_AIR
  if entry['action'] in SIZE_REWORK_AIR:checks.append('raw_head_calibration')
  if brake.blocked(checks):save(folder/'blocked.json',dict(status='待人工',reason='同一门连续拒收3个不同帧，暂停并诊断',paused={k:v for k,v in brake.state['paused'].items() if k in checks}));return
  before=len(own());feedback=''
  if own():
   p=folder/f'take-{own()[-1]["sequence"]:02}/qa.json'
   if p.exists():feedback='\n上一稿问题：'+str(read(p)['issues'][:4])+'。纠正上述问题，不能改身份或换姿势。'
  try:row=pilot.generate_action('gomora',key,make_brief(key,feedback))
  except Exception as exc:
   if len(own())==before:raise
   row=own()[-1];print(key,'请求结果',type(exc).__name__,flush=True)
   message=str(exc)
   if message.startswith(('Image API','Image response','Alpha QA failed','Character image requires')):
    save(folder/f'request-{row["sequence"]:02}-failure.json',dict(request=row['ledger_sequence'],safe_diagnostic=message,credentials_or_response_body_logged=False))
  try:dest=process(key,row);q=read(dest/'qa.json')
  except Exception as exc:
   dest=folder/f'take-{row["sequence"]:02}';dest.mkdir(parents=True,exist_ok=True);q=dict(issues=[type(exc).__name__+': '+str(exc)]);save(dest/'qa.json',q)
  if (dest/'head-qa.json').exists():
   records={r['frame']:r for r in read(dest/'head-qa.json')['frames']}
   for i,fi in enumerate(entry['indices']):
    r=records.get(i);local=[x for x in q['issues'] if x.startswith(f'frame {i}:')]
    checks={k:not any(k+':' in t for t in local) for k in ['layout','island','alpha','palette']}
    if requires_standing(entry['action'],fi,profile['frames']):checks['standing']=not any('standing:' in t for t in local)
    brake.record(f'{key}/frame-{i:02}',checks,dest/r['image'] if r else ROOT/row['output'])
  print(key,'attempt',row['sequence'],q['issues'][:3],flush=True)
  if not q['issues']:
   save(folder/'selected.json',dict(folder=rel(dest),request=row['ledger_sequence'],status='数值门通过，待逐帧视觉复核'));return
  if once:return
 save(folder/'blocked.json',dict(status='待人工',reason='固定素材10次仍未通过，不改名重算；继续下一项'))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['setup','generate','trial']);p.add_argument('--key',nargs='+');p.add_argument('--once',action='store_true');a=p.parse_args();setup()
 if a.command=='trial':
  for key in TRIALS:generate(key,True)
 elif a.command=='generate':
  for key in a.key:
   try:generate(key,a.once)
   except Exception as exc:print(key,type(exc).__name__,str(exc),flush=True)

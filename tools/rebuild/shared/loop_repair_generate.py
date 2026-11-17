"""本分支独立GPT整帧请求。只量化全图，禁止区域换色、拼肢体或画最终人物。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
from types import SimpleNamespace
from datetime import datetime,timezone
import argparse,copy,hashlib,math,shutil,sys,time
import cv2,numpy as np
from contextlib import contextmanager
from PIL import Image,ImageDraw
from head_scale import ROOT,read,save,sha,font
from loop_repair_plan import RUN,REPORT,WORK,rel,old_frame,snapshot
import head_size,island_qa,process_phase2 as proc,loop_qa
sys.path.insert(0,str(ROOT/'tools'))
import art.pipeline,produce_character
from qa_brake import Brake
produce_character.BRAKE_PATH=WORK/'brake.json'

MODEL='gpt-image-2.5-sunburst'


@contextmanager
def ledger_lock():
    path=WORK/'ledger.lock'
    for _ in range(1200):
        try:handle=path.open('x');handle.close();break
        except FileExistsError:time.sleep(.05)
    else:raise ValueError('本分支台账写锁超时')
    try:yield
    finally:path.unlink()


def knee(hip,ankle,upper,lower):
    h=np.array(hip,dtype=float);a=np.array(ankle,dtype=float);v=a-h;d=np.linalg.norm(v)
    if d>upper+lower or d<abs(upper-lower):raise ValueError('目标超过实测骨长，不能拉长腿')
    u=v/d;q=(upper*upper-lower*lower+d*d)/(2*d);p=h+u*q;b=math.sqrt(max(0,upper*upper-q*q));n=np.array([-u[1],u[0]])
    return max([p+n*b,p-n*b],key=lambda p:p[0]).tolist()


def foot_features(im,fighter,windows=None):
    a=np.asarray(im);rgb=a[:,:,:3].astype(float);v=a[:,:,3]>0;yy,xx=np.indices(v.shape);mean=rgb.mean(2);r,g,b=rgb.transpose(2,0,1);result={}
    for side in ['near','far']:
        if fighter=='ultraman':mask=v&(yy>im.height-62)&(rgb.max(2)-rgb.min(2)<40)&(mean>110)&((mean>=184) if side=='near' else (mean<184))
        else:
            mask=v&(yy>im.height-50)&(rgb.max(2)-rgb.min(2)<12)&((mean>=45)&(mean<80) if side=='near' else (mean>=13)&(mean<45))
        if windows:
            tx,ty=windows[side]['x'],windows[side]['bottom'];mask&=(abs(xx-tx)<19)&(abs(yy-ty)<15)
        ys,xs=np.where(mask)
        if not len(xs):raise ValueError(side+'脚部没有足够像素')
        bottom=int(ys.max());sel=ys>=bottom-4;ys,xs=ys[sel],xs[sel]
        if fighter=='zetton' and windows is None:
            # 暗轮廓也在亮脚外缘；取最集中横向分量，报告时逐帧目视复核。
            n,ls,stats,cs=cv2.connectedComponentsWithStats((mask&(yy>=bottom-4)).astype('uint8'),8)
            good=[j for j in range(1,n) if stats[j,4]>=2]
            if good:
                j=max(good,key=lambda j:stats[j,4]);ys,xs=np.where(ls==j)
        result[side]=dict(x=float(xs.mean()),y=float(ys.mean()),bottom=bottom,bounds=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],pixels=len(xs))
    return result


def old_foot_boxes(fighter,action,index):
    if fighter=='ultraman':
        path=ROOT/('art/fighters/ultraman/stage2/legacy/walk_forward_final/foot-boxes.json' if action=='walk_forward' else 'art/fighters/ultraman/stage2/legacy/walk_back_single/foot-boxes.json')
        boxes=read(path)[str(index)];r=next(r for r in read(ROOT/'art/shared/production/head-scale/audit.json')['rows'] if r['fighter']==fighter and r['action']==action and r['frame']==index)
        sx,sy=r['old_to_new']['scale'];dx,dy=r['old_to_new']['translation']
        return {side:[round(x0*sx+dx),round(y0*sy+dy),round(x1*sx+dx),min(192,round(y1*sy+dy))] for side,(x0,y0,x1,y1) in boxes.items()}
    forward=[[[141,235,173,248],[82,231,108,248]],[[129,234,157,248],[86,225,113,245]],[[118,236,146,248],[92,219,119,241]],[[80,232,111,248],[133,225,169,245]],[[77,229,106,248],[129,234,165,248]],[[84,229,113,248],[132,235,163,248]],[[120,224,149,243],[109,235,137,248]],[[136,228,168,245],[87,235,117,248]]]
    back=[[[78,230,108,248],[134,235,165,248]],[[108,233,133,248],[128,233,155,248]],[[140,233,174,248],[79,230,110,248]],[[131,233,158,248],[113,232,137,248]]]
    near,far=(forward if action=='walk_forward' else back)[index];return dict(near=near,far=far)


def measured_feet(im,fighter,boxes):
    a=np.array(im);rgb=a[:,:,:3].astype(float);result={}
    for side in ['near','far']:
        x0,y0,x1,y1=boxes[side];roi=(a[y0:y1,x0:x1,3]>0)
        colors=rgb[y0:y1,x0:x1];m=colors.mean(2)
        if fighter=='ultraman':roi&=(colors.max(2)-colors.min(2)<40)&(m>110)&((m>=184) if side=='near' else (m<184))
        else:roi&=(colors.max(2)-colors.min(2)<14)&(m<90)&(m>10)
        ys,xs=np.where(roi)
        if len(xs)<3:raise ValueError(side+'脚部测量ROI内没有足够像素：'+str(boxes[side]))
        result[side]=dict(x=float(xs.mean()+x0),y=float(ys.mean()+y0),bottom=int(ys.max()+y0),bounds=boxes[side],pixels=len(xs))
    return result


def eye_feature(im,fighter,head):
    if fighter=='zetton':return __import__('idle_qa').feature(im,fighter,dict(hint=head['center'])),None
    a=np.array(im);r,g,b=a[:,:,:3].astype(int).transpose(2,0,1);yy,xx=np.indices(a.shape[:2]);cx,cy=head['center']
    mask=(a[:,:,3]>0)&(abs(xx-cx)<24)&(abs(yy-cy)<20)&(r>90)&(g>50)&(r-b>40)&(g-b>25)
    n,ls,stats,cs=cv2.connectedComponentsWithStats(mask.astype('uint8'),8)
    good=[j for j in range(1,n) if stats[j,4]>=2]
    if not good:raise ValueError('新帧完整近眼无法定位')
    j=max(good,key=lambda j:stats[j,4]);x,y,w,h,area=map(int,stats[j]);bounds=[x,y,x+w,y+h]
    return [(x+x+w-1)/2,(y+y+h-1)/2],bounds


def geometry(fighter):
    # 定稿原生网格的关节中心；只用于GPT姿势约束，不是运行时骨骼。
    joints=({'hip':[95,123],'knee':[77,148],'ankle':[59,178],'toe':[74,183],'head_top':[98,42],'neck':[98,78]} if fighter=='ultraman' else {'hip':[124,180],'knee':[107,210],'ankle':[90,242],'toe':[105,247],'head_top':[123,100],'neck':[122,140]})
    return dict(model=f'assets/fighters/{fighter}/model-native.png',model_sha256=sha(ROOT/f'assets/fighters/{fighter}/model-native.png'),joints=joints,thigh=math.dist(joints['hip'],joints['knee']),shin=math.dist(joints['knee'],joints['ankle']),trunk=math.dist(joints['hip'],joints['neck']),foot_length=16,method='在已审定稿像素网格标注关节中心；双腿固定股/胫长的姿势引导，不处理最终人物区域')


def prepare(only=None):
    data=snapshot();plan=read(RUN/'plan.json');registry=read(RUN/'registry.json') if only else {}
    for fighter in ['ultraman','zetton']:
        if only and not any(key.startswith(fighter+'/') for key in only):continue
        g=geometry(fighter);save(RUN/fighter/'model-geometry.json',g)
        model=Image.open(ROOT/g['model']).convert('RGBA');model.resize((model.width*4,model.height*4),Image.Resampling.NEAREST).save(RUN/fighter/'model-reference-x4.png')
        for key,r in plan.items():
            if only and key not in only:continue
            if r['fighter']!=fighter or r.get('single_frame_impossible'):continue
            action=r['action'];original=data[fighter]['actions'][action]
            for i in r['frames']:
                folder=RUN/fighter/action/f'frame-{i:02}';folder.mkdir(parents=True,exist_ok=True)
                im=old_frame(fighter,action,i);cell=im.width;anchor=[cell//2,cell-8]
                im.resize((cell*4,cell*4),Image.Resampling.NEAREST).save(folder/'original-x4.png')
                target=dict(fighter=fighter,action=action,frame=i,eye=[r.get('target_x',np.array(original['centers'])[:,0].tolist())[i],r['target_y'][i]],anchor=anchor,original_sha256=sha(RUN/'before'/fighter/action/f'frame-{i:02}.png'))
                if action=='stun' and fighter=='ultraman':target['eye'][0]=original['centers'][[0,0,3,3,4,0][i]][0]
                if action=='charge' and fighter=='zetton':target['eye']=[145,[125,126,126,125][i]]
                guide=Image.new('RGBA',im.size);d=ImageDraw.Draw(guide)
                if action.startswith('walk_'):
                    boxes=old_foot_boxes(fighter,action,i);feet=measured_feet(im,fighter,boxes);target['feet']=feet;target['foot_boxes']=boxes
                    # 以眼睛目标和定稿躯干长确定髋；脚位全部读取旧正式像素。
                    ex,ey=target['eye'];neck=[ex-7,ey+(16 if fighter=='ultraman' else 23)];hip=[ex-10,neck[1]+g['trunk']]
                    legs={}
                    for side in ['far','near']:
                        f=feet[side];ankle=[f['x']-4,f['bottom']-5]
                        try:kn=knee(hip,ankle,g['thigh'],g['shin'])
                        except ValueError:
                            # 按真实脚位选择满足固定腿长的髋高，不改变脚；将差额写进引导诊断。
                            maxreach=g['thigh']+g['shin']-.5;dy=math.sqrt(max(1,maxreach**2-(ankle[0]-hip[0])**2));hip[1]=max(hip[1],ankle[1]-dy);kn=knee(hip,ankle,g['thigh'],g['shin'])
                        legs[side]=dict(hip=list(hip),knee=kn,ankle=ankle)
                    target.update(legs=legs,hip=hip,neck=neck,bone_geometry=rel(RUN/fighter/'model-geometry.json'))
                    for side,color in [('far','#71666d'),('near','#df493e')]:
                        leg=legs[side];d.line([tuple(leg[k]) for k in ['hip','knee','ankle']],fill=color,width=9,joint='curve');f=feet[side];d.ellipse((f['x']-9,f['bottom']-4,f['x']+8,f['bottom']),fill=color)
                    d.line([tuple(hip),tuple(neck)],fill='#df493e',width=22)
                    for side,color,dx in [('far','#71666d',1),('near','#df493e',-5)]:
                        if action=='walk_back':pts=[(neck[0]+dx,neck[1]+3),(neck[0]-9+dx,neck[1]+21),(neck[0]+15+dx,neck[1]+10)]
                        else:pts=[(neck[0]+dx,neck[1]+3),(neck[0]+dx+(14 if i<4 else -10),neck[1]+22),(neck[0]+dx+(23 if i<4 else -17),neck[1]+34)]
                        d.line(pts,fill=color,width=7,joint='curve')
                    ex,ey=target['eye'];d.ellipse((ex-17,ey-20,ex+5,ey+11),fill='#dfdfdf')
                elif fighter=='zetton' and action=='charge':
                    # 每帧完全相同的胯/膝/脚，头部只呼吸1px；手臂是唯一明显颤动。
                    hip=[128,188];neck=[139,148];feet={'near':dict(x=89,bottom=247),'far':dict(x=157,bottom=247)};target.update(hip=hip,neck=neck,feet=feet)
                    for side,c in [('far','#71666d'),('near','#df493e')]:
                        ankle=[feet[side]['x']-4,242];kn=knee(hip,ankle,g['thigh'],g['shin']);d.line([tuple(hip),tuple(kn),tuple(ankle)],fill=c,width=12,joint='curve');d.ellipse((feet[side]['x']-9,242,feet[side]['x']+8,247),fill=c)
                    d.line([tuple(hip),tuple(neck)],fill='#df493e',width=27);ex,ey=target['eye'];d.ellipse((ex-18,ey-21,ex+7,ey+19),fill='#33333a')
                    for dx,c in [(-9,'#71666d'),(4,'#df493e')]:d.line([(139+dx,151),(145+dx,175),(142+dx,190+[0,1,0,-1][i])],fill=c,width=9,joint='curve')
                elif fighter=='ultraman' and action=='stun':
                    # 第二种引导：用已审0帧骨长重建全身平涂姿势，不让旧小帧的头身比误导。
                    ex,ey=target['eye'];neck=[ex-6,81];hip=[95,125]
                    for pts,color in [([(95,125),(76,150),(60,178)],'#71666d'), ([(95,125),(120,149),(132,178)],'#df493e')]:
                        d.line(pts,fill=color,width=10,joint='curve');x,y=pts[-1];d.ellipse((x-8,y-3,x+10,183),fill=color)
                    d.line([tuple(hip),tuple(neck)],fill='#df493e',width=26)
                    d.line([(98,86),(85,110),(81,135)],fill='#71666d',width=8,joint='curve');d.line([(106,87),(116,110),(122,133)],fill='#df493e',width=8,joint='curve')
                    d.ellipse((ex-14,ey-21,ex+8,ey+10),fill='#dddde1');target.update(neck=neck,hip=hip,guide_method='按已审0/3/4骨长和站高的整帧骨架约束；旧小帧只提供摇晃方向')
                else:
                    # 原帧全身的平涂剪影仅作参考；眩晕小帧按正确头部比例整体放大再放到眼高目标。
                    b=im.getbbox();scale=(140/(b[3]-b[1])) if fighter=='ultraman' and action=='stun' else 1
                    silhouette=Image.new('RGBA',im.size,'#b65a59');silhouette.putalpha(im.getchannel('A'))
                    silhouette=silhouette.resize((round(cell*scale),round(cell*scale)),Image.Resampling.NEAREST)
                    oldxy=original['centers'][i];dx=round(target['eye'][0]-oldxy[0]*scale);dy=round(target['eye'][1]-oldxy[1]*scale);guide.alpha_composite(silhouette,(dx,dy))
                ex,ey=target['eye'];d=ImageDraw.Draw(guide);d.ellipse((ex-2,ey-1,ex+2,ey+1),fill='#ffdd40')
                if 'legs' in target:
                    for leg in target['legs'].values():
                        for joint,c in [('hip','#48d8ff'),('knee','#e9d441'),('ankle','#61e892')]:
                            x,y=leg[joint];d.ellipse((x-1,y-1,x+1,y+1),fill=c)
                guide.save(folder/'guide-native.png');guide.resize((cell*4,cell*4),Image.Resampling.NEAREST).save(folder/'guide-x4.png');save(folder/'target.json',target)
                registry[f'{fighter}/{action}/frame-{i:02}']=dict(folder=rel(folder),target=target)
    save(RUN/'registry.json',registry);print('准备',len(registry),'个固定帧；未生成')


def prompt_for(target,feedback=''):
    f,a,i=target['fighter'],target['action'],target['frame'];cell=target['anchor'][1]+8;name='初代奥特曼C型' if f=='ultraman' else '宇宙恐龙杰顿'
    identity=('银色C型面具，黄色眼部，头顶小鳍，胸口蓝色计时器，原有红银花纹。' if f=='ultraman' else '黑色头躯，完整双触角，脸部中央竖长橙黄发光体，胸前双发光体，浅奶白节状手臂和大腿，黑色手和足。')
    action={'walk_forward':'维持原图这一帧前走的双腿相位、双脚位置和摆臂方向，只校正身体高度，不加大步子','walk_back':'维持原图这一帧后退的双腿相位和护架，只校正身体高度，始终朝右','stun':'原帧的眩晕摇晃方向保持一致，低垂双臂、膝微弯、身体失衡；不要恢复战斗护架','idle':'双脚钉住，保持相邻帧相同的待机护架，只有轻微呼吸','charge':'紧绷身体蓄力，双臂低垂或握拳在腰侧，眼睛位置稳定，不蹲起、不抬胸伸膝'}[a]
    p=(f'只输出一张完整{name}的整帧像素画：{a}第{i}帧。真正透明背景。附件1是要修复的当前正式帧，附件2是唯一身份/比例/配色定稿，附件3是脚位/眼高/固定骨长姿势引导，最后附件是邻帧衔接参考。'
       f'{action}。{identity}人物面朝右，固定侧视镜头，左上光源，1原生像素深色轮廓。必须严格匹配定稿的像素密度和头部大小；不要把整个人画小，尤其眩晕帧。'
       f'原生{cell}×{cell}坐标中，眼部标志中心必须在({target["eye"][0]:.2f},{target["eye"][1]:.2f})，脚底锚y={target["anchor"][1]}；先遵循附件3原生坐标对应的画布摆位。输出1024×1024，为原生格的均匀放大；不要重居中/自动裁边。'
       '完整四肢、连贯人体，头部和身体比例和定稿完全一致，没有多余碎片。远侧手臂和腿必须由你在生成时整条画成palette暗色，近侧保持亮色；远侧经过近侧胯/躯干后方时沿肢体轮廓画1像素深色分隔，绝不矩形或直线色块压暗躯干。'
       +('近银RGB229,229,229/192,190,191，近红243,25,25；远银169,167,170/144,137,140，远红202,8,10。' if f=='ultraman' else '近侧节状肢体奶白RGB234,220,200/213,198,179；远侧整条肢体灰褐167,151,134/150,136,121/118,110,102；近手足54,54,57，远手足38,38,42；胸前发光体不压暗。')
       +'硬边像素，无抗锯齿、模糊、渐变、投影、地面、文字、数字、框、引导关节点或特效。只绘制一个角色一帧；不把附件引导平涂颜色画进成品。')
    if target.get('feet'):p+='脚位必须保持：'+str(target['feet'])+'；原帧脚步已审定，不准换腿或改步距。'
    if f=='ultraman' and a=='stun':p+='身体原生脚底到头顶约140像素，银色头壳最大弦长约32像素。附件1原帧的缩小是错误，必须以附件2及末尾正确眩晕邻帧的身体大小为准。'
    if f=='zetton' and a=='charge':p+='四帧胯中心(128,188)、双脚中心(89,247)/(157,247)完全固定，脸灯中心x145，y只变1像素；只有手臂胸口轻颤，不要照抄附件1旧版的上下晃动。'
    return p+('\n上次拒收原因与此次必须改正项：'+feedback if feedback else '')


def generate(key,feedback=''):
    registry=read(RUN/'registry.json');target=registry[key]['target'];folder=ROOT/registry[key]['folder'];ledger=read(WORK/'ledger.json')
    brake=Brake(produce_character.BRAKE_PATH)
    if brake.blocked(['head_ratio','small_islands',f'{target["fighter"]}_{target["action"]}_continuity']):raise ValueError('本检查已暂停；先交诊断，不继续请求')
    prior=[r for r in ledger['requests'] if r['asset']==key]
    if len(prior)>=10:raise ValueError(key+'已用完10次，待人工')
    take=folder/f'take-{len(prior)+1:02}';take.mkdir(parents=True,exist_ok=False)
    f,a,i=target['fighter'],target['action'],target['frame'];n=len(read(RUN/'before.json')[f]['actions'][a]['centers'])
    refs=[folder/'original-x4.png',RUN/f/'model-reference-x4.png',folder/'guide-x4.png']
    peer=0 if a=='stun' and f=='ultraman' else (i-1)%n
    peerim=old_frame(f,a,peer);peerpath=folder/'neighbor-x4.png';peerim.resize((peerim.width*4,peerim.height*4),Image.Resampling.NEAREST).save(peerpath)
    # 补步行帧只约束自己的腿相位，避免上一帧参考把腿相位复制过来。
    if not a.startswith('walk_'):refs.append(peerpath)
    if f=='ultraman' and a=='stun' and len(prior):refs=[RUN/f/'model-reference-x4.png',folder/'original-x4.png',folder/'guide-x4.png',peerpath]
    if f=='zetton' and a=='charge' and i>0 and len(prior):
        canonical=RUN/'zetton/charge/frame-00/take-01/preview-x4.png'
        if len(prior)>=3:canonical=RUN/'zetton/charge/frame-00/take-01/raw.png'
        refs=[canonical,RUN/f/'model-reference-x4.png',folder/'guide-x4.png',folder/'original-x4.png']
    frozen=[]
    for j,path in enumerate(refs):
        p=take/'inputs'/f'{j}.png';p.parent.mkdir(exist_ok=True);shutil.copy2(path,p);frozen.append(p)
    prompt=prompt_for(target,feedback)
    if f=='ultraman' and a=='stun' and len(prior):
        prompt=prompt.replace('附件1是要修复的当前正式帧，附件2是唯一身份/比例/配色定稿','附件1是唯一身份/正确头身比/配色定稿，附件2是尺寸错误的原帧（仅看摇晃方向，不继承其比例）')
    if f=='zetton' and a=='charge' and i>0 and len(prior):prompt+='\n附件1现在是新蓄能第0帧的正确身体定姿（不是旧漂移帧），此帧头、躯干、胯、膝、脚必须与附件1保持同一位置和大小，只让手指握紧程度与胸前发光轻微改变。附件4旧帧仅供手臂蓄力方向参考，不能继承它的身体偏移。'
    save(take/'request.json',dict(prompt=prompt,size='1024x1024',quality='high',background='transparent',references=[dict(path=rel(p),sha256=sha(p)) for p in frozen]))
    row=dict(number=len(ledger['requests'])+1,fighter=f,action=a,frame=i,asset=key,sequence=len(prior)+1,size='1024x1024',quality='high',input_images=len(frozen),category='移动' if a.startswith('walk_') else '循环回修',started_at=datetime.now(timezone.utc).isoformat(),result='submitted',folder=rel(take))
    with ledger_lock():
        ledger=read(WORK/'ledger.json');row['number']=len(ledger['requests'])+1;ledger['requests'].append(row);save(WORK/'ledger.json',ledger)
    try:
        art_pipeline.generate_image(SimpleNamespace(model=MODEL,reference=frozen,out=take/'raw.png',dry_run=False,mask=None),dict(prompt=prompt,size='1024x1024',quality='high',asset_kind='character'),'初代杰顿已装循环回修；完整人物单帧，待用户复核')
        row.update(result='generated',finished_at=datetime.now(timezone.utc).isoformat())
    except Exception as exc:row.update(result='failed_or_alpha_rejected_or_remote_unknown',reason=str(exc),finished_at=datetime.now(timezone.utc).isoformat())
    with ledger_lock():
        ledger=read(WORK/'ledger.json');ledger['requests'][row['number']-1]=row;ledger['counts']={ff:sum(r['fighter']==ff for r in ledger['requests']) for ff in ['ultraman','zetton']};ledger['counts']['total']=len(ledger['requests']);save(WORK/'ledger.json',ledger)
    print(key,row['sequence'],row['result'],row.get('reason',''),flush=True);return take


def process(key,take=None):
    registry=read(RUN/'registry.json');target=registry[key]['target'];folder=ROOT/registry[key]['folder'];take=Path(take) if take else sorted(folder.glob('take-*'))[-1]
    raw=take/'raw.png';f,a,i=target['fighter'],target['action'],target['frame'];cell=target['anchor'][1]+8
    if not raw.exists():return None
    image=Image.open(raw).convert('RGBA');rh=head_size.head(image,f)
    if not rh:raise ValueError('原图头部不可测')
    reference=head_size.reference(f);factor=reference['measurement']['length']/rh['length'];candidates=[]
    # 候选尺度以固定头部标尺为中心；最终硬限仍为实测±8%，绝不按人物外框定比例。
    for multiplier in [1,.97,1.03,1.06,1.08,1.10,1.12]:
        s=factor*multiplier;snap,_,_=proc.snap_for_scale(image,s);native=proc._kcentroid_downscale(snap,round(image.width*s),round(image.height*s));proc.binarize_alpha(native);native=proc.apply_palette(native,read(ROOT/f'content/fighters/{f}/palette.json')['colors'])
        nh=head_size.head(native,f);eye,_=eye_feature(native,f,nh);dx=round(target['eye'][0]-eye[0]);old=old_frame(f,a,i);bottom=old.getbbox()[3]
        if f=='ultraman' and a=='stun':bottom=184
        if f=='zetton' and a=='charge':bottom=248
        dy=bottom-native.getbbox()[3];im=Image.new('RGBA',(cell,cell));im.alpha_composite(native,(dx,dy));h=head_size.head(im,f,hint=[nh['center'][0]+dx,nh['center'][1]+dy]);hint=h['center']
        foot_error=0
        if a.startswith('walk_'):
            options=[]
            for shift in range(-7,8):
                aligned=Image.new('RGBA',im.size);aligned.alpha_composite(im,(shift,0))
                try:feet=measured_feet(aligned,f,target['foot_boxes'])
                except ValueError:continue
                errors=[feet[side]['x']-target['feet'][side]['x'] for side in ['near','far']]
                options.append((sum(e*e for e in errors),abs(shift),shift,aligned))
            if options:
                error,_,shift,im=min(options,key=lambda r:r[:2]);dx+=shift;foot_error=error**.5
                h=head_size.head(im,f,hint=[hint[0]+shift,hint[1]]);hint=h['center']
            else:foot_error=100
        point,bounds=eye_feature(im,f,h);headdev=h['length']/reference['measurement']['length']-1
        # 初代完整近眼需要自检标注，新图不能继承旧标注。暂以色块检测作候选排序。
        score=abs(point[1]-target['eye'][1])+abs(headdev)*10+foot_error
        if abs(headdev)>.08:score+=100
        if im.getbbox() is None:continue
        candidates.append((score,im,h,point,s,dx,dy,headdev,bounds))
    score,im,h,eye,s,dx,dy,dev,bounds=min(candidates,key=lambda x:x[0]);im.save(take/'frame-0.png');im.resize((cell*4,cell*4),Image.Resampling.NEAREST).save(take/'preview-x4.png')
    issues=[]
    if abs(dev)>.08:issues.append('头部比例超±8%')
    islands=island_qa.components(im)
    if islands:issues.append('孤立像素块≤20px：'+str([v['area'] for v in islands]))
    guide_diagnostics=[]
    if abs(eye[1]-target['eye'][1])>2:guide_diagnostics.append(f'眼高{eye[1]:.3f}目标{target["eye"][1]:.3f}差>2px，仅引导诊断；以整条循环真实门为准')
    qa=dict(asset=key,target=target,eye=eye,eye_bounds=bounds,head_deviation=dev,head=h,alpha_bounds=list(im.getbbox()),issues=issues,guide_diagnostics=guide_diagnostics,source=rel(raw),source_sha256=sha(raw),image_sha256=sha(take/'frame-0.png'),shared_scale=s,raw_head_length=rh['length'],raw_head=rh,translation=[dx,dy],processing='仅整帧头部标尺统一缩放、整图量化、完整人物对齐脚底；无区域换色、修补或拼肢体')
    save(take/'qa.json',qa);save(take/'head-qa.json',dict(reference=reference,scale_policy='per_frame_head',frames=[dict(frame=0,image='frame-0.png',image_sha256=qa['image_sha256'],source=rel(raw),source_sha256=sha(raw),shared_scale=s,raw_head_length=rh['length'],hint=h['center'],measurement=h,foot_anchor=target['anchor'])],issues=[]))
    Brake(produce_character.BRAKE_PATH).record(key,dict(head_ratio=abs(dev)<=.08,small_islands=not islands),take/'preview-x4.png')
    print(key,take.name,'eye',eye,'dev',round(dev,4),'issues',issues,flush=True);return qa


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','generate','process','both']);p.add_argument('keys',nargs='*');p.add_argument('--feedback',default='');p.add_argument('--take',type=Path);args=p.parse_args()
    if args.command=='prepare':prepare(args.keys or None);return
    for key in args.keys:
        try:
            take=generate(key,args.feedback) if args.command in ['generate','both'] else args.take
            if args.command in ['process','both']:process(key,take)
        except Exception as exc:print(key,type(exc).__name__,str(exc),flush=True)


if __name__=='__main__':main()

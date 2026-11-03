"""固定腿长的步行姿势引导。骨架仅作GPT输入，绝不作为游戏人物渲染。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import argparse,copy,math,sys
import numpy as np
from PIL import Image,ImageDraw
from head_scale import ROOT,read,save,sha,font
import stage4_pilot as pilot
import head_size,idle_qa,slugger_qa,process_phase2 as proc,limb_color_qa as color
from seven_gpt_redraw import RUN,OUT,rel

WORK=RUN/'skeleton-walk'
SERIES='fixed-bone-whole-walk-v1'

def knee(hip,ankle,upper,lower):
    h=np.array(hip,dtype=float);a=np.array(ankle,dtype=float);v=a-h;d=float(np.linalg.norm(v))
    if not abs(upper-lower)<=d<=upper+lower:raise ValueError('姿势目标超出固定腿长可达范围')
    u=v/d;q=(upper*upper-lower*lower+d*d)/(2*d);p=h+u*q
    bend=math.sqrt(max(0,upper*upper-q*q));n=np.array([-u[1],u[0]])
    points=[p+n*bend,p-n*bend]
    return max(points,key=lambda v:v[0]).tolist()

def prepare(overrides=None):
    WORK.mkdir(parents=True,exist_ok=True)
    if (WORK/'profiles.json').exists() and overrides is None:return
    model=ROOT/'art/fighters/ultraseven/model/model-native.png';im=Image.open(model).convert('RGBA');h=head_size.head(im,'ultraseven');eye=idle_qa.feature(im,'ultraseven',dict(hint=h['center']))
    # 逐像素网格视查的近腿关节中心，保留坐标和原图哈希供复核。
    hip=[95,125];kn=[77,146];an=[60,174];upper=math.dist(hip,kn);lower=math.dist(kn,an)
    geometry=dict(model=rel(model),sha256=sha(model),hip=hip,knee=kn,ankle=an,thigh=upper,shin=lower,hip_height=184-hip[1],foot_length=18,
        measurement='从已审定稿原生像素网格标髋/膝/踝中心；鞋底水平长度18px；关节作为引导标注，非骨骼拼片成品',eye=eye,head_hint=h['center'])
    save(WORK/'model-geometry.json',geometry);profiles={};assets={}
    for action,sign in [('walk_forward',1),('walk_back',-1)]:
        ticks=[6]*8
        phase=[0,-2,-5,-2,0,-2,-5,-2]
        near=[120,108,96,84,72,84,96,108] if sign==1 else [72,84,96,108,120,108,96,84]
        far=[72,84,96,108,120,108,96,84] if sign==1 else [120,108,96,84,72,84,96,108]
        if overrides and action in overrides:
            values=overrides[action]
            half_ticks=[round((values['near0']-values['near4'])*sign/2),round((values['far4']-values['far0'])*sign/2)]
            if min(half_ticks)<4:raise ValueError('接触关键帧没有形成正确方向的撑地位移；不伪造步距或速度')
            ticks=[half//4+(1 if j<half%4 else 0) for half in half_ticks for j in range(4)]
            near=[values['near0']+(values['near4']-values['near0'])*(i/4 if i<=4 else (8-i)/4) for i in range(8)]
            far=[values['far0']+(values['far4']-values['far0'])*(i/4 if i<=4 else (8-i)/4) for i in range(8)]
            # 实测接触步距较大时，下沉同一条髋/眼曲线以保持固定骨长，不能伸长腿。
            max_dx=max(abs(x-4-94) for x in near+far)
            if max_dx>=upper+lower-1:raise ValueError('实测关键步距超出固定腿长，待人工，不拉长腿')
            required=179-math.sqrt(max(0,(upper+lower-.5)**2-max_dx**2))
            drop=max(0,math.ceil(required-125))
        else:drop=0
        rows=[];sheet=Image.new('RGB',(192*4*4,240*4*2),'#202632');d=ImageDraw.Draw(sheet)
        for i in range(8):
            hh=[94,125+drop+phase[i]];feet={};legs={}
            for side,xs in [('near',near),('far',far)]:
                swing=(side=='far' and i in [1,2,3]) or (side=='near' and i in [5,6,7])
                bottom=184-([3,7,3][i%4-1] if swing else 0)
                feet[side]=[xs[i],bottom-1];ank=[xs[i]-4,bottom-5]
                legs[side]=dict(hip=hh,knee=knee(hh,ank,upper,lower),ankle=ank,foot=feet[side],swing=swing)
            row=dict(frame=i,phase=['接触A','下沉A','交错A','上升A','接触B','下沉B','交错B','上升B'][i],hip=hh,eye=[eye[0]+(2 if sign==1 else -2),eye[1]+drop+phase[i]],feet=feet,legs=legs,tick=ticks[i],sign=sign)
            rows.append(row);folder=WORK/action/f'frame-{i:02}';folder.mkdir(parents=True,exist_ok=True)
            guide=Image.new('RGBA',(192,192));g=ImageDraw.Draw(guide)
            # 远侧在下、近侧在上；关节圆点仅用于姿势引导，不进assets。
            for side,c in [('far','#7d1725'),('near','#e12e31')]:
                p=legs[side];pts=[tuple(p[k]) for k in ['hip','knee','ankle']]
                g.line(pts,fill=c,width=9,joint='curve');x,y=feet[side];g.rectangle((x-8,y-4,x+9,y),fill=c)
            ex,ey=row['eye'];head_center=[ex-5,ey+3];neck=[96+(2 if sign==1 else -2),82+drop+phase[i]]
            g.line([tuple(hh),tuple(neck)],fill='#e12e31',width=23);g.ellipse((head_center[0]-10,head_center[1]-16,head_center[0]+10,head_center[1]+13),fill='#e1e8ea')
            for pts,c in [([(98,86+drop+phase[i]),(119,105+drop+phase[i]),(130,91+drop+phase[i])],'#7d1725'), ([(91,86+drop+phase[i]),(79,107+drop+phase[i]),(111,106+drop+phase[i])],'#e12e31')]:g.line(pts,fill=c,width=8,joint='curve')
            g.ellipse((ex-1,ey-1,ex+2,ey+1),fill='#fbedb3')
            for side in ['far','near']:
                for joint,c in [('hip','#30d8ff'),('knee','#ffd449'),('ankle','#71ec8b')]:
                    x,y=legs[side][joint];g.ellipse((x-1,y-1,x+1,y+1),fill=c)
            guide.save(folder/'guide-native.png');guide.resize((1152,1152),Image.Resampling.NEAREST).save(folder/'guide.png');save(folder/'target.json',row)
            big=guide.resize((768,768),Image.Resampling.NEAREST);xx=i%4*768;yy=i//4*960;sheet.paste(big,(xx,yy+100),big);d.text((xx+8,yy+8),f'{action} #{i} {row["phase"]}\n眼睛y{row["eye"][1]:.2f}  髋y{hh[1]}',font=font(24),fill='white')
            assets[f'{action}/frame-{i:02}']=dict(action=action,indices=[i],category='移动')
        profiles[action]=dict(ticks=ticks,sign=sign,targets=rows,description='固定股/胫长；接触最低、交错最高，眼/髋同一平滑5px曲线，拳在胸前护架；关键帧实测步距÷速度2定周期')
        sheet.save(WORK/f'{action}-skeleton-contact.png')
    save(WORK/'profiles.json',profiles);save(WORK/'asset-registry.json',dict(batch='seven-skeleton-walk',fighters=['ultraseven'],assets=assets))
    with pilot.ledger_lock():
        l=read(pilot.LEDGER);l.setdefault('method_authorizations',{})[SERIES]=dict(assets=list(assets),per_asset=6,authorization='用户指定固定腿长骨架逐帧整帧生成，前后走各8帧，固定帧重新6次；不再只编辑腿部')
        save(pilot.LEDGER,l)

def calibrate():
    """先量关键帧实际步距再画中间引导；未过关关键稿只提供诊断步距，不能安装。"""
    values={};records=[]
    for action in ['walk_forward','walk_back']:
        pairs={}
        for i in [0,4]:
            choices=[]
            for p in (WORK/action/f'frame-{i:02}').glob('take-*/qa.json'):
                q=read(p)
                if q.get('feet') and q.get('eye'):
                    choices.append((len(q['issues']),abs(q['eye'][1]-q['target']['eye'][1]),p,q))
            if choices:
                _,_,p,q=min(choices,key=lambda v:v[:2]);pairs[i]=q
                records.append(dict(action=action,frame=i,source=rel(p),feet=q['feet'],issues=q['issues'],passed=not q['issues']))
        if len(pairs)==2:
            values[action]=dict(near0=pairs[0]['feet']['near']['x'],far0=pairs[0]['feet']['far']['x'],near4=pairs[4]['feet']['near']['x'],far4=pairs[4]['feet']['far']['x'])
    save(WORK/'key-measurements.json',dict(records=records,interpolation=values,note='中间帧按真实关键稿的脚部像素插值；关键稿未过门则整条仍待人工，不能借测量放行'))
    if values:
        try:prepare(values)
        except ValueError as exc:save(WORK/'key-geometry-block.json',dict(reason=str(exc),status='关键实测步距不可达；保持原始固定骨长引导，不伪造腿长'))

def brief(action,i,feedback=''):
    folder=WORK/action/f'frame-{i:02}';target=read(folder/'target.json');sign=target['sign'];key=f'{action}/frame-{i:02}'
    support='近侧亮腿' if i<4 else '远侧暗腿';description=target['phase'];feet=target['feet']
    text=f'''赛文奥特曼整帧逐帧像素步行动画，只画第{i}帧【{description}】。透明背景、真实Alpha，只画一个完整人物。参考1已审全身定稿，参考2已审头部8倍，参考3是本帧原生192×192的6倍固定腿长引导（髋蓝点、膝黄点、踝绿点），这些点线不画到成品。
严格按照引导图的腿部骨架和身体高度，不能自行加长/缩短大小腿。身体{'略前倾、向右前走' if sign==1 else '略后仰、向左后退'}，始终面朝右，躯干纯正侧面、胸肩不朝镜头；双拳保持胸前格斗护架，仅小幅摆动。髋坐标{target['hip']}、黄眼中心约{target['eye']}；原生两只脚中心与底部{feet}。撑地腿是{support}，脚底y183。步幅要短，两脚都在髋下附近。交错帧2/6的摆动膝向前弯、脚从支撑踝旁经过，脚距不得超过一只脚长，不要画成两条直腿分开或高抬腿。接触帧两脚前后分开，腿长与交错帧相同。
原生头盔固定长27.42px，同定稿比例；黄眼/绿额灯，银色胸肩条甲，红身，无计时器。头镖严格复制参考2：前缘竖直、高出头骨0.3H，后尾沿后脑下扫，不能前勾、低平冠或暗底座。
远侧整条手臂/腿从肩胯到指脚，必须由你在这张完整人物里画成暗红125,23,37/81,22,34与暗银117,137,149/72,89,104；近侧整条臂腿亮红225,46,49/179,27,38与亮银225,232,234/172,187,194。近侧与躯干的自阴影也只用近侧两档，不挪用远侧暗色画矩形阴影。远腿经过近侧胯后，用1原生像素深轮廓分界，胯和躯干保持亮红，不用矩形/多边形直边切暗。不要靠后期换色。
画布1152×1152，以192×192原生像素的6倍硬边格绘制，原生脚底锚(96,184)，全身包含头冠，左上光、1原生像素深轮廓，32色，无抗锯齿、无阴影地面、无字、无关节点，绝不复制参考定稿的固定站姿。'''+feedback
    value=dict(model='gpt-image-2.5-sunburst',fighter='ultraseven',asset_key=key,identity_revision='model05',attempt_series=SERIES,asset_registry=rel(WORK/'asset-registry.json'),category='移动',quality='high',asset_kind='character',size='1152x1152',references=['art/fighters/ultraseven/model/model-reference-x4.png','art/fighters/ultraseven/model/head-reference-x8.png',rel(folder/'guide.png')],prompt=text)
    save(folder/'brief.json',value);return folder/'brief.json'

def measure_feet(im,target):
    a=np.array(im);r,g,b=a[:,:,:3].astype(int).transpose(2,0,1);yy,xx=np.indices(a.shape[:2]);red=(a[:,:,3]>0)&(r>65)&(r>g*2)&(r>b*1.6);feet={}
    for side in ['near','far']:
        tx,ty=target['feet'][side];mask=red&(abs(xx-tx)<18)&(abs(yy-ty)<14)&((r>=160) if side=='near' else (r<160))
        # 靠色块识别远近身份；同一脚必须至少有完整的底部色块。
        ys,xs=np.where(mask)
        if len(xs)<6:raise ValueError(side+'脚实际像素不可测')
        sel=ys>=ys.max()-4;feet[side]=dict(x=float(xs[sel].mean()),y=float(ys[sel].mean()),bottom=int(ys.max()),pixels=int(sel.sum()))
    return feet

def process(action,i,row):
    folder=WORK/action/f'frame-{i:02}'/f'take-{row["sequence"]:02}';folder.mkdir(parents=True,exist_ok=True);raw=ROOT/row['output'];target=read(folder.parent/'target.json');issues=[]
    if not raw.exists():save(folder/'qa.json',dict(issues=['失败/Alpha拒收，无成品']));return folder
    image=Image.open(raw).convert('RGBA');rh=head_size.head(image,'ultraseven')
    if not rh:save(folder/'qa.json',dict(issues=['头盔不可测']));return folder
    factor=head_size.reference('ultraseven')['measurement']['length']/rh['length'];snap,_,_=proc.snap_for_scale(image,factor)
    native=proc._kcentroid_downscale(snap,round(image.width*factor),round(image.height*factor));proc.binarize_alpha(native);native=proc.apply_palette(native,read(ROOT/'content/fighters/ultraseven/palette.json')['colors'])
    h=head_size.head(native,'ultraseven');ey=idle_qa.feature(native,'ultraseven',dict(hint=h['center']));dx=round(target['eye'][0]-ey[0]);dy=184-native.getbbox()[3]
    im=Image.new('RGBA',(192,192));im.alpha_composite(native,(dx,dy));im.save(folder/'frame-0.png');im.save(folder/'atlas.png')
    h=head_size.head(im,'ultraseven');record=dict(frame=0,image='frame-0.png',image_sha256=sha(folder/'frame-0.png'),source=rel(raw),source_sha256=sha(raw),shared_scale=factor,raw_head_length=rh['length'],hint=h['center'],head_region=h['polygon'],head_direction=[0,-1],measurement=h,foot_anchor=[96,184])
    eye=idle_qa.feature(im,'ultraseven',record)
    if abs(eye[1]-target['eye'][1])>2:issues.append(f'眼睛y={eye[1]:.2f}，目标{target["eye"][1]:.2f}，偏差>2px')
    if abs(h['length']/head_size.reference('ultraseven')['measurement']['length']-1)>.08:issues.append('头部尺寸超±8%')
    feet=None
    try:
        feet=measure_feet(im,target);side='near' if i<4 else 'far'
        if abs(feet[side]['x']-target['feet'][side][0])>3:issues.append(side+'撑地脚x目标差>3px')
        if abs(feet[side]['bottom']-183)>1:issues.append('撑地脚未触地')
    except ValueError as exc:issues.append(str(exc))
    crown=slugger_qa.compare(im,record)
    if not crown['pass_']:issues.append('头镖剪影未过')
    edges=color.boundaries(im,'ultraseven')
    if edges:issues.append('直线明暗候选需语义复核')
    save(folder/'head-qa.json',dict(reference=head_size.reference('ultraseven'),scale_policy='per_frame_head',frames=[record],issues=[s for s in issues if '头' in s]))
    save(folder/'qa.json',dict(issues=issues,eye=eye,feet=feet,crown=crown,boundaries=edges,target=target,request=row['ledger_sequence'],processing='GPT完整帧，头部比例整帧网格还原/量化，脚底对齐；没有区域换色'))
    im.resize((768,768),Image.Resampling.NEAREST).save(folder/'reference.png');print(action,i,row['revision_sequence'],issues,flush=True);return folder

def generate(action,i):
    key=f'{action}/frame-{i:02}';get=lambda:[r for r in read(pilot.LEDGER)['requests'] if r['fighter']=='ultraseven' and r['action']==key and r.get('attempt_series')==SERIES]
    if (WORK/action/f'frame-{i:02}/candidate.json').exists():return
    while len(get())<6:
        own=get();feedback=''
        if own:
            p=WORK/action/f'frame-{i:02}/take-{own[-1]["sequence"]:02}/qa.json'
            if p.exists():
                q=read(p)
                feedback='上一稿拒收：'+str(q['issues'])+'。原生实测眼睛='+str(q.get('eye'))+'，脚部='+str(q.get('feet'))+'。未沿1像素深轮廓的明暗直线坐标='+str(q.get('boundaries',[])[:10])+'。这些是错误诊断位置，不能画成遮罩边；请在真实远肢与近肢/胯的交叠处画深色轮廓，近肢本身的阴影仍用近侧色。严格照本帧骨架和腿长重画。'
        try:row=pilot.generate_action('ultraseven',key,brief(action,i,feedback))
        except Exception:
            if len(get())<=len(own):raise
            row=get()[-1]
        try:f=process(action,i,row)
        except Exception as exc:
            f=WORK/action/f'frame-{i:02}'/f'take-{row["sequence"]:02}';f.mkdir(exist_ok=True)
            save(f/'qa.json',dict(request=row['ledger_sequence'],source=row['output'],issues=['本地后处理/测量未完成：'+type(exc).__name__+': '+str(exc)]))
        if not read(f/'qa.json')['issues']:save(WORK/action/f'frame-{i:02}/candidate.json',dict(folder=rel(f),status='pending_visual_review'));return
    save(WORK/action/f'frame-{i:02}/blocked.json',dict(status='待人工',reason='新骨架方法6次仍未通过数值/身份门；未安装，继续下一帧'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','generate','calibrate']);p.add_argument('--action',default='walk_forward');p.add_argument('--frame',type=int,default=0);a=p.parse_args()
    if a.command=='prepare':prepare()
    elif a.command=='calibrate':calibrate()
    else:generate(a.action,a.frame)

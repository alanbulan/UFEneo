"""杰顿第一批：复用GPT客户端与整帧后处理；单帧循环、条带攻击、独立80次预算。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import argparse,copy,math,sys
from pathlib import Path
Path = _LayoutProjectPath
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parent))
from phase3_air import ROOT,read,save,sha,font,producer,process,spec

WORK=ROOT/'art/fighters/zetton/stage3/legacy/zetton1'
OUT=ROOT/'reports/review/2026-10-22-zetton-first'
PREFIX='p3zet_'
CELL=256;ANCHOR=[128,248]

def pose(**kw):
    p=dict(head=(133,111),neck=(130,132),hip=(124,184),shoulder_back=(124,138),shoulder_front=(134,140),elbow_back=(151,160),wrist_back=(167,144),elbow_front=(153,160),wrist_front=(176,146),knee_back=(107,213),ankle_back=(86,245),knee_front=(143,214),ankle_front=(163,245));p.update(kw);return p

def crouch(b=0,**kw):
    p=pose(head=(141,148+b),neck=(135,167+b),hip=(119,210+b),knee_front=(155,221),ankle_front=(179,245),knee_back=(95,224),ankle_back=(78,245),shoulder_front=(140,175+b),shoulder_back=(129,171+b),elbow_front=(165,197+b),wrist_front=(185,181+b),elbow_back=(151,194+b),wrist_back=(169,178+b));p.update(kw);return p

def vary(poses,count):
    # 仅编排参考关节，所有成品仍由GPT完整重画。
    return [copy.deepcopy(poses[min(len(poses)-1,round(i*(len(poses)-1)/(count-1)))]) for i in range(count)]

S={
'idle':spec('沉重待机',[12]*6,'身体正侧面朝右，双手自然前伸略屈肘、张开的黑色手刀，膝微屈；缓慢呼吸0收腹、1微低、2稍抬胸、3最高、4回落、5回到0前一刻。触角、橙色竖脸、胸口双发光体稳定，双脚固定。',[pose(head=(133,111+y),neck=(130,132+y),wrist_front=(176,146+y)) for y in [0,1,0,-1,-1,0]],loop=True),
'light1':spec('手刀一段',[3,3,4,4,5,9],'近手从胸前向右水平斜劈，黑色张掌侧缘打击胸口；另一手护住身体。起手、出掌、完全伸展、回收清楚，不画拳头。',vary([pose(),pose(wrist_front=(160,130)),pose(elbow_front=(166,148),wrist_front=(197,145)),pose(wrist_front=(184,151)),pose()],6),{2:[197,145,15]}),
'light2':spec('手刀二段',[3,3,4,4,5,10],'远侧暗手后拉，再由下向右横切肋部，近手回护；与一段换手且切线更低，不能复用一段。',vary([pose(),pose(wrist_back=(121,154)),pose(elbow_back=(169,169),wrist_back=(201,167)),pose(wrist_back=(182,161)),pose()],6),{2:[201,167,16]}),
'light3':spec('双手刀终段',[3,3,3,4,4,5,10],'双臂先向后张开，再两手刀并排向右上凶猛推出击退；双掌错开不融合，不是拳。',vary([pose(),pose(wrist_front=(103,152),wrist_back=(98,139)),pose(elbow_front=(167,142),wrist_front=(201,134),elbow_back=(161,159),wrist_back=(192,150)),pose()],7),{3:[201,134,19]}),
'heavy':spec('重手刀',[4,4,4,5,4,4,4,11],'近臂举起过肩后向右下大幅劈出，黑手掌根劈中胸腹；躯干重压前脚，慢起手重收势，不是初代直拳。',vary([pose(),pose(wrist_front=(128,87),elbow_front=(144,122)),pose(wrist_front=(205,162),elbow_front=(171,151)),pose()],8),{4:[205,162,19]}),
'launcher':spec('上挑手刀',[4,4,4,4,4,4,5,11],'屈膝下沉、近手收至腰侧，再张掌由下向右上挑击，手刀举过头，带起对手；双腿始终落地，不用踢腿。',vary([crouch(),crouch(wrist_front=(150,204)),pose(wrist_front=(188,86),elbow_front=(166,122)),pose()],8),{4:[188,86,20]}),
'spin_heavy':spec('转背回旋手刀',[4,4,4,5,4,4,5,11],'身体转背，双臂随肩旋转，远臂反手横扫向右胸部，后转回侧面。必须出现转背轮廓与横向手臂扫击，不能直拳，不能踢腿。',vary([pose(),pose(head=(123,113),wrist_front=(102,149)),pose(head=(117,111),elbow_back=(166,152),wrist_back=(207,151),wrist_front=(95,166)),pose()],8),{4:[207,151,20]}),
'crush':spec('双臂猛砸',[4,4,5,5,5,4,5,12],'两只黑手高举头顶蓄势，身体大幅压下，双手向正右下同时砸在对手胸腹；双臂不要融合，攻击强而沉，随后慢收架。',vary([pose(),pose(elbow_front=(145,109),wrist_front=(143,72),elbow_back=(131,105),wrist_back=(126,70)),crouch(head=(152,145),wrist_front=(202,184),elbow_front=(174,177),wrist_back=(191,173),elbow_back=(165,163)),pose()],8),{4:[202,184,24]}),
'tackle':spec('甲壳冲撞',[4,4,4,4,4,4,5,11],'低重心收双臂于胸侧，头肩与黑色胸甲前倾向右撞击，然后前脚制动恢复；用身体而不是出拳，突出厚重甲壳轮廓。',vary([pose(),crouch(wrist_front=(153,170)),pose(head=(164,135),neck=(147,150),wrist_front=(144,181),wrist_back=(132,174),hip=(128,193)),pose()],8),{3:[164,151,24],4:[164,151,24]}),
'pulse':spec('脸部小火球',[4,4,4,4,4,5,10],'头部竖长橙色发光体朝正右，稍向后蓄力再向前吐射小火球，双臂在身体两侧低位张开而不是推掌，最后还原。只画人物，不画火焰，特效另做。',vary([pose(),pose(head=(126,111),wrist_front=(156,176),wrist_back=(110,166)),pose(head=(146,113),wrist_front=(175,184),wrist_back=(105,177)),pose()],7),{3:[150,115,12]}),
'ranged_forward':spec('杰顿光线',[4,4,4,5,5,4,5,11],'双臂从两侧展开后向前伸出，双黑手平行朝右发射直线光束，手掌不相交；躯干正侧面，胸部发光体露出。手臂姿势与脸部火球清楚不同，光线另做。',vary([pose(),pose(wrist_front=(103,148),wrist_back=(104,133)),pose(elbow_front=(172,147),wrist_front=(205,145),elbow_back=(166,159),wrist_back=(198,157)),pose()],8),{4:[205,151,12]}),
'crouch_start':spec('下蹲',[4,5],'站姿屈双膝压低重心至低蹲，触角和身体比例不变，手刀仍在胸前。',[pose(head=(137,129),hip=(122,198)),crouch()]),
'crouch':spec('蹲姿保持',[12,12],'低蹲稳定护架，低位双膝承重，手刀前伸，小幅呼吸。',[crouch(),crouch(1)],loop=True),
'crouch_rise':spec('蹲姿起身',[4,5],'由低蹲伸膝恢复正侧面待机，不能变成倒地起身。',[crouch(),pose()]),
'crouch_light':spec('下段手刀一段',[3,3,4,5,10],'保持蹲姿，近手张掌向右下斜劈对手小腿，另一手留在胸前，最后收回。',vary([crouch(),crouch(elbow_front=(164,217),wrist_front=(202,231)),crouch()],5),{2:[202,231,16]}),
'crouch_light2':spec('下段手刀二段',[3,3,4,5,10],'保持蹲姿换远侧暗手横切脚踝，比一段更低，近手回护，明确换手。',vary([crouch(),crouch(elbow_back=(164,229),wrist_back=(205,239)),crouch()],5),{2:[205,239,16]}),
'sweep':spec('低位扫腿',[4,4,4,5,4,4,5,11],'低蹲手撑地，近腿向右地面扫出打倒对手；这是本条自己的下段腿法，双触角随低头倾斜，不做手刀冒充。',vary([crouch(),crouch(head=(146,185),neck=(134,201),hip=(120,226),wrist_front=(158,245),knee_front=(173,236),ankle_front=(214,244)),crouch()],8),{4:[214,244,17]}),
'slide':spec('低姿滑撞',[4,4,4,5,5,4,5,11],'蹲低后单腿向右伸直、另一腿蜷在身下，侧身向右滑铲撞小腿，黑手撑身；最后回蹲，不借扫腿。',vary([crouch(),crouch(head=(148,197),neck=(135,211),hip=(117,228),knee_front=(174,238),ankle_front=(220,246),knee_back=(105,236),ankle_back=(94,245),wrist_front=(153,244)),crouch()],8),{3:[220,246,18],4:[220,246,18]}),
'low_pulse':spec('贴地火球',[4,4,4,4,5,11],'深蹲头前探，脸部竖橙发光体向右下贴地吐出小火球，黑手低位撑架，不用推掌；不画火焰，特效另做。',vary([crouch(),crouch(head=(154,185),neck=(140,203),hip=(119,218),wrist_front=(168,230)),crouch()],6),{3:[172,201,12]})
}

def walk_pose(action,i,near=None,far=None):
    sign=1 if action=='walk_forward' else -1
    near=near or [158,146,134,122,110,122,134,146]
    far=far or [110,122,134,146,158,146,134,122]
    if sign<0:near=[256-x for x in near];far=[256-x for x in far]
    bob=[0,2,0,-2,0,2,0,-2][i]
    def leg(x,phase):
        lift=0 if phase<=4 else [0,8,10,5][phase-4]
        return [((128+x)//2+(8 if lift else 0),213+bob-lift),(x,245-lift)]
    nk,na=leg(near[i],i);fk,fa=leg(far[i],(i+4)%8)
    return pose(head=(133+(0 if sign>0 else -5),111+bob),neck=(130,132+bob),hip=(124,184+bob),knee_front=nk,ankle_front=na,knee_back=fk,ankle_back=fa)

for action in ['walk_forward','walk_back']:
    S[action]=spec('沉重前走' if action=='walk_forward' else '谨慎后走',[6]*8,'面朝右，身体'+('前进向右' if action=='walk_forward' else '向左后退，略后仰，脚尖先着地')+'。脚步交替，暗远腿/臂身份固定，慢而沉，双臂保持杰顿前伸姿势，小幅随动。',[walk_pose(action,i) for i in range(8)],loop=True)

dash=[crouch(),pose(head=(151,123),wrist_front=(161,154),ankle_back=(90,244)),
      pose(head=(155,122),hip=(128,186),knee_back=(167,206),ankle_back=(190,233),knee_front=(107,200),ankle_front=(88,219),wrist_front=(98,163),wrist_back=(181,139)),
      pose(head=(154,120),knee_back=(169,214),ankle_back=(190,245),ankle_front=(88,239),wrist_front=(102,160),wrist_back=(185,137)),
      pose(head=(155,122),hip=(128,186),knee_front=(167,206),ankle_front=(190,233),knee_back=(107,200),ankle_back=(88,219),wrist_back=(98,163),wrist_front=(181,139)),
      pose(head=(154,120),knee_front=(169,214),ankle_front=(190,245),ankle_back=(88,239),wrist_back=(102,160),wrist_front=(185,137)),
      pose(head=(140,117),ankle_front=(177,245),ankle_back=(113,245)),pose(head=(126,111),ankle_front=(164,245)),pose()]
S['dash_sequence']=spec('一次性重冲刺',[2,2,3,3,3,3,2,2,2],'起步两格→腾空B（暗远腿在前、两脚离地）→着地B→腾空A（亮近腿在前、两脚离地）→着地A→前脚制动→后仰→复位。不是单腿蹦，躯干正侧面。',dash)
LOOPS=['idle','crouch','walk_forward','walk_back','dash_sequence']

def guide(poses,path):
    cols=min(4,math.ceil(len(poses)/2)) if len(poses)>1 else 1;rows=math.ceil(len(poses)/cols)
    im=Image.new('RGB',(512*cols,512*rows),'#f1f3f4');d=ImageDraw.Draw(im)
    for n,p in enumerate(poses):
        ox=n%cols*512;oy=n//cols*512
        def xy(k):return (ox+p[k][0]*2,oy+p[k][1]*2)
        for side,color in [('back','#bd783d'),('front','#32b8e2')]:
            for seq in [('hip','knee_'+side,'ankle_'+side),('shoulder_'+side,'elbow_'+side,'wrist_'+side)]:
                d.line([xy(k) for k in seq],fill=color,width=18,joint='curve')
            x,y=xy('ankle_'+side);d.polygon([(x-12,y-8),(x+20,y-6),(x+22,y+5),(x-12,y+5)],fill=color)
        d.line([xy('head'),xy('neck'),xy('hip')],fill='#56616c',width=30)
        x,y=xy('head');d.ellipse((x-18,y-26,x+18,y+20),fill='#56616c')
        d.line([(x-14,y-20),(x-28,y-55)],fill='#56616c',width=6);d.line([(x+12,y-20),(x+26,y-55)],fill='#56616c',width=6)
    im.save(path);return cols,rows

def request(action,index=None,previous=None,correction=''):
    s=S[action];suffix=action if index is None else f'{action}_{index}';name=PREFIX+suffix
    poses=s['poses'] if index is None else [s['poses'][index]]
    ticks=s['ticks'] if index is None else [s['ticks'][index]]
    folder=ROOT/f'art/shared/poses/templates/humanoid/air_batch/{name}';folder.mkdir(parents=True,exist_ok=True)
    cols,rows=guide(poses,folder/'guide.png')
    save(folder/'poses.json',{'cell':[256,256],'anchor':ANCHOR,'source':'content/fighters/zetton/MOVES.md','method':'原剧外形/重心与街机相位人工重编参考关节，非RTMlib提取，不是成品拆肢','frames':[{'joints':p,'ticks':ticks[i],'height':0} for i,p in enumerate(poses)]})
    count=len(poses);layout=(f'{cols}列{rows}行，恰好{count}个完整杰顿，顺序从左到右再下一行，每个512像素方格、无格线；最后{cols*rows-count}个空余格必须全透明，禁止多画人物补满。' if index is None else f'只画一个完整杰顿，是{action}第{index}帧，绝不画多个人或整条动作。')
    phase=''
    if index is not None:
        if action.startswith('walk'):
            phase=['着地A：亮近腿在'+('右前脚跟先着地' if action=='walk_forward' else '左后脚尖先着地')+'，暗远腿相反。','下沉A：亮近腿承重，暗远脚开始回摆。','交错A：亮近腿竖直承重，暗远膝屈曲从后向前摆；脚部投影交错。','抬起A：亮近腿斜撑、脚跟抬起，暗远脚低位摆前，下一格才落地。','着地B：与0相反，暗远腿开始撑地，亮近腿回摆。','下沉B：暗远腿承重，亮近脚回摆。','交错B：暗远腿竖直承重，亮近膝屈曲摆动并遮住暗远腿。','抬起B：暗远腿斜撑，亮近脚即将落地，不能复制0。'][index]
            if action=='walk_back':
                phase=['着地A：亮近腿向左后伸脚尖先着地，暗远腿在右前。','下沉A：亮近脚仍在左后承重并向右移，暗远脚开始向左后低位回摆。','交错A：亮近腿竖直撑地，暗远膝屈曲向左后摆，两脚横坐标交错。','抬起A：亮近脚在右前继续撑地，暗远脚已摆到左后即将落地。','着地B：暗远脚在左后脚尖着地，亮近腿右前开始回摆。','下沉B：暗远脚左后撑地向右移，亮近脚低位向左后回摆。','交错B：暗远腿竖直撑地，亮近膝屈曲向左后摆，两脚横坐标交错。','抬起B：暗远脚在右前继续撑地，亮近脚已到左后即将落地，下一格接0。'][index]
        elif action=='dash_sequence':phase=['深蹲蓄势，亮近腿在前。','后脚蹬地，前倾起步。','腾空B：暗远腿向右前摆，亮近腿向左后折，双脚都离地。','着地B：暗远脚向右前着地承重，亮近脚在左后。','腾空A：亮近腿右前、暗远腿左后，两脚都离地。','着地A：亮近脚向右前着地承重，暗远脚在左后。','亮近脚继续踩地刹停。','后仰回收后脚。','回到身份锚的待机姿势。'][index]
        elif action=='idle':phase=f'呼吸六相位的第{index}格，脚底不动、只微小胸肩呼吸，前后紧接。'
        else:phase=f'低蹲呼吸第{index}格。'
    if index is not None and s.get('measured_targets'):
        target=s['measured_targets'][str(index)]
        phase+=f'按已生成关键帧的实测步距插值：原生256画布中，近脚中心x约{target[0]}、远脚中心x约{target[1]}，支撑脚底y248；不能把步幅重新画大。'
    refs=['art/fighters/zetton/stage3/legacy/zetton1/model-reference.png',(folder/'guide.png').relative_to(ROOT).as_posix()]
    if previous:refs+=previous
    elif (WORK/'accepted/idle_0.png').exists():refs+=['art/fighters/zetton/stage3/legacy/zetton1/accepted/idle_0.png']
    else:refs+=['art/fighters/zetton/stage3/legacy/zetton1/model-reference.png']
    target=int(round(max(max(pv[1] for pv in p.values())+3-min(p['head'][1]-29,min(pv[1] for pv in p.values())-3) for p in poses)))
    target=min(178,target)
    prompt=(f'为唯一身份锚中的宇宙恐龙杰顿（初代1966）绘制整帧硬边像素动画，透明背景PNG Alpha，GPT Image高质量。{layout}'
        f'动作：{s["description"]} 本帧要求：{phase}。'
        '固定正侧视面向右，窄单肩侧面；保持完全相同的高挑比例、长黑头、双叉触角、竖长橙色面部发光体、胸腹橙黄发光体、黑甲壳白斑、米白分节肢体和黑色手脚。杰顿没有人类眼睛、嘴、红纹或蓝计时器，不画奥特曼。'
        '近侧手腿米白RGB234,220,200及213,198,179，近手黑RGB66,66,68；远侧手腿统一暗米灰167,151,134及150,136,121、远手暗黑38,38,42。哪怕远腿在前也暗、近腿在后也亮，禁止换色。参考双色剪影蓝为近侧、橙为远侧，但成品不画引导色。'
        '参考1仅身份，参考2仅本帧姿势，其余为已选稿保持尺寸配色；不抄参考里的其他相位。黑色手掌五指不超过五根、两只手两条腿完整连续，禁止碎片、多肢、光效遮手脚。'
        f'原生256×256，站姿含触角高166像素，脚底根锚x128/y248，按参考关节真实屈膝降低高度、不得给蹲姿缩身体；输出人物为原生的2倍绘制，单帧图时加透明留白放在1024×1024中心且人物高约332像素。'
        '像素密度和身份图一致，单原生像素深色轮廓、清楚方块，无抗锯齿柔边，无地面、影子、编号、文字、参考线、边框、残影、特效或背景。'+correction)
    b={'id':name,'fighter':'zetton','native_cell':256,'native_anchor':ANCHOR,'target_height':target,'template':'air_batch','frames':count,'ticks':ticks,'loop':s['loop'],'columns':cols,'rows':rows,'size':f'{max(1024,cols*512)}x{max(1024,rows*512)}','guide':(folder/'guide.png').relative_to(ROOT).as_posix(),'reference_images':refs,'prompt':prompt,'generation_dir':f'art/fighters/zetton/stage2/generation/phase3_first/{suffix}','review_dir':OUT.relative_to(ROOT).as_posix(),'budget':{'journal':'art/fighters/zetton/stage3/legacy/zetton1/requests.json','max_requests':80,'action_key':suffix}}
    if index is not None and action=='dash_sequence' and index in [2,4]:
        b['native_bottom']=round(max(poses[0]['ankle_front'][1],poses[0]['ankle_back'][1])+3)
    save(ROOT/f'art/fighters/ultraman/stage2/legacy/requests/{name}.json',b);return name

def prepare():
    if (WORK/'requests.json').exists():raise ValueError('已有生产记录，禁止重置')
    WORK.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True);(WORK/'accepted').mkdir(exist_ok=True)
    model=Image.open(ROOT/'assets/fighters/zetton/model-native.png').convert('RGBA');model.resize((1024,1024),Image.Resampling.NEAREST).save(WORK/'model-reference.png')
    p=ROOT/'content/fighters/zetton/palette.json';d=read(p);d['colors']=[list(c) for c in dict.fromkeys(map(tuple,d['colors']))];assert len(d['colors'])<=32
    d['side_view_roles']={'policy':'固定侧视远侧手臂和腿压暗，身份不因前后交替互换；躯干发光体不调暗','near_side':{'limb_rgb':[[234,220,200],[213,198,179],[177,162,144]],'hand_foot_rgb':[[66,66,68],[54,54,57]]},'far_side':{'limb_rgb':[[167,151,134],[150,136,121],[118,110,102]],'hand_foot_rgb':[[38,38,42],[15,16,19]]}};save(p,d)
    save(WORK/'profiles.json',S);save(WORK/'requests.json',[]);save(WORK/'review.json',{})
    for a in S:
        if a in LOOPS:
            for i in range(len(S[a]['ticks'])):request(a,i)
        else:request(a)
    print('杰顿第一批准备完成；80次独立预算；256画布与底部根锚')

def generate(action,index=None,previous=None,correction=''):
    name=request(action,index,previous,correction);result=producer.generate(name);print(result,flush=True)
    if result.get('status')=='generated' or result.get('take'):
        # 指定本次稿号；低Alpha角噪点获准清理时也不能悄悄退回旧稿。
        print(process.process(name,int(Path(result['take']).name)),flush=True)
    src=ROOT/f'art/fighters/ultraman/stage2/legacy/processed/{name}/atlas.png'
    if src.exists():
        im=Image.open(src).convert('RGBA');bg=Image.new('RGB',(im.width*2,512),'#202632');big=im.resize(bg.size,Image.Resampling.NEAREST);bg.paste(big,(0,0),big);bg.save(OUT/(name+'-screen.png'))

if (WORK/'profiles.json').exists():S=read(WORK/'profiles.json')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','generate']);p.add_argument('--action');p.add_argument('--index',type=int);p.add_argument('--previous',nargs='*');p.add_argument('--correction',default='');a=p.parse_args()
    prepare() if a.command=='prepare' else generate(a.action,a.index,a.previous,a.correction)

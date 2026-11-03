"""赛文首批：复用现有请求客户端、姿势条和整帧后处理，不借用人物成品。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import argparse,copy,math,sys
import shutil
from PIL import Image,ImageDraw
from head_scale import ROOT,read,save,sha
import art_phase2 as art
import process_phase2 as process
import stage4_pilot as pilot
from phase3_air import pose

WORK=pilot.RUN/'ultraseven-first'
OUT=ROOT/'reports/review/2026-10-22-seven-model5'


def from_request(name):
    q=read(ROOT/f'art/fighters/ultraman/stage2/legacy/requests/{name}.json')
    p=read((ROOT/q['guide']).parent/'poses.json')
    return [r['joints'] for r in p['frames']],q['ticks']


def locomotion(action,i):
    bob=[0,2,0,-2,0,2,0,-2][i]
    near=[124,112,100,88,76,88,100,112];far=[76,88,100,112,124,112,100,88]
    if action=='walk_back':near,far=far,near
    def leg(x,phase):
        lift={5:6,6:10,7:4}.get(phase,0)
        return [(96+x)//2+(6 if lift else 0),149+bob-lift],[x,181-lift]
    nk,na=leg(near[i],i);fk,fa=leg(far[i],(i+4)%8)
    p=pose(head=(100-(5 if action=='walk_back' else 0),52+bob),neck=(98,72+bob),hip=(96,120+bob),knee_front=nk,ankle_front=na,knee_back=fk,ankle_back=fa)
    if action=='walk_forward':
        swing=[-14,-9,0,8,14,9,0,-8][i]
        p.update(wrist_front=(111+swing,106+bob),elbow_front=(105+swing//2,97+bob),wrist_back=(105-swing,102+bob),elbow_back=(99-swing//2,94+bob))
    return p


def convert_dash(p):
    lean=p.get('lean',0);bob=p.get('bob',0)
    return pose(head=(100+lean,52+bob),neck=(98+lean//2,72+bob),hip=p['hip'],knee_front=p['near']['knee'],ankle_front=p['near']['ankle'],knee_back=p['far']['knee'],ankle_back=p['far']['ankle'],elbow_front=p['near_arm']['elbow'],wrist_front=p['near_arm']['wrist'],elbow_back=p['far_arm']['elbow'],wrist_back=p['far_arm']['wrist'])


def crouch_profiles(profiles):
    """本批自己的腿法与换手参考，不能用旧通用直拳姿势冒充扫腿/滑铲。"""
    def crouch(**kw):
        p=pose(head=(105,96),neck=(101,116),hip=(91,148),knee_front=(122,165),ankle_front=(135,181),knee_back=(76,164),ankle_back=(62,181),shoulder_front=(105,121),shoulder_back=(97,119),elbow_front=(122,139),wrist_front=(136,122),elbow_back=(105,141),wrist_back=(122,130));p.update(kw);return p
    specs={
      'crouch_start':('下蹲',[pose(head=(102,73),hip=(94,136),knee_front=(117,158)),crouch()],'两帧都是屈膝下降：半蹲、低蹲护架；不出拳，不站直。'),
      'crouch':('蹲姿保持',[crouch(),crouch(head=(105,97))],'两帧低蹲护架呼吸，脚和拳不出击，膝盖深弯。'),
      'crouch_rise':('蹲姿起身',[pose(head=(102,73),hip=(94,136),knee_front=(117,158)),pose()],'由半蹲伸双膝，第二帧恢复站立护架；不出拳。'),
      'crouch_light':('下段轻击一段',[crouch(),crouch(elbow_front=(127,146),wrist_front=(140,151)),crouch(elbow_front=(137,151),wrist_front=(161,153)),crouch()],'全程低蹲，亮近手直拳打右侧小腿，暗远手留在胸前，最后收回。'),
      'crouch_light2':('下段轻击二段',[crouch(),crouch(elbow_back=(122,148),wrist_back=(142,156)),crouch(elbow_back=(136,156),wrist_back=(164,159)),crouch()],'全程低蹲，换暗远手打更低的脚踝，亮近拳保持胸前护架，末帧收回。'),
      'sweep':('扫腿',[crouch(),crouch(head=(98,114),wrist_back=(77,176)),crouch(head=(96,126),neck=(94,141),hip=(89,163),wrist_back=(73,179),knee_front=(132,172),ankle_front=(166,180)),crouch(head=(96,126),neck=(94,141),hip=(89,163),wrist_back=(73,179),knee_front=(139,174),ankle_front=(177,181)),crouch(head=(99,116),knee_front=(133,170),ankle_front=(161,181)),crouch(),crouch()],'低蹲、暗远手撑地、亮近腿沿地面向右扫出脚跟、扫到最大、收腿、回蹲；最大帧腿水平伸直，不能画直拳。'),
      'slide':('滑铲',[crouch(),crouch(head=(95,121),hip=(86,164)),crouch(head=(88,136),neck=(91,149),hip=(88,169),wrist_back=(71,179),knee_front=(130,177),ankle_front=(171,182)),crouch(head=(85,140),neck=(90,151),hip=(89,169),wrist_back=(69,179),knee_front=(136,179),ankle_front=(178,182)),crouch(head=(89,139),neck=(94,151),hip=(91,167),wrist_back=(73,180),knee_front=(138,178),ankle_front=(178,182)),crouch(head=(98,123)),crouch(),crouch()],'上身后仰低滑铲，亮近腿向右水平伸直、暗远腿蜷在臀下，暗远手在身后撑地；不是蹲拳，不是扫腿的前倾姿势。'),
      'low_pulse':('低姿艾梅利姆光线',[crouch(),crouch(wrist_front=(115,99)),crouch(wrist_front=(113,94),elbow_front=(130,118)),crouch(wrist_front=(113,94),elbow_front=(130,118)),crouch()],'保持低蹲，两指靠近额头绿色灯向正右发射细光束，人物图不画光束；不从手掌发射。')}
    for a,(name,poses,description) in specs.items():profiles[a].update(name=name,poses=poses,description=description+'普通招式为街机游戏编排。')
    return profiles


def prepare():
    WORK.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    profiles={}
    def add(a,name,poses,ticks,description,category,loop=False,single=False):
        profiles[a]=dict(name=name,poses=poses,ticks=ticks,description=description,category=category,loop=loop,single=single)
    for a in ['idle','light1','light2','light3','launcher']:
        count=art.CLIPS[a][1];poses=[art.pose(a,i,count) for i in range(count)]
        add(a,{'idle':'待机','light1':'轻击一段','light2':'轻击二段','light3':'轻击三段','launcher':'升击'}[a],poses,art.CLIPS[a][2],art.CLIPS[a][4],'移动' if a=='idle' else '站立',a=='idle',a=='idle')
    for a in ['walk_forward','walk_back']:
        add(a,'前走' if a=='walk_forward' else '后走',[locomotion(a,i) for i in range(8)],[6]*8,'身体始终正侧面朝右；'+('前进交替迈步，手臂反向自然摆动' if a=='walk_forward' else '身体向左后退、略后仰，脚尖先着地，双拳保持护架小幅摆动')+'；0着地A、1下沉A、2交错A、3抬起A、4着地B、5下沉B、6交错B、7抬起B接0前一刻，不复制0。','移动',True,True)
    dash=read(ROOT/'art/fighters/ultraman/stage2/legacy/dash_single/poses.json')['frames'];order=[0,1,7,5,4,2,8,9,10]
    add('dash_sequence','冲刺',[convert_dash(dash[i]) for i in order],[2,2,3,3,3,3,2,2,2],'起步蓄势、起步蹬地、腾空B（暗远腿前）、着地B、腾空A（亮近腿前）、着地A、近脚制动、后仰、回护架。腾空两格双脚离地；22tick一次性。','移动',False,True)
    for a in ['heavy','tackle','crouch_start','crouch','crouch_rise','crouch_light','crouch_light2','sweep','slide','low_pulse']:
        poses,ticks=from_request(a);q=read(ROOT/f'art/fighters/ultraman/stage2/legacy/requests/{a}.json')
        category='下蹲' if a.startswith('crouch') or a in ['sweep','slide','low_pulse'] else '站立'
        add(a,a,poses,ticks,'按附件的街机人形姿势编排本招的起手、攻击、收招。普通拳脚均为游戏编排。',category,a=='crouch',a=='crouch')
    poses,ticks=from_request('p3air_spin_heavy');add('spin_heavy','回旋后踢',poses,ticks,'转身背对右侧对手，中段脚跟后踢，再收腿转回右向护架；不是直拳。','站立')
    poses,ticks=from_request('p3react_turn');add('turn','站立转身',poses,ticks,'左向站姿、整帧转背、右向站姿，三张全新完整姿势，不用镜像代替。','移动')
    a,ta=from_request('crush_a');b,tb=from_request('crush_b')
    add('crush','超重击',a[:4]+b,ta[:4]+tb,'双拳举过头蓄势，向右前下方猛砸，再收势。共9帧，分两条原图，每条最多8帧。','站立')
    pulse=[pose(),pose(wrist_front=(108,60),elbow_front=(119,86)),pose(wrist_front=(111,53),elbow_front=(124,76)),pose(wrist_front=(111,53),elbow_front=(124,76)),pose(),pose()]
    add('pulse','艾梅利姆光线',pulse,[3,3,4,4,5,7],'两指靠近额头绿色光束灯，头朝右瞄准，由额头发射细光束；人物图不画光束特效。原剧具体手势依据待核实。','站立')
    slugger=[pose(),pose(wrist_front=(104,39),elbow_front=(122,62)),pose(wrist_front=(112,33),elbow_front=(132,59)),pose(wrist_front=(156,53),elbow_front=(135,63)),pose(wrist_front=(167,76),elbow_front=(142,82)),pose(wrist_front=(136,98)),pose(wrist_front=(115,42)),pose()]
    add('ranged_forward','头镖投掷',slugger,[3,3,3,4,4,4,4,6],'伸手摘下头顶Eye Slugger、向右横甩掷出、保持投后姿态、回收并装回。第2至5帧头盔顶部必须没有头镖，第6帧接回，第7帧恢复；不是八分光轮，不画蓝色计时器。人物图不画飞行头镖。','站立')
    registry={}
    for a,s in profiles.items():
        count=len(s['ticks'])
        parts=[(f'{a}/frame-{i:02}',[i]) for i in range(count)] if s['single'] else [(a,list(range(count)))] if count<=8 else [(a+'/start',list(range(4))),(a+'/finish',list(range(4,count)))]
        for key,indices in parts:registry[key]=dict(action=a,indices=indices,category=s['category'])
    crouch_profiles(profiles)
    record=dict(batch='ultraseven-first',per_asset_attempt_limit=6,assets=registry)
    path=WORK/'asset-registry.json'
    if path.exists() and read(path)!=record:raise ValueError('固定资产清单已存在，禁止改名重算')
    save(path,record);save(WORK/'profiles.json',profiles)
    ledger=pilot.read(pilot.LEDGER)
    ledger.setdefault('batch_authorizations',{})['ultraseven-first']=dict(scope='总次数不设上限；动作暂停等待头部返工定稿复核；哥莫拉和其余八位动作本轮不做')
    pilot.save(pilot.LEDGER,ledger)
    print('赛文首批姿势和固定预算键已准备；未调用生图。')


def guide(poses,path):
    cols=len(poses) if len(poses)<=3 else min(4,math.ceil(len(poses)/2));rows=math.ceil(len(poses)/cols)
    im=Image.new('RGB',(512*cols,512*rows),'#f1f3f4');d=ImageDraw.Draw(im)
    for i,p in enumerate(poses):
        def xy(k):return (i%cols*512+64+p[k][0]*2,i//cols*512+64+p[k][1]*2)
        for side,color in [('back','#ba7444'),('front','#32b7e0')]:
            for chain in [('hip','knee_'+side,'ankle_'+side),('shoulder_'+side,'elbow_'+side,'wrist_'+side)]:d.line([xy(k) for k in chain],fill=color,width=18,joint='curve')
        d.line([xy('head'),xy('neck'),xy('hip')],fill='#53616d',width=28)
        x,y=xy('head');d.ellipse((x-17,y-25,x+17,y+22),fill='#53616d')
    path.parent.mkdir(parents=True,exist_ok=True);im.save(path)
    return cols,rows


def generate(key,previous=None,correction='',attempt_series=None):
    registry=read(WORK/'asset-registry.json');asset=registry['assets'][key];s=read(WORK/'profiles.json')[asset['action']];indices=asset['indices'];poses=[s['poses'][i] for i in indices];folder=WORK/key
    cols,rows=guide(poses,folder/'guide.png')
    if key=='turn':
        # 姿势参考的鼻尖/眼标明左、背、右，避免无面向的椭圆误导；不改成品轮廓。
        im=Image.open(folder/'guide.png');d=ImageDraw.Draw(im)
        for index,direction in [(0,-1),(2,1)]:
            x=index*512+64+poses[index]['head'][0]*2;y=64+poses[index]['head'][1]*2
            d.polygon([(x+direction*13,y-9),(x+direction*30,y+1),(x+direction*13,y+8)],fill='#53616d')
            d.rectangle((x+direction*9-3,y-10,x+direction*9+3,y-5),fill='#ffd65a')
        im.save(folder/'guide.png')
    save(folder/'poses.json',dict(frames=[dict(joints=p,ticks=s['ticks'][i]) for i,p in zip(indices,poses)],source='已审初代同体型街机姿势参考；只复用参考关节，不复用人物成品；普通招式为游戏编排'))
    refs=['art/fighters/ultraseven/model/model-reference-x4.png','art/fighters/ultraseven/model/head-reference-x8.png',(folder/'guide.png').relative_to(ROOT).as_posix()]+(previous or ['art/fighters/ultraseven/model/model-reference-x4.png'])
    if asset['action'] in ['walk_forward','walk_back'] and indices[0] not in [0,4]:
        adjacent={1:[0,2],3:[2,4],5:[4,6],7:[6,0]}.get(indices[0],[0,4])
        if not all((WORK/f'accepted/{asset["action"]}/frame-{i:02}/reference.png').exists() for i in adjacent):adjacent=[0,4]
        refs=refs[:3]+[(WORK/f'accepted/{asset["action"]}/frame-{i:02}/reference.png').relative_to(ROOT).as_posix() for i in adjacent]
    single=len(indices)==1
    layout='只画一个完整人物，1024×1024透明画布中央，站立人物高约576像素，原生像素的4倍硬边格' if single else f'{cols}列{rows}行，每格512×512，按行恰好{len(indices)}个完整人物，其余格真透明，站立人物高约288像素'
    phase=f'本次只画动作第{indices[0]}帧，不能复制上一帧姿势。' if single else '各格依次跟随姿势条。'
    description=s['description']
    if single and s.get('measured_key_targets'):
        i=indices[0];targets=s['measured_key_targets']
        description+=f'本帧以脚底根锚(96,184)定位：亮近脚中心x约{targets["near"][i]}，暗远脚中心x约{targets["far"][i]}。严格遵循附件两腿剪影，交错时一条直撑另一条低摆，不画高抬腿。'
    if single and asset['action'] in ['walk_forward','walk_back','dash_sequence']:
        i=indices[0]
        if asset['action']=='dash_sequence':
            description=['起步蓄势，亮近腿在前，双脚着地，身体前倾。','起步蹬地，亮近腿在前，暗远腿在后蹬地。','腾空B：暗远腿向右前伸，亮近腿向左后折；双脚离地，不能画亮腿在前。','着地B：暗远腿向右前伸，右侧暗脚脚跟踏地；亮近腿向左后伸，左侧亮脚脚尖在地；不是抬膝腾空。','腾空A：亮近腿向右前伸，暗远腿向左后折；双脚离地。','着地A：亮近腿向右前伸，右侧亮脚脚跟踏地；暗远腿向左后伸，左侧暗脚脚尖在地。','亮近脚在右前方踩地刹停，暗远腿在后，身体略后仰。','身体后仰减速，亮近腿仍在前，双脚落地、拳回胸前。','恢复右向格斗护架，双脚稳定落地。'][i]
            if i==5:description+='这一帧脚跟接在身体正下方略前，亮近脚中心(103,181)，暗远脚中心(65,181)，身体前倾、近膝微弯，短落地步而不是大跨步，严格按剪影。'
        elif i in [0,4]:
            near_front=(i==0)==(asset['action']=='walk_forward')
            description=('亮近腿向右前伸、亮脚在右侧，暗远腿向左后伸、暗脚在左侧。' if near_front else '暗远腿向右前伸、暗脚在右侧，亮近腿向左后伸、亮脚在左侧。')+('前脚脚跟着地、后脚脚尖在地。' if asset['action']=='walk_forward' else '向左后退，左侧后脚脚尖先落地，右侧前脚脚掌仍在地。拳在胸前保持格斗护架，不大摆臂。')+'两脚分开，不交错，不抬膝，不腾空。'+description
        elif asset['action']=='walk_forward':
            phase_name={1:'下沉A：亮近腿弯膝撑地，暗远腿脚跟抬起',2:'交错A：亮近腿竖直撑地，暗远膝折弯，暗脚从亮腿后经过',3:'抬起A：亮近腿斜向左后撑地，暗远腿低低前摆',5:'下沉B：暗远腿弯膝撑地，亮近腿脚跟抬起',6:'交错B：暗远腿竖直撑地，亮近膝折弯，亮脚从暗腿前经过',7:'抬起B：暗远腿斜向左后撑地，亮近腿低低前摆'}[i]
            description=phase_name+'。另外两张人物参考只能用于头盔/护甲/色板，绝对不能照抄其中的大跨步腿。只复制本次蓝橙剪影的关节和脚距。'+description
        else:
            phases={1:'下沉A：亮近腿在左后方屈膝接重，暗远脚在右前方抬跟',2:'交错A：亮近腿必须竖直在身体正下方撑地，暗远腿屈膝向左后摆，暗脚在亮腿后、离地约8像素，两脚靠拢，绝对不能大跨步',3:'抬起A：亮近腿伸向右前方撑地，暗远腿往左后低摆',5:'下沉B：暗远腿在左后方屈膝接重，亮近脚在右前方抬跟',6:'交错B：暗远腿必须竖直在身体正下方撑地，亮近腿屈膝向左后摆，亮脚挡在暗腿前、离地约8像素，两脚靠拢，绝对不能大跨步',7:'抬起B：暗远腿伸向右前方撑地，亮近腿往左后低摆'}
            description=phases[i]+'。两张着地参考只保持身份，不复制它们前后大跨步的腿。'+description
    if key=='crush/start':description='本次恰好四帧：护架、双拳抬至额前、双拳举过头顶、双手开始向前下挥。只画蓄势部分，不画砸到底或后面的恢复。'
    if key=='crush/finish':description='本次恰好五帧：双拳向右下猛砸、双臂伸至最低胸腹高度、收双拳起身、半起身护架、回到站立护架。只画这五帧，不画前面的举拳蓄势。'
    facing='本条特例：首帧脸、黄色眼和绿色灯朝左，中帧转背看不到脸，末帧脸朝右，不能首尾同向。' if key=='turn' else '固定街机正侧面朝右，窄胸单肩；只有回旋允许转背。'
    prompt=(f'绘制已定稿的赛文奥特曼（1967原版）整帧像素动画【{s["name"]}】：{description} {phase} {layout}。透明背景，PNG真实Alpha，四角完全透明。'
      '参考1是唯一已通过身份全身，参考2是定稿头部8倍特写，参考3是本次剪影，其余是已通过身份/动作参考。'+facing+'身高约144原生像素，左上光、单像素深轮廓，32色，红色躯干和四肢、银色头盔、胸肩横条护甲、绿色额头灯、黄色六角眼、头顶Eye Slugger。没有胸前彩色计时器，没有初代的红银腿部条纹。'
      '重点：每格头部必须复制参考2的轮廓比例！头镖前端在画面右侧，前缘是平直竖边、钝直角，高出头骨0.3个头高。顶边往后/左略下降，后尾沿后脑向下扫，到耳朵与下巴之间，尾粗3像素收到1像素尖；尾与后脑留1-2像素缝。不能前勾、不能低矮平冠、不能有深色底座或脖子。脸干净银色大色块、黄大眼、绿额灯、矩形护耳。'
      '近侧臂腿亮红225,46,49/179,27,38；远侧整条臂腿暗红125,23,37/81,22,34，近肩亮银225,232,234/172,187,194，远肩暗银117,137,149/72,89,104。远近身份不随前后换腿改变。远肢经过近侧胯和躯干后方时，交界沿真实肢体轮廓画1原生像素深色线，近侧和躯干不涂暗，不能用直角色块切暗。远侧暗色必须直接画在整帧原图里，后处理只量化整图色板，不做区域换色。'
      '同一张原图所有人物的头盔尺寸严格一致，蹲下或倾斜只改变姿势，不缩小身体。完整两手两脚连续，不多肢、不截断。硬边像素格，不要抗锯齿、软边、背景、地面、阴影、文字、参考线、编号、残影、特效。'+correction)
    brief=dict(model=art.MODEL,fighter='ultraseven',asset_key=key,identity_revision='model05',quality='high',asset_kind='character',size=f'{max(1024,cols*512)}x{max(1024,rows*512)}',references=refs,prompt=prompt)
    if attempt_series:brief['attempt_series']=attempt_series
    bp=folder/'brief.json';pilot.save(bp,brief)
    error=None
    try:row=pilot.generate_action('ultraseven',key,bp)
    except Exception as exc:
        error=exc
        candidates=[r for r in read(pilot.LEDGER)['requests'] if r['fighter']=='ultraseven' and r['action']==key and r.get('identity_revision')=='model05']
        if not candidates:raise
        row=candidates[-1]
    name='s4seven_'+key.replace('/','_');q=dict(id=name,fighter='ultraseven',native_cell=192,native_anchor=[96,184],frames=len(indices),ticks=[s['ticks'][i] for i in indices],loop=s['loop'],columns=cols,rows=rows,guide=(folder/'guide.png').relative_to(ROOT).as_posix(),generation_dir=str(Path(row['output']).parent.parent).replace('\\','/'),review_dir=OUT.relative_to(ROOT).as_posix())
    if asset['action'] in ['launcher','crush']:q.update(native_cell=256,native_anchor=[128,248])
    if asset['action']=='dash_sequence' and indices[0] in [2,4]:q['native_bottom']=174
    if asset['action']=='ranged_forward':q['native_head_annotations']={str(j):dict(slugger_detached=True) for j,i in enumerate(indices) if 2<=i<=5}
    if key=='turn' and attempt_series=='turn-back-v1':
        source=ROOT/row['output']
        if not source.exists():source=source.parent/'rejected/raw.png'
        cells=process.grid_figures(Image.open(source).convert('RGBA'),cols,rows,len(indices));regions={}
        from head_scale import measure
        for j,cell in enumerate(cells):
            h=measure(cell,'ultraman',hint=[cell.width/2,cell.height*.13])
            if h:regions[str(j)]=[[x/cell.width,y/cell.height] for x,y in h['polygon']]
        q.update(head_regions=regions,head_measurement_axis='width',native_head_annotations={'0':dict(facing='left'),'1':dict(crown_view='back',manual_crown_reason='用户指定背面仅露窄银色竖刃、后尾下延，侧面剪影门不适用；需人工复核8倍头条带')})
    save(ROOT/f'art/fighters/ultraman/stage2/legacy/requests/{name}.json',q)
    result=process.process(name,row['sequence'])
    if result.get('status')!='blocked':
        import slugger_qa
        try:slugger_qa.validate(ROOT/f'art/fighters/ultraman/stage2/legacy/processed/{name}')
        except ValueError as exc:result.update(status='blocked',issues=[str(exc)])
    if error:result['generation_error']=str(error)
    save(folder/f'local-qa-{row["sequence"]}.json',result);print(result,flush=True)
    return result


def accept(key):
    """仅在逐帧视觉检查后手动调用；不把自动质检当用户已审。"""
    import head_size
    name='s4seven_'+key.replace('/','_');src=ROOT/f'art/fighters/ultraman/stage2/legacy/processed/{name}'
    qa=read(src/'qa.json');assert not qa['issues'],qa['issues']
    import slugger_qa
    hq=head_size.validate(src,'ultraseven');slugger_qa.validate(src);dst=WORK/'accepted'/key;dst.mkdir(parents=True,exist_ok=True)
    for row in hq['frames']:shutil.copy2(src/row['image'],dst/row['image'])
    for filename in ['qa.json','slugger-qa.json','region-color.json']:
        if (src/filename).exists():shutil.copy2(src/filename,dst/filename)
    save(dst/'head-qa.json',hq);shutil.copy2(src/'atlas.png',dst/'atlas.png')
    reference=Image.open(dst/'frame-0.png');reference.resize((reference.width*4,reference.height*4),Image.Resampling.NEAREST).save(dst/'reference.png')
    save(dst/'visual-review.json',dict(status='self_checked_pending_user_review',user_approved=False,asset=key,source=qa['source'],frames=[dict(image=r['image'],sha256=sha(dst/r['image'])) for r in hq['frames']],notes='逐帧检查完整轮廓、赛文身份、绿额灯/黄眼/无计时器、远侧颜色；仍需用户看主游戏审片'))
    print((dst/'reference.png').relative_to(ROOT).as_posix())


def normalize(key):
    """一次整条共同尺度反馈；不生图、不逐帧改变比例。"""
    name='s4seven_'+key.replace('/','_');path=ROOT/f'art/fighters/ultraman/stage2/legacy/requests/{name}.json';q=read(path)
    if q.get('head_scale_multiplier'):raise ValueError('已做过统一比例反馈，仍失败应列待人工')
    h=read(ROOT/f'art/fighters/ultraman/stage2/legacy/processed/{name}/head-qa.json');lengths=[r['measurement']['length'] for r in h['frames'] if r['measurement']]
    multiplier=2*h['reference']['measurement']['length']/(min(lengths)+max(lengths))
    q['head_scale_multiplier']=multiplier
    save(WORK/key/'head-normalization-first-pass.json',h);save(path,q)
    print(process.process(name))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','generate','accept','batch','normalize']);p.add_argument('--asset');p.add_argument('--assets',nargs='+');p.add_argument('--previous',nargs='*');p.add_argument('--correction',default='');a=p.parse_args()
    if a.command=='prepare':prepare()
    elif a.command=='accept':accept(a.asset)
    elif a.command=='generate':generate(a.asset,a.previous,a.correction)
    elif a.command=='normalize':normalize(a.asset)
    else:
        for key in a.assets:
            try:generate(key,a.previous,a.correction)
            except Exception as exc:
                save(WORK/key/'last-error.json',dict(error_type=type(exc).__name__,reason=str(exc),automatic_retry=False));print(key,type(exc).__name__,flush=True)

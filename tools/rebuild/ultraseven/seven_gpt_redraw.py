"""本轮固定帧队列：GPT整帧压暗重画，绝不区域换色或恢复旧图像素。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import argparse,copy,json,math,shutil,sys,time; json = _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import cv2,numpy as np
from PIL import Image,ImageDraw
from head_scale import ROOT,read,save,sha,font
import stage4_pilot as pilot
import process_phase2 as proc
import head_size,slugger_qa,limb_color_qa as color

RUN=ROOT/'art/fighters/ultraseven/stage4/revisions/seven-gpt-redraw'
OUT=ROOT/'reports/review/2026-10-22-seven-gpt-redraw'
SERIES='gpt-whole-frame-limbs-v1'
REG=RUN/'asset-registry.json'
OLD={'ultraman':['flip_forward','hit_high','heavy','timeout','taunt'],
     'zetton':['motion_214','launch_rise','burst']}

def rel(p):return Path(p).relative_to(ROOT).as_posix()
def prepare():
    RUN.mkdir(parents=True,exist_ok=True)
    if (RUN/'batch.json').exists():return
    ledger=read(pilot.LEDGER);start=len(ledger['requests'])
    scan=read(ROOT/'reports/review/2026-10-22-seven-repairs/installed-quality-scan.json')
    selected=[r for r in scan['frames'] if any(b.get('introduced_by_postprocess') for b in r['boundaries']) and
        (r['fighter']=='ultraseven' or r['action'] in OLD.get(r['fighter'],[]))]
    tasks=[];assets={};seen=set()
    for r in selected:
        fighter=r['fighter'];mp=ROOT/f'assets/fighters/{fighter}/animations/manifest.json';m=read(mp)
        clip=m['clips'][r['action']];index=r['frame'];rect=clip['rects'][index]
        ident=(fighter,clip['texture'],tuple(rect))
        if ident in seen:continue
        seen.add(ident);action='dash_sequence' if 'dash_sequence' in clip['texture'] else r['action']
        actual=clip.get('sequence_frames',list(range(len(clip['rects']))))[index]
        key=f'{action}/frame-{actual:02}'
        folder=RUN/fighter/key;folder.mkdir(parents=True,exist_ok=True)
        x,y,w,h=rect;atlas=Image.open(ROOT/clip['texture'].removeprefix('res://')).convert('RGBA');im=atlas.crop((x,y,x+w,y+h))
        im.save(folder/'before.png');im.resize((w*6,h*6),Image.Resampling.NEAREST).save(folder/'edit-input-x6.png')
        hq=read(ROOT/clip['head_qa']);row=copy.deepcopy(hq['frames'][actual if len(hq['frames'])>len(clip['rects']) else index])
        save(folder/'before-head.json',row)
        task=dict(fighter=fighter,key=key,action=action,index=actual,clip=r['action'],clip_index=index,
            rect=rect,texture=clip['texture'],head_qa=clip['head_qa'],anchor=clip.get('anchors',[clip.get('anchor',[w//2,clip.get('anchor_y',h-8)])]*len(clip['rects']))[index],
            before=rel(folder/'before.png'),before_sha256=sha(folder/'before.png'),introduced_boundaries=[b for b in r['boundaries'] if b.get('introduced_by_postprocess')])
        tasks.append(task);assets[key]=dict(action=action,indices=[actual],category='压暗重画')
    assert sum(t['fighter']=='ultraseven' for t in tasks)==68
    tasks.sort(key=lambda t:(t['fighter']!='ultraseven',t['fighter'],t['action'],t['index']))
    save(REG,dict(batch='seven-gpt-redraw',fighters=['ultraseven','ultraman','zetton'],assets=assets,assets_by_fighter={f:[t['key'] for t in tasks if t['fighter']==f] for f in ['ultraseven','ultraman','zetton']}))
    save(RUN/'tasks.json',tasks);save(RUN/'batch.json',dict(start=start,scope='用户授权：赛文68帧、初代与杰顿指定8动作命中帧；其它旧角色帧不动',method=SERIES,unlimited=True))
    ledger.setdefault('method_authorizations',{})[SERIES]=dict(fighters=['ultraseven','ultraman','zetton'],assets=list(assets),per_asset=6,authorization='用户2026-10-22授权GPT整帧重画新方法；固定帧重计6次，失败继续下一项，禁止后处理区域换色')
    save(pilot.LEDGER,ledger)
    mp=ROOT/'assets/fighters/ultraseven/animations/manifest.json';m=read(mp)
    m['clips']['idle']['motion_review']=dict(user_approved=True,verdict='用户已审：六帧平稳、仅呼吸起伏；本轮颜色重画须保留运动')
    m['clips']['turn']['motion_review']=dict(user_approved=False,verdict='结构与背面窄头刃用户通过；背面站高待修',review_dimensions=dict(structure=True,back_crown=True,size=False))
    m['clips']['walk_back']['motion_review']=dict(user_approved=False,verdict='用户撤回后走通过：眼睛高度跳动，按固定腿长骨架整帧重做')
    save(mp,m)
    p=ROOT/'content/roster/production.json';q=read(p)
    q['fighters']['ultraseven']['matrix']['idle'].update(reviewed=True,frames_reviewed=True,timing_reviewed=True)
    for cell in q['fighters']['ultraseven']['matrix'].values():
        if cell.get('animation',{}).get('clip')=='walk_back':cell.update(reviewed=False,frames_reviewed=False)
    save(p,q)
    print('固定队列',len(tasks),'赛文68；旧角色',len(tasks)-68,'台账起点',start,flush=True)

def attempts(t):
    return [r for r in read(pilot.LEDGER)['requests'] if r['fighter']==t['fighter'] and r['action']==t['key'] and r.get('attempt_series')==SERIES]

def brief(t,feedback=''):
    f=t['fighter'];folder=RUN/f/t['key'];im=Image.open(folder/'before.png');w,h=im.size
    palette=read(ROOT/f'content/fighters/{f}/palette.json')
    anchors=['art/fighters/ultraseven/model/model-reference-x4.png','art/fighters/ultraseven/model/head-reference-x8.png'] if f=='ultraseven' else [f'assets/fighters/{f}/model-native.png']
    prompt=f'''对参考1当前正式帧做精确的整帧像素重画。透明背景，真实Alpha。必须完整复制参考1的姿势、四肢轮廓、头部、脸部特征、身体比例、所有脚尖、画布留白和站位，禁止重新设计姿势，禁止任何形变。参考1为原生{w}×{h}像素的6倍图。请输出同样{w*6}×{h*6}的透明画布，维持6×6的硬边像素格，只有一个完整人物。Alpha外轮廓必须逐像素保留，脚底位置一个原生像素都不能移动。只改变远侧肢体内部的明暗和交叠处轮廓。
把远侧整条手臂（肩至指尖）和远侧整条腿（胯根至脚尖）画为暗色；近侧手臂/腿保持亮色，躯干/胯部不能被涂暗。远侧肢体在近侧胯和躯干后方通过时，交界沿真实解剖轮廓画1原生像素深色线；不是一块矩形/直边遮罩。禁止沿水平或竖直线把近侧胯、短裤、近腿切暗。远侧暗色不能只到小腿或局部：整条肢体连续一致。亮暗角色不会因为脚在前或后而交换。
用此色板的远近角色定义：{json.dumps(palette['side_view_roles'],ensure_ascii=False)}。
左上光，1原生像素深外轮廓，硬边像素，无抗锯齿，最多32色。其余参考只用于身份，不改参考1姿势。不得加地面、文字、阴影、特效、额外肢体。直接完成整帧成品，我们不会把标签或局部像素映射回旧图。'''
    if f=='ultraseven':prompt+='赛文头冠严格复制已审头部参考：前缘竖直高0.3头高，后尾沿后脑下扫；黄眼绿额灯、无胸计时器；参考1若已摘镖则保持低棱，不擅自补上头镖。'
    prompt+='本帧原图人为压暗断层位于：'+json.dumps(t['introduced_boundaries'],ensure_ascii=False)+'。这些坐标是原生坐标，仅用于解释错误，不是新遮罩。'+feedback
    # API编辑蒙版仅约束透明画布/最外轮廓，整个人物内部统一可编辑。
    # 这是提交给GPT的保护条件，不在后处理恢复任何原像素，也不含远近颜色区域。
    a=np.array(im.getchannel('A'))>0
    interior=cv2.erode(a.astype('uint8'),np.ones((3,3),np.uint8))>0
    mask=np.zeros((h,w,4),dtype='uint8');mask[:,:,:3]=255;mask[:,:,3]=np.where(interior,0,255)
    Image.fromarray(mask).resize((w*6,h*6),Image.Resampling.NEAREST).save(folder/'silhouette-protection.png')
    prompt+='编辑蒙版仅保护透明画布和最外1像素轮廓；整个人物内部全部允许GPT重画，必须遵守蒙版固定外剪影，不改变任何透明边界。'
    value=dict(model='gpt-image-2.5-sunburst',fighter=f,asset_key=t['key'],identity_revision='model05' if f=='ultraseven' else 'approved-head-scale',attempt_series=SERIES,
        asset_registry=rel(REG),category='压暗重画',quality='high',asset_kind='character',size=f'{w*6}x{h*6}',references=[rel(folder/'edit-input-x6.png')]+anchors,prompt=prompt)
    value['mask']=rel(folder/'silhouette-protection.png')
    save(folder/'brief.json',value);return folder/'brief.json'

def iou(a,b):return float((a&b).sum()/max(1,(a|b).sum()))

def foot_registration(before,after):
    """最低Alpha带的二维登记；直立可作接地点代理，空翻只作外轮廓诊断。"""
    def point(im):
        y,x=np.where(np.array(im.getchannel('A'))>0)
        if not len(x):raise ValueError('空Alpha无法测脚底')
        band=y>=y.max()-1
        return [float(x[band].mean()),float(y.max()+1)]
    a,b=point(before),point(after);delta=[b[0]-a[0],b[1]-a[1]]
    return dict(before=a,after=b,delta=delta,distance=math.hypot(*delta),method='原生最低两行脚部Alpha中心，二维欧氏距离；canvas根锚不改')

def register(raw,base,fighter):
    """仅全帧统一缩放/平移；没有旧像素粘贴、Alpha替换或部位形变。"""
    source=np.array(raw.getchannel('A'))>=128;target=np.array(base.getchannel('A'))>0
    by,bx=np.where(target);sy,sx=np.where(source)
    if not len(sx):raise ValueError('空图')
    w0,h0=bx.max()-bx.min()+1,by.max()-by.min()+1
    sw,sh=sx.max()-sx.min()+1,sy.max()-sy.min()+1
    center_scale=(w0/sw+h0/sh)/2
    best=(-1,None,None,None)
    # 统一比例在宽高估计附近搜索；只用透明Alpha登记，不以颜色标签恢复旧图。
    for scale in sorted(set(round(float(s),6) for s in np.linspace(center_scale*.94,center_scale*1.06,49))):
        rw,rh=round(raw.width*scale),round(raw.height*scale)
        if rw<16 or rh<16:continue
        alpha=cv2.resize(source.astype('uint8'),(rw,rh),interpolation=cv2.INTER_NEAREST)>0
        yy,xx=np.where(alpha)
        ox=round((bx.min()+bx.max()-xx.min()-xx.max())/2);oy=int(by.max()-yy.max())
        for dx in range(-2,3):
            for dy in [-1,0,1]:
                mat=np.float32([[1,0,ox+dx],[0,1,oy+dy]])
                placed=cv2.warpAffine(alpha.astype('uint8'),mat,base.size,flags=cv2.INTER_NEAREST)>0
                score=iou(target,placed)
                if score>best[0]:best=(score,scale,(ox+dx,oy+dy),(rw,rh))
    score,scale,offset,size=best
    snapped,_,_=proc.snap_for_scale(raw,scale)
    native=proc._kcentroid_downscale(snapped,*size);proc.binarize_alpha(native)
    # 正式后处理只有整体网格还原、二值透明和全图色板量化。
    native=proc.apply_palette(native,read(ROOT/f'content/fighters/{fighter}/palette.json')['colors'])
    canvas=Image.new('RGBA',base.size);canvas.alpha_composite(native,offset)
    # kCentroid透明边界与最近邻预搜索不同，重新平移登记实际成品（仍整帧）。
    best=(-1,None,None)
    for dx in range(-1,2):
        for dy in [-1,0,1]:
            im=Image.new('RGBA',base.size);im.alpha_composite(native,(offset[0]+dx,offset[1]+dy))
            a=np.array(im.getchannel('A'))>0
            ys,xs=np.where(a)
            if not len(xs):continue
            if abs(int(ys.max())-int(by.max()))>1:continue
            sc=iou(target,a)
            if sc>best[0]:best=(sc,im,[offset[0]+dx,offset[1]+dy])
    return best[1],dict(alpha_iou=best[0],scale=scale,translation=best[2],resized=size,processing='GPT整帧 → sprite-gen网格还原/kCentroid → 二值Alpha → 整图色板量化 → 整帧平移；无区域换色，无旧像素恢复')

def process(t,row):
    f=t['fighter'];folder=RUN/f/t['key']/f'take-{row["sequence"]:02}';folder.mkdir(parents=True,exist_ok=True)
    raw=ROOT/row['output']
    if not raw.exists():
        save(folder/'qa.json',dict(issues=['网络/Alpha失败，无可安装成品'],request=row['ledger_sequence']));return folder
    base=Image.open(ROOT/t['before']).convert('RGBA');im,reg=register(Image.open(raw).convert('RGBA'),base,f)
    if im is None:save(folder/'qa.json',dict(issues=['无法整帧登记'],request=row['ledger_sequence']));return folder
    im.save(folder/'frame-0.png');im.save(folder/'atlas.png');im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST).save(folder/'reference.png')
    old=read(RUN/f/t['key']/'before-head.json');h=head_size.head(im,f,old['hint'],direction=old.get('head_direction'),region=old.get('head_region'))
    ref=head_size.reference(f);issues=[]
    if reg['alpha_iou']<.97:issues.append(f'Alpha剪影IoU {reg["alpha_iou"]:.5f} < 0.97')
    if not h or abs(h['length']/ref['measurement']['length']-1)>.08:issues.append('头部尺寸±8%未过')
    a=np.array(im);b=np.array(base);foot_measure=foot_registration(base,im);foot_shift=foot_measure['distance']
    if foot_shift>1:issues.append('脚底锚点偏差>1px')
    headrow=dict(frame=0,image='frame-0.png',image_sha256=sha(folder/'frame-0.png'),source=rel(raw),source_sha256=sha(raw),shared_scale=reg['scale'],hint=(h or {}).get('center',old['hint']),head_direction=old.get('head_direction',[0,-1]),raw_head_length=(h or {}).get('length',0)/reg['scale'],measurement=h,foot_anchor=t['anchor'])
    for key in ['slugger_detached','facing','crown_view','manual_crown_reason','registration_angle_degrees','head_region','occlusion_polygon']:
        if key in old:headrow[key]=old[key]
    crown=None
    if f=='ultraseven' and h:
        try:
            crown=slugger_qa.compare(im,headrow,bool(headrow.get('slugger_detached')))
            if not crown['pass_']:issues.append('头镖剪影未过')
        except ValueError:issues.append('头镖不可测')
    # 严格列出所有未被轮廓隔开的4px直边；不把新图充当自身baseline。
    edges=color.boundaries(im,f)
    if edges:issues.append('无深轮廓的直线明暗候选，需逐条语义复核')
    save(folder/'head-qa.json',dict(reference=ref,scale_policy='per_frame_head',frames=[headrow],issues=[s for s in issues if '头' in s]))
    save(folder/'qa.json',dict(fighter=f,asset=t['key'],request=row['ledger_sequence'],registration=reg,foot_anchor_shift=foot_shift,foot_anchor_registration=foot_measure,crown=crown,boundaries=edges,issues=issues,
        semantic_review='实际脚部、整条远侧肢体、近侧/躯干未压暗及判定框抓点仍须逐帧复核；最低Alpha带不能替代空中脚部标点',status='rejected' if issues else 'pending_visual_review',direct_gpt_output=True))
    preview=Image.new('RGB',(base.width*12,base.height*6+48),'#202632');d=ImageDraw.Draw(preview)
    for i,pic in enumerate([base,im]):
        big=pic.resize((pic.width*6,pic.height*6),Image.Resampling.NEAREST);preview.paste(big,(i*pic.width*6,48),big);d.text((i*pic.width*6+8,8),'修前' if i==0 else f'GPT整帧候选 IoU={reg["alpha_iou"]:.4f}',font=font(22),fill='white')
    preview.save(folder/'comparison-x6.png');print(f,t['key'],row['revision_sequence'],issues,flush=True)
    return folder

def generate_one(t):
    previous=attempts(t);feedback=''
    if previous:
        p=RUN/t['fighter']/t['key']/f'take-{previous[-1]["sequence"]:02}/qa.json'
        if p.exists():feedback='上一稿未通过：'+str(read(p)['issues'])+'。本次务必精确复制参考1，不可改姿势、脚位或外框。'
    try:row=pilot.generate_action(t['fighter'],t['key'],brief(t,feedback))
    except Exception as exc:
        newer=attempts(t)
        if len(newer)<=len(previous):raise
        row=newer[-1];print(t['key'],type(exc).__name__,flush=True)
    return process(t,row)

def run_queue(fighter,start=0,stop=None,once=False):
    if fighter!='ultraseven':
        # 多进程补做也遵守先赛文、后旧角色试做，不跨越未结案的前置帧。
        all_seven=[t for t in read(RUN/'tasks.json') if t['fighter']=='ultraseven']
        while True:
            pending=[i for i,t in enumerate(all_seven) if not any((RUN/'ultraseven'/t['key']/n).exists() for n in ['candidate.json','accepted.json','blocked.json'])]
            if not pending:break
            for i in pending:
                t=all_seven[i]
                if not (RUN/'ultraseven'/t['key']/'.queue.lock').exists():run_queue('ultraseven',i,i+1)
            time.sleep(2)
    tasks=[t for t in read(RUN/'tasks.json') if t['fighter']==fighter][start:stop]
    for t in tasks:
        if (RUN/fighter/t['key']/'accepted.json').exists():continue
        lock=RUN/fighter/t['key']/'.queue.lock'
        try:handle=lock.open('x');handle.write(str(__import__('os').getpid()));handle.close()
        except FileExistsError:continue
        try:
            while len(attempts(t))<6:
                before=len(attempts(t))
                try:folder=generate_one(t);q=read(folder/'qa.json')
                except Exception as exc:
                    if len(attempts(t))<=before:
                        save(RUN/fighter/t['key']/'local-block.json',dict(status='本地前置阻塞',error_type=type(exc).__name__,reason=str(exc)));raise
                    save(RUN/fighter/t['key']/f'local-qa-error-{before+1}.json',dict(error_type=type(exc).__name__,reason=str(exc)))
                    continue
                if not q['issues']:
                    save(RUN/fighter/t['key']/'candidate.json',dict(folder=rel(folder),status='数值初筛通过；尚需远近整条肢体语义复核'))
                    break
                if once:break
            if len(attempts(t))>=6 and not (RUN/fighter/t['key']/'candidate.json').exists():
                save(RUN/fighter/t['key']/'blocked.json',dict(status='待人工',attempts=6,reason='新授权GPT整帧重画6次仍未达到剪影/头部/轮廓验收，不安装；继续下一帧'))
        finally:lock.unlink()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','queue','process']);p.add_argument('--fighter',default='ultraseven');p.add_argument('--start',type=int,default=0);p.add_argument('--stop',type=int);p.add_argument('--once',action='store_true');a=p.parse_args()
    if a.command=='prepare':prepare()
    elif a.command=='queue':run_queue(a.fighter,a.start,a.stop,a.once)
    else:
        for t in read(RUN/'tasks.json'):
            rows=attempts(t)
            if rows:process(t,rows[-1])

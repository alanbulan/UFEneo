"""初代/杰顿循环的只读测量审计；不生成、不变换或替换人物帧。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import argparse,csv,hashlib,json,subprocess,sys; json = _LayoutJson
from datetime import datetime,timezone
import cv2
import numpy as np
from PIL import Image,ImageDraw
from head_scale import ROOT,read,save,font,sha
sys.path.insert(0,str(ROOT/'tools'))
from check.limb_idle import frame_row
import loop_qa
from idle_qa import feature as legacy_feature
from loop_repair_landmarks import annotation,marked_feature

WORK=ROOT/'art/shared/production/loop-repair'
OUT=ROOT/'reports/review/2026-10-22/loop-repair'
ACTIONS=['idle','walk_forward','walk_back','stun','charge','crouch']
NAMES={'idle':'待机','walk_forward':'前走','walk_back':'后走','stun':'眩晕','charge':'蓄能','crouch':'蹲姿保持'}
FIGHTERS={'ultraman':'初代','zetton':'杰顿'}


def clips(fighter):
    manifest=read(ROOT/f'assets/fighters/{fighter}/animations/manifest.json')['clips']
    for action,c in manifest.items():
        if not c.get('loop') or (fighter in ['ultraman','zetton'] and action not in ACTIONS):continue
        atlas=Image.open(ROOT/c['texture'].removeprefix('res://')).convert('RGBA');hq=read(ROOT/c['head_qa'])
        images=[atlas.crop((x,y,x+w,y+h)) for x,y,w,h in c['rects']]
        heads=[frame_row(hq['frames'],c,i) for i in range(len(images))]
        yield action,c,images,heads


def snapshot():
    WORK.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    if (WORK/'baseline.json').exists():
        return read(WORK/'baseline.json')
    if not (WORK/'ledger.json').exists():
        save(WORK/'ledger.json',dict(schema=1,scope='初代、杰顿已装循环只读测量核实；未经下一条授权不得生图或替换帧',requests=[],counts=dict(ultraman=0,zetton=0,total=0)))
        save(WORK/'brake.json',dict(scope='loop-repair独立防空转',paused={},records=[],generation_enabled=False,reason='本轮仅测量核实，零请求'))
    records={}
    for fighter in ['ultraman','zetton','ultraseven']:
        result=[]
        for action,c,images,heads in clips(fighter):
            result.append(dict(action=action,clip=c,heads=heads,texture_sha256=sha(ROOT/c['texture'].removeprefix('res://')),frame_hashes=[hashlib.sha256(im.tobytes()).hexdigest() for im in images],legacy=loop_qa.evaluate([legacy_feature(im,fighter,h) for im,h in zip(images,heads)],action),measurement_before=loop_qa.measure(images,fighter,heads,action)))
        records[fighter]=result
    save(WORK/'baseline.json',records)
    return records


def baseline_contacts():
    baseline=read(WORK/'baseline.json')
    for fighter in ['ultraman','zetton']:
        for action,c,images,heads in clips(fighter):
            r=next(x for x in baseline[fighter] if x['action']==action);centers=r['legacy']['centers'];w,h=images[0].size;cols=4
            sheet=Image.new('RGB',(w*4*cols,(h*4+100)*int(np.ceil(len(images)/cols))),'#202632');d=ImageDraw.Draw(sheet)
            for i,(im,head,point) in enumerate(zip(images,heads,centers)):
                x=i%cols*w*4;y=i//cols*(h*4+100);big=im.resize((w*4,h*4),Image.Resampling.NEAREST);sheet.paste(big,(x,y+100),big)
                px,py=point;cx,cy=head['hint'];d.line((x+px*4-14,y+100+py*4,x+px*4+14,y+100+py*4),fill='#ff7288',width=3);d.line((x+px*4,y+100+py*4-14,x+px*4,y+100+py*4+14),fill='#ff7288',width=3)
                d.ellipse((x+cx*4-10,y+100+cy*4-10,x+cx*4+10,y+100+cy*4+10),outline='#7dd3fc',width=2)
                d.text((x+10,y+8),f'{fighter}/{action} #{i} / {c["ticks"][i]} tick',font=font(25),fill='white');d.text((x+10,y+44),f'红十字旧测量({px:.2f},{py:.2f}) 蓝圈旧头部提示',font=font(21),fill='white')
            dest=OUT/fighter/action;dest.mkdir(parents=True,exist_ok=True);sheet.save(dest/'legacy-points-x4.png')


def marker_probes():
    """仅输出检测候选，先目视核对再决定是否修改共享测量。"""
    records=[]
    for fighter in ['ultraman','zetton']:
        for action,c,images,heads in clips(fighter):
            tiles=[]
            for i,(im,h) in enumerate(zip(images,heads)):
                a=np.asarray(im);r,g,b=a[:,:,:3].astype(int).transpose(2,0,1);yy,xx=np.indices(a.shape[:2]);cx,cy=h['hint']
                region=(abs(xx-cx)<24)&(abs(yy-cy)<24)&(a[:,:,3]>0)
                warm=((r>90)&(g>50)&(r-b>40)&(g-b>25)) if fighter=='ultraman' else ((r>150)&(g>60)&(b<110)&(r>g*1.05))
                n,labels,stats,centers=cv2.connectedComponentsWithStats((warm&region).astype('uint8'),8)
                ids=[j for j in range(1,n) if stats[j,4]>=2]
                candidate=[]
                for j in ids:
                    x,y,w,hh,area=map(int,stats[j]);candidate.append(dict(bbox=[x,y,x+w,y+hh],centroid=centers[j].tolist(),area=area))
                records.append(dict(fighter=fighter,action=action,frame=i,hint=h['hint'],legacy=legacy_feature(im,fighter,h),candidates=candidate))
                x0=int(cx)-28;y0=int(cy)-28
                tile=Image.new('RGB',(720,790),'#202632');d=ImageDraw.Draw(tile)
                crop=im.crop((x0,y0,x0+56,y0+56)).resize((672,672),Image.Resampling.NEAREST);tile.paste(crop,(24,90),crop)
                for j,comp in enumerate(candidate):
                    x,y,x1,y1=comp['bbox'];d.rectangle((24+(x-x0)*12,90+(y-y0)*12,24+(x1-x0)*12-1,90+(y1-y0)*12-1),outline='#2eeeb7',width=2)
                    d.text((24+(x-x0)*12,90+(y-y0)*12-25),f'C{j} a{comp["area"]}',font=font(19),fill='#2eeeb7')
                px,py=legacy_feature(im,fighter,h);x=24+(px-x0+.5)*12;y=90+(py-y0+.5)*12
                d.line((x-12,y,x+12,y),fill='#ff7288',width=3);d.line((x,y-12,x,y+12),fill='#ff7288',width=3)
                d.text((12,8),f'{fighter}/{action} #{i}',font=font(25),fill='white');d.text((12,44),'绿框暖色分量；红十字旧测点；12倍',font=font(22),fill='white')
                tiles.append(tile)
            sheet=Image.new('RGB',(720*4,790*int(np.ceil(len(tiles)/4))),'#202632')
            for i,tile in enumerate(tiles):sheet.paste(tile,((i%4)*720,(i//4)*790))
            dest=OUT/fighter/action;dest.mkdir(parents=True,exist_ok=True);sheet.save(dest/'marker-probes-x12.png')
    save(WORK/'marker-probes.json',records)


def annotate():
    """近侧眼框逐帧目视核实的测量标注；坐标为原生像素，不改帧。"""
    boxes={
        'idle':[[98,63,107,70],[99,61,108,68],[94,61,105,68],[99,60,108,68],[98,61,108,68],[99,61,108,68]],
        'walk_forward':[[101,61,110,68],[101,53,110,60],[103,56,112,62],[102,45,111,52],[103,52,111,58],[102,49,110,56],[100,48,108,54],[103,55,112,62]],
        'walk_back':[[95,64,104,71],[93,59,103,67],[94,60,103,67],[94,60,104,67],[96,58,105,65],[97,63,106,70],[95,61,104,68],[96,59,104,65]],
        'stun':[[103,60,111,68],[101,98,107,104],[103,108,106,112],[103,63,111,71],[102,61,111,70],[101,103,107,108]],
        'charge':[[117,91,124,99],[117,88,124,95],[117,85,124,93],[117,83,124,91]],
        'crouch':[[111,84,120,91],[108,82,118,89]],
    }
    records=[]
    for action,c,images,heads in clips('ultraman'):
        assert len(images)==len(boxes[action])
        for i,(im,bounds) in enumerate(zip(images,boxes[action])):
            records.append(dict(fighter='ultraman',action=action,frame=i,size=list(im.size),frame_sha256=hashlib.sha256(im.tobytes()).hexdigest(),feature='近侧完整眼框中心（含眼内白色）',bounds=bounds,annotation_status='本轮目视标注，交用户复核'))
    save(WORK/'marker-annotations.json',dict(schema=1,date='2026-10-22',purpose='仅修正旧测量在近侧眼、远侧小眼、眼框碎片间跳选；不改人物、不改门槛、不替新图豁免',coordinate_convention='左上闭、右下开；像素中心为整数坐标，点取外框中心',frames=records))


def lamp_bounds(im,head,point):
    """杰顿面部发光体几何框，独立复核其旧色块重心没有落到胸灯。"""
    a=np.asarray(im);r,g,b=a[:,:,:3].astype(int).transpose(2,0,1);yy,xx=np.indices(a.shape[:2]);cx,cy=head['hint']
    mask=(abs(xx-cx)<24)&(abs(yy-cy)<24)&(a[:,:,3]>0)&(r>150)&(g>60)&(b<110)&(r>g*1.05)
    n,labels,stats,centers=cv2.connectedComponentsWithStats(mask.astype('uint8'),8)
    ids=[j for j in range(1,n) if stats[j,4]>=2]
    j=min(ids,key=lambda j:np.linalg.norm(centers[j]-point));x,y,w,h,_=map(int,stats[j])
    return [x,y,x+w,y+h]


def cross(draw,x,y,color,arm=11):
    draw.line((x-arm,y,x+arm,y),fill=color,width=3);draw.line((x,y-arm,x,y+arm),fill=color,width=3)


def contact_sheet(fighter,action,c,images,heads,old,result,bounds):
    w,h=images[0].size;cols=min(4,len(images));tile_h=h*4+122
    sheet=Image.new('RGB',(w*4*cols,tile_h*int(np.ceil(len(images)/cols))),'#202632');d=ImageDraw.Draw(sheet)
    for i,(im,head,point,prior,box) in enumerate(zip(images,heads,result['centers'],old['centers'],bounds)):
        x=i%cols*w*4;y=i//cols*tile_h;top=y+122
        big=im.resize((w*4,h*4),Image.Resampling.NEAREST);sheet.paste(big,(x,top),big)
        d.text((x+12,y+6),f'{FIGHTERS[fighter]} {NAMES[action]} #{i} / {c["ticks"][i]} tick',font=font(28),fill='white')
        d.text((x+12,y+47),f'绿:复核({point[0]:.2f},{point[1]:.2f}) 红:旧({prior[0]:.2f},{prior[1]:.2f})',font=font(21),fill='white')
        d.text((x+12,y+80),'完整近侧眼框中心' if fighter=='ultraman' else '脸部发光体重心（不是胸部）',font=font(24),fill='#5fe8be')
        if box:
            bx,by,bx1,by1=box;d.rectangle((x+bx*4,top+by*4,x+bx1*4-1,top+by1*4-1),outline='#5fe8be',width=2)
        cross(d,x+(prior[0]+.5)*4,top+(prior[1]+.5)*4,'#ff7288',arm=14)
        cross(d,x+(point[0]+.5)*4,top+(point[1]+.5)*4,'#5fe8be',arm=8)
        anchor=c.get('anchor',c.get('foot_anchor',[w/2,h-8]));ay=anchor[1] if isinstance(anchor,(list,tuple)) else h-8
        d.line((x,top+ay*4,x+w*4-1,top+ay*4),fill='#426074',width=1)
    return sheet


def head_strip(fighter,action,images,result,old,bounds):
    tile_w=480;tile_h=540;sheet=Image.new('RGB',(tile_w*len(images),tile_h),'#202632');d=ImageDraw.Draw(sheet)
    for i,(im,point,prior,box) in enumerate(zip(images,result['centers'],old['centers'],bounds)):
        x=i*tile_w;left=int(point[0])-28;top=int(point[1])-27
        crop=im.crop((left,top,left+56,top+56)).resize((448,448),Image.Resampling.NEAREST);sheet.paste(crop,(x+16,80),crop)
        d.text((x+12,6),f'{FIGHTERS[fighter]} {NAMES[action]} #{i}',font=font(25),fill='white');d.text((x+12,42),f'x={point[0]:.2f}, y={point[1]:.2f}',font=font(23),fill='#5fe8be')
        bx,by,bx1,by1=box;d.rectangle((x+16+(bx-left)*8,80+(by-top)*8,x+16+(bx1-left)*8-1,80+(by1-top)*8-1),outline='#5fe8be',width=2)
        cross(d,x+16+(prior[0]-left+.5)*8,80+(prior[1]-top+.5)*8,'#ff7288',arm=12)
        cross(d,x+16+(point[0]-left+.5)*8,80+(point[1]-top+.5)*8,'#5fe8be',arm=9)
    return sheet


def curve(fighter,action,c,old,result):
    sheet=Image.new('RGB',(1500,1060),'#202632');d=ImageDraw.Draw(sheet)
    ys=np.asarray(result['centers'])[:,1];xs=np.asarray(result['centers'])[:,0]
    d.text((45,18),f'{FIGHTERS[fighter]} / {NAMES[action]}：原生画布坐标轨迹（含首尾接头）',font=font(31),fill='white')
    d.text((45,64),f'总幅 {np.ptp(ys):.3f}px / 相邻最大 {max(result["adjacent_y"]):.3f}px / 水平 {np.ptp(xs):.3f}px',font=font(27),fill='#5fe8be')
    d.text((45,106),'绿色：复核点；红色虚线：旧点；纵坐标向下增大；点间按正式 tick 时长排布',font=font(24),fill='white')
    elapsed=np.r_[0,np.cumsum(c['ticks'])];total=elapsed[-1]
    for dim,top,bottom,label in [(1,205,520,'画布 y（向下为低头）'),(0,665,980,'画布 x')]:
        new=np.r_[np.asarray(result['centers'])[:,dim],result['centers'][0][dim]];prev=np.r_[np.asarray(old['centers'])[:,dim],old['centers'][0][dim]]
        lo=float(min(new.min(),prev.min())-2);hi=float(max(new.max(),prev.max())+2)
        if hi-lo<8:lo-=2;hi+=2
        def pos(t,v):return (130+t/total*1280,top+(v-lo)/(hi-lo)*(bottom-top))
        d.text((45,top-43),label,font=font(25),fill='white')
        for v in np.linspace(lo,hi,5):
            _,py=pos(0,v);d.line((130,py,1410,py),fill='#3a4657',width=1);d.text((40,py-13),f'{v:.1f}',font=font(20),fill='#ced5e1')
        prior_points=[pos(t,v) for t,v in zip(elapsed,prev)];new_points=[pos(t,v) for t,v in zip(elapsed,new)]
        for a,b in zip(prior_points,prior_points[1:]):
            for t in np.arange(0,1,.15):
                t1=min(1,t+.075);d.line((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[0]+(b[0]-a[0])*t1,a[1]+(b[1]-a[1])*t1),fill='#ff7288',width=2)
        d.line(new_points,fill='#5fe8be',width=3)
        for i,((px,py),v) in enumerate(zip(new_points,new)):
            d.ellipse((px-5,py-5,px+5,py+5),fill='#5fe8be');d.text((px-18,py-27),f'{v:g}',font=font(20),fill='white')
            d.text((px-20,bottom+12),str(i) if i<len(new)-1 else '0接头',font=font(20),fill='white')
    return sheet


def three_cycles(dest,fighter,action,c,images,result):
    frames=[];durations=[];elapsed_ms=0;previous=0;w,h=images[0].size
    for cycle in range(3):
        for i,im in enumerate(images):
            tile=Image.new('RGB',(w*4,h*4+104),'#202632');d=ImageDraw.Draw(tile);big=im.resize((w*4,h*4),Image.Resampling.NEAREST);tile.paste(big,(0,104),big)
            d.text((12,8),f'{FIGHTERS[fighter]} {NAMES[action]} | 周期 {cycle+1}/3 | 帧 {i}',font=font(26),fill='white')
            point=result['centers'][i];d.text((12,49),f'{c["ticks"][i]} tick  原生点 x={point[0]:.2f}, y={point[1]:.2f}',font=font(24),fill='#5fe8be')
            frames.append(tile);elapsed_ms+=c['ticks'][i]*1000/60;rounded=int(round(elapsed_ms/10))*10;durations.append(rounded-previous);previous=rounded
    # 不写无限循环标记；文件内部就是三个完整周期。仅四倍最近邻展示。
    frames[0].save(dest/'three-cycles.gif',save_all=True,append_images=frames[1:],duration=durations,optimize=False,disposal=2)


def proofs():
    baseline=read(WORK/'baseline.json');unchanged=[];seven=[]
    for fighter in ['ultraman','zetton']:
        for action,c,images,heads in clips(fighter):
            prior=next(x for x in baseline[fighter] if x['action']==action)
            frame_hashes=[hashlib.sha256(im.tobytes()).hexdigest() for im in images]
            row=dict(fighter=fighter,action=action,clip_unchanged=c==prior['clip'],texture_unchanged=sha(ROOT/c['texture'].removeprefix('res://'))==prior['texture_sha256'],all_frame_pixels_unchanged=frame_hashes==prior['frame_hashes'],frame_hashes=frame_hashes)
            unchanged.append(row)
            assert all(row[k] for k in ['clip_unchanged','texture_unchanged','all_frame_pixels_unchanged']),row
    for action,c,images,heads in clips('ultraseven'):
        legacy=dict(fighter='ultraseven',**loop_qa.evaluate([legacy_feature(im,'ultraseven',h) for im,h in zip(images,heads)],action));current=loop_qa.measure(images,'ultraseven',heads,action)
        prior=next((x for x in baseline['ultraseven'] if x['action']==action),None)
        seven.append(dict(action=action,frames=len(images),same_input_old_new_exactly_equal=legacy==current,baseline_inputs_still_equal=bool(prior and c==prior['clip'] and [hashlib.sha256(im.tobytes()).hexdigest() for im in images]==prior['frame_hashes']),result=current))
        assert legacy==current,action
    paths=['assets/fighters/ultraman','assets/fighters/zetton','content/fighters/ultraman','content/fighters/zetton']
    dirty=subprocess.check_output(['git','diff','--name-only','--',*paths],cwd=ROOT,text=True,encoding='utf-8').splitlines()
    save(OUT/'unchanged-formal-inputs.json',dict(formal_files_diff=dirty,clips=unchanged,no_asset_replacement=True))
    save(OUT/'seven-invariance.json',dict(policy='同一份当前赛文输入分别运行旧函数与增量后的函数，逐字段精确相等；不修改赛文素材或数据',all_equal=all(x['same_input_old_new_exactly_equal'] for x in seven),clips=seven))
    assert not dirty,dirty
    return unchanged,seven


def export():
    baseline=read(WORK/'baseline.json');records=[]
    for fighter in ['ultraman','zetton']:
        for action,c,images,heads in clips(fighter):
            old=next(x for x in baseline[fighter] if x['action']==action)['legacy'];result=loop_qa.measure(images,fighter,heads,action)
            bounds=[annotation(im,fighter)['bounds'] if fighter=='ultraman' else lamp_bounds(im,h,p) for im,h,p in zip(images,heads,result['centers'])]
            boxes_centers=[[(x+x1-1)/2,(y+y1-1)/2] for x,y,x1,y1 in bounds]
            corroboration=loop_qa.evaluate(boxes_centers,action)
            if fighter=='ultraman':
                trust='近侧完整眼框逐帧标注可信；旧色块法有远眼/碎片跳选' if action in ['walk_forward','walk_back','stun','charge'] else '旧点位于近侧眼；完整眼框复核可信'
            else:trust='可信：全部点位于脸部发光体；不是眼睛、不是胸灯'
            if fighter=='ultraman' and action=='stun':cause='真实尺寸跳变；0/3/4帧大、1/2/5帧小，眼点始终在头上；测量误差不足以解释46px'
            elif result['issues']:cause='真实头部/标志点位移仍超门槛'+('；旧测量还夹杂选点误差' if fighter=='ultraman' and action in ['walk_forward','walk_back','charge'] else '')
            else:cause='复核后在现行循环门槛内，无需由本轮决定返工'
            r=dict(fighter=fighter,action=action,frames=len(images),ticks=c['ticks'],feature='近侧完整眼框中心' if fighter=='ultraman' else '脸部发光体暖色连通区域重心',measurement_trust=trust,diagnosis=cause,old=old,corrected=result,geometric_corroboration=corroboration,feature_bounds=bounds,alpha_bounds=[list(im.getbbox()) for im in images])
            records.append(r);dest=OUT/fighter/action;dest.mkdir(parents=True,exist_ok=True)
            save(dest/'measurement.json',r)
            contact_sheet(fighter,action,c,images,heads,old,result,bounds).save(dest/'measurement-points-x4.png')
            head_strip(fighter,action,images,result,old,bounds).save(dest/'measurement-heads-x8.png')
            curve(fighter,action,c,old,result).save(dest/'feature-curve.png');three_cycles(dest,fighter,action,c,images,result)
    save(OUT/'measurements.json',dict(scope='只核实初代/杰顿六类已装循环；不生图、不替换、不改时长',frames=64,clips=records))
    with (OUT/'measurement-summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['角色','动作','测量是否可信','旧总幅','旧相邻最大','旧水平漂移','复核总幅','复核相邻最大含接头','复核水平漂移','结论','超门槛项'])
        for r in records:
            a=r['old'];b=r['corrected'];writer.writerow([FIGHTERS[r['fighter']],r['action'],r['measurement_trust'],f'{a["vertical_range"]:.3f}',f'{max(a["adjacent_y"]):.3f}',f'{a["horizontal_range"]:.3f}',f'{b["vertical_range"]:.3f}',f'{max(b["adjacent_y"]):.3f}',f'{b["horizontal_range"]:.3f}',r['diagnosis'],'；'.join(b['issues'])])
    proofs()
    print(json.dumps([dict(fighter=r['fighter'],action=r['action'],vertical=r['corrected']['vertical_range'],adjacent=max(r['corrected']['adjacent_y']),horizontal=r['corrected']['horizontal_range'],issues=r['corrected']['issues']) for r in records],ensure_ascii=False,indent=2))


def report():
    rows=read(OUT/'measurements.json')['clips'];seven=read(OUT/'seven-invariance.json')
    def triple(r):return f'{r["vertical_range"]:.3f} / {max(r["adjacent_y"]):.3f} / {r["horizontal_range"]:.3f}'
    lines=['# 初代、杰顿循环：测量核实（2026-10-22）','',
        '本轮只核实正式素材的测量点，没有生图、替换帧、改时长、移动锚点、改判定或更改已审状态。所有修复都等待用户下一条决定。初代与杰顿各六条循环，共64个播放帧。','',
        '**结论**','',
        '- 杰顿一直量的是脸部中央橙黄色发光体的连通色块重心，全部标点都落在脸上，没有量到胸部发光体；另用完整脸灯外框中心交叉复核。原扫描的大幅位移真实存在。',
        '- 初代旧算法只挑“离头部提示点最近的暖色连通分量”。前走1、2、6帧会挑远侧小眼；另有眼框被白色眼内高光拆开、只挑到一段边框的情况。此次逐帧标注完整近侧眼框（含眼内白色），统一取框中心；标注图交用户复核。',
        '- 初代眩晕不是46px的纯测量误报：复核仍为46.000px、相邻最大43.000px。0/3/4帧主体高141/139/140px，1/2/5帧仅97/89/93px；头眼也随人物真实变小。此处应由用户判断尺寸与动作，不以换测量点掩盖。',
        '- 初代后走的接头被旧选点低估：完整眼框复核后的总幅6.000px、相邻最大5.500px（7→0）。原算法本来就包含首尾；此次修正的是测量部位。杰顿蹲姿保持的水平3.826px也列出，未擅自修复。','',
        '**测量口径**','',
        '数值单位全部为原生像素，按正式画布坐标测量，y向下增大。总幅=max(y)-min(y)，相邻最大包括末帧回首帧；水平=max(x)-min(x)。没有平移、归一化或对齐人物后再量。所有曲线保留正式tick时长；动图以四倍最近邻展示原帧，文件内恰好三个周期，GIF时间以10ms累计取整。','',
        '初代标注为完整近侧眼框的像素外框，坐标为左上闭、右下开，取像素中心的几何中点；形状破碎的眩晕小帧也保持同一解剖部位。它是本轮可复核的逐帧标注，不是通用于新图的自动识别结果。标注绑定完整RGBA像素哈希和画布尺寸，新帧不能继承；没有匹配标注的帧继续原检测器。杰顿保留已核实的原脸灯重心；完整脸灯外框中心的独立对照存于每条measurement.json的geometric_corroboration。','',
        '门槛未变：待机、蓄能、蹲姿保持的总幅≤6、相邻≤3、水平≤3；眩晕总幅≤12、相邻≤4；步行总幅≤8、相邻≤4。步行的脚步和时长数据本轮未动，也没有重新声明它们已审。初代、杰顿仍按原政策只报告。','',
        '**逐动作判定**','',
        '下表实测顺序均为“总幅 / 相邻最大（含接头）/ 水平漂移”。精确标注和旧值在[CSV](measurement-summary.csv)、[JSON](measurements.json)。','',
        '|角色 / 动作|测量是否可信|旧实测 px|复核后实测 px|问题判断|',
        '|---|---|---|---|---|']
    for r in sorted(rows,key=lambda r:(['ultraman','zetton'].index(r['fighter']),ACTIONS.index(r['action']))):
        if r['fighter']=='zetton':trust='可信：脸灯，非胸灯'
        elif r['action'] in ['walk_forward','walk_back','stun','charge']:trust='旧选点有偏；完整近眼标注待用户复核'
        else:trust='旧点在近眼；完整眼框已复核'
        conclusion=('真实尺寸跳变，非测错部位' if r['fighter']=='ultraman' and r['action']=='stun' else ('仍超门槛：'+'；'.join(r['corrected']['issues']) if r['corrected']['issues'] else '现行门槛内'))
        lines.append(f'|{FIGHTERS[r["fighter"]]} {r["action"]}（{NAMES[r["action"]]}）|{trust}|{triple(r["old"])}|{triple(r["corrected"])}|{conclusion}|')
    lines+=['','**逐动作审片材料**','','绿框和绿十字是复核点，红十字是旧测量点。四倍整帧图保持正式画布和脚底位置；头部八倍条带仅为看清标志点而裁切，不用于计算整帧位移。','',
        '|角色 / 动作|四倍逐帧标注|头部八倍|眼高与水平曲线|原时长三周期动图|','|---|---|---|---|---|']
    for r in sorted(rows,key=lambda r:(['ultraman','zetton'].index(r['fighter']),ACTIONS.index(r['action']))):
        base=f'{r["fighter"]}/{r["action"]}';lines.append(f'|{FIGHTERS[r["fighter"]]} {r["action"]}|[标注]({base}/measurement-points-x4.png)|[头部]({base}/measurement-heads-x8.png)|[曲线]({base}/feature-curve.png)|[动图]({base}/three-cycles.gif)|')
    lines+=['','**隔离与验证**','',
        '- 正式PNG、每帧RGBA、manifest中的各循环clip数据均与开工基线一致；初代/杰顿的assets和content没有git差异。[未改素材证据](unchanged-formal-inputs.json)。没有替换资源，因而没有旧正式帧需要移档。',
        f'- 共享loop_qa只新增精确指纹匹配的初代测量标注入口，赛文继续原算法。赛文当前所有{len(seven["clips"])}条loop输入，旧函数与增量后的函数逐字段精确相等。[赛文不变证据](seven-invariance.json)。同组输入的比较不受主会话后续换图影响。',
        '- 本分支独立[台账](../../../art/production/loop-repair/ledger.json)：初代0、杰顿0、本轮合计0、分支累计0；[防空转记录](../../../art/production/loop-repair/brake.json)明确禁止本轮生成。没有写共享台账，也没有碰赛文或哥莫拉文件。']
    vr=OUT/'verify-run.json'
    if vr.exists():
        v=read(vr);failed=v['failed'];lines+=['',f'完整verify通过Godot锁执行，退出码{v["exit_code"]}。[完整日志](verify.log) / [原始结果](verification-result.json) / [执行信息](verify-run.json)。']
        if failed:
            lines+=['','实际失败项：'+ '；'.join(f'{r["name"]}（{r["reason"]}）' for r in failed)+'。失败保留，不调整其他会话文件。']
            context=OUT/'parallel-failure-context.json'
            if context.exists():
                lines+=['','失败归属依据（[原始日志及状态快照](parallel-failure-context.json)）：','']
                for name,reason in read(context)['attribution'].items():
                    if any(r['name']==name for r in failed):lines.append(f'- {name}：{reason}')
        else:lines+=['','本次verify没有失败项。画面质量仍由用户审片，不把脚本结果等同于审片通过。']
    else:lines+=['','完整verify正在Godot锁中排队，最终结果将在交付前写入本专题。']
    lines+=['','**复现**','','```bash',
        '.venv/bin/python tools/rebuild/shared/loop_repair_audit.py export',
        '.venv/bin/python tools/godot_lock.py -- .venv/bin/python tools/rebuild/shared/loop_repair_verify.py',
        '.venv/bin/python tools/rebuild/shared/loop_repair_audit.py report','```','',
        '本轮交付的是正式帧的只读测量材料，不是新录的主游戏演示。开始游戏.command → 训练 → 选初代 / 杰顿可查看保持原样的循环动作；测量动图请直接打开上表文件。下一步：停下，等用户指定返工动作。','']
    (OUT/'README.md').write_text('\n'.join(lines),'utf-8')


def validate():
    """验证逐帧标注不会套用新图，动图保留正式帧数与时长；不判美术好坏。"""
    records=[]
    for fighter in ['ultraman','zetton']:
        for action,c,images,heads in clips(fighter):
            r=read(OUT/fighter/action/'measurement.json');dest=OUT/fighter/action
            assert r['corrected']==loop_qa.measure(images,fighter,heads,action)
            for im,h,point in zip(images,heads,r['corrected']['centers']):
                px,py=point;assert im.getpixel((int(round(px)),int(round(py))))[3]>0,(fighter,action,point)
                if fighter=='ultraman':
                    assert annotation(im,fighter) is not None
                    changed=im.copy();red,green,blue,alpha=changed.getpixel((0,0));changed.putpixel((0,0),((red+1)%256,green,blue,alpha))
                    assert marked_feature(changed,fighter) is None,'新图不能继承标注'
                    assert loop_qa.feature(changed,fighter,h)==legacy_feature(changed,fighter,h),'新图检测器回退行为变了'
                else:assert loop_qa.feature(im,fighter,h)==legacy_feature(im,fighter,h)
            gif=Image.open(dest/'three-cycles.gif');assert gif.n_frames==3*len(images),(fighter,action,gif.n_frames)
            assert 'loop' not in gif.info,'三周期文件不应额外无限重复'
            total=0
            for i in range(gif.n_frames):gif.seek(i);total+=gif.info['duration']
            assert abs(total-3*sum(c['ticks'])*1000/60)<=5.01,(fighter,action,total)
            contact=Image.open(dest/'measurement-points-x4.png');assert contact.width==images[0].width*4*min(4,len(images))
            records.append(dict(fighter=fighter,action=action,annotation_pixels_opaque=True,hash_invalidation=True,gif_frames=gif.n_frames,gif_ms=total,formal_tick_ms=3*sum(c['ticks'])*1000/60))
    proofs();save(OUT/'measurement-validation.json',dict(policy='只验证标注绑定、兼容性、三周期帧数/时长和展示倍率；不判画面合格',clips=records))
    print('循环测量材料验证完成；正式素材未改，赛文同输入测量不变。')


def snapshot_failures():
    """保存当前持锁 verify 已完成的失败日志；只读其他会话的状态。"""
    own=OUT/'verification-result.json';outcomes=read(own if own.exists() else ROOT/'reports/verification.json');failed=[r for r in outcomes if r['status']=='failed'];kept=[]
    for r in failed:
        src=ROOT/'reports'/f'{r["name"]}.log'
        if src.exists():
            dest=OUT/'verify-failures'/src.name;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_text(src.read_text('utf-8'),'utf-8',newline='\n')
            else:dest.write_text(dest.read_text('utf-8'),'utf-8',newline='\n')
            kept.append(dict(name=r['name'],log=dest.relative_to(OUT).as_posix(),sha256=sha(dest)))
    states={}
    for fighter in ['ultraseven','gomora']:
        definition=read(ROOT/f'content/fighters/{fighter}/definition.json');states[fighter]={k:definition.get(k) for k in ['production_status','playable','pilot_playable']}
    save(OUT/'parallel-failure-context.json',dict(captured_utc=datetime.now(timezone.utc).isoformat(),failed_so_far=failed,logs=kept,read_only_parallel_states=states,attribution={
        'stage4-preparation':'哥莫拉并行分支已将definition设为pilot_partial/pilot_playable，旧检查器active分支仍只接受ultraseven；本分支没有改这些文件。',
        'stage4-pilot':'同一哥莫拉启用状态触发旧检查器fighter==ultraseven断言；不是本轮0请求台账问题。',
        'seven-fourth-ledger':'调用同一check_stage4_pilot入口，仍在角色启用状态处失败，并非请求记录不合法。',
        'loop-resources':'赛文现有charge总幅/相邻8.820px、水平5.099px；同输入新旧算法精确相同，属于主会话负责的既有动作。',
        'ultraseven-fourth':'对局manifest在read_json处JSON解析失败，随后_animation收到Nil，最终120秒超时。疑似并行写入时读取到不完整manifest，原因交主会话确认；本分支未改该测试、赛文资源或Godot逻辑。'
    }))
    print('已留存当前失败日志；未改其他会话文件。')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['snapshot','baseline_contacts','marker_probes','annotate','export','proofs','report','validate','snapshot_failures']);a=p.parse_args();globals()[a.command]()

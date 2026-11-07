"""确定性整帧后处理、资源清单与主游戏帧数据连接。不会生成或拼接肢体。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
from statistics import median
import argparse
import hashlib
import json; json = _LayoutJson
import math
import sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT=_LayoutProjectPath(_layout_root)
sys.path.insert(0,str(Path.home()/'.codex/skills/sprite-gen'))
from sprite_gen.frames.extract import (detect_pixel_grid,grid_snap_downscale,
    _kcentroid_downscale,apply_palette,binarize_alpha)
sys.path.insert(0,str(Path(__file__).resolve().parent))
from art_phase2 import CLIPS, save


def grid_figures(image,cols,rows,expected,with_bounds=False):
    """按姿势条网格分配完整连通域，允许原图轻微跨格，不能把邻格的脚切下来。

    行程并查集避免在百万像素原图上做逐像素 Python BFS。不补画、不拼接身体。
    同一格中的断肢仍完整保留，交给后面的碎片筛查拒收。
    """
    alpha=np.asarray(image)[:,:,3]>=200
    parent=[];runs=[];previous=[]
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for y,row in enumerate(alpha):
        edges=np.flatnonzero(np.diff(np.r_[False,row,False].astype(np.int8)))
        current=[]
        for start,end in zip(edges[::2],edges[1::2]):
            index=len(parent);parent.append(index);runs.append((y,int(start),int(end)))
            for pstart,pend,pindex in previous:
                if pend>=start and pstart<=end:
                    root_a,root_b=find(index),find(pindex)
                    if root_a!=root_b:parent[root_a]=root_b
            current.append((int(start),int(end),index))
        previous=current
    groups={}
    for index,run in enumerate(runs):groups.setdefault(find(index),[]).append(run)
    owned=[[] for _ in range(cols*rows)]
    major=[0 for _ in owned]
    for group in groups.values():
        area=sum(end-start for _,start,end in group)
        if area<20:continue
        cx=sum((start+end-1)/2*(end-start) for _,start,end in group)/area
        cy=sum(y*(end-start) for y,start,end in group)/area
        cell=min(rows-1,int(cy*rows/image.height))*cols+min(cols-1,int(cx*cols/image.width))
        owned[cell].extend(group)
        major[cell]=max(major[cell],area)
    if any(size>500 for size in major[expected:]):raise ValueError('生成帧数多于请求，空格出现额外人物')
    result=[]
    for index,group in enumerate(owned[:expected]):
        if not group:raise ValueError(f'格子{index}缺少完整人物')
        left=min(start for _,start,_ in group);right=max(end for _,_,end in group)
        top=min(y for y,_,_ in group);bottom=max(y for y,_,_ in group)+1
        mask=Image.new('L',(right-left,bottom-top))
        draw=ImageDraw.Draw(mask)
        for y,start,end in group:draw.line((start-left,y-top,end-left-1,y-top),fill=255)
        cut=image.crop((left,top,right,bottom));cut.putalpha(mask)
        result.append((cut,(left,top,right,bottom)) if with_bounds else cut)
    return result


def components(image):
    mask=(np.asarray(image)[:,:,3]>0).astype('uint8')
    count,labels=cv2.connectedComponents(mask,connectivity=8);groups=[]
    for label in range(1,count):
        ys,xs=np.where(labels==label);groups.append(list(zip(xs.tolist(),ys.tolist())))
    groups.sort(key=len,reverse=True)
    return groups


def snap_for_scale(image,factor,max_pitch=8):
    """检测到谐波粗格时取其细分格，禁止先过度降采样再放大到目标像素。"""
    if not math.isfinite(factor) or factor<=0:raise ValueError('头部比例必须为正的有限数')
    if factor>=1:return image.copy(),(1,1),(0,0)
    detected,phase=detect_pixel_grid(image,max_pitch=max_pitch)
    pitch=list(detected)
    limit=1/factor
    for axis in [0,1]:
        while pitch[axis]>limit and pitch[axis]>1:pitch[axis]/=2
    used=tuple(pitch);adjusted=tuple(v%p for v,p in zip(phase,used))
    snapped=grid_snap_downscale(image,used,phase=adjusted) if min(used)>1 else image.copy()
    if snapped.width<round(image.width*factor) or snapped.height<round(image.height*factor):
        raise ValueError('网格还原低于目标原生分辨率，不能再放大')
    return snapped,used,adjusted


def process(name,take=None):
    request=json.loads((ROOT/'art/fighters/ultraman/stage2/legacy/requests'/f'{name}.json').read_text('utf-8'))
    base=ROOT/request.get('generation_dir',f'art/fighters/ultraman/stage2/generation/{name}')
    candidates=sorted(base.glob('[0-9][0-9]/raw.png'))
	# 有真实 Alpha、仅四角低 Alpha 噪点的拒收原图可以进入确定性清理；仍不直接入库。
    if not candidates:
        rejected=sorted(base.glob('[0-9][0-9]/rejected/raw.png'))
        if rejected:
            check=Image.open(rejected[-1]).convert('RGBA')
            corners=[check.getpixel(p)[3] for p in [(0,0),(check.width-1,0),(0,check.height-1),(check.width-1,check.height-1)]]
            alpha=np.asarray(check)[:,:,3]
            if max(corners)<128 and (alpha==0).mean()>.05:candidates=[rejected[-1]]
    if not candidates: return dict(action=name,status='blocked',reason='缺少透明原图')
    raw=base/f'{take:02d}'/'raw.png' if take else candidates[-1]
    if take and not raw.exists():
        rejected=raw.parent/'rejected/raw.png'
        if not rejected.exists():return dict(action=name,status='blocked',reason='指定稿缺少原图')
        check=Image.open(rejected).convert('RGBA');alpha=np.asarray(check)[:,:,3]
        if max(check.getpixel(p)[3] for p in [(0,0),(check.width-1,0),(0,check.height-1),(check.width-1,check.height-1)])>=128 or (alpha==0).mean()<=.05:
            return dict(action=name,status='blocked',reason='拒收原图不满足低Alpha噪点清理条件')
        raw=rejected
    image=Image.open(raw).convert('RGBA')
    try:cells=grid_figures(image,request['columns'],request['rows'],request.get('source_frames',request['frames']))
    except ValueError as exc:return dict(action=name,status='blocked',reason=str(exc))
    if request.get('selected_frames'):
        selection=request['selected_frames']
        if len(selection)!=request['frames'] or len(set(selection))!=len(selection) or any(i<0 or i>=len(cells) for i in selection):raise ValueError('选稿帧必须为该原图独立完整人物，不重复、不越界')
        cells=[cells[i] for i in selection]
    if request.get('frame_order'):
        if sorted(request['frame_order'])!=list(range(len(cells))):raise ValueError('帧序必须只重排本条完整帧')
        cells=[cells[i] for i in request['frame_order']]
    fighter=request.get('fighter','ultraman');native_cell=int(request.get('native_cell',192));anchor=request.get('native_anchor',[native_cell//2,native_cell-8])
    palette=json.loads((ROOT/f'content/fighters/{fighter}/palette.json').read_text('utf-8'))['colors']
    # 姿势外框不是身体尺度；只有头部稳定特征能决定整张原图的唯一比例。
    import head_size
    try:factor,raw_heads,head_reference,head_issues=head_size.calibration(fighter,cells,request)
    except ValueError as exc:return dict(action=name,status='blocked',reason=str(exc))
    correction=float(request.get('head_scale_multiplier',1))
    if not math.isfinite(correction) or correction<=0:raise ValueError('只允许整张原图共用一个有效头部校准系数')
    factor*=correction
    head_reference['native_scale_correction']=correction
    frames=[];reports=[];head_records=[]
    for index,cell in enumerate(cells):
        factor=head_reference['frame_scales'][index]*correction*request.get('frame_scale_corrections',{}).get(str(index),1)
        snapped,pitch,phase=snap_for_scale(cell,factor)
        width=max(1,round(cell.width*factor));height=max(1,round(cell.height*factor))
        limit=native_cell-4 if request.get('airborne',False) else native_cell-8
        if width>limit or height>limit:
            return dict(action=name,status='blocked',reason=f'格子{index}超出原生画布，不能裁掉肢体')
        logical=_kcentroid_downscale(snapped,width,height)
        binarize_alpha(logical)
        logical=apply_palette(logical,palette)
        groups=components(logical)
        total=sum(map(len,groups))
        fragments=sum(len(g) for g in groups[1:] if len(g)>2)
        for group in groups[1:]:
            if len(group)<=2:
                for point in group:logical.putpixel(point,(0,0,0,0))
        alpha=np.asarray(logical)[:,:,3]>0
        waist_start,waist_end=round(height*.45),round(height*.65)
        fy,fx=np.where(alpha[waist_start:waist_end])
        foot_x=float(np.median(fx)) if len(fx) else width/2
        canvas=Image.new('RGBA',(native_cell,native_cell))
        intended_left=round(anchor[0]-foot_x)
        bottoms=request.get('native_bottoms',[])
        bottom=bottoms[index] if bottoms else request.get('native_bottom',anchor[1])
        offset=(max(0,min(native_cell-width,intended_left)),int(bottom)-height)
        if (name in ['flip_forward','diagonal_heavy','chase_light1'] or request.get('airborne',False)) and not request.get('align_root_to_bottom',False):
            ly,lx=np.where(alpha)
            offset=(max(0,min(192-width,round(96-float(lx.mean())))),max(0,min(192-height,round(116-float(ly.mean())))))
        if offset[1]<0 or offset[1]+height>native_cell:
            return dict(action=name,status='blocked',reason=f'格子{index}根锚会裁切，需修正参考根点；不裁人物')
        canvas.alpha_composite(logical,offset)
        rgba=np.asarray(canvas)
        visible=rgba[:,:,3]>0
        ys,xs=np.where(visible)
        colors=rgba[:,:,:3]
        blue=visible&(colors[:,:,2]>140)&(colors[:,:,1]>100)&((colors[:,:,2].astype(int)-colors[:,:,0].astype(int))>40)
        red=visible&(colors[:,:,0]>150)&(colors[:,:,0]>colors[:,:,1]*1.4)
        bright=visible&(colors[:,:,0]>180)&(colors[:,:,1]>170)&(colors[:,:,2]>110)
        if not len(xs):return dict(action=name,status='blocked',reason=f'格子{index}后处理为空')
        report=dict(frame=index,height=height,width=width,grid_pitch=pitch,grid_phase=phase,
                    fragment_fraction=fragments/max(1,total),blue_pixels=int(blue.sum()),
                    red_pixels=int(red.sum()),eye_color_pixels=int(bright.sum()),
                    centroid=[float(xs.mean()),float(ys.mean())],alpha_binary=True,anchor_clamp=offset[0]-intended_left)
        hint=[offset[0]+raw_heads[index]['center'][0]*factor,offset[1]+raw_heads[index]['center'][1]*factor]
        raw_region=request.get('head_regions',{}).get(str(index))
        raw_region=[[x*cell.width,y*cell.height] for x,y in raw_region] if raw_region else raw_heads[index]['polygon']
        head_region=[[offset[0]+x*factor,offset[1]+y*factor] for x,y in raw_region]
        direction=request.get('head_directions',{}).get(str(index),[0,-1]) if fighter=='ultraseven' else __import__('head_scale').pose_direction(request,index)
        measurement_axis=request.get('head_measurement_axes',{}).get(str(index),request.get('head_measurement_axis','length'))
        measured_head=head_size.width_measure(canvas,head_region) if measurement_axis=='width' else head_size.head(canvas,fighter,hint,direction=direction,region=head_region,method=head_reference.get('measurement_method'),facing=request.get('head_facings',{}).get(str(index)))
        head_deviation=(measured_head[measurement_axis]/head_reference['measurement'][measurement_axis]-1) if measured_head else None
        hidden=str(index) in head_reference.get('occluded_interpolation',{})
        if not hidden and (head_deviation is None or abs(head_deviation)>.08):head_issues.append(f'frame {index}: 成品头部尺寸超出±8%或不可测')
        report['head_size_deviation_percent']=None if head_deviation is None else round(head_deviation*100,4)
        head_records.append(dict(frame=index,image=f'frame-{index}.png',hint=hint,head_region=head_region,head_direction=direction,source=raw.relative_to(ROOT).as_posix(),source_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),raw_head_length=raw_heads[index]['length'],shared_scale=factor,measurement=measured_head))
        if fighter=='ultraseven':
            source_rgb=np.array(cell);cr,cg,cb=source_rgb[:,:,:3].astype(int).transpose(2,0,1)
            ly,lx=np.where((source_rgb[:,:,3]>0)&(cg>cr*1.3)&(cg>cb*1.1)&(cg>80))
            if len(lx):head_records[-1]['alignment_origin']=[offset[0]+float(lx.mean())*factor,offset[1]+float(ly.mean())*factor]
        head_records[-1].update(request.get('native_head_annotations',{}).get(str(index),{}))
        if hidden:head_records[-1].update(occluded=True,interpolation=head_reference['occluded_interpolation'][str(index)],measurement=None)
        if str(index) in request.get('head_facings',{}):head_records[-1]['facing']=request['head_facings'][str(index)]
        head_records[-1]['measurement_axis']=measurement_axis
        frames.append(canvas);reports.append(report)
    issues=list(head_issues)
    for item in reports:
        if item['fragment_fraction']>.005:issues.append(f"frame {item['frame']}: 存在游离身体碎片")
        if fighter=='ultraman' and item['blue_pixels']<1:issues.append(f"frame {item['frame']}: 蓝色计时器缺失")
        if fighter=='ultraman' and item['red_pixels']<60:issues.append(f"frame {item['frame']}: 身份红色块缺失")
        if item['eye_color_pixels']<8:issues.append(f"frame {item['frame']}: 高光/眼部颜色缺失")
    for before,after in zip(reports,reports[1:]):
        jump=math.dist(before['centroid'],after['centroid'])
        if jump>32:issues.append(f"frame {after['frame']}: 重心突变需复核")
    out=ROOT/'art/fighters/ultraman/stage2/legacy/processed'/name
    out.mkdir(parents=True,exist_ok=True)
    atlas=Image.new('RGBA',(native_cell*len(frames),native_cell))
    for index,frame in enumerate(frames):
        frame.save(out/f'frame-{index}.png');atlas.alpha_composite(frame,(native_cell*index,0))
        head_records[index]['image_sha256']=hashlib.sha256((out/f'frame-{index}.png').read_bytes()).hexdigest()
    atlas.save(out/'atlas.png')
    save(out/'head-qa.json',dict(scale_policy='per_frame_head',reference=head_reference,frames=head_records,issues=head_issues,rule='逐帧头部比例；成品头部偏差≤±8%；不使用姿势外框'))
    import limb_color_qa
    limb_color_qa.freeze_raw_baseline(out,frames,raw)
    # 联系表真 4 倍最近邻；每动作一行，背景只用于审片。
    contact=Image.new('RGB',(native_cell*len(frames)*4,native_cell*4+64),(29,35,48))
    contact.paste(atlas.resize((atlas.width*4,native_cell*4),Image.Resampling.NEAREST),(0,64),atlas.resize((atlas.width*4,native_cell*4),Image.Resampling.NEAREST))
    draw=ImageDraw.Draw(contact)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24)
    draw.text((16,12),f'{name} | 原生{native_cell}×{native_cell}，4倍最近邻 | '+' / '.join(issues[:2]),font=font,fill=(240,240,240))
    review=ROOT/request.get('review_dir','reports/review/2026-10-21-gate-a')
    review.mkdir(parents=True,exist_ok=True);contact_path=review/f'{name}-contact.png';contact_path.parent.mkdir(parents=True,exist_ok=True);contact.save(contact_path)
    contact.save(out/'contact.png')
    qa=dict(action=name,status='blocked' if issues else 'screened_pending_user_review',issues=issues,frames=reports,
            source=raw.relative_to(ROOT).as_posix(),source_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
            transform='姿势条网格分配完整连通域 → Alpha阈值 → 网格检测/对齐 → kCentroid → 共用32色 → 去孤立点 → 根锚点')
    save(out/'qa.json',qa)
    if fighter=='ultraseven' and head_issues and not request.get('native_feedback_pass') and all(r['measurement'] for r in head_records):
        # 量化后的头盔尺寸回馈一次，只缩放完整人物，不单独修头或移动肢体。
        request['frame_scale_corrections']={str(r['frame']):head_reference['measurement'][r['measurement_axis']]/r['measurement'][r['measurement_axis']] for r in head_records}
        request['native_feedback_pass']=1
        request['native_feedback_source_sha256']=qa['source_sha256']
        save(ROOT/'art/fighters/ultraman/stage2/legacy/requests'/f'{name}.json',request)
        return process(name,take)
    return dict(action=name,status=qa['status'],issues=issues)


def install():
    manifest=dict(schema=1,cell=[192,192],anchor=[96,184],reviewed=False,clips={})
    annotations=json.loads((ROOT/'art/fighters/ultraman/stage2/legacy/collision-annotations.json').read_text('utf-8'))['moves']
    production={}
    for name,(_,count,ticks,loop,_) in CLIPS.items():
        source=ROOT/'art/fighters/ultraman/stage2/legacy/processed'/name
        if not (source/'qa.json').exists():
            production[name]=dict(status='not_processed',reviewed=False);continue
        qa=json.loads((source/'qa.json').read_text('utf-8'))
        import head_size
        head_size.validate(source,'ultraman')
        production[name]=dict(status=qa['status'],reviewed=False,issues=qa['issues'])
        if qa['status']=='blocked':continue
        if qa.get('motion_review',{}).get('verdict') == 'blocked':
            production[name].update(status='motion_blocked_runtime_fallback',motion_review=qa['motion_review'])
        target=ROOT/'assets/fighters/ultraman/animations'/name
        target.mkdir(parents=True,exist_ok=True)
        shutil_source=source/'atlas.png'
        target.joinpath('atlas.png').write_bytes(shutil_source.read_bytes())
        manifest['clips'][name]=dict(texture='res://'+(target/'atlas.png').relative_to(ROOT).as_posix(),
            cell=192,anchor_y=184,rects=[[192*i,0,192,192] for i in range(count)],ticks=ticks,loop=loop,
            source_sha256=qa['source_sha256'])
        if qa.get('motion_review'):
            manifest['clips'][name]['motion_review']=qa['motion_review']
        if name in ['light1','light2','light3','diagonal_heavy','launcher','chase_light1']:
            move=json.loads((ROOT/'content/templates/humanoid/moves'/f'{name}.json').read_text('utf-8'))
            poses=json.loads((ROOT/'art/shared/poses/templates/humanoid'/CLIPS[name][0]/name/'poses.json').read_text('utf-8'))
            frame_index=0;age=0
            for tick,frame in enumerate(move['frames']):
                while frame_index<count-1 and age+ticks[frame_index]<=tick:
                    age+=ticks[frame_index];frame_index+=1
                frame['sprite']=frame_index
                joints=poses['frames'][frame_index]['joints']
                # 身体与四肢的受击框由关节段推出；拳脚攻击框只在攻击 tick 生效。
                hurt=[]
                for chain in [('head','hip'),('shoulder_back','wrist_back'),('shoulder_front','wrist_front'),('hip','ankle_back'),('hip','ankle_front')]:
                    p,q=joints[chain[0]],joints[chain[1]]
                    hurt.append([min(p[0],q[0])-96-6,184-max(p[1],q[1])-4,abs(p[0]-q[0])+12,abs(p[1]-q[1])+12])
                frame['hurtboxes']=hurt
                if frame['hitboxes']:
                    # 最终整帧与姿势条存在偏差时，使用明确的人工拳脚标注，不把收招图当攻击帧。
                    endpoint=annotations[name]['centers'][str(frame_index)]
                    frame['hitboxes']=[[endpoint[0]-96-14,184-endpoint[1]-14,28,28]]
            save('content/fighters/ultraman/moves/'+name+'.json',move)
    save('assets/fighters/ultraman/animations/manifest.json',manifest)
    for fighter in ['ultraman','zetton']:
        path=ROOT/'content/fighters'/fighter/'definition.json'
        data=json.loads(path.read_text('utf-8'));data['presentation']['model']='res://assets/fighters/'+fighter+'/model-native.png'
        data['presentation']['native']=True;data['presentation']['cell']=192 if fighter=='ultraman' else 256
        data['presentation']['anchor_y']=184 if fighter=='ultraman' else 248
        save(path,data)
    save('content/roster/production.json',dict(stage='gate_a_preparation',fighters={
        'ultraman':dict(model='refined_pending_review',actions=production,playable_matrix=False),
        'zetton':dict(model='refined_pending_review',animation='static_phase1_proxy',playable_matrix=False)}))
    print(json.dumps(production,ensure_ascii=False))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['process','install'])
    parser.add_argument('actions',nargs='*')
    parser.add_argument('--take',type=int)
    args=parser.parse_args()
    if args.command=='install':install()
    else:
        for name in args.actions:
            result=process(name,args.take)
            if result['status']=='blocked' and 'reason' in result:
                save('art/fighters/ultraman/stage2/legacy/processed/'+name+'/qa.json',dict(**result,issues=[result['reason']]))
            print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__=='__main__':main()

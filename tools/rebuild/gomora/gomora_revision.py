"""主会话尺寸返工：原图实测、已审指纹与前后证据；不写其他分支。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import argparse
import copy
import csv
import math
from pathlib import Path
Path = _LayoutProjectPath

import numpy as np
from PIL import Image, ImageDraw

from gomora_qa import ROOT, WORK, MODEL, read, save, sha, rel, font

REV = WORK / 'scale-revision'
OUT = ROOT / 'reports/review/2026-10-22/gomora-batch2/scale-revision'
MANIFEST = ROOT / 'assets/fighters/gomora/animations/manifest.json'
GROUND = 'turn walk_back dash_stop light2 light3 launcher spin_heavy crush tackle sweep takeoff land'.split()
AIR = 'air_rise air_apex air_fall vertical_jump flip_forward flip_back vertical_light vertical_heavy diagonal_light diagonal_heavy air_crush dive chase_takeoff chase_light1 chase_light2 chase_end'.split()
PAIRS = [('eye', 'nose_tip'), ('eye', 'ear_root'), ('nose_tip', 'ear_root')]


def baseline():
    path = REV / 'baseline.json'
    if path.exists():
        return read(path)
    m = read(MANIFEST)
    snapshot = dict(manifest=m, head_qa={}, ledger_requests=len(read(WORK/'ledger.json')['requests']),
                    instructions='原图三点距离比中位数先在已审帧校准±5%，后处理不从旧成品缩放',
                    original_git='153691c5', new_requests=0)
    for action in AIR:
        clip = m['clips'][action]
        snapshot['head_qa'][action] = read(ROOT/clip['head_qa'])
        dest = OUT/'before'/action
        dest.mkdir(parents=True, exist_ok=True)
        atlas = Image.open(ROOT/clip['texture'].removeprefix('res://')).convert('RGBA')
        for i, (x,y,w,h) in enumerate(clip['rects']):
            atlas.crop((x,y,x+w,y+h)).save(dest/f'frame-{i}.png')
    save(path, snapshot)
    return snapshot


def approve():
    baseline()
    m = read(MANIFEST)
    plan_path = ROOT/'content/fighters/gomora/production_plan.json'
    plan = read(plan_path)
    records = {}
    for action in GROUND:
        clip = m['clips'][action]
        assert sha(ROOT/clip['texture'].removeprefix('res://')) == clip['atlas_sha256']
        note = '用户逐帧同比例条带目视通过；转身方向记录获确认' if action=='turn' else '用户逐帧同比例条带目视通过'
        if action in ['dash_stop','light3','spin_heavy']:
            note += '；个别剪影面积开平方比>1.06为整尾伸直，用户目视确认正常，显式放行'
        review = dict(user_approved=True, date='2026-10-22', verdict=note,
                      atlas_sha256=clip['atlas_sha256'], authority='本轮用户复核指令')
        clip['motion_review'] = review
        records[action] = copy.deepcopy(review)
        for cell in plan['cells']:
            if cell['action']==action:
                cell.update(completed=True, reviewed=True, review_date='2026-10-22', review_note=note,
                            review_atlas_sha256=clip['atlas_sha256'])
    for action in AIR:
        clip=m['clips'][action]
        clip['motion_review'].update(user_approved=False, verdict='用户否决空中尺寸；待高分辨率原图标尺校准后返工',
                                     rejected_atlas_sha256=clip['atlas_sha256'])
    save(MANIFEST,m)
    save(plan_path,plan)
    save(REV/'ground-approvals.json',records)
    print('已登记地面审批及图集指纹；空中明确标记尺寸退回')


def prepare():
    baseline()
    source=WORK/'batch3/rework/raw-head-points.json'
    data=read(source)
    points={k:copy.deepcopy(v) for k,v in data.items() if k=='model' or k.startswith('cal/')}
    path=REV/'raw-head-points.json'
    if path.exists():
        points=read(path)
    else:
        for row in points.values():
            row['point_provenance']=rel(source)
            row['point_review']='沿用其他分支已核对实测；主会话需独立复核疑点，禁止按合格结果反推'
        save(path,points)
    render_points(list(points), 'calibration-points')
    return points


def render_points(keys, name):
    points=read(REV/'raw-head-points.json')
    dest=OUT/name
    dest.mkdir(parents=True, exist_ok=True)
    maps={}
    for start in range(0,len(keys),12):
        page=Image.new('RGB',(1020,4*326),'#202632')
        d=ImageDraw.Draw(page)
        for j,key in enumerate(keys[start:start+12]):
            row=points[key]
            if not row.get('eye'):continue
            x=j%3*340;y=j//3*326
            e=row['eye'];radius=45/row['native_factor']
            box=[round(e[0]-radius),round(e[1]-radius),round(e[0]+radius),round(e[1]+radius)]
            crop=Image.open(ROOT/row['source']).convert('RGBA').crop(box).resize((300,300),Image.Resampling.NEAREST)
            page.paste(crop,(x+20,y+24),crop)
            d.text((x+4,y+2),key,font=font(15),fill='white')
            display=300/(box[2]-box[0])
            maps[key]=dict(box=box,display=display,x=x+20,y=y+24,page=start//12)
            for field,color,label in [('eye','#ff4c87','E'),('nose_tip','#66ff9d','N'),('ear_root','#57d7fa','R')]:
                if row.get(field) is None:continue
                px=(row[field][0]-box[0])*display+x+20;py=(row[field][1]-box[1])*display+y+24
                d.line((px-4,py,px+4,py),fill=color);d.line((px,py-4,px,py+4),fill=color)
                d.text((px+4,py-16),label,font=font(12),fill=color)
        page.save(dest/f'{start//12:02}.png')
    save(dest/'mapping.json',maps)


def calibrate():
    points=read(REV/'raw-head-points.json')
    ref=points['model']
    refd=[math.dist(ref[a],ref[b])*ref['native_factor'] for a,b in PAIRS]
    rows=[]
    for key,row in points.items():
        if not key.startswith('cal/'):continue
        assert sha(ROOT/row['source'])==row['source_sha256']
        dist=[math.dist(row[a],row[b]) for a,b in PAIRS]
        ratios=[a/b*row['native_factor'] for a,b in zip(dist,refd)]
        error=(float(np.median(ratios))-1)*100
        rows.append(dict(key=key, distances_raw=dist, reference_native=refd, ratios=ratios,
                         deviation_percent=error, usable=abs(error)<=5, source=row['source'],
                         source_sha256=row['source_sha256'],native_factor=row['native_factor'],
                         points={k:row[k] for k in ['eye','nose_tip','ear_root']}))
    # 第二种修法固定使用两条较长的线段，减少最短ER对耳根歧义的敏感性。
    # 不逐帧挑选最接近1的线段，也不改坐标追逐合格范围。
    second=[]
    for row in rows:
        error=(float(np.median([row['ratios'][0],row['ratios'][2]]))-1)*100
        second.append(dict(key=row['key'],deviation_percent=error,usable=abs(error)<=5))
    result=dict(method='GPT原图E眼心、N鼻角尖、R近侧月牙耳角根；EN/ER/NR三段各与定稿相除后取中位数',
                tolerance_percent=5, all_usable=all(r['usable'] for r in rows),frames=rows,
                second_method=dict(method='固定EN、NR两段距离比中位数，剔除最短ER；不逐帧选择',
                                   all_usable=all(r['usable'] for r in second),frames=second),
                hard_gate_active=False,policy='未全通过±5%不得批量改空中比例；不改已审地面帧凑校准')
    save(OUT/'calibration.json',result)
    with (OUT/'calibration.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['已审动作帧','EN比例','ER比例','NR比例','三段中位数偏差%','三段±5%可用','两段偏差%','两段±5%可用','原图','原图SHA256'])
        for r,s in zip(rows,second):w.writerow([r['key'],*r['ratios'],r['deviation_percent'],r['usable'],s['deviation_percent'],s['usable'],r['source'],r['source_sha256']])
    if not result['all_usable'] and not result['second_method']['all_usable']:
        failed=[r['key'] for r in rows if not r['usable']]
        save(REV/'calibration-pause.json',dict(status='blocked',generation_requests=0,
             reason='两种固定测法均未满足所有已审帧±5%；slide/0、1、2连续超差，停止该项批量缩放',
             failed=failed,scope=AIR,original_frames_changed=False,
             reference='AGENTS.md 美术返工教训：同一检查连续拒收3个不同帧暂停该项、出诊断图；同问题最多2种修法'))
        render_points(['model','cal/idle/0','cal/dash/1','cal/heavy/3','cal/slide/0','cal/slide/1','cal/slide/2'], 'calibration-diagnostic')
        from qa_brake import Brake
        brake=Brake(WORK/'brake.json')
        for i in range(3):
            brake.record(f'raw-head-calibration/slide/{i}',{'raw_head_calibration':False},OUT/'calibration-diagnostic/00.png')
    print('原图三段中位数校准', '可用' if result['all_usable'] else '未达逐帧±5%',
          '偏差范围',round(min(r['deviation_percent'] for r in rows),2),round(max(r['deviation_percent'] for r in rows),2))
    return result


def strips():
    """保留当前真实尺寸供诊断；校准阻塞时明确不冒充返工后对照。"""
    m=read(MANIFEST)
    c=m['clips']['idle'];x,y,w,h=c['rects'][0]
    idle=Image.open(ROOT/c['texture'].removeprefix('res://')).convert('RGBA').crop((x,y,x+w,y+h))
    idle_area=int(np.count_nonzero(np.array(idle)[:,:,3]))
    rows=[]
    for action in AIR:
        clip=m['clips'][action]
        atlas=Image.open(ROOT/clip['texture'].removeprefix('res://')).convert('RGBA')
        frames=[atlas.crop((x,y,x+w,y+h)) for x,y,w,h in clip['rects']]
        records=read(ROOT/clip['head_qa'])['frames']
        dest=OUT/'current-diagnostic'/action;dest.mkdir(parents=True,exist_ok=True)
        strip=Image.new('RGB',(512*(len(frames)+1),360),'#202632');d=ImageDraw.Draw(strip)
        for i,im in enumerate([idle]+frames):
            ox=i*512;strip.paste(im,(ox,40),im)
            ratio=math.sqrt(np.count_nonzero(np.array(im)[:,:,3])/idle_area)
            d.line((ox,344,ox+511,344),fill='#718482')
            d.text((ox+5,5),'待机基准' if i==0 else f'{action} #{i-1} 剪影比{ratio:.3f} 待尺寸返工',font=font(17),fill='white')
            if i:rows.append(dict(action=action,frame=i-1,silhouette_sqrt_ratio=ratio,review='用户否决；校准阻塞未改图',atlas_sha256=clip['atlas_sha256']))
        strip.save(dest/'with-idle-native.png')
        strip.resize((strip.width*4,strip.height*4),Image.Resampling.NEAREST).save(dest/'with-idle-x4.png')
        strip.thumbnail((1024,1024),Image.Resampling.NEAREST);strip.save(dest/'inspection-1024.png')
        headstrip=Image.new('RGB',(1024*len(frames),1060),'#202632');hd=ImageDraw.Draw(headstrip)
        for i,(im,record) in enumerate(zip(frames,records)):
            hint=record.get('measurement') or record.get('raw_head')
            if not hint:continue
            cx,cy=hint['eye'];box=[round(cx)-64,round(cy)-64,round(cx)+64,round(cy)+64]
            crop=im.crop(box).resize((1024,1024),Image.Resampling.NEAREST);headstrip.paste(crop,(i*1024,36),crop)
            hd.text((i*1024+6,4),f'{action} #{i} 当前头部8倍（定位只用于裁图，不定比例）',font=font(20),fill='white')
        headstrip.save(dest/'heads-x8.png')
        headstrip.thumbnail((1024,1024),Image.Resampling.NEAREST);headstrip.save(dest/'heads-inspection-1024.png')
        if action in ['flip_forward','flip_back']:
            imgs=[]
            for im in frames:
                bg=Image.new('RGB',(512,320),'#202632');bg.paste(im,(0,0),im);imgs.append(bg)
            imgs[0].save(dest/'quarter-speed.gif',save_all=True,append_images=imgs[1:],duration=[round(t*4000/60) for t in clip['ticks']],loop=0,disposal=2)
    save(OUT/'current-silhouettes.json',dict(status='校准未通过，仅当前问题诊断，不是已修复的前后对照',frames=rows))
    print('已保存当前空中动作待机同行诊断条带；没有伪造返工后结果')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['approve','prepare','calibrate','strips'])
    args=parser.parse_args()
    {'approve':approve,'prepare':prepare,'calibrate':calibrate,'strips':strips}[args.command]()

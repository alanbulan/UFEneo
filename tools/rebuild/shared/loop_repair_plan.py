"""初代/杰顿循环回修：不可变开工快照、最少补帧求解及姿势引导。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import argparse,copy,hashlib,itertools,math,shutil
import numpy as np
from PIL import Image,ImageDraw
from head_scale import ROOT,read,save,sha,font
from loop_repair_audit import clips,WORK,OUT
import loop_qa

RUN=WORK/'repair-v1'
REPORT=OUT/'repair-v1'
FIGHTERS=['ultraman','zetton']


def rel(p):return Path(p).relative_to(ROOT).as_posix()


def snapshot():
    RUN.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
    if (RUN/'before.json').exists():return read(RUN/'before.json')
    result={}
    for fighter in FIGHTERS:
        mp=ROOT/f'assets/fighters/{fighter}/animations/manifest.json'
        sp=ROOT/f'content/fighters/{fighter}/state_frames.json'
        dest=RUN/'before'/fighter;dest.mkdir(parents=True,exist_ok=True)
        shutil.copy2(mp,dest/'manifest.json');shutil.copy2(sp,dest/'state_frames.json')
        rows={}
        for action,c,images,heads in clips(fighter):
            folder=dest/action;folder.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/c['texture'].removeprefix('res://'),folder/'atlas.png')
            shutil.copy2(ROOT/c['head_qa'],folder/'head-qa-original.json')
            for i,im in enumerate(images):im.save(folder/f'frame-{i:02}.png')
            rows[action]=dict(clip=c,heads=heads,centers=loop_qa.measure(images,fighter,heads,action)['centers'],frame_sha256=[hashlib.sha256(im.tobytes()).hexdigest() for im in images])
        result[fighter]=dict(manifest_sha256=sha(mp),state_sha256=sha(sp),actions=rows)
    save(RUN/'before.json',result)
    approvals=[]
    for fighter,action,reason in [('ultraman','idle','水平漂移4.0px，仅比3px多1px；用户本轮人工复核放行，不改正式帧'),('zetton','crouch','水平漂移3.826px，超限不足1px；用户本轮人工复核放行，不改正式帧')]:
        r=result[fighter]['actions'][action]
        approvals.append(dict(fighter=fighter,action=action,date='2026-10-22',reason=reason,frame_sha256=r['frame_sha256'],scope='仅本组已审像素；新生成帧不得继承'))
    save(WORK/'manual-approvals.json',dict(approvals=approvals))
    ledger=read(WORK/'ledger.json');ledger.update(scope='用户2026-10-22授权：初代和杰顿循环回修；总次数不限，每个固定帧最多10次',per_frame_limit=10,total_limit=None)
    save(WORK/'ledger.json',ledger)
    brake=read(WORK/'brake.json');brake.update(generation_enabled=True,reason='最新用户已授权本分支修复循环；每帧最多10次',checks=brake.get('checks',{}))
    save(WORK/'brake.json',brake)
    return result


def feasible(y,selected,span,adjacent):
    fixed=[i for i in range(len(y)) if i not in selected];n=len(y)
    return all(abs(y[i]-y[j])<=min(span,adjacent*min((i-j)%n,(j-i)%n))+1e-7 for i in fixed for j in fixed)


def targets(y,selected,span,adjacent):
    n=len(y);fixed=[i for i in range(n) if i not in selected]
    if not fixed:return [float(np.median(y))]*n
    lo=max(y[i] for i in fixed)-span;hi=min(y[i] for i in fixed)+span
    ranges=[]
    for i in range(n):
        lower=max([lo]+[y[j]-adjacent*min((i-j)%n,(j-i)%n) for j in fixed]);upper=min([hi]+[y[j]+adjacent*min((i-j)%n,(j-i)%n) for j in fixed])
        ranges.append([lower,upper])
    # 固定点间最短环段线性插值；区间交集的截断保持Lipschitz约束。
    result=list(map(float,y))
    for i in selected:
        left=next((i-k)%n for k in range(1,n+1) if (i-k)%n in fixed);right=next((i+k)%n for k in range(1,n+1) if (i+k)%n in fixed)
        dl=(i-left)%n;dr=(right-i)%n
        value=(y[left]*dr+y[right]*dl)/(dl+dr)
        result[i]=max(ranges[i][0],min(ranges[i][1],value))
    if max(result)-min(result)>span:
        low=max(min(result),max(result)-span);high=low+span
        result=[max(low,min(high,v)) if i in selected else v for i,v in enumerate(result)]
    assert max(result)-min(result)<=span+1e-6 and max(abs(result[i]-result[(i+1)%n]) for i in range(n))<=adjacent+1e-6,(y,selected,result)
    return result


def minimal(y,span,adjacent,required=()):
    n=len(y)
    for count in range(len(required),n+1):
        solutions=[]
        for chosen in itertools.combinations(range(n),count):
            if not set(required).issubset(chosen) or not feasible(y,chosen,span,adjacent):continue
            t=targets(y,chosen,span,adjacent)
            # 变更最少优先；再最小化所需最大/平方位移。
            score=(max(abs(t[i]-y[i]) for i in chosen) if chosen else 0,sum((t[i]-y[i])**2 for i in chosen))
            solutions.append((score,list(chosen),t))
        if solutions:
            solutions.sort(key=lambda x:x[0]);return dict(minimum_frames=count,frames=solutions[0][1],target_y=solutions[0][2],all_minimum_subsets=[x[1] for x in solutions])


def reorder(y,span,adjacent):
    if max(y)-min(y)>span+1e-6:return None
    for rest in itertools.permutations(range(1,len(y))):
        p=[0,*rest]
        if all(abs(y[p[i]]-y[p[(i+1)%len(p)]])<=adjacent+1e-6 for i in range(len(p))):return p
    return None


def plan():
    data=snapshot();result={}
    for fighter in FIGHTERS:
        for action in ['walk_forward','walk_back','stun','charge','idle']:
            if fighter=='ultraman' and action=='idle':continue
            row=data[fighter]['actions'][action];xy=np.array(row['centers']);y=xy[:,1].tolist();rule=loop_qa.limits(action)
            r=minimal(y,rule['vertical'],rule['adjacent'],[1,2,5] if fighter=='ultraman' and action=='stun' else [])
            r.update(fighter=fighter,action=action,before_centers=xy.tolist(),original_ticks=row['clip']['ticks'],reorder_only=reorder(y,rule['vertical'],rule['adjacent']))
            if fighter=='zetton' and action=='charge':r.update(frames=list(range(4)),target_y=[125,126,126,125],minimum_frames=4,method='用户指定固定胯/脚骨架整条重做')
            if fighter=='ultraman' and action=='stun':r['target_y']=[63.5,64.5,65.5,66.5,65,64]
            if fighter=='zetton' and action=='idle':
                # 重排无法改变总幅。第0帧还是唯一超水平边界的保留点，需同时补它。
                r.update(minimum_frames=3,frames=[0,2,4],target_y=[123,124.2549,125,124.6053,123,122.3365],target_x=[131,131.2255,131,129.7895,131,129.2788],method='先枚举帧序，无可行解；补0/2/4同时满足水平≤3')
            if fighter=='ultraman' and action=='walk_back':
                r.update(status='单帧约束不可行，等待用户决定',incompatible_edges=[dict(edge=[i,(i+1)%len(y)],delta=abs(y[i]-y[(i+1)%len(y)])) for i in range(len(y)) if abs(y[i]-y[(i+1)%len(y)])>4],single_frame_impossible=True)
            result[f'{fighter}/{action}']=r
    save(RUN/'plan.json',result)
    lines=['# 循环回修最少补帧计划','','帧号从0开始；保留正式脚位、速度、时长。只改用户指定循环。所有总幅和相邻差包含接头。','','|角色/动作|最少补帧|目标眼高 y|仅重排能否解决|','|---|---|---|---|']
    for key,r in result.items():lines.append(f'|{key}|{r["frames"]}|{[round(v,3) for v in r["target_y"]]}|{r["reorder_only"]}|')
    lines+=['','初代后走：7→0为5.5px，0→1为4.5px，4→5为5px。前两边只能同时改第0帧消除；4→5还必须改第4或5帧。数学上最少2帧，无法按“只补1帧”同时达成相邻≤4。此动作先保留正式版本，其余照常推进。','']
    (REPORT/'plan.md').write_text('\n'.join(lines),'utf-8')
    print({k:dict(frames=r['frames'],target_y=r['target_y'],reorder=r['reorder_only']) for k,r in result.items()})


def old_frame(fighter,action,index):return Image.open(RUN/'before'/fighter/action/f'frame-{index:02}.png').convert('RGBA')


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['snapshot','plan']);a=p.parse_args();globals()[a.command]()


if __name__=='__main__':main()

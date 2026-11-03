"""只读检测同材质、没有轮廓隔开的直线明暗断层；不提供区域换色。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import json,sys; json = _LayoutJson
from functools import lru_cache
import numpy as np
import cv2
from PIL import Image
from head_scale import ROOT,read,save,sha


@lru_cache(maxsize=None)
def materials(fighter):
    palette=read(ROOT/f'content/fighters/{fighter}/palette.json');roles=palette['side_view_roles']
    near,far=roles['near_side'],roles['far_side']
    if fighter in ['ultraseven','ultraman']:
        # 包括原图的中间明度，避免只认识四个锚色而漏掉185红/212银旁的矩形边。
        colors=palette['colors'];silver=[c for c in colors if max(c)-min(c)<48 and sum(c)/3>100];red=[c for c in colors if c[0]>65 and c[0]>c[1]*2 and c[0]>c[2]*1.6]
        threshold=160 if fighter=='ultraseven' else 210
        return [('silver',[c for c in silver if sum(c)/3>=(155 if fighter=='ultraseven' else 184)],[c for c in silver if sum(c)/3<(155 if fighter=='ultraseven' else 184)]),('red',[c for c in red if c[0]>=threshold],[c for c in red if c[0]<threshold])]
    return [(k,near[k],far[k]) for k in ['limb_rgb','hand_foot_rgb']]


def isin(a,colors):
    return np.logical_or.reduce([(a[:,:,:3]==c).all(2) for c in colors])&(a[:,:,3]>0)


def boundaries(im,fighter,before=None):
    a=np.array(im);result=[]
    for name,near,far in materials(fighter):
        n=isin(a,near);f=isin(a,far)
        original_edges=None
        if before is not None:
            b=np.array(before);bn=isin(b,near);bf=isin(b,far)
            changed=np.any(a!=b,axis=2)
            original_edges=[bn[:-1]&bf[1:]|bf[:-1]&bn[1:],bn[:,:-1]&bf[:,1:]|bf[:,:-1]&bn[:,1:]]
        # 杰顿的黑色手脚与全身深轮廓共色，属于用户指定的深轮廓例外。
        if max(np.mean(c) for c in far)<64:continue
        # 边界两边必须直接接触且属于同一种材质。中间有轮廓像素即不会形成候选。
        for axis in [0,1]:
            edges=(n[:-1]&f[1:]|f[:-1]&n[1:]) if axis==0 else (n[:,:-1]&f[:,1:]|f[:,:-1]&n[:,1:])
            if before is not None:
                affected=(changed[:-1]|changed[1:]) if axis==0 else (changed[:,:-1]|changed[:,1:])
                edges=edges&affected&~original_edges[axis]
            for fixed,line in enumerate(edges if axis==0 else edges.T):
                positions=np.flatnonzero(np.diff(np.r_[False,line,False].astype('int8')))
                for start,end in zip(positions[::2],positions[1::2]):
                    if end-start<4:continue
                    record=dict(material=name,orientation='horizontal' if axis==0 else 'vertical',start=[int(start),fixed] if axis==0 else [fixed,int(start)],length=int(end-start))
                    if before is not None:
                        original=original_edges[axis]
                        oldline=original[fixed] if axis==0 else original[:,fixed]
                        record['introduced_by_postprocess']=not bool(oldline[start:end].all())
                    result.append(record)
    return result


def validate(images,fighter,baselines=None):
    """基线是调色前的原生像素；原图固有明暗单列，不能冒充新增压暗遮罩。

    未提供基线时无法判断来源，必须补原生量化基线。GPT原生明暗不受此门拦截。
    """
    if baselines is None or len(images)!=len(baselines):raise ValueError('逐帧GPT量化基线缺失')
    rows=[dict(frame=i,boundaries=boundaries(im,fighter,baselines[i] if baselines is not None else None)) for i,im in enumerate(images)]
    issues=[f'frame {r["frame"]}: 未沿深轮廓的直线明暗分界' for r in rows if any(b.get('introduced_by_postprocess',True) for b in r['boundaries'])]
    if issues:raise ValueError('; '.join(issues))
    return rows


def validate_folder(folder,fighter,action):
    """只查量化原生基线之后新增的直边；GPT原生纹理不作硬拦截。"""
    folder=Path(folder);q=read(folder/'head-qa.json');images=[Image.open(folder/r['image']).convert('RGBA') for r in q['frames']];baselines=None
    record=folder/'limb-color-baseline.json'
    if record.exists():
        before=read(record)
        if before.get('source') and sha(ROOT/before['source'])!=before['source_sha256']:raise ValueError('调色基线原图指纹变化')
        if len(before['frames'])!=len(images):raise ValueError('调色前逐帧基线数量变化')
        baselines=[]
        for r in before['frames']:
            p=folder/r['image']
            if sha(p)!=r['sha256']:raise ValueError('调色前基线已被覆盖')
            baselines.append(Image.open(p).convert('RGBA'))
        # 基线由原图确定性处理入口冻结并核对指纹，不是事后补的颜色标签。
    result=validate(images,fighter,baselines)
    if action=='idle':
        import idle_qa
        motion=idle_qa.measure(images,fighter,q['frames'])
        save(folder/'idle-qa.json',motion)
        if motion['issues']:raise ValueError('; '.join(motion['issues']))
    save(folder/'limb-color-qa.json',dict(frames=result,issues=[]))
    return result


def freeze_raw_baseline(folder,images,source):
    """只由原图后处理入口调用，发生在任何远侧调色之前；保留可追溯原图指纹。"""
    digest=sha(source);records=[]
    for i,im in enumerate(images):
        p=folder/f'color-source-{digest[:12]}-{i}.png'
        if p.exists() and Image.open(p).convert('RGBA').tobytes()!=im.tobytes():
            # 同原图不同缩放也不能覆盖旧基线。
            import hashlib
            p=folder/f'color-source-{digest[:12]}-{i}-{hashlib.sha256(im.tobytes()).hexdigest()[:10]}.png'
        if not p.exists():im.save(p)
        records.append(dict(image=p.name,sha256=sha(p)))
    save(folder/'limb-color-baseline.json',dict(source=source.relative_to(ROOT).as_posix(),source_sha256=digest,frames=records,stage='原图网格/色板处理后，任何远侧调色前'))


def scan(output):
    report=dict(rule='同材质近远色直接相邻且连续横/竖线≥4px；深轮廓隔开的边界不报错',fighters={})
    for fighter in ['ultraman','zetton','ultraseven']:
        m=read(ROOT/f'assets/fighters/{fighter}/animations/manifest.json');rows=[];cache={}
        for action,clip in m['clips'].items():
            p=ROOT/clip['texture'].removeprefix('res://');atlas=cache.setdefault(str(p),Image.open(p).convert('RGBA'))
            for i,(x,y,w,h) in enumerate(clip['rects']):
                im=atlas.crop((x,y,x+w,y+h));found=boundaries(im,fighter)
                rows.append(dict(action=action,frame=i,texture=clip['texture'],rect=[x,y,w,h],sha256=sha(p),boundaries=found))
        report['fighters'][fighter]=dict(frames=len(rows),hit_frames=sum(bool(r['boundaries']) for r in rows),rows=rows)
    save(Path(output),report)
    print({f:(v['frames'],v['hit_frames']) for f,v in report['fighters'].items()})
    return report


if __name__=='__main__':scan(ROOT/'reports/review/2026-10-22-seven-repairs/limb-scan-before.json')

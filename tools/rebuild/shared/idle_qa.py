"""待机特征轨迹检查；首尾作为相邻帧，绝不以外框高度代替头部。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import numpy as np,cv2
from PIL import Image
from head_scale import ROOT,read,save


def feature(im,fighter,row):
    from form_loop_feature import configuration, feature as form_feature, hint
    form=configuration(fighter)
    if form is not None:return form_feature(im,fighter,row,form)
    if fighter=='eleking':
        from eleking_loop_feature import feature as eleking_feature
        return eleking_feature(im,row)
    if fighter=='black_king':
        from blackking_loop_feature import feature as blackking_feature
        return blackking_feature(im,row)
    if fighter=='gomora':
        # 哥莫拉浅褐鳞甲不能混入金黄色眼睛；其他角色继续原有特征路径。
        from gomora_qa import eye
        measured=eye(im)
        if not measured:raise ValueError('哥莫拉黄色眼睛不可测量')
        return measured['center']
    a=np.array(im);r,g,b=a[:,:,:3].astype(int).transpose(2,0,1);yy,xx=np.indices(a.shape[:2])
    if row.get('hint') is not None:cx,cy=row['hint']
    else:
        from pathlib import Path
        import json
        path=Path(str(ROOT))/f'art/fighters/{fighter}/model/head-fit/{fighter}.json'
        cfg=json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}
        cx,cy=hint(row,cfg)
    region=(abs(xx-cx)<24)&(abs(yy-cy)<24)&(a[:,:,3]>0)
    color=(r>150)&(g>60)&(b<110)&(r>g*1.05) if fighter=='zetton' else (r>90)&(g>50)&(b<110)&(r>g*1.15)&(g>b*1.4) if fighter=='ultraman' else (r>150)&(g>115)&(r-b>35)&(g-b>25)
    mask=region&color
    n,labels,stats,centers=cv2.connectedComponentsWithStats(mask.astype('uint8'),8)
    ids=[i for i in range(1,n) if stats[i,4]>=2]
    if not ids:raise ValueError('头部特征不可测量')
    i=min(ids,key=lambda i:abs(centers[i,1]-cy)+abs(centers[i,0]-cx)*.3)
    return list(map(float,centers[i]))


def measure(images,fighter,rows):
    centers=[feature(im,fighter,row) for im,row in zip(images,rows)];x,y=np.array(centers).T
    dy=np.abs(np.roll(y,-1)-y);issues=[]
    if np.ptp(y)>4:issues.append('头部垂直总幅度超过4px')
    if max(dy)>2:issues.append('相邻帧含首尾垂直变化超过2px')
    if np.ptp(x)>2:issues.append('头部水平总漂移超过2px')
    # 一次下沉、一次回升（平台忽略），不能锯齿往复。
    signs=[int(np.sign(v)) for v in np.diff(np.r_[y,y[0]]) if abs(v)>.25]
    changes=sum(a!=b for a,b in zip(signs,signs[1:]+signs[:1])) if signs else 0
    if changes>2:issues.append('呼吸曲线多次反向，不是平滑单周期')
    return dict(fighter=fighter,feature='脸部发光体' if fighter=='zetton' else '眼睛',centers=centers,vertical_range=float(np.ptp(y)),horizontal_range=float(np.ptp(x)),adjacent_y=dy.tolist(),issues=issues)


def installed():
    result=[]
    for fighter in ['ultraman','zetton','ultraseven']:
        c=read(ROOT/f'assets/fighters/{fighter}/animations/manifest.json')['clips']['idle'];atlas=Image.open(ROOT/c['texture'].removeprefix('res://')).convert('RGBA');hq=read(ROOT/c['head_qa']);images=[atlas.crop((x,y,x+w,y+h)) for x,y,w,h in c['rects']]
        result.append(measure(images,fighter,hq['frames']))
    save(ROOT/'reports/review/2026-10-22-seven-repairs/idle-audit.json',result);print(result)
    return result


if __name__=='__main__':installed()

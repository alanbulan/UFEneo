"""赛文定稿5头镖剪影门；只测量，不修补/替换人物像素。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import json,math; json = _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import cv2,numpy as np
from PIL import Image
from head_scale import ROOT,read,save,sha
import head_size

MODEL=ROOT/'art/fighters/ultraseven/model/model-native.png'
CONFIG=ROOT/'content/fighters/ultraseven/slugger_qa.json'

def lamp(im):
    a=np.array(im);r,g,b=a[:,:,:3].astype(int).transpose(2,0,1)
    y,x=np.where((a[:,:,3]>0)&(g>r*1.3)&(g>b*1.1)&(g>80))
    return np.array([x.mean(),y.mean()]) if len(x) else None

def aligned(im,measurement,mirrored=False):
    if mirrored:
        im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        measurement=dict(measurement,hint=[im.width-1-measurement['hint'][0],measurement['hint'][1]]) if measurement.get('hint') else measurement
    model=Image.open(MODEL).convert('RGBA');ref=head_size.head(model,'ultraseven',method='eye-ear-v2');source=head_size.head(im,'ultraseven',measurement.get('hint'),method='eye-ear-v2')
    if not source:raise ValueError('头盔不可测，不能绕过头镖检查')
    s=ref['length']/source['length'];origin=lamp(im);target=lamp(model)
    if origin is None and measurement.get('alignment_origin') is not None:
        origin=np.array(measurement['alignment_origin'],dtype=float)
    if origin is None:raise ValueError('额灯被遮挡/背向：必须明确登记可见区域与头部定位，不得自动当通过')
    angle=source.get('angle_degrees',0)
    transform=cv2.getRotationMatrix2D(tuple(origin),angle,s)
    transform[:,2]+=target-origin
    return cv2.warpAffine(np.array(im),transform,(192,192),flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)

def compare(im,row=None,detached=False):
    config=read(CONFIG);row=row or {};a=aligned(im,row,row.get('facing')=='left');base=np.array(Image.open(MODEL).convert('RGBA'));yy,xx=np.indices(a.shape[:2])
    # 头顶上方 + 后脑外侧尾部；不把大面积脸/躯干算进分数，避免错误头镖被脸部掩盖。
    domain=((xx>=76)&(xx<=110)&(yy>=30)&(yy<=54))|((xx>=76)&(xx<=88)&(yy>=55)&(yy<=76))
    expected=(base[:,:,3]>0)&domain;actual=(a[:,:,3]>0)&domain
    # 红色手臂遮挡只检查露出部分；遮挡掩码和比例一并保存。
    r,g,b=a[:,:,:3].astype(int).transpose(2,0,1);occluded=(a[:,:,3]>0)&(r>g*1.7)&(r>b*1.5)&(r>70)
    occluded=cv2.dilate(occluded.astype('uint8'),np.ones((3,3),np.uint8))>0
    if row.get('occlusion_polygon'):
        from PIL import ImageDraw
        mask=Image.new('1',(192,192));ImageDraw.Draw(mask).polygon([tuple(p) for p in row['occlusion_polygon']],fill=1);occluded|=np.array(mask)
    visible=domain&~occluded;expected&=visible;actual&=visible
    if detached:
        # 先切开红色持镖手臂，只检测头盔连通域；离头的银色武器不属于头冠。
        mask=((a[:,:,3]>0)&~occluded).astype('uint8');_,labels=cv2.connectedComponents(mask,8)
        head_label=int(labels[66,100])
        if not head_label:
            choices=labels[60:74,95:107];vals,counts=np.unique(choices[choices>0],return_counts=True);head_label=int(vals[counts.argmax()]) if len(vals) else 0
        helmet=(labels==head_label) if head_label else np.zeros_like(visible)
        # 定稿露出的头骨顶约y47，低棱可高2px；不能把正常头骨当残留头镖。
        upper=visible&(yy<config['detached_upper_y']);rear=visible&(xx<84)&(yy>=55)&(yy<76)
        excess=int((helmet&upper).sum());tail=int((helmet&rear).sum());ok=bool(head_label and excess<=config['detached_max_upper_pixels'] and tail<=8 and visible.sum()/domain.sum()>=.15)
        return dict(mode='detached_low_ridge',upper_pixels=excess,rear_tail_pixels=tail,pass_=ok,visible_fraction=float(visible.sum()/domain.sum()))
    # 额灯只有几像素，中心量化允许±1原生像素登记误差；不改变轮廓、阈值或成品。
    best=None
    for dy in [-1,0,1]:
        for dx in [-1,0,1]:
            alpha=np.roll(a[:,:,3]>0,(dy,dx),(0,1));hidden=np.roll(occluded,(dy,dx),(0,1))
            expose=domain&~hidden;e=(base[:,:,3]>0)&expose;v=alpha&expose
            score=int((e&v).sum())/max(1,int((e|v).sum()))
            if best is None or score>best[0]:best=(score,dx,dy,e,v,hidden)
    iou,dx,dy,expected,actual,occluded=best
    visible_fraction=float((domain&~occluded).sum()/domain.sum())
    return dict(mode='attached',iou=round(iou,5),alignment_shift=[dx,dy],threshold=config['minimum_iou'],expected_pixels=int(expected.sum()),actual_pixels=int(actual.sum()),occluded_pixels=int((domain&occluded).sum()),visible_fraction=round(visible_fraction,4),minimum_visible_fraction=.15,pass_=iou>=config['minimum_iou'] and visible_fraction>=.15)

def calibrate():
    # 阈值由定稿自身的±1px登记噪声与两种已否决轮廓分离，不按新候选降低。
    save(CONFIG,dict(model_sha256=sha(MODEL),minimum_iou=.75,hard_rejection=False,detached_max_upper_pixels=8,detached_upper_y=45,alignment='按实测眼睛/护耳倾角旋转归一，再按额灯登记及固定头盔比例对齐；±1px量化登记；仅测量不改成品',domain='头顶30..54及后脑76..88/55..76，排除脸和躯干',occlusion='红色手臂自动遮挡，额外遮挡必须显式标注；只计可见部分',threshold_basis='旋转归一后旧平冠0.71074、旧勾鳍0.55149、定稿1.0；0.75只触发8倍条带人工复核，不拦安装'))
    tests=[]
    for label,path in [('approved',MODEL),('rejected_flat',ROOT/'art/fighters/ultraseven/stage4/revisions/crown-counter-revision/before.png'),('rejected_hook',ROOT/'art/fighters/ultraseven/stage4/revisions/ultraseven-head-edit/before.png')]:
        result=compare(Image.open(path).convert('RGBA'));tests.append(dict(label=label,**result))
    assert tests[0]['pass_'] and all(not r['pass_'] for r in tests[1:]),tests
    save(CONFIG.with_name('slugger_qa-self-test.json'),tests);print(tests)

def validate(folder):
    folder=Path(folder);q=read(folder/'head-qa.json');result=[];fail=[]
    for row in q['frames']:
        if row.get('crown_view')=='back_crouched':
            if not row.get('occluded') or not row.get('manual_crown_reason'):raise ValueError('背面蹲姿必须登记前后比例插值及人工头冠复核原因')
            result.append(dict(frame=row['frame'],mode='back_crouched_manual_review',pass_=None,review_required=True,reason=row['manual_crown_reason']));continue
        if row.get('crown_view')=='back':
            im=Image.open(folder/row['image']).convert('RGBA')
            if lamp(im) is not None or row.get('size_policy')!='standing_height' or not row.get('manual_crown_reason'):raise ValueError('背面人工检查例外必须无额灯、用站高测量且说明原因')
            result.append(dict(frame=row['frame'],mode='back_manual_review',pass_=None,review_required=True,reason=row['manual_crown_reason']));continue
        try:r=compare(Image.open(folder/row['image']).convert('RGBA'),row,bool(row.get('slugger_detached')))
        except ValueError as exc:r=dict(pass_=False,reason=str(exc),mode='unmeasurable')
        r.update(frame=row['frame'],review_required=not r['pass_'],disposition='需人工复核' if not r['pass_'] else '模板比对通过');result.append(r)
        if not r['pass_']:fail.append('frame '+str(row['frame'])+'头镖剪影不符')
    save(folder/'slugger-qa.json',dict(model_sha256=sha(MODEL),frames=result,issues=fail))
    return result

if __name__=='__main__':calibrate()

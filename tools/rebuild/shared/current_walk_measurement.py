"""每次按当前正式图集重测；旧指纹仅留作审计，不作为拒收条件。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from PIL import Image
from head_scale import ROOT,read,sha
from check.limb_idle import frame_row
from loop_repair_generate import old_foot_boxes,measured_feet
import loop_qa
from walk_rhythm import deviations

def refresh(previous):
    fighter,action=previous['fighter'],previous['action']
    clip=read(ROOT/f'assets/fighters/{fighter}/animations/manifest.json')['clips'][action]
    path=ROOT/clip['texture'].removeprefix('res://')
    current_sha=sha(path)
    changed=current_sha!=previous['atlas_sha256'] or list(clip['ticks'])!=previous.get('ticks',clip['ticks'])
    atlas=Image.open(path).convert('RGBA')
    images=[atlas.crop((x,y,x+w,y+h)) for x,y,w,h in clip['rects']]
    hq=read(ROOT/clip['head_qa'])
    heads=[frame_row(hq['frames'],clip,i) for i in range(len(images))]
    # 眼睛从当前像素测，不复制历史测量值；脚ROI只限定近/远脚身份，质心重测。
    feet=[measured_feet(im,fighter,old_foot_boxes(fighter,action,i)) for i,im in enumerate(images)]
    measured=loop_qa.measure(images,fighter,heads,action)
    stance=deviations(feet,clip['ticks'],1 if action=='walk_forward' else -1)
    maximum=max(abs(v['deviation']) for v in stance)
    ticks=clip['ticks'];average=sum(ticks)/len(ticks);issues=list(measured['issues'])
    if maximum>8:issues.append('撑地世界坐标偏差>±8px')
    if min(ticks)<average*.6 or max(ticks)>average*1.5:issues.append('帧时长超出均值0.6–1.5倍')
    result=dict(eyes=measured['centers'],eye_range=measured['vertical_range'],
        adjacent_eye_y=measured['adjacent_y'],ticks=ticks,stance=stance,max_foot_deviation=maximum,issues=issues)
    return dict(previous,atlas=path.relative_to(ROOT).as_posix(),atlas_sha256=current_sha,
        previous_atlas_sha256=previous['atlas_sha256'],measurement_refreshed=True,atlas_or_timing_changed=changed,
        measurement_source='当前正式图集逐帧像素：眼睛与脚部质心；未修改任何角色资源',**result)

"""检查本轮旧动作校准候选，未解决的超差必须令verify失败，不能假报整批完成。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import sys
from pathlib import Path
Path = _LayoutProjectPath
from collections import defaultdict
from PIL import Image
ROOT=_LayoutProjectPath(_layout_root)
sys.path.insert(0,str(ROOT/'tools/rebuild'))
from head_scale import read,sha,measure,WORK
import head_size

def main():
 q=read(WORK/'audit.json');rows=q['rows'];seen=set();scales={};blocked=[]
 finish=ROOT/'art/shared/production/head-scale-finish/audit.json'
 if finish.exists():
  overrides={(r['fighter'],r['action'],r['frame']):r for r in read(finish)['rows']}
  rows=[overrides.get((r['fighter'],r['action'],r['frame']),r) for r in rows]
 for r in rows:
  key=(r['fighter'],r['action'],r['frame']);assert key not in seen;seen.add(key)
  raw=ROOT/r['raw'];assert raw.is_file() and sha(raw)==r.get('source_sha256',sha(raw)),key
  if not r.get('output') or (not r.get('new_head') and not r.get('occluded')):blocked.append(key);continue
  image=ROOT/r['output'];assert image.is_file() and sha(image)==r['image_sha256'],key
  group=(r['fighter'],r['raw'])
  if r.get('scale_policy')!='per_frame_head':
   assert group not in scales or abs(scales[group]-r['shared_scale'])<1e-10,group
   scales[group]=r['shared_scale']
  if r.get('occluded') or r.get('auxiliary'):continue # 下面validate核对插值依据或真实辅助部位，不冒充可测头部。
  im=Image.open(image).convert('RGBA');m=measure(im,r['fighter'],r['new_head']['center'],region=r.get('head_region'));baseline=q['baseline'][r['fighter']]['length']
  if m is None or abs(m['length']/baseline-1)>.08 or r['status']=='blocked':blocked.append(key)
 assert not q['missing_raw'],'仍缺原图，不能宣称全部追溯'
 for fighter in ['ultraman','zetton','ultraseven']:
  path=ROOT/f'assets/fighters/{fighter}/animations/manifest.json'
  if not path.exists():continue
  for action,clip in read(path)['clips'].items():
   if not clip.get('head_qa'):continue # 本轮保留旧版的阻塞动作在上面的全量审计中报错。
   folder=(ROOT/clip['head_qa']).parent;hq=head_size.validate(folder,fighter)
   if fighter=='ultraseven':
    import slugger_qa
    assert clip.get('slugger_qa'),'赛文正式动作缺少头镖质检'
    slugger_qa.validate(folder)
   atlas=Image.open(ROOT/clip['texture'].removeprefix('res://')).convert('RGBA')
   indices=list(range(len(clip['rects']))) if len(hq['frames'])==len(clip['rects']) else clip['sequence_frames']
   for rect,index in zip(clip['rects'],indices):
    x,y,w,h=rect;actual=atlas.crop((x,y,x+w,y+h));expected=Image.open(folder/hq['frames'][index]['image']).convert('RGBA')
    assert actual.size==expected.size and actual.tobytes()==expected.tobytes(),(fighter,action,'正式图集与质检整帧不一致')
    if fighter=='ultraseven':
     assert set(actual.getchannel('A').getdata())=={0,255},(action,index,'必须是真透明二值Alpha')
     assert len(set(p[:3] for p in actual.getdata() if p[3]))<=32,(action,index,'超出32色')
     left,top,right,bottom=actual.getbbox();assert left>0 and top>0 and right<w and bottom<h,(action,index,'轮廓触到画布边界')
 installation=WORK/'installation.json'
 resolved=ROOT/'art/shared/production/head-scale-finish/grip-audit.json'
 if installation.exists() and read(installation).get('integration_blocks') and not (resolved.exists() and read(resolved).get('pass')):
  print('HEAD_SIZE INTEGRATION BLOCKED：被抓起姿势与地面/抓点配合仍需处理。')
  blocked.extend((r['fighter'],r['action'],'integration') for r in read(installation)['integration_blocks'])
 if blocked:
  print('HEAD_SIZE BLOCKED：旧动作仍有头部超差、遮挡或测量区域待人工核对。')
  print('完整逐帧清单：reports/review/2026-10-22-head-scale/head-size-by-frame.csv')
  print('示例：'+', '.join(f'{f}/{a}#{i}' for f,a,i in blocked[:12]))
  raise SystemExit(1)
 print('HEAD_SIZE PASS：全部候选的同源比例、头部尺度与资源指纹一致；仍需视觉审片。')
if __name__=='__main__':main()

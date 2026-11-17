"""逐个实际rect扫描正式人物图集，不把图集中的相邻人物当同一主体。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import sys,json; json = _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
sys.path.insert(0,str(Path(__file__).resolve().parent/'rebuild'))
from head_scale import ROOT,read,save
from PIL import Image
import island_qa

def scan():
 rows=[];seen=set()
 for mp in sorted((ROOT/'assets/fighters').glob('*/animations/manifest.json')):
  for action,clip in read(mp)['clips'].items():
   texture=ROOT/clip['texture'].removeprefix('res://');atlas=Image.open(texture).convert('RGBA')
   for i,(x,y,w,h) in enumerate(clip['rects']):
    key=(str(texture),x,y,w,h)
    if key in seen:continue
    seen.add(key);found=island_qa.check(atlas.crop((x,y,x+w,y+h)),mp.parents[1].name,action,i)
    if found:rows.append(dict(fighter=mp.parents[1].name,action=action,frame=i,texture=clip['texture'],rect=[x,y,w,h],components=found))
 return rows

if __name__=='__main__':
 rows=scan();save(ROOT/'reports/island-scan.json',dict(frames=rows))
 errors=[r for r in rows if any(not c['allowed'] for c in r['components'])]
 print(json.dumps(errors,ensure_ascii=False,indent=2))
 if errors:raise SystemExit(1)
 print('ISLAND_QA PASS：正式人物微小游离块均有明确道具登记。')

"""同一检查连续拒收三个不同帧时暂停；不因换动作或重试而空转。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
from contextlib import contextmanager
import os,time
from head_scale import read,save,ROOT,font

class Brake:
 def __init__(self,path):
  self.path=path;self.state=read(path) if path.exists() else dict(checks={},paused={})
 @contextmanager
 def lock(self):
  lock=self.path.with_suffix('.lock');lock.parent.mkdir(parents=True,exist_ok=True)
  for _ in range(1200):
   try:handle=lock.open('x');handle.write(str(os.getpid()));handle.close();break
   except FileExistsError:time.sleep(.05)
  else:raise ValueError('质检防空转写锁超时')
  try:yield
  finally:lock.unlink()
 def record(self,frame,checks,evidence=None):
  with self.lock():
   if self.path.exists():self.state=read(self.path)
   return self._record(frame,checks,evidence)
 def _record(self,frame,checks,evidence=None):
  if evidence is not None:self.state.setdefault('evidence',{})[frame]=str(evidence)
  for key,passed in checks.items():
   history=self.state['checks'].setdefault(key,[])
   if passed:history.clear();continue
   if frame not in history:history.append(frame)
   if len(history)>=3 and key not in self.state['paused']:
    self.state['paused'][key]=dict(frames=history[-3:],reason='连续拒收3个不同帧，暂停此项；先交诊断，不继续请求')
    self.diagnostic(key,history[-3:])
  save(self.path,self.state)
  return self.state['paused']
 def blocked(self,checks):return any(key in self.state['paused'] for key in checks)
 def diagnostic(self,key,frames):
  from PIL import Image,ImageDraw
  canvas=Image.new('RGB',(1500,620),'#202632');d=ImageDraw.Draw(canvas)
  d.text((12,10),key+'：连续三个不同帧拒收，暂停检查并转做其它项目',font=font(23),fill='white')
  for i,frame in enumerate(frames):
   d.text((i*500+12,52),frame,font=font(15),fill='#8bd9ff')
   p=Path(self.state.get('evidence',{}).get(frame,''))
   if p.is_file():
    im=Image.open(p).convert('RGBA');scale=min(480/im.width,500/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST);canvas.paste(im,(i*500+(500-im.width)//2,100),im)
   else:d.text((i*500+12,110),'缺可测成品；保留原始请求和失败记录',font=font(18),fill='white')
  target=self.path.with_name(self.path.stem+'-'+key+'-diagnostic.png');canvas.save(target)
  self.state['paused'][key]['diagnostic']=str(target)

"""运行时音频/特效资源清单校验；不代替画面与听感审片。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import hashlib,json,math,wave; json = _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import numpy as np
from PIL import Image
ROOT=_LayoutProjectPath(_layout_root)
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def main():
 records=read(ROOT/'content/audio/sources.json')['records'];ids=set();metrics=[]
 for record in records:
  # 已明确不接入运行时的历史/原创记录不参与运行时音频资源硬门。
  if record.get('deprecated_for_runtime'):continue
  path=ROOT/record['path'].removeprefix('res://');assert path.is_file(),path
  assert record['id'] not in ids;ids.add(record['id'])
  assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256'],path
  with wave.open(str(path)) as f:
   seconds=f.getnframes()/f.getframerate();channels=f.getnchannels()
   assert channels in (1,2) and f.getsampwidth()==2,path
   data=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2')
  assert abs(seconds-record['duration_seconds'])<.001
  assert np.max(np.abs(data.astype(np.int32)))>100 and np.max(np.abs(data.astype(np.int32)))<32700
  # 当前原剧整句保留双声道；无LUFS实测的收据不虚构该指标。
  if 'integrated_lufs' in record:assert math.isfinite(record['integrated_lufs']),path
  assert record['true_peak_dbfs']<=-1.8,path
  assert 20*math.log10(float(np.max(np.abs(data.astype(np.int32))))/32768)<=-1.8,path
  assert record['source_kind'] in ['original','episode','derivative'] and record['license']
  metrics.append({'id':record['id'],'seconds':seconds,'channels':channels,'integrated_lufs':record.get('integrated_lufs'),'sha256':record['sha256']})
 effects=read(ROOT/'content/presentation/phase3_projectiles.json');fx=[]
 for key in ['beam_loop','zetton_super_fire']:
  for level,clip in effects[key]['variants'].items():
   path=ROOT/clip['texture'].removeprefix('res://');im=Image.open(path).convert('RGBA')
   assert hashlib.sha256(path.read_bytes()).hexdigest()==clip['atlas_sha256']
   assert clip['display_scale']==[1,1]
   assert set(im.getchannel('A').getdata())<={0,255}
   heights=[]
   for i,r in enumerate(clip['rects']):
    x,y,w,h=r;frame=np.array(im.crop((x,y,x+w,y+h)))
    if key=='beam_loop':
     assert np.array_equal(frame[:,0],frame[:,-1]),'平铺边界不一致'
     assert np.all(frame[h//2,:,3]==255),'中心存在透明断点'
    bounds=Image.fromarray(frame).getbbox();heights.append(bounds[3]-bounds[1])
    if key=='zetton_super_fire':
     box=clip['frame_boxes'][i];assert box[2:]==[bounds[2]-bounds[0],bounds[3]-bounds[1]]
   if key=='zetton_super_fire' and level=='3':assert all(249<=h<=332 for h in heights)
   fx.append({'effect':key,'level':int(level),'native_alpha_heights':heights,'runtime_scale':[1,1]})
 out={'audio':metrics,'effects':fx,'note':'资源尺寸/Alpha/哈希/平铺边界核对，不代替实际画面与听感验收'}
 (ROOT/'reports/fx-audio-resources.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('FX_AUDIO_RESOURCES PASS')
if __name__=='__main__':main()

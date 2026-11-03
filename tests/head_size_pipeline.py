"""验证强制尺寸门、图像指纹和同源比例完整性；不把画面美感当测试。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import tempfile,sys,json; json = _LayoutJson
from PIL import Image
ROOT=_LayoutProjectPath(_layout_root)
sys.path.insert(0,str(ROOT/'tools/rebuild'))
import head_size as h

def expect_rejection(folder,why):
 try:h.validate(folder,'ultraman')
 except ValueError:return
 raise AssertionError('应拒收：'+why)
def main():
 with tempfile.TemporaryDirectory(prefix='ufeneo-head-size-') as temp:
  folder=Path(temp);expect_rejection(folder,'没有头部质检凭据')
  model=h.model_path('ultraman');image=folder/'native.png';image.write_bytes(model.read_bytes());ref=h.reference('ultraman')
  row=dict(frame=0,image='native.png',image_sha256=h.digest(image),hint=ref['measurement']['center'],source=model.relative_to(ROOT).as_posix(),source_sha256=h.digest(model),raw_head_length=ref['measurement']['length'],shared_scale=1)
  def write(rows): (folder/'head-qa.json').write_text(json.dumps(dict(reference=ref,frames=rows)),encoding='utf-8')
  write([]);expect_rejection(folder,'空的逐帧测量不能放行')
  write([dict(row,shared_scale=float('nan'))]);expect_rejection(folder,'非有限缩放系数不能放行')
  write([row]);h.validate(folder,'ultraman')
  second=dict(row,frame=1,shared_scale=1.1);write([row,second]);expect_rejection(folder,'同一张原图使用两个比例')
  # 新规则必须显式声明逐帧测量；保留旧共享规则的审计，防止静默改变旧凭据。
  (folder/'head-qa.json').write_text(json.dumps(dict(scale_policy='per_frame_head',reference=ref,frames=[row,second])),encoding='utf-8');h.validate(folder,'ultraman')
  source=Image.open(model).convert('RGBA');_,_,calibrated,_=h.calibration('ultraman',[source,source.resize((240,240),Image.Resampling.NEAREST)],{})
  assert calibrated['scale_policy']=='per_frame_head' and calibrated['frame_scales'][1]<calibrated['frame_scales'][0]
  write([row]);im=Image.open(image).convert('RGBA');im.resize((250,250),Image.Resampling.NEAREST).save(image);expect_rejection(folder,'质检后图片指纹改变')
  enlarged=dict(row,image_sha256=h.digest(image),hint=[v*250/192 for v in row['hint']]);write([enlarged]);expect_rejection(folder,'成品头部超过8%')
  # 真实旧俯冲稿曾被错误的模板头轴截断，导致大头漏报；新标尺必须识别。
  reference=h.reference('ultraseven','eye-ear-v2')['measurement']['length']
  for index in [2,3]:
   path=ROOT/f'art/fighters/ultraseven/stage4/revisions/seven-gpt-redraw/air-batch/dive/take-06/frame-{index}.png'
   measured=h.head(Image.open(path).convert('RGBA'),'ultraseven',method='eye-ear-v2')
   assert measured and measured['length']/reference>1.20,'倾斜大头不得因为裁错半个头壳而漏报'
  from qa_brake import Brake
  brake=Brake(folder/'brake.json');assert not brake.record('a',{'size':False});assert not brake.record('a',{'size':False});assert not brake.record('b',{'size':False});assert brake.record('c',{'size':False})
 print('HEAD_SIZE_PIPELINE PASS：缺测量、同源比例冲突、过期质检和超差头部均拒收。')
if __name__=='__main__':main()

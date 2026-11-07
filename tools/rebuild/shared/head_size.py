"""强制头部尺度门：逐帧比例，遮挡依据可追溯；兼容旧版已审共享比例凭据。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import hashlib,json,math; json = _LayoutJson
import numpy as np
from PIL import Image
from head_scale import measure,pose_direction,ROOT

TOLERANCE=.08
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text('utf-8-sig'))
def model_path(fighter):
 path=ROOT/f'assets/fighters/{fighter}/model-native.png'
 return path if path.exists() else ROOT/_LayoutJson.path_text(f'art/model_sheets/{fighter}/model-native.png')
def head(im,fighter,hint=None,direction=None,region=None,method=None,facing=None):
 if fighter=='ultraseven' and facing=='left':
  # 只镜像测量输入坐标，最终人物图绝不翻转或重画。
  reflected=im.transpose(__import__('PIL.Image',fromlist=['Transpose']).Transpose.FLIP_LEFT_RIGHT)
  m=head(reflected,fighter,None if hint is None else [im.width-1-hint[0],hint[1]],method=method)
  if m is None:return None
  for k in ['center','eye','ear','lamp']:
   if m.get(k) is not None:m[k]=[im.width-1-m[k][0],m[k][1]]
  m['polygon']=[[im.width-1-x,y] for x,y in m['polygon']]
  if m.get('bounds'):x0,y0,x1,y1=m['bounds'];m['bounds']=[im.width-x1,y0,im.width-x0,y1]
  m['measured_facing']='left';return m
 if fighter in ['ultraman','zetton']:return measure(im,fighter,hint,direction,region)
 if fighter=='ultraseven':
  if method=='eye-ear-v2':
   from seven_head_features import measure as seven_measure
   return seven_measure(im,hint)
  a=np.array(im);r,g,b=a[:,:,:3].astype(int).transpose(2,0,1)
  ys,xs=np.where((a[:,:,3]>0)&(g>r*1.3)&(g>b*1.1)&(g>80))
  if not len(xs):
   # 转背无额灯：必须显式标出排除头镖的固定头盔；不能自动换成胸肩或姿势外框。
   return measure(im,'ultraman',hint,region=region) if region is not None else None
  lamp=np.array([float(xs.mean()),float(ys.mean())])
  if hint is None:
   axis=np.array(direction or [0,-1],dtype=float);axis=axis/max(1e-9,np.linalg.norm(axis));tangent=np.array([-axis[1],axis[0]])
   hint=(lamp-4*tangent-5*axis).tolist()
  rough=measure(im,'ultraman',hint,region=region)
  if not rough:return None
  axis=np.array(direction or [0,-1]);axis=axis/max(1e-9,np.linalg.norm(axis))
  yy,xx=np.indices(a.shape[:2]);projection=(xx-lamp[0])*axis[0]+(yy-lamp[1])*axis[1]
  # 用额头灯所在平面定位固定头盔，排除可拆头镖；相同规则同时用于定稿和成品。
  # 固定额灯所在平面以上全部不参与比例；头镖摘下时也不能放大整个人。
  a[projection>0,3]=0
  return measure(Image.fromarray(a),'ultraman',hint,region=region)
 raise ValueError(fighter+'缺少已确认的稳定头部测量规则；不允许退回按姿势外框缩放')
def reference(fighter,method=None):
 path=model_path(fighter);im=Image.open(path).convert('RGBA');m=head(im,fighter,method=method)
 if m is None:raise ValueError(fighter+'定稿头部无法可靠测量，需标注')
 return dict(image=path.relative_to(ROOT).as_posix(),sha256=digest(path),measurement_method=method,feature=('实测眼/护耳倾角下固定头盔最大弦长（旋转不变）' if method else {'ultraman':'银色头壳最大弦长','zetton':'脸部发光体最大弦长','ultraseven':'额灯平面以下固定头盔最大弦长（排除可拆头镖）'}.get(fighter,'待标注稳定头部特征')),measurement=m)

def width_measure(im,region):
 """转背头盔被中线轮廓分成左右两块，头宽必须合测，不能把窄头刃当头。"""
 if not region:return None
 from PIL import ImageDraw
 mask=Image.new('1',im.size);ImageDraw.Draw(mask).polygon([tuple(p) for p in region],fill=1)
 a=np.array(im);rgb=a[:,:,:3].astype(int);ys,xs=np.where(np.array(mask)&(a[:,:,3]>0)&(rgb.max(2)-rgb.min(2)<48)&(rgb.mean(2)>105))
 if not len(xs):return None
 x0,x1,y0,y1=map(int,[xs.min(),xs.max(),ys.min(),ys.max()]);w=x1-x0+1;h=y1-y0+1
 return dict(width=float(w),length=float(np.hypot(w,h)),center=[float(xs.mean()),float(ys.mean())],polygon=[[x0,y0],[x1,y0],[x1,y1],[x0,y1]],bounds=[x0,y0,x1+1,y1+1],area=len(xs),aspect=h/w)
def calibration(fighter,cells,request):
 method='eye-ear-v2' if fighter=='ultraseven' else None
 ref=reference(fighter,method);heads=[]
 hidden=set(request.get('head_occluded_frames',[]))
 for i,cell in enumerate(cells):
  region=request.get('head_regions',{}).get(str(i))
  if region:region=[[x*cell.width,y*cell.height] for x,y in region]
  # 直接测原始像素，不用检测缩图的四舍五入误差决定正式比例。
  direction=request.get('head_directions',{}).get(str(i),[0,-1]) if fighter=='ultraseven' else pose_direction(request,i)
  axis=request.get('head_measurement_axes',{}).get(str(i),request.get('head_measurement_axis','length'))
  m=width_measure(cell,region) if axis=='width' else head(cell,fighter,direction=direction,region=region,method=method,facing=request.get('head_facings',{}).get(str(i)))
  if i in hidden:m=None
  if m is None and i not in hidden:raise ValueError(f'frame {i}: 头部遮挡/不可可靠测量，需人工标注，禁止按外框代替')
  heads.append(m)
 # 仅显式登记的遮挡帧使用同条前后可测帧的整帧比例插值。
 # 不用背面头宽或蹲姿外框决定人物尺寸。
 interpolated={}
 for i in sorted(hidden):
  left=next((j for j in range(i-1,-1,-1) if heads[j] is not None and j not in hidden),None)
  right=next((j for j in range(i+1,len(heads)) if heads[j] is not None and j not in hidden),None)
  if left is None or right is None:raise ValueError(f'frame {i}: 遮挡比例插值缺少前后可测帧')
  t=(i-left)/(right-left);scale=(1-t)*ref['measurement']['length']/heads[left]['length']+t*ref['measurement']['length']/heads[right]['length']
  m=dict(heads[left]);m['length']=ref['measurement']['length']/scale
  # 该定位仅用于头部审片裁切，不宣称是可见头部实测。
  m['center']=[(1-t)*heads[left]['center'][k]+t*heads[right]['center'][k] for k in [0,1]]
  heads[i]=m;interpolated[str(i)]=[dict(frame=left),dict(frame=right)]
 axis=request.get('head_measurement_axis','length')
 if axis not in ['length','width']:raise ValueError('未知头部测量轴')
 lengths=[m[axis] for m in heads];factor=2*ref['measurement'][axis]/(min(lengths)+max(lengths))
 ref['frame_scales']=[ref['measurement'][request.get('head_measurement_axes',{}).get(str(i),axis)]/m[request.get('head_measurement_axes',{}).get(str(i),axis)] for i,m in enumerate(heads)]
 ref['measurement_axis']=axis
 ref['scale_policy']='per_frame_head'
 ref['occluded_interpolation']=interpolated
 # 原图差异作诊断；最终是否通过以像素还原后实际成品为准，不额外扩大用户的质量门。
 ref['raw_spread_percent']=(max(lengths)-min(lengths))/(max(lengths)+min(lengths))*100
 return factor,heads,ref,[]
def validate(folder,fighter):
 """安装时重读真实PNG及定稿；不相信旧的pass布尔值。"""
 folder=Path(folder);path=folder/'head-qa.json'
 if not path.exists():raise ValueError('缺少强制头部尺寸质检：'+str(path))
 q=read(path);method=q['reference'].get('measurement_method');ref=reference(fighter,method);issues=list(q.get('issues',[]));scales={}
 if not q.get('frames'):raise ValueError('没有逐帧头部测量，禁止安装')
 if q['reference']['sha256']!=ref['sha256']:issues.append('定稿已改变，必须重测头部')
 for row in q['frames']:
  if not math.isfinite(row['shared_scale']) or row['shared_scale']<=0:
   issues.append('缩放系数必须是正的有限数');continue
  image=folder/row['image'];raw=ROOT/row['source']
  if digest(image)!=row['image_sha256'] or digest(raw)!=row['source_sha256']:issues.append('质检后的图像或原图已变化');continue
  if q.get('scale_policy')!='per_frame_head' and raw.as_posix() in scales and not math.isclose(scales[raw.as_posix()],row['shared_scale'],abs_tol=1e-10):issues.append('同一原图使用不同缩放系数')
  scales[raw.as_posix()]=row['shared_scale']
  if row.get('size_policy')=='standing_height':
   import standing_size_qa
   peer_heights=[]
   if row.get('crown_view')=='back':
    peers=[peer for peer in q['frames'] if abs(peer['frame']-row['frame'])==1]
    peer_heights=[standing_size_qa.measure(Image.open(folder/peer['image']).convert('RGBA'),fighter,peer)['height'] for peer in peers]
   standing=standing_size_qa.check(Image.open(image).convert('RGBA'),fighter,row,peer_heights)
   if not standing['pass_']:issues.append(f'frame {row["frame"]}: 直立站高超出±3%')
   continue
  if row.get('crown_view')=='back':
   issues.append(f'frame {row["frame"]}: 看不到脸的直立帧必须用站高，不能用头宽定比例')
   continue
  if row.get('auxiliary'):
   aux=row['auxiliary'];m=head(Image.open(image).convert('RGBA'),fighter,row['hint'],region=row.get('head_region'))
   baseline=head(Image.open(model_path(fighter)).convert('RGBA'),fighter,region=aux['reference_region'])
   if not baseline or not m or abs(m['length']/baseline['length']-1)>TOLERANCE:issues.append('遮挡头部的稳定辅助部位尺寸超差或不可测')
   continue
  if row.get('occluded'):
   basis=row.get('interpolation',[])
   if len(basis)!=2 or not basis[0]['frame']<row['frame']<basis[1]['frame']:
    issues.append('遮挡帧缺少前后可靠测量');continue
   peers={r['frame']:r for r in q['frames']}
   if any(b['frame'] not in peers or peers[b['frame']].get('occluded') for b in basis):issues.append('遮挡插值依据不可用');continue
   t=(row['frame']-basis[0]['frame'])/(basis[1]['frame']-basis[0]['frame'])
   for b in basis:
    peer=peers[b['frame']];s=b.get('scale',peer['shared_scale'])
    if abs(peer['raw_head_length']*s/ref['measurement']['length']-1)>TOLERANCE:issues.append('插值依据的原图测量比例超差')
   expected=basis[0].get('scale',peers[basis[0]['frame']]['shared_scale'])*(1-t)+basis[1].get('scale',peers[basis[1]['frame']]['shared_scale'])*t
   if not math.isclose(expected,row['shared_scale'],abs_tol=1e-9):issues.append('遮挡帧没有使用已记录的前后比例插值')
   continue
  if q.get('pilot_polish_source') is True and row.get('head_polish',{}).get('changed'):
   # 只接入本轮白名单派生帧；来源、像素、配置和整头读数均须重新核对。
   from pilot_polish_qa import validate_registered_head
   validate_registered_head(folder,fighter,q,row)
   continue
  axis=row.get('measurement_axis','length')
  im=Image.open(image).convert('RGBA')
  m=width_measure(im,row.get('head_region')) if axis=='width' else head(im,fighter,row['hint'],direction=row.get('head_direction'),region=row.get('head_region'),method=row.get('measurement_method',method),facing=row.get('facing'))
  if axis not in ['length','width']:raise ValueError('未知头部测量轴')
  if m is None or abs(m[axis]/ref['measurement'][axis]-1)>TOLERANCE:issues.append(f'frame {row["frame"]}: 成品头部尺寸超出±8%或无法识别')
 if issues:raise ValueError('; '.join(issues))
 return q

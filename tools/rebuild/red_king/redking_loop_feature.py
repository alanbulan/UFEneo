"""雷德王暗眼循环：读取已核原图标点，绑定当前帧像素；不套英雄金眼颜色。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import hashlib
import numpy as np
from PIL import Image

ROOT=_LayoutProjectPath(_layout_root)


def feature(image, row):
    path=ROOT/row['image']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=row['image_sha256']:
        raise ValueError('雷德王循环标点对应的候选PNG已改变')
    source=Image.open(path).convert('RGBA')
    if not np.array_equal(np.asarray(source),np.asarray(image.convert('RGBA'))):
        raise ValueError('雷德王循环标点与当前图集像素不一致')
    if row.get('points_status')!='已核对':
        raise ValueError('雷德王循环原图眼点未经核对')
    point=np.asarray(row['native_points']['eye'],dtype=float)
    if not np.isfinite(point).all() or not (0<=point[0]<image.width and 0<=point[1]<image.height):
        raise ValueError('雷德王原图眼点映射越界')
    return point.tolist()


def measure(images,rows,action):
    from loop_qa import evaluate
    result=evaluate([feature(image,row) for image,row in zip(images,rows)],action)
    factor=176/135
    result['limits']={key:value*factor if key in {'vertical','adjacent','horizontal'} and value is not None else value for key,value in result['limits'].items()}
    result['issues']=[]
    for key,value,name in [('vertical',result['vertical_range'],'眼高总幅'),('adjacent',max(result['adjacent_y']),'相邻含首尾眼高差'),('horizontal',result['horizontal_range'],'水平漂移')]:
        limit=result['limits'][key]
        if limit is not None and value>limit+1e-6:result['issues'].append(f'{name}{value:.3f}px > {limit:.3f}px')
    return dict(fighter='red_king',source='已核高分原图眼点→固定比例→实际PNG/图集像素逐点绑定；不挑奶白鳞甲或沟槽',size_factor=factor,**result)

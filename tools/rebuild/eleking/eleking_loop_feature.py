"""艾雷王无眼球：按原图已核对的近角固定轴H测循环，逐帧像素指纹绑定。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import hashlib
import math


def feature(im, row):
    point = row.get('loop_feature', {})
    if point.get('name') != 'H近角固定轴':
        raise ValueError('艾雷王循环缺少真实近角轴H标点')
    if hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest() != point.get('rgba_sha256'):
        raise ValueError('艾雷王循环图像与原图H标点凭据不一致')
    x, y = point['point']
    if not all(math.isfinite(v) for v in [x, y]) or not (0 <= x < im.width and 0 <= y < im.height):
        raise ValueError('艾雷王H点越界')
    # 标点直接来自高分原图，禁止角尖或模板误中斑纹后换成另一个点。
    crop = im.crop((max(0,round(x)-2),max(0,round(y)-2),min(im.width,round(x)+3),min(im.height,round(y)+3)))
    if not any(p[3] and max(p[:3]) < 100 for p in crop.getdata()):
        raise ValueError('艾雷王H邻域没有真实深色角轴')
    return [x, y]

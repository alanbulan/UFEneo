"""布莱泽青白单眼标注，绑定完整帧像素；不沿用黄眼角色检测器。"""
import hashlib, math

def feature(image,row):
    if hashlib.sha256(image.convert('RGBA').tobytes()).hexdigest()!=row.get('rgba_sha256'):
        raise ValueError('布莱泽循环标点与当前完整帧像素不符，必须重测')
    point=row.get('native_points',{}).get('eye')
    if not point or len(point)!=2 or not all(math.isfinite(float(x)) for x in point):
        raise ValueError('布莱泽缺少逐相单眼原图标点')
    if not (0<=point[0]<image.width and 0<=point[1]<image.height):
        raise ValueError('布莱泽单眼标点越界')
    return list(map(float,point))

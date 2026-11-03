"""校准真实骨长、像素指纹及正式躺姿配置；不改变任何人物像素。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import hashlib,sys
from pathlib import Path
Path = _LayoutProjectPath
from PIL import Image
ROOT=_LayoutProjectPath(_layout_root)
sys.path.insert(0,str(ROOT/'tools/rebuild'))
from head_scale import read,sha
import body_length_qa as qa

def main():
    path=ROOT/'art/fighters/ultraseven/stage4/revisions/seven-body-fix/body-calibration.json'
    calibration=read(path)
    assert calibration['all_pass'],'真实骨长门须先用已审旧帧校准，不能绕过或放宽阈值'
    assert calibration['tolerance']==.08
    for row in calibration['frames']:
        im=Image.open(ROOT/row['source_texture'].removeprefix('res://')).convert('RGBA');x,y,w,h=row['source_rect'];im=im.crop((x,y,x+w,y+h))
        assert hashlib.sha256(im.tobytes()).hexdigest()==row['frame_pixel_sha256'],'校准旧帧变化，须重新测量'
        measurement=row['measurement'];marks=dict(path=measurement['path'],reason=measurement['method']) if measurement.get('path') else None
        m=qa.measure(im,row['head_input'],row['fighter'],marks);ref=qa.reference(row['fighter'])
        assert m and abs(m['length']/ref['length']-1)<=.08,(row['fighter'],row['action'],'身长校准超差')
    for fighter in ['ultraman','zetton','ultraseven']:
        qa.reference(fighter)
        mp=ROOT/f'assets/fighters/{fighter}/animations/manifest.json'
        for action,clip in read(mp)['clips'].items():
            if not clip.get('head_qa'):continue
            folder=(ROOT/clip['head_qa']).parent
            policy=folder/'body-length-policy.json'
            if policy.exists():qa.validate_folder(folder,fighter,action)
            elif fighter=='ultraseven' and action=='down':raise ValueError('赛文正式倒地缺少真实骨长强制配置')
    print('BODY_LENGTH PASS：定稿真实骨长、已审旧帧校准和正式躺姿一致，阈值保持±8%。')

if __name__=='__main__':main()

"""检查赛文头镖身份门的有效性；不评判动作美感。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import sys
from pathlib import Path
Path = _LayoutProjectPath
import numpy as np
from PIL import Image
ROOT=_LayoutProjectPath(_layout_root)
sys.path.insert(0,str(ROOT/'tools/rebuild'))
import slugger_qa as q
from head_scale import read,sha

def main():
    config=read(q.CONFIG);assert config['model_sha256']==sha(q.MODEL)
    assert config['minimum_iou']==.75 and config['hard_rejection'] is False
    base=Image.open(q.MODEL).convert('RGBA');assert q.compare(base)['pass_']
    for path in ['art/fighters/ultraseven/stage4/revisions/crown-counter-revision/before.png','art/fighters/ultraseven/stage4/revisions/ultraseven-head-edit/before.png']:
        assert not q.compare(Image.open(ROOT/path).convert('RGBA'))['pass_'],'旧错误轮廓应拒收'
    # 摘镖不是缩头。只在测试副本擦掉冠域，固定头盔测量长度必须不变。
    a=np.array(base);a[:51,:,3]=0;a[51:76,:89,3]=0;detached=Image.fromarray(a)
    assert q.compare(detached,detached=True)['pass_']
    assert not q.compare(base,detached=True)['pass_'],'头镖未离头不能算摘镖'
    import head_size
    assert head_size.head(base,'ultraseven')['length']==head_size.head(detached,'ultraseven')['length']
    mirrored=base.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    assert q.compare(mirrored,dict(facing='left'))['pass_']
    assert not q.compare(base,dict(occlusion_polygon=[[0,0],[191,0],[191,191],[0,191]]))['pass_'],'不得用整域遮挡绕过轮廓检查'
    # 用户授权的背面仅可转人工冠形复核，不能把有脸帧标成背面逃过身份门。
    import tempfile,json,shutil; json = _LayoutJson
    actual=(ROOT/read(ROOT/'assets/fighters/ultraseven/animations/manifest.json')['clips']['turn']['head_qa']).parent
    if actual.exists():
        with tempfile.TemporaryDirectory(prefix='ufeneo-back-crown-') as temp:
            folder=Path(temp)
            for p in actual.glob('frame-*.png'):shutil.copy2(p,folder/p.name)
            data=read(actual/'head-qa.json');(folder/'head-qa.json').write_text(json.dumps(data),encoding='utf-8')
            result=q.validate(folder);assert result[1]['review_required'] and result[1]['pass_'] is None
            data['frames'][0].update(crown_view='back',measurement_axis='width',manual_crown_reason='测试错误背面标注')
            (folder/'head-qa.json').write_text(json.dumps(data),encoding='utf-8')
            try:q.validate(folder)
            except ValueError:pass
            else:raise AssertionError('有额灯帧不得跳过侧面冠形门')
    print('SLUGGER_PIPELINE PASS：定稿、错误冠形、摘镖和左向对齐符合身份门。')

if __name__=='__main__':main()

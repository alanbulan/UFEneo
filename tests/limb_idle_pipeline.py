"""仅验证质检规则的拒收行为，不用自动检查替代视觉审片。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import sys
import tempfile
import numpy as np
from PIL import Image
ROOT=_LayoutProjectPath(_layout_root)
sys.path.insert(0,str(ROOT/'tools/rebuild'))
import limb_color_qa as color
import idle_qa
sys.path.insert(0,str(ROOT/'tools'))
from check.limb_idle import frame_row,legacy_baseline

def main():
    near=color.materials('ultraseven')[1][1][0];far=color.materials('ultraseven')[1][2][0]
    a=np.zeros((12,12,4),dtype='uint8');a[:]=list(near)+[255];base=Image.fromarray(a.copy())
    a[:,6:,:3]=far;block=Image.fromarray(a.copy())
    hits=color.boundaries(block,'ultraseven',base)
    assert any(r['length']>=4 and r['introduced_by_postprocess'] for r in hits)
    try:color.validate([block],'ultraseven',[base])
    except ValueError:pass
    else:raise AssertionError('矩形压暗应拒收')
    a[:,5,:3]=[15,20,29];outlined=Image.fromarray(a)
    assert not color.boundaries(outlined,'ultraseven'), '有深色轮廓隔开不应判矩形切块'
    assert not any(r['introduced_by_postprocess'] for r in color.boundaries(block,'ultraseven',block)), '原生光影单列'
    # GPT原生直线不拦截；生产入口必须用冻结的原生量化证据区分来源。
    with tempfile.TemporaryDirectory(prefix='ufeneo-color-gate-') as temp:
        folder=Path(temp);block.save(folder/'frame-0.png');block.save(folder/'source-0.png')
        color.save(folder/'head-qa.json',dict(frames=[dict(image='frame-0.png')]))
        color.save(folder/'limb-color-baseline.json',dict(frames=[dict(image='source-0.png',sha256=color.sha(folder/'source-0.png'))]))
        color.validate_folder(folder,'ultraseven','heavy')
        base.save(folder/'source-0.png');color.save(folder/'limb-color-baseline.json',dict(frames=[dict(image='source-0.png',sha256=color.sha(folder/'source-0.png'))]))
        try:color.validate_folder(folder,'ultraseven','heavy')
        except ValueError:pass
        else:raise AssertionError('后处理新增分界必须拒收')
    a=np.array(base);a[2:5,6:9,:3]=far
    assert not color.boundaries(Image.fromarray(a),'ultraseven'), '不足4px不应报长直线'
    # 冲刺拆成2/4/3帧后，局部质检与全段质检都应解析同一实际帧。
    clip=dict(rects=[[]]*4,sequence_frames=[2,3,4,5])
    assert frame_row([dict(frame=i) for i in range(4)],clip,0)['frame']==0
    assert frame_row([dict(frame=i) for i in range(9)],clip,0)['frame']==2
    with tempfile.TemporaryDirectory(prefix='ufeneo-legacy-baseline-') as temp:
        folder=Path(temp);base.save(folder/'0.png');block.save(folder/'2.png')
        color.save(folder/'0.json',dict(source_sha256='actual-source'))
        color.save(folder/'2.json',dict(source_sha256='other-source'))
        assert legacy_baseline(folder,block,dict(source_sha256='actual-source')).name=='0.png'
        assert legacy_baseline(folder,block,dict(source_sha256='missing')) is None
        cropped=Image.new('RGBA',base.size)
        assert legacy_baseline(folder,cropped,dict(source_sha256='actual-source')) is None
    # 由独立输入特征验证首尾、水平漂移和单周期，避免只检查前五次变化。
    original=idle_qa.feature
    try:
        idle_qa.feature=lambda im,f,r:im
        def measure(points):return idle_qa.measure(points,'ultraseven',[{}]*len(points))
        assert not measure([[10,10],[10,11],[10,12],[10,12],[10,11],[10,10]])['issues']
        assert measure([[10,10],[10,12],[10,14],[10,14],[10,13],[10,13]])['issues'], '必须检查末帧到首帧'
        assert measure([[10,10],[13,10],[10,10]])['issues'], '水平漂移应拒收'
        assert measure([[10,10],[10,12],[10,10],[10,12],[10,10],[10,12]])['issues'], '锯齿起伏应拒收'
    finally:idle_qa.feature=original
    print('LIMB_IDLE_PIPELINE PASS：直角遮罩、深轮廓例外、首尾及呼吸轨迹规则有效。')

if __name__=='__main__':main()

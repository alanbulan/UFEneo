"""正式资源的压暗遮罩及待机轨迹门；初代/杰顿待机按用户要求只报告。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import argparse
import sys
from collections import Counter
import numpy as np
from PIL import Image
ROOT=_LayoutProjectPath(_layout_root)
sys.path.insert(0,str(ROOT/'tools/rebuild'))
from head_scale import read,save,sha
import limb_color_qa as color
import idle_qa


def frame_row(records,clip,index):
    """拆分动作的质检可局部存储，也可共用整段；不能混用两种下标。"""
    if len(records)==len(clip['rects']):return records[index]
    sequence=clip['sequence_frames'][index]
    return next((r for r in records if r.get('frame')==sequence),records[sequence])


def legacy_baseline(directory,image,head):
    """历史文件名混用局部/全段编号，只按原图指纹和实际Alpha唯一匹配。"""
    matches=[];alpha=np.array(image.getchannel('A'));digest=head.get('source_sha256')
    if not digest:return None
    for metadata in sorted(Path(directory).glob('*.json')):
        data=read(metadata);candidate=metadata.with_suffix('.png')
        if data.get('source_sha256')!=digest or not candidate.exists():continue
        before=Image.open(candidate).convert('RGBA')
        if before.size==image.size and np.array_equal(np.array(before.getchannel('A')),alpha):matches.append(candidate)
    if len(matches)>1 and len({sha(p) for p in matches})>1:
        raise ValueError('原图指纹和Alpha对应多份不同基线：'+str(directory))
    return matches[0] if matches else None


def main(output=None):
    rows=[];idles=[];errors=[];digests={}
    for fighter in ['ultraman','zetton','ultraseven']:
        manual_path=ROOT/f'content/fighters/{fighter}/limb-color-manual-review.json'
        manual=read(manual_path)['frames'] if manual_path.exists() else []
        manifest=read(ROOT/f'assets/fighters/{fighter}/animations/manifest.json');cache={}
        for action,clip in manifest['clips'].items():
            p=ROOT/clip['texture'].removeprefix('res://')
            if p not in cache:cache[p]=Image.open(p).convert('RGBA')
            atlas=cache[p];folder=(ROOT/clip['head_qa']).parent;hq=read(folder/'head-qa.json');images=[];heads=[]
            cb=read(folder/'limb-color-baseline.json') if (folder/'limb-color-baseline.json').exists() else None
            for i,(x,y,w,h) in enumerate(clip['rects']):
                idx=clip.get('sequence_frames',list(range(len(clip['rects']))))[i]
                head=frame_row(hq['frames'],clip,i);im=atlas.crop((x,y,x+w,y+h));images.append(im);heads.append(head)
                if cb:
                    cr=frame_row(cb['frames'],clip,i);baseline=folder/cr['image'];assert sha(baseline)==cr['sha256'],'调色前基线被覆盖'
                    resolution='逐帧GPT量化基线记录'
                else:
                    a='dash_sequence' if fighter=='ultraseven' and action in ['dash_start','dash','dash_stop'] else action
                    baseline=legacy_baseline(ROOT/f'art/shared/production/limb-contours/baselines/{fighter}/{a}',im,head)
                    resolution='原图SHA256与Alpha匹配'
                if p not in digests:digests[p]=sha(p)
                record=dict(fighter=fighter,action=action,frame=i,atlas_frame=idx,head_frame=head['frame'],texture=clip['texture'],atlas_sha256=digests[p])
                pixel_digest=__import__('hashlib').sha256(im.tobytes()).hexdigest()
                reviewed=next((r for r in manual if r['action']==action and r['frame']==i and (r.get('atlas_sha256')==digests[p] or r.get('frame_pixel_sha256')==pixel_digest)),None)
                if reviewed:
                    record.update(boundaries=color.boundaries(im,fighter),disposition='已人工复核保留',review_source=manual_path.relative_to(ROOT).as_posix());rows.append(record);continue
                if baseline is not None and baseline.exists():
                    base=Image.open(baseline).convert('RGBA')
                    if im.size!=base.size or not np.array_equal(np.array(im)[:,:,3],np.array(base)[:,:,3]):errors.append(f'{fighter}/{action}#{i}: 调色前基线轮廓不匹配');continue
                    hit=color.boundaries(im,fighter,base);record.update(boundaries=hit,baseline=baseline.relative_to(ROOT).as_posix(),baseline_sha256=sha(baseline),baseline_resolution=resolution)
                    if any(r['introduced_by_postprocess'] for r in hit):errors.append(f'{fighter}/{action}#{i}: 后处理压暗产生无轮廓≥4px直线')
                else:
                    hit=color.boundaries(im,fighter);record.update(boundaries=hit,baseline=None)
                    if hit:errors.append(f'{fighter}/{action}#{i}: 直线候选缺调色前基线，不能自动放行')
                rows.append(record)
            if action=='idle':
                result=idle_qa.measure(images,fighter,heads);result['report_only']=fighter in ['ultraman','zetton'];idles.append(result)
                if result['issues'] and not result['report_only']:errors.extend(fighter+'/idle: '+s for s in result['issues'])
    output=Path(output) if output else ROOT/'reports/installed-quality-scan.json'
    save(output,dict(rule='≥4px压暗直线：严格检查调色前后新增分界；原生成图光影候选保留列表，供审片。新待机强制拒收，初代/杰顿待机仅报告。',frames=rows,idles=idles,errors=errors))
    for r in idles:
        if r['issues']:print(r['fighter']+'待机'+('（只报告，未改动）' if r['report_only'] else '（阻塞）')+'：'+'；'.join(r['issues']))
    if errors:
        print('\n'.join(errors[:30]));raise SystemExit(1)
    print('LIMB_IDLE_RESOURCES PASS：正式帧没有新增直角压暗遮罩；原图光影候选与旧待机问题见扫描报告。')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path)
    main(parser.parse_args().output)

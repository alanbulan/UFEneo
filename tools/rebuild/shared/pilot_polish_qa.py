"""本轮已批准派生帧的严格配准检查；旧短尺只作定位，不改变其他帧的检查。"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import hashlib
from pathlib import Path
Path = _LayoutProjectPath
from PIL import Image
import head_fit as hf
from pilot_polish_install import ROOT, ART, OUT, APPROVAL, read, digest, pixel_sha, manifest_path


def text_fingerprint_matches(data, expected):
    """历史指纹保留原字节，仅兼容Git的LF/CRLF转换，不忽略内容改动。"""
    normalized = data.replace(b'\r\n', b'\n')
    return expected in {hashlib.sha256(value).hexdigest()
                        for value in (data, normalized, normalized.replace(b'\n', b'\r\n'))}


def validate_registered_head(folder, fighter, document, row):
    folder = Path(folder).resolve()
    relative = folder.relative_to((ART/'installed').resolve())
    if len(relative.parts) != 2 or relative.parts[0] != fighter:
        raise ValueError('头部配准派生源不属于本轮角色目录')
    action = relative.parts[1]
    base = read(OUT/'precheck.json')
    choice = next((c for c in base['selection'] if c['character']==fighter and c['action']==action
                   and c['status']=='批准安装' and row['frame'] in c['frames']), None)
    if choice is None or document.get('head_polish',{}).get('approval') != APPROVAL:
        raise ValueError('该帧没有本轮连续性安装授权')
    if not text_fingerprint_matches((hf.CONFIG/f'{fighter}.json').read_bytes(), base['configs'][fighter]):
        raise ValueError('配准配置相对安装核对已变化')
    plan_path = ART/'scale-plan.json'
    if not text_fingerprint_matches(plan_path.read_bytes(), base['source_sha256'][str(plan_path.relative_to(ROOT)).replace('\\','/')]):
        raise ValueError('已审缩放方案指纹变化')
    frame = read(plan_path)['characters'][fighter]['actions'][action]['frames'][row['frame']]
    candidate = ROOT/frame['candidate']
    if digest(candidate) != base['candidates'][frame['candidate']]:
        raise ValueError('已审候选指纹变化')
    image = Image.open(folder/row['image']).convert('RGBA')
    if pixel_sha(image) != frame['candidate_pixel_sha256']:
        raise ValueError('派生帧像素不等于已审整帧候选')
    manifest = read(manifest_path(fighter))
    idle = manifest['clips']['idle']
    if digest(ROOT/idle['texture'].removeprefix('res://')) != base['manifests'][fighter]['clips']['idle']['atlas_sha256']:
        raise ValueError('idle参考图集变化，必须重新计算中位数')
    after = read(OUT/'head-fit-after.json')
    saved = next(r for r in after['changed_frames'] if r['character']==fighter and r['action']==action and r['frame']==row['frame'])
    measured = hf.measure(fighter, image, center=saved['center'])
    normalized = measured['scale']/after['idle_medians'][fighter] if measured['scale'] is not None else None
    if measured['grade'] != '可用' or normalized is None or not .92 <= normalized <= 1.08:
        raise ValueError(f'安装帧整头配准超差或不可测：{fighter}/{action}#{row["frame"]} {normalized}')
    return dict(character=fighter, action=action, frame=row['frame'], normalized_head=normalized,
                grade=measured['grade'], candidate_pixels_unchanged=True,
                authority=APPROVAL, method='本轮已批准帧实际重跑head_fit，idle中位数归一；不使用旧短尺替代整头')

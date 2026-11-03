"""按指挥连续性白名单增量安装既有整帧候选；不生图、不改模拟数据。"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import copy
import csv
import hashlib
import json; json = _LayoutJson
import math
import os
from pathlib import Path
Path = _LayoutProjectPath
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw

import head_fit as hf
from forge_backend import backend_info, binarize_alpha, palette_mode
from pilot_polish_candidates import anchor, pixel_sha

ROOT = hf.ROOT
SOURCE = ROOT / 'reports/review/2026-10-23/pilot-head-polish'
ART = ROOT / 'art/shared/production/pilot-polish'
OUT = ROOT / 'reports/review/2026-10-23/pilot-head-polish-install'
IDS = ('ultraman', 'ultraseven', 'zetton', 'gomora')
APPROVAL = '指挥目视通过（2026-10-23，头部配准缩放）'
QA_EXCEPTIONS = {f'assets/fighters/ultraseven/animations/{a}/slugger-qa.json'
                 for a in ('motion_236', 'motion_41236', 'special', 'special3')}


def rel(path):
    return Path(path).relative_to(ROOT).as_posix()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return hf.read_json(path)


def save(path, value):
    hf.save_json(path, value)


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8').strip()


def manifest_path(cid):
    return ROOT / f'assets/fighters/{cid}/animations/manifest.json'


def runtime_fingerprints():
    return {rel(p): digest(p) for cid in IDS
            for base in (ROOT / f'assets/fighters/{cid}', ROOT / f'content/fighters/{cid}')
            for p in sorted(base.rglob('*'))
            if p.is_file() and p.suffix not in ('.import', '.uid')
            and rel(p) not in QA_EXCEPTIONS}


def decisions():
    rows = read(SOURCE / 'decisions.json')
    with (SOURCE / 'continuity-review.csv').open(encoding='utf-8-sig', newline='') as f:
        edges = list(csv.DictReader(f))
    grouped = defaultdict(list)
    for row in rows:
        if row['status'] == '缩放可修':
            grouped[row['character'], row['action']].append(row['frame'])
    results = []
    for (cid, action), frames in sorted(grouped.items()):
        adjacent = [x for x in edges if x['character'] == cid and x['action'] == action]
        reasons = []
        assert adjacent, (cid, action, '连续性清单缺项')
        for edge in adjacent:
            label = f"#{edge['from_frame']}→#{edge['to_frame']}"
            after = edge['head_step_proposed_percent']
            before = edge['head_step_before_percent']
            if not after or not before:
                reasons.append(label + '邻帧头读数不可用')
            elif float(after) > 8:
                reasons.append(f'{label}相邻头差{float(before):.2f}%→{float(after):.2f}%，超过8%')
            elif float(after) > float(before) + 1e-8:
                reasons.append(f'{label}相邻头差{float(before):.2f}%→{float(after):.2f}%，比原来更大')
        results.append(dict(character=cid, action=action, frames=frames,
                            status='暂缓整招' if reasons else '批准安装',
                            reasons=reasons, edges=adjacent))
    return rows, results


def precheck():
    path = OUT / 'precheck.json'
    if path.exists():
        raise FileExistsError('安装前核对已存盘，勿覆盖')
    owned = [f'{base}/{cid}' for base in ('assets/fighters', 'content/fighters') for cid in IDS]
    dirty = git('diff', '--name-only', '--', *owned).splitlines()
    staged = git('diff', '--cached', '--name-only', '--', *owned).splitlines()
    untracked = git('ls-files', '--others', '--exclude-standard', '--', *owned).splitlines()
    unexpected = (set(dirty) | set(staged) | set(untracked)) - QA_EXCEPTIONS
    if unexpected:
        raise RuntimeError('分配路径发现非质检副产物改动：' + ', '.join(sorted(unexpected)))
    snapshot = read(SOURCE / 'audit/snapshot.json')
    for cid, old in snapshot['characters'].items():
        assert digest(manifest_path(cid)) == old['manifest_sha256'], cid + '运行清单相对方案已变化'
        for source, expected in old['textures'].items():
            assert digest(ROOT / source) == expected, source + '相对方案已变化'
        assert digest(hf.CONFIG / f'{cid}.json') == digest(SOURCE / f'audit/inputs/configs/{cid}.json')
    rows, selection = decisions()
    assert Counter(r['status'] for r in rows) == {'缩放可修': 20, '需重画': 95, '读数不可用': 10}
    plan = read(ART / 'scale-plan.json')
    baseline = dict(git_head=git('rev-parse', 'HEAD'), art_source='existing', image_requests=0,
                    approval=APPROVAL, selection=selection,
                    source_sha256={rel(p): digest(p) for p in (
                        ART / 'scale-plan.json', SOURCE / 'decisions.json',
                        SOURCE / 'continuity-review.csv', SOURCE / 'audit/snapshot.json')},
                    runtime_fingerprints=runtime_fingerprints(),
                    ignored_qa={p: digest(ROOT / p) for p in sorted(QA_EXCEPTIONS)},
                    manifests={cid: read(manifest_path(cid)) for cid in IDS},
                    candidates={}, configs={cid: digest(hf.CONFIG / f'{cid}.json') for cid in IDS})
    for choice in selection:
        if choice['status'] != '批准安装':
            continue
        cid, action = choice['character'], choice['action']
        clip = baseline['manifests'][cid]['clips'][action]
        p = plan['characters'][cid]['actions'][action]
        assert p['padding'] == [0, 0, 0, 0], '本批无需改画布；扩边须单独复核'
        assert p['ticks'] == clip['ticks'] and p['loop'] == clip['loop']
        before = OUT / f'before/{cid}/{action}.png'
        before.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / clip['texture'].removeprefix('res://'), before)
        for i in choice['frames']:
            row = p['frames'][i]
            im = Image.open(ROOT / row['candidate']).convert('RGBA')
            assert pixel_sha(im) == row['candidate_pixel_sha256']
            assert row['anchor'] == anchor(baseline['manifests'][cid], clip, i) == row['source_anchor']
            assert row['head_after']['grade'] == '可用'
            assert .92 <= row['head_after']['normalized_head'] <= 1.08
            baseline['candidates'][row['candidate']] = digest(ROOT / row['candidate'])
    save(path, baseline)
    hf.write_csv(OUT / 'installation-selection.csv', selection,
                 ['character', 'action', 'frames', 'status', 'reasons'])
    print('安装前核对已存盘；批准：' + '、'.join(
        f"{r['character']}/{r['action']} {r['frames']}" for r in selection if r['status'] == '批准安装'))


def install(cid, action):
    base = read(OUT / 'precheck.json')
    choice = next(x for x in base['selection'] if x['character'] == cid and x['action'] == action)
    assert choice['status'] == '批准安装', '动作未通过连续性条件'
    for p, expected in base['source_sha256'].items():
        assert digest(ROOT / p) == expected, '方案输入变化'
    mp = manifest_path(cid)
    m = read(mp)
    original = base['manifests'][cid]['clips'][action]
    assert m['clips'][action] == original, '动作已变化或已安装'
    target = ROOT / original['texture'].removeprefix('res://')
    assert digest(target) == original['atlas_sha256']
    assert [a for a, c in m['clips'].items() if c['texture'] == original['texture']] == [action], '共享图集须复核所有别名'
    atlas = Image.open(target).convert('RGBA')
    frames = read(ART / 'scale-plan.json')['characters'][cid]['actions'][action]['frames']
    for i in choice['frames']:
        row = frames[i]
        candidate_path = ROOT / row['candidate']
        assert digest(candidate_path) == base['candidates'][row['candidate']]
        before = hf.crop_frame(atlas, original['rects'][i])
        assert pixel_sha(before) == row['source_pixel_sha256']
        im = Image.open(candidate_path).convert('RGBA')
        clean = im.copy()
        with palette_mode('rgb'):
            binarize_alpha(clean)
        assert pixel_sha(clean) == pixel_sha(im), '候选不是既有规范真透明像素'
        assert list(im.size) == original['rects'][i][2:]
        x, y, w, h = original['rects'][i]
        atlas.paste(im, (x, y))
    folder = OUT / f'actions/{cid}/{action}'
    folder.mkdir(parents=True, exist_ok=True)
    baked = folder / 'atlas.png'
    atlas.save(baked)
    archive = (ROOT.parent / f'UFEneo_archive/2026-10-23/pilot-head-polish-install/{cid}/{action}').resolve()
    archive.relative_to((ROOT.parent / 'UFEneo_archive/2026-10-23/pilot-head-polish-install').resolve())
    archive.mkdir(parents=True, exist_ok=True)
    old = archive / (target.stem + '-' + digest(target)[:12] + '.png')
    assert not old.exists(), '不覆盖归档'
    shutil.copy2(target, old)
    shutil.copy2(baked, target)
    clip = copy.deepcopy(original)
    clip['atlas_sha256'] = digest(target)
    clip['head_polish'] = dict(date='2026-10-23', approval=APPROVAL,
                               changed_frames=choice['frames'],
                               source_plan=rel(ART / 'scale-plan.json'), report=rel(folder / 'installation.json'),
                               previous_atlas_sha256=original['atlas_sha256'],
                               previous_motion_review=original.get('motion_review', {}),
                               anchor_unchanged=True, simulation_unchanged=True)
    clip['motion_review'] = dict(original.get('motion_review', {}), user_approved=True,
                                commander_approved=True, date='2026-10-23', verdict=APPROVAL,
                                atlas_sha256=clip['atlas_sha256'], approved_atlas_sha256=clip['atlas_sha256'],
                                approval_scope_frames=choice['frames'], report=rel(OUT / 'README.md'))
    m['clips'][action] = clip
    save(mp, m)
    save(folder / 'installation.json', dict(choice, approval=APPROVAL, before=original, after=clip,
                                           archived_original=str(old), backend=backend_info(),
                                           art_source='existing', image_requests=0,
                                           method='原图集布局烘图，仅替换白名单完整帧；rects和anchors逐项核对未变'))
    print(f'已安装 {cid}/{action} {choice["frames"]}，时长、rects、根点及模拟数据不变')


def fit_task(task):
    cid, action, i, image, center, median = task
    result = hf.measure(cid, image, center=center)
    result.update(character=cid, action=action, frame=i,
                  normalized_head=result['scale'] / median if result['scale'] is not None else None)
    return result


def verify_heads():
    base = read(OUT / 'precheck.json')
    plan = read(ART / 'scale-plan.json')
    jobs = []
    for cid in sorted({c['character'] for c in base['selection'] if c['status'] == '批准安装'}):
        original = read(SOURCE / f'audit/results/{cid}.json')
        idle_rows = {r['frame']: r for r in original['frames'] if r['action'] == 'idle'}
        m = read(manifest_path(cid))
        atlas = Image.open(ROOT / m['clips']['idle']['texture'].removeprefix('res://')).convert('RGBA')
        median = plan['characters'][cid]['idle_median']
        for i, rect in enumerate(m['clips']['idle']['rects']):
            jobs.append((cid, 'idle', i, hf.crop_frame(atlas, rect), idle_rows[i]['center'], median))
        for choice in base['selection']:
            if choice['character'] != cid or choice['status'] != '批准安装':
                continue
            action = choice['action']
            clip = m['clips'][action]
            atlas = Image.open(ROOT / clip['texture'].removeprefix('res://')).convert('RGBA')
            for i, rect in enumerate(clip['rects']):
                row = plan['characters'][cid]['actions'][action]['frames'][i]
                reference = row['head_after'] if i in choice['frames'] else row['head_before']
                jobs.append((cid, action, i, hf.crop_frame(atlas, rect), reference['center'], median))
    with ProcessPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(fit_task, jobs))
    medians = {cid: float(np.median([r['scale'] for r in results
                                   if r['character'] == cid and r['action'] == 'idle' and r['grade'] == '可用']))
               for cid in {r['character'] for r in results}}
    for r in results:
        r['normalized_head'] = r['scale'] / medians[r['character']] if r['scale'] is not None else None
    changed = []
    for choice in base['selection']:
        if choice['status'] != '批准安装':
            continue
        cid, action = choice['character'], choice['action']
        readings = {r['frame']: r for r in results if r['character'] == cid and r['action'] == action}
        for i in choice['frames']:
            row = readings[i]
            assert row['grade'] == '可用' and .92 <= row['normalized_head'] <= 1.08, row
            changed.append(row)
        for edge in choice['edges']:
            a, b = readings[int(edge['from_frame'])], readings[int(edge['to_frame'])]
            assert a['grade'] == b['grade'] == '可用'
            step = abs(b['normalized_head'] / a['normalized_head'] - 1) * 100
            assert step <= 8 and step <= float(edge['head_step_before_percent']) + 1e-8, (cid, action, step)
    save(OUT / 'head-fit-after.json', dict(tool='tools/rebuild/shared/head_fit.py:measure',
         idle_medians=medians, frames=results, changed_frames=changed, configs_unchanged=True))
    hf.write_csv(OUT / 'head-fit-after.csv', results,
                 ['character', 'action', 'frame', 'scale', 'normalized_head', 'grade', 'score', 'center'])
    assert all(digest(hf.CONFIG / f'{cid}.json') == base['configs'][cid] for cid in IDS)
    print('安装后整头配准和邻帧复测完成；修改帧归一读数：' + '、'.join(
        f"{r['character']}/{r['action']}#{r['frame']}={r['normalized_head']:.4f}" for r in changed))


def validate():
    base = read(OUT / 'precheck.json')
    allowed = set()
    frame_checks = []
    for cid in IDS:
        before = base['manifests'][cid]
        after = read(manifest_path(cid))
        choices = {c['action']: c for c in base['selection'] if c['character'] == cid and c['status'] == '批准安装'}
        assert before.keys() == after.keys() and before['clips'].keys() == after['clips'].keys()
        assert {k: v for k, v in before.items() if k != 'clips'} == {k: v for k, v in after.items() if k != 'clips'}
        if choices:
            allowed.add(rel(manifest_path(cid)))
        for action, old in before['clips'].items():
            new = after['clips'][action]
            if action not in choices:
                assert old == new, (cid, action, '未授权清单变化')
                continue
            metadata_keys = ('motion_review', 'atlas_sha256', 'head_polish', 'head_qa', 'curation', 'slugger_qa')
            assert {k: v for k, v in old.items() if k not in metadata_keys} == {
                k: v for k, v in new.items() if k not in metadata_keys}
            target = ROOT / new['texture'].removeprefix('res://')
            allowed.add(rel(target))
            assert digest(target) == new['atlas_sha256']
            old_atlas = Image.open(OUT / f'before/{cid}/{action}.png').convert('RGBA')
            new_atlas = Image.open(target).convert('RGBA')
            assert old_atlas.size == new_atlas.size
            for i in range(len(old['rects'])):
                a, b = hf.crop_frame(old_atlas, old['rects'][i]), hf.crop_frame(new_atlas, new['rects'][i])
                changed = pixel_sha(a) != pixel_sha(b)
                assert changed == (i in choices[action]['frames']), (cid, action, i, '白名单帧不符')
                frame_checks.append(dict(character=cid, action=action, frame=i, changed=changed,
                                         before_pixel_sha256=pixel_sha(a), after_pixel_sha256=pixel_sha(b),
                                         anchor_before=anchor(before, old, i), anchor_after=anchor(after, new, i),
                                         ground_offset_before=a.getbbox()[3]-anchor(before, old, i)[1],
                                         ground_offset_after=b.getbbox()[3]-anchor(after, new, i)[1]))
    current = runtime_fingerprints()
    assert current.keys() == base['runtime_fingerprints'].keys()
    actual = {p for p, h in current.items() if h != base['runtime_fingerprints'][p]}
    assert actual == allowed, ('白名单外运行资源或模拟数据变化', sorted(actual ^ allowed))
    ignored = {p: digest(ROOT / p) for p in QA_EXCEPTIONS}
    save(OUT / 'runtime-validation.json', dict(allowed_changed_paths=sorted(allowed),
         content_unchanged=True, all_other_runtime_unchanged=True, frames=frame_checks,
         qa_side_effects_untouched=ignored == base['ignored_qa'],
         qa_side_effect_policy='指挥允许保留的四份verify副产物只记指纹，不提交、不还原，不作为资源阻塞',
         ignored_qa_before=base['ignored_qa'], ignored_qa_after=ignored,
         current_fingerprints=current, baseline_fingerprints=base['runtime_fingerprints']))
    print('白名单、帧数、时长、rects、根点、模拟数据及旧质检副产物指纹已核对')


def strips():
    base = read(OUT / 'precheck.json')
    fits = read(OUT / 'head-fit-after.json')['frames']
    old_results = {cid: read(SOURCE / f'audit/results/{cid}.json') for cid in IDS}
    plan = read(ART / 'scale-plan.json')
    for choice in base['selection']:
        if choice['status'] != '批准安装':
            continue
        cid, action = choice['character'], choice['action']
        before_m = base['manifests'][cid]
        after_m = read(manifest_path(cid))
        clip = before_m['clips'][action]
        old_atlas = Image.open(OUT / f'before/{cid}/{action}.png').convert('RGBA')
        new_atlas = Image.open(ROOT / clip['texture'].removeprefix('res://')).convert('RGBA')
        idle_c = after_m['clips']['idle']
        idle = hf.crop_frame(Image.open(ROOT / idle_c['texture'].removeprefix('res://')).convert('RGBA'), idle_c['rects'][0])
        idle_anchor = anchor(after_m, idle_c, 0)
        old_frames = [hf.crop_frame(old_atlas, r) for r in clip['rects']]
        new_frames = [hf.crop_frame(new_atlas, r) for r in clip['rects']]
        all_frames = [idle] + old_frames
        all_anchors = [idle_anchor] + [anchor(before_m, clip, i) for i in range(len(old_frames))]
        left = max(a[0] for a in all_anchors)
        right = max(im.width-a[0] for im, a in zip(all_frames, all_anchors))
        top = max(a[1] for a in all_anchors)
        bottom = max(im.height-a[1] for im, a in zip(all_frames, all_anchors))
        w, h = math.ceil(left+right+16), math.ceil(top+bottom+8)
        native = Image.new('RGB', (w*(len(old_frames)+1), (h+22)*2), '#202632')
        draw = ImageDraw.Draw(native)
        for line, images in enumerate((old_frames, new_frames)):
            for col, im in enumerate([idle]+images):
                ax, ay = all_anchors[col]
                x, y = col*w, line*(h+22)
                draw.line((x, y+22+top, x+w, y+22+top), fill='#6d7381')
                native.paste(im, (int(x+8+left-ax), int(y+22+top-ay)), im)
                label = 'idle' if col == 0 else f'#{col-1}'+(' *' if col-1 in choice['frames'] else '')
                draw.text((x+3, y+2), ('before ' if line == 0 else 'after ')+label, fill='white')
        folder = OUT / f'actions/{cid}/{action}'
        native.save(folder / 'body-before-after-native.png')
        native.resize((native.width*4, native.height*4), Image.Resampling.NEAREST).save(folder / 'contact-x4.png')
        heads = Image.new('RGB', ((len(old_frames)+1)*64*8, 2*(64*8+36)), '#202632')
        d = ImageDraw.Draw(heads)
        idle_reading = next(r for r in old_results[cid]['frames'] if r['action']=='idle' and r['frame']==0)
        for line, images in enumerate((old_frames, new_frames)):
            for col, im in enumerate([idle]+images):
                if col == 0:
                    r = idle_reading
                    normalized = r['scale']/plan['characters'][cid]['idle_median']
                else:
                    r = next(r for r in (old_results[cid]['frames'] if line==0 else fits)
                             if r.get('character',cid)==cid and r['action']==action and r['frame']==col-1)
                    normalized = r['scale']/plan['characters'][cid]['idle_median'] if r['scale'] is not None else None
                crop = hf.head_crop(im, r['center'], 64, 64)
                tile = crop.resize((512,512), Image.Resampling.NEAREST)
                x, y = col*512, line*548
                heads.paste(tile, (x,y+36))
                d.text((x+8,y+5), ('before ' if line==0 else 'after ')+('idle' if col==0 else f'#{col-1}')+f' H={normalized:.4f}' if normalized else 'NA', font=hf.font(18), fill='white')
        heads.save(folder / 'heads-x8.png')
        hf.jpeg_preview(native, folder / 'body-preview.jpg')
        hf.jpeg_preview(heads, folder / 'heads-preview.jpg')
        save(folder / 'strip-coverage.json', dict(frames=list(range(len(old_frames))),
             rows=['idle + 修改前全部帧', 'idle + 修改后全部帧'], body_scale=1, contact_scale=4,
             head_scale=8, common_ground=True, same_native_scale_across_all_actions=True))
    print('全相位同原生比例、四倍联系表和头部八倍条带已保存')


def install_remaining():
    assert (ROOT / 'art/shared/locks/godot.lock').exists(), '批量安装提交必须持Godot锁'
    base = read(OUT / 'precheck.json')
    names = {'ultraman':'初代', 'ultraseven':'赛文', 'gomora':'哥莫拉'}
    completed = 0
    for choice in base['selection']:
        if choice['status'] != '批准安装':
            continue
        cid, action = choice['character'], choice['action']
        record = OUT / f'actions/{cid}/{action}/installation.json'
        if record.exists():
            continue
        install(cid, action)
        clip = read(manifest_path(cid))['clips'][action]
        paths = [rel(manifest_path(cid)), clip['texture'].removeprefix('res://'),
                 rel(record.parent)]
        subprocess.run(['git', 'add', '-f', '--', *paths], cwd=ROOT, check=True)
        subprocess.run(['git', 'commit', '-m',
                        f'安装{names[cid]}{action}整帧头部配准缩放', '--', *paths], cwd=ROOT, check=True)
        completed += 1
        if completed % 3 == 0:
            thread = os.environ.get('CODEX_THREAD_ID', '')
            logs = list((Path.home()/'.codex/sessions/2026/10/23').glob(f'rollout-*-{thread}.jsonl'))
            if logs:
                size = max(p.stat().st_size for p in logs)
                print(f'会话体积 {size / 1024**2:.2f} MiB', flush=True)
                assert size <= 12*1024**2, '会话体积到上限，先更新HANDOFF并交接'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['precheck', 'install', 'remaining', 'heads', 'validate', 'strips'])
    parser.add_argument('--character', choices=IDS)
    parser.add_argument('--action')
    args = parser.parse_args()
    if args.command == 'install':
        install(args.character, args.action)
    else:
        {'precheck': precheck, 'remaining': install_remaining, 'heads': verify_heads,
         'validate': validate, 'strips': strips}[args.command]()


if __name__ == '__main__':
    main()

"""把哥莫拉冲刺三段装成模拟使用的22tick时间线，不改通用表现层。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import copy
import json; json = _LayoutJson
import os

from gomora_qa import ROOT, WORK, OUT, read, save, sha, rel

PARTS = ['dash_start', 'dash', 'dash_stop']


def atomic_save(path, data, expected):
    assert sha(path) == expected, '文件在读取后被其他会话改动，停止写入：'+str(path)
    temporary = path.with_name(path.name+'.gomora-dash.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', 'utf-8')
    os.replace(temporary, path)


def assemble():
    mp = ROOT/'assets/fighters/gomora/animations/manifest.json'
    sp = ROOT/'content/fighters/gomora/state_frames.json'
    before = {rel(p): sha(p) for p in [mp, sp]}
    manifest, states = read(mp), read(sp)
    if not all(p in manifest['clips'] and p in states for p in PARTS):
        return False
    old_manifest, old_states = copy.deepcopy(manifest), copy.deepcopy(states)
    durations = [sum(manifest['clips'][p]['ticks']) for p in PARTS]
    assert durations == [4, 12, 6]
    if len(states['dash']) == sum(durations):
        run = copy.deepcopy(states['dash'][durations[0]:sum(durations[:2])])
        for row in run:
            row['sprite'] -= len(manifest['clips']['dash_start']['rects'])
    else:
        run = copy.deepcopy(states['dash'])
    parts = [copy.deepcopy(states['dash_start']), run, copy.deepcopy(states['dash_stop'])]
    combined, offset = [], 0
    for key, local, duration in zip(PARTS, parts, durations):
        clip = manifest['clips'][key]
        assert len(local) == duration
        assert [r['sprite'] for r in local] == [i for i, t in enumerate(clip['ticks']) for _ in range(t)]
        for row in local:
            row['sprite'] += offset
        combined.extend(local)
        clip['simulation_sprite_offset'] = offset
        offset += len(clip['rects'])
    states['dash'] = combined
    assert len(combined) == 22 and offset == 9
    assert {k:v for k,v in states.items() if k != 'dash'} == {k:v for k,v in old_states.items() if k != 'dash'}
    for key in old_manifest['clips']:
        actual = copy.deepcopy(manifest['clips'][key])
        if key in PARTS:
            actual.pop('simulation_sprite_offset', None)
            old = copy.deepcopy(old_manifest['clips'][key]);old.pop('simulation_sprite_offset', None)
        else:
            old = old_manifest['clips'][key]
        assert actual == old
    atomic_save(sp, states, before[rel(sp)])
    atomic_save(mp, manifest, before[rel(mp)])
    assert read(sp)['dash'] == combined and read(mp) == manifest
    save(WORK/'dash/runtime-assembly.json', dict(
        before=before, after={rel(p):sha(p) for p in [mp,sp]}, durations=durations,
        offsets=[manifest['clips'][p]['simulation_sprite_offset'] for p in PARTS],
        sprites=[r['sprite'] for r in combined], other_states_unchanged=True,
        atlas_unchanged=True, note='沿用现有九张GPT整帧和既有时间；原dash只有跑步12tick，导致统一采样跳过跑步首帧与刹停前两帧。'))
    print('哥莫拉冲刺：起步2＋跑步4＋刹停3，22tick完整模拟时间线。')
    return True


if __name__ == '__main__':
    assemble()

"""四个试制角色的只读复测；不校准、不改动运行资源。"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson

import argparse
import hashlib
import json; json = _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath

import head_fit as hf

ROOT = hf.ROOT
IDS = ('ultraman', 'ultraseven', 'zetton', 'gomora')
OUT = ROOT / 'reports/review/2026-10-23/pilot-head-polish'
ART = ROOT / 'art/shared/production/pilot-polish'
OLD = ROOT / 'reports/review/2026-10-23/head-fit-audit'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--workers', type=int, default=4)
    args = ap.parse_args()
    audit = OUT / 'audit'
    audit.mkdir(parents=True, exist_ok=True)
    # 原始字节快照的SHA必须不受Git换行转换影响；PNG继承根目录LFS规则。
    (OUT / '.gitattributes').write_text('audit/inputs/** -text -whitespace\n', encoding='utf-8')
    if not (audit / 'snapshot.json').exists():
        hf.snapshot(audit, IDS)
    baseline = {cid: digest(hf.CONFIG / f'{cid}.json') for cid in IDS}
    calibration = hf.read_json(OLD / 'calibration/summary.json')
    if not calibration['passed'] or calibration['algorithm_sha256'] != hf.algorithm_hash():
        raise RuntimeError('现有校准与配准算法不一致，不能在本轮改配置校准')
    for cid in IDS:
        original = hf.read_json(OLD / f'results/{cid}.json')['summary']
        if original['config_semantic_sha256'] != hf.config_hash(hf.config_for(cid)):
            raise RuntimeError(f'{cid} 配置已改变，现有校准不可复用')
        target = audit / f'inputs/configs/{cid}.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((hf.CONFIG / f'{cid}.json').read_bytes())
    hf.save_json(audit / 'calibration/summary.json', calibration)
    hf.save_json(audit / 'calibration/reuse.json', {
        'source': str((OLD / 'calibration/summary.json').relative_to(ROOT)),
        'source_sha256': digest(OLD / 'calibration/summary.json'),
        'reason': '配准算法及四角色配置语义指纹完全相同；沿用校准，不写配置；全部帧重新计算',
        'configs_before': baseline,
    })
    hf.audit(audit, IDS, args.workers)
    after = {cid: digest(hf.CONFIG / f'{cid}.json') for cid in IDS}
    if after != baseline:
        raise RuntimeError('复测期间配置发生变化')
    hf.save_json(audit / 'config-unchanged.json', {'before': baseline, 'after': after, 'unchanged': True})


if __name__ == '__main__':
    main()

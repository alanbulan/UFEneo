"""根串行真实step空地投规则探针；先旧核baseline，再由根明确应用补丁。"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'project.godot').is_file())
sys.path.insert(0, str(ROOT / 'tools'))
from verify import godot_path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def sources():
    files = [ROOT / 'project.godot', Path(__file__), Path(__file__).with_name('throw_target_step_regression.gd')]
    for folder in ['core', 'content', 'input']:
        files += [p for p in (ROOT / folder).rglob('*') if p.is_file() and p.suffix in ['.gd', '.json', '.tres']]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(set(files))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', action='store_true')
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--baseline-file', type=Path)
    args = parser.parse_args()
    assert (ROOT / 'art/shared/locks/godot.lock').is_file(), '须根持唯一Godot锁'
    out = args.out.resolve()
    assert out.is_relative_to(ROOT) and not out.exists(), '新输出目录，不覆盖失败'
    contract = json.loads((ROOT / 'reports/review/2026-11-02/gomora-super3-back-lift-throw-target-patch-v1/patch-contract.json').read_text('utf-8-sig'))
    for item in contract['files']:
        expected = item['before_sha256' if args.baseline else 'proposed_sha256']
        assert digest(ROOT / item['path']) == expected, '产品不符合本次精确前后合同：' + item['path']
    frozen = sources()
    out.mkdir(parents=True)
    save(out / 'source-before.json', frozen)
    options = ['--baseline'] if args.baseline else ['--throw-target-baseline=' + str(args.baseline_file.resolve())]
    command = [str(godot_path()), '--headless', '--path', str(ROOT), '--script',
               'res://tools/rebuild/gomora/super3_back_lift_contract_20261102_v1/throw_target_step_regression.gd',
               '--', '--throw-target-out=' + str(out), *options]
    with (out / 'engine.log').open('xb') as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=90)
    diagnostics = [line for line in (out / 'engine.log').read_text('utf-8', errors='replace').splitlines()
                   if any(token in line for token in ['SCRIPT ERROR:', 'Parse Error:', 'ERROR:', 'WARNING:', 'FAIL '])]
    after = sources()
    save(out / 'source-after.json', after)
    evidence = dict(exit_code=result.returncode, diagnostics=diagnostics, source_bytes_held=frozen == after,
                    baseline=args.baseline, generated_videos=0, product_installed=False)
    save(out / 'root-run-result.json', evidence)
    print(json.dumps(evidence, ensure_ascii=False), flush=True)
    assert result.returncode == 0 and not diagnostics and frozen == after


if __name__ == '__main__':
    main()

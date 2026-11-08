"""Check publishable files, source aliases, credentials and runtime resource paths."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SKIP = {'.git', '.godot', '.venv', '.tools', '.references', '__pycache__', 'node_modules', 'reports'}
TEXT = {'.py', '.gd', '.gdshader', '.json', '.md', '.txt', '.toml', '.yaml', '.yml', '.tscn', '.tres', '.command', '.sh', '.mjs', '.js', '.cfg'}
SECRETS = [
    re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
    re.compile(r'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}\b'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'(?i)["\']authorization["\']\s*:\s*["\']Bearer\s+[A-Za-z0-9._-]{20,}'),
]


def iter_files(directory: Path):
    for p in directory.iterdir():
        if p.name in SKIP or p.is_symlink():
            continue
        if p.is_dir():
            yield from iter_files(p)
        elif p.is_file():
            yield p


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-source-hashes', action='store_true')
    args = parser.parse_args()
    errors = []
    warnings = []
    files = list(iter_files(ROOT))
    total = sum(p.stat().st_size for p in files)
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        if p.stat().st_size > 95 * 1024 * 1024:
            errors.append({'path': rel, 'reason': 'file larger than the clean repository limit'})
        if p.name == '.gitattributes' and p.parent != ROOT:
            errors.append({'path': rel, 'reason': 'nested attributes override'})
        if p.suffix in ('.avi', '.mp4', '.mkv', '.zip', '.7z', '.dpapi') or p.name.startswith('.env'):
            errors.append({'path': rel, 'reason': 'local/generated/private artifact'})
        if p.suffix not in TEXT or p.stat().st_size > 16 * 1024 * 1024:
            continue
        text = p.read_text('utf-8-sig', errors='replace')
        if any(pattern.search(text) for pattern in SECRETS):
            # Never print the matching secret itself.
            errors.append({'path': rel, 'reason': 'credential pattern'})
        if p.suffix in ('.gd', '.tscn', '.tres') and rel.startswith(('app/', 'core/', 'input/', 'ui/', 'presentation/', 'tests/')):
            for reference in re.findall(r'["\'](res://[^"\']+)["\']', text):
                if '%' in reference or not reference.endswith(('.gd', '.gdshader', '.tscn', '.tres', '.png', '.wav', '.otf')):
                    continue
                if reference.startswith(('res://reports/', 'res://art/', 'res://audio/')):
                    continue  # Historical output paths or optional authoring sources.
                if not (ROOT / reference.removeprefix('res://')).is_file():
                    errors.append({'path': rel, 'reason': 'missing static resource', 'resource': reference})
    index = json.loads((ROOT / 'art/source-index.json').read_text('utf-8'))
    for old, new in index['aliases'].items():
        target = ROOT / new
        if not target.is_file():
            errors.append({'path': old, 'reason': 'missing canonical source', 'resource': new})
    for record in index['files']:
        target = ROOT / record['path']
        if not target.is_file():
            errors.append({'path': record['path'], 'reason': 'missing source file'})
        elif not args.skip_source_hashes and hashlib.sha256(target.read_bytes()).hexdigest() != record['sha256']:
            errors.append({'path': record['path'], 'reason': 'source hash changed'})
    result = {'status': 'passed' if not errors else 'failed', 'files': len(files), 'bytes': total,
              'errors': errors, 'warnings': warnings, 'source_hashes_checked': not args.skip_source_hashes}
    output = ROOT / 'reports/verification'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'repository-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == '__main__':
    main()

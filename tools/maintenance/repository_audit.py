"""Check publishable files, workspace/branch hygiene, source-only Git tracking, directory layout, credentials and runtime resource paths."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SKIP = {
    '.git', '.godot', '.venv', '.tools', '.references',
    '.claude', '.cursor', '.codex', '.agent', '.godot_ai_update',
    '__pycache__', 'node_modules', 'reports', '.DS_Store',
}
ROOT_DIRS = {
    'addons', 'app', 'art', 'assets', 'content', 'core', 'docs',
    'input', 'presentation', 'tests', 'third_party', 'tools', 'ui',
}
ROOT_FILES = {
    '.editorconfig', '.gitattributes', '.gitignore',
    'AGENTS.md', 'README.md', 'REBUILD_2D_PLAN.md',
    'project.godot', '开始游戏.command',
}
DOCS_ENTRIES = {'HANDBOOK.md', 'verification'}
ART_ENTRIES = {
    '.gdignore', 'STYLE.md', 'source-index.json',
    'audio', 'catalogue-rebuild-20261113', 'fighters', 'shared',
}
ALLOWED_TRACKED_ART = {'art/.gdignore', 'art/STYLE.md'}
FORBIDDEN_TRACKED_EXTS = {
    '.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.ico', '.ora', '.psd',
    '.wav', '.ogg', '.mp3', '.m4s', '.flac', '.aac',
    '.otf', '.ttf', '.woff', '.woff2',
}
TOOLS_ENTRIES = {
    '.gdignore', 'README.md', 'godot_lock.py', 'verify.py',
    'requirements-art.txt', 'requirements-checks.txt',
    'art', 'audio', 'check', 'maintenance', 'media', 'rebuild', 'roster', 'runtime',
}
ROOT_PARENTS_RE = re.compile(
    r'^\s*ROOT\s*=\s*(?:pathlib\.)?Path\(__file__\)\.resolve\(\)\.parents\[(\d+)\]',
    re.M,
)
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


def check_git_and_workspace_hygiene(errors: list[dict], *, allow_non_main_branch: bool) -> None:
    if (ROOT / '.claude/worktrees').exists():
        errors.append({'path': '.claude/worktrees', 'reason': 'forbidden agent worktree directory'})
    gitattr = ROOT / '.gitattributes'
    if gitattr.is_file() and 'filter=lfs' in gitattr.read_text('utf-8', errors='replace'):
        errors.append({'path': '.gitattributes', 'reason': 'git-lfs filter forbidden in source-only repository'})

    git_dir = ROOT / '.git'
    if git_dir.exists():
        worktrees_dir = git_dir / 'worktrees'
        if worktrees_dir.is_dir() and any(worktrees_dir.iterdir()):
            errors.append({'path': '.git/worktrees', 'reason': 'forbidden git worktree'})
        wt = subprocess.run(
            ['git', 'worktree', 'list', '--porcelain'],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        if wt.returncode == 0:
            wt_paths = [line.removeprefix('worktree ').strip() for line in wt.stdout.splitlines() if line.startswith('worktree ')]
            if len(wt_paths) > 1:
                errors.append({'path': '.git/worktrees', 'reason': 'multiple git worktrees active', 'worktrees': wt_paths})
        if not allow_non_main_branch:
            head = subprocess.run(
                ['git', 'symbolic-ref', '--short', '-q', 'HEAD'],
                cwd=ROOT, capture_output=True, text=True, check=False,
            ).stdout.strip()
            if head != 'main':
                errors.append({'path': head or 'DETACHED_HEAD', 'reason': 'active branch must be main'})
            branches = subprocess.run(
                ['git', 'for-each-ref', '--format=%(refname:short)', 'refs/heads'],
                cwd=ROOT, capture_output=True, text=True, check=False,
            ).stdout.splitlines()
            for branch in sorted(b.strip() for b in branches if b.strip() and b.strip() != 'main'):
                errors.append({'path': branch, 'reason': 'leftover local branch (merge into main and delete)'})
        tracked = subprocess.run(
            ['git', 'ls-files', '-z'],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        if tracked.returncode == 0:
            for rel in tracked.stdout.split('\0'):
                if not rel:
                    continue
                if rel.startswith('art/') and rel not in ALLOWED_TRACKED_ART:
                    errors.append({'path': rel, 'reason': 'art authoring file must not be tracked in Git'})
                elif Path(rel).suffix.lower() in FORBIDDEN_TRACKED_EXTS:
                    errors.append({'path': rel, 'reason': 'binary media file must not be tracked in Git'})

    known_ids = {p.name for p in (ROOT / 'content/fighters').iterdir() if p.is_dir()}
    catalog_path = ROOT / 'content/roster/catalog.json'
    if catalog_path.is_file():
        catalog = json.loads(catalog_path.read_text('utf-8-sig'))
        known_ids.update(row['id'] for row in catalog.get('entries', []) if isinstance(row, dict) and 'id' in row)
    try:
        for sibling in sorted(ROOT.parent.iterdir()):
            if sibling.name == ROOT.name or sibling.name.startswith('.') or not sibling.is_dir():
                continue
            if sibling.name in known_ids:
                errors.append({
                    'path': f'../{sibling.name}',
                    'reason': 'stray sibling fighter directory outside repository root',
                })
    except OSError:
        pass


def check_layout_whitelists(errors: list[dict]) -> None:
    for p in sorted(ROOT.iterdir()):
        if p.name in SKIP:
            continue
        if p.is_dir() and p.name not in ROOT_DIRS:
            errors.append({'path': p.name, 'reason': 'unexpected root directory'})
        elif p.is_file() and p.name not in ROOT_FILES:
            errors.append({'path': p.name, 'reason': 'unexpected root file'})

    for sub, allowed, label in (
        (ROOT / 'docs', DOCS_ENTRIES, 'unexpected docs entry (merge into docs/HANDBOOK.md)'),
        (ROOT / 'art', ART_ENTRIES, 'unexpected art top-level entry'),
        (ROOT / 'tools', TOOLS_ENTRIES, 'unexpected tools top-level entry'),
    ):
        if not sub.is_dir():
            continue
        for p in sorted(sub.iterdir()):
            if p.name in SKIP:
                continue
            if p.name not in allowed:
                errors.append({'path': p.relative_to(ROOT).as_posix(), 'reason': label})

    for p in sorted((ROOT / 'tools/rebuild').iterdir()):
        if p.name in SKIP:
            continue
        if not p.is_dir():
            errors.append({
                'path': p.relative_to(ROOT).as_posix(),
                'reason': 'loose file in tools/rebuild (use batch subdirectory or delete one-off script)',
            })

    for p in sorted((ROOT / 'tools').rglob('*.py')):
        if '__pycache__' in p.parts:
            continue
        text = p.read_text('utf-8-sig', errors='replace')
        for match in ROOT_PARENTS_RE.finditer(text):
            depth = int(match.group(1))
            parents = p.resolve().parents
            resolved = parents[depth] if depth < len(parents) else None
            if resolved != ROOT:
                errors.append({
                    'path': p.relative_to(ROOT).as_posix(),
                    'reason': f'ROOT parents[{depth}] resolves to {resolved}, expected {ROOT}',
                })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-source-hashes', action='store_true')
    parser.add_argument('--allow-non-main-branch', action='store_true')
    args = parser.parse_args()
    errors = []
    warnings = []
    check_git_and_workspace_hygiene(errors, allow_non_main_branch=args.allow_non_main_branch)
    check_layout_whitelists(errors)
    source_index_path = ROOT / 'art/source-index.json'
    has_local_media = source_index_path.is_file()
    files = list(iter_files(ROOT))
    total = sum(p.stat().st_size for p in files)
    checked_exts = ('.gd', '.gdshader', '.tscn', '.tres', '.png', '.wav', '.otf') if has_local_media else ('.gd', '.gdshader', '.tscn', '.tres')
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
                if '%' in reference or not reference.endswith(checked_exts):
                    continue
                if reference.startswith(('res://reports/', 'res://art/', 'res://audio/')):
                    continue  # Historical output paths or optional authoring sources.
                if not (ROOT / reference.removeprefix('res://')).is_file():
                    errors.append({'path': rel, 'reason': 'missing static resource', 'resource': reference})
    if has_local_media:
        index = json.loads(source_index_path.read_text('utf-8'))
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
              'errors': errors, 'warnings': warnings, 'local_media_present': has_local_media,
              'source_hashes_checked': has_local_media and not args.skip_source_hashes}
    output = ROOT / 'reports/verification'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'repository-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == '__main__':
    main()

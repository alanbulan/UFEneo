"""在 Godot 锁持有期间执行完整 verify 并立即留存本分支的日志和结果。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from datetime import datetime,timezone
import argparse
import hashlib
import json; json = _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import subprocess
import sys

ROOT=_LayoutProjectPath(_layout_root)
OUT=ROOT/'reports/review/2026-10-22/loop-repair'


def fingerprints(fighters):
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for f in fighters for base in [ROOT/f'assets/fighters/{f}',ROOT/f'content/fighters/{f}']
        for p in sorted(base.rglob('*')) if p.is_file() and p.suffix not in ['.import','.uid']}


def main():
    global OUT
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path);parser.add_argument('--fingerprint-fighters',nargs='*',choices=['ultraman','zetton'],default=[]);args=parser.parse_args()
    if args.output_dir:OUT=args.output_dir.resolve()
    OUT.mkdir(parents=True,exist_ok=True)
    command=[sys.executable,'-u',str(ROOT/'tools/verify.py'),'--keep-going']
    started=datetime.now(timezone.utc).isoformat()
    before=fingerprints(args.fingerprint_fighters)
    with (OUT/'verify.log').open('w',encoding='utf-8') as log:
        process=subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
        for line in process.stdout:
            log.write(line);log.flush();print(line,end='',flush=True)
        code=process.wait()
    # 此脚本整体在 tools/godot_lock.py 内运行；释放锁前复制，避免别会话覆盖。
    source=ROOT/'reports/verification.json'
    outcomes=json.loads(source.read_text('utf-8')) if source.exists() else []
    (OUT/'verification-result.json').write_text(json.dumps(outcomes,ensure_ascii=False,indent=2)+'\n','utf-8')
    meta=dict(command=command,started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),exit_code=code,failed=[r for r in outcomes if r['status']=='failed'],godot_lock_used=True)
    if args.fingerprint_fighters:
        after=fingerprints(args.fingerprint_fighters)
        meta['runtime_fingerprints_unchanged']=before==after
        (OUT/'runtime-fingerprints.json').write_text(json.dumps(dict(before=before,after=after,unchanged=before==after),ensure_ascii=False,indent=2)+'\n','utf-8')
    (OUT/'verify-run.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n','utf-8')
    return code


if __name__=='__main__':
    raise SystemExit(main())

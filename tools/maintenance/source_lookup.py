"""Locate one retained source by its current path or frozen historical path."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from layout_runtime import ROOT, translate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference')
    args = parser.parse_args()
    reference = args.reference.removeprefix('res://')
    target = Path(translate(reference))
    if not target.is_absolute():
        target = ROOT / target
    target = target.resolve()
    if not target.is_relative_to(ROOT) or not target.is_file():
        raise SystemExit('该路径不属于保留的当前源库；不要据此重发旧请求。')
    print(json.dumps({'path': target.relative_to(ROOT).as_posix(), 'bytes': target.stat().st_size,
                      'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

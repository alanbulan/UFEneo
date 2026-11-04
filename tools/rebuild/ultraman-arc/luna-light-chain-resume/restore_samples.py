"""用固定Forge链复现缺失159派生，只在编码字节SHA与冻结收据完全相同才恢复。"""
from __future__ import annotations
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
from PIL import Image
import check

sys.path.insert(0, str(check.ROOT / 'tools/rebuild/shared'))
from forge_backend import backend_info, binarize_alpha, _kcentroid_downscale, apply_palette, palette_mode


def restore(write=False):
    rows = []
    with palette_mode('rgb'):
        backend = backend_info()
        for receipt_path in sorted(check.CANDIDATES.rglob('phase-receipt.json')):
            receipt = check.read(receipt_path)
            row = {'action':receipt['action'],'phase':receipt['phase']}
            rows.append(row)
            try:
                candidate = (check.ROOT / receipt['whole_source_sample']['path']).resolve()
                candidate.relative_to(check.CANDIDATES)
                if candidate.exists() and not candidate.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1\n'):
                    check.checked(receipt['whole_source_sample'])
                    row['status'] = 'already_verified'
                    continue
                if backend['files'] != receipt['backend']['files']:
                    raise ValueError('Forge三文件SHA与原处理链不同，拒绝处理')
                source = check.checked(receipt['source'])
                palette_path = check.checked(receipt['palette'])
                with Image.open(source) as image:
                    if image.mode != 'RGBA' or image.size != (1024,1024):
                        raise ValueError('原源不是1024整张RGBA')
                    full = binarize_alpha(image.copy())
                small = _kcentroid_downscale(full,159,159,detail_bias=True)
                apply_palette(small,check.read(palette_path)['colors'])
                binarize_alpha(small)
                encoded = BytesIO()
                small.save(encoded,format='PNG')
                data = encoded.getvalue()
                digest = hashlib.sha256(data).hexdigest()
                row['reproduced_sha256'] = digest
                if digest != receipt['whole_source_sample']['sha256']:
                    raise ValueError('派生编码SHA不同；保留原指针，不替换原冻结对象')
                row['status'] = 'exact_reproduction_available'
                if write:
                    candidate.parent.mkdir(parents=True,exist_ok=True)
                    candidate.write_bytes(data)
                    check.checked(receipt['whole_source_sample'])
                    row['status'] = 'restored_exact_frozen_bytes'
            except (OSError, ValueError, KeyError) as error:
                row['status'] = 'blocked'
                row['reason'] = str(error)
    return {'schema':'ufeneo.luna.restore-frozen-samples.v1','rows':rows,'write_requested':write,
            'new_generation_cost':0,'new_art':False,'frozen_receipts_modified':False}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='只在复现字节SHA完全一致时替换LFS指针')
    args=parser.parse_args()
    result=restore(args.write)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(1 if any(r['status']=='blocked' for r in result['rows']) else 0)

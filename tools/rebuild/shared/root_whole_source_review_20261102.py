"""完整返图的小尺寸根审记录；只做审图，不处理/安装最终人物。"""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]


def read(path):
    return json.loads(path.read_text('utf-8-sig'))


def ref(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def preview(request, out):
    assert request.is_relative_to(ROOT) and out.is_relative_to(ROOT)
    assert read(request / 'submission-result.json')['image_returned']
    source = next((request / p for p in ['candidate.png', 'rejected/candidate.png'] if (request / p).is_file()), None)
    assert source is not None
    original = Image.open(source)
    assert original.mode == 'RGBA', '原件不是RGBA，不能伪称原生Alpha'
    picture = original.copy()
    alpha = np.asarray(picture)[:, :, 3]
    solid = alpha >= 128
    assert solid.any()
    picture.thumbnail((620, 620), Image.Resampling.LANCZOS)
    page = Image.new('RGB', (640, 672), '#252934')
    page.paste(picture, ((640-picture.width)//2, 30+(620-picture.height)//2), picture)
    ImageDraw.Draw(page).text((12, 10), request.parent.name+'/'+request.name, fill='white')
    target = out / 'whole-source.jpg'
    target.parent.mkdir(parents=True, exist_ok=False)
    page.save(target, quality=80)
    assert target.stat().st_size <= 150000
    result = dict(source=ref(source), request=ref(request/'brief.json'), submission=ref(request/'submission-result.json'),
        original_size=list(original.size), original_alpha_range=[int(alpha.min()), int(alpha.max())],
        original_nonzero_bbox=original.getbbox(), partial_alpha_fraction=float(np.mean((alpha>0)&(alpha<255))),
        solid128_bbox=Image.fromarray(solid).getbbox(),
        solid128_edge_pixels=int(solid[0].sum()+solid[-1].sum()+solid[:,0].sum()+solid[:,-1].sum()),
        source_bytes_unchanged=True, actual_view=ref(target), root_visual_review_pending=True,
        processed_final_png_created=False, runtime_installed=False)
    save(out/'source-review.json', result)
    print(json.dumps(result, ensure_ascii=False))


def verdict(review, observation, accepted):
    value = read(review)
    assert observation and ref(ROOT/value['source']['path']) == value['source']
    assert ref(ROOT/value['actual_view']['path']) == value['actual_view']
    if accepted:
        assert value['solid128_edge_pixels'] == 0
    request = (ROOT/value['request']['path']).parent
    name = 'root-actual-source-review-v1.json' if accepted else 'root-actual-source-rejection-v1.json'
    save(request/name, dict(reviewer='root_delegated_by_user', source=value['source'], actual_view=value['actual_view'],
        actual_opened=True, observation=observation, accepted_for_whole_action_processing=accepted,
        source_review=ref(review), original_alpha_gate_not_rewritten=True,
        processing_only='既有Forge整图、统一动作倍率；不拼肢、不逐相面积拟合。',
        strict_size_passed=False, runtime_accepted=False, playable_approval=False, goal_status='active'))
    print(json.dumps(dict(accepted_for_processing=accepted, review=str(review.relative_to(ROOT))), ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('preview')
    p.add_argument('--request', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    for name in ['accept', 'reject']:
        p = sub.add_parser(name)
        p.add_argument('--review', type=Path, required=True)
        p.add_argument('--observation', required=True)
    args = parser.parse_args()
    if args.mode == 'preview':
        preview(args.request.resolve(), args.out.resolve())
    else:
        verdict(args.review.resolve(), args.observation, args.mode == 'accept')

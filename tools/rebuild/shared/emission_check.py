"""发射点数据门。只比较人工依据表与运行字段，不把数值通过当作视觉批准。

field 相对该 tick 的帧；projectile.* 相对招式根。兼容事件的 anchor/
spawn/point 或 x,height。state:<状态> 用于只读状态帧的蓄能/身体光效。
没有表的在制角色暂不接管；新表落盘后自动参加检查。
"""
from __future__ import annotations

import argparse
import json
import math
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOKEN = re.compile(r'([A-Za-z_][A-Za-z_0-9]*)|\[(\d+)\]')


@lru_cache(maxsize=8)
def clips_at(path, stamp):
    return load(path)


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def point_at(move, index, field):
    if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(move['frames']):
        raise ValueError('frame必须为frames有效下标')
    if not isinstance(field, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*(?:\[\d+\]|\.[A-Za-z_][A-Za-z_0-9]*)*', field):
        raise ValueError('field路径非法')
    value = move if field.startswith('projectile.') else move['frames'][index]
    for match in TOKEN.finditer(field):
        value = value[match.group(1)] if match.group(1) is not None else value[int(match.group(2))]
    if isinstance(value, dict):
        for key in ('anchor', 'spawn', 'point'):
            if key in value:
                return value[key]
        if 'x' in value and 'height' in value:
            return [value['x'], value['height']]
    return value


def valid_point(point):
    return isinstance(point, list) and len(point) == 2 and all(
        isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in point)


def effective_point(move, mark, root):
    """可选atlas_point是审过的图集亮芯像素；point仍是脚底坐标。

    中心锚点旧图集可能用招式anchor补偿亮芯，不能把这种补偿误报为悬空。
    不带atlas_point的统一格式仍直接检查原字段，兼容另一普查会话。
    """
    if 'follow_frame' in mark:
        follow = mark['follow_frame']
        if not isinstance(follow, int) or isinstance(follow, bool) or not 0 <= follow < len(move['frames']):
            raise ValueError('follow_frame必须为人物当前有效帧')
        match = re.fullmatch(r'shots\[(\d+)\]\.origin_by_frame', mark['field'])
        if not match:
            raise ValueError('follow_frame仅用于逐束origin_by_frame')
        shot = move['frames'][mark['frame']]['shots'][int(match.group(1))]
        if not shot.get('beam'):
            raise ValueError('逐帧跟随只允许持续束')
        raw = shot['origin_by_frame'].get(str(follow), shot['anchor'])
        if not valid_point(raw) or any(value != int(value) for value in raw):
            raise ValueError('逐帧跟随点必须为整数原生像素')
    else:
        raw = point_at(move, mark['frame'], mark['field'])
    if 'atlas_point' not in mark:
        return raw
    if not valid_point(mark['atlas_point']):
        raise ValueError('atlas_point必须为裁片内的二维坐标')
    match = re.fullmatch(r'attachments\[(\d+)\]\.anchor', mark['field'])
    if not match:
        raise ValueError('atlas_point只用于挂件锚点')
    attachment = move['frames'][mark['frame']]['attachments'][int(match.group(1))]
    catalog = root/'content/presentation/phase3_projectiles.json'
    clip = clips_at(str(catalog),catalog.stat().st_mtime_ns)[attachment['effect']]
    phase = int(attachment['sprite']) % len(clip['rects'])
    rect = clip['rects'][phase]
    pivot = clip.get('anchor', [rect[2]/2, rect[3]/2])
    sample = mark['atlas_point']
    if not 0 <= sample[0] < rect[2] or not 0 <= sample[1] < rect[3]:
        raise ValueError('atlas_point超出特效裁片')
    scale = [attachment.get('visual_scale', 1)] * 2
    scale = attachment.get('display_scale', scale)
    effect_scale = clip.get('display_scale', [clip.get('visual_scale',1)]*2)
    return [raw[0] + (sample[0]-pivot[0])*scale[0]*effect_scale[0],
            raw[1] - (sample[1]-pivot[1])*scale[1]*effect_scale[1]]


def check_table(path, root=ROOT):
    errors, rows = [], []
    try:
        table = load(path)
        character = path.parent.name
        if table.get('schema') != 1 or table.get('character') != character:
            raise ValueError('schema/character与目录不符')
        if not isinstance(table.get('moves'), dict) or not table['moves']:
            raise ValueError('moves不能为空')
        for move_id, entry in table['moves'].items():
            prefix = character + '/' + move_id
            if not entry.get('part') or not entry.get('evidence') or entry.get('source') not in ('episode', 'game_design'):
                errors.append(prefix + ' 缺具体部位/依据/source')
            if move_id.startswith('state:'):
                move = {'frames': load(root / 'content/fighters' / character / 'state_frames.json')[move_id[6:]]}
            else:
                move = load(root / 'content/fighters' / character / 'moves' / (move_id + '.json'))
            if not isinstance(entry.get('frames'), list) or not entry['frames']:
                errors.append(prefix + ' 缺逐帧标点')
            seen = set()
            for mark in entry.get('frames', []):
                try:
                    expected = mark['point']
                    actual = effective_point(move, mark, root)
                    tolerance = mark.get('tolerance', 2)
                    if not valid_point(expected) or not valid_point(actual):
                        raise ValueError('坐标必须为有限二维数字')
                    if isinstance(tolerance, bool) or not isinstance(tolerance, (float, int)) or not math.isfinite(tolerance) or not 0 <= tolerance <= 2:
                        raise ValueError('tolerance必须在0至2原生像素以内')
                    identity = (mark['frame'], mark['field'], mark.get('follow_frame'))
                    if identity in seen:
                        raise ValueError('同一帧同一字段重复标点')
                    seen.add(identity)
                    distance = math.dist(expected, actual)
                    row = dict(character=character, move=move_id, frame=mark['frame'], field=mark['field'], expected=expected, actual=actual, error=distance, tolerance=tolerance)
                    if 'follow_frame' in mark:
                        row['follow_frame'] = mark['follow_frame']
                    rows.append(row)
                    if distance > tolerance:
                        errors.append(f'{prefix} #{mark["frame"]} {mark["field"]}: {actual}距依据点{expected}误差{distance:.3f}>{tolerance}')
                except (ValueError, KeyError, IndexError, TypeError) as exc:
                    errors.append(prefix + ' 标点无效：' + str(exc))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        errors.append(str(path) + ' 表无效：' + str(exc))
    return errors, rows


def audit(root=ROOT, characters=None):
    errors, rows, tables = [], [], []
    paths = sorted((root / 'content/fighters').glob('*/emission_points.json'))
    for path in paths:
        if characters and path.parent.name not in characters:
            continue
        tables.append(path.parent.name)
        failed, observed = check_table(path, root)
        errors.extend(failed)
        rows.extend(observed)
    if characters:
        errors.extend(c + ' 缺emission_points.json' for c in characters if c not in tables)
    if not tables:
        errors.append('没有可检查的发射点依据表')
    return dict(passed=not errors, tables=tables, errors=errors, rows=rows,
                scope='人工依据点与运行坐标一致性；未把图形、手势或原剧依据判为自动通过')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--characters', nargs='+')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit(args.root, args.characters)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for error in result['errors']:
        print(error)
    print('发射点数据门：' + ('通过' if result['passed'] else '失败') + '；角色=' + ','.join(result['tables']))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()

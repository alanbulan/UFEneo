"""F3 只读复算：七角色装机图集逐帧硬门、拒收记录、联系表与诊断图。

正式位置：tools/check/seven_character_rework_hard_gate.py。
本脚本只允许写入 reports/review/2026-11-12/seven-character-rework/。
所有输入均按绝对路径只读打开；不调用 Godot、verify.py、生图服务或 MCP。
"""
from __future__ import annotations

# tools/README.md §路径引导
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"),
    *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()],
    *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(_layout_root)
OUT = ROOT / 'reports/review/2026-11-12/seven-character-rework'
SHEETS = OUT / 'contact_sheets'
DIAG = OUT / 'diagnostics'
IDS = [
    'ultraman-zero', 'ultraman-justice', 'ultraman-gaia',
    'ultraman-king', 'zoffy', 'father-of-ultra', 'mother-of-ultra',
]
DISPLAY = {
    'ultraman-zero': '赛罗', 'ultraman-justice': '杰斯提斯',
    'ultraman-gaia': '盖亚', 'ultraman-king': '奥王',
    'zoffy': '佐菲', 'father-of-ultra': '奥父', 'mother-of-ultra': '奥母',
}
STANDING = set('''
idle walk_forward walk_back guard block blockstun light1 light2 light3 heavy
special special2 special3 pulse ranged_forward charge charge_start charge_stop
intro win victory taunt turn hit_high hit_mid guardbreak stun motion_236
motion_214 motion_623 motion_41236 motion_22 dash_throw throw burst
guard_counter back_counter dodge_counter launcher diagonal_light diagonal_heavy
'''.split())
HEIGHT_TOL = 0.08
JUMP_TOL = 0.10
DIFF_MIN = 0.10
HALO_MAX16 = 100
COLOR_MAX = 32
FONT_PATH = '/System/Library/Fonts/STHeiti Medium.ttc'
FONT_BIG = ImageFont.truetype(FONT_PATH, 24)
FONT = ImageFont.truetype(FONT_PATH, 17)
FONT_SMALL = ImageFont.truetype(FONT_PATH, 14)

POSTURE_PREFIXES = {
    'crouch': '蹲/低蹲', 'air': '腾空', 'down': '倒地/躺姿',
    'ko': '倒地/躺姿', 'thrown': '被投', 'bounce': '腾空/弹地',
    'defeat': '倒地/躺姿', 'backflip': '腾空/空翻', 'flip': '腾空/空翻',
}
POSTURE_NAMES = {
    'takeoff': '真实屈膝/起跳', 'land': '真实屈膝/落地', 'dash': '真实屈膝/跑步',
    'backstep': '真实屈膝/后撤', 'dash_throw': '真实屈膝/冲刺投',
    'diagonal_heavy': '腾空/斜跳重击', 'diagonal_light': '腾空/斜跳轻击',
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def jload(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def jdump(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def r4(v):
    return round(float(v), 4)


def component_stats(mask: np.ndarray, conn: int):
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=conn)
    sizes = [int(x) for x in stats[1:, cv2.CC_STAT_AREA].tolist()]
    return n - 1, labels, sizes


def frame_metrics(rgba: np.ndarray) -> dict:
    alpha = rgba[..., 3]
    body = alpha >= 128
    solid = alpha >= 200
    alpha_values = sorted(int(v) for v in np.unique(alpha).tolist())
    binary = bool(np.all((alpha == 0) | (alpha == 255)))
    visible = rgba[alpha > 0]
    colors = int(np.unique(visible.reshape(-1, 4), axis=0).shape[0]) if len(visible) else 0
    c4, lab4, sizes4 = component_stats(solid, 4)
    c8, _, sizes8 = component_stats(solid, 8)
    solid_pixels = int(solid.sum())
    if c4:
        largest = 1 + int(np.argmax(sizes4))
        main = lab4 == largest
        # 7x7 MaxFilter 等价于主体 3px 方形外扩；逐帧只在 rect 内统计。
        outer = np.array(Image.fromarray((main * 255).astype(np.uint8), 'L')
                         .filter(ImageFilter.MaxFilter(7))) > 0
        outside = ~outer
        halo16 = int(((alpha >= 16) & outside).sum())
        halo200 = int(((alpha >= 200) & outside).sum())
        dust = int(((alpha >= 1) & (alpha < 16) & outside).sum())
        outside_alpha_positive = int(((alpha > 0) & outside).sum())
        main_pixels = int(main.sum())
    else:
        halo16 = halo200 = dust = outside_alpha_positive = main_pixels = 0
    if body.any():
        ys, xs = np.nonzero(body)
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
        height = int(bbox[3] - bbox[1] + 1)
        width = int(bbox[2] - bbox[0] + 1)
        top_gap, left_gap = int(ys.min()), int(xs.min())
        bottom_gap = int(alpha.shape[0] - 1 - ys.max())
        right_gap = int(alpha.shape[1] - 1 - xs.max())
        body_pixels = int(body.sum())
        # 只读代理：面积平方根 / 主体高度；不是真实骨长，必须配合姿态说明。
        limb_proxy = float(np.sqrt(body_pixels) / height) if height else 0.0
    else:
        bbox = [0, 0, 0, 0]
        height = width = top_gap = left_gap = bottom_gap = right_gap = body_pixels = 0
        limb_proxy = 0.0
    return {
        'alpha_values': alpha_values,
        'alpha_binary': binary,
        'alpha_binary_gate': '仅 0/255',
        'visible_colors': colors,
        'solid_pixels': solid_pixels,
        'main_body_pixels': main_pixels,
        'components4': c4,
        'component_areas4': sizes4[:16],
        'components8': c8,
        'component_areas8': sizes8[:16],
        'halo_alpha16_outside': halo16,
        'halo_alpha200_outside': halo200,
        'halo_dust_1_15_outside': dust,
        'outside_alpha_positive_registry_only': outside_alpha_positive,
        'bbox': bbox,
        'height': height,
        'width': width,
        'body_pixels': body_pixels,
        'limb_thickness_proxy': r4(limb_proxy),
        'edge_gaps': [top_gap, left_gap, bottom_gap, right_gap],
    }


def silhouette_diffs(masks: list[np.ndarray], loop: bool) -> list[dict]:
    out = []
    pairs = [(i - 1, i, False) for i in range(1, len(masks))]
    if loop and len(masks) > 1:
        pairs.append((len(masks) - 1, 0, True))
    for a, b, is_loop in pairs:
        xor = int((masks[a] ^ masks[b]).sum())
        union = int((masks[a] | masks[b]).sum())
        d = xor / union if union else 1.0
        out.append({'from': a, 'to': b, 'loop': is_loop, 'xor': xor,
                    'union': union, 'xor_over_union': r4(d),
                    'gate': DIFF_MIN, 'pass': d >= DIFF_MIN})
    return out


def posture_exception(clip: str) -> str | None:
    if clip in POSTURE_NAMES:
        return POSTURE_NAMES[clip]
    for prefix, reason in POSTURE_PREFIXES.items():
        if clip.startswith(prefix):
            return reason
    if 'throw' in clip and clip != 'throw':
        return '被投/投技姿态'
    if 'wake' in clip or 'getup' in clip:
        return '起身/真实屈膝'
    return '非 §1.1 明文站姿集合；按实际姿态登记高度与宽度代理'


def add_rejection(bucket: dict, key: str, fid: str, clip: str, frame: int,
                  gate: str, gate_value, measured, reason: str, sha: str) -> None:
    streak = bucket.setdefault(key, {'fighter': fid, 'check': key, 'rejected_frames': [],
                                     'paused': False, 'diagnostic_image': None,
                                     'max_fix_methods': 2})
    if len(streak['rejected_frames']) < 3:
        streak['rejected_frames'].append({'clip': clip, 'frame': frame, 'atlas_sha256': sha})
    if len(streak['rejected_frames']) >= 3:
        streak['paused'] = True
        streak['diagnostic_image'] = str(DIAG / f'{fid}_{key}.png')


def checker(rgba: Image.Image, scale: int = 4) -> Image.Image:
    w, h = rgba.width * scale, rgba.height * scale
    # 棋盘格用 NumPy 生成，避免逐像素 Python 循环拖慢 3500+ 联系表帧。
    yy, xx = np.ogrid[:h, :w]
    s = 8 * scale
    light = ((xx // s + yy // s) % 2) == 0
    bg_arr = np.empty((h, w, 3), dtype=np.uint8)
    bg_arr[light] = (38, 40, 48)
    bg_arr[~light] = (52, 55, 64)
    bg = Image.fromarray(bg_arr, 'RGB')
    big = rgba.resize((w, h), Image.Resampling.NEAREST)
    bg.paste(big, (0, 0), big)
    return bg


def contact_sheet(fid: str, rows: list[dict], pending: dict, path: Path) -> None:
    cols = 8
    cell = 288
    # tile 内只放 256×256 的 4× 显示窗（原生 64px 居中裁切），保持严格最近邻 4×。
    disp = 256
    tw, th = disp + 16, disp + 110
    n = len(rows)
    sheet = Image.new('RGB', (cols * tw, (n + cols - 1) // cols * th + 72), (24, 27, 34))
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 12), f'{DISPLAY[fid]} / {fid} · 装机 atlas 最近邻 4× · F3 只读硬门联系表',
              font=FONT_BIG, fill=(235, 238, 245))
    draw.text((18, 43), '仅技术复算：不表示造型、美术或实机通过；红边=该帧有拒收门',
              font=FONT_SMALL, fill=(185, 190, 200))
    for idx, row in enumerate(rows):
        rgba = row.pop('_rgba')
        x = (idx % cols) * tw
        y = 72 + (idx // cols) * th
        tile = Image.new('RGB', (tw, th), (30, 33, 40))
        td = ImageDraw.Draw(tile)
        td.text((8, 5), f"{row['clip']} #{row['frame']:02d} · tick {row['tick']}",
                font=FONT, fill=(245, 245, 245))
        td.text((8, 28), f"h={row['height']}px  Δprev={row['diff_from_prev']}",
                font=FONT_SMALL, fill=(160, 220, 255))
        td.text((8, 49), f"4n={row['components4']}  halo16={row['halo_alpha16_outside']}  c={row['visible_colors']}",
                font=FONT_SMALL, fill=(190, 195, 205))
        reasons = '；'.join(row['reject_reasons'][:3]) if row['reject_reasons'] else '无硬门拒收'
        # 文字宽度安全截断；完整原因在 JSON/Markdown 中。
        while td.textbbox((0, 0), reasons, font=FONT_SMALL)[2] > tw - 16 and len(reasons) > 4:
            reasons = reasons[:-2]
        td.text((8, 70), reasons, font=FONT_SMALL,
                fill=(255, 105, 105) if row['reject_reasons'] else (145, 225, 160))
        img = checker(rgba)
        # 按 4× 后人物 bbox 中心裁 256×256 显示窗；不做缩放或重标定。
        alpha = np.array(rgba)[..., 3]
        ys, xs = np.nonzero(alpha >= 128)
        if len(xs):
            cx = int(round((xs.min() + xs.max() + 1) * 2))
            cy = int(round((ys.min() + ys.max() + 1) * 2))
        else:
            cx, cy = img.width // 2, img.height // 2
        left = max(0, min(img.width - disp, cx - disp // 2))
        top = max(0, min(img.height - disp, cy - disp // 2))
        img = img.crop((left, top, left + disp, top + disp))
        tile.paste(img, (8, 94))
        if row['reject_reasons']:
            td.rectangle((7, 93, tw - 9, th - 7), outline=(255, 70, 70), width=3)
        sheet.paste(tile, (x, y))
    sheet.save(path, optimize=True)


def diagnostic_image(fid: str, gate: str, examples: list[dict], path: Path) -> None:
    # 只画前三个不同帧，符合「连续拒收 3 个不同帧就暂停并出诊断图」。
    sheet = Image.new('RGB', (3 * 300, 360), (22, 25, 32))
    d = ImageDraw.Draw(sheet)
    d.text((12, 10), f'{DISPLAY[fid]} {gate} · 连续 3 帧拒收诊断', font=FONT_BIG, fill=(245, 245, 245))
    d.text((12, 42), '装机图集最近邻 1× 显示窗（报告用缩略）；红框标出拒收帧，不修图、不重算',
           font=FONT_SMALL, fill=(190, 195, 205))
    for i, ex in enumerate(examples[:3]):
        rgba = ex['_rgba']
        big = checker(rgba, scale=1)
        # 诊断图是 1× 像素的 256px 显示窗，只作定位；联系表才承担严格 4× 复算。
        alpha = np.array(rgba)[..., 3]
        ys, xs = np.nonzero(alpha >= 128)
        if len(xs):
            cx = int(round((xs.min() + xs.max() + 1) / 2))
            cy = int(round((ys.min() + ys.max() + 1) / 2))
        else:
            cx, cy = big.width // 2, big.height // 2
        left = max(0, min(big.width - 256, cx - 128))
        top = max(0, min(big.height - 256, cy - 128))
        big = big.crop((left, top, left + 256, top + 256))
        x = 12 + i * 300
        d.text((x, 72), f"{ex['clip']} #{ex['frame']:02d}", font=FONT, fill=(255, 190, 190))
        d.text((x, 96), f"门 {ex['gate']} / 实测 {ex['measured']}", font=FONT_SMALL, fill=(210, 215, 225))
        sheet.paste(big, (x, 122))
        d.rectangle((x - 1, 121, x + 257, 379), outline=(255, 70, 70), width=2)
    sheet.save(path, optimize=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SHEETS.mkdir(parents=True, exist_ok=True)
    DIAG.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
    all_results = {
        'schema': 'f3-readonly-hard-gate-recompute-20261112',
        'generated_at': now,
        'scope': '七角色现装机 assets/fighters/<id>/animations/manifest.json 与每 clip atlas.png；只读复算',
        'authority': 'root_delegated_by_user 由根统一签署；F3 子代理不签、不冒称用户亲审',
        'source_policy': {
            'manifest': '只读，逐 clip 取自身 cell/anchor/rects/ticks；不使用顶层旧 anchor',
            'atlas': '只读，按 clip.texture 的 res:// 路径定位并按 rects 拆帧',
            'identity_ready': '七角色均缺失，记 spec_only/无 ready；不冒称身份锚已签',
            'generation_requests_and_usage': '本轮无生成请求/usage，不编造',
            'audit': str(ROOT / 'reports/review/2026-11-12/seven-character-defects/audit.json'),
        },
        'gate_definitions': {
            'subject': 'alpha>=200 最大 4 邻域连通块；主体高度按 alpha>=128 人物轮廓 bbox',
            'connectivity_primary': 'alpha>=200 4 邻域单连通；8 邻域辅助',
            'alpha': '整帧仅 0/255；透明背景必须有 alpha=0 像素',
            'colors': 'alpha>0 的 RGBA 唯一色 <=32',
            'halo': '主体 7x7 MaxFilter 外扩 3px；主体外 alpha>=16 <=100px、alpha>=200=0；alpha1-15 只登记；主体外 alpha>0 不作判死门',
            'standing_clips': sorted(STANDING),
            'standing_height': '仅 §1.1 明文站姿集合：|h-identity_card 锚站高|/锚站高 >8% 拒收',
            'adjacent_height_jump': '仅同组明文站姿相邻帧：|h_i-h_(i-1)|/h_(i-1) >10% 拒收',
            'silhouette_diff': '同 clip 同坐标 alpha>=128 掩码 XOR/Union >=0.10；含 loop 首尾对',
            'posture_exception': '非站姿集合登记具体高度、bbox 宽度及 sqrt(面积)/高度代理；代理与高度同方向大幅变化记疑似整人缩放并列入拒收，不以例外二字放行',
            'atlas_sha256': 'asset_baseline.json 记录 sha256/atlas_sha256、现场 sha256、manifest.atlas_sha256 三者对应',
        },
        'characters': {},
    }
    all_rejects = {}
    index_rows = []
    frame_spec_snapshot = []

    for fid in IDS:
        rework = ROOT / 'art/fighters' / fid / 'stage1/rework-20261112'
        ready = rework / 'identity_ready.json'
        card = jload(rework / 'identity_card.json')
        cd = jload(rework / 'clip_diagnosis.json')
        baseline = jload(rework / 'asset_baseline.json')
        manifest_path = ROOT / 'assets/fighters' / fid / 'animations/manifest.json'
        manifest = jload(manifest_path)
        clips = manifest['clips']
        baseline_clips = baseline['clips']
        diag_clips = cd['clips']
        if 'standing_height_baseline' in card:
            anchor_height = int(card['standing_height_baseline'])
            scale = card.get('unique_scale')
            height_source = 'identity_card.standing_height_baseline'
        else:
            anchor_height = int(card['frozen_scale']['installed_idle_standing_height'])
            scale = card['frozen_scale'].get('production_cells_scale')
            height_source = 'identity_card.frozen_scale.installed_idle_standing_height'
        exception_list = card.get('allowed_posture_exceptions') or card.get('allowed_pose_exceptions') or []

        # 待机代理：用于姿态例外「高度 + 体量代理」同方向变化的辅助登记。
        idle_meta = clips['idle']
        idle_atlas = np.array(Image.open(ROOT / idle_meta['texture'].removeprefix('res://')).convert('RGBA'))
        rx, ry, rw, rh = idle_meta['rects'][0]
        idle_metric = frame_metrics(idle_atlas[ry:ry + rh, rx:rx + rw])
        idle_proxy = idle_metric['limb_thickness_proxy']

        clip_records = []
        sheet_rows = []
        rejects = []
        gate_streaks = {}
        diag_examples = {}
        counters = Counter()
        total_frames = 0
        total_reject = 0
        total_pass = 0
        halo_counts = Counter()
        standing_counts = Counter()
        diff_counts = Counter()
        disagreement = []

        for clip, meta in clips.items():
            atlas_rel = meta['texture'].removeprefix('res://')
            atlas_path = ROOT / atlas_rel
            live_sha = sha256(atlas_path)
            base = baseline_clips[clip]
            base_sha = base.get('sha256') or base.get('atlas_sha256')
            recorded_sha = meta.get('atlas_sha256')
            sha_correspondence = {
                'atlas_absolute_path': str(atlas_path),
                'asset_baseline_sha256': base_sha,
                'manifest_atlas_sha256': recorded_sha,
                'live_sha256': live_sha,
                'all_match': bool(base_sha == recorded_sha == live_sha),
            }
            atlas = np.array(Image.open(atlas_path).convert('RGBA'))
            frames = []
            masks = []
            for i, rect in enumerate(meta['rects']):
                x, y, w, h = [int(v) for v in rect]
                rgba = atlas[y:y + h, x:x + w]
                m = frame_metrics(rgba)
                body = rgba[..., 3] >= 128
                masks.append(body)
                diag = diag_clips[clip]
                if 'frames' in diag:
                    dfh = int(diag['frames'][i]['height'])
                    dfb = [int(v) for v in diag['frames'][i]['bbox']]
                else:
                    dfh = int(diag['heights'][i])
                    dfb = [int(v) for v in diag['frame_meta'][i]['bbox']]
                cross = {'source': str(rework / 'clip_diagnosis.json'),
                         'diagnosed_height': dfh, 'diagnosed_bbox': dfb,
                         'recomputed_height': m['height'], 'recomputed_bbox': m['bbox'],
                         'height_match': dfh == m['height'], 'bbox_match': dfb == m['bbox']}
                if not (cross['height_match'] and cross['bbox_match']):
                    disagreement.append({'clip': clip, 'frame': i, **cross})
                record = {
                    'clip': clip, 'frame': i, 'tick': int(meta['ticks'][i]),
                    'rect': [x, y, w, h], 'cell': meta['cell'],
                    'anchor': meta['anchor'], 'atlas_sha256': live_sha,
                    'atlas_sha_correspondence': sha_correspondence,
                    **m, 'clip_diagnosis_crosscheck': cross,
                }
                frames.append(record)
                total_frames += 1

            diffs = silhouette_diffs(masks, bool(meta.get('loop', False)))
            diff_map = {(d['from'], d['to']): d for d in diffs}
            standing = clip in STANDING
            heights = [f['height'] for f in frames]
            exception = None if standing else posture_exception(clip)
            clip_standing_evaluations = []
            clip_posture_evaluations = []
            clip_diff_evaluations = []
            clip_rejections = []

            for i, f in enumerate(frames):
                reasons = []
                gate_rows = []
                # 逐帧硬门
                if not f['alpha_binary'] or f['alpha_values'] not in ([0, 255], [0]):
                    reasons.append('真 Alpha 非仅 0/255')
                    gate_rows.append(('true_alpha', [0, 255], f['alpha_values'], '整帧 Alpha 含中间值'))
                counters['alpha_binary_fail'] += int(not f['alpha_binary'])
                if f['visible_colors'] > COLOR_MAX:
                    reasons.append(f"可见色 {f['visible_colors']}>{COLOR_MAX}")
                    gate_rows.append(('visible_colors', COLOR_MAX, f['visible_colors'], '可见 RGBA 色数超过 32'))
                counters['colors_fail'] += int(f['visible_colors'] > COLOR_MAX)
                if f['components4'] != 1:
                    reasons.append(f"4 邻域主体连通块 {f['components4']}≠1")
                    gate_rows.append(('components4', 1, f['components4'], 'alpha>=200 主体须 4 邻域单连通'))
                counters['components4_fail'] += int(f['components4'] != 1)
                halo_counts['frames_registered'] += 1
                halo_counts['max_alpha16_outside'] = max(halo_counts['max_alpha16_outside'], f['halo_alpha16_outside'])
                halo_counts['sum_dust_1_15'] += f['halo_dust_1_15_outside']
                if f['halo_alpha16_outside'] > HALO_MAX16:
                    reasons.append(f"主体外 alpha>=16 {f['halo_alpha16_outside']}>100")
                    gate_rows.append(('halo_alpha16_outside', HALO_MAX16, f['halo_alpha16_outside'], '外扩 3px 后主体外 alpha>=16 超限'))
                if f['halo_alpha200_outside'] != 0:
                    reasons.append(f"主体外 alpha>=200 {f['halo_alpha200_outside']}≠0")
                    gate_rows.append(('halo_alpha200_outside', 0, f['halo_alpha200_outside'], '外扩 3px 后主体外 alpha>=200 必须为 0'))
                halo_counts['halo16_fail'] += int(f['halo_alpha16_outside'] > HALO_MAX16)
                halo_counts['halo200_fail'] += int(f['halo_alpha200_outside'] != 0)
                if not sha_correspondence['all_match']:
                    reasons.append('atlas SHA 三方不一致')
                    gate_rows.append(('atlas_sha256', '三方一致', sha_correspondence, '基线/manifest/现场 SHA 不一致'))

                # 站姿硬门
                deviation = abs(f['height'] - anchor_height) / anchor_height if anchor_height else None
                if standing and deviation is not None:
                    standing_counts['evaluated'] += 1
                    ev = {'frame': i, 'height': f['height'], 'anchor_height': anchor_height,
                          'deviation': r4(deviation), 'gate': HEIGHT_TOL, 'pass': deviation <= HEIGHT_TOL}
                    clip_standing_evaluations.append(ev)
                    if deviation > HEIGHT_TOL:
                        reasons.append(f"站姿高度偏差 {deviation:.2%}>8%")
                        gate_rows.append(('standing_height_deviation', HEIGHT_TOL, r4(deviation), '站姿主体高度对锚超 8%'))
                        standing_counts['height_fail'] += 1
                    if i > 0 and heights[i - 1]:
                        jump = abs(f['height'] - heights[i - 1]) / heights[i - 1]
                        ev['adjacent_height_jump'] = r4(jump)
                        ev['adjacent_gate'] = JUMP_TOL
                        ev['adjacent_pass'] = jump <= JUMP_TOL
                        standing_counts['adjacent_evaluated'] += 1
                        if jump > JUMP_TOL:
                            reasons.append(f"相邻站姿高度突变 {jump:.2%}>10%")
                            gate_rows.append(('adjacent_height_jump', JUMP_TOL, r4(jump), '同组相邻站姿高度突变超 10%'))
                            standing_counts['jump_fail'] += 1
                elif not standing:
                    hd = abs(f['height'] - anchor_height) / anchor_height if anchor_height else 0
                    pd = abs(f['limb_thickness_proxy'] - idle_proxy) / idle_proxy if idle_proxy else 0
                    same_direction = ((f['height'] < anchor_height and f['limb_thickness_proxy'] < idle_proxy)
                                      or (f['height'] > anchor_height and f['limb_thickness_proxy'] > idle_proxy))
                    suspicious = hd > HEIGHT_TOL and pd > HEIGHT_TOL and same_direction
                    ev = {
                        'frame': i, 'posture_exception': exception,
                        'height': f['height'], 'bbox_width': f['width'],
                        'limb_thickness_proxy': f['limb_thickness_proxy'],
                        'idle_height': anchor_height, 'idle_limb_thickness_proxy': idle_proxy,
                        'height_deviation': r4(hd), 'proxy_deviation': r4(pd),
                        'same_direction_proxy_change': bool(same_direction),
                        'suspected_whole_body_rescale': bool(suspicious),
                        'evidence_note': '真实骨长/头壳未经人工标点；proxy 只用于排除明显整人同向缩放，不证明姿势合格',
                    }
                    clip_posture_evaluations.append(ev)
                    if suspicious:
                        reasons.append(f"姿态例外疑似整人缩放 h偏差{hd:.2%}/代理偏差{pd:.2%}")
                        gate_rows.append(('posture_exception_proxy', HEIGHT_TOL, {'height': r4(hd), 'proxy': r4(pd)},
                                          '高度与体量代理同方向大变；不能以例外二字放行整人缩放'))

                # 相邻剪影差分
                if i > 0 and (i - 1, i) in diff_map:
                    d = diff_map[(i - 1, i)]
                    diff_counts['adjacent_evaluated'] += 1
                    if not d['pass']:
                        reasons.append(f"相邻 XOR/Union {d['xor_over_union']:.4f}<0.10")
                        gate_rows.append(('silhouette_xor_union', DIFF_MIN, d['xor_over_union'], '相邻剪影差分不足 0.10'))
                        diff_counts['adjacent_fail'] += 1
                    f['diff_from_prev'] = d['xor_over_union']
                    clip_diff_evaluations.append(d)
                else:
                    f['diff_from_prev'] = None
                for d in diffs:
                    if d.get('loop') and d['to'] == 0:
                        f['loop_diff_from_last'] = d['xor_over_union']

                f['standing_class'] = standing
                f['posture_exception'] = exception
                f['height_deviation'] = r4(deviation) if deviation is not None else None
                f['height_gate'] = HEIGHT_TOL if standing else None
                f['gate_rows'] = [
                    {'gate': g, 'gate_value': gv, 'measured': mv, 'reason': why}
                    for g, gv, mv, why in gate_rows
                ]
                f['reject_reasons'] = list(reasons)
                f['hard_gate_pass'] = not reasons
                total_pass += int(not reasons)
                total_reject += int(bool(reasons))
                if reasons:
                    rej = {
                        'fighter': fid, 'clip': clip, 'frame': i,
                        'frame_key': f'{clip}#{i:02d}',
                        'atlas_absolute_path': str(atlas_path),
                        'atlas_sha256': live_sha,
                        'atlas_sha_correspondence': sha_correspondence,
                        'gate_rows': f['gate_rows'], 'reasons': reasons,
                        'height': f['height'], 'anchor_height': anchor_height,
                        'diff_from_prev': f['diff_from_prev'],
                    }
                    rejects.append(rej)
                    clip_rejections.append(rej)
                    for gr in f['gate_rows']:
                        gate = gr['gate']
                        add_rejection(gate_streaks, gate, fid, clip, i, gate,
                                      gr['gate_value'], gr['measured'], gr['reason'], live_sha)
                        diag_examples.setdefault(gate, []).append({
                            'clip': clip, 'frame': i, 'gate': gate,
                            'measured': gr['measured'], '_rgba': Image.fromarray(atlas[
                                int(meta['rects'][i][1]):int(meta['rects'][i][1]) + int(meta['rects'][i][3]),
                                int(meta['rects'][i][0]):int(meta['rects'][i][0]) + int(meta['rects'][i][2])], 'RGBA').copy(),
                        })
                # 联系表最多保留每角色前 192 帧；完整逐帧数据在 hard_gate_results.json。
                if len(sheet_rows) < 192:
                    sheet_rows.append({
                        'clip': clip, 'frame': i, 'tick': int(meta['ticks'][i]),
                        'height': f['height'],
                        'diff_from_prev': f['diff_from_prev'] if f['diff_from_prev'] is not None else '—',
                        'components4': f['components4'],
                        'halo_alpha16_outside': f['halo_alpha16_outside'],
                        'visible_colors': f['visible_colors'],
                        'reject_reasons': f['reject_reasons'],
                        '_rgba': Image.fromarray(atlas[
                            int(meta['rects'][i][1]):int(meta['rects'][i][1]) + int(meta['rects'][i][3]),
                            int(meta['rects'][i][0]):int(meta['rects'][i][0]) + int(meta['rects'][i][2])], 'RGBA').copy(),
                    })

            for d in diffs:
                if d.get('loop') and not d['pass']:
                    diff_counts['loop_fail'] += 1
            clip_records.append({
                'clip': clip,
                'cell': meta['cell'], 'anchor': meta['anchor'],
                'anchors': meta.get('anchors'), 'ticks': meta['ticks'],
                'loop': bool(meta.get('loop', False)),
                'rects': meta['rects'],
                'atlas_absolute_path': str(atlas_path),
                'atlas_sha256': live_sha,
                'atlas_sha_correspondence': sha_correspondence,
                'standing_class': standing,
                'posture_exception': exception,
                'posture_exception_card_listed': (clip in exception_list) if isinstance(exception_list, list) else False,
                'anchor_height': anchor_height,
                'height_source': height_source,
                'frame_count': len(frames),
                'frames': frames,
                'silhouette_diffs': diffs,
                'standing_height_evaluations': clip_standing_evaluations,
                'posture_exception_evaluations': clip_posture_evaluations,
                'rejected_frames': [r['frame'] for r in clip_rejections],
                'rejection_count': len(clip_rejections),
                'clip_diagnosis_disagreements': [q for q in disagreement if q['clip'] == clip],
            })

        for key, streak in gate_streaks.items():
            if streak['paused']:
                path = DIAG / f'{fid}_{key}.png'
                diagnostic_image(fid, key, diag_examples[key], path)
                streak['diagnostic_image'] = str(path)
        sheet_path = SHEETS / f'{fid}_gate.png'
        contact_sheet(fid, sheet_rows, gate_streaks, sheet_path)
        for row in sheet_rows:
            row.pop('_rgba', None)
        for examples in diag_examples.values():
            for ex in examples:
                ex.pop('_rgba', None)
        character = {
            'fighter': fid,
            'display': DISPLAY[fid],
            'identity_ready': {
                'absolute_path': str(ready), 'exists': ready.exists(),
                'status': 'spec_only/无 ready' if not ready.exists() else 'present',
            },
            'identity_card_absolute_path': str(rework / 'identity_card.json'),
            'anchor_height': anchor_height,
            'anchor_height_source': height_source,
            'unique_scale': scale,
            'idle_reference': {
                'absolute_path': str(card.get('idle_pixel_whole_frame', card.get('identity_anchor', {})).get('absolute_path', '')),
                'sha256': str(card.get('idle_pixel_whole_frame', card.get('identity_anchor', {})).get('sha256', '')),
            },
            'standing_clip_count': sum(1 for c in clips if c in STANDING),
            'posture_exception_clip_count': sum(1 for c in clips if c not in STANDING),
            'exception_list_from_identity_card': exception_list,
            'manifest_absolute_path': str(manifest_path),
            'manifest_sha256': sha256(manifest_path),
            'asset_baseline_absolute_path': str(rework / 'asset_baseline.json'),
            'clip_diagnosis_absolute_path': str(rework / 'clip_diagnosis.json'),
            'clip_count': len(clips),
            'frame_count': total_frames,
            'hard_gate_pass_frames': total_pass,
            'hard_gate_reject_frames': total_reject,
            'rejected_unique_frames': len({(r['clip'], r['frame']) for r in rejects}),
            'technical_gate_counter': dict(counters),
            'halo_summary': dict(halo_counts),
            'standing_summary': dict(standing_counts),
            'silhouette_diff_summary': dict(diff_counts),
            'clip_diagnosis_disagreements': disagreement,
            'paused_check_streaks': gate_streaks,
            'contact_sheet_absolute_path': str(sheet_path),
            'contact_sheet_scope': f'从装机 atlas 最近邻 4× 重算，按人物 bbox 中心裁 256×256 显示窗，列前 {len(sheet_rows)} 帧；全部 {total_frames} 帧数值在 clips[].frames',
            'clips': clip_records,
        }
        all_results['characters'][fid] = character
        all_rejects[fid] = {
            'fighter': fid,
            'display': DISPLAY[fid],
            'anchor_height': anchor_height,
            'atlas_sha256_location': 'hard_gate_results.json: characters.<fighter>.clips[].atlas_sha_correspondence 与 clips[].frames[].atlas_sha256；asset_baseline.json 为只读来源',
            'reject_count': len(rejects),
            'rejected_unique_frames': len({(r['clip'], r['frame']) for r in rejects}),
            'paused_check_streaks': gate_streaks,
            'fix_method_policy': '同一问题最多 2 种修法；本轮是只读复算，不实施修法、不无限重算',
            'rejections': rejects,
        }
        index_rows.append({
            'fighter': fid, 'display': DISPLAY[fid],
            'clips': len(clips), 'frames': total_frames,
            'pass': total_pass, 'reject': total_reject,
            'sheet': str(sheet_path),
        })

    # 报告最后只做一次 frame_specs 存在性/字数抽查，写明时点。
    spec_time = datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
    for fid in IDS:
        stage = ROOT / 'art/fighters' / fid / 'stage1'
        candidates = []
        for rel in ['frame_specs', 'rework-20261112/frame_specs']:
            p = stage / rel
            if p.exists():
                files = [q for q in p.rglob('*') if q.is_file()]
                candidates.append({
                    'absolute_path': str(p), 'file_count': len(files),
                    'text_file_count': sum(1 for q in files if q.suffix in {'.md', '.json', '.txt'}),
                    'total_chars': sum(len(q.read_text(encoding='utf-8', errors='ignore')) for q in files
                                       if q.suffix in {'.md', '.json', '.txt'}),
                    'example_files': [str(q) for q in files[:3]],
                })
        frame_spec_snapshot.append({
            'fighter': fid,
            'status': 'found' if candidates else 'missing_at_snapshot',
            'directories': candidates,
        })
    all_results['frame_specs_snapshot'] = {
        'checked_at': spec_time,
        'policy': 'F1/F2 并行补写；F3 不等待，只在报告写完时做一次存在性/字数抽查',
        'results': frame_spec_snapshot,
    }
    all_rejects['_meta'] = {
        'generated_at': now,
        'scope': 'F3 只读拒收记录；gate_rows 含门值/实测值/原因/atlas SHA',
        'frame_specs_snapshot_at': spec_time,
        'frame_specs_snapshot': frame_spec_snapshot,
        'generation_requests_and_usage': '本轮无生成请求/usage，不编造',
    }

    jdump(OUT / 'hard_gate_results.json', all_results)
    jdump(OUT / 'rejections.json', all_rejects)

    script_path = Path(__file__).resolve()
    script_sha = sha256(script_path)
    relocation_note = (
        f'复算脚本已归位 `{script_path}`，SHA `{script_sha}`；'
        '本目录保留 JSON/联系表/诊断图/索引。'
    )
    reject_relocation_note = relocation_note + '；本文件拒收数值结论未改。'

    # Markdown 拒收记录：逐角色、逐拒收行；完整门值在 JSON。
    reject_md = [
        '# 七角色逐帧硬门拒收记录（F3 只读复算）',
        '',
        f'生成时点：{now}。本文件只记录装机 atlas 的只读复算结果，不表示美术、造型或实机通过。',
        '',
        '- 门值、实测值、原因、atlas SHA 逐条见 `rejections.json`；逐帧全部数值见 `hard_gate_results.json`。',
        '- `root_delegated_by_user` 由根统一签署，F3 子代理不签。',
        '- 同一检查连续拒收 3 个不同帧即暂停该项并出同目录诊断图；同一问题最多 2 种修法，本轮不实施修法、不无限重算。',
        f'- {reject_relocation_note}',
        '',
    ]
    for fid in IDS:
        rec = all_rejects[fid]
        reject_md.extend([
            f"## {rec['display']} / `{fid}`",
            '',
            f"拒收门项 {rec['reject_count']} 条，涉及唯一帧 {rec['rejected_unique_frames']} 张；锚站高 {rec['anchor_height']} px。",
            '',
            '| clip/帧 | 门 | 门值 | 实测 | 原因 | atlas SHA（前 12 位） |',
            '|---|---|---:|---|---|---|',
        ])
        for r in rec['rejections']:
            for gr in r['gate_rows']:
                measured = json.dumps(gr['measured'], ensure_ascii=False)
                if len(measured) > 90:
                    measured = measured[:87] + '...'
                measured = measured.replace('|', '\\|')
                reason = gr['reason'].replace('|', '\\|')
                reject_md.append(
                    f"| `{r['clip']}#{r['frame']:02d}` | `{gr['gate']}` | "
                    f"{json.dumps(gr['gate_value'], ensure_ascii=False)} | `{measured}` | {reason} | `{r['atlas_sha256'][:12]}` |")
        paused = rec['paused_check_streaks']
        if paused:
            reject_md.extend(['', '暂停项（连续 3 个不同帧）：'])
            for key, v in paused.items():
                reject_md.append(f"- `{key}`：诊断图 `{v['diagnostic_image']}`；最多 2 种修法；只读复算不实施修法。")
        reject_md.append('')
    (OUT / 'rejections.md').write_text('\n'.join(reject_md) + '\n', encoding='utf-8')

    # review_index.md
    idx = [
        '# 七角色硬门只读复核索引（F3）',
        '',
        f'生成时点：{now}；frame_specs 抽查时点：{spec_time}。',
        '',
        '本目录只含只读复算产物。源 `assets/`、`content/`、`core/`、`input/`、`presentation/`、`ui/`、`art/` 均未改动；未创建 `raw/`、`cells/`、`frame_specs`；未 commit、未跑 Godot / `tools/verify.py`、未动锁。',
        '',
        relocation_note,
        '',
        '## 每角色硬门通过 / 拒收计数',
        '',
        '| 角色 | clip | 帧 | 技术硬门通过帧 | 有拒收门帧 | 联系表绝对路径 |',
        '|---|---:|---:|---:|---:|---|',
    ]
    for row in index_rows:
        idx.append(f"| {row['display']} / `{row['fighter']}` | {row['clips']} | {row['frames']} | {row['pass']} | {row['reject']} | `{row['sheet']}` |")
    idx.extend([
        '',
        '“通过帧”只指本轮列举的逐帧技术门全部通过；不表示造型、画风、动作连续性、美术、听感或实机通过。检查数量、文件数量、联系表张数均不冒充美术完成。',
        '',
        '## 硬门与联系表产物',
        '',
        f'- 逐帧结果：`{OUT / "hard_gate_results.json"}`',
        f'- 拒收 JSON：`{OUT / "rejections.json"}`',
        f'- 拒收 Markdown：`{OUT / "rejections.md"}`',
        f'- 联系表目录：`{SHEETS}`',
        f'- 暂停项诊断图目录：`{DIAG}`',
        f'- 本索引：`{OUT / "review_index.md"}`',
        '',
        '## 站姿 / 差分 / 辉光摘要',
        '',
        '| 角色 | 站姿 >8% 帧 | 相邻站姿 >10% 对 | 相邻差分 <0.10 对 | 主体外 alpha≥16 最大 | 辉光拒收帧 |',
        '|---|---:|---:|---:|---:|---:|',
    ])
    for fid in IDS:
        c = all_results['characters'][fid]
        idx.append(
            f"| {c['display']} | {c['standing_summary'].get('height_fail', 0)} | "
            f"{c['standing_summary'].get('jump_fail', 0)} | "
            f"{c['silhouette_diff_summary'].get('adjacent_fail', 0) + c['silhouette_diff_summary'].get('loop_fail', 0)} | "
            f"{c['halo_summary'].get('max_alpha16_outside', 0)} | "
            f"{c['halo_summary'].get('halo16_fail', 0) + c['halo_summary'].get('halo200_fail', 0)} |")
    idx.extend([
        '',
        '辉光口径：主体＝`alpha≥200` 最大 4 邻域连通块，7×7 MaxFilter 外扩 3 px；主体外 `alpha≥16 ≤100 px`、`alpha≥200=0`；`alpha 1–15` 尘点只登记不计入，不拿“主体外 alpha>0”判死。站姿集合取 `SEVEN_CHARACTER_REWORK_BRIEF.md` §1.1 明文集合；非站姿按姿态逐帧登记具体高度、bbox 宽度和 `sqrt(面积)/高度` 代理，代理与高度同方向大变记疑似整人缩放，不以“例外”二字放行。',
        '',
        '## atlas SHA 对应位置',
        '',
        '- 只读来源：七角色 `art/fighters/<id>/stage1/rework-20261112/asset_baseline.json` 的 `clips[clip].sha256` / `atlas_sha256`。',
        f'- 现场复算对应：`{OUT / "hard_gate_results.json"}` → `characters.<fighter>.clips[].atlas_sha_correspondence`（基线 SHA、manifest SHA、现场 SHA 与三者一致性）及 `clips[].frames[].atlas_sha256`。',
        f'- 拒收记录对应：`{OUT / "rejections.json"}` → `<fighter>.rejections[].atlas_sha256` 与 `atlas_sha_correspondence`；`rejections.md` 列 SHA 前 12 位。',
        '- 本轮没有生成请求、usage 或新贴图；未编造生成资源对应关系。',
        '',
        '## frame_specs 一次性抽查',
        '',
        f'抽查时点：`{spec_time}`（报告写完时）。F1/F2 并行补写，F3 不等待；该时点之外的变化不在本表内。',
        '',
        '| 角色 | 状态 | 目录 / 文件数 / 文本字数 |',
        '|---|---|---|',
    ])
    for s in frame_spec_snapshot:
        if s['directories']:
            entries = '；'.join(f"`{d['absolute_path']}` / {d['file_count']} 文件 / {d['total_chars']} 字符" for d in s['directories'])
        else:
            entries = '未发现 `frame_specs` 目录；0 文件 / 0 字符'
        idx.append(f"| {DISPLAY[s['fighter']]} / `{s['fighter']}` | {s['status']} | {entries} |")
    idx.extend([
        '',
        '## 已知 blockers',
        '',
        '- 七角色 `identity_ready.json` 均缺失，记 `spec_only/无 ready`；身份卡和只读诊断存在不等于身份锚已签。',
        '- 本轮无 `raw/`、无本轮 `cells/`；未生成任何新人物帧，未创建 `raw`、`cells`、`frame_specs`。',
        '- 本轮无生成请求、无 usage；未改动或补写 `docs/verification/README.md`。',
        '- 未跑 Godot、未跑 `tools/verify.py`、未动锁、未 commit；逻辑与资源登记未在本轮复验。',
        '- 双朝向 720/1080 实机画面未验；无录屏；未听审；未用户亲审。',
        '- 仅主游戏训练/F1 才能核实际画面；本目录联系表是装机 atlas 静态技术复算，不能写成实机通过。',
        '- `root_delegated_by_user` 由根统一签署，子代理不签；本目录不修改历史 `user_approved`。',
        '',
        '## 抽查和读取边界',
        '',
        '- `git log -5` 已在会话起首只读核；本轮未产生提交。',
        '- `clip_diagnosis.json` 的逐帧 bbox/height 与本轮装机 atlas 重算逐帧交叉核对；不一致写入 `hard_gate_results.json` → `characters.<fighter>.clip_diagnosis_disagreements` 与对应 clip。',
        '- 联系表按最近邻 4× 从装机 atlas 重算，按人物 bbox 中心裁 256×256 显示窗；标注 clip/帧号、主体高度、相邻差分、拒收原因；每角色最多列前 192 帧，完整逐帧数据在 JSON。诊断图用 1× 定位窗，不承担严格 4× 审片。',
    ])
    (OUT / 'review_index.md').write_text('\n'.join(idx) + '\n', encoding='utf-8')

    print('WROTE', OUT)
    for row in index_rows:
        print(row['fighter'], 'frames', row['frames'], 'pass', row['pass'], 'reject', row['reject'], 'sheet', row['sheet'])
    print('frame_specs_snapshot_at', spec_time)
    for s in frame_spec_snapshot:
        print('SPEC', s['fighter'], s['status'], [d['file_count'] for d in s['directories']], [d['total_chars'] for d in s['directories']])


if __name__ == '__main__':
    main()

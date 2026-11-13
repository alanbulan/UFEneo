"""一次性只读诊断数据生成器（四角色，2026-11-12）。

本文件是生成诊断 JSON 的输入脚本，输出只写四个
art/fighters/<id>/stage1/rework-20261112 目录；作为本批只读证据保留，
不是正式工具入口，也不得作为新任务的批量执行器。
"""
# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
import collections
import glob
import hashlib
import json
import os
import re

import cv2
import numpy as np
from PIL import Image

ROOT = str(_layout_root)
ART = ROOT + '/art/fighters'
IDS = ['ultraman-king', 'zoffy', 'father-of-ultra', 'mother-of-ultra']
AUDIT = json.load(open(ROOT + '/reports/review/2026-11-12/seven-character-defects/audit.json'))['characters']
PHASE3 = json.load(open(ROOT + '/content/presentation/phase3_projectiles.json'))
POLICY = json.load(open(ROOT + '/content/presentation/charge_overlay_policy.json'))
DISPLAY = {'ultraman-king': '奥特之王', 'zoffy': '佐菲', 'father-of-ultra': '奥特之父', 'mother-of-ultra': '奥特之母'}
IDENTITY = {
    'ultraman-king': 'art/fighters/ultraman-king/stage1/cells/idle-candidate-v18-cell.png',
    'zoffy': 'art/fighters/zoffy/stage1/cells/idle-00-cell.png',
    'father-of-ultra': 'art/fighters/father-of-ultra/stage1/cells/idle-candidate-01-cell.png',
    'mother-of-ultra': 'art/fighters/mother-of-ultra/stage1/cells/idle-candidate-01-cell.png',
}
OFFICIAL = {
    'ultraman-king': [
        {'path': 'art/fighters/ultraman-king/sources/ref-04-front-full-official.png', 'kind': '圆谷官方现代真皮套正面全身', 'angle': '正面，身份/配色/体量；不作侧视判据', 'sha256': '7368fcc0f051bdcd14e4381917d884907331b959c04a29d709d8bf5c9c9a7237'},
        {'path': 'art/fighters/ultraman-king/sources/ref-03-side-full-uhs.jpg', 'kind': '同版 UHS 软胶第三方实拍', 'angle': '真 90° 全身；原图朝左，生成前镜像朝右；非官方皮套照', 'sha256': '55d82250e03c0fe4ea2307b7b52010cd7b7b922c2dd38b861c034f21cfe44d5f'},
        {'path': 'art/fighters/ultraman-king/sources/ref-02-side-head-upper.png', 'kind': 'Ultra-Act 同版手办侧头实拍（已镜像）', 'angle': '侧头/上胸结构；朝右', 'sha256': 'aa2e2b7f014d926e1db90aa76b444e6cab1e8e0d17568c99ed10a45cbfdc0c26'},
    ],
    'zoffy': [
        {'path': 'art/fighters/zoffy/sources/ref-02.png', 'kind': '圆谷官方英雄页全身皮套照', 'angle': '官方正面/主身份来源；不作 90° 侧视轮廓门', 'sha256': 'a64baa37fa9aba22f20c1c67197e350ee4adc46c122ff00489545e2e9119769e'},
        {'path': 'art/fighters/zoffy/sources/ref-01.webp', 'kind': '官方全身渲染对照', 'angle': '正面/站立；作辅助身份来源', 'sha256': '0bcdab23478fb8645c8486ca8cc988df7dda911646b77e8bd6febafeef8fb37f'},
    ],
    'father-of-ultra': [
        {'path': 'art/fighters/father-of-ultra/sources/ref-01.webp', 'kind': '官方全身图鉴照', 'angle': '正面/身份配色与双角结构，不作侧视轮廓门', 'sha256': '43852a3dae1c511f8b87e137b805a661f227ad411a0f3f2ed2cc887fe6cefed6'},
        {'path': 'art/fighters/father-of-ultra/sources/head-side-real-suit-01.jpg', 'kind': '现场真实皮套侧头/上胸', 'angle': '约 75–85° 近侧脸；裁图镜像为朝右；只核角/面罩结构', 'sha256': '789c410ddedaee99b949d506b5886f7870dae98c6045f74ea627faba687a4a25'},
        {'path': 'art/fighters/father-of-ultra/sources/side-figure-toybox-05.png', 'kind': 'S.H.Figuarts 同版第三方实拍裁图', 'angle': '真 90° 右侧视全身，只借轮廓/体量；去掉球关节玩具结构', 'sha256': '412e2b0f53abe1ab8b07069f9bbb75abb3c52b381bb577f96bd467d51906af9b'},
        {'path': 'art/fighters/father-of-ultra/sources/ultra-act-ua-10-original.jpg', 'kind': 'ULTRA-ACT 同版第三方实拍', 'angle': '真 90° 右侧视全身；当前固定侧视主要轮廓参照', 'sha256': 'baf1ee75f37821d9249ca1cde8c8c4c5bdb67e3d2e9d0c15e91bef5b407a64a7'},
    ],
    'mother-of-ultra': [
        {'path': 'art/fighters/mother-of-ultra/sources/ref-01.webp', 'kind': '官方全身图鉴照', 'angle': '正面/身份配色；不作 90° 侧视轮廓门', 'sha256': '80f8a3f7719d18d5a19f8571dbcb9320de0041c69b78d7e59790ed0499210012'},
        {'path': 'art/fighters/mother-of-ultra/sources/official-tsuburaya-20261109/UT_Hero_mother02.png', 'kind': '圆谷官方正面全身皮套照', 'angle': '正面；MOVES.md 仅记 SHA 前缀，本轮已核绝对路径与完整 SHA', 'sha256': 'c09674db1d049d0b4d16480ef7b50fad0f568072f67715eb02938f343dc21ab8'},
    ],
}
SIGNS = {
    'ultraman-king': {'rule': '朝右时冠球在前额上方、刃根从球后方向后上方掠；冠球/刃根 x 与眼列 x 比大小', 'official': 'ref-02 授权手办侧头朝左镜像后球在前 +59.8；ref-03 侧身朝左球在前 −52.5；v18 待机像素球在前 +15 px', 'visual': '现用锚实看：银冠顶部圆球在眼列右侧，刃向后上方扫；白须、金肩甲、红披风、紫银体、胸口红宝玉与腰带可辨', 'forbidden': '不得把「后端小球」写进提示词；不得用正面紧凑高冠判侧视'},
    'zoffy': {'rule': '现代银鳍版：中央纵鳍、淡黄杏仁眼、蓝圆胸灯、胸前 6 对星之勋章、肩/上臂 3 对 Ultra Breastar；前后判据以眼列/鼻尖朝右定前，胸灯与勋章 x 应在眼列后的躯干带', 'official': '圆谷官方页与 MOVES.md §1.2；ref-02 为主身份照；仓库无本人 90° 官方全身侧视照', 'visual': '装机待机可辨银头/中央鳍、红银体、蓝胸灯；勋章在联系表缩略图无法可靠逐颗分辨，不能以数值冒充已核', 'forbidden': '不混 1966 黑鳍版或《新·奥特曼》深蓝金设计；不把初代无勋章造型套用'},
    'father-of-ultra': {'rule': '双长角从额侧向前上弯起、远端向后掠，角根/角尖 x 与眼列 x 逐一同口径；面罩下颌无胡子', 'official': 'head-side-real-suit-01 约 75–85° 侧头 + ua-10/SH-Figuarts 真侧视；用户裁定无胡子', 'visual': '现用锚与装机帧均画红披风；用户裁定无胡子，但 MOVES.md 与旧提示词仍反复写「白须/捋须」，是明确身份规格冲突', 'forbidden': '不写白须/捋须，不把胡须当识别结构；不得给奥父写双马尾；披风按现用身份锚保留但须补可核来源'},
    'mother-of-ultra': {'rule': '双马尾/耳侧垂饰在眼列前后成对、头冠与额侧黄色识别点、红披风从肩后垂落；朝右时前侧垂饰 x 大于眼列 x', 'official': '圆谷官方角色页、日文维基与 MOVES.md §1；仓库 ref-01 与 UT_Hero_mother02 均为正面全身，无本人 90° 官方真实侧视照', 'visual': '现用锚与装机帧实看：双侧垂饰/双马尾结构、额侧黄点、红披风、蓝胸灯、红银修长体；披风展开可高过头顶，不得用整帧最高行当冠顶', 'forbidden': '不得把披风顶当冠顶；不把奥父双角/奥王银冠写进奥母提示词'},
}
ALLOW = {
    'ultraman-king': ['真实屈膝/下沉压缩', '腾空收腿与空中必杀', '倒地/被投/躺姿', '红披风惯性展开或高过头顶', '举起双拳超过头部列带'],
    'zoffy': ['真实屈膝/低蹲', '腾空/空中受身', '倒地/被投/躺姿', '压低蓄势（须用骨长/头壳证明）'],
    'father-of-ultra': ['真实屈膝/低蹲', '腾空/空翻/被投', '倒地/被投/躺姿', '红披风惯性展开'],
    'mother-of-ultra': ['真实屈膝/低蹲', '腾空收腿/空中受身', '倒地/被投/躺姿', '红披风惯性展开或高过头顶（冠顶只取眼列±26px头部列带）'],
}
RECOGNITION = {
    'ultraman-king': ['红眼/额灯', '胸口两颗红宝玉', '金肩甲/金腰带', '红披风', '白须', '银冠'],
    'zoffy': ['蓝色圆形计时器', '星之勋章', 'Ultra Breastar 肩章', '淡黄眼', '中央银鳍'],
    'father-of-ultra': ['蓝色胸灯', '浅金眼', '双长角', '红披风', '腰带'],
    'mother-of-ultra': ['额侧黄识别点/头冠', '双马尾垂饰', '蓝色胸灯', '红披风', '银十字/修长红银体'],
}
STORY_KEY = ['idle', 'walk_forward', 'walk_back', 'light1', 'light2', 'light3', 'heavy', 'special', 'special2', 'special3', 'air_special', 'dash_throw', 'launcher', 'hit_mid', 'down', 'ko', 'win', 'guard', 'turn', 'charge_start', 'charge', 'charge_stop']
STATIONARY = {'idle', 'walk_forward', 'walk_back', 'light1', 'light2', 'light3', 'heavy', 'special', 'special2', 'special3', 'launcher', 'hit_mid', 'guard', 'turn', 'charge_start', 'charge', 'charge_stop', 'crush', 'spin_heavy', 'tackle', 'throw_forward', 'throw_back', 'pulse', 'low_pulse', 'ranged_forward', 'motion_236', 'motion_623', 'motion_214', 'motion_22', 'motion_41236', 'block', 'blockstun', 'timeout', 'taunt', 'win'}
EXEMPT_CLIPS = {'down', 'ko', 'defeat', 'bounce', 'thrown_forward', 'thrown_back', 'thrown_air', 'thrown_dash', 'grabbed', 'hit_air', 'launch_rise', 'launch_fall', 'air_apex', 'air_rise', 'air_fall', 'air_tech', 'air_crush', 'air_pulse', 'air_special', 'air_throw', 'vertical_jump', 'flip_forward', 'flip_back', 'roll_forward', 'roll_back', 'wake', 'wake_low', 'wake_mid', 'crouch', 'crouch_start', 'crouch_guard', 'crouch_turn', 'crouch_light', 'crouch_light2', 'crouch_blockstun', 'crouch_rise', 'chase_takeoff', 'chase_light1', 'chase_light2', 'chase_end', 'dive', 'diagonal_light', 'diagonal_heavy', 'dash', 'dash_start', 'dash_stop', 'dash_light', 'dash_heavy', 'dash_throw', 'backstep', 'dodge', 'dodge_counter', 'back_counter', 'guardbreak', 'slide', 'sweep', 'takeoff', 'land', 'intro', 'victory'}
SKILLS = {'special', 'special2', 'special3', 'air_special', 'motion_214', 'motion_22', 'pulse', 'low_pulse', 'air_pulse', 'ranged_forward', 'motion_236', 'motion_623', 'burst'}
PROJECTILE_CLIPS = {'pulse', 'low_pulse', 'air_pulse', 'ranged_forward', 'motion_214', 'motion_22', 'special', 'special2', 'special3', 'air_special'}
MOTION_PRIORITY = ['idle', 'turn', 'walk_forward', 'walk_back', 'special', 'special2', 'special3', 'air_special', 'dash_throw', 'down', 'ko', 'win', 'guard', 'launcher', 'hit_mid', 'light1', 'light2', 'light3', 'heavy', 'charge_start', 'charge', 'charge_stop', 'motion_22', 'diagonal_heavy', 'pulse', 'low_pulse', 'air_pulse', 'ranged_forward']
NO_CELL_PALETTE = {'ultraman-king': 'cells.json 旧 idle bbox/SHA 与 PROGRESS 文字存在冲突；本轮以装机 idle 整帧实测 32 色和当前文件 SHA 为准', 'zoffy': 'cells.json 顶层 anchor [96,184] 是旧值；装机 clip 级 anchor [128,248]，不得回落顶层'}
THREE_SLOTS = {
    'ultraman-king': [
        {'move': 'special', 'name': '王者闪光 King Flasher', 'evidence': '圆谷官方角色页列专名；《雷欧》第26话文字与 UGF 对波；光色黄/红来源冲突，本作取红', 'difference': '双掌收胸下沉→左右水平伸展→掌缘横推→收臂；红色横束由运行时承载', 'content_gap': '未核影片逐帧、时码、台词；帧序/数值为游戏编排'},
        {'move': 'special2', 'name': '洗礼光线 Baptism Beam', 'evidence': '圆谷官方角色页列专名；《雷欧》第39话识破假阿斯特拉', 'difference': '胸前红宝玉聚能→斜上张臂→红色能量箭；原剧为识破/净化，攻击化/多段/高削气为游戏改编', 'content_gap': '未核影片逐帧；多箭齐发待运行时扩展'},
        {'move': 'special3', 'name': '王者再生光线', 'evidence': '中文资料/粉丝维基记《雷欧》第50话复活雷欧；圆谷官方页未列该专名', 'difference': '脸前交叉双掌后推出蓝色长束；原剧复活，本作改攻击终结是游戏改编；不是 S1 同束改粗', 'content_gap': '官方专名与逐帧影片未核；不拿 King Shot 凑槽'},
    ],
    'zoffy': [
        {'move': 'special', 'name': 'Z光线', 'evidence': 'MOVES.md §1.4 记原剧电流型技能', 'difference': '双掌胸前合拢指尖相对→一并前推→收掌回护架；蓝白短程电流束', 'content_gap': '射程/帧序/颜色为游戏编排；准确帧色/时码未核'},
        {'move': 'special2', 'name': '超级冻霜', 'evidence': 'MOVES.md §1.4 记双掌冷冻气体', 'difference': '双掌收胸前→前推冷冻锥/场→收掌；120 tick 减速至 50% 为游戏编排', 'content_gap': '锥体尺寸、伤害/减速为游戏编排；未核逐帧影片'},
        {'move': 'special3', 'name': 'M87光线 A型', 'evidence': '圆谷官方页与 MOVES.md §1.3 记 M87；右掌前指、左掌靠计时器', 'difference': '右掌五指并拢前指、左手靠蓝胸灯→蓝白主束→收势；B 型不作第二格', 'content_gap': 'M87 准确帧色/帧数/音效、B 型色值、声优/叫招/时码未核'},
    ],
    'father-of-ultra': [
        {'move': 'special', 'name': '父亲射击 Father Shot', 'evidence': '圆谷官方页列特殊技；《艾斯》第38话、《梦比优斯》第37话文字依据', 'difference': '双臂 L 字、右臂垂直上举→右臂前缘发射→收臂；暖白为游戏定色', 'content_gap': '原剧光色无可靠记载；帧序/数值为游戏编排'},
        {'move': 'special2', 'name': '奥特之角·力量光束', 'evidence': 'Ultra Wiki/Namu/中文资料旁证 Ultra Horns / Power Beam 自双角发射', 'difference': '低头沉肩、双拳收胸→抬头前送；全套唯一角部发射，金色为游戏定色', 'content_gap': '原剧光色/逐帧未核；人物帧角不发光'},
        {'move': 'special3', 'name': '能量充填 Ultra Charge', 'evidence': 'Ultra Charge 为原剧给奥特战士补能，非攻击技', 'difference': '双掌收向彩色计时器、屈膝下沉→周身近身冲击→收势；不是第三束光线', 'content_gap': '自身回复 150 字段未运行时接入；Big Beam 剧中未使用，不拿来凑三级'},
    ],
    'mother-of-ultra': [
        {'move': 'special', 'name': '母亲光线', 'evidence': '圆谷官方页列 Mother Beam；日文维基/Fandom 记左腕母亲之蓝取能、右臂治疗', 'difference': '左腕取能→右掌覆胸前伸、蓝白治疗光环→收臂；0 伤害/回复/清眩晕', 'content_gap': '光色无文字来源；回复/清眩晕为游戏编排；未核集数/时码/台词'},
        {'move': 'special2', 'name': '母亲破坏光线', 'evidence': '日文维基记母亲光线破坏型变体、右臂发射、威力同级斯特利姆', 'difference': '左腕取能→右臂后收→右臂前送红金破坏光束；与 S1 治疗/攻击两种实际效果不同', 'content_gap': '红金为游戏取色；未核影片逐帧'},
        {'move': 'special3', 'name': '母亲淋浴', 'evidence': '日文维基记再生光雨/复活', 'difference': '双臂下垂→双臂上举→收臂；再生光雨由运行时 special_rings/special_spiral 占位承载，人物帧不画光雨', 'content_gap': '全场回复/限时复活为游戏改编且运行时未完全实现；special_spiral 是占位'},
    ],
}


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def apath(res):
    return ROOT + '/' + res.replace('res://', '')


def comps(mask, conn):
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=conn)
    return n - 1, sorted(stats[1:, cv2.CC_STAT_AREA].tolist(), reverse=True)


EFFECT_KEYS = {'effect', 'impact_effect', 'block_effect', 'spark', 'block_spark', 'trail_effect'}


def eff_ids(obj, acc):
    """只收真正会按 effect id 查表的字段；production_note 等长文本不是 id。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in EFFECT_KEYS and isinstance(v, str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{2,80}', v):
                acc.add(v)
            if k == 'projectile_impacts' and isinstance(v, dict):
                for src, hit in v.items():
                    if isinstance(src, str):
                        acc.add(src)
                    if isinstance(hit, str):
                        acc.add(hit)
            eff_ids(v, acc)
    elif isinstance(obj, list):
        for x in obj:
            eff_ids(x, acc)


def hand_point(mask, ax, ay, y_window=None):
    """与 tools/art/derive_fighter_data.py:196 同口径复算发射点。"""
    ys, xs = np.where(mask)
    if not len(xs):
        return [40, 90]
    work = mask
    if y_window:
        rows = np.arange(mask.shape[0])[:, None]
        world_y = ay - 1 - rows
        work = mask & (world_y >= int(y_window[0])) & (world_y <= int(y_window[1]))
        if not work.any():
            work = mask
    wys, wxs = np.where(work)
    xmax = int(wxs.max())
    x0 = max(0, xmax - 13)
    band = work[:, x0:xmax + 1]
    bys, bxs = np.where(band)
    cx = float(bxs.mean() + x0)
    cy = float(bys.mean())
    return [int(round(cx)) - ax, ay - 1 - int(round(cy))]


def normalized_mask(fighter, clip, frame=0, size=128):
    """本轮自算的归一化轮廓：裁主体 bbox 后最近邻到 128×128，按重心居中。"""
    m = json.load(open(ROOT + '/assets/fighters/' + fighter + '/animations/manifest.json'))['clips'][clip]
    r = m['rects'][min(frame, len(m['rects']) - 1)]
    im = np.asarray(Image.open(apath(m['texture'])).convert('RGBA'))
    a = im[r[1]:r[1] + r[3], r[0]:r[0] + r[2], 3] >= 128
    ys, xs = np.where(a)
    if not len(xs):
        return np.zeros((size, size), np.uint8)
    crop = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    small = cv2.resize(crop.astype(np.uint8), (size, size), interpolation=cv2.INTER_NEAREST) > 0
    return small.astype(np.uint8)


def clip_frame_data(m):
    p = apath(m['texture'])
    im = np.asarray(Image.open(p).convert('RGBA'))
    rects = m['rects']
    heights, masks, frame_meta = [], [], []
    for r in rects:
        x, y, w, h = r
        f = im[y:y + h, x:x + w]
        alpha = f[:, :, 3]
        body = alpha >= 128
        ys, xs = np.where(body)
        bb = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else [0, 0, 0, 0]
        height = int(bb[3] - bb[1] + 1) if len(xs) else 0
        n4, s4 = comps(body, 4)
        n8, s8 = comps(body, 8)
        solid = alpha >= 200
        ns, lab, stats, cent = cv2.connectedComponentsWithStats(solid.astype(np.uint8), connectivity=4)
        if ns > 1:
            idx = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
            main = (lab == idx)
            outer = cv2.dilate(main.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
            gap = (alpha >= 16) & ~outer
            gap200 = (alpha >= 200) & ~outer
            dust = (alpha >= 1) & (alpha < 16) & ~outer
        else:
            gap = np.zeros_like(body)
            gap200 = gap
            dust = gap
        rgb = f[:, :, :3].astype(np.int16)
        r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
        fx_like = body & (((r > 210) & (g > 210) & (b > 190)) | ((r > 210) & (g > 130) & (g < 235) & (b < 110)) | ((b > 190) & (g > 150) & (r < 140)))
        frame_meta.append({'index': len(masks), 'height': height, 'bbox': bb, 'body_pixels': int(body.sum()), 'components_4n': n4, 'component_areas_4n': s4[:8], 'components_8n': n8, 'component_areas_8n': s8[:8], 'halo_alpha16_outside': int(gap.sum()), 'halo_alpha200_outside': int(gap200.sum()), 'halo_dust_1_15_outside': int(dust.sum()), 'fx_like_color_pixels': int(fx_like.sum()), 'alpha_values': sorted(set(alpha[body].tolist()))[:8] if body.any() else [], 'alpha_binary': bool(np.all((alpha == 0) | (alpha == 255)))})
        masks.append(body)
        heights.append(height)
    diffs = []
    for i in range(1, len(masks)):
        a, b = masks[i - 1], masks[i]
        u = int((a | b).sum())
        x = int((a ^ b).sum())
        d = x / u if u else 1.0
        diffs.append({'from': i - 1, 'to': i, 'xor_over_union': round(d, 4), 'one_minus_iou': round(1 - int((a & b).sum()) / u if u else 0, 4), 'pass_ge_0_10': d >= 0.10})
    if m.get('loop') and len(masks) > 1:
        a, b = masks[-1], masks[0]
        u = int((a | b).sum())
        x = int((a ^ b).sum())
        d = x / u if u else 1.0
        diffs.append({'from': len(masks) - 1, 'to': 0, 'loop': True, 'xor_over_union': round(d, 4), 'one_minus_iou': round(1 - int((a & b).sum()) / u if u else 0, 4), 'pass_ge_0_10': d >= 0.10})
    return {'atlas_path': p, 'frame_meta': frame_meta, 'heights': heights, 'diffs': diffs}


def state_oob(state, manifest):
    out = []
    for st, rows in state.items():
        if not isinstance(rows, list):
            continue
        n = len(manifest['clips'].get(st, {}).get('rects', []))
        if not n:
            continue
        spr = [r.get('sprite') for r in rows if isinstance(r, dict) and isinstance(r.get('sprite'), int)]
        if not spr:
            continue
        oob = [i for i, s in enumerate(spr) if s < 0 or s >= n]
        longest, cur, start, best = 1, 1, 0, (0, 1)
        for i in range(1, len(spr)):
            if spr[i] == spr[i - 1]:
                cur += 1
            else:
                cur, start = 1, i
            if cur > longest:
                longest, best = cur, (start, cur)
        if oob or longest >= 8:
            walk_state = st in {'walk', 'walk_forward', 'walk_back'}
            out.append({'state': st, 'timeline_rows': len(spr), 'max_referenced_sprite': max(spr), 'installed_frames': n, 'has_oob': bool(oob), 'oob_rows': oob[:30], 'oob_count': len(oob), 'max_same_sprite_run': longest, 'max_same_sprite_start_row': best[0], 'max_same_sprite_value': spr[best[0]], 'prolonged_same_sprite': longest >= 10, 'clamp_frozen_rows': [] if walk_state else [i for i, s in enumerate(spr) if s >= n][:30], 'side_view_sprite_override_active': not walk_state, 'note': 'side_view.gd:450 对 state=="walk" 不用 f.frame().sprite 覆盖显示索引；walk_forward/walk_back 的越界是数据与受击框口径失配，不得仅凭 OOB 断言走路画面冻结' if walk_state else '非 walk 状态显示索引取 f.frame().sprite 并 clampi；越界行会显示最后一帧'})
    return out


def move_oob(moves, manifest):
    out = []
    for mid, d in moves.items():
        fr = d.get('frames', [])
        if not isinstance(fr, list):
            continue
        n = len(manifest['clips'].get(mid, {}).get('rects', []))
        spr = [r.get('sprite') for r in fr if isinstance(r, dict) and isinstance(r.get('sprite'), int)]
        if not spr:
            continue
        oob = [i for i, s in enumerate(spr) if s < 0 or (n and s >= n)]
        longest, cur, start, best = 1, 1, 0, (0, 1)
        for i in range(1, len(spr)):
            if spr[i] == spr[i - 1]:
                cur += 1
            else:
                cur, start = 1, i
            if cur > longest:
                longest, best = cur, (start, cur)
        freeze = longest >= 10
        out.append({'move': mid, 'timeline_rows': len(spr), 'installed_frames': n, 'max_sprite': max(spr), 'sprite_oob': len(oob), 'max_same_sprite_run': longest, 'max_same_sprite_start_row': best[0], 'held_sprite': spr[best[0]], 'long_display_hold_candidate': freeze, 'note': '同 sprite 连排可能是逐 tick 显示持时，不等于数据冻结；须与 clip.ticks、发射 tick 和实机画面同时核'})
    return out


def main():
    for c in IDS:
        work = ART + '/' + c + '/stage1/rework-20261112'
        os.makedirs(work, exist_ok=True)
        manifest = json.load(open(ROOT + '/assets/fighters/' + c + '/animations/manifest.json'))
        cells = json.load(open(ROOT + '/art/fighters/' + c + '/stage1/cells/cells.json'))
        state = json.load(open(ROOT + '/content/fighters/' + c + '/state_frames.json'))
        moves = {os.path.basename(p)[:-5]: json.load(open(p)) for p in sorted(glob.glob(ROOT + '/content/fighters/' + c + '/moves/*.json'))}
        baseline = {'fighter': c, 'generated': '2026-11-12', 'manifest_path': ROOT + '/assets/fighters/' + c + '/animations/manifest.json', 'manifest_sha256': sha(ROOT + '/assets/fighters/' + c + '/animations/manifest.json'), 'top_level_cell': manifest['cell'], 'top_level_anchor': manifest['anchor'], 'clips': {}, 'state_frames': {'path': ROOT + '/content/fighters/' + c + '/state_frames.json', 'sha256': sha(ROOT + '/content/fighters/' + c + '/state_frames.json')}, 'definition': {'path': ROOT + '/content/fighters/' + c + '/definition.json', 'sha256': sha(ROOT + '/content/fighters/' + c + '/definition.json')}, 'moves': {'path': ROOT + '/content/fighters/' + c + '/moves/', 'file_count': len(moves), 'sha256': {k: sha(ROOT + '/content/fighters/' + c + '/moves/' + k + '.json') for k in moves}}, 'registered_effect_files': {}, 'readonly_do_not_overwrite': [ROOT + '/assets/fighters/' + c + '/animations/manifest.json', ROOT + '/content/fighters/' + c + '/state_frames.json', ROOT + '/content/fighters/' + c + '/definition.json', ROOT + '/content/fighters/' + c + '/MOVES.md', ROOT + '/content/presentation/phase3_projectiles.json', ROOT + '/content/presentation/charge_overlay_policy.json', ROOT + '/art/fighters/' + c + '/stage1/cells/cells.json']}
        clip_data = {}
        for cl, m in manifest['clips'].items():
            p = apath(m['texture'])
            s = sha(p)
            baseline['clips'][cl] = {'atlas_absolute_path': p, 'atlas_sha256': s, 'manifest_atlas_sha256': m.get('atlas_sha256'), 'sha_matches_manifest': s == m.get('atlas_sha256'), 'cell': m['cell'], 'anchor': m['anchor'], 'anchors': m.get('anchors'), 'rects': m['rects'], 'ticks': m['ticks'], 'loop': m.get('loop', False)}
            clip_data[cl] = clip_frame_data(m)
        for eid, v in PHASE3.items():
            tex = v.get('texture')
            if not tex:
                continue
            hit = (c == 'ultraman-king' and (eid.startswith('king_fx') or eid.startswith('ultraman_king_fx'))) or (c == 'zoffy' and eid.startswith('zoffy_fx')) or (c == 'father-of-ultra' and eid.startswith('father_fx')) or (c == 'mother-of-ultra' and (eid.startswith('mother_fx') or eid.startswith('mother_of_ultra_fx')))
            if hit:
                ep = apath(tex)
                exists = os.path.exists(ep)
                a = sha(ep) if exists else None
                r = v.get('atlas_sha256')
                baseline['registered_effect_files'][eid] = {'effect_id': eid, 'registered': True, 'atlas_absolute_path': ep, 'atlas_sha256': a, 'registered_atlas_sha256': r, 'sha_matches': (a == r if r is not None else '未声明'), 'rects': v.get('rects'), 'ticks': v.get('ticks')}
        baseline['q_charge_policy'] = {'path': ROOT + '/content/presentation/charge_overlay_policy.json', 'sha256': sha(ROOT + '/content/presentation/charge_overlay_policy.json'), 'placement': POLICY['placements'].get(c)}
        baseline['phase3_projectiles'] = {'path': ROOT + '/content/presentation/phase3_projectiles.json', 'sha256': sha(ROOT + '/content/presentation/phase3_projectiles.json'), 'total_entries': len(PHASE3)}
        idp = ROOT + '/' + IDENTITY[c]
        im = Image.open(idp).convert('RGBA')
        arr = np.asarray(im)
        alpha = arr[:, :, 3]
        body = alpha >= 128
        ys, xs = np.where(body)
        colors = sorted(set(map(tuple, arr[body][:, :3].tolist())))
        conflicts = []
        if c == 'father-of-ultra':
            conflicts = ['用户裁定无胡子；MOVES.md 与旧提示词仍写白须/捋须，制作提示词必须删去胡须字样', '现用锚与装机帧均画红披风，但 MOVES.md 写当前身份锚没有披风；返工前按现用源定死有披风并补可核来源']
        if c == 'zoffy':
            conflicts = ['stage1 README 把 4× 定稿锚记作历史动作唯一参考；按现行规则改用待机像素整帧作唯一动作参考，4× 只保留配色/像素块口径']
        if c == 'mother-of-ultra':
            conflicts = ['MOVES.md 的官方正面来源只记 SHA 前缀；本轮已核绝对路径与完整 SHA，仍缺本人 90° 官方真实侧视全身照，侧视前后结构不能由正面图猜']
        card = {'fighter': c, 'display_name': DISPLAY[c], 'date': '2026-11-12', 'phase': '只读诊断，未生成/未安装', 'identity_anchor': {'absolute_path': idp, 'sha256': sha(idp), 'size': list(im.size), 'bbox': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())], 'installed_idle_atlas': apath(manifest['clips']['idle']['texture']), 'installed_idle_atlas_sha256': sha(apath(manifest['clips']['idle']['texture'])), 'visual_review': '已按原生格和七角色联系表实看；造型结论见 structure.visual', 'not_user_approved': True}, 'official_sources': [dict(x, absolute_path=ROOT + '/' + x['path']) for x in OFFICIAL[c]], 'structure': SIGNS[c], 'frozen_scale': {'production_cells_scale': cells.get('scale'), 'installed_scale_note': '2026-11-11 重标定后装机；以 cells.json 的 scale 为全套唯一比例，不许逐帧归一', 'cell': manifest['clips']['idle']['cell'], 'anchor': manifest['clips']['idle']['anchor'], 'baseline_foot_row': manifest['clips']['idle']['anchor'][1] - 1, 'installed_idle_standing_height': clip_data['idle']['heights'][0], 'anchor_source_stationary_height': cells.get('target_standing'), 'audit_idle_height': AUDIT[c]['idle_height'], 'per_clip_cell_anchor': '逐 clip 取自身 cell/anchor；不得用顶层旧 anchor，不得用本批第一组尺寸缩放其余组'}, 'palette': {'visible_colors_idle': len(colors), 'rgb': [[int(x) for x in t] for t in colors], 'frozen_32_colors_from_cells_json': cells.get('palette', []), 'recognition_colors': cells.get('palette_reserved_global_hues', []), 'recognition_structures': RECOGNITION[c], 'policy': cells.get('palette_policy', '从现用待机整图冻结 <=32 色并全套统一映射；保留识别色')}, 'limb_baseline': {'identity_anchor_bbox': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())], 'method': '以现用待机像素整帧的肩宽、上臂/前臂、大腿/小腿、拳与靴体量为唯一基准；原生格与最近邻 4× 目视，未编造数值', 'visual': '联系表实看：各角色头肩、手臂粗细、腿/靴体量；制作代理须在原生格逐帧对锚核，不以站距/色数/Alpha 代替'}, 'allowed_pose_exceptions': ALLOW[c], 'known_identity_conflicts': conflicts, 'visual_evidence': [ROOT + '/' + p for p in ['reports/review/2026-11-12/seven-character-defects/seven_idle.png', 'reports/review/2026-11-12/seven-character-defects/seven_walk_forward.png', 'reports/review/2026-11-12/seven-character-defects/seven_special.png', 'reports/review/2026-11-12/seven-character-defects/cross_idle.png', 'reports/review/2026-11-12/seven-character-defects/cross_walk.png', 'reports/review/2026-11-12/seven-character-defects/cross_special.png', 'reports/review/2026-11-12/seven-character-defects/cross_light1.png', 'reports/review/2026-11-12/seven-character-defects/grid_defects.png', 'reports/review/2026-11-12/seven-character-defects/' + c + '_A.png', 'reports/review/2026-11-12/seven-character-defects/' + c + '_B.png']], 'not_done': ['未生成图片', '未改 assets/content', '未启动 Godot', '无录屏', '未做双朝向720/1080实机审片']}
        with open(work + '/identity_card.json', 'w') as f:
            json.dump(card, f, ensure_ascii=False, indent=2)
        idle_clip = manifest['clips']['idle']
        idle_atlas = np.asarray(Image.open(apath(idle_clip['texture'])).convert('RGBA'))
        ir = idle_clip['rects'][0]
        ia = idle_atlas[ir[1]:ir[1] + ir[3], ir[0]:ir[0] + ir[2]]
        ibody = ia[:, :, 3] >= 128
        icolors = sorted(set(map(tuple, ia[ibody][:, :3].tolist())))
        card['palette']['installed_idle_frozen_palette_rgb'] = [[int(x) for x in t] for t in icolors]
        card['palette']['installed_idle_visible_colors'] = len(icolors)
        card['palette']['source_of_truth'] = '装机 idle 第0帧；奥王/佐菲 cells.json 未存 palette 字段，以装机待机整帧实测色板为全套冻结基线'
        if c in NO_CELL_PALETTE:
            card['known_identity_conflicts'].append(NO_CELL_PALETTE[c])
        with open(work + '/identity_card.json', 'w') as f:
            json.dump(card, f, ensure_ascii=False, indent=2)
        all_eff = set()
        eff_ids(state, all_eff)
        eff_ids(moves, all_eff)
        for v in POLICY['placements'].get(c, {}).values():
            if isinstance(v, dict) and isinstance(v.get('effect'), str):
                all_eff.add(v['effect'])
        def fx_sha_status(eid):
            v = PHASE3.get(eid)
            if not v or not v.get('texture') or not os.path.exists(apath(v['texture'])):
                return None
            reg = v.get('atlas_sha256')
            if reg is None:
                return '未声明 atlas_sha256，登记条目只核本轮实测 SHA'
            return reg == sha(apath(v['texture']))
        eff_status = {e: {'registered': e in PHASE3, 'atlas_sha_matches': fx_sha_status(e)} for e in sorted(all_eff)}
        for eid in sorted(all_eff):
            v = PHASE3.get(eid)
            if not v or not v.get('texture'):
                baseline['registered_effect_files'][eid] = {'effect_id': eid, 'registered': False}
                continue
            ep = apath(v['texture'])
            exists = os.path.exists(ep)
            if eid in baseline['registered_effect_files']:
                continue
            baseline['registered_effect_files'][eid] = {'effect_id': eid, 'registered': True, 'atlas_absolute_path': ep, 'atlas_sha256': sha(ep) if exists else None, 'registered_atlas_sha256': v.get('atlas_sha256'), 'sha_matches': fx_sha_status(eid), 'rects': v.get('rects'), 'ticks': v.get('ticks')}
        with open(work + '/asset_baseline.json', 'w') as f:
            json.dump(baseline, f, ensure_ascii=False, indent=2)
        move_effects = {}
        for mid, d in moves.items():
            acc = set()
            eff_ids(d, acc)
            shots = []
            for i, f in enumerate(d.get('frames', [])):
                if isinstance(f, dict) and f.get('shots') and isinstance(f['shots'], list):
                    for x in f['shots']:
                        if isinstance(x, dict):
                            shots.append({'tick': i, 'sprite': f.get('sprite'), 'effect': x.get('effect'), 'spawn': x.get('spawn'), 'anchor': x.get('anchor'), 'registered': x.get('effect') in PHASE3})
            move_effects[mid] = {'timeline_rows': len(d.get('frames', [])), 'startup': d.get('startup'), 'active': d.get('active'), 'recovery': d.get('recovery'), 'sprite_sequence': [x.get('sprite') for x in d.get('frames', []) if isinstance(x, dict)], 'effect_ids': sorted(acc), 'unregistered_effect_ids': sorted(e for e in acc if e not in PHASE3), 'shots': shots, 'projectile_impacts': d.get('feedback', {}).get('projectile_impacts', {}) if isinstance(d.get('feedback'), dict) else {}}
        idle_h = clip_data['idle']['heights'][0]
        diag_clips = {}
        categories = collections.Counter()
        four = collections.Counter()
        soob = state_oob(state, manifest)
        moob = move_oob(moves, manifest)
        for cl, m in manifest['clips'].items():
            f = clip_data[cl]
            h, diffs = f['heights'], f['diffs']
            standing = cl in STATIONARY and cl not in EXEMPT_CLIPS
            dev = [{'frame': i, 'height': x, 'deviation_pct': round((x - idle_h) / idle_h * 100, 2), 'over_8pct': abs(x - idle_h) / idle_h > 0.08} for i, x in enumerate(h)]
            over8 = [x['frame'] for x in dev if x['over_8pct']] if standing else []
            jumps = [{'from': d['from'], 'to': d['to'], 'heights': [h[d['from']], h[d['to']]], 'change_pct': round(abs(h[d['to']] - h[d['from']]) / h[d['from']] * 100, 2) if h[d['from']] else None, 'over_10pct': abs(h[d['to']] - h[d['from']]) / h[d['from']] > 0.10 if h[d['from']] else False} for d in diffs if not d.get('loop')]
            over10 = [x for x in jumps if x['over_10pct']] if standing else []
            lowdiff = [d for d in diffs if d['xor_over_union'] < 0.10]
            independent = [{'frame': i, 'components_4n': q['components_4n'], 'component_areas_4n': q['component_areas_4n'], 'components_8n': q['components_8n'], 'component_areas_8n': q['component_areas_8n']} for i, q in enumerate(f['frame_meta']) if q['components_4n'] > 1 or q['components_8n'] > 1]
            halo = [{'frame': i, 'alpha16_outside': q['halo_alpha16_outside'], 'alpha200_outside': q['halo_alpha200_outside'], 'dust': q['halo_dust_1_15_outside'], 'fx_like_color_pixels': q['fx_like_color_pixels'], 'hard_fx_failure': q['halo_alpha16_outside'] > 100 or q['halo_alpha200_outside'] > 0} for i, q in enumerate(f['frame_meta']) if q['halo_alpha16_outside'] > 100 or q['halo_alpha200_outside'] > 0 or q['fx_like_color_pixels'] > 30]
            hard_fx = bool(independent) or any(h['hard_fx_failure'] for h in halo)
            cat, reasons = 'keep', []
            if any(x['move'] == cl and x['sprite_oob'] for x in moob) or any(x['state'] == cl and x['has_oob'] for x in soob):
                cat, _ = 'fix_timeline', reasons.append('state/move sprite 越界，presentation/side_view.gd:450 clampi 会冻结')
            if hard_fx:
                if cat == 'keep':
                    cat = 'redraw'
                reasons.append('独立连通块或主体外高 Alpha/大块亮色，须逐帧审片去除烘焙特效')
            if standing and (over8 or over10):
                if cat == 'keep':
                    cat = 'fix_scale'
                reasons.append('站姿类高度偏差>8%或相邻突变>10%')
            if lowdiff:
                if cat == 'keep':
                    cat = 'fix_pose'
                reasons.append('相邻剪影差分<0.10')
            if cl in SKILLS and len(lowdiff) >= max(2, len(h) // 3):
                cat, _ = 'redraw', reasons.append('技能帧序大段近重复，起手/发力/收势不成立')
            if cl in PROJECTILE_CLIPS and len(lowdiff) >= 2:
                cat, _ = 'redraw', reasons.append('投射类帧仅换手型或复制，须只画人物动作')
            if cl in ('down', 'ko', 'win', 'launcher', 'hit_mid', 'dash_throw', 'diagonal_heavy', 'motion_22', 'special', 'special2', 'special3', 'air_special', 'idle', 'walk_forward', 'walk_back', 'guard', 'turn', 'charge_start', 'charge', 'charge_stop'):
                if cat == 'keep':
                    cat = 'fix_pose'
                reasons.append('任务书点名且联系表实看存在模板化/帧序不足/逐帧身体运动不足')
            if cl in ('down', 'ko', 'win') and c in ('father-of-ultra', 'mother-of-ultra'):
                if cat in ('keep', 'fix_pose', 'fix_scale'):
                    cat = 'fix_identity'
                reasons.append('奥父/奥母 down/win/ko 与别角色模板化嫌疑；核本人披风、角/双马尾、头冠、蓝胸灯')
            if cl == 'idle' and len(h) == 1:
                cat, _ = 'redraw', reasons.append('待机仅1帧，不满足双脚固定仅呼吸的循环')
            if cl == 'walk_forward' and len(h) < 8:
                if cat != 'fix_timeline':
                    cat = 'redraw'
                reasons.append('前走仅%d帧，未达八相换腿' % len(h))
            if cl == 'turn' and len(h) < 3:
                if cat != 'redraw':
                    cat = 'fix_timeline'
                reasons.append('转身仅%d帧，状态帧引用到2，clamp冻结' % len(h))
            if cl == 'walk_back' and len(h) < 8:
                if cat == 'keep':
                    cat = 'fix_pose'
                reasons.append('后走仅%d帧，未达八相换腿，前/后走骨长与支撑点须同口径' % len(h))
            if cl == 'special3' and c == 'mother-of-ultra':
                cat, _ = 'redraw', reasons.append('S3 人物帧序含 11 tick 长持帧6/7，技能帧序未按 96 tick 逐相推进')
            diag_clips[cl] = {'classification': cat, 'classification_reasons': reasons, 'frame_count': len(h), 'cell': m['cell'], 'anchor': m['anchor'], 'ticks': m['ticks'], 'loop': m.get('loop', False), 'heights': h, 'standing_class': standing, 'pose_exception': not standing, 'anchor_stationary_height': idle_h, 'height_deviations': dev, 'over_8pct_frames': over8, 'adjacent_height_jumps_over_10pct': over10, 'adjacent_silhouette_diffs': diffs, 'low_diff_pairs': lowdiff, 'independent_components': independent, 'baked_fx_diagnostics': halo, 'frame_meta': f['frame_meta'], 'state_frames_oob': [x for x in soob if x['state'] == cl], 'move_frames_oob': [x for x in moob if x['move'] == cl], 'move_effect_registration': move_effects.get(cl, {}), 'needs_storyboard': cat != 'keep'}
            categories[cat] += 1
            four['keep' if cat == 'keep' else ('redraw' if cat == 'redraw' else ('fix_timeline' if cat == 'fix_timeline' else 'fix'))] += 1
        mcfg = json.load(open(ROOT + '/art/fighters/' + c + '/stage1/move_fx.json'))
        emissions = []
        for mid, d in moves.items():
            cfg = mcfg['moves'].get(mid, {})
            hy = cfg.get('hand_y')
            if not hy or mid not in manifest['clips']:
                continue
            clip = manifest['clips'][mid]
            im = np.asarray(Image.open(apath(clip['texture'])).convert('RGBA'))
            ax, ay = clip['anchor']
            for i, rect in enumerate(clip['rects']):
                x, y, w, h = rect
                mask = im[y:y + h, x:x + w, 3] >= 128
                calc = hand_point(mask, ax, ay, hy)
                dist = cv2.distanceTransform((~mask).astype(np.uint8), cv2.DIST_L2, 3)
                for tick, row in enumerate(d.get('frames', [])):
                    if not isinstance(row, dict) or row.get('sprite') != i or not row.get('shots'):
                        continue
                    for shot in row['shots']:
                        if not isinstance(shot, dict) or 'spawn' not in shot:
                            continue
                        sp = shot['spawn']
                        err = ((sp[0] - calc[0]) ** 2 + (sp[1] - calc[1]) ** 2) ** 0.5
                        cx, cy = int(ax + sp[0]), int(ay - 1 - sp[1])
                        mx = int(w - 1 - cx)
                        def body_distance(px, py):
                            if 0 <= px < w and 0 <= py < h:
                                return round(float(dist[py, px]), 3)
                            return None
                        right_d = body_distance(cx, cy)
                        mirror_d = body_distance(mx, cy)
                        emissions.append({'move': mid, 'timeline_row': tick, 'sprite': i, 'effect': shot.get('effect'), 'hand_y_window': hy, 'installed_spawn': sp, 'recomputed_hand_point': calc, 'hand_point_error_px': round(err, 3), 'pass_le_2px': err <= 2.0, 'right_body_distance_px': right_d, 'mirror_body_distance_px': mirror_d, 'bidirectional_body_distance_le_2px': (right_d is not None and mirror_d is not None and right_d <= 2.0 and mirror_d <= 2.0), 'method': '对当帧 alpha>=128 主体按 derive_fighter_data.hand_point 复算，并用 distanceTransform 测右向/镜像向发射点到人物本体的最近距离；这是贴体粗测，不代替按本人实际发射部位的人工标点与双向实机核验', 'registered': shot.get('effect') in PHASE3})
        templates = {}
        for cl in ('down', 'win', 'ko'):
            if cl not in manifest['clips']:
                continue
            masks = [normalized_mask(c, cl, i) for i in range(len(manifest['clips'][cl]['rects']))]
            templates[cl] = {'all_pairs': [], 'frame0_pairs': []}
            for other in IDS:
                if other == c or not (ROOT + '/assets/fighters/' + other + '/animations/manifest.json'):
                    continue
                om = json.load(open(ROOT + '/assets/fighters/' + other + '/animations/manifest.json'))['clips']
                if cl not in om:
                    continue
                others = []
                for j in range(len(om[cl]['rects'])):
                    mm = json.loads(json.dumps(om[cl]))
                    mm['_fighter'] = other
                    # 局部按 other 的 manifest 裁片，不走本角色 index
                    rr = om[cl]['rects'][j]
                    im = np.asarray(Image.open(apath(om[cl]['texture'])).convert('RGBA'))
                    a = im[rr[1]:rr[1] + rr[3], rr[0]:rr[0] + rr[2], 3] >= 128
                    ys, xs = np.where(a)
                    if not len(xs):
                        continue
                    crop = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
                    others.append((cv2.resize(crop.astype(np.uint8), (128, 128), interpolation=cv2.INTER_NEAREST) > 0).astype(np.uint8))
                for i, left in enumerate(masks):
                    for j, right in enumerate(others):
                        inter = int((left & right).sum())
                        union = int((left | right).sum())
                        pair = {'character': c, 'other': other, 'clip': cl, 'frame': i, 'other_frame': j, 'normalized_bbox_iou': round(inter / union, 4) if union else 0.0}
                        templates[cl]['all_pairs'].append(pair)
                        if i == 0:
                            templates[cl]['frame0_pairs'].append(pair)
            templates[cl]['all_pairs'].sort(key=lambda x: x['normalized_bbox_iou'], reverse=True)
            templates[cl]['frame0_pairs'].sort(key=lambda x: x['normalized_bbox_iou'], reverse=True)
            templates[cl]['max_iou'] = templates[cl]['all_pairs'][0]['normalized_bbox_iou'] if templates[cl]['all_pairs'] else None
            templates[cl]['top_cross_character_pairs'] = templates[cl]['all_pairs'][:6]
        known = {}
        if c == 'ultraman-king':
            known = {'motion_22_06_to_07': next((d for d in clip_data['motion_22']['diffs'] if d['from'] == 6 and d['to'] == 7), None), 'diagonal_heavy_heights': clip_data['diagonal_heavy']['heights']}
        elif c == 'father-of-ultra':
            known = {k + '_state_oob': [x for x in soob if x['state'] == k] for k in ['idle', 'walk_back', 'walk_forward', 'turn']}
        elif c == 'mother-of-ultra':
            known = {'diagonal_heavy_frame1_height': clip_data['diagonal_heavy']['heights'][1], 'dash_throw_frames2_3_heights': clip_data['dash_throw']['heights'][2:4]}
        diag = {'fighter': c, 'display_name': DISPLAY[c], 'date': '2026-11-12', 'scope': '只读诊断；遍历 manifest 全部 clip', 'methods': {'body': 'alpha>=128的人物体轮廓', 'height': 'alpha>=128最小包围盒高度；包括披风/伸展件，姿态例外单独判', 'silhouette_difference': '同 clip 相邻帧同坐标 alpha>=128 掩码 XOR / 并集 = 1-IoU；目标>=0.10', 'components': 'cv2 connectedComponentsWithStats，主口径4邻域，8邻域辅助', 'halo': 'alpha>=200最大连通块外扩3px；主体外 alpha>=16<=100、alpha>=200=0；alpha1-15只登记', 'scale': '站姿类对装机 idle 第0帧高度偏差>8%、相邻站姿高度突变>10%；姿态例外不判整人缩放', 'caveat': '高度/差分/FX色像素是自动证据，不替代原生格与4x造型审片'}, 'audit_baseline': {'idle_height': AUDIT[c]['idle_height'], 'clip_count': AUDIT[c]['clips'], 'audit_state_oob': AUDIT[c]['state_sprite_oob']}, 'recomputed_known_defects': known, 'template_similarity': templates, 'counts': {'manifest_clips': len(manifest['clips']), 'classification': dict(categories), 'four_buckets': dict(four), 'idle_frames': len(clip_data['idle']['heights']), 'walk_forward_frames': len(clip_data['walk_forward']['heights']), 'state_frames_oob': len(soob), 'state_frame_clips': len(state), 'move_json_count': len(moves)}, 'idle_loop': '1帧，无法呼吸循环' if len(clip_data['idle']['heights']) == 1 else '需按头部纵幅<=4px、相邻含首尾<=2px、横漂<=2px核循环', 'walk_forward_phase_count': len(clip_data['walk_forward']['heights']), 'state_frames_oob_and_freezes': soob, 'move_frames_oob_and_freezes': moob, 'emission_points': emissions, 'effect_id_registration': eff_status, 'q_policy': POLICY['placements'].get(c), 'three_slot_evidence': {'MOVES.md': ROOT + '/content/fighters/' + c + '/MOVES.md', 'source': '已逐项读 MOVES.md 与 moves/*.json；差异与内容缺口写入 storyboard.md', 'runtime_effects': '逐 move effect id 与 shots 在 move_effect_registration 登记', 'policy': 'effect id 登记与已声明 atlas SHA 不是当前缺陷；不得重复补登记当成果。重画帧后须按本人部位重核发射点', 'slots': THREE_SLOTS[c]}, 'rework_priority': [cl for cl in MOTION_PRIORITY if cl in diag_clips], 'clips': diag_clips}
        with open(work + '/clip_diagnosis.json', 'w') as f:
            json.dump(diag, f, ensure_ascii=False, indent=2)
        print(c, 'clips', len(diag_clips), 'cats', dict(categories), 'state_oob', len(soob), 'move_oob', sum(1 for x in moob if x['sprite_oob']), 'unreg_eff', sum(1 for x in eff_status.values() if not x['registered']))


if __name__ == '__main__':
    main()

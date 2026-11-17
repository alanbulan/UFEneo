"""由本角色 rework-20261112 的三个只读 JSON 生成 diagnosis.md / storyboard.md。

一次性诊断输入脚本，位于授权目录；不读取其它三个角色目录。
"""
# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
import json
import os
from pathlib import Path

ROOT = _layout_root
IDS = ['ultraman-king', 'zoffy', 'father-of-ultra', 'mother-of-ultra']
DISPLAY = {'ultraman-king': '奥特之王', 'zoffy': '佐菲', 'father-of-ultra': '奥特之父', 'mother-of-ultra': '奥特之母'}
KEYS = ['idle', 'walk_forward', 'walk_back', 'light1', 'light2', 'light3', 'heavy', 'special', 'special2', 'special3', 'air_special', 'dash_throw', 'launcher', 'hit_mid', 'down', 'ko', 'win', 'guard', 'turn', 'charge_start', 'charge', 'charge_stop']
PRIORITY = ['idle', 'turn', 'walk_forward', 'walk_back', 'special', 'special2', 'special3', 'air_special', 'dash_throw', 'down', 'ko', 'win', 'guard', 'launcher', 'hit_mid', 'light1', 'light2', 'light3', 'heavy', 'charge_start', 'charge', 'charge_stop', 'motion_22', 'diagonal_heavy', 'pulse', 'low_pulse', 'air_pulse', 'ranged_forward']
PERSONA = {
    'ultraman-king': {'body': '银冠球在前、刃向后掠；白须、金肩甲、红披风、胸前红宝玉、紫银体、金边银靴', 'no_fx': '人物帧只画人物与红披风布料；双手、白须、银冠、披风都不发光'},
    'zoffy': {'body': '中央银鳍、淡黄眼、蓝圆胸灯、星之勋章与肩章；红银体、无披风', 'no_fx': '人物帧只画人物；双掌和胸灯都不画电光、冰晶或能量球'},
    'father-of-ultra': {'body': '双长角向前上弯、远端向后掠，红披风、蓝胸灯、红银体；下颌无胡子', 'no_fx': '人物帧只画人物与红披风布料；角、胸灯和双掌都不发光'},
    'mother-of-ultra': {'body': '双马尾垂饰、额侧黄点、头冠、红披风、蓝胸灯、修长红银体', 'no_fx': '人物帧只画人物与红披风布料；头冠、胸灯、双掌和头顶都不画光雨/光环'},
}
SLOT = {
    'ultraman-king': [
        ('special', '王者闪光 King Flasher：圆谷官方角色页列专名；《雷欧》第26话与雷欧光线同发、UGF对波。原剧光色译作黄/红有冲突，本作取红；帧序与数值是游戏编排。双掌收胸下沉、左右水平伸展、掌缘横推、逐段收臂。'),
        ('special2', '洗礼光线 Baptism Beam：圆谷官方角色页列专名；《雷欧》第39话识破假阿斯特拉。原剧为识破/净化，本作红色能量箭、多段与高削气是游戏改编。胸前红宝玉聚能、斜上张臂、收臂。'),
        ('special3', '王者再生光线：中文资料/粉丝维基记《雷欧》第50话复活雷欧；原剧是复活，本作改攻击终结是游戏改编。脸前交叉双掌后推出、收势；不得把S1同束改色充三级。'),
    ],
    'zoffy': [
        ('special', 'Z光线：MOVES.md §1.4 记原剧电流型技能，双掌胸前合拢后前推；射程/帧序/颜色为游戏编排。'),
        ('special2', '超级冻霜：MOVES.md §1.4 记双掌冷冻气体；冷冻锥尺寸、减速120 tick至50%、伤害是游戏编排，不能沿S1同束改粗。'),
        ('special3', 'M87光线 A型：圆谷官方页与 MOVES.md §1.3 记M87；右掌五指并拢前指、左掌靠计时器，蓝白主束。B型不作第二格；准确帧色/帧数/时码未核，标内容缺口。'),
    ],
    'father-of-ultra': [
        ('special', '父亲射击 Father Shot：圆谷官方页列特殊技；《艾斯》第38话、《梦比优斯》第37话文字依据。双臂L字、右臂垂直上举后从右臂前缘发射；暖白是游戏定色。'),
        ('special2', '奥特之角·力量光束：Ultra Horns/Power Beam 由 Ultra Wiki/Namu/中文资料旁证；双角之间/角尖发射是全套唯一角部发射。金色为游戏定色；低头沉肩、抬头前送、收势。'),
        ('special3', '能量充填 Ultra Charge：原剧为给奥特战士补能，非攻击技；本作近身冲击与自身回复为游戏改编，回复字段待运行时接入。原剧不是第三束光线，三槽差异有据但须标内容缺口。'),
    ],
    'mother-of-ultra': [
        ('special', '母亲光线：圆谷官方页列 Mother Beam；日文维基/Fandom 记左腕母亲之蓝取能、右臂治疗。回复/清眩晕为本作编排，蓝白为游戏取色；不得画攻击束。'),
        ('special2', '母亲破坏光线：日文维基记母亲光线的破坏型变体、右臂发射；红金为游戏取色。与S1是治疗/攻击两种实际效果，不是同束改伤害。'),
        ('special3', '母亲淋浴：日文维基记再生光雨/复活。全场回复与限时一次再生为游戏改编，运行时未实现；special_spiral/special_rings 是运行时占位特效，人物帧只画双臂上举和收臂。'),
    ],
}


def fmt(x):
    return json.dumps(x, ensure_ascii=False) if not isinstance(x, str) else x


def main():
    for c in IDS:
        w = ROOT / 'art/fighters' / c / 'stage1/rework-20261112'
        d = json.loads((w / 'clip_diagnosis.json').read_text())
        card = json.loads((w / 'identity_card.json').read_text())
        base = json.loads((w / 'asset_baseline.json').read_text())
        clips = d['clips']
        counts = d['counts']
        oob = [x for x in d['state_frames_oob_and_freezes'] if x['has_oob']]
        holds = [x for x in d['move_frames_oob_and_freezes'] if x['long_display_hold_candidate']]
        emission = d['emission_points']
        emission_fail = [x for x in emission if not x.get('bidirectional_body_distance_le_2px')]
        scale8 = sum(len(v['over_8pct_frames']) for v in clips.values())
        adj10 = sum(len(v['adjacent_height_jumps_over_10pct']) for v in clips.values())
        lowdiff = [(cl, x['from'], x['to'], x['xor_over_union']) for cl, v in clips.items() for x in v['low_diff_pairs'] if x['xor_over_union'] < 0.10]
        indep = [(cl, x['frame'], x['component_areas_4n'], x['component_areas_8n']) for cl, v in clips.items() for x in v['independent_components']]
        hardfx = [(cl, x['frame'], x['alpha16_outside'], x['alpha200_outside'], x['fx_like_color_pixels']) for cl, v in clips.items() for x in v['baked_fx_diagnostics'] if x['hard_fx_failure']]
        softfx = [(cl, x['frame'], x['fx_like_color_pixels']) for cl, v in clips.items() for x in v['baked_fx_diagnostics'] if x['fx_like_color_pixels'] > 30 and not x['hard_fx_failure']]
        lines = []
        A = lines.append
        A('# %s 逐 clip 只读诊断（2026-11-12）' % DISPLAY[c])
        A('')
        A('本文件是阶段 A/B 只读诊断，不是制作完成记录。全部数值由 `.venv/bin/python tools/rebuild/seven-character-rework-20261112/diagnostic_probe.py` 对现装机 `assets/fighters/%s/animations/manifest.json`、atlas PNG、`content/fighters/%s/`、`phase3_projectiles.json` 与 `charge_overlay_policy.json` 重算；逐 clip 证据在 `clip_diagnosis.json`，资产 SHA 在 `asset_baseline.json`，身份卡在 `identity_card.json`，逐帧分镜在 `storyboard.md`。' % (c, c))
        A('')
        A('## 一、口径与自算结果')
        A('')
        A('- 主体 `alpha>=128`；4 邻域连通块为主、8 邻域辅助；帧高是主体最小包围盒高，披风/举拳/伸展件计入，姿态例外单列。')
        A('- 相邻剪影差分是同 clip 同坐标的 `XOR/Union = 1-IoU`，目标 ≥0.10；站姿类对装机待机第 0 帧高度偏差 >8%、相邻站姿高度突变 >10% 判不合格。')
        A('- 辉光门按 `alpha>=200` 最大连通块外扩 3 px：主体外 `alpha>=16 <=100 px`、`alpha>=200=0`；`alpha 1–15` 只登记。亮色像素只是局部启发式，接触表造型审片另算。')
        A('- 状态帧 `frames[].sprite` 越界在 `presentation/side_view.gd:450` 会被 `clampi` 到最后一帧；但 `state=="walk"` 不走该 sprite 覆盖分支，`walk_forward/walk_back` 的 OOB 只登记数据/受击框口径失配，不冒称画面冻结。移动连续同 sprite 是显示持时候选，不等于数据冻结。')
        A('- 本轮重算：%d 个 clip；四桶 `%s`；细分类 `%s`。' % (counts['manifest_clips'], fmt(counts['four_buckets']), fmt(counts['classification'])))
        A('- 主体高度：站姿类对锚偏差 >8%% 的帧 %d 个、相邻突变 >10%% 的相邻对 %d 个；相邻差分 <0.10 共 %d 对，前 12 对为 `%s`。' % (scale8, adj10, len(lowdiff), fmt(lowdiff[:12])))
        A('- 独立连通块：`%s`；硬辉光/主体外高 Alpha：`%s`。浅亮银/蓝灯色像素超过 30 px 的软证据共 %d 帧，前 12 帧 `%s`，只用于排审片顺序，不自动判烘焙特效；4 邻域单连通也不能排除与手相连的特效，必须逐帧看原生格与 4×。' % (fmt(indep[:12]), fmt(hardfx[:12]), len(softfx), fmt(softfx[:12])))
        A('- 待机 %d 帧、前走 %d 帧、后走 %d 帧、转身 %d 帧；奥王/佐菲/奥父/奥母按 `REBUILD_2D_PLAN.md` 2.5.8 的待机 6、前/后走 8、转身 3 核。' % (counts['idle_frames'], counts['walk_forward_frames'], len(clips['walk_back']['heights']), len(clips['turn']['heights'])))
        A('- 状态 OOB：%s。' % fmt([{k: x[k] for k in ('state', 'timeline_rows', 'installed_frames', 'oob_count', 'side_view_sprite_override_active')} for x in oob]))
        A('- move 时间轴：%d 份 `moves/*.json`、sprite 越界 %d 份；长显示持时候选 `%s`。special/special2/special3 均自算为 72/80/96 行、sprite 0–15 逐相覆盖，并非全 0 冻结；10 tick 图集持时与 72/80/96 tick 时间轴须在重画后同时核。' % (counts['move_json_count'], sum(1 for x in d['move_frames_oob_and_freezes'] if x['sprite_oob']), fmt([(x['move'], x['max_same_sprite_run'], x['held_sprite']) for x in holds])))
        A('- 已知缺陷复算：`%s`。' % fmt(d['recomputed_known_defects']))
        tmpl = {k: v['max_iou'] for k, v in d['template_similarity'].items()}
        A('- 跨角色模板化自算：`down/win/ko` 与本代理负责的另外三个角色按主体 bbox 裁切、最近邻归一 128×128 后取 IoU；本角色最高值 `%s`，逐对数值在 `clip_diagnosis.json.template_similarity`。归一化轮廓只是同源嫌疑，不是身份验收；`down/ko/win` 还须按本人披风、双角/双马尾、头冠、胸灯实看重画。' % fmt(tmpl))
        A('')
        A('## 二、身份、比例、特效与接线')
        A('')
        A('- 现用待机像素整帧 `%s`，SHA `%s`；装机 idle atlas 与 manifest SHA %s。' % (card['identity_anchor']['absolute_path'], card['identity_anchor']['sha256'], '相符' if all(x['sha_matches_manifest'] for x in base['clips'].values()) else '有不符'))
        A('- 唯一 scale `%s`、待机格 `%s`、根点 `%s`、装机站高 `%s`；逐 clip 必须取自身 `cell/anchor/rects/ticks/anchors`。%s' % (card['frozen_scale']['production_cells_scale'], fmt(card['frozen_scale']['cell']), fmt(card['frozen_scale']['anchor']), card['frozen_scale']['installed_idle_standing_height'], '奥父 light1/light3/heavy/dash_heavy 用 256 格、light2 用 288 格；不得用 192 格缩放这些 clip。' if c == 'father-of-ultra' else '佐菲/奥父顶层 anchor 是旧值，不得回落。' if c in {'zoffy', 'father-of-ultra'} else '本角色顶层与 clip 级一致。'))
        A('- 冻结色板取装机 idle 第 0 帧实测 %d 色，保留 `%s`；`cells.json` 未存 palette 字段的奥王/佐菲须以 `identity_card.json.installed_idle_frozen_palette_rgb` 为制作基线。' % (card['palette']['installed_idle_visible_colors'], fmt(card['palette']['recognition_structures'])))
        A('- 标志结构：%s；已知冲突 `%s`。' % (card['structure']['rule'], fmt(card['known_identity_conflicts'])))
        A('- 姿势例外：`%s`；每例须登记主体高度、稳定头壳/骨长证据，不能用一句「例外」放行整人缩放。' % fmt(card['allowed_pose_exceptions']))
        A('- 本角色引用 %d 个 effect id，未登记 %d 个；已声明 atlas SHA 的条目全部相符。Q 三态 placement 在 `charge_overlay_policy.json` 齐备。任务书明确登记不是当前缺陷，禁止重复补登记；重画换贴图才需核 SHA。' % (len(d['effect_id_registration']), sum(1 for v in d['effect_id_registration'].values() if not v['registered'])))
        A('- 发射点：本次按 `derive_fighter_data.hand_point` 对当帧 `alpha>=128` 复算 %d 处，另测右向/镜像向到人物主体最近距离；双向贴体 >2 px 或距离缺失 %d 处，逐项在 `clip_diagnosis.json.emission_points`。这是贴体粗测，不代替按本人掌/角/胸灯实际发射部位的人工标点与实机双向核；四角色无 `content/fighters/<id>/emission_points.json` 人工依据表。' % (len(emission), len(emission_fail)))
        A('- 发射点与 `hand_point` 差异大的旧值多来自人工改点、特殊角部/胸前/天顶发射或早期生成规格；不得把本轮复算值直接覆盖运行时。重画帧后以新图集、新 `hand_y`、两朝向 720/1080 实机重取。')
        A('')
        A('## 三、三槽原剧依据与差异')
        A('')
        for mid, note in SLOT[c]:
            v = clips[mid]
            me = v['move_effect_registration']
            A('- `%s`（%s，%d 帧，%d/%d/%d tick，发射 %d 处）：%s' % (mid, v['classification'], v['frame_count'], me.get('startup', 0), me.get('active', 0), me.get('recovery', 0), len(me.get('shots', [])), note))
        A('- 三槽共同要求：技能人物帧只画身体，不画光束/光晕/颗粒/蓄气圈/贴掌光/能量球/飞行物；投射类 `pulse/low_pulse/air_pulse/ranged_forward` 手中也不得有能量球。`special*` 的束体、命中、Q 三态只走运行时 shots/impact/特效层。')
        A('')
        A('## 四、重点 clip 诊断')
        A('')
        A('| clip | 分类 | 帧数/格/根点 | 逐帧主体高度 | 越 8% 帧 | 相邻 >10% | 差分 <0.10 | 独立块/烘焙特效证据 | 动作与接线结论 |')
        A('|---|---|---|---|---|---|---|---|---|')
        for cl in KEYS:
            v = clips[cl]
            lo = [(x['from'], x['to'], x['xor_over_union']) for x in v['low_diff_pairs'] if x['xor_over_union'] < 0.10]
            A('| `%s` | %s | %d / %s / %s | %s | %s | %s | %s | 4n独立 %d，硬辉光 %d | %s |' % (cl, v['classification'], v['frame_count'], fmt(v['cell']), fmt(v['anchor']), fmt(v['heights']), fmt(v['over_8pct_frames']), fmt([(x['from'], x['to'], x['change_pct']) for x in v['adjacent_height_jumps_over_10pct']][:6]), fmt(lo[:6]), len(v['independent_components']), sum(1 for x in v['baked_fx_diagnostics'] if x['hard_fx_failure']), '；'.join(v['classification_reasons'][:3])))
        A('')
        A('`clip_diagnosis.json.clips` 覆盖全部 %d 个 clip；上表列任务书点名的 22 个基础/技能/状态 clip，其余逐帧高度、差分、连通块、cell/anchor/ticks、state/move 引用和分类同文件可查。' % counts['manifest_clips'])
        A('')
        A('## 五、返工顺序')
        A('')
        for i, stage in enumerate([
            '冻结阶段 A：先按 `identity_card.json` 定唯一待机像素整帧、真实侧视前后判据、唯一 scale、色板、四肢粗细和姿势例外；奥父先消「白须/捋须」与有披风两套规格冲突，奥母/佐菲登记缺 90° 官方侧视全身照。',
            '数据接线优先：奥父 idle/turn/walk_forward/walk_back 的 state sprite 越界与 1/4/1 帧缺口；walk 两向单独注明 side_view 不覆写显示索引，但仍要修状态帧/受击框口径。不留 clamp 假通过。',
            '基础动作重画：idle 6 相呼吸、前/后走 8 相接地点、turn 3 相；按 `storyboard.md` 的支撑脚、髋、肩、双拳、头、披风/角/垂饰逐帧生成，不许复制姿势。',
            '按 `clip_diagnosis.json.rework_priority` 修 fix_scale / fix_pose / fix_identity，先解决 >8%% 与 >10%% 体型跳档、down/ko/win 模板化，再修相邻差分 <0.10 的 skill/charge/pulse 帧。',
            '三槽与空中必杀：按 `SLOT` 本人原剧依据和 `storyboard.md` 的起手/发力/收势逐帧重画；技能帧只有人物本体，投射类只画手/身；奥父 S2 是唯一角部发射，奥母 S3 光雨不得进人物帧。',
            '逐 clip 安装与接线：`stage_cells.py` 唯一 scale 落格，`install_cells.py --only <clip> --merge`，重画后重核 atlas SHA、state/move sprite、发射点、effect id 已声明 SHA、Q 三态；不覆盖 `asset_baseline.json.readonly_do_not_overwrite` 之外的运行数据。',
            '实机双向审片：主游戏训练/F1，两朝向 720/1080，逐 clip 看循环、接地、起手/发射/收势、Q 三态、双方含披风完整 Alpha 取景；逻辑与美术验收分开报。',
        ], 1):
            A('%d. %s' % (i, stage))
        A('')
        A('优先 clip 顺序：`%s`。' % '` → `'.join(d['rework_priority']))
        A('- 三槽原剧依据、差异与内容缺口已写入 `clip_diagnosis.json.three_slot_evidence.slots`，逐 move 的 `data_source`、startup/active/recovery 与 shots 在 `clips[move].move_effect_registration`。')
        A('')
        A('## 六、每阶段验收命令与门值')
        A('')
        A('```bash')
        A('# 阶段 D：单帧唯一 scale 落格；每 clip 取自身 cell/anchor/rects/ticks/anchors')
        A('.venv/bin/python tools/art/stage_cells.py --fighter %s --scale-source <现用待机像素整帧> --target-standing %s --scale %s --cell <该clip自身格> --frame <clip>-00.png[@脚底行] --out-dir <本批在制目录>' % (c, card['frozen_scale']['anchor_source_stationary_height'], card['frozen_scale']['production_cells_scale']))
        A('# 阶段 E：逐 clip 安装，禁止全量覆盖')
        A('.venv/bin/python tools/art/install_cells.py --fighter %s --only <clip> --merge' % c)
        A('# 阶段 E：发射点人工依据表补齐后跑数据门（本轮诊断不写 content）')
        A('.venv/bin/python tools/rebuild/shared/emission_check.py --characters %s' % c)
        A('.venv/bin/python tools/rebuild/shared/q_charge_registry.py --dry-run')
        A('# 阶段 F：Godot 导入/验证/录制一律串行')
        A('.venv/bin/python tools/godot_lock.py -- .venv/bin/python tools/verify.py --keep-going')
        A('```')
        A('')
        A('- 每帧硬门：真透明二值 Alpha、≤32 色且整图统一映射、4 邻域人物主体单连通（8 邻域辅助）、四边不裁、站姿类对锚高度 ≤8%%、相邻站姿 ≤10%%、相邻剪影差分 ≥0.10、循环首尾接续、无烘焙特效/独立颗粒/飞行物。')
        A('- 辉光门：主体为 `alpha>=200` 最大连通块，外扩 3 px 后主体外 `alpha>=16 <=100 px`、`alpha>=200=0`；`alpha1–15` 尘点登记不计入。')
        A('- 时间轴门：`state_frames/moves.frames[].sprite` 全部落在相应 clip 的 `rects` 内；72/80/96/24 tick 的发射 tick、active 与收势落在真实身体运动上；walk 两向按 side_view 的 ticks 路径另核，不能以 OOB 或相同持时直接判冻结。')
        A('- 发射点门：按本人当帧实际掌/角/胸灯人工标点，双向原生误差 ≤2 px、不悬空不穿体；`emission_check.py` 只核数据表与运行坐标，不代替图形/手势。')
        A('- 特效登记：每个 effect id 在 `phase3_projectiles.json` 有条目，已声明 atlas SHA 字节相符；Q 三态按 `q_charge_registry.py` 口径。本轮已核，不作为新缺陷或返工成果。')
        A('- 实机门：`开始游戏.command` / `app/scenes/main.tscn`，训练/F1，两个朝向、720/1080、真实输入与独立回放；`verify.py --keep-going` 只证明逻辑/资源，不证明美术或听感。')
        A('')
        A('## 七、风险')
        A('')
        A('- 自动高度把披风、举拳或空中伸展计入主体包围盒；`fix_scale` 中真实屈膝/倒地/腾空须用稳定头壳和骨长证据登记，不能整人归一。')
        A('- 亮色启发式无法区分白须/银甲与烘焙光；硬连通块与辉光门仍需原生格、4× 联系表逐帧目视，不能以「检查数」冒称造型通过。')
        A('- 奥王 PROGRESS/cells.json 旧 bbox/SHA 与现装机文件有历史冲突，佐菲/奥父顶层 anchor 是旧值，逐 clip 安装时不得回落顶层。')
        A('- 奥父无胡子、奥王冠球在前、奥母缺真实侧视全身官方照；资料缺口未补前生成提示词可能复刻错误结构。')
        A('- 四角色无人工 `emission_points.json`；重画后若不按本人部位重取，束根会悬空或穿体。')
        A('- 三槽有原剧专名不等于已核逐帧影片；未核集数/时码/台词/光色的项保持内容缺口，不补写。')
        A('')
        A('## 八、本轮没做的事')
        A('')
        A('- 未生成任何图片；未改 `assets/`、未改 `content/`、未 git commit；未启动 Godot、未用 `tools/godot_lock.py` 录制，未做双朝向 720/1080 实机审片。')
        A('- 无录屏；未听审；用户未亲审；`root_delegated_by_user` 历史签署不等于 `user_approved`。')
        A('- 未复现同目录其它角色的诊断，未读写另外三个角色的制作文件；只读了公共规范、七角色审计表与联系表。')
        A('- 未把 57 项逻辑 PASS、722 条 phase3、effect id 齐备或文件数量写成美术通过。')
        (w / 'diagnosis.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

        # 逐帧分镜
        s = []
        B = s.append
        B('# %s 逐帧分镜规格（2026-11-12）' % DISPLAY[c])
        B('')
        B('本文件只给阶段 B 的返工分镜，不生成帧。所有分镜的共同身份是 `%s`；`%s`。' % (card['identity_anchor']['absolute_path'], PERSONA[c]['body']))
        B('每帧只允许一张待机像素整帧作参考，固定 90° 右侧视、完整人物不裁、真透明背景；只让关节和重心改变，不把人物整张放大/缩小，不换部件，不复制上一帧姿势。帧与帧之间手、臂、腿都有可见位移；相邻 `alpha>=128` 剪影 XOR/Union ≥0.10，循环 clip 末帧接首帧。')
        B('统一门：双脚固定或支撑脚世界坐标偏差 ≤±8 px；眼睛纵幅走路 ≤8 px、相邻 ≤4 px，待机头部纵幅 ≤4 px、相邻含首尾 ≤2 px、横漂 ≤2 px；站姿类高度对锚 ≤8%%、相邻站姿 ≤10%%。姿态例外写实际高度和骨长证据。')
        B('技能帧 `special/special2/special3/air_special/pulse/low_pulse/air_pulse/ranged_forward` 一律 `%s`；束体、弹体、命中、Q 蓄气只交给运行时，投射类手中不得有能量球/光刃/飞行物。' % PERSONA[c]['no_fx'])
        B('')
        B('## 一、三槽本人依据、差异与内容缺口')
        B('')
        for mid, note in SLOT[c]:
            B('- `%s`：%s' % (mid, note))
        B('- 所有 `air_special` 在 MOVES.md 均标「游戏改编，原剧无空中发射依据」；不冒充原剧镜头。')
        B('- `idle / walk_* / light* / heavy / launcher / hit_mid / down / ko / win / guard / turn / dash_throw / charge*` 的动作描述见 `content/fighters/%s/MOVES.md` 与 `content/fighters/%s/moves/*.json`，无原剧专名的一律按游戏编排，不编造招式。' % (c, c))
        B('')
        B('## 二、基础 clip 通用逐帧分镜')
        B('')
        B('以下 6/8/3 相为制作目标；装机现状帧数、现高度、现差分、不合格帧号见 `diagnosis.md` 与 `clip_diagnosis.json`。每格描述的是**目标帧相对前一帧**，不是对现装机帧的验收通过。')
        B('')
        B('| clip | 帧 | 支撑脚 | 髋 | 肩 | 双拳/掌 | 头与本人标志结构 | 与前帧位移 | 相邻/循环门 |')
        B('|---|---|---|---|---|---|---|---|---|')
        idle = clips['idle']
        for i in range(6):
            dy = [0, 1, 2, 2, 1, 0][i]
            B('| `idle` | %d | 前后错步双脚不动，脚外缘间距约站高 0.65–0.80，前脚外缘与后脚外缘保持同坐标 | 屈膝下沉 %d px，髋不左右漂 | 肩随呼吸 %s，肩宽同锚 | 双拳胸前护架，拳距与肩宽不变；仅胸廓呼吸带动 ≤1 px | 头壳/冠/角/垂饰朝右，眼列横漂 ≤2 px，纵幅 ≤4 px；披风只作 ≤2 px 布料回摆 | 头/肩一次下沉再回升，第 5 帧必须接第 0 帧 | 相邻含首尾剪影差分 0.02–0.10 的呼吸级变化另核；不得整体平移或换脚 |' % (i, dy, '微沉' if i < 3 else '微升'))
        for cl in ['walk_forward', 'walk_back']:
            for i in range(8):
                phase = ['接触', '承重下沉', '交错', '上升', '换腿接触', '承重下沉', '交错', '上升'][i]
                lead = '前脚' if i < 4 else '后脚'
                B('| `%s` | %d | %s先着地，另一脚脚跟离地；支撑点世界坐标偏差 ≤±8 px | 髋沿 4–6 px 平滑曲线，眼纵幅 ≤8 px、相邻 ≤4 px | 肩与髋反向小幅扭转，肩宽不变 | 双拳保持胸前护架，近/远拳随肩转 2–4 px，不甩直臂 | 头壳与本人标志结构固定侧视，披风滞后一相并留完整轮廓 | 手、臂、腿相对第 %d 帧均有可见位移；%s | 相邻差分 ≥0.10；第 7 帧接第 0 帧，不得滑步或瞬移换腿 |' % (cl, i, lead, (i - 1) % 8, phase))
        for i in range(3):
            B('| `turn` | %d | 前/后脚依次碾地换朝向，不用整图镜像代替转身 | 髋开始/完成 90° 侧视转身 | 肩随髋转，近远肩前后关系逐帧变 | 护架双拳由右视护架转左视护架，拳相对胸廓位置不跳 | 头随躯干转，本人冠球/角/垂饰前后关系随朝向翻转，不得反向 | 第 0 帧起转、1 帧过身、2 帧定左视；每帧四肢可见位移 | 3 帧与 state_frames.turn 0–2 一一对应；相邻差分 ≥0.10 |' % i)
        B('')
        B('## 三、按现装机逐 clip 逐帧分镜')
        B('')
        B('每个非 keep 的目标 clip 按下面顺序逐帧重画或修：先 `clip_diagnosis.json.clips[clip].heights` 找越界帧，再按 `adjacent_silhouette_diffs` 修相邻位移，最后按 `state_frames_oob`/`move_frames_oob` 接线。`keep` 只保留，不因文件存在就重写。')
        for cl in PRIORITY:
            v = clips.get(cl)
            if not v or v['classification'] == 'keep':
                continue
            B('')
            B('### `%s`（%s，现 %d 帧 → 目标 %s 帧，格 %s，根点 %s）' % (cl, v['classification'], v['frame_count'], '按状态帧/原剧帧序' if cl not in {'idle', 'walk_forward', 'walk_back', 'turn'} else {'idle': 6, 'walk_forward': 8, 'walk_back': 8, 'turn': 3}[cl], fmt(v['cell']), fmt(v['anchor'])))
            B('')
            B('现装机主体高度 `%s`；>8%% 帧 `%s`；相邻 >10%% `%s`；低差分 `%s`。' % (fmt(v['heights']), fmt(v['over_8pct_frames']), fmt([(x['from'], x['to'], x['change_pct']) for x in v['adjacent_height_jumps_over_10pct']]), fmt([(x['from'], x['to'], x['xor_over_union']) for x in v['low_diff_pairs'] if x['xor_over_union'] < 0.10])))
            if cl in {'idle', 'walk_forward', 'walk_back', 'turn'}:
                B('逐帧按上节 6/8/3 相表；修帧同时把 `state_frames.json.%s` 的 sprite 序列、hurtboxes 与显示 ticks 对齐，奥父尤其禁止 60/70/66/6 行对 1/4/4/1 帧。' % cl)
                continue
            if cl in {'special', 'special2', 'special3'}:
                mid = cl
                me = v['move_effect_registration']
                B('依据与三槽差异见本文件 §一，`MOVES.md` 与 `moves/%s.json`；装机时间轴 %d tick（%s/%s/%s），16 帧 sprite 0–15 已逐相覆盖，发射在 `%s`。' % (mid, me.get('timeline_rows', 0), me.get('startup'), me.get('active'), me.get('recovery'), fmt([(x['tick'], x['sprite'], x['effect']) for x in me.get('shots', [])])))
                for i in range(max(6, min(16, v['frame_count']))):
                    phase = '起手' if i < 5 else '蓄势/发力' if i < 10 else '束体持续发力' if i < 13 else '收势'
                    B('- 帧 %02d（%s）：支撑脚脚底贴同一根点，髋由蓄力侧转向前送再回正；肩与髋按 %s 分相，近/远臂肩肘腕拳逐帧前伸/回收 3–8 px，双拳从护架离开又回到护架；头与本人标志结构保持侧视，披风/角/垂饰按惯性滞后一相；与前帧手、臂、腿均有可读位移，差分目标 ≥0.10。只画人物，不画任何光束或发光。' % (i, phase, '本人三槽专属动作'))
                B('- 收势末帧须接回待机护架；发射 tick 必须落在实际伸手/角部/胸前姿态上；运行时光束/弹体/命中由已登记 effect id 承载，重画后重核发射点双向 ≤2 px。')
                continue
            if cl == 'air_special':
                B('游戏改编空中版，共 8 帧：0–2 浮空收腿、双拳收胸；3 发射相只画右视前下伸手/掌和躯干前压；4–5 身体继续下落、双臂回撤；6–7 收腿变伸腿准备落地。每帧鞋底离地高度按真实腾空登记，冠顶只取眼列±26 px 头部列带，披风/举拳高过头顶不算头变大。')
                continue
            if cl in {'pulse', 'low_pulse', 'air_pulse', 'ranged_forward'}:
                B('投射类只画手部与身体：起手收掌/收臂、发力伸掌/前推、收势回架；手中不得有能量球、光刃、飞行物或贴掌光。低姿/空中帧按真实蹲/腾空登记高度和骨长，不按整帧外框归一。')
                continue
            B('按 `clip_diagnosis.json` 的逐帧高度和差分逐格修：')
            for i, height in enumerate(v['heights']):
                prev = v['heights'][i - 1] if i else None
                diff = next((x['xor_over_union'] for x in v['adjacent_silhouette_diffs'] if x['from'] == i - 1 and x['to'] == i), None)
                B('- 帧 %02d：现高 %s px%s，现相邻差分 %s。目标保持待机锚的肩宽/臂粗/腿粗，按 `%s` 的支撑脚—髋—肩—双拳—头顺序改关节和重心；本人标志结构与披风随动作滞后；站姿类对锚站高 %s px 偏差 ≤8%%，相邻高度突变 ≤10%%，差分 ≥0.10。' % (i, height, ('，前帧 %s px' % prev) if prev is not None else '', diff if diff is not None else '—', cl, v['anchor_stationary_height']))
            if cl in {'down', 'ko', 'win'}:
                B('- 身份门：这组必须与别角色模板拉开姿势和本人披风/角/双马尾/头冠/蓝胸灯；倒地/躺姿高度变化须登记骨长，不能整人缩小；KO 与 down 不复用同一张图。')
            if cl.startswith('charge'):
                B('- Q 三态只有身体起势/保持/收势；人物帧不画周身蓄气圈，Q 光效只从 `charge_overlay_policy.json` 三态 placement 的已登记 effect id 走运行时。')
            if cl in {'guard', 'hit_mid', 'launcher', 'dash_throw', 'light1', 'light2', 'light3', 'heavy'}:
                B('- 动作起手、发力、收势按 `MOVES.md` 的本人描述；不把另一角色拳架/投技姿势改名沿用。投技逐帧核攻击方与受投方对位；升击核头部列带冠顶，不拿披风顶当头。')
        extra = [cl for cl, v in clips.items() if v['needs_storyboard'] and cl not in PRIORITY]
        B('')
        B('## 四、其余非 keep 的逐帧分镜')
        B('')
        B('以下 %d 个 clip 也标为需修/重画；逐帧用同一「支撑脚—髋—肩—双拳—头—本人标志结构—披风」格式，现高、差分和具体帧号按 `clip_diagnosis.json` 逐格读取，不额外复制通用模板。无额外 clip 时本节为空，不补写不存在的需求。' % len(extra))
        B('')
        B('| clip | 分类 | 逐帧主体高度 | 硬门与分镜要点 |')
        B('|---|---|---|---|')
        for cl in extra:
            v = clips[cl]
            B('| `%s` | %s | %s | 每帧脚底/根点与本人骨长稳定；手、臂、腿逐帧可见位移；相邻差分 ≥0.10；站姿类对锚 ≤8%%、相邻站姿 ≤10%%；姿态例外登记高度和骨长；`%s` |' % (cl, v['classification'], fmt(v['heights']), '；'.join(v['classification_reasons'][:2]) if v['classification_reasons'] else '无'))
        B('')
        B('## 五、逐 clip 相邻差分与循环接续门')
        B('')
        B('| clip | 现低差分对（from→to: XOR/Union） | 循环 | 接续要求 |')
        B('|---|---|---|---|')
        for cl in [k for k in KEYS if clips[k]['classification'] != 'keep']:
            v = clips[cl]
            lo = [(x['from'], x['to'], x['xor_over_union'], x.get('loop', False)) for x in v['low_diff_pairs'] if x['xor_over_union'] < 0.10]
            B('| `%s` | %s | %s | %s |' % (cl, fmt(lo[:8]), '是' if v['loop'] else '否', '末帧姿态/脚底/头部位移须接首帧' if v['loop'] else '末帧接后续状态或待机护架，不悬空/不整张平移'))
        B('')
        B('## 六、分镜使用边界')
        B('')
        B('- 本轮未生成图、未安装、未改 assets/content、未启动 Godot、无录屏；以上分镜是制作代理的规格，不是已返工证据。')
        B('- 每帧提示词须 150–250 字，只写该帧动作与本人固定识别结构，显式要求四肢粗细与待机锚一致；角色没有的部件不得写。技能帧不写光色，光色只在运行时特效规格定义。')
        (w / 'storyboard.md').write_text('\n'.join(s) + '\n', encoding='utf-8')
        print(c, 'diagnosis.md', len(lines), 'storyboard.md', len(s))


if __name__ == '__main__':
    main()

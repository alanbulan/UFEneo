"""从基础赛罗内容派生光辉赛罗的招式与内容数据。

只改：角色 id / 显示名 / 说明文字 / 特效 id（全部改为 pending_shining_*）。
帧数、启动-持续-收招、伤害、能量、受击框与判定数据保持原样，不复制任何人物帧。
不改共享 phase3/charge policy，不改基础赛罗内容。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'content/fighters/ultraman-zero'
DEST = ROOT / 'content/fighters/ultraman-zero__shining'
TOOLS = ROOT / 'tools/rebuild/ultraman-zero__shining'
FIGHTER = 'ultraman-zero__shining'

EFFECT_KEYS = {
    'effect', 'block_effect', 'impact_effect', 'return_effect', 'trail_effect',
    'spark', 'block_spark', 'projectile', 'projectile_impact', 'shot', 'shots',
}
GENERIC = {'pulse', 'impact_light', 'impact_heavy', 'impact_guard'}


def pending_id(value: str) -> str:
    if value.startswith('pending_shining_'):
        return value
    if value.startswith('zero_fx_'):
        return 'pending_shining_' + value[len('zero_fx_'):]
    if value in GENERIC:
        return 'pending_shining_' + value
    return value


def walk_effects(node, found: dict) -> None:
    if isinstance(node, dict):
        for key in list(node):
            new_key = key
            if key.startswith('zero_fx_'):
                new_key = 'pending_shining_' + key[len('zero_fx_'):]
            value = node[key]
            if new_key != key:
                found.setdefault(new_key, set()).add(key)
                del node[key]
                node[new_key] = value
                key = new_key
            if key in EFFECT_KEYS and isinstance(value, str):
                new = pending_id(value)
                if new != value:
                    found.setdefault(new, set()).add(value)
                node[key] = new
            elif isinstance(value, str):
                if 'zero_fx_' in value:
                    node[key] = value.replace('zero_fx_', 'pending_shining_')
            else:
                walk_effects(value, found)
    elif isinstance(node, list):
        for item in node:
            walk_effects(item, found)


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / 'moves').mkdir(exist_ok=True)

    found: dict[str, set[str]] = {}
    move_ids = []
    for path in sorted((BASE / 'moves').glob('*.json')):
        move = json.loads(path.read_text(encoding='utf-8'))
        move_ids.append(move['id'])
        walk_effects(move, found)
        move['data_source'] = (
            '沿用基础赛罗同名招式的帧数、启动/持续/收招、伤害、能量与判定；'
            '本形态动作帧待按光辉赛罗身份锚重新生成，当前未安装。'
        )
        move['production_note'] = (
            '未安装：本形态动作帧未生成；特效 id 已改为 pending_shining_*，'
            '须由主会话在 content/presentation/phase3_projectiles.json 登记后可见。'
        )
        (DEST / 'moves' / path.name).write_text(
            json.dumps(move, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    for name in ('move_manifest.json', 'command_table.json', 'state_frames.json'):
        data = json.loads((BASE / name).read_text(encoding='utf-8'))
        found_local: dict[str, set[str]] = {}
        walk_effects(data, found_local)
        for k, v in found_local.items():
            found.setdefault(k, set()).update(v)
        (DEST / name).write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    definition = json.loads((BASE / 'definition.json').read_text(encoding='utf-8'))
    definition['id'] = FIGHTER
    definition['display_name'] = '光辉赛罗'
    definition['production_status'] = 'stage1_identity_anchor_only'
    definition['playable'] = False
    definition['select_visible'] = False
    definition['selection_visible'] = False
    definition['numeric_status'] = (
        '占位设计参数，沿用基础赛罗；光辉赛罗站高 188、256 格、根点 [128,248]，'
        '动作帧未生成、未安装。'
    )
    definition['presentation'] = {
        'model': 'res://assets/fighters/ultraman-zero__shining/catalogue/model-native.png',
        'manifest': 'res://assets/fighters/ultraman-zero__shining/animations/manifest.json',
        'native': True,
        'cell': 256,
        'anchor': [128, 248],
        'target_height': 188,
        'height_basis': '头冠顶至脚底；光辉赛罗身份锚原生站高 188（cells.json target_standing_height）',
        'anchor_y': 248,
    }
    definition['forms'] = ['default']
    definition['identity_notes'] = (
        '银白底衣、金色胸肩臂腿甲与金纹、蓝眼、蓝色额灯、蓝色五角胸核、完整双头镖；'
        '无披风。身份锚为待机像素整帧，落格 256×256、根点 [128,248]、站高 188。'
    )
    definition['reference_file'] = 'content/fighters/ultraman-zero__shining/catalogue_profile.json'
    definition['production_stage'] = 1
    definition['model_review_pending'] = False
    definition['model_candidate'] = 'art/fighters/ultraman-zero__shining/stage1/cells/idle-00-cell.png'
    definition['stage2_status'] = 'stage1_identity_anchor_only'
    definition['pilot_playable'] = False
    definition['pilot_manual_ready'] = False
    definition['walks_installed'] = False
    definition['unsupported_moves'] = move_ids
    definition['pilot_lock_reason'] = (
        '状态片段、47 招、form_switch 与特效均未生成/安装；不得在选人界面开放。'
    )
    definition['selection_authorization'] = (
        'root_delegated_by_user：仅身份锚已签；待机/移动/受击等状态帧与招式帧尚未制作，暂不开放选择。'
    )
    definition['state_frames_note'] = (
        definition.get('state_frames_note', '')
        + ' 光辉赛罗当前未生成动作帧；state_frames.json 的逐帧受击框沿用基础赛罗占位，'
          '安装本形态帧后须用 recalc_move_hurtboxes 重算。'
    )
    (DEST / 'definition.json').write_text(
        json.dumps(definition, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    profile = json.loads((BASE / 'profile.json').read_text(encoding='utf-8'))
    profile['name'] = '光辉赛罗'
    profile['title'] = '赛罗奥特曼 · 光辉形态'
    profile['text'] = (
        '银白底衣配金色胸甲、肩甲、前臂甲与腿部金纹，蓝眼、蓝色额灯与蓝色五角胸核，'
        '完整双头镖；无披风。\n\n范围：仅光辉赛罗本形态，其它版本与形态待补。\n身高：未知。体重：未知。'
    )
    profile['model'] = 'res://assets/fighters/ultraman-zero__shining/catalogue/model-native.png'
    profile['profile_source'] = (
        'catalogue_profile.json 与身份锚记录；称号与简介只描述已核外观，不新增设定。'
    )
    (DEST / 'profile.json').write_text(
        json.dumps(profile, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    fx = {
        'schema': 1,
        'fighter': FIGHTER,
        'form': '光辉赛罗 / Shining Ultraman Zero',
        'note': '共享 phase3_projectiles.json 与 charge_overlay_policy.json 未修改；以下 id 需由主会话登记后才可见。',
        'effects': [],
        'charge_policy_proposal': 'tools/rebuild/ultraman-zero__shining/charge_policy.json',
    }
    roles = {
        'impact_light': 'hit_spark', 'impact_heavy': 'hit_spark', 'impact_guard': 'block_spark',
        'wide_hit': 'hit_spark', 'emerium_hit': 'hit_spark', 'slugger_hit': 'hit_spark',
        'wide_beam': 'beam', 'emerium_beam': 'beam', 'slugger_flight': 'projectile',
        'slugger_trail': 'trail', 'slugger_catch': 'return', 'pulse': 'projectile',
    }
    for new_id in sorted(found):
        short = new_id[len('pending_shining_'):]
        fx['effects'].append({
            'id': new_id,
            'source_id': sorted(found[new_id])[0] if found[new_id] else '',
            'role': roles.get(short, 'effect'),
            'status': 'pending_register',
            'note': '人物动作帧只含人物本体；光效由运行时特效层承载。',
        })
    for short, note in (
        ('q_charge_start', '真实 Q 起势局部蓄气，非周身蓄气圈；由 charge_overlay_policy 提案登记。'),
        ('q_charge', '真实 Q 保持段；循环 24 帧。'),
        ('q_charge_stop', '真实 Q 收势段；9 帧。'),
    ):
        fx['effects'].append({
            'id': 'pending_shining_' + short,
            'source_id': 'zero_fx_' + short,
            'role': 'charge_overlay',
            'status': 'pending_register',
            'note': note,
        })
    (TOOLS / 'fx-proposal.json').write_text(
        json.dumps(fx, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    charge = {
        'schema': 1,
        'fighter': FIGHTER,
        'note': '提案：共享 content/presentation/charge_overlay_policy.json 未修改；主会话登记后生效。',
        'placements': {
            FIGHTER: {
                'charge_start': {'effect': 'pending_shining_q_charge_start', 'anchor': [0, 0],
                                 'color': [1, 1, 1, 1], 'behind_fighter': True, 'frames': 9, 'loop': False},
                'charge': {'effect': 'pending_shining_q_charge', 'anchor': [0, 0],
                           'color': [1, 1, 1, 1], 'behind_fighter': True, 'frames': 24, 'loop': True},
                'charge_stop': {'effect': 'pending_shining_q_charge_stop', 'anchor': [0, 0],
                                'color': [1, 1, 1, 1], 'behind_fighter': True, 'frames': 9, 'loop': False},
            }
        },
        'requires_throw_hold': [],
    }
    (TOOLS / 'charge_policy.json').write_text(
        json.dumps(charge, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    print('moves', len(move_ids), move_ids[:5], '...')
    print('pending fx', len(fx['effects']))
    for e in fx['effects']:
        print(' ', e['id'], '<-', e['source_id'], e['role'])
    print('wrote', DEST, 'and fx proposal', TOOLS / 'fx-proposal.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""记录本席逐页实看结论；不改写现装素材与先前冻结盘点。"""
from pathlib import Path
import json
import hashlib

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'reports/review/2026-11-02/gomora-super3-victim-s5-whole-inventory-v1'
FIGHTERS = ['zetton', 'ultraseven', 'ultraman-arc', 'ultraman-blazar',
            'ultraman-omega', 'ultraman-teo', 'ex_gomora', 'ex_red_king', 'gomora']

def rec(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest())

NOTES = {
    'zetton': '空中及反弹均胸腹向上；被投有倒立/团身/仰面横躺。hit_mid虽前弯，双足站地，不能挪到背上冒充横伏。',
    'ultraseven': '空中/反弹/倒地及四投均后仰、仰卧或倒立团身；defeat跪倒后侧仰躺，无俯伏承重相。',
    'ultraman-arc': '空中与四投后仰/仰面落地，thrown_back[0]倒立不是俯伏。defeat[2]撑地侧坐，[3]仰面伸腿，无横伏相。',
    'ultraman-blazar': '反应/四投以胸向上后落为主；defeat[3]近臂贴地的侧前伏，躯干和腿压扁在地面，不能直接认定为悬空腹部承重。',
    'ultraman-omega': '空中/反弹/四投均后仰、仰卧或团身；defeat[3]仰面屈膝，无胸腹朝下横伏。',
    'ultraman-teo': 'thrown_forward[0]是胸朝下斜俯翻落的完整反应相，但躯干斜、双腿分叉屈伸，非横伏。其余空中/反弹/投落为仰面，defeat终相仍跪地。',
    'ex_gomora': 'defeat[2,3]真胸腹朝下，背棘向上、全尾完整；属于贴地塌伏，手足均压地，不具接背缓冲/手足下垂/抬升逐相。其他投/倒地为仰面或团身。',
    'ex_red_king': 'defeat[2,3]真胸腹朝下，背脊向上、双拳贴头/地；是弓背贴地伏倒，不具悬空腹部承重与抬升。thrown_forward[3]为仰面，不能误认。',
    'gomora': 'hit_crouch[2]低头四肢触地仍为下蹲；所有空中/反弹/倒地/四投/defeat横躺均腹面向上，无横伏承重源。',
}
CANDIDATES = {
    'ultraman-blazar': [('defeat', 3, '侧前伏贴地', '仅作姿态比较；不是直接可装横伏')],
    'ultraman-teo': [('thrown_forward', 0, '胸向下斜俯翻落', '仅可讨论raw20–23入背前俯向候选；缺自然到横伏的整相')],
    'ex_gomora': [('defeat', 2, '真实俯伏', 'raw24–31俯伏方向候选；贴地压臂足，未证实背上承重适配'),
                  ('defeat', 3, '真实俯伏', 'raw24–31俯伏方向候选；缺抬升和脱手起相')],
    'ex_red_king': [('defeat', 2, '真实俯伏', 'raw24–31俯伏方向候选；贴地大拳/头与本人背的交叠待实际Alpha核验'),
                    ('defeat', 3, '真实俯伏', 'raw24–31俯伏方向候选；无手足自然下垂与抬升整相')],
}

def main():
    results = []
    for fighter in FIGHTERS:
        inventory_path = OUT / fighter / 'inventory.json'
        inv = json.loads(inventory_path.read_text('utf-8'))
        for page in inv['pages']:
            assert rec(ROOT / page['path']) == page
        for record in inv['records']:
            assert rec(ROOT / record['source_atlas']['path']) == record['source_atlas']
        candidates = []
        for clip, index, pose, permitted in CANDIDATES.get(fighter, []):
            source = next(r for r in inv['records'] if r['clip'] == clip and r['frame'] == index)
            candidates.append(dict(clip=clip, index=index, pose=pose, limitation=permitted,
                source_atlas=source['source_atlas'], source_rect=source['source_rect'],
                current_same_named_state_ticks=[s['tick'] for s in source['state_frames_consumers']],
                ending_clip_uses_presentation_tick=source['ending_clip_uses_presentation_tick'],
                installation_approved=False, grip=None, hold_point_overrides=None))
        results.append(dict(fighter=fighter, inventory=rec(inventory_path),
            actual_full_pages_viewed=inv['pages'], every_listed_manifest_cell_visually_viewed=True,
            observation=NOTES[fighter], prone_or_forward_facing_candidates=candidates,
            post_release_existing_pose_sequence=dict(clip='thrown_back', frames=[0,1,2,3],
                availability='完整独立已装反应格存在；仅后段后翻/落地可继续配对候选，不表示从俯伏到该首相已经连续'),
            final_down_candidates=dict(clip='down', frames=[0,1]),
            required_continuity_missing=['真实空中当前姿态→背部承接', '胸腹落背缓冲',
                '腹腰承重且头足自然下垂', '随背坡改变抬升', '俯伏→后仰脱手首相'],
            complete_raw16_to71_victim_path_available=False))
    data = dict(schema=1, scope=FIGHTERS, review_authority='delegated_read_only_pose_inventory',
        whole_cell_review=True, native_details=rec(OUT / 'native-detail/index.json'), fighters=results,
        conclusion='两EX现有defeat[2,3]具真实胸腹向下完整源；布莱泽侧伏和提欧斜俯仅方向候选。九对象均未具连续接背—横伏承重—抬升—脱手整相，不能用已有后翻/仰卧格旋转或移根宣布完成。',
        source_changed=False, runtime_changed=False, godot_run=False, post_sent=False,
        unapproved_execution=['任何新受方生图', '产品安装', '受方抓点/背点设置', '复用待机或攻击代替缺相'])
    path = OUT / 'actual-visual-review.json'
    with path.open('x', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    (OUT / 'README.md').write_text('''# 哥莫拉背掀受方：限定九对象S5完整格实查

已实际逐页查看杰顿、赛文、亚刻、布莱泽、欧米伽、提欧、EX哥莫拉、EX雷德王、哥莫拉现装反应完整格。每人三页覆盖hit_high/mid/crouch/air、launch_rise/fall、bounce、down、defeat、grabbed及四种thrown；launcher是攻击，排除。现装名为hit_air，未见独立air_hit/trip clip。

报告从manifest精确rect裁完整格，每对象统一nearest缩小，不按bbox居中、不旋转、不变形、不换色、不拼件。每格记录源atlas/manifest/state_frames SHA、rect、anchor、simulation_sprite_offset及同名状态实际消费sprite的tick；defeat在正式结算由presentation时钟消费clip.ticks，不能把同名state_frames当作实际结算播放时长。本报告只读绑定，未运行Godot。

| 对象 | 本次实际看见 | 横伏承重/过渡结论 |
| --- | --- | --- |
| 杰顿、赛文、亚刻、欧米伽、哥莫拉 | 站蹲受击、后仰、仰卧、倒立或团身 | 无胸腹向下横伏整相 |
| 布莱泽 | defeat[3]侧前伏贴地，近臂和身体压地 | 只作方向比较，不认悬空腹部承重 |
| 提欧 | thrown_forward[0]胸朝下斜俯翻落 | 可讨论入背前俯向，但非横伏，缺连续承重/抬升 |
| EX哥莫拉 | defeat[2,3]真实胸腹向下、背棘向上、全尾完整 | 俯伏方向候选；手足贴地，缺背上承重、抬升和脱手起相 |
| EX雷德王 | defeat[2,3]真实胸腹向下，双拳贴头/地 | 俯伏方向候选；大拳/头与上背交叠未核，缺悬空承重和抬升 |

`native-detail/`将这些易混姿态另存完整原生格实际放大确认，尤其EX雷德王thrown_forward[3]仍是仰面，不能因轮廓平伏误用。两EXdefeat来源与当前结算用途保留，不改原资源、不改胜败状态。

九对象现有thrown_back完整后翻/落地格可继续用于raw44之后候选，down[0,1]可候选最终稳定倒地；这些后段存在不代表raw16–43接背、横伏承重和抬升已齐。当前无任何一人的整条受方连续路径获准安装；具体缺相与候选局限逐对象写入`actual-visual-review.json`。所有grip/hold_point_overrides仍为null，未扩大任何捕获框，未POST，未注册本人18相，未改产品。
''', encoding='utf-8')
    print(path)

if __name__ == '__main__':
    main()

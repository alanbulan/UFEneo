"""只读既有1966连续源，输出三级背掀对空投的新整帧合同；不装、不联网、不运行引擎。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REPORT = ROOT / 'reports/review/2026-11-02/gomora-super3-back-lift-contract-v1'
P2 = ROOT / 'reports/review/2026-11-02/gomora-super2-newsource-v1'

def read(p): return json.loads(p.read_text('utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p): return p.relative_to(ROOT).as_posix()
def record(p): return dict(path=rel(p), sha256=sha(p), bytes=p.stat().st_size)
def save(name, value):
    REPORT.mkdir(parents=True, exist_ok=True)
    with (REPORT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def main():
    current_paths = [ROOT / p for p in [
        'content/fighters/gomora/MOVES.md', 'content/fighters/gomora/references.json',
        'content/fighters/gomora/moves/special.json', 'content/fighters/gomora/moves/special2.json',
        'content/fighters/gomora/moves/special3.json', 'content/fighters/gomora/moves/motion_41236.json',
        'content/fighters/gomora/command_table.json', 'assets/fighters/gomora/animations/manifest.json',
        'assets/fighters/gomora/animations/special3/atlas.png',
        'core/combat/hit_resolver.gd', 'core/combat/move_data.gd', 'core/combat/throw_resolver.gd',
        'core/combat/throw_hold_points.gd', 'core/combat/match_director.gd',
    ]]
    before = {rel(p): sha(p) for p in current_paths}
    video = P2 / 'public-p2-research-source.mp4'
    assert sha(video) == '5cf3713fb8c42d78360a5387abbc317ab78a18509d31804cf9b9bdf2ffb53419'
    source_index = read(P2 / 'p2-back-lift-218p97-220p97-everyframe-index.json')
    assert source_index['video']['sha256'] == sha(video)
    pages = [record(ROOT / page['image']['path']) for page in source_index['pages']]
    full_index = read(P2 / 'p2-back-lift-full-index.json')
    full_pages = [record(ROOT / page['image']['path']) for page in full_index['pages']]
    source = dict(
        reviewer='subagent_ex_roll_review', root_acceptance=None,
        original_video=record(video), pts=record(P2 / 'public-p2-pts.json'),
        public_metadata=record(P2 / 'public-metadata.json'), acquisition=record(P2 / 'acquisition.json'),
        source_url='https://www.bilibili.com/video/BV1Gx411E7p9?p=2', bvid='BV1Gx411E7p9', cid=25931870,
        identity='1966哥莫拉第二战；本段已断尾、鼻角仍在。不是EX或大怪兽格斗版。',
        episode_boundary='上传说明为第26/27话剪辑；P2画面大阪城战对应第二战。未独立核完整第27话播出时码。',
        time_basis='本公开P2媒体原PTS；不是整集时钟', source_range_seconds=[218.970, 220.972],
        source_frames=[5249, 5297], every_source_frame_reopened_this_task=True,
        actual_opened_everyframe_pages=pages, actual_opened_full_pages=full_pages,
        facts=[
            dict(pts=[218.970, 219.304], fact='受方已横伏本人背上；本人俯身负重、双足承重、双臂低置。'),
            dict(pts=[219.346, 219.721], fact='本人以膝髋伸展挺背，受方随背部上升；不是鼻角发波或尾扫。'),
            dict(pts=[219.763, 220.305], fact='本人立胸伸展，受方从后背离开、翻落到本人后侧；本人双臂和肩胸随势。'),
            dict(pts=[220.347, 220.972], fact='受方在地面，本人向前收步、重新俯身稳重。'),
        ],
        not_proven=['起始怎样把受方捕到背上', '本作对空捕获窗口/可拆/费用/伤害/时钟',
                    '该段完整长尾动作：原片为断尾且部分头足画外', '官方技能名称'],
        design_boundary='只把有连续依据的负重挺背后抛作为成功段题材。空中实体相交捕获是本作规则；完整尾巴由本人干净定稿重新整帧设计平衡，不把原剧断尾画面伪写成完整尾巴。',
        redistribution='非官方用户上传原剧研究材料；分发授权未核，不进入运行包',
    )
    phase_actions = [
        ('沉髋起架', '双足承重，肩胸略降；近亮爪和远暗爪同时离开待机，尾随髋下沉。'),
        ('抬肩示警', '胸肩向上加载，两爪打开靠近肩颈两侧，肘角不同；不向地面对手伸手吸附。'),
        ('屈膝迎落', '双膝加深，头颈前让，背部成可承重的平缓斜面；双臂共同稳架。'),
        ('上背迎接', '前后足换重完成，两爪张开在上背旁准备托承；原地，不瞬移追人。'),
        ('实体承接', '肩背真实接触空中受方后才捕获；本人两爪内合托住接触腰身的位置。'),
        ('负重缓冲', '两膝屈曲、胸髋共同下降承重，双爪稍收，尾根跟髋而尾尖保持完整。'),
        ('俯身加载', '胸躯进一步前俯，肩胯协调，双爪不穿过受方；不能一臂静止。'),
        ('背负低点', '对应原片负重俯身成功段；两足牢固、双臂分侧稳重，完整尾沿臀后低弧。'),
        ('蹬地挺髋', '双膝伸展、髋先上升，肩胸随后抬起，双爪自然离开承托。'),
        ('挺背抬肩', '背部由倾斜转近直立；双方实体仍连续相贴，不用固定受方悬浮。'),
        ('伸髋送出', '腰背完整伸展，头颈抬起，双臂前后张开平衡，受方开始脱离后背。'),
        ('后抛松爪', '双爪完全松开，受方向后下方释放；本人近远臂均跟随卸力。'),
        ('前步随势', '本人小幅前俯卸重，支撑脚保持、另一足自然收步；不追加伤害。'),
        ('摔落定势', '受方真实着地时本人稳定双足，胸肩向前卸力，尾后撑；本人不拍地或加第三脚。'),
        ('卸力收臂', '双臂由张开回收，膝髋回中；同时用于落空后的自然回架。'),
        ('重心回中', '躯干从前俯恢复，尾由低弧回待机弧，双臂继续回护。'),
        ('举爪回护', '两爪回到待机前的防备位置；双肩、胸髋恢复，整尾不骤跳。'),
        ('复架', '完整本人回架，和独立待机自然接续；不复制待机或循环前相。'),
    ]
    phases = [dict(index=i, raw_ticks=[i*4, i*4+3], ticks=4, name=name,
                   whole_body_direction=action, source='new_independent_whole_frame_required',
                   hitboxes=None if i==4 else [], hurtboxes=None, grip=None if 4<=i<=10 else 'not_held')
              for i, (name, action) in enumerate(phase_actions)]
    old = read(ROOT / 'content/fighters/gomora/moves/special3.json')
    contract = dict(
        schema=1, status='new_whole_frame_production_contract_candidate_not_installable',
        fighter='gomora', form='1966 standard, intact runtime body', slot='special3',
        display_name='背掀震落（三级·本作编排）', official_skill_name=False,
        source_decision='source-decision.json', source_success_section_verified=True,
        root_source_and_design_acceptance=None,
        difference={'special':'低位尾段实体单击；蹲防／提前跳可避',
                    'special2':'地面掌压＋前蹬两段mid实体接触；可站蹲防',
                    'special3_candidate':'本人在地面承接空中受方后背掀后抛；真实抓取、可拆、后方落地一次结算',
                    'existing_motion41236':'保持零能地面正面抱起前压摔，不借其本人图或改其数据'},
        replaced_runtime=record(ROOT / 'content/fighters/gomora/moves/special3.json'),
        old_runtime_summary={k:old[k] for k in ['display_name','kind','damage','energy_cost','stamina_cost']},
        old_beam_preserved_and_running_until_complete=True,
        no_change_to_character_version=True, no_skill_scarcity_exception=True,
        existing_whole_sources_cover_new_action=False, new_whole_frames=18,
        new_core_required=True,
        minimal_generic_core_contract={
            'field':'throw_target_air', 'type':'bool', 'new_value':True,
            'location':'move data; used only when kind==throw',
            'missing_value_fallback':'attacker.move_id==air_throw，完全保留当前旧空投/地投判定',
            'logic':'eligible_air = move.get(throw_target_air, attacker.move_id==air_throw); require eligible_air == (target.height>0)',
            'validator':'存在时必须bool，且kind必须throw；禁止错误类型静默转bool',
            'fingerprint':'新增显式throw_target_air规则版本，旧指纹回放拒绝；新输入回放保持确定',
            'forbidden':'不新建哥莫拉专用分支；不改状态/伤害/输入或让其它旧投新增可抓目标',
            'not_implemented_in_this_task':True,
        },
        move=dict(id='special3', kind='throw', level='mid', super_level=3, energy_cost=3000,
                  stamina_cost=50, damage=490, chip_damage=0, unblockable=True,
                  startup=16, active=4, recovery=52, total_ticks=72, air_allowed=False,
                  throw_target_air=True, throw_schema=2, manual_projectiles=True,
                  invulnerability=False, armor=False, cancel=[], dx_all_ticks=0, dy_all_ticks=0,
                  whiff_branch_tick=20, whiff_recovery_tick=56, total_whiff_ticks=36,
                  projectile_count=0, damage_once_at_raw_tick=52,
                  all_numbers_are_game_design=True),
        capture=dict(raw_ticks=[16,19], attack_part='上背/肩和两爪真正承接的实体区域；新图实际量取',
                     hitboxes=None, target_must_be_airborne=True, real_box_intersection_before_hold=True,
                     front_ground_capture=False, auto_track=False, suction_before_contact=False,
                     victim_state_before_capture='实际air/air_attack/launch等可抓且未无敌状态；自然高度>0',
                     tech='沿既有捕获后第1/2/3真实tick投键拆投，含hitstop；不改核心窗口',
                     missing_hold_points='捕获前can_capture预检全部必用姿势，缺点拒绝，不抓中后才补点'),
        success=dict(hold_raw_ticks=[16,43], release_raw_ticks=[44,51], landing_raw_tick=52,
                     victim_not_baked_into_actor_sprite=True,
                     paired_contact='用双方整帧实测接触点，腰身在背部真实承重点；不按一张通用waist估算所有受方',
                     hold_point_overrides=None,
                     victim_poses='优先核现装grabbed/thrown_back/thrown_forward完整被投相；外观/朝向不合即新增本人整帧，不旋转拼肢',
                     grip_interpolation='各真实tick整数抓点随成品承重点连续；捕获首帧无远距瞬移、持握中不能穿躯干',
                     release='使用现有target.mode=release/progress；向本人后侧落地，目标root X负值，实际分离距离按整Alpha安全复核',
                     authored_landing_x=None, target_impact=True, count_throw_slam=1,
                     landing_no_interpenetration='沿既有landing_offset和靠墙配对整体平移，不能单独clamp受方断开接触'),
        geometry=dict(common_scale='先串行审关键承重07整源；以已审干净本人和本轮1/4基线核尺，整动作一个倍率，禁止逐相面积拟合',
                      cell=[512,320], anchor=[256,304], native_scale=1, full_tail_from_clean_master=True,
                      body_sources_reused_from_other_moves=False, region_recolor=False,
                      all_attack_and_hurt_geometry_pending_actual_png=True,
                      forbidden='不得剪旧半圈/尾扫/掌足/EX相、静图贴FX、拼肢、只换招名'),
        phases=phases,
        production_order=[7,4,9,11,5,6,8,10,12,13,0,1,2,3,14,15,16,17],
        fx_contract=[
            dict(id='gomora_back_lift_capture_contact', trigger='仅真实捕获hit事件', frames=5,
                 design='小面积土褐/乳白接触挤压碎点；不画光圈、鼻角光或Q蓄气', collision=False, anchor='真实接触交集'),
            dict(id='gomora_back_lift_release_dust', trigger='仅已捕获成功段松爪/释放；空挥分支不播', frames=7,
                 design='上背后方稀疏土尘和短弧风屑；本人背/手完整可见', collision=False, anchor='成品实际背部脱离点'),
            dict(id='gomora_back_lift_landing_dust', trigger='唯一throw_slam事件', frames=8,
                 design='受方落地土尘，横向扩散后透明消散；无远程地震判定', collision=False, anchor='真实受方落地点'),
        ],
        fx_backend='根2026-11-01授权PixelFX MIT固定a84159688af3ca37a4be05a0d422b94451b2e24e离线整帧真Alpha；不POST',
        fx_integration_limits='先核现有throw_slam是否消费move-specific FX；不假称现有feedback.spark会自动在落地播放；需表现叶只读事件接线时单独列精确变更',
        audio_contract='仅使用现有有归属证据的本人低吼/抓取/抬升/落地事件；本作数字拟音明确标注；不复用波音，不据原片画面冒称听审',
        cutin_contract='保留三级既有短冻结/专属背景流程；旧鼻角发束特写须用新本人整帧关键相制作专属定格后再替换，不先改运行引用',
        required_runtime_cases=['自然Q3000后P和J+K双入口；杰顿/赛文双向720/1080',
            '真实起跳落向上背才捕获；地面站/蹲/站防/蹲防全部空抓零伤；前方远跳/高跳未相交也空',
            '真实背后/头顶空中接触与双方完整Alpha、持握点和脱手的连续画面',
            '空中受方N无敌/本人起手受击/起手远程打断、落空收势J惩罚',
            '捕获后第1/2/3tick可拆，第4tick不可拆；同tick投碰撞保持通用规则',
            '不足3000真实P应按原等级选择；无取消、无无敌、无自动追踪',
            '前后墙配对不穿躯干/不分离抓点、后方落地不穿尾与地面',
            '全部可选及战斗可切形态受方逐完整被投姿势兼容；缺姿势不冒称已完成',
            '自然连续KO、暂停/恢复、F4尾段、R重建；独立原双方InputFrame逐tick/hash/事件/弹体',
            '新规则指纹拒绝旧文件；旧地投/空投修前后原输入行为逐tick保持'],
        install_gate='根先接受来源及本作对空捕获编排，18完整新源/实际双人抓点/FX/声音/新通用门落地并实机核过，才精确替换special3；当前合同不可安装',
    )
    assert len(phases)==18 and sum(p['ticks'] for p in phases)==72
    assert contract['move']['startup']+contract['move']['active']+contract['move']['recovery']==72
    assert sorted(contract['production_order'])==list(range(18))
    assert contract['move']['whiff_branch_tick']+72-contract['move']['whiff_recovery_tick']==36
    save('source-decision.json', source)
    save('new-whole-frame-contract.json', contract)
    assert before == {rel(p):sha(p) for p in current_paths}
    save('readonly-check.json', dict(protected_sources=before, protected_bytes_unchanged=True,
         existing_source_images_only=True, generated_videos=0, network_requests=0, image_posts=0,
         godot_runs=0, git_operations=0, runtime_writes=0, contract_not_installable=True,
         new_tool=record(Path(__file__).resolve())))
    print(json.dumps(dict(report=rel(REPORT), protected_bytes_unchanged=True, installable=False),ensure_ascii=False))

if __name__=='__main__': main()

"""根重算空地投规则实际证据并准备精确提交；不运行引擎、不改产品。"""
from pathlib import Path
import hashlib
import json

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'project.godot').is_file())
REPORT = ROOT / 'reports/review/2026-11-02/gomora-throw-target-rule-root-closeout-v1'
BEFORE = ROOT / 'reports/review/2026-11-02/gomora-super3-throw-target-step-baseline-v1'
AFTER = ROOT / 'reports/review/2026-11-02/gomora-super3-throw-target-step-after-v2'
PATCH = ROOT / 'reports/review/2026-11-02/gomora-super3-back-lift-throw-target-patch-v1'


def read(path):
    return json.loads(path.read_text('utf-8-sig'))


def ref(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    assert not REPORT.exists()
    before, after = read(BEFORE / 'baseline-result.json'), read(AFTER / 'after-result.json')
    assert not before['errors'] and not after['errors']
    assert before['only_input_steps'] and after['only_input_steps']
    for folder in [BEFORE, AFTER]:
        run = read(folder / 'root-run-result.json')
        assert run['exit_code'] == 0 and not run['diagnostics'] and run['source_bytes_held']
    legacy = {}
    for name, original in before['cases'].items():
        current = after['cases'][name]
        assert original['rows'] == current['rows'] and len(original['rows']) == 240
        assert original['fingerprint'] != current['fingerprint']
        assert original['captured'] and current['captured'] and original['slams'] == current['slams'] == 1
        assert current['victim_hp'] == 935
        assert [row[0] for row in current['rows']] == list(range(1, 241))
        legacy[name] = dict(ticks=240, complete_input_hash_event_snapshots_equal=True,
                            before_fingerprint=original['fingerprint'], after_fingerprint=current['fingerprint'])
    for rule in [False, True]:
        for target in [False, True]:
            case = after['cases'][f'explicit_{str(rule).lower()}_target_{str(target).lower()}']
            assert case['captured'] == (rule == target)
            assert case['slams'] == int(rule == target)
            assert case['victim_hp'] == (935 if rule == target else 1000)
    for delay in [1, 2, 3, 4]:
        case = after['cases'][f'tech_{delay}']
        assert case['captured'] and case['techs'] == int(delay <= 3)
        assert case['slams'] == int(delay == 4)
        assert case['victim_hp'] == (935 if delay == 4 else 1000)
    contract = read(PATCH / 'patch-contract.json')
    for row in contract['files']:
        assert ref(ROOT / row['path'])['sha256'] == row['proposed_sha256']
    assert 'throw_target_air' not in read(ROOT / 'content/fighters/gomora/moves/special3.json')
    REPORT.mkdir()
    record = dict(reviewer='root_delegated_by_user', accepted=True, scope='generic throw target rule only',
        baseline=ref(BEFORE / 'baseline-result.json'), final_result=ref(AFTER / 'after-result.json'),
        original_patch=ref(PATCH / 'patch-contract.json'), legacy=legacy,
        invalid_data_types_rejected_by_actual_godot_fixture=True,
        actual_old_fingerprint_rejection_and_new_replay_steps_verified_by_godot_fixture=True,
        true_false_target_gate=True, real_tick_tech_1_2_3_and_reject_4=True,
        fixture_v2_change='只在已有1/3/4真实拆投时点中补测第2tick；原脚本及首轮结果保全。',
        only_original_input_steps=True, body_art_approved=False, back_lift_move_installed=False,
        main_paired_contact_approved=False, goal_status='active')
    (REPORT / 'root-acceptance.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (REPORT / 'README.md').write_text(
        '# 通用空地投目标规则根签收\n\n'
        '本轮完成：新增仅对throw合法的布尔throw_target_air；true仅抓真实空中目标，false仅抓地面。缺省保留原air_throw规则，无角色专用分支。\n\n'
        '验证：默认站位经真实step接近、跳跃和出投，双方旧地投/空投完整240tick输入、状态hash、事件和snapshot与旧核一致；显式空地四组合及1/2/3tick拆投、4tick不可拆成立。Godot实际拒绝错误类型与非投招字段，旧规则指纹回放拒绝，新同指纹原输入逐tick重播一致。\n\n'
        '怎么看：本项是新独立对空投的通用规则准备，现装技能未改。完整依据见root-acceptance.json与原baseline/after目录；无生成录屏。\n\n'
        '已知问题：哥莫拉三级仍运行旧波，新背掀的完整本人、受方横伏相、接触点/落点、FX/声音和正式main配对尚未全齐，本签收不开放该招或装甲。原v1夹具与首轮结果保全，v2仅补第2tick拆投。\n\n'
        '下一步：继续月亮蹲姿族与哥莫拉背掀完整人物/受方。Goal active。\n', encoding='utf-8')
    folders = [PATCH, BEFORE, ROOT / 'reports/review/2026-11-02/gomora-super3-throw-target-step-after-v1', AFTER, REPORT]
    paths = {p for folder in folders for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    paths.update(ROOT / row['path'] for row in contract['files'])
    paths.update([Path(__file__), Path(__file__).with_name('run_throw_target_step_regression.py'),
                  Path(__file__).with_name('throw_target_step_regression.gd'), Path(__file__).with_name('prepare_throw_target_patch.py'),
                  ROOT / 'docs/HANDBOOK.md', ROOT / 'docs/CURRENT_DELIVERY_HANDOFF.md', ROOT / 'reports/review/README.md'])
    paths.add(REPORT / 'paths.nul')
    (REPORT / 'paths.nul').write_bytes(b'\0'.join(str(p.relative_to(ROOT).as_posix()).encode() for p in sorted(paths)) + b'\0')
    print(json.dumps(dict(accepted=True, scope='generic target rule', paths=len(paths), move_installed=False), ensure_ascii=False))


if __name__ == '__main__':
    main()

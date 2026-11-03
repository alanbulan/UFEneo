"""根审核后的一次性项目generate_image入口；默认只读预检，未知绝不重POST。"""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
REPORT = ROOT / 'reports/review/2026-11-02/gomora-back-lift-ultraman-phase02-brief-v1'
PLAN = REPORT / 'submission-plan.json'
OLD_UNKNOWN = '011ff77710ed49c9b441ed80f91733be'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text('utf-8-sig'))


def save_once(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def preflight():
    plan = read(PLAN)
    assert plan['production_approved'] is False, '准备稿本身不能冒充生产授权'
    for row in plan['frozen_inputs']:
        path = (ROOT / row['path']).resolve()
        assert path.is_relative_to(ROOT) and path.is_file() and sha(path) == row['sha256'], row['path']
    brief_path = ROOT / plan['brief']['path']
    brief = read(brief_path)
    output = (ROOT / plan['fixed_output']).resolve()
    intended = (ROOT / 'art/fighters/ultraman/stage5/gomora-super3-back-lift-receiver-20261102-v1/phase-02').resolve()
    assert output.is_relative_to(intended) and output.name == 'candidate.png'
    assert not output.parent.exists(), '固定请求目录已存在；保留原结果/未知记录，不换名重发'
    assert not (REPORT / 'execution/one-attempt.json').exists(), '本入口已消费；未知不重POST'
    sys.path.insert(0, str(ROOT / 'tools'))
    import art_pipeline as client
    config = client.local_image_config()
    assert client.image_route(config) == 'api'
    configured_url = os.environ.get('UFE_IMAGE_BASE_URL') or config.get('base_url', '')
    assert configured_url.rstrip('/') == 'https://api.openai.com/v1'
    fields = client.image_fields(brief, None)
    assert fields['model'] == 'gpt-image-2.5-sunburst'
    assert (fields['size'], fields['quality'], fields['background'], fields['n']) == ('1024x1024', 'high', 'transparent', 1)
    request_sha = hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()
    assert request_sha == plan['request_fields_sha256'], '实际模型/参数/提示词变化，必须另审'
    settings = config.get('official_budget') or {}
    reserve = Decimal(str(settings['reserve_usd']))
    limit = Decimal(str(settings['limit_usd']))
    assert reserve == Decimal('1') and reserve <= limit <= Decimal('60')
    ledger_path = Path(settings['ledger_path'])
    assert ledger_path.is_absolute() and ledger_path.is_file()
    ledger = read(ledger_path)
    assert ledger['schema'] == 'ufeneo.official-image-budget.v1' and Decimal(str(ledger['limit_usd'])) == limit
    total = sum((Decimal(str(row['committed_usd'])) for row in ledger['entries']), Decimal(0))
    assert total+reserve <= limit, '本机累计预算不足；未占额、未发请求'
    old = next(row for row in ledger['entries'] if row['id'] == OLD_UNKNOWN)
    assert old['status'] == 'reserved_remote_result_unknown' and Decimal(str(old['committed_usd'])) == Decimal('10')
    unknown = [row for row in ledger['entries'] if row['status'] == 'reserved_remote_result_unknown' and row['id'] != OLD_UNKNOWN]
    assert not unknown, '另有未知新请求；先恢复/核实，不叠加新POST'
    references = [ROOT / row['path'] for row in brief['references']]
    from PIL import Image
    for path in references:
        with Image.open(path) as picture:
            assert max(picture.size) <= 1024
    return client, plan, brief, output, references, dict(
        request_fields_sha256=request_sha, route='api', host='api.openai.com', model=fields['model'],
        request_size=fields['size'], quality=fields['quality'], background=fields['background'],
        reference_count=len(references), future_reserve_usd=str(reserve), project_limit_usd=str(limit),
        project_committed_usd=str(total), actual_account_balance_verified=False,
        historical_unknown_usd='10', budget_reserved_by_preflight=False, posts_sent_by_preflight=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='仅根审核并写入固定授权后执行一次')
    args = parser.parse_args()
    client, plan, brief, output, references, snapshot = preflight()
    if not args.execute:
        print(json.dumps(dict(mode='readonly_preflight', **snapshot), ensure_ascii=False))
        return
    gate_path = REPORT / 'root-submit-acceptance.json'
    gate = read(gate_path)
    assert gate.get('reviewer') == 'root'
    assert gate.get('root_reviewed_exact_brief_and_references') is True
    assert gate.get('authorized_one_serial_request') is True
    assert gate.get('expected_submission_plan_sha256') == sha(PLAN)
    assert gate.get('expected_brief_sha256') == plan['brief']['sha256']
    assert gate.get('expected_request_fields_sha256') == plan['request_fields_sha256']
    assert gate.get('fixed_output') == plan['fixed_output']
    assert gate.get('reserve_usd') == '1' and gate.get('no_retry_if_unknown') is True
    # 只在实际请求入口设置本进程并发1；预检不占用任何请求槽或预算。
    os.environ['UFE_IMAGE_SLOTS'] = '1'
    save_once(REPORT / 'execution/one-attempt.json', dict(
        state='attempt_consumed_remote_completion_unknown_until_evidence', plan_sha256=sha(PLAN),
        brief_sha256=plan['brief']['sha256'], request_fields_sha256=plan['request_fields_sha256'],
        acceptance_sha256=sha(gate_path), output=plan['fixed_output'],
        never_repost_from_this_entry=True, budget_begin_owned_by_project_generate_image=True,
        old_unknown_preserved=True, policy_snapshot=snapshot))
    invocation = argparse.Namespace(model=None, reference=references, out=output, dry_run=False,
        mask=None, pose_guide=None, layer_spec=None, parts_spec=None)
    try:
        client.generate_image(invocation, brief, '初代C型哥莫拉背掀受方phase02独立最低承重母相；未审候选，非运行资源')
    except BaseException as exc:
        save_once(REPORT / 'execution/exception.json', dict(
            exception_type=type(exc).__name__, remote_state='unknown_unless_project_metadata_or_ledger_proves_terminal',
            no_repost=True, no_budget_release=True, historical_unknown_preserved=True,
            inspect_fixed_output_and_ledger_only=True))
        raise
    metadata = output.with_suffix('.metadata.json')
    save_once(REPORT / 'execution/returned.json', dict(
        candidate_exists=output.is_file(), candidate_sha256=sha(output) if output.is_file() else None,
        metadata_sha256=sha(metadata) if metadata.is_file() else None,
        root_visual_review_pending=True, installable=False, no_second_submission=True))
    print(json.dumps(dict(candidate=plan['fixed_output'], root_visual_review_pending=True,
        no_retry=True, product_writes=0), ensure_ascii=False))


if __name__ == '__main__':
    main()

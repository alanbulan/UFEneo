"""初代其余五相：必须指定一相、根逐张签精确SHA后单次提交，默认只读预检。"""
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
REPORT = ROOT / 'reports/review/2026-11-02/gomora-back-lift-ultraman-remaining-five-briefs-v1'
PHASES = ('00','01','03','04','05')
OLD_UNKNOWN = '011ff77710ed49c9b441ed80f91733be'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text('utf-8-sig'))


def save_once(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(data,stream,ensure_ascii=False,indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def preflight(phase):
    directory=REPORT/'phases'/('phase-'+phase)
    plan_path=directory/'submission-plan.json'
    plan=read(plan_path)
    assert plan['phase']==int(phase) and plan['production_approved'] is False
    for row in plan['frozen_inputs']:
        path=(ROOT/row['path']).resolve()
        assert path.is_relative_to(ROOT) and path.is_file() and sha(path)==row['sha256'],row['path']
    brief=read(ROOT/plan['brief']['path'])
    assert brief['frame']==int(phase) and not brief['chain_edit'] and not brief['installed']
    output=(ROOT/plan['fixed_output']).resolve()
    intended=(ROOT/'art/fighters/ultraman/stage5/gomora-super3-back-lift-receiver-20261102-v1'/('phase-'+phase)).resolve()
    assert output.is_relative_to(intended) and output.name=='candidate.png'
    assert not output.parent.exists(),'固定请求目录已经存在；不换名、不覆盖、不重POST'
    assert not (directory/'execution/one-attempt.json').exists(),'本相入口已消费；保留未知，不重POST'
    sys.path.insert(0,str(ROOT/'tools'))
    import art_pipeline as client
    config=client.local_image_config()
    assert client.image_route(config)=='api'
    url=os.environ.get('UFE_IMAGE_BASE_URL') or config.get('base_url','')
    assert url.rstrip('/')=='https://api.openai.com/v1'
    fields=client.image_fields(brief,None)
    assert (fields['model'],fields['size'],fields['quality'],fields['background'],fields['n'])==('gpt-image-2.5-sunburst','1024x1024','high','transparent',1)
    digest=hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest()
    assert digest==plan['request_fields_sha256'],'实际模型/提示/参数变化，需根重新审核'
    settings=config.get('official_budget') or {}
    reserve=Decimal(str(settings['reserve_usd'])); limit=Decimal(str(settings['limit_usd']))
    assert reserve==Decimal('1') and reserve<=limit<=Decimal('60')
    ledger_path=Path(settings['ledger_path'])
    assert ledger_path.is_absolute() and ledger_path.is_file()
    ledger=read(ledger_path)
    assert ledger['schema']=='ufeneo.official-image-budget.v1' and Decimal(str(ledger['limit_usd']))==limit
    total=sum((Decimal(str(row['committed_usd'])) for row in ledger['entries']),Decimal(0))
    assert total+reserve<=limit,'本机累计预算不足，未预占或POST'
    old=next(row for row in ledger['entries'] if row['id']==OLD_UNKNOWN)
    assert old['status']=='reserved_remote_result_unknown' and Decimal(str(old['committed_usd']))==Decimal('10')
    assert not [row for row in ledger['entries'] if row['status']=='reserved_remote_result_unknown' and row['id']!=OLD_UNKNOWN], '另有新未知，先核原请求，禁止叠加POST'
    references=[ROOT/row['path'] for row in brief['references']]
    assert len(references)==3
    from PIL import Image
    for path in references:
        with Image.open(path) as picture: assert max(picture.size)<=1024
    return client,directory,plan_path,plan,brief,output,references,dict(
        phase=int(phase),request_fields_sha256=digest,route='api',host='api.openai.com',
        model=fields['model'],size=fields['size'],quality=fields['quality'],background=fields['background'],
        reference_count=3,future_reserve_usd=str(reserve),project_limit_usd=str(limit),project_committed_usd=str(total),
        historical_unknown_usd='10',actual_account_balance_verified=False,budget_reserved_by_preflight=False,posts_sent_by_preflight=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=PHASES,required=True)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    client,directory,plan_path,plan,brief,output,references,snapshot=preflight(args.phase)
    if not args.execute:
        print(json.dumps(dict(mode='readonly_preflight',**snapshot),ensure_ascii=False))
        return
    gate_path=directory/'root-submit-acceptance.json'
    gate=read(gate_path)
    assert gate.get('reviewer')=='root' and gate.get('phase')==int(args.phase)
    assert gate.get('root_reviewed_exact_brief_and_all_three_references') is True
    assert gate.get('authorized_one_serial_request') is True
    assert gate.get('expected_submission_plan_sha256')==sha(plan_path)
    assert gate.get('expected_brief_sha256')==plan['brief']['sha256']
    assert gate.get('expected_request_fields_sha256')==plan['request_fields_sha256']
    assert gate.get('fixed_output')==plan['fixed_output']
    assert gate.get('reserve_usd')=='1' and gate.get('no_retry_if_unknown') is True
    os.environ['UFE_IMAGE_SLOTS']='1'
    save_once(directory/'execution/one-attempt.json',dict(
        phase=int(args.phase),state='attempt_consumed_remote_completion_unknown_until_evidence',
        plan_sha256=sha(plan_path),brief_sha256=plan['brief']['sha256'],request_fields_sha256=plan['request_fields_sha256'],
        acceptance_sha256=sha(gate_path),output=plan['fixed_output'],never_repost_from_this_entry=True,
        budget_begin_owned_by_project_generate_image=True,policy_snapshot=snapshot))
    invocation=argparse.Namespace(model=None,reference=references,out=output,dry_run=False,
        mask=None,pose_guide=None,layer_spec=None,parts_spec=None)
    try:
        client.generate_image(invocation,brief,'初代C型哥莫拉背掀受方phase'+args.phase+'独立整人；未审候选，非运行资源')
    except BaseException as exc:
        save_once(directory/'execution/exception.json',dict(exception_type=type(exc).__name__,
            remote_state='unknown_unless_project_metadata_or_ledger_proves_terminal',
            no_repost=True,no_budget_release=True,old_unknown_preserved=True))
        raise
    metadata=output.with_suffix('.metadata.json')
    save_once(directory/'execution/returned.json',dict(candidate_exists=output.is_file(),
        candidate_sha256=sha(output) if output.is_file() else None,
        metadata_sha256=sha(metadata) if metadata.is_file() else None,
        root_visual_review_pending=True,installable=False,no_second_submission=True))
    print(json.dumps(dict(phase=int(args.phase),candidate=plan['fixed_output'],
        root_visual_review_pending=True,no_retry=True,product_writes=0),ensure_ascii=False))


if __name__=='__main__':
    main()

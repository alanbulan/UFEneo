"""指定单相的返回只读审计：真实尺寸/Alpha/usage与完整深浅JPEG；无POST、删分量或注册。"""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[4]
PHASES=('00','01','03','04','05')
BRIEFS=ROOT/'reports/review/2026-11-02/gomora-back-lift-ultraman-remaining-five-briefs-v1/phases'
REPORTS=ROOT/'reports/review/2026-11-02/gomora-back-lift-ultraman-remaining-returned-readonly-v1'
ART=ROOT/'art/fighters/ultraman/stage5/gomora-super3-back-lift-receiver-20261102-v1'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rec(path): return dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size)
def read(path): return json.loads(path.read_text('utf-8-sig'))


def save(path,data):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(data,stream,ensure_ascii=False,indent=2);stream.write('\n')


def component_counts(alpha,threshold):
    import numpy as np
    from scipy import ndimage
    labels,count=ndimage.label(alpha>=threshold,structure=np.ones((3,3),dtype=np.uint8))
    sizes=np.bincount(labels.ravel())[1:]
    return dict(alpha_threshold=threshold,connectivity=8,count=int(count),total_pixels=int(sizes.sum()),
        largest_component_pixels=int(sizes.max()) if count else 0,singleton_components=int(np.sum(sizes==1)),
        small_components_under_8_pixels=int(np.sum(sizes<8)),top_component_sizes=sorted(map(int,sizes),reverse=True)[:12],
        measurement_only=True,removed_components=0,component_selection_used_to_make_preview=False)


def readiness(phase):
    request=ART/('phase-'+phase)/'request-001'
    regular=request/'candidate.png'; rejected=request/'rejected/candidate.png'
    assert not (regular.is_file() and rejected.is_file()),'固定请求同时出现接受/拒收图，须先人工核实'
    candidate=regular if regular.is_file() else rejected
    provider=request/'candidate.provider.png'; metadata=candidate.with_suffix('.metadata.json')
    present=dict(candidate=candidate.is_file(),provider=provider.is_file(),metadata=metadata.is_file())
    return request,candidate,provider,metadata,present


def audit(phase):
    request,candidate,provider,meta,present=readiness(phase)
    if not all(present.values()):
        print(json.dumps(dict(phase=phase,status='not_ready_no_report_written',present=present,
            no_post=True,no_retry=True,no_budget_write=True),ensure_ascii=False))
        return
    out=REPORTS/('phase-'+phase)
    assert not out.exists(),'此相报告已冻结，不回写；需要新审核材料时另版本'
    brief_directory=BRIEFS/('phase-'+phase)
    brief_path=brief_directory/'brief.json'; plan_path=brief_directory/'submission-plan.json'
    gate_path=brief_directory/'root-submit-acceptance.json'
    brief=read(brief_path); plan=read(plan_path); gate=read(gate_path); metadata=read(meta)
    assert brief['frame']==plan['phase']==gate['phase']==int(phase)
    assert gate['reviewer']=='root' and gate['root_reviewed_exact_brief_and_all_three_references'] is True
    assert gate['authorized_one_serial_request'] is True and gate['expected_submission_plan_sha256']==sha(plan_path)
    assert gate['expected_brief_sha256']==sha(brief_path)==plan['brief']['sha256']
    assert metadata['request_sha256']==gate['expected_request_fields_sha256']==plan['request_fields_sha256']
    assert metadata['prompt_sha256']==hashlib.sha256(brief['prompt'].encode()).hexdigest()
    assert metadata['endpoint_host']=='api.openai.com' and metadata['model']=='gpt-image-2.5-sunburst'
    assert (metadata['requested_size'],metadata['requested_quality'],metadata['background_requested'])==('1024x1024','high','transparent')
    assert sha(candidate)==metadata['image_sha256'] and sha(provider)==metadata['provider_image_sha256']
    assert len(metadata['references'])==len(brief['references'])==3
    for actual,expected in zip(metadata['references'],brief['references']):
        assert Path(actual['path']).resolve()==(ROOT/expected['path']).resolve()
        assert sha(ROOT/expected['path'])==actual['sha256']==expected['sha256']
    controls=[candidate,provider,meta,brief_path,plan_path,gate_path,
        ROOT/brief['mother_root_acceptance']['path'],ROOT/brief['accepted_common_mother']['path'],
        ROOT/'content/fighters/gomora/moves/special3.json',ROOT/'assets/fighters/ultraman/animations/manifest.json',
        ROOT/'content/fighters/ultraman/state_frames.json',ROOT/'assets/fighters/zetton/animations/manifest.json']
    before={row['path']:row['sha256'] for row in map(rec,controls)}
    import numpy as np
    from PIL import Image,ImageDraw,ImageFont,ImageOps
    with Image.open(candidate) as picture:
        picture.load(); mode=picture.mode; dimensions=list(picture.size)
        has_alpha='A' in picture.getbands() or 'transparency' in picture.info
        image=picture.convert('RGBA')
    with Image.open(provider) as picture:
        picture.load(); provider_mode=picture.mode; provider_dimensions=list(picture.size)
        provider_has_alpha='A' in picture.getbands() or 'transparency' in picture.info
        original=picture.convert('RGBA')
    assert dimensions==metadata['dimensions'] and provider_dimensions==metadata['provider_dimensions']
    pixels=np.asarray(image); upstream=np.asarray(original); alpha=pixels[...,3]
    histogram=np.bincount(alpha.ravel(),minlength=256)
    same_shape=pixels.shape==upstream.shape
    alpha_preserved=bool(np.array_equal(alpha,upstream[...,3])) if same_shape else None
    visible_preserved=bool(np.array_equal(pixels[alpha>0],upstream[alpha>0])) if same_shape and alpha_preserved else None
    sys.path.insert(0,str(ROOT/'tools'))
    import art.pipeline as client
    from art.image_budget import usage_cost
    actual_alpha=client.alpha_report(image if has_alpha else image.convert('RGB'))
    actual_provider_alpha=client.alpha_report(original if provider_has_alpha else original.convert('RGB'))
    assert actual_alpha==metadata['alpha'] and actual_provider_alpha==metadata['provider_alpha']
    billing=metadata['official_billing']; cost=usage_cost(billing['usage'])
    assert cost==Decimal(billing['estimated_cost_usd'])
    settings=client.local_image_config()['official_budget']; ledger_path=Path(settings['ledger_path'])
    ledger=read(ledger_path)
    entry=next(row for row in ledger['entries'] if row['id']==billing['request_id'])
    old=next(row for row in ledger['entries'] if row['id']=='011ff77710ed49c9b441ed80f91733be')
    assert entry['request_sha256']==metadata['request_sha256'] and entry['status']=='completed_usage_cost'
    assert entry['usage']==billing['usage'] and Decimal(entry['committed_usd'])==cost
    assert old['status']=='reserved_remote_result_unknown' and Decimal(old['committed_usd'])==Decimal('10')
    total=sum((Decimal(row['committed_usd']) for row in ledger['entries']),Decimal(0))
    assert Decimal(settings['limit_usd'])==Decimal('60') and total<=Decimal('60')
    out.mkdir(parents=True)
    page=Image.new('RGB',(744,650),'#30343d'); draw=ImageDraw.Draw(page)
    title=ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',22); font=ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',17)
    draw.text((12,10),'初代C型 phase%s / %s / 返回完整深浅底'%(phase,brief['phase_name']),font=title,fill='white')
    draw.text((12,48),'真实%d×%d %s；完整画布等比缩略，不裁切、不删分量。'%(*dimensions,mode),font=font,fill='#e0e3eb')
    draw.text((12,76),'Alpha %d–%d；透明 %.2f%%；此页不代表体尺/接触/注册通过。'%(int(alpha.min()),int(alpha.max()),histogram[0]/alpha.size*100),font=font,fill='#e0e3eb')
    for x,color,label in [(12,'#20252d','深底 / 完整原画布'),(380,'#f1e9df','浅底 / 完整原画布')]:
        draw.text((x,108),label,font=font,fill='white')
        flattened=Image.alpha_composite(Image.new('RGBA',image.size,color),image).convert('RGB')
        fitted=ImageOps.contain(flattened,(352,352),Image.Resampling.LANCZOS)
        panel=Image.new('RGB',(352,352),color); panel.paste(fitted,((352-fitted.width)//2,(352-fitted.height)//2))
        page.paste(panel,(x,136))
    lines=['usage计价 $'+str(cost)+'；旧未知占额 $10 保持，无本工具POST/预占。',
        '保留所有Alpha和分量；只做完整画布显示缩略，不裁框/注册/旋转。',
        '本次人物/像素/皮套/完整肢体由根实看；新语义点和root仍未定。',
        '原件不动；不因本相返回自动提交下一相，不沿用杰顿后段root。']
    for at,line in enumerate(lines):draw.text((12,510+at*31),line,font=font,fill='#e0e3eb')
    preview=out/('phase%s-full-dark-light-review.jpg'%phase)
    for quality in [88,86,84,82,80]:
        page.save(preview,quality=quality,optimize=True)
        if preview.stat().st_size<=150000:break
    assert page.width<=768 and preview.stat().st_size<=150000
    save(out/'source-and-alpha-audit.json',dict(phase=int(phase),candidate=rec(candidate),provider=rec(provider),metadata=rec(meta),
        brief=rec(brief_path),root_exact_acceptance=rec(gate_path),same_request_and_three_references=True,
        actual_mode=mode,actual_dimensions=dimensions,actual_provider_mode=provider_mode,actual_provider_dimensions=provider_dimensions,
        has_alpha_channel=has_alpha,provider_has_alpha_channel=provider_has_alpha,
        alpha_extrema=[int(alpha.min()),int(alpha.max())],alpha_histogram=list(map(int,histogram)),
        alpha=actual_alpha,provider_alpha=actual_provider_alpha,
        provider_and_candidate_alpha_equal=alpha_preserved,all_provider_nonzero_rgba_preserved=visible_preserved,
        project_client_resized=metadata['resized_to_requested_size'],project_client_padded=metadata['padded_to_requested_aspect'],
        client_transparency_accepted=metadata['transparency_accepted'],returned_under_rejected_directory='rejected' in candidate.parts,
        preview=rec(preview),preview_dimensions=list(page.size),preview_jpeg_quality=quality,
        preview_entire_canvas=True,crop=False,rotation=False,per_component_filter=False,
        original_and_candidate_not_written=True,strict_size_accepted=False,contact_accepted=False,runtime_registration_done=False))
    save(out/'component-measurements-no-removal.json',dict(measurements=[component_counts(alpha,n) for n in [1,16,128]],
        all_rgba_components_preserved=True,removed_pixels=0,largest_component_not_extracted=True))
    save(out/'usage-and-reservation-audit.json',dict(metadata_billing=billing,actual_usage_cost_recomputed_usd=str(cost),
        matched_project_ledger_entry=entry,historical_unknown_entry=old,project_total_at_observation_usd=str(total),
        project_limit_usd=str(settings['limit_usd']),metadata_total_is_at_request_completion=True,
        other_new_unknown_entries=[row for row in ledger['entries'] if row['status']=='reserved_remote_result_unknown' and row['id']!=old['id']],
        old_unknown_not_released_or_retried=True,ledger_snapshot_sha256=sha(ledger_path),ledger_written_by_this_tool=False,
        actual_account_balance_verified=False,new_budget_reservations_by_this_tool=0,post_requests_by_this_tool=0))
    after={name:sha(ROOT/name) for name in before}; assert before==after
    save(out/'readonly-byte-verification.json',dict(before=before,after=after,unchanged=True,
        originals_and_common_mother_unchanged=True,post_requests=0,budget_writes=0,art_or_product_writes=0,godot_runs=0,git_writes=0))
    (out/'README.md').write_text('''# 指定单相返回审计：只读，待根实际看人物

此工具只读固定request-001的candidate/provider/metadata、该相根精确提交授权及本机账本。核真实尺寸/Alpha/请求与三附件、usage计价及旧未知10美元保持。所有RGBA分量保留，组件表只计数；没有裁Alpha框、最大分量提取、降噪、二值化、旋转、统一尺度、语义点或运行注册。

完整深浅底JPEG展示整个原画布，最长宽不超过768且文件不超过150KB。它只作显示缩略；原件和候选字节均未改。provider到candidate若由项目客户端发生过补边/重采样，JSON明确记录；不能把RGB转换显示当作原生Alpha或替原件宣称透明。

人物身份、连续皮套、双臂双腿动作、像素与体尺仍由根实际看。新root/grip/override/hurtbox和接触仍未批准；不沿用杰顿后段root，不根据本相结果自动提交下一相。0 POST、预占/账本写、产品写、Godot、Git。
''',encoding='utf-8')
    files=sorted(p for p in out.rglob('*') if p.is_file())+[Path(__file__).resolve()]
    save(out/'owned-paths.json',dict(paths=[rec(p) for p in files],frozen_for_root_review=True))
    print(json.dumps(dict(phase=int(phase),report=out.relative_to(ROOT).as_posix(),preview=rec(preview),
        preview_dimensions=list(page.size),actual_dimensions=dimensions,alpha_extrema=[int(alpha.min()),int(alpha.max())],
        cost_usd=str(cost),old_unknown_usd='10',owned_sha256=sha(out/'owned-paths.json'),
        root_visual_review_pending=True,post_requests_by_child=0),ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=PHASES,required=True)
    parser.add_argument('--probe',action='store_true',help='只看固定文件是否齐，不生成报告')
    args=parser.parse_args()
    if args.probe:
        *_,present=readiness(args.phase)
        print(json.dumps(dict(phase=args.phase,present=present,ready=all(present.values()),writes=0,posts=0),ensure_ascii=False))
    else:audit(args.phase)

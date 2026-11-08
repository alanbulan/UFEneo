"""只读核根已返回的初代phase02原件、Alpha、usage；只写报告和完整深浅底缩略页。"""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'reports/review/2026-11-02/gomora-back-lift-ultraman-phase02-returned-readonly-v1'
REQUEST = ROOT / 'art/fighters/ultraman/stage5/gomora-super3-back-lift-receiver-20261102-v1/phase-02/request-001'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rec(path):
    return dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size)


def read(path):
    return json.loads(path.read_text('utf-8-sig'))


def save(name,data):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(data,stream,ensure_ascii=False,indent=2)
        stream.write('\n')


def components(alpha,threshold):
    import numpy as np
    from scipy import ndimage
    labels,count=ndimage.label(alpha>=threshold,structure=np.ones((3,3),dtype=np.uint8))
    sizes=np.bincount(labels.ravel())[1:]
    return dict(alpha_threshold=threshold,connectivity=8,count=int(count),
        total_pixels=int(sizes.sum()),largest_component_pixels=int(sizes.max()) if count else 0,
        singleton_components=int(np.sum(sizes==1)),small_components_under_8_pixels=int(np.sum(sizes<8)),
        top_component_sizes=sorted((int(x) for x in sizes),reverse=True)[:12],
        measurement_only=True,removed_components=0,component_selection_used_to_make_preview=False)


def main():
    assert not OUT.exists()
    candidate=REQUEST/'candidate.png'; provider=REQUEST/'candidate.provider.png'; meta=REQUEST/'candidate.metadata.json'
    brief=ROOT/'reports/review/2026-11-02/gomora-back-lift-ultraman-phase02-brief-v1/brief.json'
    plan=ROOT/'reports/review/2026-11-02/gomora-back-lift-ultraman-phase02-brief-v1/submission-plan.json'
    contract=ROOT/'reports/review/2026-11-02/gomora-back-lift-next-receiver-readonly-v1/ultraman-c-whole-frame-contract.json'
    controls=[candidate,provider,meta,brief,plan,contract,
        ROOT/'content/fighters/gomora/moves/special3.json',ROOT/'assets/fighters/ultraman/animations/manifest.json',
        ROOT/'content/fighters/ultraman/state_frames.json',ROOT/'assets/fighters/zetton/animations/manifest.json']
    before={row['path']:row['sha256'] for row in map(rec,controls)}
    metadata=read(meta); expected=read(plan)
    assert metadata['request_sha256']==expected['request_fields_sha256']
    assert sha(candidate)==metadata['image_sha256'] and sha(provider)==metadata['provider_image_sha256']
    assert metadata['endpoint_host']=='api.openai.com' and metadata['model']=='gpt-image-2.5-sunburst'
    assert (metadata['requested_size'],metadata['requested_quality'],metadata['background_requested'])==('1024x1024','high','transparent')
    for row in metadata['references']:
        assert sha(Path(row['path']))==row['sha256']
    import numpy as np
    from PIL import Image,ImageDraw,ImageFont
    with Image.open(candidate) as picture:
        assert picture.format=='PNG' and picture.mode=='RGBA' and picture.size==(1024,1024)
        image=picture.copy()
    with Image.open(provider) as picture:
        assert picture.format=='PNG' and picture.mode=='RGBA' and picture.size==(1024,1024)
        original=picture.copy()
    pixels=np.asarray(image); upstream=np.asarray(original); alpha=pixels[...,3]
    histogram=np.bincount(alpha.ravel(),minlength=256)
    assert np.array_equal(alpha,upstream[...,3])
    assert np.array_equal(pixels[alpha>0],upstream[alpha>0])
    assert not metadata['resized_to_requested_size'] and not metadata['padded_to_requested_aspect']
    assert int(alpha.min())==0 and int(alpha.max())>0
    assert all(int(alpha[y,x])==0 for x,y in [(0,0),(1023,0),(0,1023),(1023,1023)])
    sys.path.insert(0,str(ROOT/'tools'))
    from art.image_budget import usage_cost
    import art.pipeline as client
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
    OUT.mkdir(parents=True)
    page=Image.new('RGB',(744,650),'#30343d'); draw=ImageDraw.Draw(page)
    title=ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',22)
    font=ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',17)
    draw.text((12,10),'初代C型 phase02 / 返回原件完整深浅底 / 待根实看',font=title,fill='white')
    draw.text((12,48),'真实1024×1024 RGBA；完整画布等比缩略，不裁切、不删分量。',font=font,fill='#e0e3eb')
    draw.text((12,76),'Alpha 0–%d；透明 %.2f%%；原件与候选全部非零Alpha像素完全相同。'%(int(alpha.max()),histogram[0]/alpha.size*100),font=font,fill='#e0e3eb')
    for x,color,label in [(12,'#20252d','深底 / 完整1024方图'),(380,'#f1e9df','浅底 / 完整1024方图')]:
        draw.text((x,108),label,font=font,fill='white')
        background=Image.new('RGBA',image.size,color)
        composite=Image.alpha_composite(background,image).convert('RGB')
        page.paste(composite.resize((352,352),Image.Resampling.LANCZOS),(x,136))
    lines=[
        '本次usage计费 $'+str(cost)+'；历史未知占额 $10 保持。',
        '头右足左、胸腹向下、双臂垂落与双腿不同屈度；完整身体待根审。',
        '低Alpha散点全部保留；未做降噪、抠图、裁Alpha框、旋转或注册。',
        '所有新接触点、root、grip仍未定；不以本页证明已配对或可装。',
    ]
    for at,line in enumerate(lines): draw.text((12,510+at*31),line,font=font,fill='#e0e3eb')
    preview=OUT/'phase02-full-dark-light-review.jpg'; page.save(preview,quality=88,optimize=True)
    assert page.width<=768 and preview.stat().st_size<=150000
    save('source-and-alpha-audit.json',dict(candidate=rec(candidate),provider=rec(provider),metadata=rec(meta),
        request_bound_to_prepared_plan=True,real_size=[1024,1024],mode='RGBA',alpha_extrema=[int(alpha.min()),int(alpha.max())],
        alpha_histogram=[int(x) for x in histogram],clear_corners=True,transparent_fraction=float(histogram[0]/alpha.size),
        alpha_255_pixels=int(histogram[255]),all_provider_alpha_preserved=True,
        all_provider_nonzero_alpha_rgba_preserved=True,client_hidden_rgb_cleanup_only=True,
        provider_not_resized_or_padded=True,preview=rec(preview),preview_size=list(page.size),
        preview_entire_canvas=True,preview_scale=[352,1024],crop=False,rotation=False,per_component_filter=False,
        original_and_candidate_bytes_not_written=True,art_or_product_writes=0,post_requests=0,godot_run=False,git_write=False))
    save('component-measurements-no-removal.json',dict(measurements=[components(alpha,value) for value in [1,16,128]],
        all_rgba_components_preserved=True,removed_pixels=0,largest_component_not_extracted=True,
        component_qa_does_not_approve_pose=True))
    save('usage-and-reservation-audit.json',dict(metadata_billing=billing,actual_usage_cost_recomputed_usd=str(cost),
        matched_project_ledger_entry=entry,historical_unknown_entry=old,
        project_total_at_observation_usd=str(total),project_limit_usd=str(settings['limit_usd']),
        metadata_project_total_is_at_request_completion=True,old_unknown_not_released_or_retried=True,
        ledger_snapshot_sha256=sha(ledger_path),ledger_written_by_this_tool=False,
        user_reported_account_balance_usd='40.94',actual_account_balance_verified=False,
        new_budget_reservations_by_this_tool=0,post_requests_by_this_tool=0))
    after={name:sha(ROOT/name) for name in before}; assert after==before
    save('readonly-byte-verification.json',dict(before=before,after=after,unchanged=True,
        original_bytes_unchanged=True,product_writes=0,post_requests=0,godot_runs=0,git_writes=0))
    (OUT/'README.md').write_text('''# 初代C型phase02返回原件：只读离线核查

根已通过固定一次入口取得request-001。本工具只读candidate/provider/metadata，核真实1024×1024 RGBA，既有请求SHA与两参考一致；原件和候选全部Alpha一致、所有非零Alpha的RGBA逐像素一致，候选只沿项目客户端清掉Alpha=0的隐藏RGB。没有缩放/补边原件，未裁切、删分量、降噪、旋转或注册。

Alpha实际范围0–254，没有255像素；这项如实保留，并不改成不透明。透明像素与四角已核，深浅底页按完整1024方图缩略合成，保留所有可见/低Alpha散点，不用最大分量或Alpha bbox做图。组件表只统计，不改图；页面小于768宽、150KB。

metadata usage与本机官方预算账本逐项一致，按现行usage计价复算本张$0.072502；旧未知011ff77710ed49c9b441ed80f91733be仍占$10，未释放或重发。账本与余额边界只作本机记录，未通过账户接口核实40.94余额。

受方独立整相身份/姿态/完整皮套/像素与真Alpha仍交根实际看本页和原件后裁定。这里不批准任何运行注册、root/grip/override/受击框或与哥莫拉配对。原后段杰顿root边界保持，0新POST、产品写、Godot、Git。
''',encoding='utf-8')
    files=sorted(p for p in OUT.rglob('*') if p.is_file())+[Path(__file__).resolve()]
    save('owned-paths.json',dict(paths=[rec(p) for p in files],frozen_for_root_review=True))
    print(json.dumps(dict(report=OUT.relative_to(ROOT).as_posix(),preview=rec(preview),preview_size=list(page.size),
        cost_usd=str(cost),old_unknown_usd='10',owned_sha256=sha(OUT/'owned-paths.json'),
        post_requests_by_child=0),ensure_ascii=False))


if __name__=='__main__':
    main()

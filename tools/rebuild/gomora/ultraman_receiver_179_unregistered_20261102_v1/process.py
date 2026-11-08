"""根授权的初代六整源→共同179方、128二值；无根/外画布/产品注册。"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
REPORT = ROOT/'reports/review/2026-11-02/gomora-back-lift-ultraman-179-unregistered-v1'
OUTPUT = REPORT/'candidate-01'
PROPOSAL = ROOT/'reports/review/2026-11-02/gomora-back-lift-ultraman-scale-proposal-v1'
PROPOSAL_TOOL = ROOT/'tools/rebuild/gomora/ultraman_receiver_scale_proposal_20261102_v1/proposal.py'
PROPOSAL_TOOL_SHA = '6fb912558b3689a464de25be0a898c0fdd847f1e350f623a6221a2c31c114749'
PROPOSAL_OWNED_SHA = 'b14b2ed3c8fda2e95698af80d29692d8bf7c2dcebfeb3cb35bde5315bb6f9c3a'
SAMPLE = 179
SOURCE = 1024
SCALE = SAMPLE/SOURCE


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rec(path):
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size}


def read(path):
    return json.loads(path.read_text('utf-8-sig'))


def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2)
        stream.write('\n')


def rgba(path):
    from PIL import Image
    with Image.open(path) as picture:
        picture.load()
        assert picture.mode=='RGBA'
        return picture.copy()


def preflight():
    assert sha(PROPOSAL_TOOL)==PROPOSAL_TOOL_SHA
    assert sha(PROPOSAL/'closeout-owned-paths.json')==PROPOSAL_OWNED_SHA
    for row in read(PROPOSAL/'closeout-owned-paths.json')['paths']:
        path=ROOT/row['path']
        assert path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],row['path']
    spec=importlib.util.spec_from_file_location('ultraman_receiver_frozen_source_measurements',PROPOSAL_TOOL)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows,before=module.sources()
    proposal=read(PROPOSAL/'measurement-v2/common-scale-proposal.json')
    assert proposal['proposed_common_sample_scale']==SCALE
    assert proposal['proposed_common_full_canvas_sample_pixels']==[SAMPLE,SAMPLE]
    authorization=read(REPORT/'authorization-source.json')
    assert authorization['communicated_by']=='root' and authorization['receipt_writer']=='subagent_gomora_super3_resume'
    assert authorization['approved_whole_source_sample_pixels']==[SAMPLE,SAMPLE]
    assert authorization['approved_scale']==SCALE and authorization['alpha_threshold']==128
    assert authorization['runtime_registration_authorized'] is False
    for path in [PROPOSAL_TOOL,PROPOSAL/'closeout-owned-paths.json',
                 PROPOSAL/'measurement-v2/common-scale-proposal.json',REPORT/'authorization-source.json']:
        before[path.relative_to(ROOT).as_posix()]=sha(path)
    return rows,before,module


def jpeg(page,path):
    for quality in [90,86,82,78,74,70,66,62,58,54]:
        page.save(path,quality=quality,optimize=True,subsampling=0)
        if path.stat().st_size<=150000:
            break
    assert path.stat().st_size<=150000
    return dict(rec(path),dimensions=list(page.size),jpeg_quality=quality)


def flatten(picture,color):
    from PIL import Image
    return Image.alpha_composite(Image.new('RGBA',picture.size,color),picture).convert('RGB')


def one_x(native,candidate,path,index):
    from PIL import Image,ImageDraw,ImageFont
    page=Image.new('RGB',(744,668),'#30343d')
    draw=ImageDraw.Draw(page)
    font=ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',18)
    draw.text((12,10),f'初代C型 phase{index:02d} / 精确1x完整画布 / 未注册',font=font,fill='white')
    draw.text((12,40),'左右同一像素单位；各画布仅显示居中，没有按身体或根点对齐。',font=font,fill='white')
    for y,color,name in [(112,'#252b35','深底'),(376,'#f1e9df','浅底')]:
        draw.text((12,y-28),f'{name}：现装model-native 192方',font=font,fill='white')
        draw.text((380,y-28),f'{name}：完整源共同采样179方',font=font,fill='white')
        for x,picture in [(12,native),(380,candidate)]:
            panel=Image.new('RGB',(352,224),color)
            panel.paste(flatten(picture,color),((352-picture.width)//2,(224-picture.height)//2))
            page.paste(panel,(x,y))
    draw.text((12,620),'128二值 / RGB兼容整图采样；root、grip、override、hurtbox均未定。',font=font,fill='white')
    draw.text((12,646),'完整透明画布保留；此页不代表严尺、接触、配对或运行通过。',font=font,fill='white')
    return jpeg(page,path)


def four_x(native,candidate,path,index,color,name):
    from PIL import Image,ImageDraw,ImageFont
    page=Image.new('RGB',(768,1680),'#30343d')
    draw=ImageDraw.Draw(page)
    font=ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',18)
    draw.text((12,10),f'初代C型 phase{index:02d} / 精确4x最近邻 / {name} / 未注册',font=font,fill='white')
    draw.text((12,42),'现装完整192画布 → 768方；上下同一4x像素尺度。',font=font,fill='white')
    first=native.resize((native.width*4,native.height*4),Image.Resampling.NEAREST)
    second=candidate.resize((candidate.width*4,candidate.height*4),Image.Resampling.NEAREST)
    page.paste(flatten(first,color),(0,72))
    draw.text((12,848),'新完整179画布 → 716方；只显示居中，未注册/未加外画布。',font=font,fill='white')
    panel=Image.new('RGB',(768,716),color)
    panel.paste(flatten(second,color),((768-second.width)//2,0))
    page.paste(panel,(0,880))
    draw.text((12,1610),'整图尺度179/1024；没有裁Alpha框、逐相放缩、拼肢或分量过滤。',font=font,fill='white')
    draw.text((12,1638),'H0推定与肩髋差保持；此页不代表严格体尺或双方实际接触通过。',font=font,fill='white')
    return jpeg(page,path)


def execute():
    import numpy as np
    rows,before,module=preflight()
    assert not OUTPUT.exists(),'已有候选不覆盖；本入口仅创建新的candidate-01'
    sys.path.insert(0,str(ROOT/'tools/rebuild/shared'))
    from forge_backend import _kcentroid_downscale,binarize_alpha,palette_mode,backend_info
    OUTPUT.mkdir(parents=True)
    pngs=OUTPUT/'unregistered179'
    previews=OUTPUT/'review'
    pngs.mkdir()
    previews.mkdir()
    native=rgba(ROOT/rows[0]['native']['path'])
    assert native.size==(192,192)
    receipts=[]
    views=[]
    edges=[i*SOURCE//SAMPLE for i in range(SAMPLE+1)]
    assert edges[0]==0 and edges[-1]==SOURCE and min(np.diff(edges))>0
    with palette_mode('rgb'):
        backend=backend_info()
        assert backend['palette_distance']=='rgb'
        for index,row in enumerate(rows[1:]):
            source_path=ROOT/row['image']['path']
            original=rgba(source_path)
            assert original.size==(SOURCE,SOURCE)
            source_pixels=np.asarray(original)
            visible=source_pixels[...,3]>=128
            binary=binarize_alpha(original.copy())
            binary_pixels=np.asarray(binary)
            assert np.array_equal(binary_pixels[...,3],np.where(visible,255,0))
            assert np.array_equal(binary_pixels[visible,:3],source_pixels[visible,:3])
            assert np.all(binary_pixels[~visible]==0)
            sampled=_kcentroid_downscale(binary,SAMPLE,SAMPLE,detail_bias=False)
            before_final=np.asarray(sampled).copy()
            candidate=binarize_alpha(sampled)
            pixels=np.asarray(candidate)
            assert candidate.mode=='RGBA' and candidate.size==(SAMPLE,SAMPLE)
            assert set(map(int,np.unique(pixels[...,3])))=={0,255}
            assert np.all(pixels[pixels[...,3]==0]==0)
            assert not np.any(pixels[[0,-1],:,3]) and not np.any(pixels[:,[0,-1],3])
            path=pngs/f'{index:02d}.png'
            candidate.save(path,optimize=True)
            receipts.append({'phase':index,'candidate':rec(path),'source':row['image'],
                'source_provider':row['provider'],'source_metadata':row['metadata'],'root_source_review':row['root_source_review'],
                'source_dimensions':[SOURCE,SOURCE],'candidate_dimensions':[SAMPLE,SAMPLE],
                'source_alpha_extrema':[int(source_pixels[...,3].min()),int(source_pixels[...,3].max())],
                'source_nonzero_alpha_pixels':int(np.count_nonzero(source_pixels[...,3])),
                'source_pixels_at_or_above_alpha128':int(visible.sum()),
                'source_nonzero_below_threshold_pixels':int(np.count_nonzero((source_pixels[...,3]>0)&~visible)),
                'binary_stage_exact_alpha128_and_visible_rgb_preserved':True,
                'candidate_alpha_values':[0,255],'candidate_opaque_pixels':int(np.count_nonzero(pixels[...,3])),
                'final_binary_stage_pixel_changes':int(np.count_nonzero(np.any(before_final!=pixels,axis=2))),
                'all_candidate_borders_transparent':True,'full_source_canvas_sampled':True,
                'source_crop':None,'component_filter':None,'per_phase_scale':None,'limb_transforms':None,
                'runtime_root':None,'runtime_grip':None,'hold_point_override':None,'hurtboxes':None,
                'runtime_registration_done':False,'strict_size_accepted':False,'contact_accepted':False})
            views.append({'phase':index,'candidate':rec(path),
                'one_x_dark_light':one_x(native,candidate,previews/f'phase{index:02d}-1x-dark-light.jpg',index),
                'four_x_dark':four_x(native,candidate,previews/f'phase{index:02d}-4x-dark.jpg',index,'#252b35','深底'),
                'four_x_light':four_x(native,candidate,previews/f'phase{index:02d}-4x-light.jpg',index,'#f1e9df','浅底')})
    save(OUTPUT/'processing-receipt.json',{
        'authorization':rec(REPORT/'authorization-source.json'),'tool':rec(Path(__file__)),
        'accepted_scale_proposal':rec(PROPOSAL/'measurement-v2/common-scale-proposal.json'),
        'source_verification_tool':rec(PROPOSAL_TOOL),'backend_wrapper':rec(ROOT/'tools/rebuild/shared/forge_backend.py'),
        'backend':backend,'art_source':'existing','image_generation_route_invoked':False,
        'common_source_size':[SOURCE,SOURCE],'common_output_size':[SAMPLE,SAMPLE],'common_scale':SCALE,
        'pixel_processing_order':['完整源副本经forge_backend.binarize_alpha阈值128，原件不动',
                                  'forge_backend._kcentroid_downscale完整1024方→179方，detail_bias=False',
                                  'forge_backend.binarize_alpha复核最终二值Alpha128'],
        'resampler_disclosure':'项目forge_backend中公开声明的RGB Lloyd三轮kCentroid兼容补充算法，不冒称forge原生缩放器。',
        'resampling_block_edges_x_and_y':edges,'source_edge_formula':'edge[i]=floor(i*1024/179), i=0..179',
        'source_block_coverage_rule':'每格Alpha128可见样本达到半数才输出；属于统一整图采样，不是组件筛选或删散点。',
        'palette_mode':'rgb','shared_palette_learning_or_recoloring':False,'alpha_threshold':128,
        'source_alpha_threshold_removal_disclosed_per_phase':True,
        'outputs':receipts,'review_pages':views,'native_reference':rec(ROOT/rows[0]['native']['path']),
        'one_x_display':'现装192方和新179方以1源px=1显示px；完整画布显示居中，未按身体/根配准。',
        'four_x_display':'完整192方→768方、新179方→716方，均严格4x最近邻；上下两行，深浅各页。',
        'outside_padding_canvas_created':False,'root':None,'grip':None,'override':None,'hurtboxes':None,
        'strict_size_accepted':False,'contact_accepted':False,'runtime_registration_done':False,
        'png_output_scope':'仅本报告candidate-01/unregistered179六张新候选；所有原PNG不改',
        'post_requests':0,'budget_writes':0,'product_writes':0,'godot_runs':0,'git_writes':0})
    save(OUTPUT/'source-and-product-byte-verification.json',module.verify_unchanged(before))
    save(OUTPUT/'owned-paths.json',{'paths':[rec(p) for p in sorted(OUTPUT.rglob('*')) if p.is_file()]+[rec(Path(__file__))],
         'frozen_for_root_review':True,'runtime_registration_done':False})
    print(json.dumps({'report':str(OUTPUT),'receipt':rec(OUTPUT/'processing-receipt.json'),
        'owned_sha256':sha(OUTPUT/'owned-paths.json'),'common_size':[SAMPLE,SAMPLE],
        'unregistered_candidates':[row['candidate'] for row in receipts],
        'whole_source_scale':SCALE,'all_alpha_binary':True,'runtime_registration_done':False},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true',help='根已授权的本地完整六源处理；不包含POST或产品写')
    args=parser.parse_args()
    if args.execute:
        execute()
    else:
        rows,_,_=preflight()
        print(json.dumps({'ready':True,'source_ids':[row['id'] for row in rows[1:]],
            'scale':SCALE,'output_size':[SAMPLE,SAMPLE],'processing_executed':False,'writes':0},ensure_ascii=False))

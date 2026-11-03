"""初代六源只读解剖测量与一个共同scale提案；不处理PNG、不做注册。"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import median
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
REPORT = ROOT / 'reports/review/2026-11-02/gomora-back-lift-ultraman-scale-proposal-v1'
ART = ROOT / 'art/fighters/ultraman/stage5/gomora-super3-back-lift-receiver-20261102-v1'
NATIVE = ROOT / 'assets/fighters/ultraman/model-native.png'
CANON4 = ROOT / 'art/fighters/ultraman/model/model-reference-x4.png'
NATIVE_SHA = 'cd76aea1686c18390a7324ea68368daef15796e8d6ab03671eb03df3301e3d44'
CANON4_SHA = '9e084ba7ff4f4ff2ed343e2d20650ebbec5b648156cddd066ad10165e68f0e71'
POINTS = {
    'H0': '颅顶：不含头鳍的头骨冠点；鳍基遮住时明确为解剖推定，不能称可见轮廓',
    'H1': '下颏：头部长轴另一端的完整下颏外表面',
    'S': '近侧肩关节中心：同一近侧肱骨的肩端，不取肩外缘最高点',
    'P': '近侧髋关节中心：同一近侧股骨与骨盆的转接中心',
    'A': '腹腰腹侧外表面：候选承重参照，不声称独图能证明接触',
    'D': '腹腰背侧外表面：与A同横截面的躯干外表面',
    'R': '骨盆内部中线参考：离背后接续用本人语义参照，不是已注册root',
    'E': '卸重边缘腹侧表面参考：只用于04/05，未配对则不称实际最后接触点',
}
COLORS = {'H0':'#fff078','H1':'#fff078','S':'#79d5ff','P':'#79d5ff',
          'A':'#7dff9c','D':'#7dff9c','R':'#ffb7f2','E':'#ffa96d'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rec(path):
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size}


def read(path):
    return json.loads(path.read_text('utf-8-sig'))


def save(path, value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2)
        f.write('\n')


def image(path):
    from PIL import Image
    with Image.open(path) as picture:
        picture.load()
        assert picture.mode == 'RGBA', f'不是原RGBA：{path}'
        return picture.copy()


def sources():
    """先全数核源和根签；任何缺源/缺签/错SHA在创建输出前停止。"""
    from PIL import Image
    import numpy as np
    assert sha(NATIVE) == NATIVE_SHA and sha(CANON4) == CANON4_SHA
    native,canon = image(NATIVE),image(CANON4)
    assert canon.size == (native.width*4,native.height*4)
    assert np.array_equal(np.asarray(canon),np.asarray(native.resize(canon.size,Image.Resampling.NEAREST)))
    rows = [{'id':'canon-x4','image':rec(CANON4),'native':rec(NATIVE),'native_units_per_source_pixel':0.25,
             'dimensions':list(canon.size),'required_points':['H0','H1','S','P']}]
    controls = [NATIVE,CANON4,ROOT/'tools/rebuild/shared/forge_backend.py',ROOT/'assets/fighters/ultraman/animations/manifest.json',
                ROOT/'content/fighters/ultraman/state_frames.json',ROOT/'content/fighters/gomora/moves/special3.json']
    for index in range(6):
        folder = ART / f'phase-{index:02d}/request-001'
        candidate,provider,metadata,gate = [folder/name for name in
            ['candidate.png','candidate.provider.png','candidate.metadata.json','root-source-review.json']]
        for path in [candidate,provider,metadata,gate]:
            assert path.is_file(),f'六源未齐或未根签：{path}'
        approval = read(gate)
        assert approval['reviewer'] == 'root' and approval['review_authority'] == 'root_delegated_by_user'
        assert approval['accepted_as_independent_whole_source_candidate'] is True
        assert approval['all_listed_views_actually_reviewed'] is True
        assert approval['candidate']['sha256'] == sha(candidate)
        assert approval['source']['sha256'] == sha(provider)
        assert approval['metadata']['sha256'] == sha(metadata)
        assert approval['source_to_native_scale'] is None and approval['runtime_data_authorized'] is False
        picture = image(candidate)
        assert picture.size == (1024,1024)
        required = ['H0','H1','S','P','A','D','R'] + (['E'] if index>=4 else [])
        rows.append({'id':f'phase-{index:02d}','image':rec(candidate),'provider':rec(provider),
                     'metadata':rec(metadata),'root_source_review':rec(gate),'dimensions':list(picture.size),
                     'native_units_per_source_pixel':None,'required_points':required})
        controls.extend([candidate,provider,metadata,gate])
    return rows,{path.relative_to(ROOT).as_posix():sha(path) for path in controls}


def verify_unchanged(before):
    after = {name:sha(ROOT/name) for name in before}
    assert before == after,'只读测量期间源或产品变更，不能冻结为同一来源'
    return {'before':before,'after':after,'unchanged':True,'png_writes':0,'registrations':0,
            'product_writes':0,'post_requests':0,'budget_writes':0,'godot_runs':0,'git_writes':0}


def page(row, path, points=None, metrics=None):
    """完整原画布的只读坐标层；不裁Alpha框、不滤分量、不写PNG。"""
    from PIL import Image,ImageDraw,ImageFont
    picture = image(ROOT/row['image']['path'])
    page = Image.new('RGB',(744,1010),'#30343d')
    draw = ImageDraw.Draw(page)
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    small = ImageFont.truetype('C:/Windows/Fonts/consola.ttf',13)
    draw.text((12,8),f"{row['id']} / 完整原画布 / 仅坐标提案",font=font,fill='white')
    draw.text((12,36),f"{picture.width}×{picture.height} RGBA；单位=源像素；不代表严尺/接触通过",font=font,fill='#e3e6ef')
    panel = Image.alpha_composite(Image.new('RGBA',picture.size,'#252b35'),picture).convert('RGB')
    factor = 720/picture.width
    panel = panel.resize((720,round(picture.height*factor)),Image.Resampling.LANCZOS)
    pdraw = ImageDraw.Draw(panel)
    for tick in range(0,picture.width,64):
        position = round(tick*factor)
        pdraw.line((position,0,position,panel.height-1),fill='#525b69')
        pdraw.line((0,position,panel.width-1,position),fill='#525b69')
        pdraw.text((position+2,0),str(tick),font=small,fill='white')
        pdraw.text((1,position+2),str(tick),font=small,fill='white')
    if points:
        for a,b,color in [('H0','H1','#fff078'),('S','P','#79d5ff'),('A','D','#7dff9c')]:
            if a in points and b in points:
                pdraw.line(tuple(v*factor for key in [a,b] for v in points[key]['xy']),fill=color,width=2)
        for key,point in points.items():
            x,y = [v*factor for v in point['xy']]
            radius = max(3,point['radius_px']*factor)
            pdraw.ellipse((x-radius,y-radius,x+radius,y+radius),outline=COLORS[key],width=2)
            pdraw.line((x-5,y,x+5,y),fill=COLORS[key])
            pdraw.line((x,y-5,x,y+5),fill=COLORS[key])
            pdraw.text((x+6,y-17),key,font=small,fill=COLORS[key],stroke_width=1,stroke_fill='#15191f')
    page.paste(panel,(12,72))
    if points:
        for number,(key,point) in enumerate(points.items()):
            line = f"{key} ({point['xy'][0]:g}, {point['xy'][1]:g}) ±{point['radius_px']:g}源px"
            x,y = 12+(number%2)*364,804+(number//2)*27
            draw.text((x,y),line,font=font,fill=COLORS[key])
    else:
        draw.text((12,810),'请在完整源和坐标页上逐个独立读点；点为空不能执行测量。',font=font,fill='white')
    if metrics:
        draw.text((12,918),f"头长 {metrics['head']['length_px']:.3f}；肩髋弦长 {metrics['shoulder_hip']['length_px']:.3f} 源px",font=font,fill='white')
    draw.text((12,950),'误差圆=目测位置上界；独图腹腰参照不等于真实接触点。',font=font,fill='white')
    draw.text((12,978),'未裁框/提取最大分量/旋转/逐相缩放/改原PNG/注册。',font=font,fill='white')
    for quality in [88,84,80,76]:
        page.save(path,quality=quality,optimize=True)
        if path.stat().st_size<=150000:
            break
    assert path.stat().st_size<=150000
    return rec(path)


def prepare():
    rows,before = sources()
    out = REPORT/'preparation'
    assert not out.exists(),'既有准备包不回写'
    out.mkdir(parents=True)
    template = {'schema':'ultraman-six-source-manual-points.v1','measurer':'subagent_gomora_super3_resume',
                'method':'完整RGBA与完整坐标JPEG实际目测；源空间坐标；误差为保守径向上界，不是统计置信区间',
                'point_definitions':POINTS,'whole_frame_only':True,'sources':[]}
    for row in rows:
        view = page(row,out/(row['id']+'-full-grid.jpg'))
        template['sources'].append(dict(row,measurement_page=view,
            all_source_and_grid_views_actually_opened=False,pose_note='',
            points={key:{'xy':None,'radius_px':None,'visibility':None,'note':None} for key in row['required_points']}))
    save(out/'manual-points.TEMPLATE.json',template)
    save(out/'readonly-byte-verification.json',verify_unchanged(before))
    save(out/'owned-paths.json',{'paths':[rec(p) for p in sorted(out.iterdir()) if p.is_file()]+[rec(Path(__file__))],
         'candidate_points_scale_and_runtime_values_not_approved':True})
    print(json.dumps({'status':'preparation_only','report':str(out),'image_count':len(rows),'measurement_executed':False},ensure_ascii=False))


def distance(points, a, b):
    first,second = points[a],points[b]
    size = math.dist(first['xy'],second['xy'])
    error = first['radius_px']+second['radius_px']
    assert size>error>0,'点位误差覆盖整个尺长，需重读或明确不可测，不能据此估scale'
    return {'endpoints':[a,b],'length_px':size,'error_bound_px':error,
            'interval_px':[size-error,size+error],'projection':'二维图像弦长，未作三维透视或姿态反解'}


def measure(points_path, version):
    import numpy as np
    from scipy import ndimage
    rows,before = sources()
    manual = read(points_path)
    assert manual['schema']=='ultraman-six-source-manual-points.v1' and manual['whole_frame_only'] is True
    assert [row['id'] for row in rows]==[row['id'] for row in manual['sources']]
    measurements = []
    for current,row in zip(rows,manual['sources']):
        assert row['image']==current['image'] and row['required_points']==current['required_points']
        assert row['all_source_and_grid_views_actually_opened'] is True and row['pose_note']
        assert sha(ROOT/row['measurement_page']['path'])==row['measurement_page']['sha256']
        assert set(row['points'])==set(current['required_points'])
        picture = image(ROOT/current['image']['path'])
        alpha = np.asarray(picture)[...,3]
        mask = alpha>=128
        inside = ndimage.distance_transform_edt(mask)
        outside = ndimage.distance_transform_edt(~mask)
        neighborhoods = []
        for key,point in row['points'].items():
            assert point['visibility'] in ['direct_surface','anatomical_center_estimate'] and point['note']
            assert isinstance(point['xy'],list) and len(point['xy'])==2
            assert all(isinstance(v,(int,float)) and math.isfinite(v) for v in point['xy'])
            assert 0<=point['xy'][0]<picture.width and 0<=point['xy'][1]<picture.height
            assert isinstance(point['radius_px'],(int,float)) and 0<point['radius_px']<=32
            x,y = map(round,point['xy'])
            signed = float(inside[y,x]-outside[y,x])
            is_surface = point['visibility']=='direct_surface'
            within = abs(signed)<=point['radius_px'] if is_surface else None
            assert within is not False,f'{row["id"]}/{key}可见表面不在申报误差内，必须重读或明确推定，不自动吸附轮廓'
            neighborhoods.append({'key':key,'alpha_at_point':int(alpha[y,x]),
                'signed_distance_to_alpha128_boundary_px':signed,
                'boundary_within_stated_radius_if_direct_surface':within,
                'measurement_only_no_mask_or_point_was_changed':True})
        measurements.append({'id':row['id'],'source':current['image'],'points':row['points'],'pose_note':row['pose_note'],
            'point_neighborhood_evidence':neighborhoods,
            'head':distance(row['points'],'H0','H1'),'shoulder_hip':distance(row['points'],'S','P')})
    canon = measurements[0]
    target_head = canon['head']['length_px']/4
    target_torso = canon['shoulder_hip']['length_px']/4
    sys.path.insert(0,str(ROOT/'tools/rebuild/shared'))
    from forge_backend import shared_source_scale
    raw_heads = [row['head']['length_px'] for row in measurements[1:]]
    scale = shared_source_scale(head_readings=raw_heads,target_head_reading=target_head)
    central = scale['scale']
    source_interval = [median(row['head']['interval_px'][i] for row in measurements[1:]) for i in [0,1]]
    target_interval = [v/4 for v in canon['head']['interval_px']]
    scale_interval = [target_interval[0]/source_interval[1],target_interval[1]/source_interval[0]]
    canvas = round(1024*central)
    actual_scale = canvas/1024
    for row in measurements[1:]:
        for name,target in [('head',target_head),('shoulder_hip',target_torso)]:
            metric = row[name]
            target_bounds = [v/4 for v in canon[name]['interval_px']]
            metric['common_sampled_native_px'] = metric['length_px']*actual_scale
            metric['native_reference_px'] = target
            metric['native_reference_interval_px'] = target_bounds
            metric['central_deviation_fraction'] = metric['common_sampled_native_px']/target-1
            metric['sampled_measurement_error_bound_native_px'] = metric['error_bound_px']*actual_scale
            metric['deviation_interval_at_fixed_common_scale'] = [
                metric['interval_px'][0]*actual_scale/target_bounds[1]-1,
                metric['interval_px'][1]*actual_scale/target_bounds[0]-1]
            metric['diagnostic_only_not_acceptance'] = True
        row['source_semantics_in_common_sample_canvas_only'] = {key:{
            'xy':[v*actual_scale for v in value['xy']],'radius_px':value['radius_px']*actual_scale}
            for key,value in row['points'].items() if key in ['A','D','R','E']}
        row['runtime_root']=row['runtime_grip']=row['hold_point_override']=row['hurtboxes']=None
        row['actual_actor_contact_accepted']=False
    out = REPORT/version
    assert out.parent==REPORT and version.startswith('measurement-') and not out.exists()
    out.mkdir(parents=True)
    previews = []
    for current,row in zip(rows,measurements):
        previews.append(page(current,out/(row['id']+'-full-points.jpg'),row['points'],row))
    common = {'status':'root_review_required_scale_proposal_only','native_reference':rec(NATIVE),'exact_x4_reference':rec(CANON4),
              'method':'六个独立整人源H0–H1弦长的中位数；肩髋弦长独立复核，不据偏差再缩放各相',
              'calculation_backend':rec(ROOT/'tools/rebuild/shared/forge_backend.py'),
              'art_source':'existing','image_generation_route_not_invoked':True,
              'forge_backend_result':scale,'central_nominal_scale':central,
              'conservative_scale_interval':scale_interval,'interval_is_not_statistical_confidence':True,
              'proposed_common_full_canvas_sample_pixels':[canvas,canvas],'proposed_common_sample_scale':actual_scale,
              'sample_shape_is_for_future_only_no_png_resampled':True,'all_source_dimensions':[1024,1024],
              'proposed_outer_padding_canvas':[256,256],'outer_padding_and_root_not_executed':True,
              'per_phase_scales':None,'runtime_registration':None,'approved_scale':None,
              'head_reference_native_px':target_head,'shoulder_hip_reference_native_px':target_torso,
              'bbox_used_for_scale':False,'alpha_components_removed':0,'strict_size_accepted':False,
              'projection_limit':'头部俯仰、躯干弯曲、遮挡及近远侧透视只记录；本工具不将二维投影改成三维骨尺。'}
    save(out/'common-scale-proposal.json',common)
    save(out/'all-source-anatomy-and-semantic-measurements.json',{'manual_points_input':rec(points_path),'measurements':measurements,
         'point_definitions':POINTS,'all_preview_pages':previews,'runtime_points_not_approved':True})
    save(out/'next-contact-and-release-plan.json',{
        'root':None,'grip':None,'override':None,'hurtboxes':None,'actor_contact_point':None,
        'already_measured':'六源A/D腹腰表面、R骨盆参照及04/05的E卸重表面，全部是本人源空间读数，含逐点误差。',
        'next_steps':['根实际看完整测点页和各尺偏差后裁定唯一整图sample比例；不逐相体积拟合。',
                      '获准后仅由forge_backend对完整RGBA做128二值及共同整图采样；不删分量或裁Alpha框。',
                      '按哥莫拉05/06/07/09完整背部表面独立测接触，并和初代00–03的A/D腹腰表面配对；不能把A先称为真实接触。',
                      '04/05按初代E/R和哥莫拉08/10背缘逐相独立量，结合本人现装thrown_back[0]骨盆/头颈测接续；杰顿root/grip不参与计算。',
                      '只读接触页确认后再另审root/grip/override及hurtbox数据方案；当前全部运行参数仍null，未注册。'],
        'same_hold_phase_variants_order_preserved':[0,1,4,5,2,3],
        'old_frozen_reports_not_modified':True,'post_requests':0,'product_writes':0,'godot_runs':0,'git_writes':0})
    save(out/'readonly-byte-verification.json',verify_unchanged(before))
    save(out/'owned-paths.json',{'paths':[rec(p) for p in sorted(out.iterdir()) if p.is_file()]+[rec(points_path),rec(Path(__file__))],
         'root_review_required':True,'candidate_points_scale_and_runtime_values_not_approved':True})
    print(json.dumps({'report':str(out),'nominal_scale':central,'proposed_sample_scale':actual_scale,
                      'proposed_common_sample_canvas':[canvas,canvas],'scale_interval':scale_interval,
                      'head_native_px':target_head,'torso_native_px':target_torso,'owned_sha256':sha(out/'owned-paths.json'),
                      'png_writes':0,'registrations':0,'runtime_parameters_approved':False},ensure_ascii=False))


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--prepare',action='store_true')
    choice.add_argument('--measure',type=Path)
    parser.add_argument('--version',default='measurement-v1')
    args = parser.parse_args()
    if args.prepare:
        prepare()
    else:
        measure(args.measure.resolve(),args.version)

"""只读测初代/哥莫拉本人表面并提出192外画布及接触几何；不注册PNG或运行数据。"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[4]
REPORT=ROOT/'reports/review/2026-11-02/gomora-back-lift-ultraman-contact-proposal-v1'
PREVIOUS=ROOT/'reports/review/2026-11-02/gomora-back-lift-ultraman-179-unregistered-v1'
ACTOR=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-registration-v1/registered18-v1'
ACTOR_PHASES=[5,6,7,9,8,10]
ROOT_REVIEW_SHA='1413bf763a453f762454cf96a7b43573b7afc313badfde8205af772c0bceeec4'
PADDING=[6,6]
RECEIVER_CANVAS=[192,192]
RECEIVER_ANCHOR=[96,184]
ACTOR_ANCHOR=[256,304]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')


def picture(row):
    from PIL import Image
    path=ROOT/row['image']['path']
    assert sha(path)==row['image']['sha256']
    with Image.open(path) as im:
        im.load();assert im.mode=='RGBA'
        result=im.copy()
    if row.get('atlas_rect'):
        x,y,w,h=row['atlas_rect']
        result=result.crop((x,y,x+w,y+h))
    assert list(result.size)==row['dimensions']
    return result


def source_rows():
    gate=PREVIOUS/'candidate-01/root-179-candidate-review.json'
    assert sha(gate)==ROOT_REVIEW_SHA
    approval=read(gate)
    assert approval['reviewer']=='root_delegated_by_user' and approval['no_zetton_coordinates_permitted'] is True
    registration_path=ACTOR/'registration-candidate.json'
    registration=read(registration_path)
    assert registration['cell']==[512,320] and registration['anchor']==ACTOR_ANCHOR
    rows=[]
    controls=[gate,registration_path,PREVIOUS/'candidate-01/processing-receipt.json',
              ROOT/'assets/fighters/ultraman/model-native.png',
              ROOT/'assets/fighters/ultraman/animations/manifest.json',ROOT/'content/fighters/ultraman/state_frames.json',
              ROOT/'core/combat/throw_resolver.gd',ROOT/'core/combat/throw_hold_points.gd']
    for index,actor_phase in enumerate(ACTOR_PHASES):
        actor=next(r for r in registration['phases'] if r['phase']==actor_phase)
        ap=ROOT/actor['native']['path'];assert sha(ap)==actor['native']['sha256']
        rows.append({'id':f'actor-{actor_phase:02d}','phase':index,'role':'actor','image':rec(ap),
                     'dimensions':[512,320],'anchor':ACTOR_ANCHOR,'required_points':['B0','C','B1'],
                     'definitions':{'B0':'后侧背棘/背部表面参考','C':'实际承重或卸重背缘候选表面','B1':'前侧背棘/背部表面参考'}})
        approved=approval['frames'][index]
        rp=ROOT/approved['path'];assert sha(rp)==approved['sha256']
        rows.append({'id':f'receiver-{index:02d}','phase':index,'role':'receiver','image':rec(rp),
                     'dimensions':[179,179],'required_points':['A','D','R']+(['E'] if index>=4 else []),
                     'definitions':{'A':'实际179方腹腰腹侧表面','D':'同横截面的背侧表面','R':'骨盆解剖中线推定参照','E':'实际179方朝向承重背缘的卸重表面；04腹侧，05翻体后的背侧'}})
        controls.extend([ap,rp])
    manifest=read(ROOT/'assets/fighters/ultraman/animations/manifest.json')
    clip=manifest['clips']['thrown_back'];atlas=ROOT/clip['texture'].removeprefix('res://')
    assert sha(atlas)==clip['atlas_sha256']
    rect=clip['rects'][0]
    assert rect==[0,0,192,192] and clip['anchors'][0]==RECEIVER_ANCHOR
    rows.append({'id':'thrown-back-0','role':'continuation','image':rec(atlas),'dimensions':[192,192],
                 'atlas_rect':rect,'atlas_rect_is_complete_declared_runtime_cell_not_alpha_crop':True,
                 'anchor':RECEIVER_ANCHOR,'required_points':['R','S','H'],
                 'definitions':{'R':'本人既有倒立格骨盆中线推定参照','S':'本人倒立格肩胸中心参考','H':'本人倒立格头颈参考'}})
    controls.append(atlas)
    return rows,{p.relative_to(ROOT).as_posix():sha(p) for p in controls}


def jpeg(im,path):
    for q in [90,86,82,78,74,70,66,62,58,54]:
        im.save(path,quality=q,optimize=True,subsampling=0)
        if path.stat().st_size<=150000:break
    assert path.stat().st_size<=150000
    return dict(rec(path),dimensions=list(im.size),jpeg_quality=q)


def point_page(row,path,points=None,scale_override=None):
    from PIL import Image,ImageDraw,ImageFont
    im=picture(row)
    scale=scale_override or (4 if im.width<=192 else 2)
    width=max(744,im.width*scale)
    height=im.height*scale+150
    page=Image.new('RGB',(width,height),'#30343d')
    d=ImageDraw.Draw(page);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
    small=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12)
    d.text((12,8),f"{row['id']} / 完整画布 / 原生坐标 / 显示{scale}x",font=font,fill='white')
    d.text((12,34),'测点/配对提案；不改变原图，不作为严格骨尺或运行验收。',font=font,fill='white')
    panel=Image.alpha_composite(Image.new('RGBA',im.size,'#252b35'),im).convert('RGB')
    panel=panel.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
    p=ImageDraw.Draw(panel)
    step=8 if scale==4 else 16
    for x in range(0,im.width,step):
        p.line((x*scale,0,x*scale,panel.height-1),fill='#4b5361')
        if x%(step*2)==0:p.text((x*scale+1,0),str(x),font=small,fill='white')
    for y in range(0,im.height,step):
        p.line((0,y*scale,panel.width-1,y*scale),fill='#4b5361')
        if y%(step*2)==0:p.text((1,y*scale+1),str(y),font=small,fill='white')
    if points:
        for key,v in points.items():
            x,y=[a*scale for a in v['xy']];radius=v['radius_px']*scale
            color='#86ffae' if key in ['A','E','C'] else '#ffe582' if key in ['R','H'] else '#7ed6ff'
            p.ellipse((x-radius,y-radius,x+radius,y+radius),outline=color,width=1)
            p.line((x-4,y,x+4,y),fill=color);p.line((x,y-4,x,y+4),fill=color)
            p.text((x+5,y-15),key,font=small,fill=color,stroke_width=1,stroke_fill='black')
    page.paste(panel,((width-panel.width)//2,64))
    if points:
        line='；'.join(f"{key}{v['xy']} ±{v['radius_px']}px" for key,v in points.items())
        d.text((12,height-72),line,font=font,fill='white')
    d.text((12,height-42),'原生完整图；骨盆R为推定点。表面C/A/E需看完整人物遮挡。',font=font,fill='white')
    return jpeg(page,path)


def prepare():
    rows,before=source_rows();out=REPORT/'preparation'
    assert not out.exists();out.mkdir(parents=True)
    manual={'schema':'ufeneo.ultraman-gomora.independent-native-contact-points.v1',
            'method':'逐张看本人完整原生图及坐标页，独立量点；未读取任何杰顿root/grip/override数值。',
            'proposed_outer_canvas':RECEIVER_CANVAS,'proposed_fixed_paste_origin':PADDING,
            'proposed_fixed_anchor':RECEIVER_ANCHOR,'all_runtime_values_pending':True,'sources':[]}
    for row in rows:
        view=point_page(row,out/(row['id']+'-full-grid.jpg'))
        manual['sources'].append(dict(row,measurement_page=view,all_complete_views_actually_opened=False,note='',
            points={k:{'xy':None,'radius_px':None,'visibility':None,'note':None} for k in row['required_points']}))
    save(out/'manual-points.TEMPLATE.json',manual)
    save(out/'source-before.json',before)
    print(json.dumps({'report':str(out),'sources':[r['id'] for r in rows],'proposal_executed':False},ensure_ascii=False))


def next_actor_row():
    registration=read(ACTOR/'registration-candidate.json')
    native=next(r['native'] for r in registration['phases'] if r['phase']==11)
    path=ROOT/native['path'];assert sha(path)==native['sha256']
    return {'id':'actor-11-continuation','role':'actor-continuation','image':rec(path),
            'dimensions':[512,320],'anchor':ACTOR_ANCHOR}


def prepare_enlarged():
    rows,before=source_rows();out=REPORT/'preparation-enlarged'
    assert not out.exists();out.mkdir(parents=True)
    views=[]
    for row in [r for r in rows if r['role']=='actor']+[next_actor_row()]:
        views.append(point_page(row,out/(row['id']+'-full-grid-2x.jpg'),scale_override=2))
    save(out/'whole-view-index.json',{'pages':views,'complete_canvas_nearest_integer_display_only':True})
    print(json.dumps({'report':str(out),'pages':len(views),'proposal_executed':False},ensure_ascii=False))


def local(point,anchor):return [point[0]-anchor[0],anchor[1]-point[1]]


def validate_manual(path,rows):
    import numpy as np
    from scipy import ndimage
    manual=read(path)
    assert manual['schema']=='ufeneo.ultraman-gomora.independent-native-contact-points.v1'
    assert [r['id'] for r in rows]==[r['id'] for r in manual['sources']]
    evidence=[]
    for source,row in zip(rows,manual['sources']):
        assert source['image']==row['image'] and row['all_complete_views_actually_opened'] and row['note']
        assert source['required_points']==list(row['points'])
        alpha=np.asarray(picture(source))[...,3];inside=ndimage.distance_transform_edt(alpha>=128);outside=ndimage.distance_transform_edt(alpha<128)
        points=[]
        for key,v in row['points'].items():
            assert len(v['xy'])==2 and all(isinstance(a,int) for a in v['xy'])
            x,y=v['xy'];assert 0<=x<source['dimensions'][0] and 0<=y<source['dimensions'][1]
            assert isinstance(v['radius_px'],(int,float)) and 0<v['radius_px']<=12
            assert v['visibility'] in ['direct_surface','anatomical_estimate'] and v['note']
            signed=float(inside[y,x]-outside[y,x])
            assert v['visibility']!='direct_surface' or abs(signed)<=v['radius_px'],f'{row["id"]}/{key}表面不在声明误差内'
            points.append({'key':key,'alpha_at_point':int(alpha[y,x]),'signed_alpha128_distance_px':signed,
                           'surface_within_stated_error':abs(signed)<=v['radius_px'] if v['visibility']=='direct_surface' else None})
        evidence.append({'id':row['id'],'points':points})
    return manual,evidence


def paired_page(actor,receiver,origin,path,index,measure,annotated):
    from PIL import Image,ImageDraw,ImageFont
    page=Image.new('RGB',(744,1030),'#30343d');d=ImageDraw.Draw(page)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
    d.text((12,8),f'phase{index:02d} / 哥莫拉本人{ACTOR_PHASES[index]:02d} / 完整原生同屏配对提案',font=font,fill='white')
    d.text((12,34),'整图只平移展示；179体尺不变；虚拟192外边距[6,6]，未写注册PNG。',font=font,fill='white')
    for top,color,name in [(98,'#252b35','深底'),(546,'#f1e9df','浅底')]:
        d.text((12,top-28),f'{name} / actor→receiver层序仅演示；非正式游戏遮挡验收',font=font,fill='white')
        scene=Image.new('RGBA',(640,384),color)
        scene.alpha_composite(actor,(64,64));scene.alpha_composite(receiver,(64+origin[0],64+origin[1]))
        if annotated:
            sd=ImageDraw.Draw(scene)
            for key,xy in [('C',measure['actor_contact_xy']),('A/E',measure['actor_contact_xy']),('R',measure['receiver_R_in_actor_canvas'])]:
                x,y=xy[0]+64,xy[1]+64
                c='#75ff9a' if key!='R' else '#ffe079'
                sd.ellipse((x-3,y-3,x+3,y+3),outline=c,width=1)
                sd.text((x+5,y-16),key,font=font,fill=c,stroke_width=1,stroke_fill='#151920')
            sd.line((0,368,639,368),fill='#5d6779')
        page.paste(scene.convert('RGB'),(52,top))
    d.text((12,946),f"C={measure['actor_contact_xy']}；对齐{measure['receiver_contact_key']}={measure['receiver_contact_xy']}；原179平移={origin}",font=font,fill='white')
    d.text((12,974),f"提案root={measure['proposed_receiver_root_relative_actor']}；误差±{measure['contact_position_error_bound_px']:g}px；接触未根签",font=font,fill='white')
    d.text((12,1002),'头/手/背棘要看整图；点重合和Alpha相交统计不能单独证明自然接触。',font=font,fill='white')
    return jpeg(page,path)


def measure(points_path,version):
    import numpy as np
    rows,before=source_rows();manual,point_evidence=validate_manual(points_path,rows)
    assert manual['proposed_outer_canvas']==RECEIVER_CANVAS and manual['proposed_fixed_paste_origin']==PADDING
    assert manual['proposed_fixed_anchor']==RECEIVER_ANCHOR
    out=REPORT/version;assert version.startswith('proposal-') and out.parent==REPORT and not out.exists()
    out.mkdir(parents=True);points_pages=[];pairs=[]
    by_id={r['id']:r for r in manual['sources']}
    for row in manual['sources']:
        points_pages.append(point_page(row,out/(row['id']+'-full-points.jpg'),row['points']))
    for index,actor_phase in enumerate(ACTOR_PHASES):
        ar=by_id[f'actor-{actor_phase:02d}'];rr=by_id[f'receiver-{index:02d}']
        a=picture(ar);b=picture(rr)
        contact_key='A' if index<4 else 'E'
        c=ar['points']['C']['xy'];v=rr['points'][contact_key]['xy']
        origin=[c[0]-v[0],c[1]-v[1]]
        # 只在配对页中用整图平移；不生成已注册外画布或更改原PNG。
        canvas_origin=[origin[i]-PADDING[i] for i in range(2)]
        root_pixel=[canvas_origin[i]+RECEIVER_ANCHOR[i] for i in range(2)]
        proposed_root=local(root_pixel,ACTOR_ANCHOR)
        rpoint=rr['points']['R']['xy'];rworld=[origin[i]+rpoint[i] for i in range(2)]
        mask_a=np.asarray(a)[...,3]>=128;mask_b=np.asarray(b)[...,3]>=128
        placed=np.zeros(mask_a.shape,dtype=bool)
        x,y=origin
        assert 0<=x and 0<=y and x+b.width<=a.width and y+b.height<=a.height,'完整179画布越过完整actor画布，须先审场景外边距'
        placed[y:y+b.height,x:x+b.width]=mask_b
        overlap=mask_a&placed
        actor_grip=local(c,ACTOR_ANCHOR)
        padded_contact=[v[i]+PADDING[i] for i in range(2)]
        receiver_hold_point=local(padded_contact,RECEIVER_ANCHOR)
        assert proposed_root==[actor_grip[i]-receiver_hold_point[i] for i in range(2)]
        datum={'phase':index,'raw_ticks':[20+4*index,23+4*index],'actor_source_phase':actor_phase,
               'actor':ar['image'],'receiver':rr['image'],'receiver_contact_key':contact_key,
               'actor_contact_xy':c,'receiver_contact_xy':v,'whole_179_display_origin_in_actor_canvas':origin,
               'virtual_192_display_origin_in_actor_canvas':canvas_origin,
               'proposed_receiver_root_relative_actor':proposed_root,'proposed_actor_grip':actor_grip,
               'proposed_receiver_hold_point':receiver_hold_point,'receiver_R_in_actor_canvas':rworld,
               'receiver_R_relative_actor':local(rworld,ACTOR_ANCHOR),
               'contact_position_error_bound_px':ar['points']['C']['radius_px']+rr['points'][contact_key]['radius_px'],
               'opaque_intersection_pixels':int(overlap.sum()),'intersection_count_is_not_contact_acceptance':True,
               'pose_mode':'hold' if index<4 else 'root','runtime_approved':False,'actual_contact_accepted':False}
        datum['clean_pair_page']=paired_page(a,b,origin,out/f'phase{index:02d}-full-pair.jpg',index,datum,False)
        datum['marked_pair_page']=paired_page(a,b,origin,out/f'phase{index:02d}-full-pair-marked.jpg',index,datum,True)
        pairs.append(datum)
    legacy=by_id['thrown-back-0'];legacy_r=legacy['points']['R']['xy']
    previous_r=pairs[5]['receiver_R_in_actor_canvas']
    legacy_origin=[previous_r[i]-legacy_r[i] for i in range(2)]
    legacy_root_pixel=[legacy_origin[i]+RECEIVER_ANCHOR[i] for i in range(2)]
    continuation={'source':legacy['image'],'declared_complete_atlas_rect':legacy['atlas_rect'],
       'independently_measured_legacy_R':legacy['points']['R'],
       'previous_phase05_R_world_in_actor_canvas':previous_r,
       'next_thrown_back0_full_cell_origin':legacy_origin,
       'proposed_thrown_back0_root_relative_actor':local(legacy_root_pixel,ACTOR_ANCHOR),
       'R_continuity_delta_at_actor_height_unchanged':[0,0],
       'continuity_error_bound_px':by_id['receiver-05']['points']['R']['radius_px']+legacy['points']['R']['radius_px'],
       'actor_height_continuity_still_requires_actual_main':True,'runtime_approved':False}
    save(out/'precise-contact-and-canvas-proposal.json',{
       'root_candidate_acceptance':rec(PREVIOUS/'candidate-01/root-179-candidate-review.json'),
       'manual_points':rec(points_path),'fixed_outer_canvas':RECEIVER_CANVAS,'unchanged_whole_source_sample_canvas':[179,179],
       'fixed_paste_origin':PADDING,'padding_left_top_right_bottom':[6,6,7,7],'fixed_anchor':RECEIVER_ANCHOR,
       'supersedes_early_tentative_canvas':[256,256],'supersedes_early_tentative_anchor':[128,248],
       'supersession_scope':'只覆盖早期暂拟外透明边距/锚点；179共同体尺、整源及已签读数不变。',
       'actor_canvas':[512,320],'actor_anchor':ACTOR_ANCHOR,
       'coordinates':'图像x右/y下；局部模拟点=(像素x-anchor_x, anchor_y-像素y)',
       'equation':'受方179原点=C_actor-A_or_E_receiver；192原点=179原点-[6,6]；root=local(192原点+[96,184],[256,304])',
       'pairs':pairs,'thrown_back0_continuation':continuation,'point_surface_evidence':point_evidence,
       'point_pages':points_pages,'actual_registered_pngs_created':False,'runtime_data_created':False,
       'strict_size_accepted':False,'actual_contact_accepted':False,'root_grip_override_accepted':False,
       'post_requests':0,'budget_writes':0,'product_writes':0,'godot_runs':0,'git_writes':0})
    after={p:sha(ROOT/p) for p in before};assert before==after
    save(out/'readonly-byte-verification.json',{'before':before,'after':after,'unchanged':True,
       'old_frozen_directories_not_written':True,'png_writes':0,'registered_pngs':0,
       'post_requests':0,'budget_writes':0,'product_writes':0,'godot_runs':0,'git_writes':0})
    print(json.dumps({'report':str(out),'pair_roots':[r['proposed_receiver_root_relative_actor'] for r in pairs],
         'intersection_pixels':[r['opaque_intersection_pixels'] for r in pairs],
         'continuation_root':continuation['proposed_thrown_back0_root_relative_actor'],
         'runtime_approved':False,'png_writes':0},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    choice=p.add_mutually_exclusive_group(required=True)
    choice.add_argument('--prepare',action='store_true');choice.add_argument('--prepare-enlarged',action='store_true');choice.add_argument('--measure',type=Path)
    p.add_argument('--version',default='proposal-v1')
    args=p.parse_args()
    if args.prepare:prepare()
    elif args.prepare_enlarged:prepare_enlarged()
    else:measure(args.measure.resolve(),args.version)

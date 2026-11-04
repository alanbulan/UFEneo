"""背掀接续：冻结源审计、几何提案与固定Forge整帧注册。不会安装正式招式。"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/maintenance'))
from layout_runtime import translate
ROOTS=[[704,918],[712,930],[692,922],[704,930],[712,863],[700,958],[712,912],[700,947],
       [720,920],[724,894],[724,928],[724,932],[700,900],[700,902],[704,942],[716,912],[720,926],[724,934]]
ORDER=[0,1,2,3,4,5,6,7,9,8,10,11,12,13,14,15,16,17]
ALTERNATIVE=[0,1,3,4,5,6,7,2,9,8,10,11,12,13,14,15,16,17]
SURFACES=[[106,98],[106,89],[106,84],[104,82],[94,105],[92,101]]
FORGE_SHA={'forge_palette.py':'fd62e77ccc2d41c2ad50152d51048f5c9f18a3f94f8064247f5c721821607ebe',
           'pixel_reduce.py':'dcfa614389671ca4b1168d4ffe9ea7dbbf94e37bfbd73e54afad46cc15b342cf',
           'forge_core.py':'f227ac7fd81335544a9f33f23cde74324a4e6f906146581562e705d4214bf61b'}
REPORT=ROOT/'reports/gomora-resume'
ACTOR_OUT=ROOT/'art/fighters/gomora/stage4/super3-back-lift-registration/current'
RECEIVER_OUT=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/registered192'
MEASUREMENT=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/measurements/all-source-anatomy-and-semantic-measurements.json'

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def nearest(value):return math.floor(value+.5)
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def relative(path):return path.relative_to(ROOT).as_posix()

def source_records():
    records=[];base=ROOT/'art/fighters/gomora/stage4/super3-back-lift-20261102-v1'
    for phase in range(18):
        receipt=read(base/f'phase-{phase:02d}/request-001/root-actual-source-review-v1.json')
        records.append({'kind':'actor','phase':phase,**receipt['source']})
    base=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/candidate-179'
    for phase,row in enumerate(read(base/'root-179-candidate-review.json')['frames']):
        records.append({'kind':'receiver','phase':phase,'path':row['path'],'sha256':row['sha256']})
    for row in records:
        path=ROOT/translate(row['path']);row['path']=relative(path)
        if not path.is_file():row['status']='missing';continue
        with path.open('rb') as stream:prefix=stream.read(128)
        if prefix.startswith(b'version https://git-lfs.github.com/spec/v1'):
            row['status']='lfs_pointer_pending';continue
        row['actual_sha256']=sha(path)
        if row['actual_sha256']!=row['sha256']:row['status']='sha_mismatch';continue
        with Image.open(path) as image:
            image.load();row['size']=list(image.size);row['mode']=image.mode
            if row['kind']=='receiver':
                assert image.mode=='RGBA' and image.size==(179,179)
                assert set(np.unique(np.asarray(image)[...,3]))<={0,255}
            else:assert image.mode=='RGBA' and image.size==(1024,1024)
        row['status']='passed'
    return records

def audit():
    records=source_records();data={'rows':records,'passed':all(r['status']=='passed' for r in records),
                                  'generation':False,'runtime_install':False}
    save(REPORT/'source-audit.json',data);return data

def geometry():
    data=audit();assert data['passed'],'待LFS/SHA完整，不重复生成源图'
    rows={(r['kind'],r['phase']):r for r in data['rows']}
    measure=read(MEASUREMENT)['measurements'][1:];actors=[];pairs=[]
    for phase,root in enumerate(ROOTS):
        image=Image.open(ROOT/rows['actor',phase]['path']);mask=np.asarray(image)[...,3]>=128
        widths=[int(np.count_nonzero(mask[y,400:720])) for y in range(root[1]-1,root[1]+2)]
        assert max(widths)>20,(phase,'近足宽底窗未成立')
        quarter=[nearest(v/4) for v in root]
        actors.append({'phase':phase,'source':rows['actor',phase],'root_source':root,
                       'quarter_root':quarter,'paste_origin':[256-quarter[0],304-quarter[1]],
                       'near_sole_widths':widths,'registration_rendered':False})
    for rp,ap in enumerate([5,6,7,9,8,10]):
        key='A' if rp<4 else 'E';point=measure[rp]['points'][key]
        sampled=[v*179/1024 for v in point['xy']];x,y=SURFACES[rp]
        mask=np.asarray(Image.open(ROOT/rows['receiver',rp]['path']))[...,3]>0
        assert mask[y,x] and not mask[y+1,x]
        assert math.dist([x,y],sampled)<=point['radius_px']*179/1024
        pairs.append({'receiver_phase':rp,'actor_phase':ap,'semantic_point':key,
                      'original_source_point':point,'sampled_float_point':sampled,'visible_boundary179':[x,y],
                      'receiver_anchor':[96,184],'receiver_padding':[6,6],
                      'receiver_hold_point':[x-90,178-y],'pair_accepted':False})
    result={'schema':1,'actor_registration':actors,'source_order':ORDER,'pairs':pairs,
            'common_actor_scale':[1,4],'common_receiver_scale':[179,1024],
            'actor_cell':[512,320],'actor_anchor':[256,304],
            'receiver_measurement_sha256':sha(MEASUREMENT),'runtime_accepted':False,
            'root_provenance':'保留的final18_readpoint_plan/three_key_prototype/phase05_prototype/phase06_08_order_prototype/update_readpoint_plan_04_13/four_key_prototype脚本；本轮复核实际源宽足底。'}
    save(REPORT/'geometry-proposal.json',result)
    traces={}
    for name,chain in {'original':[(5,0),(6,1),(7,2),(9,3),(8,4),(10,5)],
                       'reordered':[(5,0),(6,1),(7,2),(2,3),(9,3),(8,4),(10,5)]}.items():
        trace=[];last=None
        for ap,rp in chain:
            mask=np.asarray(Image.open(ROOT/rows['actor',ap]['path']))[...,3]>=128
            cy=int(np.flatnonzero(mask[:,640])[0]);quarter=actors[ap]['quarter_root']
            C=[160-quarter[0],quarter[1]-nearest(cy/4)]
            A=[SURFACES[rp][0]-90,178-SURFACES[rp][1]];offset=[C[j]-A[j] for j in [0,1]]
            R=measure[rp]['points']['R']['xy'];pelvis=[offset[0]+R[0]*179/1024-90,offset[1]+178-R[1]*179/1024]
            distance=math.dist(pelvis,last) if last else 0
            trace.append({'actor':ap,'receiver':rp,'contact':C,'receiver_root':offset,'pelvis':pelvis,'step':distance})
            last=pelvis
        traces[name]={'pairs':trace,'max_pelvis_step':max(r['step'] for r in trace)}
    save(REPORT/'trajectory-comparison.json',{'original_order':ORDER,'candidate_order':ALTERNATIVE,
        'each_source_once':True,'traces':traces,'accepted':False,'root_interpolation':False,
        'timing_proposal':{'capture_tick':20,'source01_ticks':8,'other_ticks':4,'total_ticks':76},
        'limits':['只是接触几何，不能代替动态验收。','起手删02和07→02→09须看完整动作。','离背/倒立接续未通过，不能替换正式三级。']})
    return rows,result

def register():
    data=audit();rows={(r['kind'],r['phase']):r for r in data['rows']}
    assert all(rows['actor',p]['status']=='passed' for p in range(18)),'哥莫拉完整源尚未到齐'
    sys.path.insert(0,str(ROOT/'tools/rebuild/shared'));import forge_backend as forge
    with forge.palette_mode('rgb'):backend=forge.backend_info()
    assert backend['files']==FORGE_SHA,'Forge版本不匹配，拒绝运行'
    palette_path=ROOT/'content/fighters/gomora/palette.json';colors=read(palette_path)['colors']
    receipt_path=ACTOR_OUT/'registration.json';prior=read(receipt_path) if receipt_path.exists() else None
    actors=[];receivers=[];pending=[]
    if prior:
        assert prior['palette_sha256']==sha(palette_path) and prior['wrapper_sha256']==sha(ROOT/'tools/rebuild/shared/forge_backend.py')
        assert prior['forge']['files']==FORGE_SHA
        actors=prior['actor']
        for row in actors:
            assert sha(ROOT/row['path'])==row['sha256'] and row['source']['sha256']==rows['actor',row['phase']]['sha256']
        assert len(actors)==18,'不继续不完整或未知候选'
    else:
        assert not ACTOR_OUT.exists(),'有未记录候选，先核现件'
        for phase,root in enumerate(ROOTS):
            source=rows['actor',phase];image=Image.open(ROOT/source['path']).convert('RGBA')
            mask=np.asarray(image)[...,3]>=128
            assert max(np.count_nonzero(mask[y,400:720]) for y in range(root[1]-1,root[1]+2))>20
            down=forge.binarize_alpha(image.copy());down=forge._kcentroid_downscale(down,256,256);forge.binarize_alpha(down)
            with forge.palette_mode('rgb'):forge.apply_palette(down,colors)
            quarter=[nearest(v/4) for v in root];origin=[256-quarter[0],304-quarter[1]]
            canvas=Image.new('RGBA',(512,320));canvas.paste(down,tuple(origin))
            assert np.count_nonzero(np.asarray(canvas)[...,3])==np.count_nonzero(np.asarray(down)[...,3]),'整帧裁切'
            assert set(np.unique(np.asarray(canvas)[...,3]))<={0,255}
            target=ACTOR_OUT/f'{phase:02d}.png';pending.append((target,canvas))
            actors.append({'phase':phase,'source':source,'path':relative(target),'root_source':root,
                           'quarter_root':quarter,'paste_origin':origin,'size':[512,320],'anchor':[256,304]})
    receiver_ready=all(rows['receiver',p]['status']=='passed' for p in range(6))
    if prior and prior.get('receiver'):
        receivers=prior['receiver']
        for row in receivers:assert sha(ROOT/row['path'])==row['sha256'] and row['source']['sha256']==rows['receiver',row['phase']]['sha256']
    elif receiver_ready:
        assert not RECEIVER_OUT.exists(),'有未记录受方候选，先核现件'
        for phase in range(6):
            source=rows['receiver',phase];image=Image.open(ROOT/source['path']).convert('RGBA')
            canvas=Image.new('RGBA',(192,192));canvas.paste(image,(6,6))
            assert np.array_equal(np.asarray(canvas)[6:185,6:185],np.asarray(image))
            target=RECEIVER_OUT/f'{phase:02d}.png';pending.append((target,canvas))
            receivers.append({'phase':phase,'source':source,'path':relative(target),'padding':[6,6],'size':[192,192],'anchor':[96,184]})
    for target,canvas in pending:
        target.parent.mkdir(parents=True,exist_ok=True);canvas.save(target)
    for row in actors+receivers:row['sha256']=sha(ROOT/row['path'])
    for row in data['rows']:
        if row['status']=='passed':assert sha(ROOT/row['path'])==row['sha256'],'冻结输入变化'
    public_backend={k:v for k,v in backend.items() if k not in ['scripts','python']}
    receipt={'schema':1,'actor':actors,'receiver':receivers,'actor_order':ORDER,'forge':public_backend,
             'status':'registered_candidates' if len(receivers)==6 else 'actor_registered_receiver_LFS_pending',
             'forge_commit':'5324342fdfab72430f4e9604f3fe427009f8596d','wrapper_sha256':sha(ROOT/'tools/rebuild/shared/forge_backend.py'),
             'palette_sha256':sha(palette_path),'common_actor_scale':[1,4],'common_receiver_scale':[179,1024],
             'per_phase_scaling':False,'limb_editing':False,'runtime_installed':False,'contact_accepted':False,
             'strict_size_accepted':False,'reviewer':'root_delegated_by_user','scope':'离线完整帧注册候选'}
    if prior and prior.get('static_actor_review'):receipt['static_actor_review']=prior['static_actor_review']
    save(receipt_path,receipt);print(receipt_path,receipt['status'])

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['audit','geometry','register'])
    args=parser.parse_args()
    if args.action=='audit':
        result=audit();print(json.dumps({s:sum(r['status']==s for r in result['rows']) for s in {r['status'] for r in result['rows']}}));return 0 if result['passed'] else 1
    if args.action=='geometry':geometry();print(REPORT/'geometry-proposal.json')
    if args.action=='register':register()
    return 0
if __name__=='__main__':raise SystemExit(main())

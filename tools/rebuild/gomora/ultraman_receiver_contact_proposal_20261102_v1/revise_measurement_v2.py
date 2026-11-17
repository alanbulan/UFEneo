"""保全首读点门失败；按已实看完整坐标页修订边缘读点，不改图或按旧root拟合。"""
from pathlib import Path
import json
import hashlib
import numpy as np
from scipy import ndimage
import propose as p

out=p.REPORT/'measurement-diagnostic-v1';out.mkdir(exist_ok=False)
source=p.REPORT/'manual-native-contact-points-v1.json';d=p.read(source)
evidence=[]
for row in d['sources']:
    alpha=np.asarray(p.picture(row))[...,3]>=128
    signed=ndimage.distance_transform_edt(alpha)-ndimage.distance_transform_edt(~alpha)
    evidence.append({'id':row['id'],'points':[{'key':k,'xy':v['xy'],'signed_distance_px':float(signed[v['xy'][1],v['xy'][0]]),'radius_px':v['radius_px']}
        for k,v in row['points'].items() if v['visibility']=='direct_surface']})
    p.point_page(row,out/(row['id']+'-first-read-points-not-accepted.jpg'),row['points'])
p.save(out/'surface-gate-failure.json',{'status':'first_manual_surface_read_not_accepted','first_assertion':'actor-05/C signed_distance 3.1622776601683795 exceeds 3px',
    'all_surface_read_diagnostics':evidence,'no_pair_or_registration_created':True,'first_manual':p.rec(source)})
changes={
 'actor-05':{'C':[241,174],'B1':[261,164]},
 'actor-06':{'B0':[223,204]},
 'actor-07':{'B0':[216,212]},
 'receiver-03':{'D':[114,65]},
 'actor-08':{'B1':[251,134]},
 'receiver-04':{'A':[106,114],'D':[121,96],'E':[102,111]},
 'actor-10':{'B0':[220,167],'C':[235,145]},
 'receiver-05':{'A':[114,96],'D':[99,108],'E':[99,108]},
}
for row in d['sources']:
    for name,xy in changes.get(row['id'],{}).items():
        old=row['points'][name]['xy'];row['points'][name]['xy']=xy
        row['points'][name]['note']+=f' 首读{old}保全；完整坐标页的外表面读点修订为{xy}；未看配对前完成，非贴图返修或旧坐标拟合。'
d['supersedes_first_manual_surface_read']=p.rec(source)
d['measurement_revision']='首读有点不在3px可见外缘门内；完整坐标页再读边缘，保持每点误差与全部原图不变。'
p.save(p.REPORT/'manual-native-contact-points-v2.json',d)
print(json.dumps({'report':str(out),'manual_v2':str(p.REPORT/'manual-native-contact-points-v2.json')},ensure_ascii=False))

"""将逐张完整坐标页的人工独立读点另存；不查旧target数据或改图。"""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[4]
REPORT=ROOT/'reports/review/2026-11-02/gomora-back-lift-ultraman-contact-proposal-v1'
manual=json.loads((REPORT/'preparation/manual-points.TEMPLATE.json').read_text('utf-8-sig'))
# 手工读完整图。C/B均由完整2x哥莫拉坐标页量；A/D/E/R由完整4x初代页量。
# xy不经Alpha吸附，不根据配对统计、旧杰顿root/grip或bbox反推。
points={
 'actor-05':{'B0':([218,194],3),'C':([243,176],3),'B1':([263,166],3)},
 'actor-06':{'B0':([226,207],3),'C':([250,184],3),'B1':([272,177],3)},
 'actor-07':{'B0':([219,215],3),'C':([246,188],3),'B1':([274,180],3)},
 'actor-09':{'B0':([215,181],3),'C':([237,159],3),'B1':([252,150],3)},
 'actor-08':{'B0':([215,164],3),'C':([234,146],3),'B1':([253,136],3)},
 'actor-10':{'B0':([207,167],3),'C':([226,145],3),'B1':([249,134],3)},
 'receiver-00':{'A':([111,102],3),'D':([113,80],3),'R':([92,85],5)},
 'receiver-01':{'A':([112,92],3),'D':([112,73],3),'R':([91,79],5)},
 'receiver-02':{'A':([110,86],3),'D':([112,66],3),'R':([90,70],5)},
 'receiver-03':{'A':([110,90],3),'D':([114,69],3),'R':([94,63],5)},
 'receiver-04':{'A':([107,112],3),'D':([119,98],3),'R':([91,94],5),'E':([105,109],3)},
 'receiver-05':{'A':([111,98],3),'D':([102,108],3),'R':([89,85],5),'E':([102,108],3)},
 'thrown-back-0':{'R':([98,101],6),'S':([94,139],6),'H':([92,165],5)},
}
for row in manual['sources']:
    key=row['id'];row['all_complete_views_actually_opened']=True
    row['note']='本席逐张实看完整原生坐标页；仅独立人工读点，未打开旧target的root/grip数值。'
    if key.startswith('actor-'):
        path=REPORT/'preparation-enlarged'/f'{key}-full-grid-2x.jpg'
        row['additional_complete_measurement_view']=str(path.relative_to(ROOT)).replace('\\','/')
        row['note']+=' 另实看完整512×320的精确2倍坐标页；C取躯干上背外缘，B0/B1约束该背缘走向。'
    for name,(xy,radius) in points[key].items():
        estimated=name in ['R','S','H']
        text='骨盆解剖中线推定；不是可见硬表面或严格骨尺。' if name=='R' else '整图肩胸解剖中心推定。' if name=='S' else '倒立格头部解剖中心推定。' if name=='H' else '完整像素图可见边缘的人工读点；3px为保守读点/像素外缘误差。'
        if name=='E':text+=' 04取腹侧卸重缘；05后翻已露胸腹，取朝向怪兽的背侧卸重缘，不再强称腹侧。'
        row['points'][name]={'xy':xy,'radius_px':radius,'visibility':'anatomical_estimate' if estimated else 'direct_surface','note':text}
    if key=='receiver-05':
        row['definitions']['E']='后翻后朝向怪兽的背侧卸重表面；与腹侧A分开。'
        row['note']+=' 05胸腹向上/右，故E采用背侧D所在可见外缘；不把翻体后的背侧改称腹侧。'
manual['manual_reviewer']='gomora_super3_resume'
manual['all_13_preparation_views_and_7_enlarged_actor_views_actually_opened']=True
manual['manual_surface_method']='只读整图人工坐标，无自动吸附、裁切、最大分量筛选、拼肢、旋转、缩放或逐相返修。'
out=REPORT/'manual-native-contact-points-v1.json'
with out.open('x',encoding='utf-8',newline='\n') as f:
    json.dump(manual,f,ensure_ascii=False,indent=2);f.write('\n')
print(out)

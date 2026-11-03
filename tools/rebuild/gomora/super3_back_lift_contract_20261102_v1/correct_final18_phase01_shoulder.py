"""复看纠正01举臂时的肩代理；保留初稿，足底和源根逐字不改。"""
import copy
import final18_readpoint_plan as p
from PIL import Image, ImageDraw

def main():
 old_points=p.OUT/'full18-readpoints-candidate.json';old_plan=p.OUT/'full18-registration-plan-candidate.json'
 data=p.read(old_points);plan=p.read(old_plan);row=next(r for r in data['records'] if r['source_phase']==1)
 old_row=copy.deepcopy(row);point=[628,456]
 row['source_points']['near_shoulder_proxy']=point
 origin=row['proposed_paste_origin'];native=[point[0]/4+origin[0],point[1]/4+origin[1]]
 row['proposed_native_points']['near_shoulder_proxy']=native
 row['near_shoulder_proxy_height']=304-native[1]
 row['shoulder_proxy_correction']='01举臂，初稿[667,413]在抬起手/腕附近；复看完整原源后改近肩上臂体积代理[628,456]。原源、足底、髋、注册根均不改。'
 source=p.ROOT/row['source']['path'];im=Image.open(source).convert('RGBA')
 bg=p.annotated(im,row['source_points'],row['feet'],row['root'])
 page=Image.new('RGB',(768,768),'#242934');page.paste(bg.resize((720,720),Image.Resampling.LANCZOS),(24,32))
 ImageDraw.Draw(page).text((6,7),'01 FULL SOURCE / CORRECTED SHOULDER PROXY 628,456 / ROOT UNCHANGED / v2',fill='white')
 image_path=p.OUT/'phase-01-full-source-readpoints-v2.jpg';page.save(image_path,quality=80,optimize=True)
 row['coordinate_page']=p.rec(image_path)
 data['supersedes']=p.rec(old_points);data['only_revision']='phase01肩代理；其余源/根/足底/髋/顺序与所有执行门保持初稿。'
 new_points=p.OUT/'full18-readpoints-candidate-v2.json';p.save(new_points,data)
 for phase in plan['phases']:phase['readpoint_candidate']=p.rec(new_points)
 plan['supersedes']=p.rec(old_plan)
 new_plan=p.OUT/'full18-registration-plan-candidate-v2.json';p.save(new_plan,plan)
 original=(p.OUT/'README.md').read_text('utf8')
 original=original.replace('# 全18源根点计划候选：等待根亲看读窗后授权','# 全18源根点计划候选v2：等待根亲看读窗后授权')
 original=original.replace('| 01 | [712, 930] | 930/947 | 920/939 | 72.75/129.75 |',f"| 01 | [712, 930] | 930/947 | 920/939 | 72.75/{row['near_shoulder_proxy_height']:.2f} |")
 original=original.replace('full18-registration-plan-candidate.json','full18-registration-plan-candidate-v2.json')
 original+=f"\nv2只更正01肩代理：举臂时初稿[667,413]落在手/腕附近，改近肩上臂体积代理[628,456]，对应整图注册整数根下的原生肩高{row['near_shoulder_proxy_height']:.2f}。原始v1记录与页保全；所有18源根、宽底、爪、髋及顺序未改。肩更正不影响根已执行的registered18-v1。v2仅为代理叠加更正，勿重复注册。\n"
 (p.OUT/'README-v2.md').write_text(original,encoding='utf8')
 p.save(p.OUT/'phase01-shoulder-readpoint-correction.json',dict(before=old_row,after=row,
    source_bytes_unchanged=p.sha(source)==row['source']['sha256'],
    foot_root_hip_unchanged=all(row[k]==old_row[k] for k in ['root','feet','quarter_root','proposed_paste_origin','near_hip_proxy_height']),
    root_execution_gates_changed=False,registration_executed=False,runtime_changed=False))
 print(new_plan)

if __name__=='__main__':main()

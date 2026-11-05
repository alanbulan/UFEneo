"""只量化现有整相之间的几何缺口；弧上坐标是设计参考，绝不插值生成素材。"""
import math
from resume import ROOT,read,save,sha
base=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver'
r1=base/'builtin-r01-20261105/candidate.png';r2=base/'builtin-r02-20261105/candidate-5.png'
a=[[223,217],[237,220]];b=[[200,185],[196,167]]
p1=[219,192];p2=[224,188];arcs=[]
for start,end in zip(a,b):
 u=[start[i]-p1[i] for i in [0,1]];v=[end[i]-p2[i] for i in [0,1]];r=math.hypot(*u);s=math.hypot(*v);angle=math.atan2(u[1],u[0]);stop=math.atan2(v[1],v[0]);stop+=2*math.pi if stop<angle else 0
 examples=[]
 for t in [1/3,.5,2/3]:
  rr=r+(s-r)*t;theta=angle+(stop-angle)*t;examples.append({'fraction':t,'relative_knee':[round(rr*math.cos(theta)),round(rr*math.sin(theta))]})
 arcs.append({'start_relative':u,'end_relative':v,'start_thigh_length':r,'end_thigh_length':s,'swing_degrees':math.degrees(stop-angle),'whole_pose_design_examples_only':examples})
d={'schema':1,'installed':False,'generation_performed':False,'source_sha256':{'R01':sha(r1),'R02':sha(r2)},'same_side_knee_delta':[[b[j][i]-a[j][i] for i in [0,1]] for j in [0,1]],'swapped_correspondence_distances':[math.dist(a[0],b[1]),math.dist(a[1],b[0])],'interpretation':'即使近远膝身份互换，约57与51px跳变仍存在，不依赖唯一对应来判断缺口。','arcs':arcs,'timing':{'current':{'20-23':'R00 / A05','24-27':'R01 / A06','28-31':'R02 / A07','32':'A02上提和离背起点'},'candidate_two_phase_layout_not_approved':{'24-25':'R01 / A06','26-27':'新完整收腿早中相 / A06','28-29':'新完整收腿晚中相 / A07','30-31':'R02 / A07','32':'保持原上提边界，需重验'}},'limits':['只延长静帧保持不能生成关节运动，不能用持帧平均速度证明顺滑。','弧样点不是逐帧旋转、插肢或缩放指令；新源若需要必须完整角色。','一张中相是否足够未知；两张相位方案也未保证足够，须按真实整相和动态复核。','接触点、髋/肩/膝/足路径和实际头角余量必须一起核，不能仅闭合膝位置。','不得沿用旧76tick结果签新时序；即使保留t32和t68边界也须重放。']}
save(ROOT/'docs/verification/gomora-r01-r02-existing-frame-gap.json',d)

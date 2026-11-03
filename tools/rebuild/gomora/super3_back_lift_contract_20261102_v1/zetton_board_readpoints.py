"""只读候选四格的真实表面/高分骨尺人工读点，另存新增报告。"""
from zetton_board_forge_candidate import *
POINTS={
 'A':dict(skull_crown=[419,176],skull_chin=[383,279],neck_surface=[369,280],hip_proxy=[268,340],abdomen_surface=[328,326],near_shoulder=[304,261]),
 'B':dict(skull_crown=[450,229],skull_chin=[417,312],neck_surface=[391,302],hip_proxy=[225,304],abdomen_surface=[275,317],near_shoulder=[336,276]),
 'C':dict(skull_crown=[427,82],skull_chin=[421,200],neck_surface=[399,198],hip_proxy=[344,285],abdomen_surface=[366,252],near_shoulder=[348,179]),
 'D':dict(skull_crown=[351,388],skull_chin=[304,309],neck_surface=[305,321],hip_proxy=[288,198],abdomen_surface=[286,235],near_shoulder=[365,290]),
 'MODEL':dict(skull_crown=[481,414],skull_chin=[488,552],neck_surface=[473,556],hip_proxy=[452,724],abdomen_surface=[469,675],near_shoulder=[414,564])}
def main():
 out=OUT/'readpoints-v2';assert not out.exists();out.mkdir()
 source=SRC/'rejected/candidate.png';frozen={p:sha(p)for p in SRC.rglob('*')if p.is_file()};im=Image.open(source).convert('RGBA')
 result=[]
 for name,origin in zip('ABCD',[(0,0),(512,0),(0,512),(512,512)]):
  x,y=origin;cell=im.crop((x,y,x+512,y+512));result.append((name,cell,2))
 model=ROOT/'art/fighters/zetton/stage3/legacy/zetton1/model-reference.png';result.append(('MODEL',Image.open(model).convert('RGBA'),4));rows=[]
 for name,cell,divisor in result:
  bg=Image.new('RGBA',cell.size,'#242934');bg.alpha_composite(cell);d=ImageDraw.Draw(bg);points=POINTS[name]
  for i,(label,(x,y))in enumerate(points.items()):
   d.ellipse((x-3,y-3,x+3,y+3),fill='#fa6688');tx=max(2,min(x-95,cell.width-145));d.text((tx,y-13),label,fill='white')
  d.line([tuple(points['skull_crown']),tuple(points['skull_chin'])],fill='#61f2cb',width=2)
  d.line([tuple(points['neck_surface']),tuple(points['hip_proxy'])],fill='#d8b9ff',width=2)
  jpg(bg.convert('RGB').resize((min(cell.width,720),min(cell.height,720))),out/f'{name}-whole-source-points.jpg')
  alpha=np.asarray(cell)[...,3]
  assert all(alpha[y,x]>=128 for x,y in points.values()),(name,'人工点未落实体')
  rows.append(dict(cell=name,source_points=points,source_point_alpha={k:int(alpha[y,x])for k,(x,y)in points.items()},
   skull_length_source=math.dist(points['skull_crown'],points['skull_chin']),skull_length_native=math.dist(points['skull_crown'],points['skull_chin'])/divisor,
   neck_hip_distance_source=math.dist(points['neck_surface'],points['hip_proxy']),neck_hip_distance_native=math.dist(points['neck_surface'],points['hip_proxy'])/divisor,
   divisor=divisor,uncertainty_source_px=6 if name!='MODEL'else 8,skull_long_ruler_excludes_horns=True,
   note='人工二维表面代理，颈髋距离受透视与屈伸影响，不能当真实解剖骨长；abdomen为可见表面，非抓点/waist。'))
 mp=ROOT/'assets/fighters/zetton/animations/manifest.json';m=read(mp);legacy=[];labels=[]
 for clip,idxs in [('thrown_forward',[2,3]),('down',[0,1])]:
  c=m['clips'][clip];atlas=Image.open(ROOT/c['texture'].removeprefix('res://')).convert('RGBA')
  for idx in idxs:
   x,y,w,h=c['rects'][idx];legacy.append(atlas.crop((x,y,x+w,y+h)));labels.append(f'{clip}{idx} whole {w}x{h}')
 fullpage(legacy,labels,out/'forward-down-whole-unclipped-dark-light.jpg')
 for p,digest in frozen.items():assert sha(p)==digest
 save(out/'manual-readpoints-candidate.json',dict(source=rec(source),model=rec(model),rows=rows,proxy_only=True,
  original_half_scale_retained=True,common_scale_alternative_proposal=[1,3],alternative_not_processed=True,
  strict_size_passed=False,paired_plan_passed=False,grips_created=False,body_parts=False,runtime_installed=False,godot_run=False,post_submitted=False,
  page_correction='旧forward-down-whole-dark-light.jpg把264宽格放256列，右边8px显示不足；本目录unclipped页以264列完整显示，旧页不再作裁脚证据。'))
 print(json.dumps(rows,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

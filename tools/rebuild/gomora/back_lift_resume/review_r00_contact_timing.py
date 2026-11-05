"""仅诊断R00v2更后背部接触，不改变捕获范围、正式或候选运行合同。"""
from PIL import Image,ImageOps,ImageDraw
import numpy as np
from resume import ROOT,ACTOR_OUT,sha,save
src=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r00-20261105/candidate-2.png'
out=ROOT/'reports/gomora-builtin/r00-contact-timing';out.mkdir(parents=True,exist_ok=True)
im=Image.open(src).convert('RGBA').resize((146,219),Image.Resampling.NEAREST);m=np.asarray(im)[...,3]>=128
actors={i:Image.open(ACTOR_OUT/f'{i:02}.png').convert('RGBA') for i in [4,5,6,7]}
surfaces={str(i):[[x,int(np.flatnonzero(np.asarray(a)[...,3][:,x]>=128)[0])] for x in range(225,242)] for i,a in actors.items()}
rows=[]
for dx,dy in [(0,0),(0,11),(-2,11),(-2,13),(-3,14)]:
 paste=[145+dx,63+dy];canvas=Image.new('RGBA',(512,320));canvas.paste(im,tuple(paste));mask=np.asarray(canvas)[...,3]>=128
 # 只为定位风险，不把矩形ROI等同精确解剖掩模。
 head=np.zeros_like(mask);head[paste[1]+45:paste[1]+81,paste[0]+94:paste[0]+123]=mask[paste[1]+45:paste[1]+81,paste[0]+94:paste[0]+123]
 actor_mask=np.asarray(actors[5])[...,3]>=128
 row={'translation_from_pelvis_locked':[dx,dy],'paste':paste,'pelvis_canvas':[paste[0]+61,paste[1]+122],'whole_alpha_overlap_diagnostic':int((mask&actor_mask).sum()),'head_rectangle_overlap_diagnostic':int((head&actor_mask).sum()),'belly_edge_samples':[]}
 for y in [105,107,108,109,111]:
  x=int(np.flatnonzero(m[y])[-1]);cx=x+paste[0];cy=y+paste[1];ay=int(np.flatnonzero(actor_mask[:,cx])[0]);row['belly_edge_samples'].append({'receiver_canvas':[cx,cy],'actor_upper_alpha_y':ay,'signed_gap_down':ay-cy})
 rows.append(row);sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
 for layer in range(2):
  c=Image.alpha_composite(actors[5],canvas) if layer==0 else Image.alpha_composite(canvas,actors[5])
  for f in range(2):
   pic=ImageOps.mirror(c) if f else c;sheet.paste(pic,(512*f,345*layer+24),pic);d.text((512*f+4,345*layer+4),f'dx{dx} dy{dy} layer{layer}',fill='white')
 sheet.save(out/f'pair-{dx}-{dy}.png')
# 仅测试候选完整图注册是否裁切可见身体。
cell=Image.new('RGBA',(256,192));cell.paste(im,(61,-12));assert np.count_nonzero(np.asarray(cell)[...,3]>=128)==np.count_nonzero(m)
data={'schema':1,'source':str(src.relative_to(ROOT)),'source_sha256':sha(src),'installed':False,'accepted':False,'runtime_changed':False,'actor_source_sha256':{str(i):sha(ACTOR_OUT/f'{i:02}.png') for i in actors},'surfaces_alpha128':surfaces,'candidates':rows,'possible_entry':{'raw_tick':20,'receiver_whole_size':[146,219],'candidate_cell':[256,192],'whole_paste_in_cell':[61,-12],'anchor':[128,184],'pelvis_cell':[122,110],'pelvis_local_y_up':[-6,74],'root':[-46,34],'captured_root':[-44,45],'root_delta':[-2,-11],'max_entry_root_delta_unchanged':[14,14],'no_visible_body_cropped_alpha128':True,'low_alpha_specks_outside_cell':2,'contact_receiver_small':[89,107],'contact_receiver_alpha':242,'contact_actor_canvas':[232,181],'contact_actor_alpha':255,'hold_point':[22,89],'grip':[-24,123],'contact_meaning':'上腹开始接触，下腹仍有空隙；不是已完整承重。'},'known_timing':'raw18/19保原相/root；含4tick hitstop，保存vy=-14但thrown实际vy=0；不能把冻结称自然下降。raw20初接触只是设计候选。','limits':['头框0交叠只是诊断，不是全头颈精确无穿体。','近侧悬腿与身体Alpha相交不可自动等同穿体；保留两层观察，不通过改layer隐藏。','腹部上缘与背脊是陡面接触，仍需轮廓及误差验证。','A05→A06背部下沉约14px，必须重设计后续连续轨迹与R01，不能保留旧根高度骤降27px。','此候选没有主游戏/独立回放，不代表捕获链已经修改或验收。']}
save(ROOT/'docs/verification/gomora-r00-contact-timing-design.json',data);print(rows)

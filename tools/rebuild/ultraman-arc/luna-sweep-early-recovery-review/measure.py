# 只读原源，免费整图诊断；不覆盖生产来源或注册。
from pathlib import Path
import json,hashlib,math,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4]
SOURCE=ROOT/'art/fighters/ultraman-arc__luna/stage2/sweep-early-recovery-session-candidate-20261105'
OUT=ROOT/'reports/luna-sweep-early-recovery-review';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'tools/rebuild/shared'))
from forge_backend import _kcentroid_downscale
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(SOURCE/'early-recovery.raw.png')=='fd3fbe8402f6d7c00dc275a1b8eceec20076e2a2afc34408f777e7dbadb33f0e'
b=json.loads((ROOT/'art/fighters/ultraman-arc__luna/stage2/sweep-early-recovery-keyframe-brief-20261105-v1/brief.json').read_text())
for r in b['references']:assert sha(ROOT/r['path'])==r['sha256']
old=json.loads((ROOT/'art/fighters/ultraman-arc__luna/stage2/sweep-recovery-session-candidate-20261105/measurements.json').read_text())
ph=old['phases'];ph['late']=ph.pop('new')
ph['early']={'path':str((SOURCE/'early-recovery.raw.png').relative_to(ROOT)),'manual_landmarks':{'near_knee':[520,690],'near_ankle':[365,899],'near_sole':[360,974],'far_ankle':[723,823],'far_toe':[845,902],'crest_top':[575,87],'chin':[776,355],'chest_disc_diameter':88}}
scale=159/1254;result={'scale':scale,'method':'整帧固定159/1254像素倍率；1536×1024新图输出195×130，旧1254²输出159²，仅整数取整误差。不按bbox、身高或骨长重缩。旧根点诊断x固定80、近鞋底y280；另仅整体横移对齐近踝，纵向同底，严禁当作正式注册。','landmark_uncertainty_source_px':{'joint_centers':12,'crest_chin':8,'disc_diameter':8},'phases':{}}
rootcanvas=Image.new('RGBA',(1280,320),(25,29,38,255));anchorcanvas=rootcanvas.copy()
for i,name in enumerate(['03','early','late','06']):
 p=ph[name]['manual_landmarks'];path=ROOT/ph[name]['path'];im=Image.open(path).convert('RGBA');a=np.array(im)[:,:,3]
 sample=_kcentroid_downscale(im,round(im.width*scale),round(im.height*scale));arr=np.array(sample);arr[arr[:,:,3]<128]=0;arr[arr[:,:,3]>=128,3]=255;sample=Image.fromarray(arr);sample.save(OUT/f'{name}-fixed-scale-alpha128.png');box=sample.getbbox();trans=[80,281-box[3]]
 for c,tx in [(rootcanvas,80),(anchorcanvas,round(114-p['near_ankle'][0]*scale))]:
  c.alpha_composite(sample,(i*320+tx,trans[1]));d=ImageDraw.Draw(c);d.text((i*320+12,12),name,fill='white');d.line((i*320,281,i*320+319,281),fill=(80,95,110))
 metrics={'projected_near_shin':math.dist(p['near_knee'],p['near_ankle']),'head_height_proxy':p['chin'][1]-p['crest_top'][1],'chest_disc_diameter':p['chest_disc_diameter'],'far_ankle_from_near_ankle':[p['far_ankle'][j]-p['near_ankle'][j] for j in (0,1)],'far_toe_from_near_sole':[p['far_toe'][j]-p['near_sole'][j] for j in (0,1)],'near_ankle_registered_x':80+p['near_ankle'][0]*scale}
 stats={'size':im.size,'mode':im.mode,'alpha_min':int(a.min()),'alpha_max':int(a.max()),'alpha_zero_pixels':int((a==0).sum()),'alpha_1_to_127_pixels':int(((a>0)&(a<128)).sum()),'alpha_128_plus_pixels':int((a>=128).sum()),'bbox_alpha_1':Image.fromarray((a>0).astype('uint8')*255).getbbox(),'bbox_alpha_128':Image.fromarray((a>=128).astype('uint8')*255).getbbox(),'edge_alpha_max':int(np.concatenate([a[0],a[-1],a[:,0],a[:,-1]]).max())}
 result['phases'][name]={'path':str(path.relative_to(ROOT)),'sha256':sha(path),'manual_landmarks':p,'alpha':stats,'metrics_source_pixels':metrics,'sample_translation':trans,'sample_size':sample.size}
for name,c in [('comparison-root-common-scale',rootcanvas),('comparison-near-ankle-anchor-diagnostic',anchorcanvas)]:c.resize((2560,640),Image.Resampling.NEAREST).save(OUT/f'{name}-2x.png')
im=Image.open(SOURCE/'early-recovery.raw.png').convert('RGBA');arr=np.array(im);a=arr[:,:,3].copy();arr[a<128]=0;arr[a>=128,3]=255;Image.fromarray(arr).save(OUT/'early-alpha128-clean-diagnostic.png')
for name,bg in [('gray',(65,65,65,255)),('white',(255,255,255,255))]:
 c=Image.new('RGBA',im.size,bg);c.alpha_composite(im);c.convert('RGB').save(OUT/f'alpha-composite-{name}.png')
result['alpha_cleanup']={'method':'仅诊断整图Alpha<128清零、>=128置255；RGBA透明区RGB随之清零，未分肢、描轮廓或修绘。','pixels_removed':int(((a>0)&(a<128)).sum()),'opaque_core_pixels_lost':0,'limitation':'可去透明区隐藏RGB及弱Alpha边缘，但阈值会舍弃原生抗锯齿，不能声称逐像素完全无损或净化图为原生输出。'}
result['scale_interpretation']={'not_equal_bone_length':'固定像素密度只是可复算基线，新画布横向变化可能伴随生成适配，不代表严格同骨长。下列仅数值解释，不实施重缩或注册。','new_to_03_ratios':{'head':268/260,'disc':88/88,'shin_projection':260.20376630633154/223.0425968284982},'late_to_new_uniform_scale_estimates':{'head':296/268,'disc':96/88,'shin_projection':286.8327038536575/260.20376630633154},'late_scale_1_10_new_far_ankle':358*1.1,'late_scale_1_10_new_far_toe':485*1.1,'matching_03_head_disc_shin_scales':[260/268,1,223.0425968284982/260.20376630633154],'matching_03_new_far_ankle_range':[358*223.0425968284982/260.20376630633154,358]}
a=np.array(im)[:,:,3];yy,xx=np.where(a[785:930,650:875]>=128);result['phases']['early']['alpha']['far_shoe_region']=[650,785,875,930];result['phases']['early']['alpha']['far_shoe_lowest_alpha128_y']=int(yy.max()+785);result['phases']['early']['alpha']['near_vs_far_sole_gap']=975-int(yy.max()+785)
result['alpha_cleanup']['hidden_rgb_samples']=[{'xy':[200,500],'rgba':list(map(int,np.array(im)[500,200]))},{'xy':[550,50],'rgba':list(map(int,np.array(im)[50,550]))}]
(OUT/'measurements-reproduced.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))

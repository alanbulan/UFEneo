# 月亮扫腿晚回收的只读整图同尺诊断；不改原源、生产元数据或注册。
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/rebuild/shared'))
from forge_backend import _kcentroid_downscale
out=ROOT/'art/fighters/ultraman-arc__luna/stage2/sweep-recovery-session-candidate-20261105'
rep=ROOT/'reports/luna-sweep-recovery-review';rep.mkdir(parents=True,exist_ok=True)
b=json.loads((ROOT/'art/fighters/ultraman-arc__luna/stage2/sweep-recovery-keyframe-brief-20261105-v1/brief.json').read_text());dst=out/'recovery.raw.png'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(dst)=='4b06e8372f6dcb377eff25193f5f91168eceec1de9edf92a59d2552d47790d58'
for r in b['references']:assert sha(ROOT/r['path'])==r['sha256']
paths={'03':ROOT/b['references'][1]['path'],'new':dst,'06':ROOT/b['references'][2]['path']}
# Visible joint/armor centers, manually estimated from raw pixels. Not anatomical ground truth.
pts={'03':{'near_knee':[409,846],'near_ankle':[267,1018],'near_sole':[244,1101],'far_ankle':[1074,972],'far_toe':[1222,881],'crest_top':[430,245],'chin':[623,505],'chest_disc_diameter':88},'new':{'near_knee':[448,798],'near_ankle':[360,1071],'near_sole':[355,1161],'far_ankle':[662,1005],'far_toe':[788,1096],'crest_top':[494,96],'chin':[727,392],'chest_disc_diameter':96},'06':{'near_knee':[463,755],'near_ankle':[406,1075],'near_sole':[375,1191],'far_ankle':[855,1080],'far_toe':[1046,1125],'crest_top':[532,85],'chin':[773,407],'chest_disc_diameter':104}}
measure={'scale':159/1254,'normalization':'全部1254²整图共同缩到159²；不按bbox或逐张骨长重缩。保留旧注册x平移80，y仅将主近鞋最低Alpha128行移到280。另列相对近踝/近鞋的测点差以区分支撑脚漂移，不作为注册。','landmark_uncertainty_source_px':{'joint_centers':12,'crest_chin':8,'disc_diameter':8},'phases':{}}
canvas=Image.new('RGBA',(960,320),(25,29,38,255)); draw=ImageDraw.Draw(canvas)
for i,(name,path) in enumerate(paths.items()):
 im=Image.open(path).convert('RGBA'); a=np.array(im)[:,:,3]; p=pts[name]; sample=_kcentroid_downscale(im,159,159); arr=np.array(sample); arr[arr[:,:,3]<128]=0; arr[arr[:,:,3]>=128,3]=255; sample=Image.fromarray(arr); sample.save(rep/f'{name}-159.png')
 box=sample.getbbox(); trans=[80,281-box[3]]; frame=Image.new('RGBA',(320,320));frame.alpha_composite(sample,tuple(trans));frame.save(rep/f'{name}-root.png');canvas.alpha_composite(frame,(i*320,0)); draw.text((i*320+12,12),name,fill='white');draw.line((i*320,281,i*320+319,281),fill=(80,95,110));draw.line((i*320+160,270,i*320+160,292),fill=(190,100,100))
 stats={'size':im.size,'mode':im.mode,'alpha_zero_pixels':int((a==0).sum()),'alpha_nonzero_pixels':int((a>0).sum()),'alpha_1_to_127_pixels':int(((a>0)&(a<128)).sum()),'alpha_128_plus_pixels':int((a>=128).sum()),'bbox_alpha_1':Image.fromarray((a>0).astype('uint8')*255).getbbox(),'bbox_alpha_128':Image.fromarray((a>=128).astype('uint8')*255).getbbox(),'edge_alpha_max':int(np.concatenate([a[0],a[-1],a[:,0],a[:,-1]]).max())}
 metrics={'projected_near_shin':math.dist(p['near_knee'],p['near_ankle']),'head_height_proxy':p['chin'][1]-p['crest_top'][1],'chest_disc_diameter':p['chest_disc_diameter'],'far_ankle_from_near_ankle':[p['far_ankle'][j]-p['near_ankle'][j] for j in (0,1)],'far_toe_from_near_sole':[p['far_toe'][j]-p['near_sole'][j] for j in (0,1)]}
 # Entire far shoe lies in these y/x regions; alpha threshold is diagnostic, not changed raw.
 far_regions={'03':[1040,860,1254,1090],'new':[600,975,810,1140],'06':[790,1050,1070,1160]}; x0,y0,x1,y1=far_regions[name]; yy,xx=np.where(a[y0:y1,x0:x1]>=128); stats['far_shoe_region']=far_regions[name];stats['far_shoe_lowest_alpha128_y']=int(yy.max()+y0);stats['near_vs_far_sole_gap']=stats['bbox_alpha_128'][3]-1-stats['far_shoe_lowest_alpha128_y']; metrics['scaled_sole_gap']=stats['near_vs_far_sole_gap']*159/1254
 measure['phases'][name]={'path':str(path.relative_to(ROOT)),'sha256':sha(path),'alpha':stats,'manual_landmarks':p,'metrics_source_pixels':metrics,'sample_translation':trans,'sample_sha256':sha(rep/f'{name}-159.png')}
canvas.save(rep/'comparison-root-common-scale.png'); canvas.resize((1920,640),Image.Resampling.NEAREST).save(rep/'comparison-root-common-scale-2x.png')
(rep/'measurements-reproduced.json').write_text(json.dumps(measure,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(measure,ensure_ascii=False,indent=2))

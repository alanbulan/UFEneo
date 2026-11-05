"""整链首承重段真实像素接触预检；不改运行合同，不代表动态验收。"""
from PIL import Image,ImageDraw,ImageOps
import numpy as np,math
from resume import ROOT,ACTOR_OUT,sha,save
base=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver';out=ROOT/'reports/gomora-builtin/main-chain-geometry';out.mkdir(parents=True,exist_ok=True)
specs={
'R00v2':('builtin-r00-20261105/candidate-2.png',(146,219),(61,122),(89,107),(94,45,123,81)),
'R01':('builtin-r01-20261105/candidate.png',(176,193),(72,110),(98,104),(109,45,135,80)),
'early':('builtin-r01-r02-early-20261105/candidate.png',(176,193),(72,113),(102,102),(106,47,134,81)),
'mid':('builtin-r01-r02-mid-20261105/candidate.png',(168,154),(73,82),(98,74),(102,16,132,49)),
'late':('builtin-r01-r02-late-20261105/candidate.png',(210,105),(99,78),(114,78),(138,10,165,43)),
'R02':(str(ROOT/'reports/gomora-builtin/bridge-review/R02-full-210.png'),(210,105),(97,77),(114,81),(138,10,165,43))}
table=[(t,'R00v2',5,[204,196],[-46,34],[-24,123],[22,89]) for t in range(20,24)]+[(24,'R01',6,[204,203],[-46,27],[-26,107],[20,80]),(25,'early',6,[209,202],[-41,28],[-17,113],[24,85]),(26,'mid',6,[214,199],[-36,31],[-17,113],[19,82]),(27,'mid',6,[217,198],[-33,32],[-14,114],[19,82]),(28,'late',7,[219,196],[-31,34],[-22,108],[9,74]),(29,'late',7,[222,194],[-28,36],[-19,110],[9,74]),(30,'R02',7,[224,188],[-24,49],[-15,112],[9,63]),(31,'R02',7,[224,188],[-24,49],[-15,112],[9,63])]
rows=[];sources={}
for tick,label,ap,hip,root,grip,hold in table:
 file,size,lp,contact,roi=specs[label];path=base/file;raw=Image.open(path).convert('RGBA').resize(size,Image.Resampling.NEAREST);arr=np.array(raw);original_alpha=int(arr[contact[1],contact[0],3]);arr[:,:,3]=np.where(arr[:,:,3]>=128,255,0);im=Image.fromarray(arr);a=Image.open(ACTOR_OUT/f'{ap:02}.png').convert('RGBA');am=np.asarray(a)[...,3]>=128;p=[hip[i]-lp[i] for i in [0,1]];cp=[p[i]+contact[i] for i in [0,1]];assert [grip[0]+256,304-grip[1]]==cp;assert [grip[i]-hold[i] for i in [0,1]]==root;assert am[cp[1],cp[0]] and original_alpha>=128
 layer=Image.new('RGBA',a.size);layer.paste(im,tuple(p));mask=np.asarray(layer)[...,3]>0;head=np.zeros_like(mask);l,t,r,b=roi;head[p[1]+t:p[1]+b,p[0]+l:p[0]+r]=mask[p[1]+t:p[1]+b,p[0]+l:p[0]+r]
 ys,xs=np.where(head);worst=0
 for dx in range(-2,3):
  for dy in range(-2,3):
   if dx*dx+dy*dy<=4:worst=max(worst,int(am[ys+dy,xs+dx].sum()))
 row={'tick':tick,'receiver':label,'actor':ap,'source_sha256':sha(path),'source_size':list(Image.open(path).size),'fixed_whole_size':list(size),'pelvis_canvas':hip,'root':root,'grip':grip,'hold_point':hold,'contact_canvas':cp,'receiver_original_alpha':original_alpha,'actor_alpha':int(np.asarray(a)[cp[1],cp[0],3]),'head_roi_overlap':int((head&am).sum()),'head_roi_overlap_worst_translation_radius2':worst,'pelvis_step':0 if not rows else math.dist(hip,rows[-1]['pelvis_canvas'])};rows.append(row);sources[label]={'path':str(path.relative_to(ROOT)),'sha256':sha(path),'fixed_whole_size':list(size),'local_pelvis':list(lp)}
 sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
 for z in range(2):
  c=Image.alpha_composite(a,layer) if z==0 else Image.alpha_composite(layer,a)
  for f in range(2):
   pic=ImageOps.mirror(c) if f else c;sheet.paste(pic,(512*f,345*z+24),pic);d.text((512*f+4,345*z+4),f't{tick} {label} A{ap} contact{cp} layer{z}',fill='white')
 sheet.save(out/f'tick{tick}-{label}.png')
data={'schema':1,'sources':sources,'frames':rows,'accepted':False,'installed':False,'capture_boxes_changed':False,'existing_entry_limit':[14,14],'entry_delta':[-2,-11],'root_registration':'新相统一256x320，anchor128,288，髋cell122,214；旧R02及后相只整格pad104。','limits':['名义实体共点且头ROI为0不是全头颈安全或动态承重验收。','半径2平移敏感值保留，不能掩盖近角余量。','全部素材仅一次固定整图NEAREST尺寸和统一Alpha128，不逐tick缩放/旋转/改层。','保留原t32之后离背、倒立、落地合同；新前段需要真实主游戏与独立回放。','近侧腿与身侧Alpha相交不能自动当穿体，也不许改层遮盖。']}
save(ROOT/'docs/verification/gomora-main-chain-registration.json',data);print([(r['tick'],r['head_roi_overlap'],r['head_roi_overlap_worst_translation_radius2'],r['pelvis_step']) for r in rows])

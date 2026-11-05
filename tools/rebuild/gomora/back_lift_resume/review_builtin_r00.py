"""R00整帧等比配对；保留真实alpha，不抠光晕、不安装。"""
import json, math
import numpy as np
from PIL import Image,ImageDraw,ImageOps
from resume import ROOT,ACTOR_OUT,sha,save
src=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r00-20261105/candidate.png'
out=ROOT/'reports/gomora-builtin/r00-review';out.mkdir(parents=True,exist_ok=True)
im=Image.open(src).convert('RGBA');a=np.asarray(im)[...,3]
# 独立人工读点：脸顶至下颌约180，统一到约25原生像素，完整图等比缩放。
scale=1/7;size=(round(im.width*scale),round(im.height*scale));small=im.resize(size,Image.Resampling.NEAREST)
pelvis=[455,850];contact=[570,750];world_pelvis=[206,185];world_contact=[241,174]
local=lambda p:[round(p[0]*size[0]/im.width),round(p[1]*size[1]/im.height)]
sp=local(pelvis);sc=local(contact)
actor=Image.open(ACTOR_OUT/'05.png').convert('RGBA');rows=[]
for kind,target,point in [('pelvis_locked',world_pelvis,sp),('abdomen_locked',world_contact,sc)]:
 paste=[target[i]-point[i] for i in (0,1)];layer=Image.new('RGBA',actor.size);layer.paste(small,tuple(paste));sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
 for z in range(2):
  comp=Image.alpha_composite(actor,layer) if z==0 else Image.alpha_composite(layer,actor)
  for f in range(2):
   pic=ImageOps.mirror(comp) if f else comp;sheet.paste(pic,(512*f,345*z+24),pic);d.text((512*f+4,345*z+4),kind+f' layer{z}',fill='white')
 sheet.save(out/f'{kind}.png');rows.append({'kind':kind,'paste':paste,'pelvis_canvas':[paste[i]+sp[i] for i in (0,1)],'abdomen_canvas':[paste[i]+sc[i] for i in (0,1)]})
back=Image.new('RGBA',im.size,(48,52,60,255));back.alpha_composite(im);back.convert('RGB').save(out/'true-alpha-composite.png')
data={'schema':1,'source_sha256':sha(src),'size':list(im.size),'mode':im.mode,'alpha':{'zero':int((a==0).sum()),'partial':int(((a>0)&(a<255)).sum()),'opaque':int((a==255).sum()),'maximum':int(a.max()),'below_16_nonzero':int(((a>0)&(a<16)).sum())},'alpha_findings':'原预览光晕多数来自alpha0区域RGB；真实合成未见宽光晕。主体常为253，无255不能单独判失败。低alpha残留仍保留，不抠图。','source_points':{'pelvis':pelvis,'pelvis_radius':45,'abdomen':contact,'abdomen_range':[[535,790],[580,745]],'head_length_approx':180},'uniform_whole_size':list(size),'local_pelvis':sp,'local_abdomen':sc,'required_world_pelvis':world_pelvis,'required_world_abdomen':world_contact,'pairs':rows,'accepted':False,'installed':False,'geometry_result':'整图前倾直立、屈膝，未形成足够腹侧前伸。保髋配对腹点距指定背点约19px；腹点对齐则髋约向前19px。手工点有误差，不能靠移动整帧同时满足名义两点。','limits':['只读离线两向两层配对，不是主游戏截图。','头长和髋点是人工估计，未当精确骨点。','不局部变形、不切肢、不去背景、不安装。']}
save(src.parent/'review.json',data);print(json.dumps(rows))

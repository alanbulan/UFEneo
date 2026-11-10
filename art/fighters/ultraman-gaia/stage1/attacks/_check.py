import sys, os
from PIL import Image, ImageDraw
import numpy as np

def maxrun(row):
    best=cur=0
    for v in row:
        cur=cur+1 if v else 0; best=max(best,cur)
    return best

def stats(p):
    im=Image.open(p).convert('RGBA'); a=np.array(im); al=a[:,:,3]; m=al>128
    ys,xs=np.where(m)
    if not len(ys): return im.size,0,0,0,0,0,0
    H=int(ys.max()-ys.min()+1); top=int(ys.min())
    w=max(maxrun(m[y]) for y in range(top,top+max(6,int(H*0.12))))
    return im.size,H,w,round(H*0.14694656,1),round(w/149.715*100,1),int((al>=200).sum()),int(((al>=128)&(al<200)).sum())

clip=sys.argv[1]; files=sys.argv[2:]
rows=[]
for p in files:
    s=stats(p); rows.append((p,s)); print(os.path.basename(p),s)
th=360; pad=10
ims=[]
for p,_ in rows:
    im=Image.open(p).convert('RGBA'); im.thumbnail((th,th),Image.LANCZOS); ims.append((os.path.basename(p),im))
W=sum(im.width for _,im in ims)+pad*(len(ims)+1); Hh=th+40
sheet=Image.new('RGBA',(W,Hh),(232,232,232,255)); d=ImageDraw.Draw(sheet)
x=pad
for name,im in ims:
    sheet.alpha_composite(im,(x,30)); d.text((x,8),name,fill=(0,0,0,255)); x+=im.width+pad
out=f'art/fighters/ultraman-gaia/stage1/attacks/landing/test/{clip}-contact.png'
sheet.convert('RGB').save(out); print('sheet',out,sheet.size)

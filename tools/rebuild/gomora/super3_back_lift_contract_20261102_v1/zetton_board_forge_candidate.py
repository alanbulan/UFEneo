"""新板四格整图离线候选；无网络、产品写入、Godot或Git。"""
from pathlib import Path
import hashlib,json,sys,math
import numpy as np
from PIL import Image,ImageDraw
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/rebuild/shared'))
import forge_backend as forge
SRC=ROOT/'art/fighters/zetton/stage5/gomora-super3-back-lift-receiver-20261102-v1/board-2x2/request-001'
OUT=ROOT/'reports/review/2026-11-02/gomora-super3-zetton-board-forge-candidate-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,d):
 with p.open('x',encoding='utf8',newline='\n')as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def jpg(im,p):
 assert im.width<=768
 im.convert('RGB').save(p,quality=81,optimize=True)
 assert p.stat().st_size<150000
def grid(im,p,label):
 im=im.copy(); bg=Image.new('RGBA',im.size,'#242934');bg.alpha_composite(im);d=ImageDraw.Draw(bg)
 step=64 if im.width==512 else 128
 for x in range(0,im.width,step):
  d.line((x,0,x,im.height-1),fill='#687180');d.text((x+2,2),str(x),fill='white')
 for y in range(0,im.height,step):
  d.line((0,y,im.width-1,y),fill='#687180');d.text((2,y+2),str(y),fill='white')
 scale=min(1,720/im.width,720/im.height)
 thumb=bg.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
 page=Image.new('RGB',(thumb.width,thumb.height+25),'#242934');page.paste(thumb.convert('RGB'),(0,25));ImageDraw.Draw(page).text((5,5),label,fill='white');jpg(page,p)
def fullpage(frames,labels,p):
 w=max(im.width for im in frames);h=max(im.height for im in frames);cols=min(768//w,len(frames));rows=math.ceil(len(frames)/cols)
 page=Image.new('RGB',(cols*w,rows*(h+24)*2),'#242934');d=ImageDraw.Draw(page)
 for j,col in enumerate(['#242934','#dedcd1']):
  base=j*rows*(h+24);d.rectangle((0,base,page.width,base+rows*(h+24)),fill=col)
  for i,(im,label)in enumerate(zip(frames,labels)):
   x=i%cols*w;y=base+i//cols*(h+24)
   d.text((x+4,y+4),label,fill='white'if j==0 else '#242934')
   # Whole cells kept at native 1:1; a wider legacy cell gets transparent extra column.
   page.paste(im,(x,y+24),im)
 jpg(page,p)
def main():
 source=SRC/'rejected/candidate.png';assert sha(source)=='ba8b537b0de8c54521a735676487ce60afda65b5efbefc4057ae17b9b0526642'
 assert not OUT.exists();OUT.mkdir();(OUT/'native').mkdir()
 frozen={p:sha(p)for p in SRC.rglob('*')if p.is_file()}
 palette=ROOT/'content/fighters/zetton/palette.json';frozen[palette]=sha(palette);colors=read(palette)['colors']
 for p in (ROOT/'reports/review/2026-11-02/gomora-super3-zetton-board-root-source-v1').glob('*.json'):frozen[p]=sha(p)
 im=Image.open(source).convert('RGBA');rows=[];frames=[]
 for name,(x,y)in zip('ABCD',[(0,0),(512,0),(0,512),(512,512)]):
  cell=im.crop((x,y,x+512,y+512));mask=np.asarray(cell)[...,3]>=128
  down=forge.binarize_alpha(cell.copy());down=forge._kcentroid_downscale(down,256,256);forge.binarize_alpha(down)
  with forge.palette_mode('rgb'):forge.apply_palette(down,colors)
  p=OUT/f'native/{name}.png';down.save(p);frames.append(down)
  grid(cell,OUT/f'source-{name}-full-coordinate.jpg',f'{name} whole 512 cell / source coordinates / weak Alpha source retained')
  rows.append(dict(cell=name,rect=[x,y,512,512],native=rec(p),native_bbox=down.getbbox(),source_solid_bbox=Image.fromarray(mask).getbbox(),
   source_edges_solid_pixels=int(mask[0].sum()+mask[-1].sum()+mask[:,0].sum()+mask[:,-1].sum()),alpha_values=list(map(int,np.unique(np.asarray(down)[...,3])))))
 fullpage(frames[:3],list('ABC'),OUT/'ABC-whole-native-dark-light.jpg');fullpage(frames[3:],['D'],OUT/'D-whole-native-dark-light.jpg')
 model=ROOT/'art/fighters/zetton/stage3/legacy/zetton1/model-reference.png';frozen[model]=sha(model)
 grid(Image.open(model).convert('RGBA'),OUT/'model-reference-full-coordinate.jpg','MODEL whole high-res reference / grid128')
 mp=ROOT/'assets/fighters/zetton/animations/manifest.json';frozen[mp]=sha(mp);manifest=read(mp);legacy=[];labs=[];legacyrecords=[]
 for clip,idxs in [('idle',[0]),('thrown_back',[0,1]),('thrown_forward',[2,3]),('down',[0,1])]:
  c=manifest['clips'][clip];atlas=ROOT/c['texture'].removeprefix('res://');frozen[atlas]=sha(atlas);atlasim=Image.open(atlas).convert('RGBA')
  for idx in idxs:
   x,y,w,h=c['rects'][idx];frame=atlasim.crop((x,y,x+w,y+h));legacy.append(frame);labs.append(f'{clip}{idx}')
   legacyrecords.append(dict(clip=clip,index=idx,atlas=rec(atlas),rect=[x,y,w,h],bbox=frame.getbbox(),edge_right_alpha_pixels=int((np.asarray(frame)[:,-1,3]>0).sum())))
 fullpage([frames[3]]+legacy[:3],['D']+labs[:3],OUT/'D-installed-back-whole-dark-light.jpg')
 fullpage(legacy[3:],[*labs[3:]],OUT/'forward-down-whole-dark-light.jpg')
 old=ROOT/'art/fighters/zetton/stage2/generation/phase3_defense/down/01/raw.png';frozen[old]=sha(old);oldim=Image.open(old).convert('RGBA');assert oldim.size==(887,1774)
 grid(oldim,OUT/'old-down-whole-source-coordinate.jpg','OLD DOWN whole887x1774 / grid128 / no recrop')
 for k in range(2):
  cell=oldim.crop((0,k*887,887,(k+1)*887));grid(cell,OUT/f'old-down-{k}-whole-source-coordinate.jpg',f'OLD DOWN {k} whole887 cell / grid128')
 for p,digest in frozen.items():assert sha(p)==digest,str(p)
 save(OUT/'candidate-processing.json',dict(source=rec(source),common_scale=[1,2],native_cell=[256,256],phases=rows,palette=rec(palette),backend=forge.backend_info(),
  preserved_inputs=[rec(p)for p in frozen],legacy_cells=legacyrecords,whole_cells_only=True,palette_mode='rgb',alpha_threshold=128,
  per_phase_fit=False,rotation=False,mirror=False,body_parts=False,source_rewritten=False,forty_pixel_border_passed=False,
  root_source_review_json_rewritten=False,strict_size_passed=False,paired_static_plan_accepted=False,runtime_installed=False,godot_run=False,post_submitted=False))
 print(str(OUT))
if __name__=='__main__':main()

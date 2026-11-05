"""内置生图R02真实Alpha与完整帧配对诊断；不安装，不发生成请求。"""
import os,sys,json,hashlib,argparse
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT/'tools/rebuild/shared'),str(ROOT/'tools/rebuild/gomora/back_lift_resume')]
# 固定Forge路径由调用方提供；不下载、不更换版本。
import forge_backend as forge
from resume import FORGE_SHA
assert forge.backend_info()['files']==FORGE_SHA
parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=int,choices=[1,2,3,4,5],default=1);args=parser.parse_args()
fifth=args.candidate==5
fourth=args.candidate==4
third=args.candidate==3
second=args.candidate>=2
source_name=f'candidate-{args.candidate}.png' if second else 'candidate.png'
source_path=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r02-20261105'/source_name
expected='edda91826d3c7b13e7c255dd5544228224ca387d2147d81951d75488682f1ccf' if fifth else 'c11be3012441d0808be0fd2ecc84558b81ece3178fbfab94c6c7b399104125b8' if fourth else '60806c5b0d590d50f4cb3824c4e701026e4efc9c9b1c514dcaf36b3646c623b2' if third else '0bb3e641890632da50580d3ea25b56dfca4e5bf2ac4c77fef58033f9f43b612d' if second else '40717933f95997ffd78bc6be4d5affa57a5d1587fdea812afaa9d3cb20c6ff00'
assert hashlib.sha256(source_path.read_bytes()).hexdigest()==expected
source=Image.open(source_path)
assert source.mode=='RGBA' and source.size==(1774,887)
actor_path=ROOT/'art/fighters/gomora/stage4/super3-back-lift-registration/current/07.png'
assert hashlib.sha256(actor_path.read_bytes()).hexdigest()=='359a96088d95e0a9dc29ad5e95db83f0ed72311f64e6f7f4fd57dba7a42d4114'
a=Image.open(ROOT/'art/fighters/gomora/stage4/super3-back-lift-registration/current/07.png').convert('RGBA');am=np.asarray(a)[...,3]>0
out=ROOT/(f'reports/gomora-builtin/review-{args.candidate}' if second else 'reports/gomora-builtin/review');out.mkdir(parents=True,exist_ok=True)
rows=[]
for size in ([(180,90),(200,100),(220,110)] if fourth else [(200,100),(220,110),(240,120)] if second else [(160,80),(178,89),(200,100)]):
 im=forge.binarize_alpha(source.copy());im=forge._kcentroid_downscale(im,*size);forge.binarize_alpha(im)
 # 骨盆最低点仅作对照；另核真正腹侧点，不混为已接受承重。
 mask=np.asarray(im)[...,3]>0;x=round((740 if fourth else 750 if third else 835 if second else 900)*size[0]/1774)
 column=np.where(mask[:,x])[0];gaps=np.where(np.diff(column)>1)[0]
 y=int(column[gaps[0]] if fourth and len(gaps) else column[-1])
 cx,cy=241,192;paste=(cx-x,cy-y)
 canvas=Image.new('RGBA',a.size);canvas.paste(im,paste)
 overlap=int((am&(np.asarray(canvas)[...,3]>0)).sum())
 assert np.count_nonzero(np.asarray(canvas)[...,3])==mask.sum()
 sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
 for layer in range(2):
  c=Image.alpha_composite(a,canvas) if layer==0 else Image.alpha_composite(canvas,a)
  for f in range(2):
   pic=c if f==0 else ImageOps.mirror(c);sheet.paste(pic,(f*512,layer*345+24),pic)
   d.text((f*512+8,layer*345+5),f'{size} alpha128 {"ambiguous-body" if fourth else "pelvis-low"} diagnostic / overlap {overlap} / layer{layer}',fill='white')
 sheet.save(out/f'pair-{size[0]}.png');im.save(out/f'full-{size[0]}.png')
 rows.append({'size':list(size),'scale':size[0]/1774,('ambiguous_upper_body_boundary' if fourth else 'pelvis_low_boundary'):[x,y],'actor_contact':[cx,cy],'paste':list(paste),'alpha_overlap_pixels':overlap,'accepted':False})
print(json.dumps(rows))

# 腹侧候选外缘对照；每候选各使用同一整图尺度，不改变局部比例。
width=200 if fourth else 220 if second else 200
im=Image.open(out/f'full-{width}.png'); mask=np.asarray(im)[...,3]>0
for sx in ((840,860,880) if fourth else (900,960,1000) if third else (960,1000,1040) if second else (1000,1030,1060)):
    x=round(sx*width/1774);column=np.where(mask[:,x])[0]
    # 第四版双拳位于腹侧之下，不能把列最末Alpha当腹缘。取最上连续段末端作有歧义的体表候选。
    gaps=np.where(np.diff(column)>1)[0]
    y=int(column[gaps[0]] if fourth and len(gaps) else column[-1]);paste=(241-x,192-y)
    canvas=Image.new('RGBA',a.size);canvas.paste(im,paste)
    assert np.count_nonzero(np.asarray(canvas)[...,3])==mask.sum()
    sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
    for layer in range(2):
        c=Image.alpha_composite(a,canvas) if layer==0 else Image.alpha_composite(canvas,a)
        for f in range(2):
            pic=c if f==0 else ImageOps.mirror(c);sheet.paste(pic,(f*512,layer*345+24),pic)
            d.text((f*512+8,layer*345+5),f'abdomen source x={sx} native={x,y} layer{layer}',fill='white')
    sheet.save(out/f'abdomen-{sx}.png')
    yy,xx=np.where(mask);hit=am[yy+paste[1],xx+paste[0]]
    head=(xx>=round((1170 if fourth else 1190 if third else 1170 if second else 1340)*width/1774))&(yy<=round((560 if fourth else 350 if third else 365 if second else 390)*width/1774))
    arm=(xx>=round((750 if fourth else 750 if third else 790 if second else 1090)*width/1774))&(xx<=round((1030 if fourth else 1110 if second else 1380)*width/1774))&(yy>=round((270 if fourth else 350 if third else 430 if second else 540)*width/1774))&(yy<=round((470 if fourth else 500 if third else 610 if second else 680)*width/1774))
    rows.append({'size':[width,width//2],'source_abdomen_column':sx,'surface_ambiguous_under_arms':fourth,'column_selection':'upper_contiguous_run' if fourth else 'last_alpha','contact':[x,y],'paste':list(paste),
                 'alpha_overlap_pixels':int(hit.sum()),'head_roi_overlap_pixels':int(hit[head].sum()),
                 'near_forearm_roi_overlap_pixels':int(hit[arm].sum()),'accepted':False})
alpha=np.asarray(source)[...,3]
summary={'schema':1,'source_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),
         'source_size':list(source.size),'source_mode':source.mode,'alpha_levels':len(np.unique(alpha)),
         'transparent_pixels':int((alpha==0).sum()),'opaque_pixels':int((alpha==255).sum()),
         'partial_alpha_pixels':int(((alpha>0)&(alpha<255)).sum()),'alpha_lt128_nonzero_pixels':int(((alpha>0)&(alpha<128)).sum()),
         'original_edges_nonzero':[int(np.count_nonzero(z)) for z in (alpha[0],alpha[-1],alpha[:,0],alpha[:,-1])],
         'forge_files':forge.backend_info()['files'],'palette_applied':False,'alpha_threshold':128,
         'roi_note':'头/前臂矩形ROI只作诊断，不是精确人体分割；Alpha重叠不等价于穿体。','whole_frame_only':True,'limb_editing':False,'runtime_installed':False,'accepted':False,'pairs':rows}
(out/'measurement.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

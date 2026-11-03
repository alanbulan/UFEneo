"""杰顿受方限定来源只读页；源/产品不写，不生图。"""
from pathlib import Path
import json,hashlib,math,re
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'reports/review/2026-11-02/gomora-super3-zetton-minimal-receiver-source-v1'
def rec(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def read(p):return json.loads(p.read_text('utf-8-sig'))
def pages(items,stem,cols=4,per=16):
 records=[]
 for start in range(0,len(items),per):
  subset=items[start:start+per];page=Image.new('RGB',(768,30+math.ceil(len(subset)/cols)*216),'#242934');d=ImageDraw.Draw(page)
  d.text((4,7),stem+' / exact whole source or manifest cell / uniform scale in each item',fill='white')
  for i,item in enumerate(subset):
   im=Image.open(ROOT/item['source']['path']).convert('RGBA')
   if item.get('rect'):
    x,y,w,h=item['rect'];im=im.crop((x,y,x+w,y+h))
   ratio=min(192/im.width,192/im.height);small=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.NEAREST)
   x=(i%cols)*192;y=30+(i//cols)*216
   page.paste(small,(x,y+24),small);d.text((x+3,y+6),item['label'],fill='white')
   item['preview_ratio']=ratio
  p=OUT/f'{stem}-{start//per:02d}.jpg';page.save(p,quality=82,optimize=True);assert p.stat().st_size<=150000
  records.append(dict(page=rec(p),items=subset))
 return records
def main():
 assert not OUT.exists();OUT.mkdir()
 prod=ROOT/'art/fighters/zetton/stage6/teo-capture-receiver-codex-20261029/production-v1'
 raw=[dict(source=rec(p),label='/'.join(p.relative_to(prod).parts[:3])) for p in sorted(prod.rglob('raw.png'))]
 mp=ROOT/'assets/fighters/zetton/animations/manifest.json';m=read(mp);items=[]
 keys=['wake','wake_low','wake_mid','roll_forward','roll_back','air_tech','air_rise','air_apex','air_fall','capture_enclosed','capture_shrinking','capture_restore']
 for key in keys:
  c=m['clips'][key];p=ROOT/c['texture'].removeprefix('res://')
  for i,r in enumerate(c['rects']):items.append(dict(source=rec(p),rect=r,label=f'{key}:{i}'))
 old=[]
 gen=ROOT/'art/fighters/zetton/stage2/generation'
 for group,key in [('phase3_defense',k) for k in ['hit_air','launch_rise','launch_fall','bounce','down','wake','wake_low','wake_mid','air_tech','roll_forward','roll_back']]+[('phase3_throws',k) for k in ['grabbed','thrown_forward','thrown_back','thrown_air','thrown_dash']]+[('phase3_specials','defeat')]:
  for p in sorted((gen/group/key).rglob('raw.png')):
   old.append(dict(source=rec(p),label=f'{key}/{p.parent.name}'+('/rej' if 'rejected' in p.parts else '')))
 index=dict(teo_full_originals=pages(raw,'teo-original'),runtime_extra_cells=pages(items,'runtime-extra'),
   historical_reaction_sheets=pages(old,'historical-sheet',cols=2,per=4),runtime_manifest=rec(mp),
   original_sheet_note='历史页只缩整张原图，不截除相位；原meta保留。小页不能代替必要的原格复看。',
   source_changed=False,runtime_changed=False,post_sent=False,godot_run=False)
 (OUT/'source-pages-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(dict(output=str(OUT),teo_originals=len(raw),extra_cells=len(items),old_sheets=len(old)),ensure_ascii=False))
if __name__=='__main__':main()

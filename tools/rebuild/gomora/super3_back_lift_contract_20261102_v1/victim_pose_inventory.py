"""只读现装完整被投格；首核杰顿/赛文，绝不旋转/挪肢体补姿势。"""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'reports/review/2026-11-02/gomora-super3-victim-pose-inventory-v1'
KEYS=['grabbed','thrown_back','thrown_forward']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def read(p):return json.loads(p.read_text('utf-8-sig'))
def main():
 assert not OUT.exists();OUT.mkdir();rows=[]
 for fighter in ['zetton','ultraseven']:
  mp=ROOT/f'assets/fighters/{fighter}/animations/manifest.json';m=read(mp)
  sp=ROOT/f'content/fighters/{fighter}/state_frames.json';states=read(sp);records=[]
  total_rows=sum((len(m['clips'][key]['rects'])+3)//4 for key in KEYS)
  page=Image.new('RGB',(768,total_rows*224),'#242934');d=ImageDraw.Draw(page);row=0
  for key in KEYS:
   clip=m['clips'][key];ap=ROOT/clip['texture'].removeprefix('res://');atlas=Image.open(ap).convert('RGBA')
   for i,rect in enumerate(clip['rects']):
    x,y,w,h=map(int,rect);assert [w,h]==[256,256]
    frame=atlas.crop((x,y,x+w,y+h));col=i%4;top=(row+i//4)*224
    small=frame.resize((192,192),Image.Resampling.NEAREST);page.paste(small,(col*192,top+24),small)
    d.text((col*192+4,top+5),f'{fighter} {key} {i}',fill='white')
    records.append(dict(clip=key,frame=i,source_atlas=rec(ap),source_rect=rect,full_cell=[256,256],
      anchor=clip.get('anchors',[])[i] if clip.get('anchors',[]) else clip.get('anchor',[128,clip.get('anchor_y',248)]),
      image_bbox=frame.getbbox(),state_frames=[dict(tick=j,data=s) for j,s in enumerate(states.get(key,[])) if int(s.get('sprite',0))==i]))
   row+=(len(clip['rects'])+3)//4
  dest=OUT/f'{fighter}-whole-victim-cells.jpg';page.save(dest,quality=80,optimize=True)
  assert page.width<=768 and dest.stat().st_size<=150000
  rows.append(dict(fighter=fighter,manifest=rec(mp),state_frames=rec(sp),whole_cells=rec(dest),records=records,
   transformations='exact manifest full cell -> uniform nearest3/4 report preview; no centering/rotation/local parts',
   actual_visual_review_pending=True))
 queue=[]
 for mp in sorted((ROOT/'assets/fighters').glob('*/animations/manifest.json')):
  if mp.parent.parent.name in ['zetton','ultraseven']:continue
  m=read(mp);present={key:len(m.get('clips',{}).get(key,{}).get('rects',[])) for key in KEYS}
  queue.append(dict(fighter=mp.parent.parent.name,manifest=rec(mp),clip_frame_counts=present,actual_visual_reviewed=False))
 with (OUT/'inventory.json').open('x',encoding='utf8') as f:json.dump(dict(first_two=rows,remaining_actual_manifest_queue=queue,
  queue_scope='assets现有manifest实际文件；不是本轮已目视角色名单，也不据目录推断全部正式可玩。',runtime_changed=False,godot_run=False),f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(dict(report=str(OUT),images=[r['whole_cells']['path'] for r in rows]),ensure_ascii=False))
if __name__=='__main__':main()

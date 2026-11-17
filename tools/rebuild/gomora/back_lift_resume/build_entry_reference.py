"""只从已验证输入回放快照重建R00设计参考；不是主游戏截图。"""
import json
from PIL import Image,ImageDraw,ImageOps
from resume import ROOT,ACTOR_OUT,sha
out=ROOT/'reports/gomora-builtin/main-candidate210/entry-reference';out.mkdir(parents=True,exist_ok=True)
replay=ROOT/'reports/gomora-builtin/main-candidate210/rear-verified-owner0-rear_vertical_hit-replay/replay-result.json';data=json.loads(replay.read_text());assert data['errors']==[] and data['captures']==1
snapshot=data['capture_snapshots'][0];saved=snapshot['memory'];animation=snapshot['actual_animation'];assert saved['state']=='air' and saved['facing']==1 and saved['vx']==0 and saved['vy']==-14
p=ROOT/animation['texture'].removeprefix('res://');source=Image.open(p).convert('RGBA');x,y,w,h=map(int,animation['rect']);victim=source.crop((x,y,x+w,y+h));victim.save(out/'incoming-whole.png')
window=next(r for r in data['windows'] if r['tick']==snapshot['tick']);relative=[int(saved['x'])-int(window['actor_root'][0]),int(saved['height'])]
actor=Image.open(ACTOR_OUT/'04.png').convert('RGBA');canvas=Image.new('RGBA',actor.size);paste=[256+relative[0]-96,304-relative[1]-184];canvas.paste(victim,tuple(paste))
sheet=Image.new('RGB',(1024,690),'#30343c');draw=ImageDraw.Draw(sheet)
for layer in range(2):
 pair=Image.alpha_composite(actor,canvas) if layer==0 else Image.alpha_composite(canvas,actor)
 for facing in range(2):
  im=pair if facing==0 else ImageOps.mirror(pair);sheet.paste(im,(512*facing,345*layer+24),im);draw.text((512*facing+5,345*layer+5),f'Actual input snapshot raw18 / source A04 / layer{layer}',fill='white')
sheet.save(out/'actual-incoming-pair.png')
receipt={'source_replay':str(replay.relative_to(ROOT)),'source_replay_sha256':sha(replay),'snapshot':snapshot,'relative_root':relative,'actor_source':str((ACTOR_OUT/'04.png').relative_to(ROOT)),'actor_sha256':sha(ACTOR_OUT/'04.png'),'receiver_atlas':str(p.relative_to(ROOT)),'receiver_atlas_sha256':sha(p),'crop_is_complete_frame':True,'limb_edits':False,'source_pixels_changed':False,'not_main_screenshot':True,'generated_reference_paths':['incoming-whole.png','actual-incoming-pair.png']};(out/'reference.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(relative,paste)

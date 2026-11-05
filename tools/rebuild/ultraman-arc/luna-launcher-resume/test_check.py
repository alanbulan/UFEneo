"""只读核月亮升击完整源共同尺度、真实拳面及候选关闭边界。"""
from pathlib import Path
import copy,json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'art/fighters/ultraman-arc__luna/stage2/launcher-registered-20261105-v1'
def read(p):return json.loads(p.read_text())
def checkref(r):
 p=ROOT/r['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];return p
m=read(BASE/'manifest.json');plan=read(checkref(m['registration_plan']))
assert not m['installed'] and not m['art_passed'] and not m['playable'] and not m['transform_enabled']
for action,group in m['actions'].items():
 clip=read(checkref(group['clip']));atlas=Image.open(ROOT/clip['texture'].removeprefix('res://'))
 assert hashlib.sha256((ROOT/clip['texture'].removeprefix('res://')).read_bytes()).hexdigest()==clip['atlas_sha256']
 assert clip['anchors']==[[160,280]]*len(group['frames'])
 for row in group['frames']:
  raw=Image.open(checkref({'path':row['source'],'sha256':row['source_sha256']}));assert raw.size==(1254,1254)
  sample=Image.open(checkref(row['whole_source_sample']));assert sample.size==(159,159)
  image=Image.open(checkref({'path':row['image'],'sha256':row['image_sha256']}));assert image.size==(320,320)
  offset=row['whole_source_destination_offset'];assert offset[0]==80
  expected=Image.new('RGBA',(320,320));expected.paste(sample,tuple(offset));assert expected.tobytes()==image.tobytes()
  assert image.getbbox()[3]==280 and {i for i,n in enumerate(image.getchannel('A').histogram()) if n}=={0,255}
  x,y,w,h=clip['rects'][row['phase']];assert atlas.crop((x,y,x+w,y+h)).tobytes()==image.tobytes()
g=m['actions']['launcher'];move=read(checkref(g['move']));expected=read(checkref(g['rule_reference']))
for key in ['startup','active','recovery','display_name','production_source']:expected[key]=move[key]
assert (move['startup'],move['active'],move['recovery'])==(9,5,9)
assert g['fist_boxes']=={'3':[29,131,12,12]}
phases=[r['phase'] for r in g['frames'] for _ in range(r['ticks'])];assert len(phases)==23
for i,phase in enumerate(phases):
 f=move['frames'][i];assert f['sprite']==phase and f['hitboxes']==([[29,131,12,12]] if phase==3 else []) and f['cancel']==[]
 for k in ['sprite','hitboxes','hurtboxes','cancel']:expected['frames'][i][k]=copy.deepcopy(f[k])
assert expected==move
flags=read(ROOT/'content/fighters/ultraman-arc__luna/definition.json')
assert all(flags[k] is False for k in ['implemented','playable','select_visible'])
print('PASS: 13完整相共同尺度/整图平移/atlas像素/SHA/9-5-9与拳面/正式关闭；非美术或运行验收')

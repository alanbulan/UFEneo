"""只读验证两完整候选源、完整采样、真实Alpha受击框与正式内容未覆盖。"""
import copy,json,hashlib
from pathlib import Path
from PIL import Image
from register import ROOT,OUT,hurts

def read(p):return json.loads(p.read_text())
def checked(r):
 p=ROOT/r['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];return p
m=read(OUT/'manifest.json');clip=read(checked(m['clip']));states=read(checked(m['state_frames']));original=read(checked(m['reference_state_frames']))['crouch_blockstun']
assert m['installed'] is False and m['art_passed'] is False
assert clip['ticks']==[4,6] and clip['anchors']==[[160,280]]*2
assert [f['sprite'] for f in states]==[0]*4+[1]*6
atlas=Image.open(ROOT/clip['texture'].removeprefix('res://'))
assert hashlib.sha256((ROOT/clip['texture'].removeprefix('res://')).read_bytes()).hexdigest()==clip['atlas_sha256']
for r in m['frames']:
 assert Image.open(checked(r['source'])).size==(1254,1254)
 sample=Image.open(checked(r['sample']));image=Image.open(checked(r['image']));assert sample.size==(256,256) and image.size==(320,320)
 assert r['whole_source_destination_offset'][0]==32
 expected=Image.new('RGBA',(320,320));expected.paste(sample,tuple(r['whole_source_destination_offset']));assert expected.tobytes()==image.tobytes()
 assert image.getbbox()[3]==280 and {i for i,n in enumerate(image.getchannel('A').histogram()) if n}=={0,255}
 x,y,w,h=clip['rects'][r['phase']];assert atlas.crop((x,y,x+w,y+h)).tobytes()==image.tobytes()
 assert hurts(image)==r['hurtboxes']
for index,f in enumerate(states):
 expected=copy.deepcopy(original[index]);expected['hurtboxes']=m['frames'][f['sprite']]['hurtboxes'];assert f==expected
print('PASS: 两整源共同256/1254、整样本不裁/atlas/SHA、4px真实Alpha框、4/6源表与原事件保持；非图形验收')

"""三端点RAM试排独立复建与规则防篡改；不宣称美术通过。"""
import copy,importlib.util,json,sys
from pathlib import Path
from PIL import Image
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import main_bundle as b

def main():
 m=b.read(b.DEFAULT_MANIFEST);b.processing_resources(m)
 spec=importlib.util.spec_from_file_location('endpoint_geometry',b.checked(m['geometry_tool']));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
 images,result=g.build_frames(b.checked(m['registration_plan']));again,second=g.build_frames(b.checked(m['registration_plan']))
 assert result==second and json.loads(json.dumps(result))==b.read(b.checked(m['geometry']))
 assert len(images)==3 and images[0].tobytes()==images[2].tobytes()
 for action,ticks in b.manifest_clocks(m).items():
  group=m['actions'][action];rows=group['frames'];clip=b.read(b.checked(group['clip']))
  assert clip['ticks']==ticks and clip['anchors']==[[160,280]]*len(ticks)
  with Image.open(b.checked({'path':clip['texture'],'sha256':clip['atlas_sha256']})) as atlas:
   for i,row in enumerate(rows):
    with Image.open(b.checked({'path':row['image'],'sha256':row['image_sha256']})) as im,Image.open(b.checked(row['whole_source_sample'])) as sample:
     expected=images[i] if action=='crouch_light' else images[0]
     assert im.tobytes()==expected.tobytes() and images[i if action=='crouch_light' else 0].tobytes()==again[i if action=='crouch_light' else 0].tobytes()
     reconstructed=Image.new('RGBA',(320,320));reconstructed.paste(sample,tuple(row['whole_source_destination_offset']))
     assert reconstructed.tobytes()==im.tobytes()==atlas.crop((320*i,0,320*(i+1),320)).tobytes()
 group=m['actions']['crouch_light'];move=b.read(b.checked(group['move']));b.validate_move(move,group['fist_boxes'])
 assert [i for i,f in enumerate(move['frames']) if f['hitboxes']]==[3,4,5]
 assert [f['hurtboxes'] for f in move['frames']]==[f['hurtboxes'] for f in b.state_frames(group['frames'])]
 row=group['frames'][1];roi=row['fist_roi_native'];tight=images[1].getchannel('A').crop(roi).getbbox();bbox=[roi[0]+tight[0],roi[1]+tight[1],roi[0]+tight[2],roi[1]+tight[3]]
 assert bbox==row['fist_alpha_bbox_native'] and group['fist_boxes']['1']==[bbox[0]-160,280-bbox[3],bbox[2]-bbox[0],bbox[3]-bbox[1]]
 for key in ['damage','recovery','launch','knockdown','unblockable']:
  bad=copy.deepcopy(move);bad[key]=not bad[key] if isinstance(bad[key],bool) else bad[key]+1
  try:b.validate_move(bad,group['fist_boxes'])
  except AssertionError:pass
  else:raise AssertionError('规则篡改未拒绝 '+key)
 bad=copy.deepcopy(move);bad['frames'][3]['cancel']=[]
 try:b.validate_move(bad,group['fist_boxes'])
 except AssertionError:pass
 else:raise AssertionError('删除第二拳取消目标未拒绝')
 for p in b.REVIEW.glob('*.gd'):
  s=p.read_text();assert '.move_id =' not in s and '.move_id=' not in s
 flags=b.read(b.ROOT/'content/fighters/ultraman-arc__luna/definition.json');assert all(flags[k] is False for k in ['implemented','playable','select_visible'])
 print(json.dumps({'passed':True,'phases':3,'unique_images':2,'ticks':18,'active_ticks':[3,4,5],'fist_box':group['fist_boxes']['1'],'cancel_preserved':True,'second_punch_loaded':False,'art_passed':False,'input':'held down plus one LIGHT'},ensure_ascii=False))
if __name__=='__main__':main()

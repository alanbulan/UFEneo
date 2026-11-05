"""只读检查六相来源、整图注册、真实脚部接触框和未开放边界。"""
import copy
import unittest
import numpy as np
from PIL import Image
import prepare as P
import main_bundle

CONTACT_BOXES = {2: [[66,52,9,12]],3: [[63,61,10,10]]}

class DashHeavyCandidateTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.manifest=P.read(P.OUTPUT/'manifest.json');cls.samples=P.read(P.OUTPUT/'samples.json')
 def test_sources_and_common_scale(self):
  self.assertEqual(len(self.samples['phases']),6)
  self.assertEqual(self.samples['common_source_scale'],159/1254)
  self.assertFalse(self.samples['old_area_fit_samples_used'])
  for row in self.samples['phases']:
   for key in ['source','sample']:
    p=main_bundle.checked(row[key])
    with Image.open(p) as im:self.assertEqual(im.size,(1254,1254) if key=='source' else (159,159))
 def test_whole_frame_preserved(self):
  for row in self.manifest['frames']:
   with Image.open(main_bundle.checked(row['sample'])) as sample,Image.open(main_bundle.checked(row['image'])) as im:
    x,y=row['translation'];self.assertEqual(im.size,(320,320))
    self.assertEqual(im.crop((x,y,x+159,y+159)).tobytes(),sample.tobytes())
    a=np.asarray(im)[:,:,3];b=np.asarray(sample)[:,:,3]
    self.assertEqual(int((a>0).sum()),int((b>0).sum()))
    if row['phase'] in [0,4,5]:self.assertEqual(int(np.where(a>0)[0].max()),280)
    else:
     self.assertEqual(y,127)
     self.assertLess(int(np.where(a>0)[0].max()),280)
    self.assertEqual(x,80)
 def test_palette_and_alpha(self):
  palette={tuple(c) for c in P.read(main_bundle.checked(self.samples['palette']))['colors']}
  for row in self.manifest['frames']:
   a=np.asarray(Image.open(main_bundle.checked(row['image'])))
   self.assertLessEqual(set(np.unique(a[:,:,3])),{0,255})
   self.assertTrue({tuple(c) for c in a[a[:,:,3]>0][:,:3]}.issubset(palette))
   self.assertFalse(a[a[:,:,3]==0][:,:3].any())
 def test_atlas_and_timing(self):
  clip=P.read(main_bundle.checked(self.manifest['clip']))
  atlas=P.OUTPUT/'atlas.png';self.assertEqual(P.sha(atlas),clip['atlas_sha256'])
  with Image.open(atlas) as im:
   self.assertEqual(im.size,(1920,320))
   for row in self.manifest['frames']:
    n=row['phase']
    with Image.open(main_bundle.checked(row['image'])) as frame:self.assertEqual(im.crop((320*n,0,320*(n+1),320)).tobytes(),frame.tobytes())
  self.assertEqual(clip['ticks'],[2,2,3,4,4,7])
  self.assertEqual(clip['anchors'],[[160,280]]*6)
 def test_rules_only_approved_changes(self):
  base=P.read(main_bundle.checked(self.manifest['rule_reference']));actual=P.read(main_bundle.checked(self.manifest['move']))
  expected=copy.deepcopy(base);expected.update(production_source=actual['production_source'])
  for before,after in zip(expected['frames'],actual['frames']):
   before['hurtboxes']=after['hurtboxes'];before['hitboxes']=CONTACT_BOXES.get(int(before['sprite']),[])
  self.assertEqual(actual,expected)
  self.assertEqual(sum(bool(f['hitboxes']) for f in actual['frames']),7)
  self.assertEqual(actual['startup']+actual['active']+actual['recovery'],len(actual['frames']))
 def test_contact_pixels_and_recovery(self):
  self.assertTrue(CONTACT_BOXES,'实体接触框待确认，禁止验收')
  for phase,boxes in CONTACT_BOXES.items():
   im=np.asarray(Image.open(P.OUTPUT/f'frame-{phase:02}.png'))
   for x,y,w,h in boxes:
    mask=im[280-y-h:280-y,160+x:160+x+w,3]>0
    self.assertEqual(mask.shape,(h,w))
    self.assertGreater(float(mask.mean()),0.5)
  move=P.read(P.OUTPUT/'move.json')
  self.assertTrue(all(not f['hitboxes'] for f in move['frames'] if int(f['sprite']) not in [2,3]))
 def test_dash_heavy_and_movement(self):
  commands=P.read(P.ROOT/'content/fighters/ultraman-arc/command_table.json')
  command=[r for r in commands if r['move']=='dash_heavy']
  self.assertEqual(len(command),1)
  self.assertEqual(command[0]['buttons'],2)
  self.assertEqual(command[0]['directions'],[0])
  self.assertEqual(command[0]['states'],['dash'])
  move=P.read(P.OUTPUT/'move.json')
  self.assertEqual(move['damage'],65)
  self.assertEqual(move['pushback'],8)
  self.assertEqual(move['level'],'mid')
  self.assertTrue(move['finish_on_landing'])
  self.assertEqual(move['frames'][2]['velocity'],[0,4])
  self.assertEqual([move[k] for k in ['startup','active','recovery']],[4,7,11])
  self.assertEqual(sum(f['dx'] for f in move['frames']),35)
  for key in ['launch','bounce','knockdown']:self.assertFalse(move[key])
 def test_closed_armor(self):
  flags=P.read(P.ROOT/'content/fighters/ultraman-arc__luna/definition.json')
  for key in ['implemented','playable','select_visible']:self.assertFalse(flags[key])
  self.assertFalse(self.manifest['main_game_accepted'])
 def test_changed_source_rejected(self):
  ref=dict(self.manifest['rule_reference']);ref['sha256']='0'*64
  with self.assertRaises(ValueError):main_bundle.checked(ref)

 def test_dash_dependency_whole_frames(self):
  prior=P.STAGE/'dash-repair-20261102-v1/offline-nine-registered-v1'
  clips=P.read(prior/'candidate-clips.json')
  resources=main_bundle.checked_dash_sources(prior,clips)
  self.assertGreater(len(resources),15)
  states=[]
  for action in main_bundle.DASH_ACTIONS:states.extend(main_bundle.alpha_state_frames(prior/'atlas.png',clips[action]))
  self.assertEqual(len(states),22)
  self.assertEqual(set(f['sprite'] for f in states),set(range(9)))
  self.assertTrue(all(not f['hitboxes'] for f in states))
 def test_dash_source_tamper_rejected(self):
  prior=P.STAGE/'dash-repair-20261102-v1/offline-nine-registered-v1';clips=P.read(prior/'candidate-clips.json')
  clips['dash']['atlas_sha256']='0'*64
  with self.assertRaises(ValueError):main_bundle.checked_dash_sources(prior,clips)

if __name__=='__main__':unittest.main()

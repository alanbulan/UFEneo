"""真实逻辑trace正负例；图形元数据fixtures仅验拒绝逻辑，不是实际画面证据。"""
import copy,unittest
from unittest.mock import patch
import main_bundle as B
class Checks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.base=B.read(B.REPORT/'logic-v2/1280x720-right-original/main-trace.json')
 def reject(self,edit):
  d=copy.deepcopy(self.base);edit(d)
  with self.assertRaises(AssertionError):B.check_trace(d)
 def test_four_actual_traces(self):
  for p in (B.REPORT/'logic-v2').glob('*/main-trace.json'):B.check_trace(B.read(p))
 def test_clock(self):self.reject(lambda d:d['trace'][55]['pair'][0].update(state_tick=14))
 def test_displacement(self):self.reject(lambda d:d['trace'][56]['pair'][0].update(x=283))
 def test_height(self):self.reject(lambda d:d['trace'][41]['pair'][0].update(height=1))
 def test_phase(self):self.reject(lambda d:d['trace'][46]['pair'][0]['animation'].update(index=1))
 def test_sprite(self):self.reject(lambda d:d['trace'][46]['pair'][0].update(frame_sprite=1))
 def test_second_trigger(self):self.reject(lambda d:d['trace'][80]['pair'][0].update(state='idle'))
 def test_input(self):self.reject(lambda d:d['trace'][78].update(original_inputs=[[0,0,0],[0,0,0]]))
 def test_stamina(self):self.reject(lambda d:d['trace'][41]['pair'][0].update(stamina=999))
 def test_health(self):self.reject(lambda d:d['trace'][41]['pair'][1].update(hp=999))
 def test_training_visible(self):self.reject(lambda d:d['trace'][41].update(training_overlay_visible=False))
 def fixture(self):
  d=copy.deepcopy(self.base);d['stills']=[]
  for f in [0,110]+[s+n for s in [40,80] for n in B.CAPTURE_N]:
   row=d['trace'][f];sprite=row['pair'][0]['frame_sprite']
   req=dict(tick=row['tick'],movie_frame=f,sprite=sprite,state_hash=row['state_hash'],pair=copy.deepcopy(row['pair']),final_safe_rect=[16,70,608,250],hud_safe_rect=[16,70,608,250],hud_visible=True,training_overlay_visible=True,final_render_bounds=[[20,100,60,180],[500,100,60,180]])
   d['stills'].append(dict(movie_frame=f,dimensions=[1280,720],window_dimensions=[1280,720],resized=False,path='fixture',sha256='fixture',request=req,captured_tick=row['tick'],captured_sprite=sprite))
  return d
 def graphic(self,edit=None):
  d=self.fixture()
  if edit:edit(d['stills'][0]['request'])
  with patch.object(B,'sha',return_value='fixture'):
   if edit:
    with self.assertRaises(AssertionError):B.check_trace(d,True,[1280,720])
   else:B.check_trace(d,True,[1280,720])
 def test_graphic_fixture_only(self):self.graphic()
 def test_hud(self):self.graphic(lambda r:r.update(hud_visible=False))
 def test_safe(self):self.graphic(lambda r:r.update(final_safe_rect=[0,0,640,360]))
 def test_overlap(self):self.graphic(lambda r:r.update(final_render_bounds=[[20,100,60,230],[500,100,60,180]]))
 def test_missing_second(self):self.graphic(lambda r:r.update(pair=r['pair'][:1]))
 def test_second_phase(self):self.graphic(lambda r:r['pair'][1].update(frame_sprite=99))
 def test_second_region(self):self.graphic(lambda r:r['pair'][1]['animation'].update(rect=[0,0,1,1]))
 def test_second_state(self):self.graphic(lambda r:r['pair'][1].update(state='air'))
if __name__=='__main__':unittest.main()

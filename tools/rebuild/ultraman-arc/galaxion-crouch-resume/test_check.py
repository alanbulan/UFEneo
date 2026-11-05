"""合成正负例仅验证检查器，不冒充实际主游戏证据；可指定真实trace目录。"""
import copy, os, unittest
from pathlib import Path
from unittest.mock import patch
import main_bundle as B

def fixture():
    trace=[]
    for i in range(B.LENGTH):
        state='idle';age=i
        for start in B.STARTS:
            if start<=i<start+60:
                n=i-start;state='crouch_start' if n<6 else 'crouch' if n<54 else 'crouch_rise'
                age=n if n<6 else n-6 if n<54 else n-54
                break
            if i>=start+60:age=i-start-60
        phases=[p for p,t in enumerate(B.CLOCKS[state]) for _ in range(t)];phase=phases[age%len(phases)]
        own=dict(state=state,state_tick=age,x=360,height=0,hp=1000,stamina=1000,frame_sprite=phase,animation=dict(key=state,index=phase,rect=[phase*320,0,320,320]),full_alpha_viewport_bounds=[20,100,60,180])
        other=copy.deepcopy(own);other.update(x=900,state='idle',state_tick=i,frame_sprite=0,animation=dict(key='idle',index=0,rect=[0,0,320,320]))
        trace.append(dict(movie_frame=i,tick=i+1,state_hash=str(i),original_inputs=[[0,-1 if 24<=i<78 or 102<=i<156 else 0,0],[0,0,0]],pair=[own,other],events=[],projectiles=[],training_overlay_visible=True))
    return dict(direction=1,failures=[],trace=trace,stills=[])

class Checks(unittest.TestCase):
    def setUp(self):self.base=fixture()
    def reject(self,edit):
        d=copy.deepcopy(self.base);edit(d)
        with self.assertRaises(AssertionError):B.check_trace(d)
    def test_synthetic_positive_not_runtime_evidence(self):B.check_trace(self.base)
    def test_actual_traces_if_requested(self):
        folder=os.environ.get('GALAXION_TRACE_DIR')
        if not folder:self.skipTest('未指定真实运行结果，不宣称主游戏通过')
        files=list(Path(folder).glob('*/main-trace.json'));self.assertGreaterEqual(len(files),4)
        for p in files:B.check_trace(B.read(p))
    def test_clock(self):self.reject(lambda d:d['trace'][26]['pair'][0].update(state_tick=1))
    def test_displacement(self):self.reject(lambda d:d['trace'][30]['pair'][0].update(x=361))
    def test_loop(self):self.reject(lambda d:d['trace'][54]['pair'][0].update(frame_sprite=1))
    def test_idle_six_phases(self):self.reject(lambda d:d['trace'][212]['pair'][0].update(frame_sprite=0))
    def test_rise(self):self.reject(lambda d:d['trace'][78]['pair'][0].update(state='idle'))
    def test_release(self):self.reject(lambda d:d['trace'][78].update(original_inputs=[[0,-1,0],[0,0,0]]))
    def test_second_trigger(self):self.reject(lambda d:d['trace'][102]['pair'][0].update(state='idle'))
    def test_health(self):self.reject(lambda d:d['trace'][42]['pair'][1].update(hp=999))
    def test_stamina(self):self.reject(lambda d:d['trace'][42]['pair'][0].update(stamina=999))
    def test_attack(self):self.reject(lambda d:d['trace'][42].update(events=[{'kind':'hit'}]))
    def graphic(self,edit=None):
        d=copy.deepcopy(self.base)
        for f in B.CAPTURE_FRAMES:
            row=d['trace'][f];sprite=row['pair'][0]['frame_sprite']
            req=dict(tick=row['tick'],movie_frame=f,sprite=sprite,state_hash=row['state_hash'],pair=copy.deepcopy(row['pair']),final_safe_rect=[16,70,608,250],hud_safe_rect=[16,70,608,250],hud_visible=True,training_overlay_visible=True,final_render_bounds=[[20,100,60,180],[500,100,60,180]])
            d['stills'].append(dict(movie_frame=f,dimensions=[1280,720],window_dimensions=[1280,720],resized=False,path='fixture',sha256='fixture',request=req,captured_tick=row['tick'],captured_sprite=sprite))
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
    def test_unknown_warning(self):self.assertFalse(B.classify_diagnostics({'test':'WARNING: unknown'})['passed'])
    def test_exact_vsync(self):self.assertTrue(B.classify_diagnostics({'test':B.KNOWN_VSYNC_WARNING})['passed'])
if __name__=='__main__':unittest.main()

"""合成正负例只验门禁；未运行Godot不构成主游戏通过。"""
import copy,os,unittest
from pathlib import Path
from unittest.mock import patch
import main_bundle as B

def fixture(kind='hit'):
    trace=[]
    phases=[p for p,t in enumerate(B.CLOCKS['light1']) for _ in range(t)]
    for i in range(B.LENGTH):
        active=20<=i<39;age=i if i<20 else i-39 if i>=39 else 0
        tick=i-19 if active else 0;phase=phases[tick] if active else (age%60)//10
        key='light1' if active else 'idle'
        own=dict(state='attack' if active else 'idle',state_tick=age,move_id='light1' if active else '',move_tick=tick,x=590,height=0,hp=1000,stamina=970 if i>=20 else 1000,frame_sprite=phase,animation=dict(key=key,index=phase,rect=[phase*320,0,320,320]),full_alpha_viewport_bounds=[20,100,60,180])
        other=copy.deepcopy(own);other.update(x=660,hp=935 if kind=='hit' and i>=22 else 1000,state='idle',move_id='',state_tick=i,frame_sprite=0,animation=dict(key='idle',index=0,rect=[0,0,320,320]))
        events=[{'kind':kind,'player':0,'move':'light1'}] if i==22 and kind!='whiff' else []
        trace.append(dict(movie_frame=i,tick=i+1,state_hash=str(i),original_inputs=[[0,0,1 if i==20 else 0],[0,0,8 if kind=='block' else 0]],pair=[own,other],events=events,projectiles=[],training_overlay_visible=True))
    return dict(direction=1,kind=kind,failures=[],trace=trace,stills=[])

class Checks(unittest.TestCase):
    def setUp(self):self.base=fixture()
    def reject(self,edit):
        d=copy.deepcopy(self.base);edit(d)
        with self.assertRaises(AssertionError):B.check_trace(d)
    def test_synthetic_cases_not_runtime_evidence(self):
        for kind in ['hit','block','whiff']:B.check_trace(fixture(kind))
    def test_actual_traces_if_requested(self):
        folder=os.environ.get('GALAXION_LIGHT1_TRACE_DIR')
        if not folder:self.skipTest('未指定实际主游戏trace，不宣称运行通过')
        files=list(Path(folder).glob('*/main-trace.json'));self.assertGreaterEqual(len(files),12)
        for p in files:B.check_trace(B.read(p))
    def test_clock(self):self.reject(lambda d:d['trace'][26]['pair'][0].update(move_tick=1))
    def test_displacement(self):self.reject(lambda d:d['trace'][30]['pair'][0].update(x=591))
    def test_phase(self):self.reject(lambda d:d['trace'][27]['pair'][0].update(frame_sprite=0))
    def test_wrong_input(self):self.reject(lambda d:d['trace'][20].update(original_inputs=[[0,0,2],[0,0,0]]))
    def test_second_trigger(self):self.reject(lambda d:d['trace'][70].update(original_inputs=[[0,0,1],[0,0,0]]))
    def test_wrong_damage(self):self.reject(lambda d:d['trace'][-1]['pair'][1].update(hp=900))
    def test_no_combo(self):self.reject(lambda d:d['trace'][30]['pair'][0].update(move_id='light2'))
    def test_multiple_contacts(self):self.reject(lambda d:d['trace'][24].update(events=[{'kind':'hit','player':0,'move':'light1'}]))
    def test_projectile(self):self.reject(lambda d:d['trace'][24].update(projectiles=[{}]))
    def graphic(self,edit=None):
        d=copy.deepcopy(self.base)
        captures=[('before-input-idle',0),('returned-idle',39)]+[(f'light1-tick-{t:02d}-phase-{d["trace"][19+t]["pair"][0]["frame_sprite"]:02d}',19+t) for t in B.MOVE_TICKS]
        for key,f in captures:
            row=d['trace'][f];sprite=row['pair'][0]['frame_sprite']
            req=dict(tick=row['tick'],movie_frame=f,sprite=sprite,state_hash=row['state_hash'],pair=copy.deepcopy(row['pair']),final_safe_rect=[16,70,608,250],hud_safe_rect=[16,70,608,250],hud_visible=True,training_overlay_visible=True,final_render_bounds=[[20,100,60,180],[500,100,60,180]])
            d['stills'].append(dict(key=key,movie_frame=f,dimensions=[1280,720],window_dimensions=[1280,720],resized=False,path='fixture',sha256='fixture',request=req,captured_tick=row['tick'],captured_sprite=sprite))
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
    def test_rules(self):
        manifest=B.DEFAULT_MANIFEST
        if not manifest.exists():self.skipTest('尚待本人配准素材')
        m=B.read(manifest);group=m['actions']['light1'];move=B.read(B.checked(group['move']));B.validate_move(move,group['fist_boxes'])
        for key,value in [('damage',99),('stamina_cost',0),('recovery',0)]:
            changed=copy.deepcopy(move);changed[key]=value
            with self.assertRaises(AssertionError):B.validate_move(changed,group['fist_boxes'])
if __name__=='__main__':unittest.main()

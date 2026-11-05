"""合成正负例只验门禁；未运行Godot不构成主游戏通过。"""
import copy,os,re,unittest
from pathlib import Path
from unittest.mock import patch
import main_bundle as B

def fixture(kind='hit'):
    trace=[]
    phases=[p for p,t in enumerate(B.CLOCKS['launcher']) for _ in range(t)]
    for i in range(B.LENGTH):
        active=20<=i<42;age=i if i<20 else i-42 if i>=42 else 0
        tick=i-19 if active else 0;phase=phases[tick] if active else (age%60)//10
        key='launcher' if active else 'idle'
        own=dict(state='attack' if active else 'idle',state_tick=age,move_id='launcher' if active else '',move_tick=tick,x=590,height=0,vy=0,hp=1000,stamina=970 if i>=20 else 1000,frame_sprite=phase,animation=dict(key=key,index=phase,rect=[phase*320,0,320,320]),full_alpha_viewport_bounds=[20,100,60,180])
        other=copy.deepcopy(own);other.update(x=660,hp=925 if kind=='hit' and i>=25 else 1000,state='idle',move_id='',state_tick=i,frame_sprite=0,animation=dict(key='idle',index=0,rect=[0,0,320,320]))
        if kind=='hit':
            if 25<=i<29:other.update(state='launch',height=0,vy=18)
            elif 29<=i<65:
                t=i-28;other.update(state='launch',height=max(0,18*t-t*(t-1)//2),vy=18-t)
            elif 65<=i<100:other.update(state='down',height=0,vy=0)
            elif 100<=i<120:other.update(state='wake',height=0,vy=0)
        events=[{'kind':kind,'player':0,'move':'launcher'}] if i==25 and kind!='whiff' else []
        trace.append(dict(movie_frame=i,tick=i+1,state_hash=str(i),original_inputs=[[1 if i==20 else 0,0,2 if i==20 else 0],[0,0,8 if kind=='block' else 0]],pair=[own,other],events=events,projectiles=[],training_overlay_visible=True))
    return dict(direction=1,kind=kind,failures=[],trace=trace,stills=[])

class Checks(unittest.TestCase):
    def setUp(self):self.base=fixture()
    def reject(self,edit):
        d=copy.deepcopy(self.base);edit(d)
        with self.assertRaises(AssertionError):B.check_trace(d)
    def test_synthetic_cases_not_runtime_evidence(self):
        for kind in ['hit','block','whiff']:B.check_trace(fixture(kind))
    def test_actual_traces_if_requested(self):
        folder=os.environ.get('GALAXION_LAUNCHER_TRACE_DIR')
        if not folder:self.skipTest('未指定实际主游戏trace，不宣称运行通过')
        files=list(Path(folder).glob('*/main-trace.json'));self.assertGreaterEqual(len(files),12)
        for p in files:B.check_trace(B.read(p))
    def test_clock(self):self.reject(lambda d:d['trace'][26]['pair'][0].update(move_tick=1))
    def test_displacement(self):self.reject(lambda d:d['trace'][30]['pair'][0].update(x=591))
    def test_phase(self):self.reject(lambda d:d['trace'][27]['pair'][0].update(frame_sprite=0))
    def test_wrong_input(self):self.reject(lambda d:d['trace'][20].update(original_inputs=[[0,0,1],[0,0,0]]))
    def test_second_trigger(self):self.reject(lambda d:d['trace'][70].update(original_inputs=[[0,0,1],[0,0,0]]))
    def test_wrong_damage(self):self.reject(lambda d:d['trace'][-1]['pair'][1].update(hp=900))
    def test_no_combo(self):self.reject(lambda d:d['trace'][30]['pair'][0].update(move_id='light2'))
    def test_multiple_contacts(self):self.reject(lambda d:d['trace'][24].update(events=[{'kind':'hit','player':0,'move':'launcher'}]))
    def test_missing_launch(self):self.reject(lambda d:[r['pair'][1].update(state='idle',height=0,vy=0) for r in d['trace']])
    def test_missing_recovery(self):self.reject(lambda d:[r['pair'][1].update(state='down') for r in d['trace'][120:]])
    def test_apex(self):self.reject(lambda d:[r['pair'][1].update(vy=5) for r in d['trace']])
    def test_projectile(self):self.reject(lambda d:d['trace'][24].update(projectiles=[{}]))
    def graphic(self,edit=None):
        d=copy.deepcopy(self.base)
        captures=[('before-input-idle',0),('returned-idle',42)]+[(f'launcher-tick-{t:02d}-phase-{d["trace"][19+t]["pair"][0]["frame_sprite"]:02d}',19+t) for t in B.MOVE_TICKS]
        captures+=list(B.launch_milestones(d['trace'],'hit').items())
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
    def test_candidate_rules_without_materials(self):
        move=copy.deepcopy(B.read(B.ROOT/'content/fighters/ultraman-arc/moves/launcher.json'))
        move.update(active=5,recovery=12,display_name='升拳候选')
        fists={'2':[30,120,10,12]}
        phases=[p for p,t in enumerate(B.CLOCKS['launcher']) for _ in range(t)]
        for frame,phase in zip(move['frames'],phases):
            frame.update(sprite=phase,cancel=[],hitboxes=[fists['2']] if phase==2 else [])
        B.validate_move(move,fists)
        for key,value in [('active',8),('recovery',9),('damage',99),('stamina_cost',0),('level','high'),('launch',False)]:
            changed=copy.deepcopy(move);changed[key]=value
            with self.assertRaises(AssertionError):B.validate_move(changed,fists)
        changed=copy.deepcopy(move);changed['frames'][11]['hitboxes']=[fists['2']]
        with self.assertRaises(AssertionError):B.validate_move(changed,fists)
    def window_gate_expression(self):
        source=(B.REVIEW/'main_entry.gd').read_text()
        sample=source.split('await process_frame',1)[1].split('record["stable_frames"]',1)[0]
        self.assertEqual(sample.count('Time.get_ticks_msec()'),1)
        self.assertIn('var elapsed_ms:=Time.get_ticks_msec()-start',sample)
        self.assertIn('"elapsed_ms":elapsed_ms',sample)
        expression=re.search(r'if (stable>=8 and elapsed_ms>=500):',sample)
        self.assertIsNotNone(expression)
        return expression.group(1)
    def test_window_gate_single_clock_sample(self):self.window_gate_expression()
    def test_window_gate_rejects_499ms(self):
        expression=self.window_gate_expression()
        for stable in [8,1000]:self.assertFalse(eval(expression,{'__builtins__':{}},{'stable':stable,'elapsed_ms':499}))
    def test_window_gate_accepts_500ms_only_when_stable(self):
        expression=self.window_gate_expression()
        for stable,elapsed_ms,expected in [(7,500,False),(7,501,False),(8,500,True),(8,501,True)]:
            self.assertEqual(eval(expression,{'__builtins__':{}},{'stable':stable,'elapsed_ms':elapsed_ms}),expected)
    def test_rules(self):
        manifest=B.DEFAULT_MANIFEST
        if not manifest.exists():self.skipTest('尚待本人配准素材')
        m=B.read(manifest);group=m['actions']['launcher'];move=B.read(B.checked(group['move']));B.validate_move(move,group['fist_boxes'])
        for key,value in [('damage',99),('stamina_cost',0),('recovery',0)]:
            changed=copy.deepcopy(move);changed[key]=value
            with self.assertRaises(AssertionError):B.validate_move(changed,group['fist_boxes'])
if __name__=='__main__':unittest.main()

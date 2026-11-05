"""对实际主游戏trace做负例注入；不把模拟或截图元数据的成功自证为美术通过。"""
import copy
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import main_bundle as B

class VerticalTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(os.environ.get('LUNA_VERTICAL_TRACE',str(B.REPORT/'headless-v4/1280x720-right-original/main-trace.json')))
        cls.base=B.read(path)
        B.check_trace(cls.base)
    def rejects(self, edit):
        data=copy.deepcopy(self.base);edit(data)
        with self.assertRaises(AssertionError):B.check_trace(data)
    def test_actual_success(self):B.check_trace(self.base)
    def test_bad_height(self):self.rejects(lambda d:d['trace'][56]['pair'][0].update(height=137))
    def test_bad_sprite(self):self.rejects(lambda d:d['trace'][56]['pair'][0].update(frame_sprite=4))
    def test_bad_display_phase(self):self.rejects(lambda d:d['trace'][56]['pair'][0]['animation'].update(index=4))
    def test_training_panel_visible(self):self.rejects(lambda d:d['trace'][56].update(training_overlay_visible=True))
    def test_missing_tick(self):self.rejects(lambda d:d['trace'].pop(56))
    def test_wrong_tick(self):self.rejects(lambda d:d['trace'][56].update(tick=58))
    def test_missing_phase(self):
        def edit(d):
            for row in d['trace'][55:58]:row['pair'][0]['animation']['index']=1
        self.rejects(edit)
    def test_pure_jump_cannot_damage(self):self.rejects(lambda d:d['trace'][56]['pair'][1].update(hp=999))
    def test_pure_jump_cannot_spend_stamina(self):self.rejects(lambda d:d['trace'][56]['pair'][0].update(stamina=999))
    def test_no_attack_event(self):self.rejects(lambda d:d['trace'][56].update(events=[{'kind':'hit'}]))
    def test_no_projectile(self):self.rejects(lambda d:d['trace'][56].update(projectiles=[{'id':1}]))
    def graphical(self):
        d=copy.deepcopy(self.base);d['stills']=[]
        for frame in [0,100]+[40+n for n in B.CAPTURE_N]:
            row=d['trace'][frame];sprite=row['pair'][0]['frame_sprite']
            d['stills'].append({'movie_frame':frame,'dimensions':[1280,720],'window_dimensions':[1280,720],'resized':False,'path':'parser-fixture-only','sha256':'fixture',
                'request':{'tick':row['tick'],'movie_frame':frame,'sprite':sprite,'state_hash':row['state_hash']},'captured_tick':row['tick'],'captured_sprite':sprite})
        return d
    def test_graphical_parser_success(self):
        with patch.object(B,'sha',return_value='fixture'):B.check_trace(self.graphical(),True,[1280,720])
    def test_wrong_capture_dimensions(self):
        d=self.graphical();d['stills'][0]['dimensions']=[1920,1080]
        with patch.object(B,'sha',return_value='fixture'),self.assertRaises(AssertionError):B.check_trace(d,True,[1280,720])
    def test_capture_advanced_tick(self):
        d=self.graphical();d['stills'][0]['captured_tick']+=1
        with patch.object(B,'sha',return_value='fixture'),self.assertRaises(AssertionError):B.check_trace(d,True,[1280,720])
    def test_capture_wrong_hash(self):
        d=self.graphical();d['stills'][0]['request']['state_hash']='wrong'
        with patch.object(B,'sha',return_value='fixture'),self.assertRaises(AssertionError):B.check_trace(d,True,[1280,720])
    def test_missing_boundary_capture(self):
        d=self.graphical();d['stills'].pop()
        with patch.object(B,'sha',return_value='fixture'),self.assertRaises(AssertionError):B.check_trace(d,True,[1280,720])

if __name__=='__main__':unittest.main()

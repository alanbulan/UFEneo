"""数据门反例：漂移、漏字段、越界帧、超额容差及事件路径不能静默通过。"""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('emission_check', ROOT/'tools/rebuild/shared/emission_check.py')
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class EmissionCheckTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.folder = self.root/'content/fighters/probe'
        (self.folder/'moves').mkdir(parents=True)
        self.move = {'projectile': {'spawn': [17, 132]}, 'frames': [
            {'beam_origin': [17, 132], 'shots': [{'spawn': [17,132], 'anchor': [17,132]}],
             'attachments': [{'anchor':[17,132]}], 'events':[{'anchor':[17,132]}]}]}
        (self.folder/'moves/pulse.json').write_text(json.dumps(self.move))
        self.table = {'schema':1, 'character':'probe', 'moves': {'pulse': {
            'part':'额头中央光灯', 'evidence':'游戏编排校准', 'source':'game_design', 'frames':[
                {'frame':0, 'point':[17,132], 'field':f, 'tolerance':2}
                for f in ['beam_origin','projectile.spawn','shots[0].spawn','shots[0].anchor','attachments[0].anchor','events[0]']]}}}
        self.path = self.folder/'emission_points.json'

    def tearDown(self):
        self.temp.cleanup()

    def result(self, table=None):
        self.path.write_text(json.dumps(self.table if table is None else table))
        return check.audit(self.root, ['probe'])

    def test_real_paths_and_boundary(self):
        self.assertTrue(self.result()['passed'])
        self.table['moves']['pulse']['frames'][0]['point']=[19,132]
        self.assertTrue(self.result()['passed'])
        self.table['moves']['pulse']['frames'][0]['point']=[19,133]
        self.assertFalse(self.result()['passed'])

    def test_drift_and_invalid_marks(self):
        for patch in [{'point':[20,132]}, {'field':'shots[9].spawn'}, {'frame':1},
                      {'frame':-1}, {'tolerance':3}, {'point':[float('nan'),0]}, {'field':'events[0].missing'}]:
            with self.subTest(patch=patch):
                table=copy.deepcopy(self.table)
                table['moves']['pulse']['frames'][0].update(patch)
                self.assertFalse(self.result(table)['passed'])

    def test_missing_character_is_error(self):
        self.assertFalse(check.audit(self.root,['missing'])['passed'])

    def test_asymmetric_flash_core_is_measured_in_body_coordinates(self):
        catalog=self.root/'content/presentation'
        catalog.mkdir(parents=True)
        (catalog/'phase3_projectiles.json').write_text(json.dumps({'flash':{'anchor':[36,36],'rects':[[0,0,72,72]],'display_scale':[1,1]}}))
        self.move['frames'][0]['attachments'][0].update({'effect':'flash','sprite':0,'anchor':[42,133]})
        (self.folder/'moves/pulse.json').write_text(json.dumps(self.move))
        mark=self.table['moves']['pulse']['frames'][4]
        mark['atlas_point']=[11,37]
        self.assertTrue(self.result()['passed'])
        self.move['frames'][0]['attachments'][0]['anchor'][0]+=3
        (self.folder/'moves/pulse.json').write_text(json.dumps(self.move))
        self.assertFalse(self.result()['passed'])


if __name__ == '__main__':
    unittest.main()

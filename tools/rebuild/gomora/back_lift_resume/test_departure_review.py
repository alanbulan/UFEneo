"""免费离线离背候选回归，不代表主游戏或美术验收。"""
import unittest
import numpy as np
from departure_review import build

class DepartureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.receipt,cls.frames=build()
    def test_integer_and_tick_continuity(self):
        self.assertEqual([r['tick'] for r in self.frames],list(range(28,48)))
        self.assertTrue(all(type(v) is int for r in self.frames for v in r['receiver_root']))
        for i in range(4,len(self.frames)):
            previous,current=self.frames[i-1],self.frames[i]
            self.assertEqual([current['receiver_pelvis'][j]-previous['receiver_pelvis'][j] for j in (0,1)], [6,15-(current['tick']-32)])
    def test_late_frames_clear_both_facings(self):
        for row in self.frames:
            a=np.asarray(row['actor'])[...,3]>0;b=np.asarray(row['receiver'])[...,3]>0
            self.assertEqual(int((a&b).sum()),int((a[:,::-1]&b[:,::-1]).sum()))
            if row['receiver_phase']>=4:self.assertEqual(row['alpha_overlap_pixels'],0)
    def test_early_failure_not_hidden(self):
        self.assertGreater(self.frames[4]['alpha_overlap_pixels'],0)
        self.assertFalse(self.receipt['runtime_installed'])
    def test_repeat_is_deterministic(self):
        _,second=build()
        keys=('tick','actor_phase','receiver_phase','receiver_root','receiver_pelvis','alpha_overlap_pixels')
        self.assertEqual([{k:r[k] for k in keys} for r in self.frames],[{k:r[k] for k in keys} for r in second])

if __name__=='__main__':unittest.main()

"""保全前三v1，加入根已接11整源；全部共同1/4，不按bbox/面积拟合。"""
from pathlib import Path
import copy
import three_key_prototype as shared
def main():
 specs=copy.deepcopy(shared.SPECS)
 specs[11]=dict(root=[724,932],
  feet=[dict(name='near_light_LEFT_rear',x=[470,695],sole_y=932),dict(name='far_dark_RIGHT_front',x=[780,982],sole_y=924)],
  points=dict(near_hip_proxy=[616,642],near_knee_proxy=[632,744],near_ankle_proxy=[528,881],near_shoulder_proxy=[673,374],
   eye=[844,246],nasal_tip=[931,220],chin_proxy=[849,322],back_rear=[528,395],back_front=[642,231]))
 shared.main(out_override=shared.ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-four-key-prototype-v2',specs_override=specs)
if __name__=='__main__':main()

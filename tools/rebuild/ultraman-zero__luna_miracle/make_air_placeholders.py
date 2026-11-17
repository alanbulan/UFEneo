import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
cells = ROOT / "art/fighters/ultraman-zero__luna_miracle/stage1/cells"

m = {
    "takeoff-00-cell.png": "jump-00-cell.png",
    "takeoff-01-cell.png": "jump-01-cell.png",
    "vertical_jump-00-cell.png": "jump-00-cell.png",
    "vertical_jump-01-cell.png": "jump-01-cell.png",
    "vertical_jump-02-cell.png": "jump-02-cell.png",
    "vertical_jump-03-cell.png": "jump-03-cell.png",
    "air_rise-00-cell.png": "jump-01-cell.png",
    "air_apex-00-cell.png": "jump-02-cell.png",
    "air_fall-00-cell.png": "jump-03-cell.png",
    "land-00-cell.png": "jump-00-cell.png",
    "land-01-cell.png": "jump-00-cell.png",
    "chase_takeoff-00-cell.png": "jump-00-cell.png",
    "chase_takeoff-01-cell.png": "jump-01-cell.png",
    "chase_takeoff-02-cell.png": "jump-02-cell.png",
    "flip_forward-00-cell.png": "jump-01-cell.png",
    "flip_forward-01-cell.png": "jump-02-cell.png",
    "flip_forward-02-cell.png": "jump-03-cell.png",
    "flip_forward-03-cell.png": "jump-01-cell.png",
    "flip_back-00-cell.png": "jump-03-cell.png",
    "flip_back-01-cell.png": "jump-02-cell.png",
    "flip_back-02-cell.png": "jump-01-cell.png",
    "flip_back-03-cell.png": "jump-00-cell.png",
    "air_recover-00-cell.png": "jump-03-cell.png",
    "air_recover-01-cell.png": "jump-02-cell.png",
    "air_recover-02-cell.png": "jump-01-cell.png",
    "air_recover-03-cell.png": "jump-00-cell.png",
    "air_tech-00-cell.png": "jump-02-cell.png",
    "air_tech-01-cell.png": "jump-01-cell.png",
    "air_tech-02-cell.png": "jump-02-cell.png",
    "air_tech-03-cell.png": "jump-01-cell.png",
}

for dst, src in m.items():
    shutil.copy2(cells / src, cells / dst)
print("copied", len(m))

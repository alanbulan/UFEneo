# 临时落格包装：色板强制取身份锚 32 色，输出到临时目录，不写正式 cells.json。
import sys
from pathlib import Path

ROOT = Path('/Users/wurulan/Developer/Projects/Game/ultraman-neo')
sys.path.insert(0, str(ROOT / 'tools/art'))
sys.path.insert(0, str(ROOT / 'tools/media/art'))
import stage_cells as sc

ANCHOR = ROOT / 'art/fighters/ultraman-gaia/stage1/idle/frames/identity-idle-pixel.png'
sc.approved_path = lambda fighter: ANCHOR
raise SystemExit(sc.main(sys.argv[1:]))

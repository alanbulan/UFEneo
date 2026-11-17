"""全18计划前只读新增八相完整源/足部坐标窗；不注册。"""
from pathlib import Path
import json
import hashlib
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[4]
ART = ROOT / 'art/fighters/gomora/stage4/super3-back-lift-20261102-v1'
OUT = ROOT / 'reports/review/2026-11-02/gomora-super3-back-lift-full18-readpoint-plan-candidate-v1'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p): return dict(path=p.relative_to(ROOT).as_posix(), sha256=sha(p))

def main():
    assert not OUT.exists()
    OUT.mkdir()
    rows = []
    for phase in [0,1,2,3,14,15,16,17]:
        gate_path = ART / f'phase-{phase:02d}/request-001/root-actual-source-review-v1.json'
        gate = json.loads(gate_path.read_text('utf-8-sig'))
        assert gate['accepted_for_whole_action_processing'] is True
        source = ROOT / gate['source']['path']
        assert sha(source) == gate['source']['sha256']
        im = Image.open(source).convert('RGBA')
        assert im.size == (1024,1024)
        bg = Image.new('RGBA',im.size,'#242934'); bg.alpha_composite(im)
        draw=ImageDraw.Draw(bg)
        for n in range(0,1024,64):
            color='#626773' if n%128 == 0 else '#3e4552'
            draw.line((n,0,n,1023),fill=color)
            draw.line((0,n,1023,n),fill=color)
            if n%128 == 0:
                draw.text((n+3,3),str(n),fill='white')
                draw.text((3,n+3),str(n),fill='white')
        page=Image.new('RGB',(768,768),'#242934')
        page.paste(bg.convert('RGB').resize((720,720),Image.Resampling.LANCZOS),(24,32))
        ImageDraw.Draw(page).text((6,7),f'{phase:02d} FULL ROOT-ACCEPTED SOURCE / source-coordinate grid / NOT REGISTERED',fill='white')
        full=OUT/f'phase-{phase:02d}-full-source-grid.jpg'; page.save(full,quality=80,optimize=True)
        foot=Image.new('RGB',(768,542),'#242934')
        # Exact 1:1 source window x256..1024, y512..1024; read-only diagnostic crop.
        foot.paste(bg.convert('RGB').crop((256,512,1024,1024)),(0,30))
        ImageDraw.Draw(foot).text((4,7),f'{phase:02d} FOOT WINDOW SOURCE x256..1024 y512..1024 / 1:1 / NOT ART',fill='white')
        fp=OUT/f'phase-{phase:02d}-foot-window-native.jpg';foot.save(fp,quality=85,optimize=True)
        assert full.stat().st_size<=150000 and fp.stat().st_size<=150000
        rows.append(dict(phase=phase,source=rec(source),root_acceptance=rec(gate_path),full_grid=rec(full),foot_window=rec(fp)))
    with (OUT/'new8-read-window-index.json').open('x',encoding='utf8') as f:
        json.dump(dict(records=rows,registration_executed=False,runtime_changed=False),f,ensure_ascii=False,indent=2);f.write('\n')
    print(OUT)
if __name__ == '__main__':main()

"""核第三版正常/诊断截图原生尺寸、逐tick身份及图集配准；美术意见另写回执。"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageChops
ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'reports/gomora-builtin/main-midlate-v3-20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    out=BASE/'graphics-technical-audit.json';assert not out.exists()
    cases=[]
    for name in ['owner0-720','owner1-720','owner0-1080','owner1-1080']:
        owner=int(name[5]);size=[1920,1080] if name.endswith('1080') else [1280,720]
        normal=read(BASE/'gui'/name/'main-trace.json')
        for mode in ['gui','diagnostic']:
            folder=BASE/mode/name;tp=folder/'main-trace.json';t=read(tp);run=read(folder/'run-result.json')
            assert run['exit']==0 and not run['diagnostics'] and run['sources_unchanged']
            assert t['owner']==owner and t['case']=='rear_vertical_hit' and len(t['trace'])==760 and not t['failures']
            assert len(t['stills'])==(42 if mode=='gui' else 51)
            rows={r['movie_frame']:r for r in t['trace']};pics=[]
            for s in t['stills']:
                p=Path(s['path']);assert sha(p)==s['sha256'] and list(Image.open(p).size)==s['dimensions']==size
                assert not s['resized'] and s['requested_frame']==s['actual_frame']
                row=rows[s['actual_frame']]
                assert s['actual']['state_hash']==row['state_hash'] and s['actual']['tick']==row['tick']
                for i in [0,1]:
                    for k,v in s['actual']['pair'][i].items():assert row['pair'][i].get(k)==v,(name,mode,s['key'],i,k)
                pics.append({k:s[k] for k in ['key','path','sha256','dimensions','actual_frame']})
            samples=[]
            for raw,sprite in [(26,13),(27,16),(28,15),(29,14)]:
                row=next(r for r in t['trace'] if r['pair'][owner]['move']=='special3' and r['pair'][owner]['move_tick']==raw)
                a,b=row['pair'][owner],row['pair'][1-owner]
                assert b['animation']['index']==sprite and b['animation']['anchor']==[128,288]
                assert b['body_node']['rotation']==0 and b['body_node']['scale']==[1,1]
                root=[(b['x']-a['x'])*a['facing'],b['height']-a['height']]
                if raw==27:assert root==[-34,33] and a['animation']['index']==6
                if raw==28:assert root==[-31,36] and a['animation']['index']==7
                normal_image=BASE/'gui'/name/'stills'/f'receiver-gomora_back_lift_receiver-{sprite:02d}.png'
                diagnostic_image=BASE/'diagnostic'/name/'stills'/f'diagnostic-raw-{raw:02d}.png'
                same_pixels=ImageChops.difference(Image.open(normal_image).convert('RGB'),Image.open(diagnostic_image).convert('RGB')).getbbox() is None
                samples.append({'normal_diagnostic_pixels_equal':same_pixels,'raw':raw,'sprite':sprite,'relative_root':root,'movie_frame':row['movie_frame'],'tick':row['tick'],'state_hash':row['state_hash']})
            if mode=='diagnostic':
                comparison=read(folder/'normal-comparison.json');assert comparison['all_input_hash_state_event_cost_and_exit_equal'] and comparison['normal_sha256']==sha(BASE/'gui'/name/'main-trace.json')
                for r,n in zip(t['trace'],normal['trace']):
                    for k in ['inputs','tick','state_hash','pre','events','hitstop','remaining','finished','projectiles']:assert r[k]==n[k]
                    for i in [0,1]:
                        for k in ['x','height','vx','vy','facing','state','state_tick','move','move_tick','hp','energy','stamina','motion','combat','animation','body_node']:assert r['pair'][i][k]==n['pair'][i][k]
                ds=[s for s in t['stills'] if s['key'].startswith('diagnostic-raw-')]
                assert len(ds)==13
                assert [s['actual_frame'] for s in ds]==list(range(335,348))
            cases.append({'mode':mode,'case':name,'trace':str(tp.relative_to(ROOT)),'trace_sha256':sha(tp),'png_count':len(pics),'samples':samples,'pictures':pics})
    out.write_text(json.dumps({'cases':cases,'total_pngs':sum(c['png_count'] for c in cases),'technical_checks_pass':True,'art_accepted':False,'installed':False},ensure_ascii=False,indent=2)+'\n');print(out)
if __name__=='__main__':main()

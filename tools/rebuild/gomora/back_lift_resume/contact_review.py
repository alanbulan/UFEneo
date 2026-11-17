"""在真实注册像素上复现接触方案；只输出测量与检查页，不安装招式。"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from resume import ROOT, ACTOR_OUT, REPORT, SURFACES, MEASUREMENT, read, save, sha


def main():
    receipt = read(ACTOR_OUT / 'registration.json')
    assert len(receipt['receiver']) == 6
    measurement = read(MEASUREMENT)['measurements'][1:]
    chains = {'original': [(5,0),(6,1),(7,2),(9,3),(8,4),(10,5)],
              'reordered': [(5,0),(6,1),(7,2),(2,3),(9,3),(8,4),(10,5)]}
    out = REPORT / 'contact-review'; out.mkdir(parents=True, exist_ok=True)
    report = {'schema':1,'registration_sha256':sha(ACTOR_OUT/'registration.json'),
              'runtime_installed':False,'accepted':False,'chains':{},
              'limits':['接触点共点不等于躯干贴合或无穿体。','受方04/05仍需独立离背轨迹，不能沿用保持接触。','静态双向页不代替主游戏720/1080动态验收。']}
    for name, chain in chains.items():
        rows=[]; previous=None
        for index,(ap,rp) in enumerate(chain):
            ar=receipt['actor'][ap];rr=receipt['receiver'][rp]
            actor=Image.open(ROOT/ar['path']).convert('RGBA');receiver=Image.open(ROOT/rr['path']).convert('RGBA')
            assert sha(ROOT/ar['path'])==ar['sha256'] and sha(ROOT/rr['path'])==rr['sha256']
            # 固定源列640，落在本链已人工核的背部，不应用到后续角部帧。
            x=ar['paste_origin'][0]+160
            a=np.asarray(actor)[...,3]>0;y=int(np.flatnonzero(a[:,x])[0]);contact=[x,y]
            sx,sy=SURFACES[rp];hold=[sx+6,sy+6]
            r=np.asarray(receiver)[...,3]>0;assert r[hold[1],hold[0]] and not r[hold[1]+1,hold[0]]
            paste=[contact[j]-hold[j] for j in (0,1)]
            canvas=Image.new('RGBA',actor.size);canvas.paste(receiver,tuple(paste))
            assert np.count_nonzero(np.asarray(canvas)[...,3])==np.count_nonzero(r),'受方裁切'
            overlap=int(np.count_nonzero(a & (np.asarray(canvas)[...,3]>0)))
            offset=[paste[0]+96-256,304-(paste[1]+184)]
            pelvis_source=measurement[rp]['points']['R']['xy']
            pelvis=[offset[0]+pelvis_source[0]*179/1024-90,offset[1]+178-pelvis_source[1]*179/1024]
            row={'actor_phase':ap,'receiver_phase':rp,'actor_grip':[x-256,304-y],
                 'receiver_hold_point':[sx-90,178-sy],'receiver_root':offset,
                 'receiver_pelvis':pelvis,'pelvis_step':math.dist(previous,pelvis) if previous else 0,
                 'alpha_overlap_pixels':overlap,'contact_error_px':0,'accepted':False}
            if name == 'reordered' and rp >= 4:
                solutions=[]
                count=int(np.count_nonzero(r))
                for dx in range(81):
                    for up in range(81):
                        moved=Image.new('RGBA',actor.size)
                        moved.paste(receiver,(paste[0]+dx,paste[1]-up))
                        mask=np.asarray(moved)[...,3]>0
                        if int(np.count_nonzero(mask))==count and not np.any(mask & a):
                            solutions.append((dx*dx+up*up,dx,up))
                best=min(solutions)
                row['conservative_separation_diagnostic']={'search_forward_up_range':[0,80],
                    'smallest_translation':[best[1],best[2]],'distance':math.sqrt(best[0]),
                    'accepted':False,'note':'仅整Alpha零交叠诊断；不作为瞬移或实际抛掷轨迹。'}
            rows.append(row);previous=pelvis
            # 两种绘制顺序都保留，防止一侧遮挡隐藏穿体；整幅镜像检双向。
            sheet=Image.new('RGB',(1024,690),'#30343c');draw=ImageDraw.Draw(sheet)
            for layer in range(2):
                composite=Image.alpha_composite(actor,canvas) if layer==0 else Image.alpha_composite(canvas,actor)
                for facing in range(2):
                    frame=composite if facing==0 else ImageOps.mirror(composite)
                    ox=facing*512;oy=layer*345+24;sheet.paste(frame,(ox,oy),frame)
                    cx=x if facing==0 else 511-x
                    draw.ellipse((ox+cx-2,oy+y-2,ox+cx+2,oy+y+2),outline='#00ffff')
                    draw.text((ox+5,oy-19),f'{name} A{ap:02d}/R{rp:02d} {"R" if facing==0 else "L"} / {"receiver front" if layer==0 else "actor front"}',fill='white')
            sheet.save(out/f'{name}-{index:02d}.png')
        report['chains'][name]={'pairs':rows,'max_pelvis_step':max(row['pelvis_step'] for row in rows)}
    save(out/'measurement.json',report)
    print({name:row['max_pelvis_step'] for name,row in report['chains'].items()})

if __name__=='__main__':main()

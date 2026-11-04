"""03卸重的整数离背候选。只移动完整注册帧，不写运行资产或正式招式。"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from resume import ROOT, ACTOR_OUT, REPORT, MEASUREMENT, read, save, sha, nearest


def build(vx=6, vy=15):
    receipt=read(ACTOR_OUT/'registration.json')
    measures=read(MEASUREMENT)['measurements'][1:]
    pairs=read(REPORT/'contact-review/measurement.json')['chains']['reordered']['pairs']
    local=[]
    for row in measures:
        x,y=row['points']['R']['xy'];local.append([nearest(x*179/1024-90),nearest(178-y*179/1024)])
    # 02末帧骨盆作为唯一初值。03起逐tick整数积分，不按背部吸附，不插值人物/根点。
    start=pairs[2]['receiver_root'];pelvis=[start[i]+local[2][i] for i in (0,1)]
    frames=[]
    for tick in range(28,48):
        if tick<32: ap,rp=7,2;root=start[:]
        else:
            ap,rp=(2,3) if tick<36 else (9,3) if tick<40 else (8,4) if tick<44 else (10,5)
            n=tick-32;pelvis[0]+=vx;pelvis[1]+=vy-n
            root=[pelvis[i]-local[rp][i] for i in (0,1)]
        ar,rr=receipt['actor'][ap],receipt['receiver'][rp]
        for r in (ar,rr): assert sha(ROOT/r['path'])==r['sha256']
        actor=Image.open(ROOT/ar['path']).convert('RGBA');receiver=Image.open(ROOT/rr['path']).convert('RGBA')
        a=Image.new('RGBA',(768,512));b=a.copy()
        a.paste(actor,(128,160));b.paste(receiver,(128+256+root[0]-96,160+304-root[1]-184))
        am=np.asarray(a)[...,3]>0;bm=np.asarray(b)[...,3]>0
        assert bm.sum()==np.count_nonzero(np.asarray(receiver)[...,3]),'受方裁切'
        overlap=int((am & bm).sum())
        frames.append({'tick':tick,'actor_phase':ap,'receiver_phase':rp,'receiver_root':root,
                       'receiver_pelvis':[root[i]+local[rp][i] for i in (0,1)],
                       'alpha_overlap_pixels':overlap,'actor':a,'receiver':b})
    return receipt,frames


def separation_diagnostic(receipt):
    """有界完整轮廓诊断，不把遮挡全部判为穿体。"""
    measures=read(MEASUREMENT)['measurements'][1:]
    def local(p):
        x,y=measures[p]['points']['R']['xy']
        return np.array([nearest(x*179/1024-90),nearest(178-y*179/1024)])
    prior=np.array([-31,18])+local(2); current=local(3)
    actor=np.asarray(Image.open(ROOT/receipt['actor'][2]['path']))[...,3]>0
    ys,xs=np.where(np.asarray(Image.open(ROOT/receipt['receiver'][3]['path']))[...,3]>0)
    best=None
    for x in range(-100,101):
        for y in range(201):
            xx=xs+256+x-96; yy=ys+304-y-184
            if xx.min()<0 or xx.max()>=512 or yy.min()<0 or yy.max()>=320:continue
            if not actor[yy,xx].any():
                cost=int(np.square(np.array([x,y])+current-prior).sum())
                if best is None or cost<best[0]:best=(cost,x,y)
    return {'root_search_x':[-100,100],'root_search_y':[0,200],
            'min_first03_pelvis_step':math.sqrt(best[0]),'root':[best[1],best[2]],
            'accepted':False,'meaning':'有界整Alpha零重叠解，不是全局下界，不表示真实遮挡都错误；拒绝将此解当瞬移补丁。'}


def main():
    out=REPORT/'departure-review';out.mkdir(parents=True,exist_ok=True)
    receipt,frames=build();previous=None
    for row in frames:
        row['pelvis_step']=math.dist(previous,row['receiver_pelvis']) if previous else 0
        previous=row['receiver_pelvis']
    # 每一tick实测，而非只抽查关键帧。末两相必须完整Alpha零交叠。
    assert all(r['alpha_overlap_pixels']==0 for r in frames if r['receiver_phase']>=4)
    for index in (3,4,7,8,11,12,15,16,19):
        row=frames[index];sheet=Image.new('RGB',(1536,1064),'#30343c');d=ImageDraw.Draw(sheet)
        for layer in range(2):
            comp=Image.alpha_composite(row['actor'],row['receiver']) if layer==0 else Image.alpha_composite(row['receiver'],row['actor'])
            for facing in range(2):
                im=comp if facing==0 else ImageOps.mirror(comp);sheet.paste(im,(768*facing,532*layer+20),im)
                d.text((768*facing+8,532*layer+5),f"tick {row['tick']} A{row['actor_phase']:02d}/R{row['receiver_phase']:02d} overlap={row['alpha_overlap_pixels']} {'R' if facing==0 else 'L'} / layer {layer}",fill='white')
        sheet.save(out/f"tick-{row['tick']:02d}.png")
    rows=[{k:v for k,v in r.items() if k not in ('actor','receiver')} for r in frames]
    data={'schema':1,'registration_sha256':sha(ACTOR_OUT/'registration.json'),'accepted':False,'runtime_installed':False,
          'reviewer':'root_delegated_by_user','trajectory':{'start_tick':32,'initial_velocity':[6,15],'gravity_per_tick':1,'anchor':'rounded measured pelvis','source_pixels_unchanged':True},
          'first03_separation_diagnostic':separation_diagnostic(receipt),
          'frames':rows,'first_fully_separated_tick':next((r['tick'] for r in rows if r['alpha_overlap_pixels']==0),None),
          'max_pelvis_step':max(r['pelvis_step'] for r in rows),
          'limits':['03初始抬离仍有交叠，不能宣称全段无穿体。','未接倒立落地；未验证主游戏空接保相、双向720/1080与回放。','整数轨迹为独立候选，不覆盖正式三级，不以整Alpha诊断代替接触美术审查。']}
    save(out/'measurement.json',data)
    print({k:data[k] for k in ('first_fully_separated_tick','max_pelvis_step')})
    print([(r['tick'],r['alpha_overlap_pixels']) for r in rows])

if __name__=='__main__':main()

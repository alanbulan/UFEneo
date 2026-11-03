"""按成品脚位重排显示时长；不改变角色速度、模拟或旧测量。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import csv,itertools,math,sys
from pathlib import Path
Path = _LayoutProjectPath
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parent))
from phase3_zetton import ROOT,read,save,font
OUT=ROOT/'reports/review/2026-10-22-zetton-defense'

def deviations(rows,ticks,sign):
    n=len(ticks);half=n//2;result=[]
    for side,start in [('near',0),('far',half)]:
        elapsed=0;origin=rows[start][side]['x']
        for k in range(half+1):
            i=start+k
            x=rows[i%n][side]['x']
            result.append(dict(side=side,frame=i,elapsed_tick=elapsed,local_x=x,deviation=round(x+sign*2*elapsed-origin,3)))
            if k<half:elapsed+=ticks[i]
    return result

def optimize(rows,old,sign,radius=4):
    n=len(old);half=n//2;best=None
    olddev=deviations(rows,old,sign)
    if min(old)>=.6*sum(old)/n and max(old)<=1.5*sum(old)/n and max(abs(r['deviation']) for r in olddev)<=8:return old
    for total in range(sum(old)-radius,sum(old)+radius+1):
        lo=math.ceil(.6*total/n);hi=math.floor(1.5*total/n);halves=[]
        for side,start in [('near',0),('far',half)]:
            choices={}
            for ts in itertools.product(range(lo,hi+1),repeat=half):
                elapsed=0;errors=[0]
                for k,t in enumerate(ts):
                    elapsed+=t;errors.append(rows[(start+k+1)%n][side]['x']+sign*2*elapsed-rows[start][side]['x'])
                score=(max(map(abs,errors)),sum(e*e for e in errors),sum((t-total/n)**2 for t in ts))
                if sum(ts) not in choices or score<choices[sum(ts)][0]:choices[sum(ts)]=(score,ts)
            halves.append(choices)
        for subtotal,(sc,a) in halves[0].items():
            if total-subtotal not in halves[1]:continue
            sc2,b=halves[1][total-subtotal];score=(max(sc[0],sc2[0]),abs(total-sum(old)),sc[1]+sc2[1],sc[2]+sc2[2])
            if best is None or score<best[0]:best=(score,list(a+b))
    return best[1]

def report(key,rows,old,ticks,sign,frames):
    OUT.mkdir(parents=True,exist_ok=True);stance=deviations(rows,ticks,sign);maximum=max(abs(r['deviation']) for r in stance)
    average=sum(ticks)/len(ticks)
    data=dict(old_ticks=old,ticks=ticks,average_tick=average,allowed_range=[.6*average,1.5*average],speed=2,cycle_ticks=sum(ticks),cycle_distance=sum(ticks)*2,rows=rows,stance=stance,max_abs_deviation=maximum,pass_=maximum<=8 and min(ticks)>=.6*average and max(ticks)<=1.5*average,method='沿用既有成品亮近/暗远脚部像素测量，世界x=局部x+方向×2×累计tick；每段起点为零；枚举整tick，最小化最大偏差。')
    save(OUT/f'{key}-measurements.json',data)
    with (OUT/f'{key}-deviations.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(stance[0]));w.writeheader();w.writerows(stance)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif']=['Microsoft YaHei'];plt.rcParams['axes.unicode_minus']=False
    times=np.r_[0,np.cumsum(ticks)];fig,axes=plt.subplots(2,1,figsize=(11,7))
    for side,c,label in [('near','#268fbc','近侧亮腿'),('far','#b56b30','远侧暗腿')]:
        axes[0].plot(times,[r[side]['x'] for r in rows]+[rows[0][side]['x']],'o-',c=c,label=label)
        rs=[r for r in stance if r['side']==side];axes[1].plot([r['frame'] for r in rs],[r['deviation'] for r in rs],'o-',c=c,label=label)
        for r in rs:axes[1].annotate(f"{r['deviation']:+.2f}",(r['frame'],r['deviation']),xytext=(3,5),textcoords='offset points')
    axes[0].legend();axes[0].set_ylabel('成品脚中心x / px');axes[0].set_xlabel('累计tick');axes[1].axhspan(-8,8,color='#cee5d3',alpha=.5);axes[1].axhline(0,c='#333',lw=1);axes[1].set_ylabel('撑地世界坐标偏差 / px');axes[1].set_xlabel('帧号，末格=下一周期帧0')
    for ax in axes:ax.grid(alpha=.2)
    fig.suptitle(f'{key} 旧{old} → 新{ticks}\n最大偏差{maximum:.3f}px，速度2，周期{sum(ticks)}tick');fig.tight_layout();fig.savefig(OUT/f'{key}-curves.png',dpi=160);plt.close(fig)
    previews=[];tile=frames[0].width*3
    for i,im in enumerate(frames):
        bg=Image.new('RGB',(tile,tile+48),'#202632');big=im.resize((tile,tile),Image.Resampling.NEAREST);bg.paste(big,(0,48),big);ImageDraw.Draw(bg).text((8,7),f'{key} #{i} / {ticks[i]}tick',font=font(20),fill='white');previews.append(bg)
    seq=previews*3;seq[0].save(OUT/f'{key}-3cycles.gif',save_all=True,append_images=seq[1:],duration=[round(t*1000/60) for t in ticks]*3,loop=0,disposal=2)
    seam=Image.new('RGB',(4*tile,tile+48),'#202632')
    for j,i in enumerate([len(frames)-2,len(frames)-1,0,1]):seam.paste(previews[i],(tile*j,0))
    seam.save(OUT/f'{key}-seam.png')
    return data

def main():
    configs=[('zetton','walk_forward','reports/review/2026-10-22-zetton-first/walk_forward-foot-measurements.json',[8,6,12,6,2,11,9,6],1),('ultraman','walk_back','art/fighters/ultraman/stage2/legacy/walk_back_single/foot-measurements.json',[11,11,7,3,11,12,5,4],-1),('ultraman','walk_forward','art/fighters/ultraman/stage2/legacy/walk_forward_final/foot-measurements.json',[8,8,11,5,8,8,8,8],1)]
    for fighter,action,path,old,sign in configs:
        d=read(ROOT/path);rows=d.get('frames',d.get('rows'));ticks=optimize(rows,old,sign)
        mp=ROOT/f'assets/fighters/{fighter}/animations/manifest.json';m=read(mp);clip=m['clips'][action];atlas=Image.open(ROOT/clip['texture'].removeprefix('res://')).convert('RGBA');frames=[atlas.crop((x,y,x+w,y+h)) for x,y,w,h in clip['rects']]
        result=report(f'{fighter}-{action}',rows,old,ticks,sign,frames);assert result['pass_'],result
        clip['ticks']=ticks;clip['rhythm_review']={'date':'2026-10-22','old_ticks':old,'max_abs_deviation':result['max_abs_deviation'],'report':f'reports/review/2026-10-22-zetton-defense/{fighter}-{action}-measurements.json'};save(mp,m)
        print(fighter,action,ticks,result['max_abs_deviation'],flush=True)

if __name__=='__main__':main()

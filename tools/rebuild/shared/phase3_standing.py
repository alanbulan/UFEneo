"""阶段三首批：整帧筛选、区域色替换、成品标框和增量安装；不调用生图。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import argparse, hashlib, json, shutil, sys; json = _LayoutJson
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=_LayoutProjectPath(_layout_root)
sys.path.insert(0,str(Path(__file__).resolve().parent))
import process_phase2 as process
import gate_a_finalize as color_tools
from sprite_gen.frames.extract import build_shared_palette
WORK=ROOT/'art/shared/stage3/batches/curated'
OUT=ROOT/'reports/review/2026-10-22-standing-crouch'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def font(n=24):return ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',n)

# 只选择该招式自己生成的完整帧。删错相位和调整停留沿用用户批准的关键姿势方法。
SELECT={
 'heavy':('heavy',list(range(7)),[3,3,3,4,4,5,6]),
 'spin_heavy':('spin_heavy',list(range(7)),[3,3,3,4,4,5,6]),
 'crush':(['crush_a']*3+['crush_b']*5,[0,1,2,0,1,2,3,4],[3,3,4,4,4,4,5,6]),
 'tackle':('tackle',list(range(8)),[2,2,3,3,3,3,4,6]),
 'pulse':('pulse',list(range(6)),[3,4,4,4,5,7]),
 'ranged_forward':('ranged_forward',[0,3,4,5,6,7],[5,4,4,5,7,7]),
 'crouch_start':('crouch_start',[0,1],[3,3]),
 'crouch':('crouch',[0,1],[12,12]),
 'crouch_rise':('crouch_rise',[0,1],[3,3]),
 'crouch_light':('crouch_light',list(range(4)),[3,3,4,8]),
 'crouch_light2':('crouch_light2',list(range(4)),[3,3,4,8]),
 'sweep':('sweep',[0,1,2,3,5],[3,3,4,8,10]),
 'slide':('slide',[0,1,2,3,4,5,7],[2,2,3,3,3,5,8]),
 'low_pulse':('low_pulse',list(range(5)),[3,4,4,5,7]),
}
NAMES={'heavy':'重击','spin_heavy':'回旋重击','crush':'超重击','tackle':'突进撞击','pulse':'光弹','ranged_forward':'八分光轮','crouch_start':'下蹲','crouch':'蹲姿保持','crouch_rise':'起身','crouch_light':'下段轻击','crouch_light2':'下段轻击二段','sweep':'扫腿','slide':'滑铲','low_pulse':'低姿光弹'}
# 人工在成品上标注的拳、掌、肩、脚中心；原生画布坐标。不是从姿势模板冒充实测。
ACTIVE={'heavy':{3:(161,86,13)},'spin_heavy':{3:(153,76,14)},
 'crush':{3:(150,85,16),4:(133,125,16)},'tackle':{3:(127,101,18),4:(126,101,18)},
 'pulse':{2:(151,83,12)},'ranged_forward':{2:(162,78,12)},
 'crouch_light':{2:(153,148,12)},'crouch_light2':{2:(157,122,12)},
 'sweep':{2:(171,174,13),3:(182,176,13)},'slide':{2:(174,177,14),3:(174,176,14),4:(139,177,14)},
 'low_pulse':{2:(160,120,12)}}

def paths(action,count):
    """每帧人工确认的远腿/远臂中心线，仅作RGB区域选择，绝不变换肢体。"""
    leg=[[(90,127),(70,149),(52,178)]]*count
    arm=[[(114,84),(125,101),(132,83)]]*count
    if action=='heavy':
        arm=[arm[0],arm[0],[(117,91),(141,91),(162,90)],[],[(119,91),(137,91),(156,91)],arm[0],arm[0]]
    if action=='spin_heavy':arm=[arm[0],arm[0],[],[],arm[0],arm[0],arm[0]]
    if action=='crush':
        arm=[[(111,73),(109,47),(106,20)],[(109,71),(99,45),(90,27)],[(112,82),(97,61),(82,42)],[],[(112,106),(119,119),(133,125)],[(116,103),(119,115),(120,124)],arm[0],arm[0]]
    if action=='tackle':
        arm=[[],[],[],[],[],[],[],[]] # 双臂缩在胸前互相遮挡，不能猜解剖后乱涂。
        leg=[[(90,125),(69,148),(48,179)],[(90,132),(65,155),(38,179)],[(90,132),(58,151),(31,174)],[(89,129),(56,149),(25,168)],[(91,130),(58,152),(28,170)],[(92,130),(64,155),(42,179)],[(91,127),(68,152),(49,178)],[(90,125),(71,149),(53,178)]]
    if action=='pulse':arm=[arm[0],[(113,86),(128,99),(137,79)],[(116,86),(138,85),(151,83)],arm[0],arm[0],arm[0]]
    if action=='ranged_forward':arm=[[(113,87),(122,105),(132,112)],[(114,91),(125,105),(132,111)],[],[],[(112,90),(124,105),(132,111)],arm[0]]
    if action in ['crouch','crouch_start','crouch_rise','crouch_light','crouch_light2','low_pulse']:
        # 同一动作的压低程度由画面头顶/髋位人工记录；腿的左右身份不换。
        hips={'crouch':[146,146],'crouch_start':[126,147],'crouch_rise':[147,126],
              'crouch_light':[146,153,154,146],'crouch_light2':[146,151,147,146],'low_pulse':[146,150,150,146,146]}[action]
        leg=[[(88,y),(63,(y+180)//2),(45,179)] for y in hips]
        arm=[[(113,y-37),(125,y-17),(131,y-40)] for y in hips]
        if action=='crouch_light':arm[1]=[(111,135),(132,143),(150,147)];arm[2]=[(112,135),(136,144),(153,148)]
        if action=='crouch_light2':arm[1]=[(112,124),(139,133),(151,139)];arm[2]=[(115,121),(139,121),(157,122)]
        if action=='low_pulse':arm[1]=[(116,124),(139,128),(157,124)];arm[2]=[(114,121),(141,126),(160,120)]
    if action=='sweep':
        leg=[[(89,149),(67,163),(57,179)],[(90,155),(72,169),(55,179)],[(87,159),(73,164),(69,177)],[(85,157),(79,166),(78,177)],[(88,145),(66,161),(50,179)]]
        arm=[[(114,116),(126,135),(134,120)],[(114,126),(131,142),(142,132)],[(113,131),(131,148),(142,135)],[(114,130),(132,146),(142,136)],[(113,115),(127,132),(133,117)]]
    if action=='slide':
        leg=[[(82,150),(70,167),(63,179)],[(80,164),(74,173),(66,179)],[(78,169),(72,174),(63,178)],[(80,170),(73,174),(61,179)],[(81,164),(75,173),(65,178)],[(80,159),(74,171),(68,178)],[(83,149),(68,165),(57,179)]]
        arm=[[(113,120),(124,138),(131,119)],[(114,132),(127,147),(136,134)],[(122,143),(135,151),(140,139)],[(121,142),(135,152),(143,139)],[(116,135),(132,147),(138,135)],[(112,122),(128,139),(134,123)],[(112,119),(127,136),(134,121)]]
    return leg,arm

def recolor(image,leg,arm):
    raise RuntimeError("永久停用远侧区域换色；仅允许GPT生成时画好暗色，后处理只做整图色板量化。历史脚本已归档。")

def hurtboxes(image):
    # 读取成品Alpha分段包围盒，避免站立框套低蹲；只产生模拟数据，不绘制角色。
    a=np.asarray(image)[:,:,3]>0;top=int(np.where(a)[0].min());boxes=[]
    for y0,y1 in [(top,min(top+35,184)),(min(top+35,183),min(top+75,184)),(min(top+75,183),184)]:
        ys,xs=np.where(a[y0:y1])
        if len(xs):boxes.append([int(xs.min())-96,184-y1,int(xs.max()-xs.min()+1),int(y1-y0)])
    return boxes

def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    for action,(sources,indices,ticks) in SELECT.items():
        folder=WORK/action;folder.mkdir(parents=True,exist_ok=True)
        leg,arm=paths(action,len(indices));frames=[];records=[]
        sources=[sources]*len(indices) if isinstance(sources,str) else sources
        compare=Image.new('RGB',(768*3,832*len(indices)),'#202632')
        for j,(source,index) in enumerate(zip(sources,indices)):
            p=ROOT/f'art/fighters/ultraman/stage2/legacy/processed/{source}/frame-{index}.png';before=Image.open(p).convert('RGBA')
            q=read(p.parent/'qa.json');issues=q.get('issues',[])
            exceptions=[]
            for issue in issues:
                if issue.startswith(f'frame {index}:'):
                    assert action in ['heavy','spin_heavy'] and '蓝色计时器缺失' in issue,issue
                    exceptions.append('攻击臂遮住计时器；不补画，头鳍、眼、胸肩花纹及相邻帧身份一致，静态复核保留')
            after,regions=recolor(before,leg[j],arm[j]);after.save(folder/f'frame-{j}.png');frames.append(after)
            regions.update(frame=j,source=p.relative_to(ROOT).as_posix(),source_sha256=sha(p),source_take=q.get('source','逐帧提取'),identity_exceptions=exceptions)
            save(folder/f'frame-{j}.json',regions);records.append(regions)
            mask=np.zeros((192,192),bool)
            for y,x0,x1 in regions['mask_rle_y_x0_x1']:mask[y,x0:x1]=True
            marked=np.array(before);marked[mask,:3]=[70,230,195]
            for col,(im,title) in enumerate([(before,'调色前'),(after,'调色后'),(Image.fromarray(marked),'青绿=实际RGB替换')]):
                big=im.resize((768,768),Image.Resampling.NEAREST);compare.paste(big,(col*768,j*832+64),big)
                ImageDraw.Draw(compare).text((col*768+10,j*832+8),f'{NAMES[action]} #{j} · {title}',font=font(),fill='white')
        atlas=Image.new('RGBA',(192*len(frames),192))
        for i,im in enumerate(frames):atlas.paste(im,(192*i,0))
        atlas.save(folder/'atlas.png');compare.save(OUT/f'{action}-recolor.png')
        save(folder/'curation.json',{'action':action,'sources':sources,'source_frames':indices,'ticks':ticks,'loop':action=='crouch','geometry_changed':False,'frames':records})
        # 非循环动作在原位播完；蹲姿循环连续3周期。GIF只作帧序审阅，主游戏实录另交。
        preview=[]
        for im in frames:
            bg=Image.new('RGB',(384,384),'#202632');large=im.resize((384,384),Image.Resampling.NEAREST);bg.paste(large,(0,0),large);preview.append(bg)
        seq=preview*3 if action=='crouch' else preview
        durations=[round(t*1000/60) for t in (ticks*3 if action=='crouch' else ticks)]
        seq[0].save(OUT/f'{action}.gif',save_all=True,append_images=seq[1:],duration=durations,loop=0 if action=='crouch' else 1,disposal=2)

def effects():
    clips={}
    for name,width in [('pulse',32),('slash',48)]:
        raw=ROOT/f'art/fighters/ultraman/stage2/generation/fx_{name}/02/raw.png'
        cells=process.grid_figures(Image.open(raw).convert('RGBA'),2,2,4)
        factor=width/max(c.width for c in cells);logical=[]
        for c in cells:
            pitch,phase=process.detect_pixel_grid(c,max_pitch=32)
            snapped=process.grid_snap_downscale(c,pitch,phase=phase) if min(pitch)>1 else c.copy()
            im=process._kcentroid_downscale(snapped,max(1,round(c.width*factor)),max(1,round(c.height*factor)))
            process.binarize_alpha(im)
            # 只去Alpha阈值后已脱离主体的孤立噪点；保留圆环中央透明孔。
            groups=process.components(im)
            for group in groups[1:]:
                if len(group)<=2:
                    for pt in group:im.putpixel(pt,(0,0,0,0))
                else:raise ValueError(name+'存在未解释碎片')
            logical.append(im)
        pal=build_shared_palette(logical,16)
        atlas=Image.new('RGBA',(64*4,64));frames=[]
        for i,im in enumerate(logical):
            im=process.apply_palette(im,pal);cell=Image.new('RGBA',(64,64));cell.paste(im,((64-im.width)//2,(64-im.height)//2));frames.append(cell);atlas.paste(cell,(64*i,0))
        folder=WORK/f'fx_{name}';folder.mkdir(parents=True,exist_ok=True);atlas.save(folder/'atlas.png')
        for i,im in enumerate(frames):im.save(folder/f'frame-{i}.png')
        dest=ROOT/f'assets/effects/{name}/atlas.png';dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists() and sha(dest)!=sha(folder/'atlas.png'):raise ValueError('旧特效需先归档')
        shutil.copy2(folder/'atlas.png',dest)
        clips[name]={'texture':'res://'+dest.relative_to(ROOT).as_posix(),'rects':[[64*i,0,64,64] for i in range(4)],'ticks':3,'source':raw.relative_to(ROOT).as_posix(),'source_sha256':sha(raw),'atlas_sha256':sha(dest),'colors':len(pal),'alpha_binary':True}
        sheet=Image.new('RGB',(1024,300),'#202632');big=atlas.resize((1024,256),Image.Resampling.NEAREST);sheet.paste(big,(0,44),big);ImageDraw.Draw(sheet).text((10,8),f'{name} · GPT Image像素特效 / 4帧 / 4倍',font=font(),fill='white');sheet.save(OUT/f'fx_{name}-contact.png')
    save(ROOT/'content/presentation/phase3_projectiles.json',clips)

def data_for(action,frames,ticks):
    template=ROOT/f'content/templates/humanoid/moves/{action}.json'
    d=read(template) if template.exists() else None;timeline=[];age=0
    first=min(ACTIVE.get(action,{999:None}));last=max(ACTIVE.get(action,{-1:None}))
    startup=sum(ticks[:first]);active=sum(ticks[first:last+1]) if last>=0 else 0
    for i,(im,duration) in enumerate(zip(frames,ticks)):
        hurt=hurtboxes(im);hit=[]
        if i in ACTIVE.get(action,{}):
            x,y,r=ACTIVE[action][i];hit=[[x-96-r,184-y-r,r*2,r*2]]
        for local in range(duration):
            cancel=[]
            if d and i>=first:
                if action=='crouch_light':cancel=['crouch_light2']
                elif action=='crouch_light2':cancel=['sweep']
                elif action in ['heavy','spin_heavy']:cancel=['motion_236','motion_623','special']
            dx=3 if action=='tackle' and i in [2,3,4] else 2 if action=='slide' and i in [2,3,4] else 0
            events=[{'kind':'sound','id':'heavy' if action in ['heavy','spin_heavy','crush','tackle'] else 'light' if action in ['crouch_light','crouch_light2','sweep','slide'] else 'pulse'}] if d and age==0 else []
            timeline.append({'sprite':i,'dx':dx,'dy':0,'hitboxes':hit,'hurtboxes':hurt,'cancel':cancel,'events':events});age+=1
    if d:
        d.update(startup=startup,active=active,recovery=sum(ticks)-startup-active,frames=timeline)
        if action=='ranged_forward':d['display_name']='八分光轮'
        if d['kind']=='projectile':
            x,y,_=ACTIVE[action][first]
            d['projectile']={'effect':'slash' if action=='ranged_forward' else 'pulse','spawn':[x-96,184-y],'box':[-22,-8,44,16] if action=='ranged_forward' else [-14,-10,28,20],'speed':10 if action=='ranged_forward' else 8,'life':100}
        save(ROOT/f'content/fighters/ultraman/moves/{action}.json',d)
    return timeline

def install():
    manifest_path=ROOT/'assets/fighters/ultraman/animations/manifest.json';m=read(manifest_path);postures={}
    for action,(_,indices,ticks) in SELECT.items():
        folder=WORK/action;c=read(folder/'curation.json');assert c['ticks']==ticks
        frames=[Image.open(folder/f'frame-{i}.png').convert('RGBA') for i in range(len(indices))]
        timeline=data_for(action,frames,ticks)
        if action not in ACTIVE:postures[action]=timeline
        dest=ROOT/f'assets/fighters/ultraman/animations/{action}/atlas.png';dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists() and sha(dest)!=sha(folder/'atlas.png'):raise ValueError(action+'正式旧图应先归档')
        shutil.copy2(folder/'atlas.png',dest)
        m['clips'][action]={'texture':'res://'+dest.relative_to(ROOT).as_posix(),'cell':192,'anchor_y':184,'rects':[[192*i,0,192,192] for i in range(len(indices))],'ticks':ticks,'loop':action=='crouch','atlas_sha256':sha(dest),'curation':(folder/'curation.json').relative_to(ROOT).as_posix(),'motion_review':{'user_approved':False,'verdict':'screened_pending_user_review'}}
        # 真4倍联系表，逐帧标本帧全部tick中的攻击/受击框；飞行盒另附特效表。
        sheet=Image.new('RGB',(768*min(4,len(indices)),832*((len(indices)+3)//4)),'#202632');draw=ImageDraw.Draw(sheet)
        for i,im in enumerate(frames):
            x=i%4*768;y=i//4*832;big=im.resize((768,768),Image.Resampling.NEAREST);sheet.paste(big,(x,y+64),big)
            frame=timeline[sum(ticks[:i])]
            for key,color in [('hurtboxes','#50d9ff'),('hitboxes','#ff5c62')]:
                for bx,by,bw,bh in frame[key]:draw.rectangle((x+(96+bx)*4,y+64+(184-by-bh)*4,x+(96+bx+bw)*4,y+64+(184-by)*4),outline=color,width=3)
            draw.text((x+8,y+8),f'{NAMES[action]} #{i} · {ticks[i]} tick · 红攻/蓝受',font=font(),fill='white')
        sheet.save(OUT/f'{action}-contact.png')
    save(manifest_path,m);save(ROOT/'content/fighters/ultraman/state_frames.json',postures)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','effects','install']);a=p.parse_args();globals()[a.command]()

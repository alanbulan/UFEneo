"""阶段 2 整帧生产：定稿、姿势条、GPT Image、像素网格、共享色板、质检和审片。

必须使用 sprite-gen 的专用虚拟环境运行。项目总方案明确采用透明、固定格切帧，
因此不采用技能默认的色键或研究网页；像素还原复用其确定性网格/kCentroid 实现。
"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
from concurrent.futures import ThreadPoolExecutor, as_completed
from types import SimpleNamespace
import argparse
import hashlib
import json; json = _LayoutJson
import math
import shutil
import sys
import time
from statistics import median
from PIL import Image, ImageDraw
import numpy as np

ROOT = _LayoutProjectPath(_layout_root)
SKILL = Path.home()/'.codex/skills/sprite-gen'
sys.path.insert(0,str(SKILL))
sys.path.insert(0,str(ROOT/'tools'))
import art_pipeline
from sprite_gen.frames.extract import (detect_pixel_grid, grid_snap_downscale,
    _kcentroid_downscale, build_shared_palette, apply_palette, binarize_alpha)

MODEL = 'gpt-image-2.5-sunburst'
CELL, ANCHOR = 192, (96,184)
CLIPS = {
 'idle': ('idle',6,[10]*6,True,'自然呼吸待机，双臂与两腿有细微且清晰的配合，不要摇晃整张静止图'),
 'walk_forward': ('locomotion',8,[5]*8,True,'向右前走：左右腿依次接触、下沉、经过、抬起；双臂反向摆动'),
 'walk_back': ('locomotion',8,[5]*8,True,'面向右向后退走，始终面朝右；先移动后脚再移动前脚，双臂保持格斗防守'),
 'dash_start': ('locomotion',2,[2,2],False,'冲刺起步：深屈膝蹬地，然后身体前倾加速，双臂开始摆动'),
 'dash': ('locomotion',6,[2]*6,True,'面向右冲刺循环，双腿交替大幅蹬地腾空，双臂大幅前后摆动，身体保持前倾'),
 'dash_stop': ('locomotion',3,[2,2,2],False,'冲刺刹停：前脚撑地制动、后腿回收、恢复格斗站姿'),
 'light1': ('strike',5,[2,2,4,4,8],False,'左手直拳第一段：屈肘预备、伸左拳、完全击出、屈肘收回、恢复；另一手护胸，两腿移重心'),
 'light2': ('strike',5,[2,2,4,4,8],False,'右手后手直拳第二段：右肩后拉、转髋、右拳前伸完全击出、收回、恢复；与第一段明确不同'),
 'light3': ('strike',6,[2,2,2,3,5,6],False,'第三段掌根重击：腰身下沉、双肩蓄力、右掌向前上击出、伸臂顶峰、回收、恢复；不用前两段拳法冒充'),
 'takeoff': ('jump',2,[1,1],False,'斜跳起跳：双腿压低蓄力、后腿完全蹬地；完整人物、脚底基线固定'),
 'flip_forward': ('jump',4,[3,3,3,3],True,'斜跳前空翻：收膝、头向前下翻转、背部朝前、展开双腿；四帧是完整重画的整帧，不是旋转同一张人物'),
 'land': ('jump',2,[2,2],False,'落地衔接：前脚先着地双膝深屈吸震，然后后脚着地恢复站姿'),
 'diagonal_heavy': ('jump',5,[3,4,4,5,7],False,'斜跳空中重击飞踢：收膝、向前下伸右腿、右腿完全伸展、回收屈膝、准备落地，双臂维持平衡'),
 'launcher': ('strike',7,[3,3,5,3,3,3,3],False,'前向升击：蹲低蓄力、后手下收、由腰带动向前上方上勾拳、拳举过头、另一手护胸、回收、准备追击'),
 'chase_takeoff': ('jump',3,[1,1,1],False,'升击后的专用追击跳：手臂由升击收回、前膝提起、后腿猛蹬地向右上追击；与普通起跳不同'),
 'chase_light1': ('jump',4,[2,3,5,10],False,'追击跳空中轻击第一段：双膝收起、前手拳伸出、前手拳击中、收拳保持浮空；与斜跳飞踢完全不同'),
}


def save(path, data):
    # 多会话并行时别的进程可能正在读同一文件：先写临时文件再整体替换，读者不会读到半截JSON。
    import os,time
    path=ROOT/path if not isinstance(path,Path) else path
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(f'.{path.name}.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for attempt in range(50):
        try:
            os.replace(tmp,path);return
        except PermissionError:
            time.sleep(.1)
    os.replace(tmp,path)


def native_models():
    for fighter,height,cell in [('ultraman',144,192),('zetton',166,256)]:
        source=ROOT/'art/model_sheets'/fighter/'model.png'
        rgba=Image.open(source).convert('RGBA')
        bbox=rgba.getbbox()
        crop=rgba.crop(bbox)
        pitch,phase=detect_pixel_grid(crop,max_pitch=6)
        # 旧素材清单声明 pixel_grid=2；自动检测会把重复的 2px 块误判为4。
        logical=grid_snap_downscale(crop,2,phase=(0,0))
        if logical.height!=height:
            logical=_kcentroid_downscale(logical,round(logical.width*height/logical.height),height)
        binarize_alpha(logical)
        palette=build_shared_palette([logical],32)
        # 关键身份色固定留在共用色板，避免极小计时器色块被中位切分吞掉。
        if fighter=='ultraman':
            palette=build_shared_palette([logical],28)+[(30,170,230),(155,230,250),(245,230,155),(224,204,115)]
        logical=apply_palette(logical,palette)
        canvas=Image.new('RGBA',(cell,cell))
        canvas.alpha_composite(logical,(cell//2-logical.width//2,cell-8-height))
        out=ROOT/'assets/fighters'/fighter/'model-native.png'
        canvas.save(out)
        canvas.resize((cell*4,cell*4),Image.Resampling.NEAREST).save(source.parent/'model-reference-x4.png')
        save('content/fighters/'+fighter+'/palette.json',dict(colors=[list(c) for c in palette],source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),measured_pitch=pitch,source_grid=2))


def pose(name,index,count):
    phase=index/count*math.tau
    points=dict(head=(100,53),neck=(98,72),hip=(94,120),shoulder_back=(86,78),shoulder_front=(108,78),
                elbow_back=(76,103),wrist_back=(89,99),elbow_front=(120,95),wrist_front=(132,79),
                knee_back=(76,148),ankle_back=(65,184),knee_front=(111,149),ankle_front=(125,184))
    if name.startswith('walk') or name=='dash':
        stride=21 if name=='dash' else 15
        wave=math.sin(phase)
        lift=max(0,math.cos(phase))*14
        points.update(knee_back=(91-int(wave*12),149-int(lift)),ankle_back=(94-int(wave*stride),184-int(lift)),
                      knee_front=(98+int(wave*12),149),ankle_front=(98+int(wave*stride),184),
                      elbow_back=(87+int(wave*14),100),wrist_back=(94+int(wave*20),107),
                      elbow_front=(107-int(wave*14),95),wrist_front=(117-int(wave*20),101))
        if name=='walk_back':
            points['wrist_front']=(128,79)
            points['wrist_back']=(91,95)
        if name=='dash':
            for key in ['head','neck','shoulder_back','shoulder_front','elbow_back','wrist_back','elbow_front','wrist_front']:
                x,y=points[key];points[key]=(x+14,y+8)
    elif name.startswith('light') or name=='launcher':
        power=[0.1,0.45,1.0,0.55,0.0][min(4,index*5//count)]
        hand='back' if name=='light2' else 'front'
        end_y=26 if name=='launcher' else (66 if name=='light3' else 82)
        points['wrist_'+hand]=(int(124+power*43),int(95+(end_y-95)*power))
        points['elbow_'+hand]=(int(108+power*28),int(97+(end_y-95)*power*.6))
        points['hip']=(94+int(power*5),120)
    elif name=='diagonal_heavy':
        power=[0,.5,1,.55,.15][index]
        points.update(knee_front=(119,131),ankle_front=(int(126+power*43),int(168-power*35)),
                      knee_back=(81,139),ankle_back=(72,160))
    elif name=='chase_light1':
        power=[0,.7,1,0][index]
        points.update(knee_front=(116,136),ankle_front=(108,163),knee_back=(79,136),ankle_back=(72,160),
                      wrist_front=(int(130+power*35),78),elbow_front=(int(117+power*24),89))
    elif name=='flip_forward':
        # 火柴人只约束完整重画的姿势，不供运行时肢体变换。
        angle=index/max(1,count-1)*math.tau
        points={k:(round(96+(x-96)*math.cos(angle)-(y-118)*math.sin(angle)),
                   round(118+(x-96)*math.sin(angle)+(y-118)*math.cos(angle))) for k,(x,y) in points.items()}
    elif name in ['takeoff','land','dash_start','dash_stop','chase_takeoff']:
        bend=(count-index)/count if name in ['land','dash_stop'] else 1-index/max(1,count-1)
        for key in ['head','neck','shoulder_back','shoulder_front','elbow_back','wrist_back','elbow_front','wrist_front','hip']:
            x,y=points[key];points[key]=(x+int((1-bend)*5),y+int(bend*22))
    elif name=='idle':
        for key in ['head','neck','shoulder_back','shoulder_front','elbow_back','wrist_back','elbow_front','wrist_front']:
            x,y=points[key];points[key]=(x,y+round(math.sin(phase)*2))
    return points


def prepare():
    native_models()
    for name,(template,count,ticks,loop,description) in CLIPS.items():
        cols=max(2,math.ceil(count/2));rows=2
        guide=Image.new('RGB',(cols*512,1024),(246,246,246))
        draw=ImageDraw.Draw(guide)
        frames=[]
        for index in range(count):
            joints=pose(name,index,count)
            ox=index%cols*512+64;oy=index//cols*512+64
            def xy(key):
                x,y=joints[key];return ox+x*2,oy+y*2
            for chain in [('head','neck','hip'),('neck','shoulder_back','elbow_back','wrist_back'),
                          ('neck','shoulder_front','elbow_front','wrist_front'),('hip','knee_back','ankle_back'),('hip','knee_front','ankle_front')]:
                draw.line([xy(k) for k in chain],fill=(40,70,95),width=6)
            hx,hy=xy('head');draw.ellipse((hx-12,hy-15,hx+12,hy+15),outline=(40,70,95),width=5)
            draw.line((ox,oy+368,ox+384,oy+368),fill=(100,180,130),width=2)
            height_curve=[0,30,58,84,105,120,128,132,130,124,112,96,76,52,24,0]
            frames.append(dict(joints=joints,ticks=ticks[index],height=height_curve[min(15,index*16//count)] if template=='jump' else 0))
        folder=ROOT/'art/shared/poses/templates/humanoid'/template/name
        folder.mkdir(parents=True,exist_ok=True);guide.save(folder/'guide.png')
        save(folder/'poses.json',dict(action=name,template=template,cell=[192,192],anchor=list(ANCHOR),frames=frames,
             source='art/shared/references/games/locomotion-v001/ultraman-fe3/'+('jump-detail-028' if template=='jump' else 'run-cycle-v001' if name.startswith('dash') else 'walk-scan')+'/capture.json',
             method='同类格斗参考的节奏与关键姿势；关节为人工编排，不是剧集姿势提取结果'))
        prompt=(f'为附件中的同一个初代奥特曼 C 型绘制【{description}】完整逐帧像素动画。'
                f'严格保持身份定稿的比例、花纹、配色、眼睛、头顶鳍和蓝色计时器，左上光源，深色一像素轮廓，真正清晰像素块。'
                f'参考图一是唯一身份锚，最近邻四倍图；图二只约束姿势和顺序，不要画火柴人或参考线。'
                f'输出 {cols*512}×1024，{cols} 列、2 行，每格 512×512。按先左后右、再上到下，恰好 {count} 个完整人物，末尾空格透明。'
                f'每个人物站立身高约 288 像素（原生144像素的2倍），脚底基线为所在格 y=432，身体中心约x=256。'
                f'所有格子都是同一个镜头、同一尺寸，固定正侧视朝右。空翻只改变完整重画的姿态，不改变画布、镜头或人物真实尺寸。'
                f'逐格严格跟随姿势条的关节位置；人物是连续完整身体，双臂双腿都要参与动作。'
                f'透明背景，真正 PNG Alpha；无地面、投影、文字、边框、格线、标签、速度线、特效、残影、其他人物，不得裁切头脚。')
        save('art/fighters/ultraman/stage2/legacy/requests/'+name+'.json',dict(id=name,template=template,frames=count,ticks=ticks,loop=loop,
             guide=folder.relative_to(ROOT).as_posix()+'/guide.png',size=f'{cols*512}x1024',columns=cols,rows=2,prompt=prompt))


def generate(name):
    is_ui=name.startswith('ui-')
    brief=json.loads((ROOT/'art/fighters/ultraman/stage2/legacy/requests'/f'{name}.json').read_text('utf-8'))
    parent=ROOT/brief['generation_dir'] if brief.get('generation_dir') else ROOT/'art/generation'/('ui' if is_ui else 'ultraman')/name
    existing=sorted(parent.glob('[0-9][0-9]'))
    if len(existing)>=6: return dict(id=name,status='blocked',reason='已达六次生成上限，待人工')
    take=parent/f'{len(existing)+1:02d}'
    take.mkdir(parents=True)
    if 'reference_images' in brief: refs=[ROOT/path for path in brief['reference_images']]
    else:
        refs=[ROOT/'art/fighters/ultraman/model/model-reference-x4.png']
        if not is_ui: refs.append(ROOT/brief['guide'])
        else: refs.append(ROOT/'art/fighters/zetton/model/model-reference-x4.png')
        refs.extend(ROOT/path for path in brief.get('additional_references',[]))
	# 每次请求冻结实际输入，之后修定身份锚也不会改变已提交请求的证据。
    snapshots=[]
    for i,path in enumerate(refs):
        frozen=take/'inputs'/f'{i}.png'
        frozen.parent.mkdir(parents=True,exist_ok=True)
        frozen.write_bytes(path.read_bytes());snapshots.append(frozen)
    refs=snapshots
    prompt=brief['prompt']
    args=SimpleNamespace(model=MODEL,reference=refs,out=take/'raw.png',dry_run=False,mask=None)
    request=dict(prompt=prompt,size=brief['size'],quality='high',asset_kind=brief.get('asset_kind','background' if is_ui else 'character'))
    meta=dict(id=name,model=MODEL,quality='high',prompt=prompt,inputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in refs],created_unix=int(time.time()),status='submitting')
    save(take/'meta.json',meta)
    try:
        art_pipeline.generate_image(args,request,'验收门 A UI 风格候选' if is_ui else '验收门 A 整帧动作候选')
        meta['status']='generated'
    except Exception as exc:
        meta['status']='blocked'
        meta['reason']=str(exc)
    save(take/'meta.json',meta)
    return dict(id=name,status=meta['status'],take=str(take.relative_to(ROOT)),reason=meta.get('reason'))


def ui_requests():
    variants={
      'a':'经典街机银红：粗厚银色九宫格金属面板、红色装甲条、蓝色计时器宝石、深蓝星空，强对比大块像素高光与铆钉，厚边框但留白足',
      'b':'机械格斗银红：冷银深铁金属、鲜红切角护甲、厚实机械锁扣与接缝，蓝白计时器槽；朴素硬朗的街机机台质感，较紧凑的信息布局',
      'c':'光之国银红：明亮银色与红色细装甲、青蓝宝石点缀、祖母绿星云，边框更轻、分区宽敞，光之国建筑的像素棱面与白蓝能量扫光',
    }
    for key,style in variants.items():
        prompt=(f'绘制一套高完成度的像素街机格斗游戏 UI 风格稿，游戏正式名称为“奥特曼格斗进化Neo”，方案 {key.upper()}：{style}。'
          '一张 1536×1024 整体效果图，二乘二版面：左上标题页、右上双人选人页、左下实战HUD、右下该方案的面板按钮血条与色板放大样例。'
          '前三个游戏画面分别保持16:9，按640×360原生像素设计，最近邻像素效果；不是网页后台或科幻仪表盘。'
          '标题页：M78星空、左侧附件定稿初代与杰顿像素大图、右侧纵向菜单：开始对战、训练、档案、设置。'
          '选人页：双方共用的密集头像大网格、红蓝双光标、底部小站像和形态选择；角色格统一宽高与间距，角色格优先占面积，不做双方独立翻页。必须有奥特曼、怪兽、宇宙人三个独立分类入口。'
          '战斗页：固定侧视城市，双方像素角色、顶部像素血条、三格能量和体力，中央90秒与计时器，画面底部留空。'
          '质感参考经典拳皇街机像素界面，布局参考格斗进化3；只用简体中文，文字清晰整齐，纹理由像素高光暗部构成。'
          '角色身份只使用两个附件；不要扭曲其花纹、比例和配色。不要把稿中的任何UI当成已实现的游戏界面。')
        save('art/fighters/ultraman/stage2/legacy/requests/ui-'+key+'.json',dict(id='ui-'+key,size='1536x1024',prompt=prompt))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['prepare','generate'])
    parser.add_argument('actions',nargs='*')
    args=parser.parse_args()
    if args.command=='prepare':
        prepare();ui_requests()
        print('定稿、四类姿势模板及请求已准备')
    else:
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures={pool.submit(generate,name):name for name in args.actions}
            for future in as_completed(futures):
                print(json.dumps(future.result(),ensure_ascii=False),flush=True)


if __name__=='__main__': main()

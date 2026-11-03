"""按动作安装通过头部校准的整帧，并同步原点、碰撞框和投技抓点。

超差动作整体保留原正式版；本工具不会生成图像或修改速度、位移、时序。
"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from collections import defaultdict
from pathlib import Path
Path = _LayoutProjectPath
import copy,math,shutil
from PIL import Image
from head_scale import ROOT,WORK,OUT,read,save,sha
import head_size

ARCHIVE=ROOT.parent/'UFEneo_archive/2026-10-22/head-scale-before'


def point(p,row):
    """模拟坐标(x右、y上)→旧图→新图→模拟坐标，根点保持不动。"""
    _,_,w,h=row['old_rect'];ax,ay=row['anchor'];sx,sy=row['old_to_new']['scale'];tx,ty=row['old_to_new']['translation']
    return [round((p[0]+w/2)*sx+tx-ax),round(ay-((h-8-p[1])*sy+ty))]


def box(b,row):
    _,_,w,h=row['old_rect'];ax,ay=row['anchor'];sx,sy=row['old_to_new']['scale'];tx,ty=row['old_to_new']['translation']
    # 向外取整，禁止因四舍五入漏掉边缘像素。
    left=math.floor((b[0]+w/2)*sx+tx-ax);right=math.ceil((b[0]+b[2]+w/2)*sx+tx-ax)
    low=math.floor(ay-((h-8-b[1])*sy+ty));high=math.ceil(ay-((h-8-b[1]-b[3])*sy+ty))
    return [left,low,max(1,right-left),max(1,high-low)]


def geometry(frame,row):
    result=copy.deepcopy(frame)
    for key in ['hitboxes','hurtboxes']:
        if key in result:result[key]=[box(b,row) for b in result[key]]
    if 'guard_box' in result:result['guard_box']=box(result['guard_box'],row)
    if 'target' in result:result['target']['grip']=point(result['target']['grip'],row)
    if 'grab_points' in result:result['grab_points']={k:point(p,row) for k,p in result['grab_points'].items()}
    for attachment in result.get('attachments',[]):attachment['anchor']=point(attachment['anchor'],row)
    if 'beam_origin' in result:result['beam_origin']=point(result['beam_origin'],row)
    for shot in result.get('shots',[]):
        if 'spawn' in shot:shot['spawn']=point(shot['spawn'],row)
        if 'anchor' in shot:shot['anchor']=point(shot['anchor'],row)
    # 飞行物自己的大小/判定跟特效走，不能随人物重采样而缩放。
    # target.root是抛出后的世界落点，dx/dy、速度、跳跃和取消窗口均保留。
    return result


def backup(path):
    dest=ARCHIVE/path.relative_to(ROOT)
    if dest.exists():raise ValueError('已有归档，禁止重复校准：'+str(path))
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(path),str(dest))


def state_clip(key,sprite,clips):
    mapping={'vertical_air':'vertical_jump','backward_air':'flip_back','diagonal_air':'flip_forward','charge':'charge'}
    key=mapping.get(key,key)
    if key=='dash' and 'dash_start' in clips:
        for name in ['dash_start','dash','dash_stop']:
            seq=clips[name].get('sequence_frames',[])
            if sprite in seq:return name,seq.index(sprite)
    if key in clips:
        offset=int(clips[key].get('simulation_sprite_offset',0));index=sprite-offset
        # air_apex/fall的模拟sprite沿用vertical_jump的全局编号。
        if key=='air_apex':index=sprite-2
        elif key=='air_fall':index=sprite-3
        return key,max(0,min(len(clips[key]['rects'])-1,index))
    return None,None


def add_missing_postures(fighter,states,clips,eligible):
    # 初代早期版本的这些状态使用统一矩形；补成跟随新整帧的实际几何。
    for action in ['idle','walk_forward','walk_back','takeoff','land','chase_takeoff']:
        if action in states or (fighter,action) not in eligible:continue
        seq=[]
        for row,ticks in zip(eligible[(fighter,action)],clips[action]['ticks']):
            im=Image.open(ROOT/row['output']);a=im.getchannel('A');x0,y0,x1,y1=a.getbbox();ax,ay=row['anchor'];height=y1-y0;boxes=[]
            for top,bottom in [(y0,y0+height//3),(y0+height//3,y0+height*2//3),(y0+height*2//3,y1)]:
                b=a.crop((0,top,im.width,bottom)).getbbox()
                if b:boxes.append([b[0]-round(ax),round(ay)-bottom,b[2]-b[0],bottom-top])
            for _ in range(ticks):seq.append(dict(sprite=row['frame'],dx=0,dy=0,hitboxes=[],hurtboxes=boxes,cancel=[],events=[]))
        states[action]=seq
    return states


def main():
    if (WORK/'installation.json').exists():raise ValueError('已经安装；不得对已转换数据再次仿射')
    audit=read(WORK/'audit.json');groups=defaultdict(list)
    for row in audit['rows']:groups[(row['fighter'],row['action'])].append(row)
    feet=read(OUT/'walk-summary.json');walk_pass={(r['fighter'],r['action']):r for r in feet if r['variant']=='candidate' and r['pass_']}
    eligible={};blocked=[]
    for key,rows in groups.items():
        rows.sort(key=lambda r:r['frame'])
        if any(r['status']=='blocked' for r in rows) or (key[1].startswith('walk_') and key not in walk_pass):blocked.append(key);continue
        head_size.validate(WORK/'candidates'/key[0]/key[1],key[0]);eligible[key]=rows
    # 所有计划和转换在移动正式文件之前计算完成。
    plans={}
    for fighter in ['ultraman','zetton']:
        path=ROOT/f'assets/fighters/{fighter}/animations/manifest.json';old=read(path);new=copy.deepcopy(old);data={};atlases={}
        for (f,action),rows in eligible.items():
            if f!=fighter:continue
            frames=[Image.open(ROOT/r['output']).convert('RGBA') for r in rows]
            atlas=Image.new('RGBA',(sum(im.width for im in frames),max(im.height for im in frames)));rects=[];left=0
            for im in frames:atlas.alpha_composite(im,(left,0));rects.append([left,0,im.width,im.height]);left+=im.width
            dest=ROOT/f'assets/fighters/{f}/animations/{action}/head-calibrated.png';atlases[dest]=atlas
            clip=new['clips'][action];clip.update(texture='res://'+dest.relative_to(ROOT).as_posix(),rects=rects,anchors=[r['anchor'] for r in rows],head_qa=(WORK/'candidates'/f/action/'head-qa.json').relative_to(ROOT).as_posix(),head_calibration={'source':'art/shared/production/head-scale/audit.json','rule':'同原图统一比例、头部偏差≤±8%','geometry_synchronized':True},motion_review={'user_approved':False,'verdict':'head_calibrated_pending_user_review'})
            if action.startswith('walk_'):clip['ticks']=walk_pass[(f,action)]['ticks']
            move_path=ROOT/f'content/fighters/{f}/moves/{action}.json'
            if move_path.exists():
                move=read(move_path);move['frames']=[geometry(r,rows[min(int(r['sprite']),len(rows)-1)]) for r in move['frames']];data[move_path]=move
        state_path=ROOT/f'content/fighters/{fighter}/state_frames.json';states=read(state_path)
        for key,seq in states.items():
            for i,frame in enumerate(seq):
                clip,index=state_clip(key,int(frame['sprite']),old['clips'])
                if (fighter,clip) in eligible:seq[i]=geometry(frame,eligible[(fighter,clip)][index])
        add_missing_postures(fighter,states,new['clips'],eligible)
        data[state_path]=states;data[path]=new;plans[fighter]=(old,new,data,atlases)
    for fighter,(old,new,data,atlases) in plans.items():
        for path,value in data.items():backup(path);save(path,value)
        for path,atlas in atlases.items():path.parent.mkdir(parents=True,exist_ok=True);atlas.save(path)
        # 只有不再被正式manifest引用的旧atlas才移走；未过门槛的动作仍使用原图。
        used={v['texture'] for v in new['clips'].values()}
        for texture in {v['texture'] for v in old['clips'].values()}-used:backup(ROOT/texture.removeprefix('res://'))
        path=ROOT/f'assets/fighters/{fighter}/animations/manifest.json';m=read(path)
        for action,c in m['clips'].items():
            if (fighter,action) in eligible:c['atlas_sha256']=sha(ROOT/c['texture'].removeprefix('res://'))
        save(path,m)
    save(WORK/'installation.json',dict(installed=[list(k) for k in eligible],blocked=[list(k) for k in blocked],archive=str(ARCHIVE),simulation_policy='只同步图像坐标相关框/抓点/特效发射位置；不改dx/dy、速度、时序、伤害和取消规则'))
    print('已安装合格动作；未通过动作完整保留旧版。详见installation.json')


if __name__=='__main__':main()

"""赛文首批增量装配：只读逐帧看过的本角色成品，不借用初代人物帧。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import copy,shutil
from PIL import Image,ImageDraw
from head_scale import ROOT,read,save,sha,font
import head_size
from stage4_ultraseven import WORK,OUT


def assemble(action):
    registry=read(WORK/'asset-registry.json')['assets'];profile=read(WORK/'profiles.json')[action]
    sources=[];ticks=[];heads=[];color_sources=[]
    for key,entry in registry.items():
        if entry['action']!=action:continue
        folder=WORK/'accepted'/key
        if not (folder/'visual-review.json').exists() or read(folder/'visual-review.json').get('status')!='self_checked_pending_user_review':raise ValueError(key+'尚未逐帧自检通过')
        import slugger_qa
        hq=head_size.validate(folder,'ultraseven');slugger_qa.validate(folder);request=ROOT/f'art/fighters/ultraman/stage2/legacy/requests/s4seven_{key.replace("/","_")}.json'
        import limb_color_qa
        limb_color_qa.validate_folder(folder,'ultraseven',action)
        cb=read(folder/'limb-color-baseline.json')
        q=read(request) if request.exists() else dict(ticks=[profile['ticks'][i] for i in entry['indices']])
        if len(hq['frames'])!=len(q['ticks']):raise ValueError('实际帧数与已记录时长不符')
        for row,t,cr in zip(hq['frames'],q['ticks'],cb['frames']):sources.append(folder/row['image']);heads.append(copy.deepcopy(row));ticks.append(t);color_sources.append(folder/cr['image'])
    if not sources:raise ValueError('没有该动作的已检查本角色素材')
    timing=read(WORK/'timing.json') if (WORK/'timing.json').exists() else {}
    ticks=timing.get(action,ticks)
    assert len(ticks)==len(sources)
    folder=WORK/'assembled'/action;folder.mkdir(parents=True,exist_ok=True);frames=[]
    cell=max(Image.open(p).width for p in sources)
    # 完整原图可恰好贴边；只增加透明边界，人物与脚底锚同步平移，绝不缩小人物。
    if any((lambda im: im.getbbox()[0]<=0 or im.getbbox()[1]<=0 or im.getbbox()[2]>=im.width or im.getbbox()[3]>=im.height)(Image.open(p)) for p in sources):cell+=64
    atlas=Image.new('RGBA',(cell*len(sources),cell))
    color_rows=[]
    for i,path in enumerate(sources):
        original=Image.open(path).convert('RGBA');assert original.width==original.height
        dx=(cell-original.width)//2;dy=cell-original.height
        heads[i]['assembly_offset']=[dx,dy]
        anchor=heads[i].get('foot_anchor',[original.width//2,original.height-8]);heads[i]['foot_anchor']=[anchor[0]+dx,anchor[1]+dy]
        image=Image.new('RGBA',(cell,cell));image.alpha_composite(original,(dx,dy))
        heads[i]['hint']=[heads[i]['hint'][0]+dx,heads[i]['hint'][1]+dy]
        heads[i]['head_region']=[[x+dx,y+dy] for x,y in heads[i]['head_region']]
        if heads[i].get('alignment_origin'):heads[i]['alignment_origin']=[heads[i]['alignment_origin'][0]+dx,heads[i]['alignment_origin'][1]+dy]
        dest=folder/f'frame-{i}.png';image.save(dest);frames.append(image);atlas.alpha_composite(image,(cell*i,0));heads[i].update(frame=i,image=dest.name,image_sha256=sha(dest))
        base=Image.new('RGBA',(cell,cell));base.alpha_composite(Image.open(color_sources[i]).convert('RGBA'),(dx,dy));p=folder/f'color-source-{i}.png';base.save(p);color_rows.append(dict(image=p.name,sha256=sha(p)))
    atlas.save(folder/'atlas.png');save(folder/'head-qa.json',dict(scale_policy='per_frame_head',reference=head_size.reference('ultraseven'),frames=heads,issues=[]));head_size.validate(folder,'ultraseven');slugger_qa.validate(folder)
    save(folder/'limb-color-baseline.json',dict(frames=color_rows,stage='由逐帧可信调色前源做相同透明平移'))
    limb_color_qa.validate_folder(folder,'ultraseven',action)
    save(folder/'curation.json',dict(action=action,ticks=ticks,loop=profile['loop'],sources=[s.relative_to(ROOT).as_posix() for s in sources],atlas_sha256=sha(folder/'atlas.png'),user_approved=False))
    return frames,ticks


def hurtboxes(im,anchor=None):
    alpha=im.getchannel('A');x,y,r,b=alpha.getbbox();height=b-y;result=[];ax,ay=anchor or [im.width//2,im.height-8]
    for top,bottom in [(y,y+height//3),(y+height//3,y+2*height//3),(y+2*height//3,b)]:
        box=alpha.crop((0,top,im.width,bottom)).getbbox()
        if box:result.append([box[0]-ax,ay-bottom,box[2]-box[0],bottom-top])
    return result


def timeline(action,frames,ticks):
    points=read(WORK/'hit-points.json') if (WORK/'hit-points.json').exists() else {}
    active=points.get(action,{})
    template=ROOT/f'content/templates/humanoid/moves/{action}.json'
    move=read(template) if template.exists() else None
    if move and not active:raise ValueError(action+'缺少成品拳/脚/发射原点标注，禁止用剪影坐标填充')
    first=min(map(int,active)) if active else len(ticks);last=max(map(int,active)) if active else -1
    result=[]
    heads=read(WORK/f'assembled/{action}/head-qa.json')['frames']
    for i,(im,t) in enumerate(zip(frames,ticks)):
        ox,oy=heads[i].get('assembly_offset',[0,0])
        ax,ay=heads[i].get('foot_anchor',[im.width//2,im.height-8])
        hit=[]
        if str(i) in active:
            x,y,r=active[str(i)];x+=ox;y+=oy;hit=[[x-ax-r,ay-y-r,r*2,r*2]]
        for j in range(t):
            cancel=[]
            if i>=first:
                if action=='light1':cancel=['light2']
                elif action=='light2':cancel=['light3']
                elif action=='crouch_light':cancel=['crouch_light2']
                elif action=='crouch_light2':cancel=['sweep']
            sound='pulse' if action in ['pulse','ranged_forward','low_pulse'] else 'heavy' if action in ['heavy','spin_heavy','crush','tackle','launcher','sweep','slide'] else 'light'
            row=dict(sprite=i,dx=3 if action=='tackle' and i in [2,3,4] else 2 if action=='slide' and i in [2,3,4] else 0,dy=0,hitboxes=hit if move else [],hurtboxes=hurtboxes(im,[ax,ay]),cancel=cancel,events=[dict(kind='sound',id=sound)] if move and i==j==0 else [])
            row.update(impact_effect='impact_heavy' if sound=='heavy' else 'impact_light',block_effect='impact_guard')
            if action in ['pulse','low_pulse'] and str(i) in active:
                x,y,_=active[str(i)];row['beam_origin']=[x+ox-ax,ay-y-oy]
            result.append(row)
    if move:
        move.update(display_name=read(WORK/'profiles.json')[action]['name'],startup=sum(ticks[:first]),active=sum(ticks[first:last+1]),recovery=sum(ticks[last+1:]),frames=result)
        if action in ['pulse','low_pulse','ranged_forward']:
            effects=read(WORK/'projectiles.json') if (WORK/'projectiles.json').exists() else {}
            if action not in effects:raise ValueError(action+'还没有本招特效和飞行物数据')
            move['projectile']=effects[action]
        move['feedback']=dict(spark='impact_heavy' if action in ['heavy','spin_heavy','crush','tackle','launcher'] else 'impact_light',block_spark='impact_guard',hitstop=7 if action in ['heavy','crush'] else 4,blockstop=3,shake=2 if action in ['heavy','crush'] else 0,flash=2,color=[1,1,1,1])
    return result,move


def install(action):
    frames,ticks=assemble(action);seq,move=timeline(action,frames,ticks);folder=WORK/'assembled'/action
    mp=ROOT/'assets/fighters/ultraseven/animations/manifest.json'
    manifest=read(mp) if mp.exists() else dict(schema=1,cell=[192,192],anchor=[96,184],reviewed=False,clips={})
    if action in manifest['clips']:raise ValueError('已安装该动作，旧图应先归档，禁止重复覆盖')
    target=ROOT/f'assets/fighters/ultraseven/animations/{action}/atlas.png';target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(folder/'atlas.png',target)
    cell=frames[0].width
    clip=dict(texture='res://'+target.relative_to(ROOT).as_posix(),cell=cell,anchor=[cell//2,cell-8],anchor_y=cell-8,rects=[[cell*i,0,cell,cell] for i in range(len(frames))],ticks=ticks,loop=read(WORK/'profiles.json')[action]['loop'],atlas_sha256=sha(target),head_qa=(folder/'head-qa.json').relative_to(ROOT).as_posix(),slugger_qa=(folder/'slugger-qa.json').relative_to(ROOT).as_posix(),curation=(folder/'curation.json').relative_to(ROOT).as_posix(),motion_review={'user_approved':False,'verdict':'self_checked_pending_user_review'},audio_events=[{'kind':'sound','id':'step','at':'state_entry'}])
    clip['anchors']=[r['foot_anchor'] for r in read(folder/'head-qa.json')['frames']]
    if action=='dash_sequence':
        for name,indices in [('dash_start',[0,1]),('dash',[2,3,4,5]),('dash_stop',[6,7,8])]:
            c=copy.deepcopy(clip);c.update(rects=[clip['rects'][i] for i in indices],anchors=[clip['anchors'][i] for i in indices],ticks=[ticks[i] for i in indices],loop=False,sequence_frames=indices,simulation_sprite_offset=indices[0]);manifest['clips'][name]=c
    else:manifest['clips'][action]=clip
    save(mp,manifest)
    if move:save(ROOT/f'content/fighters/ultraseven/moves/{action}.json',move)
    else:
        path=ROOT/'content/fighters/ultraseven/state_frames.json';states=read(path) if path.exists() else {};states['dash' if action=='dash_sequence' else action]=seq;save(path,states)
    definition_path=ROOT/'content/fighters/ultraseven/definition.json';definition=read(definition_path)
    definition['unsupported_moves']=[a for a in read(ROOT/'content/templates/humanoid/move_manifest.json') if not (ROOT/f'content/fighters/ultraseven/moves/{a}.json').exists()]
    save(definition_path,definition)
    # 审片联系表只绘制标注，不用这些线条作为游戏内人物/装饰。
    tile=cell*4;stride=tile+64
    sheet=Image.new('RGB',(min(4,len(frames))*tile,((len(frames)+3)//4)*stride),'#202632');d=ImageDraw.Draw(sheet)
    for i,im in enumerate(frames):
        x=i%4*tile;y=i//4*stride;large=im.resize((tile,tile),Image.Resampling.NEAREST);sheet.paste(large,(x,y+64),large)
        for kind,color in [('hurtboxes','#50d9ff'),('hitboxes','#ff5c62')]:
            ax,ay=clip['anchors'][i]
            for bx,by,bw,bh in seq[sum(ticks[:i])][kind]:d.rectangle((x+(ax+bx)*4,y+64+(ay-by-bh)*4,x+(ax+bx+bw)*4,y+64+(ay-by)*4),outline=color,width=3)
        d.text((x+8,y+8),f'{action} #{i} · {ticks[i]} tick · 红攻/蓝受',font=font(22),fill='white')
    OUT.mkdir(parents=True,exist_ok=True);sheet.save(OUT/f'{action}-contact.png')
    return dict(action=action,status='installed_pending_user_review')

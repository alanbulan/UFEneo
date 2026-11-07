"""用户指定的单帧前走修订。只生成完整人物，不绘制或拼接成品肢体。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
from types import SimpleNamespace
import argparse
import hashlib
import json; json = _LayoutJson
import sys
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = _LayoutProjectPath(_layout_root)
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path.home() / '.codex/skills/sprite-gen'))
import art.pipeline
from process_phase2 import components
from sprite_gen.frames.extract import detect_pixel_grid, grid_snap_downscale, _kcentroid_downscale, apply_palette, binarize_alpha

RUN = ROOT / 'art/fighters/ultraman/stage2/generation/walk_forward_single_v1'
WORK = ROOT / 'art/fighters/ultraman/stage2/legacy/walk_forward_single'
OUT = ROOT / 'reports/review/2026-10-21-forward-walk'
MODEL = 'gpt-image-2.5-sunburst'
ORDER = [0, 2, 4, 6, 1, 3, 5, 7]
PHASES = ['着地A', '下沉A', '交错A', '抬起A', '着地B', '下沉B', '交错B', '抬起B']
DESCRIPTIONS = [
 '近腿在前伸出、脚跟着地；远腿在后、脚尖着地。远臂向前、近臂向后，四肢反向摆动。',
 '下沉A：近腿在地面承重并屈膝，脚比帧0后退10原生像素；远腿离地从后方回收，向前摆。',
 '交错A：亮色近腿伸直、垂直撑住身体；暗色远腿屈膝向前摆，被近腿遮住一部分，远脚离地。两臂接近垂下。',
 '抬起A：近腿仍在身下略后方支撑，近支撑腿几乎垂直、仅略向后倾斜，不能大幅后伸；远腿向前抬膝准备伸腿落地，远脚尚未着地。近臂开始向前，远臂开始向后。',
 '近腿在后、脚尖着地；暗色远腿在前伸出、脚跟着地。近臂向前、远臂向后，与帧0近远身份完全相反。',
 '下沉B：远腿在地面承重并屈膝，脚比帧4后退10原生像素；近腿离地从后方回收，向前摆。',
 '交错B：暗色远腿伸直、垂直撑住身体；亮色近腿屈膝向前摆，遮在远腿前面，近脚离地。两臂接近垂下。',
 '抬起B，也是下一帧0前一刻：远腿在后撑地、脚尖推地；近腿向前抬膝再伸展，但近脚仍离地，下一帧才脚跟着地。绝不能复制帧0。',
]

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text('utf-8'))

def frame_pose(i):
    bob = [0, 2, 0, -2, 0, 2, 0, -2][i]
    # 肢体形状仅作生成参考，绝不进入运行时渲染。
    legs = [
      {'knee':[108,147], 'ankle':[116,178], 'foot':[[113,177],[119,178],[133,180],[133,183],[116,184],[112,183]], 'track':[116,184]},
      {'knee':[106,150], 'ankle':[106,178], 'foot':[[101,176],[110,177],[122,180],[122,184],[103,184],[100,182]], 'track':[106,184]},
      {'knee':[96,149], 'ankle':[96,178], 'foot':[[91,176],[100,178],[111,180],[111,184],[92,184],[89,182]], 'track':[96,184]},
      {'knee':[91,148], 'ankle':[85,177], 'foot':[[80,174],[88,176],[101,181],[100,184],[83,184],[79,181]], 'track':[86,184]},
      {'knee':[80,145], 'ankle':[69,175], 'foot':[[65,171],[72,173],[79,181],[79,184],[75,184],[66,178]], 'track':[76,184]},
      {'knee':[85,140], 'ankle':[80,164], 'foot':[[76,161],[83,162],[96,169],[95,173],[84,172],[76,166]], 'track':[86,171]},
      {'knee':[111,139], 'ankle':[94,161], 'foot':[[90,158],[97,159],[111,164],[110,168],[96,167],[89,163]], 'track':[96,166]},
      {'knee':[115,144], 'ankle':[108,171], 'foot':[[103,168],[111,168],[124,173],[124,177],[108,176],[102,174]], 'track':[106,175]},
    ]
    near_arm = [(81,97,70,115),(87,99,82,119),(95,100,95,121),(108,97,115,119),
                (112,96,122,113),(105,99,111,119),(95,100,95,121),(87,98,81,119)]
    def arm(j):
        ex,ey,wx,wy = near_arm[j]
        return {'elbow':[ex,ey+bob], 'wrist':[wx,wy+bob]}
    return {'index':i, 'phase':PHASES[i], 'ticks':5, 'height':144-bob,
            'bob':bob, 'hip':[96,118+bob], 'near':legs[i], 'far':legs[(i+4)%8],
            'near_arm':arm(i), 'far_arm':arm((i+4)%8)}

def current_pose(i):
    return read(WORK/'poses.json')['frames'][i]

def guide(p):
    im = Image.new('RGB', (192,192), '#f1f3f4')
    d = ImageDraw.Draw(im)
    near, far, torso = '#35b7e0', '#c8793a', '#56626f'
    b = p['bob']
    for side,color in [('far',far),('near',near)]:
        leg=p[side]; hip=(92 if side=='far' else 96,118+b)
        d.line([hip,tuple(leg['knee']),tuple(leg['ankle'])],fill=color,width=9)
        for pt in [hip,tuple(leg['knee']),tuple(leg['ankle'])]:
            d.ellipse((pt[0]-4,pt[1]-4,pt[0]+4,pt[1]+4),fill=color)
        d.polygon([tuple(q) for q in leg['foot']],fill=color)
        if side=='far':
            a=p['far_arm']; d.line([(92,78+b),tuple(a['elbow']),tuple(a['wrist'])],fill=far,width=7)
            d.polygon([(89,74+b),(100,76+b),(106,89+b),(103,103+b),(100,119+b),(89,121+b),(86,104+b),(86,86+b)],fill=torso)
            d.polygon([(94,44+b),(99,40+b),(102,47+b),(108,48+b),(112,56+b),(109,62+b),(109,68+b),(101,74+b),(94,70+b),(91,60+b),(91,50+b)],fill=torso)
            d.rectangle((96,68+b,103,80+b),fill=torso)
        else:
            a=p['near_arm']; d.line([(95,79+b),tuple(a['elbow']),tuple(a['wrist'])],fill=near,width=7)
    return im.resize((960,960),Image.Resampling.NEAREST)

def prepare():
    if (WORK/'method.json').exists():
        raise ValueError('已准备本次方法，禁止覆盖姿势与生成记录')
    WORK.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    palette_path=ROOT/'content/fighters/ultraman/palette.json'
    palette=read(palette_path)
    palette['side_view_roles']={
      'rule':'远侧肢体银色与红色压暗一档；近远身份不随前后位置交换。只选用现有32项色板，不添加颜色。',
      'near_side':{'name':'近侧色','silver_indices':[0,2], 'red_indices':[4,7,12,14],
                   'silver_rgb':[[229,229,229],[192,190,191]],'red_rgb':[[243,25,25],[244,35,33],[250,63,56],[246,71,64]]},
      'far_side':{'name':'远侧色','silver_indices':[9,10], 'red_indices':[3],
                  'silver_rgb':[[169,167,170],[144,137,140]], 'red_rgb':[[202,8,10]]},
      'shared_outline_indices':[1,5,8,23],
      'foot_measurement':'银色靴部按近侧亮银/远侧暗银分组；曲线只能读取实际成品像素，不以姿势坐标冒充实测。'}
    save(palette_path,palette)
    base=Image.open(ROOT/'assets/fighters/ultraman/model-native.png').convert('RGBA')
    reference=Image.new('RGBA',(1024,1024));reference.alpha_composite(base.resize((960,960),Image.Resampling.NEAREST),(32,32))
    reference.save(WORK/'model-reference.png')
    poses=[]
    contact=Image.new('RGB',(192*4,232*2),'#202632');draw=ImageDraw.Draw(contact)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
    for i in range(8):
        p=frame_pose(i);poses.append(p)
        canvas=Image.new('RGB',(1024,1024),'#f1f3f4');canvas.paste(guide(p),(32,32))
        canvas.save(WORK/f'pose-{i}.png')
        thumbnail=canvas.crop((32,32,992,992)).resize((192,192),Image.Resampling.NEAREST)
        x=i%4*192;y=i//4*232
        contact.paste(thumbnail,(x,y+32));draw.text((x+5,y+5),f'帧{i} {PHASES[i]}',font=font,fill='white')
    contact.save(OUT/'pose-contact.png')
    save(WORK/'poses.json',{'cell':[192,192],'anchor':[96,184],'frames':poses,
        'reference':'art/shared/references/games/lpc-walk-cycle/source.png', 'reference_sha256':sha(ROOT/'art/shared/references/games/lpc-walk-cycle/source.png'),
        'reference_row_zero_based':11,'reference_columns':[1,2,3,4,5,6,7,8],
        'method':'仅核对完整左右脚相位；按初代144像素重新编排侧身窄躯干、双色四肢，不复制LPC比例或像素。'})
    save(WORK/'method.json',{'schema':1,'id':'walk_forward_single_v1','action':'walk_forward','model':MODEL,
        'request_size':'1024x1024','quality':'high','background':'transparent','frames':8,'order':ORDER,
        'ticks':[5]*8,'walk_speed':2,'cycle_displacement':80,'step_displacement':40,
        'max_attempts_per_frame':6,'max_requests':None,'user_approved':False,
        'bootstrap':'帧0没有此前前走关键帧，第三附件使用既有定稿；以后使用上一个自检通过帧。补间同时附前后关键帧。'})
    save(WORK/'review.json',{'frames':{},'user_approved':False,'motion_verdict':'not_generated'})
    print('已准备侧身双色单帧参考和本次独立计数。')

def refs_for(i,review):
    refs=[WORK/'model-reference.png',WORK/f'pose-{i}.png']
    if i in [0,2,4,6]:
        prior={0:None,2:0,4:2,6:4}[i]
        if prior is None:refs.append(WORK/'model-reference.png')
        else:
            if str(prior) not in review['frames']:raise ValueError('上一关键帧未自检通过')
            refs.append(ROOT/review['frames'][str(prior)]['reference'])
    else:
        if any(str(k) not in review['frames'] for k in [0,2,4,6]):raise ValueError('四个关键帧全部通过后才能补间')
        for key in [(i-1)%8,(i+1)%8]:refs.append(ROOT/review['frames'][str(key)]['reference'])
    return refs

def generate(i,correction):
    if read(WORK/'method.json').get('status') == 'blocked':
        raise ValueError('本次动作已因单帧三次上限停止；禁止继续生成或更换标签重算')
    review=read(WORK/'review.json')
    refs=refs_for(i,review)
    parent=RUN/f'frame-{i:02d}'
    attempts=list(parent.glob('[0-9][0-9]/meta.json'))
    total=list(RUN.glob('frame-*/*/meta.json'))
    if len(attempts)>=6:raise ValueError('同一帧已用完6次，标待人工；不设动作总次数上限')
    take=parent/f'{len(attempts)+1:02d}';take.mkdir(parents=True)
    frozen=[]
    for n,p in enumerate(refs):
        dest=take/'inputs'/f'{n}.png';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());frozen.append(dest)
    p=current_pose(i)
    guide_role='附件2的蓝色=近侧手臂和近侧腿，橙色=远侧手臂和远侧腿；这些引导色绝不画进角色。'
    prompt=(f'为纯2D侧视格斗游戏绘制一张且仅一张完整初代奥特曼C型的前走帧，帧{i}：{PHASES[i]}。透明背景。'
      '附件1是唯一身份与像素风格定稿；附件2是本帧必须严格遵循的侧身姿势剪影。'+guide_role+
      ('附件3是上一张自检通过帧，仅维持面具、体型、花纹、明暗和像素密度，不复制它的姿势。' if i in [2,4,6] else
       '附件3是同一定稿作首次启动身份参考。' if i==0 else
       '附件3、4分别是前一个和后一个已通过关键帧；只画两者之间的这一小步，不抄端点。')+
      f'本帧动作必须是：{DESCRIPTIONS[i]}'
      f'附件2的原生坐标：亮近手腕{p["near_arm"]["wrist"]}、暗远手腕{p["far_arm"]["wrist"]}；亮近膝{p["near"]["knee"]}、亮近踝{p["near"]["ankle"]}；暗远膝{p["far"]["knee"]}、暗远踝{p["far"]["ankle"]}。这些坐标只帮助服从剪影，不在成品写字。'
      '镜头固定、人物面朝画面右方，身体窄侧面，胸腹不要画成正面方块；双臂在身体两侧前后摆，不交叉在胸前、不握拳护胸。'
      '重要：两腿银红花纹相同，必须用明暗区分。近侧臂腿亮银RGB229,229,229与192,190,191，近侧红RGB243,25,25；'
      '远侧臂腿始终压暗一档，远侧靴全部暗银RGB169,167,170与144,137,140，远侧红RGB202,8,10。'
      '远侧脚在前面时也必须暗，近侧脚在后面时也必须亮；禁止把颜色绑定到左右位置。两只靴都朝右，不能让后脚反向朝左。'
      '保留初代C型银色面具、头顶鳍、黄色眼部、胸前蓝色计时器、红银皮套同一纹样；侧身也需看见胸前蓝计时器的小色块。'
      '身体和手脚完整连接，无多余肢体，无断肢，无黑色脸部竖条，无塑料护甲，不增加靴子装饰、膝部护甲或服装。'
      '左上光，深色一原生像素外轮廓，真正硬边像素画，严格匹配定稿的原生144像素人体比例和头身比。'
      f'画布1024x1024，姿势位置严格贴合附件2，原生192x192画布放大5倍并四周留32像素透明；原生脚底y184即画布y952，原生根点x96即画布x512；本帧原生高度{p["height"]}。'
      '两只脚相对身体的前后位置、脚跟/脚尖触地方式完全照剪影，不把两脚重居中，不变步幅。只输出一个完整人物，不是动作条、不是多帧图。'
      '无文字、图例、数字、格线、地面、影子、棋盘格、速度线或特效，角色以外真正Alpha透明。')
    if correction:prompt+='\n本次额外姿势约束（重试时包含上次拒收原因）：'+correction
    meta={'frame':i,'attempt':len(attempts)+1,'action_request_number':len(total)+1,'model':MODEL,'quality':'high',
          'prompt':prompt,'inputs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in frozen],
          'created_unix':int(time.time()),'status':'submitting','user_approved':False}
    save(take/'meta.json',meta)
    args=SimpleNamespace(model=MODEL,reference=frozen,out=take/'raw.png',dry_run=False,mask=None)
    try:
        art_pipeline.generate_image(args,{'prompt':prompt,'size':'1024x1024','quality':'high','asset_kind':'character'},'前走单帧修订，待自检与用户审片')
        meta['status']='generated'
    except Exception as exc:
        meta['status']='request_failed_or_rejected';meta['reason']=str(exc)
    save(take/'meta.json',meta)
    print(json.dumps({k:meta.get(k) for k in ['frame','attempt','action_request_number','status','reason']},ensure_ascii=False),flush=True)

def extract(i,attempt):
    take=RUN/f'frame-{i:02d}'/f'{attempt:02d}'
    raw=take/'raw.png'
    if not raw.exists():raw=take/'rejected/raw.png'
    image=Image.open(raw).convert('RGBA')
    source_alpha=art_pipeline.alpha_report(image)
    if source_alpha['transparent_fraction']<.05 or source_alpha['rectangular_matte']:raise ValueError('原图没有可靠真透明')
    solid=image.getchannel('A').point(lambda a:255 if a>=200 else 0)
    bbox=solid.getbbox();cut=image.crop(bbox)
    import head_size
    factor,heads,head_reference,head_issues=head_size.calibration('ultraman',[cut],{})
    from process_phase2 import snap_for_scale
    snap,pitch,phase=snap_for_scale(cut,factor,max_pitch=12)
    height=round(cut.height*factor);width=round(cut.width*factor)
    if width>176:raise ValueError('人物超宽，禁止裁切')
    pixel=_kcentroid_downscale(snap,width,height);binarize_alpha(pixel)
    palette=read(ROOT/'content/fighters/ultraman/palette.json')['colors']
    pixel=apply_palette(pixel,palette)
    groups=components(pixel);total=sum(map(len,groups));fragments=sum(len(g) for g in groups[1:] if len(g)>2)
    for group in groups[1:]:
        if len(group)<=2:
            for point in group:pixel.putpixel(point,(0,0,0,0))
    # 以髋部横向根点配准；腾空姿势可显式保留离地高度，走路默认脚底184。
    a=np.asarray(pixel);mask=a[:,:,3]>0
    _,hips=np.where(mask[round(height*.48):round(height*.57)])
    root_x=float(np.median(hips)) if len(hips) else width/2
    left=round(96-root_x);top=int(current_pose(i).get('foot_bottom',184))-height
    if left<0 or left+width>192:raise ValueError('配准越界，禁止裁掉身体')
    canvas=Image.new('RGBA',(192,192));canvas.alpha_composite(pixel,(left,top));canvas.save(take/'native.png')
    rgba=np.asarray(canvas);rgb=rgba[:,:,:3].astype(int);visible=rgba[:,:,3]>0
    blue=visible&(rgb[:,:,2]>140)&(rgb[:,:,1]>100)&(rgb[:,:,2]-rgb[:,:,0]>40)
    red=visible&(rgb[:,:,0]>150)&(rgb[:,:,0]>rgb[:,:,1]*1.4)
    bright=visible&(rgb[:,:,0]>180)&(rgb[:,:,1]>170)&(rgb[:,:,2]>110)
    ys,xs=np.where(visible)
    issues=list(head_issues)
    head_hint=[left+heads[0]['center'][0]*factor,top+heads[0]['center'][1]*factor]
    head_region=[[left+x*factor,top+y*factor] for x,y in heads[0]['polygon']]
    actual_head=head_size.head(canvas,'ultraman',head_hint,region=head_region)
    deviation=actual_head['length']/head_reference['measurement']['length']-1 if actual_head else None
    if deviation is None or abs(deviation)>.08:issues.append('成品头部尺寸超出±8%或不可测')
    save(take/'head-qa.json',dict(reference=head_reference,frames=[dict(frame=0,image='native.png',image_sha256=sha(take/'native.png'),hint=head_hint,head_region=head_region,source=raw.relative_to(ROOT).as_posix(),source_sha256=sha(raw),raw_head_length=heads[0]['length'],shared_scale=factor,measurement=actual_head)],issues=issues))
    if not blue.any():issues.append('蓝色计时器缺失')
    if red.sum()<60:issues.append('红色身份色块缺失')
    if bright.sum()<8:issues.append('眼部/银色高光缺失')
    if fragments/max(1,total)>.005:issues.append('存在游离身体碎片')
    report={'frame':i,'attempt':attempt,'source':raw.relative_to(ROOT).as_posix(),'source_sha256':sha(raw),
      'source_alpha':source_alpha,'height':height,'width':width,'grid_pitch':pitch,'grid_phase':phase,
      'source_corner_alpha':[image.getpixel(q)[3] for q in [(0,0),(image.width-1,0),(0,image.height-1),(image.width-1,image.height-1)]],
      'blue_pixels':int(blue.sum()),'red_pixels':int(red.sum()),'fragment_fraction':fragments/max(1,total),
      'opaque_colors':len(set(map(tuple,rgba[visible,:3]))),'alpha_binary':set(np.unique(rgba[:,:,3]))<={0,255},
      'centroid':[float(xs.mean()),float(ys.mean())], 'root_registration':[left,top], 'issues':issues,
      'manual_checks_required':['头顶鳍','面具与花纹','近远腿相位与遮挡','远侧臂腿压暗','完整四肢','脚底与步幅'],
      'user_approved':False}
    save(take/'qa.json',report)
    preview=Image.new('RGB',(768,768),'#202632');large=canvas.resize((768,768),Image.Resampling.NEAREST);preview.paste(large,(0,0),large);preview.save(take/'preview.png')
    print(json.dumps(report,ensure_ascii=False))

def accept(i,attempt,note):
    if not note:raise ValueError('必须记录逐帧人工视觉检查结论')
    take=RUN/f'frame-{i:02d}'/f'{attempt:02d}';qa=read(take/'qa.json')
    if qa['issues']:raise ValueError('像素筛查仍失败，不能接受')
    review=read(WORK/'review.json');p=WORK/'accepted'/f'frame-{i}.png';p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes((take/'native.png').read_bytes())
    reference=p.with_name(f'frame-{i}-reference.png')
    c=Image.new('RGBA',(1024,1024));c.alpha_composite(Image.open(p).resize((960,960),Image.Resampling.NEAREST),(32,32));c.save(reference)
    review['frames'][str(i)]={'attempt':attempt,'image':p.relative_to(ROOT).as_posix(),'reference':reference.relative_to(ROOT).as_posix(),
      'image_sha256':sha(p),'qa':(take/'qa.json').relative_to(ROOT).as_posix(),'agent_accepted':True,'user_approved':False,'note':note}
    save(WORK/'review.json',review);print(f'帧{i}记录自检通过，仍待用户审片。')

def reject(i,attempt,note):
    if not note:raise ValueError('拒收必须记录原因')
    take=RUN/f'frame-{i:02d}'/f'{attempt:02d}';qa=read(take/'qa.json')
    qa['visual_verdict']='rejected';qa['issues'].append('视觉拒收：'+note);save(take/'qa.json',qa)
    meta=read(take/'meta.json');meta['status']='agent_rejected';meta['visual_reason']=note;save(take/'meta.json',meta)
    print(f'帧{i}第{attempt}次已拒收；不安装。')

def candidate(attempt):
    review=read(WORK/'review.json');qa=read(RUN/'frame-03'/f'{attempt:02d}'/'qa.json')
    selection=json.loads(json.dumps(review));selection['frames']['3']={'attempt':attempt,
       'image':(RUN/'frame-03'/f'{attempt:02d}'/'native.png').relative_to(ROOT).as_posix(),
       'agent_accepted':False,'user_approved':False,'note':'三次生成后仍无合格支撑脚过渡，仅供失败审片证据'}
    selection.update(motion_verdict='blocked',user_approved=False,installed=False)
    folder=WORK/'candidate';folder.mkdir(parents=True,exist_ok=True)
    save(folder/'selection.json',selection)
    atlas=Image.new('RGBA',(192*8,192))
    for i in range(8):atlas.alpha_composite(Image.open(ROOT/selection['frames'][str(i)]['image']).convert('RGBA'),(i*192,0))
    atlas.save(folder/'atlas.png')
    save(folder/'clip.json',{'texture':str((folder/'atlas.png').resolve()),'cell':192,'anchor_y':184,
      'rects':[[i*192,0,192,192] for i in range(8)],'ticks':read(WORK/'method.json')['ticks'],'loop':True,
      'motion_review':{'verdict':'blocked','runtime_fallback':True,'reason':'帧3仍不合格，主游戏仅通过显式审片参数临时读取候选图集；不安装'}})
    print('已生成未通过候选的审片图集，不改assets或生产状态。')

def preview(use_candidate=False):
    review=read(WORK/'candidate/selection.json' if use_candidate else WORK/'review.json');indices=sorted(map(int,review['frames']))
    frames={i:Image.open(ROOT/review['frames'][str(i)]['image']).convert('RGBA') for i in indices}
    contact=Image.new('RGB',(384*4,424*2),'#202632');d=ImageDraw.Draw(contact)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    for i,f in frames.items():
        x=i%4*384;y=i//4*424;big=f.resize((384,384),Image.Resampling.NEAREST)
        contact.paste(big,(x,y+36),big);d.text((x+10,y+5),f'帧{i} {PHASES[i]}',font=font,fill='white')
    contact.save(OUT/'contact.png')
    if indices!=list(range(8)):return
    method=read(WORK/'method.json');ticks=method['ticks']
    gif=[];durations=[];elapsed=0
    for _ in range(3):
        for i,f in frames.items():
            im=Image.new('RGB',(768,768),'#202632');big=f.resize((768,768),Image.Resampling.NEAREST);im.paste(big,(0,0),big)
            gif.append(im)
            next_elapsed=elapsed+ticks[i]*1000/60
            durations.append((round(next_elapsed/10)-round(elapsed/10))*10);elapsed=next_elapsed
    gif_name='walk-back-3-cycles.gif' if method.get('action')=='walk_back' else 'walk-forward-3-cycles.gif'
    gif[0].save(OUT/gif_name,save_all=True,append_images=gif[1:],duration=durations,loop=0,disposal=2,optimize=False)
    seam=Image.new('RGB',(768*4,832),'#202632');d=ImageDraw.Draw(seam)
    for col,i in enumerate([6,7,0,1]):
        big=frames[i].resize((768,768),Image.Resampling.NEAREST);seam.paste(big,(768*col,64),big)
        d.text((768*col+16,16),f'帧{i} {PHASES[i]}'+(' ← 循环接头' if i==0 else ''),font=font,fill='white')
    seam.save(OUT/'seam-6-7-0-1.png')

def measure(use_candidate=False):
    review=read(WORK/'candidate/selection.json' if use_candidate else WORK/'review.json');boxes=read(WORK/'foot-boxes.json');rows=[]
    diagnostic=Image.new('RGB',(384*4,424*2),'#202632');draw=ImageDraw.Draw(diagnostic)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
    for i in range(8):
        f=Image.open(ROOT/review['frames'][str(i)]['image']).convert('RGBA')
        rgba=np.asarray(f);rgb=rgba[:,:,:3].astype(int);visible=rgba[:,:,3]>0
        neutral=(rgb.max(2)-rgb.min(2)<32)&(rgb.mean(2)>110)&visible
        row={'frame':i};debug=Image.new('RGBA',f.size)
        for side in ['near','far']:
            x0,y0,x1,y1=boxes[str(i)][side]
            area=np.zeros(visible.shape,dtype=bool);area[y0:y1,x0:x1]=True
            all_silver=neutral&area
            selected=all_silver&((rgb.mean(2)>=184) if side=='near' else (rgb.mean(2)<184))
            ys,xs=np.where(selected)
            if len(xs)<6:raise ValueError(f'帧{i}{side}缺少可分辨的银色脚部像素，不能用计划坐标补测')
            fraction=int(selected.sum())/max(1,int(all_silver.sum()))
            row[side]={'x':round(float(xs.mean()),3),'y':round(float(ys.mean()),3),'pixels':len(xs),
                       'silver_role_fraction':round(fraction,3),'box':[x0,y0,x1,y1]}
            color=(53,183,224,255) if side=='near' else (200,121,58,255)
            for x,y in zip(xs,ys):debug.putpixel((int(x),int(y)),color)
        rows.append(row)
        x=i%4*384;y=i//4*424
        big=f.resize((384,384),Image.Resampling.NEAREST);diagnostic.paste(big,(x,y+32),big)
        overlay=debug.resize((384,384),Image.Resampling.NEAREST);diagnostic.paste(overlay,(x,y+32),overlay)
        draw.text((x+8,y+5),f'帧{i} 近{row["near"]["x"]:.1f} / 远{row["far"]["x"]:.1f}',font=font,fill='white')
    method=read(WORK/'method.json')
    near=[r['near']['x'] for r in rows];far=[r['far']['x'] for r in rows]
    ticks=method['ticks'];ages=[0]
    for t in ticks:ages.append(ages[-1]+t)
    contact_drift={};world_speed=method.get('world_speed',method['walk_speed'])
    for side,values,ids in [('near',near,[0,1,2,3,4]),('far',far,[4,5,6,7,8])]:
        world=[round(values[j%8]+ages[j]*world_speed,3) for j in ids]
        contact_drift[side]={'samples':world,'range':round(max(world)-min(world),3),
          'local_deltas':[round(values[(j+1)%8]-values[j%8],3) for j in ids[:-1]],
          'world_deltas':[round(world[j+1]-world[j],3) for j in range(4)]}
    result={'schema':1,'source':'实际透明192×192候选帧的脚部银色像素；矩形仅限定脚部区域，不提供横坐标；近亮银>=184、远暗银<184',
            'blocked_candidate':review.get('motion_verdict')=='blocked','frame_3_approved':review['frames']['3'].get('agent_accepted',False),
            'frames':rows,'ticks':ticks,'walk_speed':method['walk_speed'],'world_speed':world_speed,'action':method.get('action','walk_forward'),'contact_drift':contact_drift,
            'near_far_correlation':float(np.corrcoef(near,far)[0,1]),'user_approved':False,
            'frame_hold_note':'按ticks逐帧定格，图表比较换帧时的累计脚位；脚部中心含脚跟至脚尖滚动误差，不代表逐tick脚部插值。'}
    save(OUT/'foot-measurements.json',result);diagnostic.save(OUT/'foot-masks.png')
    print(json.dumps({'near':near,'far':far,'contact_drift':contact_drift,'correlation':result['near_far_correlation']},ensure_ascii=False))

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','generate','extract','accept','reject','candidate','preview','measure']);p.add_argument('--frame',type=int,choices=range(8));p.add_argument('--attempt',type=int);p.add_argument('--note',default='');p.add_argument('--candidate',action='store_true')
    args=p.parse_args()
    if args.command=='prepare':prepare()
    elif args.command=='generate':generate(args.frame,args.note)
    elif args.command=='extract':extract(args.frame,args.attempt)
    elif args.command=='accept':accept(args.frame,args.attempt,args.note)
    elif args.command=='reject':reject(args.frame,args.attempt,args.note)
    elif args.command=='candidate':candidate(args.attempt)
    elif args.command=='preview':preview(args.candidate)
    elif args.command=='measure':measure(args.candidate)

if __name__=='__main__':main()

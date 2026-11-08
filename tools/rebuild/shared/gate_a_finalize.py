"""验收门A：仅调整冲刺顺序和区域RGB；从主游戏录屏取审片证据。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import argparse
import hashlib
import io
import json; json = _LayoutJson
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = _LayoutProjectPath(_layout_root)
WORK = ROOT / 'art/fighters/ultraman/stage2/legacy/gate_a_final'
OUT = ROOT / 'reports/review/2026-10-21-gate-a-final'
MANIFEST = ROOT / 'assets/fighters/ultraman/animations/manifest.json'
ACTIONS = ['idle', 'light1', 'light2', 'light3', 'takeoff', 'flip_forward', 'land',
           'diagonal_heavy', 'launcher', 'chase_takeoff', 'chase_light1']
DASH_ORDER = [0, 1, 7, 5, 4, 2, 8, 9, 10]
NAMES = {'idle':'待机', 'walk_forward':'前走', 'walk_back':'后走', 'dash_start':'冲刺起步',
         'dash':'冲刺跑步', 'dash_stop':'冲刺刹停', 'light1':'轻击一段', 'light2':'轻击二段',
         'light3':'轻击三段', 'takeoff':'起跳', 'flip_forward':'前空翻', 'land':'落地',
         'diagonal_heavy':'斜跳重击', 'launcher':'升击', 'chase_takeoff':'追击跳', 'chase_light1':'空中轻击'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def font(size=22):
    return ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', size)


def texture(clip):
    return ROOT / clip['texture'].removeprefix('res://')


def snapshot():
    assert not WORK.exists(), '保留已有记录，禁止覆盖调色前素材'
    WORK.mkdir(parents=True)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = read(MANIFEST)
    save(WORK/'manifest-before.json', manifest)
    for action in ACTIONS:
        clip = manifest['clips'][action]
        folder = WORK/'before'/action
        folder.mkdir(parents=True)
        shutil.copy2(texture(clip), folder/'atlas.png')
        atlas = Image.open(texture(clip)).convert('RGBA')
        for i, (x,y,w,h) in enumerate(clip['rects']):
            atlas.crop((x,y,x+w,y+h)).save(folder/f'frame-{i}.png')
        inspect(action)


def inspect(action):
    frames = list((WORK/'before'/action).glob('frame-*.png'))
    sheet = Image.new('RGB', (576*min(4,len(frames)), 620*((len(frames)+3)//4)), '#202632')
    for i in range(len(frames)):
        im = Image.open(WORK/'before'/action/f'frame-{i}.png').convert('RGBA')
        cell = Image.new('RGB', (576,620), '#202632')
        cell.paste(im.resize((576,576),Image.Resampling.NEAREST),(0,44),im.resize((576,576),Image.Resampling.NEAREST))
        draw = ImageDraw.Draw(cell)
        draw.text((8,4),f'{action} #{i}',font=font(),fill='white')
        for n in range(20,192,20):
            draw.line([(n*3,44),(n*3,620)],fill='#375262')
            draw.line([(0,44+n*3),(576,44+n*3)],fill='#375262')
            draw.text((n*3,44),str(n),font=font(14),fill='#52dbe8')
            draw.text((0,44+n*3),str(n),font=font(14),fill='#52dbe8')
        sheet.paste(cell,(i%4*576,i//4*620))
    folder=WORK/'inspect';folder.mkdir(exist_ok=True)
    sheet.save(folder/f'{action}.png')


def components(mask):
    """4连通；按行列扫描编号，使像素分块和JSON可重复。"""
    labels=np.zeros(mask.shape,dtype=np.int32)
    result=[]
    for y,x in np.argwhere(mask):
        if labels[y,x]:continue
        index=len(result)+1;stack=[(int(x),int(y))];points=[];labels[y,x]=index
        while stack:
            px,py=stack.pop();points.append((px,py))
            for nx,ny in [(px-1,py),(px+1,py),(px,py-1),(px,py+1)]:
                if 0<=nx<mask.shape[1] and 0<=ny<mask.shape[0] and mask[ny,nx] and not labels[ny,nx]:
                    labels[ny,nx]=index;stack.append((nx,ny))
        result.append(points)
    return labels,result


def rle(mask):
    result=[]
    for y,row in enumerate(mask):
        start=None
        for x,value in enumerate(list(row)+[False]):
            if value and start is None:start=x
            if not value and start is not None:result.append([y,start,x]);start=None
    return result


def build():
    raise RuntimeError('永久停用远侧区域换色；只允许GPT生成时绘制远侧暗色，后处理只做整图色板量化。')


def dash_build():
    m=read(WORK/'manifest-before.json');clip=m['clips']['dash'];atlas=Image.open(texture(clip)).convert('RGBA')
    before=WORK/'before/dash';before.mkdir(parents=True,exist_ok=True)
    if not (before/'atlas.png').exists():shutil.copy2(texture(clip),before/'atlas.png')
    atlas=Image.open(before/'atlas.png').convert('RGBA');output=Image.new('RGBA',atlas.size)
    frames=[]
    for col,old in enumerate([3,2,1,0]):
        x,y,w,h=clip['rects'][old];im=atlas.crop((x,y,x+w,y+h));frames.append(im);output.paste(im,(col*192,0))
    folder=WORK/'after/dash';folder.mkdir(parents=True,exist_ok=True);output.save(folder/'atlas.png')
    for i,im in enumerate(frames):im.save(folder/f'frame-{i}.png')
    a=read(ROOT/'art/fighters/ultraman/stage2/legacy/dash_single/foot-measurements.json')
    first=a['feet']['5']['x']+7*6;second=a['feet']['2']['x']+13*6
    deviation=round(second-first-36,3)
    assert abs(deviation)<=8
    save(WORK/'dash-reorder.json',{'source_frames':DASH_ORDER,'ticks':[2,2,3,3,3,3,2,2,2],
         'generation_requests':0,'total_requests_carried':19,'first_landing':{'id':5,'side':'far','age':7,'foot_x':a['feet']['5']['x'],'world_x':round(first,3)},
         'second_landing':{'id':2,'side':'near','age':13,'foot_x':a['feet']['2']['x'],'world_x':round(second,3)},
         'expected_distance':36,'actual_world_distance':round(second-first,3),'deviation':deviation,'limit':8,'self_check_passed':True})
    (OUT/'landing-distance.md').write_text(f'# 冲刺换序后着地间距\n\n先着地B原5：累计7tick，远脚x{a["feet"]["5"]["x"]:.3f}，世界x{first:.3f}。\n\n后着地A原2：累计13tick，近脚x{a["feet"]["2"]["x"]:.3f}，世界x{second:.3f}。\n\n两次相隔6tick，身体36px；世界间距{second-first:.3f}px，偏差{deviation:+.3f}px，符合±8px。时长不变，不新增生成。\n',encoding='utf-8')


def install():
    archive=(ROOT.parent/'UFEneo_archive/2026-10-21/gate-a-before-far-color-final').resolve()
    assert archive.is_relative_to((ROOT.parent/'UFEneo_archive').resolve()) and not archive.exists()
    assert sha(MANIFEST)==sha(WORK/'manifest-before.json'), '正式清单已有其他改动，不能覆盖'
    archive.mkdir(parents=True);shutil.copy2(MANIFEST,archive/'manifest.json')
    m=read(MANIFEST);records=[]
    for action in ACTIONS+['dash']:
        clip=m['clips'][action];asset=texture(clip).resolve()
        assert asset.is_relative_to(ROOT)
        dest=archive/'assets'/action/'atlas.png';dest.parent.mkdir(parents=True)
        records.append({'action':action,'old_sha256':sha(asset),'archive':str(dest)})
        shutil.move(str(asset),str(dest))
        old_processed=(ROOT/f'art/fighters/ultraman/stage2/legacy/processed/{action}').resolve()
        assert old_processed.is_relative_to(ROOT)
        if old_processed.exists():
            target=archive/'processed'/action;target.parent.mkdir(exist_ok=True)
            assert target.resolve().is_relative_to(archive)
            shutil.move(str(old_processed),str(target))
        old_processed.mkdir()
        after=WORK/'after'/action
        if action!='dash':
            atlas=Image.new('RGBA',Image.open(dest).size)
            for i,(x,y,w,h) in enumerate(clip['rects']):atlas.paste(Image.open(after/f'frame-{i}.png'),(x,y))
            atlas.save(after/'atlas.png')
        shutil.copy2(after/'atlas.png',asset);shutil.copy2(asset,old_processed/'atlas.png')
        for i in range(len(clip['rects'])):shutil.copy2(after/f'frame-{i}.png',old_processed/f'frame-{i}.png')
        clip['atlas_sha256']=sha(asset)
        if action=='dash':
            clip['global_frames']=[7,5,4,2];clip['sequence_frames']=[2,3,4,5]
            clip['motion_review'].update(reason='用户基本通过后换序：腾空B→着地B→腾空A→着地A，各3tick；世界着地间距偏差−6.881px符合±8px，等最终审片。',pose_set_user_approved=True)
            clip['sequence_review']='art/fighters/ultraman/stage2/legacy/gate_a_final/dash-reorder.json'
        else:
            clip['color_review']={'source':'art/fighters/ultraman/stage2/legacy/gate_a_final/regions/'+action,
                                  'geometry_and_alpha_unchanged':True,'generation_requests':0,
                                  'ambiguous_blocks':'每帧JSON记录；无法判断的重叠块保持原色。'}
        save(old_processed/'qa.json',{'action':action,'installed':True,'image_sha256':clip['atlas_sha256'],
             'generation_requests':0,'geometry_and_alpha_unchanged':True,
             'review':'art/fighters/ultraman/stage2/legacy/gate_a_final/REVIEW.md','user_approved':False})
        records[-1]['new_sha256']=clip['atlas_sha256']
    save(MANIFEST,m);save(WORK/'archive.json',{'root':str(archive),'records':records})
    save(WORK/'manifest-after.json',m)
    print('已安装区域调色与冲刺新顺序，旧图及processed已工程外归档。')


def contact(frames,labels,path,columns=3):
    sheet=Image.new('RGB',(768*min(columns,len(frames)),832*((len(frames)+columns-1)//columns)),'#202632')
    for i,(im,label) in enumerate(zip(frames,labels)):
        large=im.resize((768,768),Image.Resampling.NEAREST);x=i%columns*768;y=i//columns*832
        sheet.paste(large,(x,y+64),large);ImageDraw.Draw(sheet).text((x+8,y+8),label,font=font(25),fill='white')
    sheet.save(path)


def contacts():
    m=read(MANIFEST);all_frames={}
    for action,clip in m['clips'].items():
        atlas=Image.open(texture(clip)).convert('RGBA')
        frames=[atlas.crop((x,y,x+w,y+h)) for x,y,w,h in clip['rects']];all_frames[action]=frames
        contact(frames,[f'{NAMES[action]} #{i} · {clip["ticks"][i]}tick' for i in range(len(frames))],OUT/f'{action}-contact.png')
    frames=all_frames['dash_start']+all_frames['dash']+all_frames['dash_stop']
    labels=['起步蓄势','起步蹬地','腾空B · 远腿前','着地B · 远腿前','腾空A · 近腿前','着地A · 近腿前','刹停踩地','刹停后仰','收回护架']
    ticks=[2,2,3,3,3,3,2,2,2]
    contact(frames,[f'{i} {n} · {ticks[i]}tick' for i,n in enumerate(labels)],OUT/'dash-nine-contact.png')
    slow=[];durations=[];elapsed=0
    for i,im in enumerate(frames):
        large=im.resize((768,768),Image.Resampling.NEAREST);page=Image.new('RGB',(768,832),'#202632')
        page.paste(large,(0,64),large);ImageDraw.Draw(page).text((8,8),f'1/4速度 · {i} {labels[i]}',font=font(25),fill='white');slow.append(page)
        nxt=elapsed+ticks[i]*4000/60;durations.append((round(nxt/10)-round(elapsed/10))*10);elapsed=nxt
    slow[0].save(OUT/'dash-quarter-speed.gif',save_all=True,append_images=slow[1:],duration=durations,disposal=2,optimize=False)
    for name in ['dash-nine-contact.png','dash-quarter-speed.gif']:shutil.copy2(OUT/name,WORK/name)
    transitions=[
        '近腿在前，后脚继续蹬地，前倾加深。','后方远腿向前摆，进入远腿在前的腾空B。',
        '同一条远腿保持在前，从腾空到触地。','远腿着地后回收，近腿摆到前方进入腾空A。',
        '同一条近腿保持在前，从腾空到触地。','近脚继续踩地减速，未再交换为另一脚。',
        '近脚保持前方，身体后仰，两臂收回。','脚位保持前后，回到护架，随后接待机。']
    save(WORK/'dash-adjacency-review.json',{'source_frames':DASH_ORDER,'generation_requests':0,
        'transitions':[{'from':i,'to':i+1,'observation':v} for i,v in enumerate(transitions)],
        'remaining':'起步肩臂细节和腾空A略半正面为用户已接受的旧稿；9帧不补蹬地，不改轮廓。'})


def runtime():
    """证据均截自正式主游戏影片；trace决定取哪一帧。"""
    def grab(movie, number):
        raw=subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-vf',f'select=eq(n\\,{number})',
                            '-frames:v','1','-f','image2pipe','-c:v','png','-'],capture_output=True,check=True).stdout
        return Image.open(io.BytesIO(raw)).convert('RGB')
    def crop(movie, row):
        x=(row['x']-row['camera_x']+320)*2
        assert 192<=x<=1088
        return grab(movie,row['movie_frame']).crop((x-192,240,x+192,624))
    movie=OUT/'dash-reordered-runtime.mp4'
    rows=read(movie.with_name(movie.stem+'-trace.json'))['trace'];first={}
    for row in rows:
        if row['state']!='dash':continue
        offset=0 if '/dash_start/' in row['texture'] else 6 if '/dash_stop/' in row['texture'] else 2
        i=offset+row['sprite_index']
        first.setdefault(i,row)
    assert set(first)==set(range(9))
    labels=['起步蓄势','起步蹬地','腾空B','着地B','腾空A','着地A','刹停踩地','刹停后仰','收回护架']
    sheet=Image.new('RGB',(1152,1260),'#202632');draw=ImageDraw.Draw(sheet)
    for i,row in first.items():
        x=i%3*384;y=i//3*420;sheet.paste(crop(movie,row),(x,y+36))
        draw.text((x+8,y+5),f'{i} {labels[i]} · 影片{row["movie_frame"]}',font=font(18),fill='white')
    sheet.save(OUT/'dash-runtime-contact.png')
    movie=OUT/'color-switches-runtime.mp4';rows=read(movie.with_name(movie.stem+'-trace.json'))['trace']
    def action(row):
        if row['state']=='walk':return '前走' if '/walk_forward/' in row['texture'] else '后走'
        if row['state']=='dash':return '冲刺'
        if row['move']=='light1':return '轻击'
        return '待机' if row['state']=='idle' else row['state']
    required=[('待机','前走'),('前走','待机'),('待机','后走'),('后走','待机'),('待机','冲刺'),('冲刺','待机'),('待机','轻击')]
    found={}
    for before,after in zip(rows,rows[1:]):
        pair=(action(before),action(after))
        if pair in required:found.setdefault(pair,(before,after))
    assert set(found)==set(required),f'切换截图缺失：{set(required)-set(found)}'
    sheet=Image.new('RGB',(768,420*len(required)),'#202632');draw=ImageDraw.Draw(sheet);switches=[]
    for j,pair in enumerate(required):
        before,after=found[pair];y=j*420
        sheet.paste(crop(movie,before),(0,y+36));sheet.paste(crop(movie,after),(384,y+36))
        draw.text((8,y+5),f'{pair[0]} → {pair[1]} · 影片{before["movie_frame"]} → {after["movie_frame"]}',font=font(18),fill='white')
        switches.append({'from':pair[0],'to':pair[1],'before_frame':before['movie_frame'],'after_frame':after['movie_frame'],
                         'before_texture':before['texture'],'before_index':before['sprite_index'],
                         'after_texture':after['texture'],'after_index':after['sprite_index']})
    sheet.save(OUT/'color-switches-contact.png')
    movie=OUT/'gate-a-final-40s-v2.mp4';rows=read(movie.with_name(movie.stem+'-trace.json'))['trace']
    sheet=Image.new('RGB',(1280,390*6),'#202632');draw=ImageDraw.Draw(sheet);sections=[]
    for part in range(6):
        pair=[]
        for boxes in [False,True]:
            candidates=[r for r in rows if r['section']==part and r['boxes']==boxes]
            if part==2:candidates=[r for r in candidates if r['state']=='dash' and '/dash/' in r['texture']]
            if part>=3:
                move=['light3','diagonal_heavy','chase_light1'][part-3]
                candidates=[r for r in candidates if r['move']==move]
            assert candidates
            row=candidates[len(candidates)//2];pair.append(row['movie_frame'])
            im=grab(movie,row['movie_frame']);im.save(OUT/f'group-{part+1}-{"boxes" if boxes else "clean"}.png')
            x=640 if boxes else 0;y=390*part
            sheet.paste(im.resize((640,360),Image.Resampling.NEAREST),(x,y+30))
            draw.text((x+8,y+4),f'第{part+1}组 · {"后半F1" if boxes else "前半"} · 影片{row["movie_frame"]}',font=font(18),fill='white')
        section=[r for r in rows if r['section']==part]
        sections.append({'section':part,'start_frame':section[0]['movie_frame'],'end_trace_frame':section[-1]['movie_frame'],
                         'f1_start_frame':next(r['movie_frame'] for r in section if r['boxes']),'capture_frames':pair})
    sheet.save(OUT/'six-groups-runtime.png')
    save(WORK/'runtime-frames.json',{'dash':{str(i):{'movie_frame':r['movie_frame'],'source_id':DASH_ORDER[i],
         'texture':r['texture'],'sprite_index':r['sprite_index']} for i,r in first.items()},'switches':switches,'sections':sections,
         'source':'正式assets主游戏影片，未改写截图内角色位置、姿势或镜头；每组两半分别取帧。'})
    for name in ['dash-runtime-contact.png','color-switches-contact.png','six-groups-runtime.png']:
        shutil.copy2(OUT/name,WORK/name)


def qa():
    palette=set(map(tuple,read(ROOT/'content/fighters/ultraman/palette.json')['colors']));frames=[]
    for action in ACTIONS:
        for path in sorted((WORK/'after'/action).glob('frame-*.png')):
            before=np.array(Image.open(WORK/'before'/action/path.name).convert('RGBA'))
            after=np.array(Image.open(path).convert('RGBA'));visible=after[:,:,3]>0
            assert np.array_equal(before[:,:,3],after[:,:,3])
            assert set(np.unique(after[:,:,3]))<={0,255}
            assert set(map(tuple,after[visible,:3]))<=palette
            assert len(components(visible)[1])==1
            record=read(WORK/'regions'/action/path.with_suffix('.json').name)
            mask=np.zeros(visible.shape,bool)
            for y,x0,x1 in record['mask_rle_y_x0_x1']:mask[y,x0:x1]=True
            assert np.array_equal(np.any(before[:,:,:3]!=after[:,:,:3],axis=2),mask)
            frames.append({'action':action,'frame':int(path.stem.split('-')[-1]),'image_sha256':sha(path),
                'alpha_binary':True,'alpha_and_silhouette_identical':True,'palette_match':True,'one_component':True,
                'changed_pixels':int(mask.sum()),'ambiguous_kept':record['ambiguous_kept']})
        shutil.copy2(OUT/f'{action}-contact.png',ROOT/f'art/fighters/ultraman/stage2/legacy/processed/{action}/contact.png')
        existing=read(ROOT/f'art/fighters/ultraman/stage2/legacy/processed/{action}/qa.json')
        existing['prior_qa_archive']=str(Path(read(WORK/'archive.json')['root'])/'processed'/action/'qa.json')
        existing['frames']=[r for r in frames if r['action']==action]
        save(ROOT/f'art/fighters/ultraman/stage2/legacy/processed/{action}/qa.json',existing)
    save(WORK/'qa.json',{'installed':True,'generation_requests':0,'user_approved':False,'frames':frames,
        'dash':'dash-reorder.json；只换格次序，起步/刹停像素不改。','visual_review':'逐帧查看调色前后；头部、计时器、轮廓不在调色区域；颜色效果仍待用户最终复核。'})


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['snapshot','build','dash-build','install','contacts','runtime','qa'])
    args=parser.parse_args()
    if args.command=='snapshot':snapshot()
    if args.command=='build':build()
    if args.command=='dash-build':dash_build()
    if args.command=='install':install()
    if args.command=='contacts':contacts()
    if args.command=='runtime':runtime()
    if args.command=='qa':qa()

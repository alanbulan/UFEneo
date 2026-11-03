"""最小整帧流水线：复用条带生成/处理与逐帧extract；不会重置历史计数。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import argparse,json,sys,hashlib,shutil,re; json = _LayoutJson
from threading import Lock
ROOT=_LayoutProjectPath(_layout_root)
sys.path.insert(0,str(ROOT/'tools/rebuild'))
import art_phase2 as art
import process_phase2 as process
import head_size
import limb_color_qa
import island_qa
import body_length_qa
from qa_brake import Brake
from roster_production import single_writer
MUTEX=Lock()
BRAKE_PATH=ROOT/'art/production/quality-gate-v2/brake.json'

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))

def _quality_gate(folder,fighter,action):
    # 站高只查真正直立姿势。屈膝起落地、蹲姿和空中一律用头部；
    # 倾斜头部用实测眼/护耳轴，头冠差异只列人工复核，不硬拒收。
    q=read(Path(folder)/'head-qa.json')
    if action in ['takeoff','land','crouch','crouch_idle','stand'] or action.startswith(('air_','flip_','vertical_','diagonal_','chase_')) or action=='dive':
        if any(r.get('size_policy')=='standing_height' for r in q['frames']):raise ValueError('非直立帧不得用站高校验')
    if fighter=='ultraseven' and q['reference'].get('measurement_method')!='eye-ear-v2':
        raise ValueError('新赛文帧必须使用实测倾角的旋转不变头部标尺')
    head_size.validate(folder,fighter)
    island_qa.validate_folder(folder,fighter,action)
    body_length_qa.validate_folder(folder,fighter,action)
    limb_color_qa.validate_folder(folder,fighter,action)
    import loop_qa
    loop_qa.validate_folder(folder,fighter,action)
    if action in ['walk_forward','walk_back']:
        import walk_cycle_qa
        walk_cycle_qa.validate_folder(folder,fighter,action)
    if fighter=='ultraseven':
        import slugger_qa
        slugger_qa.validate(folder)

def quality_gate(folder,fighter,action):
    folder=Path(folder);brake=Brake(BRAKE_PATH)
    try:
        result=_quality_gate(folder,fighter,action)
    except ValueError as exc:
        reason=str(exc)
        check='head_size' if '头部' in reason or '头高' in reason or '站高' in reason else 'postprocess_color' if '明暗' in reason or '基线' in reason else 'walk_motion' if action.startswith('walk_') else 'resource_quality'
        q=read(folder/'head-qa.json')
        bad=set(map(int,re.findall(r'frame (\d+)',reason)))
        for row in q['frames']:
            if bad and row['frame'] not in bad:continue
            brake.record(f'{fighter}/{action}/frame-{row["frame"]:02}',{check:False},folder/row['image'])
            if not bad:break
        raise
    else:
        brake.record(f'{fighter}/{action}',dict(head_size=True,postprocess_color=True,walk_motion=True,resource_quality=True))
        return result
def generate(name):
    brief=read(ROOT/f'art/fighters/ultraman/stage2/legacy/requests/{name}.json')
    budget=brief.get('budget',{})
    journal=ROOT/budget.get('journal','art/shared/stage3/batches/requests.json')
    key=budget.get('action_key',name)
    with MUTEX,single_writer():
        records=read(journal) if journal.exists() else []
        folder=ROOT/brief.get('generation_dir',f'art/fighters/ultraman/stage2/generation/{name}')
        if len(list(folder.glob('[0-9][0-9]')))>=6:raise ValueError(name+'已用完6次，待人工')
        if sum(r.get('action_key',r['action'])==key for r in records)>=6:raise ValueError(key+'已用完6次，待人工')
        records.append({'action':name,'action_key':key,'number':len(records)+1,'status':'reserved'})
        art.save(journal,records);number=len(records)
    try:result=art.generate(name)
    except Exception as exc:result={'id':name,'status':'preflight_failed','reason':str(exc)}
    with MUTEX,single_writer():
        records=read(journal);records[number-1].update(result)
        records[number-1]['api_submitted']=bool(result.get('take') and (ROOT/result['take']/'meta.json').exists())
        art.save(journal,records)
    return result

def run(fighter,action,reuse=False,install=False):
    brake=Brake(BRAKE_PATH)
    if not reuse and brake.blocked(['head_size','postprocess_color','walk_motion' if action.startswith('walk_') else 'resource_quality']):
        return dict(action=action,status='待人工',reason='同一检查连续拒收三个不同帧，已暂停生成，详见诊断图',paused=brake.state['paused'])
    if fighter=='ultraseven':
        import stage4_ultraseven as seven
        if install:
            if not reuse:raise ValueError('赛文必须先生成并逐帧自检，--reuse --install只安装通过的成品')
            from ultraseven_install import install as install_seven
            return install_seven(action)
        if reuse:
            key='s4seven_'+action.replace('/','_')
            result=process.process(key)
            if result.get('status')!='blocked':
                import slugger_qa
                quality_gate(ROOT/f'art/fighters/ultraman/stage2/legacy/processed/{key}',fighter,action.split('/')[0])
            return result
        result=seven.generate(action)
        if result.get('status')!='blocked':
            quality_gate(ROOT/f'art/fighters/ultraman/stage2/legacy/processed/s4seven_{action.replace("/","_")}',fighter,action.split('/')[0])
        return result
    if fighter!='ultraman':raise ValueError('最小版本已有初代参数；杰顿尚无动作姿势配置，不能套用初代图')
    curated=ROOT/f'art/shared/stage3/batches/curated/{action}'
    if reuse and install and (curated/'curation.json').exists():
        quality_gate(curated,fighter,action)
        qa=read(curated/'visual-review.json');selection=read(curated/'curation.json')
        atlas=curated/'atlas.png';digest=hashlib.sha256(atlas.read_bytes()).hexdigest()
        if qa.get('pixel_issues') or qa.get('atlas_sha256')!=digest:raise ValueError('选稿或图集已变化，需重新质检/逐帧自检')
        dest=ROOT/f'assets/fighters/{fighter}/animations/{action}/atlas.png'
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()!=digest:raise ValueError('不同的旧正式图须先归档')
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():shutil.copy2(atlas,dest)
        path=ROOT/f'assets/fighters/{fighter}/animations/manifest.json';m=read(path)
        m['clips'][action]={'texture':'res://'+dest.relative_to(ROOT).as_posix(),'cell':192,'anchor_y':184,'rects':[[i*192,0,192,192] for i in range(len(selection['ticks']))],'ticks':selection['ticks'],'loop':selection['loop'],'atlas_sha256':digest,'curation':(curated/'curation.json').relative_to(ROOT).as_posix(),'motion_review':{'user_approved':False,'verdict':'screened_pending_user_review'}}
        art.save(path,m)
        return {'action':action,'status':'installed_pending_user_review','source':'curated','generation_requests':0}
    profile=read(ROOT/'art/shared/stage3/batches/profiles.json')[action]
    if profile['method']=='single':
        import walk_single as walk
        work=ROOT/_LayoutJson.path_text(f'art/phase3/{action}');work.mkdir(exist_ok=True)
        art.save(work/'poses.json',{'frames':[{'height':108,'foot_bottom':184} for _ in range(profile['frames'])]})
        walk.WORK=work;walk.RUN=ROOT/f'art/fighters/ultraman/stage2/generation/phase3_{action}'
        frames=[];head_frames=[];head_reference=None
        for i in range(profile['frames']):
            name=f'{action}-frame-{i}';result=generate(name) if not reuse else {}
            take=sorted((walk.RUN/f'frame-{i:02d}').glob('[0-9][0-9]'))[-1]
            walk.extract(i,int(take.name));qa=read(take/'qa.json')
            if qa['issues']:return {'action':action,'status':'blocked','issues':qa['issues']}
            hq=head_size.validate(take,fighter);head_reference=hq['reference']
            row=dict(hq['frames'][0]);row.update(frame=i,image=f'frame-{i}.png');head_frames.append(row)
            frames.append(take/'native.png')
        from PIL import Image
        out=ROOT/f'art/fighters/ultraman/stage2/legacy/processed/{action}';out.mkdir(exist_ok=True);atlas=Image.new('RGBA',(192*len(frames),192))
        for i,p in enumerate(frames):shutil.copy2(p,out/f'frame-{i}.png');atlas.paste(Image.open(p),(192*i,0))
        atlas.save(out/'atlas.png');art.save(out/'qa.json',{'action':action,'issues':[],'status':'screened_pending_user_review','method':'walk_single.extract'})
        art.save(out/'head-qa.json',{'reference':head_reference,'frames':head_frames,'issues':[]})
        result={'action':action,'status':'screened_pending_user_review'}
    else:
        if not reuse:
            result=generate(action)
            if result['status']!='generated':return result
        result=process.process(action)
    if result.get('status')!='blocked':quality_gate(ROOT/f'art/fighters/ultraman/stage2/legacy/processed/{action}',fighter,action)
    if install:
        out=ROOT/f'art/fighters/ultraman/stage2/legacy/processed/{action}';qa=read(out/'qa.json')
        quality_gate(out,fighter,action)
        if qa['issues'] or not (out/'visual-review.json').exists():raise ValueError('必须先完成像素与逐帧视觉自检，才能安装')
        dest=ROOT/f'assets/fighters/{fighter}/animations/{action}/atlas.png'
        if dest.exists():raise ValueError('旧正式图须先按规则归档，不覆盖')
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(out/'atlas.png',dest)
        path=ROOT/f'assets/fighters/{fighter}/animations/manifest.json';m=read(path)
        m['clips'][action]={'texture':'res://'+dest.relative_to(ROOT).as_posix(),'cell':192,'anchor_y':184,'rects':[[i*192,0,192,192] for i in range(profile['frames'])],'ticks':profile['ticks'],'loop':profile['loop'],'atlas_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'motion_review':{'user_approved':False,'verdict':'screened_pending_user_review'}}
        art.save(path,m)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('fighter');p.add_argument('--action',required=True);p.add_argument('--reuse',action='store_true');p.add_argument('--install',action='store_true');a=p.parse_args()
    print(json.dumps(run(a.fighter,a.action,a.reuse,a.install),ensure_ascii=False))

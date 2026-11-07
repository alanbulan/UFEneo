"""阶段4试生产定稿：单次请求先记账，复用GPT客户端与sprite-gen像素还原。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
from types import SimpleNamespace
from datetime import datetime, timezone
import argparse
import hashlib
import json; json = _LayoutJson
import sys
from contextlib import contextmanager
from PIL import Image, ImageDraw, ImageFont
from production_io import read_json
import numpy as np

ROOT = _LayoutProjectPath(_layout_root)
SKILL = Path.home()/'.codex/skills/sprite-gen'
sys.path[:0] = [str(ROOT/'tools'), str(SKILL)]
import art.pipeline as art
from sprite_gen.frames.extract import (detect_pixel_grid, grid_snap_downscale,
    _kcentroid_downscale, build_shared_palette, apply_palette, binarize_alpha)

RUN = ROOT/'art/production/stage4-pilot'
LEDGER = RUN/'ledger.json'
OUT = ROOT/'reports/review/2026-10-22-stage4-pilot-models'
SPECS = {'ultraseven': (192,144,None,'赛文奥特曼'), 'gomora': (256,192,None,'哥莫拉')}

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def read(path): return read_json(path)
def save(path, value):
    import time,os
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+f'.{os.getpid()}.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf-8')
    for attempt in range(100):
        try:temp.replace(path);break
        except PermissionError:
            if attempt==99:raise
            time.sleep(.02)
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

@contextmanager
def ledger_lock():
    import time,os
    lock=RUN/'.ledger.lock'
    for _ in range(1200):
        try:handle=lock.open('x',encoding='utf-8');break
        except FileExistsError:time.sleep(.05)
    else:raise ValueError('台账写锁超时，先核对写入进程')
    try:
        handle.write(str(os.getpid()));handle.close();yield
    finally:lock.unlink()

def init():
    if LEDGER.exists(): return
    save(LEDGER, {'schema':1, 'started':now(), 'authorization':'2026-10-22用户授权两角色试生产；本轮仅定稿，每个定稿最多6次',
        'limits':{'per_asset':6},
        'counting':'每次真实提交前落账；失败、Alpha拒收、远端未知均计数；无自动重试，不按改名重置',
        'billing':'保存接口返回的usage及请求标识；无价格或账单时不虚报金额', 'requests':[]})

def generate(fighter):
    init()
    # 排他锁保护预算检查与单条原子写入，禁止并发超额；异常退出遗留锁需先核对台账。
    lock = RUN/'request.lock'
    with lock.open('x',encoding='utf-8') as handle:
        handle.write(now())
    try:
        ledger = read(LEDGER)
        rows = ledger['requests']
        own = [r for r in rows if r['fighter']==fighter]
        model = [r for r in own if r['action']=='model']
        if len(model)>=ledger['limits']['per_asset']:
            raise ValueError('定稿同一素材已达6次，标待人工；不得改名重算')
        brief_path = RUN/fighter/'brief.json'
        brief = read(brief_path)
        assert brief['quality']=='high' and brief['asset_kind']=='character'
        refs = [ROOT/p for p in brief['references']]
        assert all(p.is_file() for p in refs)
        args = SimpleNamespace(model=None, reference=refs, dry_run=False,
            out=ROOT/'art/shared/generation/stage4-pilot'/fighter/'model'/f'{len(model)+1:02}'/'raw.png')
        if brief.get('mask'):args.mask=ROOT/brief['mask']
        # 本地参数/凭据预检不计为网络请求；凭据永不记录。
        art.image_fields(brief)
        url, token = art.credentials()
        if not token or not url.startswith('https://'): raise ValueError('本机GPT Image配置不可用')
        args.out.parent.mkdir(parents=True,exist_ok=True)
        snapshot=args.out.parent/'brief.json'
        snapshot.write_bytes(brief_path.read_bytes())
        transport = art.request_api
        row = None
        def tracked_request(*a, **kw):
            nonlocal row
            row = {'fighter':fighter,'action':'model','category':'定稿','sequence':len(model)+1,
                'ledger_sequence':len(rows)+1,'size':brief['size'],'quality':'high',
                'model':brief['model'],'input_image_count':len(refs),'submitted_at':now(),
                'result':'submitted_remote_unknown','output':args.out.relative_to(ROOT).as_posix(),
                'brief':snapshot.relative_to(ROOT).as_posix(),'brief_sha256':digest(snapshot),
                'usage':None,'provider_id':None,'actual_cost':None}
            rows.append(row);save(LEDGER,ledger)
            result = transport(*a,**kw)  # 客户端retry=0，绝不自动补发。
            row['result']='response_received_pending_local_qa';row['response_at']=now()
            row['usage']=result.get('usage')
            row['provider_id']=result.get('id',result.get('request_id'))
            row['provider_created']=result.get('created')
            save(LEDGER,ledger)
            return result
        art.request_api=tracked_request
        try:
            art.generate_image(args,brief,'阶段4定稿候选；未审、不接入、不生成动作')
            row['result']='alpha_accepted_pending_model_review'
        except Exception as exc:
            if row is not None:
                row['result']='alpha_rejected' if 'Alpha QA failed' in str(exc) else 'failed_or_remote_unknown'
                row['error_type']=type(exc).__name__
            raise
        finally:
            art.request_api=transport
            if row is not None:
                row['finished_at']=now();save(LEDGER,ledger)
    finally:
        lock.unlink() # 仅删除本工具创建的临时互斥标记，不删除工程素材。


def generate_action(fighter,action,brief_path):
    """固定资产键预记账；网络期间不占写锁，不同动作可独立生成。"""
    from contextlib import contextmanager
    import time,os
    @contextmanager
    def write_lock():
        lock=RUN/'.ledger.lock'
        for _ in range(600):
            try:handle=lock.open('x',encoding='utf-8');break
            except FileExistsError:time.sleep(.05)
        else:raise ValueError('台账写锁超时，先核对写入进程')
        try:
            handle.write(str(os.getpid()));handle.close();yield
        finally:lock.unlink()
    brief_path=Path(brief_path);brief=read(brief_path)
    registry_path=ROOT/brief.get('asset_registry','art/fighters/ultraseven/stage4/pilot/ultraseven-first/asset-registry.json')
    registry=read(registry_path)
    if fighter not in registry.get('fighters',['ultraseven']):raise ValueError('角色不在本轮用户授权的固定清单')
    if action not in registry['assets']:raise ValueError('不在固定资产清单，禁止改名重算')
    if registry.get('assets_by_fighter') and action not in registry['assets_by_fighter'].get(fighter,[]):raise ValueError('该固定帧不在这个角色的授权范围')
    assert brief['asset_key']==action and brief['quality']=='high' and brief['fighter']==fighter
    refs=[ROOT/p for p in brief['references']]
    if not all(p.is_file() for p in refs):raise ValueError('缺少附件')
    art.image_fields(brief);url,token=art.credentials()
    if not token or not url.startswith('https://'):raise ValueError('本机配置不可用')
    revision=brief.get('identity_revision','original')
    with write_lock():
        ledger=read(LEDGER);rows=ledger['requests'];asset=[r for r in rows if r['fighter']==fighter and r['action']==action]
        series=brief.get('attempt_series','original')
        if series!='original':
            authorization=ledger.get('method_authorizations',{}).get(series,{})
            if action not in authorization.get('assets',[]) or fighter not in authorization.get('fighters',['ultraseven']):raise ValueError('没有用户授权的新方法计数，不得重置')
        own=[r for r in asset if r.get('identity_revision','original')==revision and r.get('attempt_series','original')==series]
        limit=ledger.get('method_authorizations',{}).get(series,{}).get('per_asset',ledger['limits']['per_asset'])
        if len(own)>=limit:raise ValueError(f'固定素材本授权方法已达{limit}次，待人工')
        revision_path='' if revision=='original' else revision+'/'
        args=SimpleNamespace(model=None,reference=refs,dry_run=False,out=ROOT/f'art/shared/generation/stage4-pilot/{fighter}/{revision_path}{action}/{len(asset)+1:02}/raw.png')
        if args.out.exists() or args.out.with_suffix('.metadata.json').exists():raise ValueError('计数对应输出已存在，先审计台账，禁止覆盖原请求')
        args.out.parent.mkdir(parents=True,exist_ok=True)
        snapshot=args.out.parent/'brief.json';snapshot.write_bytes(brief_path.read_bytes());frozen=[]
        for i,path in enumerate(refs):
            dest=args.out.parent/'inputs'/f'{i}{path.suffix}';dest.parent.mkdir(exist_ok=True);dest.write_bytes(path.read_bytes());frozen.append(dest)
        args.reference=frozen
        if brief.get('mask'):
            mask=ROOT/brief['mask'];args.mask=args.out.parent/'inputs/edit-mask.png';args.mask.write_bytes(mask.read_bytes())
        row=dict(fighter=fighter,action=action,category=registry['assets'][action]['category'],batch=registry.get('batch','ultraseven-first'),asset_registry=registry_path.relative_to(ROOT).as_posix(),identity_revision=revision,revision_sequence=len(own)+1,sequence=len(asset)+1,ledger_sequence=len(rows)+1,size=brief['size'],quality='high',model=brief['model'],input_image_count=len(refs),inputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=digest(p)) for p in frozen],submitted_at=now(),result='submitted_remote_unknown',output=args.out.relative_to(ROOT).as_posix(),brief=snapshot.relative_to(ROOT).as_posix(),brief_sha256=digest(snapshot),usage=None,provider_id=None,actual_cost=None)
        row.update(attempt_series=series,category=brief.get('category',row['category']))
        if brief.get('mask'):row['edit_mask']=dict(path=args.mask.relative_to(ROOT).as_posix(),sha256=digest(args.mask))
        rows.append(row);save(LEDGER,ledger)
    def update():
        with write_lock():
            ledger=read(LEDGER);assert ledger['requests'][row['ledger_sequence']-1]['output']==row['output'];ledger['requests'][row['ledger_sequence']-1]=row.copy();save(LEDGER,ledger)
    transport=art.request_api
    def tracked(*a,**kw):
        response=transport(*a,**kw)
        row.update(result='response_received_pending_local_qa',response_at=now(),usage=response.get('usage'),provider_id=response.get('id',response.get('request_id')));update();return response
    art.request_api=tracked
    try:
        art.generate_image(args,brief,'赛文定稿5首批；未经逐帧自检不得安装');row['result']='alpha_accepted_pending_action_review'
    except Exception as exc:
        row.update(result='alpha_rejected' if 'Alpha QA failed' in str(exc) else 'failed_or_remote_unknown',error_type=type(exc).__name__);raise
    finally:
        art.request_api=transport;metadata=args.out.with_suffix('.metadata.json')
        if not metadata.exists():metadata=args.out.parent/'rejected'/metadata.name
        if metadata.exists():row['output_size']=read(metadata)['dimensions']
        row['finished_at']=now();update()
    return row


def process(fighter, take):
    cell,height,_,_ = SPECS[fighter]
    source = ROOT/'art/shared/generation/stage4-pilot'/fighter/'model'/f'{take:02}'/'raw.png'
    raw = Image.open(source).convert('RGBA');art.require_transparency(raw)
    bounds=raw.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
    crop = raw.crop(bounds)
    pitch,phase = detect_pixel_grid(crop,max_pitch=12)
    factor = max(1,round(min(pitch)))
    # sprite-gen的grid_edges在pitch=1时是整图单格；无网格检测值必须跳过这步，仍走kCentroid。
    logical = grid_snap_downscale(crop,factor,phase=phase) if factor>1 else crop.copy()
    if logical.height < height:
        raise ValueError('检测网格还原后低于目标高度，不放大伪造像素密度')
    logical = _kcentroid_downscale(logical,round(logical.width*height/logical.height),height)
    binarize_alpha(logical)
    # 固定材质亮暗对 + 从生成图聚类的补色，共32色。额头光束灯保留，赛文无胸前计时器。
    material = ([(225,232,234),(172,187,194),(117,137,149),(72,89,104),
                 (225,46,49),(179,27,38),(125,23,37),(81,22,34),
                 (251,237,179),(206,185,112),(38,173,118),(29,39,51)] if fighter=='ultraseven' else
                [(171,121,76),(134,87,53),(102,66,43),(70,46,34),
                 (206,161,103),(160,116,72),(118,83,51),(82,57,38),
                 (225,199,147),(176,146,100),(245,198,61),(35,29,27)])
    palette = material + [c for c in build_shared_palette([logical],20) if tuple(c) not in material]
    logical = apply_palette(logical,palette)
    # 以两脚接地段的中心为根点；不以含长尾的整体包围盒中心假冒脚底锚点。
    mask=np.asarray(logical)[:,:,3]>0
    columns=np.flatnonzero(mask[-6:].any(axis=0))
    spans=[]
    start=previous=int(columns[0])
    for x in columns[1:]:
        if x>previous+1:spans.append([start,previous]);start=int(x)
        previous=int(x)
    spans.append([start,previous])
    foot_center=round(sum((a+b)/2 for a,b in spans)/len(spans))
    # 哥莫拉保留256px纵向规格，横向透明画布扩至384；尾巴、身高和像素都不缩放。
    width=384 if fighter=='gomora' else cell
    offset = (width//2-foot_center,cell-8-height)
    if offset[0]<4 or offset[0]+logical.width>width-4:raise ValueError('轮廓超出扩展方案，禁止压扁')
    canvas = Image.new('RGBA',(width,cell))
    canvas.alpha_composite(logical,offset)
    folder = ROOT/'art/model_sheets'/fighter
    folder.mkdir(parents=True,exist_ok=True)
    out = folder/'model-native.png';canvas.save(out)
    canvas.resize((width*4,cell*4),Image.Resampling.NEAREST).save(folder/'model-reference-x4.png')
    colors = np.asarray(canvas); visible = colors[colors[:,:,3]>0,:3]
    qa = {'fighter':fighter,'candidate_take':take,'status':'pending_user_review','source':source.relative_to(ROOT).as_posix(),
        'source_sha256':digest(source),'native_sha256':digest(out),'canvas':[width,cell],'height':height,
        'bounds':list(canvas.getbbox()),'foot_anchor':[width//2,cell-8],
        'source_foot_contact_spans':spans,'foot_center_before_padding':foot_center,
        'measured_pitch':list(pitch),'phase':list(phase),'grid_factor':factor,
        'pipeline':'sprite-gen detect_pixel_grid → grid_snap_downscale → kCentroid → binary alpha → shared palette → canvas',
        'opaque_colors':len(np.unique(visible,axis=0)), 'alpha_values':np.unique(colors[:,:,3]).tolist(),
        'canvas_extension_required':width!=cell,'automatic_checks_are_not_user_approval':True}
    assert qa['opaque_colors']<=32 and qa['alpha_values']==[0,255]
    save(folder/'qa.json',qa)
    near = material[0:2]+material[4:6]
    far = material[2:4]+material[6:8]
    save(ROOT/'content/fighters'/fighter/'palette.json',{'status':'candidate_pending_review','max_colors':32,
        'colors':[list(c) for c in palette],'source_sha256':digest(source),
        'side_view_roles':{'policy':'固定侧视，远侧手臂和腿统一暗一档；亮暗身份不因前后换腿互换；头部/躯干/发光体不随肢体压暗',
            'near_side':{'limb_rgb':near},'far_side':{'limb_rgb':far},
            'mapping':[{'near':a,'far':b} for a,b in zip(near,far)],'status':'定稿候选已测色，待用户复核'}})
    print(json.dumps(qa,ensure_ascii=False))

def review():
    OUT.mkdir(parents=True,exist_ok=True)
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
    entries = [('ultraman','初代奥特曼'),('zetton','宇宙恐龙杰顿'),('ultraseven','赛文奥特曼（待审）'),('gomora','哥莫拉（待审）')]
    # 同一原生像素倍率与脚底基线，不按透明画布缩放人物。
    contact = Image.new('RGBA',(1536,320),(33,40,53,255));draw=ImageDraw.Draw(contact)
    for index,(fighter,name) in enumerate(entries):
        path = ROOT/('assets/fighters' if index<2 else 'art/model_sheets')/fighter/'model-native.png'
        image = Image.open(path).convert('RGBA')
        x=index*384+(384-image.width)//2;y=270-(image.height-8)
        contact.alpha_composite(image,(x,y))
        draw.text((index*384+8,286),name,font=font,fill='white')
        image.resize((image.width*4,image.height*4),Image.Resampling.NEAREST).save(OUT/f'{fighter}-x4.png')
    contact.convert('RGB').save(OUT/'models-same-scale.png')
    contact.resize((3072,640),Image.Resampling.NEAREST).convert('RGB').save(OUT/'models-same-scale-x2.png')

def summary():
    ledger=read(LEDGER);rows=ledger['requests'];result={}
    for fighter in SPECS:
        own=[r for r in rows if r['fighter']==fighter]
        def failed(r):return 'rejected' in r['result'] or r['result'] in ['failed_or_remote_unknown','submitted_remote_unknown']
        result[fighter]={'used':len(own),'unlimited':True,
            'by_category':{category:sum(r['category']==category for r in own) for category in ['定稿','移动','站立','下蹲','动作','特效']},
            'retry_requests':sum(r['sequence']>1 for r in own),'failed_rejected_or_unknown':sum(failed(r) for r in own),
            'retry_or_failed_cross_count':sum(r['sequence']>1 or failed(r) for r in own),
            'current_batch':{'used':sum(r.get('batch')=='ultraseven-first' for r in own)},
            'input_tokens':sum((r.get('usage') or {}).get('input_tokens',0) for r in own),
            'output_tokens':sum((r.get('usage') or {}).get('output_tokens',0) for r in own)}
    result['combined']={'used':len(rows),'unlimited':True,'counting_only':True,
        'billing_status':'用户确认生图免费；只记录次数和usage供参考，无总量上限'}
    save(RUN/'summary.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['init','generate','process','review','summary'])
    parser.add_argument('--fighter',choices=SPECS);parser.add_argument('--take',type=int,default=1);a=parser.parse_args()
    if a.command=='init':init()
    elif a.command=='generate':generate(a.fighter)
    elif a.command=='process':process(a.fighter,a.take)
    elif a.command=='review':review()
    else:summary()

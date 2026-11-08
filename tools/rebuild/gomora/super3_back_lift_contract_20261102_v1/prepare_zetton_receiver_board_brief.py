"""准备杰顿四完整相板brief与离线计划；无API调用、预算操作、Godot或产品写入。"""
from pathlib import Path
import sys
import hashlib,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4]
ART=ROOT/'art/fighters/zetton/stage5/gomora-super3-back-lift-receiver-20261102-v1'
REQUEST=ART/'board-2x2/request-001'
REPORT=ROOT/'reports/review/2026-11-02/gomora-super3-zetton-receiver-brief-v1'
CONTRACT=ROOT/'reports/review/2026-11-02/gomora-super3-zetton-minimal-receiver-source-v1/minimal-four-whole-frame-contract.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,data):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  assert read(p)==data,'既存准备文件不同，禁止覆盖'
  return
 with p.open('x',encoding='utf8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')

PROMPT='''绘制一张1024×1024真正透明PNG的2×2独立整帧受方动作板。恰好四个完整的初代1966宇宙恐龙杰顿，每个512×512方格仅一只，依次为左上A、右上B、左下C、右下D。不要画格线、字母或编号。四格每一格都是你重新绘制的独立完整人物，不是把一个姿势复制旋转、镜像、拉伸或移动，不是分件拼肢，不是同一身体只动一条手臂。所有肩、肘、腕、胸、髋、膝、踝和头饰须在各相协调改变。

附件1为本人已装原生像素定稿，附件2为本人相同定稿的干净完整高分源；两张都只确定身份、身体比例、完整配色和像素画风，不是所需动作。不得照抄站姿。最终四格都只画杰顿本人，不画哥莫拉、对手、背部支架、垫子、平台、地面、影子、绳索、手、骨架或任何特效。承重点在人物的腹腰下侧，通过本人自然身体曲线表达，不把一个物体画进身体。不得把对手或支撑物烘焙进人物图。

统一固定真侧视格斗镜头，不改变远近透视、不转相机、不画正面或三分之四视角。A/B/C本地方向均朝右：完整头在右、双足在左，胸腹面向下方，背面向上方；胸前橙黄发光体随本人前侧结构向下，不可把橙色胸腹朝天的仰卧图冒充趴伏。D仍保持同一观察侧，从该俯伏自然转入向后翻落，保持近远肢体身份不对调。

身份只用初代杰顿：高挑黑色长头、两根完整米白弯触角、唯一竖长橙色面部发光体、胸腹的橙黄发光体、黑甲壳白斑、米白分节肢体和黑色五指手足。无人类眼睛、嘴、红纹、蓝灯、尾巴或奥特曼头盔。两只完整手和两条完整腿，不多肢、不断腕、不把手藏成无法区分的黑块。近侧整臂整腿保持明亮米白234/220/200与213/198/179，黑手脚66/66/68；远侧另一整臂整腿由你直接画为暗米灰167/151/134与150/136/121，远黑手足38/38/42，交叉处以清楚深像素轮廓分开，不只在远腿加一点阴影。人物天然连续皮套/怪兽皮肤和本人甲壳结构，去掉玩具球关节、圆盘轴、插接缝、螺丝孔、支架和塑料高光。

保持同一个本人的骨长和头身比：游戏本人原生站高165–166像素含完整触角。本板每格按本人的原生整人2倍绘制，等效直立身高330–332源像素；俯伏改变姿势包络，不缩人物骨长来等高。横伏完整头角至脚尖宜在380–432源像素长度范围，至少保留每格四边40源像素真正透明空间。四格使用同一人体比例、同一像素密度，任何角尖、手指或脚尖均不能贴边或跨格。不能把附件中664像素高的4倍参考直接缩小塞满每格；目标是2倍而非4倍。全板正好1024方图，每格正好512方格，不画更多小人，不加第五相，不在空隙加残影。

左上A——斜俯接背缓冲：完整被动受方，头向右、双脚向左。胸腹朝下，头胸比髋稍低，躯干在水平线下倾约15–25度，腹腰下方开始承受托力；颈肩连续，头不是折在胸前。近臂从肩自然垂到前下方张掌，远臂略后下垂且完整可辨。双腿自然滞后，一膝稍弯、另一腿稍伸，脚尖自然下落；不是主动飞踢、游泳、双足站地或双手撑地。整人姿势表达从空中斜落到腹腰接住的缓冲。

右上B——横伏负重：独立重新画完整杰顿，不旋转A。胸腹面向下、躯干接近水平，腹腰作为中部支撑，肩胸与头、髋与双腿在支撑两侧自然下垂。头仍在右，双足在左；近、远两臂从肩自然下垂、手掌被动张开，两个膝踝和黑足都完整。腰腹适度柔软下凹承重，不能画板直僵尸、仰卧、跪姿、贴地压扁或一只手撑地的侧躺。

左下C——随背挺起抬升：独立完整新姿势，不旋转B。腹腰仍承重，胸肩及头随支撑面改变而抬高，胸躯从B的水平改为头向右上约20–30度，髋腿被动滞后向左下垂。近、远手臂都因抬升而自然后摆、屈肘，双膝踝随重心变化，不能照抄B的四肢或仅改单手。胸腹仍总体朝下，头部和触角不穿过肩胸，不拉长脖子/腿。

右下D——离背后翻起相：独立完整的新受方过渡，不复制旋转C。腹腰刚离开支撑，头从右上弧向右下，髋抬高，双腿从左下被动抬向左上；头低于髋、腿高于髋，但尚未成为完全倒立。躯干从胸朝下转向可见侧面，胸肩髋连续扭转，两只手被动分开屈肘，双腿不同幅度屈伸，表达离背后将进入头下脚上的后翻。不要画主动翻筋斗、攻击、挺直倒立或仰面静躺。此格要能接上既有完整倒立被后抛姿势，不能在这一格再画另一只倒立人物。

四个完整人物都采用现装2D硬边像素画风、有限色像素簇、清楚阶梯外轮廓和自然体积，不要照片、写实皮套纹理、3D渲染或平滑插画。透明背景，真正PNG Alpha，无棋盘格、白底、灰底、绿底、地面或投影。所有动作来自本作被投配对编排，不是官方招式海报，不画任何说明文字。'''

def main():
 assert not (REQUEST/'before-submit.json').exists() and not (REQUEST/'candidate.png').exists()
 REPORT.mkdir(parents=True,exist_ok=True)
 refs=[ROOT/'assets/fighters/zetton/model-native.png',ROOT/'art/fighters/zetton/stage3/legacy/zetton1/model-reference.png']
 frozen={p:sha(p) for p in [CONTRACT,*refs]}
 contract=read(CONTRACT)
 brief=dict(schema=2,id='zetton_gomora_super3_back_lift_receiver_board4_20261102',fighter='zetton',specific_version='初代1966杰顿',
   stage=5,action='gomora_super3_back_lift_receiver_independent_board4_v1',asset_kind='character',
   size='1024x1024',quality='high',background='transparent',model='gpt-image-2.5-sunburst',
   route='tools/art/pipeline.py.generate_image only; root owns existing official route/budget/POST',
   art_source='api_planned_not_submitted',references=[rec(p) for p in refs],prompt=PROMPT,
   reference_attachment_semantics=['附件1：已装256方图整人，仅本人身份/配色/像素风格','附件2：本人干净1024整源，仅同一身份/比例；源内人物是4倍，不照抄站姿或4倍尺寸'],
   contract=rec(CONTRACT),layout=dict(columns=2,rows=2,cell=[512,512],frame_order=['A','B','C','D'],
       rects=[[0,0,512,512],[512,0,512,512],[0,512,512,512],[512,512,512,512]],min_clear_border_per_cell=40),
   phases=contract['generation_candidate']['frames'],planned_source_to_native_scale=[1,2],
   planned_native_cell=[256,256],native_standing_anatomical_height=[165,166],
   per_cell_bbox_fit=False,per_frame_scale=False,offline_rotation_or_mirroring=False,
   submitted=False,installed=False,user_approved=False,root_brief_review_required_before_post=True,
   budget_reserved_by_this_preparation=False,preserve_old_runtime_until_all_new_frames_ready=True)
 bp=REQUEST/'brief.json';save(bp,brief)
 save(REQUEST/'reference-provenance.json',dict(references=[dict(index=i+1,**rec(p),image_size=list(Image.open(p).size),
      note=brief['reference_attachment_semantics'][i]) for i,p in enumerate(refs)],
      prompt_does_not_use_paths_as_images=True,client_resolves_real_image_bytes=True,reference_count=2))
 offline=dict(brief=rec(bp),source_cells=brief['layout']['rects'],only_after_root_returned_board_acceptance=True,
  first_checks=['核原单终态/费用/metadata与provider原件，不重发POST','核1024归一化图和provider尺寸关系，保存完整源SHA',
    '逐格根实际看完整四人，A/B/C确胸腹向下，D确独立后翻起相，无对手/拼件/格线',
    '逐格四边至少40源像素透明，中央横/竖缝两边均40透明，不跨格，不裁角手足',
    '实际Alpha透明，四格均完整；不能仅凭文件RGBA声称合格','在高分源核本人头长/躯干/四肢，不按横躺bbox等高或把166压成150'],
  proposed_processing=['精确512整格裁取，不裁bbox，不旋转、镜像或变形','经项目forge_backend，整格统一1/2到256，真二值Alpha；同动作共用倍率',
    '用本人现装palette，RGB兼容量化，只整图调色，不做远侧区域换色',
    '只整图平移注册；实际腹腰受力面/双臂足/头角逐相读点后再提原生根，当前没有授权抓点',
    '全相与本人18相配对完整Alpha页：当前空中→A→B→C→D→既有倒立/落地，源相号保留',
    '只有根接受读点、完整配对与真实输入回放后才考虑产品接线；本离线计划不创建产品或运行槽'],
  source_to_native_scale=[1,2],no_native_frame_created=True,no_processing_run=True,grip=None,waist=None,
  root_registration_authorized=False,root_pairing_accepted=False,root_install_authorized=False)
 save(REPORT/'offline-plan.json',offline)
 # Free existing whole-pose landing alternative: never crop/rotate a fighter into another posture.
 mp=ROOT/'assets/fighters/zetton/animations/manifest.json';m=read(mp);cells=[]
 for key,index in [('thrown_back',3),('thrown_forward',2),('thrown_forward',3),('down',0),('down',1),('defeat',3)]:
  c=m['clips'][key];ap=ROOT/c['texture'].removeprefix('res://');x,y,w,h=c['rects'][index]
  im=Image.open(ap).convert('RGBA').crop((x,y,x+w,y+h));anchor=c.get('anchors',[])[index] if c.get('anchors') else [int(c['cell'])//2,int(c['anchor_y'])]
  cells.append(dict(clip=key,sprite=index,atlas=rec(ap),rect=[x,y,w,h],anchor=anchor,alpha_bbox=im.getbbox(),image=im))
 page=Image.new('RGB',(768,870),'#242934');d=ImageDraw.Draw(page)
 for i,item in enumerate(cells):
  left=(i%2)*384;top=(i//2)*290;im=item['image'];ox=int(round(left+192-item['anchor'][0]));oy=int(round(top+24+248-item['anchor'][1]))
  page.paste(im,(ox,oy),im);d.text((left+4,top+6),f"{item['clip']}:{item['sprite']}  FULL CELL 1:1 / common root",fill='white')
  d.line((left+2,top+24+248,left+382,top+24+248),fill='#426c65')
 pp=REPORT/'existing-whole-landing-options-native.jpg';page.save(pp,quality=85,optimize=True)
 assert pp.stat().st_size<=150000
 for item in cells:del item['image']
 landing=dict(manifest=rec(mp),whole_source_comparison=rec(pp),cells=cells,
   preferred_existing_candidate=[dict(raw_ticks=[44,47],pose='thrown_back',sprite=0),
     dict(raw_ticks=[48,49],pose='thrown_back',sprite=1),dict(raw_ticks=[50,51],pose='thrown_forward',sprite=2),
     dict(raw_ticks=[52,59],pose='thrown_forward',sprite=3,impact_first_tick_only=True),
     dict(raw_ticks=[60,71],pose='down',sprite='沿既有down状态消费')],
   rationale='用已存在完整thrown_forward[2→3]承接后翻到展开着地，避开thrown_back[3]172宽短姿直接跳到down204宽；forward[3]215宽与down204宽差约5.1%，但bbox不是骨长，不据此判通过。',
   edge_boundary='down格264宽且最右列有Alpha，下一列是透明；触格边不等于已证脚尖被裁。先核完整原源和轮廓。若脚尖完整，可仅把整格原像素和原根搬到更宽透明画布作离线注册候选，尺度/人形不动；若真缺轮廓，回到本人旧down干净整源免费重新整帧处理，不拼补脚尖。',
   original_down_whole_sheet=rec(ROOT/'art/fighters/zetton/stage2/generation/phase3_defense/down/01/raw.png'),
   no_default_down_replaced=True,no_new_image_request_for_landing=True,actual_pairing_accepted=False,
   boundary='仅既有独立整相组合候选。defeat[3]只作完整体量对照，不接入活体受方。若forward→down仍明显跳变则保留未装，不自动改通用down/核心或加吸附。')
 save(REPORT/'existing-landing-bridge-plan.json',landing)
 py=sys.executable
 dry=[py,'tools/art/pipeline.py','concept','--brief',bp.relative_to(ROOT).as_posix(),'--out',(REQUEST/'candidate.png').relative_to(ROOT).as_posix()]
 for p in refs:dry+=['--reference',p.relative_to(ROOT).as_posix()]
 dry+=['--dry-run']
 submit=[py,'tools/rebuild/shared/root_serial_image_request_20261101.py',bp.relative_to(ROOT).as_posix(),
   '--purpose','杰顿本人四个独立完整背掀受方相候选；根已审brief后最后一单，保全原单、不自动重发，未获产品安装许可']
 save(REPORT/'commands-not-executed.json',dict(working_directory=str(ROOT),safe_offline_dry_run_argv=dry,
   root_only_submit_argv=submit,submit_command_executed=False,budget_reservation_performed=False,
   root_only_submit_note='仅根审brief与参考后执行；沿现有budget客户端保守占10，不另写API代码、不并发、不自动重发。'))
 save(REPORT/'prepared-request-index.json',dict(brief=rec(bp),prompt_utf8_sha256=hashlib.sha256(PROMPT.encode('utf8')).hexdigest(),
   reference_provenance=rec(REQUEST/'reference-provenance.json'),references=[rec(p) for p in refs],
   references_exact_client_keys=all(set(r)=={'path','sha256'} for r in brief['references']),
   offline_plan=rec(REPORT/'offline-plan.json'),landing_plan=rec(REPORT/'existing-landing-bridge-plan.json'),
   source_unchanged=all(sha(p)==v for p,v in frozen.items()),post_sent=False,godot_run=False,runtime_changed=False))
 (REPORT/'README.md').write_text('''# 杰顿四独立整相板：可审brief，未提交

正式草稿：art/fighters/zetton/stage5/gomora-super3-back-lift-receiver-20261102-v1/board-2x2/request-001/brief.json。

references仅path+sha256，实际附件为本人256方图已装定稿与本人1024干净原源，不拿提示词路径冒充图片。prompt逐格规定A斜俯接背、B胸腹横伏负重、C随背抬升、D离背后翻；每格独立完整两臂两腿/双角，不复制旋转、镜像或拼件。每格512，四边40透明，原生165/166等效2倍330–332源像素，整板后统一1/2处理；不bbox等高，不压到150。只有本人，不画对手/支架/地面/FX。

离线顺序与不装条件见offline-plan.json。commands-not-executed.json提供项目客户端安全dry-run和根独占提交argv；本准备工具无网络/预算入口，未执行提交命令、未占额。

着地免费候选改用既有完整thrown_back[0→1]接thrown_forward[2→3]展开落地，再接旧down，所有完整格原生同比例排在existing-whole-landing-options-native.jpg。forward末格宽215、down宽204，避免从back末格172直接换宽；这仍须高分骨尺与实际配对核验，不能bbox相近就判过。down触格边目前只证明边缘有Alpha，不能先说脚尖已裁；完整原源保留。完整脚尖可只搬整格到更宽透明画布保原像素/根；真缺轮廓则回旧完整原源免费重新处理，绝不补脚或新增收费请求。当前未改通用down或任何产品文件。

来源、参考、prompt及brief SHA见prepared-request-index.json。候选root读点/配对/安装门均false；根负责最后一单预算与POST。
''',encoding='utf8')
 print(bp)

if __name__=='__main__':main()

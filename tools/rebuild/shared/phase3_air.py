"""阶段三跳跃/移动批次。复用已有条带生成、像素还原和安装流程。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import argparse,copy,hashlib,json,math,shutil,sys; json = _LayoutJson
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=_LayoutProjectPath(_layout_root)
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/rebuild')]
import art.produce_character as producer
import process_phase2 as process
import phase3_standing as standing
WORK=ROOT/'art/shared/stage3/batches/air'
OUT=ROOT/'reports/review/2026-10-22-jump-air'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def font(n=24):return ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',n)
def base():return dict(head=(100,52),neck=(98,72),hip=(94,120),shoulder_back=(90,78),shoulder_front=(104,78),elbow_back=(117,98),wrist_back=(128,79),elbow_front=(116,99),wrist_front=(132,80),knee_back=(76,149),ankle_back=(58,181),knee_front=(110,149),ankle_front=(130,181))
def pose(**kw):p=base();p.update(kw);return p
def air(**kw):return pose(knee_front=(114,138),ankle_front=(103,164),knee_back=(79,137),ankle_back=(66,160),**kw)
def spec(name,ticks,desc,poses,active=None,airborne=False,loop=False):return {'name':name,'ticks':ticks,'description':desc,'poses':poses,'active':active or {},'airborne':airborne,'loop':loop}

# 每帧完整关节仅是生图参考；命中末端须在最终成品上重新核对。
S={
'spin_heavy':spec('回旋后踢',[3,3,3,4,4,5,6],'先转身背对对手，再向右中段脚跟后踢。攻击格躯干背面红纹朝镜头、头回看右侧，整条腿水平踢出，以脚跟击中；不是直拳，也不是反手横扫。最后收腿转回右向格斗架势。',[
pose(),pose(head=(94,53),wrist_front=(88,86),wrist_back=(74,82)),pose(head=(86,56),knee_front=(116,116),ankle_front=(111,144),wrist_front=(74,91)),pose(head=(76,59),neck=(82,78),hip=(91,119),knee_front=(134,113),ankle_front=(172,112),wrist_front=(65,96),wrist_back=(78,75)),pose(head=(82,56),knee_front=(130,120),ankle_front=(154,119)),pose(knee_front=(114,132),ankle_front=(126,161)),pose()],{3:(172,112,14),4:(154,119,14)}),
'ranged_forward':spec('八分光轮举手甩掷',[3,3,4,4,4,4,4,6],'原剧八分光轮：右手从胸侧高举，张开的右掌明确高过头顶，掌上聚光轮；在头顶停留两格，再手臂向正右横向一甩，掷出圆盘，收回到格斗架势。不能是往前推掌。只画人物，光轮另做特效。',[
pose(),pose(elbow_front=(124,63),wrist_front=(127,40)),pose(elbow_front=(117,45),wrist_front=(116,18)),pose(elbow_front=(121,45),wrist_front=(123,18)),pose(elbow_front=(140,57),wrist_front=(165,68)),pose(elbow_front=(139,80),wrist_front=(170,87)),pose(elbow_front=(120,97),wrist_front=(138,104)),pose()],{4:(165,68,12)}),
'vertical_jump':spec('垂直跳上升顶点下落',[7,7,3,8,7],'垂直跳五相位：上升收膝、上升屈膝更紧、顶点舒展开双臂平衡、下落伸腿、落地前双腿向下准备缓冲。人物根点相同，实际整个人离地由游戏跳跃曲线负责，不在图里画地面。',[
air(),air(head=(99,58),hip=(94,124)),pose(knee_front=(115,141),ankle_front=(137,170),knee_back=(74,140),ankle_back=(51,169),wrist_front=(140,87),wrist_back=(69,87)),pose(knee_front=(110,147),ankle_front=(123,180),knee_back=(81,149),ankle_back=(69,178)),pose()],airborne=True),
'flip_back':spec('后跳空翻',[8,8,8,8],'面朝右起跳向左后撤的后空翻四相位：后仰收膝、头向左后倒翻、倒立蜷身、展开朝右准备落地。整帧重画，近远手脚身份不变。',[
air(head=(84,57),neck=(88,76)),pose(head=(49,102),neck=(69,106),hip=(112,111),knee_front=(133,81),ankle_front=(114,64),knee_back=(116,139),ankle_back=(91,143),elbow_front=(76,131),wrist_front=(89,142),elbow_back=(63,82),wrist_back=(87,75)),pose(head=(100,155),neck=(99,137),hip=(96,94),knee_front=(119,72),ankle_front=(137,90),knee_back=(76,76),ankle_back=(60,99),elbow_front=(125,121),wrist_front=(134,107),elbow_back=(76,117),wrist_back=(64,101)),air()],airborne=True),
'vertical_light':spec('垂直跳轻击',[3,3,4,8],'垂直跳短直拳：双腿收起悬空，近拳蓄势、向右短直拳、拳完全伸出、收拳，不能画成地面站立。',[
air(),air(elbow_front=(131,83),wrist_front=(151,78)),air(elbow_front=(140,80),wrist_front=(166,77)),air()],{2:(166,77,13)},True),
'vertical_heavy':spec('垂直跳下击',[3,3,4,4,7],'垂直跳重击向下：近肘先高举蓄力，近拳向右下方砸，攻击拳在髋膝高度，范围明显低于空中轻拳；双腿悬空。',[
air(elbow_front=(118,60),wrist_front=(118,36)),air(elbow_front=(137,79),wrist_front=(150,99)),air(elbow_front=(136,102),wrist_front=(158,130)),air(elbow_front=(125,99),wrist_front=(142,116)),air()],{2:(158,130,15)},True),
'diagonal_light':spec('斜跳膝撞',[3,3,5,9],'斜向前跳膝撞：抬近膝、近膝猛向右上顶、膝盖到对手胸腹前、收腿。大腿折起，脚始终收在膝下后方，不能变成伸直腿飞踢。',[
air(),pose(knee_front=(136,114),ankle_front=(115,146),knee_back=(77,141),ankle_back=(61,161)),pose(knee_front=(145,108),ankle_front=(128,139),knee_back=(77,141),ankle_back=(61,161)),air()],{2:(145,108,15)},True),
'air_crush':spec('空中双拳下砸',[2,2,3,3,4,6],'空中超重击：双拳从两侧举过头、两拳合拢蓄势、向右下双拳猛砸、双拳低至腰部、回收、准备落地；命中弹地。保持两个拳头，不能多手。',[
air(elbow_front=(118,55),wrist_front=(112,30),elbow_back=(86,53),wrist_back=(93,29)),air(elbow_front=(123,58),wrist_front=(132,43),elbow_back=(115,62),wrist_back=(126,45)),air(elbow_front=(137,91),wrist_front=(155,115),elbow_back=(127,93),wrist_back=(146,117)),air(elbow_front=(131,108),wrist_front=(142,139),elbow_back=(122,108),wrist_back=(135,140)),air(elbow_front=(119,99),wrist_front=(129,115)),air()],{2:(151,116,17),3:(140,139,17)},True),
'dive':spec('俯冲踢',[2,2,5,4,6],'向右下俯冲脚跟踢：先收膝，身体斜向前下、近腿沿右下对角线伸出，脚在身体前下方；保持斜下伸腿，随后屈膝准备落地。不是水平飞踢，也不是原地举腿。',[
air(),pose(head=(93,58),hip=(97,115),knee_front=(127,142),ankle_front=(153,177),knee_back=(76,130),ankle_back=(61,149)),pose(head=(83,61),neck=(88,78),hip=(105,118),knee_front=(135,146),ankle_front=(162,176),knee_back=(84,130),ankle_back=(68,148)),pose(head=(90,58),hip=(101,120),knee_front=(126,147),ankle_front=(151,178)),air()],{2:(162,176,14),3:(151,178,14)},True),
'air_pulse':spec('空中斜下光弹',[3,3,4,4,6],'悬空屈膝，右手掌收胸、斜向右下推出掌心、掌心瞄准右下45度发射、回收、准备落地。只画人物，光弹另用已有像素特效。',[
air(),air(elbow_front=(125,94),wrist_front=(140,112)),air(elbow_front=(132,102),wrist_front=(157,128)),air(elbow_front=(120,96),wrist_front=(138,105)),air()],{2:(157,128,12)},True),
'chase_light2':spec('空中轻击二段',[2,3,4,7],'追击空中轻击第二段：双腿收膝、远侧后手暗色拳从腰侧蓄势，转肩以远侧拳向右打出，再回收。和已通过近侧轻击第一段交替手，不能复用第一段。',[
air(),air(elbow_back=(130,89),wrist_back=(151,83)),air(elbow_back=(140,82),wrist_back=(166,79)),air()],{2:(166,79,13)},True),
'chase_end':spec('空中终结砸地',[2,2,3,3,4,6],'空中连段终结砸地：收膝，右拳高举蓄力，躯干向右前倾，右拳从上向下砸至膝下，单臂强力下劈，对手向下弹地；另一手护胸；最后伸腿向地面追击。和双拳下砸区别为单拳下劈。',[
air(),air(elbow_front=(117,53),wrist_front=(113,27)),air(head=(109,62),neck=(106,80),elbow_front=(139,96),wrist_front=(155,130)),air(head=(111,65),neck=(107,82),elbow_front=(130,115),wrist_front=(144,153)),pose(knee_front=(110,150),ankle_front=(125,182),knee_back=(80,149),ankle_back=(66,179)),pose()],{2:(155,130,17),3:(144,153,17)},True),
'dash_light':spec('冲刺拳',[2,2,4,4,8],'冲刺中向右突进近手直拳：身体明显前倾，蓄拳、近拳随前跨步打出、完全伸拳、刹住收拳、回格斗架势，可接轻击二段。',[
pose(head=(116,61),neck=(108,79)),pose(head=(118,62),elbow_front=(136,85),wrist_front=(154,80)),pose(head=(119,61),elbow_front=(145,82),wrist_front=(174,79),ankle_back=(42,178)),pose(elbow_front=(134,89),wrist_front=(148,85)),pose()],{2:(174,79,14)}),
'dash_heavy':spec('冲刺飞踢',[2,2,3,4,4,7],'冲刺中短跃飞踢：压低蹬地、抬近膝、身体前倾近腿向右水平伸直、近脚完全伸出、收腿落地、回护架。不同于斜跳飞踢，保持低空水平冲进。',[
pose(head=(110,65),hip=(96,131)),air(),pose(head=(104,62),knee_front=(134,123),ankle_front=(172,126),knee_back=(74,139),ankle_back=(56,159)),pose(head=(109,65),knee_front=(139,125),ankle_front=(176,128),knee_back=(78,137),ankle_back=(61,159)),air(),pose()],{2:(172,126,15),3:(176,128,15)}),
'backstep':spec('后撤步',[3,3,4,3,3],'面对右侧对手向左短后撤：略后仰收重心、后脚向左蹬撤、双脚小幅离地向后收、后脚先落地、回格斗架势。始终面向右不翻身，双拳护胸。',[
pose(head=(91,54),neck=(92,73)),pose(head=(88,58),hip=(92,123),knee_back=(68,149),ankle_back=(43,175)),air(head=(88,59),neck=(92,77)),pose(head=(93,57),knee_back=(75,148),ankle_back=(53,180)),pose()]),
'back_counter':spec('后撤反击',[2,2,3,4,4,7],'后撤步反击长踹：上身略后仰，抬近膝，近脚掌向右中段直蹬，脚跟伸到对手腹部，再收腿回防；与回旋后踢不同，全程面朝右不转背。',[
pose(head=(89,55)),pose(head=(86,58),knee_front=(126,119),ankle_front=(112,145)),pose(head=(83,57),knee_front=(135,124),ankle_front=(169,123)),pose(head=(86,57),knee_front=(135,122),ankle_front=(169,122)),pose(knee_front=(117,134),ankle_front=(125,161)),pose()],{2:(169,123,14),3:(169,122,14)}),
'dodge':spec('原地闪避',[3,3,3,3,3,3],'固定原地侧身闪避六相位：下沉、收肩躲闪、上身大幅向左后仰、最低闪避、回正、回护架；不改变身体根点，不画纵深移动，完整人物。',[
pose(),pose(head=(90,64),neck=(92,82),hip=(94,130)),pose(head=(73,74),neck=(81,91),hip=(93,135)),pose(head=(76,77),neck=(83,94),hip=(94,137)),pose(head=(89,65),neck=(92,83),hip=(94,129)),pose()]),
'dodge_counter':spec('闪避反击',[2,2,4,4,8],'闪避后反击短勾拳：低位闪身收近拳、从低向右上勾拳，近肘弯曲、拳打到右侧胸前，收手回防，不能画成水平直拳。',[
pose(head=(84,66),hip=(94,131),wrist_front=(104,120)),pose(head=(91,62),elbow_front=(120,116),wrist_front=(125,94)),pose(elbow_front=(134,104),wrist_front=(144,72)),pose(elbow_front=(123,101),wrist_front=(131,81)),pose()],{2:(144,72,15)})}

def prepare():
    OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    # 把上一批的用户通过事实写回对应正式清单；被拒收两招不标通过。
    mp=ROOT/'assets/fighters/ultraman/animations/manifest.json';m=read(mp)
    for action in standing.SELECT:
        if action not in ['spin_heavy','ranged_forward']:
            m['clips'][action]['motion_review']={'user_approved':True,'verdict':'user_approved_2026-10-22'}
    save(mp,m)
    for action,s in S.items():
        name='p3air_'+action;count=len(s['ticks']);cols=min(4,math.ceil(count/2));rows=2
        folder=ROOT/'art/shared/poses/templates/humanoid/air_batch'/name;folder.mkdir(parents=True,exist_ok=True)
        guide=Image.new('RGB',(cols*512,1024),'#f6f6f6');d=ImageDraw.Draw(guide)
        frames=[]
        for i,j in enumerate(s['poses']):
            ox=i%cols*512+64;oy=i//cols*512+64
            def xy(k):return (ox+j[k][0]*2,oy+j[k][1]*2)
            # 深棕远侧、蓝色近侧；窄侧身躯干，绝不作为成品渲染。
            d.line([xy(k) for k in ['shoulder_back','elbow_back','wrist_back']],fill='#9b6547',width=20)
            d.line([xy(k) for k in ['hip','knee_back','ankle_back']],fill='#9b6547',width=24)
            d.line([xy('neck'),xy('hip')],fill='#506070',width=33)
            d.line([xy(k) for k in ['hip','knee_front','ankle_front']],fill='#287eaf',width=24)
            d.line([xy(k) for k in ['shoulder_front','elbow_front','wrist_front']],fill='#287eaf',width=20)
            hx,hy=xy('head');d.ellipse((hx-17,hy-26,hx+17,hy+23),fill='#506070')
            frames.append({'joints':j,'ticks':s['ticks'][i],'height':0})
        guide.save(folder/'guide.png')
        provenance='通用动作参考格斗进化3 jump-detail-028 / run-cycle / walk-scan；侧视144像素关节为人工编排'
        if action=='ranged_forward':
            extraction=read(WORK/'reference/slash/rtmlib-keypoints.json')
            # 保留实际检测作为参考层：头顶举掌及横甩取原剧44/46/48/51；低置信度和镜头外腿明确不用。
            raw=extraction['records'];observation=Image.new('RGB',(4*512,512),'#f6f6f6');od=ImageDraw.Draw(observation)
            for n,rec in enumerate(raw[2:6]):
                p=rec['points'][0];origin=p[6]
                for chain in [[6,8,10],[5,7,9]]:
                    q=[(n*512+256-(p[k][0]-origin[0])*.9,200+(p[k][1]-origin[1])*.9) for k in chain]
                    od.line(q,fill='#9b6547' if chain[0]==5 else '#287eaf',width=16)
                od.text((n*512+20,460),Path(rec['source']).name,font=font(),fill='black')
            observation.save(WORK/'reference/slash/rtmlib-observed-arms.png')
            provenance='原剧16集slash-release-v001，已实际运行third_party/rtmlib指向的0.0.16 DWPose-s；记录在rtmlib-keypoints.json。44/46/48/51帧上肢有效，背部/镜头外腿不用；窄侧身、举掌高于头顶及完整下肢按用户要求人工侧视重编，未冒称自动提取全身。'
        save(folder/'poses.json',{'action':action,'template':'air_batch','cell':[192,192],'anchor':[96,184],'frames':frames,'source':provenance})
        prompt=(f'绘制附件同一个初代奥特曼C型【{s["description"]}】完整整帧像素动画。严格跟随姿势条顺序；蓝近/棕远只是参考，成品仍红银。'
          f'输出{cols}列2行、每格512×512，恰好{count}个完整人物，按行左到右，余格真透明。站立144原生像素即图上288像素，格内根点x256脚底y432。'
          '固定侧面朝右，窄胸单肩，躯干不转向镜头（回旋后踢允许转背）。头身比、花纹、面具、头鳍、眼睛、胸口蓝色计时器和定稿一致；计时器可被真实动作遮挡但不能乱移。'
          '远侧手臂与腿整条使用暗银169,167,170/144,137,140和暗红202,8,10，近侧亮银亮红，明暗身份不能随前后位置交换。附已通过压暗帧作色彩参考。'
          '透明背景，真正PNG Alpha，无地面投影格线文字编号残影速度线特效，不裁切任何头手脚；完整身体连贯，不多肢体、不断臂，像素块清楚。')
        refs=['art/fighters/ultraman/model/model-reference-x4.png',folder.relative_to(ROOT).as_posix()+'/guide.png','art/fighters/ultraman/stage2/legacy/gate_a_final/after/idle/frame-0.png']
        if action=='ranged_forward':refs+=['art/shared/stage3/batches/air/reference/slash/rtmlib-observed-arms.png','art/shared/references/motion/ultraman-1966/episode-16/slash-release-v001/frames/frame-046.png']
        save(ROOT/f'art/fighters/ultraman/stage2/legacy/requests/{name}.json',{'id':name,'template':'air_batch','frames':count,'ticks':s['ticks'],'loop':False,'columns':cols,'rows':rows,'size':f'{cols*512}x1024','guide':folder.relative_to(ROOT).as_posix()+'/guide.png','prompt':prompt,'reference_images':refs,'generation_dir':f'art/fighters/ultraman/stage2/generation/phase3_air/{action}','review_dir':OUT.relative_to(ROOT).as_posix(),'airborne':s['airborne'],'budget':{'journal':'art/shared/stage3/batches/air/requests.json','max_requests':70,'action_key':action}})
    save(WORK/'profiles.json',S)
    charge={'id':'p3air_fx_slash_charge','frames':4,'columns':2,'rows':2,'size':'1024x1024','asset_kind':'effect','generation_dir':'art/fighters/ultraman/stage2/generation/phase3_air/fx_slash_charge','reference_images':['assets/effects/slash/atlas.png'],'prompt':'绘制初代八分光轮在举过头顶的掌上由小变大旋转凝聚的像素特效，附件是正式飞行光轮形状和颜色。只画4个圆盘光轮特效，无人物无手无文字。2列2行每格512像素：第0格小型光轮直径约70像素，第1格中型约130，第2格完整约190，第3格完整约190且齿沿旋转相位不同。光轮白金亮边、淡青白芯、锋利齿边、侧视略扁的圆盘，轮廓像素阶梯清楚，真透明PNG Alpha，透明背景，无方形底色、无阴影、无烟雾、无游离粒子。所有完整圆盘在格中心。','budget':{'journal':'art/shared/stage3/batches/air/requests.json','max_requests':70,'action_key':'ranged_forward'}}
    save(ROOT/'art/fighters/ultraman/stage2/legacy/requests/p3air_fx_slash_charge.json',charge)
    save(WORK/'batch.json',{'request_limit':70,'per_action_limit':3,'actions':list(S),'old_batch_journal':'art/shared/stage3/batches/requests.json','reference':'reference/slash/rtmlib-keypoints.json'})
    print('本批姿势、来源和独立预算已准备')

def generate(action):
    name='p3air_'+action
    print(json.dumps(producer.generate(name),ensure_ascii=False),flush=True)
    if not action.startswith('fx_'):print(json.dumps(process.process(name),ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','generate']);p.add_argument('--action');a=p.parse_args()
    prepare() if a.command=='prepare' else generate(a.action)

"""只写杰顿四相板候选合同及来源结论，绝无请求提交。"""
from pathlib import Path
import json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'reports/review/2026-11-02/gomora-super3-zetton-minimal-receiver-source-v1'
def rec(s):
 p=ROOT/s
 return dict(path=s,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def read(s):return json.loads((ROOT/s).read_text('utf-8-sig'))
def save(name,data):
 with (OUT/name).open('x',encoding='utf8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
 manifest=read('assets/fighters/zetton/animations/manifest.json')
 def existing(key,index,role):
  c=manifest['clips'][key];p=c['texture'].removeprefix('res://');x,y,w,h=c['rects'][index]
  frame=Image.open(ROOT/p).convert('RGBA').crop((x,y,x+w,y+h))
  return dict(clip=key,sprite=index,source=rec(p),rect=[x,y,w,h],alpha_bbox=frame.getbbox(),role=role,
      whole_existing_pose=True,offline_rotation_or_mirror=False,pairing_accepted=False)
 reuse=[existing('thrown_back',i,role) for i,role in enumerate([
   'raw44–47：真正离背后完整倒立相，须由新D自然转入，不能提前当俯伏',
   'raw48–51：团身后翻下降',
   'raw52–55：首次背部触地；真实throw_slam唯一结算',
   'raw56–59：落地展开稳定'])]
 reuse.append(existing('down',0,'raw60以后旧倒地候选；当前实际bbox触右格边且比thrown_back末相宽，须根核过渡，不能默认为已齐'))
 phases=[
  dict(id='A',cell=[0,0,512,512],raw_ticks=[20,23],name='斜俯接背缓冲',
    body='受方本地方向朝右，头在右、足在左，胸腹朝下，躯干小幅前俯斜落；两臂由肩自然下垂张掌，两膝自然屈伸。腹腰开始承受背部托力，不是双足着地/跪撑。',
    purpose='衔接真实落向上背的当前空中整相；不能捕获前预摆，也不能凭新相先瞬移。'),
  dict(id='B',cell=[512,0,512,512],raw_ticks=[24,31],name='横伏负重',
    body='独立重新画完整身体；胸腹向下、躯干近水平，腹腰柔软承重，头与双脚各在腹腰两侧向下垂；两臂自然垂落，黑手不抓自己的身体。双触角完整不折断，不画地面撑手。',
    purpose='随俯负重/最低负重；与本人背坡实体接触，手脚不得穿本人。'),
  dict(id='C',cell=[0,512,512,512],raw_ticks=[32,35],name='随背挺起抬升',
    body='独立完整抬升整相；腹腰仍承重而胸肩随背坡抬高、髋腿滞后自然下垂，肩胸髋和双臂双腿共同改姿，不仅换一只手。保持头足/骨长与A/B同一杰顿。',
    purpose='提供负重到抬升的真实整人变化，不能旋转B冒充。'),
  dict(id='D',cell=[512,512,512,512],raw_ticks=[36,43],name='离背后翻起相',
    body='独立完整脱手过渡；腹腰离开支撑，头相对髋下沉、双腿抬起并被动展开，两臂失衡张开；胸由朝下转到侧面，开始后翻但尚未完全倒立，为既有thrown_back[0]预留自然衔接。',
    purpose='开始离背到抛出前的最低新相预算。持8tick仅是待审候选，若与本人多相/既有倒立跳变，不能据板齐宣布连续通过。')]
 sources=[
  'art/fighters/zetton/stage3/legacy/zetton1/model-reference.png',
  'assets/fighters/zetton/model-native.png',
  'assets/fighters/zetton/animations/manifest.json',
  'content/fighters/zetton/state_frames.json',
  'content/fighters/zetton/palette.json',
  'art/fighters/zetton/stage6/teo-capture-receiver-codex-20261029/production-contract.json',
  'art/fighters/ultraman-teo/stage6/capture-integration-codex-20261029/package-v1/receiver-zetton-clips.fragment.json',
  'art/fighters/ultraman-teo/stage5/motion-41236-codex-20261027/palm-contact-return-codex-20261028/target-waist-review-v1/read-only-index.json',
  'content/fighters/ultraman-taro/moves/special3.json',
  'art/fighters/ex_red_king/stage6/super2-grab-slam-20261101-v1/runtime-candidate-v1/integration-v2/hold-point-audit.json']
 contract=dict(schema=1,status='read_only_minimal_contract_pending_root_review_no_post',fighter='zetton',
   new_action_role='哥莫拉背掀震落专属被投受方；本作配对编排，不冒称原剧杰顿被哥莫拉此招投掷。',
   prior_actor_contract=rec('reports/review/2026-11-02/gomora-super3-back-lift-contract-v1/victim-path-contract.json'),
   first_pair_only=True,other_victims_not_covered=True,
   sources=[rec(p) for p in sources],
   actual_source_review=dict(teo_whole_originals='28张两轮，均直立/后仰包罩挣扎、悬空屈膝或复原，无横伏',
       runtime_extra='wake/roll/air_tech/air_rise/apex/fall/capture共49完整格，无胸腹横伏承重',
       historical='18张旧原图含rejected/被后续替换的thrown_back首稿；完整实看，只有倒立/团身/仰卧或起身，无俯伏承重',
       zetton_stage4='唯一现有zetton-counter-recovery为本人反击动作，排除攻击当受方',
       taro3='现装special3真实target仅grabbed[1,2]与thrown_forward[1,2,3]，无新杰顿专属俯伏源',
       teo_palm='target-waist目录明指现装grabbed/head-calibrated.png，不是独立整源',
       ex_pair='EX雷德王二级hold审计明确复用受方现装grabbed/thrown及旧waist；EX哥莫拉投目标亦为既有反应',
       other_identity_receivers='欧米伽receiver-generation已读prompt确认是欧米伽本人，不可拿来充杰顿',
       coverage_limit='已搜当前工程相关来源/协议和历史原图；不宣称逐张审完所有重复头尺/换色/缩放派生PNG，也未搜索整个外部归档盘。'),
   generation_candidate=dict(route='only_root_project_generate_image_existing_official_route',model='local_config_actual_model',
      quality='high',background='transparent',size='1024x1024',layout=[2,2],cell=[512,512],
      frames=phases,independent_whole_figures=4,empty_cell_padding_px_min=40,
      own_identity_reference=rec('art/fighters/zetton/stage3/legacy/zetton1/model-reference.png'),
      no_opponent_no_fx_no_ground_no_text=True,no_disconnected_parts=True,
      near_limb='近侧整臂整腿米白234/220/200、213/198/179；黑手脚66/66/68',
      far_limb='远侧整臂整腿由GPT画成暗米灰167/151/134、150/136/121；黑手脚38/38/42，交叉处深轮廓',
      identity='初代1966杰顿；高黑长头、完整双弯触角、唯一竖橙面灯、胸腹橙黄发光体、黑甲白斑、米白分节肢体、黑五指手足；无人眼/嘴/红纹/蓝灯/尾。',
      surface='天然连续皮套/怪兽皮肤与本人甲壳；无玩具球关节/轴孔/插接缝/螺丝/支架/塑料高光。',
      style='现装硬边像素整帧、固定真侧视；不能写真/3D/平滑插画。',
      post_authorized_by_this_contract=False,submitted=False),
   capacity=dict(actual_idle_alpha_height=165,model_alpha_height=166,
      note='根所述约150px是概数，尺寸门应对本人165/166原生高度及骨长，不把整人压到150。',
      planned_source_scale=[2,1],postprocess_common_scale=[1,2],planned_native_full_cell=[256,256],
      theoretical_source_standing_equivalent_height=[330,332],
      theoretical_source_horizontal_body_length=[380,432],native_horizontal_body_length=[190,216],
      source_head_long_ruler_hint=72,native_head_long_ruler_hint=36,
      head_ruler_basis='旧提欧生产合同的头部长尺约36仅作提示；不是已经核准的不含触角骨尺，返回后仍须高分源实际核量。',
      feasibility='512方格对2倍整人约380–432宽及330高的包络有空间，原生头部仍约36px，原则可读；四独立图/头足完整/一致体量由返回实图证明。',
      no_bbox_fit_no_frame_scale=True,no_area_fit=True,actual_generated_board_verified=False),
   reused_whole_sources=reuse,
   raw16_19='必须保留真实碰撞前当前空中姿势和实体位置；当前air_fall不等于已经完成新A的承接。不得先把受方摆成A。',
   required_root_pairing=['当前真实空中→A无明显瞬移/身体翻面跳变','A→B腹腰真实相贴且头角/手足不穿本人',
      'B→C随背坡抬升，整人姿态连续','C→D→既有thrown_back0后翻连续',
      'thrown_back2首次触地→3稳定→down无尺寸跳变/脚尖截格'],
   down_transition_known_gap='现装thrown_back3完整bbox宽172；down0矩形264宽、bbox宽204且触右格边。仅列原始实测，不能先认着地稳定闭环。',
   no_fake_contact_points=True,grip=None,waist=None,capture_hitbox=None,
   budget=dict(local_reserved_total_usd=49.985414,hard_ceiling_usd=60,conservative_reserve_next_post_usd=10,
      total_after_one_reserve_usd=59.985414,remaining_after_one_reserve_usd=0.014586,
      reserve_performed=False,root_owns_submit=True,no_retry_post=True),
   acceptance_boundary='一张板只争取最小四个独立缺相，不保证一单即全招完成。若任一相或旧相衔接/实体失败，保全候选，原三级继续运行，不旋转仰卧/补假点/吸附/扩大框/复制格凑数，也不擅自再POST。',
   source_changed=False,runtime_changed=False,godot_run=False,git_run=False)
 save('minimal-four-whole-frame-contract.json',contract)
 (OUT/'README.md').write_text('''# 杰顿最小受方方案：先补四个独立整人缺相

当前已找到并实看提欧杰顿专属28张原图、现装额外49完整格及旧generation的18张反应原图（含rejected后投首稿），没有可直接承担胸腹横伏背部的完整源。提欧原图是站立包罩挣扎/屈膝缩小；旧投是倒立、团身和仰卧。泰罗三级、提欧掌接、EX配对协议实际仍用同一批grabbed/thrown；杰顿stage4现有反击源属于攻击，不挪作受方。欧米伽receiver源已读prompt确认是欧米伽本人。

最小新板建议一张1024方图、2×2四格，各格独立生成完整杰顿：A斜俯接背，B胸腹向下横伏承重，C随背挺起抬升，D离背后翻起相。四相都用在缺口，不浪费一格重画已有落地。raw44以后先接已装thrown_back[0→1→2→3]倒立、团身、触地、展开，最后down须另看尺寸过渡。完整逐格姿势、raw tick、来源SHA、复用rect与不装条件见minimal-four-whole-frame-contract.json。未写可直接提交请求，也未POST。

本人实际idle Alpha高165、model高166原生像素，并非精确150。512源格按整人2倍绘制、统一1/2处理，可容纳约380–432宽的横伏身体（原生190–216）并留40px边；头部长尺提示约72源/36原生，原则上可读。这个是容量评估，仍须返回实图核尺/真Alpha/四个独立完整人物，不能压到150、逐格bbox拟合或裁触角脚尖。四相板暂未生成，也不能因此称连续性完成。

额外实缺：thrown_back末相完整bbox宽172，而当前down0宽204且右格边有Alpha；直接接down可能体量跳变。这里仅记录实测，未扩大修现装范围，不能把既有down默认算新配对着地已验。若新四相或后段过渡不合格，继续保留旧三级运行，不旋转仰卧、不添假waist、不吸附或扩框过关。

预算只读：49.985414/60美元，下一单按10美元占额后59.985414，余0.014586。根独占占额与POST，本席未占额/提交，不承诺重试。该方案仅杰顿首个配对对象，其余角色受方未完成。

范围边界：搜索当前工程相关来源与配对协议，实际看上述完整原源与完整格；没有声称逐张审完所有重复头尺/换色/缩放派生，也未扫整个外部归档盘。历史页和当前页只用于只读证据，不是新增动作资源。
''',encoding='utf8')
 print(OUT/'minimal-four-whole-frame-contract.json')
if __name__=='__main__':main()

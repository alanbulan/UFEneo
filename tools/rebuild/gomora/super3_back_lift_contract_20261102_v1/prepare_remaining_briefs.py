"""仅准备余16张绝对整相草稿，不占预算、不提交，不动根已提交07或备好的11。"""
from pathlib import Path
import copy
import hashlib
import json

ROOT=Path(__file__).resolve().parents[4]
ART=ROOT/'art/fighters/gomora/stage4/super3-back-lift-20261102-v1'
REPORT=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-contract-v1'
def read(p):return json.loads(p.read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def record(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size)
def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')

POSES={
0:('沉髋起架', 'OPENING HIP LOAD. Stand in the normal two-foot grounded fighting stance, both broad soles '
   'flat. Bend both knees a little and lower the pelvis slightly between the feet; chest inclines forward '
   'only about five degrees. The NEAR lighter arm has its elbow bent with the open claw in front of upper '
   'chest, the FAR darker elbow draws outward and its claw sits lower in front of ribs. Both shoulders '
   'actively load, not only one wrist. The complete heavy tail settles behind LEFT into a low loose arc. '
   'A fresh whole-body beginning, not a copied idle image, rear kick or crouch attack.'),
1:('抬肩示警', 'SHOULDERS RISE TO RECEIVE. Both soles flat in the same support stance, knees moderately '
   'flexed, hips centered, torso inclined forward about ten degrees. Head stays level facing RIGHT with '
   'both horns intact. Raise the NEAR shoulder and bend its elbow so the open near claw is beside the '
   'front of the shoulder, not above the head; FAR shoulder opens backward slightly and its darker claw '
   'opens beside the upper ribs. Both arms make distinct coordinated preparations without becoming '
   'human-length overhead arms. Back surface broad and unobstructed; complete tail counterbalances low LEFT.'),
2:('屈膝迎落', 'KNEES FLEX TO RECEIVE FROM ABOVE. Both feet remain solid, nearer foot slightly forward '
   'to RIGHT, far foot behind. Bend both knees visibly and set hips back; torso leans forward about '
   'twenty degrees as a coherent chest-pelvis unit, head reaches forward a little to clear the upper back. '
   'NEAR elbow rotates down/out, open near claw beside lower chest; FAR elbow remains separately readable '
   'outside the far ribs and its claw extends a little farther forward at rib height. Both shoulders '
   'descend with the chest. One complete tail dips with the pelvis and sweeps back LEFT without attacking.'),
3:('上背迎接', 'UPPER-BACK RECEIVING RAMP BEFORE CONTACT. Feet firmly planted, knee flexion maintained, '
   'hips back, torso inclined forward about twenty-five degrees. Shoulder blades form a broad sloping '
   'upper-back surface with empty transparent air above it; head/neck forward, not curled under belly. '
   'Both complete claws are open at the sides/front of the chest: NEAR light claw slightly lower and '
   'closer to camera, FAR dark claw a little higher and forward. Elbows and wrists articulate with both '
   'shoulders. No opponent, held body, invisible-hand grip gesture or magical catch net. Tail from pelvis '
   'continues fully behind LEFT, low and gently curved.'),
4:('实体承接', 'ACTUAL UPPER-BACK RECEIVING CONTACT POSE. Both soles grounded, knees flexed, the torso '
   'and broad connected back inclined about thirty degrees forward toward RIGHT. Pelvis shifts just '
   'slightly down/back under the imagined arriving load. The NEAR lighter elbow flexes inward and its '
   'complete open claw curls slightly beside the lower chest as if steadying a body beside the shoulder; '
   'the FAR darker shoulder lowers with the chest, elbow flexed and its claw separately visible on the '
   'far side. Hands do not reach through the back or above the head. The broad UPPER BACK, not a claw '
   'floating high in air, receives the contact. Draw NO actual opponent or burden. Head and short nose '
   'horn clear the back surface; complete long tail counters the load to LEFT. This is not the deeper '
   'lowest loaded pose and is not a forward palm strike.'),
5:('负重缓冲', 'LOAD-ABSORBING KNEE AND HIP FLEXION. Both feet flat, thighs and knees bend further, '
   'pelvis lower between support feet, chest and upper back incline forward about thirty-two degrees '
   'as one continuous torso. The NEAR shoulder rolls down/forward and near claw hangs beside lower chest '
   'with a flexed elbow; FAR arm flexes separately, darker claw slightly ahead of the near claw at lower '
   'rib height, both elbows intact. The complete head remains forward-facing, not hidden under a copied '
   'torso. The full tail root follows the lowered pelvis, tail curves behind LEFT, single tip intact. '
   'Implied weight only; no second character or object.'),
6:('俯身加载', 'FORWARD LOAD JUST ABOVE THE LOWEST POINT. Both broad soles remain planted; pelvis sits '
   'down/back and knees are deeply flexed but not touching the ground. Torso leans forward about '
   'thirty-eight degrees, chest and shoulder ridge lowering together, neck stretches slightly forward. '
   'Near lighter elbow bent, near claw relaxed/open below chest in front of knee; far darker elbow '
   'opens outward, far claw forward and a little higher. Both shoulders and the hip visibly participate. '
   'Back broad enough to read as bearing a load with nothing drawn on it; tail low LEFT with full length '
   'and a small upward curve at its complete tip. Not a copied bow, crouch punch or collapsed lying pose.'),
8:('蹬地挺髋', 'FIRST UPWARD DRIVE FROM BOTH PLANTED FEET. Both soles fully grounded; both knees '
   'extend from a deep bend but remain visibly flexed. Pelvis rises directly over the support base, '
   'torso still leans forward about thirty degrees; chest and shoulders have begun rising behind the '
   'hip drive, not a rigid vertical translation of another image. NEAR shoulder draws up and its '
   'open light claw moves outward at lower chest; FAR darker elbow opens a little wider with its claw '
   'below rib height to balance. Head faces RIGHT, neck raises modestly. Full long tail behind LEFT '
   'changes its continuous curve with rising pelvis. No jump, forward dash, kick, tail strike or FX.'),
9:('挺背抬肩', 'RISING BACK AND SHOULDER LIFT. Both planted feet carry weight, knees near half-flexion, '
   'pelvis higher and centered. Torso inclined only about fifteen to twenty degrees forward, back '
   'clearly rising toward upright, head forward/level. NEAR lighter arm opens forward to RIGHT at lower '
   'chest height with a bent elbow and open claw; FAR darker arm opens outward at a lower angle, full '
   'elbow and wrist visible. Both shoulders lift with the spine and hips. A coordinated whole-body '
   'back lift, not a nose uppercut or forearm strike. Complete tail extends low LEFT behind hips as '
   'counterweight. No opponent or burden in the drawing.'),
10:('伸髋送出', 'FINAL HIP EXTENSION BEFORE RELEASE. Both broad feet stay planted, knees almost straight '
    'but naturally soft, hips centered and chest near vertical with only a slight ten-degree forward '
    'inclination. Back and shoulders lift together, head and intact nasal horn face RIGHT and slightly '
    'up, no extreme neck bend. NEAR light claw opens forward at chest level, elbow still bent; FAR dark '
    'arm opens farther out at waist/rib height, both shoulders connected. Hands are ceasing support, '
    'not gripping an invisible neck. The single complete tail gently dips LEFT/back for balance. '
    'This is still the lift-end before the fully opened release; no beam, palm hit or jump.'),
12:('前步随势', 'UNLOADED FORWARD FOLLOW-THROUGH. Torso inclines forward about fifteen degrees after '
    'back extension, pelvis starts settling, knees naturally soft; maintain the same grounded root '
    'without a forward dash. NEAR foot remains the support sole, FAR foot is flat as a stabilizing '
    'step with its toes still fully visible. NEAR lighter shoulder lowers and its complete open claw '
    'comes down in front of the lower ribs; FAR darker elbow pulls back slightly with its claw opened '
    'beside the far waist. Both arms follow the unloading rather than freezing in the release pose. '
    'Head faces RIGHT, full tail behind LEFT settles with the hips. No opponent or landing impact FX.'),
13:('摔落定势', 'GROUNDED SETTLING AT THE OPPONENT-LANDING MOMENT. The monster itself is NOT jumping '
    'or slamming down. Both feet solid and naturally spaced, knees soften under body weight, hips '
    'settle, chest leans forward about twenty-five degrees with head still facing RIGHT. NEAR light '
    'elbow slightly flexed, near open claw below chest; FAR dark arm extends forward at a lower angle '
    'with its shoulder and wrist fully connected. Shoulder/chest/hip follow-through continues. '
    'Complete long tail settles in a low balancing curve LEFT, not sweeping to hit. No ground crack, '
    'dust, stomp, victim or magical shockwave.'),
14:('卸力收臂', 'RECOVERY START SHARED BY SUCCESS AND A REAL MISS. Both soles planted, hips return '
    'toward center, knees moderately bent, torso still leans about twenty degrees forward. Both arms '
    'actively fold back toward guard: NEAR lighter elbow bends with open claw in front of lower chest; '
    'FAR darker elbow draws inward with open claw by the ribs at a slightly different height. Head '
    'returns level RIGHT, shoulders settle. Back must not look as though still holding a burden; '
    'there is no victim in this image. Full single long tail behind LEFT begins returning toward '
    'the neutral gentle curve. This fresh whole pose is not a copied opening or idle frame.'),
15:('重心回中', 'MID RECOVERY WITH WEIGHT CENTERED. Grounded feet steady, knees softly flexed, pelvis '
    'centered; torso inclined only about ten degrees forward, neck and head level. NEAR light claw '
    'rises toward middle ribs with a bent elbow, FAR dark claw rises separately beside upper waist '
    'as its elbow draws closer to the body. Both shoulders and chest restore together. Complete '
    'long tail rises slightly from the low unloading arc into a loose rear LEFT curve, root remains '
    'at pelvis. Keep distinct nearer/farther feet and arms. No attack extension, burden, jump or effect.'),
16:('举爪回护', 'RAISED-CLAW GUARD RESTORATION. Both soles grounded in stable fighting stance, knees '
    'lightly bent, pelvis centered, torso nearly upright with only a small forward lean. NEAR '
    'lighter claw rises to upper chest/shoulder-front height with a bent elbow; FAR darker claw '
    'rises in front of middle chest, elbow slightly open outward so both complete arms remain readable. '
    'Both shoulders resume protective posture together. Head level facing RIGHT, intact horns. '
    'Complete single long tail behind LEFT returns gently toward its neutral curve. Independently '
    'draw this transition, do not paste or copy the master guard.'),
17:('复架', 'FINAL READY GUARD BEFORE THE INDEPENDENT IDLE ANIMATION. Feet flat, knees soft, pelvis '
    'stable, body upright in the accepted monster anatomy. NEAR lighter elbow flexed, open claw '
    'forward of chest; FAR darker elbow flexed separately with claw a little lower and behind, '
    'shoulders relaxed into guard. Head faces RIGHT with no sudden size or horn-angle change. '
    'Whole torso, arms and hips complete the return, while the full long tail settles in one '
    'continuous natural rear LEFT curve with its sole tip intact. This is a newly painted whole '
    'return pose that can meet idle, not duplicated idle pixels or another phase; no remaining '
    'attack, opponent, burden or FX.'),
}

def main():
    acceptance=REPORT/'root-source-and-production-acceptance-v1.json'
    accepted=read(acceptance)
    assert accepted['accepted_as_new_independent_super3_design']
    base_path=ART/'phase-07/request-001/brief.json'
    base=read(base_path)
    protected={record(p)['path']:sha(p) for p in [
        ART/'briefs/phase-07/brief.json',ART/'briefs/phase-11/brief.json',base_path,
        ART/'phase-11/request-001/brief.json',acceptance]}
    common=base['prompt'].split('NEW INDEPENDENT PHASE',1)[0]
    assert set(POSES)==set(range(18))-{7,11}
    files=[]
    for phase,(name,pose) in POSES.items():
        value=copy.deepcopy(base)
        value.update(id=f'gomora_super3_back_lift_{phase:02d}_20261102',frame=phase,phase_name=name,
            prompt=common+f'NEW INDEPENDENT PHASE {phase:02d} of 18 — '+pose,
            raw_ticks=[phase*4,phase*4+3],attack_active=phase==4,
            root_source_and_design_acceptance=record(acceptance),
            root_review_required_before_first_post=False,
            submitted=False,installed=False,source_to_native_scale=None)
        for key in ['root_reviewed_draft','reference_adaptation']:
            value.pop(key,None)
        if phase<=4:
            value['motion_evidence'].update(source_image=None,source_pts_seconds=None,
                source_boundary='上背承接的起手/捕获窗口是根已接受的本作对空投编排。原片起始受方已趴背，不能声称本相是原剧逐镜复制。',
                not_a_generation_attachment=True)
        elif phase<=8:
            value['motion_evidence'].update(source_image=record(ROOT/'reports/review/2026-11-02/gomora-super2-newsource-v1/p2-back-lift-full-000-000.jpg'),
                source_pts_seconds=[218.970,219.304])
        elif phase<=10:
            value['motion_evidence'].update(source_image=record(ROOT/'reports/review/2026-11-02/gomora-super2-newsource-v1/p2-back-lift-full-001-001.jpg'),
                source_pts_seconds=[219.346,219.721])
        else:
            value['motion_evidence'].update(source_image=record(ROOT/'reports/review/2026-11-02/gomora-super2-newsource-v1/p2-back-lift-full-003-003.jpg'),
                source_pts_seconds=[220.347,220.972])
        value['references']=[{k:r[k] for k in ['path','sha256']} for r in base['references']]
        value['absolute_pose_not_chained_edit']=True
        value['prepared_after_root_acceptance_not_a_post']=True
        value['root_source_and_contract_acceptance_required_before_post']=False
        value['serial_gate']='根仍独占POST：07首源核尺后才继续；本草稿不自动提交、不改任何在途请求。'
        value['support_foot_contract']='近足在前RIGHT、远足在后LEFT；两完整支撑足贯穿地面动作，不用每相漂移代替真实胸髋膝动作。'
        target=ART/f'briefs/phase-{phase:02d}/brief.json';save(target,value);files.append(record(target))
        assert len(value['references'])==2 and all(set(r)=={'path','sha256'} for r in value['references'])
        assert 'NEAR' in value['prompt'] and 'FAR' in value['prompt'] and 'tail' in value['prompt']
    assert protected=={p:sha(ROOT/p) for p in protected}
    save(REPORT/'remaining-16-briefs-v1.json',dict(root_acceptance=record(acceptance),briefs=files,
        protected_first_key_files_unchanged=protected,post_count=0,budget_reserved=False,
        source_to_native_scale_pending_first07=True,root_owns_only_pending_post=True,
        base_identity_prompt=record(base_path),new_tool=record(Path(__file__).resolve())))
    print(json.dumps(dict(remaining_briefs=len(files),first07_unchanged=True,post_count=0),ensure_ascii=False))

if __name__=='__main__':main()

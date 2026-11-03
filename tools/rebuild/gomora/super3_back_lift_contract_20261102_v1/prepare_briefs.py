"""准备首张负重和释放整人brief，不提交任何图单。"""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[4]
ART=ROOT/'art/fighters/gomora/stage4/super3-back-lift-20261102-v1'
REPORT=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-contract-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def record(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size)
def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    references=[ROOT/'art/fighters/gomora/model/model-native.png',
        ROOT/'reports/review/2026-11-02/gomora-original-sequence-v1/briefs/references/identity-original-full-fit.png']
    expected=['bc9a7e641c3d627e823530cd3bb62d897da2b932310bba20287a7af38ae5d708',
              'd26ed6ec179141f9392f210e0fd573d9bd1977f864c2f4aa89be2a12f511120d']
    assert [sha(p) for p in references]==expected
    source=ROOT/'reports/review/2026-11-02/gomora-super2-newsource-v1'
    common=(
        'Draw exactly ONE NEW COMPLETE full-body animation frame of classic GOMORA, the brown Ancient Monster '
        'in Ultraman 1966. Keep his complete intact long tail and intact short nasal horn from the accepted '
        'runtime master. NOT EX Gomora, not a later summoned version, not the second-battle severed-tail state. '
        'The TWO attached images are IDENTITY ONLY: accepted complete native pixel master, and its clean '
        'complete original source uniformly aspect-fitted. Neither attached pose is the requested action. '
        'Fixed SIDE-VIEW arcade fighting camera; facing RIGHT. No camera rotation, zoom, foreshortened front '
        'view or added perspective. Draw ONE coherent whole monster: head, TWO connected arms and shoulders, '
        'continuous chest and pelvis, BOTH distinct weight-bearing legs, and exactly ONE thick long tapering '
        'tail from pelvis to ONE complete tip. The two crescent head horns, blunt face, short nasal horn, '
        'small amber eye, earthy brown/tan scaled suit hide, ribbed belly and dorsal scale plates must match '
        'the accepted master. Preserve skull, torso, thigh, shin, feet and tail anatomical proportions even '
        'when bent; never shrink the monster to fit its pose. NEAR limbs are lighter brown; FAR entire arm, '
        'leg and ear horn are naturally darker from generation, with coherent one-pixel dark overlap edges. '
        'No later masked recoloring. Complete connected natural suit surfaces: NO toy ball joints, pivot '
        'discs, peg holes, straight open waist seam, screws, stand, part sockets or plastic gloss. Keep '
        'actual monster scales and skin folds. Native fighting-game PIXEL finish with deliberate hard pixel '
        'clusters, restrained brown palette, thin dark pixel contour and upper-left light. Transparent '
        '1024x1024 PNG, 真正PNG Alpha透明，透明背景. At least 40 transparent output pixels around every horn, '
        'claw, sole and tail tip. Invisible staging only: grounded supporting soles near y=930, hips around '
        'x=560; complete rear tail extends LEFT with a natural arc. Reserve generous empty room above the '
        'back and behind the body. Keep master anatomical scale corresponding to an approximately 680–720 '
        'output-pixel upright body as an initial composition target, not a per-frame bbox fit. The actual '
        'common source-to-native scale will be chosen after the first returned frame is measured. '
        'Draw the monster ALONE. Do not draw, bake, outline or silhouette an opponent, burden, dummy or '
        'object on the back; a separate complete runtime opponent will be positioned only after real '
        'physical capture. No ground, shadow, scenery, text, grid, effect, aura, beam, dust, speed line or '
        'motion ghost. Do not paste, rotate, cut or assemble limbs. Do not copy any prior half-circle grab, '
        'palm kick, tail sweep, uppercut, burrowing charge, old wave or EX pose. Independently paint this '
        'absolute whole-body pose, with both arms, shoulders, chest, hips, knees, ankles and tail cooperating.\n'
    )
    poses={
        7:dict(name='背负低点', source_image='p2-back-lift-full-000-000.jpg',pts=[218.970,219.304],
            prompt='NEW INDEPENDENT PHASE 07 of 18 — LOWEST LOADED BACK POSITION. Both broad soles firmly '
                'grounded, knees deeply but naturally bent; pelvis sits down and back between the feet. '
                'The torso inclines FORWARD toward RIGHT about 35–45 degrees from upright as a solid '
                'connected chest-and-hip unit, creating a clearly readable broad sloping upper-back support '
                'surface. Head and neck reach slightly forward, nasal horn intact. The NEAR lighter shoulder '
                'rolls forward/down; NEAR elbow bends and its complete open claw hangs in front of and below '
                'the chest. The FAR darker arm is separately visible beyond the far shoulder, elbow flexed '
                'with its claw lower and slightly farther forward for balance; neither arm is frozen in '
                'the master guard or crossed through the torso. The back is bearing imagined weight, but '
                'draw NO weight or opponent. The near and far planted feet retain distinct stance spacing; '
                'no airborne foot, kick, stomp, bowing head-only motion or collapsed flat belly. The full '
                'heavy tail flows from pelvis behind LEFT in a low continuous balancing arc, complete tip '
                'above the sole line. This is the compressed load pose immediately before knees/hips extend '
                'and the back raises; do not draw the later upright release pose.'),
        11:dict(name='后抛松爪', source_image='p2-back-lift-full-002-002.jpg',pts=[219.763,220.096],
            prompt='NEW INDEPENDENT PHASE 11 of 18 — UPRIGHT BACK-THROW RELEASE. This is the distinctly '
                'UNLOADED end of a physical knee/hip extension, after the low load pose. Both broad feet '
                'remain planted; knees have straightened to a natural slightly flexed stance, hips above '
                'the support base. Chest and upper back rise to nearly upright with a small backward '
                'extension, head and intact nasal horn pointing RIGHT/up only a little. The NEAR lighter '
                'arm opens FORWARD to RIGHT at about lower chest height with a bent elbow and fully open '
                'claw, deliberately releasing support; the FAR darker arm opens on the far side at a '
                'different lower angle, complete shoulder/elbow/wrist visible through natural occlusion. '
                'Both shoulders, chest and pelvis visibly follow the extension; no one-arm-only motion. '
                'The imagined opponent has just left the back toward LEFT/rear, but do not draw the '
                'opponent, a flight arc, silhouette or effect. Do not arch into an unnatural broken waist '
                'or throw the head backwards. The single complete long tail shifts gently down/back LEFT '
                'to counterbalance and does not become a detached tail projectile, sweep, whip or second '
                'limb. This is an open-claw release after lifting with the BACK, not a forward palm strike '
                'or kick, not a nose beam stance. Keep full tail length and the same anatomical scale as '
                'the loaded phase; feet stay solid and the body does not jump.'),
    }
    written=[]
    for phase,data in poses.items():
        brief=dict(schema=2,id=f'gomora_super3_back_lift_{phase:02d}_20261102',fighter='gomora',
            specific_version='1966标准完整长尾/完整鼻角本体；成功段参考同本人第二战背掀，完整尾平衡为本作编排',
            stage=4,action='super3_back_lift_air_throw_independent_v1',display_name='背掀震落（三级·本作编排）',
            official_skill_name=False,frame=phase,phase_name=data['name'],asset_kind='character',
            size='1024x1024',quality='high',background='transparent',model='gpt-image-2.5-sunburst',
            route='tools/art_pipeline.py.generate_image only; actual route/model recorded after root submit',
            art_source='api_planned_not_submitted',references=[record(p) for p in references],
            reference_provenance=record(ROOT/'reports/review/2026-11-02/gomora-original-sequence-v1/briefs/references/provenance.json'),
            contract=record(REPORT/'new-whole-frame-contract.json'),
            motion_evidence=dict(source_video=record(source/'public-p2-research-source.mp4'),
                source_image=record(source/data['source_image']),source_pts_seconds=data['pts'],
                source_boundary='原镜头为断尾且受方已趴背；只支持负重/伸髋/后落成功段，不证明本作捕获规则或完整长尾动作。',
                not_a_generation_attachment=True),prompt=common+data['prompt'],ticks=4,raw_ticks=[phase*4,phase*4+3],
            attack_active=False,pose_uses_old_body_frame=False,source_to_native_scale=None,
            planned_runtime_cell=[512,320],planned_runtime_anchor=[256,304],
            target_master_anatomical_height=192,
            registration_note='先根实看07首张原源，核头骨/躯干/支撑/整尾后选统一整图倍率；不按每张bbox等高或逐帧面积拟合。',
            submitted=False,installed=False,user_approved=False,
            root_source_and_contract_acceptance_required_before_post=True,
            root_review_required_before_first_post=True,preserve_old_runtime_until_all_new_frames_ready=True)
        path=ART/f'briefs/phase-{phase:02d}/brief.json';save(path,brief);written.append(record(path))
    save(REPORT/'first-key-briefs.json',dict(first_to_submit_after_root_review=7,release_key=11,
        briefs=written,source_references_unchanged=[record(p) for p in references],
        post_count=0,budget_reserved_by_child=False,existing_unknown_request_not_retried=True,
        root_must_reserve_current_budget_before_actual_post=True))
    print(json.dumps(dict(briefs=written,post_count=0),ensure_ascii=False))

if __name__=='__main__':main()

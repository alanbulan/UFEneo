"""初代背掀受方其余五相的离线简报和完整参考摘帧；不发POST、不做运行注册。"""
from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'reports/review/2026-11-02/gomora-back-lift-ultraman-remaining-five-briefs-v1'
MOTHER_DIR=ROOT/'art/fighters/ultraman/stage5/gomora-super3-back-lift-receiver-20261102-v1/phase-02/request-001'
REVIEW_SHA='cc20d4cc590ae2e3378b39e22ecf74f160a70d4a508c3f8d98f8f6f420983e78'
SOURCE=ROOT/'reports/review/2026-11-02/gomora-super2-newsource-v1'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rec(path): return dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size)
def read(path): return json.loads(path.read_text('utf-8-sig'))


def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(data,stream,ensure_ascii=False,indent=2);stream.write('\n')


POSES={
 0:dict(name='落背缓冲',frame=5249,range=[218.970,219.304],actor_source=5,state_index=0,
    boundary='原片起始已横伏；此空中到落背的过渡是本作独立补全，只用该镜头确立胸腹负重方向，不冒称拍到了起抓。',
    short=['本作落背过渡，原片未拍起抓。','肩胸向右下沉、骨盆在左略高。','近臂向右下伸接重，远臂滞后。','双腿在左，一膝回收、一腿较伸。','全身开始吸收冲量，尚未压至最低。','与02母相重绘全身，不能旋转旧图。'],
    pose='NEW INDEPENDENT PHASE 00 — FIRST CHEST-DOWN LOAD ABSORPTION. This is the newly authored transition from a genuinely airborne receiver into belly-down back support, BEFORE the accepted compressed phase02; the film reference already starts loaded and does not document this entry. The coherent torso slopes gently DOWN toward the RIGHT, roughly 15–20 degrees from horizontal; the pelvis is slightly higher at LEFT while shoulders and chest yield down/forward toward RIGHT. The abdomen has only begun to yield and has not folded into the lowest compression. Head and neck continue past the right shoulder, looking RIGHT/down. The near arm opens with a soft elbow and reaches DOWN/RIGHT in a reflexive weight-taking arc without touching a floor; the far shoulder and far elbow trail DOWN/LEFT beside the chest at a visibly different angle, both complete hands separate. Both legs trail to LEFT from continuous hips: the near thigh draws in a little with a clearly flexed knee, while the far thigh/leg remains longer and more extended behind, its ankle lagging. Both feet are fully drawn and separated. Shoulders, chest, pelvis, BOTH elbows and BOTH knees react together to this first absorption. Do not copy the static hanging arms or pelvis curve of phase02, do not draw a standing/takeoff/crawling/push-up pose, and do not translate or rotate phase02 to fake this entry.'),
 1:dict(name='随俯压背',frame=5249,range=[218.970,219.304],actor_source=6,state_index=1,
    boundary='原片胸腹横伏负重的方向有据；本相与02的四tick分相、完整侧视肢体及缓冲递进是本作编排。',
    short=['胸腹继续随俯，尚未最低压缩。','躯干近水平、右肩低于左髋。','近肘逐渐收软，远手往下回摆。','两手高低/前后位置均不同于02。','近膝仍稍抬，远小腿较长地下滞。','肩胸腰髋、两臂两腿共同过渡。'],
    pose='NEW INDEPENDENT PHASE 01 — YIELDING WITH THE LOWERING BACK. This is AFTER the first weight absorption but BEFORE the accepted phase02 minimum. The chest and abdomen remain DOWN; the torso is nearly horizontal but still slopes slightly down toward the RIGHT, around 8–12 degrees. The shoulder/chest unit has descended while the pelvis at LEFT is yielding with it, making a longer, less-compressed waist curve than phase02; preserve actual torso length. The head droops RIGHT/down with a small natural neck bend. BOTH arms are actively settling, not frozen: near shoulder rolls forward/down and near elbow begins softly folding, with the near hand slightly ahead/right of its later phase02 hanging line; far shoulder responds and the far forearm swings downward behind/left of the near arm, its hand at a different height and farther back. Do not draw floor contact. Near thigh and knee at LEFT remain slightly more lifted/flexed than phase02 while the far knee is more relaxed and the far lower leg hangs longer down/back at a distinct angle; TWO full feet remain separated. Show coordinated shoulder, chest, waist, pelvis, both arms and both legs following the lowering support. This is a newly drawn middle compression pose, not the exact phase02 body with only a hand nudged or one leg changed.'),
 3:dict(name='随背抬升',frame=5264,range=[219.346,219.721],actor_source=9,state_index=5,
    boundary='原PTS219.596位于挺膝髋抬背段；原镜头部分肢体出画，完整新侧视身体从canon补全，不能冒称原片给了完整人物定稿。',
    short=['挺背向上，腹腰尚在负重。','骨盆从左上抬、肩颈仍在右下。','全躯干斜度增大，不只是移图。','双臂因上抬各自滞后摆动。','两腿向左上回收、膝屈度不同。','与母相同骨尺，完整双手双足。'],
    pose='NEW INDEPENDENT PHASE 03 — RISING WITH THE BACK. This is the connected lift AFTER the accepted phase02 minimum, not its translated copy. The unseen support has risen through its knees and hips; the receiver abdomen/waist still yields against that broad support while the pelvis and upper thighs rise toward the UPPER LEFT. The receiver body slopes distinctly DOWN toward the head at LOWER RIGHT, approximately 30–40 degrees from horizontal; keep a continuous curved chest/waist/hip connection rather than a rigid rotated plank. Shoulder blades/chest, neck and pelvis respond together; the head/neck remain beyond the right shoulder, drooping RIGHT/down. BOTH arms lag naturally under the rising body: near elbow softens with its forearm sweeping down and slightly back LEFT relative to the shoulder, while the far elbow/forearm lags on a different arc, with both complete hands separated and changed from phase02. BOTH thighs begin recovering up/LEFT from the pelvis, one knee more drawn in while the other lower leg naturally trails; feet change relative height and angle without shortening the leg anatomy. This is a whole-body lift with correlated shoulder/chest/hip and both-limb motion, not a static prone sprite raised vertically, not a later free airborne flip. The film full frame has some body parts outside the camera; independently complete all head, hands, feet from the accepted C-type identity, do not crop to imitate it.'),
 4:dict(name='背缘卸重',frame=5270,range=[219.721,219.930],actor_source=8,state_index=2,
    boundary='原PTS219.846处于挺背末段与离背过渡，受方部分画外；只支持卸重转落方向，完整侧视和最后接触细节仍须新源实际核。',
    short=['重心越出背缘，开始卸重。','髋腿在左上、头肩转向右下。','腰腹伸展，不保持母相平伏形。','近肘开始收回、远臂反向随势。','近腿较伸、远膝较收，脚完整。','新接触/root仍null，不抄杰顿。'],
    pose='NEW INDEPENDENT PHASE 04 — UNLOADING OVER THE REAR BACK EDGE. The receiver center of mass is now moving past the support toward LEFT/rear. Draw the intact body physically rolling out of prone load, roughly 50–65 degrees from horizontal: pelvis and BOTH legs move into the UPPER LEFT while chest/shoulders and head rotate toward LOWER RIGHT. Abdomen/waist lengthens out of the compressed phase02 curve; only a final small natural support region would remain under the lower abdomen/waist, but draw NO support, contact mark or fake point. The transition is visible through connected shoulder/chest/waist/pelvis changes, not by rotating the phase02 image. BOTH arms begin a protective reaction with different arcs: near shoulder opens and near elbow draws in a little with the hand moving away from its former vertical hanging line; far shoulder and elbow swing out/back with a different bend, leaving both complete hands visible through natural occlusion. Near leg extends more toward UPPER LEFT as its hip rises, while the far knee stays more flexed and its foot trails at a different height, both feet intact. No rigid sleeping/prone plank, no floor push-up, no supine resting body. This is the distinct unload between the supported rising phase03 and the initial free backward flip phase05. The film reference partly clips the receiver; complete the entire accepted C-type character, do not copy the camera crop or the monster.'),
 5:dict(name='后翻脱离前相',frame=5273,range=[219.930,220.055],actor_source=10,state_index=3,
    boundary='原PTS219.971已开始离背后落；新相到本人既有thrown_back[0]倒立格的接续是本作责任，原片不提供完整侧视定稿。',
    short=['已脱背，进入后翻前相。','全身接近倒立，头在右下。','髋腿向左上，双腿渐开不同角。','两肩开、双肘伸展接旧倒立相。','不能旋转母相或复用旧被投图。','接44–47倒立候选仍待真实核。'],
    pose='NEW INDEPENDENT PHASE 05 — INITIAL BACKWARD FLIP JUST AFTER SEPARATION. The complete receiver has just cleared the support, entering a backward aerial turnover toward LEFT/rear. The chest/waist/hips continue the preceding physical roll, approaching a near-inverted body line around 75–85 degrees from horizontal: head/neck and shoulders are toward LOWER RIGHT while pelvis, BOTH legs and feet rise toward UPPER LEFT. Keep the character coherent rather than a stiff rotated plank: torso extends naturally after release, the pelvis follows through, the neck is protected and bends slightly with the motion. BOTH shoulders open and both elbows extend outward on different protective arcs, hands moving away from the old dangling position to anticipate the existing inverted thrown_back[0] that follows; two complete hands, no arm passing through the chest. Both legs begin opening into an asymmetrical inverted V, near thigh/leg a little straighter and farther LEFT while far knee remains slightly flexed with its foot higher/closer to the pelvis; TWO continuous leg chains and TWO full feet, not two identical mirror legs. This is the independently painted last new transition BEFORE the existing full inverted receiver pose, not that existing sprite reused and not the phase02 master rotated. Draw no support, floor, contact point, opponent, motion trail or ground collision. The original film establishes release/fall but this complete fixed-side-view transition and its later continuity must be reviewed separately.'),
}


COMMON='''Draw exactly ONE NEW INDEPENDENT COMPLETE full-body frame of the original ULTRAMAN, this game's accepted standard 1966 C-type identity. Fixed SIDE-VIEW arcade fighting CAMERA; camera does not rotate or zoom. Transparent 1024x1024 PNG, quality HIGH, 透明背景，真正PNG Alpha透明. Draw Ultraman ALONE.

All THREE images are references with strictly separated roles. REFERENCE 1 is the clean accepted C-type canon model-reference-x4, an exact four-times nearest-neighbor enlargement of the complete current native model: identity, red/silver suit topology and pixel finish ONLY, not the requested pose. REFERENCE 2 is the one root-delegated accepted phase02 full-body LOWEST LOAD source, used by EVERY new phase as the SAME shared identity and anatomical-size reference. Preserve its actual skull, upper-arm, forearm, torso, pelvis, thigh, shin and foot dimensions at this 1024 source scale; pose bending/rotation of the physical anatomy can change the total canvas extent, never scale the whole body to match a bounding box. It is NOT a pixel-edit base and its pose is NOT the requested new phase. REFERENCE 3 is one COMPLETE original-film CAMERA FRAME for the phase evidence specified below; it is an opaque historical scene and may clip parts of the original receiver. Use only its stated motion evidence. Do not copy its monster, ground, photographic texture, camera crop or lighting. The original action and this game's fixed side view are distinct; output always follows the absolute NEW pose below.

This is one independently PAINTED WHOLE new phase from the same clean canon and same accepted phase02, NOT chained editing from another newly generated phase. Do not cut, paste, mask, warp or rotate any reference body or limbs; no rig, IK, skeletal pieces or mirrored prior frame. Changes must involve shoulders, both arms, chest, waist, pelvis, both legs and neck together, not one hand moving on a frozen torso. The head end remains toward RIGHT/lower-right and the feet toward LEFT/upper-left as the coherent body physically turns through this phase. Camera stays SIDE VIEW. No front-facing or overhead camera.

Correct C-type silver mask/mouth, central silver head fin, pale yellow eyes, accepted connected red/silver suit and chest Color Timer only where naturally visible; do not draw the timer on the back. Not A/B type, Seven, Taro, Teo, another hero or a powered form. Crisp intentional fighting-game PIXEL clusters matching the clean canon and accepted mother, restrained red/silver/grey palette, thin dark pixel contour and consistent upper-left light. Far limbs are naturally shaded in this newly painted whole source. No photo texture, soft vector artwork, smooth 3D model, stock dummy or toy.

All shoulder/elbow/wrist/waist/hip/knee/ankle surfaces are natural continuous suit, with only honest anatomical folds: NO ball joints, joint discs, axles, sockets, peg gaps, straight open waist seam, screws, stand or plastic gloss. Full head fin, BOTH complete arms/hands, continuous torso/hips and BOTH complete legs/feet remain inside the frame, with only natural occlusion. Do not omit the far limbs or paste them later.

Leave at least 48 clear output pixels around the ENTIRE character in the 1024 square. Generous clear canvas is padding, not a target to inflate the body. Preserve anatomical size from phase02 regardless of physical pose or total Alpha bounding extent. Source-to-native uniform scale and all semantic abdomen/back-edge/root/grip points remain UNMEASURED; do not draw points, guides or registration marks. Draw no GOMORA, no opponent, ground, shadow, scenery, support, rail, silhouette under the body, weapon, effect, aura, beam, dust, ghost, motion trail, label, panel, grid, black/white/chroma backing or painted checkerboard. True PNG Alpha, isolated SINGLE character only.

'''


def extract_sources(frames):
    import cv2
    from PIL import Image
    video=SOURCE/'public-p2-research-source.mp4'; video_before=sha(video)
    index=read(SOURCE/'public-p2-pts.json')['video_frames']
    acquisition=read(SOURCE/'acquisition.json')
    assert video_before==acquisition['video']['sha256']
    cap=cv2.VideoCapture(str(video)); assert cap.isOpened()
    outputs={}; records=[]
    for frame in sorted(frames):
        row=index[frame]; assert row['index']==frame
        cap.set(cv2.CAP_PROP_POS_FRAMES,frame)
        ok,bgr=cap.read(); assert ok and int(cap.get(cv2.CAP_PROP_POS_FRAMES))==frame+1
        image=Image.fromarray(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)); assert image.size==(480,360)
        path=OUT/'references'/('public-p2-complete-frame-%d.png'%frame)
        path.parent.mkdir(parents=True,exist_ok=True); assert not path.exists(); image.save(path)
        outputs[frame]=path
        records.append(dict(image=rec(path),frame=row,dimensions=[480,360],full_camera_frame=True,
            crop=False,resize=False,limb_edit=False,reference_only_not_runtime=True))
    cap.release(); assert sha(video)==video_before
    save(OUT/'references/source-extraction-provenance.json',dict(video=rec(video),pts_index=rec(SOURCE/'public-p2-pts.json'),
        acquisition=rec(SOURCE/'acquisition.json'),method='OpenCV按已冻结源帧索引读完整480×360镜头；无裁切/缩放/重绘/背景分离。',
        records=records,source_bytes_unchanged=True,network_requests=0,image_posts=0,new_video_files=0))
    return outputs


def preview(phase,data,identity,mother,original):
    from PIL import Image,ImageDraw,ImageFont
    page=Image.new('RGB',(744,1110),'#30343d'); draw=ImageDraw.Draw(page)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
    title=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22)
    draw.text((16,10),'初代C型 phase%02d %s / 待根逐张审'%(phase,data['name']),font=title,fill='white')
    draw.text((16,48),'raw%d–%d；单张1024 / high / transparent；未占额、0 POST。'%(20+phase*4,23+phase*4),font=font,fill='#e0e3eb')
    draw.text((16,91),'参考1：干净canon（完整图）',font=font,fill='white')
    draw.text((380,91),'参考2：已接受02母相（完整图）',font=font,fill='white')
    for path,x in [(identity,16),(mother,380)]:
        with Image.open(path) as image:
            whole=image.convert('RGBA').resize((336,336),Image.Resampling.NEAREST if path==identity else Image.Resampling.LANCZOS)
            background=Image.new('RGBA',whole.size,'#30343d')
            page.paste(Image.alpha_composite(background,whole).convert('RGB'),(x,122))
    row=read(SOURCE/'public-p2-pts.json')['video_frames'][data['frame']]
    draw.text((16,485),'参考3：原镜头 %.3fs / %d'%(row['source_pts_seconds'],data['frame']),font=font,fill='white')
    with Image.open(original) as image:
        page.paste(image.resize((352,264),Image.Resampling.LANCZOS),(16,518))
    draw.text((384,485),'新相绝对姿态（没有新画稿）',font=font,fill='white')
    for at,line in enumerate(data['short']): draw.text((384,523+at*38),line,font=small,fill='white')
    lines=[
        '三参考都是完整画布等比缩略；新相独立整人，不链式编辑/旋转/拼肢。',
        '固定侧视，头右/右下、足左/左上；完整头、两手、两足都在画内。',
        'C型红银皮套自然连续，无玩具关节/开放腰缝/塑料光；保持像素。',
        '不画哥莫拉、地面、阴影、支撑、光效、文字或棋盘格。',
        '原剧出画部位按canon独立完整补全，不冒称原片提供全身定稿。',
        '每相根单独签精确SHA后串行POST；未来每单预占1，旧未知10保持。',
        '新scale/root/grip/override/hurtbox仍未定；不沿用杰顿root。',
        '只备料；没有运行注册、产品写、Godot、Git或新POST。',
    ]
    for at,line in enumerate(lines): draw.text((16,813+at*31),line,font=small,fill='#e0e3eb')
    path=OUT/'phases'/('phase-%02d'%phase)/'preflight-review.jpg'
    path.parent.mkdir(parents=True,exist_ok=True)
    for quality in [88,86,84,82,80]:
        page.save(path,quality=quality,optimize=True)
        if path.stat().st_size<=150000:break
    assert page.width<768 and path.stat().st_size<=150000
    return dict(**rec(path),dimensions=list(page.size),jpeg_quality=quality,all_reference_canvases_complete=True)


def main():
    assert not OUT.exists()
    review=MOTHER_DIR/'root-source-review.json'; assert sha(review)==REVIEW_SHA
    acceptance=read(review)
    assert acceptance['reviewer']=='root' and acceptance['accepted_as_independent_whole_source_candidate'] is True
    assert acceptance['runtime_data_authorized'] is False and acceptance['root'] is None and acceptance['source_to_native_scale'] is None
    mother=MOTHER_DIR/'candidate.png'; identity=ROOT/'art/fighters/ultraman/model/model-reference-x4.png'
    assert sha(mother)==acceptance['candidate']['sha256']
    contract=ROOT/'reports/review/2026-11-02/gomora-back-lift-next-receiver-readonly-v1/ultraman-c-whole-frame-contract.json'
    order=ROOT/'reports/review/2026-11-02/gomora-back-lift-ultraman-six-phase-order-readonly-v1/six-phase-state-order-contract.json'
    assert sha(contract)=='06bdc49b49e7fa7a3a66a237b73664bcac081fe3ae854864332796c37b466771'
    assert sha(order)=='ce61cf301d06a28beb116d2e5dfcb627181335b006a936c35e949fc0fda6d791'
    controls=[review,mother,MOTHER_DIR/'candidate.provider.png',MOTHER_DIR/'candidate.metadata.json',identity,contract,order,
        SOURCE/'public-p2-research-source.mp4',SOURCE/'public-p2-pts.json',SOURCE/'acquisition.json',
        ROOT/'assets/fighters/ultraman/animations/manifest.json',ROOT/'content/fighters/ultraman/state_frames.json',
        ROOT/'content/fighters/gomora/moves/special3.json',ROOT/'assets/fighters/zetton/animations/manifest.json']
    before={row['path']:row['sha256'] for row in map(rec,controls)}
    OUT.mkdir(parents=True)
    sources=extract_sources({data['frame'] for data in POSES.values()})
    sys.path.insert(0,str(ROOT/'tools'))
    import art.pipeline as client
    entries=[]
    for phase,data in POSES.items():
        directory=OUT/'phases'/('phase-%02d'%phase)
        directory.mkdir(parents=True)
        source=sources[data['frame']]
        references=[identity,mother,source]
        prompt=COMMON+'SOURCE EVIDENCE BOUNDARY: '+data['boundary']+'\n\n'+data['pose']
        brief=dict(schema=2,id='ultraman_c_gomora_back_lift_receiver_phase%02d_20261102_v1'%phase,
            fighter='ultraman',specific_version='现装初代奥特曼C型；非A/B或其它英雄',stage=5,
            action='gomora_super3_back_lift_receiver_independent_v1',frame=phase,phase_name=data['name'],
            asset_kind='character',size='1024x1024',quality='high',background='transparent',model='gpt-image-2.5-sunburst',
            route='仅项目tools/art/pipeline.py.generate_image；根逐张审核后串行提交',art_source='api_planned_not_submitted',
            references=[rec(p) for p in references],reference_roles=['干净canon本人身份/像素；不是目标姿态','同一个已接受02母相本人身份/解剖尺寸；非编辑底图','本相原剧完整镜头；实际动作边界见source_boundary'],
            accepted_common_mother=rec(mother),mother_root_acceptance=rec(review),
            original_motion_reference=rec(source),source_frame_index=data['frame'],
            source_pts_seconds=read(SOURCE/'public-p2-pts.json')['video_frames'][data['frame']]['source_pts_seconds'],
            source_motion_range=data['range'],source_boundary=data['boundary'],source_is_public_p2_pts=True,
            source_full_camera_frame=True,source_character_may_be_camera_clipped=True,
            contract=rec(contract),existing_variant_order=rec(order),
            raw_ticks=[20+phase*4,23+phase*4],duration_ticks=4,planned_state_index=data['state_index'],planned_clip_sprite=phase,
            actor_source_phase_context=data['actor_source'],new_independent_whole_frame=True,chain_edit=False,
            prior_new_phase_not_reference=True,pose_is_not_old_frame_rotation=True,
            source_to_native_scale=None,scale_profile=None,runtime_root=None,runtime_grip=None,
            actor_contact_point=None,hold_point_override=None,hurtboxes=None,
            runtime_registration_authorized=False,production_approved=False,submitted=False,installed=False,
            root_review_before_single_submission=True,prompt=prompt)
        save(directory/'brief.json',brief)
        (directory/'prompt.txt').write_text(prompt,encoding='utf-8')
        fields=client.image_fields(brief,None)
        assert fields['model']=='gpt-image-2.5-sunburst' and len(fields['prompt'].encode('utf-8'))<24000
        save(directory/'request-fields.json',fields)
        request_sha=hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest()
        output='art/fighters/ultraman/stage5/gomora-super3-back-lift-receiver-20261102-v1/phase-%02d/request-001/candidate.png'%phase
        assert not (ROOT/output).parent.exists()
        frozen=[rec(directory/'brief.json'),rec(directory/'request-fields.json'),rec(HERE/'submit_once.py'),rec(review),rec(contract),rec(order),*[rec(p) for p in references]]
        save(directory/'submission-plan.json',dict(schema=1,phase=phase,brief=rec(directory/'brief.json'),frozen_inputs=frozen,
            request_fields_sha256=request_sha,fixed_output=output,root_only_submit_one_phase=True,production_approved=False,
            future_reserve_usd='1',current_preparation_reserved_usd='0',cumulative_project_limit_usd='60',
            current_project_committed_context_usd='52.411415',historical_unknown_usd='10',
            user_reported_balance_usd='40.94',actual_account_balance_verified=False,
            no_retry_if_unknown=True,client_owns_budget_reservation_and_usage_settlement=True,posts_sent=0,installable=False))
        save(directory/'root-submit-acceptance.EXAMPLE.json',dict(reviewer='root',phase=phase,
            root_reviewed_exact_brief_and_all_three_references=False,authorized_one_serial_request=False,
            expected_submission_plan_sha256=sha(directory/'submission-plan.json'),
            expected_brief_sha256=sha(directory/'brief.json'),expected_request_fields_sha256=request_sha,
            fixed_output=output,reserve_usd='1',no_retry_if_unknown=True,
            note='未授权样例；根逐张实看并另写root-submit-acceptance.json，不能把本EXAMPLE当已签。'))
        page=preview(phase,data,identity,mother,source)
        entries.append(dict(phase=phase,name=data['name'],brief=rec(directory/'brief.json'),
            submission_plan=rec(directory/'submission-plan.json'),preview=page,
            request_fields_sha256=request_sha,planned_state_index=data['state_index'],clip_sprite=phase,
            root_review_pending=True,posts_sent=0))
    after={name:sha(ROOT/name) for name in before}; assert before==after
    save(OUT/'index.json',dict(entries=entries,accepted_mother_phase=2,mother_root_acceptance=rec(review),
        only_common_mother_used_no_chain=True,source_extraction=rec(OUT/'references/source-extraction-provenance.json'),
        next_step='根逐张审brief/三附件/小预审页并单独签；一次入口只执行指定相，绝不批量POST。',
        current_preparation_budget_reservation='0',future_each_request_reserve_usd='1',
        not_authorized_for_post_by_preparer=True,posts_sent=0,godot_run=False,product_writes=0,git_write=False))
    save(OUT/'readonly-byte-verification.json',dict(before=before,after=after,unchanged=True,
        original_mother_and_root_review_unchanged=True,old_contract_all_points_still_null=True,
        old_zetton_candidate_and_formal_wave_preserved=True,budget_ledger_not_written=True,
        posts_sent=0,art_or_product_writes=0,godot_runs=0,git_writes=0,generated_videos=0))
    (OUT/'README.md').write_text('''# 初代C型：其余五张独立完整源的离线简报

母相02经根受托实看独立整人通过，严格尺寸/注册/接触仍未验收。这里准备00/01/03/04/05五份绝对新姿态brief，每份同样附干净canon、同一个已接受02母相及本相原剧完整镜头；不引用其它新相，不链式编辑、旋转旧姿态或拼肢。母相仅作共同身份/真实骨尺参照，不强迫其它相匹配它的外框。

00落背缓冲是原片未拍的本作接入；01负重引用218.970；03抬升引用219.596；04卸重引用219.846；05后翻前相引用219.971。参考均从原已冻结公开P2研究视频离线按精确原帧索引解码完整480×360镜头，不裁切/缩放/分离或生成新视频。原镜头可能切掉原演员肢体，不能称作完整人物源；新人物仍按canon独立完整绘制。固定侧视下物理转体从胸腹俯伏逐步后翻，头在右/右下、足在左/左上，双臂和双腿随肩胸髋共同改变。

五份preflight-review.jpg均小于768宽与150KB，仅为完整参考缩略和精确姿态文字，没有新姿态画稿或虚构接触。index.json列各brief/plan/preview与SHA。相序沿既有variants方案，state0/1/4/5/2/3对应clip0/1/2/3/4/5；新scale/root/grip/override/hurtbox全null。杰顿后段root不会套入初代。

一次入口必须指定单相，默认只读，例如：

`C:/Users/13080/.codex/venvs/ufeneo/Scripts/python.exe -B tools/rebuild/gomora/ultraman_receiver_remaining_briefs_20261102_v1/submit_once.py --phase 00`

根逐张亲审后，将该相未授权EXAMPLE另存为同目录root-submit-acceptance.json，填写该相精确SHA与true，再加--execute单次调用项目generate_image。没有批量执行或全相自动授权入口。固定request-001目录和独占消费标记避免重复；异常/中断保未知，不重POST或改名，不释放旧未知10美元。实际POST前项目客户端每单预占1美元并按usage结算，本机累计60硬上限保持；准备期不预占。用户40.94是其提供余额，不声称接口核实。

本轮0新POST、预算预占、art/产品写、运行注册、Godot、Git。只写新tools/reports，原母相、原件、根review及旧合同/报告冻结。
''',encoding='utf-8')
    files=sorted(p for p in OUT.rglob('*') if p.is_file())+[HERE/'prepare.py',HERE/'submit_once.py']
    save(OUT/'prepared-owned-paths.json',dict(paths=[rec(p) for p in files],frozen_for_root_review=True,
        future_root_acceptance_and_execution_files_not_owned=True))
    print(json.dumps(dict(report=OUT.relative_to(ROOT).as_posix(),entries=entries,
        owned_sha256=sha(OUT/'prepared-owned-paths.json'),posts_sent=0,budget_reserved=False),ensure_ascii=False))


if __name__=='__main__': main()

"""只备初代C型单张最低承重母相brief、缩略预审页及一次提交计划；绝不生图。"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'reports/review/2026-11-02/gomora-back-lift-ultraman-phase02-brief-v1'
PYTHON = Path('C:/Users/13080/.codex/venvs/ufeneo/Scripts/python.exe')
CONTRACT = ROOT / 'reports/review/2026-11-02/gomora-back-lift-next-receiver-readonly-v1/ultraman-c-whole-frame-contract.json'
CONTRACT_SHA = '06bdc49b49e7fa7a3a66a237b73664bcac081fe3ae854864332796c37b466771'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rec(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path), bytes=path.stat().st_size)


def save(name, data):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def preview(reference, original):
    from PIL import Image, ImageDraw, ImageFont
    page = Image.new('RGB', (744, 1040), '#30343d')
    draw = ImageDraw.Draw(page)
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 18)
    title = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 22)
    draw.text((16, 10), '初代C型 / phase02 最低承重母相 / 待根审', font=title, fill='white')
    draw.text((16, 48), '单张1024×1024 / high / 真透明PNG；当前0 POST、未占额。', font=font, fill='#e0e3eb')
    draw.text((16, 85), '参考1：本人干净整图（身份/像素）', font=font, fill='white')
    draw.text((384, 85), '参考2：原PTS完整镜头（负重方向）', font=font, fill='white')
    with Image.open(reference) as picture:
        small = picture.resize((320, 320), Image.Resampling.NEAREST)
        page.paste(small, (16, 116), small)
    with Image.open(original) as picture:
        small = picture.resize((344, 278), Image.Resampling.LANCZOS)
        page.paste(small, (384, 116))
    draw.text((16, 446), '上方均为完整参考等比缩略；没有新姿态画稿或虚构接触。', font=font, fill='#e0e3eb')
    lines = [
        '只画初代C型完整一人，固定侧视；新绘头向右、足向左。',
        '胸腹向下横伏，腹腰自然承重微弯，头颈向右微垂。',
        '近远双臂自然垂落、双手高低不同；肩胸髋共同受力。',
        '两腿从左侧越出，近膝较收、远膝较松，双足完整。',
        '原剧镜头朝左；只取负重依据，不复制镜头、地面或哥莫拉。',
        '生成独立整帧；禁止旋转站姿、切肢、拼接、后贴肢体。',
        '像素画风、红银皮套连续；禁止玩具轴、球关节、塑料光。',
        '不画哥莫拉、地面、影子、文字、光效、棋盘格或支撑物。',
        '全头、双手双足完整；四周透明留白，不按外框放大填满。',
        '原剧只支持负重；原始起抓和本作捕获规则没有在此证明。',
        '腹腰/背缘、grip、root、override仍为null，新源返回后再测。',
        '一次提交入口默认只读；根另写精确授权后才预占1美元。',
        '若结果未知保留原占额，永不重POST；旧未知10美元保留。',
        '本次不准备其余五相生产；不改产品、不运行Godot或Git。',
    ]
    for at, line in enumerate(lines):
        draw.text((16, 491+at*34), line, font=font, fill='white' if at<4 else '#e0e3eb')
    path = OUT / 'phase02-preflight-review.jpg'
    page.save(path, quality=88, optimize=True)
    assert page.width < 768 and path.stat().st_size < 150000
    return rec(path)


def main():
    assert not OUT.exists()
    assert sha(CONTRACT) == CONTRACT_SHA
    identity = ROOT / 'art/fighters/ultraman/model/model-reference-x4.png'
    native = ROOT / 'assets/fighters/ultraman/model-native.png'
    original = ROOT / 'reports/review/2026-11-02/gomora-super2-newsource-v1/p2-back-lift-full-000-000.jpg'
    source_decision = ROOT / 'reports/review/2026-11-02/gomora-super3-back-lift-contract-v1/source-decision.json'
    original_pages = json.loads(source_decision.read_text('utf-8-sig'))['actual_opened_everyframe_pages']
    controls = [CONTRACT, identity, native, original, source_decision,
        ROOT/'content/fighters/ultraman/canon.json', ROOT/'content/fighters/ultraman/definition.json',
        ROOT/'content/fighters/ultraman/state_frames.json', ROOT/'assets/fighters/ultraman/animations/manifest.json',
        ROOT/'content/fighters/gomora/moves/special3.json', ROOT/'assets/fighters/zetton/animations/manifest.json',
        ROOT/'reports/review/2026-11-02/gomora-super3-resume-front-v1/install-plan.json',
        ROOT/'presentation/ko_finish_presentation.gd'] + [ROOT/row['path'] for row in original_pages]
    before = {row['path']:row['sha256'] for row in map(rec,controls)}
    from PIL import Image
    with Image.open(identity) as expanded, Image.open(native) as canonical:
        assert expanded.mode == canonical.mode == 'RGBA'
        assert expanded.size == (768,768) and canonical.size == (192,192)
        assert expanded.tobytes() == canonical.resize(expanded.size, Image.Resampling.NEAREST).tobytes()
    OUT.mkdir(parents=True)
    doctor = Path('C:/Users/13080/.codex/skills/generate2dmedia/scripts/forge_doctor.py')
    result = subprocess.run([str(PYTHON), '-B', str(doctor), '--host-tools','none','--no-exec','--json',
        '--save',str(OUT/'capability/doctor.json')], cwd=ROOT, capture_output=True, timeout=45)
    assert (OUT/'capability/doctor.json').is_file(), result.returncode
    save('capability/project-route-policy.json', dict(
        doctor_exit_code=result.returncode, doctor_network_requested=False,
        user_override='只用项目generate_image及现有官方GPT Image；不使用Forge通用路由或视频。',
        art_source='api_planned_not_submitted', key_or_token_written=False))
    prompt = '''Draw exactly ONE NEW INDEPENDENT COMPLETE full-body animation frame of the original ULTRAMAN, the standard 1966 C-type suit used by this game's accepted canon. Fixed SIDE-VIEW arcade fighting camera. Transparent 1024x1024 PNG, quality HIGH, 透明背景，真正PNG Alpha透明. Only Ultraman is drawn.

REFERENCE 1 is the accepted clean complete C-type PIXEL identity model, exactly four-times nearest-neighbor enlargement of the current canonical native model. It defines identity, actual anatomical proportions, red/silver pattern topology, mask, colors and pixel finish ONLY. Do not copy its upright guarded pose. It is NOT the older prototype model.png. REFERENCE 2 is a COMPLETE UNCROPPED public original-film camera frame at P2 PTS 218.970 seconds, showing the chest-down lowest loaded-back situation. It defines only the natural belly-down loaded posture and connected suit anatomy, not the game's character scale or output style. The film monster faces LEFT; the requested NEW drawing has the opposite staging described below. Do NOT copy its background, monster, photographic texture, film crop or labels. This shot already begins with the receiver on the back; it does not prove the initial capture.

NEW PHASE 02 OF SIX — LOWEST CHEST-DOWN LOAD. The character's BODY is roughly horizontal with his HEAD at the RIGHT end of the image and BOTH FEET at the LEFT end. Chest and abdomen face DOWN; back faces UP. The head, neck, shoulders, chest, waist and pelvis are one continuous, naturally yielding suit-covered body. The abdomen/waist has a small natural supported compression/sloping curve as if lying across a broad unseen back, with shoulders and pelvis following that load. Do not break the waist, shorten the torso or draw a prone push-up. The head and neck extend slightly past the RIGHT side of the support and droop a little, face turned naturally toward RIGHT/down while remaining recognizable as this C-type mask.

BOTH connected arms hang naturally DOWN under gravity on the near and far sides of the unseen support. Near shoulder rolls slightly forward/down and its elbow is gently bent; the far shoulder and far elbow follow a DIFFERENT natural lower angle, with hands at visibly different heights. Draw TWO complete hands and TWO coherent shoulder-elbow-wrist chains through natural occlusion. Neither arm remains frozen in guard; neither hand touches a floor, holds a rail or braces a push-up. BOTH legs extend from the left side of the pelvis across the unseen support's LEFT edge. The near knee is a little more drawn up/flexed while the far knee is more relaxed and its lower leg lags at a different angle. Draw TWO distinct connected thighs, knees, lower legs and TWO complete feet; no symmetrical glued legs, missing far leg or duplicated foot. This is the lowest compressed load BEFORE the back rises, not the later upright lift, airborne back-flip, supine fall or a sleeping/crawling pose.

Match the accepted C-type identity: clean silver C-type mask and mouth, its central silver head fin, pale yellow eyes, the accepted silver/red one-piece suit and correct chest Color Timer when naturally visible; do not paint a timer on the back just to make it visible. Not A-type, B-type, Seven, Taro or another hero. Keep the same head/skull, shoulder, chest, pelvis, thigh, shin and foot lengths as reference 1; pose bending does not shrink anatomy. Crisp intentional fighting-game pixel clusters, restrained red/silver/grey palette, thin dark pixel contour, coherent upper-left light. Far-side limb shading is naturally painted in the new complete image. No photographic suit texture, smooth vector painting or 3D render.

All skin/suit surfaces at shoulders, elbows, wrists, waist, hips, knees and ankles are continuous and natural. NO toy ball joints, pivots, discs, peg sockets, straight open torso seams, screw holes, stands, mannequin/stock dummy or plastic gloss. Independently paint the entire character in this absolute pose. NO cut-body layers, limb rotation, rigging, IK, pasted parts, rotation of the old upright or supine frame, anatomical stretching or per-frame bbox fitting.

Show the ENTIRE single character including full head fin, both hands and both feet with at least 48 output pixels of clear breathing room on every side. Reserve clear space below the hanging hands and around the asymmetrical legs. Keep generous transparent padding, never inflate the character merely to fill the square. The final uniform source-to-native scale and semantic abdomen contact point will be measured AFTER this new complete source is actually reviewed. Do not draw registration dots, anchors or guides.

Draw NO GOMORA, no opponent, no support object or silhouette under the abdomen, no floor, ground, shadow, scenery, dummy, burden, weapon, effect, aura, glow, beam, dust, motion trail, ghost, lettering, number, panel border, grid, black/white/chroma background or checkerboard. The character alone on real PNG Alpha transparency. Transparent background, truly clear outside the subject. This output is a new candidate, not an approved installed game frame.
'''
    brief = dict(schema=2, id='ultraman_c_gomora_back_lift_receiver_phase02_20261102_v1',
        fighter='ultraman', specific_version='现装初代奥特曼C型；不是A/B制作皮套或其它英雄',
        stage=5, action='gomora_super3_back_lift_receiver_independent_v1', frame=2,
        phase_name='最低胸腹朝下承重母相', asset_kind='character', size='1024x1024',
        quality='high', background='transparent', model='gpt-image-2.5-sunburst',
        route='仅tools/art_pipeline.py.generate_image；实际官方路由/模型由执行时配置核实',
        art_source='api_planned_not_submitted', references=[rec(identity),rec(original)],
        reference_roles=['本人身份/完整体尺/像素画风；非所求姿态', '原剧完整镜头；负重方向与皮套连续性，不抄摄影/朝向/哥莫拉/地面'],
        frozen_contract=rec(CONTRACT), canon_native=rec(native), source_decision=rec(source_decision),
        source_pts_seconds=[218.970,219.304], original_is_public_p2_pts_not_full_episode_clock=True,
        full_original_reference_cropped=False, original_character_is_partly_camera_occluded=True,
        raw_ticks=[28,31], duration_ticks=4, request_is_single_whole_frame=True,
        orientation=dict(camera='固定侧视', actor_facing=1, head_end='右', feet_end='左', chest_abdomen='下'),
        scale_profile=None, source_to_native_scale=None, runtime_root=None, runtime_grip=None,
        actor_contact_point=None, hold_point_override=None, runtime_cell_pending_measurement=True,
        submitted=False, installed=False, production_approved=False, root_review_before_submission=True,
        other_five_phases_not_prepared=True, prompt=prompt)
    save('brief.json', brief)
    (OUT/'prompt.txt').write_text(prompt, encoding='utf-8')
    review = preview(identity, original)
    save('reference-provenance.json', dict(
        references=[rec(identity),rec(original)], native=rec(native), x4_is_exact_nearest_whole_native=True,
        source_bytes_unchanged=True, original_full_camera_frame_not_alpha_crop=True,
        original_orientation='左向怪兽/受方头左足右；新绘合同固定头右足左',
        reference_use_is_not_new_generation=True, preview=review,
        preview_resized_for_readability_only=True, preview_is_not_runtime_art=True))
    sys.path.insert(0,str(ROOT/'tools'))
    import art_pipeline as client
    fields = client.image_fields(brief, None)
    assert fields['model'] == 'gpt-image-2.5-sunburst'
    save('request-fields.json', fields)
    frozen = [rec(OUT/'brief.json'),rec(OUT/'request-fields.json'),rec(CONTRACT),rec(identity),rec(native),rec(original),
        rec(source_decision),rec(HERE/'submit_once.py')]
    fixed_output = 'art/fighters/ultraman/stage5/gomora-super3-back-lift-receiver-20261102-v1/phase-02/request-001/candidate.png'
    assert not (ROOT/fixed_output).parent.exists()
    request_sha = hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest()
    save('submission-plan.json', dict(schema=1, brief=rec(OUT/'brief.json'), frozen_inputs=frozen,
        request_fields_sha256=request_sha, fixed_output=fixed_output,
        future_reserve_usd='1', current_preparation_reserved_usd='0',
        cumulative_project_limit_usd='60', historical_unknown_usd='10',
        historical_unknown_id='011ff77710ed49c9b441ed80f91733be',
        user_reported_balance_usd='40.94', actual_account_balance_verified=False,
        client_owns_reservation_and_actual_usage_settlement=True, no_retry_if_unknown=True,
        one_attempt_marker='execution/one-attempt.json', root_only_submit=True,
        production_approved=False, installable=False, posts_sent=0))
    save('root-submit-acceptance.EXAMPLE.json', dict(reviewer='root',
        root_reviewed_exact_brief_and_references=False, authorized_one_serial_request=False,
        expected_submission_plan_sha256=sha(OUT/'submission-plan.json'),
        expected_brief_sha256=sha(OUT/'brief.json'), expected_request_fields_sha256=request_sha,
        fixed_output=fixed_output, reserve_usd='1', no_retry_if_unknown=True,
        note='此为未授权样例；根亲审后另写root-submit-acceptance.json才可执行。'))
    before_after = {name:sha(ROOT/name) for name in before}
    assert before == before_after
    save('readonly-byte-verification.json', dict(before=before,after=before_after,unchanged=True,
        old_contract_all_contact_fields_unchanged_null=True, preparation_posts=0, budget_reservations=0,
        art_or_product_writes=0, godot_runs=0, git_writes=0, user_game_data_accessed=False))
    (OUT/'README.md').write_text('''# 初代C型最低承重母相：单张简报，待根审

只准备phase02最低胸腹向下承重母相。身份参考为当前canon整图的精确4倍model-reference-x4，不使用旧prototype的model.png；第二张为原PTS218.970完整镜头，原片朝左，合同新绘固定头右足左。两者均直接作为generate_image附件，不只写在提示词里。胸腹承重/双臂下垂/两腿不同屈度、完整连续皮套、像素和真Alpha约束已写入brief。原片起抓、完整被遮肢体与本作捕获规则没有被该参考证明。

`phase02-preflight-review.jpg`小于768宽及150KB，只作可读预审；没有新姿态画稿、代码人物或虚构配对。原合同和全部语义接触/root保持null，未复制杰顿。其余五相未生产，当前正式三级波和杰顿未装候选保持。

根先看brief/参考/预审页，再将未授权EXAMPLE另存为root-submit-acceptance.json，按实际审过结果填写两个true及精确SHA。一次提交工具默认仅只读预检：

`C:/Users/13080/.codex/venvs/ufeneo/Scripts/python.exe -B tools/rebuild/gomora/ultraman_receiver_phase02_brief_20261102_v1/submit_once.py`

根审核后才加`--execute`。入口固定输出目录，调用项目generate_image一次；并发1，由该客户端实际POST前预占1美元、按usage结算。例外或中断保留一次消费标记和预算未知，不自动重POST、不换输出目录、不释放旧未知10美元。预检不解密密钥、不访问网络、不写预算。返回候选后仍需根实看身份、全身、像素、真Alpha及实际比例，不能自动安装。

本目录准备过程0 POST、预算预占、art/产品写、Godot或Git。Forge doctor只作本机只读能力记录；用户指定项目官方路由覆盖通用路由/视频建议。
''',encoding='utf-8')
    files=sorted(path for path in OUT.rglob('*') if path.is_file())+[HERE/'prepare.py',HERE/'submit_once.py']
    save('prepared-owned-paths.json',dict(paths=[rec(path) for path in files],
        frozen_for_root_review=True, future_root_execution_files_not_precreated=True))
    print(json.dumps(dict(report=OUT.relative_to(ROOT).as_posix(),brief_sha256=sha(OUT/'brief.json'),
        plan_sha256=sha(OUT/'submission-plan.json'),owned_sha256=sha(OUT/'prepared-owned-paths.json'),
        preview=review, posts_sent=0,budget_reserved=False),ensure_ascii=False))


if __name__=='__main__':
    main()

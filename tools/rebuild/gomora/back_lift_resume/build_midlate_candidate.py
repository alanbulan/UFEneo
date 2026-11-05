"""方案A仅替换t27完整受方相；新内存合同，不安装或覆盖旧证据。"""
from pathlib import Path
import copy
import hashlib
import json
import sys
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools/rebuild/shared'))
import forge_backend as forge
BASE = ROOT / 'reports/gomora-builtin/main-chain-20261105/contract-roi-corrected.json'
OUT = ROOT / 'reports/gomora-builtin/main-midlate-a-20261105'
SOURCE = ROOT / 'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-midlate-20261105/candidate-2.png'
REVIEW = SOURCE.with_name('review-2.json')
POSE = 'gomora_back_lift_receiver'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not OUT.exists(), '不得覆盖历史输出'
    original = json.loads(BASE.read_text())
    cfg = copy.deepcopy(original)
    for resource in original['bound_resources']:
        assert sha(Path(resource['path'])) == resource['sha256']
    review = json.loads(REVIEW.read_text())
    assert sha(SOURCE) == review['sha256']
    assert review['fixed_whole_size'] == [210, 105] and review['native_pelvis'] == [101, 74]
    im = Image.open(SOURCE).convert('RGBA').resize((210, 105), Image.Resampling.NEAREST)
    original_pixels = np.asarray(im).copy()
    binary = forge.binarize_alpha(im.copy())
    im.putalpha(binary.getchannel('A'))
    assert np.array_equal(original_pixels[..., :3], np.asarray(im)[..., :3])
    assert np.array_equal(np.asarray(im)[..., 3], np.where(original_pixels[..., 3] >= 128, 255, 0))
    assert im.getpixel((137, 64))[3] == 255
    actor = Image.open(ROOT / 'art/fighters/gomora/stage4/super3-back-lift-registration/current/06.png')
    assert actor.getpixel((251, 185))[3] >= 128
    cell = Image.new('RGBA', (256, 320))
    cell.paste(im, (21, 140))
    assert np.count_nonzero(np.asarray(cell)[..., 3]) == np.count_nonzero(np.asarray(im)[..., 3])
    clip = cfg['clips']['ultraman'][POSE]
    atlas = Image.open(clip['texture']).convert('RGBA')
    assert atlas.size == (256*15, 320)
    new_atlas = Image.new('RGBA', (256*16, 320))
    new_atlas.paste(atlas, (0, 0)); new_atlas.paste(cell, (256*15, 0))
    assert np.array_equal(np.asarray(atlas), np.asarray(new_atlas)[:, :256*15])
    hurt = []
    alpha = np.asarray(cell)[..., 3] > 0
    for bottom in range(320, 0, -16):
        top = max(0, bottom-16); ys, xs = np.where(alpha[top:bottom])
        if len(xs):
            hurt.append([int(xs.min())-128, 288-(top+int(ys.max())+1), int(xs.max()-xs.min()+1), int(ys.max()-ys.min()+1)])
    cfg['receiver_states'][POSE].append({'sprite':15,'dx':0,'dy':0,'hitboxes':[],'hurtboxes':hurt,'cancel':[],'events':[],'grab_points':{'waist':[-6,74]}})
    frame = cfg['move']['frames'][27]
    assert frame['sprite'] == 6
    frame['target'] = {'mode':'hold','pose':POSE,'sprite':15,'facing':1,'root':[0,0],'grip':[-5,119],
                       'hold_point_overrides':{'ultraman':{POSE:{'15':[30,84]}}}}
    for t in range(76):
        if t != 27:assert cfg['move']['frames'][t] == original['move']['frames'][t]
    assert cfg['receiver_states'][POSE][:15] == original['receiver_states'][POSE]
    assert cfg['move']['throw_current_capture'] == original['move']['throw_current_capture']
    cfg['pelvis_cell_readpoints'].append([122,214]);cfg['receiver_labels'].append('midlate_v2_support_A')
    registration = {'sprite':15,'label':'midlate_v2_support_A','source':str(SOURCE),'source_sha256':sha(SOURCE),
                    'fixed_size':[210,105],'fixed_paste':[21,140],'cell_pelvis':[122,214],'local_pelvis':[-6,74],
                    'alpha_threshold':128,'rgb_unchanged':True,'full_resized_rectangle_in_cell':True,
                    'method':'NEAREST whole-image resize; adopt forge_backend.binarize_alpha A channel only; retain all RGB'}
    cfg['chain_registration'].append(registration)
    cfg['chain_pairs'][7] = {'tick':27,'receiver':'midlate_v2_support_A','actor':6,'grip':[-5,119],'hold_point':[30,84],'root':[-35,35]}
    cfg['midlate_plan_A'] = {'base_contract':str(BASE),'base_sha256':sha(BASE),'changed_ticks':[27],
                            'pelvis_actor_canvas':[215,195],'receiver_contact_resized':[137,64],
                            'actor_contact_canvas':[251,185],'root':[-35,35],
                            'study_commit':'17909b25','art_accepted':False,'installed':False}
    OUT.mkdir(parents=True)
    atlas_path = OUT / 'receiver.png';new_atlas.save(atlas_path)
    clip['texture'] = str(atlas_path);clip['rects'].append([256*15,0,256,320]);clip['anchors'].append([128,288]);clip['ticks'].append(4)
    for p in [BASE,SOURCE,REVIEW,Path(__file__),atlas_path]:cfg['bound_resources'].append({'path':str(p.resolve()),'sha256':sha(p)})
    cfg['accepted'] = False;cfg['installed'] = False
    path = OUT / 'contract.json';path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'contract':str(path),'sha256':sha(path),'only_runtime_frame_change':27,'root':[-35,35],'installed':False}))

if __name__ == '__main__':
    main()

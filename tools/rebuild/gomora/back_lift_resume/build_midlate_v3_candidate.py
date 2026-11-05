"""第三版仅替换t27/t28完整受方相；新内存合同，不安装或覆盖旧证据。"""
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
BASE = ROOT / 'reports/gomora-builtin/main-midlate-groundfx-20261105/contract.json'
OUT = ROOT / 'reports/gomora-builtin/main-midlate-v3-20261105'
SOURCE = ROOT / 'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-midlate-20261105/candidate-3.png'
REVIEW = SOURCE.with_name('review-3.json')
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
    assert sha(SOURCE) == review['source_sha256']
    assert review['fixed_whole_size'] == [168, 154] and review['native_pelvis'] == [73, 82]
    im = Image.open(SOURCE).convert('RGBA').resize((168, 154), Image.Resampling.NEAREST)
    original_pixels = np.asarray(im).copy()
    binary = forge.binarize_alpha(im.copy())
    im.putalpha(binary.getchannel('A'))
    assert np.array_equal(original_pixels[..., :3], np.asarray(im)[..., :3])
    assert np.array_equal(np.asarray(im)[..., 3], np.where(original_pixels[..., 3] >= 128, 255, 0))
    assert im.getpixel((103, 72))[3] == 255
    actor = Image.open(ROOT / 'art/fighters/gomora/stage4/super3-back-lift-registration/current/06.png')
    assert actor.getpixel((246, 187))[3] >= 128
    cell = Image.new('RGBA', (256, 320))
    cell.paste(im, (49, 132))
    assert np.count_nonzero(np.asarray(cell)[..., 3]) == np.count_nonzero(np.asarray(im)[..., 3])
    clip = cfg['clips']['ultraman'][POSE]
    atlas = Image.open(clip['texture']).convert('RGBA')
    assert atlas.size == (256*16, 320)
    assert atlas.getpixel((256*15+158,204))[3]>=128
    actor7=Image.open(ROOT / "art/fighters/gomora/stage4/super3-back-lift-registration/current/07.png")
    assert actor7.getpixel((255,184))[3]>=128
    new_atlas = Image.new('RGBA', (256*17, 320))
    new_atlas.paste(atlas, (0, 0)); new_atlas.paste(cell, (256*16, 0))
    assert np.array_equal(np.asarray(atlas), np.asarray(new_atlas)[:, :256*16])
    hurt = []
    alpha = np.asarray(cell)[..., 3] > 0
    for bottom in range(320, 0, -16):
        top = max(0, bottom-16); ys, xs = np.where(alpha[top:bottom])
        if len(xs):
            hurt.append([int(xs.min())-128, 288-(top+int(ys.max())+1), int(xs.max()-xs.min()+1), int(ys.max()-ys.min()+1)])
    cfg['receiver_states'][POSE].append({'sprite':16,'dx':0,'dy':0,'hitboxes':[],'hurtboxes':hurt,'cancel':[],'events':[],'grab_points':{'waist':[-6,74]}})
    frame = cfg['move']['frames'][27]
    assert frame['sprite'] == 6
    frame['target'] = {'mode':'hold','pose':POSE,'sprite':16,'facing':1,'root':[0,0],'grip':[-10,117],
                       'hold_point_overrides':{'ultraman':{POSE:{'16':[24,84]}}}}
    cfg['move']['frames'][28]['target']={'mode':'hold','pose':POSE,'sprite':15,'facing':1,'root':[0,0],'grip':[-1,120],'hold_point_overrides':{'ultraman':{POSE:{'15':[30,84]}}}}
    for t in range(76):
        if t not in [27,28]:assert cfg['move']['frames'][t] == original['move']['frames'][t]
    assert cfg['receiver_states'][POSE][:16] == original['receiver_states'][POSE]
    assert cfg['move']['throw_current_capture'] == original['move']['throw_current_capture']
    cfg['pelvis_cell_readpoints'].append([122,214]);cfg['receiver_labels'].append('midlate_v3_bridge')
    registration = {'sprite':16,'label':'midlate_v3_bridge','source':str(SOURCE),'source_sha256':sha(SOURCE),
                    'fixed_size':[168,154],'fixed_paste':[49,132],'cell_pelvis':[122,214],'local_pelvis':[-6,74],
                    'alpha_threshold':128,'rgb_unchanged':True,'full_resized_rectangle_in_cell':True,
                    'method':'NEAREST whole-image resize; adopt forge_backend.binarize_alpha A channel only; retain all RGB'}
    cfg['chain_registration'].append(registration)
    cfg['chain_pairs'][7] = {'tick':27,'receiver':'midlate_v3_bridge','actor':6,'grip':[-10,117],'hold_point':[24,84],'root':[-34,33]}
    cfg['chain_pairs'][8]={'tick':28,'receiver':'midlate_v2_support_A','actor':7,'grip':[-1,120],'hold_point':[30,84],'root':[-31,36]}
    cfg['midlate_v3_plan'] = {'base_contract':str(BASE),'base_sha256':sha(BASE),'changed_ticks':[27,28],
                            'pelvis_actor_canvas':[216,197],'receiver_contact_resized':[103,72],
                            'actor_contact_canvas':[246,187],'root':[-34,33],
                            'study_commit':'ae78d8e7','art_accepted':False,'installed':False}
    OUT.mkdir(parents=True)
    atlas_path = OUT / 'receiver.png';new_atlas.save(atlas_path)
    clip['texture'] = str(atlas_path);clip['rects'].append([256*16,0,256,320]);clip['anchors'].append([128,288]);clip['ticks'].append(4)
    for p in [BASE,SOURCE,REVIEW,Path(__file__),atlas_path]:cfg['bound_resources'].append({'path':str(p.resolve()),'sha256':sha(p)})
    cfg['accepted'] = False;cfg['installed'] = False
    path = OUT / 'contract.json';path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'contract':str(path),'sha256':sha(path),'only_runtime_frame_changes':[27,28],'root':[-34,33],'installed':False}))

if __name__ == '__main__':
    main()

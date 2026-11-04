"""为正式main生成只读月亮三连候选合同；只绑定已签收的整图资源。"""
import argparse
import copy
import json
from pathlib import Path
from PIL import Image
import check
import register

ROOT = check.ROOT
HERE = Path(__file__).resolve().parent


def build(manifest_path, output):
    manifest = check.read(manifest_path)
    if manifest['schema'] != 'ufeneo.luna.light-chain-registered-candidate.v1':
        raise ValueError('不是已配准月亮候选包')
    check.checked(manifest['registration_review'])
    fid = 'ultraman-arc__luna'
    resources = {manifest_path, check.checked(manifest['registration_review'])}
    resources.update(check.checked(value) for value in manifest['processing_tools'].values())
    clips, moves = {}, {}
    for action, group in manifest['actions'].items():
        clip_path, move_path = check.checked(group['clip']), check.checked(group['move'])
        check.checked(group['rule_reference'])
        clips[action], moves[action] = check.read(clip_path), check.read(move_path)
        texture = clips[action]['texture']
        atlas = ROOT / texture.removeprefix('res://') if texture.startswith('res://') else Path(texture)
        clips[action]['texture'] = atlas.as_posix()
        if register.sha(atlas) != clips[action]['atlas_sha256']:
            raise ValueError('图集SHA改变')
        with Image.open(atlas) as image:
            if image.size != (320*len(group['frames']),320):
                raise ValueError('图集尺寸不符')
        resources.update([clip_path, move_path, atlas])
        for row in group['frames']:
            resources.add(check.checked(row['image']))
            resources.add(check.checked({'path':row['sample'],'sha256':row['sha256']}))
    prior = check.STAGE / 'movement-contract-20261101-v1'
    bundle, states = check.read(prior/'bundle.json'), check.read(prior/'state_frames.json')
    resources.update([prior/'bundle.json',prior/'state_frames.json'])
    for action in ['idle','turn']:
        clips[action] = copy.deepcopy(bundle['clips'][action])
        atlas = check.STAGE / 'goal-closeout-20261101-v1' / action / 'atlas.png'
        if register.sha(atlas) != clips[action]['atlas_sha256']:
            raise ValueError(f'{action}本人图集缺失或SHA不符')
        clips[action]['texture'] = atlas.as_posix()
        clips[action]['source_fighter'] = fid
        resources.add(atlas)
    flags_path = ROOT / f'content/fighters/{fid}/definition.json'
    flags = check.read(flags_path)
    if any(flags[k] for k in ['implemented','playable','select_visible']):
        raise ValueError('禁止开放未完成装甲')
    model = ROOT / f'art/fighters/{fid}/model/model-native.png'
    with Image.open(model) as image:
        image.verify()
    commands_path = ROOT / 'content/fighters/ultraman-arc/command_table.json'
    commands = [row for row in check.read(commands_path) if row['move'] in moves]
    resources.update([model, flags_path, commands_path])
    for folder in ['core','input','content','presentation','app','ui','third_party/shoto']:
        resources.update(p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in {'.gd','.json','.tres','.tscn','.gdshader'})
    for folder in [ROOT/'tests/review/fighters/ultraman-arc/luna_light_chain', ROOT/'tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1']:
        resources.update(folder.glob('*.gd'))
    cfg = {'schema':'ufeneo.luna.light-chain-main-candidate.v1','root_runtime_ready':True,'fighter':fid,'opponent':'zetton',
           'playable':False,'implemented':False,'transform_enabled':False,'select_visible':False,
           'definition':{'id':fid,'display_name':'亚刻奥特曼 · 月亮装甲 · 三连候选','max_health':1000,'walk_speed':2,'jump_speed':16,'body_radius':18,
                         'moves':moves,'command_table':commands,'state_frames':{action:states[action] for action in ['idle','turn']}},
           'presentation':{'model':model.as_posix(),'native':True,'anchor_y':280,'manifest_data':{'fighter':fid,'clips':clips}},
           'bound_resources':[{'path':p.as_posix(),'sha256':register.sha(p)} for p in sorted(resources)],
           'manifest':register.ref(manifest_path),'main_game_accepted':False,'replay_accepted':False}
    output = output.resolve()
    output.relative_to(ROOT/'reports/luna-light-chain-resume')
    register.save(output, cfg)
    return register.ref(output)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(build(args.manifest.resolve(),args.output),ensure_ascii=False))

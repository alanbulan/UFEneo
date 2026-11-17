"""七槽候选独立静态检查；重建完整源，不执行Godot、不改正式资源。"""
import copy
import importlib.util
import json
from pathlib import Path
import sys
from PIL import Image
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import main_bundle as bundle

def main():
    manifest=bundle.read(bundle.DEFAULT_MANIFEST)
    paths=[bundle.ROOT/f'content/fighters/{bundle.FID}/definition.json',bundle.ROOT/'content/fighters/ultraman-arc/moves/crush.json',bundle.ROOT/'content/fighters/ultraman-arc/command_table.json']
    before={str(p):bundle.sha(p) for p in paths}
    for key in ['registration_plan','geometry','geometry_tool']:bundle.checked(manifest[key])
    bundle.processing_resources(manifest)
    spec=importlib.util.spec_from_file_location('crush_geometry_check',bundle.checked(manifest['geometry_tool']))
    geometry=importlib.util.module_from_spec(spec);spec.loader.exec_module(geometry)
    images,actual=geometry.build_frames(plan_path=bundle.checked(manifest['registration_plan']))
    images2,actual2=geometry.build_frames(plan_path=bundle.checked(manifest['registration_plan']))
    assert actual==actual2
    assert json.loads(json.dumps(actual))==bundle.read(bundle.checked(manifest['geometry']))
    assert len(images)==len(images2)==7
    clocks=bundle.manifest_clocks(manifest)
    for action,ticks in clocks.items():
        rows=manifest['actions'][action]['frames'];clip=bundle.read(bundle.checked(manifest['actions'][action]['clip']))
        assert clip['ticks']==ticks and clip['anchors']==[[160,280]]*len(rows)
        atlas_path=bundle.checked({'path':clip['texture'],'sha256':clip['atlas_sha256']})
        with Image.open(atlas_path) as atlas:
            assert atlas.size==(320*len(rows),320) and atlas.mode=='RGBA'
            for i,row in enumerate(rows):
                source=bundle.checked({'path':row['source'],'sha256':row['source_sha256']})
                image=bundle.checked({'path':row['image'],'sha256':row['image_sha256']})
                expected=images[i] if action=='crush' else images[0]
                with Image.open(image) as im,Image.open(bundle.checked(row['whole_source_sample'])) as sample,Image.open(source) as original:
                    assert im.tobytes()==expected.tobytes()
                    if action=='crush':assert im.tobytes()==images2[i].tobytes()
                    assert atlas.crop((320*i,0,320*(i+1),320)).tobytes()==im.tobytes()
                    assert abs((sample.width/original.width)/(sample.height/original.height)-1)<0.01
                    reconstruction=Image.new('RGBA',(320,320));reconstruction.paste(sample,tuple(row['whole_source_destination_offset']))
                    assert reconstruction.tobytes()==im.tobytes()
                assert row['phase']==i and row['ticks']==ticks[i]
        bundle.state_frames(rows)
    rows=manifest['actions']['crush']['frames'];idle=manifest['actions']['idle']['frames'][0]
    assert images[0].tobytes()==images[-1].tobytes()
    assert rows[0]['source_sha256']==rows[-1]['source_sha256']==idle['source_sha256']
    assert rows[0]['image_sha256']==rows[-1]['image_sha256']==idle['image_sha256']
    assert rows[2]['source_sha256']==rows[5]['source_sha256'] and rows[2]['image_sha256']==rows[5]['image_sha256']
    assert rows[5]['reused_source_phase']==2
    group=manifest['actions']['crush'];move=bundle.read(bundle.checked(group['move']))
    bundle.validate_move(move,group['fist_boxes'])
    assert [i for i,f in enumerate(move['frames']) if f['hitboxes']]==list(range(12,20))
    computed=bundle.state_frames(rows)
    assert [f['hurtboxes'] for f in move['frames']]==[f['hurtboxes'] for f in computed]
    for key in ['damage','recovery','launch','knockdown','unblockable']:
        bad=copy.deepcopy(move);bad[key]=not bad[key] if key in ['launch','knockdown','unblockable'] else bad[key]+1
        try:bundle.validate_move(bad,group['fist_boxes'])
        except AssertionError:pass
        else:raise AssertionError('规则篡改未被拒绝：'+key)
    flags=bundle.read(paths[0]);assert all(flags[k] is False for k in ['implemented','playable','select_visible'])
    commands=[r for r in bundle.read(paths[2]) if r['move']=='crush' and 'idle' in r['states']]
    assert len(commands)==1 and commands[0]['directions']==[4,5] and commands[0]['buttons']==64
    driver=(bundle.REVIEW/'main_driver.gd').read_text()
    assert 'UfeInputFrame.make(0, 0, UfeInputFrame.CRUSH if frame == 20 else 0)' in driver
    for path in bundle.REVIEW.glob('*.gd'):
        text=path.read_text()
        assert '.move_id =' not in text and '.move_id=' not in text,'不得直塞move_id'
    assert before=={str(p):bundle.sha(p) for p in paths},'静态检查修改了正式文件'
    print(json.dumps({'passed':True,'repeat_full_source_reconstruction':True,'phases':7,'ticks':35,'active_ticks':list(range(12,20)),'input':'5O InputFrame, not direct move_id mutation','formal_flags_disabled':True,'godot_executed':False,'art_accepted':False},ensure_ascii=False))
if __name__=='__main__':main()

"""绑定月亮heavy候选与当前主游戏代码，仅生成reports中的内存验收合同。"""
import argparse
import copy
from pathlib import Path
import prepare as P

def checked(ref):
 p=P.ROOT/ref['path']
 if P.sha(p)!=ref['sha256']:raise ValueError('SHA改变：'+str(p))
 return p

def build(out):
 out=out.resolve();out.relative_to(P.ROOT/'reports/luna-heavy-resume')
 if out.exists():raise ValueError('输出已存在')
 manifest_path=P.OUTPUT/'manifest.json';manifest=P.read(manifest_path);resources={manifest_path,Path(__file__).resolve()}
 for k in ['samples','registration_review','rule_reference','clip','move']:resources.add(checked(manifest[k]))
 resources.update(checked(r) for r in manifest['processing_tools'].values())
 for row in manifest['frames']:
  for k in ['source','sample','image']:resources.add(checked(row[k]))
 samples=P.read(P.OUTPUT/'samples.json');resources.add(checked(samples['palette']));resources.add(checked(samples['source_receipt']))
 clips={'heavy':P.read(checked(manifest['clip']))};moves={'heavy':P.read(checked(manifest['move']))}
 prior=P.STAGE/'movement-contract-20261101-v1';bundle=P.read(prior/'bundle.json');states=P.read(prior/'state_frames.json')
 resources.update([prior/'bundle.json',prior/'state_frames.json'])
 for action in ['idle','turn']:
  clips[action]=copy.deepcopy(bundle['clips'][action]);clips[action]['source_fighter']='ultraman-arc__luna'
  atlas=P.STAGE/'goal-closeout-20261101-v1'/action/'atlas.png'
  if P.sha(atlas)!=clips[action]['atlas_sha256']:raise ValueError('本人idle/turn图集变化')
  clips[action]['texture']=atlas.as_posix();resources.add(atlas)
 atlas=P.OUTPUT/'atlas.png'
 if P.sha(atlas)!=clips['heavy']['atlas_sha256']:raise ValueError('heavy图集变化')
 clips['heavy']['texture']=atlas.as_posix();resources.add(atlas)
 flags=P.ROOT/'content/fighters/ultraman-arc__luna/definition.json'
 if any(P.read(flags)[k] for k in ['implemented','playable','select_visible']):raise ValueError('禁止开放未齐装甲')
 model=P.ROOT/'art/fighters/ultraman-arc__luna/model/model-native.png';resources.update([flags,model])
 command_path=P.ROOT/'content/fighters/ultraman-arc/command_table.json';commands=[r for r in P.read(command_path) if r['move']=='heavy'];resources.add(command_path)
 for folder in ['core','input','content','presentation','app','ui','third_party/shoto','tests/review/fighters/ultraman-arc/luna_heavy','tests/review/fighters/ultraman-arc/luna_light_chain','tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1']:
  resources.update(p for p in (P.ROOT/folder).rglob('*') if p.is_file() and p.suffix in {'.gd','.json','.tres','.tscn','.gdshader'})
 cfg={'schema':'ufeneo.luna.heavy-main-candidate.v1','root_runtime_ready':True,'fighter':'ultraman-arc__luna','opponent':'zetton',
      'playable':False,'implemented':False,'transform_enabled':False,'select_visible':False,
      'definition':{'id':'ultraman-arc__luna','display_name':'亚刻奥特曼 · 月亮装甲 · 重击候选','max_health':1000,'walk_speed':2,'jump_speed':16,'body_radius':18,
                    'moves':moves,'command_table':commands,'state_frames':{a:states[a] for a in ['idle','turn']}},
      'presentation':{'model':model.as_posix(),'native':True,'anchor_y':280,'manifest_data':{'fighter':'ultraman-arc__luna','clips':clips}},
      'bound_resources':[{'path':p.as_posix(),'sha256':P.sha(p)} for p in sorted(resources)],'manifest':P.ref(manifest_path),'main_game_accepted':False,'replay_accepted':False}
 P.write(out,cfg)
 return out
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();print(build(args.output))

"""低蹲左拳完整端点诊断；复用整图采样，不注册招式。"""
from pathlib import Path
import argparse,hashlib,importlib.util,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
SHARED=ROOT/'tools/rebuild/ultraman-arc/luna-crush-geometry/geometry.py'
spec=importlib.util.spec_from_file_location('whole_endpoint_compare',SHARED)
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
def build_frames(plan):
 images,result=core.build_frames(plan)
 result['schema']='ufeneo.luna.crouch-light-endpoint-geometry.v1'
 result['notes']=core.read(plan)['notes']
 result['shared_comparison_implementation']={'path':str(SHARED.relative_to(ROOT)),'sha256':core.sha(SHARED)}
 return images,result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);a.add_argument('--out',type=Path,required=True);args=a.parse_args();assert not args.out.exists()
 ims,result=build_frames(args.plan);again,other=build_frames(args.plan)
 assert result==other and all(a.tobytes()==b.tobytes() for a,b in zip(ims,again))
 args.out.mkdir(parents=True);atlas=Image.new('RGBA',(320*len(ims),320))
 for i,(im,row) in enumerate(zip(ims,result['frames'])):
  p=args.out/(row['key']+'.png');im.save(p);row['frame_sha256']=core.sha(p);atlas.paste(im,(i*320,0))
 atlas.save(args.out/'atlas.png');result['atlas_sha256']=core.sha(args.out/'atlas.png');result['repeat_build_equal']=True
 (args.out/'geometry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('蹲左拳完整端点重复构建通过；未运行、未安装。')

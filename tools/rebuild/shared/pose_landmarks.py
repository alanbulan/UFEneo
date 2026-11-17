"""离线DWPose量真实成品的头/掌/脚；输出含置信度，不写游戏状态。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import argparse,hashlib,json; json = _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import cv2,numpy as np
from PIL import Image
from rtmlib import RTMPose
ROOT=_LayoutProjectPath(_layout_root)
def main():
 p=argparse.ArgumentParser();p.add_argument('image');p.add_argument('output');a=p.parse_args()
 im=Image.open(a.image).convert('RGBA');bg=Image.new('RGB',im.size,'#707070');bg.paste(im,(0,0),im)
 model=ROOT/'.tools/models/rtmlib/dwpose-s-256x192/end2end.onnx';est=RTMPose(str(model),model_input_size=(192,256),backend='onnxruntime',device='cpu')
 points,scores=est(np.array(bg.resize((im.width*4,im.height*4),Image.Resampling.NEAREST))[:,:,::-1].copy());points=points[0]/4;scores=scores[0]
 groups={'hand_left':[91,96,100,104,108],'hand_right':[112,117,121,125,129],'foot_left':[17,18,19],'foot_right':[20,21,22]}
 result={k:dict(point=points[ids].mean(0).tolist(),confidence=float(scores[ids].min()),indices=ids) for k,ids in groups.items()}
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(dict(model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),image_sha256=hashlib.sha256(Path(a.image).read_bytes()).hexdigest(),method='DWPose133四倍最近邻测掌心MCP均值及足部三点中心；低置信度不得放行',landmarks=result,points=points.tolist(),scores=scores.tolist()),ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()

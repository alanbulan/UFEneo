"""月亮crush完整整帧端点比较；返回RAM图像，不注册时序或运行招式。"""
from pathlib import Path
import argparse,hashlib,json,math,sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/rebuild/shared'))
from forge_backend import palette_mode,backend_info,binarize_alpha,_kcentroid_downscale,apply_palette
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def build_frames():
 p=read(HERE/'plan.json');model=ROOT/p['model_measurement']['path'];assert sha(model)==p['model_measurement']['sha256']
 m=read(model);points=m['source_landmarks'];target=math.dist(points['near_knee'],points['near_ankle'])*m['source_to_native_uniform_scale']
 colors=read(ROOT/'art/fighters/ultraman-arc__luna/model/palette.json')['colors'];images=[];rows=[]
 with palette_mode('rgb'):
  backend={k:v for k,v in backend_info().items() if k not in ['scripts','python']};assert backend['files']==p['forge_files']
  for r in p['sources']:
   path=ROOT/r['path'];assert sha(path)==r['sha256'];raw=Image.open(path).convert('RGBA');lm=r['landmarks'];scale=target/math.dist(lm['rear_knee'],lm['rear_ankle']);size=[round(raw.width*scale),round(raw.height*scale)];ras=[size[0]/raw.width,size[1]/raw.height]
   roi=r['rear_forefoot_roi'];mask=raw.getchannel('A').point(lambda a:255 if a>=128 else 0);foot=mask.crop(roi);box=foot.getbbox();assert box;ys=range(max(0,box[3]-4),box[3]);xs=[x for y in ys for x in range(foot.width) if foot.getpixel((x,y))];anchor=[roi[0]+sum(xs)/len(xs),roi[1]+box[3]]
   small=_kcentroid_downscale(binarize_alpha(raw.copy()),*size,detail_bias=True);apply_palette(small,colors);binarize_alpha(small)
   offset=[round(p['anchor'][i]-anchor[i]*ras[i]) for i in range(2)];frame=Image.new('RGBA',(320,320));frame.paste(small,tuple(offset));assert frame.getchannel('A').histogram()[255]==small.getchannel('A').histogram()[255];assert frame.crop((offset[0],offset[1],offset[0]+size[0],offset[1]+size[1])).tobytes()==small.tobytes()
   rows.append({'key':r['key'],'source':r['path'],'source_sha256':r['sha256'],'source_size':list(raw.size),'scale':scale,'sample_size':size,'raster_rounding_anisotropy':abs(ras[0]-ras[1])/scale,'whole_image_translation':offset,'source_rear_forefoot_anchor':anchor,'alpha_bbox':frame.getbbox(),'whole_source_preserved_no_crop':True,'rear_shin_target_by_construction':target,'front_shin_independent_projection':math.dist(lm['front_knee'],lm['front_ankle'])*scale,'joint_distance_uncertainty_native':36*scale,'native_landmarks':{k:[round(v[i]*ras[i]+offset[i],3) for i in range(2)] for k,v in lm.items()}});images.append(frame)
 return images,{'schema':'ufeneo.luna.crush-endpoint-geometry.v1','plan_sha256':sha(HERE/'plan.json'),'backend':backend,'frames':rows,'runtime_candidate_accepted':False,'physics_run':False,'installed':False,'notes':['左后胫同一尺整图比较；目标来自model近胫投影，不是真实骨长已证。','前掌锚强制对齐不证明无滑步；两脚没有独立移动。','五槽仅端点比较，旧06不是已合格低位随势，不给假时序或攻击框。']}
def main():
 a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);o=a.parse_args().out;assert not o.exists();images,result=build_frames();again,other=build_frames();assert result==other and all(x.tobytes()==y.tobytes() for x,y in zip(images,again));assert images[0].tobytes()==images[-1].tobytes();o.mkdir(parents=True)
 atlas=Image.new('RGBA',(320*len(images),320))
 for i,(im,row) in enumerate(zip(images,result['frames'])):
  assert row['raster_rounding_anisotropy']<.01 and sum(im.getchannel('A').histogram()[1:255])==0
  path=o/(row['key']+'.png');im.save(path);row['frame_sha256']=sha(path);atlas.paste(im,(320*i,0))
 atlas.save(o/'atlas.png');result['atlas_sha256']=sha(o/'atlas.png');result['repeat_build_equal']=True;(o/'geometry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'frames':len(images),'repeat_build_equal':True,'installed':False}))
if __name__=='__main__':main()

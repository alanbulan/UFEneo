"""三张完整回旋关键相的可移植内存几何诊断；不注册招式，不调用Godot。"""
from pathlib import Path
import argparse, hashlib, json, math, sys
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools/rebuild/shared'))
from forge_backend import backend_info, binarize_alpha, _kcentroid_downscale, apply_palette, palette_mode

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def distance(a, b):
    return math.dist(a, b)

def angle(a, b, c):
    u = [a[i]-b[i] for i in range(2)]; v = [c[i]-b[i] for i in range(2)]
    return math.degrees(math.acos(max(-1, min(1, sum(u[i]*v[i] for i in range(2))/(math.hypot(*u)*math.hypot(*v))))))

def build_frames(root=ROOT):
    """只在RAM创建三整帧；返回帧与诊断。无时序、判定、玩法开关或用户存档写入。"""
    plan = read(Path(__file__).with_name('plan.json'))
    measurement = root / plan['model_measurement']['path']
    assert sha(measurement) == plan['model_measurement']['sha256']
    palette = read(root / 'art/fighters/ultraman-arc__luna/model/palette.json')['colors']
    rows, frames = [], []
    with palette_mode('rgb'):
        info = backend_info(); info = {k:v for k,v in info.items() if k not in ['scripts','python']}
        assert info['files'] == plan['forge_files'], 'Forge版本SHA不匹配'
        for row in plan['sources']:
            p = root / row['path']; assert sha(p) == row['sha256'], str(p)
            raw = Image.open(p).convert('RGBA'); points = row['landmarks']
            support_sum = distance(points['support_hip'],points['support_knee'])+distance(points['support_knee'],points['support_ankle'])
            scale = plan['model_measurement']['target_support_leg_sum'] / support_sum
            sample_size = [round(raw.width*scale), round(raw.height*scale)]
            roi = row['support_roi']; mask = raw.getchannel('A').point(lambda a: 255 if a >= 128 else 0)
            foot = mask.crop(roi); box = foot.getbbox(); assert box
            floor_y = roi[1] + box[3]
            strip = foot.crop((0, max(0,box[3]-4), foot.width, box[3]))
            xs = [x for y in range(strip.height) for x in range(strip.width) if strip.getpixel((x,y))]
            anchor_source = [roi[0]+sum(xs)/len(xs), floor_y]
            small = _kcentroid_downscale(binarize_alpha(raw.copy()), *sample_size, detail_bias=True)
            apply_palette(small,palette); binarize_alpha(small)
            raster = [sample_size[0]/raw.width,sample_size[1]/raw.height]
            offset = [round(plan['anchor'][i]-anchor_source[i]*raster[i]) for i in range(2)]
            frame = Image.new('RGBA',tuple(plan['canvas'])); frame.paste(small,tuple(offset))
            assert frame.getchannel('A').histogram()[255] == small.getchannel('A').histogram()[255], '裁切'
            assert frame.crop((offset[0],offset[1],offset[0]+small.width,offset[1]+small.height)).tobytes() == small.tobytes()
            lengths = {}
            for name,a,b in [('support_thigh','support_hip','support_knee'),('support_shin','support_knee','support_ankle'),('attack_thigh','attack_hip','attack_knee'),('attack_shin','attack_knee','attack_ankle')]:
                lengths[name] = round(distance(points[a],points[b])*scale,3)
            attack_direction = math.degrees(math.atan2(points['attack_toe'][1]-points['attack_ankle'][1],points['attack_toe'][0]-points['attack_ankle'][0]))
            out = dict(key=row['key'],source=row['path'],source_sha256=row['sha256'],source_size=list(raw.size),uniform_scale=scale,sample_size=sample_size,raster_scale=raster,raster_rounding_anisotropy=abs(raster[0]-raster[1])/scale,support_leg_target_by_construction=plan['model_measurement']['target_support_leg_sum'],projected_bone_lengths=lengths,joint_length_uncertainty_native=2*18*scale,projected_attack_knee_angle_deg=angle(points['attack_hip'],points['attack_knee'],points['attack_ankle']),attack_ankle_to_toe_angle_deg=attack_direction,source_support_anchor=anchor_source,whole_image_translation=offset,canvas=list(frame.size),alpha_bbox=frame.getbbox(),visible_pixels=frame.getchannel('A').histogram()[255],whole_source_preserved_no_crop=True,native_landmarks={k:[round(v[i]*raster[i]+offset[i],3) for i in range(2)] for k,v in points.items()})
            rows.append(out); frames.append(frame)
    result={'schema':'ufeneo.luna.spin-geometry-result.v1','plan_sha256':sha(Path(__file__).with_name('plan.json')),'backend':info,'frames':rows,'installed':False,'playable':False,'runtime_candidate_accepted':False,'physics_run':False,'notes':['人工投影关节有误差与透视缩短，不作自动解剖硬门。','支撑股胫总长按构造归一，不把总长相等当独立验证；支撑点也是整图对齐的比较坐标，不证明实游无滑步。','仅三关键相，没有idle入招、接触后随势/收腿/回架及合法完整时序，不合成攻击框或伪装成整招。']}
    return frames,result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    assert not args.out.exists(), '输出已存在，禁止覆盖旧证据'
    frames,result=build_frames();args.out.mkdir(parents=True)
    atlas=Image.new('RGBA',(320*len(frames),320))
    for i,(frame,row) in enumerate(zip(frames,result['frames'])):
        p=args.out/(row['key']+'.png');frame.save(p);row['frame_sha256']=sha(p);atlas.paste(frame,(i*320,0))
    atlas.save(args.out/'atlas.png');result['atlas_sha256']=sha(args.out/'atlas.png')
    (args.out/'geometry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    # 仅审阅辅助：灰底放大图不用于运行，原透明整帧未改。
    review=Image.new('RGB',(960,350),(70,70,70));review.paste(atlas,(0,30),atlas);d=ImageDraw.Draw(review)
    for i,row in enumerate(result['frames']):
        d.text((i*320+10,8),row['key'],fill='white')
        for k,(x,y) in row['native_landmarks'].items():
            d.ellipse((x+i*320-1,y+29,x+i*320+1,y+31),fill='yellow')
    review.resize((1920,700),Image.Resampling.NEAREST).save(args.out/'review-points.png')
    print(json.dumps({'frames':len(frames),'out':str(args.out),'runtime_candidate_accepted':False}))
if __name__ == '__main__':main()

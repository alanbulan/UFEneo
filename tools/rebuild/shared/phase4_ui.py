"""阶段4像素UI：GPT透明生成，固定槽位提取，九宫格资源和审片联系表。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import json,sys,hashlib,urllib.request,zipfile,io,shutil,argparse; json = _LayoutJson
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=_LayoutProjectPath(_layout_root)
sys.path.insert(0,str(ROOT/'tools'))
import art.produce_character as producer
WORK=ROOT/'art/shared/ui/stage4/ui'
OUT=ROOT/'reports/review/2026-10-22-pixel-hud'
DEST=ROOT/'assets/ui/neo'
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def approve():
 p=ROOT/'content/roster/production.json';d=read(p)
 d['stage']='phase4_ui_batch1'
 d['shared_effects']['beam_loop'].update(status='user_approved',reviewed=True,review_date='2026-10-22',reason='用户复核连续无缺口和无缝平铺')
 d['fx_rework_batch'].update(beam_loop_reviewed=True,zetton_level3_reviewed=True)
 d['audio_batch'].update(metadata_reviewed=True,listening_reviewed=False,status='metadata_approved_pending_user_listening',reviewed=False)
 for fighter in ['ultraman','zetton']:
  mpath=ROOT/f'assets/fighters/{fighter}/animations/manifest.json';m=read(mpath)
  for key in ['special','special2','special3']:
   m['clips'][key].setdefault('motion_review',{}).update(user_approved=True,verdict='user_approved',review_date='2026-10-22')
   d['fighters'][fighter]['actions'][key].update(status='user_approved',reviewed=True)
  for action in d['fighters'][fighter]['actions'].values():
   if isinstance(action,dict) and isinstance(action.get('sound'),dict):action['sound'].update(metadata_reviewed=True,listening_reviewed=False)
  save(mpath,m)
 save(p,d)
 for folder in [ROOT/'assets/effects/shared/beam_loop',ROOT/'assets/effects/zetton/super_fire']:
  for path in folder.glob('*.json'):
   v=read(path);v.update(user_approved=True,review_date='2026-10-22');save(path,v)
 p=ROOT/'content/audio/sources.json';v=read(p)
 for r in v['records']:r.update(metadata_reviewed=True,listening_reviewed=False)
 save(p,v)
 # 进度正文已并入 docs/HANDBOOK.md。本函数不再覆盖任何文档。

PARTS={
 'chrome': [('panel',(80,64)),('dialog',(80,64)),('toast',(84,22)),('timer',(48,40)),('button_normal',(84,24)),('button_hover',(84,24)),('button_pressed',(84,24)),('button_disabled',(84,24)),('button_selected',(84,24)),('tab_normal',(72,24)),('tab_selected',(72,24)),('list_normal',(84,20)),('list_selected',(84,20)),('scroll_track',(12,64)),('scroll_thumb',(12,24)),('portrait',(48,48))],
 'meters': [('health_frame',(84,16)),('health_fill',(72,8)),('health_ghost',(72,8)),('energy_frame',(72,16)),('energy_fill',(64,8)),('energy_glow',(72,16)),('stamina_frame',(72,12)),('stamina_fill',(64,4)),('cursor_red',(48,48)),('cursor_blue',(48,48)),('timer_red',(48,40)),('health_red',(72,8)),('list_disabled',(84,20)),('hint',(84,22)),('pause_icon',(16,16)),('gauge_empty',(72,8))]
}
DESCS={
 'chrome':['宽面板，深海军蓝实心内底，厚银色切角边框，细红饰条','对话框，深蓝内底，银红双层边缘','窄提示条，银红边框深蓝内底','正方计时器框，银色切角双框，顶部青蓝宝石，深蓝内底','按钮常态，银框红边深蓝内底','同款按钮悬停，银色高光青蓝点亮','同款按钮按下，边缘压低，暗红内底','同款按钮禁用，灰银低饱和深蓝内底','同款按钮选中，红色内边青蓝亮点','页签常态，银框深蓝内底','页签选中，红色顶部饰条','列表项常态，细银边深蓝内底','列表项选中，银框红色小箭头点缀','竖滚动条轨道，暗银窄槽','竖滚动条滑块，银色红色高光','头像框，正方银红切角框，内部透明，不要人物'],
 'meters':['血条空框，银色红饰边，深蓝内槽','血条填充，亮红至金橙像素高光，实心矩形无框','伤害残影填充，白银像素实心矩形无框','能量槽空框，银色深蓝内槽','能量填充，青蓝白芯像素实心矩形','满格能量发光框，银框外侧青白一像素光点，内部透明','体力槽框，暗银薄边深蓝内槽','体力填充，青绿像素高光实心矩形','红色选人光标，方形四角红银箭角，中间完全透明','蓝色选人光标，和红色同款青蓝银四角，中间完全透明','低血量计时器红闪框，与chrome第4格同款外形，宝石及内边红色','低血量血条填充，红色像素高光实心矩形','禁用列表项，低饱和银灰深蓝','操作提示条，深蓝底银色边小红方块','暂停图标，两条银色立柱红色顶边，透明背景','空槽填充，暗蓝实心像素矩形无框']}

def prepare():
 WORK.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
 for key,parts in PARTS.items():
  desc='；'.join(f'第{i+1}格：{DESCS[key][i]}，原生宽{size[0]}高{size[1]}' for i,(_,size) in enumerate(parts))
  prompt='制作经典街机银红风格的正式像素UI素材图集，严格采用附件A稿的金属银高光、红装甲、青蓝宝石、深海军蓝。不是UI效果截图。透明背景，真正PNG Alpha，硬边像素，无抗锯齿、无平滑渐变、无投影。画布1536×1536，4列4行共16格，每格384×384。每个部件单独居中完整放在对应格里，无网格无文字无编号无人物。原生1像素画成4×4像素块，对应640×360游戏密度。所有部件严格矩形轴对齐，九宫格用途，四个角厚度相同，直边中段平整可伸展。外边缘透明留白至少16图上像素；宽高为下面原生尺寸乘4，严格不要填满格子。'+desc+'。全部禁止文字和数字。'
  name='ui-p4-'+key
  save(ROOT/f'art/fighters/ultraman/stage2/legacy/requests/{name}.json',dict(id=name,asset_kind='ui',size='1536x1536',reference_images=['art/shared/ui/style-proposals/a/style.png'],prompt=prompt,generation_dir='art/shared/generation/ui/phase4/'+key,budget=dict(journal='art/shared/ui/stage4/ui/requests.json',max_requests=50,action_key=key)))
 for key,word in [('ready','准备'),('fight','开战'),('victory','胜利'),('time_up','时间到'),('draw','平局')]:
  name='ui-p4-word-'+key
  prompt=f'透明背景，真正PNG Alpha，只有一组中文像素美术大字“{word}”，必须逐字准确，居中完整。经典街机银红风格，字面银白金属块状高光、红色立体像素下缘、深蓝一像素轮廓，青蓝少量高光。参考附件A稿风格。不要英文，不要其他字，不要标点，不要面板，无光晕无投影无平滑渐变。宽1024高1024，字形主体宽约800高240，四周完全透明。每个原生像素放大4×4，硬边方形网格，最终原生大字宽约200高60，适合640×360街机。'
  save(ROOT/f'art/fighters/ultraman/stage2/legacy/requests/{name}.json',dict(id=name,asset_kind='ui',size='1024x1024',reference_images=['art/shared/ui/style-proposals/a/style.png'],prompt=prompt,generation_dir='art/shared/generation/ui/phase4/word-'+key,budget=dict(journal='art/shared/ui/stage4/ui/requests.json',max_requests=50,action_key='word-'+key)))

def font():
 version='2026.10.16';url=f'https://github.com/TakWolf/fusion-pixel-font/releases/download/{version}/fusion-pixel-font-12px-monospaced-otf-v{version}.zip'
 data=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'UFEneo'}),timeout=120).read();z=zipfile.ZipFile(io.BytesIO(data))
 license=urllib.request.urlopen('https://raw.githubusercontent.com/TakWolf/fusion-pixel-font/master/LICENSE-OFL',timeout=30).read()
 assert b'SIL OPEN FONT LICENSE' in license and b'Version 1.1' in license
 folder=ROOT/'assets/ui/fonts';folder.mkdir(parents=True,exist_ok=True)
 names=[n for n in z.namelist() if n.endswith('.otf') and 'zh_hans' in n];assert len(names)==1,names
 (folder/'fusion-pixel-12px.otf').write_bytes(z.read(names[0]));(folder/'LICENSE-OFL.txt').write_bytes(license)
 save(folder/'SOURCE.json',dict(repository='https://github.com/TakWolf/fusion-pixel-font',version=version,url=url,zip_sha256=hashlib.sha256(data).hexdigest(),member=names[0],font_sha256=sha(folder/'fusion-pixel-12px.otf'),license='SIL Open Font License 1.1',license_sha256=sha(folder/'LICENSE-OFL.txt')))
 print('官方简中12px OTF与OFL 1.1已保存')

def generate(keys):
 def assets(key):
  return [name for name,_ in PARTS[key]] if key in PARTS else ['panel','dialog'] if key=='panels' else [key]
 for key in keys:
  counts={}
  for record in read(WORK/'requests.json') if (WORK/'requests.json').exists() else []:
   for asset in assets(record['action_key']):counts[asset]=counts.get(asset,0)+1
  if any(counts.get(asset,0)>=3 for asset in assets(key)):raise ValueError(key+'中的素材已达3次，待人工')
  print(producer.generate('ui-p4-'+key),flush=True)

def extract():
 sys.path.insert(0,str(ROOT/'tools/rebuild'))
 import process_phase2 as process
 # GPT并未严格遵守等分格，因此审片后固定每个完整部件的实际矩形。
 crops={
 'chrome':[(24,35,400,283),(412,38,776,283),(794,125,1176,221),(1238,60,1480,272),(24,344,392,461),(410,340,777,463),(788,344,1152,458),(1166,343,1520,456),(22,548,395,669),(451,551,774,671),(809,550,1128,668),(1170,559,1519,657),(23,790,394,891),(555,700,635,982),(932,773,1000,925),(1218,706,1478,963)],
 'meters':[(10,125,328,266),(335,153,627,240),(650,155,944,236),(951,111,1240,262),(30,444,300,531),(309,400,649,555),(647,432,944,540),(967,459,1226,522),(45,650,289,887),(355,650,603,885),(650,660,924,883),(951,740,1239,820),(10,998,323,1125),(314,999,650,1125),(730,1004,845,1125),(951,1018,1240,1100)]}
 DEST.mkdir(parents=True,exist_ok=True);manifest={'schema':1,'style':'A经典街机银红','native_canvas':[640,360],'display':'integer_nearest','parts':{},'words':{}}
 for key,parts in PARTS.items():
  raw=sorted((ROOT/'art/shared/generation/ui/phase4'/key).glob('[0-9][0-9]/raw.png'))[-1];im=Image.open(raw).convert('RGBA');w,h=im.size
  for i,(name,target) in enumerate(parts):
   region=crops[key][i];tile=im.crop(region)
   a=np.array(tile);a[a[:,:,3]<128]=0;a[a[:,:,3]>=128,3]=255;tile=Image.fromarray(a)
   groups=process.components(tile);assert groups
   keep=groups[:1] if key=='chrome' else [g for g in groups if len(g)>=len(groups[0])*0.06]
   mask=np.zeros((tile.height,tile.width),dtype=np.uint8)
   for group in keep:
    for x,y in group:mask[y,x]=255
   tile.putalpha(Image.fromarray(mask));box=tile.getbbox();assert box,(key,name)
   tile=tile.crop(box).resize(target,Image.Resampling.NEAREST)
   # 色板量化只整理生成图，不绘制任何UI轮廓。
   alpha=tile.getchannel('A');tile=tile.convert('RGB').quantize(colors=32,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGBA');tile.putalpha(alpha)
   path=DEST/(name+'.png');tile.save(path)
   margin=[6,6,6,6] if min(target)>=20 else [3,3,3,3] if min(target)>6 else [1,1,1,1]
   manifest['parts'][name]=dict(texture='res://'+path.relative_to(ROOT).as_posix(),size=list(target),margins=margin,source=raw.relative_to(ROOT).as_posix(),source_region=region,source_crop=list(box),sha256=sha(path),generated=True)
 for key in ['ready','fight','victory','time_up','draw']:
  raw=sorted((ROOT/'art/shared/generation/ui/phase4'/('word-'+key)).glob('[0-9][0-9]/raw.png'))[-1];im=Image.open(raw).convert('RGBA');a=np.array(im);a[a[:,:,3]<128]=0;a[a[:,:,3]>=128,3]=255;im=Image.fromarray(a);im=im.crop(im.getbbox());im=process._kcentroid_downscale(im,round(im.width*44/im.height),44);process.binarize_alpha(im)
  alpha=im.getchannel('A');im=im.convert('RGB').quantize(colors=32,dither=Image.Dither.NONE).convert('RGBA');im.putalpha(alpha)
  path=DEST/('word_'+key+'.png');im.save(path);manifest['words'][key]=dict(texture='res://'+path.relative_to(ROOT).as_posix(),size=list(im.size),source=raw.relative_to(ROOT).as_posix(),sha256=sha(path))
 panel_raw=ROOT/'art/shared/generation/ui/phase4/panels/01/raw.png'
 if panel_raw.exists():
  tile=Image.open(panel_raw).convert('RGBA');process.binarize_alpha(tile);groups=process.components(tile);mask=np.zeros((tile.height,tile.width),dtype=np.uint8)
  for x,y in groups[0]:mask[y,x]=255
  tile.putalpha(Image.fromarray(mask));box=tile.getbbox();tile=process._kcentroid_downscale(tile.crop(box),64,64);process.binarize_alpha(tile)
  alpha=tile.getchannel('A');tile=tile.convert('RGB').quantize(colors=32,dither=Image.Dither.NONE).convert('RGBA');tile.putalpha(alpha)
  for name in ['panel','dialog']:
   path=DEST/(name+'.png');tile.save(path)
   manifest['parts'][name]=dict(texture='res://'+path.relative_to(ROOT).as_posix(),size=[64,64],margins=[14]*4,source=panel_raw.relative_to(ROOT).as_posix(),source_crop=list(box),sha256=sha(path),generated=True,reason='均匀边线，四角装甲固定，防止中部宝石随九宫格被拉宽')
 save(DEST/'manifest.json',manifest)
 # 头像从已审身份锚裁出完整头部，保留鳍和触角；不采用旧试验头像。
 for fighter,box in [('ultraman',(73,35,120,83)),('zetton',(91,71,168,146))]:
  im=Image.open(ROOT/f'assets/fighters/{fighter}/model-native.png').convert('RGBA')
  im.crop(box).resize((40,40),Image.Resampling.NEAREST).save(DEST/f'portrait_{fighter}.png')
 contact()
 print('固定网格UI提取完成，需视觉自检')

def contact():
 d=read(DEST/'manifest.json');items=list(d['parts'].items())+list(d['words'].items());cw=max(380,max(v['size'][0]*4+16 for _,v in items));ch=310
 sheet=Image.new('RGB',(cw*4,ch*((len(items)+3)//4)),'#202735');draw=ImageDraw.Draw(sheet);f=ImageFont.truetype(str(ROOT/'assets/ui/fonts/fusion-pixel-12px.otf'),24)
 for i,(name,v) in enumerate(items):
  im=Image.open(ROOT/v['texture'].removeprefix('res://')).convert('RGBA');im=im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST)
  x=i%4*cw;y=i//4*ch;draw.text((x+8,y+5),name,font=f,fill='white');sheet.paste(im,(x+8,y+42),im)
 sheet.save(OUT/'ui-kit-contact-4x.png')

def theme():
 d=read(DEST/'manifest.json');parts={**d['parts'],**{'word_'+k:v for k,v in d['words'].items()}}
 for fighter in ['ultraman','zetton']:parts['portrait_'+fighter]={'texture':f'res://assets/ui/neo/portrait_{fighter}.png'}
 lines=['[gd_resource type="Theme" load_steps=100 format=3]','[ext_resource type="FontFile" path="res://assets/ui/fonts/fusion-pixel-12px.otf" id="font"]']
 for name,v in parts.items():lines.append(f'[ext_resource type="Texture2D" path="{v["texture"]}" id="{name}"]')
 for name,v in d['parts'].items():
  margin=v['margins'];lines.extend([f'[sub_resource type="StyleBoxTexture" id="box_{name}"]',f'texture = ExtResource("{name}")'])
  for side,number in zip(['left','top','right','bottom'],margin):lines.append(f'texture_margin_{side} = {float(number)}')
  horizontal=12 if name.startswith(('button_','tab_','list_')) else 8
  vertical=6 if name.startswith(('button_','tab_','list_')) else 4
  for side in ['left','right']:lines.append(f'content_margin_{side} = {float(horizontal)}')
  for side in ['top','bottom']:lines.append(f'content_margin_{side} = {float(vertical)}')
 lines+=['[resource]','default_font = ExtResource("font")','default_font_size = 12','Label/colors/font_color = Color(0.94,0.96,1,1)','Label/colors/font_shadow_color = Color(0.025,0.04,0.08,1)','Label/constants/shadow_offset_x = 1','Label/constants/shadow_offset_y = 1']
 for name in parts:lines.append(f'NeoKit/icons/{name} = ExtResource("{name}")')
 for cls,base,style in [('PixelPanel','PanelContainer','panel'),('PixelDialog','PanelContainer','dialog'),('PixelToast','PanelContainer','toast')]:lines.extend([f'{cls}/base_type = &"{base}"',f'{cls}/styles/panel = SubResource("box_{style}")'])
 for cls,normal,selected in [('PixelButton','button_normal','button_selected'),('PixelTab','tab_normal','tab_selected'),('PixelListItem','list_normal','list_selected')]:
  lines.append(f'{cls}/base_type = &"Button"')
  for state,part in [('normal',normal),('hover','button_hover'),('pressed',selected),('disabled','button_disabled'),('focus','button_selected')]:lines.append(f'{cls}/styles/{state} = SubResource("box_{part}")')
  lines.extend([f'{cls}/font_sizes/font_size = 12',f'{cls}/colors/font_color = Color(0.94,0.96,1,1)',f'{cls}/colors/font_focus_color = Color(1,1,1,1)',f'{cls}/colors/font_disabled_color = Color(0.47,0.52,0.61,1)'])
 for cls in ['VScrollBar','HScrollBar']:
  for state,part in [('scroll','scroll_track'),('grabber','scroll_thumb'),('grabber_highlight','button_hover'),('grabber_pressed','button_pressed')]:lines.append(f'{cls}/styles/{state} = SubResource("box_{part}")')
 for cls in ['VBoxContainer','HBoxContainer']:lines.append(f'{cls}/constants/separation = 4')
 p=ROOT/'ui/theme/neo_pixel_theme.tres';p.parent.mkdir(exist_ok=True);p.write_text('\n\n'.join(lines)+'\n','utf-8')
 imp=ROOT/'assets/ui/fonts/fusion-pixel-12px.otf.import'
 # Godot首次导入后再执行也保持点阵，不启用MSDF和抗锯齿。
 if imp.exists():
  txt=imp.read_text('utf-8').replace('antialiasing=1','antialiasing=0').replace('antialiasing=2','antialiasing=0').replace('hinting=3','hinting=0').replace('subpixel_positioning=4','subpixel_positioning=0')
  imp.write_text(txt,'utf-8')
 print('唯一像素主题已生成')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command');p.add_argument('keys',nargs='*');a=p.parse_args()
 if a.command=='generate':generate(a.keys)
 else:globals()[a.command]()

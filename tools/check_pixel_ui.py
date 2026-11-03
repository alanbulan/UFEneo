"""正式UI禁用绘图检查及九宫格清单/像素字体完整性，不评价画面美丑。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import re,json,hashlib,sys; json = _LayoutJson
from PIL import Image
ROOT=_LayoutProjectPath(_layout_root)
FORBIDDEN=re.compile(r'\bStyleBoxFlat\b|\b(?:draw_(?:line|dashed_line|rect|circle|arc|polygon|colored_polygon|polyline|multiline|mesh|primitive|style_box))\s*\(')
def main():
 errors=[]
 for directory in ['ui','app']:
  for p in (ROOT/directory).rglob('*'):
   if p.suffix not in ['.gd','.tscn','.tres','.gdshader']:continue
   for number,line in enumerate(p.read_text('utf-8-sig').splitlines(),1):
    if FORBIDDEN.search(line):errors.append(f'{p.relative_to(ROOT)}:{number} 正式UI禁止程序绘制装饰：{line.strip()}')
 manifest=json.loads((ROOT/'assets/ui/neo/manifest.json').read_text('utf-8'))
 for name,part in {**manifest['parts'],**manifest['words']}.items():
  path=ROOT/part['texture'].removeprefix('res://')
  if not path.is_file():errors.append('缺少UI素材 '+name);continue
  im=Image.open(path)
  if im.mode!='RGBA' or 0 not in im.getchannel('A').getdata():errors.append('UI素材不是真透明 '+name)
  if list(im.size)!=part['size']:errors.append('裁片尺寸不一致 '+name)
  if hashlib.sha256(path.read_bytes()).hexdigest()!=part['sha256']:errors.append('UI素材哈希已变化 '+name)
  if 'margins' in part:
   l,t,r,b=part['margins']
   if l+r>=im.width or t+b>=im.height:errors.append('九宫格无中心 '+name)
 font=ROOT/'assets/ui/fonts'
 source=json.loads((font/'SOURCE.json').read_text('utf-8'))
 if hashlib.sha256((font/'fusion-pixel-12px.otf').read_bytes()).hexdigest()!=source['font_sha256']:errors.append('字体哈希不一致')
 if 'SIL OPEN FONT LICENSE' not in (font/'LICENSE-OFL.txt').read_text('utf-8'):errors.append('缺少OFL原文')
 imports=(font/'fusion-pixel-12px.otf.import').read_text('utf-8')
 if 'antialiasing=0' not in imports or 'multichannel_signed_distance_field=false' not in imports:errors.append('像素字体导入设置不正确')
 pages=json.loads((ROOT/'assets/ui/pages/manifest.json').read_text('utf-8'))
 for name,v in pages['parts'].items():
  p=ROOT/v['texture'].removeprefix('res://');im=Image.open(p)
  if im.mode!='RGBA' or im.getchannel('A').getextrema()[0]!=0:errors.append('页面素材不是真透明 '+name)
  if list(im.size)!=v['size'] or hashlib.sha256(p.read_bytes()).hexdigest()!=v['sha256']:errors.append('页面素材清单不一致 '+name)
 roster=json.loads((ROOT/'content/roster/catalog.json').read_text('utf-8'));catalog={e['id']:e for e in roster['entries']}
 selection=json.loads((ROOT/'content/roster/selection.json').read_text('utf-8'))
 ids=set();names=set()
 for entry in selection['entries']:
  if entry['id'] in ids or entry['name'] in names:errors.append('正式选人名单重复 '+entry['id'])
  ids.add(entry['id']);names.add(entry['name'])
  if entry.get('selection_category') not in ['ultra','kaiju','alien'] or not entry.get('forms'):errors.append('正式分类/形态缺失 '+entry['id'])
  definition_path=ROOT/'content/fighters'/entry['id']/'definition.json'
  definition=json.loads(definition_path.read_text('utf-8-sig')) if definition_path.is_file() else {}
  direct_form=definition.get('direct_selection') is True and definition.get('implemented') is True
  if entry['id'] not in catalog and not direct_form:errors.append('正式名单缺少名册或已实现直选形态 '+entry['id'])
  if catalog.get(entry['id'],{}).get('kind') in ['form','story'] and not direct_form:errors.append('未开放形态/剧情对象不能单独成格 '+entry['id'])
  if not entry.get('sources'):errors.append('正式名单缺少研究来源 '+entry['id'])
 if errors:raise SystemExit('\n'.join(errors))
 print('正式UI禁用扫描、九宫格资源清单、OFL字体及选人身份：通过')
if __name__=='__main__':main()

"""只调用主游戏截屏/录屏；输出呈现状态，不能生成预览场景。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import sys,subprocess,json,argparse; json = _LayoutJson
ROOT=_LayoutProjectPath(_layout_root)
sys.path.insert(0,str(ROOT/'tools'))
from verify import godot_path
OUT=ROOT/'reports/review/2026-10-22-pixel-pages'
def capture(page,res='1280x720',extra=()):
 OUT.mkdir(parents=True,exist_ok=True)
 name=page+'-'+res+('-long' if '--review-long-text' in extra else '')
 command=[godot_path(),'--path',str(ROOT),'--resolution',res,'--',f'--capture-ui={page}',f'--capture={OUT/(name+".png")}','--capture-frame=45','--auto-quit=65',*extra]
 result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=80)
 output=(result.stdout+result.stderr).decode('utf-8','replace').replace('\r\n','\n').replace('\r','');(OUT/(name+'.log')).write_text(output,'utf-8')
 if 'SCRIPT ERROR' in output or '\nERROR:' in output:raise RuntimeError(output[-5000:])
 if not (OUT/(name+'.png')).exists():raise RuntimeError('没有截图 '+name)
 print(name,result.returncode,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('pages',nargs='+');p.add_argument('--resolution',default='1280x720');p.add_argument('--long',action='store_true');p.add_argument('--output-dir',type=Path);a=p.parse_args()
 if a.output_dir:OUT=a.output_dir.resolve()
 for page in a.pages:capture(page,a.resolution,['--review-long-text'] if a.long else [])

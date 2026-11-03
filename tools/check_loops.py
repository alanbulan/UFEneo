
# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import sys
from pathlib import Path
Path = _LayoutProjectPath
sys.path[:0]=[str(Path(__file__).resolve().parent/'rebuild'),str(Path(__file__).resolve().parent)]
import loop_qa
if __name__=='__main__':
    rows,errors=loop_qa.installed()
    for r in rows:
        if r['issues']:print(r['fighter']+'/'+r['action']+('（仅报告）' if r['report_only'] else '（阻塞）')+'：'+'；'.join(r['issues']))
    if errors:raise SystemExit(1)
    print('LOOP_RESOURCES PASS：循环含接头的头部特征已实测，旧角色偏差见报告。')

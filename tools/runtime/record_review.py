"""只录制主游戏。成功转码后删除AVI；临时MP4审阅后直接删除。须经Godot锁运行。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import argparse
import hashlib
import json; json = _LayoutJson
import re
import subprocess
import sys
sys.path.insert(0, str((_LayoutProjectPath(_layout_root) / 'tools')))
from verify import godot_path
ROOT = _LayoutProjectPath(_layout_root)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name')
    parser.add_argument('--frames', type=int, default=1800)
    parser.add_argument('--review', action='store_true')
    parser.add_argument('--forward-walk', action='store_true', help='只录前走，连续按住6秒，主游戏训练输入')
    parser.add_argument('--back-walk', action='store_true', help='只录后走，连续按住6秒，主游戏训练输入')
    parser.add_argument('--dash', action='store_true', help='真实双击前冲刺三次，中间静止半秒')
    parser.add_argument('--switches', action='store_true', help='主游戏待机/前走/后走/冲刺切换截图来源')
    parser.add_argument('--color-switches', action='store_true', help='区域调色后含待机到轻击的切换')
    parser.add_argument('--phase3', action='store_true', help='阶段3站立下蹲逐招F1命中审片')
    parser.add_argument('--air', action='store_true', help='阶段3跳跃空中连段及移动攻击逐招F1审片')
    parser.add_argument('--reactions', action='store_true', help='初代防御受击倒地蓄能，杰顿真实输入占位攻击')
    parser.add_argument('--zetton', action='store_true', help='玩家二杰顿首批逐招真实输入命中初代')
    parser.add_argument('--ultraseven', action='store_true', help='赛文首批逐招训练真实输入；未安装项明确跳过')
    parser.add_argument('--seven-defense', action='store_true', help='杰顿真实攻击赛文，防御受击倒地与反击')
    parser.add_argument('--seven-fourth', action='store_true', help='赛文第四批三种配对投技与胜负演出')
    parser.add_argument('--seven-body', action='store_true', help='赛文身长修正、前投、蓄能和完整倒地链')
    parser.add_argument('--seven-air-special', action='store_true', help='赛文空中念力头镖真实输入、三段命中与回收')
    parser.add_argument('--seven-action', help='仅录赛文首批中的一个动作；仍在主游戏训练模式内')
    parser.add_argument('--zetton-defense', action='store_true', help='初代真实输入攻击杰顿，防御受击倒地与完整追击链')
    parser.add_argument('--zetton-air', action='store_true', help='杰顿跳跃空连移动攻击、初代完整空连镜头验证')
    parser.add_argument('--zetton-counter', action='store_true', help='杰顿侧闪手刀对站姿/蹲姿初代真实输入')
    parser.add_argument('--specials', action='store_true', help='双角色专属、盾/吸收和完整回合演出')
    parser.add_argument('--supers', action='store_true', help='双角色三级必杀命中/防御')
    parser.add_argument('--feedback', action='store_true', help='普通对打通用打击反馈')
    parser.add_argument('--audio', action='store_true', help='登场到KO完整有声回合，双方必杀')
    parser.add_argument('--hud', action='store_true', help='正式像素HUD完整回合与暂停菜单')
    parser.add_argument('--pages', action='store_true', help='正式页面主游戏真实事件导航流程')
    parser.add_argument('--gate-b', action='store_true', help='标题到选人和胜负，玩家一代按，玩家二正式困难AI')
    parser.add_argument('--gate-b-patch', action='store_true', help='双向指令投、防御/拆投/跳开与三级必杀KO')
    parser.add_argument('--vs', action='store_true', help='正式VS页面入场动画')
    parser.add_argument('--pair', help='主游戏审片的两个角色id，逗号分隔')
    parser.add_argument('--flash', action='store_true', help='真实呈现帧闪白与KO失败动画')
    parser.add_argument('--throws', action='store_true', help='初代与杰顿双向前后空冲刺投及拆投')
    parser.add_argument('--final', action='store_true', help='验收门A最终40秒六组审片')
    parser.add_argument('--output-dir', type=Path, help='审片输出目录，默认reports/review')
    parser.add_argument('--forward-candidate','--walk-candidate',dest='forward_candidate',type=Path,help='显式读取未安装的前走/后走候选clip.json，仅用于主游戏审片')
    args = parser.parse_args()
    target = (args.output_dir if args.output_dir else ROOT/'reports/review').resolve()
    if not target.is_relative_to(ROOT.resolve()/'reports'):
        raise RuntimeError('临时录屏必须写在本工程reports目录内')
    if not args.name or Path(args.name).name != args.name or args.name in ('.','..'):
        raise RuntimeError('录屏名称必须是单一文件名')
    target.mkdir(parents=True, exist_ok=True)
    avi = target/(args.name+'.avi')
    mp4 = avi.with_suffix('.mp4')
    if avi.exists() or mp4.exists(): raise RuntimeError('影片已存在，请使用新名称')
    # 独立运行主游戏不会导入刚安装的PNG；先完成资源导入，避免录到空白纹理。
    with (target/(args.name+'-import.log')).open('w',encoding='utf-8') as log:
        imported=subprocess.run([godot_path(),'--headless','--path',str(ROOT),'--editor','--import','--quit'],stdout=log,stderr=log,timeout=120)
    import_text=(target/(args.name+'-import.log')).read_text('utf-8',errors='replace')
    if imported.returncode or re.search(r'(?:SCRIPT ERROR:|^ERROR:)',import_text,re.MULTILINE):raise RuntimeError('主游戏录屏前资源导入失败')
    command = [godot_path(), '--path', str(ROOT), '--write-movie', str(avi),
               '--fixed-fps', '60', '--quit-after', str(args.frames), '--',
               '--review-forward-candidate='+str(args.forward_candidate.resolve()) if args.forward_candidate else '--review-zetton-defense' if args.zetton_defense else '--review-zetton' if args.zetton else '--review-reactions' if args.reactions else '--review-air' if args.air else '--review-phase3' if args.phase3 else '--review-final' if args.final else '--review-color-switches' if args.color_switches else '--review-switches' if args.switches else '--review-dash' if args.dash else '--review-back-walk' if args.back_walk else '--review-forward-walk' if args.forward_walk else '--review' if args.review else '--demo']
    if args.zetton_air: command[-1]='--review-zetton-air'
    if args.zetton_counter:
        command[-1]='--review-zetton-counter'
        command.append('--review-trace='+str(target/(args.name+'-trace.json')))
    if args.throws: command[-1]='--review-throws'
    if args.specials: command[-1]='--review-specials'
    if args.supers: command[-1]='--review-supers'
    if args.feedback: command[-1]='--review-feedback'
    if args.audio: command[-1]='--review-audio'
    if args.hud: command[-1]='--review-hud'
    if args.pages: command[-1]='--review-pages'
    if args.gate_b:command[-1]='--review-gate-b'
    if args.gate_b_patch:
        command[-1]='--review-gate-b-patch'
        command.append('--review-trace='+str(target/(args.name+'-trace.json')))
    if args.vs:command[-1]='--capture-ui=vs'
    if args.pair:command.append('--capture-pair='+args.pair)
    if args.ultraseven:
        command[-1]='--review-ultraseven'
        command.append('--review-trace='+str(target/(args.name+'-trace.json')))
        if args.seven_action:command.append('--review-ultraseven-only='+args.seven_action)
    if args.seven_defense:
        command[-1]='--review-ultraseven-defense'
        command.append('--review-trace='+str(target/(args.name+'-trace.json')))
    if args.seven_fourth:
        command[-1]='--review-ultraseven-fourth'
        command.append('--review-trace='+str(target/(args.name+'-trace.json')))
    if args.seven_body:
        command[-1]='--review-ultraseven-body'
        command.append('--review-trace='+str(target/(args.name+'-trace.json')))
    if args.seven_air_special:
        command[-1]='--review-ultraseven-air-special'
        command.append('--review-trace='+str(target/(args.name+'-trace.json')))
    if args.flash: command[-1]='--review-flash'
    if args.flash: command.append('--review-trace='+str(target/(args.name+'-trace.json')))
    if args.pages or args.review or args.forward_walk or args.back_walk or args.forward_candidate or args.dash or args.switches or args.color_switches or args.final or args.phase3 or args.air or args.reactions or args.zetton or args.zetton_defense or args.zetton_air or args.throws or args.specials or args.supers or args.feedback or args.audio or args.hud:
        command.append('--review-trace='+str(target/(args.name+'-trace.json')))
    if args.ultraseven or args.forward_candidate or args.seven_defense or args.seven_fourth or args.seven_body or args.seven_air_special:
        command.append('--review-capture-frames='+str(args.frames))
    manifest_path=ROOT/'assets/fighters/zetton/animations/manifest.json'
    manifest_before=hashlib.sha256(manifest_path.read_bytes()).hexdigest() if args.zetton_defense or args.zetton_air else None
    with (target/(args.name+'.log')).open('w', encoding='utf-8') as log:
        process = subprocess.run(command, stdout=log, stderr=log, timeout=600)
    result = {'godot_exit': process.returncode}
    runtime_log=(target/(args.name+'.log')).read_text('utf-8',errors='replace')
    if re.search(r'(?:SCRIPT ERROR:|^ERROR:)',runtime_log,re.MULTILINE):raise RuntimeError('录屏存在脚本/资源错误，禁止作为合格影片交付；请查看日志')
    if manifest_before:
        result['zetton_manifest_sha256']=manifest_before
        assert manifest_before==hashlib.sha256(manifest_path.read_bytes()).hexdigest(), '录制期间正式资源清单发生变更'
    if args.forward_candidate:
        result['candidate_clip'] = str(args.forward_candidate.resolve())
        result['candidate_clip_sha256'] = hashlib.sha256(args.forward_candidate.read_bytes()).hexdigest()
        result['production_installed'] = False
    if not avi.exists():
        raise RuntimeError('主游戏未输出影片；请查看日志')
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(avi),'-c:v','libx264','-crf','18',
                    '-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(mp4)],check=True)
    probe = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height,nb_frames',
                            '-of','json',str(mp4)],capture_output=True,text=True,check=True)
    result['video'] = json.loads(probe.stdout)
    assert avi.resolve().is_relative_to(target) and avi.suffix == '.avi'
    avi.unlink()
    result['temporary_video'] = str(mp4)
    result['cleanup'] = 'AVI已删除；审阅后删除本次MP4，不建立工程外归档。'
    (target/(args.name+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__': main()

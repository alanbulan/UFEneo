"""只录制主游戏。成功转码后删除AVI；临时MP4审阅后直接删除。须经Godot锁运行。"""

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))
from runtime.environment import godot_path, isolated_test_environment


@contextmanager
def movie_resolution(resolution: str):
    width, height = (int(value) for value in resolution.split('x'))
    path = ROOT / 'override.cfg'
    settings = ('[display]\n'
                f'window/size/viewport_width={width}\n'
                f'window/size/viewport_height={height}\n'
                f'window/size/window_width_override={width}\n'
                f'window/size/window_height_override={height}\n')
    with path.open('x', encoding='utf-8') as output:
        output.write(settings)
    try:
        yield
    finally:
        if path.read_text(encoding='utf-8') != settings:
            raise RuntimeError('录制期间override.cfg被修改，保留现场并停止，未覆盖外部改动')
        path.unlink()


def validate_render_trace(report: dict, frames: int, resolution: str) -> list[dict]:
    rendered = report.get('render_trace', [])
    if len(rendered) != frames or [row.get('capture_tick') for row in rendered] != list(range(frames)):
        raise RuntimeError('实录缺少完整逐tick重绘证据，包含前台页面与末帧')
    if [row.get('render_pass') for row in rendered] != list(range(1, frames + 1)):
        raise RuntimeError('实录逐tick重绘次数不连续')
    first_frame = rendered[0].get('source_movie_frame')
    if type(first_frame) is not int or first_frame < 0 or [row.get('source_movie_frame') for row in rendered] != list(range(first_frame, first_frame + frames)):
        raise RuntimeError('源影片帧与模拟tick不是一一连续对应，禁止补帧或覆盖姿势')
    expected_size = [int(value) for value in resolution.split('x')]
    for row in rendered:
        if row.get('root_size') != expected_size or row.get('viewport_size') != [640, 360]:
            raise RuntimeError('实际重绘像素尺寸与请求不符')
        if any(not re.fullmatch(r'[0-9a-f]{64}', str(row.get(key, ''))) for key in ('root_sha256', 'viewport_sha256')):
            raise RuntimeError('实录缺少重绘后的根窗口或SubViewport像素SHA')
    return rendered


def probe_video(path: Path) -> dict:
    probe = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-show_entries',
                            'format=duration:stream=codec_name,width,height,nb_frames,nb_read_frames',
                            '-of', 'json', str(path)], capture_output=True, text=True, check=True)
    return json.loads(probe.stdout)


def validate_pair(value: str) -> list[str]:
    pair = value.split(',')
    if len(pair) != 2 or any(re.fullmatch(r'[a-z0-9][a-z0-9_-]*', fighter) is None for fighter in pair):
        raise RuntimeError('--pair 必须是两个有效角色id，禁止路径或空角色')
    fighters = (ROOT / 'content/fighters').resolve()
    for fighter in pair:
        path = fighters / fighter / 'definition.json'
        if not path.resolve().is_relative_to(fighters) or not path.is_file():
            raise RuntimeError('审片角色定义不存在或路径越界：'+fighter)
        try:
            definition = json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError, ValueError) as error:
            raise RuntimeError('审片角色定义不可读取：'+fighter) from error
        if not isinstance(definition, dict) or definition.get('id') != fighter:
            raise RuntimeError('审片角色定义与id不符：'+fighter)
        if definition.get('playable', True) is not True and definition.get('pilot_playable', False) is not True:
            raise RuntimeError('审片角色尚未开放：'+fighter)
    return pair


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
    parser.add_argument('--skill', help='已登记技能的双朝向真实输入审片，固定360tick')
    parser.add_argument('--idle', action='store_true', help='双朝向原地待机，各三个循环，固定360tick')
    parser.add_argument('--resolution', choices=['1280x720', '1920x1080'], default='1280x720')
    parser.add_argument('--flash', action='store_true', help='真实呈现帧闪白与KO失败动画')
    parser.add_argument('--throws', action='store_true', help='初代与杰顿双向前后空冲刺投及拆投')
    parser.add_argument('--fighter-throws', action='store_true', help='佐菲五种投技双朝向主游戏审片')
    parser.add_argument('--stills-dir', type=Path, help='主游戏审片抽取的姿势截图目录（必须位于reports内）')
    parser.add_argument('--final', action='store_true', help='验收门A最终40秒六组审片')
    parser.add_argument('--output-dir', type=Path, help='审片输出目录，默认reports/review')
    parser.add_argument('--forward-candidate','--walk-candidate',dest='forward_candidate',type=Path,help='显式读取未安装的前走/后走候选clip.json，仅用于主游戏审片')
    args = parser.parse_args()
    if args.frames <= 0:
        raise RuntimeError('录制帧数必须大于0')
    if args.idle:
        if args.skill:
            raise RuntimeError('--idle 与 --skill 不能同时使用')
        args.skill = 'idle'
    if args.skill and (args.frames != 360 or not args.pair):
        raise RuntimeError('--skill 必须指定 --frames 360 与 --pair=<角色>,<对手>')
    pair = validate_pair(args.pair) if args.pair is not None else []
    if args.fighter_throws:
        if args.frames != 1800:
            raise RuntimeError('佐菲五投双向审片固定为1800 tick')
        if len(pair) != 2 or pair[0] != 'zoffy':
            raise RuntimeError('--fighter-throws 必须明确指定 --pair=zoffy,<有效对手>')
    target = (args.output_dir if args.output_dir else ROOT/'reports/review').resolve()
    if not target.is_relative_to(ROOT.resolve()/'reports'):
        raise RuntimeError('临时录屏必须写在本工程reports目录内')
    if not args.name or Path(args.name).name != args.name or args.name in ('.','..'):
        raise RuntimeError('录屏名称必须是单一文件名')
    target.mkdir(parents=True, exist_ok=True)
    stills = args.stills_dir.resolve() if args.stills_dir else None
    if stills is not None and not stills.is_relative_to(ROOT.resolve()/'reports'):
        raise RuntimeError('审片截图必须写在本工程reports目录内')
    if stills is not None:
        stills.mkdir(parents=True, exist_ok=True)
    avi = target/(args.name+'.avi')
    mp4 = avi.with_suffix('.mp4')
    if avi.exists() or mp4.exists(): raise RuntimeError('影片已存在，请使用新名称')
    try:
        record_review(args, target, stills, avi, mp4)
    except BaseException:
        avi.unlink(missing_ok=True)
        mp4.unlink(missing_ok=True)
        raise


def record_review(args, target: Path, stills: Path | None, avi: Path, mp4: Path):
    env = isolated_test_environment(target/(args.name+'-runtime'))
    # 独立运行主游戏不会导入刚安装的PNG；先完成资源导入，避免录到空白纹理。
    with (target/(args.name+'-import.log')).open('w',encoding='utf-8') as log:
        imported=subprocess.run([godot_path(),'--headless','--path',str(ROOT),'--editor','--import','--quit'],stdout=log,stderr=log,timeout=120,env=env)
    import_text=(target/(args.name+'-import.log')).read_text('utf-8',errors='replace')
    if imported.returncode or re.search(r'(?:SCRIPT ERROR:|^ERROR:)',import_text,re.MULTILINE):raise RuntimeError('主游戏录屏前资源导入失败')
    command = [godot_path(), '--path', str(ROOT), '--resolution', args.resolution, '--write-movie', str(avi),
               '--fixed-fps', '60', '--disable-render-loop', '--quit-after', str(args.frames + 2), '--', '--capture-size='+args.resolution,
               '--review-forward-candidate='+str(args.forward_candidate.resolve()) if args.forward_candidate else '--review-zetton-defense' if args.zetton_defense else '--review-zetton' if args.zetton else '--review-reactions' if args.reactions else '--review-air' if args.air else '--review-phase3' if args.phase3 else '--review-final' if args.final else '--review-color-switches' if args.color_switches else '--review-switches' if args.switches else '--review-dash' if args.dash else '--review-back-walk' if args.back_walk else '--review-forward-walk' if args.forward_walk else '--review' if args.review else '--demo']
    if args.zetton_air: command[-1]='--review-zetton-air'
    if args.zetton_counter:
        command[-1]='--review-zetton-counter'
        command.append('--review-trace='+str(target/(args.name+'-trace.json')))
    if args.throws: command[-1]='--review-throws'
    if args.fighter_throws:
        command[-1]='--review-fighter-throws'
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
    if args.skill:
        command.append('--review-skill='+args.skill)
    if stills is not None: command.append('--review-stills='+str(stills))
    if args.pages or args.review or args.forward_walk or args.back_walk or args.forward_candidate or args.dash or args.switches or args.color_switches or args.final or args.phase3 or args.air or args.reactions or args.zetton or args.zetton_defense or args.zetton_air or args.throws or args.fighter_throws or args.skill or args.specials or args.supers or args.feedback or args.audio or args.hud:
        command.append('--review-trace='+str(target/(args.name+'-trace.json')))
    if args.ultraseven or args.forward_candidate or args.seven_defense or args.seven_fourth or args.seven_body or args.seven_air_special:
        command.append('--review-capture-frames='+str(args.frames))
    command.append('--harness=res://tests/review/cli_harness.gd')
    command.append('--review-force-draw')
    command.append('--review-capture-frames='+str(args.frames))
    command.append('--review-trace='+str(target/(args.name+'-trace.json')))
    if args.pair:command.append('--capture-pair='+args.pair)
    manifest_path=ROOT/'assets/fighters/zetton/animations/manifest.json'
    manifest_before=hashlib.sha256(manifest_path.read_bytes()).hexdigest() if args.zetton_defense or args.zetton_air else None
    with movie_resolution(args.resolution), (target/(args.name+'.log')).open('w', encoding='utf-8') as log:
        process = subprocess.run(command, stdout=log, stderr=log, timeout=600, env=env)
    result = {'godot_exit': process.returncode}
    runtime_log=(target/(args.name+'.log')).read_text('utf-8',errors='replace')
    if process.returncode or re.search(r'(?:SCRIPT ERROR:|^ERROR:)',runtime_log,re.MULTILINE):
        avi.unlink(missing_ok=True)
        raise RuntimeError('录屏存在脚本/资源错误或异常退出；无效AVI已删除，请查看日志')
    report = json.loads((target/(args.name+'-trace.json')).read_text(encoding='utf-8'))
    rendered = validate_render_trace(report, args.frames, args.resolution)
    result['rendered_ticks'] = len(rendered)
    result['source_movie_frames'] = [rendered[0]['source_movie_frame'], rendered[-1]['source_movie_frame']]
    if args.skill:
        trace = report['trace']
        requested_pair = args.pair.split(',')
        if len(trace) != args.frames or {row['section'] for row in trace} != {0, 1}:
            raise RuntimeError('技能审片未完整覆盖双朝向360tick')
        if [row.get('render_pass') for row in trace] != list(range(1, args.frames + 1)):
            raise RuntimeError('实录缺少逐tick完成重绘的证据')
        for row, drawn in zip(trace, rendered):
            participants = row.get('pair', [])
            if not isinstance(participants, list) or len(participants) != 2 or any(not isinstance(fighter, dict) or fighter.get('fighter') != requested for fighter, requested in zip(participants, requested_pair)):
                raise RuntimeError('技能审片逐tick双方角色与请求配对不符')
            if any(row.get(key) != drawn.get(key) for key in ('source_movie_frame', 'root_sha256', 'viewport_sha256')):
                raise RuntimeError('技能模拟trace与实际重绘像素证据未逐tick对应')
            shown = row.get('rendered_sprites', [])
            if len(shown) != 2 or any(sprite['flip_h'] != (fighter['facing'] < 0) for sprite, fighter in zip(shown, row['pair'])):
                raise RuntimeError('实录Sprite朝向与模拟不符')
        for section, facing in [(0, 1), (1, -1)]:
            rows = [row for row in trace if row['section'] == section]
            if not any(row['move'] == args.skill or (args.skill in ('charge', 'idle') and row['state'] == args.skill) for row in rows):
                raise RuntimeError(f'技能未由真实输入触发：{args.skill} 朝向{facing}')
            if any(row['pair'][0]['facing'] != facing for row in rows):
                raise RuntimeError('技能审片朝向与分段不符')
            if args.skill == 'idle':
                for player in range(2):
                    samples = [row['pair'][player] for row in rows]
                    manifest = json.loads((ROOT/'assets/fighters'/samples[0]['fighter']/'animations/manifest.json').read_text(encoding='utf-8'))
                    clip = manifest['clips']['idle']
                    if any(sample['state'] != 'idle' or sample['clip'] != 'idle' or sample['height'] != 0 for sample in samples):
                        raise RuntimeError('待机审片包含非待机姿势')
                    if len({sample['x'] for sample in samples}) != 1 or any(sample['pixel_bottom'] != 0 for sample in samples):
                        raise RuntimeError('待机审片存在位移或脚底离地')
                    if {sample['sprite'] for sample in samples} != set(range(len(clip['rects']))):
                        raise RuntimeError('待机审片未显示全部独立帧')
        result['skill'] = args.skill
        result['trace_ticks'] = len(trace)
        result['rendered_ticks'] = trace[-1]['render_pass']
        replay = subprocess.run([godot_path(), '--headless', '--path', str(ROOT),
                                 '--script', 'res://tests/review_inputs.gd', '--',
                                 '--skill-trace='+str(target/(args.name+'-trace.json'))],
                                capture_output=True, text=True, timeout=120, env=env)
        replay_text = replay.stdout + replay.stderr
        (target/(args.name+'-replay.log')).write_text(replay_text, encoding='utf-8')
        if replay.returncode or 'SKILL_TRACE_REPLAY {"missing":[]}' not in replay_text or re.search(r'(?:SCRIPT ERROR:|^ERROR:)', replay_text, re.MULTILINE):
            raise RuntimeError('技能实录原InputFrame独立回放不一致，请查看replay日志')
        result['input_replay'] = '360tick状态、事件与双方实际姿势一致'
    if args.fighter_throws:
        trace_path = target/(args.name+'-trace.json')
        trace = json.loads(trace_path.read_text(encoding='utf-8'))['trace']
        sections = set(row['section'] for row in trace)
        if len(trace) != args.frames or sections != set(range(10)):
            raise RuntimeError('佐菲五投审片未走完十组实际模拟tick')
        if any(sum(event['kind'] == 'throw_slam' for row in trace if row['section'] == section for event in row['events']) != 1 for section in sections):
            raise RuntimeError('佐菲五投审片存在未命中或重复撞地，不能作为完整审片')
        required = {'player', 'fighter', 'state', 'state_tick', 'move', 'move_tick', 'clip', 'sprite', 'height', 'hurtbox_bottom', 'pixel_bottom', 'alpha_bounds', 'texture', 'rect', 'anchor'}
        if any(len(row.get('pair', [])) != 2 or any(not required.issubset(fighter) for fighter in row['pair']) for row in trace):
            raise RuntimeError('佐菲五投trace缺少双方实际姿势或双净空，不能作为完整审片')
        clearance = []
        for section in sorted(sections):
            rows = [row for row in trace if row['section'] == section]
            held = [row for row in rows if row['pair'][1]['state'] == 'thrown' and row['pair'][0].get('target', {}).get('mode') == 'hold']
            if not held or any(row['pair'][0].get('grip_world') is None or row['pair'][0]['grip_world'] != row['pair'][1].get('grab_world') for row in held):
                raise RuntimeError('佐菲五投trace缺少持握样本或双方世界抓点不一致')
            participants = []
            for player in range(2):
                samples = [row['pair'][player] for row in rows]
                participant = {'player': player, 'fighter': samples[0]['fighter'],
                               'hurtbox_min': min(sample['hurtbox_bottom'] for sample in samples),
                               'pixel_min': min(sample['pixel_bottom'] for sample in samples),
                               'below_ground_ticks': sum(sample['pixel_bottom'] < 0 for sample in samples)}
                if player == 1:
                    participant['held_pixel_min'] = min(row['pair'][1]['pixel_bottom'] for row in held)
                participants.append(participant)
            clearance.append({'section': section, 'action': rows[0]['action'], 'facing': rows[0]['pair'][0]['facing'],
                              'held_ticks': len(held), 'participants': participants})
        result['throw_sections'] = len(sections)
        result['trace_ticks'] = len(trace)
        result['clearance'] = clearance
    if manifest_before:
        result['zetton_manifest_sha256']=manifest_before
        assert manifest_before==hashlib.sha256(manifest_path.read_bytes()).hexdigest(), '录制期间正式资源清单发生变更'
    if args.forward_candidate:
        result['candidate_clip'] = str(args.forward_candidate.resolve())
        result['candidate_clip_sha256'] = hashlib.sha256(args.forward_candidate.read_bytes()).hexdigest()
        result['production_installed'] = False
    if not avi.exists():
        raise RuntimeError('主游戏未输出影片；请查看日志')
    source_video = probe_video(avi)
    source_streams = [stream for stream in source_video['streams'] if 'width' in stream]
    first_frame, last_frame = result['source_movie_frames']
    if len(source_streams) != 1 or int(source_streams[0].get('nb_read_frames', -1)) != last_frame + 1:
        raise RuntimeError('源AVI实解码帧数与最后一次重绘不符，禁止用转码补齐')
    result['source_video'] = source_video
    result['discarded_startup_frames'] = first_frame
    trim = []
    if first_frame:
        trim = ['-vf', f'trim=start_frame={first_frame}:end_frame={last_frame + 1},setpts=PTS-STARTPTS',
                '-af', f'atrim=start={first_frame / 60}:end={(last_frame + 1) / 60},asetpts=PTS-STARTPTS']
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(avi),*trim,'-fps_mode','passthrough','-c:v','libx264','-crf','18',
                    '-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(mp4)],check=True)
    assert avi.resolve().is_relative_to(target) and avi.suffix == '.avi'
    avi.unlink()
    result['video'] = probe_video(mp4)
    expected_size = [int(value) for value in args.resolution.split('x')]
    video_streams = [stream for stream in result['video']['streams'] if 'width' in stream]
    if len(video_streams) != 1 or [video_streams[0]['width'], video_streams[0]['height']] != expected_size:
        mp4.unlink()
        raise RuntimeError('实收影片分辨率与请求不符，无效影片已删除，不能作为该分辨率验收')
    if int(video_streams[0].get('nb_read_frames', -1)) != args.frames:
        raise RuntimeError('实收MP4帧数与逐tick重绘证据不符')
    result['temporary_video'] = str(mp4)
    result['cleanup'] = 'AVI已删除；审阅后删除本次MP4，不建立工程外归档。'
    (target/(args.name+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__': main()

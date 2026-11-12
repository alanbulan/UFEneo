"""生成强壮日冕赛罗全部动作帧的逐帧提示词计划。

帧数来自基础赛罗现装 manifest；动作只写本形态人物本体，不含任何特效。
计划只供生图与落格使用，不安装、不改共享文件。

用法：.venv/bin/python tools/rebuild/ultraman-zero__strong_corona/build_frame_plan.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "content/fighters/ultraman-zero"
MANIFEST = ROOT / "assets/fighters/ultraman-zero/animations/manifest.json"
OUT = ROOT / "tools/rebuild/ultraman-zero__strong_corona/frame_plan.json"
FIGHTER = "ultraman-zero__strong_corona"
REFERENCE = f"art/fighters/{FIGHTER}/stage1/idle/frames/pixel-raw-03.png"

PREFIX = (
    "同一强壮日冕赛罗，2D像素整帧。参考图是同一待机像素整帧的原始竖幅："
    "人物几乎占满画面高度，头顶与脚底只留少量空白；保持参考的竖幅构图、"
    "人物高度与体量、成年人头身比和四肢粗细，只改动作。"
)
SUFFIX = (
    "配色与参考一致：红色主甲、银面银腿、金色头冠向后掠、黄眼、绿额灯、"
    "蓝芯胸计时器、红拳套。只画单个完整人物的单独一帧，全身不裁切；"
    "纯透明背景，无地面、阴影、光晕、颗粒、文字、边框、网格；"
    "只画人物本体，无任何能量光效；像素风与参考一致。"
)

MOVE_STAGES = {
    "light1": ["护架收拳蓄势", "前手直拳打出一半", "前手短直拳完全伸出", "拳收回胸前护架"],
    "light2": ["后手收拳蓄势、后肩后转", "后手直拳打出一半", "后手直拳完全伸出", "收拳回胸前护架"],
    "light3": ["屈膝下沉、前拳降到腰下", "前拳由下向上勾起", "上勾拳打到最高点", "收拳落回护架", "重心回中"],
    "heavy": ["后肩后转、后拳收腰", "前脚踏出半步、肩送前", "踏步重拳完全打出", "拳收、前脚落稳"],
    "launcher": ["屈膝下沉、双拳收腰", "前拳由下向上勾出", "上勾拳到顶、身体升起", "落回护架"],
    "spin_heavy": ["收拳转肩蓄势", "髋部先转、肘随身后摆", "回身横扫肘完全展开", "肘收、身体转正"],
    "crush": ["双拳举过头顶蓄势", "双拳举到最高、上身后仰", "双拳向下砸出一半", "双拳砸到腰前",
              "砸击落点、屈膝下沉", "保持下压", "拳开始回收", "起身收拳", "回到护架"],
    "tackle": ["屈膝沉肩蓄势", "前脚踏出、肩头压低", "沉肩突进一半", "肩头撞出",
               "身体跟进", "脚步刹车", "收肩起身", "回护架"],
    "sweep": ["蹲身、重心移到后脚", "前腿贴地扫出一半", "低扫腿完全展开", "扫腿经过前方",
              "腿收回、身体转动", "起身一半", "回护架"],
    "slide": ["蹲身蓄势", "前脚蹬地、身体前倾", "低身滑铲一半", "滑铲腿完全伸出",
              "滑行保持低位", "屈膝刹车", "起身一半", "回护架"],
    "crouch_light": ["蹲姿收拳", "蹲姿前手直拳打出一半", "蹲姿直拳完全伸出", "收拳回蹲姿护架"],
    "crouch_light2": ["蹲姿后手收拳", "蹲姿后手直拳打出一半", "蹲姿后手直拳完全伸出", "收拳回蹲姿护架"],
    "vertical_light": ["垂直跳起、收拳", "空中前手直拳打出一半", "空中直拳完全伸出", "收拳下落"],
    "vertical_heavy": ["垂直跳起、双拳举高", "空中双拳下砸一半", "双拳砸到腰前", "屈膝落地", "回护架"],
    "diagonal_light": ["斜跳起、屈膝收腿", "空中膝撞一半", "膝撞完全顶出", "收腿下落"],
    "diagonal_heavy": ["斜跳起、屈膝蓄力", "空中飞踢腿伸出一半", "飞踢腿完全伸出", "收腿下落"],
    "air_crush": ["空中双拳举高", "空中双拳下砸一半", "双拳砸到腰前", "落地屈膝", "起身回护架"],
    "dive": ["空中收腿蓄势", "身体前倾、脚跟对准前方", "俯冲脚跟踢出", "腿收回、身体下落"],
    "chase_light1": ["追击前踏、收拳", "追击前刺拳打出一半", "前刺拳完全伸出", "收拳回护架"],
    "chase_light2": ["追击贴身、肘部收拢", "横肘扫出一半", "横肘完全展开", "收肘回护架"],
    "chase_end": ["追击跃起、双掌举起", "双掌向下砸出一半", "双掌砸到地面、屈膝"],
    "dash_light": ["冲刺步中收拳", "冲刺直拳打出一半", "冲刺直拳完全伸出", "收拳回护架"],
    "dash_heavy": ["冲刺起跳、屈膝", "空中飞踢腿完全伸出", "落地收腿屈膝"],
    "back_counter": ["后闪一步、收拳", "后闪中前手拳打出一半", "反击直拳完全伸出", "收拳回护架"],
    "dodge_counter": ["侧闪、身体压低", "侧闪中收拳", "反击拳打出一半", "反击拳完全伸出", "回护架"],
    "wake_low": ["起身中单膝跪地、收拳", "起身下段拳打出一半", "下段拳完全伸出", "收拳站起"],
    "wake_mid": ["起身中屈膝、收拳", "起身中段拳打出一半", "中段拳完全伸出", "收拳站起", "站稳护架"],
    "guard_counter": ["护架收紧、肩后转", "护架中前臂推出", "反击前臂完全推出", "收臂回护架"],
    "burst": ["屈膝下沉、双拳收腰", "双拳向两侧张开、身体蓄力", "爆气张臂到最大", "收臂回护架"],
    "pulse": ["护架收拳、前手抬到胸前", "前手向前推出一半", "发射手完全前伸", "手收回一半", "回护架"],
    "low_pulse": ["蹲身、前手收到腰侧", "前手向前下方推出一半", "低姿发射手完全伸出", "手收回、起身一半", "回护架"],
    "air_pulse": ["空中收腿、手收到胸前", "空中前手向前下方推出一半", "空中发射手完全伸出", "手收回、继续下落"],
    "ranged_forward": ["侧身收拳、前手收到胸前", "前脚踏出、手向前推出一半", "远程发射手完全前伸",
                       "保持前伸", "手收回一半", "回护架"],
    "special": ["双臂收到胸前聚能", "双拳在胸前靠拢", "双拳蓄力到最紧", "双臂向前伸出",
                "双臂形成L字前臂", "前臂前缘向前推出一半", "发射、双臂完全前伸", "保持发射",
                "后坐力使上身后仰", "保持发射", "双臂开始回收", "收臂一半",
                "回护架", "重心回中", "站定", "回到待机护架"],
    "special2": ["额灯前倾、双拳收在胸前", "双拳靠拢蓄力", "额头前顶、身体后仰", "额灯蓄光到最亮",
                 "头略低、双手向下收", "额灯向前射出光束", "头部保持前顶", "身体承受后坐",
                 "手开始回收", "头回正", "回护架", "重心回中",
                 "站定", "护架微调", "待机", "待机护架"],
    "special3": ["双手抬向头侧、准备取镖", "双手抓住两侧头镖", "头镖取下、双手向外拉", "双臂展开到头侧",
                 "一手向前掷出一半", "双镖离手、双臂前伸", "双臂完全展开", "保持投掷姿态",
                 "双臂开始回收", "头镖回旋、双手抬起", "双手向头侧接镖", "双镖接回、手收拢",
                 "回护架", "重心回中", "站定", "待机护架"],
    "air_special": ["空中收膝、双臂收到胸前", "双臂靠拢蓄力", "双臂向前伸出", "L字前臂形成",
                    "发射、双臂前伸", "保持发射、身体后仰", "双臂回收", "收臂下落"],
    "throw_forward": ["扣住对手手臂、身体转身", "背起对手、重心下沉", "过肩摔出、双臂前伸"],
    "throw_back": ["从后抱住对手腰部", "抱腰转身、重心下沉", "回身摔出、双臂前伸"],
    "air_throw": ["空中揽住对手肩颈", "空中扣肩、身体翻转", "空中翻摔一半", "翻摔到顶",
                  "松手、身体下落", "落地屈膝"],
    "dash_throw": ["冲刺中张开双臂", "冲步抱住对手身体", "抱身收紧", "抱起对手", "前冲摔出", "落地屈膝"],
    "taunt": ["抬手向对手招了招", "手掌翻转、头微扬", "收回手、护架站定"],
    "motion_214": ["前踏收拳蓄势", "前脚踏出、肩送前", "双臂向前推出一半", "突进拳完全伸出",
                   "保持前推", "收臂一半", "回护架", "站定"],
    "motion_236": ["垫步收掌蓄势", "垫步向前、双掌收到胸前", "双掌向前推出一半", "双掌完全推出",
                   "保持前推", "收掌一半", "回护架", "站定"],
    "motion_623": ["屈膝下沉、双手收在胸前", "单膝向上提起", "膝盖上顶一半", "膝盖顶到最高",
                   "收膝下落", "脚踏地", "回护架", "站定"],
    "motion_22": ["双臂收到胸前", "双臂交叉成护壁", "护壁向前推出一半", "护壁完全展开",
                  "保持护壁", "收臂一半", "回护架", "站定"],
    "motion_41236": ["双手扣住对手手臂", "转身背起对手", "对手过顶一半", "过顶摔到最高点",
                     "向下摔出", "松手、屈膝", "起身", "回护架"],
}

STATE_STAGES = {
    "walk_forward": ["前脚迈出、后脚蹬地", "前脚承重、后脚离地", "后脚向前收、重心前移", "双脚落稳、准备下一步"],
    "walk_back": ["前脚向后踏出、重心后移", "后脚承重、前脚离地", "前脚向后收、身体后坐", "双脚落稳、准备下一步"],
    "crouch_start": ["屈膝开始下蹲", "蹲到底、双拳护架"],
    "crouch": ["蹲姿护架、重心下沉", "蹲姿护架微调、双拳护胸"],
    "crouch_rise": ["蹲姿起身一半", "站起回护架"],
    "crouch_guard": ["蹲姿双拳护胸", "蹲姿护架收紧"],
    "crouch_turn": ["蹲姿、肩向后转", "蹲姿转体一半", "蹲姿转正"],
    "crouch_blockstun": ["蹲姿护架受震、上身后仰", "蹲姿护架回弹"],
    "guard": ["双拳抬到胸前护架", "护架收紧、肘部下沉"],
    "block": ["双前臂在胸前交叉护架、身体略侧"],
    "blockstun": ["护架受震、上身后仰", "护架回弹、脚步撑住"],
    "hit": ["受击后仰、肩背收紧", "回弹、身体前倾"],
    "hit_high": ["头部受击后仰", "身体后仰到最大", "回弹、头回正"],
    "hit_mid": ["胸腹受击、上身后仰", "身体弯腰后缩", "回弹、身体回正"],
    "hit_crouch": ["蹲姿受击、上身后仰", "蹲姿身体后缩", "蹲姿回弹"],
    "hit_air": ["空中受击、身体后仰", "空中身体翻转", "空中回弹"],
    "hit_air_rise": ["空中受击上升、身体后仰", "上升中身体翻转", "上升到顶、四肢张开"],
    "hit_air_fall": ["空中下落、身体后仰", "下落中身体翻转", "下落四肢张开"],
    "launch_rise": ["被击飞上升、身体后仰", "上升中双腿离地", "上升到顶、身体翻转"],
    "launch_fall": ["从空中下落、身体后仰", "下落中翻转", "下落双腿伸开"],
    "air_rise": ["空中上升、收腿"],
    "air_apex": ["空中最高点、收腿护架"],
    "air_fall": ["空中下落、双腿伸开"],
    "air_recover": ["空中收腿", "空中转身", "伸腿准备落地", "落地前屈膝"],
    "air_tech": ["空中收腿抱膝", "空中翻转一半", "空中继续翻转", "伸腿落地"],
    "takeoff": ["屈膝蹬地", "双脚离地上升"],
    "vertical_jump": ["屈膝起跳", "空中上升", "空中最高点", "下落"],
    "land": ["落地屈膝", "起身回护架"],
    "dash": ["冲刺前倾、前脚迈出", "冲刺中后脚蹬地", "冲刺中前脚承重", "冲刺步循环"],
    "dash_start": ["屈膝启动", "前倾踏出第一步"],
    "dash_stop": ["刹车、后脚拖地", "屈膝稳住", "站起回护架"],
    "backstep": ["后脚向后踏出", "重心后移", "后脚承重", "前脚收回", "回护架"],
    "dodge": ["侧闪屈膝", "侧闪中身体压低", "侧闪到最远", "侧闪回中", "收回脚步", "回护架"],
    "roll_forward": ["蹲身抱膝", "向前滚翻一半", "滚翻到背", "滚翻起身", "回护架"],
    "roll_back": ["蹲身抱膝", "向后滚翻一半", "滚翻到背", "滚翻起身", "回护架"],
    "flip_forward": ["屈膝蓄力", "向前空翻起跳", "空中翻转", "落地屈膝"],
    "flip_back": ["屈膝蓄力", "向后空翻起跳", "空中翻转", "落地屈膝"],
    "bounce": ["落地弹起", "空中反弹", "再次落地"],
    "down": ["倒地仰躺、四肢张开", "倒地静止、准备起身"],
    "getup": ["撑地起身", "站起回护架"],
    "getup_forward": ["伏地撑手", "收膝跪起", "单膝起身", "站起一半", "站稳护架"],
    "getup_back": ["仰躺收腿", "翻身撑地", "跪起", "站起一半", "站稳护架"],
    "wake": ["倒地撑手", "收膝坐起", "单膝跪起", "站起一半", "站稳护架"],
    "grabbed": ["被抓住肩臂、身体前倾", "挣扎后拉", "被拉近、身体前倾"],
    "thrown_forward": ["被向前抛出、身体前倾", "空中翻转", "落地前伸腿"],
    "thrown_back": ["被向后抛出、身体后仰", "空中翻转", "落地前伸腿"],
    "thrown_air": ["空中被抛出、身体翻转", "继续翻转", "四肢张开", "下落"],
    "thrown_dash": ["被拖拽前冲、身体前倾", "继续前冲", "脚步踉跄", "屈膝稳住"],
    "stun": ["站立摇晃、双臂垂下", "身体向左晃", "身体向右晃", "低头摇晃", "抬头摇晃", "回稳"],
    "guardbreak": ["护架被破、双臂张开", "上身后仰", "脚步踉跄", "跪地撑住"],
    "intro": ["单膝落地、一手撑地", "起身一半、收拳", "站定护架"],
    "victory": ["举拳过头、挺胸", "收拳站定"],
    "win": ["举拳过头、挺胸", "收拳站定"],
    "defeat": ["单膝跪地、低头", "倒地"],
    "timeout": ["双手叉腰、低头", "抬头站定"],
    "ko": ["仰面倒地、四肢张开", "倒地静止"],
    "charge_start": ["屈膝下沉、双拳收腰", "双拳向两侧张开", "蓄气起势"],
    "charge": ["蓄气护架、双拳收在胸前", "蓄气加深、身体下沉", "蓄气保持、肩背收紧", "蓄气循环"],
    "charge_stop": ["收臂回护架", "站定"],
    "chase_takeoff": ["追击前踏", "蹬地跃起", "空中前冲"],
    "light_combo1": ["护架收拳蓄势", "前手直拳打出一半", "前手短直拳完全伸出"],
    "light_combo2": ["收拳转肩", "后手直拳打出一半", "后手直拳完全伸出"],
    "light_combo3": ["屈膝下沉、前拳降到腰下", "前拳由下向上勾起", "上勾拳打到最高点", "收拳落回护架"],
    "throw_tech": ["双手扣住对手手臂", "转体背起对手", "过肩摔出", "松手回护架"],
}

AIR_CLIPS = {
    "air_apex", "air_fall", "air_recover", "air_rise", "air_tech", "bounce",
    "flip_back", "flip_forward", "hit_air", "hit_air_fall", "hit_air_rise",
    "launch_fall", "launch_rise", "takeoff", "thrown_air", "thrown_back",
    "thrown_dash", "thrown_forward", "vertical_jump",
    "air_crush", "air_pulse", "air_special", "air_throw", "diagonal_heavy",
    "diagonal_light", "dive", "vertical_heavy", "vertical_light", "dash_heavy",
}
CROUCH_CLIPS = {
    "crouch", "crouch_blockstun", "crouch_guard", "crouch_light", "crouch_light2",
    "crouch_rise", "crouch_start", "crouch_turn", "hit_crouch", "wake_low",
    "slide", "dodge", "chase_takeoff",
}
DOWN_CLIPS = {"down", "getup", "getup_back", "getup_forward", "wake", "ko", "defeat", "bounce", "guardbreak"}
STANCE_CLIPS = {"idle", "guard", "block", "crouch_guard", "form_switch"}

DETAILS = [
    "重心略前移", "肩再送出一寸", "前脚再压低", "后脚蹬地", "肘部再收紧",
    "身体再转一点", "拳头再向前", "呼吸下沉", "后肩再打开", "髋部再转",
]


def stages_for(clip: str, is_move: bool) -> list[str]:
    table = MOVE_STAGES if is_move else STATE_STAGES
    if clip in table:
        return table[clip]
    # 未列出的状态：按名字给出通用动作。
    if clip.startswith("hit"):
        return ["受击后仰", "身体回弹", "回正"]
    if clip.startswith("air"):
        return ["空中收腿", "空中转身", "伸腿下落"]
    if clip.startswith("thrown"):
        return ["被抛出、身体翻转", "空中继续翻转", "四肢张开", "下落"]
    if clip.startswith("getup") or clip.startswith("wake"):
        return ["撑地", "收膝跪起", "站起一半", "站稳护架"]
    if "guard" in clip or "block" in clip:
        return ["双拳护架", "护架收紧"]
    return ["护架站立", "重心下沉", "动作推进", "回护架"]


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    move_ids = set(json.loads((BASE / "move_manifest.json").read_text(encoding="utf-8")))
    clips = {}
    total = 0
    for clip, entry in manifest["clips"].items():
        n = len(entry["rects"])
        is_move = clip in move_ids
        stages = stages_for(clip, is_move)
        frames = []
        for i in range(n):
            stage = stages[min(len(stages) - 1, round(i * (len(stages) - 1) / max(1, n - 1)))]
            detail = DETAILS[i % len(DETAILS)]
            foot_row = 225 if clip in AIR_CLIPS else 247
            frames.append({
                "index": i,
                "action": f"{stage}；{detail}。这是第{i + 1}/{n}帧。",
                "foot_row": foot_row,
                "height_class": ("air" if clip in AIR_CLIPS else
                                 "crouch" if clip in CROUCH_CLIPS else
                                 "down" if clip in DOWN_CLIPS else "ground"),
                "stance_gate": clip in STANCE_CLIPS,
            })
        total += n
        clips[clip] = {
            "group": "moves" if is_move else "states",
            "frames": frames,
            "ticks": entry.get("ticks", []),
            "loop": entry.get("loop", False),
            "raw_dir": (f"art/fighters/{FIGHTER}/stage2/moves/{clip}/frames" if is_move
                        else f"art/fighters/{FIGHTER}/stage2/states/{clip}/frames"),
            "cell_prefix": f"art/fighters/{FIGHTER}/stage1/cells/{clip}",
        }
    plan = {
        "fighter": FIGHTER,
        "reference": REFERENCE,
        "prompt_prefix": PREFIX,
        "prompt_suffix": SUFFIX,
        "total_frames": total,
        "clips": clips,
        "rules": {
            "single_reference": "每一帧只传 reference 这一张身份锚。",
            "no_fx": "人物帧只画本体，整帧不得烘焙光束、光晕、颗粒、能量球、飞行物。",
            "fixed_scale": "全部帧按身份锚 scale 0.123198 落格，不逐帧重标定。",
            "height_gate": "ground/站立帧缩放后站高 188±8%；crouch/air/down 登记数值。",
            "stance_gate": "idle/guard/block/crouch_guard/form_switch 落格后脚外缘/站高 0.65–0.80；form_switch 末帧必须过。",
        },
    }
    OUT.write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"clips": len(clips), "total_frames": total, "out": str(OUT.relative_to(ROOT))},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

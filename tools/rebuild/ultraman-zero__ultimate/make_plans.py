"""生成究极赛罗逐 clip 的落格 plan 与逐帧生图请求。

每个 clip 一组固定比例（全套动作共用 plan 顶层的 action_scale），
逐帧只写该帧动作；提示词固定段只交代同一角色、右侧视、纯人物与无特效。
用法：
    .venv/bin/python tools/rebuild/ultraman-zero__ultimate/make_plans.py --group states
    .venv/bin/python tools/rebuild/ultraman-zero__ultimate/make_plans.py --group moves --clip light1
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
FIGHTER = "ultraman-zero__ultimate"
STAGE = ROOT / "art/fighters" / FIGHTER / "stage1"
PLANS = ROOT / "tools/rebuild" / FIGHTER / "plans"
REQUESTS = ROOT / "tools/rebuild" / FIGHTER / "requests"
ACTION_SCALE = 0.2027897
GROUND, AIR = 247, 225
CELL = 256
AIR_SPECIAL_CELL = 288

HEAD = ("参考图是唯一身份与画风来源：同一究极赛罗，右侧视像素整帧，银甲肩翼、"
        "肩后近侧薄刃、层叠胸甲与蓝灯、右前臂长刃、黄眼绿额灯照参考。")
BODY = "四肢粗细必须与参考完全一致，不缩头、不放大手脚。"
TAIL = ("右侧视，人物完整不裁切，透明背景，无地面文字边框；整帧只有人物本体，"
        "无光束、光晕、颗粒、蓄气圈、贴掌光、飞行物。")

# clip -> (beats, foot_rows, pose_exception indices)
STATES: dict[str, tuple[list[str], list[int], list[int]]] = {
    "idle": ([
        "格斗待机护架：两脚前后分开，双膝屈沉，双拳抬到胸前",
        "呼吸下沉：双拳保持护架略沉，肩线放松，膝盖微沉",
        "重心左移：髋部压向前脚，后脚掌轻压，双拳一高一低",
        "回中抬头：重心回中，头略抬，双拳收回胸前",
        "后脚碾地：后脚轻碾，膝盖再屈，肩甲随呼吸起伏",
        "回到护架：双拳回胸前，双脚站定，视线朝前，与首帧接续",
    ], [GROUND] * 6, []),
    "walk_forward": ([
        "前脚向前迈出脚跟着地，后脚蹬直，双拳护架",
        "重心前移，前脚踩实，后脚离地屈膝",
        "后脚向前摆过支撑腿，膝盖抬到腰高",
        "后脚落地成前后站，前脚掌碾地",
        "前脚再向前迈，身体略前倾，双臂随步伐小幅摆动",
        "重心压到前脚，后脚蹬离地面",
        "后腿前摆，脚尖勾起准备落地",
        "双脚落成护架站，双拳收回胸前，与首帧接续",
    ], [GROUND] * 8, []),
    "walk_back": ([
        "前脚向后退半步，脚尖点地，重心后坐",
        "后脚踩实，前脚离地屈膝",
        "前脚向后收过支撑腿，膝盖内收",
        "双脚落回前后护架，身体回正",
    ], [GROUND] * 4, []),
    "crouch": ([
        "双膝深屈下蹲，臀部下沉，双拳收在胸前，脚掌贴地",
        "蹲势略下沉，肩甲随呼吸微动，双拳护住胸腹",
    ], [GROUND] * 2, [0, 1]),
    "crouch_start": ([
        "从站架开始屈膝，臀部后坐，双拳下落",
        "蹲到底，双脚踩实，上身略前倾，双拳护胸",
    ], [GROUND] * 2, [1]),
    "crouch_rise": ([
        "蹲姿发力，双脚蹬地，膝盖开始伸直",
        "站起回到护架，双拳抬回胸前",
    ], [GROUND] * 2, [0]),
    "crouch_guard": ([
        "蹲姿双臂交叉护住头胸，肩甲前挡",
        "蹲姿护架微收，双拳贴近面门，膝盖保持弯曲",
    ], [GROUND] * 2, [0, 1]),
    "crouch_turn": ([
        "蹲姿重心移到前脚，后脚脚跟抬起",
        "蹲姿碾转，髋部转向后方，后脚向外撇",
        "蹲姿转回侧向，双脚落稳，双拳护胸",
    ], [GROUND] * 3, [0, 1, 2]),
    "crouch_blockstun": ([
        "蹲姿护架被压退，双臂上抬吃住冲击，上身后仰",
        "蹲姿回稳，双臂放下半寸，双拳仍护胸",
    ], [GROUND] * 2, [0, 1]),
    "guard": ([
        "站架双臂交叉护住头胸，肘部收紧",
        "护架保持，肩甲前挡，双拳略上抬",
    ], [GROUND] * 2, []),
    "block": (["双臂交叉高位护架，身体侧向收紧，双拳护住头胸"],
              [GROUND], [0]),
    "dash": ([
        "前脚蹬地起动，身体前倾，双拳收腰",
        "大步前冲，前脚跨出，后脚蹬直",
        "后脚腾空前摆，身体压低，肩甲前送",
        "前脚落地制动，双拳回到护架",
    ], [GROUND, GROUND, AIR, GROUND], [2]),
    "dash_start": ([
        "屈膝蓄力，后脚蹬地准备",
        "身体前倾冲出，前脚离地",
    ], [GROUND, AIR], [1]),
    "dash_stop": ([
        "前脚重踩制动，身体后坐",
        "后脚拖地减速，双臂张开平衡",
        "站稳回到护架",
    ], [GROUND] * 3, []),
    "backstep": ([
        "前脚蹬地向后跃，身体后仰",
        "双脚离地后跃，双拳收胸",
        "后脚先落地，膝盖弯曲缓冲",
        "前脚落地，重心后坐",
        "站稳护架",
    ], [GROUND, AIR, GROUND, GROUND, GROUND], [1]),
    "dodge": ([
        "屈膝侧闪，重心压向一侧",
        "双脚蹬地弹开，身体侧倾",
        "腾空侧移，双拳收在胸前",
        "单脚落地，膝盖深屈缓冲",
        "另一脚落稳，重心回中",
        "回护架",
    ], [GROUND, GROUND, AIR, GROUND, GROUND, GROUND], [2]),
    "roll_forward": ([
        "屈膝前扑，双手撑向地面",
        "低头团身，肩背触地开始前滚",
        "团身翻过背部，双腿收在胸前",
        "滚到蹲姿，双脚落地",
        "起身回到护架",
    ], [GROUND] * 5, [1, 2, 3]),
    "roll_back": ([
        "屈膝后坐，双手撑地",
        "团身后滚，背部贴地",
        "翻过肩背，双腿上举",
        "滚到蹲姿，双脚踩实",
        "起身回护架",
    ], [GROUND] * 5, [1, 2, 3]),
    "flip_forward": ([
        "屈膝蹬地起跳，双臂上摆",
        "腾空前翻，团身抱膝",
        "翻转过顶，双腿展开准备落地",
        "双脚落地屈膝，双臂平衡",
    ], [GROUND, AIR, AIR, GROUND], [1, 2]),
    "flip_back": ([
        "屈膝后蹬，身体后仰",
        "腾空后翻，团身收膝",
        "翻转过顶，身体展开",
        "双脚落地缓冲，回护架",
    ], [GROUND, AIR, AIR, GROUND], [1, 2]),
    "vertical_jump": ([
        "屈膝蓄力，双拳收腰",
        "蹬地起跳，身体伸展，双脚离地",
        "腾空到顶点，双拳抬到胸前",
        "下落双脚落地，屈膝缓冲",
    ], [GROUND, AIR, AIR, GROUND], [1, 2]),
    "takeoff": ([
        "屈膝蹬地，前脚离地",
        "身体腾起，双脚离地，双拳收胸",
    ], [GROUND, AIR], [1]),
    "chase_takeoff": ([
        "前倾蹬地，前脚离地",
        "腾空前冲，后脚蹬直",
        "空中收腿准备追击",
    ], [GROUND, AIR, AIR], [1, 2]),
    "land": ([
        "双脚落地屈膝，身体下沉",
        "缓冲站起，双拳回护架",
    ], [GROUND] * 2, [0]),
    "air_apex": (["腾空顶点，双膝收起，双拳护胸，肩甲背刃随身体上升"], [AIR], [0]),
    "air_rise": (["腾空上升，身体伸展，双拳收在胸前，双脚离地"], [AIR], [0]),
    "air_fall": (["腾空下落，双腿微屈准备接地，双拳护胸"], [AIR], [0]),
    "air_recover": ([
        "空中收膝团身，双拳护胸",
        "空中展体，双腿下伸准备落地",
        "伸腿迎地，脚尖朝下",
        "落地屈膝缓冲，双拳前伸平衡",
    ], [AIR, AIR, AIR, GROUND], [0, 1, 2]),
    "air_tech": ([
        "空中屈膝，双臂收在胸前",
        "空中翻身，身体侧转，腿收起",
        "空中展体，双臂张开保持平衡",
        "落地屈膝站稳",
    ], [AIR, AIR, AIR, GROUND], [0, 1, 2]),
    "hit": ([
        "上身向后一顿，头部后仰，双臂震开",
        "回稳半步，双拳收回护架",
    ], [GROUND] * 2, [0]),
    "hit_high": ([
        "头部被击中后仰，肩甲上抬，脚步踉跄",
        "上身后仰到极限，双臂散开",
        "收势回稳，护架略低",
    ], [GROUND] * 3, [0, 1]),
    "hit_mid": ([
        "胸腹被击中，上身前折，双臂内收",
        "身体弓起后退半步",
        "直起身回护架",
    ], [GROUND] * 3, [0, 1]),
    "hit_crouch": ([
        "蹲姿被击中，上身后仰，双拳震开",
        "蹲姿后滑，单手撑地",
        "蹲姿回稳，双拳护胸",
    ], [GROUND] * 3, [0, 1, 2]),
    "hit_air": ([
        "空中受击，身体后仰，四肢张开",
        "空中翻身，双腿上摆",
        "下落中收身护胸",
    ], [AIR] * 3, [0, 1, 2]),
    "hit_air_rise": ([
        "空中被击上浮，身体反弓",
        "上升中翻身，双臂展开",
        "升到顶点收身",
    ], [AIR] * 3, [0, 1, 2]),
    "hit_air_fall": ([
        "空中受击下坠，团身",
        "下坠翻身，双腿朝向地面",
        "接近地面展体准备受身",
    ], [AIR] * 3, [0, 1, 2]),
    "launch_rise": ([
        "被击飞离地，身体后仰上升",
        "上升中翻转，四肢张开",
        "升到顶点，身体开始下坠",
    ], [AIR, AIR, AIR], [0, 1, 2]),
    "launch_fall": ([
        "从顶点下坠，身体后仰",
        "下坠加速，双腿上摆",
        "接近地面，双臂前伸准备受身",
    ], [AIR] * 3, [0, 1, 2]),
    "bounce": ([
        "身体砸地弹起，四肢张开",
        "再次砸地，肩背触地",
        "小幅弹起后落定",
    ], [AIR, GROUND, AIR], [0, 1, 2]),
    "down": ([
        "仰面倒地，四肢摊开，头偏向一侧",
        "躺地微动，膝盖屈起准备起身",
    ], [GROUND] * 2, [0, 1]),
    "getup": ([
        "单手撑地坐起，一膝立起",
        "站起回到护架",
    ], [GROUND] * 2, [0]),
    "getup_forward": ([
        "俯卧撑地，抬头",
        "收膝跪起，一手撑地",
        "单膝立起，重心前移",
        "蹬地起身，身体前倾",
        "站定护架",
    ], [GROUND] * 5, [0, 1, 2]),
    "getup_back": ([
        "仰卧屈膝，双脚收向臀部",
        "手撑地抬臀，背部离地",
        "蹲坐姿势，双手前撑",
        "单膝立起，重心上抬",
        "站定护架",
    ], [GROUND] * 5, [0, 1, 2, 3]),
    "wake": ([
        "倒地侧翻，手撑地",
        "收膝跪起",
        "单膝立起",
        "起身半蹲",
        "站定护架",
    ], [GROUND] * 5, [0, 1, 2, 3]),
    "stun": ([
        "站立摇晃，头部低垂，双臂垂下",
        "身体向一侧倾，脚步踉跄",
        "扶住额头，膝盖发软",
        "另一侧摇晃，双臂摆动",
        "低头站稳，肩甲下沉",
        "抬头回护架",
    ], [GROUND] * 6, [0, 1, 2, 3, 4]),
    "guardbreak": ([
        "护架被重击压开，双臂向两侧震散",
        "门户大开，上身后仰，脚步后退",
        "身体前倾试图回护，双臂无力",
        "护架散开，单膝下沉",
    ], [GROUND] * 4, [0, 1, 2, 3]),
    "blockstun": ([
        "护架吃住冲击，双臂后压，身体后滑",
        "护架回稳，双拳仍护头胸",
    ], [GROUND] * 2, [0]),
    "thrown_air": ([
        "被抛到空中，身体横转",
        "空中翻滚，四肢张开",
        "下坠翻身，双腿朝下",
        "落地砸实，身体摊开",
    ], [AIR, AIR, AIR, GROUND], [0, 1, 2, 3]),
    "thrown_forward": ([
        "被向前抛出，身体前倾离地",
        "空中前翻，双腿上摆",
        "落地砸实，肩背先着地",
    ], [AIR, AIR, GROUND], [0, 1, 2]),
    "thrown_back": ([
        "被向后抛出，身体后仰离地",
        "空中后翻，四肢张开",
        "下坠中收身",
        "落地砸实，身体摊开",
    ], [AIR, AIR, AIR, GROUND], [0, 1, 2, 3]),
    "thrown_dash": ([
        "被斜向抛出，身体横转离地",
        "空中翻滚，双腿甩起",
        "下坠伸腿",
        "落地侧滚，撑地",
    ], [AIR, AIR, AIR, GROUND], [0, 1, 2, 3]),
    "grabbed": ([
        "被抓住肩胸，身体前倾，双臂抬起挣扎",
        "被提起，脚尖离地，双腿蹬动",
        "被压制，身体弓起，双手抓向对方手腕",
    ], [GROUND, AIR, GROUND], [0, 1, 2]),
    "throw_tech": ([
        "扣住对方手臂，屈膝沉腰",
        "转身背起，髋部顶住，双臂拉紧",
        "过顶翻摔，身体前倾，双臂下压",
        "收势站定，双拳回护架",
    ], [GROUND] * 4, [0, 1, 2]),
    "intro": ([
        "侧身站定，双拳自然下垂，抬头",
        "抬起右拳到胸前，肩甲展开",
        "摆出格斗护架，视线向前",
    ], [GROUND] * 3, []),
    "victory": ([
        "站定抬头，右拳举向天空",
        "双拳收胸，身体挺直",
    ], [GROUND] * 2, []),
    "win": ([
        "右拳高举，身体挺直",
        "收回护架，抬头",
    ], [GROUND] * 2, []),
    "defeat": ([
        "单膝跪地，一手撑地，头低下",
        "身体前倾伏地，双臂垂下",
    ], [GROUND] * 2, [0, 1]),
    "ko": ([
        "仰面倒地，四肢摊开",
        "躺地不动，头偏向一侧",
    ], [GROUND] * 2, [0, 1]),
    "timeout": ([
        "站定喘气，双肩下沉，双拳低垂",
        "抬头看向前方，护架略抬",
    ], [GROUND] * 2, [0]),
    "turn": ([
        "站架重心移到前脚，后脚脚跟离地",
        "髋部转动，后脚向外撇，上身随转",
        "转回侧向站架，双拳护胸",
    ], [GROUND] * 3, []),
    "charge_start": ([
        "站架双拳收在腰侧，膝盖下沉",
        "身体略前倾，双拳握紧，肩甲收紧",
        "蓄势站定，双拳抬到胸前",
    ], [GROUND] * 3, []),
    "charge": ([
        "护架站立，双拳微颤，重心下沉",
        "身体略向后坐，双拳握紧",
        "肩线起伏，双拳再收紧",
        "蓄势保持，膝盖微屈",
    ], [GROUND] * 4, []),
    "charge_stop": ([
        "身体回正，双拳松开半寸",
        "回到护架站定",
    ], [GROUND] * 2, []),
}

MOVES: dict[str, tuple[list[str], list[int], list[str]]] = {
    "light1": (["前手收肘蓄力", "前手短直拳向前击出", "收拳回护架"], [GROUND] * 3, []),
    "light2": (["后手收肘转髋", "后手直拳向前击出", "收拳回护架"], [GROUND] * 3, []),
    "light3": (["屈膝下沉，前手收拳", "进身半步，后手向上勾", "上勾拳到顶点", "收拳回护架"], [GROUND] * 4, []),
    "heavy": (["后脚蹬地，后手收拳", "踏步进身，肩部前送", "重拳击出到顶点", "收拳回护架"], [GROUND] * 4, []),
    "launcher": (["屈膝下沉", "后手垂到腰侧", "蹬地起身上冲", "上勾拳从下向上击出", "拳到头顶，身体伸展", "顶点略停", "收拳落地护架"], [GROUND] * 7, []),
    "spin_heavy": (["前脚内扣，上身预转", "髋部转动", "回身抬肘", "横扫肘向前", "肘击到顶点", "身体继续转过", "收势回护架"], [GROUND] * 7, []),
    "crush": (["双拳举过头顶", "身体后仰蓄力", "双膝屈沉", "双拳向下砸", "砸到胸高", "砸到腰高", "双拳到最低点，上身前折", "身体回起", "收拳护架"], [GROUND] * 9, []),
    "tackle": (["屈膝沉肩", "后脚蹬地", "沉肩前冲", "肩甲撞出", "撞击顶点", "身体前压", "收势减速", "回护架"], [GROUND] * 8, []),
    "sweep": (["屈膝下沉", "前脚向外撇", "身体下蹲转髋", "后腿贴地扫出", "扫到最远", "收腿", "起身护架"], [GROUND] * 7, []),
    "slide": (["屈膝前倾", "前脚滑出", "身体下沉", "低姿滑铲", "前腿伸直贴地", "滑到最远", "收腿起身", "站定护架"], [GROUND] * 8, []),
    "crouch_light": (["蹲姿收拳", "蹲姿下段直拳", "拳到顶点", "收拳回蹲姿护架"], [GROUND] * 4, []),
    "crouch_light2": (["蹲姿收后手", "蹲姿第二段直拳", "拳到顶点，肩部前送", "收拳回蹲姿护架"], [GROUND] * 4, []),
    "vertical_light": (["屈膝起跳", "腾空出拳", "拳头到顶点", "落地屈膝"], [GROUND, AIR, AIR, GROUND], []),
    "vertical_heavy": (["屈膝起跳", "腾空举双拳", "下砸拳到顶点", "双拳下砸", "落地屈膝"], [GROUND, AIR, AIR, AIR, GROUND], []),
    "diagonal_light": (["屈膝斜跳", "腾空提膝", "膝盖向上顶", "落地屈膝"], [GROUND, AIR, AIR, GROUND], []),
    "diagonal_heavy": (["屈膝斜跳", "腾空展腿", "飞踢腿伸出", "踢到顶点", "落地屈膝"], [GROUND, AIR, AIR, AIR, GROUND], []),
    "air_crush": (["空中收双拳", "举拳过头", "下砸拳", "砸到胸前", "砸到腰下", "落地屈膝"], [AIR, AIR, AIR, AIR, AIR, GROUND], []),
    "dive": (["空中团身", "身体前倾", "腿向下伸", "脚跟向下踢", "落地屈膝"], [AIR, AIR, AIR, AIR, GROUND], []),
    "chase_light1": (["前冲收拳", "前刺拳", "拳到顶点", "收拳"], [GROUND] * 4, []),
    "chase_light2": (["前冲收肘", "横肘向前", "肘到顶点", "收肘"], [GROUND] * 4, []),
    "chase_end": (["前冲举双掌", "双掌高举", "向下砸", "双掌到胸前", "双掌砸到地面", "收势起身"], [GROUND] * 6, []),
    "dash_light": (["冲刺前倾", "前脚跨出", "直拳击出", "拳到顶点", "制动收拳"], [GROUND] * 5, []),
    "dash_heavy": (["冲刺前倾", "后脚蹬地", "腾空飞踢", "腿踢到顶点", "下落收腿", "落地屈膝"], [GROUND, GROUND, AIR, AIR, AIR, GROUND], []),
    "back_counter": (["后跃收身", "后脚落地", "扭髋回转", "反击拳击出", "拳到顶点", "收拳护架"], [AIR, GROUND, GROUND, GROUND, GROUND, GROUND], []),
    "dodge_counter": (["侧闪屈膝", "身体回中", "反击肘击出", "肘到顶点", "收势护架"], [GROUND] * 5, []),
    "wake_low": (["单膝撑地", "起身半步", "起身下段拳", "拳到顶点", "站起护架"], [GROUND] * 5, []),
    "wake_mid": (["坐起撑地", "单膝立起", "起身半步", "起身中段拳", "拳到顶点", "站定护架"], [GROUND] * 6, []),
    "guard_counter": (["护架吃住冲击", "身体后压", "蹬地反击", "反击拳击出", "拳到顶点", "收拳护架"], [GROUND] * 6, []),
    "burst": (["屈膝下沉，双拳收腰", "双拳握紧，身体前倾", "双拳向两侧震开，身体伸展", "爆气顶点，肩甲展开", "收势回护架"], [GROUND] * 5, []),
    "pulse": (["站架收手", "后手收腰", "前手向前推出", "手掌伸到最远", "收手", "回护架"], [GROUND] * 6, []),
    "low_pulse": (["屈膝下沉", "前手收腰", "低姿手掌向前推出", "手伸到最远", "收手回护架"], [GROUND] * 5, []),
    "air_pulse": (["空中收手", "空中转体", "手掌斜下推出", "手伸到最远", "空中收手"], [AIR] * 5, []),
    "ranged_forward": (["站架收手", "后手收腰", "前脚跨出", "上身转向前", "前掌推出", "掌到最远", "收掌", "回护架"], [GROUND] * 8, []),
    "special": (["站架收拳", "双拳收腰", "屈膝下沉", "身体侧转", "右前臂抬起", "前臂横到胸前", "手掌贴住前臂", "蓄势", "上身向前送", "前臂向前伸出", "手臂伸直", "发射姿态", "身体后坐", "手臂回收", "收手", "回护架"], [GROUND] * 16, []),
    "special2": (["站架", "双拳收腰", "屈膝", "身体侧转", "右手抬到额前", "指尖贴额灯", "蓄势", "上身后仰", "身体前送", "手向前挥出", "手臂横挥", "挥到最远", "身体回正", "手收回", "收势", "护架"], [GROUND] * 16, []),
    "special3": (["站架", "双手抬到头侧", "摸到头镖", "双镖取下", "双手分开", "身体侧转", "双镖举到胸前", "蓄势", "双镖向前送出", "手臂伸直", "掷出姿态", "身体前倾", "手臂回收", "双手收回胸前", "收势", "护架"], [GROUND] * 16, []),
    "air_special": (["空中收手", "空中转体", "右前臂抬起", "前臂横到胸前", "手掌贴臂蓄势", "手臂向前伸出", "手臂伸直发射姿态", "空中收手"], [AIR] * 8, []),
    "throw_forward": (["扣住对方手臂，屈膝沉腰", "转身背起，髋部顶住", "过肩摔下压，身体前倾"], [GROUND] * 3, []),
    "throw_back": (["抱住对方腰，屈膝", "回身背起，臀部顶住", "向后摔下压，身体后坐"], [GROUND] * 3, []),
    "air_throw": (["空中扣住对方肩臂", "空中收膝", "空中翻身", "把对方甩出", "空中收势", "落地屈膝"], [AIR, AIR, AIR, AIR, AIR, GROUND], []),
    "dash_throw": (["冲步前倾", "双手前抱", "屈膝抱紧", "抱起对方", "转身摔出", "收势站定"], [GROUND] * 6, []),
    "motion_214": (["前脚踏出", "身体前倾", "双臂前推", "双掌到最远", "收势护架"], [GROUND] * 5, []),
    "motion_236": (["垫步前冲", "双掌收在胸前", "双掌前推", "收势护架"], [GROUND] * 4, []),
    "motion_623": (["屈膝下沉", "膝向上顶", "膝到顶点", "落地护架"], [GROUND, AIR, AIR, GROUND], []),
    "motion_22": (["双臂收到胸前", "双臂交叠", "身体下沉", "双臂向前推出", "交叠壁到最远", "身体后坐反震", "双臂收回", "护架"], [GROUND] * 8, []),
    "motion_41236": (["扣住对方手臂", "屈膝转身", "背起对方", "对方过顶", "向前摔下", "身体前压", "收势", "站定护架"], [GROUND] * 8, []),
    "taunt": (["站定抬右手", "右手向自己招动", "收回护架"], [GROUND] * 3, []),
}


def clip_frames(n: int) -> list[str]:
    return [f"{i:02d}" for i in range(n)]


def write_clip(clip: str, beats: list[str], foot_rows: list[int],
               exceptions: list[int], group: str, start: int = 0) -> None:
    if len(beats) != len(foot_rows):
        raise SystemExit(f"{clip}: 节拍 {len(beats)} 与脚底行 {len(foot_rows)} 数量不一致")
    idxs = clip_frames(len(beats))
    frame_dir = STAGE / clip / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    cell = AIR_SPECIAL_CELL if clip == "air_special" else CELL
    frames = []
    requests = []
    for index in range(start, len(beats)):
        idx, beat, row = idxs[index], beats[index], foot_rows[index]
        raw = f"art/fighters/{FIGHTER}/stage1/{clip}/frames/{clip}-{idx}-raw.png"
        prompt = f"第 {index + 1}/{len(beats)} 帧：{beat}。{HEAD}{BODY}{TAIL}"
        frames.append({"idx": idx, "source": raw, "pose": "air" if row == AIR else "ground",
                       "foot_row": row, "beat": beat})
        requests.append({"idx": idx, "prompt": prompt, "path": raw,
                         "requested_size": "1024x1024",
                         "reference": f"art/fighters/{FIGHTER}/stage1/cells/idle-00-cell-x4.png"})
    plan = {
        "clip": clip,
        "group": group,
        "cell": cell,
        "root": [128, 248],
        "foot_row": GROUND,
        "scale": ACTION_SCALE,
        "scale_rule": "全形态动作帧共用固定源比例 0.2027897；不逐帧重标定",
        "frames": frames,
        "pose_exceptions": [idxs[i] for i in exceptions],
        "adjacent_exceptions": [],
    }
    (PLANS / f"{clip}.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (REQUESTS / f"{clip}.json").write_text(
        json.dumps({"clip": clip, "group": group, "frames": requests},
                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", choices=["states", "moves", "all"], default="all")
    ap.add_argument("--clip", default="")
    args = ap.parse_args()
    PLANS.mkdir(parents=True, exist_ok=True)
    REQUESTS.mkdir(parents=True, exist_ok=True)
    if args.group in ("states", "all"):
        for clip, (beats, rows, exc) in STATES.items():
            if clip == "form_switch":
                continue
            if args.clip and clip != args.clip:
                continue
            write_clip(clip, beats, rows, exc, "state",
                       start=1 if clip == "idle" else 0)
    if args.group in ("moves", "all"):
        for clip, (beats, rows, exc) in MOVES.items():
            if args.clip and clip != args.clip:
                continue
            write_clip(clip, beats, rows, exc, "move")
    count = sum(1 for _ in PLANS.glob("*.json"))
    print(f"plans {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

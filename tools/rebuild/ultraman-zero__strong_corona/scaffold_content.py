"""强壮日冕赛罗内容骨架：复制基础赛罗 47 招与状态帧，改写形态表述与特效 id。

只写本形态 content 目录与 tools/rebuild/ultraman-zero__strong_corona/。
- 招式帧数、起止帧、伤害、能量、硬直与命中时序原样保留；只改
  display_name / data_source / production_note 的形态表述。
- 基础赛罗专属 `zero_fx_*` 全部改为 `pending_corona_*`；共享通用
  `impact_light/impact_guard/impact_heavy` 与共享 `pulse` 弹体保留。
- 状态帧逐 tick 数据原样继承（用于模拟受击框与节奏），另加 6 帧
  `form_switch`（人物动作帧待生成，hurtbox 暂继承 idle，登记为占位）。
- 不写 assets/、不改共享 phase3/policy/roster/docs。

用法：.venv/bin/python tools/rebuild/ultraman-zero__strong_corona/scaffold_content.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "content/fighters/ultraman-zero"
OUT = ROOT / "content/fighters/ultraman-zero__strong_corona"
TOOLS = ROOT / "tools/rebuild/ultraman-zero__strong_corona"
FORM_ID = "ultraman-zero__strong_corona"
FORM_NAME = "强壮日冕赛罗"
PREFIX = "强壮日冕·"
FX_RE = re.compile(r"zero_fx_[a-z0-9_]+")
PENDING_RE = re.compile(r"pending_corona_[a-z0-9_]+")
FORM_SWITCH_FRAMES = 6


def rename_fx(value):
    if isinstance(value, str):
        return FX_RE.sub(lambda m: "pending_corona_" + m.group(0)[len("zero_fx_"):], value)
    if isinstance(value, list):
        return [rename_fx(v) for v in value]
    if isinstance(value, dict):
        return {rename_fx(k): rename_fx(v) for k, v in value.items()}
    return value


def collect_fx(value, out):
    if isinstance(value, str):
        out.update(FX_RE.findall(value))
    elif isinstance(value, list):
        for v in value:
            collect_fx(v, out)
    elif isinstance(value, dict):
        for k, v in value.items():
            collect_fx(k, out)
            collect_fx(v, out)


def form_display_name(name: str) -> str:
    if name.startswith(PREFIX):
        return name
    return PREFIX + name


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "moves").mkdir(parents=True, exist_ok=True)
    TOOLS.mkdir(parents=True, exist_ok=True)

    move_ids = json.loads((BASE / "move_manifest.json").read_text(encoding="utf-8"))
    all_fx = set()
    for move_id in move_ids:
        src = json.loads((BASE / "moves" / f"{move_id}.json").read_text(encoding="utf-8"))
        collect_fx(src, all_fx)
        move = rename_fx(src)
        move["display_name"] = form_display_name(str(move.get("display_name", move_id)))
        original_source = str(src.get("data_source", "")).strip()
        source_note = (
            f"{FORM_NAME}形态沿用基础赛罗同招的帧数、起止帧、伤害、能量、"
            "硬直与命中时序，不扩判定；人物动作帧待按本形态待机锚重生成。"
        )
        if original_source:
            source_note += f" 原始来源：{original_source}"
        move["data_source"] = source_note
        pending = sorted(set(PENDING_RE.findall(json.dumps(move, ensure_ascii=False))))
        move["production_note"] = (
            f"未安装：{FORM_NAME}人物动作帧尚未生成；"
            + ("专属特效 " + "、".join(pending) + " 均为 pending，未登记前不显示。"
               if pending else "本招无专属特效。")
        )
        (OUT / "moves" / f"{move_id}.json").write_text(
            json.dumps(move, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # 状态帧：继承基础赛罗的逐 tick 时长与受击框；新增 form_switch 占位。
    states = json.loads((BASE / "state_frames.json").read_text(encoding="utf-8"))
    probe = states["idle"][0]
    states["form_switch"] = [
        {
            "sprite": i,
            "dx": 0,
            "dy": 0,
            "hitboxes": [],
            "hurtboxes": json.loads(json.dumps(probe["hurtboxes"])),
            "cancel": [],
            "events": [],
            "impact_effect": "impact_light",
            "block_effect": "impact_guard",
        }
        for i in range(FORM_SWITCH_FRAMES)
    ]
    (OUT / "state_frames.json").write_text(
        json.dumps(states, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    commands = json.loads((BASE / "command_table.json").read_text(encoding="utf-8"))
    for row in commands:
        row["display_name"] = form_display_name(str(row.get("display_name", row.get("move", ""))))
    (OUT / "command_table.json").write_text(
        json.dumps(commands, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    (OUT / "move_manifest.json").write_text(
        json.dumps(move_ids, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    definition = {
        "id": FORM_ID,
        "display_name": FORM_NAME,
        "template": "humanoid",
        "production_status": "stage2_content_scaffolded_frames_incomplete",
        "playable": True,
        "select_visible": False,
        "selection_visible": False,
        "max_health": 1000,
        "walk_speed": 2,
        "jump_speed": 16,
        "numeric_status": "沿用基础赛罗占位数值；动作帧未齐，未实机校准。",
        "presentation": {
            "model": f"res://assets/fighters/{FORM_ID}/catalogue/model-native.png",
            "manifest": f"res://assets/fighters/{FORM_ID}/animations/manifest.json",
            "native": True,
            "cell": 256,
            "anchor": [128, 248],
            "target_height": 188,
            "height_basis": "冠顶/头冠顶至鞋底；本形态身份锚实测站高188，脚底247",
            "anchor_y": 248,
        },
        "forms": ["default"],
        "identity_notes": (
            "强壮日冕赛罗：红银金配色，完整金色头冠向后掠，黄眼、绿额灯、"
            "蓝芯胸计时器、红拳套；无披风。身份锚为待机像素整帧，"
            "256 格、根点 [128,248]、站高 188。"
        ),
        "reference_file": f"content/fighters/{FORM_ID}/catalogue_profile.json",
        "production_stage": 7,
        "model_review_pending": False,
        "model_candidate": f"art/fighters/{FORM_ID}/stage1/idle/frames/identity-idle-pixel.png",
        "stage2_status": "stage2_content_scaffolded_frames_incomplete",
        "pilot_playable": False,
        "pilot_manual_ready": False,
        "walks_installed": False,
        "unsupported_moves": [],
        "pilot_lock_reason": "全部状态片段与47招人物动作帧尚未生成安装；未开放选人。",
        "selection_authorization": (
            "root_delegated_by_user：仅内容骨架与身份锚；动作帧未齐，"
            "select_visible/selection_visible 暂为 false，待帧安装后由主会话接线开放。"
        ),
        "state_frames_note": (
            "逐 tick 受击框与节奏继承基础赛罗同形状态；form_switch 六帧 hurtbox "
            "暂继承 idle，登记为占位，待本形态整帧落地后重算。"
        ),
    }
    (OUT / "definition.json").write_text(
        json.dumps(definition, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    profile = {
        "name": "赛罗奥特曼 · 强壮日冕",
        "title": "红银金强攻形态",
        "text": (
            "红色为主、金色头冠与胸腹纹样的强壮日冕外形；完整双头饰、"
            "黄眼、绿额灯、蓝芯计时器与红拳套清楚可见。\n\n"
            "范围：仅当前强壮日冕形态；动作帧制作中。身高：未知。体重：未知。"
        ),
        "source_label": "本人既有官方商品与图鉴来源；简体外观整理，未证实设定记未知",
        "source_url": "https://tamashiiweb.com/item/13046",
        "license": "按原来源条款",
        "model": f"res://assets/fighters/{FORM_ID}/catalogue/model-native.png",
        "audio_timer": {"enabled": True, "sound": "timer"},
        "profile_source": "catalogue_profile.json；称号/简介按本形态外观整理，不新增设定。",
    }
    (OUT / "profile.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 特效提案（只写本工具目录，不登记共享 phase3/policy）。
    entries = []
    for fx in sorted(all_fx):
        pending = "pending_corona_" + fx[len("zero_fx_"):]
        kind = ("beam" if pending.endswith("_beam") else
                "hit" if pending.endswith("_hit") else
                "flight" if ("flight" in pending or "trail" in pending) else
                "catch" if pending.endswith("_catch") else "other")
        entries.append({
            "id": pending,
            "status": "pending",
            "kind": kind,
            "source_zero_effect": fx,
            "proposal_only": True,
            "atlas": None,
            "note": "强壮日冕专属特效待自绘 PixelFX；未登记前运行时静默跳过。",
        })
    q_charge = []
    for suffix, frames, loop in [("start", 9, False), ("charge", 24, True), ("stop", 9, False)]:
        fid = f"pending_corona_q_charge_{suffix}"
        q_charge.append({
            "id": fid, "status": "pending", "frames": frames, "loop": loop,
            "anchor": [0, 0], "behind_fighter": True, "proposal_only": True, "atlas": None,
        })
        entries.append({
            "id": fid, "status": "pending", "kind": "charge",
            "source_zero_effect": "zero_fx_q_charge_" + suffix,
            "proposal_only": True, "atlas": None,
            "note": "只在真实 Q 起势/保持/收势出现；待自绘 PixelFX。",
        })
    proposal = {
        "fighter": FORM_ID,
        "target": "assets/effects/ultraman-zero__strong_corona/",
        "status": "proposal_only",
        "registered": False,
        "shared_reused": {
            "impact_light": "共享通用命中火花，已登记，保留",
            "impact_guard": "共享通用格挡火花，已登记，保留",
            "impact_heavy": "共享通用重击火花，已登记，保留",
            "pulse": "共享通用弹体，已登记，保留；投射类人物帧不画能量球",
        },
        "entries": entries,
        "q_charge": q_charge,
        "note": "主会话合并前不得写入 content/presentation/phase3_projectiles.json 或 charge_overlay_policy.json。",
    }
    (TOOLS / "fx-proposal.json").write_text(
        json.dumps(proposal, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (TOOLS / "phase3_entries.json").write_text(
        json.dumps({"fighter": FORM_ID, "status": "proposal_only", "entries": entries},
                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (TOOLS / "charge_policy.json").write_text(
        json.dumps({
            "fighter": FORM_ID,
            "status": "proposal_only",
            "charge_only_effects": [x["id"] for x in q_charge],
            "placements": {
                "charge_start": {"effect": q_charge[0]["id"], "anchor": [0, 0],
                                 "color": [1, 1, 1, 1], "behind_fighter": True,
                                 "frames": 9, "loop": False},
                "charge": {"effect": q_charge[1]["id"], "anchor": [0, 0],
                           "color": [1, 1, 1, 1], "behind_fighter": True,
                           "frames": 24, "loop": True},
                "charge_stop": {"effect": q_charge[2]["id"], "anchor": [0, 0],
                                "color": [1, 1, 1, 1], "behind_fighter": True,
                                "frames": 9, "loop": False},
            },
            "note": "主会话合并进 charge_overlay_policy.json 前，本形态 Q 蓄气不可见。",
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(json.dumps({
        "moves": len(move_ids),
        "state_keys": len(states),
        "form_switch_frames": FORM_SWITCH_FRAMES,
        "pending_fx": len(entries),
        "content_dir": str(OUT.relative_to(ROOT)),
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Validate on-screen references before paid character-motion generation."""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import hashlib
import json; json = _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath

ROOT = _LayoutProjectPath(_layout_root)
EVIDENCE = ROOT / "art/shared/references/motion-evidence.json"


def verified_record(record, character, state, root=ROOT, expected_form=None):
    scope = record.get("motion_scope")
    scoped = scope in {"sustained_hold", "guard_entry"}
    if scope not in {None, "sustained_hold", "guard_entry"}:
        raise ValueError("Unknown motion evidence scope")
    gameplay = record.get("kind") == "gameplay_clip"
    if record.get("kind") not in {"episode_clip", "gameplay_clip"} or record.get("reviewed") is not True:
        raise ValueError("Motion requires a reviewed episode or gameplay clip; a name or publicity still is insufficient")
    if gameplay and (state not in {"walk", "dash", "sidestep", "backstep", "jump", "land", "crouch"}
                     or record.get("platform") != "PS2" or not record.get("adaptation_limits")):
        raise ValueError("PS2 gameplay evidence is limited to reviewed locomotion with explicit adaptation limits")
    if record.get("character_id") != character or record.get("state") != state:
        raise ValueError("Motion evidence belongs to a different character or state")
    if expected_form is not None and record.get("form") != expected_form:
        raise ValueError("Motion evidence belongs to a different form")
    source_fields = ("work", "platform", "form", "source_url", "reviewer") if gameplay else ("work", "episode", "form", "source_url", "reviewer")
    if not all(record.get(k) for k in source_fields):
        raise ValueError("Motion evidence needs work, source context, form, source URL and reviewer")
    start, end = record.get("start_ms"), record.get("end_ms")
    if type(start) is not int or type(end) is not int or not 0 <= start < end:
        raise ValueError("Motion evidence needs an exact ordered time range")
    poses = record.get("key_poses", [])
    if scoped:
        from media.references.hold_evidence import ORDERS
        required = set(ORDERS[scope])
    else:
        required = {"start", "middle", "end"} if gameplay else ({"rest", "extreme", "return"} if state == "idle" else {"start", "contact", "recovery"})
    if not required <= {p.get("phase") for p in poses}:
        raise ValueError("Motion evidence is missing required key poses")
    times = [p.get("time_ms") for p in poses]
    if any(type(t) is not int or not start <= t <= end for t in times) or times != sorted(times):
        raise ValueError("Key poses must be ordered within the exact source interval")
    for pose in poses:
        if not pose.get("observation"):
            raise ValueError("Key poses need visible posture observations")
        file = (root / pose.get("file", "")).resolve()
        if not file.is_relative_to(root.resolve()) or not file.is_file():
            raise ValueError("Key-pose evidence must be a local reference file inside the project")
        if hashlib.sha256(file.read_bytes()).hexdigest() != pose.get("sha256"):
            raise ValueError("Key-pose reference changed after review")
    if scoped:
        from media.references.hold_evidence import verify
        verify(record,state,root)
    if gameplay:
        capture_path = (root / record.get("capture_manifest", "")).resolve()
        if (not capture_path.is_relative_to(root.resolve()) or not capture_path.is_file()
                or hashlib.sha256(capture_path.read_bytes()).hexdigest() != record.get("capture_manifest_sha256")):
            raise ValueError("Gameplay evidence requires its unchanged frame capture")
        capture = json.loads(capture_path.read_text("utf-8"))
        if (capture.get("ffprobe_actual_decode_pts_equal") is not True
                or capture.get("all_source_frames_in_range") is not True
                or capture.get("original_frame_dimensions") is not True):
            raise ValueError("Gameplay motion requires actual consecutive original-size frames")
        for pose in poses:
            if not any(row["file"] == pose["file"] and row["sha256"] == pose["sha256"]
                       and round(float(row["source_pts_seconds"]) * 1000) == pose["time_ms"]
                       for row in capture.get("frames", [])):
                raise ValueError("Gameplay key pose is outside its verified source capture")
    return record


def require_row_evidence(request, state, root=ROOT):
    if request.get("subject") == "effect":
        return None  # Generic effects make no character-motion fidelity claim.
    if request.get("purpose") == "static_pixel_portrait":
        if request["states"][state].get("frames") != 1 or request["states"][state].get("loop") is not False:
            raise ValueError("Static portrait exemption cannot generate an animation")
        return None
    character = request.get("source_character_id")
    form = request.get("source_form")
    evidence_id = request.get("states", {}).get(state, {}).get("motion_evidence")
    if not character or not form or not evidence_id:
        raise ValueError("剧中动作证据缺失：先登记角色、原剧或PS2步法片段、时间段与关键姿势，再生成动作")
    data = json.loads((root / "art/shared/references/motion-evidence.json").read_text(encoding="utf-8"))
    record = next((r for r in data.get("records", []) if r.get("id") == evidence_id), None)
    if record is None:
        raise ValueError("Unknown motion evidence ID")
    return verified_record(record, character, state, root, expected_form=form)

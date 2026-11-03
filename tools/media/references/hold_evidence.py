"""持续防御只授权可见持势，不替代完整攻击所需的起手、接触、收势证据。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from ..materials.character_layers import checked
import json; json = _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath

ROOT = _LayoutProjectPath(_layout_root)
ORDER = ("hold_start", "hold_mid_1", "hold_mid_2", "hold_end")
PHASES = set(ORDER)
ENTRY_ORDER = ("entry_start", "entry_mid_1", "entry_mid_2", "entry_end")
ORDERS = {"sustained_hold": ORDER, "guard_entry": ENTRY_ORDER}


def verify(record, state, root=ROOT):
    scope = record.get("motion_scope")
    expected_state = {"sustained_hold": "guard", "guard_entry": "guard_enter"}.get(scope)
    excluded = {"entry", "exit", "release", "reflection"} if scope == "sustained_hold" else {"exit", "release", "reflection"}
    if (expected_state is None or state != expected_state or record.get("kind") != "episode_clip"
            or record.get("visible_body_scope") != "upper_body"
            or not record.get("coverage") or not record.get("adaptation_limits")
            or set(record.get("excluded_phases", [])) != excluded):
        raise ValueError("片段证据仅授权已声明的上身防御阶段，必须排除未覆盖的收势、发射和反射")
    order = ORDERS[scope]
    path = checked(root, record.get("capture_manifest", ""), record.get("capture_manifest_sha256"))
    capture = json.loads(path.read_text("utf-8"))
    if (capture.get("sampling_stride_frames") != 1
            or any(capture.get(key) is not True for key in ["all_source_frames_in_range",
                   "ffprobe_actual_decode_pts_equal", "original_frame_dimensions"])):
        raise ValueError("持势需要原尺寸、真实PTS且无跳帧的连续捕获")
    checked(root, capture.get("source_file", ""), capture.get("source_sha256"))
    start, end = record["start_ms"], record["end_ms"]
    rows = [row for row in capture.get("frames", []) if start <= round(float(row["source_pts_seconds"])*1000) <= end]
    if len(rows) < 4 or [row["index"] for row in rows] != list(range(rows[0]["index"], rows[-1]["index"]+1)):
        raise ValueError("持势范围必须包含至少四张连续原帧")
    times = [round(float(row["source_pts_seconds"])*1000) for row in rows]
    if times[0] != start or times[-1] != end or any(b <= a or b-a > 50 for a,b in zip(times,times[1:])):
        raise ValueError("持势时间必须精确绑定连续捕获边界，不能跨剪辑拼接")
    for row in rows:
        checked(root, row["file"], row["sha256"])
    poses = record["key_poses"]
    if (tuple(pose["phase"] for pose in poses) != order
            or poses[0]["time_ms"] != start or poses[-1]["time_ms"] != end
            or any(b["time_ms"] <= a["time_ms"] for a,b in zip(poses,poses[1:]))):
        raise ValueError("持势需要四个按顺序核对的阶段")
    for pose in poses:
        if not any(row["file"] == pose["file"] and row["sha256"] == pose["sha256"]
                   and round(float(row["source_pts_seconds"])*1000) == pose["time_ms"] for row in rows):
            raise ValueError("持势关键帧必须来自核对范围，不能用推掌发射帧替代收势")
    return record

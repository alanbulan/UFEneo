"""有来源的音频截取；先在浮点域衰减，再量化，避免新增削波。"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson

import math


def extraction_gain(spec):
    gain = spec.get("extraction_gain_db", 0)
    if type(gain) not in {int, float} or not math.isfinite(gain) or not -60 <= gain <= 0:
        raise ValueError("来源截取增益只能是-60～0dB的有限衰减")
    return gain


def extract(spec_path, output):
    import audio.pipeline as pipeline

    spec = pipeline.read(spec_path)
    source = pipeline.source_reference(spec)
    gain = extraction_gain(spec)
    if output.exists() or output.with_suffix(".json").exists() or output.suffix.lower() != ".wav":
        raise ValueError("截取必须输出到新版本 WAV")
    output.parent.mkdir(parents=True, exist_ok=True)
    length = spec["end_ms"] - spec["start_ms"]
    channels = 1 if spec["asset_kind"] == "voice" else 2
    filters = []
    if gain:
        layout = "mono" if channels == 1 else "stereo"
        filters = ["-af", f"aformat=sample_fmts=flt:sample_rates=48000:channel_layouts={layout},volume={gain:.9f}dB"]
    # Seek after input. Leave timing unchanged; gain occurs before integer PCM.
    pipeline.run_ffmpeg(["-i", str(source), "-ss", str(spec["start_ms"] / 1000), "-t", str(length / 1000),
        "-map", "0:a:0", "-vn", *filters, "-ar", "48000", "-ac", str(channels), "-c:a", "pcm_s16le", str(output)])
    measured = pipeline.probe(output)
    if abs(measured["duration_ms"] - length) > 25:
        raise ValueError("截取实际时长偏离来源；文件保留待检查，不能提交")
    record = {"kind": "ufe-audio-clip", "asset_kind": spec["asset_kind"],
        "reference": spec_path.resolve().relative_to(pipeline.ROOT).as_posix(), "reference_sha256": pipeline.sha(spec_path),
        "file_sha256": pipeline.sha(output), "language": spec.get("language"), "measurement": measured,
        "extraction_gain_db": gain, "runtime_approved": False}
    pipeline.write_new(output.with_suffix(".json"), record)
    return record

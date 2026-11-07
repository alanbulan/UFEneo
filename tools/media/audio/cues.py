"""从有来源的分离轨提取短事件；保留原时间，不以裁切代替听审。"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson

from pathlib import Path
Path = _LayoutProjectPath
import math

from media.audio.measure import sample_metrics


def cut(spec_path: Path, output: Path):
    import audio.pipeline as pipeline

    spec = pipeline.read(spec_path)
    if spec.get("kind") != "ufe-audio-cue-recipe" or not spec.get("name"):
        raise ValueError("短音频需要独立事件配方与中文名称")
    source = pipeline.project_file(spec["input_file"])
    metadata = source.with_suffix(".json")
    if (pipeline.sha(source) != spec.get("input_sha256")
            or pipeline.sha(metadata) != spec.get("input_metadata_sha256")):
        raise ValueError("输入音轨或元数据已改变，必须重新核对事件边界")
    info = pipeline.clip_record(source, "separate")
    if info["asset_kind"] not in {"voice", "effect"}:
        raise ValueError("此工具只切语音和技能效果；音乐另用编配流程")
    if info["asset_kind"] == "voice" and info["kind"] != "ufe-prepared-voice":
        raise ValueError("先将分离人声整理为峰值安全的单声道，再切事件")
    reference = pipeline.read(pipeline.project_file(info["reference"]))
    duration = pipeline.probe(source)["duration_ms"]
    if abs(duration - (reference["end_ms"] - reference["start_ms"])) > 25:
        raise ValueError("音轨与原上下文时长不同，不能推算原剧时间码")
    start, end = spec.get("start_ms"), spec.get("end_ms")
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= duration:
        raise ValueError("事件边界必须在实际音轨内")
    if end - start > 15000:
        raise ValueError("单事件最多15秒")
    gain = spec.get("gain_db", 0)
    if type(gain) not in {int, float} or not math.isfinite(gain) or not -60 <= gain <= 0:
        raise ValueError("事件只允许有限的衰减，不自动放大噪声")
    fades = [spec.get("fade_in_ms", 3), spec.get("fade_out_ms", 8)]
    if any(type(value) is not int or not 0 <= value <= 20 for value in fades) or sum(fades) > end - start:
        raise ValueError("边缘淡入淡出各最多20ms，不能吃掉完整事件")
    output = output.resolve()
    if (not output.is_relative_to(pipeline.ROOT) or output.suffix.lower() != ".wav"
            or output.exists() or output.with_suffix(".json").exists()):
        raise ValueError("事件只能写入项目内的新版本WAV")
    # Decode first; sample coordinates refer to the declared 48kHz timeline.
    filters = ["aresample=48000", f"atrim=start_sample={start * 48}:end_sample={end * 48}",
               "asetpts=PTS-STARTPTS", f"volume={gain:.9f}dB"]
    if fades[0]:
        filters.append(f"afade=t=in:ss=0:ns={fades[0] * 48}")
    if fades[1]:
        filters.append(f"afade=t=out:ss={(end - start - fades[1]) * 48}:ns={fades[1] * 48}")
    output.parent.mkdir(parents=True, exist_ok=True)
    channels = "1" if info["asset_kind"] == "voice" else "2"
    pipeline.run_ffmpeg(["-i", str(source), "-map", "0:a:0", "-vn", "-af", ",".join(filters),
                         "-ar", "48000", "-ac", channels, "-c:a", "pcm_s16le", str(output)])
    measured = sample_metrics(output, 15000)
    if abs(measured["duration_ms"] - (end - start)) > 1:
        raise ValueError("事件长度改变；保留输出待排查，不可采用")
    record = {
        "kind": "ufe-audio-cue", "name": spec["name"], "asset_kind": info["asset_kind"],
        "language": info.get("language"), "character_id": reference.get("character_id"),
        "recipe": spec_path.resolve().relative_to(pipeline.ROOT).as_posix(),
        "recipe_sha256": pipeline.sha(spec_path),
        "input_file": spec["input_file"], "input_sha256": pipeline.sha(source),
        "input_metadata_sha256": pipeline.sha(metadata),
        "reference": info["reference"], "reference_sha256": info["reference_sha256"],
        "source_range_ms": [reference["start_ms"] + start, reference["start_ms"] + end],
        "relative_range_ms": [start, end], "gain_db": gain,
        "fade_in_ms": fades[0], "fade_out_ms": fades[1],
        "file_sha256": pipeline.sha(output), "metrics": measured,
        "numeric_checks_passed": not measured["silent"] and not measured["samples_at_or_above_full_scale"],
        "boundary_listening_reviewed": False, "speaker_listening_reviewed": False,
        "listening_reviewed": False, "runtime_approved": False,
        "note": "仅按画面时间窗口提取候选；音频起止、串音和音色尚需听审。原始API分轨完整保留。",
    }
    pipeline.write_new(output.with_suffix(".json"), record)
    return record

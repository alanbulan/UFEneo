"""日语语音、技能音效与配乐制作；Kits 只在离线工作台运行。"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson

import argparse
import array
import hashlib
import json; json = _LayoutJson
import math
from pathlib import Path
Path = _LayoutProjectPath
import re
import shutil
import subprocess
import sys

import audio.kits_client as kits

ROOT = _LayoutProjectPath(_layout_root)
JOBS = ROOT / ".tools/audio/jobs"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output:
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.write("\n")


def update(path, data):
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("x", encoding="utf-8") as output:
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.write("\n")
    temporary.replace(path)


def run_ffmpeg(arguments):
    exe = shutil.which("ffmpeg")
    if not exe:
        raise ValueError("需要开源 FFmpeg；当前 PATH 中未找到")
    result = subprocess.run([exe, "-hide_banner", "-nostdin", "-loglevel", "error", "-n", *arguments],
                            capture_output=True, timeout=120)
    if result.returncode:
        raise ValueError("FFmpeg 处理失败；未覆盖已有文件")


def probe(path):
    exe = shutil.which("ffprobe")
    if not exe or not path.is_file():
        raise ValueError("音频文件或 FFprobe 不存在")
    result = subprocess.run([exe, "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,sample_rate,channels", "-of", "json", str(path)],
        capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError("媒体无法解码")
    data = json.loads(result.stdout)
    stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    duration = float(data.get("format", {}).get("duration", 0))
    if not stream or not 0 < duration < 86400:
        raise ValueError("媒体缺少有效音轨或时长")
    return {"duration_ms": round(duration * 1000), "sample_rate": int(stream["sample_rate"]),
            "channels": stream["channels"]}


def voice_levels(path):
    if probe(path)["duration_ms"] > 15025:
        raise ValueError("人声幅值检查只接受15秒以内片段")
    result = subprocess.run([shutil.which("ffmpeg"), "-hide_banner", "-nostdin", "-loglevel", "error",
        "-i", str(path), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "48000", "-f", "f32le", "pipe:1"],
        capture_output=True, timeout=30)
    if result.returncode or not result.stdout:
        raise ValueError("人声幅值解码失败")
    values = array.array("f", result.stdout)
    if sys.byteorder != "little":
        values.byteswap()
    if any(not math.isfinite(v) for v in values):
        raise ValueError("人声存在无效采样值")
    peak = max(abs(v) for v in values)
    return {"peak_dbfs": 20 * math.log10(peak) if peak > 0 else None,
            "samples_at_or_above_full_scale": sum(abs(v) >= 1 for v in values)}


def project_file(value):
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("音频制作输入必须位于项目目录内")
    return path


def source_reference(spec):
    from media.audio.extraction import extraction_gain
    extraction_gain(spec)
    if spec.get("kind") != "ufe-audio-reference" or spec.get("reviewed") is not True:
        raise ValueError("先完成来源、日语音轨及字幕核对")
    if not all(spec.get(key) for key in ("id", "work", "episode", "source_url", "reviewer")):
        raise ValueError("音频来源缺少作品、集数、链接或复核者")
    kind = spec.get("asset_kind")
    if kind not in {"voice", "music", "effect"}:
        raise ValueError("音频用途必须是 voice、effect 或 music")
    source_kind = spec.get("source_kind")
    if source_kind is not None and source_kind not in {"original", "episode", "derivative"}:
        raise ValueError("音频来源类型只能是 original、episode 或 derivative")
    if source_kind == "episode" and not isinstance(spec.get("reprint"), bool):
        raise ValueError("原剧或官方音源转载必须注明 reprint 布尔值")
    if kind == "effect" and (not spec.get("effect_id") or not spec.get("visual_reference")):
        raise ValueError("技能音效必须注明技能与实际画面证据；不能冒充角色语音")
    if kind == "voice":
        if spec.get("language") != "ja":
            raise ValueError("角色语音只接受已核对的日语原声与日语转写")
        if spec.get("voice_event") == "nonverbal":
            # A grunt is not dialogue: do not invent Japanese words for ASR noise.
            evidence = project_file(spec.get("language_evidence", ""))
            language = read(evidence)
            if (sha(evidence) != spec.get("language_evidence_sha256") or language.get("language") != "ja"
                    or language.get("language_probability", 0) < 0.8
                    or not spec.get("event_id") or not spec.get("visual_reference")):
                raise ValueError("非语言叫声需要日语音轨证据和角色动作时间码")
        elif not re.search(r"[\u3040-\u30ff]", spec.get("transcript", "")):
            raise ValueError("角色语音只接受已核对的日语原声与日语转写")
        if not spec.get("character_id") or not spec.get("speaker"):
            raise ValueError("语音必须注明角色与发声者，不能混用旁白或其他人物")
    start, end = spec.get("start_ms"), spec.get("end_ms")
    limit = 180000 if kind == "music" else 15000
    if type(start) is not int or type(end) is not int or not 0 <= start < end or end - start > limit:
        raise ValueError("语音和音效单段最多15秒，音乐单段最多180秒，时间码必须有序")
    source = project_file(spec["source_file"])
    if sha(source) != spec.get("source_sha256"):
        raise ValueError("音频原始来源哈希变化，必须重新核对")
    if end > probe(source)["duration_ms"] + 20:
        raise ValueError("截取范围超过源媒体时长")
    return source


def extract(spec_path, output):
    from media.audio.extraction import extract as extract_source
    return extract_source(spec_path, output)


def clip_record(path, task_kind):
    info = read(path.with_suffix(".json"))
    if info.get("kind") not in {"ufe-audio-clip", "ufe-kits-result", "ufe-prepared-voice"} or sha(path) != info.get("file_sha256"):
        raise ValueError("只提交已绑定来源与哈希的音频片段")
    ref = project_file(info["reference"])
    if sha(ref) != info.get("reference_sha256"):
        raise ValueError("音频参考记录已改变")
    source_reference(read(ref))
    if task_kind == "voice" and (info.get("asset_kind") != "voice" or info.get("language") != "ja"):
        raise ValueError("声线转换只接受日语角色语音")
    if task_kind == "voice" and info["kind"] == "ufe-kits-result" and info.get("stem") not in {"vocal", "converted"}:
        raise ValueError("背景或乐器分轨不能冒充角色人声进行声线转换")
    if task_kind == "instrument":
        if info.get("asset_kind") != "music":
            raise ValueError("乐器转换只接受音乐，不能改变人物语音或技能音效的身份")
        if info["kind"] == "ufe-kits-result" and info.get("stem") == "vocal":
            raise ValueError("人声分轨不能冒充乐器")
        if info["kind"] == "ufe-kits-result" and info.get("stem") == "indexed":
            label = (info.get("provider_stem_label") or "").lower()
            if label not in {"bass", "drums", "guitar", "piano", "other", "backing"}:
                raise ValueError("先核对未知分轨的实际内容，再进行乐器转换")
    measured = probe(path)
    limit = 180000 if info["asset_kind"] == "music" else 15000
    if measured["duration_ms"] > limit + 25:
        raise ValueError("片段超过制作时长上限")
    return info


def prepare_voice(source, output):
    """Attenuate only, keep timing/dynamics; preserve the untouched provider file."""
    info = clip_record(source, "voice")
    if output.exists() or output.with_suffix(".json").exists() or output.suffix.lower() != ".wav":
        raise ValueError("人声整理必须输出到新版本 WAV")
    before = voice_levels(source)
    if before["peak_dbfs"] is None:
        raise ValueError("人声为空白，不能整理")
    gain_db = min(0.0, -3.0 - before["peak_dbfs"])
    output.parent.mkdir(parents=True, exist_ok=True)
    # Downmix as float before attenuation; integer rematrixing would introduce
    # an implicit extra gain change before quantisation.
    run_ffmpeg(["-i", str(source), "-map", "0:a:0", "-vn", "-af",
                f"aformat=sample_fmts=flt:sample_rates=48000:channel_layouts=mono,volume={gain_db:.9f}dB",
                "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(output)])
    after = voice_levels(output)
    measured = probe(output)
    if after["peak_dbfs"] is None or after["peak_dbfs"] > -2.99 or after["samples_at_or_above_full_scale"]:
        raise ValueError("整理后人声峰值未通过；保留文件待检查")
    if abs(measured["duration_ms"] - probe(source)["duration_ms"]) > 1:
        raise ValueError("人声整理改变了时长，拒绝采用")
    record = {"kind": "ufe-prepared-voice", "asset_kind": "voice", "language": "ja",
              "input_sha256": sha(source), "file_sha256": sha(output),
              "reference": info["reference"], "reference_sha256": info["reference_sha256"],
              "gain_db": gain_db, "before": before, "after": after, "measurement": measured,
              "runtime_approved": False, "listening_reviewed": False,
              "note": "仅统一单声道与降低线性增益；不变调、不变速、不裁切、不冒称听审通过"}
    write_new(output.with_suffix(".json"), record)
    return record


def job_path(name):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", name):
        raise ValueError("任务名只允许小写字母、数字、下划线和连字符")
    return JOBS / (name + ".json")


def submit(args):
    path = job_path(args.job)
    if path.exists():
        raise ValueError("该任务已经登记；查询原任务，不能重复提交")
    source = args.input.resolve()
    info = clip_record(source, args.kind)
    conversion = args.kind in {"voice", "instrument"}
    maximum = (100 if conversion else 50) * 1024 * 1024
    extensions = {".wav", ".mp3", ".flac"} | ({".webm"} if not conversion else set())
    if source.stat().st_size > maximum or source.suffix.lower() not in extensions:
        raise ValueError("Kits 输入格式或大小超限")
    fields = {}
    if conversion:
        if not args.voice_model or args.voice_model < 1:
            raise ValueError("转换前必须明确选择目标 voiceModelId，不自动套用陌生声线")
        if args.kind == "voice" and voice_levels(source)["samples_at_or_above_full_scale"]:
            raise ValueError("人声幅值超过播放上限，先用 prepare-voice 整理到新版本")
        if args.kind == "instrument":
            from media.audio.measure import sample_metrics
            levels = sample_metrics(source)
            if levels["silent"] or levels["rms_dbfs"] < -45:
                raise ValueError("乐器轨为空或信号过弱，不提交低价值转换")
            if levels["samples_at_or_above_full_scale"]:
                raise ValueError("乐器轨幅值超限，先整理到新版本")
        model = kits.request("GET", f"/voice-models/{args.voice_model}")
        if model.get("id") != args.voice_model or model.get("isUsable") is False:
            raise ValueError("所选声线不可用")
        is_instrument = "Instrument" in model.get("tags", [])
        if is_instrument != (args.kind == "instrument"):
            raise ValueError("人物声线与乐器模型用途不符，未提交任务")
        fields = {"voiceModelId": args.voice_model, "conversionStrength": args.strength,
                  "pitchShift": 0, "modelVolumeMix": 0}
    token = kits.credential()  # Missing credentials must fail before reserving a paid job.
    body, mime = kits.multipart(fields, "soundFile" if conversion else "inputFile", source)
    kits.reserve_post()
    record = {"schema": 1, "kind": args.kind, "input_sha256": sha(source),
              "input_file": source.relative_to(ROOT).as_posix(),
              "reference": info["reference"], "reference_sha256": info["reference_sha256"],
              "asset_kind": info["asset_kind"], "language": info.get("language"),
              "voice_model_id": args.voice_model, "parameters": fields,
              "status": "submission_unknown", "remote_id": None}
    write_new(path, record)  # Reserved before sending; a timeout cannot cause duplicate billing.
    response = kits.request("POST", "/" + kits.KINDS[args.kind], body, mime, token=token)
    remote_id = response.get("id")
    if type(remote_id) is not int or remote_id < 1:
        raise ValueError("Kits 未返回有效任务 ID；保留未知状态，禁止重发")
    record.update(remote_id=remote_id, status=response.get("status", "running"))
    update(path, record)
    return {"job": args.job, "remote_id": remote_id, "status": record["status"]}


def poll(name):
    path = job_path(name)
    record = read(path)
    if record.get("remote_id") is None:
        raise ValueError("提交状态未知且没有远端ID；先人工核查账户任务，不能重新提交")
    response = kits.remote_job(record["kind"], record["remote_id"])
    if response.get("id") != record["remote_id"]:
        raise ValueError("Kits 返回的任务ID不匹配")
    record["status"] = response.get("status", "unknown")
    # Signed URLs expire and stay only in ignored local job state, never logs.
    record["results"] = {key: response.get(key) for key in (
        "outputFileUrl", "vocalAudioFileUrl", "backingAudioFileUrl", "stemFileUrls") if response.get(key)}
    update(path, record)
    return {"job": name, "remote_id": record["remote_id"], "status": record["status"],
            "available": list(record["results"])}


def fetch_result(args):
    record = read(job_path(args.job))
    if record["status"] != "success":
        raise ValueError("任务未完成；先查询原任务")
    results = record.get("results", {})
    provider_label = None
    if args.stem == "converted":
        url = results.get("outputFileUrl")
    elif args.stem in {"vocal", "backing"}:
        url = results.get("vocalAudioFileUrl" if args.stem == "vocal" else "backingAudioFileUrl")
    else:
        urls = results.get("stemFileUrls", [])
        entry = urls[args.index] if isinstance(urls, list) and 0 <= args.index < len(urls) else None
        # Current Kits responses label each entry; older responses were URL strings.
        # Retain the provider label without pretending it is a listening review.
        url = entry.get("url") if isinstance(entry, dict) else entry
        provider_label = entry.get("instrument") if isinstance(entry, dict) else None
    if not isinstance(url, str):
        raise ValueError("任务没有该输出；不猜测 stem 顺序或下载地址")
    if args.out.with_suffix(".json").exists():
        raise ValueError("结果元数据已存在，请使用新版本目录")
    kits.download(url, args.out)
    measured = probe(args.out)
    output = {"kind": "ufe-kits-result", "asset_kind": record["asset_kind"], "language": record.get("language"),
              "reference": record["reference"], "reference_sha256": record["reference_sha256"],
              "remote_id": record["remote_id"], "operation": record["kind"], "stem": args.stem,
              "stem_index": args.index if args.stem == "indexed" else None,
              "provider_stem_label": provider_label,
              "voice_model_id": record.get("voice_model_id"), "parameters": record.get("parameters", {}),
              "input_sha256": record.get("input_sha256"), "input_file": record.get("input_file"),
              "file_sha256": sha(args.out), "measurement": measured, "runtime_approved": False,
              "listening_reviewed": False}
    write_new(args.out.with_suffix(".json"), output)
    return output


def mix(spec_path, output):
    """Rearrange verified stems locally. This is mixing, not AI composition."""
    spec = read(spec_path)
    stems = spec.get("stems", [])
    if spec.get("kind") != "ufe-music-stem-mix" or not 2 <= len(stems) <= 8:
        raise ValueError("配乐变奏需要2～8条已分离的实际音轨")
    if output.exists() or output.with_suffix(".json").exists() or output.suffix.lower() != ".wav":
        raise ValueError("混音必须输出到新版本 WAV")
    inputs, filters, measurements = [], [], []
    for i, stem in enumerate(stems):
        path = project_file(stem["file"])
        if sha(path) != stem.get("sha256") or not -60 <= float(stem["gain_db"]) <= 6:
            raise ValueError("分轨哈希变化或混音增益超限")
        measurements.append(probe(path))
        inputs.extend(["-i", str(path)])
        filters.append(f'[{i}:a]aresample=48000,volume={float(stem["gain_db"])}dB[s{i}]')
    durations = [m["duration_ms"] for m in measurements]
    if max(durations) - min(durations) > 50 or max(durations) > 180000:
        raise ValueError("分轨没有对齐或超过180秒，先校对来源和时间范围")
    filters.append("".join(f"[s{i}]" for i in range(len(stems))) +
                   f"amix=inputs={len(stems)}:duration=shortest:normalize=0,alimiter=limit=0.89:level=0[out]")
    output.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg([*inputs, "-filter_complex", ";".join(filters), "-map", "[out]", "-ac", "2",
                "-ar", "48000", "-c:a", "pcm_s16le", str(output)])
    report = {"kind": "ufe-local-music-mix", "recipe_sha256": sha(spec_path), "stems": stems,
              "file_sha256": sha(output), "measurement": probe(output), "runtime_approved": False,
              "description": "免费开源FFmpeg分轨编配与混音，不宣称AI生成新曲或已听审通过"}
    write_new(output.with_suffix(".json"), report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor")
    doctor.add_argument("--check-api", action="store_true")
    model = sub.add_parser("models")
    model.add_argument("--page", type=int, default=1)
    model.add_argument("--per-page", type=int, default=10)
    model.add_argument("--mine", action="store_true")
    model.add_argument("--instruments", action="store_true")
    cut = sub.add_parser("extract")
    cut.add_argument("--spec", type=Path, required=True)
    cut.add_argument("--out", type=Path, required=True)
    prepare = sub.add_parser("prepare-voice")
    prepare.add_argument("--input", type=Path, required=True)
    prepare.add_argument("--out", type=Path, required=True)
    cue = sub.add_parser("cut-cue")
    cue.add_argument("--spec", type=Path, required=True)
    cue.add_argument("--out", type=Path, required=True)
    send = sub.add_parser("submit")
    send.add_argument("--kind", choices=list(kits.KINDS), required=True)
    send.add_argument("--input", type=Path, required=True)
    send.add_argument("--voice-model", type=int)
    send.add_argument("--strength", type=float, default=0.15)
    send.add_argument("--job", required=True)
    status = sub.add_parser("poll")
    status.add_argument("--job", required=True)
    fetch = sub.add_parser("download")
    fetch.add_argument("--job", required=True)
    fetch.add_argument("--stem", choices=["converted", "vocal", "backing", "indexed"], required=True)
    fetch.add_argument("--index", type=int, default=0)
    fetch.add_argument("--out", type=Path, required=True)
    arrangement = sub.add_parser("mix")
    arrangement.add_argument("--spec", type=Path, required=True)
    arrangement.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "doctor":
        result = {"ffmpeg": bool(shutil.which("ffmpeg")), "ffprobe": bool(shutil.which("ffprobe")),
                  "credential_configured": bool(kits.credential()), "api": "not_checked"}
        if args.check_api:
            response = kits.models(1, 1)
            result.update(api="authenticated", returned_models=len(response["models"]))
    elif args.command == "models":
        result = kits.models(args.page, args.per_page, args.mine, args.instruments)
    elif args.command == "extract":
        result = extract(args.spec, args.out)
    elif args.command == "prepare-voice":
        result = prepare_voice(args.input, args.out)
    elif args.command == "cut-cue":
        from media.audio.cues import cut
        result = cut(args.spec, args.out)
    elif args.command == "submit":
        if not 0 <= args.strength <= 1:
            raise ValueError("声线转换强度必须在0～1之间")
        result = submit(args)
    elif args.command == "poll":
        result = poll(args.job)
    elif args.command == "download":
        result = fetch_result(args)
    else:
        result = mix(args.spec, args.out)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as exc:
        # Network exceptions are redacted in kits_client; never print headers or URLs.
        print(str(exc), file=sys.stderr)
        sys.exit(1)

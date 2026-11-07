"""Local, open source language/transcript check; never substitutes for listening QA."""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import argparse
import json; json = _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import shutil
import subprocess
import sys

from audio.pipeline import probe, sha, write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", choices=["tiny", "base", "small"], default="base")
    args = parser.parse_args()
    if args.out.exists() or probe(args.input)["duration_ms"] > 30000:
        raise ValueError("自动音轨检查只接受30秒以内样音和新版本输出")
    from faster_whisper import WhisperModel
    import numpy as np
    # Use the same FFmpeg decoder as the clip pipeline. Passing PCM directly
    # avoids depending on PyAV's changing metadata_errors argument.
    decoded = subprocess.run([shutil.which("ffmpeg"), "-hide_banner", "-nostdin", "-loglevel", "error",
        "-i", str(args.input), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "pipe:1"],
        capture_output=True, timeout=45,
        creationflags=0x08000000 if sys.platform == "win32" else 0)
    if decoded.returncode or not decoded.stdout:
        raise ValueError("FFmpeg未能解码识别样音")
    samples = np.frombuffer(decoded.stdout, dtype=np.float32)
    model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=4, num_workers=1)
    # Do not force ja: automatic detection must be able to reveal a wrong dub.
    segments, info = model.transcribe(samples, beam_size=5, vad_filter=False, condition_on_previous_text=False)
    report = {"kind": "ufe-audio-asr-observation", "model": "faster-whisper/" + args.model,
              "input_sha256": sha(args.input), "language": info.language,
              "language_probability": info.language_probability,
              "segments": [{"start_ms": round(s.start * 1000), "end_ms": round(s.end * 1000), "text": s.text} for s in segments],
              "listening_reviewed": False, "runtime_approved": False,
              "note": "自动识别辅助核对；不能证明声线、发音完整度、串音或主观听感通过"}
    write_new(args.out, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

"""离线采样检查；不将数值通过等同于实际听审。"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson

import array
import math
from pathlib import Path
Path = _LayoutProjectPath
import shutil
import subprocess
import sys


def sample_metrics(path: Path, duration_limit_ms=180000):
    from audio.pipeline import probe

    measurement = probe(path)
    if measurement["duration_ms"] > duration_limit_ms:
        raise ValueError("采样检查超出单段时长上限")
    # Preserve channel samples; do not hide a clipped channel through downmixing.
    result = subprocess.run([shutil.which("ffmpeg"), "-hide_banner", "-nostdin", "-loglevel", "error",
        "-i", str(path), "-map", "0:a:0", "-vn", "-c:a", "pcm_f32le", "-f", "f32le", "pipe:1"],
        capture_output=True, timeout=60,
        creationflags=0x08000000 if sys.platform == "win32" else 0)
    if result.returncode or not result.stdout:
        raise ValueError("音频采样解码失败")
    values = array.array("f", result.stdout)
    if sys.byteorder != "little":
        values.byteswap()
    if any(not math.isfinite(v) for v in values):
        raise ValueError("音频存在无效采样值")
    peak = max(abs(v) for v in values)
    rms = math.sqrt(math.fsum(v * v for v in values) / len(values))
    return {**measurement, "peak_dbfs": 20 * math.log10(peak) if peak else None,
            "rms_dbfs": 20 * math.log10(rms) if rms else None,
            "samples_at_or_above_full_scale": sum(abs(v) >= 1 for v in values),
            "silent": peak < 0.00001, "listening_reviewed": False}

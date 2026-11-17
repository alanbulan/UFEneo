"""运行时音频清单与文件的一致性检查；不代替听审。

检查项：
- runtime.json / battle_music.json / 动作音效清单引用的路径都存在；
- 清单引用的每个文件可读、16 位 PCM、采样率与位深统一；
- 清单引用的文件无静音、无削波、无异常短文件；未引用文件只列 orphan，不作为运行时硬门；
- 同类（sfx/voice/music）内部响度极差不超过阈值；
- 未被任何清单引用的音频文件单独列出。

输出 reports/audio-manifest.json，失败时退出码 1。
"""
from __future__ import annotations

import json
import sys
import wave
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
AUDIO_ROOT = ROOT / "assets/audio"
MANIFESTS = (
    "content/audio/runtime.json",
    "content/audio/battle_music.json",
    "content/presentation/action_sounds.json",
    "content/presentation/character_sounds.json",
    "content/presentation/projectile_audio.json",
)
# 同类响度极差上限（dB）。超过说明混音没统一。
LOUDNESS_SPREAD_DB = 12.0
# 视为无效的极短文件（秒）。
MIN_SECONDS = 0.03
SILENT_PEAK = 0.01
CLIPPED_PEAK = 0.995


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def collect_paths(node, found: set) -> None:
    """递归收集所有 path 字段。"""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "path" and isinstance(value, str) and value.startswith("res://"):
                found.add(value)
            else:
                collect_paths(value, found)
    elif isinstance(node, list):
        for item in node:
            collect_paths(item, found)


def referenced() -> set:
    found: set = set()
    for name in MANIFESTS:
        path = ROOT / name
        if path.is_file():
            collect_paths(read(path), found)
    # 代码里直接拼的常量路径（接触音效按 kind 拼 sound.wav）。
    contact = ROOT / "presentation/audio/contact_sound_library.gd"
    if contact.is_file():
        text = contact.read_text(encoding="utf-8")
        marker = 'const ROOT := "'
        if marker in text:
            base = text.split(marker, 1)[1].split('"', 1)[0]
            for kind in ("light", "heavy", "block", "special", "throw"):
                found.add(base + kind + "/sound.wav")
    return found


def measure(path: Path) -> dict:
    """WAV 直接读 PCM；OGG 没有标准库解码器，只核对容器头与时长。"""
    if path.suffix.lower() == ".ogg":
        return measure_ogg(path)
    with wave.open(str(path)) as handle:
        rate = handle.getframerate()
        channels = handle.getnchannels()
        width = handle.getsampwidth() * 8
        frames = handle.getnframes()
        samples = np.frombuffer(handle.readframes(frames), dtype="<i2").astype(np.float32) / 32768.0
    seconds = frames / rate if rate else 0.0
    peak = float(np.max(np.abs(samples))) if samples.size else 0.0
    rms = float(np.sqrt(np.mean(samples**2))) if samples.size else 0.0
    return {
        "seconds": round(seconds, 3),
        "rate": rate,
        "channels": channels,
        "bits": width,
        "peak": round(peak, 4),
        "rms_db": round(20 * np.log10(max(rms, 1e-9)), 1),
    }


def measure_ogg(path: Path) -> dict:
    """读 Ogg 页头的采样率/声道，按最后一页的 granule 位置估时长。"""
    data = path.read_bytes()
    if not data.startswith(b"OggS"):
        raise ValueError("不是 Ogg 容器")
    rate = channels = 0
    last_granule = 0
    offset = 0
    while offset + 27 <= len(data):
        if data[offset : offset + 4] != b"OggS":
            break
        granule = int.from_bytes(data[offset + 6 : offset + 14], "little", signed=True)
        segments = data[offset + 26]
        if granule > 0:
            last_granule = granule
        body = offset + 27 + segments
        if rate == 0 and body + 16 <= len(data) and data[body : body + 1] == b"\x01":
            # 第一个包是 identification header：\x01vorbis + version + channels + rate
            channels = data[body + 11]
            rate = int.from_bytes(data[body + 12 : body + 16], "little")
        table = data[offset + 27 : offset + 27 + segments]
        offset = body + sum(table)
    seconds = last_granule / rate if rate else 0.0
    return {
        "seconds": round(seconds, 3),
        "rate": rate,
        "channels": channels,
        "bits": None,
        "peak": None,
        "rms_db": None,
    }


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    wanted = referenced()

    missing = sorted(p for p in wanted if not (ROOT / p.removeprefix("res://")).is_file())
    for path in missing:
        errors.append("清单引用但文件不存在：" + path)

    on_disk = {
        "res://" + p.relative_to(ROOT).as_posix()
        for p in AUDIO_ROOT.rglob("*")
        if p.suffix.lower() in (".wav", ".ogg", ".mp3")
    }
    orphans = sorted(on_disk - wanted)
    for path in orphans:
        warnings.append("磁盘有但清单未引用：" + path)

    metrics: list[dict] = []
    formats: Counter = Counter()
    by_kind: defaultdict[str, list] = defaultdict(list)
    runtime = read(ROOT / "content/audio/runtime.json")
    kinds = {sid: str(item.get("kind", "sfx")) for sid, item in runtime.get("sounds", {}).items()}
    paths_by_id = {sid: str(item.get("path", "")) for sid, item in runtime.get("sounds", {}).items()}

    for path in sorted(on_disk):
        local = ROOT / path.removeprefix("res://")
        try:
            data = measure(local)
        except Exception as error:  # noqa: BLE001 - 任何解码失败都要报出来
            errors.append(f"读取失败 {path}: {error}")
            continue
        data["path"] = path
        metrics.append(data)
        formats[(data["rate"], data["channels"], data["bits"])] += 1
        # 中间制作源、分离轨和旧未引用文件不在运行时清单内，只列 orphan；
        # 静音/削波/过短硬门只判清单实际引用的文件，避免把制作中间物冒充运行时缺陷。
        if path not in wanted:
            continue
        # OGG 没有解码器，peak/rms 为 None，跳过波形判据。
        if data["peak"] is not None:
            if data["peak"] < SILENT_PEAK:
                errors.append(f"近乎无声：{path} peak={data['peak']}")
            if data["peak"] > CLIPPED_PEAK:
                errors.append(f"削波：{path} peak={data['peak']}")
        if data["seconds"] < MIN_SECONDS:
            errors.append(f"过短：{path} {data['seconds']}s")
        for sid, item_path in paths_by_id.items():
            if item_path == path:
                if data["rms_db"] is not None:
                    by_kind[kinds[sid]].append((sid, data["rms_db"]))
                break

    if len(formats) > 1:
        summary = ", ".join(f"{rate}Hz/{ch}ch/{bits}bit×{n}" for (rate, ch, bits), n in formats.most_common())
        warnings.append("音频格式不统一：" + summary)

    spreads = {}
    for kind, rows in by_kind.items():
        values = [db for _, db in rows]
        if not values:
            continue
        spread = max(values) - min(values)
        spreads[kind] = round(spread, 1)
        if spread > LOUDNESS_SPREAD_DB:
            warnings.append(f"{kind} 类响度极差 {spread:.1f}dB 超过 {LOUDNESS_SPREAD_DB}dB")

    report = {
        "files": len(metrics),
        "referenced": len(wanted),
        "orphans": orphans,
        "formats": {f"{r}Hz/{c}ch/{b}bit": n for (r, c, b), n in formats.items()},
        "loudness_spread_db": spreads,
        "errors": errors,
        "warnings": warnings,
        "note": "只核对清单引用文件、格式、静音/削波/时长与同类响度离散度；未引用制作中间物只列 orphan；不代替人耳听审。",
    }
    output = ROOT / "reports/audio-manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"音频文件 {len(metrics)}，清单引用 {len(wanted)}，未引用 {len(orphans)}")
    for message in errors:
        print("错误:", message)
    for message in warnings:
        print("提示:", message)
    print("AUDIO_MANIFEST " + ("PASS" if not errors else "FAIL"))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

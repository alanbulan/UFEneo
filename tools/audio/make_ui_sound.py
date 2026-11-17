"""生成图鉴/菜单的像素 UI 提示音。

项目里没有现成的短 UI 音——select.wav、menu.wav 实际是 63 秒的整曲，直接当
点击音会播放整首。这里用固定参数合成一个 90 毫秒的双音阶方波提示音：纯数字
合成，不涉及任何原作素材，也不冒充原声。

用法：
    python tools/audio/make_ui_sound.py            # 写入默认路径
    python tools/audio/make_ui_sound.py --check    # 只校验现有文件
"""
from __future__ import annotations

import argparse
import hashlib
import math
import struct
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "assets/audio/production/v1/catalogue_pick.wav"
RATE = 48000
TONE_A = 1180.0
TONE_B = 1560.0
SEGMENT = 0.028
AMPLITUDE = 0.22


def envelope(index: int, total: int) -> float:
    """两端各 15% 的线性淡入淡出，避免爆音。"""
    edge = max(1, int(total * 0.15))
    if index < edge:
        return index / edge
    if index > total - edge:
        return (total - index) / edge
    return 1.0


def render() -> bytes:
    samples = bytearray()
    for tone, count in ((TONE_A, 2), (TONE_B, 1)):
        total = int(RATE * SEGMENT)
        for _repeat in range(count):
            for index in range(total):
                phase = 2.0 * math.pi * tone * index / RATE
                # 方波：只取符号，保持像素时代的硬音色。
                value = AMPLITUDE * envelope(index, total) * (1.0 if math.sin(phase) >= 0.0 else -1.0)
                samples += struct.pack("<h", int(max(-1.0, min(1.0, value)) * 32767))
    tail = int(RATE * 0.006)
    for index in range(tail):
        value = AMPLITUDE * (1.0 - index / tail) * (1.0 if math.sin(2.0 * math.pi * TONE_B * index / RATE) >= 0.0 else -1.0)
        samples += struct.pack("<h", int(value * 32767))
    return bytes(samples)


def write(out: Path) -> dict:
    payload = render()
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(payload)
    return {
        "out": out.relative_to(ROOT).as_posix(),
        "seconds": round(len(payload) / 2 / RATE, 3),
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true", help="只检查文件是否存在且时长合理")
    args = parser.parse_args()

    if args.check:
        if not args.out.is_file():
            print(f"缺少 {args.out.relative_to(ROOT)}", file=sys.stderr)
            return 1
        with wave.open(str(args.out), "rb") as handle:
            seconds = handle.getnframes() / handle.getframerate()
        ok = 0.05 <= seconds <= 0.30
        print(f"{args.out.relative_to(ROOT).as_posix()}  {seconds:.3f}s  " + ("OK" if ok else "时长异常"))
        return 0 if ok else 1

    print(write(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

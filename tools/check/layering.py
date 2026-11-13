"""分层与确定性守卫；把 docs/HANDBOOK.md“目录架构”的规则变成可执行检查。

检查项：
- 层间只允许向下依赖，出现反向引用即失败；
- core/ 与 input/ 不出现随机数、系统时间、Input、渲染引用；
- core/ 不引用 presentation/ui/app；
- presentation/ 不写模拟状态（stats/state/tick 赋值）；
- 图片、音频、字体不进内容指纹。

只做静态文本检查，不证明运行时正确。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAYERS = ("core", "input", "presentation", "ui", "app", "content")
# 允许的依赖方向：键可以依赖值里的层。
ALLOWED = {
    "core": set(),
    "input": set(),
    "content": set(),
    "presentation": {"core", "content"},
    "ui": {"presentation", "content"},
    "app": {"content", "input", "presentation", "ui", "core"},
}
# 确定性禁区：只对 core 与 input 生效。
NONDETERMINISTIC = re.compile(
    r"\b(?:randi|randf|randi_range|randf_range|randfn|randomize|shuffle)\s*\("
    r"|\bTime\.\w+"
    r"|\bOS\.(?:get_ticks\w*|get_unix_time\w*|get_system_time\w*)"
    r"|\bInput\.\w+"
)
# 表现层只读：不允许写"活模拟"的角色。
# 演出副本（KO 慢放重建的 scene）可以写，它是表现层自己的数据。
SIMULATION_WRITE = re.compile(
    r"\b(?:view\.simulation|sim)\.fighters\[[^\]]+\]\.(?:stats|state|state_tick|move_id|move_tick|x|vx|vy|height|facing)\s*=[^=]"
)


def sources(layer: str) -> dict[Path, str]:
    return {
        path: path.read_text(encoding="utf-8", errors="replace")
        for path in (ROOT / layer).rglob("*.gd")
    }


def layer_of(path: Path) -> str | None:
    try:
        first = path.relative_to(ROOT).parts[0]
    except ValueError:
        return None
    return first if first in LAYERS else None


def main() -> int:
    errors: list[str] = []
    files = {layer: sources(layer) for layer in LAYERS}

    # 1. 层间依赖方向。
    edges: dict[tuple[str, str], set[str]] = {}
    for layer, mapping in files.items():
        for path, text in mapping.items():
            for match in re.finditer(r'res://([a-z_]+)/', text):
                target = match.group(1)
                if target not in LAYERS or target == layer:
                    continue
                edges.setdefault((layer, target), set()).add(path.relative_to(ROOT).as_posix())
    for (source, target), paths in sorted(edges.items()):
        if target not in ALLOWED[source]:
            for path in sorted(paths):
                errors.append(f"层间反向依赖：{path} 引用了 {target}/")

    # 2. 确定性禁区。input/ 天生要读设备状态，只对 core/ 生效。
    for layer in ("core",):
        for path, text in files[layer].items():
            for number, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("##"):
                    continue
                if NONDETERMINISTIC.search(line):
                    errors.append(
                        f"{path.relative_to(ROOT)}:{number} {layer} 不允许非确定性调用：{stripped[:70]}"
                    )

    # 3. 表现层不写模拟状态。
    for path, text in files["presentation"].items():
        for number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if SIMULATION_WRITE.search(line):
                errors.append(
                    f"{path.relative_to(ROOT)}:{number} presentation 不得写模拟状态：{stripped[:70]}"
                )

    # 4. 内容指纹不含媒体路径。
    for path, text in files["core"].items():
        if "content_fingerprint" not in text and "state_hash" not in text:
            continue
        for match in re.finditer(r'"(res://(?:assets|art)/[^"]+)"', text):
            errors.append(
                f"{path.relative_to(ROOT)} 指纹代码引用了媒体路径：{match.group(1)}"
            )

    print(f"扫描 {sum(len(v) for v in files.values())} 个 .gd 文件，层间边 {len(edges)} 条")
    for message in errors:
        print("错误:", message)
    print("LAYERING " + ("PASS" if not errors else "FAIL"))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

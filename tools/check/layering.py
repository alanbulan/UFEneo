"""分层与确定性守卫；把 docs/HANDBOOK.md“目录架构”的规则变成可执行检查。

检查项：
- 六层单向 DAG：app → ui → presentation → content/core，input → core，content → core，严禁反向引用；
- 运行层（core/content/input/presentation/ui/app）严禁通过路径或全局 class_name 引用 tests/；
- core/ 不出现随机数、系统时间、Input；
- presentation/ 不写活模拟状态（含 stats/combat/motion/state/位置等）；
- 指纹与状态哈希代码不含媒体路径。

只做静态文本检查，不证明运行时正确。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAYERS = ("core", "content", "input", "presentation", "ui", "app")
ALL_CODE_ROOTS = (*LAYERS, "tests")
# 允许的严格单向依赖：键层只能引用自身或值集合中的层。
ALLOWED = {
    "core": set(),
    "content": {"core"},
    "input": {"core"},
    "presentation": {"core", "content"},
    "ui": {"core", "content", "input", "presentation"},
    "app": {"core", "content", "input", "presentation", "ui"},
}
# 确定性禁区：只对 core 生效。
NONDETERMINISTIC = re.compile(
    r"\b(?:randi|randf|randi_range|randf_range|randfn|randomize|shuffle)\s*\("
    r"|\bTime\.\w+"
    r"|\bOS\.(?:get_ticks\w*|get_unix_time\w*|get_system_time\w*)"
    r"|\bInput\.\w+"
)
# 表现层只读：不允许写“活模拟”的角色或其 stats/combat/motion 字段。
SIMULATION_WRITE = re.compile(
    r"\b(?:view\.simulation|sim|simulation)\.fighters\[[^\]]+\]\."
    r"(?:stats|combat|motion|state|state_tick|move_id|move_tick|x|vx|vy|height|facing)"
    r"(?:\.[A-Za-z_][A-Za-z0-9_]*)?\s*(?:[+\-*/]?=)(?!=)"
)
CLASS_NAME_RE = re.compile(r"^\s*class_name\s+([A-Za-z_][A-Za-z0-9_]*)\b", re.M)
RES_PATH_RE = re.compile(r'res://([a-z_]+)/')


def strip_gdscript(text: str, strip_strings: bool = True) -> str:
    """移除 GDScript 注释（以及可选的字符串字面量），保留换行以维持行号。"""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "#":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if text.startswith('"""', i) or text.startswith("'''", i):
            quote = text[i : i + 3]
            if not strip_strings:
                out.append(quote)
            i += 3
            while i < n and not text.startswith(quote, i):
                if text[i] == "\\" and i + 1 < n:
                    if not strip_strings:
                        out.append(text[i : i + 2])
                    i += 2
                    continue
                if text[i] == "\n":
                    out.append("\n")
                elif not strip_strings:
                    out.append(text[i])
                i += 1
            if i < n:
                if not strip_strings:
                    out.append(quote)
                i += 3
            continue
        if ch in ('"', "'"):
            quote = ch
            if not strip_strings:
                out.append(quote)
            i += 1
            while i < n and text[i] != quote and text[i] != "\n":
                if text[i] == "\\" and i + 1 < n:
                    if not strip_strings:
                        out.append(text[i : i + 2])
                    i += 2
                    continue
                if not strip_strings:
                    out.append(text[i])
                i += 1
            if i < n and text[i] == quote:
                if not strip_strings:
                    out.append(quote)
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def sources(layer: str) -> dict[Path, str]:
    base = ROOT / layer
    if not base.is_dir():
        return {}
    return {
        path: path.read_text(encoding="utf-8", errors="replace")
        for path in sorted(base.rglob("*.gd"))
    }


def collect_class_owners() -> dict[str, tuple[str, str]]:
    """收集全仓 .gd（含 tests/）的全局 class_name -> (所属顶层目录, 相对路径)。"""
    owners: dict[str, tuple[str, str]] = {}
    for root_dir in ALL_CODE_ROOTS:
        for path, text in sources(root_dir).items():
            for match in CLASS_NAME_RE.finditer(text):
                symbol = match.group(1)
                owners[symbol] = (root_dir, path.relative_to(ROOT).as_posix())
    return owners


def main() -> int:
    errors: list[str] = []
    files = {layer: sources(layer) for layer in LAYERS}
    owners = collect_class_owners()
    symbol_re = (
        re.compile(r"\b(" + "|".join(sorted(map(re.escape, owners), key=len, reverse=True)) + r")\b")
        if owners
        else None
    )

    edges: set[tuple[str, str, str, str]] = set()
    for layer, mapping in files.items():
        allowed = ALLOWED[layer] | {layer}
        for path, text in mapping.items():
            rel = path.relative_to(ROOT).as_posix()
            no_comments = strip_gdscript(text, strip_strings=False)
            code_only = strip_gdscript(text, strip_strings=True)
            own_class = CLASS_NAME_RE.search(text)
            own_symbol = own_class.group(1) if own_class else ""

            for match in RES_PATH_RE.finditer(no_comments):
                target = match.group(1)
                if target not in ALL_CODE_ROOTS or target == layer:
                    continue
                edges.add((layer, target, rel, f"res://{target}/"))
                if target not in allowed:
                    errors.append(f"越层路径依赖：{rel} 引用了 {target}/")

            if symbol_re is not None:
                for match in symbol_re.finditer(code_only):
                    symbol = match.group(1)
                    if symbol == own_symbol:
                        continue
                    target_layer, target_file = owners[symbol]
                    if target_layer == layer:
                        continue
                    edges.add((layer, target_layer, rel, symbol))
                    if target_layer not in allowed:
                        errors.append(
                            f"越层符号依赖：{rel} 引用了 {target_layer} 层的 {symbol}（来自 {target_file}）"
                        )

    # 2. core 确定性禁区。
    for path, text in files["core"].items():
        code_only = strip_gdscript(text, strip_strings=True)
        for number, line in enumerate(code_only.splitlines(), 1):
            if NONDETERMINISTIC.search(line):
                errors.append(
                    f"{path.relative_to(ROOT)}:{number} core 不允许非确定性调用：{line.strip()[:70]}"
                )

    # 3. 表现层只读：禁止写模拟状态。
    for path, text in files["presentation"].items():
        code_only = strip_gdscript(text, strip_strings=True)
        for number, line in enumerate(code_only.splitlines(), 1):
            if SIMULATION_WRITE.search(line):
                errors.append(
                    f"{path.relative_to(ROOT)}:{number} presentation 不得写模拟状态：{line.strip()[:70]}"
                )

    # 4. 内容指纹不含媒体路径。
    for path, text in files["core"].items():
        if "content_fingerprint" not in text and "state_hash" not in text:
            continue
        no_comments = strip_gdscript(text, strip_strings=False)
        for match in re.finditer(r'"(res://(?:assets|art)/[^"]+)"', no_comments):
            errors.append(
                f"{path.relative_to(ROOT)} 指纹代码引用了媒体路径：{match.group(1)}"
            )

    layer_pairs = {(src, dst) for src, dst, _, _ in edges}
    print(f"扫描 {sum(len(v) for v in files.values())} 个 .gd 文件，跨层边 {len(layer_pairs)} 对（符号/路径引用 {len(edges)} 处）")
    for message in sorted(set(errors)):
        print("错误:", message)
    print("LAYERING " + ("PASS" if not errors else "FAIL"))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

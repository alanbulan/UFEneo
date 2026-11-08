"""扫描 GDScript 静态分析警告，对应编辑器 Debugger 面板里的黄色警告。

原理：临时把 project.godot 的相关警告级别设为「错误」，再用 `--check-only`
逐文件解析——这样 Godot 自己的分析器会报出 exact 文件与行号，不需要自己
写正则去猜类型。

用法：
    python tools/check/gdscript_warnings.py            # 扫描全仓
    python tools/check/gdscript_warnings.py --summary  # 只输出按文件汇总
    python tools/check/gdscript_warnings.py --fix-hint # 附带修复建议

退出码：0 = 零警告，1 = 有警告。
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "project.godot"
SCAN_DIRS = ("core", "input", "presentation", "ui", "app", "content", "tests")

# 需要纳入扫描的警告类别。级别 2 = 当成错误，从而在 --check-only 时暴露。
WARNING_SETTINGS = {
    "unused_parameter": 2,
    "unused_variable": 2,
    "unused_signal": 2,
    "integer_division": 2,
    "int_as_enum_without_cast": 2,
    "shadowed_variable_base_class": 2,
    "shadowed_variable": 2,
    "standalone_expression": 2,
}

MESSAGE = re.compile(r"Parse Error: (?P<message>.+?)(?: \(Warning treated as error\))?$")


def godot_executable() -> str:
    """从 GODOT_PATH 或常见安装位置取 Godot 可执行文件。"""
    import os
    candidate = os.environ.get("GODOT_PATH", "").strip()
    if candidate and Path(candidate).is_file():
        return candidate
    for guess in ("/opt/homebrew/bin/godot", "/Applications/Godot.app/Contents/MacOS/Godot"):
        if Path(guess).is_file():
            return guess
    found = shutil.which("godot")
    if found:
        return found
    raise SystemExit("未找到 Godot；设置 GODOT_PATH 或把它加进 PATH")


def with_warning_settings():
    """临时把警告级别写进 project.godot，返回恢复函数。"""
    original = PROJECT.read_text(encoding="utf-8")
    if "[debug]" in original:
        # 已有 debug 段：逐条插入缺失项。
        lines = original.splitlines()
        insert_at = lines.index("[debug]") + 1
        existing = {line.split("=")[0].strip() for line in lines}
        additions = [
            f"gdscript/warnings/{name}={level}"
            for name, level in WARNING_SETTINGS.items()
            if f"gdscript/warnings/{name}" not in existing
        ]
        lines[insert_at:insert_at] = additions
        patched = "\n".join(lines) + "\n"
    else:
        block = "\n[debug]\n\n" + "\n".join(
            f"gdscript/warnings/{name}={level}" for name, level in WARNING_SETTINGS.items()
        ) + "\n"
        patched = original.rstrip() + "\n" + block
    PROJECT.write_text(patched, encoding="utf-8")

    def restore() -> None:
        PROJECT.write_text(original, encoding="utf-8")

    return restore


def scan_file(executable: str, relative: str) -> list[dict]:
    """用 --check-only 解析单个文件，返回它自己的警告（不含依赖）。"""
    command = [executable, "--headless", "--path", str(ROOT),
               "--check-only", "--script", f"res://{relative}"]
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=30, cwd=ROOT)
    except subprocess.TimeoutExpired:
        return [{"file": relative, "line": 0, "message": "解析超时", "raw": ""}]
    output = (result.stdout or "") + (result.stderr or "")
    findings: list[dict] = []
    pending = None
    for raw_line in output.splitlines():
        line = raw_line.strip()
        match = MESSAGE.search(line)
        if match:
            pending = match.group("message")
            continue
        location = re.search(r"at: GDScript::reload \(res://(?P<path>[^:]+):(?P<line>\d+)\)", line)
        if location and pending:
            # 只保留本文件自己的警告；依赖文件的警告由依赖自己那一轮报告。
            if location.group("path") == relative:
                findings.append({
                    "file": relative,
                    "line": int(location.group("line")),
                    "message": pending,
                    "raw": line,
                })
            pending = None
    return findings


def sources() -> list[str]:
    found: list[str] = []
    for name in SCAN_DIRS:
        for path in sorted((ROOT / name).rglob("*.gd")):
            found.append(path.relative_to(ROOT).as_posix())
    return found


def fix_hint(message: str) -> str:
    """把 Godot 的原始警告翻译成可执行的修复建议。"""
    if "never used" in message:
        match = re.search(r'"(\w+)"', message)
        name = match.group(1) if match else "x"
        return f'前缀下划线："{name}" -> "_{name}"'
    if "Integer division" in message:
        return "确认是否有意取整；有意则用 int() 显式表达或加 @warning_ignore(\"integer_division\")"
    if "shadowing an already-declared" in message:
        match = re.search(r'"(\w+)"', message)
        name = match.group(1) if match else "x"
        return f'改名避开基类成员："{name}" -> "_{name}" 或更具体的名字'
    if "Integer used when an enum value is expected" in message:
        return '改用枚举常量，或用 "as" 显式转换'
    if "declared but never used" in message:
        match = re.search(r'"(\w+)"', message)
        name = match.group(1) if match else "x"
        return f'删掉或改名 "_​{name}"'
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true", help="只输出按文件汇总")
    parser.add_argument("--fix-hint", action="store_true", help="附带修复建议")
    parser.add_argument("--only", nargs="*", help="只扫描指定目录")
    args = parser.parse_args()

    executable = godot_executable()
    targets = sources()
    if args.only:
        targets = [t for t in targets if t.split("/")[0] in args.only]

    restore = with_warning_settings()
    findings: list[dict] = []
    try:
        for index, relative in enumerate(targets, 1):
            findings.extend(scan_file(executable, relative))
            if index % 40 == 0:
                print(f"  已扫描 {index}/{len(targets)}，累计 {len(findings)} 条", file=sys.stderr)
    finally:
        restore()

    # 同一文件同一行的同类警告去重。
    unique = {(f["file"], f["line"], f["message"]): f for f in findings}
    findings = sorted(unique.values(), key=lambda f: (f["file"], f["line"]))

    by_message = Counter(f["message"] for f in findings)
    by_file = Counter(f["file"] for f in findings)

    print(f"扫描 {len(targets)} 个 .gd 文件，发现 {len(findings)} 条警告")
    print()
    print("按类型：")
    for message, count in by_message.most_common():
        print(f"  {count:4d}  {message[:100]}")

    if args.summary:
        print()
        print("按文件：")
        for name, count in by_file.most_common():
            print(f"  {count:4d}  {name}")
    else:
        print()
        for finding in findings:
            hint = f"  → {fix_hint(finding['message'])}" if args.fix_hint else ""
            print(f"{finding['file']}:{finding['line']}  {finding['message'][:90]}{hint}")

    print()
    print("GDSCRIPT_WARNINGS " + ("CLEAN" if not findings else "FOUND"))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())

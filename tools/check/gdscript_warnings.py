"""扫描 GDScript 静态分析警告，对应编辑器 Debugger 面板里的黄色警告。

原理：校验 project.godot 的 [debug] 段已固化全部严格警告级别（2 = 视作错误），
再并发使用 `--headless --check-only` 只读解析每个 `.gd` 文件，不修改项目文件。

用法：
    python tools/check/gdscript_warnings.py            # 扫描全仓
    python tools/check/gdscript_warnings.py --summary  # 只输出按文件汇总
    python tools/check/gdscript_warnings.py --fix-hint # 附带修复建议

退出码：0 = 零警告，1 = 有警告或配置缺失。
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import re
import subprocess
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from runtime.environment import ROOT, godot_path

PROJECT = ROOT / "project.godot"
SCAN_DIRS = ("core", "input", "presentation", "ui", "app", "content", "tests")

WARNING_SETTINGS = {
    "unused_parameter": 2,
    "unused_variable": 2,
    "unused_signal": 2,
    "integer_division": 2,
    "int_as_enum_without_cast": 2,
    "shadowed_variable_base_class": 2,
    "shadowed_variable": 2,
    "standalone_expression": 2,
    "incompatible_ternary": 2,
    "confusable_local_declaration": 2,
    "confusable_local_usage": 2,
    "shadowed_global_identifier": 2,
}

MESSAGE = re.compile(r"Parse Error: (?P<message>.+?)(?: \(Warning treated as error\))?$")


def verify_project_settings() -> list[str]:
    """只读校验 project.godot 已固化 exclude_addons=true 及全部严格警告级别=2。"""
    if not PROJECT.is_file():
        return ["缺少 project.godot"]
    content = PROJECT.read_text(encoding="utf-8")
    in_debug = False
    debug_values: dict[str, str] = {}
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            in_debug = line == "[debug]"
            continue
        if in_debug and "=" in line:
            key, value = line.split("=", 1)
            debug_values[key.strip()] = value.strip()
    errors: list[str] = []
    if debug_values.get("gdscript/warnings/exclude_addons") != "true":
        errors.append("project.godot [debug] 缺少 gdscript/warnings/exclude_addons=true")
    for name, level in WARNING_SETTINGS.items():
        key = f"gdscript/warnings/{name}"
        if debug_values.get(key) != str(level):
            errors.append(f"project.godot [debug] 缺少或未固化 {key}={level}（当前：{debug_values.get(key, '未配置')}）")
    return errors


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
        return '确认是否有意取整；有意则用 int() 显式表达或加 @warning_ignore("integer_division")'
    if "shadowing an already-declared" in message:
        match = re.search(r'"(\w+)"', message)
        name = match.group(1) if match else "x"
        return f'改名避开基类成员："{name}" -> "_{name}" 或更具体的名字'
    if "Integer used when an enum value is expected" in message:
        return '改用枚举常量，或用 "as" 显式转换'
    if "declared but never used" in message:
        match = re.search(r'"(\w+)"', message)
        name = match.group(1) if match else "x"
        return f'删掉或改名 "_{name}"'
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true", help="只输出按文件汇总")
    parser.add_argument("--fix-hint", action="store_true", help="附带修复建议")
    parser.add_argument("--only", nargs="*", help="只扫描指定目录")
    args = parser.parse_args()

    config_errors = verify_project_settings()
    if config_errors:
        for err in config_errors:
            print("配置错误:", err, file=sys.stderr)
        print("GDSCRIPT_WARNINGS FAIL")
        return 1

    executable = godot_path()
    targets = sources()
    if args.only:
        targets = [t for t in targets if t.split("/")[0] in args.only]

    findings: list[dict] = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        for file_findings in executor.map(lambda rel: scan_file(executable, rel), targets):
            findings.extend(file_findings)

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

"""Capture main-game UI pages via tests/review/cli_harness.gd."""
from pathlib import Path
import argparse, subprocess, sys

TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
from runtime.environment import ROOT, godot_path, isolated_test_environment


def capture(page: str, res: str, out_dir: Path, long_text: bool) -> None:
    if not out_dir.resolve().is_relative_to(ROOT / "reports"):
        raise RuntimeError("截图输出必须位于本工程reports目录内")
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{page}-{res}{'-long' if long_text else ''}"
    cmd = [godot_path(), "--path", str(ROOT), "--resolution", res, "--",
           "--harness=res://tests/review/cli_harness.gd", f"--capture-size={res}", f"--capture-ui={page}",
           f"--capture={out_dir / (name + '.png')}", "--capture-frame=45", "--auto-quit=65"]
    if long_text:
        cmd.append("--review-long-text")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, errors="replace", timeout=80,
                          env=isolated_test_environment(out_dir / (name + "-runtime")))
    output = (proc.stdout or "") + (proc.stderr or "")
    (out_dir / f"{name}.log").write_text(output, encoding="utf-8")
    if "SCRIPT ERROR" in output or "\nERROR:" in output or not (out_dir / f"{name}.png").is_file():
        raise RuntimeError(output[-4000:] or f"Missing screenshot: {name}")
    print(name, proc.returncode, flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("pages", nargs="+")
    p.add_argument("--resolution", default="1280x720")
    p.add_argument("--long", action="store_true")
    p.add_argument("--output-dir", type=Path, default=ROOT / "reports/review/ui-captures")
    args = p.parse_args()
    for page in args.pages:
        capture(page, args.resolution, args.output_dir.resolve(), args.long)

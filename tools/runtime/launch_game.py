"""Launch the main game using GODOT_PATH or a locally installed Godot."""
from pathlib import Path
import argparse
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime.environment import godot_path, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--battle", action="store_true")
    mode.add_argument("--local", action="store_true")
    mode.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    command = [godot_path(), "--path", str(ROOT)]
    flag = "--battle" if args.battle else "--local" if args.local else "--demo=neo" if args.demo else ""
    if flag:
        command += ["--", flag]
    # Keep the same shared lock throughout the lifetime of the game process.
    command = [sys.executable, str(ROOT / "tools/godot_lock.py"), "--", *command]
    subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError) as error:
        print(f"无法启动游戏：{error}")
        raise SystemExit(1)

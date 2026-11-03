"""Resolve a local Godot executable without depending on production artwork tools."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import tomllib

ROOT = Path(__file__).resolve().parents[2]


def godot_path() -> str:
    configured = os.environ.get("GODOT_PATH")
    if configured:
        if not Path(configured).is_file():
            raise RuntimeError("GODOT_PATH does not point to a file")
        return configured
    for name in ("godot", "godot4"):
        found = shutil.which(name)
        if found:
            return found
    # Compatibility with this machine's existing configuration. Never copy it.
    config = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "config.toml"
    if config.is_file():
        data = tomllib.loads(config.read_text(encoding="utf-8"))
        configured = data.get("mcp_servers", {}).get("godot", {}).get("env", {}).get("GODOT_PATH")
        if configured and Path(configured).is_file():
            return str(configured)
    raise RuntimeError("Install Godot 4.7 and set GODOT_PATH to its executable")


def isolated_test_environment(output: Path) -> dict[str, str]:
    """Tests must never overwrite the player's settings or saved replay."""
    env = os.environ.copy()
    data = output / "userdata"
    data.mkdir(parents=True, exist_ok=True)
    env["APPDATA"] = str(data)
    env["XDG_DATA_HOME"] = str(data)
    return env

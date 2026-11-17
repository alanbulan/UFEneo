#!/bin/bash
# macOS 启动器：优先 UFENEO_PYTHON，其次项目 .venv，最后 PATH 中的 python3。
cd "$(dirname "$0")" || exit 1

if [ -n "$UFENEO_PYTHON" ]; then
  PY="$UFENEO_PYTHON"
elif [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="$(command -v python3)"
fi

if [ -z "$PY" ]; then
  echo "未找到 Python 3.12+；请先运行 python3 -m venv .venv 并安装依赖。" >&2
  read -r -p "按回车关闭..." _
  exit 1
fi

"$PY" -B tools/runtime/launch_game.py
status=$?
if [ "$status" -ne 0 ]; then
  read -r -p "启动失败（退出码 $status），按回车关闭..." _
fi
exit "$status"

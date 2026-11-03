@echo off
chcp 65001 >nul
cd /d "%~dp0"
if defined UFENEO_PYTHON (
  "%UFENEO_PYTHON%" -B "tools\runtime\launch_game.py"
) else if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -B "tools\runtime\launch_game.py"
) else (
  python -B "tools\runtime\launch_game.py"
)
if errorlevel 1 pause

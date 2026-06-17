@echo off
REM open_is_backoffice.bat — wrapper to run scripts\open_is_backoffice.py
SETLOCAL ENABLEDELAYEDEXPANSION
REM Resolve script directory and repo root (parent of scripts) 
SET SCRIPT_DIR=%~dp0
PUSHD "%SCRIPT_DIR%..\"
REM Prefer venv python if present, otherwise use system python
IF EXIST ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" "%CD%\scripts\open_is_backoffice.py" %*
) ELSE (
  python "%CD%\scripts\open_is_backoffice.py" %*
)
POPD
ENDLOCAL

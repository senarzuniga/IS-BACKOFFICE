@echo off
REM RC1 launcher for Reel Load Simulator (Windows)
python "scripts\run_reel_rc1.py" %*
if %errorlevel% neq 0 (
  echo Simulator exited with code %errorlevel%
  exit /b %errorlevel%
)
exit /b 0

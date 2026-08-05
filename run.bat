@echo off
REM run.bat — Launch IS-BACKOFFICE Streamlit application (improved)

setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

REM Prefer the project's virtual environment if present
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

REM Validate Python executable/command before continuing
if /i "%PY%"=="python" (
    where python >nul 2>&1
    if errorlevel 1 (
        echo Python is not available in PATH.
        pause
        exit /b 1
    )
)

REM Find a free port between 8501 and 8530
set "PORT="
for /l %%P in (8501,1,8530) do (
    rem Use PowerShell TCP query to avoid locale-dependent netstat parsing
    powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort %%P -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }" >nul 2>&1
    if not errorlevel 1 (
        set "PORT=%%P"
        goto :port_found
    )
)

echo No se encontro un puerto libre entre 8501 y 8530.
pause
exit /b 1

:port_found
echo Usando puerto %PORT%

REM Ensure streamlit is installed in the selected Python
"%PY%" -m pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo Streamlit not found. Installing dependencies into %PY%...
    "%PY%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency installation failed.
        pause
        exit /b 1
    )
)

start "" "http://localhost:%PORT%"
"%PY%" -m streamlit run streamlit_app.py --server.port %PORT% --server.fileWatcherType none
set "APP_EXIT=%ERRORLEVEL%"

endlocal & exit /b %APP_EXIT%

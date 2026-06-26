@echo off
REM run.bat — Launch IS-BACKOFFICE Streamlit application (improved)

setlocal
cd /d "%~dp0"

REM Prefer the project's virtual environment if present
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

REM Find a free port between 8501 and 8530
set "PORT="
for /l %%P in (8501,1,8530) do (
    netstat -ano | findstr /r /c:":%%P .*LISTENING" >nul 2>&1
    if errorlevel 1 (
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
if %ERRORLEVEL% neq 0 (
    echo Streamlit not found. Installing dependencies into %PY%...
    "%PY%" -m pip install -r requirements.txt
)

start "" "http://localhost:%PORT%"
"%PY%" -m streamlit run streamlit_app.py --server.port %PORT% --server.fileWatcherType none

endlocal

@echo off
@echo off
setlocal
cd /d "%~dp0"

REM Prefer the project virtual environment when it exists.
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

if not exist "%~dp0scripts\open_is_backoffice.py" (
	echo ERROR: No se encuentra scripts\open_is_backoffice.py
	pause
	exit /b 1
)

REM Install the runtime only when this environment is not ready.
"%PY%" -c "import streamlit" >nul 2>&1
if errorlevel 1 (
	echo Streamlit no esta instalado. Instalando el runtime principal...
	"%PY%" -m pip install streamlit
	if errorlevel 1 (
		echo ERROR: No se pudieron instalar las dependencias.
		pause
		exit /b 1
	)
)

REM The Python launcher selects a free port, waits for HTTP readiness, and opens the browser.
"%PY%" scripts\open_is_backoffice.py --python "%PY%" --cwd "%~dp0." --page "" --wait 45
if errorlevel 1 (
	echo ERROR: IS-BACKOFFICE no pudo iniciar.
	pause
	exit /b 1
)

endlocal

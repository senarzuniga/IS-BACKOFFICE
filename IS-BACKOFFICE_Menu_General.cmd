@echo off
REM IS-BACKOFFICE Menu Launcher - single entrypoint
REM Usage: double-click this file or run from cmd

setlocal
cd /d "%~dp0"

REM Prefer virtual environment python if present
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
	set "PY=python"
)

REM Ensure streamlit is installed in selected python
"%PY%" -m pip show streamlit >nul 2>&1
if %ERRORLEVEL% neq 0 (
	echo Streamlit not found in %PY%. Installing requirements (may take a while)...
	"%PY%" -m pip install -r requirements.txt
)

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
echo Pruebe cerrar otras instancias de la aplicación o cambiar el rango de puertos.
pause
exit /b 1

:port_found
echo Usando puerto %PORT%

REM Open browser
start "" "http://localhost:%PORT%"

REM Launch Streamlit (logs will appear in this window)
echo Iniciando Streamlit con %PY%
"%PY%" -m streamlit run streamlit_app.py --server.port %PORT% --server.fileWatcherType none

endlocal

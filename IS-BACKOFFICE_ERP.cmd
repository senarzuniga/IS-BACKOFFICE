@echo off
setlocal
cd /d "%~dp0"

set "PORT="
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

for /l %%P in (8514,1,8535) do (
    netstat -ano | findstr /r /c:":%%P .*LISTENING" >nul
    if errorlevel 1 (
        set "PORT=%%P"
        goto :port_found
    )
)

echo No se encontro un puerto libre entre 8514 y 8535.
pause
exit /b 1

:port_found
start "" "http://localhost:%PORT%"
"%PY%" -m streamlit run pages/facturacion.py --server.port %PORT% --server.fileWatcherType none

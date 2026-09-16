@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "APP_ROOT=%~dp0"
set "PY_CMD=python"
where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        echo Python no encontrado. Instala Python 3.11+ y vuelve a ejecutar este acceso directo.
        pause
        exit /b 1
    )
    set "PY_CMD=py -3"
)

call %PY_CMD% -m pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo Streamlit no encontrado. Instalando dependencias del proyecto...
    call %PY_CMD% -m pip install -r "%APP_ROOT%requirements.txt"
    if errorlevel 1 (
        echo Error durante la instalacion de dependencias.
        pause
        exit /b 1
    )
)

set "PORT="
for /l %%P in (8501,1,8530) do (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, %%P); try { $listener.Start(); $listener.Stop(); exit 0 } catch { exit 1 }" >nul 2>&1
    if not errorlevel 1 (
        set "PORT=%%P"
        goto :port_found
    )
)

echo No se encontro un puerto libre entre 8501 y 8530.
echo Cierra otras instancias o cambia el rango de puertos.
pause
exit /b 1

:port_found
echo Usando puerto %PORT%
start "" "http://localhost:%PORT%"

echo Iniciando IS-BACKOFFICE con Streamlit en el puerto %PORT%...
start "IS-BACKOFFICE" cmd /c "call %PY_CMD% -m streamlit run streamlit_app.py --server.port %PORT% --server.address localhost --server.fileWatcherType none --browser.gatherUsageStats false"

exit /b 0


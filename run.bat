@echo off
REM run.bat — Launch IS-BACKOFFICE Streamlit application (improved)

setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "PORT_FILE=.streamlit_last_port"
set "DEFAULT_PORT=8501"
set "MAX_PORT=8530"

REM Prefer the project's virtual environment if present
set "PY_EXE=.venv\Scripts\python.exe"
set "PY_CMD="%PY_EXE%""
set "PY_ARGS="
if not exist "%PY_EXE%" (
    set "PY_CMD=python"
)

REM Validate Python executable/command before continuing
if /i "%PY_CMD%"=="python" (
    where python >nul 2>&1
    if errorlevel 1 (
        echo Python is not available in PATH.
        pause
        exit /b 1
    )
)

REM Reuse the last known port if Streamlit is already active there.
set "SAVED_PORT="
if exist "%PORT_FILE%" (
    set /p SAVED_PORT=<"%PORT_FILE%"
)

if defined SAVED_PORT (
    call :is_port_alive !SAVED_PORT!
    if not errorlevel 1 (
        echo Streamlit ya esta activo en el puerto !SAVED_PORT!.
        start "" "http://localhost:!SAVED_PORT!"
        endlocal & exit /b 0
    )
)

REM Prefer the default port when the previous instance is stopped.
set "PORT=%DEFAULT_PORT%"
call :is_port_free %PORT%
if errorlevel 1 (
    REM If default port is busy, search a free alternative.
    set "PORT="
    for /l %%P in (%DEFAULT_PORT%,1,%MAX_PORT%) do (
        call :is_port_free %%P
        if not errorlevel 1 (
            set "PORT=%%P"
            goto :port_found
        )
    )

    echo No se encontro un puerto libre entre %DEFAULT_PORT% y %MAX_PORT%.
    pause
    exit /b 1
)

:port_found
echo Usando puerto %PORT%

REM Ensure streamlit is installed in the selected Python
call %PY_CMD% %PY_ARGS% -m pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo Streamlit not found. Installing dependencies...
    call %PY_CMD% %PY_ARGS% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency installation failed.
        pause
        exit /b 1
    )
)

echo Iniciando IS-BACKOFFICE en una nueva ventana...
start "IS-BACKOFFICE" cmd /k "cd /d "%~dp0" && %PY_CMD% %PY_ARGS% -m streamlit run streamlit_app.py --server.port %PORT% --server.fileWatcherType none"

set "READY=0"
for /L %%S in (1,1,30) do (
    call :is_port_alive %PORT%
    if not errorlevel 1 (
        set "READY=1"
        goto :open_menu
    )
)

:open_menu
if "%READY%"=="1" (
    >"%PORT_FILE%" echo %PORT%
    echo Streamlit listo. Abriendo menu general de IS-BACKOFFICE...
    start "" "http://localhost:%PORT%"
    endlocal & exit /b 0
)

echo Streamlit no respondio a tiempo. Revisa la ventana "IS-BACKOFFICE" para ver logs.
pause
set "APP_EXIT=1"

endlocal & exit /b %APP_EXIT%

:is_port_alive
powershell -NoProfile -Command "if ((Test-NetConnection -ComputerName 127.0.0.1 -Port %1 -WarningAction SilentlyContinue).TcpTestSucceeded) { exit 0 } else { exit 1 }" >nul 2>&1
exit /b %ERRORLEVEL%

:is_port_free
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort %1 -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }" >nul 2>&1
exit /b %ERRORLEVEL%

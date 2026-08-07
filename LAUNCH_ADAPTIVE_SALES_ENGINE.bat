@echo off
setlocal EnableExtensions

REM Launch Adaptive Sales Engine (Streamlit) from sibling repository.
REM Optional: pass --validate to run a smoke test with Ingecart demo pack before launch.

set "ROOT_DIR=%~dp0"
for %%I in ("%ROOT_DIR%..\adaptive-sales-engine") do set "ASE_REPO=%%~fI"

if not exist "%ASE_REPO%\streamlit_app.py" (
  echo [ERROR] streamlit_app.py not found in: %ASE_REPO%
  echo         Verify Adaptive Sales Engine repo location.
  exit /b 1
)

set "PYTHON_EXE=%ASE_REPO%\.venv\Scripts\python.exe"
set "PYTHON_CMD="%PYTHON_EXE%""
set "PYTHON_ARGS="
if not exist "%PYTHON_EXE%" (
  echo [WARN] Python venv not found at: %PYTHON_EXE%
  echo [INFO] Falling back to py -3 from PATH.
  set "PYTHON_CMD=py"
  set "PYTHON_ARGS=-3"
)

set "SRC_PACK=C:\Users\Inaki Senar\Documents\GitHub\adaptive-sales-engine\Architecture\outputs\archives\1782712887\public\company-packs\IngecartDemo\ingecart_demo_pack.json"
set "DST_PACK_DIR=%ASE_REPO%\public\company-packs\IngecartDemo"
set "DST_PACK=%DST_PACK_DIR%\ingecart_demo_pack.json"

if /I "%~1"=="--validate" (
  echo [INFO] Running validation with Ingecart demo pack...
  if not exist "%SRC_PACK%" (
    echo [ERROR] Source demo pack not found:
    echo         %SRC_PACK%
    exit /b 1
  )

  if not exist "%DST_PACK_DIR%" mkdir "%DST_PACK_DIR%"
  copy /Y "%SRC_PACK%" "%DST_PACK%" >nul
  if errorlevel 1 (
    echo [ERROR] Could not copy demo pack to canonical location.
    exit /b 1
  )

  pushd "%ASE_REPO%"
  call %PYTHON_CMD% %PYTHON_ARGS% scripts\run_with_company_pack.py
  if errorlevel 1 (
    echo [ERROR] Smoke test failed. Aborting launch.
    popd
    exit /b 1
  )
  popd
  echo [OK] Smoke test passed.
)

echo [INFO] Launching Adaptive Sales Engine Streamlit app (main menu)...
pushd "%ASE_REPO%"

set "STREAMLIT_PORT=8517"
set "APP_URL=http://localhost:%STREAMLIT_PORT%"

start "Adaptive Sales Engine" cmd /k "cd /d "%ASE_REPO%" && %PYTHON_CMD% %PYTHON_ARGS% -m streamlit run streamlit_app.py --server.headless true --server.port %STREAMLIT_PORT%"

set "READY=0"
for /L %%G in (1,1,30) do (
  powershell -NoProfile -Command "if ((Test-NetConnection -ComputerName 127.0.0.1 -Port %STREAMLIT_PORT% -WarningAction SilentlyContinue).TcpTestSucceeded) { exit 0 } else { exit 1 }" >nul 2>&1
  if not errorlevel 1 (
    set "READY=1"
    goto :open_ui
  )
)

:open_ui
if "%READY%"=="1" (
  echo [OK] Application is up. Opening general menu in browser: %APP_URL%
  start "" "%APP_URL%"
  popd
  exit /b 0
)

echo [WARN] Server startup check timed out. You can still open: %APP_URL%
popd
exit /b 1

@echo off
REM run.bat — Launch IS-BACKOFFICE Streamlit application

cd /d "%~dp0"
REM Prefer the project's virtual environment if present
if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

REM Ensure streamlit is installed in the selected Python
"%PYTHON%" -m pip show streamlit >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Streamlit not found. Installing dependencies into %PYTHON%...
    "%PYTHON%" -m pip install -r requirements.txt
)

echo Starting IS-BACKOFFICE Streamlit app at http://localhost:8501
"%PYTHON%" -m streamlit run streamlit_app.py

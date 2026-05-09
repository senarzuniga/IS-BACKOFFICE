@echo off
REM run.bat — Launch IS-BACKOFFICE Streamlit application

cd /d "%~dp0"

where streamlit >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Streamlit not found. Installing dependencies...
    pip install -r requirements.txt
)

echo Starting IS-BACKOFFICE Streamlit app at http://localhost:8501
streamlit run streamlit_app.py

#!/usr/bin/env bash
# run.sh — Launch IS-BACKOFFICE Streamlit application
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verify streamlit is available
if ! command -v streamlit &>/dev/null; then
    echo "Streamlit not found. Installing dependencies..."
    pip install -r requirements.txt
fi

echo "Starting IS-BACKOFFICE Streamlit app at http://localhost:8501"
streamlit run streamlit_app.py

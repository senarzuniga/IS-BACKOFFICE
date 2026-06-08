#!/bin/bash
echo "========================================"
echo "   IS-BACKOFFICE - Lanzador"
echo "========================================"
cd "/c/Users/Inaki Senar/Documents/GitHub/IS-BACKOFFICE"
echo "📂 Directorio: $(pwd)"
PORT=8511
echo "✅ Puerto: $PORT"
echo "🌐 Abriendo navegador..."
cmd //c start "http://localhost:$PORT"
echo "🚀 Iniciando Streamlit..."
".venv/Scripts/python.exe" -m streamlit run streamlit_app.py --server.port $PORT --server.fileWatcherType none

"""
Página Streamlit para envío automático de correos — Ingecart
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


import streamlit as st
import importlib.util
import sys
from pathlib import Path

# Cargar el módulo main.py de email_sender dinámicamente
email_sender_path = Path(__file__).parent.parent / "ingecart-marketing-kit" / "email_sender" / "main.py"
spec = importlib.util.spec_from_file_location("email_sender_main", str(email_sender_path))
email_sender_main = importlib.util.module_from_spec(spec)
sys.modules["email_sender_main"] = email_sender_main
spec.loader.exec_module(email_sender_main)


# Ejecutar la función principal de la app de envío de correos
if hasattr(email_sender_main, "main"):
    email_sender_main.main()
else:
    # Si no hay función main, ejecuta el script como módulo
    pass

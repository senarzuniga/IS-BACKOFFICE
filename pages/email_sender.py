"""
Página Streamlit para envío automático de correos — Ingecart
"""
# ============================================
# EMAIL SENDER PARA IONOS SE
# Cuenta: cgo@ingecart.es
# ============================================

import os
import smtplib
import streamlit as st
import pandas as pd
import email
from email import policy

UPLOAD_DIR = "uploaded_campaign_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.title("📧 Campaña de Emails IONOS SE - INGECART (Guardar Archivos)")
st.write("""
1. Sube un archivo Excel con las columnas **Nombre** y **Email**.
2. Sube un archivo .eml como plantilla del mensaje (usa # donde irá el nombre).
3. Pulsa 'Guardar archivos' para almacenarlos y luego ejecuta el script de envío.
""")

excel_file = st.file_uploader("Excel de destinatarios (Nombre, Email)", type=["xlsx", "xls", "csv"])
eml_file = st.file_uploader("Plantilla de correo (.eml)", type=["eml"])

if st.button("Guardar archivos"):
    if not (excel_file and eml_file):
        st.warning("Completa todos los campos y sube los archivos necesarios.")
    else:
        excel_path = os.path.join(UPLOAD_DIR, "destinatarios.xlsx")
        eml_path = os.path.join(UPLOAD_DIR, "plantilla.eml")
        # Guardar Excel
        with open(excel_path, "wb") as f:
            f.write(excel_file.getbuffer())
        # Guardar EML
        with open(eml_path, "wb") as f:
            f.write(eml_file.getbuffer())
        st.success(f"Archivos guardados en la carpeta '{UPLOAD_DIR}'. Ejecuta el script de envío para completar la campaña.")
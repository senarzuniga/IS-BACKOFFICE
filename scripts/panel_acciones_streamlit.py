import streamlit as st
import pandas as pd
import os

# Ruta del Excel generado
destino = "ingecart-marketing-kit/FESPA 2026 RESULTADOS/acciones_comerciales_leads.xlsx"

# Cargar resumen de acciones
df = pd.read_excel(destino, sheet_name="Resumen Acciones")

st.set_page_config(page_title="Panel Acciones Comerciales FESPA 2026", layout="wide")
st.title("Panel de Acciones Comerciales — FESPA 2026")

st.markdown("""
**Haz clic en una acción para ver todos los detalles.**
""")

# Mostrar tabla resumen
table = st.dataframe(df)

# Selección de acción
opciones = df.apply(lambda x: f"{x['Lead']} — {x['Empresa']} — {x['Acción'][:40]}", axis=1)
action_selected = st.selectbox(
    "Selecciona una acción para ver detalles:",
    opciones
)
lead_name = action_selected.split(" — ")[0]

# Buscar hoja correspondiente (nombre hoja sanitizado)
import re
hoja_nombre = lead_name[:28]
hoja_nombre = re.sub(r"[\\/?*\[\]]", "_", hoja_nombre)

with pd.ExcelFile(destino) as xls:
    ficha = pd.read_excel(xls, sheet_name=hoja_nombre)

st.subheader(f"Detalles de la acción: {lead_name}")
for i, row in ficha.iterrows():
    st.markdown(f"**{row['Campo']}:** {row['Valor']}")

st.info("Este panel es un ejemplo y puede integrarse en tu aplicación principal.")

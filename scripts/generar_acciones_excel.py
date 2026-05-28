import pandas as pd
import os
from datetime import datetime, timedelta
import re

# Cargar leads enriquecidos
df = pd.read_excel("ingecart-marketing-kit/FESPA 2026 RESULTADOS/leads_fespa2026_enriched.xlsx")

acciones = []
fichas = {}

for idx, row in df.iterrows():
    nombre = str(row.get("Nombre", "")).strip()
    empresa = str(row.get("Empresa", "")).strip()
    cargo = str(row.get("Cargo", "")).strip()
    email = str(row.get("Email", "")).strip()
    tel = str(row.get("Teléfono", "")).strip()
    interes = str(row.get("Notas / Interés", "")).strip()
    proxima = str(row.get("Próxima Acción", "")).strip()
    contexto = str(row.get("Company Context", "")).strip()
    prioridad = "Alta" if "muy interesado" in interes.lower() or "prioridad" in proxima.lower() else "Media"
    urgencia = "Alta" if "contactar" in proxima.lower() or "demo" in proxima.lower() else "Media"
    fecha_limite = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    criticidad = "85/100" if prioridad == "Alta" else "70/100"
    estado = "Pendiente"
    kpis = "Contacto, Interés, Reunión"
    mini_desc = f"{proxima[:60]}..." if len(proxima) > 60 else proxima
    accion = f"{proxima} ({interes})"
    acciones.append({
        "Lead": nombre,
        "Empresa": empresa,
        "Acción": mini_desc,
        "Prioridad": prioridad,
        "Urgencia": urgencia,
        "Fecha Límite": fecha_limite,
        "Criticidad": criticidad,
        "Estado": estado,
        "KPIs": kpis
    })
    # Limpiar nombre para hoja Excel
    hoja_nombre = nombre[:28] or f"Lead_{idx}"
    hoja_nombre = re.sub(r"[\\/?*\[\]]", "_", hoja_nombre)
    ficha = {
        "Campo": [
            "Lead", "Empresa", "Cargo", "Email", "Teléfono", "Acción", "Prioridad", "Urgencia", "Fecha Límite", "Criticidad", "Estado", "KPIs", "Contexto", "Notas / Interés", "Próxima Acción"
        ],
        "Valor": [
            nombre, empresa, cargo, email, tel, accion, prioridad, urgencia, fecha_limite, criticidad, estado, kpis, contexto, interes, proxima
        ]
    }
    fichas[hoja_nombre] = ficha

# Crear Excel con hoja resumen y una hoja por acción
destino = "ingecart-marketing-kit/FESPA 2026 RESULTADOS/acciones_comerciales_leads.xlsx"
with pd.ExcelWriter(destino, engine="openpyxl", mode="w") as writer:
    pd.DataFrame(acciones).to_excel(writer, sheet_name="Resumen Acciones", index=False)
    for nombre, ficha in fichas.items():
        pd.DataFrame(ficha).to_excel(writer, sheet_name=nombre, index=False)
print(f"Excel generado: {destino}")

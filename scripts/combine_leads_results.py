import pandas as pd
import os

# Paths
base = "ingecart-marketing-kit/FESPA 2026 RESULTADOS/"
leads_path = os.path.join(base, "leads_fespa2026_enriched.xlsx")
acciones_path = os.path.join(base, "leads_fespa2026_acciones.xlsx")
output_path = os.path.join(base, "leads_fespa2026_enriched_con_resultados.xlsx")

# Cargar leads y acciones
leads = pd.read_excel(leads_path)
acciones = pd.read_excel(acciones_path)

# Unir por nombre y empresa (mejor aproximación)
leads_acciones = pd.merge(
    leads,
    acciones,
    left_on=["Nombre", "Empresa"],
    right_on=["name", "comments"],
    how="left",
    suffixes=("", "_accion")
)

# Si no hay match exacto, unir por nombre (más laxo)
if leads_acciones.isnull().any(axis=None):
    acciones_simple = acciones.copy()
    acciones_simple["Empresa"] = acciones_simple["name"].str.extract(r"\((.*?)\)")
    acciones_simple["Nombre"] = acciones_simple["name"].str.split("(").str[0].str.replace("Contacto con ", "").str.strip()
    leads_acciones = pd.merge(
        leads,
        acciones_simple,
        on=["Nombre", "Empresa"],
        how="left",
        suffixes=("", "_accion")
    )

# Añadir columna de estado y prioridad de acción
if "status" in leads_acciones.columns:
    leads_acciones["Estado Acción"] = leads_acciones["status"]
if "priority" in leads_acciones.columns:
    leads_acciones["Prioridad Acción"] = leads_acciones["priority"]

# Guardar
leads_acciones.to_excel(output_path, index=False)
print(f"Archivo combinado generado: {output_path}")

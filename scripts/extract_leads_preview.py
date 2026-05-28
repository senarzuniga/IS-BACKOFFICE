import pandas as pd
import requests
from bs4 import BeautifulSoup
import os

# Ruta del archivo original
EXCEL_PATH = r"C:\Users\Inaki Senar\Documents\INGECART\MARKETING\FERIAS\FESPA 2026 BARCELONA\Leads_Ingecart FESPA 2026.xlsx"

# Cargar el archivo Excel
leads = pd.read_excel(EXCEL_PATH)

# Mostrar las primeras filas para inspección
print(leads.head())
print(leads.columns)
print(f"Total de leads: {len(leads)}")

# Guardar una copia CSV temporal para inspección
leads.to_csv("leads_fespa2026_temp.csv", index=False)

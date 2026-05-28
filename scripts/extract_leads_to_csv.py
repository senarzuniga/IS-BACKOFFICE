import pandas as pd
import os

EXCEL_PATH = r"C:\Users\Inaki Senar\Documents\INGECART\MARKETING\FERIAS\FESPA 2026 BARCELONA\Leads_Ingecart FESPA 2026.xlsx"
CSV_PATH = "scripts/leads_fespa2026_temp.csv"

leads = pd.read_excel(EXCEL_PATH)
leads.to_csv(CSV_PATH, index=False)
print(f"Archivo CSV generado en: {CSV_PATH}")

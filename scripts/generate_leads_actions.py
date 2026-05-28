import pandas as pd
import uuid
from datetime import datetime

# Cargar leads enriquecidos
leads = pd.read_excel('scripts/leads_fespa2026_enriched.xlsx')

# Plantilla de acciones
headers = [
    'action_id', 'name', 'goal', 'assigned_to_role', 'status', 'comments',
    'created_at', 'last_modified', 'supportive_content_json', 'required_info_json',
    'department', 'priority'
]

acciones = []

for idx, row in leads.iterrows():
    action_id = str(uuid.uuid4())
    name = f"Contacto con {row['Nombre']} ({row['Empresa']})"
    goal = f"Convertir lead en oportunidad comercial. {row['Notas / Interés']}"
    assigned_to_role = "Comercial"
    status = "open"
    comments = f"{row['Próxima Acción']} | Contexto empresa: {row.get('Company Context', '')}"
    created_at = datetime.now().strftime('%Y-%m-%d')
    last_modified = created_at
    supportive_content_json = "{}"
    required_info_json = "{}"
    department = "Commercial"
    priority = "Alta" if 'muy interesado' in str(row['Notas / Interés']).lower() or 'avanzar' in str(row['Próxima Acción']).lower() else "Media"
    acciones.append([
        action_id, name, goal, assigned_to_role, status, comments,
        created_at, last_modified, supportive_content_json, required_info_json,
        department, priority
    ])

acciones_df = pd.DataFrame(acciones, columns=headers)
acciones_df.to_excel('scripts/leads_fespa2026_acciones.xlsx', index=False)
print('Archivo de acciones generado: scripts/leads_fespa2026_acciones.xlsx')
